import sqlite3
import pandas as pd
from datetime import date

DB_NAME = "herd_management.db"


def get_connection():
    """Establishes a connection to the SQLite database file."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")  # Enforce data relationships
    return conn


def initialize_db():
    """Creates structural tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Main Herd Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS herd (
            tag_no TEXT PRIMARY KEY,
            category TEXT CHECK(category IN ('Ewes', 'Fattening', 'Pregnant', 'Small Sheep - Female', 'Small Sheep - Male')),
            status TEXT,
            birth_date DATE,
            registration_date DATE
        )
    """)

    # 2. Weight Tracking Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weight_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_no TEXT,
            weight_kg REAL,
            feed_consumed_since_last_kg REAL,
            entry_date DATE,
            FOREIGN KEY(tag_no) REFERENCES herd(tag_no) ON DELETE CASCADE
        )
    """)

    # 3. Feed Inventory Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            item_name TEXT PRIMARY KEY,
            quantity_kg REAL,
            reorder_level_kg REAL
        )
    """)

    # 4. Birth History Records Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS birth_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ewe_tag_no TEXT,
            birth_date DATE,
            lambs_count INTEGER,
            FOREIGN KEY(ewe_tag_no) REFERENCES herd(tag_no)
        )
    """)

    conn.commit()
    conn.close()


def get_table_data(table_name):
    """Fetches raw table contents and packages them as a Pandas DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df


def add_animal(tag_no, category, status, birth_date):
    """Registers a new animal into the system schema safely."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO herd (tag_no, category, status, birth_date, registration_date) VALUES (?, ?, ?, ?, ?)",
            (tag_no, category, status, birth_date, date.today()),
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    return success


def register_birth_event(ewe_tag, count, lamb_category):
    """Executes an atomic transition: logs a birth, drops Ewe to normal state, adds lamb."""
    conn = get_connection()
    cursor = conn.cursor()
    today_str = date.today().isoformat()
    try:
        # Step A: Update Ewe category from 'Pregnant' to standard 'Ewes'
        cursor.execute(
            "UPDATE herd SET category = 'Ewes', status = 'Active' WHERE tag_no = ?",
            (ewe_tag,),
        )

        # Step B: Record birth log history
        cursor.execute(
            "INSERT INTO birth_records (ewe_tag_no, birth_date, lambs_count) VALUES (?, ?, ?)",
            (ewe_tag, today_str, count),
        )

        # Step C: Bulk register the new offspring
        for i in range(count):
            lamb_tag = f"NEW-{ewe_tag}-{i+1}-{today_str[-2:]}"
            cursor.execute(
                "INSERT INTO herd (tag_no, category, status, birth_date, registration_date) VALUES (?, ?, ?, ?, ?)",
                (lamb_tag, lamb_category, "Active", today_str, today_str),
            )

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def log_growth_metrics(tag_no, current_weight, feed_kg):
    """Logs an entry inside the weight journal database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO weight_logs (tag_no, weight_kg, feed_consumed_since_last_kg, entry_date) VALUES (?, ?, ?, ?)",
        (tag_no, current_weight, feed_kg, date.today()),
    )
    conn.commit()
    conn.close()


def adjust_inventory_stock(item_name, amount_kg):
    """Adds or subtracts physical stock numbers inside inventory metrics."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO inventory (item_name, quantity_kg, reorder_level_kg) 
        VALUES (?, ?, 100.0)
        ON CONFLICT(item_name) DO UPDATE SET quantity_kg = quantity_kg + ?
    """,
        (item_name, amount_kg, amount_kg),
    )
    conn.commit()
    conn.close()
