from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from database import cursor, conn
import time
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


# -------------------------
# ГЛАВНАЯ
# -------------------------
@app.get("/", response_class=HTMLResponse)
def home():

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
        seller = lot[5]
        leader = lot[6]
        end_time = lot[7]

        if end_time and now > end_time:
            status = "🏁 АУКЦИОН ЗАВЕРШЁН"
        elif end_time:
            remaining = end_time - now
            m = remaining // 60
            s = remaining % 60
            status = f"⏱ {m}м {s}с"
        else:
            status = "⏳ Без таймера"

        html += f"""
        <div class="lot">

            <div class="photo">📷 Фото товара</div>

            <h2>{title}</h2>
            <p>{desc}</p>

            <div class="info">

                <div>💰 Ставка: <b>{price} грн</b></div>
                <div>⚡ Блиц: <b>{blitz} грн</b></div>
                <div>👤 Продавец: <b>{seller}</b></div>
                <div>👑 Лидер: <b>{leader}</b></div>
                <div>{status}</div>

            </div>

            <div class="buttons">
                <button onclick="bid({lot_id}, this)">+50 грн</button>
            </div>

        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Auction</title>

        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <link rel="stylesheet" href="/static/style.css">
    </head>

    <body>

        <div class="header">
            <h1>🏆 Auction Store</h1>
        </div>

        <div class="container">
            {html}
        </div>

        <script src="/static/app.js"></script>

    </body>
    </html>
    """


# -------------------------
# СТАВКА
# -------------------------
@app.post("/bid/{lot_id}")
async def bid(lot_id: int, request: Request):

    data = await request.json()
    user = data.get("user", "unknown")

    cursor.execute("SELECT current_price, end_time FROM lots WHERE id=?", (lot_id,))
    lot = cursor.fetchone()

    if not lot:
        return {"ok": False}

    price = lot[0]
    end_time = lot[1]

    if end_time and time.time() > end_time:
        return {"ok": False}

    new_price = price + 50

    cursor.execute("""
        UPDATE lots
        SET current_price=?, leader=?
        WHERE id=?
    """, (new_price, user, lot_id))

    conn.commit()

    return {
        "ok": True,
        "price": new_price,
        "leader": user
    }


# -------------------------
# RUN (Render)
# -------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
