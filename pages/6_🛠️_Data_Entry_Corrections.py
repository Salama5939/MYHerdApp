import streamlit as st
import sys
import os
import pandas as pd
import database as db
from translations import init_language_state, t, apply_rtl_styling

st.set_page_config(page_title="Data Entry Corrections", layout="wide")

# 🔒 SECURITY ACCESS LOCK & LANGUAGE INITIALIZATION
if "authenticated" not in st.session_state or not st.session_state.get(
    "authenticated", False
):
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

init_language_state()
apply_rtl_styling()

is_arabic = st.session_state.get("language", "English") == "العربية (Arabic)"

st.title(t("nav_6"))
db.draw_home_button()

# 1. Define the unique identifier for each table
pk_map = {"birth_records": "id", "herd": "tag_no"}

# 2. Select Table with translated display names if Arabic
table_options = list(pk_map.keys())
table_labels = {
    "birth_records": "Birth Records (سجلات الولادة)" if is_arabic else "birth_records",
    "herd": "Herd Registry (سجل القطيع)" if is_arabic else "herd",
}

table_choice_display = st.selectbox(
    (
        "Select the Database Table to view/edit:"
        if not is_arabic
        else "اختر جدول قاعدة البيانات لعرضه/تعديله:"
    ),
    options=table_options,
    format_func=lambda x: str(table_labels.get(x, x)),
)
table_choice = table_choice_display

# Determine the Primary Key for this table based on the selection
current_pk = pk_map[table_choice]

# ===================================================
# 📂 Path management
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# ===================================================

# 3. Fetch Data
try:
    df = db.get_table_data(table_choice)
    table_title_text = (
        f"Live Spreadsheet View: {table_choice}"
        if not is_arabic
        else f"عرض الجدول المباشر: {table_choice}"
    )
    st.write(f"### {table_title_text}")
    st.dataframe(df, use_container_width=True, hide_index=True)
except Exception as e:
    st.error(
        f"Error loading table: {e}" if not is_arabic else f"خطأ في تحميل الجدول: {e}"
    )
    st.stop()

# 4. Targeted Record Correction
st.markdown("---")
st.subheader(
    "🎯 " + ("Targeted Record Correction" if not is_arabic else "تصحيح سجل مستهدف")
)

col1, col2, col3 = st.columns(3)

# Use current_pk to dynamically look up the list of IDs
record_id_list = df[current_pk].astype(str).tolist()

with col1:
    record_id = st.selectbox(
        f"1. {'Select Record by' if not is_arabic else 'اختر السجل بواسطة'} {current_pk}:",
        record_id_list,
    )

with col2:
    # Filter out the PK so we don't accidentally rename the ID itself
    columns = [c for c in df.columns if c != current_pk]
    column_to_edit = st.selectbox(
        "2. "
        + (
            "Select Column to Correct:"
            if not is_arabic
            else "اختر العمود المراد تصحيحه:"
        ),
        columns,
    )

with col3:
    new_value = st.text_input(
        "3. "
        + (
            "Enter The New Correct Value:"
            if not is_arabic
            else "أدخل القيمة الصحيحة الجديدة:"
        )
    )

# 5. Commit Actions
col_a, col_b = st.columns(2)

with col_a:
    commit_btn_label = "Commit Correction" if not is_arabic else "اعتماد التصحيح"
    if st.button(commit_btn_label, type="primary"):
        try:
            db.update_table_record(
                table_choice, current_pk, record_id, column_to_edit, new_value
            )
            success_msg = (
                f"Success! Record {record_id} updated."
                if not is_arabic
                else f"نجاح! تم تحديث السجل {record_id}."
            )
            st.success(success_msg)
            st.rerun()
        except Exception as e:
            st.error(f"Update failed: {e}" if not is_arabic else f"فشل التحديث: {e}")

with col_b:
    delete_btn_label = (
        "DELETE RECORD (Permanent)" if not is_arabic else "حذف السجل (نهائي)"
    )
    if st.button(delete_btn_label, type="secondary"):
        try:
            db.delete_table_record(table_choice, current_pk, record_id)
            warning_msg = (
                f"Deleted Record {record_id}."
                if not is_arabic
                else f"تم حذف السجل {record_id}."
            )
            st.warning(warning_msg)
            st.rerun()
        except Exception as e:
            st.error(f"Delete failed: {e}" if not is_arabic else f"فشل الحذف: {e}")
