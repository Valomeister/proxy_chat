import asyncio
import datetime
import logging
import os
import sys
from decimal import Decimal
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, CallbackQuery, InlineKeyboardMarkup, \
    InlineKeyboardButton
from dotenv import load_dotenv

from bot.display_functions import display_workers, display_worker_detail, display_orders, display_order_detail, \
    validate_deadline_message, validate_money_message
from bot.keyboards import workers_keyboard, WorkersPageCallback, WorkerCallback, worker_edit_keyboard, \
    DeadlineCallback, MoneyCallback, input_format_keyboard, OrderCallback, order_edit_keyboard, OrdersPageCallback, \
    orders_keyboard, order_edit_status_keyboard
from bot.utils import format_timedelta
from db.session import SessionLocal
from db.tables.orders import ORDER_STATUS_EMOJI, ORDER_STATUS_RU, OrderStatus
from services.manager_worker_service import ManagerWorkerService
from services.order_service import OrderService
from services.user_service import UserService

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')

dp = Dispatcher()


class LinkCreationForm(StatesGroup):
    name = State()
    username = State()


class LinkEditForm(StatesGroup):
    name = State()
    username = State()
    delete = State()

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



@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    async with SessionLocal() as session:
        tg_id = message.from_user.id
        tg_chat_id = message.chat.id

        user = await UserService.get_by_tg_id(session, tg_id)

        if not user:
            await message.answer(
                "Добро пожаловать!\n"
                "Вы впервые активировали бота Proxy Chat.\n\n"
            )
            await message.answer(
                "<b>Этот бот:</b>\n"
                "- Предоставляет чат между клиентом и исполнителем.\n\n"
                "<b>Запрещено:</b>\n"
                "- Обмениваться контактными данными с собеседниками.\n\n"
                "<b>Обратите внимание:</b>\n"
                "- Все ваши сообщения будут видны менеджеру заказа.\n"
            )
            user = await UserService.create(session, tg_id, tg_chat_id)
            await message.answer(
                f"Для вас был автоматически создан аккаунт. Он привязан "
                f"к вашему Telegram аккаунту, но ваши собеседники не смогут "
                f"узнать ваш @username"
            )

        args = message.text.split(maxsplit=1)

        if len(args) > 1:
            payload = args[1]

            if payload.startswith("mwid_"):
                mwid = int(payload.replace("mwid_", ""))

                link = await ManagerWorkerService.get_by_id(session, link_id=mwid)

                if link is None:
                    await message.answer(
                        f"Приглашение, указанное в ссылке, не сещуствет"
                    )

                if link.worker_tg_id is not None:
                    await message.answer(
                        f"Приглашение #{mwid} невалидно, оно уже было активировано"
                    )
                else:

                    await ManagerWorkerService.set_workers_link_worker(session, mwid, tg_id)

                    await message.answer(
                        f"Вы активировали приглашение #{mwid}. Теперь человек, отправивший "
                        f"вам это приглашение, может назначать вам заказы"
                    )

                    # Notify manager
                    manager_chat_id = await UserService.get_chat_id(session, link.manager_tg_id)
                    await bot.send_message(
                        chat_id=manager_chat_id,
                        text=f"Исполнитель {link.saved_name} ({link.tg_username}) активировал "
                             f"ваше приглашение #{mwid}. Теперь вы можете назначать ему заказы."
                    )

            elif payload.startswith("oid_"):
                order_id = int(payload.replace("oid_", ""))

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

                    # notify customer (current chat)
                    await message.answer(
                        f"Вы подтвердили заказ #{order_id}. Теперь вам доступен "
                        f"чат с исполнителем"
                    )

                    # Notify manager
                    manager_chat_id = await UserService.get_chat_id(session, order.manager_tg_id)
                    await bot.send_message(
                        chat_id=manager_chat_id,
                        text=f"Клиент активировал ссылку заказа #{order_id} \"{order.title}\"\n"
                             f"Теперь ему доступен чат."
                    )

                    # Notify worker
                    worker_chat_id = await UserService.get_chat_id(session, order.worker_tg_id)
                    await bot.send_message(
                        chat_id=worker_chat_id,
                        text=f"У вас новый заказ: #{order_id} \"{order.title}\"\n"
                             f"Вы можете написать клиенту."
                    )

        print(user)


