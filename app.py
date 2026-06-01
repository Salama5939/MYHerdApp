import streamlit as st
import pandas as pd
import plotly.express as px
import database
from datetime import datetime, date

st.set_page_config(page_title="Professional Herd Controller", layout="wide")
database.initialize_db()

st.sidebar.title("Navigation Panel")
menu = st.sidebar.radio(
    "Go to module:",
    [
        "Strategic Dashboard",
        "Herd Registry & Intake",
        "Lifecycle Growth Transitions",
        "Birth Event Registration",
        "Fattening Performance Log",
        "Sales & Off-take Portal",
        "Feed Inventory Controller",
        "Data Entry Corrections",
    ],
)

# 📊 MODULE 1: STRATEGIC DASHBOARD
if menu == "Strategic Dashboard":
    st.title("Strategic Herd & Financial Analysis Dashboard")

    df_herd = database.get_table_data("herd")
    df_inv = database.get_table_data("inventory")
    df_w = database.get_table_data("weight_logs")

    # Financial aggregation calculations
    active_herd = (
        df_herd[~df_herd["category"].isin(["Sold", "Slaughtered"])]
        if not df_herd.empty
        else pd.DataFrame()
    )
    sales_df = (
        df_herd[df_herd["category"].isin(["Sold", "Slaughtered"])]
        if not df_herd.empty
        else pd.DataFrame()
    )

    total_purchase_outlay = (
        df_herd["purchase_price"].sum() if not df_herd.empty else 0.0
    )
    total_feed_cost_accum = (
        df_w["calculated_feed_cost"].sum() if not df_w.empty else 0.0
    )
    total_revenue = sales_df["sale_price"].sum() if not sales_df.empty else 0.0
    net_profit_margin = total_revenue - (total_purchase_outlay + total_feed_cost_accum)

    # Top Metric Grid Indicators
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Active Herd (Heads)", len(active_herd))
    with c2:
        st.metric(
            "Total Capital Outlay",
            f"${total_purchase_outlay:,.2f}",
            help="Sum of all animal purchase costs",
        )
    with c3:
        st.metric("Total Accumulated Feed Cost", f"${total_feed_cost_accum:,.2f}")
    with c4:
        st.metric(
            "Net Operational Profit",
            f"${net_profit_margin:,.2f}",
            delta=f"${net_profit_margin:,.2f}",
        )

    st.markdown("---")

    # Fattening Growth Performance Tracking Data Layout Table
    st.subheader(
        "📈 Fattening Growth & Feed Efficiency Ledger (Individual Tag Analysis)"
    )
    if not df_w.empty:
        display_w = df_w.copy().sort_values(by="entry_date", ascending=False)
        display_w.columns = [
            "ID",
            "Tag Number",
            "Weight (kg)",
            "Feed Used (kg)",
            "Log Date",
            "Days Elapsed",
            "Weight Gained (kg)",
            "DLWG (kg/Day)",
            "Feed Cost Allocation ($)",
        ]
        st.dataframe(display_w, use_container_width=True, hide_index=True)
    else:
        st.info(
            "No monthly weight performance logs available to analyze growth efficiency profiles."
        )

    st.markdown("---")
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Herd Structural Composition")
        if not active_herd.empty:
            cat_counts = active_herd["category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Head Count"]
            fig = px.pie(
                cat_counts,
                values="Head Count",
                names="Category",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Physical Feed Ingredient Stock Levels (kg)")
        if not df_inv.empty:
            fig_bar = px.bar(
                df_inv,
                x="item_name",
                y="quantity_kg",
                labels={"item_name": "Ingredient", "quantity_kg": "Stocks (kg)"},
                color="quantity_kg",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

# 🐏 MODULE 2: HERD INTAKE (With Custom Purchase Tracking)
elif menu == "Herd Registry & Intake":
    st.title("Livestock Registration Intake Portal")

    with st.form("animal_registration_form"):
        col1, col2 = st.columns(2)
        with col1:
            tag_no = st.text_input("Ear Tag Number (Unique):")
            category = st.selectbox(
                "Management Category Group:",
                [
                    "Ewes",
                    "Fattening",
                    "Permanent Sire",
                    "Pregnant",
                    "Small Sheep - Female",
                    "Small Sheep - Male",
                ],
            )
            status = st.text_input("Health Status Note:", value="Active/Healthy")
        with col2:
            birth_date = st.date_input(
                "Animal Birth Date / Estimate:", value=date(2025, 1, 1)
            )
            purchase_price = st.number_input(
                "Purchasing Acquisition Price ($):",
                min_value=0.0,
                step=50.0,
                value=0.0,
                help="Leave 0.0 if born on farm",
            )
            purchase_date = st.date_input(
                "Acquisition / Purchase Date:", value=date(2026, 2, 22)
            )

        submit = st.form_submit_button("Commit Animal Record to Database")
        if submit:
            if tag_no.strip() == "":
                st.error("Submission Denied: Ear tag identifier cannot be left blank.")
            else:
                success = database.add_animal(
                    tag_no.strip(),
                    category,
                    status,
                    birth_date.isoformat(),
                    purchase_price,
                    purchase_date.isoformat(),
                )
                if success:
                    st.success(
                        f"Success! Animal '{tag_no}' added with an purchase value of ${purchase_price:,.2f}."
                    )
                    st.rerun()
                else:
                    st.error(
                        "Database Conflict: This ear tag identifier already exists."
                    )

    st.subheader("Active Stock Registry Ledger")
    df_all = database.get_table_data("herd")
    st.dataframe(df_all, use_container_width=True)

# 🔄 MODULE 3: LIFECYCLE GROWTH TRANSITIONS
elif menu == "Lifecycle Growth Transitions":
    st.title("🔄 Life Cycle Growth & Category Transition Center")
    st.markdown(
        "As lambs grow up, use this portal to upgrade their operational groups according to age milestones. Their background feed cost model updates instantly."
    )

    df_herd = database.get_table_data("herd")
    active_pool = (
        df_herd[~df_herd["category"].isin(["Sold", "Slaughtered"])]
        if not df_herd.empty
        else pd.DataFrame()
    )

    if active_pool.empty:
        st.info(
            "No active animals inside database available for transition processing."
        )
    else:
        with st.form("transition_form"):
            col1, col2 = st.columns(2)
            with col1:
                selected_animal = st.selectbox(
                    "Select Animal Tag to Transition:", active_pool["tag_no"].tolist()
                )
                current_cat = active_pool[active_pool["tag_no"] == selected_animal][
                    "category"
                ].values[0]
                st.info(f"Current Assigned Category: **{current_cat}**")
            with col2:
                target_cat = st.selectbox(
                    "Target New Lifecycle Category Group:",
                    [
                        "Ewes",
                        "Fattening",
                        "Permanent Sire",
                        "Pregnant",
                        "Small Sheep - Female",
                        "Small Sheep - Male",
                    ],
                )

            execute_transition = st.form_submit_button(
                "Execute Lifecycle Category Shift"
            )
            if execute_transition:
                database.update_animal_category(selected_animal, target_cat)
                st.success(
                    f"Success! Animal '{selected_animal}' upgraded from '{current_cat}' to '{target_cat}'."
                )
                st.rerun()

# 🍼 MODULE 4: BIRTH EVENT REGISTRATION
elif menu == "Birth Event Registration":
    st.title("Automated Maternal Delivery Hub")
    df_herd = database.get_table_data("herd")
    pregnant_list = (
        df_herd[df_herd["category"] == "Pregnant"]["tag_no"].tolist()
        if not df_herd.empty
        else []
    )

    if not pregnant_list:
        st.warning(
            "No livestock units currently flagged as 'Pregnant' to execute delivery entries."
        )
    else:
        with st.form("birth_event_form"):
            ewe_tag = st.selectbox("Select Delivering Mother ID Tag:", pregnant_list)
            lamb_count = st.number_input(
                "Offspring Head Count Yield:", min_value=1, max_value=4, value=1
            )
            lamb_gender = st.selectbox(
                "Offspring Target Category Group (Nursing = $0 Cost):",
                ["Small Sheep - Female", "Small Sheep - Male"],
            )

            submit_birth = st.form_submit_button("Record Birth Delivery")
            if submit_birth:
                if database.register_birth_event(ewe_tag, lamb_count, lamb_gender):
                    st.success(
                        f"Maternal record '{ewe_tag}' updated and {lamb_count} newborn lambs initialized."
                    )
                    st.rerun()

# ⚖️ MODULE 5: FATTENING LOG (With Advanced Calculations)
elif menu == "Fattening Performance Log":
    st.title("Market Growth Group Weight Ledger")

    df_herd = database.get_table_data("herd")
    fattening_list = (
        df_herd[df_herd["category"] == "Fattening"]["tag_no"].tolist()
        if not df_herd.empty
        else []
    )

    df_recipes = database.get_table_data("feed_recipes")
    fatt_recipe_setup = (
        "Fattening" in df_recipes["recipe_type"].tolist()
        if not df_recipes.empty
        else False
    )

    if not fatt_recipe_setup:
        st.error(
            "Configuration Required: Please formulate your Fattening Recipe Cost parameters inside the 'Feed Inventory Controller' tab first before entering weight logs."
        )
    elif not fattening_list:
        st.info(
            "No active livestock units currently categorized inside the 'Fattening' group."
        )
    else:
        with st.form("weight_log_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                selected_tag = st.selectbox("Select Lot Animal Tag:", fattening_list)
                weigh_date = st.date_input("Weighing Date:", value=date(2026, 3, 22))
            with c2:
                current_w = st.number_input(
                    "Observed Scale Weight (kg):", min_value=1.0, step=0.5, value=45.0
                )
            with c3:
                feed_used = st.number_input(
                    "Total Feed Consumed Since Last Check (kg):",
                    min_value=0.0,
                    step=1.0,
                    value=30.0,
                )

            submit_log = st.form_submit_button(
                "Calculate and Record Performance Metrics"
            )
            if submit_log:
                database.log_growth_metrics_advanced(
                    selected_tag, current_w, feed_used, weigh_date.isoformat()
                )
                st.success(
                    f"Advanced growth metrics compiled and saved for tag '{selected_tag}'."
                )
                st.rerun()

# 💰 MODULE 6: SALES PORTAL
elif menu == "Sales & Off-take Portal":
    st.title("💰 Fattening Group Sales Processing Desk")
    df_herd = database.get_table_data("herd")
    fattening_pool = (
        df_herd[df_herd["category"] == "Fattening"]["tag_no"].tolist()
        if not df_herd.empty
        else []
    )

    if not fattening_pool:
        st.info(
            "There are currently zero animals assigned to the 'Fattening' group available for off-take sales."
        )
    else:
        with st.form("sales_transaction_form"):
            col1, col2 = st.columns(2)
            with col1:
                target_tag = st.selectbox(
                    "Select Animal Tag to process:", fattening_pool
                )
                target_action = st.selectbox(
                    "Action Status Group:", ["Sold", "Slaughtered"]
                )
            with col2:
                sale_price = st.number_input(
                    "Realized Transaction Selling Price ($):",
                    min_value=0.0,
                    step=50.0,
                    value=150.0,
                )
                transaction_date = st.date_input(
                    "Off-take Processing Date:", value=datetime.today()
                )

            submit_sale = st.form_submit_button("Finalize Sale Transaction")
            if submit_sale:
                if database.sell_or_slaughter_animal(
                    target_tag, target_action, sale_price, transaction_date.isoformat()
                ):
                    st.success(
                        f"Animal '{target_tag}' successfully group-shifted to '{target_action}' for ${sale_price:,.2f}."
                    )
                    st.rerun()

# 🌾 MODULE 7: FEED INVENTORY & RECIPE CALCULATOR
elif menu == "Feed Inventory Controller":
    st.title("Warehouse Inventory & Blended Feed Recipe Calculators")

    st.markdown("---")
    st.subheader("🧪 Interactive Feed Recipe Cost Formulation Desks")

    df_inv = database.get_table_data("inventory")

    if df_inv.empty:
        st.warning(
            "⚠️ Inventory is empty. Please add raw feed commodities via the Data Entry Corrections panel first."
        )
    else:
        # Create a clean lookup dictionary mapping: item_name -> cost_per_kg
        price_lookup = {
            row["item_name"]: float(row["cost_per_kg"]) for _, row in df_inv.iterrows()
        }

        # Generate inline inventory cost summary string dynamically
        cost_summary = " | ".join(
            [f"{name}: **${cost}/kg**" for name, cost in price_lookup.items()]
        )
        st.markdown(f"**Current Ingredient Costs:** {cost_summary}")

        tab1, tab2 = st.tabs(["Fattening Formulation", "General Herd Formulation"])

        with tab1:
            with st.form("fattening_recipe_form"):
                f_ratios = {}
                for row in df_inv.itertuples():
                    f_ratios[row.item_name] = st.slider(
                        f"{row.item_name} Ratio (%)", 0, 100, 0
                    )

                total_f_pct = sum(f_ratios.values())
                st.write(
                    f"Total Combined Formulation Matrix Weight: **{total_f_pct}%**"
                )

                # Type-safe dynamic math calculation using our new price lookup dictionary
                f_blended_cost = sum(
                    ((pct / 100) * price_lookup.get(name, 0.0))
                    for name, pct in f_ratios.items()
                )
                st.info(
                    f"📊 Calculated Fattening Mix Cost: **${f_blended_cost:.2f} per 1 kg**"
                )

                save_f_recipe = st.form_submit_button(
                    "Lock & Save Fattening Ration Cost Parameters"
                )
                if save_f_recipe:
                    if total_f_pct != 100:
                        st.error(
                            "Formulation Aborted: Ratios must sum up to exactly 100%."
                        )
                    else:
                        corn_val = f_ratios.get("Corn", 0)
                        soy_val = f_ratios.get("Soybean Meal", 0)
                        hay_val = f_ratios.get("Alfalfa Hay", 0)
                        database.save_feed_recipe(
                            "Fattening", corn_val, soy_val, hay_val, f_blended_cost
                        )
                        st.success(
                            "Fattening formulation parameters committed successfully."
                        )

        with tab2:
            with st.form("general_recipe_form"):
                g_ratios = {}
                for row in df_inv.itertuples():
                    g_ratios[row.item_name] = st.slider(
                        f"{row.item_name} Ratio (%)", 0, 100, 0
                    )

                total_g_pct = sum(g_ratios.values())
                st.write(
                    f"Total Combined Formulation Matrix Weight: **{total_g_pct}%**"
                )

                # Type-safe dynamic math calculation using our new price lookup dictionary
                g_blended_cost = sum(
                    ((pct / 100) * price_lookup.get(name, 0.0))
                    for name, pct in g_ratios.items()
                )
                st.info(
                    f"📊 Calculated General Herd Mix Cost: **${g_blended_cost:.2f} per 1 kg**"
                )

                save_g_recipe = st.form_submit_button(
                    "Lock & Save General Herd Ration Cost Parameters"
                )
                if save_g_recipe:
                    if total_g_pct != 100:
                        st.error(
                            "Formulation Aborted: Ratios must sum up to exactly 100%."
                        )
                    else:
                        corn_val = g_ratios.get("Corn", 0)
                        soy_val = g_ratios.get("Soybean Meal", 0)
                        hay_val = g_ratios.get("Alfalfa Hay", 0)
                        database.save_feed_recipe(
                            "General Herd", corn_val, soy_val, hay_val, g_blended_cost
                        )
                        st.success(
                            "General Herd formulation parameters committed successfully."
                        )

    # 📦 Sub-Panel B: Raw Stock Movements
    st.markdown("---")
    st.subheader("📦 Warehouse Inventory Stock Adjustments")
    with st.form("inventory_adjustment_form"):
        col1, col2 = st.columns(2)
        with col1:
            item_options = (
                df_inv["item_name"].tolist()
                if not df_inv.empty
                else ["Corn", "Soybean Meal", "Alfalfa Hay"]
            )
            chosen_item = st.selectbox(
                "Select Feed Ingredient Description:", item_options
            )
            add_qty = st.number_input(
                "Stock Volume Shift Value (+ Purchases, - Mix Drawdowns):",
                value=100.0,
                step=50.0,
            )
        with col2:
            cost_per_kg = st.number_input(
                "Observed Unit Buying Cost per 1 kg ($):",
                min_value=0.0,
                step=1.0,
                value=15.0,
            )

        submit_inv = st.form_submit_button("Update Stock Balance Ledger Account")
        if submit_inv:
            database.adjust_inventory_stock_advanced(chosen_item, add_qty, cost_per_kg)
            st.success(f"Warehouse Balance Updated for '{chosen_item}'.")
            st.rerun()

    st.subheader("Active Feed Stock Valuation & Safety Parameters")
    st.dataframe(
        database.get_table_data("inventory"), use_container_width=True, hide_index=True
    )

# 🛠️ MODULE 8: INTERACTIVE CELL CORRECTIONS
elif menu == "Data Entry Corrections":
    st.title("🛠️ System Data Editor & Corrections Panel")

    table_choice = st.selectbox(
        "Select Table to Edit:",
        [
            "Herd Registry (herd)",
            "Weight Logs (weight_logs)",
            "Feed Inventory (inventory)",
            "Feed Recipes (feed_recipes)",
        ],
    )
    db_table_map = {
        "Herd Registry (herd)": "herd",
        "Weight Logs (weight_logs)": "weight_logs",
        "Feed Inventory (inventory)": "inventory",
        "Feed Recipes (feed_recipes)": "feed_recipes",
    }
    target_table = db_table_map[table_choice]
    df_current = database.get_table_data(target_table)

    if not df_current.empty:
        edited_df = st.data_editor(
            df_current,
            use_container_width=True,
            num_rows="dynamic",
            key=f"editor_{target_table}",
        )
        if st.button("Save Amendments to Table Row Storage"):
            conn = database.get_connection()
            try:
                edited_df.to_sql(target_table, conn, if_exists="replace", index=False)
                st.success(f"Database Table row storage updated successfully.")
                database.initialize_db()
            except Exception as e:
                st.error(f"Failed to update database: {e}")
            finally:
                conn.close()
    else:
        st.info("Selected data row indices are completely empty.")
