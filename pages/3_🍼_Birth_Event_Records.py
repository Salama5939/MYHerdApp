import sys
import os
import streamlit as st
import pandas as pd
from datetime import date

# 🖥️ Force Wide Layout to use full screen space
st.set_page_config(page_title="Birth Event Records", layout="wide")

# 📂 Path Setup
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import database as db
from translations import init_language_state, t, apply_rtl_styling

# 🔒 SECURITY & LANGUAGE INITIALIZATION
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

init_language_state()
apply_rtl_styling()

# Check active language state
is_arabic = st.session_state.get("language", "English") == "العربية (Arabic)"
from translations import TRANSLATIONS

ar_dict = TRANSLATIONS.get("العربية (Arabic)", {})

st.title(t("nav_3"))
db.draw_home_button()
st.markdown("---")

# 🌾 Fetch Data
try:
    df_herd = db.get_table_data("herd")
except Exception:
    df_herd = pd.DataFrame(columns=["tag_no", "category", "status"])

if "df_births_cached" not in st.session_state:
    try:
        st.session_state.df_births_cached = db.get_table_data("birth_records")
    except Exception:
        st.session_state.df_births_cached = pd.DataFrame()

# 📝 INPUT SECTION
lambs_count = st.number_input(
    "Count of Born Lambs:" if not is_arabic else "عدد المواليد الجدد:",
    min_value=1,
    max_value=4,
    value=1,
    step=1,
)

with st.form("birth_event_form", clear_on_submit=True):
    st.subheader(
        "Log Successful Lambing Event" if not is_arabic else "تسجيل حدث ولادة ناجح"
    )

    col1, col2 = st.columns(2)

    # Mother Selection
    with col1:
        pregnant_ewes = df_herd[
            (df_herd["status"] == "Active/Healthy")
            & (df_herd["category"] == "Pregnant")
        ]["tag_no"].tolist()

        if pregnant_ewes:
            ewe_tag = st.selectbox(
                "Dam Ewe Ear Tag Code:" if not is_arabic else "كود أذن النعجة الأم:",
                pregnant_ewes,
            )
        else:
            st.warning(
                "⚠️ No Pregnant Ewes found."
                if not is_arabic
                else "⚠️ لم يتم العثور على نعاج حامل."
            )
            ewe_tag = st.text_input(
                "Dam Ewe Ear Tag Code (Manual):"
                if not is_arabic
                else "كود أذن النعجة الأم (إدخال يدوي):"
            ).strip()

    with col2:
        birth_date = st.date_input(
            "Event Date:" if not is_arabic else "تاريخ الحدث:", value=date.today()
        )
        foster_ewe = st.text_input(
            "Foster Ewe Tag Code (Optional):"
            if not is_arabic
            else "كود أذن النعجة الحاضنة/البديلة (اختياري):"
        ).strip()

    # DYNAMIC INPUT LOOP
    st.write(
        "--- Enter Newborn Details ---"
        if not is_arabic
        else "--- أدخل تفاصيل المواليد الجدد ---"
    )
    lambs_data = []
    for i in range(int(lambs_count)):
        row_col1, row_col2 = st.columns(2)
        with row_col1:
            tag = st.text_input(
                f"Lamb {i+1} Tag #:" if not is_arabic else f"رقم أذن المولود {i+1}:",
                key=f"tag_{i}",
            ).strip()
        with row_col2:
            cat_options = ["Small - Female", "Small - Male"]
            cat_labels = {
                "Small - Female": (
                    "Small - Female (صغير - أنثى)" if is_arabic else "Small - Female"
                ),
                "Small - Male": (
                    "Small - Male (صغير - ذكر)" if is_arabic else "Small - Male"
                ),
            }
            cat = st.selectbox(
                f"Lamb {i+1} Category:" if not is_arabic else f"فئة المولود {i+1}:",
                options=cat_options,
                format_func=lambda x: cat_labels[x],
                key=f"cat_{i}",
            )
        lambs_data.append({"tag": tag, "cat": cat})

    comments = st.text_area("Observations:" if not is_arabic else "الملاحظات:")
    submit_birth = st.form_submit_button(
        "Register Event Parameters" if not is_arabic else "تسجيل بيانات حدث الولادة"
    )

    if submit_birth:
        if not ewe_tag or any(not l["tag"] for l in lambs_data):
            st.error(
                "Validation Error: Mother and ALL Newborn Tag fields are required."
                if not is_arabic
                else "خطأ في التحقق: حقول الأم وجميع المواليد مطلوبة."
            )
        else:
            try:
                db.register_birth_and_update_herd(
                    ewe_tag=ewe_tag,
                    birth_date=str(birth_date),
                    count=int(lambs_count),
                    foster_val=foster_ewe if foster_ewe else None,
                    comments=comments.strip(),
                    lambs_list=lambs_data,
                )
                st.success(
                    "Successfully registered twins/multiples!"
                    if not is_arabic
                    else "تم تسجيل الولادة بنجاح!"
                )
                st.session_state.pop("df_births_cached", None)
                st.rerun()
            except Exception as e:
                st.error(
                    f"Database Error: {e}"
                    if not is_arabic
                    else f"خطأ في قاعدة البيانات: {e}"
                )

# 📋 Historical View
st.subheader(
    "Historical Birth Event Logs" if not is_arabic else "سجلات أحداث الولادة التاريخية"
)
if not st.session_state.df_births_cached.empty:
    display_births_df = st.session_state.df_births_cached.copy()
    if is_arabic:
        cat_map = {"Small - Female": "صغير - أنثى", "Small - Male": "صغير - ذكر"}
        if "category" in display_births_df.columns:
            display_births_df["category"] = (
                display_births_df["category"]
                .map(cat_map)
                .fillna(display_births_df["category"])
            )

    st.dataframe(display_births_df, use_container_width=True, hide_index=True)
else:
    st.info(
        "📂 No historical lambing records found."
        if not is_arabic
        else "📂 لم يتم العثور على سجلات ولادة تاريخية."
    )
