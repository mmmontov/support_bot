from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class EnsureUserBody(BaseModel):
    telegram_id: int = Field(..., description="Telegram user id")
    username: str | None = Field(None, max_length=255)


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    last_ticket_time: datetime | None

    model_config = {"from_attributes": True}
