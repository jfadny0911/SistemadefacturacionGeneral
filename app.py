import streamlit as st
from fpdf import FPDF
from datetime import datetime
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import base64
import tempfile
import os
import bcrypt


# =========================
# CONFIGURACIÓN DE PÁGINA
# =========================
st.set_page_config(
    page_title="Peralta's Garage Doors | Sistema de Facturación",
    layout="wide"
)

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)


# =========================
# CONEXIÓN A NEON
# =========================
conn = st.connection("postgresql", type="sql")


# =========================
# FUNCIONES AUXILIARES
# =========================
def safe_text(value):
    if value is None:
        return ""
    return str(value).encode("latin-1", "replace").decode("latin-1")


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def save_uploaded_logo(uploaded_logo):
    if uploaded_logo is None:
        return None

    suffix = os.path.splitext(uploaded_logo.name)[1].lower()

    if suffix not in [".png", ".jpg", ".jpeg"]:
        st.warning("Please upload a PNG or JPG logo.")
        return None

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.write(uploaded_logo.read())
    temp_file.close()

    return temp_file.name


# =========================
# BASE DE DATOS
# =========================
def init_db():
    try:
        with conn.session as session:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS peralta_invoices (
                    id SERIAL PRIMARY KEY,
                    inv_num VARCHAR(100) NOT NULL,
                    cliente VARCHAR(255) NOT NULL,
                    project_addr TEXT,
                    total_amount NUMERIC(12, 2) DEFAULT 0,
                    fecha_hoy VARCHAR(50),
                    due_date VARCHAR(50),
                    business_name VARCHAR(255) DEFAULT 'Peralta''s Garage Doors',
                    business_phone VARCHAR(50) DEFAULT '832-752-0930',
                    business_description TEXT DEFAULT 'Residencial y Comercial - Instalacion y Reparacion de Garajes y Motores - Espanol',
                    status VARCHAR(50) DEFAULT 'Paid',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            session.execute(text("""
                CREATE TABLE IF NOT EXISTS peralta_invoice_items (
                    id SERIAL PRIMARY KEY,
                    invoice_id INTEGER NOT NULL REFERENCES peralta_invoices(id) ON DELETE CASCADE,
                    description TEXT NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    unit_price NUMERIC(12, 2) NOT NULL DEFAULT 0
                )
            """))

            session.execute(text("""
                CREATE TABLE IF NOT EXISTS peralta_users (
                    id SERIAL PRIMARY KEY,
                    full_name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    active BOOLEAN DEFAULT TRUE,
                    role VARCHAR(50) DEFAULT 'admin',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            session.commit()

    except OperationalError:
        st.error("Error de conexión con la base de datos. Reinicia la app desde Streamlit Cloud.")
        st.stop()

    except Exception as e:
        st.error(f"Error inicializando la base de datos: {e}")
        st.stop()


# =========================
# LOGIN / USUARIOS
# =========================
def hash_password(password):
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(password, password_hash):
    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8")
    )


def create_default_admin():
    default_email = "admin@peraltasgarage.com"
    default_password = "123456"

    try:
        with conn.session as session:
            result = session.execute(
                text("""
                    SELECT id
                    FROM peralta_users
                    WHERE email = :email
                """),
                {"email": default_email}
            )

            user_exists = result.fetchone()

            if not user_exists:
                password_hash = hash_password(default_password)

                session.execute(
                    text("""
                        INSERT INTO peralta_users
                            (full_name, email, password_hash, active, role)
                        VALUES
                            (:full_name, :email, :password_hash, TRUE, 'admin')
                    """),
                    {
                        "full_name": "Administrador",
                        "email": default_email,
                        "password_hash": password_hash
                    }
                )

                session.commit()

    except Exception as e:
        st.error(f"Error creando usuario administrador: {e}")
        st.stop()


def get_user_by_email(email):
    with conn.session as session:
        result = session.execute(
            text("""
                SELECT
                    id,
                    full_name,
                    email,
                    password_hash,
                    active,
                    role
                FROM peralta_users
                WHERE email = :email
            """),
            {"email": email}
        )

        user = result.fetchone()

    if user:
        return dict(user._mapping)

    return None


def login_screen():
    st.markdown("""
        <style>
            .login-box {
                max-width: 430px;
                margin: auto;
                padding-top: 70px;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-box">', unsafe_allow_html=True)

    st.title("🔐 Login")
    st.subheader("Peralta's Garage Doors System")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Ingresar", use_container_width=True):
        if not email.strip() or not password.strip():
            st.warning("Ingrese email y contraseña.")
            st.stop()

        user = get_user_by_email(email.strip().lower())

        if not user:
            st.error("Usuario o contraseña incorrectos.")
            st.stop()

        if not user["active"]:
            st.error("Este usuario está desactivado.")
            st.stop()

        if verify_password(password, user["password_hash"]):
            st.session_state["logged_in"] = True
            st.session_state["user"] = {
                "id": user["id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"]
            }
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

    st.info("Usuario inicial: admin@peraltasgarage.com | Password: 123456")

    st.markdown('</div>', unsafe_allow_html=True)


def logout_button():
    with st.sidebar:
        user = st.session_state.get("user", {})
        st.write(f"👤 **{user.get('full_name', 'Usuario')}**")
        st.caption(f"Rol: {user.get('role', '')}")

        if st.button("🚪 Cerrar sesión"):
            st.session_state["logged_in"] = False
            st.session_state["user"] = None
            st.rerun()

        st.markdown("---")


# =========================
# INICIALIZAR DB Y LOGIN
# =========================
init_db()
create_default_admin()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_screen()
    st.stop()


# =========================
# NÚMERO AUTOMÁTICO
# =========================
def get_next_invoice_number():
    try:
        with conn.session as session:
            result = session.execute(
                text("""
                    SELECT COALESCE(MAX(id), 0) + 1 AS next_id
                    FROM peralta_invoices
                """)
            )
            next_id = result.fetchone()[0]

        return f"PGD-{int(next_id):04d}"

    except Exception:
        return "PGD-0001"


# =========================
# ESTADOS
# =========================
if "address_rows" not in st.session_state:
    st.session_state.address_rows = [""]

if "service_rows" not in st.session_state:
    st.session_state.service_rows = [
        {"desc": "", "qty": 1, "price": 0.0}
    ]


# =========================
# CLASE PDF
# =========================
class ModernInvoice(FPDF):

    def draw_header(self, data):
        self.azul = data["primary_color"]
        self.rojo = data["accent_color"]
        self.amarillo = data["highlight_color"]
        self.gris = (245, 245, 245)

        language = data.get("language", "English")

        if language == "Español":
            invoice_text = "FACTURA"
            invoice_no_text = "Factura No:"
            date_text = "Fecha:"
            due_date_text = "Vence:"
            invoice_to_text = "FACTURADO A:"
            business_info_text = "INFORMACIÓN"
            phone_text = "Tel:"
            payable_text = "Pagar a:"
        else:
            invoice_text = "INVOICE"
            invoice_no_text = "Invoice No:"
            date_text = "Date:"
            due_date_text = "Due Date:"
            invoice_to_text = "INVOICE TO:"
            business_info_text = "BUSINESS INFO"
            phone_text = "Tel:"
            payable_text = "Payable to:"

        self.set_fill_color(*self.azul)
        self.rect(0, 0, 210, 50, "F")

        self.set_fill_color(*self.rojo)
        self.rect(0, 0, 210, 3, "F")

        logo_path = data.get("logo_path")
        text_start_x = 10

        if logo_path and os.path.exists(logo_path):
            try:
                self.image(logo_path, 10, 7, 30)
                text_start_x = 45
            except Exception:
                text_start_x = 10

        self.set_xy(text_start_x, 8)
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(255, 255, 255)
        self.cell(100, 8, safe_text(data["business_name"]), ln=True)

        self.set_x(text_start_x)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*self.amarillo)
        self.cell(100, 6, safe_text(data["business_subtitle"]), ln=True)

        self.set_x(text_start_x)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(230, 230, 230)
        self.multi_cell(
            95,
            5,
            safe_text(data["business_description"]),
            align="L"
        )

        self.set_x(text_start_x)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(255, 255, 255)
        self.cell(100, 6, f"{phone_text} {safe_text(data['phone'])}", ln=True)

        self.set_xy(122, 10)
        self.set_font("Helvetica", "B", 32)
        self.set_text_color(*self.amarillo)
        self.cell(78, 14, invoice_text, align="R")

        self.set_text_color(255, 255, 255)

        self.set_xy(125, 28)
        self.set_font("Helvetica", "", 10)
        self.cell(32, 5, invoice_no_text)
        self.set_font("Helvetica", "B", 10)
        self.cell(43, 5, f"#{safe_text(data['inv_num'])}", align="R", ln=True)

        self.set_xy(125, 34)
        self.set_font("Helvetica", "", 10)
        self.cell(32, 5, date_text)
        self.set_font("Helvetica", "B", 10)
        self.cell(43, 5, safe_text(data["date"]), align="R", ln=True)

        self.set_xy(125, 40)
        self.set_font("Helvetica", "", 10)
        self.cell(32, 5, due_date_text)
        self.set_font("Helvetica", "B", 10)
        self.cell(43, 5, safe_text(data["due_date"]), align="R", ln=True)

        self.set_fill_color(*self.amarillo)
        self.rect(0, 50, 210, 5, "F")

        self.set_xy(12, 64)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*self.rojo)
        self.cell(80, 6, invoice_to_text, ln=True)

        self.set_x(12)
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(*self.azul)
        self.cell(100, 7, safe_text(data["client_name"]).upper(), ln=True)

        self.set_x(12)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(95, 5, safe_text(data["project_addr"]), align="L")

        self.set_xy(125, 64)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*self.azul)
        self.cell(75, 6, business_info_text, ln=True)

        self.set_draw_color(*self.rojo)
        self.line(125, 71, 175, 71)

        self.set_xy(125, 75)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(
            75,
            5,
            safe_text(
                f"{payable_text} {data['payable_to']}\n"
                f"{phone_text} {data['phone']}"
            ),
            align="L"
        )


# =========================
# GENERAR PDF
# =========================
def generate_pdf(data, services, addresses):
    language = data.get("language", "English")

    if language == "Español":
        columns = [
            {"name": "DESCRIPCIÓN", "w": 100},
            {"name": "PRECIO", "w": 35},
            {"name": "CANT.", "w": 20},
            {"name": "TOTAL", "w": 35}
        ]
        terms_title = "TÉRMINOS Y CONDICIONES"
        terms_text = (
            "Gracias por su preferencia.\n"
            "El pago debe realizarse según la fecha indicada en esta factura.\n"
            "Las condiciones de garantía pueden variar según el tipo de instalación o reparación."
        )
        subtotal_label = "Sub-total:"
        tax_label = "Impuesto:"
        total_label = "Total:"
        signature_label = "Administrador"
    else:
        columns = [
            {"name": "DESCRIPTION", "w": 100},
            {"name": "UNIT PRICE", "w": 35},
            {"name": "QTY", "w": 20},
            {"name": "TOTAL", "w": 35}
        ]
        terms_title = "TERMS AND CONDITIONS"
        terms_text = (
            "Thank you for your business.\n"
            "Payment is due according to the date listed on this invoice.\n"
            "Warranty and service conditions may vary depending on the type of installation or repair."
        )
        subtotal_label = "Sub-total:"
        tax_label = "Tax:"
        total_label = "Total:"
        signature_label = "Administrator"

    project_addr_str = "\n".join(
        [safe_text(a) for a in addresses if str(a).strip()]
    )

    pdf = ModernInvoice()
    pdf.add_page()

    header_data = data.copy()
    header_data["project_addr"] = project_addr_str

    pdf.draw_header(header_data)

    pdf.set_y(100)

    pdf.set_fill_color(*pdf.azul)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(255, 255, 255)

    current_x = 10

    for col in columns:
        align = "L" if col["name"] in ["DESCRIPTION", "DESCRIPCIÓN"] else "C"
        pdf.set_xy(current_x, 100)
        pdf.cell(col["w"], 10, safe_text(col["name"]), fill=True, align=align)
        current_x += col["w"]

    total_general = 0
    current_y = 110

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.set_draw_color(210, 210, 210)

    for service in services:
        desc = safe_text(service["desc"]).strip()
        qty = int(service["qty"])
        price = float(service["price"])

        if not desc:
            continue

        line_total = qty * price
        total_general += line_total

        values = [
            desc,
            f"${price:,.2f}",
            str(qty),
            f"${line_total:,.2f}"
        ]

        current_x = 10

        for index, col in enumerate(columns):
            align = "L" if index == 0 else "C"
            pdf.set_xy(current_x, current_y)
            pdf.cell(col["w"], 9, safe_text(values[index]), border="B", align=align)
            current_x += col["w"]

        current_y += 9

        if current_y > 235:
            pdf.add_page()
            current_y = 20

    totals_x = 115
    totals_y = current_y + 12

    pdf.set_fill_color(*pdf.gris)
    pdf.rect(totals_x, totals_y, 85, 28, "F")

    pdf.set_xy(totals_x, totals_y + 4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(40, 7, subtotal_label, align="R")
    pdf.cell(40, 7, f"${total_general:,.2f}", align="R", ln=True)

    pdf.set_x(totals_x)
    pdf.cell(40, 7, tax_label, align="R")
    pdf.cell(40, 7, "$0.00", align="R", ln=True)

    pdf.set_fill_color(*pdf.azul)
    pdf.rect(totals_x, totals_y + 28, 85, 14, "F")

    pdf.set_xy(totals_x, totals_y + 29)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(40, 12, total_label, align="R")
    pdf.cell(40, 12, f"${total_general:,.2f}", align="R")

    pdf.set_xy(10, totals_y)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*pdf.azul)
    pdf.cell(90, 7, safe_text(terms_title), ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(95, 5, safe_text(terms_text))

    pdf.set_y(250)
    pdf.set_font("Times", "BI", 16)
    pdf.set_text_color(*pdf.azul)
    pdf.cell(0, 8, safe_text(data["business_name"]), align="R", ln=True)

    pdf.set_draw_color(*pdf.azul)
    pdf.line(130, 262, 200, 262)

    pdf.set_xy(130, 264)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(70, 5, safe_text(signature_label), align="C")

    pdf.set_fill_color(*pdf.azul)
    pdf.rect(0, 282, 210, 15, "F")

    pdf.set_fill_color(*pdf.rojo)
    pdf.rect(0, 279, 90, 3, "F")
    pdf.rect(165, 279, 45, 3, "F")

    output = pdf.output(dest="S")

    if isinstance(output, str):
        return output.encode("latin-1")

    return bytes(output)


# =========================
# MOSTRAR PDF
# =========================
def display_pdf(pdf_bytes):
    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    pdf_display = f"""
        data:application/pdf;base64,{base64_pdf}
    """
    st.markdown(pdf_display, unsafe_allow_html=True)


# =========================
# INTERFAZ PRINCIPAL
# =========================
st.title("🛠️ Peralta's Garage Doors System")

logout_button()

with st.sidebar:
    st.header("⚙️ Business Info")

    uploaded_logo = st.file_uploader(
        "Upload Logo",
        type=["png", "jpg", "jpeg"]
    )

    logo_path = save_uploaded_logo(uploaded_logo)

    my_business = st.text_input(
        "Business Name",
        "Peralta's Garage Doors"
    )

    my_subtitle = st.text_input(
        "Business Subtitle",
        "RESIDENCIAL Y COMERCIAL"
    )

    my_phone = st.text_input(
        "Phone",
        "832-752-0930"
    )

    my_description = st.text_area(
        "Business Description",
        "Instalacion y Reparacion de Garajes y Motores\nEspanol"
    )

    my_payable = st.text_input(
        "Payable to",
        "Peralta's Garage Doors"
    )

    st.markdown("---")
    st.header("🎨 PDF Design")

    pdf_language = st.selectbox(
        "PDF Language",
        ["English", "Español"]
    )

    primary_hex = st.color_picker(
        "Primary Color",
        "#14325A"
    )

    accent_hex = st.color_picker(
        "Accent Color",
        "#BE1423"
    )

    highlight_hex = st.color_picker(
        "Highlight Color",
        "#F5CD46"
    )

    primary_color = hex_to_rgb(primary_hex)
    accent_color = hex_to_rgb(accent_hex)
    highlight_color = hex_to_rgb(highlight_hex)


tab1, tab2 = st.tabs(["🆕 Create Invoice", "📜 Invoice History"])


# =========================
# TAB 1 - CREAR FACTURA
# =========================
with tab1:
    st.subheader("👤 Invoice & Client Details")

    c1, c2, c3 = st.columns([1, 2, 1])

    inv_no = get_next_invoice_number()

    c1.text_input(
        "Invoice #",
        value=inv_no,
        disabled=True
    )

    c_name = c2.text_input("Client Name")
    due_d = c3.date_input("Due Date")

    st.subheader("📍 Project Addresses")

    for i, addr in enumerate(st.session_state.address_rows):
        col_in, col_del = st.columns([0.9, 0.1])

        st.session_state.address_rows[i] = col_in.text_input(
            f"Address {i + 1}",
            value=addr,
            key=f"addr_{i}"
        )

        if col_del.button("🗑️", key=f"del_a_{i}"):
            st.session_state.address_rows.pop(i)

            if len(st.session_state.address_rows) == 0:
                st.session_state.address_rows.append("")

            st.rerun()

    if st.button("➕ Add Address"):
        st.session_state.address_rows.append("")
        st.rerun()

    st.subheader("📦 Services")

    current_total = 0

    for i, serv in enumerate(st.session_state.service_rows):
        d, q, p, x = st.columns([0.5, 0.15, 0.25, 0.1])

        st.session_state.service_rows[i]["desc"] = d.text_input(
            "Description",
            value=serv["desc"],
            key=f"d_{i}"
        )

        st.session_state.service_rows[i]["qty"] = q.number_input(
            "Qty",
            min_value=1,
            value=int(serv["qty"]),
            step=1,
            key=f"q_{i}"
        )

        st.session_state.service_rows[i]["price"] = p.number_input(
            "Price",
            min_value=0.0,
            value=float(serv["price"]),
            step=1.0,
            key=f"p_{i}"
        )

        current_total += (
            st.session_state.service_rows[i]["qty"]
            * st.session_state.service_rows[i]["price"]
        )

        if x.button("🗑️", key=f"del_s_{i}"):
            st.session_state.service_rows.pop(i)

            if len(st.session_state.service_rows) == 0:
                st.session_state.service_rows.append(
                    {"desc": "", "qty": 1, "price": 0.0}
                )

            st.rerun()

    st.info(f"### Total: ${current_total:,.2f}")

    if st.button("➕ Add Service"):
        st.session_state.service_rows.append(
            {"desc": "", "qty": 1, "price": 0.0}
        )
        st.rerun()

    st.markdown("---")

    if st.button("💾 SAVE & GENERATE PDF"):
        if not c_name.strip():
            st.warning("Please enter the client name.")
            st.stop()

        valid_services = [
            s for s in st.session_state.service_rows
            if str(s["desc"]).strip()
        ]

        if not valid_services:
            st.warning("Please enter at least one service.")
            st.stop()

        hoy = datetime.now().strftime("%m/%d/%Y")
        due_date_text = due_d.strftime("%m/%d/%Y")

        try:
            with conn.session as session:
                all_addrs = " | ".join(
                    [a for a in st.session_state.address_rows if str(a).strip()]
                )

                res = session.execute(
                    text("""
                        INSERT INTO peralta_invoices
                            (
                                inv_num,
                                cliente,
                                project_addr,
                                total_amount,
                                fecha_hoy,
                                due_date,
                                business_name,
                                business_phone,
                                business_description
                            )
                        VALUES
                            (
                                :inv,
                                :clie,
                                :proj,
                                :total,
                                :hoy,
                                :due_date,
                                :business_name,
                                :business_phone,
                                :business_description
                            )
                        RETURNING id
                    """),
                    {
                        "inv": inv_no,
                        "clie": c_name,
                        "proj": all_addrs,
                        "total": float(current_total),
                        "hoy": hoy,
                        "due_date": due_date_text,
                        "business_name": my_business,
                        "business_phone": my_phone,
                        "business_description": my_description
                    }
                )

                invoice_id = res.fetchone()[0]

                for s in valid_services:
                    session.execute(
                        text("""
                            INSERT INTO peralta_invoice_items
                                (
                                    invoice_id,
                                    description,
                                    quantity,
                                    unit_price
                                )
                            VALUES
                                (
                                    :invoice_id,
                                    :description,
                                    :quantity,
                                    :unit_price
                                )
                        """),
                        {
                            "invoice_id": invoice_id,
                            "description": s["desc"],
                            "quantity": int(s["qty"]),
                            "unit_price": float(s["price"])
                        }
                    )

                session.commit()

            pdf_info = {
                "business_name": my_business,
                "business_subtitle": my_subtitle,
                "business_description": my_description,
                "phone": my_phone,
                "client_name": c_name,
                "inv_num": inv_no,
                "date": hoy,
                "due_date": due_date_text,
                "payable_to": my_payable,
                "logo_path": logo_path,
                "primary_color": primary_color,
                "accent_color": accent_color,
                "highlight_color": highlight_color,
                "language": pdf_language
            }

            pdf_bytes = generate_pdf(
                pdf_info,
                valid_services,
                st.session_state.address_rows
            )

            st.success(f"Invoice {inv_no} saved and PDF generated!")

            st.download_button(
                "📥 Download PDF",
                data=pdf_bytes,
                file_name=f"Invoice_{inv_no}.pdf",
                mime="application/pdf"
            )

            st.subheader("📄 Preview")
            display_pdf(pdf_bytes)

            st.session_state.address_rows = [""]
            st.session_state.service_rows = [
                {"desc": "", "qty": 1, "price": 0.0}
            ]

        except Exception as e:
            st.error(f"Error saving invoice: {e}")


# =========================
# TAB 2 - HISTORIAL
# =========================
with tab2:
    st.subheader("📜 Saved Invoices")

    try:
        with conn.session as session:
            result = session.execute(
                text("""
                    SELECT
                        id,
                        inv_num,
                        cliente,
                        total_amount,
                        fecha_hoy,
                        due_date,
                        project_addr,
                        business_name,
                        business_phone,
                        business_description
                    FROM peralta_invoices
                    ORDER BY id DESC
                """)
            )

            history_df = pd.DataFrame(
                result.fetchall(),
                columns=result.keys()
            )

        if not history_df.empty:
            for index, row in history_df.iterrows():
                with st.expander(
                    f"📅 {row['fecha_hoy']} | Invoice: {row['inv_num']} | Client: {row['cliente']}"
                ):
                    st.write(f"**Client:** {row['cliente']}")
                    st.write(f"**Invoice #:** {row['inv_num']}")
                    st.write(f"**Date:** {row['fecha_hoy']}")
                    st.write(f"**Due Date:** {row['due_date']}")
                    st.write(f"**Total:** ${float(row['total_amount']):,.2f}")
                    st.write(f"**Addresses:** {row['project_addr']}")

                    col_pdf, col_delete = st.columns([0.7, 0.3])

                    with col_pdf:
                        if st.button(
                            f"📄 Re-Generate PDF #{row['inv_num']}",
                            key=f"re_{row['id']}"
                        ):
                            with conn.session as session:
                                items_result = session.execute(
                                    text("""
                                        SELECT
                                            description AS desc,
                                            quantity AS qty,
                                            unit_price AS price
                                        FROM peralta_invoice_items
                                        WHERE invoice_id = :invoice_id
                                    """),
                                    {"invoice_id": int(row["id"])}
                                )

                                items_df = pd.DataFrame(
                                    items_result.fetchall(),
                                    columns=items_result.keys()
                                )

                            items_list = items_df.to_dict("records")
                            addr_list = str(row["project_addr"]).split(" | ")

                            pdf_info_re = {
                                "business_name": row["business_name"] or my_business,
                                "business_subtitle": my_subtitle,
                                "business_description": row["business_description"] or my_description,
                                "phone": row["business_phone"] or my_phone,
                                "client_name": row["cliente"],
                                "inv_num": row["inv_num"],
                                "date": row["fecha_hoy"],
                                "due_date": row["due_date"] or row["fecha_hoy"],
                                "payable_to": row["business_name"] or my_payable,
                                "logo_path": logo_path,
                                "primary_color": primary_color,
                                "accent_color": accent_color,
                                "highlight_color": highlight_color,
                                "language": pdf_language
                            }

                            re_pdf_bytes = generate_pdf(
                                pdf_info_re,
                                items_list,
                                addr_list
                            )

                            st.download_button(
                                "📥 Click here to Download",
                                data=re_pdf_bytes,
                                file_name=f"Invoice_{row['inv_num']}.pdf",
                                mime="application/pdf",
                                key=f"dl_{row['id']}"
                            )

                    with col_delete:
                        if st.button(
                            "🗑️ Delete",
                            key=f"del_invoice_{row['id']}"
                        ):
                            try:
                                with conn.session as session:
                                    session.execute(
                                        text("""
                                            DELETE FROM peralta_invoices
                                            WHERE id = :invoice_id
                                        """),
                                        {"invoice_id": int(row["id"])}
                                    )
                                    session.commit()

                                st.success(f"Invoice {row['inv_num']} deleted.")
                                st.rerun()

                            except Exception as e:
                                st.error(f"Error deleting invoice: {e}")

        else:
            st.info("No invoices found.")

    except Exception as e:
        st.error(f"Error loading history: {e}")
