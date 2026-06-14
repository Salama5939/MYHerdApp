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
import database as db

# 🔒 SECURITY ACCESS LOCK
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

st.title("Ewe Lambing & Prolificacy Records Entry Desk")

# 🟢 Add this one line to every page!
db.draw_home_button()

st.markdown("---")

# 🌾 Fetch Live Herd Data (To find Pregnant Ewes)
try:
    df_herd = db.get_table_data("herd")
except Exception as e:
    df_herd = pd.DataFrame(columns=["tag_no", "category", "status"])

# 🍼 Fetch Live Birth Records Data (To populate the historical matrix)
if (
    "df_births_cached" in st.session_state
    and st.session_state.df_births_cached is not None
):
    df_births = st.session_state.df_births_cached
else:
    try:
        # Note: Ensure "birth_records" matches your actual table name in Supabase
        df_births = db.get_table_data("birth_records")
        st.session_state.df_births_cached = df_births
    except Exception as e:
        st.error(f"Supabase Connection Error: {e}")
        df_births = pd.DataFrame()

# 📝 Active Form for Logging New Births
with st.form("birth_event_form", clear_on_submit=True):
    st.subheader("Log Successful Lambing Event Occurrence")

    # Pull eligible mothers from the active herd ledger who are currently "Pregnant"
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
            st.warning(
                "⚠️ No active animals are currently classified as 'Pregnant' in the registry."
            )
            ewe_tag = st.text_input(
                "Dam Ewe Ear Tag Code (Mother ID) - Manual Entry:"
            ).strip()

        lambs_count = st.number_input(
            "Count of Born Lambs (Headcount):",
            min_value=1,
            max_value=4,
            value=1,
            step=1,
        )

        newborn_category = st.selectbox(
            "Newborn Classification:", ["Small - Female", "Small - Male"]
        )

    with col2:
        birth_date = st.date_input("Event Date (Calendar):", value=date.today())
        foster_ewe = st.text_input("Foster Ewe Tag Code (Optional):").strip()

    comments = st.text_area("Birth Weight/Vigor Contextual Observations:")
    submit_birth = st.form_submit_button("Register Event Parameters")

    if submit_birth:
        if not ewe_tag:
            st.error(
                "Validation Error: Mother Dam Ewe Ear Tag Code cannot be left empty."
            )
        else:
            foster_val = foster_ewe if foster_ewe else None
            # Combine newborn category directly into comments tracking context
            full_comments = f"[{newborn_category}] {comments}".strip()

            try:
                db.register_birth_event(
                    ewe_tag,
                    str(birth_date),
                    int(lambs_count),
                    foster_val,
                    full_comments,
                )
                st.success("Lambing event logs processed successfully.")

                # Clear the cache so the historical table updates instantly!
                st.session_state.pop("df_births_cached", None)
                st.rerun()
            except Exception as e:
                st.error(f"Database Error: Could not register birth. Details: {e}")

# 📋 Historical Matrix View
st.subheader("Historical Birth Event Logs")
if not df_births.empty:
    st.dataframe(df_births, width="stretch", hide_index=True)
else:
    st.info("📂 No historical lambing records found in the registry.")
