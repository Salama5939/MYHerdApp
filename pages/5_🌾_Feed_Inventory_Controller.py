from datetime import date
import sys
import os
import streamlit as st
import pandas as pd

# 🖥️ Force Wide Layout to use full screen space
st.set_page_config(page_title="Feed Inventory Controller", layout="wide")

# 📂 Path setup to find your database.py file
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import database as db
from translations import init_language_state, t, apply_rtl_styling

# 🔒 SECURITY ACCESS LOCK & LANGUAGE INITIALIZATION
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

init_language_state()
apply_rtl_styling()

is_arabic = st.session_state.get("language", "English") == "العربية (Arabic)"

st.title(t("nav_5"))

# 🟢 Add Home Button
db.draw_home_button()

st.markdown("---")
st.subheader(
    "🧪 Interactive Feed Recipe Cost Formulation Desks"
    if not is_arabic
    else "🧪 مكاتب صياغة تكلفة وصفات الأعلاف التفاعلية"
)

# ⚡ LIVE CLOUD DATA EXTRACTION
try:
    df_inv = db.get_table_data("inventory")
    df_recipes = db.get_table_data("feed_recipes")

    # Update session cache for the dynamic sliders
    st.session_state.cached_recipes = df_recipes
except Exception as e:
    st.error(
        f"Cloud Connection Error: {e}"
        if not is_arabic
        else f"خطأ في الاتصال بالسحاب: {e}"
    )
    df_inv = pd.DataFrame()
    df_recipes = pd.DataFrame()

# --- SETUP LIVE RENDER OBJECTS ---
if not df_inv.empty and "is_active" in df_inv.columns:
    df_active = df_inv[df_inv["is_active"] == 1]
    df_inactive = df_inv[df_inv["is_active"] == 0]
else:
    df_active = df_inv.copy()
    df_inactive = pd.DataFrame()

active_item_options = df_active["item_name"].tolist() if not df_active.empty else []

if df_inv.empty:
    st.warning(
        "⚠️ Feed stock database is currently empty. Please register your first commodity record below!"
        if not is_arabic
        else "⚠️ قاعدة بيانات مخزون الأعلاف فارغة حالياً. يرجى تسجيل سجل السلعة الأول أدناه!"
    )
    df_active_sliders = pd.DataFrame()
else:
    df_active_sliders = df_active

# Create ingredient price map dynamically
price_lookup = {
    row["item_name"]: float(row["cost_per_kg"])
    for _, row in df_active_sliders.iterrows()
}

cost_summary = " | ".join(
    [f"{name}: **${cost}/kg**" for name, cost in price_lookup.items()]
)
if cost_summary:
    st.markdown(
        f"**{'Current Ingredient Costs' if not is_arabic else 'تكاليف المكونات الحالية'}:** {cost_summary}"
    )


# Helper function to decode values stored in the breakdown column
def get_saved_ratio_dynamic(recipe_type, item_name):
    cached_df = st.session_state.get("cached_recipes", pd.DataFrame())
    if not cached_df.empty:
        match = cached_df[cached_df["recipe_type"] == recipe_type]
        if not match.empty and "recipe_breakdown" in match.columns:
            breakdown = str(match["recipe_breakdown"].values[0])
            if breakdown and ":" in breakdown:
                parts = breakdown.split(";")
                for part in parts:
                    if ":" in part:
                        name, val = part.split(":")
                        if name.strip() == item_name.strip():
                            try:
                                return int(val)
                            except ValueError:
                                return 0
    return 0


