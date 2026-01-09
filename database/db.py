# database/db.py

import sqlite3
from config import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
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


def add_search_history(user_id: int, query: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO search_history (user_id, query) VALUES (?, ?)",
        (user_id, query),
    )
    conn.commit()
    conn.close()


def get_search_history(user_id: int, limit: int = 10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT query, timestamp
        FROM search_history
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def add_favorite(user_id: int, video_id: str, title: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO favorites (user_id, video_id, title)
        VALUES (?, ?, ?)
        """,
        (user_id, video_id, title),
    )
    conn.commit()
    conn.close()


def get_favorites(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT video_id, title
        FROM favorites
        WHERE user_id = ?
        ORDER BY added_at DESC
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows
