import asyncio
import datetime
import logging
import os
import sys
from decimal import Decimal
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, CallbackQuery, InlineKeyboardMarkup, \
    InlineKeyboardButton, WebAppInfo
from dotenv import load_dotenv

from api.internal_api_client import InternalApiClient
from bot_v2.display_functions import display_workers, display_worker_detail, display_orders, display_order_detail, \
    validate_deadline_message, validate_money_message, send_message_or_print
from bot_v2.keyboards import WEB_APP_LINK, MoneyCallback, \
    input_format_keyboard, OrderCallback, order_edit_keyboard, OrdersPageCallback, \
    orders_keyboard, order_edit_status_keyboard, menu_keyboard, MenuCallback
from bot_v2.utils import format_timedelta
from db.session import SessionLocal
from db.tables.orders import ORDER_STATUS_EMOJI, ORDER_STATUS_RU, OrderStatus
from db.tables.messages import MessageType
from services.chat_service import ChatService
from services.crypto_service import CryptoService
from services.manager_worker_service import ManagerWorkerService
from services.order_service import OrderService
from services.user_service import UserService

from bot_v2.bot import bot

from dotenv import load_dotenv


load_dotenv()

internal_api = InternalApiClient(os.getenv('INTERNAL_API_KEY'))


router = Router()






@router.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    async with SessionLocal() as session:
        tg_id = message.from_user.id
        tg_username = message.from_user.username
        tg_chat_id = message.chat.id

        user = await UserService.get_by_tg_id(session, tg_id)

        user_was_created = False
        link_was_activated = False

        if not user:
            await message.answer(
                "Добро пожаловать! Вы впервые активировали бота\n\n"
                "<b>Этот бот:</b>\n"
                "- Предоставляет чат между менеджером, клиентом и исполнителем.\n\n"
                "<b>Запрещено:</b>\n"
                "- Обмениваться контактными данными между клиентом и исполнителем заказа.\n\n"
                "Меню: /menu"
            )
            user = await UserService.create(session, tg_id, tg_chat_id, tg_username)
            user_was_created = True
        args = message.text.split(maxsplit=1)

        if len(args) > 1:
            payload = args[1]

            # customer_invitation
            if payload.startswith("cinv_"):
                # formaе: ...cinv_213 <=> cinv_<order_id>
                try:
                    order_id = int(payload.replace("cinv_", ""))
                except Exception:
                    await message.answer(
                        "Активированная вами реферальная ссылка не существует"
                    )
                    return

                order = await OrderService.get_by_id(session, order_id)

                if order is None:
                    await message.answer(
                        "Заказ, указанный в ссылке, не существует."
                    )
                    return
                if order.customer_tg_id is not None:
                    if order.customer_tg_id == tg_id:
                        error_msg = f"Вы уже активировали эту ссылку."
                    else:
                        error_msg = f"Ссылка, которую вы активировали, является одноразовой и уже была использована."
                    await message.answer(
                        error_msg
                    )

                else:
                    await OrderService.update(
                        session,
                        order_id=order_id,
                        customer_tg_id=tg_id,
                    )
                    
                    await internal_api.send_system_message(
                        order_id=order_id,
                        text="Клиент присоединился к чату"
                    )

                    # notify customer (current chat)
                    await message.answer(
                        f"Вы подтвердили заказ \n<b>#{order_id} {order.title}</b>\n\nТеперь вам доступен "
                        f"чат с исполнителем",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(
                                text='Открыть чат',
                                web_app=WebAppInfo(url=f"https://wdraft.online/#/chat/{order.id}")
                            )   
                        ]])
                    )

                    # Notify manager
                    manager_chat_id = await UserService.get_chat_id(session, order.manager_tg_id)
                    await send_message_or_print(
                        bot=bot,
                        chat_id=manager_chat_id,
                        text=f"Клиент "
                             f"@{tg_username if tg_username else '<неизвстный>'} "
                             f"активировал ссылку заказа \n<b>#{order_id} {order.title}</b>\n\n"
                             f"Теперь ему доступен чат.",
                        tg_id=order.manager_tg_id,
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(
                                text='Открыть чат',
                                web_app=WebAppInfo(url=f"https://wdraft.online/#/chat/{order.id}")
                            )   
                        ]])
                    )
                    

                    # Notify worker
                    if order.worker_tg_id:
                        worker_chat_id = await UserService.get_chat_id(session, order.worker_tg_id)
                        await send_message_or_print(
                            bot=bot,
                            chat_id=worker_chat_id,
                            text=f"Клиент заказа \n<b>#{order_id} {order.title}</b>\nзашел в чат.\n\n"
                                f"Теперь вы можете ему писать.",
                            tg_id=order.worker_tg_id,
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                                InlineKeyboardButton(
                                    text='Открыть чат',
                                    web_app=WebAppInfo(url=f"https://wdraft.online/#/chat/{order.id}")
                                )   
                            ]])
                        )
                    
                    link_was_activated = True


            # worker_invitation
            if payload.startswith("winv_"):
                # format: ...winv_213 <=> winv_<order_id>
                try:
                    order_id = int(payload.replace("winv_", ""))
                except Exception:
                    await message.answer(
                        "Активированная вами реферальная ссылка не существует"
                    )
                    return

                order = await OrderService.get_by_id(session, order_id)

                if order is None:
                    await message.answer(
                        "Заказ, указанный в ссылке, не существует."
                    )
                    return
                if order.worker_tg_id is not None:
                    if order.worker_tg_id == tg_id:
                        error_msg = f"Вы уже активировали эту ссылку."
                    else:
                        error_msg = f"Ссылка, которую вы активировали, является одноразовой и уже была использована."
                    await message.answer(
                        error_msg
                    )

                else:
                    await OrderService.update(
                        session,
                        order_id=order_id,
                        worker_tg_id=tg_id,
                    )

                    await internal_api.send_system_message(
                        order_id=order_id,
                        text="Исполнитель присоединился к чату"
                    )

                    # notify worker (current chat)
                    await message.answer(
                        f"Вы подтвердили заказ \n<b>#{order_id} {order.title}</b>\n\nТеперь вам доступен "
                        f"чат с клиентом",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(
                                text='Открыть чат',
                                web_app=WebAppInfo(url=f"https://wdraft.online/#/chat/{order.id}")
                            )   
                        ]])
                    )

                    # Notify manager
                    manager_chat_id = await UserService.get_chat_id(session, order.manager_tg_id)
                    await send_message_or_print(
                        bot=bot,
                        chat_id=manager_chat_id,
                        text=f"Исполнитель "
                             f"@{tg_username if tg_username else '<неизвстный>'} "
                             f"активировал ссылку заказа \n<b>#{order_id} {order.title}</b>\n\n"
                             f"Теперь ему доступен чат.",
                        tg_id=order.manager_tg_id,
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(
                                text='Открыть чат',
                                web_app=WebAppInfo(url=f"https://wdraft.online/#/chat/{order.id}")
                            )   
                        ]])
                    )

                    link_was_activated = True

        if not user_was_created and not link_was_activated:
            await message.answer(
                "Выберите действие",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=menu_keyboard())
            )
        print(user)


@router.callback_query(OrderCallback.filter(F.action == "back_to_menu"))
async def show_menu(
    callback: CallbackQuery,
    callback_data: MoneyCallback
):
    await callback.answer();
    
    await callback.message.edit_text(
        "Выберите действие",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=menu_keyboard())
    )



@router.message(Command('menu'))
async def show_menu(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Выберите действие",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=menu_keyboard())
    )
