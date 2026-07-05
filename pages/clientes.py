import streamlit as st
import pandas as pd

from database.connection import get_connection


def clientes_page():

    st.title("👥 Clientes")

    st.divider()

    tab1, tab2 = st.tabs(["📋 Lista de Clientes", "➕ Nuevo Cliente"])

    # ============================================================
    # LISTA DE CLIENTES
    # ============================================================

    with tab1:

        buscar = st.text_input(
            "Buscar cliente"
        )

        conn = get_connection()

        query = """
            SELECT
                id,
                full_name,
                company_name,
                phone,
                email,
                city,
                active

            FROM clients

            WHERE company_id=%s
        """

        params = [st.session_state.company_id]

        if buscar:

            query += """
                AND (
                    LOWER(full_name) LIKE LOWER(%s)
                    OR LOWER(company_name) LIKE LOWER(%s)
                )
            """

            params.append(f"%{buscar}%")
            params.append(f"%{buscar}%")

        query += """
            ORDER BY full_name
        """

        df = pd.read_sql(query, conn, params=params)

        conn.close()

        if df.empty:

            st.info("No existen clientes registrados.")

        else:

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

    # ============================================================
    # NUEVO CLIENTE
    # ============================================================

    with tab2:

        with st.form("nuevo_cliente"):

            full_name = st.text_input(
                "Nombre del cliente *"
            )

            company_name = st.text_input(
                "Empresa"
            )

            email = st.text_input(
                "Correo"
            )

            phone = st.text_input(
                "Teléfono"
            )

            address = st.text_area(
                "Dirección"
            )

            col1, col2 = st.columns(2)

            with col1:

                city = st.text_input(
                    "Ciudad"
                )

                state = st.text_input(
                    "Estado"
                )

            with col2:

                postal_code = st.text_input(
                    "Código Postal"
                )

                country = st.text_input(
                    "País",
                    value="USA"
                )

            notes = st.text_area(
                "Notas"
            )

            guardar = st.form_submit_button(
                "💾 Guardar Cliente",
                use_container_width=True
            )

            if guardar:

                if full_name == "":

                    st.error(
                        "Debe ingresar el nombre del cliente."
                    )

                else:

                    conn = get_connection()

                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        INSERT INTO clients(

                            company_id,
                            full_name,
                            company_name,
                            email,
                            phone,
                            address,
                            city,
                            state,
                            postal_code,
                            country,
                            notes,
                            active

                        )

                        VALUES(

                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            TRUE

                        )
                        """,

                        (

                            st.session_state.company_id,

                            full_name,

                            company_name,

                            email,

                            phone,

                            address,

                            city,

                            state,

                            postal_code,

                            country,

                            notes

                        )

                    )

                    conn.commit()

                    cursor.close()

                    conn.close()

                    st.success("Cliente guardado correctamente.")

                    st.rerun()
