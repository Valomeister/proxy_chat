from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from db.tables.invitations import Invitation, InvitationRole


class InvitationRepository:
    @staticmethod
    async def create_invitation(session: AsyncSession, order_id: int, role: InvitationRole, secret_key: str) -> Invitation:
        new_invitation = Invitation(order_id=order_id, role=role, secret_key=secret_key)
        session.add(new_invitation)
        await session.flush()

        return new_invitation

    @staticmethod
    async def get_by_id(session: AsyncSession, invitation_id: int) -> Invitation | None:
        result = await session.execute(
            select(Invitation)
            .where(Invitation.id == invitation_id)
        )

        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_id_with_order(session: AsyncSession, invitation_id: int) -> Invitation | None:
        result = await session.execute(
            select(Invitation)
            .options(joinedload(Invitation.order))
            .where(Invitation.id == invitation_id)
        )

        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_order_id(session: AsyncSession, order_id: int) -> List[Invitation]:
        result = await session.scalars(
            select(Invitation)
            .where(Invitation.order_id == order_id)
        )

        return list(result.all())
