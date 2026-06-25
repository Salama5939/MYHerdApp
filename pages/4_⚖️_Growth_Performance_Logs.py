import sys
import os
import streamlit as st
import pandas as pd
from datetime import date

# 📂 Path setup to find your database.py file
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import working_before_merging_database as db

# 🔒 SECURITY ACCESS LOCK
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

st.title("Growth Metrics & Individual Weigh-In Logging Station")

# 🟢 Add this one line to every page!
db.draw_home_button()

st.markdown("---")

# 🌾 Fetch Live Herd Data (To find Fattening Sheep)
try:
    df_herd = db.get_table_data("herd")
except Exception as e:
    df_herd = pd.DataFrame(columns=["tag_no", "category", "status"])

# ⚖️ Fetch Live Weight Logs Data
if (
    "df_weights_cached" in st.session_state
    and st.session_state.df_weights_cached is not None
):
    df_weights = st.session_state.df_weights_cached
else:
    try:
        df_weights = db.get_table_data("weight_logs")
        st.session_state.df_weights_cached = df_weights
    except Exception as e:
        st.error(f"Supabase Connection Error: {e}")
        df_weights = pd.DataFrame()

with st.form("growth_metrics_form", clear_on_submit=True):
    st.subheader("Log Growth Performance Milestone Metrics")

    # 🟢 Filter active herd strictly for the "Fattening" category
    fattening_tags = []
    if not df_herd.empty:
        fattening_tags = df_herd[
            (df_herd["status"] == "Active/Healthy")
            & (df_herd["category"] == "Fattening")
        ]["tag_no"].tolist()

    col1, col2 = st.columns(2)
    with col1:
        # 🟢 Display the Dropdown!
        # (If no fattening sheep exist, it safely falls back to a warning and text box)
        if fattening_tags:
            tag_no = st.selectbox("Animal Target Ear Tag Code (ID):", fattening_tags)
        else:
            st.warning("⚠️ No active animals are currently classified as 'Fattening'.")
            tag_no = st.text_input(
                "Animal Target Ear Tag Code (ID) - Manual Entry:"
            ).strip()

        weight = st.number_input(
            "Observed Body Weight (Scale Value in kg):",
            min_value=0.5,
            step=2.0,
            value=25.0,
        )
    with col2:
        weigh_date = st.date_input("Scale Weighing Date:", value=date.today())
        feed_kg = st.number_input(
            "Allocated Concentrates Mix Consumed Since Last Weighing (kg):",
            min_value=0.0,
            step=1.0,
            value=0.0,
        )

    comments = st.text_area("Growth Quality / Health Observations:")
    submit_growth = st.form_submit_button("Commit Growth Performance Entry")

    if submit_growth:
        if not tag_no:
            st.error("Validation Error: Animal Target Ear Tag Code cannot be empty.")
        else:
            try:
                db.log_growth_metrics_advanced(
                    tag_no, weight, feed_kg, str(weigh_date), comments
                )
                st.success(
                    f"Growth performance logs for Tag {tag_no} adjusted successfully."
                )

                # Clear cache so the matrix updates instantly
                st.session_state.pop("df_weights_cached", None)
                st.rerun()
            except Exception as e:
                st.error(f"Database Error: Could not save log. Details: {e}")

# 📋 Render the Historical Matrix View
st.subheader("Historical Weight Logs Matrix Grid")
if not df_weights.empty:
    st.dataframe(df_weights, width="stretch", hide_index=True)
else:
    st.info("📂 No historical growth performance records found in the registry.")
