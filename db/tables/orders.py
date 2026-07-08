import datetime
import enum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.tables.messages import Message


class OrderStatus(str, enum.Enum):
    created = "created"
    completed = "completed"
    cancelled = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    worker_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    deadline: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    price: Mapped[Numeric] = mapped_column(Numeric(10, 2))
    paycheck: Mapped[float] = mapped_column(Numeric(10, 2))

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        default=OrderStatus.created,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
    )

    manager: Mapped["User"] = relationship(
        foreign_keys=[manager_id],
        back_populates="orders_as_manager",
    )

    worker: Mapped["User | None"] = relationship(
        foreign_keys=[worker_id],
        back_populates="orders_as_worker",
    )

    customer: Mapped["User | None"] = relationship(
        foreign_keys=[customer_id],
        back_populates="orders_as_customer",
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )