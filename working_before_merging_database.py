import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# Initialize the Supabase client
# Make sure these match your specific setup (e.g., secrets from Streamlit)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)


def create_connection():
    """Establishes a connection to the Cloud PostgreSQL database."""
    # Now this works because 'st' is defined above
    conn_str = st.secrets["CONNECTION_STRING"]
    conn = psycopg2.connect(conn_str)
    with conn.cursor() as cursor:
        cursor.execute("SET search_path TO public;")
    return conn


def init_db():
    """Initializes database tables in the public schema."""
    conn = (
        create_connection()
    )  # Establishes a connection to the PostgreSQL database using the connection string from Streamlit secrets.

    cursor = conn.cursor()  # Using 'public.' prefix to guarantee visibility
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.herd (
            tag_no TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            status TEXT NOT NULL,
            birth_date TEXT,
            registration_date TEXT NOT NULL,
            purchase_price REAL,
            comments TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.birth_records (
            id SERIAL PRIMARY KEY,
            ewe_tag_no TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            lambs_count INTEGER NOT NULL,
            foster_ewe_tag TEXT,
            comments TEXT,
            FOREIGN KEY (ewe_tag_no) REFERENCES public.herd(tag_no) ON DELETE CASCADE
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.weight_logs (
            id SERIAL PRIMARY KEY,
            tag_no TEXT NOT NULL,
            weight_kg REAL NOT NULL,
            feed_consumed_since_last_kg REAL DEFAULT 0.0,
            weigh_date TEXT NOT NULL,
            comments TEXT,
            FOREIGN KEY (tag_no) REFERENCES public.herd(tag_no) ON DELETE CASCADE
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.inventory (
            item_name TEXT PRIMARY KEY,
            quantity_kg REAL NOT NULL DEFAULT 0.0,
            reorder_level_kg REAL NOT NULL DEFAULT 100.0,
            cost_per_kg REAL NOT NULL DEFAULT 0.0,
            is_active INTEGER NOT NULL DEFAULT 1
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.feed_recipes (
            recipe_type TEXT PRIMARY KEY CHECK(recipe_type IN ('Fattening', 'General Herd')),
            calculated_mix_cost_per_kg REAL NOT NULL DEFAULT 0.0,
            recipe_breakdown TEXT DEFAULT ''
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()


def initialize_db():
    """Alias for app.py compatibility."""
    init_db()


def get_table_data(table_name):
    """Retrieves records using public schema."""
    conn = (
        create_connection()
    )  # Establishes a connection to the PostgreSQL database using the connection string from Streamlit secrets.

    query = f"SELECT * FROM public.{table_name}"  # Using 'public.' prefix to guarantee visibility
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = (
                [desc[0] for desc in cursor.description] if cursor.description else []
            )
            df = pd.DataFrame(rows, columns=columns)
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df


def execute_custom_query(query, params=(), is_select=True):
    """Executes SQL safely."""
    conn = create_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if is_select:
                    data = cursor.fetchall()
                    colnames = (
                        [desc[0] for desc in cursor.description]
                        if cursor.description
                        else []
                    )
                    return pd.DataFrame(data, columns=colnames)
                else:
                    conn.commit()
                    return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ... (Keep your existing helper functions like add_animal, etc., below here)


# -------------------------------------------------------------------------
# FLEXIBLE MODULE BINDINGS REQUIRED BY APP.PY
# -------------------------------------------------------------------------


def add_animal(tag_no, category, status, birth_date, reg_date, price, comments=""):
    """Inserts a new sheep into the herd registry table with an optional comment parameter."""
    query = """
        INSERT INTO herd (tag_no, category, status, birth_date, registration_date, purchase_price, comments)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    execute_custom_query(
        query,
        (tag_no, category, status, birth_date, reg_date, price, comments),
        is_select=False,
    )


def update_animal_category(tag_no, new_category):
    """Updates the classification bucket of a specific animal ID."""
    # 🟢 Changed ? to %s for PostgreSQL
    query = "UPDATE herd SET category = %s WHERE tag_no = %s"
    execute_custom_query(query, (new_category, tag_no), is_select=False)


# Old function commented out for future reference; replaced by register_birth_and_update_herd in app.py
# def register_birth_event(
#    ewe_tag, birth_date, lambs_count, foster_ewe=None, comments=""
# ):
#    """Logs a successful lambing birth occurrence with optional foster/comment specs."""
#    query = """
#        INSERT INTO birth_records (ewe_tag_no, birth_date, lambs_count, foster_ewe_tag, comments)
#        VALUES (%s, %s, %s, %s, %s)
#    """
#    execute_custom_query(
#        query, (ewe_tag, birth_date, lambs_count, foster_ewe, comments), is_select=False
#    )

# New function to handle both birth registration and herd update in a single transaction


def register_birth_and_update_herd(
    ewe_tag, birth_date, count, foster_val, comments, lambs_list
):
    """
    lambs_list: A list of dictionaries, e.g.,
    [{'tag': '123', 'cat': 'Small - Male'}, {'tag': '124', 'cat': 'Small - Female'}]
    """
    conn = get_supabase_connection()
    cur = conn.cursor()
    try:
        # 1. Update Mother status
        cur.execute(
            "UPDATE public.herd SET category = 'Ewe' WHERE tag_no = %s", (ewe_tag,)
        )

        # 2. Insert Birth Record (Store all tags in comments or a new field)
        tags_str = ", ".join([l["tag"] for l in lambs_list])
        sql_birth = """
        INSERT INTO public.birth_records (ewe_tag_no, birth_date, lambs_count, foster_ewe_tag, comments, newborn_tag)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cur.execute(
            sql_birth, (ewe_tag, birth_date, count, foster_val, comments, tags_str)
        )

        # 3. Create New Lamb Entries (Loop through all lambs)
        sql_lamb = """
        INSERT INTO public.herd (tag_no, category, status, birth_date, registration_date)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (tag_no) DO NOTHING
        """
        for lamb in lambs_list:
            cur.execute(
                sql_lamb,
                (lamb["tag"], lamb["cat"], "Active/Healthy", birth_date, birth_date),
            )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def log_growth_metrics_advanced(
    tag_no, weight, feed_kg, feed_cost, weigh_date, comments
):
    """
    Saves growth logs to the Supabase weight_logs table.
    """
    try:
        # Create the data dictionary
        # IMPORTANT: The keys (left side) MUST match your exact
        # column names in the Supabase 'weight_logs' table.
        data = {
            "tag_no": tag_no,
            "weight_kg": weight,
            "feed_consumed_since_last_kg": feed_kg,  # Ensure this matches your DB column name
            "feed_cost": feed_cost,  # <--- THIS IS THE NEW PART
            "weigh_date": weigh_date,
            "comments": comments,
        }

        # Insert into Supabase
        response = supabase.table("weight_logs").insert(data).execute()
        return response
    except Exception as e:
        print(f"Error logging metrics: {e}")
        raise e


def sell_or_slaughter_animal(tag_no, structural_status, sale_price=None, date_str=None):
    """Modifies an animal status to reflect an off-take exit event dynamically."""
    if sale_price is not None and str(sale_price).strip() != "":
        log_comment = f"Sold for ${sale_price}"
        if date_str:
            log_comment += f" on {date_str}"
        # 🟢 Changed to %s for PostgreSQL
        query = "UPDATE herd SET status = %s, comments = %s WHERE tag_no = %s"
        execute_custom_query(
            query, (structural_status, log_comment, tag_no), is_select=False
        )
    else:
        # 🟢 Changed to %s for PostgreSQL
        query = "UPDATE herd SET status = %s WHERE tag_no = %s"
        execute_custom_query(query, (structural_status, tag_no), is_select=False)


# -------------------------------------------------------------------------
# CORE PARAMETER CALCULATOR LOGIC (Dynamic Serialized System Engine)
# -------------------------------------------------------------------------


def adjust_inventory_stock_advanced(item_name, amount_kg, cost_per_kg):
    """Safely adjusts raw ingredient balances matching the strict layout."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT quantity_kg FROM inventory WHERE item_name = %s", (item_name,)
    )
    row = cursor.fetchone()

    if row:
        new_qty = max(0.0, float(row[0]) + float(amount_kg))
        cursor.execute(
            """
            UPDATE inventory 
            SET quantity_kg = %s, cost_per_kg = %s 
            WHERE item_name = %s
        """,
            (new_qty, float(cost_per_kg), item_name),
        )
    else:
        cursor.execute(
            """
            INSERT INTO inventory (item_name, quantity_kg, reorder_level_kg, cost_per_kg, is_active) 
            VALUES (%s, %s, 100.0, %s, 1)
        """,
            (item_name, max(0.0, float(amount_kg)), float(cost_per_kg)),
        )

    conn.commit()
    conn.close()


def save_feed_recipe_advanced(recipe_type, breakdown_string, calculated_cost):
    """
    Saves advanced dynamic configurations using text-serialized breakdowns.
    Ensures that any inventory item is captured and can be parsed natively by app.py.
    """
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO feed_recipes (recipe_type, calculated_mix_cost_per_kg, recipe_breakdown)
        VALUES (%s, %s, %s)
        ON CONFLICT(recipe_type) DO UPDATE SET
            calculated_mix_cost_per_kg = excluded.calculated_mix_cost_per_kg,
            recipe_breakdown = excluded.recipe_breakdown
    """,
        (
            recipe_type,
            float(calculated_cost),
            breakdown_string,
        ),
    )

    conn.commit()
    conn.close()


# import psycopg2
# import streamlit as st


def get_supabase_connection():
    """Establishes a direct, secure connection to the cloud Supabase PostgreSQL database."""
    conn_str = st.secrets["CONNECTION_STRING"]
    return psycopg2.connect(conn_str)


def verify_user_login(username, password):
    """Checks the cloud app_users table to validate login credentials."""
    try:
        conn = get_supabase_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT username, user_role FROM app_users WHERE username = %s AND password_hash = %s AND is_active = True;",
            (username, password),
        )
        user = cursor.fetchone()

        cursor.close()
        conn.close()
        return user  # Returns (username, role) if found, or None if incorrect
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None


def log_system_activity(
    username, action_type, target_table, record_identifier, context_details
):
    """Automatically writes a security track log line to the online system_audit_logs table."""
    try:
        conn = get_supabase_connection()
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO system_audit_logs (username, action_type, target_table, record_identifier, context_details)
               VALUES (%s, %s, %s, %s, %s);""",
            (username, action_type, target_table, record_identifier, context_details),
        )

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Failed to write audit log: {e}")


def update_single_record(table_name, pk_column, pk_value, target_column, new_value):
    """Safely updates a single specific cell in the cloud database without destroying table structure."""
    # We dynamically insert the table and column names, but safely parameterize the values
    query = f"UPDATE {table_name} SET {target_column} = %s WHERE {pk_column} = %s"
    execute_custom_query(query, (new_value, pk_value), is_select=False)


def draw_home_button():
    """Renders a consistent 'Return to Dashboard' button."""
    # We use st.container to ensure it stays neatly at the top
    if st.button("⬅️ Return to Control Room"):
        st.switch_page("app.py")


def update_table_record(table_name, key_column, record_id, column_name, new_value):
    """Updates a record using a dynamic key column."""
    conn = get_supabase_connection()
    cur = conn.cursor()
    # Dynamic column names: We use the key_column provided by the UI
    query = f"UPDATE public.{table_name} SET {column_name} = %s WHERE {key_column} = %s"
    cur.execute(query, (new_value, record_id))
    conn.commit()
    cur.close()
    conn.close()


def delete_table_record(table_name, key_column, record_id):
    """Deletes a record using a dynamic key column."""
    conn = get_supabase_connection()
    cur = conn.cursor()
    query = f"DELETE FROM public.{table_name} WHERE {key_column} = %s"
    cur.execute(query, (record_id,))
    conn.commit()
    cur.close()
    conn.close()
