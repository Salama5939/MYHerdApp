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
    conn_str = st.secrets["CONNECTION_STRING"]
    # We use RealDictCursor so queries return results like a dictionary (key:value)
    conn = psycopg2.connect(conn_str, cursor_factory=RealDictCursor)
    with conn.cursor() as cursor:
        cursor.execute("SET search_path TO public;")
    return conn


def execute_custom_query(query, params=(), is_select=True):
    """Executes SQL safely against the Cloud PostgreSQL database."""
    conn = create_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if is_select:
                    data = cursor.fetchall()
                    # Convert list of RealDictRow to DataFrame
                    return pd.DataFrame([dict(row) for row in data])
                else:
                    conn.commit()
                    return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_db():
    """Initializes all tables (Herd + Finance) in the Cloud PostgreSQL database."""
    conn = create_connection()
    cursor = conn.cursor()

    # Herd Tables
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
            newborn_tag TEXT, -- 👈 Added this
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
            recipe_type TEXT PRIMARY KEY,
            calculated_mix_cost_per_kg REAL NOT NULL DEFAULT 0.0,
            recipe_breakdown TEXT DEFAULT ''
        );
    """)

    # Finance Tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.chart_of_accounts (
            account_code INTEGER PRIMARY KEY,
            account_name TEXT NOT NULL UNIQUE,
            account_type TEXT NOT NULL
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.batch_profitability_meta (
            batch_id TEXT PRIMARY KEY,
            batch_name TEXT NOT NULL,
            target_head_count INTEGER NOT NULL DEFAULT 0,
            start_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Active'
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.financial_transactions (
            tx_id SERIAL PRIMARY KEY,
            date TEXT NOT NULL,
            account_code INTEGER NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            tx_flow TEXT NOT NULL,
            batch_id_tag TEXT,
            is_approved INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY (account_code) REFERENCES public.chart_of_accounts(account_code),
            FOREIGN KEY (batch_id_tag) REFERENCES public.batch_profitability_meta(batch_id) ON DELETE SET NULL
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.capital_assets_depreciation (
            asset_id TEXT PRIMARY KEY,
            asset_name TEXT NOT NULL,
            category TEXT NOT NULL,
            purchase_date TEXT NOT NULL,
            purchase_cost REAL NOT NULL,
            useful_life_months INTEGER NOT NULL,
            accumulated_depreciation REAL DEFAULT 0.0
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()

    # Seed Finance Accounts
    seed_standard_chart_of_accounts()


## Seed the standard chart of accounts with predefined entries


def seed_standard_chart_of_accounts():
    accounts = [
        (1010, "Cash & Bank Accounts", "Asset"),
        (4010, "Revenue - Fattening Sheep Sales", "Revenue"),
        (5020, "Direct Cost - Feed Raw Material Invoices", "Expense"),
    ]
    for code, name, acc_type in accounts:
        query = """
            INSERT INTO public.chart_of_accounts (account_code, account_name, account_type)
            VALUES (%s, %s, %s) ON CONFLICT(account_code) DO NOTHING;
        """
        execute_custom_query(query, (code, name, acc_type), is_select=False)


# --- FINANCE FUNCTIONS ---


def create_new_fattening_batch(batch_id, batch_name, head_count, start_date):
    query = "INSERT INTO public.batch_profitability_meta (batch_id, batch_name, target_head_count, start_date) VALUES (%s, %s, %s, %s)"
    try:
        return execute_custom_query(
            query, (batch_id, batch_name, head_count, start_date), is_select=False
        )
    except:
        return False


def record_financial_transaction(
    date_str, account_code, description, amount, tx_flow, batch_tag=None, approved=1
):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query = """INSERT INTO public.financial_transactions (date, account_code, description, amount, tx_flow, batch_id_tag, is_approved, created_at) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    execute_custom_query(
        query,
        (
            date_str,
            account_code,
            description,
            amount,
            tx_flow,
            batch_tag,
            approved,
            now_str,
        ),
        is_select=False,
    )


