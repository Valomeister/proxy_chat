import datetime
from decimal import Decimal
from typing import List

from sqlalchemy import Numeric
from sqlalchemy.ext.asyncio import AsyncSession

from db.tables.managers_workers import ManagerWorker
from db.tables.orders import OrderStatus
from db.tables.users import Order
from repositories.order_repository import OrderRepository


class OrderService:
    @staticmethod
    async def create(
            session: AsyncSession,
            title: str,
            manager_tg_id: int,
            price: Decimal,
            paycheck: Decimal,
            worker_tg_id: int | None = None,
            customer_tg_id: int | None = None,
            deadline: datetime.datetime | None = None,
            status: OrderStatus = OrderStatus.created,
    ) -> Order:
        new_order = await OrderRepository.create_order(
            session,
            title=title,
            manager_tg_id=manager_tg_id,
            worker_tg_id=worker_tg_id,
            customer_tg_id=customer_tg_id,
            deadline=deadline,
            price=price,
            paycheck=paycheck,
            status=status,
        )

        await session.commit()

        return new_order

    @staticmethod
    async def get_by_id(session: AsyncSession, order_id: int) -> Order | None:
        return await OrderRepository.get_by_id(session, order_id)

    @staticmethod
    async def get_by_user_tg_id(
            session: AsyncSession,
            manager_tg_id: int | None = None,
            worker_tg_id: int | None = None,
            customer_tg_id: int | None = None,
            any_tg_id: int | None = None,
    ) -> List[Order]:
        return await OrderRepository.get_by_user_tg_id(
            session, manager_tg_id, worker_tg_id, customer_tg_id, any_tg_id
        )

    @staticmethod
    async def set_customer_tg_id(session: AsyncSession, order_id: int, customer_tg_id: int) -> None:
        order = await OrderRepository.get_by_id(session, order_id)

        if order:
            order.customer_tg_id = customer_tg_id
            await session.commit()

    @staticmethod
    async def update(
            session: AsyncSession,
            order_id: int,
            **fields,
    ) -> Order | None:
        order = await OrderRepository.get_by_id(session, order_id)

        if not order:
            return None

        for field, value in fields.items():
            setattr(order, field, value)

        await session.commit()

        return order

    @staticmethod
    async def delete_by_id(
            session: AsyncSession,
            order_id: int
    ):
        order = await OrderRepository.delete_by_id(session, order_id)

        await session.commit()

        return order

