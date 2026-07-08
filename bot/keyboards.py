from math import ceil

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


PAGE_SIZE = 1


class WorkersPageCallback(CallbackData, prefix="workers"):
    page: int


class WorkerCallback(CallbackData, prefix="worker"):
    link_id: int
    saved_name: str | None = None
    saved_username: str | None = None
    action: str | None = None


def workers_keyboard(
    links: list,
    page: int,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    total_pages = max(1, ceil(len(links) / PAGE_SIZE))

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE

    for link in links[start:end]:
        builder.button(
            text=link.saved_name,
            callback_data=WorkerCallback(
                link_id=link.id,
                saved_name=link.saved_name,
                saved_username=link.tg_username
            ),
        )

    builder.adjust(1)


    left_callback = 'ignore' if page + 1 == 1 else WorkersPageCallback(page=page - 1).pack()
    right_callback = 'ignore' if page + 1 >= total_pages else WorkersPageCallback(page=page + 1).pack()

    nav = [
        InlineKeyboardButton(
            text="⬅️",
            callback_data=left_callback,
        ),
        InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data="ignore",
        ),
        InlineKeyboardButton(
            text="➡️",
            callback_data=right_callback,
        )
    ]

    builder.row(*nav)

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