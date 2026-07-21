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

from bot_v2.bot import bot



router = Router()


class OrderCreationForm(StatesGroup):
    title = State()
    worker = State()
    deadline = State()
    price = State()
    paycheck = State()

class OrderEditForm(StatesGroup):
    title = State()
    deadline = State()
    price = State()
    paycheck = State()
    status = State()
    delete = State()


@router.callback_query(OrdersPageCallback.filter())
async def orders_page(
    callback: CallbackQuery,
    callback_data: OrdersPageCallback,
):
    async with SessionLocal() as session:
        tg_id = callback.from_user.id
        orders = await OrderService.get_by_user_tg_id(session, any_tg_id=tg_id)

    await callback.message.edit_reply_markup(
        reply_markup=orders_keyboard(
            orders,
            callback_data.page,
        )
    )

    await callback.answer()

@router.message(OrderCreationForm.title)
async def process_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(OrderCreationForm.price)

    async with SessionLocal() as session:
        all_links, active_links = await ManagerWorkerService.get_all_workers_links(
            session, manager_tg_id=message.from_user.id
        )

    await message.answer(
        "Введите стоимость заказа:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=input_format_keyboard(action='show', callback_class=MoneyCallback)
        )
    )
    

@router.message(OrderCreationForm.price)
async def process_price(message: types.Message, state: FSMContext):
    is_good, value = await validate_money_message(message)
    if not is_good:
        return

    await state.update_data(price=value)
    await state.set_state(OrderCreationForm.paycheck)

    await message.answer(
        "Введите оплату исполнителю заказа:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=input_format_keyboard(action='show', callback_class=MoneyCallback)
        )
    )


@router.message(OrderCreationForm.paycheck)
async def process_paycheck(message: types.Message, state: FSMContext):
    is_good, value = await validate_money_message(message)
    if not is_good:
        return
    
    data = await state.update_data(paycheck=value)
    await state.clear()

    async with SessionLocal() as session:
        order = await OrderService.create(
            session,
            title=data['title'],
            manager_tg_id=message.from_user.id,
            price=data['price'],
            paycheck=data['paycheck'],
        )

        usernames = await UserService.get_usernames_by_tg_ids(
            session, 
            tg_ids = [order.manager_tg_id, order.worker_tg_id, order.customer_tg_id]
        )

        await ChatService.create(
            session,
            order.id,
            sender_tg_id = 0,
            text = "Менеджер создал чат",
            type = MessageType.system
        )

    await message.answer(
        "Вы создали новый заказ"
    )

    await display_order_detail(message, order, message.from_user.id, usernames, in_place=False, back_dest='menu')

    await message.answer(
        f"Ссылка для добавления исполнителя в чат по заказу \n"
        f"<b>#{order.id} {order.title}</b>\n\n"
        f"t.me/transparent_chat_bot?start=winv_{order.id}"
    )
    await message.answer(
        f"Ссылка для добавления клиента в чат по заказу \n"
        f"<b>#{order.id} {order.title}</b>\n\n"
        f"t.me/transparent_chat_bot?start=cinv_{order.id}"
    )


@router.callback_query(MoneyCallback.filter(F.action == "show"))
async def show_money_formats(
        callback: CallbackQuery,
        callback_data: MoneyCallback
):
    await callback.answer()
    await callback.message.edit_text(
        f"{callback.message.text.split('\n')[0]}\n\n"
        f"Примеры допустимых форматов:\n"
        f"- 1000\n"
        f"- 49.50\n"
        f"- 99,99",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=input_format_keyboard(action='hide', callback_class=MoneyCallback)
        )
    )


@router.callback_query(MoneyCallback.filter(F.action == "hide"))
async def hide_money_formats(
        callback: CallbackQuery,
        callback_data: MoneyCallback
):
    await callback.answer()

    await callback.message.edit_text(
        callback.message.text.split('\n')[0],
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=input_format_keyboard(action='show', callback_class=MoneyCallback)
        )
    )

@router.callback_query(OrderCallback.filter(F.action == "back_to_detail"))
@router.callback_query(OrderCallback.filter(F.action.is_(None)))
async def order_selected(
    callback: CallbackQuery,
    callback_data: OrderCallback,
):
    await callback.answer()

    async with SessionLocal() as session:
        order = await OrderService.get_by_id(session, callback_data.order_id)
        usernames = await UserService.get_usernames_by_tg_ids(
            session, 
            tg_ids = [order.manager_tg_id, order.worker_tg_id, order.customer_tg_id]
        )

    await display_order_detail(callback.message, order, callback.from_user.id, usernames, in_place=True)


@router.callback_query(OrderCallback.filter(F.action == "edit"))
async def edit_worker(
        callback: CallbackQuery,
        callback_data: OrderCallback,
        state: FSMContext
):
    await callback.answer()

    await state.clear()

    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=order_edit_keyboard(callback_data.order_id))
    )


