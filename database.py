import sqlite3
import pandas as pd
from datetime import date

DB_NAME = "herd_management.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Main Herd Table (With enhanced tracking for Acquisition Costs & Dates)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS herd (
            tag_no TEXT PRIMARY KEY,
            category TEXT CHECK(category IN ('Ewes', 'Fattening', 'Permanent Sire', 'Pregnant', 'Small Sheep - Female', 'Small Sheep - Male', 'Sold', 'Slaughtered')),
            status TEXT,
            birth_date DATE,
            registration_date DATE,
            purchase_price REAL DEFAULT 0.0,
            purchase_date DATE,
            sale_price REAL DEFAULT 0.0,
            sale_date DATE
        )
    """)

    # 2. Upgraded Weight and Production Logs Table (Saves calculated growth & cost values)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weight_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_no TEXT,
            weight_kg REAL,
            feed_consumed_since_last_kg REAL,
            entry_date DATE,
            days_elapsed INTEGER DEFAULT 0,
            weight_gained_kg REAL DEFAULT 0.0,
            dlwg_kg_day REAL DEFAULT 0.0,
            calculated_feed_cost REAL DEFAULT 0.0,
            FOREIGN KEY(tag_no) REFERENCES herd(tag_no) ON DELETE CASCADE
        )
    """)

    # 3. Enhanced Feed Stock Inventory Table (Includes cost per kg)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            item_name TEXT PRIMARY KEY,
            quantity_kg REAL,
            reorder_level_kg REAL DEFAULT 100.0,
            cost_per_kg REAL DEFAULT 0.0
        )
    """)

    # 4. NEW: Unified Feed Recipe Formulations Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feed_recipes (
            recipe_type TEXT PRIMARY KEY CHECK(recipe_type IN ('Fattening', 'General Herd')),
            corn_pct REAL DEFAULT 0.0,
            soybean_pct REAL DEFAULT 0.0,
            hay_pct REAL DEFAULT 0.0,
            calculated_mix_cost_per_kg REAL DEFAULT 0.0
        )
    """)

    # 5. Historical Maternal Birth Delivery Records Table
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
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df


def add_animal(
    tag_no, category, status, birth_date, purchase_price=0.0, purchase_date=None
):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO herd (tag_no, category, status, birth_date, registration_date, purchase_price, purchase_date) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                tag_no,
                category,
                status,
                birth_date,
                date.today(),
                purchase_price,
                purchase_date,
            ),
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    return success


def register_birth_event(ewe_tag, count, lamb_category):
    conn = get_connection()
    cursor = conn.cursor()
    today_str = date.today().isoformat()
    try:
        cursor.execute(
            "UPDATE herd SET category = 'Ewes', status = 'Active' WHERE tag_no = ?",
            (ewe_tag,),
        )
        cursor.execute(
            "INSERT INTO birth_records (ewe_tag_no, birth_date, lambs_count) VALUES (?, ?, ?)",
            (ewe_tag, today_str, count),
        )

        for i in range(count):
            lamb_tag = f"NEW-{ewe_tag}-{i+1}-{today_str[-2:]}"
            # Farm-born lambs default to 0.0 purchase cost and today's birth date
            cursor.execute(
                """INSERT INTO herd (tag_no, category, status, birth_date, registration_date, purchase_price, purchase_date) 
                   VALUES (?, ?, ?, ?, ?, 0.0, ?)""",
                (lamb_tag, lamb_category, "Active", today_str, today_str, today_str),
            )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def save_feed_recipe(recipe_type, corn, soy, hay, computed_cost):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO feed_recipes (recipe_type, corn_pct, soybean_pct, hay_pct, calculated_mix_cost_per_kg)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(recipe_type) DO UPDATE SET
            corn_pct=excluded.corn_pct,
            soybean_pct=excluded.soybean_pct,
            hay_pct=excluded.hay_pct,
            calculated_mix_cost_per_kg=excluded.calculated_mix_cost_per_kg
    """,
        (recipe_type, corn, soy, hay, computed_cost),
    )
    conn.commit()
    conn.close()


def log_growth_metrics_advanced(tag_no, current_weight, feed_kg, log_date):
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Fetch the absolute last recorded weight log entry for this animal tag
    cursor.execute(
        """
        SELECT weight_kg, entry_date FROM weight_logs 
        WHERE tag_no = ? ORDER BY entry_date DESC LIMIT 1
    """,
        (tag_no,),
    )
    prev_log = cursor.fetchone()

    # 2. If no previous weight log exists, pull its initial historical entry date (e.g., Feb 22, 2026)
    if not prev_log:
        cursor.execute(
            "SELECT birth_date, registration_date, purchase_date FROM herd WHERE tag_no = ?",
            (tag_no,),
        )
        herd_row = cursor.fetchone()
        # Fallback tracking order: purchase_date -> registration_date -> birth_date
        base_date_str = (
            herd_row[2]
            if herd_row[2]
            else (herd_row[1] if herd_row[1] else herd_row[0])
        )
        prev_weight = 0.0  # Assumes a baseline or zero-gain starting calculation point
        prev_date = date.fromisoformat(base_date_str)
    else:
        prev_weight = prev_log[0]
        prev_date = date.fromisoformat(prev_log[1])

    current_date = date.fromisoformat(log_date)

    # 3. Core Production Mathematical Formulations
    days_elapsed = max((current_date - prev_date).days, 1)
    weight_gained = max(current_weight - prev_weight, 0.0) if prev_weight > 0 else 0.0
    dlwg = weight_gained / days_elapsed

    # 4. Fetch the dynamic Fattening Recipe Cost to evaluate true feeding value
    cursor.execute(
        "SELECT calculated_mix_cost_per_kg FROM feed_recipes WHERE recipe_type = 'Fattening'"
    )
    recipe_row = cursor.fetchone()
    mix_cost_per_kg = recipe_row[0] if recipe_row else 0.0
    total_feed_cost = feed_kg * mix_cost_per_kg

    # 5. Insert advanced metrics array to weight ledger
    cursor.execute(
        """
        INSERT INTO weight_logs (tag_no, weight_kg, feed_consumed_since_last_kg, entry_date, days_elapsed, weight_gained_kg, dlwg_kg_day, calculated_feed_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            tag_no,
            current_weight,
            feed_kg,
            log_date,
            days_elapsed,
            weight_gained,
            dlwg,
            total_feed_cost,
        ),
    )

    conn.commit()
    conn.close()


def update_animal_category(tag_no, new_category):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE herd SET category = ? WHERE tag_no = ?", (new_category, tag_no)
    )
    conn.commit()
    conn.close()


def adjust_inventory_stock_advanced(item_name, amount_kg, cost_per_kg=0.0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO inventory (item_name, quantity_kg, reorder_level_kg, cost_per_kg) 
        VALUES (?, ?, 100.0, ?)
        ON CONFLICT(item_name) DO UPDATE SET 
            quantity_kg = quantity_kg + EXCLUDED.quantity_kg,
            cost_per_kg = CASE WHEN EXCLUDED.cost_per_kg > 0 THEN EXCLUDED.cost_per_kg ELSE inventory.cost_per_kg END
        """,
        (item_name, amount_kg, cost_per_kg),
    )
    conn.commit()
    conn.close()


def sell_or_slaughter_animal(tag_no, target_status, price, custom_date):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE herd 
            SET category = ?, status = ?, sale_price = ?, sale_date = ? 
            WHERE tag_no = ?
        """,
            (target_status, target_status, price, custom_date, tag_no),
        )
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()
