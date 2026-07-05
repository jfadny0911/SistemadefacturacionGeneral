import streamlit as st

from database.connection import get_connection
from auth.security import verify_password


def login():

    st.title("🔐 PG Manager")

    email = st.text_input("Correo")

    password = st.text_input(
        "Contraseña",
        type="password"
    )

    if st.button("Iniciar sesión"):

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute(
            """
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
WHERE email=%s
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user is None:
            st.error("Correo o contraseña incorrectos")
            return

        if not user[4]:
            st.error("Usuario inactivo")
            return

        if verify_password(password, user[3]):

            st.session_state.logged = True

            st.session_state.user_id = user[0]

            st.session_state.user_name = f"{user[1]} {user[2]}"

            st.rerun()

        else:

            st.error("Correo o contraseña incorrectos")
