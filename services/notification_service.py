import asyncio
import os
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from api.internal_api_client import InternalApiClient
from db.session import SessionLocal
from db.tables.notification_channels import NotificationChannel

from repositories.notification_repository import NotificationRepository
from services.chat_service import ChatService

from dotenv import load_dotenv

from services.order_service import OrderService
from services.user_service import UserService


load_dotenv()

internal_api = InternalApiClient(os.getenv('INTERNAL_API_KEY'))


class NotificationService:
    @staticmethod
    async def create(session: AsyncSession, order_id: int, recipient_tg_id: int) -> NotificationChannel:
        channel = await NotificationRepository.create_channel(session, order_id, recipient_tg_id)

        await session.commit()

        return channel


    @staticmethod
    async def get_or_create(session: AsyncSession, order_id: int, recipient_tg_id: int) -> NotificationChannel:
        channel = await NotificationRepository.get_channel(session, order_id, recipient_tg_id)

        if channel:
            return channel, False

        channel = await NotificationRepository.create_channel(session, order_id, recipient_tg_id)
        await session.commit()

        return channel, True
    
    @staticmethod
    async def plan_notification_if_needed(session: AsyncSession, order_id: int, recipients: List[int], message_id: int) -> None:
        """
        message_id - the first unread message, the state is tied to it
        """
        for recipient_tg_id in recipients:
            channel, _ = await NotificationService.get_or_create(session, order_id, recipient_tg_id)

            if not channel.is_pending:
                channel.is_pending = True
                await session.commit()
                asyncio.create_task(
                    NotificationService.send_notification_if_needed(order_id, recipient_tg_id, message_id)
                )

    
    @staticmethod
    async def send_notification_if_needed(order_id: int, recipient_tg_id: int, message_id: int) -> None:
        await asyncio.sleep(5)
        async with SessionLocal() as session:
            channel, _ = await NotificationService.get_or_create(session, order_id, recipient_tg_id)

            if channel.is_pending:
                message = await ChatService.get_message_by_id(session, message_id)

                if message.read_at is None:
                    order = await OrderService.get_by_id(session, order_id)
                    user = await UserService.get_by_tg_id(session, recipient_tg_id)

                    await internal_api.send_bot_notification(
                        tg_chat_id=user.tg_chat_id, 
                        text=f"🔔 У вас есть новые сообщения по заказу:\n<b>#{order.id} \"{order.title}\"</b>",
                        order_id=order.id
                        )
                
    @staticmethod
    async def unset_pending(session: AsyncSession, order_id: int, recipient_tg_id: int) -> None:
        channel = await NotificationRepository.get_channel(session, order_id, recipient_tg_id)

        if not channel:
            return
        
        channel.is_pending = False
        await session.commit()


    # @staticmethod
    # async def get_by_tg_id(session: AsyncSession, tg_id: int) -> User | None:
    #     return await UserRepository.get_by_tg_id(session, tg_id)

    # @staticmethod
    # async def get_chat_id(session: AsyncSession, tg_id: int) -> int | None:
    #     user = await UserRepository.get_by_tg_id(session, tg_id)

    #     if user is not None:
    #         return user.tg_chat_id

    #     return None

    # @staticmethod
    # async def get_usernames_by_tg_ids(
    #     session: AsyncSession,
    #     tg_ids: List[int | None]
    # ) -> dict[int, str]:
    #     not_none_ids = [tg_id for tg_id in tg_ids if tg_id is not None]

    #     users = await UserRepository.get_by_tg_ids(session, not_none_ids)

    #     usernames = {
    #         user.tg_id: user.tg_username
    #         for user in users
    #     }

    #     return usernames