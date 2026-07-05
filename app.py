import streamlit as st
from fpdf import FPDF
from datetime import datetime
import pandas as pd
from sqlalchemy import text
import base64


# =========================
# CONFIGURACIÓN DE PÁGINA
# =========================
st.set_page_config(
    page_title="Peralta's Garage Doors | Sistema de Facturación",
    layout="wide"
)


# =========================
# CONEXIÓN A NEON
# =========================
conn = st.connection("postgresql", type="sql")


# =========================
# CREAR TABLAS SI NO EXISTEN
# =========================
def init_db():
    with conn.session as session:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS invoices (
                id SERIAL PRIMARY KEY,
                inv_num VARCHAR(100) NOT NULL,
                cliente VARCHAR(255) NOT NULL,
                project_addr TEXT,
                total_amount NUMERIC(12, 2) DEFAULT 0,
                fecha_hoy VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        session.execute(text("""
            CREATE TABLE IF NOT EXISTS invoice_items (
                id SERIAL PRIMARY KEY,
                invoice_id INTEGER REFERENCES invoices(id) ON DELETE CASCADE,
                description TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price NUMERIC(12, 2) NOT NULL
            )
        """))

        session.commit()


init_db()


# =========================
# ESTADOS DE STREAMLIT
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
        self.azul = (20, 50, 90)
        self.rojo = (190, 20, 35)
        self.amarillo = (245, 205, 70)
        self.gris = (245, 245, 245)

        # Fondo superior
        self.set_fill_color(*self.azul)
        self.rect(0, 0, 210, 48, "F")

        # Línea roja superior
        self.set_fill_color(*self.rojo)
        self.rect(0, 0, 210, 3, "F")

        # Título negocio
        self.set_xy(10, 9)
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(255, 255, 255)
        self.cell(110, 8, "PERALTA'S GARAGE DOORS", ln=True)

        self.set_x(10)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(245, 205, 70)
        self.cell(110, 6, "RESIDENCIAL Y COMERCIAL", ln=True)

        self.set_x(10)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(230, 230, 230)
        self.multi_cell(
            100,
            5,
            "Instalacion y Reparacion de Garajes y Motores\nEspanol",
            align="L"
        )

        self.set_x(10)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(255, 255, 255)
        self.cell(100, 7, f"Tel: {data['phone']}", ln=True)

        # Invoice title
        self.set_xy(120, 10)
        self.set_font("Helvetica", "B", 34)
        self.set_text_color(*self.amarillo)
        self.cell(80, 14, "INVOICE", align="R")

        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "", 10)

        self.set_xy(125, 28)
        self.cell(30, 5, "Invoice No:")
        self.set_font("Helvetica", "B", 10)
        self.cell(45, 5, f"#{data['inv_num']}", align="R", ln=True)

        self.set_xy(125, 34)
        self.set_font("Helvetica", "", 10)
        self.cell(30, 5, "Date:")
        self.set_font("Helvetica", "B", 10)
        self.cell(45, 5, f"{data['date']}", align="R", ln=True)

        self.set_xy(125, 40)
        self.set_font("Helvetica", "", 10)
        self.cell(30, 5, "Due Date:")
        self.set_font("Helvetica", "B", 10)
        self.cell(45, 5, f"{data['due_date']}", align="R", ln=True)

        # Barra amarilla
        self.set_fill_color(*self.amarillo)
        self.rect(0, 48, 210, 5, "F")

        # Cliente
        self.set_xy(12, 62)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*self.rojo)
        self.cell(80, 6, "INVOICE TO:", ln=True)

        self.set_x(12)
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(*self.azul)
        self.cell(100, 7, data["client_name"].upper(), ln=True)

        self.set_x(12)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(95, 5, data["project_addr"], align="L")

        # Información de pago
        self.set_xy(125, 62)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*self.azul)
        self.cell(75, 6, "BUSINESS INFO", ln=True)

        self.set_draw_color(*self.rojo)
        self.line(125, 69, 170, 69)

        self.set_xy(125, 73)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(
            75,
            5,
            f"Payable to: {data['payable_to']}\nPhone: {data['phone']}",
            align="L"
        )


