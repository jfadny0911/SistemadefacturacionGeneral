import streamlit as st


def dashboard_page():

    st.title("🏠 Dashboard")

    st.write(f"Bienvenido **{st.session_state.user_name}**")

    st.divider()

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("👥 Clientes", "0")

    with c2:
        st.metric("📦 Productos", "0")

    with c3:
        st.metric("🧾 Facturas", "0")

    c4, c5, c6 = st.columns(3)

    with c4:
        st.metric("💰 Ventas", "$0")

    with c5:
        st.metric("📄 Cotizaciones", "0")

    with c6:
        st.metric("📅 Agenda", "0")

    st.divider()

    st.subheader("Actividad reciente")

    st.info("Aún no hay actividad registrada.")
