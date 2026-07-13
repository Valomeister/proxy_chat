import os

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from api.schemas.notification import Notification
from bot_v2.bot import bot

import uvicorn

from bot_v2.display_functions import send_message_or_print
from bot_v2.keyboards import WEB_APP_LINK


load_dotenv()

INTERNAL_KEY = os.getenv('INTERNAL_API_KEY')


app = FastAPI()


@app.post("/api/internal/bot_chat/{tg_chat_id}/message")
async def send_notification(
    tg_chat_id: int,
    data: Notification,
    x_internal_key: str = Header(),
):
    print("bot_api.send_notification()")

    if x_internal_key != INTERNAL_KEY:
        raise HTTPException(
            status_code=403
        )

    await send_message_or_print(
        bot=bot,
        chat_id=tg_chat_id,
        text=data.text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text='Открыть чат',
                web_app=WebAppInfo(url=f"https://wdraft.online/#/chat/{data.order_id}")
            )   
        ]])
    )

    return {
        "ok": True
    }


@app.get("/api")
async def root():
    return {
        "ok": True
    }


async def start_api():

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8081,
        log_level="info",
    )

    server = uvicorn.Server(config)

    await server.serve()