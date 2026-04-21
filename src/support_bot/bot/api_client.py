from __future__ import annotations

import logging
from typing import Any

import httpx

from support_bot.config import get_settings

logger = logging.getLogger(__name__)


class SupportApiClient:
    def __init__(self) -> None:
        s = get_settings()
        self._base = s.api_base_url.rstrip("/")
        self._headers = {"X-Bot-Token": s.api_secret}

    def _url(self, path: str) -> str:
        return f"{self._base}{path}"

    async def create_ticket(
        self,
        *,
        telegram_id: int,
        username: str | None,
        topic: str,
        first_message_text: str | None,
    ) -> dict[str, Any]:
        payload = {
            "telegram_id": telegram_id,
            "username": username,
            "topic": topic,
            "first_message_text": first_message_text,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                self._url("/tickets/create"),
                json=payload,
                headers=self._headers,
            )
        if r.status_code == 429:
            try:
                detail = r.json().get("detail", "rate limited")
            except Exception:
                detail = r.text or "rate limited"
            raise RateLimitedError(detail)
        r.raise_for_status()
        return r.json()

    async def append_user_message(
        self,
        *,
        ticket_id: int,
        telegram_id: int,
        text: str | None,
    ) -> None:
        '''Добавляет сообщение пользователя в тикет'''
        payload = {"telegram_id": telegram_id, "text": text}
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                self._url(f"/tickets/{ticket_id}/message"),
                json=payload,
                headers=self._headers,
            )
        if r.status_code == 400:
            try:
                detail = r.json().get("detail", "")
            except Exception:
                detail = r.text
            if "закрыт" in str(detail).lower() or "closed" in str(detail).lower():
                raise TicketClosedError(str(detail))
            raise ApiClientError(str(detail))
        if r.status_code == 204:
            return
        r.raise_for_status()

    async def close_ticket(self, ticket_id: int) -> dict[str, Any]:
        '''Закрывает тикет'''
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                self._url(f"/tickets/{ticket_id}/close"),
                headers=self._headers,
            )
        r.raise_for_status()
        return r.json()

    async def ticket_by_admin_message(self, message_id: int) -> dict[str, Any] | None:
        '''Получает информацию о тикете по ID административного сообщения'''
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                self._url(f"/tickets/by-admin-message/{message_id}"),
                headers=self._headers,
            )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    async def register_admin_message(self, ticket_id: int, admin_message_id: int) -> None:
        '''Регистрирует ID административного сообщения в тикете'''
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                self._url(f"/tickets/{ticket_id}/register-admin-message"),
                json={"admin_message_id": admin_message_id},
                headers=self._headers,
            )
        if r.status_code == 409:
            logger.debug("admin_message_id %s already registered", admin_message_id)
            return
        r.raise_for_status()

    async def record_admin_reply(
        self,
        ticket_id: int,
        text: str | None,
    ) -> dict[str, Any]:
        '''Записывает ответ администратора в тикет'''
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                self._url(f"/tickets/{ticket_id}/admin-reply"),
                json={"text": text},
                headers=self._headers,
            )
        r.raise_for_status()
        return r.json()

    async def ensure_user(self, *, telegram_id: int, username: str | None) -> dict[str, Any]:
        '''Гарантирует, что пользователь существует в базе данных'''
        payload = {"telegram_id": telegram_id, "username": username}
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                self._url("/users/ensure"),
                json=payload,
                headers=self._headers,
            )
        r.raise_for_status()
        return r.json()

    async def get_user(self, telegram_id: int) -> dict[str, Any] | None:
        '''Получает информацию о пользователе по ID'''
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                self._url(f"/users/{telegram_id}"),
                headers=self._headers,
            )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    async def get_all_active_tickets(self) -> list[dict[str, Any]]:
        '''Получает все активные тикеты'''
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                self._url("/tickets/all-active"),
                headers=self._headers,
            )
        r.raise_for_status()
        return r.json()

    async def close_all_active_tickets(self) -> None:
        '''Закрывает все активные тикеты'''
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                self._url("/tickets/close-all-active"),
                headers=self._headers,
            )
        r.raise_for_status()
        return r.json()
        
class RateLimitedError(Exception):
    pass


class TicketClosedError(Exception):
    pass


class ApiClientError(Exception):
    pass
