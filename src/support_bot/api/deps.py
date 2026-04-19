from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from support_bot.config import get_settings
from support_bot.db.session import async_session_maker


async def get_db() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def verify_bot_token(
    x_bot_token: Annotated[str | None, Header(alias="X-Bot-Token")] = None,
) -> None:
    settings = get_settings()
    if not x_bot_token or x_bot_token != settings.api_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Bot-Token",
        )


DbSession = Annotated[AsyncSession, Depends(get_db)]
BotAuth = Annotated[None, Depends(verify_bot_token)]
