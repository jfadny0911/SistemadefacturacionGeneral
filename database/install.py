import streamlit as st
from database.connection import get_connection
from auth.security import hash_password


def system_installed():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM companies")
    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return count > 0

    st.set_page_config(
        page_title="Instalación - PG Manager",
        page_icon="🚪",
        layout="centered"
    )

    st.title("🚪 Bienvenido a PG Manager")

    st.write(
        "Esta parece ser la primera vez que ejecuta el sistema."
    )

    st.divider()

    # ======================================================
    # EMPRESA
    # ======================================================

    st.subheader("🏢 Información de la empresa")

    company_name = st.text_input(
        "Nombre de la empresa *"
    )

    trade_name = st.text_input(
        "Nombre comercial"
    )

    company_email = st.text_input(
        "Correo electrónico"
    )

    phone = st.text_input(
        "Teléfono"
    )

    website = st.text_input(
        "Sitio web"
    )

    address = st.text_input(
        "Dirección"
    )

    col1, col2 = st.columns(2)

    with col1:

        city = st.text_input(
            "Ciudad"
        )

        country = st.text_input(
            "País",
            value="USA"
        )

    with col2:

        state = st.text_input(
            "Estado"
        )

        postal_code = st.text_input(
            "Código Postal"
        )

    tax_id = st.text_input(
        "Tax ID"
    )

    st.divider()

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    st.subheader("⚙ Configuración")

    col1, col2 = st.columns(2)

    with col1:

        currency = st.selectbox(
            "Moneda",
            [
                "USD",
                "EUR",
                "MXN",
                "CRC",
                "GTQ"
            ]
        )

    with col2:

        language = st.selectbox(
            "Idioma",
            [
                "Español",
                "English"
            ]
        )

    primary_color = st.color_picker(
        "Color principal",
        "#C8102E"
    )

    secondary_color = st.color_picker(
        "Color secundario",
        "#000000"
    )

    st.divider()

    # ======================================================
    # ADMINISTRADOR
    # ======================================================

    st.subheader("👤 Administrador")

    first_name = st.text_input(
        "Nombre *"
    )

    last_name = st.text_input(
        "Apellido *"
    )

    admin_email = st.text_input(
        "Correo del administrador *"
    )

    password = st.text_input(
        "Contraseña *",
        type="password"
    )

    confirm_password = st.text_input(
        "Confirmar contraseña *",
        type="password"
    )

    st.divider()

    # ======================================================
    # BOTÓN
    # ======================================================

    if st.button(
        "🚀 Instalar Sistema",
        use_container_width=True
    ):

        # ==========================
        # VALIDACIONES
        # ==========================

        if company_name == "":
            st.error("Ingrese el nombre de la empresa.")
            st.stop()

        if first_name == "":
            st.error("Ingrese el nombre del administrador.")
            st.stop()

        if admin_email == "":
            st.error("Ingrese el correo del administrador.")
            st.stop()

        if password == "":
            st.error("Ingrese una contraseña.")
            st.stop()

        if password != confirm_password:
            st.error("Las contraseñas no coinciden.")
            st.stop()

        # ==========================
        # CREAR EMPRESA
        # ==========================

        company_id = create_company(

            company_name=company_name,

            trade_name=trade_name,

            tax_id=tax_id,

            email=company_email,

            phone=phone,

            website=website,

            address=address,

            city=city,

            state=state,

            country=country,

            postal_code=postal_code,

            primary_color=primary_color,

            secondary_color=secondary_color,

            currency=currency,

            language=language

        )

        # ==========================
        # CREAR ADMIN
        # ==========================

        user = create_admin(

            company_id=company_id,

            first_name=first_name,

            last_name=last_name,

            email=admin_email,

            password=password

        )

        # ==========================
        # LOGIN AUTOMÁTICO
        # ==========================

        st.session_state.logged = True

        st.session_state.user_id = user["id"]

        st.session_state.company_id = company_id

        st.session_state.user_name = (
            first_name + " " + last_name
        )

        st.success("Sistema instalado correctamente.")

        st.rerun()
