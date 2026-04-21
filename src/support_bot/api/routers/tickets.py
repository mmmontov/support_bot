from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from support_bot.api.deps import DbSession, verify_bot_token
from support_bot.api.schemas.tickets import (
    AdminReplyBody,
    CreateTicketBody,
    CreateTicketResponse,
    RegisterAdminMessageBody,
    TicketLookupResponse,
    TicketNotifyResponse,
    UserMessageBody,
)
from support_bot.api.services import ticket_service

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
    dependencies=[Depends(verify_bot_token)],
)


@router.get("/all-active", response_model=list[TicketLookupResponse])
async def get_all_active_tickets(session: DbSession) -> list[TicketLookupResponse]:
    tickets = await ticket_service.get_all_active_tickets(session)
    
    return [TicketLookupResponse(
        ticket_id=t.id,
        user_id=t.user_id,
        user_telegram_id=t.user.telegram_id,
        status=t.status,
        topic=t.topic,
    ) for t in tickets]



@router.post("/close-all-active") 
async def close_all_active_tickets(session: DbSession) -> list[TicketLookupResponse]:
    tickets = await ticket_service.get_all_active_tickets(session)
    await ticket_service.close_all_active_tickets(session)
    return [TicketLookupResponse(
        ticket_id=t.id,
        user_id=t.user_id,
        user_telegram_id=t.user.telegram_id,
        status=t.status,
        topic=t.topic,
    ) for t in tickets]


@router.post("/create", response_model=CreateTicketResponse)
async def create_ticket(
    body: CreateTicketBody,
    session: DbSession,
) -> CreateTicketResponse:
    ticket_id, user_id = await ticket_service.create_ticket(
        session,
        telegram_id=body.telegram_id,
        username=body.username,
        topic=body.topic,
        first_message_text=body.first_message_text,
    )
    return CreateTicketResponse(ticket_id=ticket_id, user_id=user_id)


@router.post("/{ticket_id}/message", status_code=status.HTTP_204_NO_CONTENT)
async def append_user_message(
    ticket_id: int,
    body: UserMessageBody,
    session: DbSession,
) -> None:
    await ticket_service.append_user_message(
        session,
        ticket_id=ticket_id,
        telegram_id=body.telegram_id,
        text=body.text,
    )


@router.post("/{ticket_id}/close", response_model=TicketNotifyResponse)
async def close_ticket(
    ticket_id: int,
    session: DbSession,
) -> TicketNotifyResponse:
    user_telegram_id = await ticket_service.close_ticket(session, ticket_id=ticket_id)
    return TicketNotifyResponse(ticket_id=ticket_id, user_telegram_id=user_telegram_id)


@router.get("/by-admin-message/{message_id}", response_model=TicketLookupResponse)
async def ticket_by_admin_message(
    message_id: int,
    session: DbSession,
) -> TicketLookupResponse:
    row = await ticket_service.get_ticket_by_admin_message(session, message_id=message_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    ticket, user = row
    return TicketLookupResponse(
        ticket_id=ticket.id,
        user_id=user.id,
        user_telegram_id=user.telegram_id,
        status=ticket.status,
        topic=ticket.topic,
    )


@router.post("/{ticket_id}/register-admin-message", status_code=status.HTTP_204_NO_CONTENT)
async def register_admin_message(
    ticket_id: int,
    body: RegisterAdminMessageBody,
    session: DbSession,
) -> None:
    try:
        await ticket_service.register_admin_message(
            session,
            ticket_id=ticket_id,
            admin_message_id=body.admin_message_id,
        )
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="admin_message_id already mapped",
        ) from e


@router.post("/{ticket_id}/admin-reply", response_model=TicketNotifyResponse)
async def admin_reply(
    ticket_id: int,
    body: AdminReplyBody,
    session: DbSession,
) -> TicketNotifyResponse:
    """Record an admin message in DB; bot sends the Telegram message to the user."""
    user_telegram_id = await ticket_service.record_admin_reply(
        session,
        ticket_id=ticket_id,
        text=body.text,
    )
    return TicketNotifyResponse(ticket_id=ticket_id, user_telegram_id=user_telegram_id)
