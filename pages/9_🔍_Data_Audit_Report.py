import streamlit as st
import sys
import os
import pandas as pd
import database as db
from translations import init_language_state, t, apply_rtl_styling

st.set_page_config(page_title="Data Auditor", layout="wide")

# 🔒 SECURITY ACCESS LOCK & LANGUAGE INITIALIZATION
if "authenticated" not in st.session_state or not st.session_state.get(
    "authenticated", False
):
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

init_language_state()
apply_rtl_styling()

is_arabic = st.session_state.get("language", "English") == "العربية (Arabic)"

st.title(t("nav_9"))
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
    # 2. FILTERING CONTROLS
    st.subheader(
        "Filter & Sort Herd Data" if not is_arabic else "تصفية وترتيب بيانات القطيع"
    )

    col1, col2 = st.columns(2)

    # Filter by Status
    raw_statuses = list(df_herd["status"].unique())
    all_statuses = ["All"] + raw_statuses

    # Translate status values for dropdown display if Arabic
    status_display_map = {
        "All": "All (الكل)" if is_arabic else "All",
        "Active/Healthy": (
            "Active/Healthy (نشط / سليم)" if is_arabic else "Active/Healthy"
        ),
        "Sold": "Sold (مباع)" if is_arabic else "Sold",
        "Slaughtered": "Slaughtered (مذبوح)" if is_arabic else "Slaughtered",
        "Died": "Died (نافق)" if is_arabic else "Died",
        "Zakate": "Zakate (زكاة)" if is_arabic else "Zakate",
        "Donate": "Donate (تبرع)" if is_arabic else "Donate",
    }

    selected_status_display = col1.selectbox(
        "Filter by Status:" if not is_arabic else "التصفية حسب الحالة:",
        all_statuses,
        format_func=lambda x: str(status_display_map.get(x, x)),
    )
    selected_status = selected_status_display

    # Sort by column with clean display names if Arabic
    col_mapping = {
        "tag_no": "رقم الأذن (tag_no)" if is_arabic else "tag_no",
        "category": "الفئة (category)" if is_arabic else "category",
        "status": "الحالة (status)" if is_arabic else "status",
        "birth_date": "تاريخ الميلاد (birth_date)" if is_arabic else "birth_date",
        "registration_date": (
            "تاريخ التسجيل (registration_date)" if is_arabic else "registration_date"
        ),
        "purchase_price": (
            "سعر الشراء (purchase_price)" if is_arabic else "purchase_price"
        ),
        "comments": "الملاحظات (comments)" if is_arabic else "comments",
    }

    def format_sort_col(col):
        return str(col_mapping.get(col, col))

    sort_cols = list(df_herd.columns)
    sort_col_display = col2.selectbox(
        "Sort by:" if not is_arabic else "الترتيب حسب:",
        options=sort_cols,
        format_func=format_sort_col,
    )
    sort_col = sort_col_display

    # Apply Filters
    df_filtered = df_herd.copy()
    if selected_status != "All":
        df_filtered = df_filtered[df_filtered["status"] == selected_status]

    # Apply Sorting
    df_filtered = df_filtered.sort_values(by=sort_col)

    # Prepare DataFrame view for Arabic if active
    display_audit_df = df_filtered.copy()
    if is_arabic:
        cat_map = {
            "Fattening": "تسمين",
            "Ewes": "نعاج",
            "Pregnant": "حامل",
            "Small - Female": "صغير - أنثى",
            "Small - Male": "صغير - ذكر",
        }
        stat_map = {
            "Active/Healthy": "نشط / سليم",
            "Sold": "مباع",
            "Slaughtered": "مذبوح",
            "Died": "نافق",
            "Zakate": "زكاة",
            "Donate": "تبرع",
        }
        if "category" in display_audit_df.columns:
            display_audit_df["category"] = (
                display_audit_df["category"]
                .map(cat_map)
                .fillna(display_audit_df["category"])
            )
        if "status" in display_audit_df.columns:
            display_audit_df["status"] = (
                display_audit_df["status"]
                .map(stat_map)
                .fillna(display_audit_df["status"])
            )

        display_audit_df = display_audit_df.rename(
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

    # 3. DISPLAY TABLE
    st.dataframe(display_audit_df, use_container_width=True, hide_index=True)

    # 4. PRINTABLE REPORT TIP
    st.info(
        "💡 Tip: Use 'Ctrl + P' to print this audit list."
        if not is_arabic
        else "💡 نصيحة: استخدم 'Ctrl + P' لطباعة قائمة التدقيق هذه."
    )

    # Quick Summary
    record_count_text = (
        f"Total records displayed: **{len(df_filtered)}**"
        if not is_arabic
        else f"إجمالي السجلات المعروضة: **{len(df_filtered)}**"
    )
    st.write(record_count_text)

else:
    st.warning(
        "No data found in the 'herd' table."
        if not is_arabic
        else "لم يتم العثور على بيانات في جدول القطيع."
    )
