# myHerdApp Engine - Comprehensive Herd Management Dashboard
import streamlit as st
import pandas as pd
import plotly.express as px
import database
from datetime import datetime, date
import sqlite3
import requests
import os

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
    
    # --- ☁️ SUPABASE CLOUD SYNC CONFIGURATION ---
    SUPABASE_URL = "https://gvsocmhaarkierzeprgw.supabase.co"
    BUCKET_NAME = "feed-vault"
    DB_FILENAME = "feed_inventory.db"

    DOWNLOAD_URL = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{DB_FILENAME}"
    UPLOAD_URL = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{DB_FILENAME}"

    # 🔑 AUTHENTICATION LAYER
    if "SUPABASE_KEY" in st.secrets:
        SB_API_KEY = st.secrets["SUPABASE_KEY"]
    else:
        SB_API_KEY = ""

    # 🔄 HELPER FUNCTION: PUSH LOCAL DB TO SUPABASE VAULT
    def upload_db_to_supabase():
        if os.path.exists(DB_FILENAME):
            try:
                with open(DB_FILENAME, "rb") as f:
                    response = requests.put(
                        UPLOAD_URL,
                        data=f,
                        headers={
                            "Authorization": f"Bearer {SB_API_KEY}",
                            "Content-Type": "application/x-sqlite3",
                        },
                    )
                if response.status_code in [200, 201]:
                    st.toast(
                        "🔒 Secure Cloud Backup: Database successfully synchronized to Supabase!",
                        icon="✅",
                    )
                else:
                    print(f"⚠️ Cloud Sync Notice: {response.text}")
            except Exception as e:
                print(f"Cloud upload error: {e}")

    # 🚀 INITIAL RUN: DOWNLOAD LIVE DATABASE ONCE ON STARTUP
    if "db_downloaded" not in st.session_state:
        try:
            res = requests.get(DOWNLOAD_URL)
            if res.status_code == 200:
                with open(DB_FILENAME, "wb") as f:
                    f.write(res.content)
                st.session_state.db_downloaded = True
            else:
                st.session_state.db_downloaded = True
        except Exception as download_err:
            st.warning(f"Could not reach Supabase storage. Using local sandbox mode. ({download_err})")

    # ⚡ AUTOMATIC TABLE INITIALIZATION ENGINE
    try:
        conn = sqlite3.connect(DB_FILENAME, timeout=20)
        cursor = conn.cursor()
        
        # 1. Guarantee Core Inventory Table Exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                item_name TEXT PRIMARY KEY,
                quantity_kg REAL DEFAULT 0.0,
                reorder_level_kg REAL DEFAULT 100.0,
                cost_per_kg REAL DEFAULT 15.0,
                is_active INTEGER DEFAULT 1
            );
        """)
        
        # 2. Guarantee Recipe Formulation History Table Exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feed_recipes (
                recipe_type TEXT PRIMARY KEY,
                calculated_mix_cost_per_kg REAL DEFAULT 0.0,
                recipe_breakdown TEXT DEFAULT ''
            );
        """)
        conn.commit()
        conn.close()
    except Exception as db_init_err:
        st.error(f"Critical Database Initialization Error: {db_init_err}")

    # ⚡ DIRECT EXTRACTION LAYER (Keeps sliders and dashboards in fast memory sync)
    if "cached_inventory" not in st.session_state:
        conn = sqlite3.connect(DB_FILENAME, timeout=20)
        st.session_state.cached_inventory = pd.read_sql_query("SELECT * FROM inventory", conn)
        conn.close()
        
    if "cached_recipes" not in st.session_state:
        conn = sqlite3.connect(DB_FILENAME, timeout=20)
        st.session_state.cached_recipes = pd.read_sql_query("SELECT * FROM feed_recipes", conn)
        conn.close()

    # Assign live data frames from our clean session memory cache
    df_inv = st.session_state.cached_inventory
    df_recipes = st.session_state.cached_recipes

    # 🌟 STRUCTURAL CHECKS
    if not df_recipes.empty and "recipe_breakdown" not in df_recipes.columns:
        conn = sqlite3.connect("feed_inventory.db", timeout=20)
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE feed_recipes ADD COLUMN recipe_breakdown TEXT DEFAULT ''")
            conn.commit()
        except Exception:
            pass
        conn.close()
        
        conn = sqlite3.connect("feed_inventory.db", timeout=20)
        df_recipes = pd.read_sql_query("SELECT * FROM feed_recipes", conn)
        conn.close()
        st.session_state.cached_recipes = df_recipes

    if not df_inv.empty and "is_active" not in df_inv.columns:
        conn = sqlite3.connect("feed_inventory.db", timeout=20)
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE inventory ADD COLUMN is_active INTEGER DEFAULT 1")
            conn.commit()
        except Exception:
            pass
        conn.close()
        
        conn = sqlite3.connect("feed_inventory.db", timeout=20)
        df_inv = pd.read_sql_query("SELECT * FROM inventory", conn)
        conn.close()
        st.session_state.cached_inventory = df_inv

    # --- SETUP LIVE RENDER OBJECTS ---
    raw_inv_df = df_inv.copy()
    df_inactive = df_inv[df_inv["is_active"] == 0] if "is_active" in df_inv.columns else pd.DataFrame()
    df_active = df_inv[df_inv["is_active"] == 1] if "is_active" in df_inv.columns else df_inv
    active_item_options = df_active["item_name"].tolist() if not df_active.empty else []

    if df_inv.empty:
        st.warning("⚠️ Feed stock database is currently empty. Please type an item name below to register your first commodity record!")
        df_active_sliders = pd.DataFrame()
    else:
        df_active_sliders = df_active

    # Create ingredient price map dynamically from user database
    price_lookup = {row["item_name"]: float(row["cost_per_kg"]) for _, row in df_active_sliders.iterrows()}
    cost_summary = " | ".join([f"{name}: **${cost}/kg**" for name, cost in price_lookup.items()])
    st.markdown(f"**Current Ingredient Costs:** {cost_summary}")

    # Helper function to decode values stored in the breakdown column
    def get_saved_ratio_dynamic(recipe_type, item_name):
        cached_df = st.session_state.cached_recipes
        if cached_df is not None and not cached_df.empty:
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

    # --- DRAWING THE INTERACTIVE RECIPE SLIDER ENGAGEMENT DESK ---
    tab1, tab2 = st.tabs(["Fattening Formulation", "General Herd Formulation"])

    # 🧪 TAB 1: FATTENING FORMULATION MATRIX
    with tab1:
        st.markdown("#### Adjust Fattening Ingredient Ratios (%)")
        ratios_fattening = {}
        for _, row in df_active_sliders.iterrows():
            ing_name = row["item_name"]
            default_val = get_saved_ratio_dynamic("Fattening", ing_name)
            ratios_fattening[ing_name] = st.slider(
                f"Ratio for {ing_name} (%)",
                min_value=0,
                max_value=100,
                value=default_val,
                key=f"fattening_slide_{ing_name}",
            )

        total_fattening = sum(ratios_fattening.values())
        st.metric("Total Formulation Sum:", f"{total_fattening} %")

        blend_cost_fattening = sum(
            (ratios_fattening[name] / 100.0) * price_lookup[name]
            for name in ratios_fattening
        )
        st.info(f"**Calculated Blended Fattening Feed Cost:** $ {blend_cost_fattening:.2f} per kg")

        if st.button("Save Fattening Blend Specification Parameters", key="save_fattening_btn"):
            if total_fattening != 100:
                st.error("Ratios must sum to exactly 100% before saving.")
            else:
                breakdown_str = ";".join([f"{k}:{v}" for k, v in ratios_fattening.items()])
                conn = sqlite3.connect("herd_management.db", timeout=20)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO feed_recipes (recipe_type, calculated_mix_cost_per_kg, recipe_breakdown) VALUES (?, ?, ?)",
                    ("Fattening", blend_cost_fattening, breakdown_str),
                )
                conn.commit()
                conn.close()

                st.session_state.cached_recipes = database.get_table_data("feed_recipes")
                st.success("Fattening feed parameters committed successfully!")
                st.rerun()

    # 🧪 TAB 2: GENERAL HERD FORMULATION MATRIX
    with tab2:
        st.markdown("#### Adjust General Herd Ingredient Ratios (%)")
        ratios_general = {}
        for _, row in df_active_sliders.iterrows():
            ing_name = row["item_name"]
            default_val = get_saved_ratio_dynamic("General Herd", ing_name)
            ratios_general[ing_name] = st.slider(
                f"Ratio for {ing_name} (%)",
                min_value=0,
                max_value=100,
                value=default_val,
                key=f"general_slide_{ing_name}",
            )

        total_general = sum(ratios_general.values())
        st.metric("Total Formulation Sum:", f"{total_general} %")

        blend_cost_general = sum(
            (ratios_general[name] / 100.0) * price_lookup[name]
            for name in ratios_general
        )
        st.info(f"**Calculated Blended General Feed Cost:** $ {blend_cost_general:.2f} per kg")

        if st.button("Save General Herd Blend Specification Parameters", key="save_general_btn"):
            if total_general != 100:
                st.error("Ratios must sum to exactly 100% before saving.")
            else:
                breakdown_str = ";".join([f"{k}:{v}" for k, v in ratios_general.items()])
                conn = sqlite3.connect("herd_management.db", timeout=20)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO feed_recipes (recipe_type, calculated_mix_cost_per_kg, recipe_breakdown) VALUES (?, ?, ?)",
                    ("General Herd", blend_cost_general, breakdown_str),
                )
                conn.commit()
                conn.close()

                st.session_state.cached_recipes = database.get_table_data("feed_recipes")
                st.success("General Herd feed parameters committed successfully!")
                st.rerun()

    # --- SUB-PANEL B: ADVANCED WAREHOUSE INVENTORY MANAGEMENT DESK ---
    st.markdown("---")
    st.subheader("📦 Warehouse Inventory Control Desk")

    raw_inv_df = database.get_table_data("inventory")
    if not raw_inv_df.empty and "is_active" in raw_inv_df.columns:
        df_active = raw_inv_df[raw_inv_df["is_active"] == 1]
        df_inactive = raw_inv_df[raw_inv_df["is_active"] == 0]
    else:
        df_active = raw_inv_df
        df_inactive = pd.DataFrame()

    active_item_options = df_active["item_name"].tolist() if not df_active.empty else []
    all_item_options = raw_inv_df["item_name"].tolist() if not raw_inv_df.empty else []

    # --- STEP 1: REGISTRATION FORM DIRECT TO ISOLATED LEDGER ---
    st.markdown("### Initial Item Setup")
    with st.form(key="new_ingredient_registration_form"):
        col_reg1, col_reg2 = st.columns(2)
        with col_reg1:
            new_item_name = st.text_input(
                "Type Brand New Ingredient Name (e.g., Wheat, Radda):",
                value="",
                key="new_item_name_input",
            )
        with col_reg2:
            new_item_cost = st.number_input(
                "Set Baseline Unit Cost per 1 kg ($):",
                min_value=0.0,
                step=0.1,
                value=15.0,
                key="new_item_cost_input",
            )

        st.caption("⚠️ **Operational Notice:** Registering or submitting here will clear the application data cache to refresh your sliders immediately.")
        submit_registration = st.form_submit_button("Register Ingredient with 0.0 kg Stock")

        if submit_registration:
            clean_name = new_item_name.strip()
            if clean_name == "":
                st.error("❌ Registration failed: Ingredient name cannot be left empty.")
            else:
                conn = sqlite3.connect("feed_inventory.db", timeout=20)
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM inventory WHERE item_name = ?", (clean_name,))
                exists = cursor.fetchone()

                if exists:
                    st.warning(f"ℹ️ '{clean_name}' already exists in your active inventory catalog.")
                    conn.close()
                else:
                    try:
                        cursor.execute(
                            """
                            INSERT INTO inventory (item_name, quantity_kg, reorder_level_kg, cost_per_kg, is_active)
                            VALUES (?, 0.0, 100.0, ?, 1)
                        """,
                            (clean_name, new_item_cost),
                        )
                        conn.commit()
                        conn.close()

                        if "cached_inventory" in st.session_state:
                            del st.session_state.cached_inventory

                        st.success(f"🎉 Success! '{clean_name}' has been safely registered into your isolated feed stock ledger.")
                        st.rerun()
                    except Exception as e:
                        conn.close()
                        st.error(f"❌ Database error encountered: {e}")

    # Ensure variables exist before rendering tabs
    if "active_item_options" not in locals():
        active_item_options = df_active["item_name"].tolist() if not df_active.empty else []
    if "df_inactive" not in locals():
        df_inactive = df_inv[df_inv["is_active"] == 0] if "is_active" in df_inv.columns else pd.DataFrame()

    # --- UPDATED TAB MANAGEMENT W/ MODIFY & DELETE ---
    tab_purchase, tab_modify, tab_status, tab_delete = st.tabs(
        [
            "📥 Log Stock Movements",
            "✏️ Modify Cost & Safety Alerts",
            "⏸️ Toggle Active/Archive Status",
            "🗑️ Permanent Delete",
        ]
    )

    with tab_purchase:
        st.markdown("### Log Warehouse Stock Movements")
        with st.form(key="purchase_movement_form_isolated"):
            col1, col2 = st.columns(2)
            with col1:
                if active_item_options:
                    chosen_stock_item = st.selectbox(
                        "Select Target Feed Ingredient:",
                        active_item_options,
                        key="purch_select_isolated",
                    )
                else:
                    st.warning("No active ingredients available. Please register or reactivate items first.")
                    chosen_stock_item = None

                stock_shift = st.number_input(
                    "Stock Volume Shift Value (+ Purchases, - Mix Drawdowns):",
                    step=50.0,
                    value=0.0,
                    key="stock_shift_input",
                )
            with col2:
                current_cost_val = 15.0
                if chosen_stock_item and not df_active.empty:
                    match_row = df_active[df_active["item_name"] == chosen_stock_item]
                    if not match_row.empty:
                        current_cost_val = float(match_row.iloc[0]["cost_per_kg"])

                updated_cost = st.number_input(
                    "Confirm/Update Unit Buying Cost ($/1 kg):",
                    min_value=0.0,
                    step=0.1,
                    value=current_cost_val,
                    key="updated_cost_input",
                )

            submit_purch = st.form_submit_button("Commit Movement Entry to Stock Ledger")
            if submit_purch and chosen_stock_item:
                conn = sqlite3.connect("feed_inventory.db", timeout=20)
                cursor = conn.cursor()
                # code will continue smoothly here with your next lines...
                cursor.execute(
                    """
                    UPDATE inventory 
                    SET quantity_kg = quantity_kg + ?, cost_per_kg = ? 
                    WHERE item_name = ?
                    """,
                        (stock_shift, updated_cost, chosen_stock_item),
                    )
                conn.commit()
                conn.close()

                if "cached_inventory" in st.session_state:
                        del st.session_state.cached_inventory

                st.success(
                        f"Warehouse Ledger updated for '{chosen_stock_item}' (Shift: {stock_shift} kg)!"
                    )
                st.rerun()

        with tab_modify:
            st.markdown("### Update Existing Commodity Configurations")
            #=====================================
            with tab_modify:
                st.markdown("### Update Existing Commodity Configurations")
            
            # 1. Keep the dropdown OUTSIDE the form so it triggers an instant update when changed
            if active_item_options:
                target_modify_item = st.selectbox(
                    "Choose Ingredient to Modify:",
                    active_item_options,
                    key="modify_select",
                )

                # Retrieve current specs to pre-populate form inputs dynamically
                current_q, current_r, current_c = 0.0, 100.0, 15.0
                if not df_active.empty and target_modify_item:
                    m_row = df_active[df_active["item_name"] == target_modify_item]
                    if not m_row.empty:
                        current_q = float(m_row.iloc[0]["quantity_kg"])
                        current_r = float(m_row.iloc[0].get("reorder_level_kg", 100.0))
                        current_c = float(m_row.iloc[0]["cost_per_kg"])

                # 2. Start the form container HERE for the inputs and submit button only
                with st.form(key="modify_parameters_form"):
                    mod_col1, mod_col2, mod_col3 = st.columns(3)
                    with mod_col1:
                        new_qty = st.number_input(
                            "Direct Inventory Adjustment (kg):", value=current_q, step=10.0
                        )
                    with mod_col2:
                        new_reorder = st.number_input(
                            "Safety Reorder Threshold Alert level (kg):",
                            value=current_r,
                            step=10.0,
                            )
                    with mod_col3:
                        new_price = st.number_input(
                            "Unit Value Cost per kg ($):", value=current_c, step=0.1
                        )

                    submit_mod = st.form_submit_button("Save Altered Record Parameters")
                    
                    if submit_mod and target_modify_item:
                        import sqlite3
                        conn = sqlite3.connect("feed_inventory.db", timeout=20)
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            UPDATE inventory 
                            SET quantity_kg = ?, reorder_level_kg = ?, cost_per_kg = ? 
                            WHERE item_name = ?
                        """,
                            (new_qty, new_reorder, new_price, target_modify_item),
                        )
                        conn.commit()
                        conn.close()

                        if "cached_inventory" in st.session_state:
                            del st.session_state.cached_inventory
                        st.success(
                            f"✏️ Successfully updated settings for '{target_modify_item}'!"
                        )
                        st.rerun()
            else:
                st.info("No active materials available to edit.")
                    #==========================================

        with tab_status:
            st.markdown("### Change Ingredient Status Visibility")
            st.info(
                "Deactivating an item hides its slider from the formulation page, but leaves all historical data untouched."
            )

            col_deact, col_react = st.columns(2)
            with col_deact:
                st.markdown("#### ⏸️ Archive Unused Item")
                with st.form(key="deactivate_form_isolated"):
                    if active_item_options:
                        to_deactivate = st.selectbox(
                            "Select Ingredient to Hide:",
                            active_item_options,
                            key="deact_box_isolated",
                        )
                        submit_deact = st.form_submit_button("Mark as Inactive / Archive")
                        if submit_deact and to_deactivate:
                            import sqlite3

                            conn = sqlite3.connect("feed_inventory.db", timeout=20)
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE inventory SET is_active = 0 WHERE item_name = ?",
                                (to_deactivate,),
                            )
                            conn.commit()
                            conn.close()

                            if "cached_inventory" in st.session_state:
                                del st.session_state.cached_inventory

                            st.success(
                                f"'{to_deactivate}' is now hidden from active formulation sliders."
                            )
                            st.rerun()
                    else:
                        st.write("No active items to hide.")

            with col_react:
                st.markdown("#### ▶️ Reactivate Historical Item")
                with st.form(key="reactivate_form_isolated"):
                    inactive_options = (
                        df_inactive["item_name"].tolist() if not df_inactive.empty else []
                    )
                    if inactive_options:
                        to_reactivate = st.selectbox(
                            "Select Ingredient to Restore:",
                            inactive_options,
                            key="react_box_isolated",
                        )
                        submit_react = st.form_submit_button("Restore to Active Duty")
                        if submit_react and to_reactivate:
                            import sqlite3

                            conn = sqlite3.connect("feed_inventory.db", timeout=20)
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE inventory SET is_active = 1 WHERE item_name = ?",
                                (to_reactivate,),
                            )
                            conn.commit()
                            conn.close()

                            if "cached_inventory" in st.session_state:
                                del st.session_state.cached_inventory

                            st.success(
                                f"'{to_reactivate}' has been restored to your active slider dashboard!"
                            )
                            st.rerun()
                    else:
                        st.write("No archived items found.")

        with tab_delete:
            st.markdown("### ⚠️ Permanent Record Removal")
            st.error(
                "Danger Zone: Deleting an item removes it permanently from your ledger file. This action cannot be undone."
            )

            # Combine active and inactive items so the user can wipe anything from existence
            all_deletable_items = df_inv["item_name"].tolist() if not df_inv.empty else []

            with st.form(key="hard_delete_form"):
                if all_deletable_items:
                    to_delete_permanently = st.selectbox(
                        "Select Commodity to Wipe Permanently:",
                        all_deletable_items,
                        key="delete_select_box",
                    )
                    confirm_checkbox = st.checkbox(
                        "I confirm that I want to completely delete this row and all its recorded weights from the file."
                    )

                    submit_delete = st.form_submit_button(
                        "Permanently Execute Ledger Purge"
                    )
                    if submit_delete and to_delete_permanently:
                        if not confirm_checkbox:
                            st.error(
                                "❌ Deletion aborted: You must check the confirmation box first."
                            )
                        else:
                            import sqlite3

                            conn = sqlite3.connect("feed_inventory.db", timeout=20)
                            cursor = conn.cursor()
                            cursor.execute(
                                "DELETE FROM inventory WHERE item_name = ?",
                                (to_delete_permanently,),
                            )
                            conn.commit()
                            conn.close()

                            if "cached_inventory" in st.session_state:
                                del st.session_state.cached_inventory
                            st.success(
                                f"💥 '{to_delete_permanently}' has been permanently wiped from the ledger file database."
                            )
                            st.rerun()
                else:
                    st.info("No records present to delete.")

        # --- DATAFRAME RENDERING: SYNCED EXCLUSIVELY WITH ISOLATED DB ---
        st.subheader("Active Feed Stock Valuation & Safety Parameters")
        if not df_inv.empty:
            st.dataframe(df_inv, use_container_width=True, hide_index=True)
        else:
            st.info("No active records to display in the main inventory ledger.")