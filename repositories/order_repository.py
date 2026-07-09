import datetime
from decimal import Decimal
from typing import List

from sqlalchemy import Numeric, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from db.tables.orders import Order, OrderStatus


class OrderRepository:
    @staticmethod
    async def create_order(
            session: AsyncSession,
            title: str,
            manager_tg_id: int,
            worker_tg_id: int,
            price: Decimal,
            paycheck: Decimal,
            customer_tg_id: int | None = None,
            deadline: datetime.datetime | None = None,
            status: OrderStatus = OrderStatus.created,
    ) -> Order:
        new_order = Order(
            title=title,
            manager_tg_id=manager_tg_id,
            worker_tg_id=worker_tg_id,
            customer_tg_id=customer_tg_id,
            deadline=deadline,
            price=price,
            paycheck=paycheck,
            status=status,
        )
        session.add(new_order)
        await session.flush()

        return new_order

    @staticmethod
    async def get_by_id(session: AsyncSession, order_id: int) -> Order | None:
        result = await session.execute(
            select(Order)
            .where(Order.id == order_id)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user_tg_id(
            session: AsyncSession,
            manager_tg_id: int | None = None,
            worker_tg_id: int | None = None,
            customer_tg_id: int | None = None,
            any_tg_id: int | None = None
    ) -> List[Order]:
        """
        if any_tg_id is specified, then returns all the orders of the user, regardless of his role in those order
        otherwise, only the orders where he has specific roles are returned
        """
        filters = []
        if any_tg_id is None:
            if manager_tg_id:
                filters.append(Order.manager_tg_id == manager_tg_id)
            if worker_tg_id:
                filters.append(Order.worker_tg_id == worker_tg_id)
            if customer_tg_id:
                filters.append(Order.customer_tg_id == customer_tg_id)
        else:
            filters.append(or_(
                Order.manager_tg_id == any_tg_id,
                Order.worker_tg_id == any_tg_id,
                Order.customer_tg_id == any_tg_id,
            ))

        result = await session.scalars(
            select(Order)
            .where(*filters)
            .order_by(Order.created_at.desc())
        )

        return list(result.all())

    @staticmethod
    async def delete_by_id(
            session: AsyncSession,
            order_id: int
    ):
        order = await OrderRepository.get_by_id(session, order_id)
        if order:
            await session.delete(order)

        return order

