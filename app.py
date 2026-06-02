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

        # 🌟 SAFETY FILTER STRUCTURAL CHECK: Ensure our tracking column flag exists
    if not df_inv.empty and "is_active" not in df_inv.columns:
            import sqlite3
            conn = sqlite3.connect("herd_management.db")
            cursor = conn.cursor()
            try:
                cursor.execute("ALTER TABLE inventory ADD COLUMN is_active INTEGER DEFAULT 1")
                conn.commit()
            except Exception:
                pass
            conn.close()
            # Reload to grab the newly initialized column structure
            df_inv = database.get_table_data("inventory")

    if df_inv.empty:
            st.warning(
                "⚠️ Inventory is empty. Please add raw feed commodities via the Data Entry Corrections panel first."
            )
    else:
            # 🌟 FILTER: Separate active elements from archived records
            df_active_sliders = df_inv[df_inv["is_active"] == 1] if "is_active" in df_inv.columns else df_inv

            # Create ingredient price map (Updated to use df_active_sliders)
            price_lookup = {
                row["item_name"]: float(row["cost_per_kg"]) for _, row in df_active_sliders.iterrows()
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
            
            # (Your existing slider drawing matrix loop continues here inside tab1 and tab2)
            # Make sure your inner interactive loop now pulls from: df_active_sliders

        # --- SUB-PANEL B: ADVANCED WAREHOUSE INVENTORY MANAGEMENT DESK ---
    st.markdown("---")
    st.subheader("📦 Warehouse Inventory Control Desk")
        
        # Reload fresh dataframe for the control desk tabs
    raw_inv_df = database.get_table_data("inventory")
    if not raw_inv_df.empty and "is_active" in raw_inv_df.columns:
            df_active = raw_inv_df[raw_inv_df["is_active"] == 1]
            df_inactive = raw_inv_df[raw_inv_df["is_active"] == 0]
    else:
            df_active = raw_inv_df
            df_inactive = pd.DataFrame()

    active_item_options = df_active["item_name"].tolist() if not df_active.empty else []
    all_item_options = raw_inv_df["item_name"].tolist() if not raw_inv_df.empty else []

        # Clean workspace separation using three operational tabs
    tab_register, tab_purchase, tab_status = st.tabs([
            "✨ Step 1: Register New Ingredient", 
            "🚛 Step 2: Log Feed Purchases & Stock Adjustments",
            "⏸️ Step 3: Toggle Active / Historical Status"
        ])
        
        # ------------------ TAB 1: REGISTRATION ------------------
    with tab_register:
            st.markdown("### Initial Item Setup")
            with st.form("registration_form_clean"):
                col1, col2 = st.columns(2)
                with col1:
                    new_item_name = st.text_input("Type Brand New Ingredient Name (e.g., Wheat, Radda):").strip()
                with col2:
                    initial_cost = st.number_input("Set Baseline Unit Cost per 1 kg ($):", min_value=0.0, step=0.1, value=15.0)
                
                submit_reg = st.form_submit_button("Register Ingredient with 0.0 kg Stock")
                if submit_reg:
                    if not new_item_name:
                        st.error("Validation Error: Ingredient name cannot be left blank.")
                    elif new_item_name in all_item_options:
                        import sqlite3
                        conn = sqlite3.connect("herd_management.db")
                        cursor = conn.cursor()
                        cursor.execute("UPDATE inventory SET is_active = 1, cost_per_kg = ? WHERE item_name = ?", (initial_cost, new_item_name))
                        conn.commit()
                        conn.close()
                        st.success(f"'{new_item_name}' was previously archived and has been safely reactivated!")
                        st.rerun()
                    else:
                        database.adjust_inventory_stock_advanced(new_item_name, 0.0, initial_cost)
                        import sqlite3
                        conn = sqlite3.connect("herd_management.db")
                        cursor = conn.cursor()
                        cursor.execute("UPDATE inventory SET is_active = 1 WHERE item_name = ?", (new_item_name,))
                        conn.commit()
                        conn.close()
                        st.success(f"'{new_item_name}' successfully registered at $ {initial_cost}/kg!")
                        st.rerun()

        # ------------------ TAB 2: PURCHASES ------------------
    with tab_purchase:
            st.markdown("### Log Warehouse Stock Movements")
            with st.form("purchase_movement_form_clean"):
                col1, col2 = st.columns(2)
                with col1:
                    if active_item_options:
                        chosen_stock_item = st.selectbox("Select Target Feed Ingredient:", active_item_options, key="purch_select")
                    else:
                        st.warning("No active ingredients available. Please register or reactivate items first.")
                        chosen_stock_item = None
                    
                    stock_shift = st.number_input("Stock Volume Shift Value (+ Purchases, - Mix Drawdowns):", step=50.0, value=0.0)
                with col2:
                    current_cost_val = 15.0
                    if chosen_stock_item and not df_active.empty:
                        match_row = df_active[df_active["item_name"] == chosen_stock_item]
                        if not match_row.empty:
                            current_cost_val = float(match_row.iloc[0]["cost_per_kg"])
                    
                    updated_cost = st.number_input("Confirm/Update Unit Buying Cost ($/1 kg):", min_value=0.0, step=0.1, value=current_cost_val)

                submit_purch = st.form_submit_button("Commit Movement Entry to Stock Ledger")
                if submit_purch and chosen_stock_item:
                    database.adjust_inventory_stock_advanced(chosen_stock_item, stock_shift, updated_cost)
                    st.success(f"Warehouse Ledger updated for '{chosen_stock_item}' (Shift: {stock_shift} kg)!")
                    st.rerun()

        # ------------------ TAB 3: STATUS TOGGLE ------------------
    with tab_status:
            st.markdown("### Change Ingredient Status Visibility")
            st.info("Deactivating an item hides its slider from the formulation page, but leaves all historical data untouched.")
            
            col_deact, col_react = st.columns(2)
            
            with col_deact:
                st.markdown("#### ⏸️ Archive Unused Item")
                with st.form("deactivate_form"):
                    if active_item_options:
                        to_deactivate = st.selectbox("Select Ingredient to Hide:", active_item_options, key="deact_box")
                        submit_deact = st.form_submit_button("Mark as Inactive / Archive")
                        if submit_deact and to_deactivate:
                            import sqlite3
                            conn = sqlite3.connect("herd_management.db")
                            cursor = conn.cursor()
                            cursor.execute("UPDATE inventory SET is_active = 0 WHERE item_name = ?", (to_deactivate,))
                            conn.commit()
                            conn.close()
                            st.success(f"'{to_deactivate}' is now hidden from active formulation sliders.")
                            st.rerun()
                    else:
                        st.write("No active items to hide.")

            with col_react:
                st.markdown("#### ▶️ Reactivate Historical Item")
                with st.form("reactivate_form"):
                    inactive_options = df_inactive["item_name"].tolist() if not df_inactive.empty else []
                    if inactive_options:
                        to_reactivate = st.selectbox("Select Ingredient to Restore:", inactive_options, key="react_box")
                        submit_react = st.form_submit_button("Restore to Active Duty")
                        if submit_react and to_reactivate:
                            import sqlite3
                            conn = sqlite3.connect("herd_management.db")
                            cursor = conn.cursor()
                            cursor.execute("UPDATE inventory SET is_active = 1 WHERE item_name = ?", (to_reactivate,))
                            conn.commit()
                            conn.close()
                            st.success(f"'{to_reactivate}' has been restored to your active slider dashboard!")
                            st.rerun()
                    else:
                        st.write("No archived items found.")

    st.subheader("Active Feed Stock Valuation & Safety Parameters")
    st.dataframe(raw_inv_df, use_container_width=True, hide_index=True)


    # 🛠️ MODULE 6: DATA ENTRY CORRECTIONS PANEL
elif menu == "Data Entry Corrections":
        st.title("Data Entry Corrections & Direct SQL Ledger Overrides")
        st.markdown("---")