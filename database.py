"""Работа с базой данных SQLite."""

import os
import sqlite3
from contextlib import contextmanager

DB_PATH = "game.db"


def init_db() -> None:
    """Создаёт таблицы и добавляет демо-события при первом запуске."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                name               TEXT    NOT NULL,
                video_embed_url    TEXT    NOT NULL,
                event_time_seconds REAL    NOT NULL,
                category           TEXT    NOT NULL DEFAULT 'sport',
                is_active          INTEGER DEFAULT 1
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id         INTEGER   PRIMARY KEY AUTOINCREMENT,
                token      TEXT      NOT NULL UNIQUE,
                event_id   INTEGER   NOT NULL,
                nickname   TEXT      NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id             INTEGER   PRIMARY KEY AUTOINCREMENT,
                event_id       INTEGER   NOT NULL,
                nickname       TEXT      NOT NULL,
                elapsed_time   REAL      NOT NULL,
                score          INTEGER   NOT NULL,
                created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(event_id, nickname)
            )
        """)

        _seed_events(conn)


def _seed_events(conn: sqlite3.Connection) -> None:
    """Добавляет стартовые события если их ещё нет."""
    for category, prefix in (("sport", "SPORT"), ("esport", "ESPORT")):
        exists = conn.execute(
            "SELECT 1 FROM events WHERE category = ? AND is_active = 1", (category,)
        ).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO events (name, video_embed_url, event_time_seconds, category) VALUES (?, ?, ?, ?)",
                (
                    os.getenv(f"{prefix}_EVENT_NAME", f"Demo {category}"),
                    os.getenv(f"{prefix}_VIDEO_EMBED_URL", ""),
                    float(os.getenv(f"{prefix}_EVENT_TIME_SECONDS", "60")),
                    category,
                ),
            )


@contextmanager
def get_conn():
    """Контекстный менеджер для подключения к SQLite с автокоммитом."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
