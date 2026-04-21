from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class CreateTicketBody(BaseModel):
    telegram_id: int
    username: str | None = None
    topic: str = Field(..., max_length=128)
    first_message_text: str | None = None


class CreateTicketResponse(BaseModel):
    ticket_id: int
    user_id: int


class UserMessageBody(BaseModel):
    telegram_id: int
    text: str | None = None


class RegisterAdminMessageBody(BaseModel):
    admin_message_id: int


class AdminReplyBody(BaseModel):
    text: str | None = None


class TicketLookupResponse(BaseModel):
    ticket_id: int
    user_id: int
    user_telegram_id: int
    status: str
    topic: str


class TicketNotifyResponse(BaseModel):
    ticket_id: int
    user_telegram_id: int


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None
