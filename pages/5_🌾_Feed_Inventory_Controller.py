from datetime import date, timedelta
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

st.title(
    t("nav_5")
    if "nav_5" in st.session_state.get("translations", {})
    else ("Feed Inventory Controller" if not is_arabic else "متحكم مخزون الأعلاف")
)

# 🟢 Add Home Button
db.draw_home_button()

st.markdown("---")
st.subheader(
    "📦 Flow-Based Warehouse Inventory & Category Consumption Control"
    if not is_arabic
    else "📦 تحكم مخزون المستودع القائم على التدفق واستهلاك الفئات"
)

# ⚡ LIVE CLOUD DATA EXTRACTION
try:
    df_inv = db.get_table_data("inventory")
    df_logs = db.get_table_data("inventory_logs")
    df_recipes = db.get_table_data("feed_recipes")
    st.session_state.cached_recipes = df_recipes
except Exception as e:
    st.error(
        f"Cloud Connection Error: {e}"
        if not is_arabic
        else f"خطأ في الاتصال بالسحاب: {e}"
    )
    df_inv = pd.DataFrame()
    df_logs = pd.DataFrame()
    df_recipes = pd.DataFrame()

# --- SETUP LIVE RENDER OBJECTS ---
if not df_inv.empty and "is_active" in df_inv.columns:
    df_active = df_inv[df_inv["is_active"] == 1]
    df_inactive = df_inv[df_inv["is_active"] == 0]
else:
    df_active = df_inv.copy()
    df_inactive = pd.DataFrame()

active_item_options = df_active["item_name"].tolist() if not df_active.empty else []

price_lookup = {
    row["item_name"]: float(row["cost_per_kg"]) for _, row in df_active.iterrows()
}

cost_summary = " | ".join(
    [f"{name}: **${cost}/kg**" for name, cost in price_lookup.items()]
)
if cost_summary:
    st.markdown(
        f"**{'Current Ingredient Costs' if not is_arabic else 'تكاليف المكونات الحالية'}:** {cost_summary}"
    )


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


# --- NAVIGATION TABS ---
tab_receive_label = "📥 Supplier Receiving" if not is_arabic else "📥 استلام الموردين"
tab_withdraw_label = "📤 Category Withdrawal" if not is_arabic else "📤 سحب الفئات"
tab_stock_label = (
    "📊 Stock & Forecast Dashboard" if not is_arabic else "📊 لوحة المخزون والتوقعات"
)
tab_mgmt_label = (
    "✏️ Catalog & Item Management" if not is_arabic else "✏️ إدارة الكتالوج والأصناف"
)
tab_ref_label = (
    "📋 Recipe Ratios (Reference)" if not is_arabic else "📋 نسب الوصفات (مرجع)"
)
tab_reports_label = "📑 Reports & Vouchers" if not is_arabic else "📑 التقارير والسندات"

tab_receive, tab_withdraw, tab_stock, tab_mgmt, tab_ref, tab_reports = st.tabs(
    [
        tab_receive_label,
        tab_withdraw_label,
        tab_stock_label,
        tab_mgmt_label,
        tab_ref_label,
        tab_reports_label,
    ]
)

