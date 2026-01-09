# handlers/search.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.youtube_search import search_youtube
from database.db import add_search_history


async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    user_id = update.message.from_user.id

    add_search_history(user_id, query)

    await update.message.reply_text("🔍 Ищу музыку...")

    results = search_youtube(query)

    if not results:
        await update.message.reply_text("❌ Ничего не найдено.")
        return

    keyboard = []

    for item in results:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"🎵 {item['title'][:40]}",
                    callback_data=f"download:{item['id']}:{item['title']}",
                ),
                InlineKeyboardButton(
                    text="⭐",
                    callback_data=f"fav:{item['id']}:{item['title']}",
                ),
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎧 Вот что я нашёл:",
        reply_markup=reply_markup,
    )
