from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from database import cursor, conn
import time
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


# -------------------------
# CHECK FINISH
# -------------------------
def check_finish():
    now = int(time.time())

    cursor.execute("SELECT id, end_time, status FROM lots")
    lots = cursor.fetchall()

    for lot_id, end_time, status in lots:
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

    check_finish()
    now = int(time.time())

    cursor.execute("SELECT * FROM lots ORDER BY id DESC")
    lots = cursor.fetchall()

    html = ""

    for l in lots:

        id, title, desc, price, blitz, step, seller, leader, end_time, status = l

        if status == "finished":
            timer = "🏁 FINISHED"
        else:
            remaining = end_time - now
            timer = f"⏱ {remaining//60}m {remaining%60}s"

        html += f"""
        <div class="lot">

            <h2>{title}</h2>
            <p>{desc}</p>

            <div>💰 {price} грн</div>
            <div>⚡ {blitz} грн</div>
            <div>📈 step {step}</div>
            <div>👤 {seller}</div>
            <div>👑 {leader}</div>
            <div>{timer}</div>

            <button onclick="bid({id})">+ ставка</button>
            <button onclick="customBid({id})">своя цена</button>
            <button onclick="blitz({id})">blitz</button>

        </div>
        """

    return f"""
    <html>
    <head>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <link rel="stylesheet" href="/static/style.css">
    </head>

    <body>

        <h1>🏆 Auction PRO</h1>

        <div class="create-box">

            <h2>➕ Создать лот</h2>

            <input id="title" placeholder="Название">
            <input id="desc" placeholder="Описание">
            <input id="price" placeholder="Старт цена">
            <input id="blitz" placeholder="Блиц цена">
            <input id="step" placeholder="Шаг ставки">
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

    title = data["title"]
    desc = data["desc"]
    price = int(data["price"])
    blitz = int(data["blitz"])
    step = int(data["step"])
    minutes = int(data["time"])
    seller = data.get("seller", "user")

    end_time = int(time.time()) + minutes * 60

    cursor.execute("""
        INSERT INTO lots(title, description, current_price, blitz_price, min_step, seller, leader, end_time, status)
        VALUES(?,?,?,?,?,?,?,?, 'active')
    """, (
        title, desc, price, blitz, step, seller, "", end_time
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

    if status == "finished":
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
# BLITZ
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
# RUN
# -------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
