import streamlit as st
import pandas as pd
import sys
import os
import database as db
from translations import init_language_state, t, apply_rtl_styling

st.set_page_config(page_title="Off-Take History", layout="wide")

# 🔒 SECURITY ACCESS LOCK & LANGUAGE INITIALIZATION
if "authenticated" not in st.session_state or not st.session_state.get(
    "authenticated", False
):
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

init_language_state()
apply_rtl_styling()

is_arabic = st.session_state.get("language", "English") == "العربية (Arabic)"

st.title(t("nav_12"))
db.draw_home_button()

# ===================================================
# 📂 Path management
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# ===================================================

# 1. FETCH DATA
df_herd = db.get_table_data("herd")

if not df_herd.empty:
    # 2. DEFINE EXCLUSION LIST
    excluded_statuses = ["Died", "Slaughtered", "Sold", "Zakate", "Donate"]

    # 3. FILTER FOR OFF-TAKE
    off_take_df = df_herd[df_herd["status"].isin(excluded_statuses)].copy()

    if not off_take_df.empty:
        # 4. SORTING
        off_take_df = off_take_df.sort_values(by="status")

        # Translate statuses and categories for display elegance if Arabic
        display_offtake = off_take_df.copy()
        stat_map = {
            "Sold": "مباع",
            "Slaughtered": "مذبوح",
            "Died": "نافق",
            "Zakate": "زكاة",
            "Donate": "تبرع",
        }

        if is_arabic:
            cat_map = {
                "Fattening": "تسمين",
                "Ewes": "نعاج",
                "Pregnant": "حامل",
                "Small - Female": "صغير - أنثى",
                "Small - Male": "صغير - ذكر",
            }
            if "category" in display_offtake.columns:
                display_offtake["category"] = (
                    display_offtake["category"]
                    .map(cat_map)
                    .fillna(display_offtake["category"])
                )
            if "status" in display_offtake.columns:
                display_offtake["status"] = (
                    display_offtake["status"]
                    .map(stat_map)
                    .fillna(display_offtake["status"])
                )

            display_offtake = display_offtake.rename(
                columns={
                    "tag_no": "رقم الأذن",
                    "category": "الفئة",
                    "status": "الحالة",
                    "birth_date": "تاريخ الميلاد",
                    "registration_date": "تاريخ التسجيل",
                    "purchase_price": "سعر الشراء",
                    "comments": "الملاحظات",
                }
            )

        # 5. DISPLAY
        total_removed_text = (
            f"Total Animals Removed: {len(off_take_df)}"
            if not is_arabic
            else f"إجمالي الحيوانات المستبعدة: {len(off_take_df)}"
        )
        st.subheader(total_removed_text)

        st.dataframe(display_offtake, use_container_width=True, hide_index=True)

        # Quick Summary
        summary = off_take_df["status"].value_counts().reset_index()
        summary.columns = ["Status", "Count"]

        if is_arabic:
            summary["Status"] = (
                summary["Status"].map(stat_map).fillna(summary["Status"])
            )
            summary.columns = ["الحالة", "العدد"]

        summary_title = "Summary by Reason" if not is_arabic else "الملخص حسب السبب"
        st.markdown(f"### {summary_title}")
        st.table(summary)

        tip_text = (
            "💡 Tip: This report serves as your audit trail. Cross-reference these tags with your manual logs to ensure your records are complete."
            if not is_arabic
            else "💡 نصيحة: يعمل هذا التقرير كمسار تدقيق خاص بك. قم بمقارنة هذه العلامات مع سجلاتك اليدوية لضمان اكتمال سجلاتك."
        )
        st.info(tip_text)

    else:
        success_msg = (
            "No off-take (Sold/Slaughtered/Died/Zakate/Donate) records found."
            if not is_arabic
            else "لم يتم العثور على سجلات استبعاد (مباع/مذبوح/نافق/زكاة/تبرع)."
        )
        st.success(success_msg)
else:
    warn_msg = (
        "No data found in the 'herd' table."
        if not is_arabic
        else "لم يتم العثور على بيانات في جدول القطيع."
    )
    st.warning(warn_msg)
