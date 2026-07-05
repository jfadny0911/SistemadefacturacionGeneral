import streamlit as st
from database.connection import get_connection

def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()

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
        if not email or not password:
            st.warning("Ingrese correo y contraseña")
            return

        user = get_user_by_email(email)

        if user:
            st.success("Usuario encontrado")
            st.session_state["logged_in"] = True
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error("Correo o contraseña incorrectos")
