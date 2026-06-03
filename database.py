import sqlite3
import time

conn = sqlite3.connect("auction.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS lots(
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    title TEXT,
    description TEXT,

    current_price INTEGER,
    blitz_price INTEGER,

    seller TEXT,

    leader TEXT DEFAULT NULL,

    end_time INTEGER DEFAULT (strftime('%s','now') + 3600)
)
""")

conn.commit()