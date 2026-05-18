import sqlite3
import pandas as pd
from datetime import date

DB_NAME = "herd_management.db"


def get_connection():
    """Establishes a connection to the SQLite database file and enables Foreign Keys."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def initialize_db():
    """Creates the structural tables inside the database file if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Main Herd Registry Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS herd (
            tag_no TEXT PRIMARY KEY,
            category TEXT CHECK(category IN ('Ewes', 'Fattening', 'Permanent Sire', 'Pregnant', 'Small Sheep - Female', 'Small Sheep - Male')),
            status TEXT,
            birth_date DATE,
            registration_date DATE
        )
    """)

    # 2. Periodic Weight and Performance Logs Table
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

    # 3. Warehouse Feed Inventory Balances Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            item_name TEXT PRIMARY KEY,
            quantity_kg REAL,
            reorder_level_kg REAL
        )
    """)

    # 4. Historical Maternal Birth Delivery Records Table
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
    """Fetches data from any specified database table and loads it into a Pandas DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df


def add_animal(tag_no, category, status, birth_date):
    """Inserts a new animal record into the herd registry safely."""
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
    """Automates birth events: updates mother status and registers newborn lambs under a unified transaction."""
    conn = get_connection()
    cursor = conn.cursor()
    today_str = date.today().isoformat()
    try:
        # A. Transition mother from Pregnant back to breeding Ewe group
        cursor.execute(
            "UPDATE herd SET category = 'Ewes', status = 'Active' WHERE tag_no = ?",
            (ewe_tag,),
        )

        # B. Log delivery event details in historical records
        cursor.execute(
            "INSERT INTO birth_records (ewe_tag_no, birth_date, lambs_count) VALUES (?, ?, ?)",
            (ewe_tag, today_str, count),
        )

        # C. Auto-generate sequential records for newborn offspring profiles
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
    """Records real-time scale weights and cumulative feed ingestion histories."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO weight_logs (tag_no, weight_kg, feed_consumed_since_last_kg, entry_date) VALUES (?, ?, ?, ?)",
        (tag_no, current_weight, feed_kg, date.today()),
    )
    conn.commit()
    conn.close()


def adjust_inventory_stock(item_name, amount_kg):
    """Updates physical stock values up or down depending on stock additions or manual mix pull-outs."""
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
