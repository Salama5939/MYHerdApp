import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 📂 Path management
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

st.title("Strategic Herd Performance & Summary Metrics")
db.draw_home_button()
st.markdown("---")

# 🌾 Data Loading
if "df_herd_cached" in st.session_state and st.session_state.df_herd_cached is not None:
    df_herd = st.session_state.df_herd_cached
else:
    try:
        df_herd = db.get_table_data("herd")
        st.session_state.df_herd_cached = df_herd
    except Exception as e:
        st.error(f"🚨 DATABASE CONNECTION ERROR: {e}")
        st.stop()

# 🔢 Calculations
if not df_herd.empty:
    # 1. CREATE ACTIVE HERD FILTER (Exclude Died)
    # Using .copy() prevents 'SettingWithCopyWarning' later
    active_df = df_herd[df_herd["status"] != "Died"].copy()

    # 2. Convert Dates and Identify Newborns (0-60 days)
    active_df["birth_date"] = pd.to_datetime(active_df["birth_date"], errors="coerce")
    two_months_ago = datetime.now() - timedelta(days=60)

    # Mask for newborns
    is_newborn = active_df["birth_date"] >= two_months_ago

    # Split the active herd into subsets
    newborns_df = active_df[is_newborn]
    others_df = active_df[~is_newborn]

    # Get category counts for the 'Other' group only
    category_counts = others_df["category"].value_counts()

    # 3. Display Metrics
    st.subheader("Current Inventory Status (Living Herd)")

    # Total Columns: Total(1) + Newborns(1) + Categories(len)
    total_metrics = 2 + len(category_counts)
    all_cols = st.columns(total_metrics)

    # Primary Metrics
    all_cols[0].metric("Total Living", len(active_df))
    all_cols[1].metric("Newborns (0-2m)", len(newborns_df))

    # Category Metrics
    for i, (cat, count) in enumerate(category_counts.items()):
        all_cols[i + 2].metric(str(cat), count)

    st.markdown("---")
    st.markdown("### 📊 Structural Population Breakdowns")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("**Herd Structure (Excluding Newborns & Died)**")
        fig_bar = px.bar(
            category_counts.reset_index(),
            x="category",
            y="count",
            color="category",
            color_discrete_sequence=px.colors.qualitative.Set1,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart_col2:
        st.markdown("**Allocation Ratio (Excluding Newborns & Died)**")
        fig_pie = px.pie(
            category_counts.reset_index(),
            values="count",
            names="category",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("📂 No active herd logs found.")
