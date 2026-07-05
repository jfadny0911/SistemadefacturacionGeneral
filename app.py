import streamlit as st

# =====================================================
# CONFIGURACIÓN
# =====================================================

st.set_page_config(
    page_title="PG Manager",
    page_icon="🚪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# IMPORTS
# =====================================================

from database.connection import get_connection
from database.install import system_installed

from auth.login import login
from auth.setup import setup_page

# Páginas
from pages.dashboard import dashboard_page
from pages.clientes import clientes_page
from pages.productos import productos_page
from pages.cotizaciones import cotizaciones_page
from pages.facturas import facturas_page
from pages.agenda import agenda_page
from pages.reportes import reportes_page
from pages.configuracion import configuracion_page

# =====================================================
# VERIFICAR CONEXIÓN
# =====================================================

try:
    conn = get_connection()
    conn.close()
except Exception as e:
    st.error(f"Error conectando con la base de datos.\n\n{e}")
    st.stop()

# =====================================================
# SESSION STATE
# =====================================================

if "logged" not in st.session_state:
    st.session_state.logged = False

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "company_id" not in st.session_state:
    st.session_state.company_id = None

# =====================================================
# PRIMERA INSTALACIÓN
# =====================================================

if not system_installed():

    setup_page()

    st.stop()

# =====================================================
# LOGIN
# =====================================================

if not st.session_state.logged:

    login()

    st.stop()

# =====================================================
# SIDEBAR
# =====================================================

try:
    st.sidebar.image("assets/logo.png", width=180)
except:
    pass

st.sidebar.title("PG Manager")

st.sidebar.success(f"👤 {st.session_state.user_name}")

st.sidebar.divider()

menu = st.sidebar.radio(
    "Menú",
    [
        "🏠 Dashboard",
        "👥 Clientes",
        "📦 Productos",
        "📄 Cotizaciones",
        "🧾 Facturas",
        "📅 Agenda",
        "📊 Reportes",
        "⚙ Configuración"
    ]
)

st.sidebar.divider()

if st.sidebar.button("🚪 Cerrar sesión", use_container_width=True):

    st.session_state.logged = False
    st.session_state.user_name = ""
    st.session_state.user_id = None
    st.session_state.company_id = None

    st.rerun()

# =====================================================
# ENRUTADOR
# =====================================================

if menu == "🏠 Dashboard":
    dashboard_page()

elif menu == "👥 Clientes":
    clientes_page()

elif menu == "📦 Productos":
    productos_page()

elif menu == "📄 Cotizaciones":
    cotizaciones_page()

elif menu == "🧾 Facturas":
    facturas_page()

elif menu == "📅 Agenda":
    agenda_page()

elif menu == "📊 Reportes":
    reportes_page()

elif menu == "⚙ Configuración":
    configuracion_page()
