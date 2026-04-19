from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from support_bot.api.routers import tickets, users
from support_bot.config import get_settings, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    yield


def create_app() -> FastAPI:
    get_settings()
    app = FastAPI(title="Support Bot API", lifespan=lifespan)
    app.include_router(tickets.router)
    app.include_router(users.router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
