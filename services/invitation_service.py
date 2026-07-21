from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from db.tables.invitations import Invitation, InvitationRole
from repositories.invitation_repository import InvitationRepository

import secrets


class InvitationService:
    @staticmethod
    async def create(session: AsyncSession, order_id: int, role: InvitationRole) -> Invitation:
        secret_key = secrets.token_hex(3)
        invitation = await InvitationRepository.create_invitation(session, order_id, role, secret_key)
        await session.commit()

        return invitation

    @staticmethod
    async def get_by_id(session: AsyncSession, invitation_id: int) -> Invitation | None:
        return await InvitationRepository.get_by_id(session, invitation_id)

    @staticmethod
    async def get_by_id_with_order(session: AsyncSession, invitation_id: int) -> Invitation | None:
        return await InvitationRepository.get_by_id_with_order(session, invitation_id)
    
    @staticmethod
    async def get_by_order_id(session: AsyncSession, order_id: int) -> List[Invitation]:
        return await InvitationRepository.get_by_order_id(session, order_id)