import datetime
import enum
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.tables.messages import Message


class OrderStatus(str, enum.Enum):
    created = "created"
    completed = "completed"
    cancelled = "cancelled"


ORDER_STATUS_RU = {
    OrderStatus.created: "в процессе",
    OrderStatus.cancelled: "отменен",
    OrderStatus.completed: "завершен"
}

ORDER_STATUS_EMOJI = {
    OrderStatus.created: "🟡",
    OrderStatus.cancelled: "🔴",
    OrderStatus.completed: "🟢"
}


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    title: Mapped[str] = mapped_column(String)

    manager_tg_id: Mapped[int] = mapped_column(ForeignKey("users.tg_id"))
    worker_tg_id: Mapped[int | None] = mapped_column(ForeignKey("users.tg_id"), nullable=True)
    customer_tg_id: Mapped[int | None] = mapped_column(ForeignKey("users.tg_id"), nullable=True)

    deadline: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    paycheck: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        default=OrderStatus.created,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
    )

    manager: Mapped["User"] = relationship(
        foreign_keys=[manager_tg_id],
        back_populates="orders_as_manager",
    )

    worker: Mapped["User | None"] = relationship(
        foreign_keys=[worker_tg_id],
        back_populates="orders_as_worker",
    )

    customer: Mapped["User | None"] = relationship(
        foreign_keys=[customer_tg_id],
        back_populates="orders_as_customer",
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )

    invitations: Mapped[list["Invitation"]] = relationship(
        "Invitation",
        back_populates="order",
    )