# --- FORECAST ENGINE ---
def get_3_week_forecast():
    df_herd = db.get_table_data("herd")
    df_std = db.get_table_data("feeding_standards")
    df_recipes = db.get_table_data("feed_recipes")
    df_inv = db.get_table_data("inventory")

    if df_herd.empty or df_std.empty or df_recipes.empty:
        return None

    active_herd = df_herd[df_herd["status"] == "Active/Healthy"]
    category_counts = active_herd.groupby("category").size()

    recipe_map = {
        "Pregnant": "General Herd",
        "Ewes": "General Herd",
        "Permanent Sire": "General Herd",
        "(Small) (Female)": "General Herd",
        "(Small) (Male)": "General Herd",
        "Fattening": "Fattening",
    }

    ingredient_needs = {}

    for cat, count in category_counts.items():
        std_row = df_std[df_std["category"] == cat]
        if std_row.empty:
            continue
        ration = float(std_row.iloc[0]["daily_ration_kg"])

        target_recipe = recipe_map.get(str(cat), str(cat))
        rec_row = df_recipes[df_recipes["recipe_type"] == target_recipe]
        if rec_row.empty:
            continue

        breakdown = str(rec_row.iloc[0]["recipe_breakdown"])
        total_21d_demand = count * ration * 21

        if ":" in breakdown:
            parts = breakdown.split(";")
            for part in parts:
                if ":" in part:
                    ing, pct = part.split(":")
                    pct = float(pct) / 100
                    ingredient_needs[ing.strip()] = ingredient_needs.get(
                        ing.strip(), 0
                    ) + (total_21d_demand * pct)

    forecast_data = []
    for ing, needed in ingredient_needs.items():
        stock = 0.0
        if not df_inv.empty and ing in df_inv["item_name"].values:
            stock = float(df_inv[df_inv["item_name"] == ing]["quantity_kg"].values[0])

        forecast_data.append(
            {
                "Ingredient" if not is_arabic else "المكون": ing,
                "Needed (21 Days)" if not is_arabic else "الاحتياج (21 يوم)": round(
                    needed, 2
                ),
                "Current Stock" if not is_arabic else "المخزون الحالي": round(stock, 2),
                "Gap (To Purchase)" if not is_arabic else "العجز (للشراء)": round(
                    max(0, needed - stock), 2
                ),
            }
        )

    return pd.DataFrame(forecast_data)


# --- DRAWING THE INTERACTIVE RECIPE SLIDER ENGAGEMENT DESK ---
tab1_label = "Fattening Formulation" if not is_arabic else "تركيبة التسمين"
tab2_label = "General Herd Formulation" if not is_arabic else "تركيبة القطيع العام"
tab3_label = "📊 3-Week Forecast" if not is_arabic else "📊 توقعات 3 أسابيع"

tab1, tab2, tab_forecast = st.tabs([tab1_label, tab2_label, tab3_label])

