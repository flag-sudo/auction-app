from database import cursor, conn

cursor.execute("""
INSERT INTO lots(
    title,
    description,
    current_price,
    blitz_price,
    seller
)
VALUES(?,?,?,?,?)
""", (
    "Logitech G Pro X",
    "Игровая мышка почти новая",
    500,
    1000,
    "@seller"
))

conn.commit()

print("Лот создан")