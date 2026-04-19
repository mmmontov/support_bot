from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from support_bot.bot.api_client import SupportApiClient
from support_bot.bot.handlers import admin, user
from support_bot.bot.middlewares.api_inject import ApiInjectMiddleware
from support_bot.config import get_settings, setup_logging

logger = logging.getLogger(__name__)


async def run_bot() -> None:
    setup_logging()
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not set")
    if not settings.admin_chat_id:
        logger.warning("ADMIN_CHAT_ID is not set — admin handlers will not match")

    bot = Bot(
        settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    api = SupportApiClient()
    dp.update.middleware(ApiInjectMiddleware(api))

    dp.include_router(user.router)
    dp.include_router(admin.router)

    logger.info("Starting bot polling…")
    await dp.start_polling(bot)


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