# 🧪 TAB 1: FATTENING FORMULATION MATRIX
with tab1:
    st.markdown(
        "#### "
        + (
            "Adjust Fattening Ingredient Ratios (%)"
            if not is_arabic
            else "ضبط نسب مكونات التسمين (%)"
        )
    )
    ratios_fattening = {}
    for _, row in df_active_sliders.iterrows():
        ing_name = row["item_name"]
        default_val = get_saved_ratio_dynamic("Fattening", ing_name)
        ratios_fattening[ing_name] = st.slider(
            f"{'Ratio for' if not is_arabic else 'نسبة'} {ing_name} (%)",
            0,
            100,
            default_val,
            key=f"fattening_slide_{ing_name}",
        )

    total_fattening = sum(ratios_fattening.values())
    st.metric(
        "Total Formulation Sum:" if not is_arabic else "إجمالي مجموع التركيبة:",
        f"{total_fattening} %",
    )

    blend_cost_fattening = sum(
        (ratios_fattening[name] / 100.0) * price_lookup[name]
        for name in ratios_fattening
    )
    st.info(
        f"**{'Calculated Blended Fattening Feed Cost:' if not is_arabic else 'تكلفة علف التسمين المخلوط المحسوبة:'}** $ {blend_cost_fattening:.2f} per kg"
    )

    if st.button(
        (
            "Save Fattening Blend Specification Parameters"
            if not is_arabic
            else "حفظ مواصفات خليط التسمين"
        ),
        key="save_fattening_btn",
    ):
        if total_fattening != 100:
            st.error(
                "Ratios must sum to exactly 100% before saving."
                if not is_arabic
                else "يجب أن تكون النسبة المئوية الإجمالية مساوية لـ 100% تماماً قبل الحفظ."
            )
        else:
            breakdown_str = ";".join([f"{k}:{v}" for k, v in ratios_fattening.items()])
            try:
                query = """
                    INSERT INTO feed_recipes (recipe_type, calculated_mix_cost_per_kg, recipe_breakdown) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (recipe_type) 
                    DO UPDATE SET 
                        calculated_mix_cost_per_kg = EXCLUDED.calculated_mix_cost_per_kg,
                        recipe_breakdown = EXCLUDED.recipe_breakdown;
                """
                db.execute_custom_query(
                    query,
                    ("Fattening", blend_cost_fattening, breakdown_str),
                    is_select=False,
                )
                st.success(
                    "Fattening feed parameters committed successfully to the cloud!"
                    if not is_arabic
                    else "تم حفظ معاملات علف التسمين بنجاح في السحاب!"
                )
                st.rerun()
            except Exception as e:
                st.error(
                    f"Database Execution Error: {e}"
                    if not is_arabic
                    else f"خطأ في تنفيذ قاعدة البيانات: {e}"
                )

# 🧪 TAB 2: GENERAL HERD FORMULATION MATRIX
with tab2:
    st.markdown(
        "#### "
        + (
            "Adjust General Herd Ingredient Ratios (%)"
            if not is_arabic
            else "ضبط نسب مكونات القطيع العام (%)"
        )
    )
    ratios_general = {}
    for _, row in df_active_sliders.iterrows():
        ing_name = row["item_name"]
        default_val = get_saved_ratio_dynamic("General Herd", ing_name)
        ratios_general[ing_name] = st.slider(
            f"{'Ratio for' if not is_arabic else 'نسبة'} {ing_name} (%)",
            0,
            100,
            default_val,
            key=f"general_slide_{ing_name}",
        )

    total_general = sum(ratios_general.values())
    st.metric(
        "Total Formulation Sum:" if not is_arabic else "إجمالي مجموع التركيبة:",
        f"{total_general} %",
    )

    blend_cost_general = sum(
        (ratios_general[name] / 100.0) * price_lookup[name] for name in ratios_general
    )
    st.info(
        f"**{'Calculated Blended General Feed Cost:' if not is_arabic else 'تكلفة العلف المخلوط للقطيع العام المحسوبة:'}** $ {blend_cost_general:.2f} per kg"
    )

    if st.button(
        (
            "Save General Herd Blend Specification Parameters"
            if not is_arabic
            else "حفظ مواصفات خليط القطيع العام"
        ),
        key="save_general_btn",
    ):
        if total_general != 100:
            st.error(
                "Ratios must sum to exactly 100% before saving."
                if not is_arabic
                else "يجب أن تكون النسبة المئوية الإجمالية مساوية لـ 100% تماماً قبل الحفظ."
            )
        else:
            breakdown_str = ";".join([f"{k}:{v}" for k, v in ratios_general.items()])
            try:
                query = """
                    INSERT INTO feed_recipes (recipe_type, calculated_mix_cost_per_kg, recipe_breakdown) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (recipe_type) 
                    DO UPDATE SET 
                        calculated_mix_cost_per_kg = EXCLUDED.calculated_mix_cost_per_kg,
                        recipe_breakdown = EXCLUDED.recipe_breakdown;
                """
                db.execute_custom_query(
                    query,
                    ("General Herd", blend_cost_general, breakdown_str),
                    is_select=False,
                )
                st.success(
                    "General Herd feed parameters committed successfully to the cloud!"
                    if not is_arabic
                    else "تم حفظ معاملات علف القطيع العام بنجاح في السحاب!"
                )
                st.rerun()
            except Exception as e:
                st.error(
                    f"Database Execution Error: {e}"
                    if not is_arabic
                    else f"خطأ في تنفيذ قاعدة البيانات: {e}"
                )

