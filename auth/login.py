import streamlit as st
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host=st.secrets["DB_HOST"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        database=st.secrets["DB_NAME"],
        port=int(st.secrets["DB_PORT"])
    )

def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        id,
        company_id,
        first_name,
        last_name,
        email,
        password_hash,
        active,
        user_type
    FROM users
    WHERE email = %s
    """

    cursor.execute(query, (email,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user

def login():
    st.title("Inicio de sesión")

    email = st.text_input("Correo electrónico")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        user = get_user_by_email(email)

        if user:
            st.success("Usuario encontrado")
            st.session_state["user"] = user
            st.session_state["logged_in"] = True
        else:
            st.error("Correo o contraseña incorrectos")
