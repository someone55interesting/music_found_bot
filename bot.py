import logging
import os
import asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import yt_dlp

TOKEN = "8251495842:AAGhV8CiNltswmUmWSveZ4viaZd1xqaxjkk"

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ---------------- TEMP ----------------
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# ---------------- DB ----------------
DB_PATH = "bot.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        query TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        video_id TEXT,
        title TEXT,
        added_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def add_search_history(user_id, query):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO search_history (user_id, query) VALUES (?, ?)",
        (user_id, query)
    )
    conn.commit()
    conn.close()


def get_search_history(user_id, limit=10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT query FROM search_history WHERE user_id=? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]


def add_favorite(user_id, video_id, title):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO favorites (user_id, video_id, title) VALUES (?, ?, ?)",
        (user_id, video_id, title)
    )
    conn.commit()
    conn.close()


def get_favorites(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT video_id, title FROM favorites WHERE user_id=? ORDER BY added_at DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


# ---------------- SEARCH CACHE ----------------
SEARCH_CACHE = {}  # user_id -> list of tracks


# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 Привет! Я музыкальный бот.\n\n"
        "Напиши название трека для поиска.\n\n"
        "Команды:\n"
        "/history — история поиска\n"
        "/favorites — избранное"
    )


# ================== SEARCH ==================
async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    user_id = update.message.from_user.id

    add_search_history(user_id, query)

    await update.message.reply_text("🔍 Ищу музыку...")

    ydl_opts = {"quiet": True, "skip_download": True, "extract_flat": True}
    results = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search = ydl.extract_info(f"ytsearch5:{query}", download=False)
        if "entries" in search:
            for entry in search["entries"]:
                results.append({"title": entry["title"], "url": entry["url"]})

    if not results:
        await update.message.reply_text("❌ Ничего не найдено.")
        return

    SEARCH_CACHE[user_id] = results

    keyboard = []
    for i, track in enumerate(results):
        keyboard.append([
            InlineKeyboardButton(
                text=track["title"][:40],
                callback_data=f"track_{i}"
            ),
            InlineKeyboardButton(
                text="⭐",
                callback_data=f"fav_{i}"
            )
        ])

    await update.message.reply_text(
        "🎵 Выбери трек или добавь в избранное:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================== CALLBACK ==================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if user_id not in SEARCH_CACHE:
        await query.edit_message_text("⚠️ Время выбора истекло. Введи запрос снова.")
        return

    if data.startswith("track_"):
        index = int(data.split("_")[1])
        track = SEARCH_CACHE[user_id][index]

        await query.edit_message_text(f"⬇️ Скачиваю: {track['title']}")
        file_path = await download_track(track["url"])
        await context.bot.send_audio(
            chat_id=query.message.chat_id,
            audio=open(file_path, "rb"),
            title=track["title"]
        )
        os.remove(file_path)

    elif data.startswith("fav_"):
        index = int(data.split("_")[1])
        track = SEARCH_CACHE[user_id][index]
        add_favorite(user_id, track["url"], track["title"])
        await query.message.reply_text("⭐ Добавлено в избранное!")


# ================== DOWNLOAD ==================
async def download_track(url: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, sync_download, url)


def sync_download(url: str) -> str:
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": TEMP_DIR + "/%(title)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }],
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename.replace(".webm", ".mp3").replace(".m4a", ".mp3")


# ================== HISTORY COMMAND ==================
async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    history = get_search_history(user_id)
    if not history:
        await update.message.reply_text("🕒 История пуста.")
        return
    text = "🕒 Последние запросы:\n\n" + "\n".join(f"• {q}" for q in history)
    await update.message.reply_text(text)


# ================== FAVORITES COMMAND ==================
async def favorites_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    favorites = get_favorites(user_id)
    if not favorites:
        await update.message.reply_text("⭐ Избранное пусто.")
        return

    keyboard = []
    for url, title in favorites:
        keyboard.append([
            InlineKeyboardButton(
                text=title[:40],
                callback_data=f"track_fav_{url}"
            )
        ])

    await update.message.reply_text(
        "⭐ Твои избранные треки:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================== MAIN ==================
def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("favorites", favorites_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("🤖 Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