# --- 3-WEEK FORECAST ---
with tab_forecast:
    st.markdown(
        "### "
        + (
            "📅 Demand vs. Stock Forecast (Next 21 Days)"
            if not is_arabic
            else "📅 توقعات الطلب مقابل المخزون (الـ 21 يوماً القادمة)"
        )
    )
    forecast_df = get_3_week_forecast()

    if forecast_df is not None and not forecast_df.empty:
        st.dataframe(forecast_df, use_container_width=True, hide_index=True)

        for _, row in forecast_df.iterrows():
            ing_col = "Ingredient" if not is_arabic else "المكون"
            stock_col = "Current Stock" if not is_arabic else "المخزون الحالي"
            needed_col = "Needed (21 Days)" if not is_arabic else "الاحتياج (21 يوم)"
            gap_col = "Gap (To Purchase)" if not is_arabic else "العجز (للشراء)"

            if row[stock_col] == 0 and row[needed_col] > 0:
                st.error(
                    f"🚨 ALERT: {row[ing_col]} is completely OUT OF STOCK! Purchase **{row[gap_col]} kg** immediately."
                    if not is_arabic
                    else f"🚨 تنبيه: {row[ing_col]} نافد تماماً من المخزون! قم بشراء **{row[gap_col]} كجم** فوراً."
                )
            elif row[gap_col] > 0:
                st.warning(
                    f"⚠️ Need: {row[gap_col]} kg of {row[ing_col]}."
                    if not is_arabic
                    else f"⚠️ الاحتياج: {row[gap_col]} كجم من {row[ing_col]}."
                )
            else:
                st.success(
                    f"✅ {row[ing_col]} stock is sufficient."
                    if not is_arabic
                    else f"✅ مخزون {row[ing_col]} كافٍ."
                )
    else:
        st.info(
            "Ensure all herd groups have registered feeding standards and recipes to see the forecast."
            if not is_arabic
            else "تأكد من تسجيل معايير التغذية ووصفات الأعلاف لجميع مجموعات القطيع لرؤية التوقعات."
        )

# --- SUB-PANEL B: ADVANCED WAREHOUSE INVENTORY MANAGEMENT DESK ---
st.markdown("---")
st.subheader(
    "📦 Warehouse Inventory Control Desk"
    if not is_arabic
    else "📦 مكتب تحكم مخزون المستودع"
)

