import asyncio
from html import escape
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import database
from config import config

STATUS_LABELS = {
    "new": "Yangi",
    "accepted": "Qabul qilindi",
    "cooking": "Tayyorlanmoqda",
    "delivering": "Yetkazilmoqda",
    "done": "Yakunlandi",
    "cancelled": "Bekor qilindi",
}
STATUS_FLOW = ["accepted", "cooking", "delivering", "done", "cancelled"]


PLACEHOLDER_ADMIN_ID = 123456789


async def is_admin(user_id: int) -> bool:
    # .env dagi namuna ID (123456789) inobatga olinmaydi.
    configured = [i for i in config.admin_ids if i != PLACEHOLDER_ADMIN_ID]
    if configured:
        return user_id in configured
    return user_id in await database.list_admins()


async def ensure_admin(user_id: int, username: str | None) -> bool:
    """Faqat ADMIN_IDS namuna bo'lganda birinchi /start yuborganni admin qiladi."""
    if [i for i in config.admin_ids if i != PLACEHOLDER_ADMIN_ID]:
        return await is_admin(user_id)
    if await is_admin(user_id):
        return True
    if await database.list_admins():
        return False
    await database.add_admin(user_id, username)
    print(f"[admin_bot] Yangi admin royxatga olindi: {user_id} (@{username})")
    return True


def status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for s in STATUS_FLOW:
        row.append(InlineKeyboardButton(text=STATUS_LABELS[s], callback_data=f"st:{order_id}:{s}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def e(value) -> str:
    """Foydalanuvchi kiritgan matnni HTML uchun xavfsiz qiladi."""
    return escape("" if value is None else str(value))


def format_order(o: dict) -> str:
    items = "\n".join([f"  • {e(i['name'])} × {i['qty']} — {i['price']*i['qty']:,} so‘m" for i in o.get("items", [])])
    uname = f"@{e(o['username'])}" if o.get("username") else "-"
    return (
        f"<b>Buyurtma #{o['id']}</b>\n"
        f"Holat: <b>{STATUS_LABELS.get(o['status'], o['status'])}</b>\n"
        f"Mijoz: {e(o.get('full_name') or '-')} ({uname})\n"
        f"ID: {o.get('user_id')}\n"
        f"Tel: {e(o.get('phone') or '-')}\n"
        f"Manzil: {e(o.get('address') or '-')}\n"
        f"Izoh: {e(o.get('comment') or '-')}\n\n"
        f"<b>Mahsulotlar:</b>\n{items or '  -'}\n\n"
        f"<b>Jami: {o.get('total',0):,} so‘m</b>"
    )


async def cmd_start(message: Message):
    if not await ensure_admin(message.from_user.id, message.from_user.username):
        return
    await message.answer(
        "Hot Dog Mafia Admin bot.\n\nBuyruqlar:\n/orders — oxirgi buyurtmalar\n/new — yangi buyurtmalar\n/order <id> — buyurtma ko‘rish"
    )


async def cmd_orders(message: Message):
    if not await is_admin(message.from_user.id):
        return
    orders = await database.list_orders(limit=15)
    if not orders:
        await message.answer("Buyurtmalar yo‘q.")
        return
    for o in orders:
        await message.answer(format_order(o), parse_mode="HTML", reply_markup=status_keyboard(o["id"]))


async def cmd_new(message: Message):
    if not await is_admin(message.from_user.id):
        return
    orders = await database.list_orders(status="new", limit=20)
    if not orders:
        await message.answer("Yangi buyurtmalar yo‘q.")
        return
    for o in orders:
        await message.answer(format_order(o), parse_mode="HTML", reply_markup=status_keyboard(o["id"]))


async def cmd_order(message: Message):
    if not await is_admin(message.from_user.id):
        return
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Foydalanish: /order 123")
        return
    o = await database.get_order(int(parts[1]))
    if not o:
        await message.answer("Buyurtma topilmadi.")
        return
    await message.answer(format_order(o), parse_mode="HTML", reply_markup=status_keyboard(o["id"]))


async def cb_status(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo‘q", show_alert=True)
        return
    _, oid, status = callback.data.split(":", 2)
    ok = await database.update_order_status(int(oid), status)
    if not ok:
        await callback.answer("Topilmadi", show_alert=True)
        return
    o = await database.get_order(int(oid))
    await callback.message.edit_text(format_order(o), parse_mode="HTML", reply_markup=status_keyboard(o["id"]))
    await callback.answer(f"Holat: {STATUS_LABELS.get(status, status)}")


async def notify_admins_new_order(bot: Bot, order_id: int):
    o = await database.get_order(order_id)
    if not o:
        return
    text = "🆕 Yangi buyurtma!\n\n" + format_order(o)
    configured = [i for i in config.admin_ids if i != PLACEHOLDER_ADMIN_ID]
    admin_ids = configured or await database.list_admins()
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML", reply_markup=status_keyboard(order_id))
        except Exception as e:
            print(f"[admin_bot] notify xatolik {admin_id}: {e}")


async def run_admin_bot(app_state=None, stop_event: asyncio.Event | None = None):
    if not config.admin_bot_token or "your_" in config.admin_bot_token:
        print("[admin_bot] ADMIN_BOT_TOKEN sozlanmagan, admin boti ishga tushmadi.")
        if stop_event:
            await stop_event.wait()
        return
    if not [i for i in config.admin_ids if i != PLACEHOLDER_ADMIN_ID]:
        print("[admin_bot] ADMIN_IDS namuna holatda — birinchi /start yuborgan foydalanuvchi admin bo'ladi.")
    bot = Bot(token=config.admin_bot_token)
    dp = Dispatcher()
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_orders, Command("orders"))
    dp.message.register(cmd_new, Command("new"))
    dp.message.register(cmd_order, Command("order"))
    dp.callback_query.register(cb_status, F.data.startswith("st:"))

    async def notifier(order_id: int):
        await notify_admins_new_order(bot, order_id)

    if app_state is not None:
        app_state.notify_admin_new_order = notifier

    print("[admin_bot] Ishga tushdi")
    try:
        await dp.start_polling(bot, handle_signals=False)
    finally:
        await bot.session.close()
