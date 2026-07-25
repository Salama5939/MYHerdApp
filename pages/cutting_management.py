from datetime import datetime
import streamlit as st
import database as db


# Robust translation helper checking all possible app language session keys
def t(en_text, ar_text):
    is_ar = (
        st.session_state.get("is_arabic", False)
        or st.session_state.get("language") == "Arabic"
        or st.session_state.get("lang") == "ar"
        or "عربي" in str(st.session_state.get("language", ""))
    )
    return ar_text if is_ar else en_text


# Page Configuration
st.set_page_config(
    page_title=t("Cutting & Butcher Management", "إدارة التقطيع والجزارين"),
    layout="wide",
)

st.title(
    t(
        "🥩 Customer Cutting Orders & Butcher Performance",
        "🥩 طلبات تقطيع اللحوم وأداء الجزارين",
    )
)
st.markdown(
    t(
        "Manage customer processing specs, box wrapping preferences, and track butcher productivity.",
        "إدارة مواصفات تقطيع العملاء، تفضيلات التعبئة والتغليف، وتتبع إنتاجية الجزارين.",
    )
)

# Robustly retrieve the authenticated Supabase client from session state or database module
supabase = st.session_state.get("supabase")
if not supabase:
    supabase = getattr(db, "supabase", None)

if not supabase:
    st.error(
        t(
            "Database connection not found. Please ensure Supabase is initialized.",
            "تعذر الاتصال بقاعدة البيانات. يرجى التأكد من إعدادات الاتصال.",
        )
    )
    st.stop()

# Tabs
tab1, tab2, tab3 = st.tabs(
    [
        t("📝 New Cutting Order", "📝 طلب تقطيع جديد"),
        t("📦 Order Status & Tracking", "📦 متابعة حالة الطلبات"),
        t("⚡ Butcher Performance Logs", "⚡ سجلات أداء الجزارين"),
    ]
)

