from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies.db import get_db
from api.dependencies.auth import get_current_telegram_user
from api.schemas.order import OrderSchema
from api.schemas.message import MessageSchema, MessageCreate
from services.order_service import OrderService
from services.chat_service import ChatService



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


@app.get("/chat")
async def get_chat(
    order_id: int,
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

    if tg_id is None or tg_id not in (order.manager_tg_id, order.worker_tg_id, order.customer_tg_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this chat"
        )

    messages = await ChatService.get_order_messages(session, order_id)

    order = OrderSchema(
        id=order.id,
        title=order.title,
        price=order.price,
        paycheck=order.paycheck,
        manager_tg_id=order.manager_tg_id,
        worker_tg_id=order.worker_tg_id,
        customer_tg_id=order.customer_tg_id,
    )

    return {
        "order": order, 
        "messages": messages
    }


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
        text=data.text,
    )


    return MessageSchema.model_validate(message)