@dp.message(Command('workers'))
async def handle_workers(message: types.Message, state: FSMContext):
    await state.clear()
    async with SessionLocal() as session:
        tg_id = message.from_user.id
        all_links, active_links = await ManagerWorkerService.get_all_workers_links(session, manager_tg_id=tg_id)

    await display_workers(message, active_links)


@dp.message(Command('add_worker'))
async def workers(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(LinkCreationForm.name)
    await message.answer(
        "Введите имя исполнителя: \n(Его будете видеть только вы)"
    )


@dp.message(Command('orders'))
async def handle_orders(message: types.Message, state: FSMContext):
    await state.clear()
    async with SessionLocal() as session:
        tg_id = message.from_user.id
        orders = await OrderService.get_by_user_tg_id(session, any_tg_id=tg_id)

    await display_orders(message, orders)


@dp.message(Command('add_order'))
async def add_order(message: types.Message, state: FSMContext):
    await state.clear()

    async with SessionLocal() as session:
        tg_id = message.from_user.id
        all_links, active_links = await ManagerWorkerService.get_all_workers_links(session, manager_tg_id=tg_id)

        if not active_links:
            await message.answer(
                "Для создания заказа необходимо добавить хотя бы одного исполнителя:\n"
                "/add_worker"
            )

    await state.set_state(OrderCreationForm.title)
    await message.answer(
        "Введите название заказа:"
    )


@dp.callback_query(WorkersPageCallback.filter())
async def workers_page(
    callback: CallbackQuery,
    callback_data: WorkersPageCallback,
):
    async with SessionLocal() as session:
        all_links, active_links = await ManagerWorkerService.get_all_workers_links(
            session, manager_tg_id=callback.from_user.id
        )

    await callback.message.edit_reply_markup(
        reply_markup=workers_keyboard(
            active_links,
            callback_data.page,
        )
    )

    await callback.answer()


@dp.callback_query(WorkerCallback.filter(F.action.is_(None)))
async def worker_selected(
    callback: CallbackQuery,
    callback_data: WorkerCallback,
):

    await callback.answer()

    await display_worker_detail(
        callback.message,
        callback_data.saved_name, callback_data.saved_username, callback_data.link_id,
        in_place=True
    )


@dp.callback_query(WorkerCallback.filter(F.action == "edit_name"))
async def edit_worker_name(
        callback: CallbackQuery,
        callback_data: WorkerCallback,
        state: FSMContext,
):
    await state.set_state(LinkEditForm.name)
    await state.set_data({'link_id': callback_data.link_id})
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.message.answer(
        "Введите новое имя исполнителя:"
    )
    await callback.answer()


@dp.message(LinkEditForm.name)
async def process_new_name(message: types.Message, state: FSMContext):
    data = await state.update_data(name=message.text)
    await state.clear()
    # await bot.delete_message(message.chat.id, message.message_id)

    async with SessionLocal() as session:
        link = await ManagerWorkerService.set_name(session, data['link_id'], data['name'])

    await display_worker_detail(
        message,
        link.saved_name, link.tg_username, link.id,
        in_place=False
    )


@dp.callback_query(WorkerCallback.filter(F.action == "edit_username"))
async def edit_worker_username(
        callback: CallbackQuery,
        callback_data: WorkerCallback,
        state: FSMContext,
):
    await state.set_state(LinkEditForm.username)
    await state.set_data({'link_id': callback_data.link_id})
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.message.answer(
        "Введите новый username исполнителя:"
    )
    await callback.answer()


@dp.message(LinkEditForm.username)
async def process_new_username(message: types.Message, state: FSMContext):
    data = await state.update_data(username=message.text)
    await state.clear()
    # await bot.delete_message(message.chat.id, message.message_id)

    async with SessionLocal() as session:
        link = await ManagerWorkerService.set_username(session, data['link_id'], data['username'])

    await display_worker_detail(
        message,
        link.saved_name, link.tg_username, link.id,
        in_place=False
    )


@dp.callback_query(WorkerCallback.filter(F.action == "delete"))
async def delete_worker(
        callback: CallbackQuery,
        callback_data: WorkerCallback,
        state: FSMContext,
):
    await state.set_state(LinkEditForm.delete)
    await state.set_data({'link_id': callback_data.link_id})
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.message.answer(
        "Вы уверены, что хотите удалить исполнителя? Напишите \"Да\" для удаления"
    )
    await callback.answer()


@dp.message(LinkEditForm.delete)
async def confirm_delete_worker(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    if message.text != 'Да':
        await message.answer(
            'Отмена удаления'
        )

        async with SessionLocal() as session:
            link = await ManagerWorkerService.get_by_id(session, int(data['link_id']))

        await display_worker_detail(
            message,
            link.saved_name, link.tg_username, link.id,
            in_place=False
        )

        return

    tg_id = message.from_user.id
    async with SessionLocal() as session:
        link = await ManagerWorkerService.delete_by_id(session, int(data['link_id']))
        all_links, active_links = await ManagerWorkerService.get_all_workers_links(session, manager_tg_id=tg_id)

    await message.answer(
        f"Исполнитель:\n"
        f"{link.saved_name} ({link.tg_username})\n"
        f"Был удален",
    )

    await display_workers(message, active_links)


@dp.callback_query(WorkerCallback.filter(F.action == "back"))
async def back_to_workers(
        callback: CallbackQuery,
        callback_data: WorkerCallback
):
    await callback.answer()

    async with SessionLocal() as session:
        tg_id = callback.from_user.id
        all_links, active_links = await ManagerWorkerService.get_all_workers_links(session, manager_tg_id=tg_id)

    await display_workers(callback.message, active_links, in_place=True)


@dp.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    print('ignore')
    await callback.answer()


@dp.message(LinkCreationForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(LinkCreationForm.username)
    await message.answer(
        "Введите @username исполнителя: \n(Его будете видеть только вы)"
    )


@dp.message(LinkCreationForm.username)
async def process_name(message: types.Message, state: FSMContext):
    data = await state.update_data(username=message.text)
    await state.clear()
    name, username = data['name'], data['username']


    async with SessionLocal() as session:
        new_link = await ManagerWorkerService.create_workers_link(
            session,
            manager_tg_id=message.from_user.id,
            saved_name=name,
            saved_username=username,
        )

    await message.answer(
        "Вы зарегистрировали нового исполнителя"
    )
    await message.answer(
        f"Имя: {new_link.saved_name}\n"
        f"username: {new_link.tg_username}"
    )
    await message.answer(
        f"Ссылка для приглашения исполнителя: \n"
        f"t.me/transparent_chat_bot?start=mwid_{new_link.id}"
    )


@dp.callback_query(OrdersPageCallback.filter())
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


@dp.message(OrderCreationForm.title)
async def process_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(OrderCreationForm.worker)

    async with SessionLocal() as session:
        all_links, active_links = await ManagerWorkerService.get_all_workers_links(
            session, manager_tg_id=message.from_user.id
        )

    await message.answer(
        "Выберите исполнителя:",
        reply_markup=workers_keyboard(
            active_links,
            page=0,
            source='/orders'
        )
    )


@dp.callback_query(WorkerCallback.filter(F.action == "assign_to_order"))
async def process_worker(
        callback: CallbackQuery,
        callback_data: WorkerCallback,
        state: FSMContext,
):
    await state.set_state(OrderCreationForm.deadline)
    await state.update_data(worker=callback_data.link_id)
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.message.answer(
        f"Выбран исполнитель {callback_data.saved_name} ({callback_data.saved_username})"
    )
    await callback.message.answer(
        f"Введите дедлайн заказа:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=input_format_keyboard(action='show', callback_class=DeadlineCallback)
        )
    )
    await callback.answer()


@dp.callback_query(DeadlineCallback.filter(F.action == "show"))
async def show_deadline_formats(
        callback: CallbackQuery,
        callback_data: DeadlineCallback
):
    await callback.answer()

    await callback.message.edit_text(
        f"Введите дедлайн заказа:\n\n"
        f"Примеры допустимых форматов:\n"
        f"- 24.07.2026 14:00\n\n"
        f"<i>Дедлайн указывается по московскому времени</i>\n",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=input_format_keyboard(action='hide', callback_class=DeadlineCallback)
        )
    )


@dp.callback_query(DeadlineCallback.filter(F.action == "hide"))
async def show_deadline_formats(
        callback: CallbackQuery,
        callback_data: DeadlineCallback
):
    await callback.answer()

    await callback.message.edit_text(
        f"Введите дедлайн заказа:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=input_format_keyboard(action='show', callback_class=DeadlineCallback)
        )
    )