# 📥 TAB 1: SUPPLIER RECEIVING FORM (INBOUND)
with tab_receive:
    st.markdown(
        "### "
        + (
            "Log Inbound Supplier Shipment"
            if not is_arabic
            else "تسجيل شحنة المورد الواردة"
        )
    )
    with st.form(key="supplier_receiving_form"):
        col_rec1, col_rec2 = st.columns(2)
        with col_rec1:
            received_date = st.date_input(
                "1. Date Received:" if not is_arabic else "1. تاريخ الاستلام:",
                value=date.today(),
            )

            supplier_options = [
                "ألحاج أحمد",
                "الحاج فؤاد",
                "عم خميس",
                "الحاج عبد الباسط",
                "Other Supplier",
            ]
            chosen_supplier = st.selectbox(
                "2. Supplier:" if not is_arabic else "2. المورد:", supplier_options
            )

            target_ingredient = st.selectbox(
                (
                    "3. Target Feed Ingredient:"
                    if not is_arabic
                    else "3. مكون العلف المستهدف:"
                ),
                (
                    active_item_options
                    if active_item_options
                    else ["No active items found"]
                ),
            )

        with col_rec2:
            qty_received = st.number_input(
                (
                    "4. Quantity Received by kg:"
                    if not is_arabic
                    else "4. الكمية المستلمة بالكجم:"
                ),
                min_value=0.0,
                step=100.0,
                value=1000.0,
            )

            default_item_cost = price_lookup.get(target_ingredient, 15.0)
            purchased_price_per_kg = st.number_input(
                (
                    "5. Purchased Price per kg ($):"
                    if not is_arabic
                    else "5. سعر الشراء لكل كجم ($):"
                ),
                min_value=0.0,
                step=0.1,
                value=default_item_cost,
            )

            calculated_total_price = qty_received * purchased_price_per_kg
            st.metric(
                (
                    "6. Calculated Total Purchase Price ($):"
                    if not is_arabic
                    else "6. إجمالي سعر الشراء المحسوب ($):"
                ),
                f"$ {calculated_total_price:,.2f}",
            )

        comments_rec = st.text_input(
            "Receipt Notes / Invoice Reference:"
            if not is_arabic
            else "ملاحظات الاستلام / مرجع الفاتورة:"
        )

        submit_receiving = st.form_submit_button(
            "Commit Receiving Shipment" if not is_arabic else "اعتماد شحنة الاستلام"
        )

        if submit_receiving:
            if not target_ingredient or target_ingredient == "No active items found":
                st.error(
                    "Please select a valid target feed ingredient."
                    if not is_arabic
                    else "يرجى اختيار مكون علف مستهدف صالح."
                )
            elif qty_received <= 0:
                st.error(
                    "Quantity received must be greater than zero."
                    if not is_arabic
                    else "يجب أن تكون الكمية المستلمة أكبر من الصفر."
                )
            else:
                try:
                    comment_text = f"Supplier: {chosen_supplier} | Total: ${calculated_total_price:,.2f} | {comments_rec}".strip()
                    db.log_warehouse_movement(
                        item_name=target_ingredient,
                        quantity_shift=qty_received,
                        unit_cost=purchased_price_per_kg,
                        received_date=received_date,
                        comments=comment_text,
                    )
                    st.success(
                        f"🎉 Successfully received {qty_received:,.2f} kg of {target_ingredient} from {chosen_supplier}!"
                        if not is_arabic
                        else f"🎉 تم استلام {qty_received:,.2f} كجم من {target_ingredient} بنجاح من {chosen_supplier}!"
                    )
                    st.rerun()
                except Exception as e:
                    st.error(
                        f"Database error during receiving: {e}"
                        if not is_arabic
                        else f"خطأ في قاعدة البيانات أثناء الاستلام: {e}"
                    )

