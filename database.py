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
    min_step INTEGER,
    seller TEXT,
    leader TEXT,
    end_time INTEGER,
    status TEXT DEFAULT 'active',
    contact_locked INTEGER DEFAULT 1
)
""")
conn.commit()


# авто-лот
cursor.execute("SELECT COUNT(*) FROM lots")
count = cursor.fetchone()[0]

if count == 0:
    cursor.execute("""
    INSERT INTO lots(title, description, current_price, blitz_price, min_step, seller, leader, end_time)
    VALUES(?,?,?,?,?,?,?,?)
    """, (
        "iPhone 14 Pro",
        "Почти новый, без царапин",
        500,
        1200,
        50,
        "@seller",
        "",
        int(time.time()) + 3600
    ))

    conn.commit()
