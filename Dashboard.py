import streamlit as st
import sys
import os

# 🗃️ Database Import
import working_before_merging_database as db

st.set_page_config(page_title="Dashboard", layout="wide")

# Force authentication check
if not st.session_state.get("authenticated", False):
    st.warning("🔒 Access Denied. Please log in.")
    st.switch_page("Home.py")


st.title("Jalila's Farm Control Center")
# ===================================================
# 📂 Path management
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# ===================================================

# --- SIDEBAR LOGOUT ---
st.sidebar.markdown(f"**User:** `{st.session_state.get('username', 'Guest')}`")
if st.sidebar.button("🔒 Secure Sign-Out"):
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.rerun()

# --- MAIN DASHBOARD CONTENT ---
st.title("🐑 myHerdApp Control Room")
st.markdown("---")
# ===========================================
# Section 2.1: Herd Management
st.header("Herd Management Applications")
col1, col2, col3 = st.columns(3)

with col1:
    st.page_link(
        "pages/1_📊_Strategic_Performance_Metrics.py",
        label="1. Strategic Metrics",
        icon="📊",
    )
    st.page_link(
        "pages/2_🐏_Active_Herd_Registry.py", label="2. Active Herd Registry", icon="🐏"
    )
with col2:
    st.page_link(
        "pages/3_🍼_Birth_Event_Records.py", label="3. Birth Records", icon="🍼"
    )
    st.page_link(
        "pages/4_⚖️_Growth_Performance_Logs.py", label="4. Growth Logs", icon="⚖️"
    )
with col3:
    st.page_link(
        "pages/5_🌾_Feed_Inventory_Controller.py", label="5. Feed Inventory", icon="🌾"
    )
    st.page_link(
        "pages/6_🛠️_Data_Entry_Corrections.py", label="6. Data Corrections", icon="🛠️"
    )

st.markdown("---")

# Section 2.2: Herd Performance Reports
st.header("Herd Performance Reports")
col4, col5, col6 = st.columns(3)

with col4:
    st.page_link(
        "pages/7_📈_Performance_Report.py.py", label="7. Performance Reports", icon="📈"
    )
    st.page_link(
        "pages/8_🏆_Summarized_Achievement_Performance_Report.py",
        label="8. Achievements",
        icon="🏆",
    )
with col5:
    st.page_link("pages/9_🔍_Data_Audit_Report.py", label="9. Data Audit", icon="🔍")
    st.page_link(
        "pages/10_🍼_Breeding_Prediction_Report.py",
        label="10. Breeding Prediction",
        icon="🍼",
    )
with col6:
    st.page_link(
        "pages/11_📅_Breeding_Readiness_Report.py",
        label="11. Breeding Readiness",
        icon="📅",
    )
    st.page_link(
        "pages/12_📉_Off_Take_History_Report.py",
        label="12. Off-Take History",
        icon="📉",
    )

if st.button("Logout"):
    st.session_state.authenticated = False
    st.switch_page("app.py")
