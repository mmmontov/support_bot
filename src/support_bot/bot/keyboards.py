from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

TOPIC_PAYMENT = "payment"
TOPIC_ACTIVATION = "activation"
TOPIC_SERVICE = "service"
TOPIC_OTHER = "other"

TOPIC_LABELS = {
    TOPIC_PAYMENT: "Оплата",
    TOPIC_ACTIVATION: "Активация ключа",
    TOPIC_SERVICE: "Проблемы с сервисом",
    TOPIC_OTHER: "Другое",
}


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Задать вопрос", callback_data="ask_question")],
        ],
    )


def topics_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=TOPIC_LABELS[TOPIC_PAYMENT],
                callback_data=f"topic:{TOPIC_PAYMENT}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=TOPIC_LABELS[TOPIC_ACTIVATION],
                callback_data=f"topic:{TOPIC_ACTIVATION}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=TOPIC_LABELS[TOPIC_SERVICE],
                callback_data=f"topic:{TOPIC_SERVICE}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=TOPIC_LABELS[TOPIC_OTHER],
                callback_data=f"topic:{TOPIC_OTHER}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def topic_display(topic_key: str) -> str:
    return TOPIC_LABELS.get(topic_key, topic_key)
