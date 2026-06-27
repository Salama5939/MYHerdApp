import sys
import os
import streamlit as st
import pandas as pd
from datetime import date

# 📂 Path setup
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import working_before_merging_database as db

# 🔒 SECURITY
if "authenticated" not in st.session_state or not st.session_state.get(
    "authenticated", False
):
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

st.title("Growth Metrics & Weigh-In Station")
db.draw_home_button()
st.markdown("---")


# 1. FETCH DATA (With Caching)
@st.cache_data(ttl=60)
def get_data():
    try:
        herd_df = db.get_table_data("herd")
        weights_df = db.get_table_data("weight_logs")
        return herd_df, weights_df
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()


df_herd, df_weights = get_data()

# 2. FILTER DATA (Ensure we only list living Fattening sheep)
if not df_herd.empty:
    fattening_df = df_herd[
        (df_herd["status"] != "Died") & (df_herd["category"] == "Fattening")
    ]
    fattening_tags = fattening_df["tag_no"].unique().tolist()
else:
    fattening_tags = []

# 3. INPUT FORM
with st.form("growth_metrics_form", clear_on_submit=True):
    st.subheader("Log Growth Performance")

    col1, col2 = st.columns(2)

    with col1:
        if fattening_tags:
            tag_no = st.selectbox("Animal Target Ear Tag Code (ID):", fattening_tags)
        else:
            st.warning("⚠️ No 'Fattening' category sheep found.")
            tag_no = st.text_input("Manual Tag Entry:").strip()

        weight_kg = st.number_input(
            "Observed Body Weight (kg):", min_value=0.5, step=0.5, value=25.0
        )

    with col2:
        weigh_date = st.date_input("Weighing Date:", value=date.today())
        feed_kg = st.number_input(
            "Feed Consumed (kg):", min_value=0.0, step=0.5, value=0.0
        )
        feed_cost = st.number_input(
            "Total Feed Cost:", min_value=0.0, step=1.0, value=0.0
        )

    comments = st.text_area("Observations (Health/Quality):")
    submit_growth = st.form_submit_button("Commit Growth Performance Entry")

    if submit_growth:
        if not tag_no:
            st.error("Validation Error: Tag ID is required.")
        else:
            try:
                # IMPORTANT: Ensure your DB function now takes 'feed_cost'
                db.log_growth_metrics_advanced(
                    tag_no, weight_kg, feed_kg, feed_cost, str(weigh_date), comments
                )
                st.success(f"Log saved for {tag_no}")
                # Force cache refresh
                st.rerun()
            except Exception as e:
                st.error(f"Database Error: {e}")

# 4. HISTORICAL VIEW
st.subheader("Recent Growth Logs")
if not df_weights.empty:
    # Optional: Sort by date so the newest are at the top
    df_weights["weigh_date"] = pd.to_datetime(df_weights["weigh_date"])
    st.dataframe(
        df_weights.sort_values(by="weigh_date", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("📂 No historical records found.")