# 📤 TAB 2: CATEGORY WITHDRAWAL FORM (OUTBOUND)
with tab_withdraw:
    st.markdown(
        "### "
        + (
            "Log Daily Category Consumption & Withdrawal"
            if not is_arabic
            else "تسجيل الاستهلاك اليومي وسحب الفئات"
        )
    )
    with st.form(key="category_withdrawal_form"):
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            withdrawal_date = st.date_input(
                "1. Date of Withdrawal:" if not is_arabic else "1. تاريخ السحب:",
                value=date.today(),
            )

            outbound_category = st.selectbox(
                "2. Outbound Category:" if not is_arabic else "2. فئة الصرف:",
                ["Fattening Category", "Rest of the Herd (Excluding Newborns)"],
            )

            withdrawal_ingredient = st.selectbox(
                (
                    "Select Feed Ingredient to Withdraw:"
                    if not is_arabic
                    else "اختر مكون العلف المراد سحبه:"
                ),
                (
                    active_item_options
                    if active_item_options
                    else ["No active items found"]
                ),
            )

        with col_w2:
            qty_withdrawal = st.number_input(
                (
                    "3. Quantity Withdrawal by Kg:"
                    if not is_arabic
                    else "3. كمية السحب بالكجم:"
                ),
                min_value=0.0,
                step=50.0,
                value=200.0,
            )

            current_ing_cost = price_lookup.get(withdrawal_ingredient, 15.0)
            calculated_withdrawal_cost = qty_withdrawal * current_ing_cost

            st.metric(
                (
                    "Calculated Total Consumption Cost ($):"
                    if not is_arabic
                    else "إجمالي تكلفة الاستهلاك المحسوبة ($):"
                ),
                f"$ {calculated_withdrawal_cost:,.2f}",
            )

        withdrawal_notes = st.text_input(
            "Withdrawal Notes / Pen ID:"
            if not is_arabic
            else "ملاحظات السحب / رقم الحظيرة:"
        )

        submit_withdrawal = st.form_submit_button(
            "Commit Category Withdrawal" if not is_arabic else "اعتماد سحب الفئة"
        )

        if submit_withdrawal:
            if (
                not withdrawal_ingredient
                or withdrawal_ingredient == "No active items found"
            ):
                st.error(
                    "Please select a valid feed ingredient."
                    if not is_arabic
                    else "يرجى اختيار مكون علف صالح."
                )
            elif qty_withdrawal <= 0:
                st.error(
                    "Quantity withdrawn must be greater than zero."
                    if not is_arabic
                    else "يجب أن تكون كمية السحب أكبر من الصفر."
                )
            else:
                current_stock_row = df_active[
                    df_active["item_name"] == withdrawal_ingredient
                ]
                available_stock = (
                    float(current_stock_row.iloc[0]["quantity_kg"])
                    if not current_stock_row.empty
                    else 0.0
                )

                if qty_withdrawal > available_stock:
                    st.warning(
                        f"⚠️ Warning: Withdrawing {qty_withdrawal} kg exceeds current stock ({available_stock} kg) for {withdrawal_ingredient}!"
                        if not is_arabic
                        else f"⚠️ تحذير: سحب {qty_withdrawal} كجم يتجاوز المخزون الحالي ({available_stock} كجم) لـ {withdrawal_ingredient}!"
                    )

                try:
                    comment_text = f"Outbound Category: {outbound_category} | Cost: ${calculated_withdrawal_cost:,.2f} | {withdrawal_notes}".strip()
                    db.log_warehouse_movement(
                        item_name=withdrawal_ingredient,
                        quantity_shift=-qty_withdrawal,
                        unit_cost=current_ing_cost,
                        received_date=withdrawal_date,
                        comments=comment_text,
                    )
                    st.success(
                        f"📤 Successfully withdrawn {qty_withdrawal:,.2f} kg of {withdrawal_ingredient} for {outbound_category}!"
                        if not is_arabic
                        else f"📤 تم سحب {qty_withdrawal:,.2f} كجم من {withdrawal_ingredient} لـ {outbound_category} بنجاح!"
                    )
                    st.rerun()
                except Exception as e:
                    st.error(
                        f"Database error during withdrawal: {e}"
                        if not is_arabic
                        else f"خطأ في قاعدة البيانات أثناء السحب: {e}"
                    )

# 📊 TAB 3: STOCK & FORECAST DASHBOARD
with tab_stock:
    st.markdown(
        "### "
        + (
            "Active Feed Stock Valuation & Safety Parameters"
            if not is_arabic
            else "تقييم مخزون الأعلاف النشط ومعايير الأمان"
        )
    )
    if not df_inv.empty:
        st.dataframe(df_inv, use_container_width=True, hide_index=True)
    else:
        st.info(
            "No active records to display."
            if not is_arabic
            else "لا توجد سجلات نشطة للعرض."
        )

    st.markdown("---")
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
    else:
        st.info(
            "Ensure all herd groups have registered feeding standards and recipes to see the forecast."
            if not is_arabic
            else "تأكد من تسجيل معايير التغذية ووصفات الأعلاف لرؤية التوقعات."
        )

