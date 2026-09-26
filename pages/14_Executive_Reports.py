import streamlit as st
import pandas as pd
import sys
import os
import database as db
from translations import init_language_state, t, apply_rtl_styling

# 🖥️ Force Wide Layout to use full screen space
st.set_page_config(page_title="Executive Reports & Board Analytics", layout="wide")

# 🔒 SECURITY ACCESS LOCK & LANGUAGE INITIALIZATION
if "authenticated" not in st.session_state or not st.session_state.get(
    "authenticated", False
):
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

init_language_state()
apply_rtl_styling()

is_arabic = st.session_state.get("language", "English") == "العربية (Arabic)"

# Page Title & Home Button (Matching standard app design)
st.title(
    "📑 Executive Reports & Board Analytics"
    if not is_arabic
    else "📑 مركز التقارير التنفيذية وتحليلات مجلس الإدارة"
)
db.draw_home_button()
st.markdown("---")

# ===================================================
# 📂 Path management
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# ===================================================

# Navigation Tabs for Executive Suites
tab1, tab2, tab3 = st.tabs(
    [
        (
            "⚖️ Biological Asset Valuation"
            if not is_arabic
            else "⚖️ تقييم الأصول البيولوجية"
        ),
        "📊 Tag-Level Unit Economics" if not is_arabic else "📊 اقتصاديات وحدات الأذن",
        "🌾 Feed Inventory Audit" if not is_arabic else "🌾 مراجعة مخزون الأعلاف",
    ]
)

# ===================================================
# TAB 1: Biological Asset Valuation
# ===================================================
with tab1:
    st.subheader(
        "Biological Asset Capitalization & Headcount Valuation"
        if not is_arabic
        else "رسملة الأصول البيولوجية وتقييم الرؤوس"
    )
    st.markdown(
        "Active herd headcounts valued against established fixed per-head tier rates."
        if not is_arabic
        else "تقييم أعداد القطيع النشط مقابل معدلات الفئات الثابتة لكل رأس."
    )

    try:
        # Fetch data using dedicated db helper function
        bio_data = db.get_biological_asset_valuation()
        if bio_data:
            df_bio = pd.DataFrame(bio_data)

            total_valuation = (
                df_bio["total_asset_value"].sum()
                if "total_asset_value" in df_bio.columns
                else 0
            )
            total_head = (
                df_bio["total_headcount"].sum()
                if "total_headcount" in df_bio.columns
                else 0
            )

            col1, col2 = st.columns(2)
            col1.metric(
                "Total Active Headcount" if not is_arabic else "إجمالي القطيع النشط",
                f"{total_head:,}",
            )
            col2.metric(
                (
                    "Total Biological Asset Capital"
                    if not is_arabic
                    else "إجمالي رأس مال الأصول البيولوجية"
                ),
                f"{total_valuation:,.2f} EGP",
            )

            st.markdown("---")
            st.dataframe(df_bio, use_container_width=True, hide_index=True)

            csv_bio = df_bio.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=(
                    "Download Valuation CSV"
                    if not is_arabic
                    else "تحميل تقرير التقييم (CSV)"
                ),
                data=csv_bio,
                file_name="biological_asset_valuation.csv",
                mime="text/csv",
            )
        else:
            st.warning(
                "No records found in biological asset valuation view."
                if not is_arabic
                else "لا توجد سجلات في عرض تقييم الأصول البيولوجية."
            )
    except Exception as e:
        st.error(f"Error loading biological asset valuation: {e}")

