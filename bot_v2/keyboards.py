import datetime
from decimal import Decimal
from math import ceil
from sys import prefix
from zoneinfo import ZoneInfo

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.tables.orders import Order, OrderStatus, ORDER_STATUS_EMOJI

PAGE_SIZE = 5
WEB_APP_LINK = WebAppInfo(url="https://wdraft.online/")

class MenuCallback(CallbackData, prefix="menu"):
    action: str | None = None

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


def menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text='Заказы',
                callback_data=MenuCallback(action='orders').pack()
            ),
            InlineKeyboardButton(
                text='Новый',
                callback_data=MenuCallback(action='create_order').pack()
            )
        ],
        [
            InlineKeyboardButton(
                text='Запустить App',
                web_app=WEB_APP_LINK
            )
        ],
        [
            InlineKeyboardButton(
                text='Помощь',
                callback_data=MenuCallback(action='help').pack()
            )
        ]
    ]
    return keyboard


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


def orders_keyboard(
    orders: list[Order],
    page: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE

    for order in orders[start:end]:
        builder.button(
            text=f"{order.title}",
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

    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data=MenuCallback().pack(),
        )
    )

    return builder.as_markup()


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


def order_detail_keyboard(order_id, is_manager, back_dest='list'):
    """
    back == list | menu, depending where "back" will move us
    """
    keyboard = []
    keyboard.append([
        InlineKeyboardButton(
            text='Открыть чат',
            web_app=WebAppInfo(url=f"https://wdraft.online/#/chat/{order_id}")
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
            callback_data=OrderCallback(order_id=order_id, action=f'back_to_{back_dest}').pack()
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
