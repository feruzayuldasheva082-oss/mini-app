import asyncio
import contextlib
import signal

import uvicorn

import database
from config import config
from server import app
from customer_bot import run_customer_bot
from admin_bot import run_admin_bot


class BotServer(uvicorn.Server):
    """Signal'larni o'zimiz boshqaramiz: botlar ham to'g'ri to'xtashi uchun."""

    @contextlib.contextmanager
    def capture_signals(self):
        yield


async def main() -> None:
    await database.init_db()
    server_config = uvicorn.Config(app, host=config.host, port=config.port, log_level="info")
    server = BotServer(server_config)

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except (NotImplementedError, RuntimeError):
            pass

    tasks = [
        asyncio.create_task(server.serve(), name="webapp"),
        asyncio.create_task(run_admin_bot(app_state=app.state, stop_event=stop_event), name="admin-bot"),
        asyncio.create_task(run_customer_bot(stop_event=stop_event), name="customer-bot"),
    ]
    stop_task = asyncio.create_task(stop_event.wait(), name="stop-watcher")

    try:
        done, _ = await asyncio.wait([*tasks, stop_task], return_when=asyncio.FIRST_COMPLETED)
        if stop_task in done:
            server.should_exit = True
            for task in tasks:
                task.cancel()
    finally:
        for task in [stop_task, *tasks]:
            task.cancel()
        await asyncio.gather(stop_task, *tasks, return_exceptions=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
