from sqlalchemy.ext.asyncio import AsyncSession

from db.tables.users import User
from repositories.user_repository import UserRepository


class UserService:
    @staticmethod
    async def create(session: AsyncSession, tg_id: int) -> User:
        user = await UserRepository.create_user(session, tg_id)
        await session.commit()

        return user


    @staticmethod
    async def get_or_create(session: AsyncSession, tg_id: int) -> tuple[User, bool]:
        user = await UserRepository.get_by_tg_id(session, tg_id)

        if user:
            return user, False

        user = await UserRepository.create_user(session, tg_id)
        await session.commit()

        return user, True

    @staticmethod
    async def get_by_tg_id(session: AsyncSession, tg_id: int) -> User | None:
        return await UserRepository.get_by_tg_id(session, tg_id)