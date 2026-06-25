import sys
import os
import streamlit as st
import pandas as pd
from datetime import date

# 📂 Path Setup: Ensure we can find your main database helper
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# ☁️ Import the helper file
# Ensure this file contains the new 'register_birth_and_update_herd' function
import working_before_merging_database as db

# 🔒 SECURITY ACCESS LOCK
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

st.title("Ewe Lambing & Prolificacy Records Entry Desk")

# 🟢 Add the home button
db.draw_home_button()

st.markdown("---")

# 🌾 Fetch Live Herd Data
try:
    df_herd = db.get_table_data("herd")
except Exception as e:
    df_herd = pd.DataFrame(columns=["tag_no", "category", "status"])

# 🍼 Fetch Live Birth Records Data (Cached)
if "df_births_cached" not in st.session_state:
    try:
        st.session_state.df_births_cached = db.get_table_data("birth_records")
    except Exception as e:
        st.error(f"Supabase Connection Error: {e}")
        st.session_state.df_births_cached = pd.DataFrame()

df_births = st.session_state.df_births_cached

# 📝 Active Form for Logging New Births
with st.form("birth_event_form", clear_on_submit=True):
    st.subheader("Log Successful Lambing Event Occurrence")

    # Logic to find Pregnant Ewes
    pregnant_ewes = []
    if not df_herd.empty:
        pregnant_ewes = df_herd[
            (df_herd["status"] == "Active/Healthy")
            & (df_herd["category"] == "Pregnant")
        ]["tag_no"].tolist()

    col1, col2 = st.columns(2)

    with col1:
        if pregnant_ewes:
            ewe_tag = st.selectbox("Dam Ewe Ear Tag Code (Mother ID):", pregnant_ewes)
        else:
            st.warning("⚠️ No active animals classified as 'Pregnant'.")
            ewe_tag = st.text_input("Dam Ewe Ear Tag Code (Manual Entry):").strip()

        lambs_count = st.number_input(
            "Count of Born Lambs:", min_value=1, max_value=4, value=1, step=1
        )

        newborn_category = st.selectbox(
            "Newborn Classification:", ["Small - Female", "Small - Male"]
        )

        # New Field for the Lamb's Tag
        newborn_tag = st.text_input("Newborn Lamb Tag # (Required):").strip()

    with col2:
        birth_date = st.date_input("Event Date:", value=date.today())
        foster_ewe = st.text_input("Foster Ewe Tag Code (Optional):").strip()

    comments = st.text_area("Observations:")
    submit_birth = st.form_submit_button("Register Event Parameters")

    if submit_birth:
        # Validation
        if not ewe_tag or not newborn_tag:
            st.error("Validation Error: Mother and Newborn Tag fields are required.")
        else:
            foster_val = foster_ewe if foster_ewe else None
            full_comments = f"[{newborn_category}] {comments}".strip()

            try:
                # 🚀 Call the New Multi-Action Transaction Function
                db.register_birth_and_update_herd(
                    ewe_tag=ewe_tag,
                    birth_date=str(birth_date),
                    count=int(lambs_count),
                    foster_val=foster_val,
                    comments=full_comments,
                    newborn_tag=newborn_tag,
                    newborn_cat=newborn_category,
                )

                st.success(
                    "Success: Mother updated, Birth logged, and Lamb added to Herd!"
                )

                # Refresh cache
                st.session_state.pop("df_births_cached", None)
                st.rerun()

            except Exception as e:
                st.error(f"Database Error: Could not register birth. Details: {e}")

# 📋 Historical Matrix View
st.subheader("Historical Birth Event Logs")
if not df_births.empty:
    st.dataframe(df_births, use_container_width=True, hide_index=True)
else:
    st.info("📂 No historical lambing records found.")
