from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from support_bot.config import get_settings


def get_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=False,
    )


engine = get_engine()
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
