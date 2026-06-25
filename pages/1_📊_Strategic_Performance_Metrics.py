import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px

# 📂 Path management to find main cloud database helper
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# ☁️ Import live Supabase database module
import working_before_merging_database as db

# 🔒 SECURITY ACCESS LOCK
if "authenticated" not in st.session_state or not st.session_state.get(
    "authenticated", False
):
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

st.title("Strategic Herd Performance & Summary Metrics")

# 🟢 Global Home Button
db.draw_home_button()

st.markdown("---")

# 🌾 Fetch Live Data
if "df_herd_cached" in st.session_state and st.session_state.df_herd_cached is not None:
    df_herd = st.session_state.df_herd_cached
else:
    try:
        df_herd = db.get_table_data("herd")
        st.session_state.df_herd_cached = df_herd
    except Exception as e:
        st.error(f"🚨 DATABASE CONNECTION ERROR: {e}")
        st.stop()

# 🔢 Dynamic Calculations (Self-Updating)
if not df_herd.empty:
    # 1. Get counts for ALL categories dynamically
    category_counts = df_herd["category"].value_counts()

    # 2. Display them using a loop
    st.subheader("Current Inventory Status")
    cols = st.columns(len(category_counts))

    for i, (cat, count) in enumerate(category_counts.items()):
        cols[i].metric(str(cat), count)

    st.markdown("---")
    st.markdown("### 📊 Structural Population Breakdowns")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("**Herd Structure Category Count**")
        fig_bar = px.bar(
            category_counts.reset_index(),
            x="category",
            y="count",
            color="category",
            color_discrete_sequence=px.colors.qualitative.Set1,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart_col2:
        st.markdown("**Herd Category Allocation Ratio**")
        fig_pie = px.pie(
            category_counts.reset_index(),
            values="count",
            names="category",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("📂 No active herd logs found in the cloud repository registries.")
