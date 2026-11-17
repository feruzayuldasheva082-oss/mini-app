import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import database
from config import config

WEBAPP_DIR = Path(__file__).parent / "webapp"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()
    yield


app = FastAPI(title="Hot Dog Mafia API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OrderItem(BaseModel):
    id: int
    name: str
    price: int
    qty: int = Field(ge=1)


class OrderCreate(BaseModel):
    user_id: int = 0
    username: Optional[str] = None
    full_name: str
    phone: str
    address: str
    comment: Optional[str] = None
    items: list[OrderItem]
    total: int


@app.get("/api/health")
@app.get("/health")
async def api_health():
    return {"status": "ok"}


@app.get("/api/menu")
async def api_menu():
    return await database.get_menu()


@app.post("/api/orders")
async def api_create_order(payload: OrderCreate):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Savat bo'sh")
    data = payload.model_dump()
    data["items"] = [i.model_dump() for i in payload.items]
    order_id = await database.create_order(data)
    # Notify admin bot by writing to a simple outbox file is avoided; bots can poll DB or be notified via shared queue.
    # For simplicity we trigger notification via app.state hook if set.
    notifier = getattr(app.state, "notify_admin_new_order", None)
    if notifier:
        asyncio.create_task(notifier(order_id))
    return {"id": order_id, "status": "new"}


@app.get("/api/orders")
async def api_get_orders(user_id: int = Query(0)):
    if user_id <= 0:
        return []
    return await database.get_user_orders(user_id)


@app.get("/")
async def index():
    return FileResponse(WEBAPP_DIR / "index.html")


app.mount("/", StaticFiles(directory=WEBAPP_DIR, html=True), name="webapp")