# ✏️ TAB 4: CATALOG & ITEM MANAGEMENT
with tab_mgmt:
    st.markdown(
        "### "
        + (
            "Warehouse Catalog & Item Management"
            if not is_arabic
            else "إدارة الكتالوج والأصناف في المستودع"
        )
    )
    sub_reg, sub_mod, sub_stat, sub_del = st.tabs(
        ["➕ Register", "✏️ Modify", "⏸️ Status", "🗑️ Delete"]
    )

    with sub_reg:
        with st.form(key="reg_form"):
            new_item_name = st.text_input("Ingredient Name:", value="").strip()
            new_item_cost = st.number_input(
                "Unit Cost ($/kg):", min_value=0.0, step=0.1, value=15.0
            )
            if st.form_submit_button("Register") and new_item_name:
                db.execute_custom_query(
                    "INSERT INTO inventory (item_name, quantity_kg, reorder_level_kg, cost_per_kg, is_active) VALUES (%s, 0.0, 100.0, %s, 1)",
                    (new_item_name, new_item_cost),
                    is_select=False,
                )
                st.success("Registered successfully!")
                st.rerun()

    with sub_mod:
        if active_item_options:
            target_mod = st.selectbox("Select Item:", active_item_options)
            m_row = df_active[df_active["item_name"] == target_mod].iloc[0]
            with st.form(key="mod_form"):
                nq = st.number_input(
                    "Quantity (kg):", value=float(m_row["quantity_kg"])
                )
                nr = st.number_input(
                    "Safety Threshold (kg):",
                    value=float(m_row.get("reorder_level_kg", 100.0)),
                )
                nc = st.number_input("Cost ($/kg):", value=float(m_row["cost_per_kg"]))
                if st.form_submit_button("Save"):
                    db.execute_custom_query(
                        "UPDATE inventory SET quantity_kg = %s, reorder_level_kg = %s, cost_per_kg = %s WHERE item_name = %s",
                        (nq, nr, nc, target_mod),
                        is_select=False,
                    )
                    st.success("Updated!")
                    st.rerun()

    with sub_stat:
        if active_item_options:
            to_hide = st.selectbox("Archive Item:", active_item_options)
            if st.button("Archive"):
                db.execute_custom_query(
                    "UPDATE inventory SET is_active = 0 WHERE item_name = %s",
                    (to_hide,),
                    is_select=False,
                )
                st.rerun()

    with sub_del:
        if active_item_options:
            to_del = st.selectbox("Delete Item:", active_item_options)
            if st.button("Purge"):
                db.execute_custom_query(
                    "DELETE FROM inventory WHERE item_name = %s",
                    (to_del,),
                    is_select=False,
                )
                st.rerun()

# 📋 TAB 5: RECIPE RATIOS (REFERENCE)
with tab_ref:
    st.markdown(
        "### "
        + (
            "Recipe Ratios & Benchmark Standards (Reference)"
            if not is_arabic
            else "نسب الوصفات ومعايير المؤشرات (مرجع)"
        )
    )
    ratios_fattening = {}
    for _, row in df_active.iterrows():
        ing_name = row["item_name"]
        default_val = get_saved_ratio_dynamic("Fattening", ing_name)
        ratios_fattening[ing_name] = st.slider(
            f"Fattening Ratio - {ing_name} (%)",
            0,
            100,
            default_val,
            key=f"f_{ing_name}",
        )
    if st.button("Save Fattening Ratio"):
        breakdown_str = ";".join([f"{k}:{v}" for k, v in ratios_fattening.items()])
        blend_cost = sum(
            (ratios_fattening[k] / 100.0) * price_lookup.get(k, 0)
            for k in ratios_fattening
        )
        db.execute_custom_query(
            "INSERT INTO feed_recipes (recipe_type, calculated_mix_cost_per_kg, recipe_breakdown) VALUES (%s, %s, %s) ON CONFLICT (recipe_type) DO UPDATE SET calculated_mix_cost_per_kg = EXCLUDED.calculated_mix_cost_per_kg, recipe_breakdown = EXCLUDED.recipe_breakdown",
            ("Fattening", blend_cost, breakdown_str),
            is_select=False,
        )
        st.success("Saved Fattening Recipe!")
        st.rerun()

