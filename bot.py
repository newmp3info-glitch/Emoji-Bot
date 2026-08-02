import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
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
CHANNEL_ID = "@fullyonocode"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

class PostState(StatesGroup):
    waiting_for_text = State()

async def handle_root(request):
    return web.Response(text="Bot is active and running!")

@dp.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Create New Channel Post", callback_data="start_post")],
        [InlineKeyboardButton(text="➡️ Open Channel", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")]
    ])
    text = (
        "<b>Bot Admin Panel</b>\n\n"
        "Click the button below to type your message with custom emojis and broadcast it directly to your channel!"
    )
    await message.answer(text, reply_markup=keyboard)

@dp.callback_query(F.data == "start_post")
async def start_post_cb(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PostState.waiting_for_text)
    await callback.message.answer(
        "<b>Type your text now!</b>\n\n"
        "You can use HTML tags and custom emojis like this:\n"
        "<code>&lt;tg-emoji id='6291753830212182163'&gt;💰&lt;/tg-emoji&gt;</code>\n\n"
        "Send your text message:"
    )
    await callback.answer()

@dp.message(PostState.waiting_for_text)
async def receive_text_content(message: Message, state: FSMContext):
    await state.update_data(post_text=message.text)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Confirm & Broadcast to Channel", callback_data="send_to_channel")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_post")]
    ])
    
    await message.reply(
        "<b>Preview Saved!</b>\n\n"
        "Click below to send this post directly to your channel with custom emojis and buttons:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "send_to_channel")
async def send_to_channel_cb(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    post_text = data.get("post_text")
    
    if not post_text:
        await callback.answer("No text found! Start over with /start.", show_alert=True)
        return

    channel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Facebook", url="https://facebook.com")],
        [InlineKeyboardButton(text="➡️ YouTube", url="https://youtube.com")],
        [InlineKeyboardButton(text="➡️ Download", url="https://t.me/yourlink")]
    ])

    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=post_text,
            reply_markup=channel_keyboard
        )
        await callback.message.edit_text("✅ Post successfully broadcasted to your channel with custom emojis and buttons!")
    except Exception as e:
        await callback.message.edit_text(f"❌ Failed to broadcast: {e}")
    
    await state.clear()

@dp.callback_query(F.data == "cancel_post")
async def cancel_post_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Cancelled. Send /start to begin again.")

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
