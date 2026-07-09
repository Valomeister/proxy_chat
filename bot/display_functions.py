import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from aiogram import types
from aiogram.types import InlineKeyboardMarkup

from bot.keyboards import workers_keyboard, worker_edit_keyboard, orders_keyboard, order_edit_keyboard, \
    order_detail_keyboard
from bot.utils import format_timedelta
from db.tables.orders import OrderStatus, ORDER_STATUS_RU, ORDER_STATUS_EMOJI, Order
from services.manager_worker_service import ManagerWorkerService
from services.user_service import UserService



async def display_workers(message, active_links, in_place=False):
    if len(active_links) == 0:
        word1_form = 'нет'
    else:
        word1_form = len(active_links)

    if len(active_links) % 10 == 0 or len(active_links) % 10 >= 5:
        word2_form = 'исполнителей'
    elif len(active_links) % 10 == 1:
        word2_form = 'исполнитель'
    else:
        word2_form = 'исполнителя'

    display_func = message.edit_text if in_place else message.answer

    await display_func(
        text=f'У вас есть {word1_form} {word2_form}',
        reply_markup=workers_keyboard(active_links, page=0),
    )


async def display_worker_detail(message, name, username, link_id, in_place=False):
    display_func = message.edit_text if in_place else message.answer
    await display_func(
        f"Исполнитель:\n"
        f"{name} ({username})\n"
        f"<i>(имя и username видны только вам)</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=worker_edit_keyboard(link_id))
    )


async def display_orders(message, orders, in_place=False, page=0):
    if len(orders) == 0:
        word1_form = 'нет'
    else:
        word1_form = len(orders)

    if len(orders) % 10 == 0 or len(orders) % 10 >= 5:
        word2_form = 'заказов'
    elif len(orders) % 10 == 1:
        word2_form = 'заказ'
    else:
        word2_form = 'заказа'

    display_func = message.edit_text if in_place else message.answer

    await display_func(
        text=f'У вас есть {word1_form} {word2_form}',
        reply_markup=orders_keyboard(orders, page=0),
    )

#
# def get_order_desc():
#


async def display_order_detail(message, order, tg_id, link, in_place=False):
    display_func = message.edit_text if in_place else message.answer

    roles = []
    if order.manager_tg_id == tg_id:
        roles.append('менеджер')
    if order.worker_tg_id == tg_id:
        roles.append('исполнитель')
    if order.customer_tg_id == tg_id:
        roles.append('клиент')

    is_manager = order.manager_tg_id == tg_id
    is_worker = order.worker_tg_id == tg_id
    is_customer = order.customer_tg_id == tg_id

    text = (
        f"<b>Заказ #{order.id}</b>\n"
        f"Название: {order.title}\n"
        f"Вы: {', '.join(roles)}\n"
    )
    if is_manager and not is_worker:
        text += f"Исполнитель: {link.saved_name}  ({link.tg_username})\n"
    text += f"Срок: {format_timedelta(order.deadline - datetime.datetime.now(datetime.UTC))}\n"
    if is_customer or is_manager:
        text += f"Цена: {order.price:.2f}\n"
    if is_worker or is_manager:
        text += f"Оплата: {order.paycheck:.2f}\n"
    text += f"\n{ORDER_STATUS_EMOJI[order.status]} {ORDER_STATUS_RU[order.status].capitalize()}\n"

    await display_func(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=order_detail_keyboard(order.id, is_manager))
    )


async def validate_deadline_message(message: types.Message):
    try:
        deadline_dt = (datetime.datetime.
                       strptime(message.text, "%d.%m.%Y %H:%M").
                       replace(tzinfo=ZoneInfo("Europe/Moscow")))
    except Exception:
        await message.answer(
            "Не удалось интерпретировать дату и время. "
            "Убедитесь, что формат валиден"
        )
        return False, None

    utc_now = datetime.datetime.now(datetime.UTC)
    if deadline_dt <= utc_now:
        await message.answer(
            "Предупреждение: указанный вами дедлайн находится в прошлом"
        )

    return True, deadline_dt


async def validate_money_message(message):
    try:
        value = Decimal(message.text.strip().replace(",", "."))
        return True, value
    except Exception:
        await message.answer(
            "Не удалось интерпретировать стоимость. "
            "Убедитесь, что формат ввода верный.\n"
        )
        return False, None
