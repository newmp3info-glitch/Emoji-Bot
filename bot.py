import os
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

# Your Telegram Channel Username (e.g., @your_channel_username)
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
        "Click the button below to send a custom post to your channel, or send any custom emoji to get its ID!"
    )
    await message.answer(text, reply_markup=keyboard)

# Trigger posting flow
@dp.callback_query(F.data == "start_posting")
async def start_posting_cb(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PostState.waiting_for_post)
    await callback.message.answer(
        "<b>Send your post now!</b>\n\n"
        "You can send text, promo codes, custom emojis, or photos with captions. I am waiting for your content:"
    )
    await callback.answer()

# Receive user's custom post content
@dp.message(PostState.waiting_for_post)
async def receive_post_content(message: Message, state: FSMContext):
    await state.update_data(user_msg_id=message.message_id, user_chat_id=message.chat.id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Confirm & Broadcast to Channel", callback_data="confirm_broadcast")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_broadcast")]
    ])
    
    await message.reply(
        "<b>Post Preview Received!</b>\n\n"
        "Click the button below to publish this exact post to your channel with buttons and custom emojis:",
        reply_markup=keyboard
    )

# Confirm and push to channel
@dp.callback_query(F.data == "confirm_broadcast")
async def confirm_broadcast_cb(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get("user_msg_id")
    chat_id = data.get("user_chat_id")
    
    if not msg_id:
        await callback.answer("No post found! Please start over with /start.", show_alert=True)
        return

    # Default Inline Buttons attached to the channel post
    channel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Facebook", url="https://facebook.com")],
        [InlineKeyboardButton(text="➡️ YouTube", url="https://youtube.com")],
        [InlineKeyboardButton(text="➡️ Download", url="https://t.me/yourlink")]
    ])

    try:
        # Copies user's exact message (text, photos, custom emojis) to the channel
        await bot.copy_message(
            chat_id=CHANNEL_ID,
            from_chat_id=chat_id,
            message_id=msg_id,
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

# Custom Emoji ID detector when not in posting state
@dp.message(F.text & ~F.state)
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
