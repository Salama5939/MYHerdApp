import streamlit as st
import sys
import os

# 🖥️ Force Wide Layout to use full screen space
st.set_page_config(page_title="Growth Performance Logs", layout="wide")

# This line finds the folder where the current file is located automatically
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import database as db
import pandas as pd
from translations import init_language_state, t, apply_rtl_styling

# 🔒 SECURITY ACCESS LOCK & LANGUAGE INITIALIZATION
if "authenticated" not in st.session_state or not st.session_state.get(
    "authenticated", False
):
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

init_language_state()
apply_rtl_styling()

is_arabic = st.session_state.get("language", "English") == "العربية (Arabic)"

st.title(t("nav_4"))
db.draw_home_button()

## 1. Fetch and Prepare Data
df_weights = db.get_table_data("weight_logs")

if not df_weights.empty:
    df_weights["weigh_date"] = pd.to_datetime(df_weights["weigh_date"])
    df_weights = df_weights.sort_values(by=["tag_no", "weigh_date"])

    # --- THE CLEAN UP CODE ---
    # This resets the internal "address" of the rows so the ghost column disappears
    df_weights = df_weights.reset_index(drop=True)
    # -------------------------

# 2. THE EDITOR
edit_logs_title = "Edit Logs Directly" if not is_arabic else "تعديل السجلات مباشرة"
st.subheader(edit_logs_title)

edited_df = st.data_editor(
    df_weights,
    num_rows="dynamic",
    use_container_width=True,
    column_config={"id": st.column_config.NumberColumn("ID", disabled=True)},
)

# 3. SAVE CHANGES (The Logic)
save_btn_label = (
    "💾 Save Changes to Database"
    if not is_arabic
    else "💾 حفظ التغييرات في قاعدة البيانات"
)
if st.button(save_btn_label):
    try:
        spinner_text = "Processing..." if not is_arabic else "جاري المعالجة..."
        with st.spinner(spinner_text):
            for i, row in edited_df.iterrows():
                # Helper function to extract numbers safely
                def safe_float(val):
                    try:
                        # If it's None, NaN, or Empty, return 0.0
                        if pd.isna(val) or val == "":
                            return 0.0
                        return float(val)
                    except:
                        return 0.0

                # Extract values using the safe helper
                w_kg = safe_float(row["weight_kg"])
                f_kg = safe_float(row["feed_consumed_since_last_kg"])
                f_cost = safe_float(row["feed_cost"])

                # Format dates (using .astype(str) to avoid series issues)
                d_date = pd.to_datetime(row["weigh_date"]).strftime("%Y-%m-%d")
                e_date = pd.to_datetime(row["entry_date"]).strftime("%Y-%m-%d")

                # Logic
                if pd.isna(row["id"]):
                    db.insert_weight_log(
                        str(row["tag_no"]),
                        w_kg,
                        f_kg,
                        f_cost,
                        d_date,
                        str(row["comments"]),
                        e_date,
                    )
                else:
                    db.update_weight_log(
                        int(row["id"]),
                        str(row["tag_no"]),
                        w_kg,
                        f_kg,
                        f_cost,
                        d_date,
                        str(row["comments"]),
                        e_date,
                    )

        success_text = (
            "✅ Database Updated Successfully!"
            if not is_arabic
            else "✅ تم تحديث قاعدة البيانات بنجاح!"
        )
        st.success(success_text)
        st.rerun()
    except Exception as e:
        fail_text = f"Save Failed: {e}" if not is_arabic else f"فشل الحفظ: {e}"
        st.error(fail_text)
