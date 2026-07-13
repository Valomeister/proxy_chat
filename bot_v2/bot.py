from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

import os

from dotenv import load_dotenv


load_dotenv()


BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode='HTML')
)

dp = Dispatcher()


async def start_bot():
    await dp.start_polling(
        bot
    )