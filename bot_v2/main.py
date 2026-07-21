import asyncio
import signal



from bot_v2.api import start_api, server
from bot_v2.bot import bot, dp, start_bot
from bot_v2.handlers import routers
from bot_v2.middlewares.maintenance import MaintenanceMiddleware



async def main():
    for router in routers:
        dp.include_router(router)

    dp.message.middleware(
        MaintenanceMiddleware()
    )

    dp.callback_query.middleware(
        MaintenanceMiddleware()
    )


    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()

    loop.add_signal_handler(
        signal.SIGINT,
        stop_event.set,
    )

    loop.add_signal_handler(
        signal.SIGTERM,
        stop_event.set,
    )

    api_task = asyncio.create_task(start_api())
    bot_task = asyncio.create_task(start_bot())

    await stop_event.wait()

    await stop_event.wait()

    print("Stopping tasks")

    bot_task.cancel()

    if server:
        server.should_exit = True

    await asyncio.gather(
        api_task,
        bot_task,
        return_exceptions=True,
    )

    print("Stopped")

if __name__ == "__main__":
    asyncio.run(main())