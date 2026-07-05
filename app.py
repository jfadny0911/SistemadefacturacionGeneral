import streamlit as st

from pages.dashboard import dashboard_page
from pages.clientes import clientes_page
from pages.productos import productos_page
from pages.cotizaciones import cotizaciones_page
from pages.facturas import facturas_page
from pages.configuracion import configuracion_page
from pages.agenda import agenda_page
from pages.reportes import reportes_page

st.set_page_config(
    page_title="PG Manager",
    page_icon="🚪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- SIDEBAR ----------

st.sidebar.image("assets/logo.png", width=200)

st.sidebar.title("PG MANAGER")

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

# ---------- ROUTER ----------

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
