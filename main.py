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

    for l in lots:
        lot_id, end_time, status = l

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

    for lot in lots:

        id, title, desc, price, blitz, step, seller, leader, end_time, status = lot

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
        <h1>Auction PRO</h1>
        {html}
        <script src="/static/app.js"></script>
    </body>
    </html>
    """


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
