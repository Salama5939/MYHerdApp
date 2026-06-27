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
    # Ensure birth_date is a datetime object
    df_herd["birth_date"] = pd.to_datetime(df_herd["birth_date"], errors="coerce")

    # 1. Identify Newborns (Born within the last 60 days)
    two_months_ago = datetime.now() - timedelta(days=60)
    newborn_mask = df_herd["birth_date"] >= two_months_ago

    newborn_count = len(df_herd[newborn_mask])

    # 2. Get counts for all other categories (excluding newborns)
    # The '~' symbol means 'NOT', so we filter for sheep NOT in the newborn mask
    remaining_herd = df_herd[~newborn_mask]
    category_counts = remaining_herd["category"].value_counts()

    # 3. Display Metrics
    st.subheader("Current Inventory Status")

    # Calculate columns: 1 (Total) + 1 (Newborns) + X (Rest of Categories)
    total_metrics = 2 + len(category_counts)
    all_cols = st.columns(total_metrics)

    # Metric: Total
    all_cols[0].metric("Total Herd", len(df_herd))

    # Metric: Newborns
    all_cols[1].metric("Newborns (0-2m)", newborn_count)

    # Metrics: Remaining Categories
    for i, (cat, count) in enumerate(category_counts.items()):
        all_cols[i + 2].metric(str(cat), count)

    st.markdown("---")
    st.markdown("### 📊 Structural Population Breakdowns")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("**Herd Structure (Excluding Newborns)**")
        fig_bar = px.bar(
            category_counts.reset_index(),
            x="category",
            y="count",
            color="category",
            color_discrete_sequence=px.colors.qualitative.Set1,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart_col2:
        st.markdown("**Allocation Ratio (Excluding Newborns)**")
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
