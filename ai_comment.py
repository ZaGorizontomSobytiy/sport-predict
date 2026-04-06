"""Генерация AI-комментария и транскрипция речи через OpenAI."""

import io
import os
from openai import AsyncOpenAI

_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

_SYSTEM_PROMPT = (
    "Ты саркастичный спортивный комментатор. "
    "Комментируй точность предсказания одним коротким предложением на русском языке."
)

_TRIGGER_WORDS = {
    "гол", "гооол", "goal", "kill", "убийство", "фраг",
    "победа", "win", "ace", "скорпион", "fatality",
}


async def generate(score: int, delta: float) -> str:
    """Возвращает комментарий модели или запасную фразу при ошибке API."""
    try:
        response = await _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Игрок угадал момент события с точностью до {delta:.1f} сек. "
                        f"и получил {score} очков из 100."
                    ),
                },
            ],
            max_tokens=80,
            temperature=0.9,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return _fallback(score)


async def transcribe(audio_bytes: bytes, filename: str, content_type: str) -> str:
    """Транскрибирует аудио через Whisper API."""
    file_obj = io.BytesIO(audio_bytes)
    file_obj.name = filename or "recording.webm"
    response = await _client.audio.transcriptions.create(
        model="whisper-1",
        file=file_obj,
    )
    return response.text


def contains_trigger(transcript: str) -> bool:
    """Проверяет наличие ключевого слова-триггера в тексте."""
    lower = transcript.lower()
    return any(word in lower for word in _TRIGGER_WORDS)


def _fallback(score: int) -> str:
    if score >= 90:
        return "Снайперская точность — даже боги завидуют."
    if score >= 50:
        return "Неплохо, но чемпионы берут ±0.5 секунды."
    return "Попробуйте ещё раз — или смотрите внимательнее."
