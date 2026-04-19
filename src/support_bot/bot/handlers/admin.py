from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from support_bot.bot.api_client import SupportApiClient
from support_bot.bot.storage import active_ticket_by_user
from support_bot.config import get_settings

logger = logging.getLogger(__name__)

router = Router(name="admin")


class AdminChatFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        cid = get_settings().admin_chat_id
        if not cid:
            return False
        return message.chat.id == cid


admin_chat = AdminChatFilter()


def _extract_text(message: Message) -> str | None:
    if message.text:
        return message.text
    if message.caption:
        return message.caption
    return None


@router.message(admin_chat, Command("close"), F.reply_to_message)
async def cmd_close(message: Message, api: SupportApiClient) -> None:
    mid = message.reply_to_message.message_id
    info = await api.ticket_by_admin_message(mid)
    if not info:
        await message.reply("Не удалось найти тикет по этому сообщению.")
        return
    ticket_id = int(info["ticket_id"])
    user_tg = int(info["user_telegram_id"])
    try:
        await api.close_ticket(ticket_id)
    except Exception as e:
        logger.exception("close_ticket: %s", e)
        await message.reply("Ошибка при закрытии тикета.")
        return

    active_ticket_by_user.pop(user_tg, None)
    try:
        await message.bot.send_message(user_tg, "Ваш диалог закрыт")
    except Exception as e:
        logger.warning("notify user close: %s", e)
    await message.reply("Тикет закрыт.")


@router.message(admin_chat, F.reply_to_message)
async def admin_reply(message: Message, state: FSMContext, api: SupportApiClient) -> None:
    if await state.get_state():
        return
    if message.text and message.text.strip().startswith("/close"):
        return

    mid = message.reply_to_message.message_id
    info = await api.ticket_by_admin_message(mid)
    if not info:
        return

    ticket_id = int(info["ticket_id"])
    user_tg = int(info["user_telegram_id"])

    if info.get("status") == "closed":
        await message.reply("Тикет уже закрыт.")
        return

    try:
        if message.photo or message.document or message.video:
            await message.bot.copy_message(
                chat_id=user_tg,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
            )
            text_for_db = _extract_text(message) or "(вложение)"
            await api.record_admin_reply(ticket_id, text_for_db)
        else:
            text = _extract_text(message)
            if text is None:
                return
            await message.bot.send_message(user_tg, text)
            await api.record_admin_reply(ticket_id, text)
    except Exception as e:
        logger.exception("admin_reply: %s", e)
        await message.reply("Не удалось доставить сообщение пользователю.")
