import streamlit as st
import sys
import os
import pandas as pd
from datetime import timedelta
import database as db
from translations import init_language_state, t, apply_rtl_styling

st.set_page_config(page_title="Breeding Readiness", layout="wide")

# 🔒 SECURITY ACCESS LOCK & LANGUAGE INITIALIZATION
if "authenticated" not in st.session_state or not st.session_state.get(
    "authenticated", False
):
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

init_language_state()
apply_rtl_styling()

is_arabic = st.session_state.get("language", "English") == "العربية (Arabic)"

st.title(t("nav_11"))
db.draw_home_button()

# ===================================================
# 📂 Path management
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# ===================================================

# 1. FETCH DATA
df_births = db.get_table_data("birth_records")

if not df_births.empty:
    df_births["birth_date"] = pd.to_datetime(df_births["birth_date"])

    # 2. GET LATEST BIRTH PER EWE
    latest_births = df_births.groupby("ewe_tag_no")["birth_date"].max().reset_index()

    # 3. CALCULATE READINESS DATE
    latest_births["Ready_to_Breed_Date"] = latest_births["birth_date"] + pd.DateOffset(
        months=3
    )
    latest_births["Ready_to_Breed_Date"] = pd.to_datetime(
        latest_births["Ready_to_Breed_Date"]
    )

    # 4. CALCULATE STATUS
    today = pd.Timestamp.now().normalize()
    latest_births["Days_Until_Ready"] = (
        latest_births["Ready_to_Breed_Date"] - today
    ).dt.days

    def get_status(days):
        if days <= 0:
            return "✅ Ready Now" if not is_arabic else "✅ جاهزة الآن"
        if days <= 7:
            return (
                "⚠️ Ready in < 1 Week"
                if not is_arabic
                else "⚠️ جاهزة خلال أقل من أسبوع"
            )
        return "⏳ Resting" if not is_arabic else "⏳ فترة راحة"

    latest_births["Status"] = latest_births["Days_Until_Ready"].apply(get_status)

    # Translate dataframe headers and layout for display elegance if Arabic
    display_readiness_df = latest_births.sort_values("Days_Until_Ready").copy()
    if is_arabic:
        display_readiness_df = display_readiness_df.rename(
            columns={
                "ewe_tag_no": "رقم أذن النعجة",
                "birth_date": "تاريخ الولادة الأخيرة",
                "Ready_to_Breed_Date": "تاريخ الجاهزية للتكاثر",
                "Days_Until_Ready": "الأيام المتبقية للجاهزية",
                "Status": "الحالة",
            }
        )

    # 5. DISPLAY
    st.dataframe(
        display_readiness_df.style.format(
            {
                "birth_date": "{:%Y-%m-%d}",
                "Ready_to_Breed_Date": "{:%Y-%m-%d}",
                "تاريخ الولادة الأخيرة": "{:%Y-%m-%d}",
                "تاريخ الجاهزية للتكاثر": "{:%Y-%m-%d}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    note_text = (
        "💡 **Planning Note:** This report shows the 3-month recovery mark. Check this list during your weekly rounds to select ewes for the ram."
        if not is_arabic
        else "💡 **ملاحظة تخطيطية:** يعرض هذا التقرير علامة التعافي لمدة 3 أشهر. راجع هذه القائمة خلال جولاتك الأسبوعية لاختيار النعاج للكبش."
    )
    st.info(note_text)

else:
    warn_text = (
        "No birth records found to calculate readiness."
        if not is_arabic
        else "لم يتم العثور على سجلات ولادة لحساب الجاهزية."
    )
    st.warning(warn_text)
