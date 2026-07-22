import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
import datetime
import database as db
from translations import init_language_state, t, apply_rtl_styling

st.set_page_config(page_title="Breeding Prediction", layout="wide")

# 🔒 SECURITY ACCESS LOCK & LANGUAGE INITIALIZATION
if "authenticated" not in st.session_state or not st.session_state.get(
    "authenticated", False
):
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

init_language_state()
apply_rtl_styling()

is_arabic = st.session_state.get("language", "English") == "العربية (Arabic)"

st.title(t("nav_10"))
db.draw_home_button()

# ===================================================
# 📂 Path management
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# ===================================================

# 1. FETCH DATA
df = db.get_table_data("herd")

if not df.empty and "registration_date" in df.columns:
    # Convert to datetime
    df["registration_date"] = pd.to_datetime(df["registration_date"])

    # 2. FILTER FOR PREGNANT SHEEP
    if "category" in df.columns:
        pregnant_df = df[
            df["category"].astype(str).str.strip().str.lower() == "pregnant"
        ].copy()
    else:
        err_msg = (
            "Column 'category' not found in herd data."
            if not is_arabic
            else "لم يتم العثور على عمود 'category' في بيانات القطيع."
        )
        st.error(err_msg)
        pregnant_df = pd.DataFrame()

    if not pregnant_df.empty:
        # 3. CALCULATE DELIVERY METRICS
        gestation_days = 155
        pregnant_df["Expected_Delivery_Date"] = pregnant_df[
            "registration_date"
        ] + pd.Timedelta(days=gestation_days)

        # Calculate days remaining until delivery
        today = pd.Timestamp.now().normalize()
        pregnant_df["Days_Remaining"] = (
            pregnant_df["Expected_Delivery_Date"] - today
        ).dt.days

        # 4. ORGANIZE REPORT
        display_df = pregnant_df[
            ["tag_no", "registration_date", "Expected_Delivery_Date", "Days_Remaining"]
        ].copy()

        if not is_arabic:
            display_df.columns = [
                "Tag #",
                "Pregnancy Start Date",
                "Expected Delivery Date",
                "Days to Delivery",
            ]
        else:
            display_df.columns = [
                "رقم الأذن",
                "تاريخ بدء الحمل",
                "تاريخ الولادة المتوقع",
                "الأيام المتبقية للولادة",
            ]

        # Sort by expected date
        date_sort_col = (
            "Expected Delivery Date" if not is_arabic else "تاريخ الولادة المتوقع"
        )
        display_df = display_df.sort_values(by=date_sort_col)

        # 5. DISPLAY
        st.subheader(
            "Current Pregnant Herd" if not is_arabic else "القطيع الحامل حالياً"
        )

        # Style the countdown
        subset_col = "Days to Delivery" if not is_arabic else "الأيام المتبقية للولادة"
        st.dataframe(
            display_df.style.format(
                {
                    "Pregnancy Start Date": "{:%Y-%m-%d}",
                    "Expected Delivery Date": "{:%Y-%m-%d}",
                    "تاريخ بدء الحمل": "{:%Y-%m-%d}",
                    "تاريخ الولادة المتوقع": "{:%Y-%m-%d}",
                }
            ).background_gradient(subset=[subset_col], cmap="RdYlGn_r"),
            use_container_width=True,
            hide_index=True,
        )

        note_text = (
            "💡 **Planning Note:** The expected delivery date is calculated using a 155-day gestation period. Please account for the natural 150-160 day variation."
            if not is_arabic
            else "💡 **ملاحظة تخطيطية:** يتم حساب تاريخ الولادة المتوقع باستخدام فترة حمل مدتها 155 يوماً. يرجى مراعاة التباين الطبيعي الذي تتراوح مدته بين 150-160 يوماً."
        )
        st.info(note_text)

    else:
        success_msg = (
            "No sheep currently marked as 'Pregnant' in the herd registry."
            if not is_arabic
            else "لا توجد أغنام مسجلة حالياً كـ 'حامل' في سجل القطيع."
        )
        st.success(success_msg)
else:
    warn_msg = (
        "Ensure your 'herd' table has a 'registration_date' column and contains data."
        if not is_arabic
        else "تأكد من أن جدول 'herd' يحتوي على عمود 'registration_date' ويحتوي على بيانات."
    )
    st.warning(warn_msg)
