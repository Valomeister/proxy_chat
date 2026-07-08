from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.tables.managers_workers import ManagerWorker


class ManagerWorkerRepository:
    @staticmethod
    async def get_workers_links(
            session,
            manager_tg_id: int | None = None,
            worker_tg_id: int | None = None,
    ) -> list[ManagerWorker]:
        if manager_tg_id is None and worker_tg_id is None:
            raise ValueError('Must specify at least one of manager_tg_id, worker_tg_id')

        filters = []
        if manager_tg_id is not None:
            filters.append(ManagerWorker.manager_tg_id == manager_tg_id)
        if worker_tg_id is not None:
            filters.append(ManagerWorker.worker_tg_id == worker_tg_id)

        query = (
            select(ManagerWorker)
            .options(
                selectinload(ManagerWorker.manager),
                selectinload(ManagerWorker.worker),
            )
            .where(*filters)
        )

        result = await session.scalars(query)

        return list(result.all())

    @staticmethod
    async def get_by_id(
            session: AsyncSession,
            link_id: int,
    ) -> ManagerWorker | None:
        query = (
            select(ManagerWorker)
            .where(ManagerWorker.id == link_id)
        )

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @staticmethod
    async def delete_by_id(
            session: AsyncSession,
            link_id: int
    ):
        link = await ManagerWorkerRepository.get_by_id(session, link_id)
        if link:
            await session.delete(link)

        return link

    @staticmethod
    async def create_workers_link(
            session,
            manager_tg_id: int,
            saved_name: str,
            saved_username: str
    ) -> ManagerWorker:
        link = ManagerWorker(
            manager_tg_id=manager_tg_id,
            saved_name=saved_name,
            tg_username=saved_username
        )

        session.add(link)
        await session.flush()

        return link


    @staticmethod
    async def set_workers_link_worker(
            session,
            link_id: int,
            worker_tg_id: int
    ) -> None:
        result = await session.execute(
            select(ManagerWorker)
            .where(ManagerWorker.id == link_id)
        )

        link = result.scalar_one_or_none()

        if link:
            link.worker_tg_id = worker_tg_id
            await session.flush()
