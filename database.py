import psycopg2
import pandas as pd
import streamlit as st


def create_connection():
    """Establishes and returns a robust connection to the live Supabase PostgreSQL cloud database."""
    conn = psycopg2.connect(st.secrets["CONNECTION_STRING"])
    return conn


def init_db():
    """Initializes the database tables if they do not already exist."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS herd (
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
        CREATE TABLE IF NOT EXISTS birth_records (
            id SERIAL PRIMARY KEY,
            ewe_tag_no TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            lambs_count INTEGER NOT NULL,
            foster_ewe_tag TEXT,
            comments TEXT,
            FOREIGN KEY (ewe_tag_no) REFERENCES herd(tag_no) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weight_logs (
            id SERIAL PRIMARY KEY,
            tag_no TEXT NOT NULL,
            weight_kg REAL NOT NULL,
            feed_consumed_since_last_kg REAL DEFAULT 0.0,
            weigh_date TEXT NOT NULL,
            comments TEXT,
            FOREIGN KEY (tag_no) REFERENCES herd(tag_no) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            item_name TEXT PRIMARY KEY,
            quantity_kg REAL NOT NULL DEFAULT 0.0,
            reorder_level_kg REAL NOT NULL DEFAULT 100.0,
            cost_per_kg REAL NOT NULL DEFAULT 0.0,
            is_active INTEGER NOT NULL DEFAULT 1
        );
    """)

    # FIXED: Simplified layout to exactly match the dynamic 3-column parameters required by app.py
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feed_recipes (
            recipe_type TEXT PRIMARY KEY CHECK(recipe_type IN ('Fattening', 'General Herd')),
            calculated_mix_cost_per_kg REAL NOT NULL DEFAULT 0.0,
            recipe_breakdown TEXT DEFAULT ''
        );
    """)

    conn.commit()
    conn.close()


def initialize_db():
    """Alias function to satisfy app.py calling database.initialize_db()."""
    init_db()


def get_table_data(table_name):
    """Retrieves all records from a table as a Pandas DataFrame."""
    conn = create_connection()
    query = f"SELECT * FROM {table_name}"
    try:
# Adding # type: ignore at the end tells VS Code type checker to relax
        df = pd.read_sql_query(query, conn)  # type: ignore
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df


def execute_custom_query(query, params=(), is_select=True):
    """Executes raw SQL commands safely with optional parameters."""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if is_select:
            data = cursor.fetchall()
            # If description is None, fall back to an empty list safely
            colnames = (
                [desc[0] for desc in cursor.description] if cursor.description else []
            )
            result = pd.DataFrame(data, columns=colnames)
        else:
            conn.commit()
            result = True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    return result


def get_connection():
    """Returns a raw connection object for functions requiring direct manual cursors."""
    return create_connection()


# -------------------------------------------------------------------------
# FLEXIBLE MODULE BINDINGS REQUIRED BY APP.PY
# -------------------------------------------------------------------------


def add_animal(tag_no, category, status, birth_date, reg_date, price, comments=""):
    """Inserts a new sheep into the herd registry table with an optional comment parameter."""
    query = """
        INSERT INTO herd (tag_no, category, status, birth_date, registration_date, purchase_price, comments)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    execute_custom_query(
        query,
        (tag_no, category, status, birth_date, reg_date, price, comments),
        is_select=False,
    )


def update_animal_category(tag_no, new_category):
    """Updates the classification bucket of a specific animal ID."""
    query = "UPDATE herd SET category = ? WHERE tag_no = ?"
    execute_custom_query(query, (new_category, tag_no), is_select=False)


def register_birth_event(
    ewe_tag, birth_date, lambs_count, foster_ewe=None, comments=""
):
    """Logs a successful lambing birth occurrence with optional foster/comment specs."""
    query = """
        INSERT INTO birth_records (ewe_tag_no, birth_date, lambs_count, foster_ewe_tag, comments)
        VALUES (?, ?, ?, ?, ?)
    """
    execute_custom_query(
        query, (ewe_tag, birth_date, lambs_count, foster_ewe, comments), is_select=False
    )


def log_growth_metrics_advanced(tag_no, weight, feed_kg, weigh_date, comments=""):
    """Logs individual animal weight milestones and feed metrics with optional comments."""
    query = """
        INSERT INTO weight_logs (tag_no, weight_kg, feed_consumed_since_last_kg, weigh_date, comments)
        VALUES (?, ?, ?, ?, ?)
    """
    execute_custom_query(
        query,
        (tag_no, float(weight), float(feed_kg), weigh_date, comments),
        is_select=False,
    )


def sell_or_slaughter_animal(tag_no, structural_status, sale_price=None, date_str=None):
    """Modifies an animal status to reflect an off-take exit event dynamically."""
    if sale_price is not None and str(sale_price).strip() != "":
        log_comment = f"Sold for ${sale_price}"
        if date_str:
            log_comment += f" on {date_str}"
        query = "UPDATE herd SET status = ?, comments = ? WHERE tag_no = ?"
        execute_custom_query(
            query, (structural_status, log_comment, tag_no), is_select=False
        )
    else:
        query = "UPDATE herd SET status = ? WHERE tag_no = ?"
        execute_custom_query(query, (structural_status, tag_no), is_select=False)


# -------------------------------------------------------------------------
# CORE PARAMETER CALCULATOR LOGIC (Dynamic Serialized System Engine)
# -------------------------------------------------------------------------


def adjust_inventory_stock_advanced(item_name, amount_kg, cost_per_kg):
    """Safely adjusts raw ingredient balances matching the strict layout."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT quantity_kg FROM inventory WHERE item_name = ?", (item_name,)
    )
    row = cursor.fetchone()

    if row:
        new_qty = max(0.0, float(row[0]) + float(amount_kg))
        cursor.execute(
            """
            UPDATE inventory 
            SET quantity_kg = ?, cost_per_kg = ? 
            WHERE item_name = ?
        """,
            (new_qty, float(cost_per_kg), item_name),
        )
    else:
        cursor.execute(
            """
            INSERT INTO inventory (item_name, quantity_kg, reorder_level_kg, cost_per_kg, is_active) 
            VALUES (?, ?, 100.0, ?, 1)
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
        VALUES (?, ?, ?)
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

import psycopg2
import streamlit as st

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
            (username, password)
        )
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        return user  # Returns (username, role) if found, or None if incorrect
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def log_system_activity(username, action_type, target_table, record_identifier, context_details):
    """Automatically writes a security track log line to the online system_audit_logs table."""
    try:
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO system_audit_logs (username, action_type, target_table, record_identifier, context_details)
               VALUES (%s, %s, %s, %s, %s);""",
            (username, action_type, target_table, record_identifier, context_details)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Failed to write audit log: {e}")