# ==========================================
# TAB 1: NEW CUTTING ORDER
# ==========================================
with tab1:
    st.subheader(t("New Processing & Cutting Order", "تسجيل طلب تجهيز وتقطيع جديد"))

    with st.form("cutting_order_form"):
        st.markdown(t("### 1. Customer Information", "### 1. بيانات العميل"))
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input(t("Customer Name *", "اسم العميل *"))
            mobile_number = st.text_input(
                t("Mobile Number * (Unique ID)", "رقم الجوال * (معرف فريد)")
            )
        with col2:
            contact_name = st.text_input(
                t(
                    "Contact / Representative Name (Optional)",
                    "اسم المسؤول / المندوب (اختياري)",
                )
            )
            address = st.text_area(t("Delivery Address", "عنوان التوصيل"))

        st.markdown(t("### 2. Logistics & Packaging", "### 2. اللوجستيات والتعبئة"))
        col3, col4 = st.columns(2)
        with col3:
            delivery_date = st.date_input(
                t("Delivery Date", "تاريخ التوصيل"), value=datetime.today().date()
            )
        with col4:
            delivery_time = st.time_input(t("Delivery Time", "وقت التوصيل"))

        target_box_weight = st.number_input(
            t(
                "Target Box Weight for Wrapping (kg)",
                "وزن الصندوق المستهدف للتغليف (كجم)",
            ),
            min_value=0.5,
            max_value=50.0,
            value=5.0,
            step=0.5,
        )

        st.markdown(
            t(
                "### 3. Cut Pieces Definition (Check requested parts)",
                "### 3. تحديد أجزاء الذبيحة (حدد الأجزاء المطلوبة)",
            )
        )
        st.info(
            t(
                "Check all parts the customer wants included in their cut package.",
                "حدد جميع الأجزاء التي يريدها العميل ضمن الحزمة الخاص به.",
            )
        )

        # 12 Parts Checkbox Grid
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            p_head = st.checkbox(t("Head", "الرأس"), value=True)
            p_neck = st.checkbox(t("Neck", "الرقبة"), value=True)
            p_r_shoulder = st.checkbox(t("Right Shoulder", "الكتف الأيمن"), value=True)
        with c2:
            p_l_shoulder = st.checkbox(t("Left Shoulder", "الكتف الأيسر"), value=True)
            p_ribs = st.checkbox(t("Ribs", "الضلوع"), value=True)
            p_r_thigh = st.checkbox(t("Right Thigh", "الفخذ الأيمن"), value=True)
        with c3:
            p_l_thigh = st.checkbox(t("Left Thigh", "الفخذ الأيسر"), value=True)
            p_lungs = st.checkbox(t("Lungs", "الرئتان"), value=False)
            p_heart = st.checkbox(t("Heart", "القلب"), value=True)
        with c4:
            p_liver = st.checkbox(t("Liver", "الكبد"), value=True)
            p_intestine = st.checkbox(
                t("Small Intestine", "الأمعاء الدقيقة"), value=False
            )
            p_liyya = st.checkbox(t("Liyya (Fat Tail)", "الليّة (الألية)"), value=True)

        special_instructions = st.text_area(
            t(
                "Special Cutting & Packaging Instructions",
                "تعليمات التطيع والتعبئة الخاصة",
            ),
            placeholder=t(
                "E.g., Chop ribs small for grilling, keep Liyya in a separate container...",
                "مثال: تقطيع الضلوع بحجم صغير للشواء، وضع الليّة في وعاء منفصل...",
            ),
        )

        submit_order = st.form_submit_button(
            t("💾 Save & Register Cutting Order", "💾 حفظ وتسجيل طلب التطيع"),
            type="primary",
        )

        if submit_order:
            if not customer_name or not mobile_number:
                st.error(
                    t(
                        "Please fill in at least the Customer Name and Mobile Number.",
                        "يرجى إدخال اسم العميل ورقم الجوال على الأقل.",
                    )
                )
            else:
                delivery_datetime = datetime.combine(delivery_date, delivery_time)

                cust_id = db.get_or_create_customer(
                    supabase, customer_name, mobile_number, address, contact_name
                )

                if cust_id:
                    parts_data = {
                        "part_head": p_head,
                        "part_neck": p_neck,
                        "part_right_shoulder": p_r_shoulder,
                        "part_left_shoulder": p_l_shoulder,
                        "part_ribs": p_ribs,
                        "part_right_thigh": p_r_thigh,
                        "part_left_thigh": p_l_thigh,
                        "part_lungs": p_lungs,
                        "part_heart": p_heart,
                        "part_liver": p_liver,
                        "part_small_intestine": p_intestine,
                        "part_liyya": p_liyya,
                    }

                    success = db.save_cutting_order(
                        supabase,
                        cust_id,
                        delivery_datetime,
                        target_box_weight,
                        special_instructions,
                        parts_data,
                    )
                    if success:
                        st.success(
                            t(
                                f"Cutting order successfully registered for {customer_name}!",
                                f"تم تسجيل طلب التطيع بنجاح للعميل: {customer_name}!",
                            )
                        )
                    else:
                        st.error(
                            t(
                                "Failed to save the cutting order. Please check database connection.",
                                "فشل حفظ طلب التطيع. يرجى التحقق من اتصال قاعدة البيانات.",
                            )
                        )
                else:
                    st.error(
                        t(
                            "Could not register or retrieve customer profile.",
                            "تعذر تسجيل أو استرجاع بيانات العميل.",
                        )
                    )

