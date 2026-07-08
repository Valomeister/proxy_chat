import datetime
from typing import List

from sqlalchemy import Integer, BigInteger, String, Boolean, DateTime, Table, Column, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from db.base import Base
from db.tables.managers_workers import ManagerWorker
from db.tables.orders import Order

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC)
    )

    workers: Mapped[list["ManagerWorker"]] = relationship(
        foreign_keys="ManagerWorker.manager_id",
        back_populates="manager",
        cascade="all, delete-orphan",
    )

    orders_as_manager: Mapped[List["Order"]] = relationship(
        foreign_keys="Order.manager_id",
        back_populates="manager",
    )

    orders_as_worker: Mapped[List["Order"]] = relationship(
        foreign_keys="Order.worker_id",
        back_populates="worker",
    )

    orders_as_customer: Mapped[List["Order"]] = relationship(
        foreign_keys="Order.customer_id",
        back_populates="customer",
    )

    def __repr__(self):
        return f'User(id={self.id}, tg_id={self.tg_id})'
