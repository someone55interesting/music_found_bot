# handlers/favorites.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.db import get_favorites


async def favorites_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    favorites = get_favorites(user_id)

    if not favorites:
        await update.message.reply_text("⭐ Избранное пусто.")
        return

    keyboard = []
    for video_id, title in favorites:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"🎵 {title[:40]}",
                    callback_data=f"download:{video_id}:{title}",
                )
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "⭐ Твои избранные треки:",
        reply_markup=reply_markup,
    )