@router.callback_query(OrderCallback.filter(F.action == "edit_title"))
async def edit_order_title(
        callback: CallbackQuery,
        callback_data: OrderCallback,
        state: FSMContext
):
    await callback.answer()

    await state.clear()
    await state.set_state(OrderEditForm.title)
    await state.update_data(order_id=callback_data.order_id)

    await callback.message.answer("Введите новое имя заказа:")


@router.message(OrderEditForm.title)
async def process_title(
        message: types.Message,
        state: FSMContext
):
    data = await state.get_data()
    await state.clear()

    async with SessionLocal() as session:
        order = await OrderService.update(
            session,
            order_id=data['order_id'],
            title=message.text,
        )
        usernames = await UserService.get_usernames_by_tg_ids(
            session, 
            tg_ids = [order.manager_tg_id, order.worker_tg_id, order.customer_tg_id]
        )

    await display_order_detail(message, order, message.from_user.id, usernames, in_place=False)


@router.callback_query(OrderCallback.filter(F.action == "edit_price"))
async def edit_order_price(
        callback: CallbackQuery,
        callback_data: OrderCallback,
        state: FSMContext
):
    await callback.answer()

    await state.clear()
    await state.set_state(OrderEditForm.price)
    await state.update_data(order_id=callback_data.order_id)

    await callback.message.answer(
        "Введите новую цену:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=input_format_keyboard(action='show', callback_class=MoneyCallback)
        )
    )


@router.message(OrderEditForm.price)
async def process_price(
        message: types.Message,
        state: FSMContext
):
    data = await state.get_data()

    is_good, price = await validate_money_message(message)
    if not is_good:
        return

    async with SessionLocal() as session:
        order = await OrderService.update(
            session,
            order_id=data['order_id'],
            price=price,
        )
        usernames = await UserService.get_usernames_by_tg_ids(
            session, 
            tg_ids = [order.manager_tg_id, order.worker_tg_id, order.customer_tg_id]
        )

    await display_order_detail(message, order, message.from_user.id, usernames, in_place=False)



@router.callback_query(OrderCallback.filter(F.action == "edit_paycheck"))
async def edit_order_paycheck(
        callback: CallbackQuery,
        callback_data: OrderCallback,
        state: FSMContext
):
    await callback.answer()

    await state.clear()
    await state.set_state(OrderEditForm.paycheck)
    await state.update_data(order_id=callback_data.order_id)

    await callback.message.answer(
        "Введите новую оплату:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=input_format_keyboard(action='show', callback_class=MoneyCallback)
        )
    )


@router.message(OrderEditForm.paycheck)
async def process_paycheck(
        message: types.Message,
        state: FSMContext
):
    data = await state.get_data()

    is_good, paycheck = await validate_money_message(message)
    if not is_good:
        return

    async with SessionLocal() as session:
        order = await OrderService.update(
            session,
            order_id=data['order_id'],
            paycheck=paycheck,
        )
        usernames = await UserService.get_usernames_by_tg_ids(
            session, 
            tg_ids = [order.manager_tg_id, order.worker_tg_id, order.customer_tg_id]
        )

    await display_order_detail(message, order, message.from_user.id, usernames, in_place=False)


@router.callback_query(OrderCallback.filter(F.action == "delete"))
async def delete_order(
        callback: CallbackQuery,
        callback_data: OrderCallback,
        state: FSMContext,
):
    await state.set_state(OrderEditForm.delete)
    await state.update_data(order_id=callback_data.order_id)
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.message.answer(
        "Вы уверены, что хотите удалить заказ? Напишите \"Да\" для удаления"
    )
    await callback.answer()


@router.message(OrderEditForm.delete)
async def confirm_delete_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    async with SessionLocal() as session:
        order = await OrderService.get_by_id(session, data['order_id'])
        usernames = await UserService.get_usernames_by_tg_ids(
            session, 
            tg_ids = [order.manager_tg_id, order.worker_tg_id, order.customer_tg_id]
        )


    if message.text != 'Да':
        await message.answer(
            'Отмена удаления'
        )

        await display_order_detail(message, order, message.from_user.id, usernames, in_place=False)

        return

    tg_id = message.from_user.id
    async with SessionLocal() as session:
        order = await OrderService.delete_by_id(session, data['order_id'])
        orders = await OrderService.get_by_user_tg_id(session, any_tg_id=tg_id)

    await message.answer(
        f"Заказ #{order.id}\n"
        f"Название: {order.title}\n"
        f"Был удален",
    )

    await display_orders(message, orders, in_place=False)

@router.callback_query(OrderCallback.filter(F.action == "back_to_list"))
async def back_to_workers(
        callback: CallbackQuery,
        callback_data: OrderCallback
):
    await callback.answer()

    async with SessionLocal() as session:
        tg_id = callback.from_user.id
        orders = await OrderService.get_by_user_tg_id(session, any_tg_id=tg_id)

    await display_orders(callback.message, orders, in_place=True)


