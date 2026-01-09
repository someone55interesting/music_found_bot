# handlers/history.py

from telegram import Update
from telegram.ext import ContextTypes

from database.db import get_search_history


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    history = get_search_history(user_id)

    if not history:
        await update.message.reply_text("🕒 История пуста.")
        return

    text = "🕒 Последние запросы:\n\n"
    for query, ts in history:
        text += f"• {query}\n"

    await update.message.reply_text(text)
