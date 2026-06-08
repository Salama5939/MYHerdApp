import sqlite3
import psycopg2
import streamlit as st


def migrate():
    print("🚀 Connecting to local SQLite database...")
    local_conn = sqlite3.connect("herd_management.db")
    local_cursor = local_conn.cursor()

    print("☁️ Connecting to Supabase PostgreSQL database...")
    cloud_conn = psycopg2.connect(st.secrets["CONNECTION_STRING"])
    cloud_cursor = cloud_conn.cursor()

    # Get all tables from local file
    local_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [
        row[0] for row in local_cursor.fetchall() if not row[0].startswith("sqlite_")
    ]

    print(f"📦 Found tables to migrate: {tables}")

    for table in tables:
        print(f"\n🔄 Inspecting table structure: {table}...")

        # 1. Get local columns
        local_cursor.execute(f"PRAGMA table_info({table})")
        local_columns = [col[1] for col in local_cursor.fetchall()]

        # 2. Get cloud columns safely
        try:
            cloud_cursor.execute(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}';"
            )
            cloud_columns = [row[0] for row in cloud_cursor.fetchall()]
        except Exception as e:
            print(f"⚠️ Could not read cloud schema for {table}: {e}. Skipping.")
            continue

        if not cloud_columns:
            print(
                f"⚠️ Table '{table}' does not exist in the cloud database layout. Skipping."
            )
            continue

        # 3. Find matching intersect columns
        matching_columns = [col for col in local_columns if col in cloud_columns]
        print(f"📋 Matching columns to migrate: {matching_columns}")

        if not matching_columns:
            print(f"⚠️ No matching columns found for {table}. Skipping.")
            continue

        # 4. Fetch only the data for matching columns from SQLite
        cols_str = ", ".join(matching_columns)
        local_cursor.execute(f"SELECT {cols_str} FROM {table}")
        rows = local_cursor.fetchall()

        if not rows:
            print(f"📄 Table {table} has no rows to transfer. Skipping.")
            continue

        # 5. Clear old rows from cloud table safely
        print(f"🧹 Clearing default template data from cloud table {table}...")
        try:
            cloud_cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
        except:
            cloud_cursor.execute(f"DELETE FROM {table};")
            cloud_conn.commit()

        # 6. Insert matching data into PostgreSQL
        placeholders = ", ".join(["%s"] * len(matching_columns))
        insert_query = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})"

        try:
            cloud_cursor.executemany(insert_query, rows)
            print(
                f"✅ Successfully transferred {len(rows)} records into cloud table '{table}'!"
            )
        except Exception as e:
            print(f"❌ Failed to insert data into {table}: {e}")
            cloud_conn.rollback()
            continue

    cloud_conn.commit()
    local_conn.close()
    cloud_conn.close()
    print("\n🎉 All matched database tables have been successfully synchronized!")


if __name__ == "__main__":
    migrate()