# ==========================================
# TAB 2: ORDER STATUS & TRACKING
# ==========================================
with tab2:
    st.subheader(t("Active Cutting Orders", "طلبات التطيع النشطة والحالية"))
    try:
        orders = db.get_all_cutting_orders(supabase)
        customers_map = db.get_customers_lookup(supabase)

        if not orders:
            st.info(
                t("No cutting orders found yet.", "لا توجد طلبات تقطيع مسجلة حتى الآن.")
            )
        else:
            for order in orders:
                cust_info = customers_map.get(order.get("customer_id"), {})
                c_name = cust_info.get("customer_name", t("Unknown", "غير معروف"))
                c_mobile = cust_info.get("mobile_number", "")

                status_map_ar = {
                    "Pending": "قيد الانتظار",
                    "Processing": "قيد التجهيز",
                    "Ready": "جاهز",
                    "Delivered": "تم التوصيل",
                }
                is_ar_active = (
                    st.session_state.get("is_arabic", False)
                    or st.session_state.get("language") == "Arabic"
                    or st.session_state.get("lang") == "ar"
                    or "عربي" in str(st.session_state.get("language", ""))
                )
                current_status_disp = (
                    status_map_ar.get(order["status"], order["status"])
                    if is_ar_active
                    else order["status"]
                )

                with st.expander(
                    f"Order #{order['order_id']} — {c_name} ({c_mobile}) | Status: {current_status_disp}"
                ):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(
                            f"**{t('Delivery Time:', 'وقت التوصيل:')}** {order['delivery_datetime']}"
                        )
                        st.write(
                            f"**{t('Box Weight:', 'وزن الصندوق:')}** {order['target_box_weight_kg']} kg"
                        )
                        st.write(
                            f"**{t('Special Instructions:', 'تعليمات خاصة:')}** {order.get('special_instructions', t('None', 'لا توجد'))}"
                        )
                    with col_b:
                        st.write(f"**{t('Included Parts:', 'الأجزاء المطلوبة:')}**")

                        parts_en_names = {
                            "head": "Head",
                            "neck": "Neck",
                            "right shoulder": "Right Shoulder",
                            "left shoulder": "Left Shoulder",
                            "ribs": "Ribs",
                            "right thigh": "Right Thigh",
                            "left thigh": "Left Thigh",
                            "lungs": "Lungs",
                            "heart": "Heart",
                            "liver": "Liver",
                            "small intestine": "Small Intestine",
                            "liyya": "Liyya",
                        }
                        parts_ar_names = {
                            "head": "الرأس",
                            "neck": "الرقبة",
                            "right shoulder": "الكتف الأيمن",
                            "left shoulder": "الكتف الأيسر",
                            "ribs": "الضلوع",
                            "right thigh": "الفخذ الأيمن",
                            "left thigh": "الفخذ الأيسر",
                            "lungs": "الرئتان",
                            "heart": "القلب",
                            "liver": "الكبد",
                            "small intestine": "الأمعاء الدقيقة",
                            "liyya": "الليّة",
                        }

                        raw_parts = [
                            k.replace("part_", "").replace("_", " ")
                            for k, v in order.items()
                            if k.startswith("part_") and v is True
                        ]
                        if is_ar_active:
                            parts_list = [
                                str(parts_ar_names.get(p, p)) for p in raw_parts
                            ]
                            st.write(
                                "، ".join(parts_list)
                                if parts_list
                                else "لا توجد أجزاء محددة"
                            )
                        else:
                            parts_list = [
                                str(parts_en_names.get(p, p)).title() for p in raw_parts
                            ]
                            st.write(
                                ", ".join(parts_list) if parts_list else "None selected"
                            )

                    status_options = ["Pending", "Processing", "Ready", "Delivered"]
                    status_labels = (
                        ["Pending", "Processing", "Ready", "Delivered"]
                        if not is_ar_active
                        else ["قيد الانتظار", "قيد التجهيز", "جاهز", "تم التوصيل"]
                    )

                    current_idx = (
                        status_options.index(order["status"])
                        if order["status"] in status_options
                        else 0
                    )

                    new_status_selection = st.selectbox(
                        t("Update Status", "تحديث حالة الطلب"),
                        status_labels,
                        index=current_idx,
                        key=f"status_{order['order_id']}",
                    )

                    if is_ar_active:
                        new_status = status_options[
                            status_labels.index(new_status_selection)
                        ]
                    else:
                        new_status = new_status_selection

                    if st.button(
                        t("Update Status", "تحديث الحالة"),
                        key=f"btn_{order['order_id']}",
                    ):
                        db.update_order_status_db(
                            supabase, order["order_id"], new_status
                        )
                        st.success(
                            t(
                                f"Order #{order['order_id']} status updated to {new_status}!",
                                f"تم تحديث حالة الطلب #{order['order_id']} بنجاح!",
                            )
                        )
                        st.rerun()

    except Exception as e:
        st.error(t(f"Error loading orders: {e}", f"خطأ أثناء تحميل الطلبات: {e}"))

