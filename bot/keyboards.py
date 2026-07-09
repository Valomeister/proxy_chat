import datetime
from decimal import Decimal
from math import ceil
from sys import prefix
from zoneinfo import ZoneInfo

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.tables.orders import Order, OrderStatus, ORDER_STATUS_EMOJI

PAGE_SIZE = 5


class WorkersPageCallback(CallbackData, prefix="workers"):
    page: int

class WorkerCallback(CallbackData, prefix="worker"):
    link_id: int
    saved_name: str | None = None
    saved_username: str | None = None
    action: str | None = None

class DeadlineCallback(CallbackData, prefix="deadline"):
    action: str

class MoneyCallback(CallbackData, prefix="money"):
    action: str

class OrdersPageCallback(CallbackData, prefix="orders"):
    page: int

class OrderCallback(CallbackData, prefix="order"):
    order_id: int
    title: str | None = None
    deadline: str | None = None
    price: Decimal | None = None
    paycheck: Decimal | None = None
    status: OrderStatus | None = None
    action: str | None = None


def add_pagination(
    builder: InlineKeyboardBuilder,
    *,
    page: int,
    total_items: int,
    page_size: int,
    callback_factory,
) -> None:
    total_pages = max(1, ceil(total_items / page_size))

    if total_pages <= 1:
        return

    builder.row(
        InlineKeyboardButton(
            text="⬅️",
            callback_data=(
                "ignore"
                if page == 0
                else callback_factory(page=page - 1).pack()
            ),
        ),
        InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data="ignore",
        ),
        InlineKeyboardButton(
            text="➡️",
            callback_data=(
                "ignore"
                if page >= total_pages - 1
                else callback_factory(page=page + 1).pack()
            ),
        ),
    )


def workers_keyboard(
    links: list,
    page: int,
    source: str = "/workers",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE

    action = "assign_to_order" if source == "/orders" else None

    for link in links[start:end]:
        builder.button(
            text=link.saved_name,
            callback_data=WorkerCallback(
                link_id=link.id,
                saved_name=link.saved_name,
                saved_username=link.tg_username,
                action=action,
            ),
        )

    builder.adjust(1)

    add_pagination(
        builder,
        page=page,
        total_items=len(links),
        page_size=PAGE_SIZE,
        callback_factory=WorkersPageCallback,
    )

    return builder.as_markup()


def orders_keyboard(
    orders: list[Order],
    page: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE

    for order in orders[start:end]:
        builder.button(
            text=f"{ORDER_STATUS_EMOJI[order.status]} {order.title}",
            callback_data=OrderCallback(
                order_id=order.id,
                title=order.title,
            ),
        )

    builder.adjust(1)

    add_pagination(
        builder,
        page=page,
        total_items=len(orders),
        page_size=PAGE_SIZE,
        callback_factory=OrdersPageCallback,
    )

    return builder.as_markup()



def worker_edit_keyboard(link_id):
    return \
        [
            [
                InlineKeyboardButton(
                    text='Изменить имя',
                    callback_data=WorkerCallback(link_id=link_id, action='edit_name').pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='Изменить @username',
                    callback_data=WorkerCallback(link_id=link_id, action='edit_username').pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='Удалить исполнителя',
                    callback_data=WorkerCallback(link_id=link_id, action='delete').pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='Назад',
                    callback_data=WorkerCallback(link_id=link_id, action='back').pack()
                )
            ],
        ]


def input_format_keyboard(action: str, callback_class):
    """
    action = "show" | "hide"
    """
    action_verb = 'Показать' if action == 'show' else 'Скрыть'
    return \
        [
            [
                InlineKeyboardButton(
                    text=f'{action_verb} допустимые форматы',
                    callback_data=callback_class(action=action).pack()
                )
            ]
        ]


def order_detail_keyboard(order_id, is_manager):
    keyboard = []
    keyboard.append([
        InlineKeyboardButton(
            text='Открыть чат',
            callback_data=OrderCallback(order_id=order_id, action='ignore').pack()
        )
    ])
    if is_manager:
        keyboard.append([
            InlineKeyboardButton(
                text='Изменить',
                callback_data=OrderCallback(order_id=order_id, action='edit').pack()
            )
        ])
    keyboard.append([
        InlineKeyboardButton(
            text='Назад',
            callback_data=OrderCallback(order_id=order_id, action='back').pack()
        )
    ])

    return keyboard

def order_edit_keyboard(order_id):
    return \
        [
            [
                InlineKeyboardButton(
                    text='Название',
                    callback_data=OrderCallback(order_id=order_id, action='edit_title').pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='Срок',
                    callback_data=OrderCallback(order_id=order_id, action='edit_deadline').pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='Цена',
                    callback_data=OrderCallback(order_id=order_id, action='edit_price').pack()
                ),
                InlineKeyboardButton(
                    text='Оплата',
                    callback_data=OrderCallback(order_id=order_id, action='edit_paycheck').pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='Статус',
                    callback_data=OrderCallback(order_id=order_id, action='edit_status').pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='Удалить',
                    callback_data=OrderCallback(order_id=order_id, action='delete').pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='Назад',
                    callback_data=OrderCallback(order_id=order_id, action='back_to_detail').pack()
                )
            ],
        ]


def order_edit_status_keyboard(order_id):
    return \
        [
            [
                InlineKeyboardButton(
                    text=f'{ORDER_STATUS_EMOJI[OrderStatus.created]} В процессе',
                    callback_data=OrderCallback(order_id=order_id, action='update_status_created').pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text=f'{ORDER_STATUS_EMOJI[OrderStatus.cancelled]} Отменен',
                    callback_data=OrderCallback(order_id=order_id, action='update_status_cancelled').pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text=f'{ORDER_STATUS_EMOJI[OrderStatus.completed]} Выполнен',
                    callback_data=OrderCallback(order_id=order_id, action='update_status_completed').pack()
                ),
            ],
            [
                InlineKeyboardButton(
                    text='Отмена',
                    callback_data=OrderCallback(order_id=order_id, action='back_to_detail').pack()
                )
            ],
        ]