@dp.message(OrderCreationForm.deadline)
async def process_deadline(message: types.Message, state: FSMContext):
    is_good, deadline_dt = await validate_deadline_message(message)
    if not is_good:
        return

    await state.set_state(OrderCreationForm.price)
    await state.update_data(deadline=deadline_dt)

    await message.answer(
        "Введите стоимость заказа:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=input_format_keyboard(action='show', callback_class=MoneyCallback)
        )
    )





@dp.message(OrderCreationForm.price)
async def process_price(message: types.Message, state: FSMContext):
    is_good, value = await validate_money_message(message)

    await state.update_data(price=value)
    await state.set_state(OrderCreationForm.paycheck)

    await message.answer(
        "Введите оплату исполнителю заказа:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=input_format_keyboard(action='show', callback_class=MoneyCallback)
        )
    )


@dp.message(OrderCreationForm.paycheck)
async def process_paycheck(message: types.Message, state: FSMContext):
    try:
        value = Decimal(message.text.strip().replace(",", "."))
    except Exception:
        await message.answer(
            "Не удалось интерпретировать оплату. "
            "Убедитесь, что формат ввода верный.\n"
        )
        return
    data = await state.update_data(paycheck=value)
    await state.clear()

    async with SessionLocal() as session:
        link = await ManagerWorkerService.get_by_id(session, data['worker'])
        order, _, _ = await OrderService.create(
            session,
            title=data['title'],
            manager_tg_id=message.from_user.id,
            worker_tg_id=link.worker_tg_id,
            price=data['price'],
            paycheck=data['paycheck'],
            deadline=data['deadline'],
        )

    await message.answer(
        "Вы создали новый заказ"
    )

    await display_order_detail(message, order, message.from_user.id, link, in_place=False, back_destination='manu')

    await message.answer(
        f"Ссылка для добавления клиента в чат: \n"
        f"t.me/transparent_chat_bot?start=oid_{order.id}"
    )