# --- STEP 1: REGISTRATION FORM DIRECT TO ISOLATED LEDGER ---
st.markdown(
    "### " + ("Initial Item Setup" if not is_arabic else "إعداد صنف جديد أولياً")
)
with st.form(key="new_ingredient_registration_form"):
    col_reg1, col_reg2 = st.columns(2)
    with col_reg1:
        new_item_name = st.text_input(
            (
                "Type Brand New Ingredient Name (e.g., Wheat, Radda):"
                if not is_arabic
                else "اكتب اسم المكون الجديد (مثل: قمح، ردة):"
            ),
            value="",
        ).strip()
    with col_reg2:
        new_item_cost = st.number_input(
            (
                "Set Baseline Unit Cost per 1 kg ($):"
                if not is_arabic
                else "حدد تكلفة الوحدة الأساسية لكل 1 كجم ($):"
            ),
            min_value=0.0,
            step=0.1,
            value=15.0,
        )

    submit_registration = st.form_submit_button(
        "Register Ingredient with 0.0 kg Stock"
        if not is_arabic
        else "تسجيل المكون بمخزون 0.0 كجم"
    )

    if submit_registration:
        if new_item_name == "":
            st.error(
                "❌ Registration failed: Ingredient name cannot be empty."
                if not is_arabic
                else "❌ فشل التسجيل: لا يمكن ترك اسم المكون فارغاً."
            )
        else:
            try:
                existing = db.execute_custom_query(
                    "SELECT 1 FROM inventory WHERE item_name = %s", (new_item_name,)
                )

                if isinstance(existing, pd.DataFrame) and not existing.empty:
                    st.warning(
                        f"ℹ️ '{new_item_name}' already exists in your cloud catalog."
                        if not is_arabic
                        else f"ℹ️ '{new_item_name}' موجود بالفعل في كتالوج السحاب الخاص بك."
                    )
                else:
                    db.execute_custom_query(
                        """
                        INSERT INTO inventory (item_name, quantity_kg, reorder_level_kg, cost_per_kg, is_active)
                        VALUES (%s, 0.0, 100.0, %s, 1)
                        """,
                        (new_item_name, new_item_cost),
                        is_select=False,
                    )
                    st.success(
                        f"🎉 Success! '{new_item_name}' registered into the cloud ledger."
                        if not is_arabic
                        else f"🎉 نجاح! تم تسجيل '{new_item_name}' في دفتر السحاب."
                    )
                    st.rerun()
            except Exception as e:
                st.error(
                    f"❌ Database error: {e}"
                    if not is_arabic
                    else f"❌ خطأ في قاعدة البيانات: {e}"
                )

# --- UPDATED TAB MANAGEMENT W/ MODIFY & DELETE ---
t_p_label = "📥 Log Stock Movements" if not is_arabic else "📥 تسجيل حركات المخزون"
t_m_label = (
    "✏️ Modify Cost & Alerts" if not is_arabic else "✏️ تعديل التكلفة والتنبيهات"
)
t_s_label = "⏸️ Toggle Status" if not is_arabic else "⏸️ تبديل الحالة"
t_d_label = "🗑️ Permanent Delete" if not is_arabic else "🗑️ حذف نهائي"

tab_purchase, tab_modify, tab_status, tab_delete = st.tabs(
    [t_p_label, t_m_label, t_s_label, t_d_label]
)

with tab_purchase:
    st.markdown(
        "### "
        + (
            "Log Warehouse Stock Movements"
            if not is_arabic
            else "تسجيل حركات مخزون المستودع"
        )
    )
    with st.form(key="purchase_movement_form_isolated"):
        col1, col2 = st.columns(2)
        with col1:
            if active_item_options:
                chosen_stock_item = st.selectbox(
                    (
                        "Select Target Feed Ingredient:"
                        if not is_arabic
                        else "اختر مكون العلف المستهدف:"
                    ),
                    active_item_options,
                )
            else:
                st.warning(
                    "No active ingredients available."
                    if not is_arabic
                    else "لا توجد مكونات نشطة متاحة."
                )
                chosen_stock_item = None

            stock_shift = st.number_input(
                (
                    "Stock Volume Shift (+ Purchases, - Drawdowns):"
                    if not is_arabic
                    else "تغير حجم المخزون (+ مشتريات، - سحب):"
                ),
                step=50.0,
                value=0.0,
            )

            received_date = st.date_input(
                "Transaction Date:" if not is_arabic else "تاريخ المعاملة:",
                value=date.today(),
            )

        with col2:
            current_cost_val = 15.0
            if chosen_stock_item and not df_active.empty:
                match_row = df_active[df_active["item_name"] == chosen_stock_item]
                if not match_row.empty:
                    current_cost_val = float(match_row.iloc[0]["cost_per_kg"])

            updated_cost = st.number_input(
                (
                    "Confirm/Update Unit Cost ($/kg):"
                    if not is_arabic
                    else "تأكيد/تحديث تكلفة الوحدة ($/كجم):"
                ),
                min_value=0.0,
                step=0.1,
                value=current_cost_val,
            )

            comments = st.text_area(
                "Observations/Notes:" if not is_arabic else "ملاحظات / ملاحظات توضيحية:"
            )

        if (
            st.form_submit_button(
                "Commit Movement Entry" if not is_arabic else "اعتماد حركة المخزون"
            )
            and chosen_stock_item
        ):
            try:
                db.log_warehouse_movement(
                    chosen_stock_item,
                    stock_shift,
                    updated_cost,
                    received_date,
                    comments,
                )
                st.success(
                    f"Ledger and History updated for '{chosen_stock_item}'!"
                    if not is_arabic
                    else f"تم تحديث دفتر السجلات والسجل التاريخي لـ '{chosen_stock_item}'!"
                )
                st.rerun()
            except Exception as e:
                st.error(
                    f"Transaction failed: {e}"
                    if not is_arabic
                    else f"فشلت المعاملة: {e}"
                )

