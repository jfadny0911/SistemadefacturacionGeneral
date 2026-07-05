import streamlit as st
from database.connection import get_connection

try:
    conn = get_connection()
    st.sidebar.success("✅ Conectado a Neon")
    conn.close()
except Exception as e:
    st.sidebar.error(f"❌ {e}")
