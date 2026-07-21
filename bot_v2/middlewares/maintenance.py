from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from os import getenv

from dotenv import load_dotenv


load_dotenv()


MAINTENANCE = getenv("MAINTENANCE", "0") == "1"


class MaintenanceMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler,
        event,
        data,
    ):

        if not MAINTENANCE:
            return await handler(event, data)

        if isinstance(event, Message):
            await event.answer(
                "🛠 Сейчас проводятся технические работы.\n"
                "Попробуйте немного позже."
            )

        elif isinstance(event, CallbackQuery):
            await event.answer(
                "🛠 Сейчас проводятся технические работы.",
                show_alert=True,
            )

        return