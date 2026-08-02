import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# গিটহাবে কোনো টোকেন থাকবে না, এটি রেন্ডার থেকে সুরক্ষিতভাবে রিড করবে
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("ERROR: BOT_TOKEN is missing in Render Environment Variables!")

PORT = int(os.getenv("PORT", 10000))
WEBHOOK_PATH = f"/{TOKEN}"

# রেন্ডারের লাইভ লিংকটি এখানে ফিক্সড করে দেওয়া হলো যাতে ওয়েবহুক মিস না হয়
RENDER_URL = "https://emoji-bot-msn5.onrender.com"
WEBHOOK_URL = f"{RENDER_URL}{WEBHOOK_PATH}"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def handle_root(request):
    return web.Response(text="Bot is active and running!")

@dp.message(Command("start"))
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Facebook", url="https://facebook.com")],
        [InlineKeyboardButton(text="➡️ YouTube", url="https://youtube.com")],
        [InlineKeyboardButton(text="➡️ Download", url="https://t.me/yourlink")]
    ])
    
    text = (
        "<b>Game Rummy ➡️ New Promo Code Fast Claim Now!!</b>\n\n"
        "🎁 <b>PROMO CODE</b> ➡️ gamerummy.net\n"
        "🔥 <b>JOIN THIS CHANNEL</b> for regular updates!"
    )
    
    await message.answer(text, reply_markup=keyboard)

async def on_startup():
    if WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)
        print(f"Webhook successfully set to: {WEBHOOK_URL}")

def main():
    logging.basicConfig(level=logging.INFO)
    dp.startup.register(on_startup)
    
    app = web.Application()
    app.router.add_get("/", handle_root)
    
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp)
    
    web.run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
