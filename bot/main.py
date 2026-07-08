import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, CallbackQuery, InlineKeyboardMarkup
from dotenv import load_dotenv

from bot.display_functions import display_workers, display_worker_detail
from bot.keyboards import workers_keyboard, WorkersPageCallback, WorkerCallback, worker_edit_keyboard
from db.session import SessionLocal
from services.manager_worker_service import ManagerWorkerService
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

        print(user)


@dp.message(Command('workers'))
async def handle_workers(message: types.Message, state: FSMContext):
    await state.clear()
    async with SessionLocal() as session:
        tg_id = message.from_user.id
        all_links, active_links = await ManagerWorkerService.get_all_workers_links(session, manager_tg_id=tg_id)

    await display_workers(message, active_links)


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


@dp.message(Command('add_worker'))
async def workers(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(LinkCreationForm.name)
    await message.answer(
        "Введите имя исполнителя: \n(Его будете видеть только вы)"
    )


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


async def main() -> None:
    global bot
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())