import datetime
import enum

from sqlalchemy import Enum, Integer, ForeignKey, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class InvitationRole(str, enum.Enum):
    worker = "worker"
    customer = "customer"


class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[InvitationRole] = mapped_column(
        Enum(InvitationRole),
        nullable=False,
    )

    secret_key: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="invitations",
    )
