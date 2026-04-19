"""In-memory mapping: Telegram user id -> open ticket id for follow-up messages."""

from __future__ import annotations

active_ticket_by_user: dict[int, int] = {}
