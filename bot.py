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
CHANNEL_ID = "@FullYonoCode"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

class PostState(StatesGroup):
    waiting_for_post = State()

async def handle_root(request):
    return web.Response(text="Bot is active and running!")

# Admin Panel Home
@dp.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Create & Send New Post", callback_data="start_posting")],
        [InlineKeyboardButton(text="➡️ Open Channel", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")]
    ])
    text = (
        "<b>Bot Admin Panel</b>\n\n"
        "Click the button below to send a custom post with custom emojis to your channel!"
    )
    await message.answer(text, reply_markup=keyboard)

# Trigger posting flow
@dp.callback_query(F.data == "start_posting")
async def start_posting_cb(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PostState.waiting_for_post)
    await callback.message.answer(
        "<b>Send your post now!</b>\n\n"
        "Send your photo with caption, promo codes, and custom emojis. I am waiting:"
    )
    await callback.answer()

# Receive and store exact post content and custom emoji entities
@dp.message(PostState.waiting_for_post)
async def receive_post_content(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id if message.photo else None
    text_content = message.text or message.caption or ""
    entities = message.entities or message.caption_entities or []
    
    await state.update_data(
        photo_id=photo_id,
        text_content=text_content,
        entities=entities,
        has_photo=bool(message.photo)
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Confirm & Broadcast to Channel", callback_data="confirm_broadcast")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_broadcast")]
    ])
    
    await message.reply(
        "<b>Post Preview Received!</b>\n\n"
        "Click below to publish with your custom emojis and buttons to the channel:",
        reply_markup=keyboard
    )

# Confirm and broadcast preserving custom emojis
@dp.callback_query(F.data == "confirm_broadcast")
async def confirm_broadcast_cb(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    has_photo = data.get("has_photo")
    photo_id = data.get("photo_id")
    text_content = data.get("text_content")
    entities = data.get("entities")
    
    if not text_content and not photo_id:
        await callback.answer("No post found! Please start over with /start.", show_alert=True)
        return

    channel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Facebook", url="https://facebook.com")],
        [InlineKeyboardButton(text="➡️ YouTube", url="https://youtube.com")],
        [InlineKeyboardButton(text="➡️ Download", url="https://t.me/yourlink")]
    ])

    try:
        if has_photo:
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo_id,
                caption=text_content,
                caption_entities=entities,
                reply_markup=channel_keyboard
            )
        else:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=text_content,
                entities=entities,
                reply_markup=channel_keyboard
            )
        await callback.message.edit_text("✅ Post successfully broadcasted to your channel with custom emojis and buttons!")
    except Exception as e:
        await callback.message.edit_text(f"❌ Failed to broadcast: {e}")
    
    await state.clear()

# Cancel broadcast
@dp.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Broadcast cancelled. Send /start to begin again.")

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
