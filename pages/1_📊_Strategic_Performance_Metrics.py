import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# ===================================================
# 📂 Path management
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# ===================================================
# 🗃️ Database Import & Translations
import database as db
from translations import init_language_state, t, apply_rtl_styling

# ===================================================
# 🔒 SECURITY & LANGUAGE INITIALIZATION
if "authenticated" not in st.session_state or not st.session_state.get(
    "authenticated", False
):
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

init_language_state()
apply_rtl_styling()
# ===================================================

st.title(t("nav_1"))  # Strategic Metrics title
db.draw_home_button()  # Draw Home Button
st.markdown("---")  # Draw Horizontal Line
# ===================================================

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
# ===================================================

# 🔢 Calculations
if not df_herd.empty:
    # 1. DEFINE OFF-TAKE STATUSES (To be excluded from metrics)
    excluded_statuses = ["Died", "Slaughtered", "Sold", "Zakate", "Donate"]

    # 2. CREATE ACTIVE HERD FILTER
    active_df = df_herd[~df_herd["status"].isin(excluded_statuses)].copy()

    # 3. Convert Dates and Identify Newborns (0-60 days)
    active_df["birth_date"] = pd.to_datetime(active_df["birth_date"], errors="coerce")
    two_months_ago = datetime.now() - timedelta(days=60)

    # Mask for newborns
    is_newborn = active_df["birth_date"] >= two_months_ago

    # Split the active herd into subsets
    newborns_df = active_df[is_newborn]
    others_df = active_df[~is_newborn]

    # Get category counts for the 'Other' group only
    category_counts = others_df["category"].value_counts()

    # 4. Display Metrics
    def safe_t(key: str, default: str) -> str:
        return str(t(key) or default)

    st.subheader(
        safe_t("current_inventory_status", "Current Inventory Status (Living Herd)")
    )

    # Total Columns: Total(1) + Newborns(1) + Categories(len)
    total_metrics = 2 + len(category_counts)
    all_cols = st.columns(total_metrics)

    # Primary Metrics
    all_cols[0].metric(safe_t("total_living", "Total Living"), len(active_df))
    all_cols[1].metric(safe_t("newborns_label", "Newborns (0-2m)"), len(newborns_df))

    # Helper dictionary for translations if Arabic is active
    is_arabic = st.session_state.get("language", "English") == "العربية (Arabic)"
    from translations import TRANSLATIONS

    ar_dict = TRANSLATIONS.get("العربية (Arabic)", {})

    # Category Metrics (Translate category names if Arabic is active)
    for i, (cat, count) in enumerate(category_counts.items()):
        display_cat = ar_dict.get(str(cat), str(cat)) if is_arabic else str(cat)
        all_cols[i + 2].metric(display_cat, count)

    st.markdown("---")
    st.markdown(f"### {t('structural_breakdowns')}")

    chart_col1, chart_col2 = st.columns(2)

    # Prepare DataFrame for charts with translated categories if Arabic
    chart_df = category_counts.reset_index()
    if is_arabic:
        chart_df["display_category"] = (
            chart_df["category"].map(ar_dict).fillna(chart_df["category"])
        )
        cat_column = "display_category"
    else:
        cat_column = "category"

    with chart_col1:
        st.markdown(t("herd_structure_title"))
        fig_bar = px.bar(
            chart_df,
            x=cat_column,
            y="count",
            color=cat_column,
            color_discrete_sequence=px.colors.qualitative.Set1,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart_col2:
        st.markdown(t("allocation_ratio_title"))
        fig_pie = px.pie(
            chart_df,
            values="count",
            names=cat_column,
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig_pie, use_container_width=True)
