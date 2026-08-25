import streamlit as st
import sys
import os

# 🗃️ Database Import
import database as db

st.set_page_config(page_title="Dashboard", layout="wide")

# Force authentication check
if not st.session_state.get("authenticated", False):
    st.warning("🔒 Access Denied. Please log in.")
    st.switch_page("app.py")

# ===================================================
# 📂 Path management
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# ===================================================

from translations import init_language_state, t, apply_rtl_styling

# 1. Initialize session state and apply RTL layout if Arabic is active
init_language_state()
apply_rtl_styling()

is_arabic = st.session_state.get("language", "English") == "العربية (Arabic)"

# --- MAIN DASHBOARD CONTENT ---
st.title(
    t("farm_control_center")
    if "farm_control_center" in st.session_state.get("translations", {})
    else ("مركز قيادة المزرعة" if is_arabic else "Farm Control Center")
)
st.subheader(f"🐑 {'غرفة التحكم التنفيذية' if is_arabic else 'Executive Control Room'}")
st.markdown("---")

# ===========================================
# Section 1: Executive Reports Hub Highlight
st.header(
    "📑 Executive Reports & Board Analytics"
    if not is_arabic
    else "📑 مركز التقارير التنفيذية وتحليلات مجلس الإدارة"
)
col_exec1, col_exec2 = st.columns([2, 1])

with col_exec1:
    st.markdown(
        "**Access the complete 6-report strategic suite:** Breakeven & Restocking, Production Line Profitability, "
        "FCR Efficiency, Biological Asset Valuation, Reproductive & Mortality Audit, and Off-Take Timing Optimization."
        if not is_arabic
        else "**الوصول إلى الحزمة الاستراتيجية المكونة من 6 تقارير:** نقطة التعادل وإعادة التسكعين، ربحية خطوط الإنتاج، كفاءة التحويل الغذائي، تقييم الأصول البيولوجية، تدقيق المواليد والنافِق، وتوقيت البيع الأمثل."
    )
with col_exec2:
    st.page_link(
        "pages/14_Executive_Reports.py",
        label="Open Executive Hub" if not is_arabic else "فتح مركز التقارير",
        icon="📑",
    )

st.markdown("---")

# ===========================================
# Section 2.1: Herd Management Apps
st.header(
    t("management_apps_header")
    if "management_apps_header" in st.session_state.get("translations", {})
    else ("تطبيقات الإدارة التشغيلية" if is_arabic else "Operational Management Apps")
)
col1, col2, col3 = st.columns(3)

with col1:
    st.page_link(
        "pages/1_📊_Strategic_Performance_Metrics.py",
        label=t("nav_1"),
        icon="📊",
    )
    st.page_link("pages/2_🐏_Active_Herd_Registry.py", label=t("nav_2"), icon="🐏")
with col2:
    st.page_link("pages/3_🍼_Birth_Event_Records.py", label=t("nav_3"), icon="🍼")
    st.page_link("pages/4_⚖️_Growth_Performance_Logs.py", label=t("nav_4"), icon="⚖️")
with col3:
    st.page_link("pages/5_🌾_Feed_Inventory_Controller.py", label=t("nav_5"), icon="🌾")
    st.page_link("pages/6_🛠️_Data_Entry_Corrections.py", label=t("nav_6"), icon="🛠️")

st.markdown("---")

# ===========================================
# Section 2.2: Herd Performance & Audit Reports
st.header(
    t("performance_reports_header")
    if "performance_reports_header" in st.session_state.get("translations", {})
    else ("تقارير الأداء والمراجعة" if is_arabic else "Performance & Audit Reports")
)
col4, col5, col6 = st.columns(3)

with col4:
    st.page_link("pages/7_📈_Performance_Report.py.py", label=t("nav_7"), icon="📈")
    st.page_link(
        "pages/8_🏆_Summarized_Achievement_Performance_Report.py",
        label=t("nav_8"),
        icon="🏆",
    )
with col5:
    st.page_link("pages/9_🔍_Data_Audit_Report.py", label=t("nav_9"), icon="🔍")
    st.page_link(
        "pages/10_🍼_Breeding_Prediction_Report.py",
        label=t("nav_10"),
        icon="🍼",
    )
with col6:
    st.page_link(
        "pages/11_📅_Breeding_Readiness_Report.py",
        label=t("nav_11"),
        icon="📅",
    )
    st.page_link(
        "pages/12_📉_Off_Take_History_Report.py",
        label=t("nav_12"),
        icon="📉",
    )
    st.page_link(
        "pages/13_📊_Feed_Audit_Report.py",
        label="Feed Audit Report" if not is_arabic else "تقرير مراجعة الأعلاف",
        icon="📊",
    )

    st.page_link(
        "pages/14_Executive_Reports.py",
        label="Executive Reports Hub" if not is_arabic else "مركز التقارير التنفيذية",
        icon="📑",
    )

    st.page_link(
        "pages/15_cutting_management.py",
        label=(
            "Cutting & Butcher Management"
            if not is_arabic
            else "إدارة التقطيع والجزارين"
        ),
        icon="🥩",
    )
