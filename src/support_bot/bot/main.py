from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat

from support_bot.bot.api_client import SupportApiClient
from support_bot.bot.handlers import admin, user
from support_bot.bot.middlewares.api_inject import ApiInjectMiddleware
from support_bot.config import get_settings, setup_logging

logger = logging.getLogger(__name__)

_USER_COMMANDS = [
    BotCommand(command="start", description="Начать работу с ботом"),
]

_ADMIN_COMMANDS = [
    BotCommand(command="tickets", description="Показать все активные тикеты"),
    BotCommand(command="close", description="Закрыть тикет (ответом на сообщение)"),
    BotCommand(command="close_all", description="Закрыть все активные тикеты"),
]


async def _setup_commands(bot: Bot, admin_chat_id: int) -> None:
    await bot.set_my_commands(_USER_COMMANDS, scope=BotCommandScopeAllPrivateChats())
    if admin_chat_id:
        await bot.set_my_commands(_ADMIN_COMMANDS, scope=BotCommandScopeChat(chat_id=admin_chat_id))
        logger.info("Admin commands set for chat %d", admin_chat_id)


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

    await _setup_commands(bot, settings.admin_chat_id)

    logger.info("Starting bot polling…")
    await dp.start_polling(bot)


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
