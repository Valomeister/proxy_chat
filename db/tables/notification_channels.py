from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        primary_key=True,
    )

    recipient_tg_id: Mapped[int] = mapped_column(
        ForeignKey("users.tg_id"),
        primary_key=True,
    )

    is_pending: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )