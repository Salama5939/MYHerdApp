import streamlit as st
import pandas as pd
import plotly.express as px
import database
from datetime import datetime, date

# Page Layout Setup
st.set_page_config(page_title="myHerdApp Engine", layout="wide", page_icon="🐑")

# Initialize SQLite structures matching active configurations
database.initialize_db()

# Navigation Sidebar Setup
st.sidebar.title("🐑 myHerdApp Control Room")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Go To Module Dashboard:",
    [
        "Strategic Performance Metrics",
        "Active Herd Registry",
        "Birth Event Records",
        "Growth Performance Logs",
        "Feed Inventory Controller",
        "Data Entry Corrections",
    ],
)

# Fetch Shared Base Application Metrics
df_herd = database.get_table_data("herd")
df_births = database.get_table_data("birth_records")
df_weights = database.get_table_data("weight_logs")

# 📊 MODULE 1: STRATEGIC PERFORMANCE METRICS
if menu == "Strategic Performance Metrics":
    st.title("Strategic Herd Performance & Summary Metrics")
    st.markdown("---")

    if df_herd.empty:
        st.info(
            "The active herd data ledger account is currently empty. Begin registering animals to see live summaries."
        )
    else:
        active_animals = df_herd[df_herd["status"] == "Active"]

        # Upper KPI Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Active Animals Registered", len(active_animals))
        m2.metric(
            "Ewes Population Group",
            len(active_animals[active_animals["category"] == "Ewe"]),
        )
        m3.metric(
            "Lambs Population Group",
            len(active_animals[active_animals["category"] == "Lamb"]),
        )

        total_lambs_born = (
            int(df_births["lambs_count"].sum()) if not df_births.empty else 0
        )
        m4.metric("Total Successful Lambings Logs", total_lambs_born)

        # Categorical Charts Section
        st.markdown("### 📈 Structural Population Breakdowns")
        c1, c2 = st.columns(2)
        with c1:
            cat_counts = active_animals["category"].value_counts().reset_index()
            fig_cat = px.bar(
                cat_counts,
                x="category",
                y="count",
                title="Herd Structure Classification Count",
                labels={"count": "Head Count"},
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        with c2:
            status_counts = df_herd["status"].value_counts().reset_index()
            fig_stat = px.pie(
                status_counts,
                names="status",
                values="count",
                title="Historical Status Allocation Ratio",
            )
            st.plotly_chart(fig_stat, use_container_width=True)

# 📝 MODULE 2: ACTIVE HERD REGISTRY
elif menu == "Active Herd Registry":
    st.title("Active Herd Register & Entry Registry")
    st.markdown("---")

    tab1, tab2 = st.tabs(["Add Single New Entry", "Execute Status Off-Take Action"])

    with tab1:
        with st.form("add_animal_form", clear_on_submit=True):
            st.subheader("Register New Animal Parameters")
            col1, col2 = st.columns(2)
            with col1:
                tag_no = st.text_input("RFID Ear Tag Code (Unique ID):").strip()
                category = st.selectbox(
                    "Herd Category Classification:", ["Ewe", "Lamb", "Ram", "Yearling"]
                )
                status = st.selectbox(
                    "Current Operational Status Level:",
                    ["Active", "Sold", "Slaughtered", "Died"],
                )
            with col2:
                birth_date = st.date_input(
                    "Approximate Birth Date (Calendar):", value=date.today()
                )
                reg_date = st.date_input(
                    "Ledger Entry Registry Date:", value=date.today()
                )
                price = st.number_input(
                    "Purchase Price Value Amount ($):",
                    min_value=0.0,
                    step=50.0,
                    value=0.0,
                )

            comments = st.text_area("Structural Descriptive Comments / Observations:")
            submit_btn = st.form_submit_button("Commit New Record to Ledger")

            if submit_btn:
                if not tag_no:
                    st.error("Validation Error: RFID Ear Tag Code cannot be empty.")
                elif not df_herd.empty and tag_no in df_herd["tag_no"].values:
                    st.error(
                        f"Duplicate Row Exception: Tag '{tag_no}' already exists in the local database records."
                    )
                else:
                    database.add_animal(
                        tag_no,
                        category,
                        status,
                        str(birth_date),
                        str(reg_date),
                        price,
                        comments,
                    )
                    st.success(f"Animal {tag_no} has been registered successfully.")
                    st.rerun()

    with tab2:
        st.subheader("Process Off-Take / Change Operational Status")
        if df_herd.empty:
            st.warning("No records found in database to modify.")
        else:
            active_list = df_herd[df_herd["status"] == "Active"]["tag_no"].tolist()
            if not active_list:
                st.info(
                    "No active animals are currently present in your herd ledger registry."
                )
            else:
                with st.form("status_offtake_form"):
                    target_tag = st.selectbox(
                        "Select Target Ear Tag Code:", active_list
                    )
                    target_action = st.selectbox(
                        "Select Exit Action Description:",
                        ["Sold", "Slaughtered", "Died"],
                    )
                    sale_price = st.number_input(
                        "Observed Sale Price Value ($) - If applicable:",
                        min_value=0.0,
                        step=100.0,
                        value=0.0,
                    )
                    transaction_date = st.date_input(
                        "Off-Take Execution Date:", value=date.today()
                    )

                    submit_action = st.form_submit_button(
                        "Execute Change Status Command"
                    )
                    if submit_action:
                        database.sell_or_slaughter_animal(
                            target_tag,
                            target_action,
                            sale_price,
                            transaction_date.isoformat(),
                        )
                        st.success(
                            f"Animal {target_tag} has been updated to '{target_action}' status successfully."
                        )
                        st.rerun()

    st.subheader("Active Operations Tracking Matrix Grid")
    st.dataframe(df_herd, use_container_width=True, hide_index=True)

# 🍼 MODULE 3: BIRTH EVENT RECORDS
elif menu == "Birth Event Records":
    st.title("Ewe Lambing & Prolificacy Records Entry Desk")
    st.markdown("---")

    with st.form("birth_event_form", clear_on_submit=True):
        st.subheader("Log Successful Lambing Event Occurrence")
        col1, col2 = st.columns(2)
        with col1:
            ewe_tag = st.text_input("Dam Ewe Ear Tag Code (Mother ID):").strip()
            lambs_count = st.number_input(
                "Count of Born Lambs (Headcount):",
                min_value=1,
                max_value=4,
                value=1,
                step=1,
            )
        with col2:
            birth_date = st.date_input("Event Date (Calendar):", value=date.today())
            foster_ewe = st.text_input("Foster Ewe Tag Code (Optional):").strip()

        comments = st.text_area("Birth Weight/Vigor Contextual Observations:")
        submit_birth = st.form_submit_button("Register Event Parameters")

        if submit_birth:
            if not ewe_tag:
                st.error(
                    "Validation Error: Mother Dam Ewe Ear Tag Code cannot be left empty."
                )
            else:
                foster_val = foster_ewe if foster_ewe else None
                database.register_birth_event(
                    ewe_tag, str(birth_date), int(lambs_count), foster_val, comments
                )
                st.success("Lambing event logs processed successfully.")
                st.rerun()

    st.subheader("Historical Birth Event Logs")
    st.dataframe(df_births, use_container_width=True, hide_index=True)

# ⚖️ MODULE 4: GROWTH PERFORMANCE LOGS
elif menu == "Growth Performance Logs":
    st.title("Growth Metrics & Individual Weigh-In Logging Station")
    st.markdown("---")

    with st.form("growth_metrics_form", clear_on_submit=True):
        st.subheader("Log Growth Performance Milestone Metrics")
        col1, col2 = st.columns(2)
        with col1:
            tag_no = st.text_input("Animal Target Ear Tag Code (ID):").strip()
            weight = st.number_input(
                "Observed Body Weight (Scale Value in kg):",
                min_value=0.5,
                step=2.0,
                value=25.0,
            )
        with col2:
            weigh_date = st.date_input("Scale Weighing Date:", value=date.today())
            feed_kg = st.number_input(
                "Allocated Concentrates Mix Consumed Since Last Weighing (kg):",
                min_value=0.0,
                step=1.0,
                value=0.0,
            )

        comments = st.text_area("Growth Quality / Health Observations:")
        submit_growth = st.form_submit_button("Commit Growth Performance Entry")

        if submit_growth:
            if not tag_no:
                st.error(
                    "Validation Error: Animal Target Ear Tag Code cannot be empty."
                )
            else:
                database.log_growth_metrics_advanced(
                    tag_no, weight, feed_kg, str(weigh_date), comments
                )
                st.success("Growth performance milestone logs adjusted successfully.")
                st.rerun()

    st.subheader("Historical Weight Logs Matrix Grid")
    st.dataframe(df_weights, use_container_width=True, hide_index=True)

# 🌾 MODULE 5: FEED INVENTORY & RECIPE CALCULATOR
elif menu == "Feed Inventory Controller":
    st.title("Warehouse Inventory & Blended Feed Recipe Calculators")
    st.markdown("---")
    st.subheader("🧪 Interactive Feed Recipe Cost Formulation Desks")

    df_inv = database.get_table_data("inventory")
    df_recipes = database.get_table_data("feed_recipes")

    if df_inv.empty:
        st.warning(
            "⚠️ Inventory is empty. Please add raw feed commodities via the Data Entry Corrections panel first."
        )
    else:
        # Create ingredient price map
        price_lookup = {
            row["item_name"]: float(row["cost_per_kg"]) for _, row in df_inv.iterrows()
        }
        cost_summary = " | ".join(
            [f"{name}: **${cost}/kg**" for name, cost in price_lookup.items()]
        )
        st.markdown(f"**Current Ingredient Costs:** {cost_summary}")

        # Helper function to decode dynamic values stored in the breakdown column
        def get_saved_ratio_dynamic(recipe_type, item_name):
            if not df_recipes.empty:
                match = df_recipes[df_recipes["recipe_type"] == recipe_type]
                if not match.empty and "recipe_breakdown" in match.columns:
                    breakdown = str(match["recipe_breakdown"].values[0])
                    if breakdown:
                        parts = breakdown.split(";")
                        for part in parts:
                            if ":" in part:
                                name, val = part.split(":")
                                if name.strip() == item_name.strip():
                                    return int(val)
            return 0

        tab1, tab2 = st.tabs(["Fattening Formulation", "General Herd Formulation"])

        # Tab A: Fattening Formulation Desk
        with tab1:
            with st.form("fattening_recipe_form"):
                f_ratios = {}
                for row in df_inv.itertuples():
                    saved_val = get_saved_ratio_dynamic("Fattening", row.item_name)
                    f_ratios[row.item_name] = st.slider(
                        f"{row.item_name} Ratio (%)",
                        0,
                        100,
                        int(saved_val),
                        key=f"flat_{row.item_name}",
                    )

                total_f_pct = sum(f_ratios.values())
                st.write(
                    f"Total Combined Formulation Matrix Weight: **{total_f_pct}%**"
                )

                f_blended_cost = sum(
                    ((pct / 100) * price_lookup.get(name, 0.0))
                    for name, pct in f_ratios.items()
                )
                st.info(
                    f"📊 Calculated Fattening Mix Cost: **${f_blended_cost:.4f} per 1 kg**"
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
                        breakdown_str = ";".join(
                            [f"{k}:{v}" for k, v in f_ratios.items()]
                        )
                        database.save_feed_recipe_advanced(
                            "Fattening", breakdown_str, f_blended_cost
                        )
                        st.success(
                            "Fattening formulation parameters committed successfully."
                        )
                        st.rerun()

        # Tab B: General Herd Formulation Desk
        with tab2:
            with st.form("general_recipe_form"):
                g_ratios = {}
                for row in df_inv.itertuples():
                    saved_val = get_saved_ratio_dynamic("General Herd", row.item_name)
                    g_ratios[row.item_name] = st.slider(
                        f"{row.item_name} Ratio (%)",
                        0,
                        100,
                        int(saved_val),
                        key=f"gen_{row.item_name}",
                    )

                total_g_pct = sum(g_ratios.values())
                st.write(
                    f"Total Combined Formulation Matrix Weight: **{total_g_pct}%**"
                )

                g_blended_cost = sum(
                    ((pct / 100) * price_lookup.get(name, 0.0))
                    for name, pct in g_ratios.items()
                )
                st.info(
                    f"📊 Calculated General Herd Mix Cost: **${g_blended_cost:.4f} per 1 kg**"
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
                        breakdown_str = ";".join(
                            [f"{k}:{v}" for k, v in g_ratios.items()]
                        )
                        database.save_feed_recipe_advanced(
                            "General Herd", breakdown_str, g_blended_cost
                        )
                        st.success(
                            "General Herd formulation parameters committed successfully."
                        )
                        st.rerun()

    # Sub-Panel B: Raw Stock Movements & New Ingredient Registration
    st.markdown("---")
    st.subheader("📦 Warehouse Inventory Stock Adjustments & New Additions")
    with st.form("inventory_adjustment_form"):
        col1, col2 = st.columns(2)
        with col1:
            item_options = df_inv["item_name"].tolist() if not df_inv.empty else []

            # 🆕 Added selection type toggle so the system knows if you are updating or adding fresh
            entry_mode = st.radio(
                "Adjustment Action Type:",
                ["Update Existing Stock", "Register Brand New Ingredient"],
                horizontal=True,
            )

            if entry_mode == "Register Brand New Ingredient":
                chosen_item = st.text_input(
                    "Type Brand New Ingredient Name (e.g., Radda, Wheat):"
                ).strip()
            else:
                chosen_item = (
                    st.selectbox("Select Existing Feed Ingredient:", item_options)
                    if item_options
                    else st.text_input("Type Feed Ingredient Name:").strip()
                )

            add_qty = st.number_input(
                "Stock Volume Shift Value (+ Purchases, - Mix Drawdowns):",
                value=100.0,
                step=50.0,
            )
        with col2:
            cost_input = st.number_input(
                "Observed Unit Buying Cost per 1 kg ($):",
                min_value=0.0,
                step=0.5,
                value=15.0,
            )

        submit_inv = st.form_submit_button("Commit Entry to Stock Ledger")
        if submit_inv:
            if not chosen_item:
                st.error("Validation Error: Ingredient name cannot be left blank.")
            elif (
                entry_mode == "Register Brand New Ingredient"
                and chosen_item in item_options
            ):
                st.error(
                    f"The item '{chosen_item}' already exists. Please choose 'Update Existing Stock' instead."
                )
            else:
                database.adjust_inventory_stock_advanced(
                    chosen_item, add_qty, cost_input
                )
                st.success(
                    f"Warehouse Ledger Account updated successfully for '{chosen_item}'!"
                )
                st.rerun()

    st.subheader("Active Feed Stock Valuation & Safety Parameters")
    st.dataframe(
        database.get_table_data("inventory"), use_container_width=True, hide_index=True
    )

# 🛠️ MODULE 6: DATA ENTRY CORRECTIONS PANEL
elif menu == "Data Entry Corrections":
    st.title("Data Entry Corrections & Direct SQL Ledger Overrides")
    st.markdown("---")

    st.subheader("🔍 Local SQLite Live Matrix Inspection Deck")
    target_table = st.selectbox(
        "Select Target Table Matrix to Load for Inspection:",
        ["herd", "birth_records", "weight_logs", "inventory", "feed_recipes"],
    )
    df_inspect = database.get_table_data(target_table)
    st.dataframe(df_inspect, use_container_width=True)

    st.markdown("---")
    st.subheader(
        "⚡ Danger Zone: Execute Direct Raw Database Custom SQL Command Override"
    )
    st.warning(
        "Executing raw manual commands bypasses systemic validations. Use extreme caution."
    )

    with st.form("custom_sql_form"):
        raw_query = st.text_area("Input Valid SQLite Query Statement Here:")
        query_type = st.radio(
            "Statement Core Operation Action Profile Type:",
            [
                "SELECT Data Operations",
                "INSERT / UPDATE / DELETE Structure Modifications",
            ],
        )
        submit_query = st.form_submit_button("Force Run SQL Directive String")

        if submit_query and raw_query.strip():
            try:
                is_sel = True if "SELECT Data" in query_type else False
                res = database.execute_custom_query(raw_query, is_select=is_sel)
                if is_sel:
                    st.success("Query processed successfully. Returned matrix rows:")
                    st.dataframe(res, use_container_width=True)
                else:
                    st.success(
                        "Database structural modification committed successfully to file storage accounts."
                    )
                    st.rerun()
            except Exception as e:
                st.error(f"SQL Backend Exception Traceback Error: {e}")
