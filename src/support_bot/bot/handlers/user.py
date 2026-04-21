from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from support_bot.bot.handlers.admin import admin_chat

from support_bot.bot.api_client import (
    ApiClientError,
    RateLimitedError,
    SupportApiClient,
    TicketClosedError,
)
from support_bot.bot.keyboards import (
    start_keyboard,
    topic_display,
    topics_keyboard,
)
from support_bot.bot.states import SupportStates
from support_bot.bot.storage import active_ticket_by_user
from support_bot.config import get_settings

logger = logging.getLogger(__name__)

router = Router(name="user")


def _extract_text(message: Message) -> str | None:
    if message.text:
        return message.text
    if message.caption:
        return message.caption
    return None


async def _notify_admin(
    api: SupportApiClient,
    *,
    ticket_id: int,
    topic_title: str,
    from_user_id: int,
    username: str | None,
    body_text: str | None,
    source_message: Message | None,
    bot,
) -> None:
    settings = get_settings()
    uname = f"@{username}" if username else "нет username"
    header = (
        f"[TICKET #{ticket_id}]\n"
        f"Тема: {topic_title}\n"
        f"Пользователь: {uname} ({from_user_id})\n\n"
        f"Сообщение:\n{body_text or '(без текста)'}"
    )
    sent = await bot.send_message(settings.admin_chat_id, header)
    await api.register_admin_message(ticket_id, sent.message_id)
    if source_message and (
        source_message.photo or source_message.document or source_message.video
    ):
        copied = await bot.copy_message(
            chat_id=settings.admin_chat_id,
            from_chat_id=source_message.chat.id,
            message_id=source_message.message_id,
        )
        await api.register_admin_message(ticket_id, copied.message_id)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, api: SupportApiClient) -> None:
    await state.clear()
    if await admin_chat(message):
        return
    
    # если у пользователя есть активные тикеты, мы пишем, что у него уже есть тикет
    if active_ticket_by_user.get(message.from_user.id):
        await message.answer("У вас уже есть активный тикет. Пожалуйста, дождитесь ответа от поддержки.")
        return
    try:
        await api.ensure_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
    except Exception as e:
        logger.warning("ensure_user on /start failed: %s", e)
    text = (
        "Здравствуйте! Это бот поддержки.\n"
        "Опишите проблему — мы передадим её команде и ответим здесь в Telegram.\n\n"
        "Нажмите кнопку ниже, чтобы задать вопрос."
    )
    await message.answer(text, reply_markup=start_keyboard())


@router.callback_query(F.data == "ask_question")
async def on_ask_question(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("Выберите тему:", reply_markup=topics_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("topic:"))
async def on_topic(callback: CallbackQuery, state: FSMContext) -> None:
    topic_key = callback.data.split(":", 1)[1]
    await state.update_data(topic_key=topic_key)
    await state.set_state(SupportStates.waiting_question)
    if callback.message:
        await callback.message.answer(
            "Напишите ваш вопрос (можно приложить фото, видео или документ).",
        )
    await callback.answer()


@router.message(
    StateFilter(SupportStates.waiting_question),
    F.chat.type == "private",
)
async def on_first_question(message: Message, state: FSMContext, api: SupportApiClient) -> None:
    data = await state.get_data()
    topic_key = data.get("topic_key")
    if not topic_key:
        await state.clear()
        await message.answer("Сессия сброшена. Нажмите /start.")
        return

    topic_title = topic_display(topic_key)
    text = _extract_text(message)

    try:
        resp = await api.create_ticket(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            topic=topic_title,
            first_message_text=text,
        )
    except RateLimitedError:
        await message.answer("Подождите перед отправкой нового запроса")
        return
    except Exception as e:
        logger.exception("create_ticket failed: %s", e)
        await message.answer("Не удалось создать обращение. Попробуйте позже.")
        return

    ticket_id = int(resp["ticket_id"])
    active_ticket_by_user[message.from_user.id] = ticket_id
    await state.clear()

    try:
        await _notify_admin(
            api,
            ticket_id=ticket_id,
            topic_title=topic_title,
            from_user_id=message.from_user.id,
            username=message.from_user.username,
            body_text=text,
            source_message=message,
            bot=message.bot,
        )
    except Exception as e:
        logger.exception("notify_admin failed: %s", e)

    await message.answer("Ваш запрос принят. Ожидайте ответа поддержки.")


@router.message(F.chat.type == "private")
async def on_followup(message: Message, state: FSMContext, api: SupportApiClient) -> None:
    if await state.get_state():
        return

    if message.text and message.text.startswith("/"):
        return

    uid = message.from_user.id
    ticket_id = active_ticket_by_user.get(uid)
    if ticket_id is None:
        await message.answer("Нажмите /start, чтобы начать диалог с поддержкой.")
        return

    text = _extract_text(message)
    try:
        await api.append_user_message(
            ticket_id=ticket_id,
            telegram_id=uid,
            text=text,
        )
    except TicketClosedError:
        active_ticket_by_user.pop(uid, None)
        await message.answer("Тикет закрыт, создайте новый через /start")
        return
    except ApiClientError as e:
        await message.answer(str(e))
        return
    except Exception as e:
        logger.exception("append_user_message failed: %s", e)
        await message.answer("Ошибка отправки. Попробуйте позже.")
        return

    try:
        await _notify_admin(
            api,
            ticket_id=ticket_id,
            topic_title="(продолжение диалога)",
            from_user_id=uid,
            username=message.from_user.username,
            body_text=text,
            source_message=message,
            bot=message.bot,
        )
    except Exception as e:
        logger.exception("notify_admin followup failed: %s", e)
