import asyncio
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from config import config

WELCOME_TEXT = (
    "🍔 *Hot Dog Mafia’ga xush kelibsiz!*\n\n"
    "Mazali hot-doglar va tez buyurtma xizmati.\n"
    "Buyurtma berish uchun quyidagi Mini App’ni oching."
)


def app_url(view: str | None = None) -> str:
    if not view:
        return config.webapp_url
    parsed = urlparse(config.webapp_url)
    query = dict(parse_qsl(parsed.query))
    query["view"] = view
    return urlunparse(parsed._replace(query=urlencode(query)))


def webapp_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Buyurtma berish / Mafia menyusi", web_app=WebAppInfo(url=app_url("menu")))],
        [InlineKeyboardButton(text="📦 Mening buyurtmalarim", web_app=WebAppInfo(url=app_url("orders")))],
    ])


async def cmd_start(message: Message):
    await message.answer(WELCOME_TEXT, parse_mode="Markdown", reply_markup=webapp_keyboard())


async def fallback(message: Message):
    await message.answer(
        "Buyurtma berish uchun Mini App’ni oching:",
        reply_markup=webapp_keyboard(),
    )


async def run_customer_bot(stop_event: asyncio.Event | None = None):
    if not config.customer_bot_token or "your_" in config.customer_bot_token:
        print("[customer_bot] CUSTOMER_BOT_TOKEN sozlanmagan, mijoz boti ishga tushmadi.")
        if stop_event:
            await stop_event.wait()
        return
    bot = Bot(token=config.customer_bot_token)
    dp = Dispatcher()
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_start, Command("tart"))
    dp.message.register(fallback)
    print("[customer_bot] Ishga tushdi")
    try:
        await dp.start_polling(bot, handle_signals=False)
    finally:
        await bot.session.close()