# ==========================================
# TAB 3: BUTCHER PERFORMANCE LOGS
# ==========================================
with tab3:
    st.subheader(
        t("Butcher Performance & Productivity Tracking", "تتبع أداء وإنتاجية الجزارين")
    )

    with st.expander(t("➕ Add New Butcher to System", "➕ إضافة جزار جديد للنظام")):
        with st.form("add_butcher_form"):
            b_name = st.text_input(t("Butcher Name", "اسم الجزار"))
            b_phone = st.text_input(t("Phone Number", "رقم الجوال"))
            submit_b = st.form_submit_button(t("Save Butcher", "حفظ الجزار"))
            if submit_b and b_name:
                supabase.table("butchers").insert(
                    {"butcher_name": b_name, "phone_number": b_phone, "is_active": True}
                ).execute()
                st.success(
                    t(
                        f"Butcher {b_name} added successfully!",
                        f"تم إضافة الجزار {b_name} بنجاح!",
                    )
                )
                st.rerun()

    st.markdown(
        t("### Log Daily / Hourly Work Output", "### تسجيل العمل اليومي / الساعي")
    )
    butchers = db.get_all_butchers(supabase)

    if not butchers:
        st.warning(
            t(
                "No active butchers found. Please add a butcher above first.",
                "لم يتم العثور على جزارين نشطين. يرجى إضافة جزار أولاً من القائمة أعلاه.",
            )
        )
    else:
        butcher_options = {b["butcher_name"]: b["butcher_id"] for b in butchers}

        with st.form("performance_log_form"):
            selected_butcher_name = st.selectbox(
                t("Select Butcher", "اختر الجزار"), list(butcher_options.keys())
            )
            work_date = st.date_input(
                t("Work Date", "تاريخ العمل"), value=datetime.today().date()
            )

            col_h1, col_h2 = st.columns(2)
            with col_h1:
                shift_hours = st.number_input(
                    t("Shift Hours Worked", "ساعات العمل المنقضية"),
                    min_value=0.5,
                    max_value=24.0,
                    value=8.0,
                    step=0.5,
                )
            with col_h2:
                is_ar_active = (
                    st.session_state.get("is_arabic", False)
                    or st.session_state.get("language") == "Arabic"
                    or st.session_state.get("lang") == "ar"
                    or "عربي" in str(st.session_state.get("language", ""))
                )
                role_options = (
                    ["Slaughtering", "Cutting"]
                    if not is_ar_active
                    else ["ذبح", "تقطيع"]
                )
                task_role_selection = st.selectbox(
                    t("Task Role", "الدور / المهمة"),
                    role_options,
                    help=t(
                        "Butchers can handle either slaughtering or cutting per shift block.",
                        "يمكن للجزار أداء مهام الذبح أو التقطيع خلال وردية العمل.",
                    ),
                )
                if is_ar_active:
                    task_role = (
                        "Slaughtering" if task_role_selection == "ذبح" else "Cutting"
                    )
                else:
                    task_role = task_role_selection

            units_completed = st.number_input(
                t(
                    "Units Completed (Animals Slaughtered or Orders Cut)",
                    "الوحدات المنجزة (عدد الذبائح المذبوحة أو الطلبات المقطعة)",
                ),
                min_value=1,
                value=1,
                step=1,
            )
            notes = st.text_area(
                t("Performance Notes / Remarks", "ملاحظات الأداء / تفاصيل إضافية")
            )

            submit_log = st.form_submit_button(
                t("📊 Log Performance", "📊 تسجيل الأداء"), type="primary"
            )

            if submit_log:
                butcher_id = butcher_options[selected_butcher_name]
                logged = db.log_butcher_performance(
                    supabase,
                    butcher_id,
                    None,
                    work_date,
                    shift_hours,
                    task_role,
                    units_completed,
                    notes,
                )
                if logged:
                    st.success(
                        t(
                            "Performance log saved successfully!",
                            "تم تسجيل الأداء بنجاح!",
                        )
                    )
                else:
                    st.error(
                        t("Failed to save performance log.", "فشل حفظ سجل الأداء.")
                    )

    st.markdown(t("### Recent Productivity Logs", "### سجلات الإنتاجية الحديثة"))
    try:
        logs = db.get_all_performance_logs(supabase)
        butchers_map = db.get_butchers_lookup(supabase)

        if logs:
            table_data = []
            for l in logs:
                b_name = butchers_map.get(
                    l.get("butcher_id"), t("Unknown", "غير معروف")
                )
                is_ar_active = (
                    st.session_state.get("is_arabic", False)
                    or st.session_state.get("language") == "Arabic"
                    or st.session_state.get("lang") == "ar"
                    or "عربي" in str(st.session_state.get("language", ""))
                )
                if is_ar_active:
                    role_disp = "ذبح" if l["task_role"] == "Slaughtering" else "تقطيع"
                    table_data.append(
                        {
                            "التاريخ": l["work_date"],
                            "الجزار": b_name,
                            "المهمة": role_disp,
                            "الساعات": l["shift_hours"],
                            "الوحدات المنجزة": l["units_completed"],
                            "الملاحظات": l.get("performance_notes", ""),
                        }
                    )
                else:
                    table_data.append(
                        {
                            "Date": l["work_date"],
                            "Butcher": b_name,
                            "Role": l["task_role"],
                            "Hours": l["shift_hours"],
                            "Units Completed": l["units_completed"],
                            "Notes": l.get("performance_notes", ""),
                        }
                    )
            st.dataframe(table_data, use_container_width=True)
        else:
            st.info(
                t(
                    "No performance logs recorded yet.",
                    "لم يتم تسجيل أي بيانات أداء حتى الآن.",
                )
            )
    except Exception as e:
        st.error(t(f"Error loading logs: {e}", f"خطأ أثناء تحميل السجلات: {e}"))
