"""Работа с базой данных.

Локально: SQLite.
На Render: PostgreSQL (через переменную DATABASE_URL).
"""

import os
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///game.db")

# Render отдаёт postgres://, SQLAlchemy требует postgresql://
if _DATABASE_URL.startswith("postgres://"):
    _DATABASE_URL = _DATABASE_URL.replace("postgres://", "postgresql://", 1)

_IS_SQLITE = _DATABASE_URL.startswith("sqlite")

_engine = create_engine(
    _DATABASE_URL,
    **({"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
       if _IS_SQLITE else {}),
)


def init_db() -> None:
    """Создаёт таблицы и добавляет демо-события при первом запуске."""
    pk = "INTEGER PRIMARY KEY" if _IS_SQLITE else "SERIAL PRIMARY KEY"

    with _engine.begin() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS events (
                id                 {pk},
                name               TEXT    NOT NULL,
                video_embed_url    TEXT    NOT NULL,
                event_time_seconds REAL    NOT NULL,
                category           TEXT    NOT NULL DEFAULT 'sport',
                is_active          INTEGER DEFAULT 1
            )
        """))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS sessions (
                id         {pk},
                token      TEXT      NOT NULL UNIQUE,
                event_id   INTEGER   NOT NULL,
                nickname   TEXT      NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS predictions (
                id             {pk},
                event_id       INTEGER   NOT NULL,
                nickname       TEXT      NOT NULL,
                elapsed_time   REAL      NOT NULL,
                score          INTEGER   NOT NULL,
                created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(event_id, nickname)
            )
        """))
        _seed_events(conn)


def _seed_events(conn) -> None:
    """Добавляет стартовые события если их ещё нет."""
    for category, prefix in (("sport", "SPORT"), ("esport", "ESPORT")):
        exists = conn.execute(
            text("SELECT 1 FROM events WHERE category = :cat AND is_active = 1"),
            {"cat": category},
        ).fetchone()
        if not exists:
            conn.execute(
                text("""
                    INSERT INTO events (name, video_embed_url, event_time_seconds, category)
                    VALUES (:name, :url, :time, :cat)
                """),
                {
                    "name": os.getenv(f"{prefix}_EVENT_NAME", f"Demo {category}"),
                    "url": os.getenv(f"{prefix}_VIDEO_EMBED_URL", ""),
                    "time": float(os.getenv(f"{prefix}_EVENT_TIME_SECONDS", "60")),
                    "cat": category,
                },
            )


def row_to_dict(row) -> dict:
    """Конвертирует строку результата SQLAlchemy в словарь."""
    return dict(row._mapping)


@contextmanager
def get_conn():
    """Контекстный менеджер для подключения к БД с автокоммитом."""
    with _engine.connect() as conn:
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
