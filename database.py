import json
import time
from typing import Any, Optional
import aiosqlite

from config import config

DEFAULT_MENU = [
    {"id": 1, "name": "Classic Don", "description": "Mol go'shti kolbasa, ketchup, xantal", "price": 25000, "category": "Hot-doglar"},
    {"id": 2, "name": "Cheese Boss", "description": "Ikki xil pishloq va maxsus sous", "price": 30000, "category": "Hot-doglar"},
    {"id": 3, "name": "Spicy Capo", "description": "Achchiq sous, piyoz va jalapeno", "price": 32000, "category": "Hot-doglar"},
    {"id": 4, "name": "Kartoshka fri", "description": "Qarsildoq kartoshka", "price": 18000, "category": "Qo'shimchalar"},
    {"id": 5, "name": "Cola 0.5L", "description": "Muzdek ichimlik", "price": 10000, "category": "Ichimliklar"},
]


async def init_db() -> None:
    async with aiosqlite.connect(config.database_path) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS menu (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price INTEGER NOT NULL,
                category TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                created_at INTEGER NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                address TEXT,
                comment TEXT,
                items_json TEXT NOT NULL,
                total INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                created_at INTEGER NOT NULL
            )
            """
        )
        await db.commit()

        cur = await db.execute("SELECT COUNT(*) FROM menu")
        row = await cur.fetchone()
        if row and row[0] == 0:
            await db.executemany(
                "INSERT INTO menu (id, name, description, price, category, is_active) VALUES (?, ?, ?, ?, ?, 1)",
                [(m["id"], m["name"], m["description"], m["price"], m["category"]) for m in DEFAULT_MENU],
            )
            await db.commit()


async def get_menu() -> list[dict[str, Any]]:
    async with aiosqlite.connect(config.database_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT id, name, description, price, category FROM menu WHERE is_active = 1 ORDER BY category, id"
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def create_order(data: dict[str, Any]) -> int:
    async with aiosqlite.connect(config.database_path) as db:
        cur = await db.execute(
            """
            INSERT INTO orders (user_id, username, full_name, phone, address, comment, items_json, total, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)
            """,
            (
                int(data.get("user_id", 0)),
                data.get("username"),
                data.get("full_name"),
                data.get("phone"),
                data.get("address"),
                data.get("comment"),
                json.dumps(data.get("items", []), ensure_ascii=False),
                int(data.get("total", 0)),
                int(time.time()),
            ),
        )
        await db.commit()
        return int(cur.lastrowid)


async def get_user_orders(user_id: int) -> list[dict[str, Any]]:
    async with aiosqlite.connect(config.database_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 50",
            (user_id,),
        )
        rows = await cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["items"] = json.loads(d["items_json"] or "[]")
            result.append(d)
        return result


async def get_order(order_id: int) -> Optional[dict[str, Any]]:
    async with aiosqlite.connect(config.database_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = await cur.fetchone()
        if not row:
            return None
        d = dict(row)
        d["items"] = json.loads(d["items_json"] or "[]")
        return d


async def list_orders(status: Optional[str] = None, limit: int = 30) -> list[dict[str, Any]]:
    async with aiosqlite.connect(config.database_path) as db:
        db.row_factory = aiosqlite.Row
        if status:
            cur = await db.execute(
                "SELECT * FROM orders WHERE status = ? ORDER BY id DESC LIMIT ?",
                (status, limit),
            )
        else:
            cur = await db.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,))
        rows = await cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["items"] = json.loads(d["items_json"] or "[]")
            result.append(d)
        return result


async def update_order_status(order_id: int, status: str) -> bool:
    async with aiosqlite.connect(config.database_path) as db:
        cur = await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()
        return cur.rowcount > 0


async def list_admins() -> list[int]:
    async with aiosqlite.connect(config.database_path) as db:
        cur = await db.execute("SELECT user_id FROM admins")
        rows = await cur.fetchall()
        return [int(r[0]) for r in rows]


async def add_admin(user_id: int, username: str | None) -> None:
    async with aiosqlite.connect(config.database_path) as db:
        await db.execute(
            "INSERT OR IGNORE INTO admins (user_id, username, created_at) VALUES (?, ?, ?)",
            (int(user_id), username, int(time.time())),
        )
        await db.commit()
