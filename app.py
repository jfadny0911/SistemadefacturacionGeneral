from database.connection import get_connection
import streamlit as st

st.title("Prueba de conexión")

try:
    conn = get_connection()
    st.success("✅ Conectado correctamente a Neon")
    conn.close()

except Exception as e:
    st.error(e)
