import streamlit as st
import working_before_merging_database as db

st.set_page_config(page_title="Jalila's Farm", layout="centered")

# Display your logo
# Ensure your logo file is saved as 'logo.png' in your project root
st.image("logo.png", width=300)

st.title("Welcome To Jalila's Farm")
st.subheader("Herd Management System")

# ==============================================================================
# 🔐 MULTI-USER ACCESS GATEWAY (Cloud Supabase Integration)
# ==============================================================================

# Initialize session state if not already set
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

                # Write an audit entry to Supabase
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

# If user IS authenticated
st.success("You are logged in.")
if st.button("Proceed to Dashboard"):
    st.switch_page("pages/Dashboard.py")
