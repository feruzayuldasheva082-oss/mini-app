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

    runners = {
        "webapp": server.serve,
        "admin-bot": lambda: run_admin_bot(app_state=app.state, stop_event=stop_event),
        "customer-bot": lambda: run_customer_bot(stop_event=stop_event),
    }
    tasks = {name: asyncio.create_task(fn(), name=name) for name, fn in runners.items()}
    stop_task = asyncio.create_task(stop_event.wait(), name="stop-watcher")

    async def shutdown() -> None:
        server.should_exit = True
        for task in [stop_task, *tasks.values()]:
            task.cancel()
        await asyncio.gather(stop_task, *tasks.values(), return_exceptions=True)

    try:
        while True:
            done, _ = await asyncio.wait(
                [stop_task, *tasks.values()], return_when=asyncio.FIRST_COMPLETED
            )
            if stop_task in done:
                break
            for task in done:
                name = task.get_name()
                if not task.cancelled():
                    exc = task.exception()
                    if exc:
                        print(f"[{name}] xatolik: {type(exc).__name__}: {exc}")
                if stop_event.is_set():
                    break
                print(f"[{name}] to'xtadi — 2 soniyadan keyin qayta ishga tushiriladi")
                await asyncio.sleep(2)
                tasks[name] = asyncio.create_task(runners[name](), name=name)
    finally:
        await shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