@dp.callback_query(MoneyCallback.filter(F.action == "show"))
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


@dp.callback_query(MoneyCallback.filter(F.action == "hide"))
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

@dp.callback_query(OrderCallback.filter(F.action == "back_to_detail"))
@dp.callback_query(OrderCallback.filter(F.action.is_(None)))
async def order_selected(
    callback: CallbackQuery,
    callback_data: OrderCallback,
):
    await callback.answer()

    async with SessionLocal() as session:
        order = await OrderService.get_by_id(session, callback_data.order_id)
        # if current user is manager
        if order.manager_tg_id == callback.from_user.id:
            _, active_links = await ManagerWorkerService.get_all_workers_links(
                session,
                manager_tg_id=callback.from_user.id,
                worker_tg_id=order.worker_tg_id
            )
            # in theory there might be multiple links for the same pair, if the manager will really want it to happen
            last_link = active_links[-1]
        else:
            last_link = None

    await display_order_detail(callback.message, order, callback.from_user.id, last_link, in_place=True)


@dp.callback_query(OrderCallback.filter(F.action == "edit"))
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


@dp.callback_query(OrderCallback.filter(F.action == "edit_title"))
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


@dp.message(OrderEditForm.title)
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
        # if current user is manager
        if order.manager_tg_id == message.from_user.id:
            _, active_links = await ManagerWorkerService.get_all_workers_links(
                session,
                manager_tg_id=message.from_user.id,
                worker_tg_id=order.worker_tg_id
            )
            # in theory there might be multiple links for the same pair, if the manager will really want it to happen
            last_link = active_links[-1]
        else:
            last_link = None

    await display_order_detail(message, order, message.from_user.id, last_link, in_place=False)


@dp.callback_query(OrderCallback.filter(F.action == "edit_deadline"))
async def edit_order_deadline(
        callback: CallbackQuery,
        callback_data: OrderCallback,
        state: FSMContext
):
    await callback.answer()

    await state.clear()
    await state.set_state(OrderEditForm.deadline)
    await state.update_data(order_id=callback_data.order_id)

    await callback.message.answer(
        "Введите новый дедлайн:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=input_format_keyboard(action='show', callback_class=DeadlineCallback)
        )
    )


@dp.message(OrderEditForm.deadline)
async def process_deadline(
        message: types.Message,
        state: FSMContext
):
    data = await state.get_data()

    is_good, deadline_dt = await validate_deadline_message(message)
    if not is_good:
        return

    async with SessionLocal() as session:
        order = await OrderService.update(
            session,
            order_id=data['order_id'],
            deadline=deadline_dt,
        )
        # if current user is manager
        if order.manager_tg_id == message.from_user.id:
            _, active_links = await ManagerWorkerService.get_all_workers_links(
                session,
                manager_tg_id=message.from_user.id,
                worker_tg_id=order.worker_tg_id
            )
            # in theory there might be multiple links for the same pair, if the manager will really want it to happen
            last_link = active_links[-1]
        else:
            last_link = None

    await display_order_detail(message, order, message.from_user.id, last_link, in_place=False)



