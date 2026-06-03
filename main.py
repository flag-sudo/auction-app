from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from database import cursor, conn
import time
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


# -------------------------
# PAYMENTS TABLE INIT (SAFE)
# -------------------------
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
# AUTO FINISH ENGINE
# -------------------------
def finish_engine():
    now = int(time.time())

    cursor.execute("SELECT id, end_time, status, leader FROM lots")
    lots = cursor.fetchall()

    for lot_id, end_time, status, leader in lots:

        if status == "active" and end_time and now > end_time:

            winner = leader if leader else "NO BIDS"

            cursor.execute("""
                UPDATE lots
                SET status='finished',
                    leader=?
                WHERE id=?
            """, (f"🏆 {winner}", lot_id))

    conn.commit()


# -------------------------
# HOME PAGE
# -------------------------
@app.get("/", response_class=HTMLResponse)
def home():

    finish_engine()
    now = int(time.time())

    cursor.execute("SELECT * FROM lots ORDER BY id DESC")
    lots = cursor.fetchall()

    html = ""

    for l in lots:

        id, title, desc, price, blitz, step, seller, leader, end_time, status = l

        if status == "finished":
            timer = "🏁 FINISHED"
        else:
            remaining = max(0, end_time - now)
            timer = f"⏱ {remaining//60}m {remaining%60}s"

        # 🔒 seller hidden
        seller_view = "🔒 hidden"

        html += f"""
        <div class="lot">

            <h2>{title}</h2>
            <p>{desc}</p>

            <div>💰 {price} грн</div>
            <div>⚡ {blitz} грн</div>
            <div>📈 step {step}</div>
            <div>👤 {seller_view}</div>
            <div>👑 {leader}</div>
            <div>{timer}</div>

            <button onclick="bid({id})">+ ставка</button>
            <button onclick="customBid({id})">своя цена</button>
            <button onclick="blitz({id})">blitz</button>

            <button onclick="unlock({id})">🔓 открыть продавца (20⭐)</button>

        </div>
        """

    return f"""
    <html>
    <head>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
    </head>

    <body>

        <h1>🏆 AUCTION COMMERCIAL v1</h1>

        <div class="create-box">

            <h3>Создать лот</h3>

            <input id="title" placeholder="Название">
            <input id="desc" placeholder="Описание">
            <input id="price" placeholder="Старт цена">
            <input id="blitz" placeholder="Блиц цена">
            <input id="step" placeholder="Шаг">
            <input id="time" placeholder="Минуты">

            <button onclick="createLot()">Создать</button>

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
    INSERT INTO lots(
        title, description, current_price,
        blitz_price, min_step,
        seller, leader, end_time, status
    )
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
    price, step, status = cursor.fetchone()

    if status != "active":
        return {"ok": False}

    new_price = price + step

    cursor.execute("""
        UPDATE lots
        SET current_price=?, leader=?
        WHERE id=?
    """, (new_price, user, lot_id))

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
    current = cursor.fetchone()[0]

    if value <= current:
        return {"ok": False}

    cursor.execute("""
        UPDATE lots
        SET current_price=?, leader=?
        WHERE id=?
    """, (value, user, lot_id))

    conn.commit()

    return {"ok": True}


# -------------------------
# BLITZ BUY
# -------------------------
@app.post("/blitz/{lot_id}")
async def blitz(lot_id: int, request: Request):

    data = await request.json()
    user = data["user"]

    cursor.execute("SELECT blitz_price FROM lots WHERE id=?", (lot_id,))
    price = cursor.fetchone()[0]

    cursor.execute("""
        UPDATE lots
        SET current_price=?, leader=?, status='finished'
        WHERE id=?
    """, (price, user, lot_id))

    conn.commit()

    return {"ok": True}


# -------------------------
# UNLOCK SELLER (COMMERCIAL CORE)
# -------------------------
@app.post("/unlock/{lot_id}")
async def unlock(lot_id: int, request: Request):

    data = await request.json()
    user = data["user"]

    cursor.execute("SELECT seller FROM lots WHERE id=?", (lot_id,))
    seller = cursor.fetchone()[0]

    # simulate payment (Stars later)
    cursor.execute("""
        INSERT INTO payments(user, lot_id, type, status, created_at)
        VALUES(?,?,?,?,?)
    """, (
        user,
        lot_id,
        "unlock_contact",
        "paid_mock",
        int(time.time())
    ))

    conn.commit()

    return {
        "ok": True,
        "seller": seller
    }


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
