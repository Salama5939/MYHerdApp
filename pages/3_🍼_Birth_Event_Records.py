import sys
import os
import streamlit as st
import pandas as pd
from datetime import date

# 📂 Path Setup
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# ☁️ Import Helper
import working_before_merging_database as db

# 🔒 SECURITY ACCESS LOCK
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

st.title("Ewe Lambing & Prolificacy Records Entry Desk")
db.draw_home_button()
st.markdown("---")

# 🌾 Fetch Live Herd Data
try:
    df_herd = db.get_table_data("herd")
except Exception:
    df_herd = pd.DataFrame(columns=["tag_no", "category", "status"])

# 🍼 Fetch Birth Records
if "df_births_cached" not in st.session_state:
    try:
        st.session_state.df_births_cached = db.get_table_data("birth_records")
    except Exception:
        st.session_state.df_births_cached = pd.DataFrame()

df_births = st.session_state.df_births_cached

# 📝 Active Form for Logging New Births
with st.form("birth_event_form", clear_on_submit=True):
    st.subheader("Log Successful Lambing Event Occurrence")

    # Select Mother
    pregnant_ewes = df_herd[
        (df_herd["status"] == "Active/Healthy") & (df_herd["category"] == "Pregnant")
    ]["tag_no"].tolist()

    col1, col2 = st.columns(2)
    with col1:
        if pregnant_ewes:
            ewe_tag = st.selectbox("Dam Ewe Ear Tag Code:", pregnant_ewes)
        else:
            st.warning("⚠️ No Pregnant Ewes found.")
            ewe_tag = st.text_input("Dam Ewe Ear Tag Code (Manual):").strip()

        lambs_count = st.number_input(
            "Count of Born Lambs:", min_value=1, max_value=4, value=1, step=1
        )

    with col2:
        birth_date = st.date_input("Event Date:", value=date.today())
        foster_ewe = st.text_input("Foster Ewe Tag Code (Optional):").strip()

    # DYNAMIC INPUT LOOP: Create inputs for each lamb
    st.write("--- Enter Newborn Details ---")
    lambs_data = []
    for i in range(int(lambs_count)):
        row_col1, row_col2 = st.columns(2)
        with row_col1:
            tag = st.text_input(f"Lamb {i+1} Tag #:", key=f"tag_{i}").strip()
        with row_col2:
            cat = st.selectbox(
                f"Lamb {i+1} Category:",
                ["Small - Female", "Small - Male"],
                key=f"cat_{i}",
            )
        lambs_data.append({"tag": tag, "cat": cat})

    comments = st.text_area("Observations:")
    submit_birth = st.form_submit_button("Register Event Parameters")

    if submit_birth:
        # Validation
        if not ewe_tag or any(not l["tag"] for l in lambs_data):
            st.error(
                "Validation Error: Mother and ALL Newborn Tag fields are required."
            )
        else:
            foster_val = foster_ewe if foster_ewe else None
            full_comments = comments.strip()

            try:
                # 🚀 Call the Atomic Transaction Function
                db.register_birth_and_update_herd(
                    ewe_tag=ewe_tag,
                    birth_date=str(birth_date),
                    count=int(lambs_count),
                    foster_val=foster_val,
                    comments=full_comments,
                    lambs_list=lambs_data,  # Passing the list of lamb dictionaries
                )

                st.success(
                    "Successfully registered event! Mother status updated and lambs added to herd."
                )
                st.session_state.pop("df_births_cached", None)
                st.rerun()

            except Exception as e:
                st.error(f"Database Error: {e}")

# 📋 Historical Matrix View
st.subheader("Historical Birth Event Logs")
if not df_births.empty:
    st.dataframe(df_births, use_container_width=True, hide_index=True)
else:
    st.info("📂 No historical lambing records found.")
