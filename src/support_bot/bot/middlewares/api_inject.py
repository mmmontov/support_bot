from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram.dispatcher.middlewares.base import BaseMiddleware

from support_bot.bot.api_client import SupportApiClient


class ApiInjectMiddleware(BaseMiddleware):
    def __init__(self, api: SupportApiClient) -> None:
        self.api = api

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        data["api"] = self.api
        return await handler(event, data)