with tab_modify:
    st.markdown(
        "### "
        + (
            "Update Existing Commodity Configurations"
            if not is_arabic
            else "تحديث إعدادات السلع الحالية"
        )
    )
    if active_item_options:
        target_modify_item = st.selectbox(
            (
                "Choose Ingredient to Modify:"
                if not is_arabic
                else "اختر المكون المراد تعديله:"
            ),
            active_item_options,
            key="modify_select",
        )

        current_q, current_r, current_c = 0.0, 100.0, 15.0
        if not df_active.empty and target_modify_item:
            m_row = df_active[df_active["item_name"] == target_modify_item]
            if not m_row.empty:
                current_q = float(m_row.iloc[0]["quantity_kg"])
                current_r = float(m_row.iloc[0].get("reorder_level_kg", 100.0))
                current_c = float(m_row.iloc[0]["cost_per_kg"])

        with st.form(key="modify_parameters_form"):
            mod_col1, mod_col2, mod_col3 = st.columns(3)
            with mod_col1:
                new_qty = st.number_input(
                    (
                        "Inventory Adjustment (kg):"
                        if not is_arabic
                        else "تعديل المخزون (كجم):"
                    ),
                    value=current_q,
                    step=10.0,
                )
            with mod_col2:
                new_reorder = st.number_input(
                    "Safety Threshold (kg):" if not is_arabic else "حد الأمان (كجم):",
                    value=current_r,
                    step=10.0,
                )
            with mod_col3:
                new_price = st.number_input(
                    "Cost per kg ($):" if not is_arabic else "التكلفة لكل كجم ($):",
                    value=current_c,
                    step=0.1,
                )

            if (
                st.form_submit_button(
                    "Save Altered Record" if not is_arabic else "حفظ السجل المعدل"
                )
                and target_modify_item
            ):
                db.execute_custom_query(
                    "UPDATE inventory SET quantity_kg = %s, reorder_level_kg = %s, cost_per_kg = %s WHERE item_name = %s",
                    (new_qty, new_reorder, new_price, target_modify_item),
                    is_select=False,
                )
                st.success(
                    f"✏️ Successfully updated '{target_modify_item}'!"
                    if not is_arabic
                    else f"✏️ تم تحديث '{target_modify_item}' بنجاح!"
                )
                st.rerun()
    else:
        st.info(
            "No active materials available."
            if not is_arabic
            else "لا توجد مواد نشطة متاحة."
        )

