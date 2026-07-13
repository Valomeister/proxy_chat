from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.tables.notification_channels import NotificationChannel


class NotificationRepository:
    @staticmethod
    async def create_channel(session: AsyncSession, order_id: int, recipient_tg_id: int) -> NotificationChannel:
        new_channgel = NotificationChannel(order_id=order_id, recipient_tg_id=recipient_tg_id)
        session.add(new_channgel)
        await session.flush()

        return new_channgel

    @staticmethod
    async def get_channel(session: AsyncSession, order_id: int, recipient_tg_id: int) -> NotificationChannel | None:
        result = await session.execute(
            select(NotificationChannel)
            .where(NotificationChannel.order_id == order_id, NotificationChannel.recipient_tg_id == recipient_tg_id)
        )

        return result.scalar_one_or_none()
    
    # @staticmethod
    # async def get_by_tg_ids(session: AsyncSession, tg_ids: List[int]) -> List[User]:
    #     result = await session.execute(
    #         select(User)
    #         .where(User.tg_id.in_(tg_ids))
    #     )

    #     return list(result.scalars().all())
