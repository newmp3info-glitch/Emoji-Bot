import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("ERROR: BOT_TOKEN Environment Variable is missing in Render!")

PORT = int(os.getenv("PORT", 10000))
WEBHOOK_PATH = f"/{TOKEN}"
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_URL = f"{RENDER_URL}{WEBHOOK_PATH}" if RENDER_URL else None

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(F.text == "/start")
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Facebook", url="https://facebook.com")],
        [InlineKeyboardButton(text="➡️ YouTube", url="https://youtube.com")],
        [InlineKeyboardButton(text="➡️ Download", url="https://t.me/yourlink")]
    ])
    
    text = (
        "<b>Game Rummy ➡️ New Promo Code Fast Claim Now!!</b>\n\n"
        "<tg-emoji id='5368324170671202286'>🎁</tg-emoji> <b>PROMO CODE</b> ➡️ gamerummy.net\n"
        "🔥 <b>JOIN THIS CHANNEL</b> for regular updates!"
    )
    
    await message.answer(text, reply_markup=keyboard)

async def on_startup():
    if WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)

def main():
    logging.basicConfig(level=logging.INFO)
    dp.startup.register(on_startup)
    
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp)
    
    web.run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
