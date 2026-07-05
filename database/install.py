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


def create_company(
    company_name,
    trade_name,
    tax_id,
    email,
    phone,
    website,
    address,
    city,
    state,
    country,
    postal_code,
    primary_color,
    secondary_color,
    currency,
    language
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO companies(
            company_name,
            trade_name,
            tax_id,
            email,
            phone,
            website,
            address,
            city,
            state,
            country,
            postal_code,
            primary_color,
            secondary_color,
            currency,
            language,
            terms_conditions,
            active
        )

        VALUES(
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,TRUE
        )

        RETURNING id
    """, (

        company_name,
        trade_name,
        tax_id,
        email,
        phone,
        website,
        address,
        city,
        state,
        country,
        postal_code,
        primary_color,
        secondary_color,
        currency,
        language,
        "Gracias por su preferencia."

    ))

    company_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()
    conn.close()

    return company_id


def create_admin(
    company_id,
    first_name,
    last_name,
    email,
    password
):

    password_hash = hash_password(password)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users(
            company_id,
            first_name,
            last_name,
            email,
            password_hash,
            role,
            active
        )

        VALUES(
            %s,%s,%s,%s,%s,%s,TRUE
        )

        RETURNING id
    """, (

        company_id,
        first_name,
        last_name,
        email,
        password_hash,
        "admin"

    ))

    user_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "id": user_id
    }