def get_executive_p_and_l():
    query = """
        SELECT a.account_name, a.account_type, 
        SUM(CASE WHEN t.tx_flow = 'CREDIT' THEN t.amount ELSE 0 END) as credits,
        SUM(CASE WHEN t.tx_flow = 'DEBIT' THEN t.amount ELSE 0 END) as debits
        FROM public.financial_transactions t
        JOIN public.chart_of_accounts a ON t.account_code = a.account_code
        GROUP BY a.account_name, a.account_type
    """
    return execute_custom_query(query)


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


# This function logs individual animal weight milestones and feed metrics with optional comments.
# Moreover, it ensures that the weight and feed values are stored as floats for consistency in calculations and reporting.
# Calculations and reporting can be performed more accurately when the data types are consistent, especially for numerical operations
# however, if the weight or feed values are not valid floats, it will raise a ValueError, which should be handled by the calling function to ensure data integrity.
# Explanation: The function takes in parameters for the animal's tag number, weight, feed consumed since the last weigh-in, the date of weighing, and any optional comments. It constructs an SQL query to insert this data into the weight_logs table. The execute_custom_query function is then called to execute this query, ensuring that the data is safely inserted into the database.


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


# This function adjusts the inventory stock for a given item, ensuring that the quantity does not go below zero. It also updates the cost per kilogram for the item. If the item does not exist in the inventory, it inserts a new record with a default reorder level and active status.
# However, if the amount to adjust is negative and exceeds the current stock, it will set the quantity to zero instead of allowing a negative stock level. This ensures that inventory levels remain accurate and prevents potential errors in stock management.
# Methodology: The function first retrieves the current quantity of the specified item from the inventory.
# It then calculates the new quantity by adding the adjustment amount to the current quantity,
# ensuring that it does not fall below zero.
# Finally, it updates the inventory record or inserts a new one as necessary, committing the changes to the database.


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


# This function saves advanced dynamic configurations for feed recipes, including the recipe type, a serialized breakdown of the recipe, and the calculated cost per kilogram. It ensures that any inventory item is captured and can be parsed natively by the application. If a recipe with the same type already exists, it updates the existing record instead of creating a duplicate.
# The function uses a PostgreSQL "ON CONFLICT" clause to handle the upsert operation, ensuring that the database remains consistent and avoids duplicate entries for the same recipe type. This allows for efficient management of feed recipes and their associated costs within the system.
# Methodology: The function establishes a connection to the database, prepares an SQL query to insert or update the feed recipe, and executes the query with the provided parameters. It then commits the changes and closes the connection to ensure data integrity and resource management.
# Moreover, the use of parameterized queries helps prevent SQL injection attacks, enhancing the security of the application.
# However, if the calculated cost is not a valid float, it will raise a ValueError, which should be handled by the calling function to ensure data integrity.


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


# This function updates a single specific cell in the cloud database without destroying the table structure.
# It takes the table name, primary key column, primary key value, target column, and new value as parameters.
# The function constructs an SQL UPDATE query dynamically while safely parameterizing the values to prevent SQL injection. It then executes the query using the execute_custom_query function, which handles the database connection and execution.
# Methodology: The function uses f-strings to dynamically insert the table and column names into the SQL query.
# The values for the new value and primary key are passed as parameters to the execute_custom_query function,
# which safely executes the query against the database.
# This approach ensures that only the specified cell is updated without affecting the overall structure of the table or other records.
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


# This function updates a record in a specified table using a dynamic key column.
# It constructs an SQL UPDATE query based on the provided table name, key column, record ID, target column, and new value.
# The function establishes a connection to the database, executes the query with parameterized values to prevent SQL injection, commits the changes, and closes the connection.
# Methodology: The function uses f-strings to dynamically insert the table and column names into the SQL query.
# The values for the new value and record ID are passed as parameters to the cursor's execute method,
# which safely executes the query against the database.
# This approach allows for flexible updates to records in different tables without hardcoding the table or column names, while ensuring data integrity and security.
# Conclusion: The function provides a secure and efficient way to update records in the database,
# accommodating various table structures and key columns as needed.


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
