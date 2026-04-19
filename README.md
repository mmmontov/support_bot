# Telegram support bot

FastAPI holds ticket logic and SQLite storage; the [aiogram](https://docs.aiogram.dev/) 3 bot calls the API over HTTP. Configure everything via `.env` (see `.env.example`).

### Project layout

- `src/support_bot/` — shared package: `api/` (FastAPI), `bot/` (aiogram), `db/` (SQLAlchemy models).
- `docker/api/Dockerfile` — image for the REST API and Alembic migrations.
- `docker/bot/Dockerfile` — image for the Telegram bot only.
- `alembic/` — migrations (used by the API container and in local dev).
- `scripts/` — local dev helpers (`run_api.py`, `run_bot.py`).

## Requirements

- Python 3.11+
- A Telegram bot token and a dedicated admin group/supergroup chat ID (negative for groups)

## Setup

1. Copy `.env.example` to `.env` and set `BOT_TOKEN`, `API_SECRET`, `ADMIN_CHAT_ID`, and optionally `DATABASE_URL`, `API_BASE_URL`, `API_HOST`, `API_PORT`.

2. Install dependencies and the package in editable mode:

   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```

   Production-only (no pytest):

   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

3. Apply database migrations:

   ```bash
   set PYTHONPATH=src
   python -m alembic upgrade head
   ```

   On Linux/macOS use `export PYTHONPATH=src` instead of `set`.

## Run

Start the API and the bot in two terminals from the project root.

**Terminal 1 — API**

```bash
set PYTHONPATH=src
python scripts/run_api.py
```

**Terminal 2 — bot**

```bash
set PYTHONPATH=src
python scripts/run_bot.py
```

The API defaults to `http://127.0.0.1:8000`. OpenAPI docs: `http://127.0.0.1:8000/docs`.

## Docker

1. Copy `.env.example` to `.env` and set `BOT_TOKEN`, `API_SECRET`, `ADMIN_CHAT_ID` (and optionally `API_PORT` for the host port, default `8000`).
2. Build and start API + bot (two containers, two images):

   ```bash
   docker compose up -d --build
   ```

The API container runs `alembic upgrade head` then `uvicorn`, stores SQLite in the volume `app_data` mounted at `/data`, and publishes `8000` (or `API_PORT`). The bot container uses `API_BASE_URL=http://api:8000` on the compose network. Logs: `docker compose logs -f api` / `docker compose logs -f bot`.

## Behaviour (short)

- Users use `/start`, choose a topic, then send text and/or photo, video, or document. New tickets are rate-limited to one per five minutes per user.
- The bot posts ticket headers into the admin chat and registers those message IDs so admins can **reply** to route answers back.
- Admins reply in the admin chat to answer users; `/close` as a **reply** to a ticket message closes the ticket and notifies the user.

## API endpoints

All bot-facing routes expect header `X-Bot-Token: <API_SECRET>`.

- `POST /tickets/create`
- `POST /tickets/{id}/message`
- `POST /tickets/{id}/close`
- `GET /tickets/by-admin-message/{message_id}`
- `GET /users/{telegram_id}`
- `POST /tickets/{id}/register-admin-message` — maps an admin-chat message id to a ticket (required for reply routing)
- `POST /tickets/{id}/admin-reply` — persists an admin message after the bot delivers it to the user

Health check: `GET /health`
