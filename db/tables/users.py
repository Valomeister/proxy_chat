import datetime
from typing import List

from sqlalchemy import Integer, BigInteger, String, Boolean, DateTime, Table, Column, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from db.base import Base
from db.tables.managers_workers import ManagerWorker
from db.tables.orders import Order

class User(Base):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # id of the chat with tg bot
    tg_chat_id: Mapped[int] = mapped_column(BigInteger)

    tg_username: Mapped[str | None] = mapped_column(String)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC)
    )

    workers_links_as_manager: Mapped[list["ManagerWorker"]] = relationship(
        foreign_keys="ManagerWorker.manager_tg_id",
        back_populates="manager",
        cascade="all, delete-orphan",
    )

    workers_links_as_worker: Mapped[list["ManagerWorker"]] = relationship(
        foreign_keys="ManagerWorker.worker_tg_id",
        back_populates="worker",
    )

    orders_as_manager: Mapped[List["Order"]] = relationship(
        foreign_keys="Order.manager_tg_id",
        back_populates="manager",
    )

    orders_as_worker: Mapped[List["Order"]] = relationship(
        foreign_keys="Order.worker_tg_id",
        back_populates="worker",
    )

    orders_as_customer: Mapped[List["Order"]] = relationship(
        foreign_keys="Order.customer_tg_id",
        back_populates="customer",
    )

    def __repr__(self):
        return f'User(tg_id={self.tg_id})'
