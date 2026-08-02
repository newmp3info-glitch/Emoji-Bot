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

# Automatic Telegram UTF-16 Entity to HTML Converter (Handles Custom Emojis & Formatting)
def convert_entities_to_html(text: str, entities: list) -> str:
    if not entities or not text:
        return text
    
    try:
        utf16_bytes = text.encode('utf-16-le')
        sorted_entities = sorted(entities, key=lambda e: e.offset, reverse=True)
        current_bytes = bytearray(utf16_bytes)
        
        for entity in sorted_entities:
            start = entity.offset * 2
            length = entity.length * 2
            end = start + length
            
            if start < 0 or end > len(current_bytes):
                continue
                
            entity_bytes = bytes(current_bytes[start:end])
            content = entity_bytes.decode('utf-16-le', errors='ignore')
            
            replacement = content
            if entity.type == 'custom_emoji':
                emoji_id = entity.custom_emoji_id
                replacement = f"<tg-emoji id='{emoji_id}'>{content}</tg-emoji>"
            elif entity.type == 'bold':
                replacement = f"<b>{content}</b>"
            elif entity.type == 'italic':
                replacement = f"<i>{content}</i>"
            elif entity.type == 'text_link':
                url = entity.url
                replacement = f"<a href='{url}'>{content}</a>"
            elif entity.type == 'code':
                replacement = f"<code>{content}</code>"
            elif entity.type == 'pre':
                replacement = f"<pre>{content}</pre>"
                
            current_bytes[start:end] = replacement.encode('utf-16-le')
            
        return current_bytes.decode('utf-16-le', errors='ignore')
    except Exception as e:
        print(f"Entity conversion error: {e}")
        return text

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
        "Click the button below to send your post. Custom emojis will be detected automatically!"
    )
    await message.answer(text, reply_markup=keyboard)

# Trigger posting flow
@dp.callback_query(F.data == "start_posting")
async def start_posting_cb(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PostState.waiting_for_post)
    await callback.message.answer(
        "<b>Send your post now!</b>\n\n"
        "Send your photo with caption (containing your premium custom emojis). I am waiting:"
    )
    await callback.answer()

# Receive post and auto-convert custom emojis to HTML
@dp.message(PostState.waiting_for_post)
async def receive_post_content(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id if message.photo else None
    raw_text = message.text or message.caption or ""
    entities = message.entities or message.caption_entities or []
    
    if not raw_text and not photo_id:
        await message.reply("❌ Please send a valid photo or text message!")
        return

    # Automatically convert text and custom emoji entities into HTML format
    converted_html_text = convert_entities_to_html(raw_text, entities)
    
    await state.update_data(
        photo_id=photo_id,
        html_text=converted_html_text,
        has_photo=bool(message.photo)
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Confirm & Broadcast to Channel", callback_data="confirm_broadcast")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_broadcast")]
    ])
    
    await message.reply(
        "<b>Post Preview Received & Processed!</b>\n\n"
        "Click below to publish this post directly to your channel with active custom emojis:",
        reply_markup=keyboard
    )

# Confirm and broadcast with active custom emojis
@dp.callback_query(F.data == "confirm_broadcast")
async def confirm_broadcast_cb(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    has_photo = data.get("has_photo")
    photo_id = data.get("photo_id")
    html_text = data.get("html_text")
    
    if not html_text and not photo_id:
        await callback.answer("No content found! Please start over with /start.", show_alert=True)
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
                caption=html_text,
                parse_mode=ParseMode.HTML,
                reply_markup=channel_keyboard
            )
        else:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=html_text,
                parse_mode=ParseMode.HTML,
                reply_markup=channel_keyboard
            )
        await callback.message.edit_text("✅ Post successfully broadcasted to your channel with active custom emojis and buttons!")
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
