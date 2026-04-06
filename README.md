# SportPredict — угадай момент события

Интерактивная игра: пользователи смотрят трансляции спортивных и киберспортивных событий и нажимают кнопку точно в момент ключевого события (гол, фраг, победа). Чем точнее — тем больше очков. После каждой ставки AI генерирует саркастичный комментарий.

## Возможности

- Две категории: ⚽ Спорт и 🎮 Киберспорт
- Ставка кнопкой или голосом (Whisper API)
- Серверный таймер — время нельзя подделать на клиенте
- Одна ставка на событие для каждого игрока
- AI-комментарий к результату (GPT-4o-mini)
- Турнирная таблица в реальном времени

## Стек

- **Backend:** Python, FastAPI, SQLite
- **Frontend:** HTML, Tailwind CSS (CDN)
- **AI:** OpenAI GPT-4o-mini (комментарии), Whisper (голос)
- **Deploy:** Render

## Установка и запуск

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Создайте `.env` по образцу `.env.example` и заполните переменные.

```bash
uvicorn main:app --reload
```

Откройте [http://localhost:8000](http://localhost:8000)

## Переменные окружения

| Переменная | Описание |
|---|---|
| `OPENAI_API_KEY` | Ключ OpenAI API |
| `SPORT_EVENT_NAME` | Название спортивного события |
| `SPORT_VIDEO_EMBED_URL` | Embed-ссылка на видео (YouTube) |
| `SPORT_EVENT_TIME_SECONDS` | Секунда события в видео |
| `ESPORT_EVENT_NAME` | Название киберспортивного события |
| `ESPORT_VIDEO_EMBED_URL` | Embed-ссылка на видео (YouTube) |
| `ESPORT_EVENT_TIME_SECONDS` | Секунда события в видео |

## Структура проекта

```
.
├── main.py          # FastAPI-приложение, все маршруты
├── database.py      # Инициализация и работа с SQLite
├── ai_comment.py    # GPT-комментарии и Whisper-транскрипция
├── static/
│   └── index.html   # Фронтенд (одна страница)
├── requirements.txt
├── runtime.txt
└── .env.example
```

## Деплой на Render

1. Создайте Web Service, подключите репозиторий
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Добавьте все переменные из `.env` в Environment Variables
