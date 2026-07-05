from database.connection import get_connection
from auth.security import hash_password

conn = get_connection()

cursor = conn.cursor()

password = hash_password("Admin123")

cursor.execute(
    """
    INSERT INTO users
    (full_name,email,password_hash)

    VALUES (%s,%s,%s)
    """,
    (
        "Administrador",
        "admin@pgmanager.com",
        password
    )
)

conn.commit()

cursor.close()
conn.close()

print("Administrador creado correctamente")
