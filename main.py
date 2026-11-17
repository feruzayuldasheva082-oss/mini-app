import asyncio
import uvicorn

import database
from config import config
from server import app
from customer_bot import run_customer_bot
from admin_bot import run_admin_bot


async def main():
    await database.init_db()
    server_config = uvicorn.Config(app, host=config.host, port=config.port, log_level="info")
    server = uvicorn.Server(server_config)

    stop_event = asyncio.Event()
    tasks = [
        asyncio.create_task(server.serve()),
        asyncio.create_task(run_admin_bot(app_state=app.state, stop_event=stop_event)),
        asyncio.create_task(run_customer_bot(stop_event=stop_event)),
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
