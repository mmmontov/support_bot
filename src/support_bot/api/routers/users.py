from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from support_bot.api.deps import DbSession, verify_bot_token
from support_bot.api.schemas.users import EnsureUserBody, UserResponse
from support_bot.api.services import ticket_service

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(verify_bot_token)],
)


@router.post("/ensure", response_model=UserResponse)
async def register_or_update_user(body: EnsureUserBody, session: DbSession) -> UserResponse:
    """Регистрация при /start: новый пользователь с last_ticket_time=null; существующий — только username."""
    user = await ticket_service.ensure_user(
        session,
        telegram_id=body.telegram_id,
        username=body.username,
    )
    return UserResponse.model_validate(user)


@router.get("/all", response_model=list[UserResponse])
async def list_users(session: DbSession) -> list[UserResponse]:
    """Список всех пользователей (по возрастанию `id`)."""
    users = await ticket_service.get_all_users(session)
    return [UserResponse.model_validate(u) for u in users]


@router.get("/{telegram_id}", response_model=UserResponse)
async def get_user(
    telegram_id: int,
    session: DbSession,
) -> UserResponse:
    user = await ticket_service.get_user_by_telegram(session, telegram_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)