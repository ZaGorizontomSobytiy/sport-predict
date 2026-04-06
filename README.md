# SportPredict ⚡

Интерактивная игра: угадай момент ключевого события в спортивной или киберспортивной трансляции. Нажми кнопку или крикни в микрофон точно в момент гола, фрага или победы — система сравнивает твою реакцию с эталоном и начисляет очки.

**Live demo:** https://sport-predict-bpvp.onrender.com

---

## Как играть

1. Выберите категорию — ⚽ Спорт или 🎮 Киберспорт
2. Введите никнейм и нажмите **«Начать просмотр»**
3. Запустите видео и нажмите **«▶ Старт таймера»**
4. В момент события нажмите **СЕЙЧАС!** или крикните ключевое слово в микрофон
5. Получите очки и AI-комментарий к результату

---

## Возможности

- **Две категории:** Спорт и Киберспорт с независимыми событиями и таблицами
- **Голосовой ввод:** транскрипция через Whisper API — работает в любом браузере
- **Антифрод:** серверный таймер — клиент не может подделать время ставки
- **Одна ставка на событие** для каждого игрока
- **AI-комментарий** к результату через GPT-4o-mini
- **Турнирная таблица** в реальном времени
- **Постоянная БД:** PostgreSQL на продакшене, SQLite локально

---

## Стек

| Слой | Технологии |
|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy |
| Frontend | HTML, Tailwind CSS (CDN), Vanilla JS |
| База данных | PostgreSQL (Render) / SQLite (dev) |
| AI | OpenAI GPT-4o-mini, Whisper API |
| Deploy | Render.com |

---

## Архитектура

```
┌─────────────────────────────────────────┐
│              Браузер                    │
│  Tailwind UI  │  YouTube iframe         │
│  Таймер JS    │  MediaRecorder API      │
└──────────────┬──────────────────────────┘
               │ HTTP
┌──────────────▼──────────────────────────┐
│           FastAPI (main.py)             │
│                                         │
│  GET  /api/event?category=              │
│  POST /api/start     ← старт таймера    │
│  POST /api/predict   ← ставка кнопкой  │
│  POST /api/voice-predict ← Whisper      │
│  GET  /api/leaderboard?category=        │
└──────────┬──────────────┬───────────────┘
           │              │
┌──────────▼───┐   ┌──────▼──────────────┐
│  PostgreSQL  │   │   OpenAI API        │
│  (database)  │   │  GPT-4o-mini        │
│              │   │  Whisper-1          │
└──────────────┘   └─────────────────────┘
```

**Защита от читерства:**
- Время фиксируется на сервере в момент `POST /api/start`
- Ставки после эталонного времени отклоняются
- Одна ставка на событие для каждого никнейма

---

## Локальный запуск

```bash
git clone https://github.com/ZaGorizontomSobytiy/sport-predict.git
cd sport-predict

python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Создайте `.env` по образцу `.env.example`:

```env
OPENAI_API_KEY=your_key

SPORT_EVENT_NAME=Ювентус — Реал Мадрид: угадай первый гол
SPORT_VIDEO_EMBED_URL=https://www.youtube.com/embed/VIDEO_ID
SPORT_EVENT_TIME_SECONDS=76

ESPORT_EVENT_NAME=Mortal Kombat: угадай победный момент
ESPORT_VIDEO_EMBED_URL=https://www.youtube.com/embed/VIDEO_ID
ESPORT_EVENT_TIME_SECONDS=153
```

```bash
uvicorn main:app --reload
```

Откройте [http://localhost:8000](http://localhost:8000)

---

## Деплой на Render

1. Fork репозитория → New Web Service на [render.com](https://render.com)
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Создайте PostgreSQL (Free) → скопируйте Internal Database URL
5. Environment Variables: добавьте все переменные из `.env` + `DATABASE_URL`

---

## Структура проекта

```
sport-predict/
├── main.py          # FastAPI: все маршруты и бизнес-логика
├── database.py      # SQLAlchemy: поддержка SQLite и PostgreSQL
├── ai_comment.py    # OpenAI: GPT-комментарии и Whisper-транскрипция
├── static/
│   └── index.html   # SPA: UI, таймер, голосовой ввод
├── requirements.txt
├── runtime.txt
├── .env.example
└── .gitignore
```

---

## Переменные окружения

| Переменная | Описание |
|---|---|
| `OPENAI_API_KEY` | Ключ OpenAI API |
| `DATABASE_URL` | PostgreSQL URL (опционально, иначе SQLite) |
| `SPORT_EVENT_NAME` | Название спортивного события |
| `SPORT_VIDEO_EMBED_URL` | YouTube embed URL |
| `SPORT_EVENT_TIME_SECONDS` | Секунда события в видео |
| `ESPORT_EVENT_NAME` | Название киберспортивного события |
| `ESPORT_VIDEO_EMBED_URL` | YouTube embed URL |
| `ESPORT_EVENT_TIME_SECONDS` | Секунда события в видео |
