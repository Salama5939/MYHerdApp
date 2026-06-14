import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px

# 📂 Path management to find main cloud database.py
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# ☁️ Import live Supabase database module
import database as db

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

# 🌾 Fetch Live Data with Enhanced Diagnostics
if "df_herd_cached" in st.session_state and st.session_state.df_herd_cached is not None:
    df_herd = st.session_state.df_herd_cached
else:
    try:
        # Perform the actual data fetch
        df_herd = db.get_table_data("herd")
        st.session_state.df_herd_cached = df_herd

    except Exception as e:
        # 🚨 DIAGNOSTIC MODE: This will show the error on the website
        st.error("🚨 DATABASE CONNECTION ERROR")
        st.write("The application tried to connect to the cloud database but failed.")
        st.write(f"**Technical Details:** {e}")
        st.write("---")
        st.info(
            "Possible causes: The 'herd' table is missing from the 'public' schema or the Connection String is incorrect."
        )
        st.stop()  # Stop the script so we don't try to draw charts with no data

# 🔢 Calculations and Display
if not df_herd.empty:
    # Live Population Calculations
    total_active = len(df_herd)
    ewes_count = len(df_herd[df_herd["category"] == "Ewes"])
    fattening_count = len(df_herd[df_herd["category"] == "Fattening"])
    pregnant_count = len(df_herd[df_herd["category"] == "Pregnant"])

    small_female = len(
        df_herd[
            df_herd["category"].astype(str).str.contains("Female", na=False, case=False)
        ]
    )
    small_male = len(
        df_herd[
            df_herd["category"].astype(str).str.contains("Male", na=False, case=False)
        ]
    )

    total_lambings = (
        len(df_herd[df_herd["status"] == "Lambing"])
        if "status" in df_herd.columns
        else 0
    )

    # Dashboard Metrics
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    col1.metric("Total Active", total_active)
    col2.metric("Ewes", ewes_count)
    col3.metric("Pregnant", pregnant_count)
    col4.metric("Fattening", fattening_count)
    col5.metric("Small - F", small_female)
    col6.metric("Small - M", small_male)
    col7.metric("Lambings", total_lambings)

    st.markdown("### 📊 Structural Population Breakdowns")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("**Herd Structure Category Count**")
        fig_bar = px.histogram(
            df_herd,
            x="category",
            color="category",
            color_discrete_sequence=px.colors.qualitative.Set1,
        )
        fig_bar.update_layout(
            showlegend=False, xaxis_title="Category", yaxis_title="Head Count"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart_col2:
        st.markdown("**Herd Category Allocation Ratio**")
        fig_pie = px.pie(
            df_herd,
            names="category",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("📂 No active herd logs found in the cloud repository registries.")
