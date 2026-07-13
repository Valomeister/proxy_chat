import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from db.tables.managers_workers import ManagerWorker
from db.tables.orders import Order
from db.tables.messages import Message, MessageType
from repositories.chat_repository import ChatRepository
from api.schemas.chat import ChatSchema
from api.schemas.message import MessageSchema
from services.crypto_service import CryptoService



class ChatService:
    @staticmethod
    async def get_user_chats(
        session: AsyncSession,
        tg_id: int,
    ) -> list[ChatSchema]:

        orders_chat_info = await ChatRepository.get_orders_chats(
            session,
            tg_id
        )

        chats = []

        for order, last_message in orders_chat_info:
            chats.append(
                ChatSchema(
                    id=str(order.id),
                    title=order.title,
                    last_message=CryptoService.decrypt(last_message)
                    if last_message
                    else None,
                    price=float(order.price)
                    if tg_id in (order.customer_tg_id, order.manager_tg_id) and order.price is not None
                    else None,
                    paycheck=float(order.paycheck)
                    if tg_id in (order.worker_tg_id, order.manager_tg_id) and order.paycheck is not None
                    else None,
                )
            )

        return chats


    @staticmethod
    async def get_order_messages(
        session: AsyncSession,
        order_id: int,
    ) -> list[MessageSchema]:
        
        order_messages = await ChatRepository.get_order_messages(session, order_id)

        messages = []

        for m in order_messages:
            messages.append(
                MessageSchema(
                    id=m.id,
                    sender_tg_id=m.sender_tg_id,
                    text=CryptoService.decrypt(m.text),
                    sent_at=m.sent_at,
                    read_at=m.read_at,
                    type=m.type,
                )
            )

        return messages
    
    @staticmethod
    async def create(
        session: AsyncSession,
        order_id: int,
        sender_tg_id: int,
        text: str,
        type: MessageType | None = None
    ) -> Message:
        
        message = Message(
            order_id=order_id,
            sender_tg_id=sender_tg_id,
            text=CryptoService.encrypt(text),
            type=type
        )

        session.add(message)
        await session.commit()
        await session.refresh(message)

        return message
    

    @staticmethod
    async def get_message_by_id(
        session: AsyncSession,
        message_id: int,
    ) -> Message:
        
        message = await ChatRepository.get_message_by_id(session, message_id)

        return message


    @staticmethod
    async def read_message(
        session: AsyncSession,
        message: Message,
    ) -> None:
        
        message.read_at = datetime.datetime.now(datetime.UTC)
        
        await session.commit()

