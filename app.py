import streamlit as st
import database as db
from translations import init_language_state, t, apply_rtl_styling

st.set_page_config(page_title="Jalila's Farm", layout="centered")

# ==============================================================================
# 🔐 MULTI-USER ACCESS GATEWAY (Cloud Supabase Integration)
# ==============================================================================

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "Operator"

# Render the Login Panel if the user is not signed in
if not st.session_state["authenticated"]:
    st.image("logo.png", width=300)
    st.title("Welcome To Jalila's Farm")
    st.subheader("Herd Management System")

    st.title("🔐 Secure Herd Engine Sign-In")
    st.write("Access to warehouse desks requires authorized database credentials.")

    with st.form("login_form"):
        username_input = st.text_input("Username").strip().lower()
        password_input = st.text_input("Password", type="password")
        submit_login = st.form_submit_button("Log In")

        if submit_login:
            user_record = db.verify_user_login(username_input, password_input)

            if user_record:
                st.session_state["authenticated"] = True
                st.session_state["username"] = user_record[0]
                st.session_state["user_role"] = user_record[1]

                db.log_system_activity(
                    username=user_record[0],
                    action_type="LOGIN",
                    target_table="app_users",
                    record_identifier=user_record[0],
                    context_details="User successfully authenticated via application interface.",
                )
                st.success("Access Granted!")
                st.rerun()
            else:
                st.error("❌ Invalid Username or Password. Please try again.")

    st.stop()  # Stop here if not logged in

# ==============================================================================
# 🚀 AUTHENTICATED AREA & GLOBAL SIDEBAR SETUP
# ==============================================================================

init_language_state()
apply_rtl_styling()

# 🌍 Render the Language Toggle & User Info globally in the Sidebar
with st.sidebar:
    st.markdown("---")
    selected_lang = st.selectbox(
        label="🌐 Language / اللغة",
        options=["English", "العربية (Arabic)"],
        index=0 if st.session_state.get("language", "English") == "English" else 1,
    )

    if selected_lang != st.session_state.get("language", "English"):
        st.session_state.language = selected_lang
        st.rerun()

    st.markdown("---")
    st.markdown(f"**User:** `{st.session_state.get('username', 'Guest')}`")
    if st.button("🔒 Secure Sign-Out"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.rerun()

# Check current active language state
is_arabic = st.session_state.get("language", "English") == "العربية (Arabic)"

# Define global navigation pages with dynamic titles
pages = [
    st.Page(
        "Dashboard.py",
        title="لوحة التحكم" if is_arabic else "Dashboard",
        icon="🏠",
        default=True,
    ),
    st.Page("pages/1_📊_Strategic_Performance_Metrics.py", title=t("nav_1"), icon="📊"),
    st.Page("pages/2_🐏_Active_Herd_Registry.py", title=t("nav_2"), icon="🐏"),
    st.Page("pages/3_🍼_Birth_Event_Records.py", title=t("nav_3"), icon="🍼"),
    st.Page("pages/4_⚖️_Growth_Performance_Logs.py", title=t("nav_4"), icon="⚖️"),
    st.Page("pages/5_🌾_Feed_Inventory_Controller.py", title=t("nav_5"), icon="🌾"),
    st.Page("pages/6_🛠️_Data_Entry_Corrections.py", title=t("nav_6"), icon="🛠️"),
    st.Page("pages/7_📈_Performance_Report.py.py", title=t("nav_7"), icon="📈"),
    st.Page(
        "pages/8_🏆_Summarized_Achievement_Performance_Report.py",
        title=t("nav_8"),
        icon="🏆",
    ),
    st.Page("pages/9_🔍_Data_Audit_Report.py", title=t("nav_9"), icon="🔍"),
    st.Page("pages/10_🍼_Breeding_Prediction_Report.py", title=t("nav_10"), icon="🍼"),
    st.Page("pages/11_📅_Breeding_Readiness_Report.py", title=t("nav_11"), icon="📅"),
    st.Page("pages/12_📉_Off_Take_History_Report.py", title=t("nav_12"), icon="📉"),
]

pg = st.navigation(pages)
pg.run()


st.markdown("---")
st.caption("System Status: 🟢 Cloud Connected | ☁️ Supabase Live")