# =========================
# GENERAR PDF
# =========================
def generate_pdf(data, services, addresses):
    project_addr_str = "\n".join(
        [a for a in addresses if str(a).strip()]
    )

    pdf = ModernInvoice()
    pdf.add_page()

    header_data = data.copy()
    header_data["project_addr"] = project_addr_str

    pdf.draw_header(header_data)

    pdf.set_y(98)

    cols = [
        {"name": "DESCRIPTION", "w": 100},
        {"name": "UNIT PRICE", "w": 35},
        {"name": "QTY", "w": 20},
        {"name": "TOTAL", "w": 35}
    ]

    pdf.set_fill_color(*pdf.azul)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(255, 255, 255)

    current_x = 10
    for col in cols:
        align = "L" if col["name"] == "DESCRIPTION" else "C"
        pdf.set_xy(current_x, 98)
        pdf.cell(col["w"], 10, col["name"], fill=True, align=align)
        current_x += col["w"]

    total_general = 0
    current_y = 108

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.set_draw_color(210, 210, 210)

    for service in services:
        desc = str(service["desc"]).strip()
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

        for index, col in enumerate(cols):
            align = "L" if col["name"] == "DESCRIPTION" else "C"
            pdf.set_xy(current_x, current_y)
            pdf.cell(col["w"], 9, values[index], border="B", align=align)
            current_x += col["w"]

        current_y += 9

        if current_y > 235:
            pdf.add_page()
            current_y = 20

    # Totales
    totals_x = 115
    totals_y = current_y + 12

    pdf.set_fill_color(*pdf.gris)
    pdf.rect(totals_x, totals_y, 85, 28, "F")

    pdf.set_xy(totals_x, totals_y + 4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(40, 7, "Sub-total:", align="R")
    pdf.cell(40, 7, f"${total_general:,.2f}", align="R", ln=True)

    pdf.set_x(totals_x)
    pdf.cell(40, 7, "Tax:", align="R")
    pdf.cell(40, 7, "$0.00", align="R", ln=True)

    pdf.set_fill_color(*pdf.azul)
    pdf.rect(totals_x, totals_y + 28, 85, 14, "F")

    pdf.set_xy(totals_x, totals_y + 29)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(40, 12, "Total:", align="R")
    pdf.cell(40, 12, f"${total_general:,.2f}", align="R")

    # Términos
    pdf.set_xy(10, totals_y)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*pdf.azul)
    pdf.cell(90, 7, "TERMS AND CONDITIONS", ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    terms = (
        "Thank you for your business.\n"
        "Payment is due according to the date listed on this invoice.\n"
        "Warranty and service conditions may vary depending on the type of installation or repair."
    )
    pdf.multi_cell(95, 5, terms)

    # Firma
    pdf.set_y(250)
    pdf.set_font("Times", "BI", 16)
    pdf.set_text_color(*pdf.azul)
    pdf.cell(0, 8, "Peralta's Garage Doors", align="R", ln=True)

    pdf.set_draw_color(*pdf.azul)
    pdf.line(130, 262, 200, 262)

    pdf.set_xy(130, 264)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(70, 5, "Administrator", align="C")

    # Footer
    pdf.set_fill_color(*pdf.azul)
    pdf.rect(0, 282, 210, 15, "F")

    pdf.set_fill_color(*pdf.rojo)
    pdf.rect(0, 279, 90, 3, "F")
    pdf.rect(165, 279, 45, 3, "F")

    output = pdf.output(dest="S")

    if isinstance(output, str):
        return output.encode("latin1")

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
# INTERFAZ
# =========================
st.title("🛠️ Peralta's Garage Doors System")

with st.sidebar:
    st.header("⚙️ Business Info")

    my_business = st.text_input(
        "Business Name",
        "Peralta's Garage Doors"
    )

    my_phone = st.text_input(
        "Phone",
        "832-752-0930"
    )

    my_address = st.text_area(
        "Business Description",
        "Residencial y Comercial\nInstalacion y Reparacion de Garajes y Motores\nEspanol"
    )

    my_payable = st.text_input(
        "Payable to",
        "Peralta's Garage Doors"
    )


tab1, tab2 = st.tabs(["🆕 Create Invoice", "📜 Invoice History"])


# =========================
# CREAR FACTURA
# =========================
with tab1:
    st.subheader("👤 Invoice & Client Details")

    c1, c2, c3 = st.columns([1, 2, 1])

    inv_no = c1.text_input("Invoice #")
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
            st.rerun()

    st.info(f"### Total: ${current_total:,.2f}")

    if st.button("➕ Add Service"):
        st.session_state.service_rows.append(
            {"desc": "", "qty": 1, "price": 0.0}
        )
        st.rerun()

    st.markdown("---")

    if st.button("💾 SAVE & GENERATE PDF"):
        if not inv_no.strip():
            st.warning("Please enter an invoice number.")
            st.stop()

        if not c_name.strip():
            st.warning("Please enter the client name.")
            st.stop()

        hoy = datetime.now().strftime("%m/%d/%Y")

        try:
            with conn.session as session:
                all_addrs = " | ".join(
                    [a for a in st.session_state.address_rows if a.strip()]
                )

                res = session.execute(
                    text("""
                        INSERT INTO invoices 
                            (inv_num, cliente, project_addr, total_amount, fecha_hoy)
                        VALUES 
                            (:inv, :clie, :proj, :total, :hoy)
                        RETURNING id
                    """),
                    {
                        "inv": inv_no,
                        "clie": c_name,
                        "proj": all_addrs,
                        "total": float(current_total),
                        "hoy": hoy
                    }
                )

                invoice_id = res.fetchone()[0]

                for s in st.session_state.service_rows:
                    if str(s["desc"]).strip():
                        session.execute(
                            text("""
                                INSERT INTO invoice_items 
                                    (invoice_id, description, quantity, unit_price)
                                VALUES 
                                    (:iid, :desc, :qty, :price)
                            """),
                            {
                                "iid": invoice_id,
                                "desc": s["desc"],
                                "qty": int(s["qty"]),
                                "price": float(s["price"])
                            }
                        )

                session.commit()

            pdf_info = {
                "address": my_address,
                "phone": my_phone,
                "email": "",
                "client_name": c_name,
                "inv_num": inv_no,
                "date": hoy,
                "due_date": due_d.strftime("%m/%d/%Y"),
                "payable_to": my_payable
            }

            pdf_bytes = generate_pdf(
                pdf_info,
                st.session_state.service_rows,
                st.session_state.address_rows
            )

            st.success("Invoice saved and PDF generated!")

            st.download_button(
                "📥 Download PDF",
                data=pdf_bytes,
                file_name=f"Invoice_{inv_no}.pdf",
                mime="application/pdf"
            )

            st.subheader("📄 Preview")
            display_pdf(pdf_bytes)

        except Exception as e:
            st.error(f"Error saving invoice: {e}")


# =========================
# HISTORIAL
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
                        project_addr
                    FROM invoices
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
                    st.write(f"**Total:** ${float(row['total_amount']):,.2f}")
                    st.write(f"**Addresses:** {row['project_addr']}")

                    if st.button(
                        f"Re-Generate PDF #{row['inv_num']}",
                        key=f"re_{row['id']}"
                    ):
                        with conn.session as session:
                            items_result = session.execute(
                                text("""
                                    SELECT 
                                        description AS desc,
                                        quantity AS qty,
                                        unit_price AS price
                                    FROM invoice_items
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
                            "address": my_address,
                            "phone": my_phone,
                            "email": "",
                            "client_name": row["cliente"],
                            "inv_num": row["inv_num"],
                            "date": row["fecha_hoy"],
                            "due_date": row["fecha_hoy"],
                            "payable_to": my_payable
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
        else:
            st.info("No invoices found.")

    except Exception as e:
        st.error(f"Error loading history: {e}")
