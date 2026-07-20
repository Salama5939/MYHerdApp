import streamlit as st
import sys
import os
import pandas as pd
import working_before_merging_database as db

st.set_page_config(page_title="Data Auditor", layout="wide")
st.title("🔍 Herd Data Auditor")
db.draw_home_button()


# ===================================================
# 📂 Path management
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# ===================================================

# 1. FETCH DATA
# Note: Ensure "herd" matches the exact name of your table in Supabase
df_herd = db.get_table_data("herd")

if not df_herd.empty:
    # 2. FILTERING CONTROLS
    st.subheader("Filter & Sort Herd Data")

    col1, col2 = st.columns(2)

    # Filter by Status
    all_statuses = ["All"] + list(df_herd["status"].unique())
    selected_status = col1.selectbox("Filter by Status:", all_statuses)

    # Sort by column
    sort_col = col2.selectbox("Sort by:", df_herd.columns)

    # Apply Filters
    df_filtered = df_herd.copy()
    if selected_status != "All":
        df_filtered = df_filtered[df_filtered["status"] == selected_status]

    # Apply Sorting
    df_filtered = df_filtered.sort_values(by=sort_col)

    # 3. DISPLAY TABLE
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

    # 4. PRINTABLE REPORT TIP
    st.info("💡 Tip: Use 'Ctrl + P' to print this audit list.")

    # Quick Summary
    st.write(f"Total records displayed: **{len(df_filtered)}**")

else:
    st.warning("No data found in the 'herd' table.")
