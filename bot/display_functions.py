from aiogram.types import InlineKeyboardMarkup

from bot.keyboards import workers_keyboard, worker_edit_keyboard


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