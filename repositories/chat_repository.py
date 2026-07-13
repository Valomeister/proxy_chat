from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.tables.managers_workers import ManagerWorker
from db.tables.orders import Order
from db.tables.messages import Message


class ChatRepository:
    @staticmethod
    async def get_orders_chats(
        session: AsyncSession,
        tg_id: int,
    ) -> list[tuple[Order, str | None]]:

        last_message = (
            select(Message.text)
            .where(Message.order_id == Order.id)
            .order_by(Message.sent_at.desc())
            .limit(1)
            .scalar_subquery()
        )

        result = await session.execute(
            select(
                Order,
                last_message.label("last_message")
            )
            .where(
                or_(
                    Order.manager_tg_id == tg_id,
                    Order.worker_tg_id == tg_id,
                    Order.customer_tg_id == tg_id,
                )
            )
            .order_by(Order.created_at.desc())
        )

        return [
            (row[0], row[1])
            for row in result.all()
        ]


    @staticmethod
    async def get_order_messages(
        session: AsyncSession,
        order_id: int,
    ) -> list[Message]:

        result = await session.execute (
            select(Message)
            .where(Message.order_id == order_id)
            .order_by(Message.sent_at)
        )

        return result.scalars().all()
    

    @staticmethod
    async def get_message_by_id(
        session: AsyncSession,
        message_id: int,
    ) -> Message:

        result = await session.execute (
            select(Message)
            .where(Message.id == message_id)
        )

        return result.scalar_one_or_none()

    
