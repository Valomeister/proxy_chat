import asyncio

from bot_v2.api import start_api
from bot_v2.bot import bot, dp, start_bot
from bot_v2.handlers import routers


async def main():
    for router in routers:
        dp.include_router(router)

    await asyncio.gather(
        start_api(),
        start_bot(),
    )


if __name__ == "__main__":
    asyncio.run(main())