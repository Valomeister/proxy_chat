from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from db.tables.managers_workers import ManagerWorker
from db.tables.users import User
from repositories.user_repository import UserRepository


class UserService:
    @staticmethod
    async def create(session: AsyncSession, tg_id: int, tg_chat_id: int, tg_username: str | None) -> User:
        user = await UserRepository.create_user(session, tg_id, tg_chat_id, tg_username)
        await session.commit()

        return user


    @staticmethod
    async def get_or_create(session: AsyncSession, tg_id: int, tg_chat_id: int) -> tuple[User, bool]:
        user = await UserRepository.get_by_tg_id(session, tg_id)

        if user:
            return user, False

        user = await UserRepository.create_user(session, tg_id, tg_chat_id)
        await session.commit()

        return user, True

    @staticmethod
    async def get_by_tg_id(session: AsyncSession, tg_id: int) -> User | None:
        return await UserRepository.get_by_tg_id(session, tg_id)

    @staticmethod
    async def get_chat_id(session: AsyncSession, tg_id: int) -> int | None:
        user = await UserRepository.get_by_tg_id(session, tg_id)

        if user is not None:
            return user.tg_chat_id

        return None

    @staticmethod
    async def get_usernames_by_tg_ids(
        session: AsyncSession,
        tg_ids: List[int | None]
    ) -> dict[int, str]:
        not_none_ids = [tg_id for tg_id in tg_ids if tg_id is not None]

        users = await UserRepository.get_by_tg_ids(session, not_none_ids)

        usernames = {
            user.tg_id: user.tg_username
            for user in users
        }

        return usernames