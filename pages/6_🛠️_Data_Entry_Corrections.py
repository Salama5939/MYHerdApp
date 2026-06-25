import streamlit as st
import pandas as pd
import working_before_merging_database as db

st.set_page_config(layout="wide")
st.title("🛠 System Data Editor & Corrections Panel")
db.draw_home_button()

# 1. Define the unique identifier for each table
# This is the "Key" that tells the code which column is the unique ID
pk_map = {"birth_records": "id", "herd": "tag_no"}

# 2. Select Table
table_choice = st.selectbox(
    "Select the Database Table to view/edit:", list(pk_map.keys())
)

# Determine the Primary Key for this table based on the selection
current_pk = pk_map[table_choice]

# 3. Fetch Data
try:
    df = db.get_table_data(table_choice)
    st.write(f"### Live Spreadsheet View: {table_choice}")
    st.dataframe(df, use_container_width=True, hide_index=True)
except Exception as e:
    st.error(f"Error loading table: {e}")
    st.stop()

# 4. Targeted Record Correction
st.markdown("---")
st.subheader("🎯 Targeted Record Correction")

col1, col2, col3 = st.columns(3)

# Use current_pk to dynamically look up the list of IDs
# We use .astype(str) to ensure dropdown handles both numbers and text tags
record_id_list = df[current_pk].astype(str).tolist()

with col1:
    record_id = st.selectbox(f"1. Select Record by {current_pk}:", record_id_list)

with col2:
    # Filter out the PK so we don't accidentally rename the ID itself
    columns = [c for c in df.columns if c != current_pk]
    column_to_edit = st.selectbox("2. Select Column to Correct:", columns)

with col3:
    new_value = st.text_input("3. Enter The New Correct Value:")

# 5. Commit Actions
col_a, col_b = st.columns(2)

with col_a:
    if st.button("Commit Correction", type="primary"):
        try:
            # We pass current_pk to the function so it knows WHERE to look
            db.update_table_record(
                table_choice, current_pk, record_id, column_to_edit, new_value
            )
            st.success(f"Success! Record {record_id} updated.")
            st.rerun()
        except Exception as e:
            st.error(f"Update failed: {e}")

with col_b:
    if st.button("DELETE RECORD (Permanent)", type="secondary"):
        try:
            db.delete_table_record(table_choice, current_pk, record_id)
            st.warning(f"Deleted Record {record_id}.")
            st.rerun()
        except Exception as e:
            st.error(f"Delete failed: {e}")
