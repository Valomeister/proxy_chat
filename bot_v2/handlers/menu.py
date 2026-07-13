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
    InlineKeyboardButton
from dotenv import load_dotenv

from bot_v2.display_functions import display_workers, display_worker_detail, display_orders, display_order_detail, \
    validate_deadline_message, validate_money_message
from bot_v2.handlers.order import OrderCreationForm
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



router = Router()


@router.callback_query(MenuCallback.filter(F.action.is_(None)))
async def handle_orders(
    callback: CallbackQuery,
    callback_data: OrderCallback,
    state: FSMContext
):
    await callback.answer()
    await state.clear()

    await callback.message.edit_text(
        "Выберите действие",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=menu_keyboard())
    )



@router.callback_query(MenuCallback.filter(F.action == "orders"))
async def handle_orders(
    callback: CallbackQuery,
    callback_data: OrderCallback,
    state: FSMContext
):
    await callback.answer()
    await state.clear()
    async with SessionLocal() as session:
        tg_id = callback.from_user.id
        orders = await OrderService.get_by_user_tg_id(session, any_tg_id=tg_id)

    await display_orders(callback.message, orders, in_place=True)


@router.callback_query(MenuCallback.filter(F.action == "create_order"))
async def handle_orders(
    callback: CallbackQuery,
    callback_data: OrderCallback, 
    state: FSMContext
):
    await callback.answer()
    await state.clear()
    await state.set_state(OrderCreationForm.title)
    await callback.message.answer(
        "Введите название заказа:"
    )


@router.callback_query(MenuCallback.filter(F.action == "help"))
async def handle_orders(
    callback: CallbackQuery,
    callback_data: OrderCallback, 
    state: FSMContext
):
    await callback.answer()
    await state.clear()
    
    await callback.message.edit_text(
        text = (
            f"<b>📌 Основная информация</b>\n\n"

            f"Этот бот предоставляет общий чат для общения между "
            f"<b>менеджером</b>, <b>клиентом</b> и <b>исполнителем</b>.\n\n"

            f"<b>🚫 Запрещено</b>\n\n"

            f"• Передавать или запрашивать контактные данные между "
            f"клиентом и исполнителем.\n"
            f"• Обсуждать способы связи вне чата.\n\n"

            f"<b>💬 Создание чата</b>\n\n"

            f"Для каждого заказа автоматически создается отдельный чат.\n\n"

            f"Чтобы чат появился, сначала необходимо создать заказ. "
            f"После этого станут доступны персональные реферальные "
            f"ссылки для приглашения остальных участников "
            f"(клиента и исполнителя). Перейдя по своей ссылке, "
            f"участник автоматически присоединится к чату "
            f"соответствующего заказа.\n\n"

            f"<b>🔔 Уведомления</b>\n\n"

            f"Если в чате появятся новые непрочитанные сообщения, "
            f"бот может отправить вам уведомление, чтобы вы не "
            f"пропустили важную информацию.\n\n"

            f"<b>🔒 Конфиденциальность</b>\n\n"

            f"Чат доступен только участникам соответствующего заказа. "
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="Назад",
                callback_data=MenuCallback().pack()
            )
        ]])
    )
