import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from dotenv import load_dotenv
import os

from db.session import SessionLocal
from services.user_service import UserService

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')

dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: types.Message):
    async with SessionLocal() as session:
        tg_id = message.from_user.id
        user = await UserService.get_by_tg_id(session, tg_id)

        if user:
            await message.answer("У вас уже есть аккаунт")
        else:
            await message.answer("Вы впервые активировали бота")
            user = await UserService.create(session, tg_id)
            await message.answer("Аккаунт был создан")

        print(user)


async def main() -> None:
    bot = Bot(token=TOKEN)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())