# ===================================================
# TAB 2: Tag-Level Unit Economics
# ===================================================
with tab2:
    st.subheader(
        "Individual Animal Profit Centers & Unit Economics"
        if not is_arabic
        else "مراكز ربحية الحيوانات الفردية واقتصاديات الوحدة"
    )
    st.markdown(
        "Tracking acquisition costs, accumulated feed expenses, and realized sales margins per tag."
        if not is_arabic
        else "تتبع تكاليف الاستحواذ، مصروفات الأعلاف المتراكمة، وهامش المبيعات المحققة لكل رقم أذن."
    )

    try:
        tag_data = db.get_tag_unit_economics()
        if tag_data:
            df_tag = pd.DataFrame(tag_data)

            total_net = (
                df_tag["net_profit"].sum() if "net_profit" in df_tag.columns else 0
            )

            col1, col2 = st.columns(2)
            col1.metric(
                (
                    "Total Evaluated Animals"
                    if not is_arabic
                    else "إجمالي الحيوانات المقيمة"
                ),
                f"{len(df_tag):,}",
            )
            col2.metric(
                (
                    "Net Profit / Margin Contribution"
                    if not is_arabic
                    else "صافي الربح / المساهمة الهامشية"
                ),
                f"{total_net:,.2f} EGP",
            )

            st.markdown("---")

            # Optional status filter if column exists
            if "status" in df_tag.columns:
                status_list = ["All"] + list(df_tag["status"].dropna().unique())
                status_filter = st.selectbox(
                    "Filter by Status" if not is_arabic else "تصفية حسب الحالة",
                    status_list,
                )
                if status_filter != "All":
                    df_tag = df_tag[df_tag["status"] == status_filter]

            st.dataframe(df_tag, use_container_width=True, hide_index=True)

            csv_tag = df_tag.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=(
                    "Download Unit Economics CSV"
                    if not is_arabic
                    else "تحميل تقرير اقتصاديات الوحدات (CSV)"
                ),
                data=csv_tag,
                file_name="tag_unit_economics.csv",
                mime="text/csv",
            )
        else:
            st.warning(
                "No records found in unit economics view."
                if not is_arabic
                else "لا توجد سجلات في عرض اقتصاديات الوحدات."
            )
    except Exception as e:
        st.error(f"Error loading unit economics: {e}")

# ===================================================
# TAB 3: Feed Inventory Audit
# ===================================================
with tab3:
    st.subheader(
        "Feed Inventory Valuation & Reorder Audit"
        if not is_arabic
        else "تقييم مخزون الأعلاف ومراجعة حدود الطلب"
    )
    st.markdown(
        "Reconciliation of physical inbound purchase logs against active stock levels and weighted-average costs."
        if not is_arabic
        else "مطابقة سجلات واردات المشتريات الفعلية مقابل مستويات المخزون النشط ومتوسط التكاليف المرجحة."
    )

    try:
        feed_data = db.get_feed_inventory_audit()
        if feed_data:
            df_feed = pd.DataFrame(feed_data)

            total_stock_value = (
                df_feed["total_stock_cost"].sum()
                if "total_stock_cost" in df_feed.columns
                else 0
            )
            reorder_alerts = (
                df_feed[df_feed["stock_status"] == "REORDER REQUIRED"]
                if "stock_status" in df_feed.columns
                else pd.DataFrame()
            )

            col1, col2 = st.columns(2)
            col1.metric(
                (
                    "Total Ending Inventory Value"
                    if not is_arabic
                    else "إجمالي قيمة المخزون الختامي"
                ),
                f"{total_stock_value:,.2f} EGP",
            )
            col2.metric(
                (
                    "Ingredients Requiring Reorder"
                    if not is_arabic
                    else "الأصناف التي تتطلب إعادة طلب"
                ),
                f"{len(reorder_alerts)}",
            )

            if not reorder_alerts.empty:
                st.warning(
                    f"⚠️ Reorder alert triggered for: {', '.join(reorder_alerts['ingredient_name'].tolist())}"
                    if not is_arabic
                    else f"⚠️ تنبيه إعادة الطلب للأصناف التالية: {', '.join(reorder_alerts['ingredient_name'].tolist())}"
                )

            st.markdown("---")
            st.dataframe(df_feed, use_container_width=True, hide_index=True)

            csv_feed = df_feed.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=(
                    "Download Feed Audit CSV"
                    if not is_arabic
                    else "تحميل تقرير مراجعة الأعلاف (CSV)"
                ),
                data=csv_feed,
                file_name="feed_inventory_audit.csv",
                mime="text/csv",
            )
        else:
            st.warning(
                "No records found in feed audit view."
                if not is_arabic
                else "لا توجد سجلات في تقرير مراجعة الأعلاف."
            )
    except Exception as e:
        st.error(f"Error loading feed inventory audit: {e}")

st.markdown("---")
st.info(
    "💡 Tip: Use 'Ctrl + P' to print or export these executive reports for your board records."
    if not is_arabic
    else "💡 نصيحة: استخدم 'Ctrl + P' لطباعة أو تصدير هذه التقارير التنفيذية لسجلات المجلس."
)
