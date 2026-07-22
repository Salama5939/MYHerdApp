import sys
import os
import streamlit as st
import pandas as pd
from datetime import date

# 🖥️ Force Wide Layout to use full screen space
st.set_page_config(page_title="Active Herd Registry", layout="wide")

# 📂 Tell Python to look one folder up to find your main cloud database.py file!
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# ☁️ Safely import your live Supabase database module & translation engine
import database as db
from translations import init_language_state, t, apply_rtl_styling

# 🔒 SECURITY ACCESS LOCK & LANGUAGE STATE INITIALIZATION
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

init_language_state()
apply_rtl_styling()

st.title(t("nav_2"))  # Dynamic Active Herd Registry title

# 🟢 Add Home Button
db.draw_home_button()

st.markdown("---")

# 🌾 Fetch Live Data directly from your Supabase PostgreSQL cloud tables
if "df_herd_cached" in st.session_state and st.session_state.df_herd_cached is not None:
    df_herd = st.session_state.df_herd_cached
else:
    try:
        df_herd = db.get_table_data("herd")
        st.session_state.df_herd_cached = df_herd
    except Exception as e:
        st.error(f"Supabase Connection Error: {e}")
        df_herd = pd.DataFrame(
            columns=[
                "tag_no",
                "category",
                "status",
                "birth_date",
                "registration_date",
                "purchase_price",
                "comments",
            ]
        )

# Check if Arabic is active for value mapping
is_arabic = st.session_state.get("language", "English") == "العربية (Arabic)"
from translations import TRANSLATIONS

ar_dict = TRANSLATIONS.get("العربية (Arabic)", {})

# 🗂️ Interactive Tabs for Data Entry and Off-Take
tab1_label = "Add Single New Entry" if not is_arabic else "إضافة سجل حيوان جديد"
tab2_label = (
    "Execute Status Off-Take Action"
    if not is_arabic
    else "تنفيذ إجراء استبعاد أو تغيير الحالة"
)
tab1, tab2 = st.tabs([tab1_label, tab2_label])

with tab1:
    with st.form("add_animal_form", clear_on_submit=True):
        st.subheader(
            "Register New Animal Parameters"
            if not is_arabic
            else "تسجيل بيانات حيوان جديد"
        )
        col1, col2 = st.columns(2)

        with col1:
            tag_no = st.text_input(
                "RFID Ear Tag Code (Unique ID):"
                if not is_arabic
                else "كود رقم الأذن الإلكتروني (RFID):"
            ).strip()

            # Category options & user-friendly labels mapping
            category_options = [
                "Fattening",
                "Ewes",
                "Pregnant",
                "Small - Female",
                "Small - Male",
            ]
            category_labels = {
                "Fattening": "Fattening (تسمين)" if is_arabic else "Fattening",
                "Ewes": "Ewes (نعاج)" if is_arabic else "Ewes",
                "Pregnant": "Pregnant (حامل)" if is_arabic else "Pregnant",
                "Small - Female": (
                    "Small - Female (صغير - أنثى)" if is_arabic else "Small - Female"
                ),
                "Small - Male": (
                    "Small - Male (صغير - ذكر)" if is_arabic else "Small - Male"
                ),
            }
            category = st.selectbox(
                (
                    "Herd Category Classification:"
                    if not is_arabic
                    else "تصنيف فئة القطيع:"
                ),
                options=category_options,
                format_func=lambda x: str(category_labels.get(x, x)),
            )

            status_options = [
                "Active/Healthy",
                "Sold",
                "Slaughtered",
                "Died",
                "Zakate",
                "Donate",
            ]
            status_labels = {
                "Active/Healthy": (
                    "Active/Healthy (نشط / سليم)" if is_arabic else "Active/Healthy"
                ),
                "Sold": "Sold (مباع)" if is_arabic else "Sold",
                "Slaughtered": "Slaughtered (مذبوح)" if is_arabic else "Slaughtered",
                "Died": "Died (نافق)" if is_arabic else "Died",
                "Zakate": "Zakate (زكاة)" if is_arabic else "Zakate",
                "Donate": "Donate (تبرع)" if is_arabic else "Donate",
            }
            status = st.selectbox(
                (
                    "Current Operational Status Level:"
                    if not is_arabic
                    else "مستوى الحالة التشغيلية الحالية:"
                ),
                options=status_options,
                format_func=lambda x: str(status_labels.get(x, x)),
            )

        with col2:
            birth_date = st.date_input(
                (
                    "Approximate Birth Date (Calendar):"
                    if not is_arabic
                    else "تاريخ الميلاد التقريبي:"
                ),
                value=date.today(),
            )
            reg_date = st.date_input(
                (
                    "Ledger Entry Registry Date:"
                    if not is_arabic
                    else "تاريخ تسجيل القيد:"
                ),
                value=date.today(),
            )
            price = st.number_input(
                (
                    "Purchase Price Value Amount ($):"
                    if not is_arabic
                    else "قيمة سعر الشراء ($):"
                ),
                min_value=0.0,
                step=50.0,
                value=0.0,
            )

        comments = st.text_area(
            "Structural Descriptive Comments / Observations:"
            if not is_arabic
            else "تعليقات وصفية أو ملاحظات هيكلية:"
        )
        submit_btn = st.form_submit_button(
            "Commit New Record to Ledger"
            if not is_arabic
            else "حفظ السجل الجديد في الدفتريات"
        )

        if submit_btn:
            if not tag_no:
                st.error(
                    "Validation Error: RFID Ear Tag Code cannot be empty."
                    if not is_arabic
                    else "خطأ في التحقق: لا يمكن ترك كود الأذن فارغاً."
                )
            elif not df_herd.empty and tag_no in df_herd["tag_no"].values:
                st.error(
                    f"Duplicate Row Exception: Tag '{tag_no}' already exists in data records."
                    if not is_arabic
                    else f"استثناء تكرار الصف: الكود '{tag_no}' موجود مسبقاً في سجلات القاعدة."
                )
            else:
                try:
                    db.add_animal(
                        tag_no,
                        category,
                        status,
                        str(birth_date),
                        str(reg_date),
                        price,
                        comments,
                    )
                    st.success(
                        f"Animal {tag_no} has been registered successfully."
                        if not is_arabic
                        else f"تم تسجيل الحيوان برقم {tag_no} بنجاح."
                    )
                    # Clear cache to force a fresh pull from Supabase on reload
                    st.session_state.pop("df_herd_cached", None)
                    st.rerun()
                except Exception as e:
                    st.error(
                        f"Database Error: Could not add animal. Details: {e}"
                        if not is_arabic
                        else f"خطأ في قاعدة البيانات: تعذر إضافة الحيوان. التفاصيل: {e}"
                    )

