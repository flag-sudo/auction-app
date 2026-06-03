from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from database import cursor, conn
import time
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


# -------------------------
# ПРОВЕРКА ЗАВЕРШЕНИЯ
# -------------------------
def finish_check():
    now = int(time.time())

    cursor.execute("SELECT id, end_time, leader, status FROM lots")
    lots = cursor.fetchall()

    for l in lots:
        lot_id = l[0]
        end_time = l[1]
        leader = l[2]
        status = l[3]

        if status == "active" and end_time and now > end_time:

            winner = leader if leader else "нет ставок"

            cursor.execute("""
                UPDATE lots
                SET status='finished',
                    leader=?
                WHERE id=?
            """, (f"🏁 {winner}", lot_id))

    conn.commit()


# -------------------------
# HOME
# -------------------------
@app.get("/", response_class=HTMLResponse)
def home():

    finish_check()

    now = int(time.time())

    cursor.execute("SELECT * FROM lots ORDER BY id DESC")
    lots = cursor.fetchall()

    html = ""

    for lot in lots:

        lot_id = lot[0]
        title = lot[1]
        desc = lot[2]
        price = lot[3]
        blitz = lot[4]
        step = lot[5]
        seller = lot[6]
        leader = lot[7]
        end_time = lot[8]
        status = lot[9]

        if status == "finished":
            time_text = "🏁 Завершён"
        else:
            remaining = end_time - now
            m = remaining // 60
            s = remaining % 60
            time_text = f"⏱ {m}м {s}с"

        html += f"""
        <div class="lot">

            <div class="photo">📷 ITEM</div>

            <h2>{title}</h2>
            <p>{desc}</p>

            <div class="info">

                <div>💰 Цена: <b>{price} грн</b></div>
                <div>⚡ Блиц: <b>{blitz} грн</b></div>
                <div>📈 Шаг: <b>{step} грн</b></div>
                <div>👤 Продавец: {seller}</div>
                <div>👑 Лидер: {leader}</div>
                <div>{time_text}</div>

            </div>

            <div class="buttons">
                <button onclick="bid({lot_id}, {step})">Сделать ставку</button>
                <button onclick="blitz({lot_id})">⚡ Блиц</button>
            </div>

        </div>
        """

    return f"""
    <html>
    <head>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <h1>🏆 PRO Auction</h1>
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
    user = data.get("user", "anon")

    cursor.execute("SELECT current_price, min_step, blitz_price, end_time, status FROM lots WHERE id=?",
                   (lot_id,))
    lot = cursor.fetchone()

    if not lot:
        return {"ok": False}

    price, step, blitz, end_time, status = lot

    if status == "finished":
        return {"ok": False}

    new_price = price + step

    now = int(time.time())

    # AUTO +5 min если ставка в конце
    if end_time - now < 120:
        end_time += 300

    cursor.execute("""
        UPDATE lots
        SET current_price=?,
            leader=?,
            end_time=?
        WHERE id=?
    """, (new_price, user, end_time, lot_id))

    conn.commit()

    return {"ok": True, "price": new_price, "leader": user}


# -------------------------
# BLITZ
# -------------------------
@app.post("/blitz/{lot_id}")
async def blitz(lot_id: int, request: Request):

    data = await request.json()
    user = data.get("user", "anon")

    cursor.execute("SELECT blitz_price FROM lots WHERE id=?", (lot_id,))
    blitz_price = cursor.fetchone()[0]

    cursor.execute("""
        UPDATE lots
        SET current_price=?,
            leader=?,
            status='finished'
        WHERE id=?
    """, (blitz_price, user, lot_id))

    conn.commit()

    return {"ok": True, "winner": user}


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
