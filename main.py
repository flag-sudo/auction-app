from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import time
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------
# DB
# -------------------------
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
    status TEXT DEFAULT 'active'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS payments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    lot_id INTEGER,
    type TEXT,
    status TEXT,
    created_at INTEGER
)
""")

conn.commit()


# -------------------------
# FINISH ENGINE
# -------------------------
def finish_engine():
    now = int(time.time())

    cursor.execute("SELECT id, end_time, status FROM lots")
    for row in cursor.fetchall():
        lot_id, end_time, status = row

        if status == "active" and end_time and now > end_time:
            cursor.execute("""
                UPDATE lots
                SET status='finished'
                WHERE id=?
            """, (lot_id,))

    conn.commit()


# -------------------------
# HOME
# -------------------------
@app.get("/", response_class=HTMLResponse)
def home():

    finish_engine()
    now = int(time.time())

    cursor.execute("SELECT * FROM lots ORDER BY id DESC")
    lots = cursor.fetchall()

    html = ""

    for l in lots:

        # 🔥 SAFE INDEX (NO UNPACK CRASH)
        id = l[0]
        title = l[1]
        desc = l[2]
        price = l[3]
        blitz = l[4]
        step = l[5]
        seller = l[6]
        leader = l[7]
        end_time = l[8]
        status = l[9]

        if status == "finished":
            timer = "🏁 FINISHED"
        else:
            remaining = max(0, end_time - now)
            timer = f"⏱ {remaining//60}m {remaining%60}s"

        html += f"""
        <div class="lot">

            <h2>{title}</h2>
            <p>{desc}</p>

            <div>💰 {price} грн</div>
            <div>⚡ {blitz} грн</div>
            <div>📈 step {step}</div>
            <div>👤 🔒 seller hidden</div>
            <div>👑 {leader}</div>
            <div>{timer}</div>

            <button onclick="bid({id})">+ ставка</button>
            <button onclick="customBid({id})">своя цена</button>
            <button onclick="blitz({id})">blitz</button>
            <button onclick="unlock({id})">🔓 unlock (20⭐)</button>

        </div>
        """

    return f"""
    <html>
    <head>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
    </head>
    <body>

        <h1>🏆 Auction PRO FINAL</h1>

        <div class="create-box">

            <h3>Create lot</h3>

            <input id="title" placeholder="title">
            <input id="desc" placeholder="desc">
            <input id="price" placeholder="price">
            <input id="blitz" placeholder="blitz">
            <input id="step" placeholder="step">
            <input id="time" placeholder="minutes">

            <button onclick="createLot()">create</button>

        </div>

        <hr>

        {html}

        <script src="/static/app.js"></script>
    </body>
    </html>
    """


# -------------------------
# CREATE LOT
# -------------------------
@app.post("/create_lot")
async def create_lot(request: Request):

    data = await request.json()

    cursor.execute("""
        INSERT INTO lots(title, description, current_price, blitz_price, min_step, seller, leader, end_time, status)
        VALUES(?,?,?,?,?,?,?,?,?)
    """, (
        data["title"],
        data["desc"],
        int(data["price"]),
        int(data["blitz"]),
        int(data["step"]),
        data["seller"],
        "",
        int(time.time()) + int(data["time"]) * 60,
        "active"
    ))

    conn.commit()

    return {"ok": True}


# -------------------------
# BID
# -------------------------
@app.post("/bid/{lot_id}")
async def bid(lot_id: int, request: Request):

    data = await request.json()
    user = data["user"]

    cursor.execute("SELECT current_price, min_step, status FROM lots WHERE id=?", (lot_id,))
    row = cursor.fetchone()

    if not row:
        return {"ok": False}

    price, step, status = row

    if status != "active":
        return {"ok": False}

    cursor.execute("""
        UPDATE lots
        SET current_price = current_price + min_step,
            leader = ?
        WHERE id=?
    """, (user, lot_id))

    conn.commit()

    return {"ok": True}


# -------------------------
# CUSTOM BID
# -------------------------
@app.post("/custom_bid/{lot_id}")
async def custom_bid(lot_id: int, request: Request):

    data = await request.json()
    user = data["user"]
    value = data["value"]

    cursor.execute("SELECT current_price FROM lots WHERE id=?", (lot_id,))
    current = cursor.fetchone()

    if not current:
        return {"ok": False}

    if value <= current[0]:
        return {"ok": False}

    cursor.execute("""
        UPDATE lots
        SET current_price=?, leader=?
        WHERE id=?
    """, (value, user, lot_id))

    conn.commit()

    return {"ok": True}


# -------------------------
# BLITZ
# -------------------------
@app.post("/blitz/{lot_id}")
async def blitz(lot_id: int, request: Request):

    data = await request.json()
    user = data["user"]

    cursor.execute("SELECT blitz_price FROM lots WHERE id=?", (lot_id,))
    row = cursor.fetchone()

    if not row:
        return {"ok": False}

    price = row[0]

    cursor.execute("""
        UPDATE lots
        SET current_price=?, leader=?, status='finished'
        WHERE id=?
    """, (price, user, lot_id))

    conn.commit()

    return {"ok": True}


# -------------------------
# UNLOCK CONTACT (MVP COMMERCIAL)
# -------------------------
@app.post("/unlock/{lot_id}")
async def unlock(lot_id: int, request: Request):

    data = await request.json()
    user = data["user"]

    cursor.execute("SELECT seller FROM lots WHERE id=?", (lot_id,))
    row = cursor.fetchone()

    if not row:
        return {"ok": False}

    seller = row[0]

    cursor.execute("""
        INSERT INTO payments(user, lot_id, type, status, created_at)
        VALUES(?,?,?,?,?)
    """, (user, lot_id, "unlock", "paid_mock", int(time.time())))

    conn.commit()

    return {"ok": True, "seller": seller}


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