with tab2:
    st.subheader(
        "Process Off-Take / Change Operational Status"
        if not is_arabic
        else "معالجة الاستبعاد أو تغيير الحالة التشغيلية"
    )
    if df_herd.empty:
        st.warning(
            "No records found in database to modify."
            if not is_arabic
            else "لم يتم العثور على سجلات في قاعدة البيانات للتعديل."
        )
    else:
        # Filter for active animals to populate the dropdown
        active_list = df_herd[df_herd["status"] == "Active/Healthy"]["tag_no"].tolist()

        if not active_list:
            st.info(
                "No active animals are currently present in your herd ledger registry."
                if not is_arabic
                else "لا توجد حيوانات نشطة حالياً في سجل دفتر القطيع الخاص بك."
            )
        else:
            with st.form("status_offtake_form"):
                target_tag = st.selectbox(
                    (
                        "Select Target Ear Tag Code:"
                        if not is_arabic
                        else "اختر كود الأذن المستهدف:"
                    ),
                    active_list,
                )

                exit_actions = ["Sold", "Slaughtered", "Died", "Zakate", "Donate"]
                exit_labels = {
                    "Sold": "Sold (مباع)" if is_arabic else "Sold",
                    "Slaughtered": (
                        "Slaughtered (مذبوح)" if is_arabic else "Slaughtered"
                    ),
                    "Died": "Died (نافق)" if is_arabic else "Died",
                    "Zakate": "Zakate (زكاة)" if is_arabic else "Zakate",
                    "Donate": "Donate (تبرع)" if is_arabic else "Donate",
                }
                target_action = st.selectbox(
                    (
                        "Select Exit Action Description:"
                        if not is_arabic
                        else "اختر وصف إجراء الخروج/الاستبعاد:"
                    ),
                    exit_actions,
                    format_func=lambda x: exit_labels.get(x, str(x)),
                )
                sale_price = st.number_input(
                    (
                        "Observed Sale Price Value ($) - If applicable:"
                        if not is_arabic
                        else "قيمة سعر البيع المرصودة ($) - إن وجدت:"
                    ),
                    min_value=0.0,
                    step=100.0,
                    value=0.0,
                )
                transaction_date = st.date_input(
                    (
                        "Off-Take Execution Date:"
                        if not is_arabic
                        else "تاريخ تنفيذ الاستبعاد:"
                    ),
                    value=date.today(),
                )

                submit_action = st.form_submit_button(
                    "Execute Change Status Command"
                    if not is_arabic
                    else "تنفيذ أمر تغيير الحالة"
                )

                if submit_action:
                    try:
                        db.sell_or_slaughter_animal(
                            target_tag,
                            target_action,
                            sale_price,
                            transaction_date.isoformat(),
                        )
                        st.success(
                            f"Animal {target_tag} has been updated to '{target_action}' status successfully."
                            if not is_arabic
                            else f"تم تحديث الحيوان {target_tag} إلى حالة '{exit_labels.get(target_action, target_action)}' بنجاح."
                        )
                        # Clear cache to force a fresh pull from Supabase on reload
                        st.session_state.pop("df_herd_cached", None)
                        st.rerun()
                    except Exception as e:
                        st.error(
                            f"Database Error: Could not update animal. Details: {e}"
                            if not is_arabic
                            else f"خطأ في قاعدة البيانات: تعذر تحديث الحيوان. التفاصيل: {e}"
                        )

# 📋 Render the Main Registry Data Table View directly from the cloud with translated columns/values if Arabic
st.subheader(
    "Active Operations Tracking Matrix Grid"
    if not is_arabic
    else "مصفوفة تتبع العمليات النشطة"
)
if not df_herd.empty:
    display_df = df_herd.copy()
    if is_arabic:
        # Map categories and statuses for display elegance in Arabic view
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
        display_df["category"] = (
            display_df["category"].map(cat_map).fillna(display_df["category"])
        )
        display_df["status"] = (
            display_df["status"].map(stat_map).fillna(display_df["status"])
        )

    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.info(
        "📂 No active records found in the herd database table."
        if not is_arabic
        else "📂 لم يتم العثور على سجلات نشطة في جدول قاعدة بيانات القطيع."
    )