# 📑 TAB 6: REPORTS & PRINTABLE VOUCHERS
with tab_reports:
    st.markdown(
        "### "
        + (
            "📑 Reports, Printable Vouchers & CSV Exports"
            if not is_arabic
            else "📑 التقارير، السندات القابلة للطباعة وتصدير CSV"
        )
    )

    rep_sub1, rep_sub2 = st.tabs(
        ["🖨️ Printable Vouchers (Slips)", "📊 Movement Audit & Export Summary"]
    )

    # 1. Printable Vouchers
    with rep_sub1:
        st.markdown(
            "#### "
            + (
                "Generate Printable Operation Voucher"
                if not is_arabic
                else "إطباع سند تشغيلي"
            )
        )
        if not df_logs.empty:
            log_options = [
                f"ID: {row['id']} | {row['item_name']} | Shift: {row['quantity_change']}kg | Date: {row['received_date']}"
                for _, row in df_logs.iterrows()
            ]
            selected_log_str = st.selectbox("Select Transaction Log ID:", log_options)

            if selected_log_str:
                selected_id = int(
                    selected_log_str.split("|")[0].replace("ID:", "").strip()
                )
                log_row = df_logs[df_logs["id"] == selected_id].iloc[0]

                # Printable Voucher Card UI
                st.markdown("---")
                voucher_type = (
                    "INBOUND SHIPMENT / RECEIVING VOUCHER"
                    if float(log_row["quantity_change"]) > 0
                    else "OUTBOUND CONSUMPTION VOUCHER"
                )

                st.markdown(
                    f"""
                <div style="border: 2px solid #4CAF50; padding: 20px; border-radius: 10px; background-color: #fafafa; color: #333;">
                    <h2 style="text-align: center; color: #2E7D32;">myHerdFinance Feed Warehouse</h2>
                    <h4 style="text-align: center; color: #555;">{voucher_type}</h4>
                    <hr>
                    <p><b>Transaction ID:</b> #{log_row['id']}</p>
                    <p><b>Date:</b> {log_row['received_date']}</p>
                    <p><b>Feed Ingredient:</b> {log_row['item_name']}</p>
                    <p><b>Quantity Movement:</b> {float(log_row['quantity_change']):,.2f} kg</p>
                    <p><b>Operational Notes / Details:</b> {log_row['comments']}</p>
                    <br><br>
                    <table style="width: 100%;">
                      <tr>
                        <td><b>Prepared By:</b> ____________________</td>
                        <td><b>Authorized Sign-off:</b> ____________________</td>
                      </tr>
                    </table>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                st.markdown(
                    "*(Tip: Press `Ctrl + P` in your browser to print this voucher directly).*"
                )
        else:
            st.info(
                "No transaction logs available yet."
                if not is_arabic
                else "لا توجد سجلات معاملات متاحة حتى الآن."
            )

    # 2. Audit Trail & Export Summary
    with rep_sub2:
        st.markdown(
            "#### "
            + (
                "Warehouse Movement Audit Trail & Summary"
                if not is_arabic
                else "سجل تدقيق حركة المستودع وملخص التقرير"
            )
        )

        if not df_logs.empty:
            # Date filter
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                start_d = st.date_input(
                    "Start Date:", value=date.today() - timedelta(days=30)
                )
            with col_d2:
                end_d = st.date_input("End Date:", value=date.today())

            # Filter dataframe by date
            df_logs["parsed_date"] = pd.to_datetime(
                df_logs["received_date"], errors="coerce"
            ).dt.date
            filtered_logs = df_logs[
                (df_logs["parsed_date"] >= start_d) & (df_logs["parsed_date"] <= end_d)
            ]

            st.dataframe(
                filtered_logs.drop(columns=["parsed_date"]),
                use_container_width=True,
                hide_index=True,
            )

            # Export CSV Download Button
            csv_data = filtered_logs.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=(
                    "📥 Download Filtered Movement Report (CSV)"
                    if not is_arabic
                    else "📥 تحميل تقرير الحركات المفلترة (CSV)"
                ),
                data=csv_data,
                file_name=f"feed_inventory_audit_{start_d}_to_{end_d}.csv",
                mime="text/csv",
            )
        else:
            st.info(
                "No movement logs found."
                if not is_arabic
                else "لم يتم العثور على سجلات حركة."
            )
