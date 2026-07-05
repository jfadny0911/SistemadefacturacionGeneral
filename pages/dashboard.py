import streamlit as st

def dashboard_page():

    st.title("🏠 Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Ventas", "$0.00")
    col2.metric("Facturas", "0")
    col3.metric("Clientes", "0")
    col4.metric("Productos", "0")

    st.divider()

    st.info("Bienvenido a PG Manager")
