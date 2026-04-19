from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from support_bot.db.base import Base


class AdminMessageMap(Base):
    __tablename__ = "admin_messages_map"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    admin_message_id: Mapped[int] = mapped_column(BigInteger(), unique=True, index=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), index=True)

    ticket: Mapped["Ticket"] = relationship(back_populates="admin_message_maps")