@dp.callback_query(OrderCallback.filter(F.action == "edit_price"))
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


@dp.message(OrderEditForm.price)
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
        # if current user is manager
        if order.manager_tg_id == message.from_user.id:
            _, active_links = await ManagerWorkerService.get_all_workers_links(
                session,
                manager_tg_id=message.from_user.id,
                worker_tg_id=order.worker_tg_id
            )
            # in theory there might be multiple links for the same pair, if the manager will really want it to happen
            last_link = active_links[-1]
        else:
            last_link = None

    await display_order_detail(message, order, message.from_user.id, last_link, in_place=False)



@dp.callback_query(OrderCallback.filter(F.action == "edit_paycheck"))
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


@dp.message(OrderEditForm.paycheck)
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
        # if current user is manager
        if order.manager_tg_id == message.from_user.id:
            _, active_links = await ManagerWorkerService.get_all_workers_links(
                session,
                manager_tg_id=message.from_user.id,
                worker_tg_id=order.worker_tg_id
            )
            # in theory there might be multiple links for the same pair, if the manager will really want it to happen
            last_link = active_links[-1]
        else:
            last_link = None

    await display_order_detail(message, order, message.from_user.id, last_link, in_place=False)


@dp.callback_query(OrderCallback.filter(F.action == "edit_status"))
async def edit_order_paycheck(
        callback: CallbackQuery,
        callback_data: OrderCallback,
        state: FSMContext
):
    await callback.answer()

    await state.clear()
    await state.set_state(OrderEditForm.status)
    await state.update_data(order_id=callback_data.order_id)

    await callback.message.answer(
        "Выберите новый статус:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=order_edit_status_keyboard(callback_data.order_id)
        )
    )


@dp.callback_query(OrderCallback.filter(F.action == 'update_status_created'))
@dp.callback_query(OrderCallback.filter(F.action == 'update_status_cancelled'))
@dp.callback_query(OrderCallback.filter(F.action == 'update_status_completed'))
async def process_status(
        callback: CallbackQuery,
        callback_data: OrderCallback,
        state: FSMContext
):
    await callback.answer()

    data = await state.get_data()

    new_status = {
        'update_status_created': OrderStatus.created,
        'update_status_cancelled': OrderStatus.cancelled,
        'update_status_completed': OrderStatus.completed,
    }[callback_data.action]

    async with SessionLocal() as session:
        order = await OrderService.update(
            session,
            order_id=data['order_id'],
            status=new_status,
        )
        # if current user is manager
        if order.manager_tg_id == callback.from_user.id:
            _, active_links = await ManagerWorkerService.get_all_workers_links(
                session,
                manager_tg_id=callback.from_user.id,
                worker_tg_id=order.worker_tg_id
            )
            # in theory there might be multiple links for the same pair, if the manager will really want it to happen
            last_link = active_links[-1]
        else:
            last_link = None

    await display_order_detail(callback.message, order, callback.from_user.id, last_link, in_place=False)


@dp.callback_query(OrderCallback.filter(F.action == "delete"))
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


@dp.message(OrderEditForm.delete)
async def confirm_delete_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    async with SessionLocal() as session:
        order = await OrderService.get_by_id(session, data['order_id'])
        # if current user is manager
        if order.manager_tg_id == message.from_user.id:
            _, active_links = await ManagerWorkerService.get_all_workers_links(
                session,
                manager_tg_id=message.from_user.id,
                worker_tg_id=order.worker_tg_id
            )
            # in theory there might be multiple links for the same pair, if the manager will really want it to happen
            last_link = active_links[-1]
        else:
            last_link = None

    if message.text != 'Да':
        await message.answer(
            'Отмена удаления'
        )

        await display_order_detail(message, order, message.from_user.id, last_link, in_place=False)

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

@dp.callback_query(OrderCallback.filter(F.action == "back"))
async def back_to_workers(
        callback: CallbackQuery,
        callback_data: OrderCallback
):
    await callback.answer()

    async with SessionLocal() as session:
        tg_id = callback.from_user.id
        orders = await OrderService.get_by_user_tg_id(session, any_tg_id=tg_id)
        print(tg_id, orders)

    await display_orders(callback.message, orders, in_place=True)


async def main() -> None:
    global bot
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())