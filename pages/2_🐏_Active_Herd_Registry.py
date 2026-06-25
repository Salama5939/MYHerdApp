import sys
import os
import streamlit as st
import pandas as pd
from datetime import date

# 📂 Tell Python to look one folder up to find your main cloud database.py file!
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# ☁️ Safely import your live Supabase database module
import working_before_merging_database as db

# 🔒 SECURITY ACCESS LOCK
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

st.title("Active Herd Register & Entry Registry")

# 🟢 Add this one line to every page!
db.draw_home_button()

st.markdown("---")

# 🌾 Fetch Live Data directly from your Supabase PostgreSQL cloud tables
if "df_herd_cached" in st.session_state and st.session_state.df_herd_cached is not None:
    df_herd = st.session_state.df_herd_cached
else:
    try:
        df_herd = db.get_table_data("herd")
        st.session_state.df_herd_cached = df_herd
    except Exception as e:
        st.error(f"Supabase Connection Error: {e}")
        df_herd = pd.DataFrame(
            columns=[
                "tag_no",
                "category",
                "status",
                "birth_date",
                "registration_date",
                "purchase_price",
                "comments",
            ]
        )

# 🗂️ Interactive Tabs for Data Entry and Off-Take
tab1, tab2 = st.tabs(["Add Single New Entry", "Execute Status Off-Take Action"])

with tab1:
    with st.form("add_animal_form", clear_on_submit=True):
        st.subheader("Register New Animal Parameters")
        col1, col2 = st.columns(2)

        with col1:
            tag_no = st.text_input("RFID Ear Tag Code (Unique ID):").strip()
            category = st.selectbox(
                "Herd Category Classification:",
                ["Fattening", "Ewes", "Pregnant", "Small - Female", "Small - Male"],
            )
            status = st.selectbox(
                "Current Operational Status Level:",
                ["Active/Healthy", "Sold", "Slaughtered", "Died"],
            )

        with col2:
            birth_date = st.date_input(
                "Approximate Birth Date (Calendar):", value=date.today()
            )
            reg_date = st.date_input("Ledger Entry Registry Date:", value=date.today())
            price = st.number_input(
                "Purchase Price Value Amount ($):",
                min_value=0.0,
                step=50.0,
                value=0.0,
            )

        comments = st.text_area("Structural Descriptive Comments / Observations:")
        submit_btn = st.form_submit_button("Commit New Record to Ledger")

        if submit_btn:
            if not tag_no:
                st.error("Validation Error: RFID Ear Tag Code cannot be empty.")
            elif not df_herd.empty and tag_no in df_herd["tag_no"].values:
                st.error(
                    f"Duplicate Row Exception: Tag '{tag_no}' already exists in the database records."
                )
            else:
                try:
                    db.add_animal(
                        tag_no,
                        category,
                        status,
                        str(birth_date),
                        str(reg_date),
                        price,
                        comments,
                    )
                    st.success(f"Animal {tag_no} has been registered successfully.")
                    # Clear cache to force a fresh pull from Supabase on reload
                    st.session_state.pop("df_herd_cached", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Database Error: Could not add animal. Details: {e}")

with tab2:
    st.subheader("Process Off-Take / Change Operational Status")
    if df_herd.empty:
        st.warning("No records found in database to modify.")
    else:
        # Filter for active animals to populate the dropdown
        active_list = df_herd[df_herd["status"] == "Active/Healthy"]["tag_no"].tolist()

        if not active_list:
            st.info(
                "No active animals are currently present in your herd ledger registry."
            )
        else:
            with st.form("status_offtake_form"):
                target_tag = st.selectbox("Select Target Ear Tag Code:", active_list)
                target_action = st.selectbox(
                    "Select Exit Action Description:",
                    ["Sold", "Slaughtered", "Died"],
                )
                sale_price = st.number_input(
                    "Observed Sale Price Value ($) - If applicable:",
                    min_value=0.0,
                    step=100.0,
                    value=0.0,
                )
                transaction_date = st.date_input(
                    "Off-Take Execution Date:", value=date.today()
                )

                submit_action = st.form_submit_button("Execute Change Status Command")

                if submit_action:
                    try:
                        db.sell_or_slaughter_animal(
                            target_tag,
                            target_action,
                            sale_price,
                            transaction_date.isoformat(),
                        )
                        st.success(
                            f"Animal {target_tag} has been updated to '{target_action}' status successfully."
                        )
                        # Clear cache to force a fresh pull from Supabase on reload
                        st.session_state.pop("df_herd_cached", None)
                        st.rerun()
                    except Exception as e:
                        st.error(
                            f"Database Error: Could not update animal. Details: {e}"
                        )

# 📋 Render the Main Registry Data Table View directly from the cloud
st.subheader("Active Operations Tracking Matrix Grid")
if not df_herd.empty:
    st.dataframe(df_herd, width="stretch", hide_index=True)
else:
    st.info("📂 No active records found in the herd database table.")
