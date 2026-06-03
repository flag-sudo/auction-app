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
    leader TEXT,
    end_time INTEGER
)
""")

conn.commit()


# -------------------------
# АВТО-СОЗДАНИЕ ЛОТА ЕСЛИ ПУСТО
# -------------------------
cursor.execute("SELECT COUNT(*) FROM lots")
count = cursor.fetchone()[0]

if count == 0:
    cursor.execute("""
    INSERT INTO lots(title, description, current_price, blitz_price, seller, leader, end_time)
    VALUES(?,?,?,?,?,?,?)
    """, (
        "Test iPhone 14",
        "Почти новый телефон",
        500,
        1000,
        "@seller",
        "",
        int(time.time()) + 3600
    ))

    conn.commit()
