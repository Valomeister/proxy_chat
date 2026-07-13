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


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    print('ignore')
    await callback.answer()


@router.message()
async def catch_any(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Выберите действие",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=menu_keyboard())
    )