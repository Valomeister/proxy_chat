from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.tables.users import User


class UserRepository:
    @staticmethod
    async def create_user(session: AsyncSession, tg_id: int) -> User:
        new_user = User(tg_id=tg_id)
        session.add(new_user)
        await session.flush()

        return new_user

    @staticmethod
    async def get_by_tg_id(session: AsyncSession, tg_id: int) -> User | None:
        result = await session.execute(
            select(User)
            .where(User.tg_id == tg_id)
        )

        return result.scalar_one_or_none()
