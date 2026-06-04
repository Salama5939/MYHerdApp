import sqlite3

# Connect directly to your isolated database file
conn = sqlite3.connect("feed_inventory.db")
cursor = conn.cursor()

try:
    # Safely inject your first real commodity record
    cursor.execute("""
        INSERT INTO inventory (item_name, quantity_kg, reorder_level_kg, cost_per_kg, is_active) 
        VALUES ('Wheat', 0.0, 100.0, 16.0, 1);
    """)
    conn.commit()
    print("✅ Success! 'Wheat' has been successfully injected into the database.")
except sqlite3.IntegrityError:
    print("ℹ️ 'Wheat' already exists in the database.")
except Exception as e:
    print(f"❌ An error occurred: {e}")
finally:
    conn.close()
