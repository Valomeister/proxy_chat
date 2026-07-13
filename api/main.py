import asyncio
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Header, WebSocketDisconnect, status, WebSocket, Query
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies.db import get_db
from api.dependencies.auth import get_current_telegram_user
from api.schemas.order import OrderSchema
from api.schemas.message import MessageSchema, MessageCreate
from services.crypto_service import CryptoService
from services.notification_service import NotificationService
from services.order_service import OrderService
from services.chat_service import ChatService
from api.websocket_manager import ws_manager
from db.tables.messages import MessageType


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/chats")
async def get_chats(
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_telegram_user)
    ):

    tg_id = user["id"]

    chats = await ChatService.get_user_chats(session, tg_id)

    return chats



@app.websocket("/chat/{order_id}/ws")
async def chat_ws(
    websocket: WebSocket,
    order_id: int,
    init_data: str = Query(...),
    session: AsyncSession = Depends(get_db),
):
    user = await get_current_telegram_user(authorization=f"tma {init_data}")

    tg_id = user["id"]

    order = await OrderService.get_by_id(session, order_id)

    if order is None:
        await websocket.close(code=1008)
        return

    if tg_id not in (order.manager_tg_id, order.worker_tg_id, order.customer_tg_id):
        await websocket.close(code=1008)
        return
    
    await ws_manager.connect(order_id, websocket)

    messages = await ChatService.get_order_messages(session, order_id)

    order_schema = OrderSchema(
        id=order.id,
        title=order.title,
        price=order.price,
        paycheck=order.paycheck,
        manager_tg_id=order.manager_tg_id,
        worker_tg_id=order.worker_tg_id,
        customer_tg_id=order.customer_tg_id,
    )

    await websocket.send_json({
        "type": "init",
        "order": order_schema.model_dump(mode="json"),
        "messages": [
            m.model_dump(mode="json")
            for m in messages
        ],
    })

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        ws_manager.disconnect(order_id, websocket)


@app.post("/chat/{order_id}/message")
async def send_message(
    order_id: int,
    data: MessageCreate,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_telegram_user)
):

    order = await OrderService.get_by_id(session, order_id)

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    tg_id = user["id"]

    if tg_id not in (
        order.manager_tg_id,
        order.worker_tg_id,
        order.customer_tg_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this chat"
        )

    message = await ChatService.create(
        session,
        order_id=order_id,
        sender_tg_id=tg_id,
        text=data.text
    )

    message_schema = MessageSchema.model_validate(message)
    message_schema.text = CryptoService.decrypt(message.text)

    await ws_manager.broadcast(
        order_id,
        {
            "type": "message",
            "message": message_schema.model_dump(mode="json"),
        },
    )

    recipients = set()
    if tg_id == order.manager_tg_id:
        recipients.update([order.customer_tg_id, order.worker_tg_id])
    if tg_id == order.worker_tg_id:
        recipients.update([order.customer_tg_id])
    if tg_id == order.customer_tg_id:
        recipients.update([order.worker_tg_id])


    await NotificationService.plan_notification_if_needed(session, order_id = order.id, recipients = list(recipients), message_id=message.id)

    return message_schema


@app.post("/chat/{order_id}/message/{message_id}/read")
async def read_message(
    order_id: int,
    message_id: int,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_telegram_user)
):
    tg_id = user["id"]

    order = await OrderService.get_by_id(session, order_id)

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    message = await ChatService.get_message_by_id(session, message_id)

    if message is None or message.order_id != order_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    if message.sender_tg_id == tg_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot mark your own message as read"
        )
    
    assert message.read_at is None


    if tg_id not in (
        order.manager_tg_id,
        order.worker_tg_id,
        order.customer_tg_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this chat"
        )

    await ChatService.read_message(session, message)

    await ws_manager.broadcast(
        order_id,
        {
            "type":"message_read",
            "message_id": message_id,
            "read_at": message.read_at.strftime('%Y-%m-%dT%H:%M:%SZ')
        },
    )

    await NotificationService.unset_pending(session, order_id=order.id, recipient_tg_id=tg_id)



# INTERNAL API

load_dotenv()

INTERNAL_KEY = os.getenv('INTERNAL_API_KEY')

@app.post("/internal/chat/{order_id}/message")
async def send_system_notification(
    order_id: int,
    data: MessageCreate,
    session: AsyncSession = Depends(get_db),
    x_internal_key: str = Header(),
):

    if x_internal_key != INTERNAL_KEY:
        raise HTTPException(
            status_code=403
        )

    order = await OrderService.get_by_id(session, order_id)

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    tg_id = 0

    message = await ChatService.create(
        session,
        order_id=order_id,
        sender_tg_id=tg_id,
        text=data.text,
        type=MessageType.system
    )

    message_schema = MessageSchema.model_validate(message)
    message_schema.text = CryptoService.decrypt(message.text)

    await ws_manager.broadcast(
        order_id,
        {
            "type": "message",
            "message": message_schema.model_dump(mode="json"),
        },
    )

    return message_schema