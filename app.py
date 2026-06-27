# myHerdApp Engine - Comprehensive Herd Management Dashboard
# This is the main entry point for the myHerdApp application, designed to provide a secure, multi-user interface for managing herd data, performance metrics, and operational records. The application integrates with a cloud-based Supabase database for user authentication and data storage.
import streamlit as st
import pandas as pd
import plotly.express as px
import working_before_merging_database as db
from datetime import datetime, date
import os

# 🟢 This hides the sidebar on load and keeps it hidden
st.set_page_config(
    page_title="myHerdApp", layout="wide", initial_sidebar_state="collapsed"
)

# 🟢 Optional: Add this CSS to completely remove the sidebar from the UI
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# Initialize the database and ensure all necessary tables are created before any operations
# db.initialize_db()
def init_db():

    # Initialize global recipe cache from cloud on initial app boot
    if (
        "cached_recipes" not in st.session_state
        or st.session_state.cached_recipes is None
    ):
        try:
            st.session_state.cached_recipes = db.get_table_data("feed_recipes")
        except Exception as e:
            st.session_state.cached_recipes = []
            st.error(f"Initial Cloud Recipe Fetch Failed: {e}")


# ==============================================================================
# 🔐 MULTI-USER ACCESS GATEWAY (Cloud Supabase Integration)
# ==============================================================================

# Initialize state flags for user session tracking if not already set
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "Operator"

# Render the Login Panel if the user is not signed in
if not st.session_state["authenticated"]:
    st.title("🔐 Secure Herd Engine Sign-In")
    st.write("Access to warehouse desks requires authorized database credentials.")

    with st.form("login_form"):
        username_input = st.text_input("Username").strip().lower()
        password_input = st.text_input("Password", type="password")
        submit_login = st.form_submit_button("Log In")

        if submit_login:
            # Query our cloud user table through the database.py handler
            user_record = db.verify_user_login(username_input, password_input)

            if user_record:
                st.session_state["authenticated"] = True
                st.session_state["username"] = user_record[0]
                st.session_state["user_role"] = user_record[1]

                # Write an audit entry to Supabase tracking this specific login action
                db.log_system_activity(
                    username=user_record[0],
                    action_type="LOGIN",
                    target_table="app_users",
                    record_identifier=user_record[0],
                    context_details="User successfully authenticated via application interface.",
                )
                st.success("Access Granted! Synchronizing database panels...")
                st.rerun()
            else:
                st.error("❌ Invalid Username or Password. Please try again.")

    st.stop()  # Halt execution right here so no farm calculators load behind the gate

# ==============================================================================
# 🐑 ACTIVE FARM DASHBOARD (Accessible only after valid login)
# ==============================================================================

# Display current user metadata and a logout trigger at the top of your sidebar
st.sidebar.markdown(
    f"**Active User:** `{st.session_state['username']}` ({st.session_state['user_role']})"
)
if st.sidebar.button("🔒 Secure Sign-Out"):
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.rerun()


# --- CLEAN DASHBOARD UI ---
st.markdown("## 🐏 myHerdApp Control Room")
st.markdown("---")

# Define your modules with emojis and brief descriptions
modules = {
    "Strategic Performance Metrics": "📊",
    "Active Herd Registry": "🐏",
    "Birth Event Records": "🍼",
    "Growth Performance Logs": "⚖️",
    "Feed Inventory Controller": "🌾",
    "Data Entry Corrections": "🛠️",
}

# Create a clean 3x2 Grid
cols = st.columns(3)

# Map human-readable names to file paths
# Make sure these filenames match exactly what is in your 'pages/' folder
page_map = {
    "Strategic Performance Metrics": "pages/1_📊_Strategic_Performance_Metrics.py",
    "Active Herd Registry": "pages/2_🐏_Active_Herd_Registry.py",
    "Birth Event Records": "pages/3_🍼_Birth_Event_Records.py",
    "Growth Performance Logs": "pages/4_⚖️_Growth_Performance_Logs.py",
    "Feed Inventory Controller": "pages/5_🌾_Feed_Inventory_Controller.py",
    "Data Entry Corrections": "pages/6_🛠️_Data_Entry_Corrections.py",
}

for i, (name, icon) in enumerate(modules.items()):
    with cols[i % 3]:
        # When button is clicked, switch to that specific page
        if st.button(f"{icon} {name}", width="stretch"):
            # This is the command that actually switches the page
            st.switch_page(page_map[name])

st.markdown("---")
# Optional: Add a subtle status footer
st.caption("System Status: 🟢 Cloud Connected | ☁️ Supabase Live")

# Fetch Shared Base Application Metrics
df_herd = db.get_table_data("herd")
df_births = db.get_table_data("birth_records")
df_weights = db.get_table_data("weight_logs")
