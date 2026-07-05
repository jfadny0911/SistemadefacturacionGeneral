import streamlit as st

# ==============================
# CONFIGURACIÓN DE LA PÁGINA
# ==============================

st.set_page_config(
    page_title="PG Manager",
    page_icon="🚪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# IMPORTACIONES
# ==============================

from auth.login import login
from database.connection import get_connection

from pages.dashboard import dashboard_page
from pages.clientes import clientes_page
from pages.productos import productos_page
from pages.cotizaciones import cotizaciones_page
from pages.facturas import facturas_page
from pages.configuracion import configuracion_page
from pages.agenda import agenda_page
from pages.reportes import reportes_page

# ==============================
# VERIFICAR CONEXIÓN
# ==============================

try:
    conn = get_connection()
    conn.close()
except Exception as e:
    st.error(f"❌ Error de conexión con la base de datos:\n\n{e}")
    st.stop()

# ==============================
# SESIÓN
# ==============================

if "logged" not in st.session_state:
    st.session_state.logged = False

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# ==============================
# LOGIN
# ==============================

if not st.session_state.logged:
    login()
    st.stop()

# ==============================
# SIDEBAR
# ==============================

st.sidebar.image("assets/logo.png", width=180)

st.sidebar.title("PG Manager")

st.sidebar.write(f"👤 **{st.session_state.user_name}**")

st.sidebar.divider()

menu = st.sidebar.radio(
    "Menú",
    (
        "Dashboard",
        "Clientes",
        "Productos",
        "Cotizaciones",
        "Facturas",
        "Agenda",
        "Reportes",
        "Configuración",
    )
)

st.sidebar.divider()

if st.sidebar.button("🚪 Cerrar sesión"):

    st.session_state.logged = False
    st.session_state.user_name = ""
    st.session_state.user_id = None

    st.rerun()

# ==============================
# ENRUTADOR
# ==============================

if menu == "Dashboard":
    dashboard_page()

elif menu == "Clientes":
    clientes_page()

elif menu == "Productos":
    productos_page()

elif menu == "Cotizaciones":
    cotizaciones_page()

elif menu == "Facturas":
    facturas_page()

elif menu == "Agenda":
    agenda_page()

elif menu == "Reportes":
    reportes_page()

elif menu == "Configuración":
    configuracion_page()