with tab_status:
    st.markdown(
        "### "
        + (
            "Change Ingredient Status Visibility"
            if not is_arabic
            else "تغيير حالة ظهور المكون"
        )
    )
    col_deact, col_react = st.columns(2)

    with col_deact:
        st.markdown(
            "#### " + ("⏸️ Archive Item" if not is_arabic else "⏸️ أرشفة العنصر")
        )
        with st.form(key="deact_form"):
            if active_item_options:
                to_deactivate = st.selectbox(
                    (
                        "Select Ingredient to Hide:"
                        if not is_arabic
                        else "اختر المكون لإخفائه:"
                    ),
                    active_item_options,
                )
                if (
                    st.form_submit_button(
                        "Mark as Inactive" if not is_arabic else "تعيين كغير نشط"
                    )
                    and to_deactivate
                ):
                    db.execute_custom_query(
                        "UPDATE inventory SET is_active = 0 WHERE item_name = %s",
                        (to_deactivate,),
                        is_select=False,
                    )
                    st.success(
                        "Item archived." if not is_arabic else "تم أرشفة العنصر."
                    )
                    st.rerun()
            else:
                st.form_submit_button(
                    "Archive Disabled" if not is_arabic else "الأرشفة معطلة",
                    disabled=True,
                )

    with col_react:
        st.markdown(
            "#### "
            + ("▶️ Reactivate Item" if not is_arabic else "▶️ إعادة تنشيط العنصر")
        )
        with st.form(key="react_form"):
            inactive_options = (
                df_inactive["item_name"].tolist() if not df_inactive.empty else []
            )
            if inactive_options:
                to_reactivate = st.selectbox(
                    (
                        "Select Ingredient to Restore:"
                        if not is_arabic
                        else "اختر المكون لاستعادته:"
                    ),
                    inactive_options,
                )
                if (
                    st.form_submit_button(
                        "Restore to Active Duty"
                        if not is_arabic
                        else "استعادة للخدمة النشطة"
                    )
                    and to_reactivate
                ):
                    db.execute_custom_query(
                        "UPDATE inventory SET is_active = 1 WHERE item_name = %s",
                        (to_reactivate,),
                        is_select=False,
                    )
                    st.success(
                        "Item restored!" if not is_arabic else "تم استعادة العنصر!"
                    )
                    st.rerun()
            else:
                st.form_submit_button(
                    "Restore Disabled" if not is_arabic else "الاستعادة معطلة",
                    disabled=True,
                )

with tab_delete:
    st.markdown(
        "### ⚠️ "
        + ("Permanent Record Removal" if not is_arabic else "إزالة السجل بشكل دائم")
    )
    all_deletable_items = df_inv["item_name"].tolist() if not df_inv.empty else []

    with st.form(key="hard_delete_form"):
        if all_deletable_items:
            to_delete = st.selectbox(
                "Select Commodity to Wipe:" if not is_arabic else "اختر السلعة لمسحها:",
                all_deletable_items,
            )
            confirm_checkbox = st.checkbox(
                "I confirm permanent deletion from the cloud."
                if not is_arabic
                else "أؤكد الحذف النهائي من السحاب."
            )

            if (
                st.form_submit_button(
                    "Permanently Purge" if not is_arabic else "مسح نهائي"
                )
                and to_delete
            ):
                if not confirm_checkbox:
                    st.error(
                        "❌ You must check the confirmation box."
                        if not is_arabic
                        else "❌ يجب تحديد مربع التأكيد."
                    )
                else:
                    db.execute_custom_query(
                        "DELETE FROM inventory WHERE item_name = %s",
                        (to_delete,),
                        is_select=False,
                    )
                    st.success(
                        f"💥 '{to_delete}' wiped from the cloud database."
                        if not is_arabic
                        else f"💥 تم مسح '{to_delete}' من قاعدة بيانات السحاب."
                    )
                    st.rerun()
        else:
            st.info(
                "No records to delete." if not is_arabic else "لا توجد سجلات للحذف."
            )

# --- DATAFRAME RENDERING ---
st.subheader(
    "Active Feed Stock Valuation & Safety Parameters"
    if not is_arabic
    else "تقييم مخزون الأعلاف النشط ومعايير الأمان"
)
if not df_inv.empty:
    st.dataframe(df_inv, use_container_width=True, hide_index=True)
else:
    st.info(
        "No active records to display."
        if not is_arabic
        else "لا توجد سجلات نشطة للعرض."
    )
