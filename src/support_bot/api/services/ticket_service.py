from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from support_bot.db.models.admin_message_map import AdminMessageMap
from support_bot.db.models.message import Message, MessageSender
from support_bot.db.models.ticket import Ticket, TicketStatus
from support_bot.db.models.user import User

RATE_LIMIT = timedelta(minutes=5)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc_aware(dt: datetime | None) -> datetime | None:
    """SQLite often returns naive datetimes; normalize for comparison with UTC-aware times."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def get_user_by_telegram(session: AsyncSession, telegram_id: int) -> User | None:
    r = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return r.scalar_one_or_none()


async def get_all_users(session: AsyncSession) -> list[User]:
    r = await session.execute(select(User).order_by(User.id))
    return list(r.scalars().all())


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
) -> User:
    user = await get_user_by_telegram(session, telegram_id)
    if user:
        if username is not None and user.username != username:
            user.username = username
        return user
    user = User(telegram_id=telegram_id, username=username, last_ticket_time=None)
    session.add(user)
    await session.flush()
    return user


async def ensure_user(
    session: AsyncSession,
    *,
    telegram_id: int,
    username: str | None,
) -> User:
    """Создать пользователя или обновить username. Новая строка: last_ticket_time=None."""
    return await get_or_create_user(session, telegram_id, username)


async def create_ticket(
    session: AsyncSession,
    *,
    telegram_id: int,
    username: str | None,
    topic: str,
    first_message_text: str | None,
) -> tuple[int, int]:
    user = await get_or_create_user(session, telegram_id, username)
    now = _now()
    # last_ticket_time is None until the first successful ticket (ensure_user / start keeps it null)
    last = _as_utc_aware(user.last_ticket_time)
    if last is not None and (now - last) < RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Подождите перед отправкой нового запроса",
            headers={"X-Error-Code": "rate_limited"},
        )

    ticket = Ticket(
        user_id=user.id,
        topic=topic,
        status=TicketStatus.open,
        created_at=now,
    )
    session.add(ticket)
    await session.flush()

    msg = Message(
        ticket_id=ticket.id,
        sender=MessageSender.user,
        text=first_message_text,
        created_at=now,
    )
    session.add(msg)

    user.last_ticket_time = now
    await session.flush()
    return ticket.id, user.id


async def append_user_message(
    session: AsyncSession,
    *,
    ticket_id: int,
    telegram_id: int,
    text: str | None,
) -> None:
    user = await get_user_by_telegram(session, telegram_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    r = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = r.scalar_one_or_none()
    if not ticket or ticket.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if ticket.status == TicketStatus.closed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Тикет закрыт, создайте новый через /start",
            headers={"X-Error-Code": "ticket_closed"},
        )

    msg = Message(
        ticket_id=ticket.id,
        sender=MessageSender.user,
        text=text,
        created_at=_now(),
    )
    session.add(msg)


async def register_admin_message(
    session: AsyncSession,
    *,
    ticket_id: int,
    admin_message_id: int,
) -> None:
    r = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = r.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    m = AdminMessageMap(admin_message_id=admin_message_id, ticket_id=ticket_id)
    session.add(m)
    await session.flush()


async def record_admin_reply(
    session: AsyncSession,
    *,
    ticket_id: int,
    text: str | None,
) -> int:
    r = await session.execute(
        select(Ticket).where(Ticket.id == ticket_id),
    )
    ticket = r.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if ticket.status == TicketStatus.closed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticket is closed",
        )

    ur = await session.execute(select(User).where(User.id == ticket.user_id))
    owner = ur.scalar_one()

    msg = Message(
        ticket_id=ticket.id,
        sender=MessageSender.admin,
        text=text,
        created_at=_now(),
    )
    session.add(msg)
    await session.flush()
    return owner.telegram_id


async def close_ticket(
    session: AsyncSession,
    *,
    ticket_id: int,
) -> int:
    r = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = r.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    ticket.status = TicketStatus.closed
    ur = await session.execute(select(User).where(User.id == ticket.user_id))
    owner = ur.scalar_one()
    return owner.telegram_id


async def get_ticket_by_admin_message(
    session: AsyncSession,
    *,
    message_id: int,
) -> tuple[Ticket, User] | None:
    r = await session.execute(
        select(AdminMessageMap, Ticket, User)
        .join(Ticket, AdminMessageMap.ticket_id == Ticket.id)
        .join(User, Ticket.user_id == User.id)
        .where(AdminMessageMap.admin_message_id == message_id),
    )
    row = r.first()
    if not row:
        return None
    _map, ticket, user = row
    return ticket, user
