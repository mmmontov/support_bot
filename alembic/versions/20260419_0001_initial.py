"""initial schema

Revision ID: 20260419_0001
Revises:
Create Date: 2026-04-19

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260419_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("last_ticket_time", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"], unique=False)

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tickets_user_id"), "tickets", ["user_id"], unique=False)

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("sender", sa.String(length=16), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_messages_ticket_id"), "messages", ["ticket_id"], unique=False)

    op.create_table(
        "admin_messages_map",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("admin_message_id", sa.BigInteger(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("admin_message_id"),
    )
    op.create_index(
        op.f("ix_admin_messages_map_admin_message_id"),
        "admin_messages_map",
        ["admin_message_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_admin_messages_map_ticket_id"),
        "admin_messages_map",
        ["ticket_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_messages_map_ticket_id"), table_name="admin_messages_map")
    op.drop_index(op.f("ix_admin_messages_map_admin_message_id"), table_name="admin_messages_map")
    op.drop_table("admin_messages_map")
    op.drop_index(op.f("ix_messages_ticket_id"), table_name="messages")
    op.drop_table("messages")
    op.drop_index(op.f("ix_tickets_user_id"), table_name="tickets")
    op.drop_table("tickets")
    op.drop_index(op.f("ix_users_telegram_id"), table_name="users")
    op.drop_table("users")
