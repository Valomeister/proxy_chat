from argparse import ArgumentError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.tables.managers_workers import ManagerWorker
from repositories.manager_worker_repository import ManagerWorkerRepository


class ManagerWorkerService:
    @staticmethod
    async def get_all_workers_links(
            session,
            manager_tg_id: int | None = None,
            worker_tg_id: int | None = None,
    ) -> tuple[list[ManagerWorker], list[ManagerWorker]]:
        all_links = await ManagerWorkerRepository.get_workers_links(session, manager_tg_id, worker_tg_id)

        active_links = [
            link
            for link in all_links
            if link.worker_tg_id is not None
        ]

        return all_links, active_links

    @staticmethod
    async def create_workers_link(
            session,
            manager_tg_id: int,
            saved_name: str,
            saved_username: str
    ) -> ManagerWorker:

        new_worker = await ManagerWorkerRepository.create_workers_link(
            session, manager_tg_id, saved_name, saved_username
        )

        await session.commit()

        return new_worker

    @staticmethod
    async def set_workers_link_worker(
            session,
            link_id: int,
            worker_tg_id: int
    ) -> None:

        await ManagerWorkerRepository.set_workers_link_worker(session, link_id, worker_tg_id)

        await session.commit()

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        link_id: int
    ):
        return await ManagerWorkerRepository.get_by_id(session, link_id)

    @staticmethod
    async def delete_by_id(
            session: AsyncSession,
            link_id: int
    ):
        link = await ManagerWorkerRepository.delete_by_id(session, link_id)

        await session.commit()

        return link

    @staticmethod
    async def set_name(
            session: AsyncSession,
            link_id: int,
            new_name: str
    ):
        link = await ManagerWorkerRepository.get_by_id(session, link_id)
        link.saved_name = new_name
        await session.commit()

        return link

    @staticmethod
    async def set_username(
            session: AsyncSession,
            link_id: int,
            new_username: str
    ):
        link = await ManagerWorkerRepository.get_by_id(session, link_id)
        link.tg_username = new_username
        await session.commit()

        return link
