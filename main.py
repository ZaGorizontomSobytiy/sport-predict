"""FastAPI-приложение: игра «Угадай момент события»."""

from dotenv import load_dotenv

load_dotenv()

import uuid
from datetime import datetime, timezone
from typing import Literal

import ai_comment
import database
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import text

app = FastAPI(title="SportPredict")


@app.on_event("startup")
def on_startup() -> None:
    database.init_db()


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    return FileResponse("static/index.html")


@app.get("/api/event")
def get_active_event(category: Literal["sport", "esport"] = "sport") -> dict:
    """Возвращает активное событие по категории."""
    with database.get_conn() as conn:
        row = conn.execute(
            text("SELECT * FROM events WHERE is_active = 1 AND category = :cat ORDER BY id DESC LIMIT 1"),
            {"cat": category},
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Нет активных событий")
    return database.row_to_dict(row)


class StartRequest(BaseModel):
    event_id: int
    nickname: str = Field(min_length=1, max_length=30)


@app.post("/api/start")
def start_session(data: StartRequest) -> dict:
    """Фиксирует серверное время начала просмотра, возвращает токен сессии."""
    with database.get_conn() as conn:
        if not conn.execute(
            text("SELECT 1 FROM events WHERE id = :id AND is_active = 1"),
            {"id": data.event_id},
        ).fetchone():
            raise HTTPException(status_code=404, detail="Событие не найдено")

        if conn.execute(
            text("SELECT 1 FROM predictions WHERE event_id = :eid AND nickname = :nick"),
            {"eid": data.event_id, "nick": data.nickname},
        ).fetchone():
            raise HTTPException(status_code=400, detail="Вы уже сделали ставку на это событие")

        conn.execute(
            text("DELETE FROM sessions WHERE event_id = :eid AND nickname = :nick"),
            {"eid": data.event_id, "nick": data.nickname},
        )

        token = str(uuid.uuid4())
        conn.execute(
            text("INSERT INTO sessions (token, event_id, nickname) VALUES (:token, :eid, :nick)"),
            {"token": token, "eid": data.event_id, "nick": data.nickname},
        )

    return {"session_token": token}


async def _execute_prediction(session_token: str) -> dict:
    """Вычисляет очки по токену сессии и возвращает результат с AI-комментарием."""
    with database.get_conn() as conn:
        session_row = conn.execute(
            text("SELECT * FROM sessions WHERE token = :token"),
            {"token": session_token},
        ).fetchone()
        if not session_row:
            raise HTTPException(status_code=404, detail="Сессия не найдена")

        session = database.row_to_dict(session_row)

        event_row = conn.execute(
            text("SELECT * FROM events WHERE id = :id AND is_active = 1"),
            {"id": session["event_id"]},
        ).fetchone()
        if not event_row:
            raise HTTPException(status_code=404, detail="Событие не найдено")

        event = database.row_to_dict(event_row)

        # PostgreSQL возвращает datetime, SQLite — строку
        started_raw = session["started_at"]
        if isinstance(started_raw, str):
            started_at = datetime.fromisoformat(started_raw).replace(tzinfo=timezone.utc)
        else:
            started_at = started_raw if started_raw.tzinfo else started_raw.replace(tzinfo=timezone.utc)

        elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()

        if elapsed >= event["event_time_seconds"]:
            raise HTTPException(status_code=400, detail="Момент события уже прошёл — слишком поздно")

        if conn.execute(
            text("SELECT 1 FROM predictions WHERE event_id = :eid AND nickname = :nick"),
            {"eid": session["event_id"], "nick": session["nickname"]},
        ).fetchone():
            raise HTTPException(status_code=400, detail="Вы уже сделали ставку на это событие")

        delta = abs(elapsed - event["event_time_seconds"])
        score = max(0, round(100 - delta * 10))

        conn.execute(
            text("INSERT INTO predictions (event_id, nickname, elapsed_time, score) VALUES (:eid, :nick, :elapsed, :score)"),
            {"eid": session["event_id"], "nick": session["nickname"], "elapsed": elapsed, "score": score},
        )
        conn.execute(
            text("DELETE FROM sessions WHERE token = :token"),
            {"token": session_token},
        )

    comment = await ai_comment.generate(score, delta)
    return {"score": score, "delta": round(delta, 2), "comment": comment}


class PredictRequest(BaseModel):
    session_token: str


@app.post("/api/predict")
async def make_prediction(data: PredictRequest) -> dict:
    """Принимает ставку по кнопке."""
    return await _execute_prediction(data.session_token)


@app.post("/api/voice-predict")
async def voice_predict(
    session_token: str = Form(...),
    audio: UploadFile = File(...),
) -> dict:
    """Транскрибирует аудио через Whisper и делает ставку при обнаружении ключевого слова."""
    audio_bytes = await audio.read()

    try:
        transcript = await ai_comment.transcribe(
            audio_bytes, audio.filename or "recording.webm", audio.content_type or "audio/webm"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка распознавания речи: {e}")

    if not ai_comment.contains_trigger(transcript):
        raise HTTPException(
            status_code=400,
            detail=f"Ключевое слово не услышано. Вы сказали: «{transcript}»",
        )

    return await _execute_prediction(session_token)


@app.get("/api/leaderboard")
def get_leaderboard(category: Literal["sport", "esport"] = "sport") -> list[dict]:
    """Возвращает топ-20 игроков по категории."""
    with database.get_conn() as conn:
        rows = conn.execute(text("""
            SELECT p.nickname, SUM(p.score) AS total_score, COUNT(*) AS predictions
            FROM predictions p
            JOIN events e ON e.id = p.event_id
            WHERE e.category = :cat
            GROUP BY p.nickname
            ORDER BY total_score DESC
            LIMIT 20
        """), {"cat": category}).fetchall()
    return [database.row_to_dict(row) for row in rows]
