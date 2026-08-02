import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_PATH = f"/{TOKEN}"
RENDER_URL = "https://emoji-bot-msn5.onrender.com"
WEBHOOK_URL = f"{RENDER_URL}{WEBHOOK_PATH}"

# Your Telegram Channel Username
CHANNEL_ID = "@your_channel_username"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def handle_root(request):
    return web.Response(text="Bot is active and running!")

# 1-Click Admin Panel UI with Send Button
@dp.message(Command("start"))
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Send Post to Channel (1-Click)", callback_data="broadcast_post")],
        [InlineKeyboardButton(text="➡️ Open Facebook", url="https://facebook.com")]
    ])
    await message.answer("Admin Panel: Click the button below to send the post to your channel instantly.", reply_markup=keyboard)

# 1-Click Broadcast Handler via Callback Query
@dp.callback_query(F.data == "broadcast_post")
async def callback_send_post(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Facebook", url="https://facebook.com")],
        [InlineKeyboardButton(text="➡️ YouTube", url="https://youtube.com")],
        [InlineKeyboardButton(text="➡️ Download", url="https://t.me/yourlink")]
    ])
    
    # Replace 'YOUR_VALID_CUSTOM_EMOJI_ID' with your real custom emoji ID
    text = (
        "<b>Game Rummy ➡️ New Promo Code Fast Claim Now!!</b>\n\n"
        "<tg-emoji id='6291753830212182163'>💰</tg-emoji> <b>PROMO CODE</b> ➡️ gamerummy.net\n"
        "🔥 <b>JOIN THIS CHANNEL</b> for regular updates!"
    )
    
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=text, reply_markup=keyboard)
        await callback.answer("Post successfully sent to the channel!", show_alert=True)
    except Exception as e:
        await callback.answer(f"Failed: {e}", show_alert=True)

# Command fallback for /post
@dp.message(Command("post"))
async def send_post_to_channel(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Facebook", url="https://facebook.com")],
        [InlineKeyboardButton(text="➡️ YouTube", url="https://youtube.com")],
        [InlineKeyboardButton(text="➡️ Download", url="https://t.me/yourlink")]
    ])
    
    text = (
        "<b>Game Rummy ➡️ New Promo Code Fast Claim Now!!</b>\n\n"
        "<tg-emoji id='6291753830212182163'>💰</tg-emoji> <b>PROMO CODE</b> ➡️ gamerummy.net\n"
        "🔥 <b>JOIN THIS CHANNEL</b> for regular updates!"
    )
    
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=text, reply_markup=keyboard)
        await message.reply("Post successfully sent to the channel!")
    except Exception as e:
        await message.reply(f"Failed to send post: {e}")

# Automatic Custom Emoji ID Detector
@dp.message(F.text)
async def get_emoji_id(message: Message):
    if message.entities:
        for entity in message.entities:
            if entity.type == "custom_emoji":
                await message.reply(f"Custom Emoji ID: {entity.custom_emoji_id}")

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
