import sys
import os
import streamlit as st
import pandas as pd

# 📂 Path setup to find your database.py file
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import working_before_merging_database as db

# 🔒 SECURITY ACCESS LOCK
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

st.title("🛠️ System Data Editor & Corrections Panel")

# 🟢 Add this one line to every page!
db.draw_home_button()

st.warning(
    "Management Notice: Changes made here directly modify permanent cloud database rows. Proceed with precision."
)

# 🗺️ Map the human-readable names to both the SQL table name AND its Primary Key column
db_table_map = {
    "Herd Registry (herd)": ("herd", "tag_no"),
    "Weight Logs (weight_logs)": ("weight_logs", "id"),
    "Birth Records (birth_records)": ("birth_records", "id"),
    "Feed Inventory (inventory)": ("inventory", "item_name"),
}

table_choice = st.selectbox(
    "Select the Database Table you need to view and edit:", list(db_table_map.keys())
)

target_table, pk_col = db_table_map[table_choice]

# 🌾 Fetch Live Data
try:
    df_current = db.get_table_data(target_table)
except Exception as e:
    st.error(f"Failed to load table: {e}")
    df_current = pd.DataFrame()

if not df_current.empty:
    # 📋 1. Display the Spreadsheet View
    st.subheader(f"Live Spreadsheet View: {target_table}")
    st.info(
        "💡 UI Shortcut: Click on any row in the table below to instantly load it into Box 1!"
    )

    # 🟢 NEW: Enable row selection and capture the click event
    grid_response = st.dataframe(
        df_current,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    # 🟢 NEW: Figure out which row was clicked and grab its Primary Key SAFELY
    selected_pk_value = None

    # Safely check if the keys exist to satisfy VS Code's strict Pylance checker
    if "selection" in grid_response and "rows" in grid_response["selection"]:
        selected_rows = grid_response["selection"]["rows"]
        if len(selected_rows) > 0:
            selected_row_idx = selected_rows[0]
            selected_pk_value = str(df_current.iloc[selected_row_idx][pk_col])

    st.markdown("---")

    # 🎯 2. The Targeted Correction Tool
    st.subheader("🎯 Targeted Record Correction")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Dropdown of all Primary Keys in the selected table
        record_list = df_current[pk_col].astype(str).tolist()

        # 🟢 NEW: Automatically change the dropdown to match the clicked row
        default_index = 0
        if selected_pk_value in record_list:
            default_index = record_list.index(selected_pk_value)

        target_record = st.selectbox(
            f"1. Select Record by {pk_col}:", record_list, index=default_index
        )

    with col2:
        # Dropdown of all editable columns
        editable_columns = [col for col in df_current.columns if col != pk_col]
        target_column = st.selectbox("2. Select Column to Correct:", editable_columns)

    with col3:
        # DYNAMIC INPUT: Changes based on what is selected in col2
        if target_column == "category":
            categories = [
                "Ewes",
                "Fattening",
                "Small Sheep - Female",
                "Small Sheep - Male",
                "Pregnant",
                "Permanent Sire",
            ]
            new_value = st.selectbox("3. Select New Correct Category:", categories)
        elif target_column == "status":
            statuses = ["Active/Healthy", "Sold", "Deceased"]
            new_value = st.selectbox("3. Select New Correct Status:", statuses)
        else:
            new_value = st.text_input("3. Enter the New Correct Value:")

    # Action button placed securely below the columns
    if st.button("Commit Correction to Cloud Database", type="primary"):
        if str(new_value).strip() == "":
            st.error("Validation Error: The new value cannot be entirely empty.")
        else:
            try:
                db.update_single_record(
                    target_table, pk_col, target_record, target_column, new_value
                )
                st.success(
                    f"Success! Record '{target_record}' has been updated in the '{target_table}' table."
                )
                st.rerun()
            except Exception as e:
                st.error(f"Database Execution Error: {e}")

else:
    st.info(f"📂 The '{target_table}' table currently contains zero records to edit.")
