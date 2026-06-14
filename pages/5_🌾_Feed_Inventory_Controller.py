import sys
import os
import streamlit as st
import pandas as pd

# 📂 Path setup to find your database.py file
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import database as db

# 🔒 SECURITY ACCESS LOCK
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

st.title("Warehouse Inventory & Blended Feed Recipe Calculators")

# 🟢 Add this one line to every page!
db.draw_home_button()

st.markdown("---")
st.subheader("🧪 Interactive Feed Recipe Cost Formulation Desks")

# ⚡ LIVE CLOUD DATA EXTRACTION
try:
    df_inv = db.get_table_data("inventory")
    df_recipes = db.get_table_data("feed_recipes")

    # Update session cache for the dynamic sliders
    st.session_state.cached_recipes = df_recipes
except Exception as e:
    st.error(f"Cloud Connection Error: {e}")
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
    st.markdown(f"**Current Ingredient Costs:** {cost_summary}")


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
            0,
            100,
            default_val,
            key=f"fattening_slide_{ing_name}",
        )

    total_fattening = sum(ratios_fattening.values())
    st.metric("Total Formulation Sum:", f"{total_fattening} %")

    blend_cost_fattening = sum(
        (ratios_fattening[name] / 100.0) * price_lookup[name]
        for name in ratios_fattening
    )
    st.info(
        f"**Calculated Blended Fattening Feed Cost:** $ {blend_cost_fattening:.2f} per kg"
    )

    if st.button(
        "Save Fattening Blend Specification Parameters", key="save_fattening_btn"
    ):
        if total_fattening != 100:
            st.error("Ratios must sum to exactly 100% before saving.")
        else:
            breakdown_str = ";".join([f"{k}:{v}" for k, v in ratios_fattening.items()])
            try:
                # 🟢 Pure PostgreSQL ON CONFLICT statement using %s
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
                )
                st.rerun()
            except Exception as e:
                st.error(f"Database Execution Error: {e}")

# 🧪 TAB 2: GENERAL HERD FORMULATION MATRIX
with tab2:
    st.markdown("#### Adjust General Herd Ingredient Ratios (%)")
    ratios_general = {}
    for _, row in df_active_sliders.iterrows():
        ing_name = row["item_name"]
        default_val = get_saved_ratio_dynamic("General Herd", ing_name)
        ratios_general[ing_name] = st.slider(
            f"Ratio for {ing_name} (%)",
            0,
            100,
            default_val,
            key=f"general_slide_{ing_name}",
        )

    total_general = sum(ratios_general.values())
    st.metric("Total Formulation Sum:", f"{total_general} %")

    blend_cost_general = sum(
        (ratios_general[name] / 100.0) * price_lookup[name] for name in ratios_general
    )
    st.info(
        f"**Calculated Blended General Feed Cost:** $ {blend_cost_general:.2f} per kg"
    )

    if st.button(
        "Save General Herd Blend Specification Parameters", key="save_general_btn"
    ):
        if total_general != 100:
            st.error("Ratios must sum to exactly 100% before saving.")
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
                )
                st.rerun()
            except Exception as e:
                st.error(f"Database Execution Error: {e}")

# --- SUB-PANEL B: ADVANCED WAREHOUSE INVENTORY MANAGEMENT DESK ---
st.markdown("---")
st.subheader("📦 Warehouse Inventory Control Desk")

# --- STEP 1: REGISTRATION FORM DIRECT TO ISOLATED LEDGER ---
st.markdown("### Initial Item Setup")
with st.form(key="new_ingredient_registration_form"):
    col_reg1, col_reg2 = st.columns(2)
    with col_reg1:
        new_item_name = st.text_input(
            "Type Brand New Ingredient Name (e.g., Wheat, Radda):", value=""
        ).strip()
    with col_reg2:
        new_item_cost = st.number_input(
            "Set Baseline Unit Cost per 1 kg ($):", min_value=0.0, step=0.1, value=15.0
        )

    submit_registration = st.form_submit_button("Register Ingredient with 0.0 kg Stock")

    if submit_registration:
        if new_item_name == "":
            st.error("❌ Registration failed: Ingredient name cannot be empty.")
        else:
            try:
                # 🟢 Safely check if it exists in the cloud first without triggering Pylance errors
                existing = db.execute_custom_query(
                    "SELECT 1 FROM inventory WHERE item_name = %s", (new_item_name,)
                )

                if isinstance(existing, pd.DataFrame) and not existing.empty:
                    st.warning(
                        f"ℹ️ '{new_item_name}' already exists in your cloud catalog."
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
                    )
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Database error: {e}")

# --- UPDATED TAB MANAGEMENT W/ MODIFY & DELETE ---
tab_purchase, tab_modify, tab_status, tab_delete = st.tabs(
    [
        "📥 Log Stock Movements",
        "✏️ Modify Cost & Alerts",
        "⏸️ Toggle Status",
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
                    "Select Target Feed Ingredient:", active_item_options
                )
            else:
                st.warning("No active ingredients available.")
                chosen_stock_item = None

            stock_shift = st.number_input(
                "Stock Volume Shift (+ Purchases, - Drawdowns):", step=50.0, value=0.0
            )
        with col2:
            current_cost_val = 15.0
            if chosen_stock_item and not df_active.empty:
                match_row = df_active[df_active["item_name"] == chosen_stock_item]
                if not match_row.empty:
                    current_cost_val = float(match_row.iloc[0]["cost_per_kg"])

            updated_cost = st.number_input(
                "Confirm/Update Unit Cost ($/kg):",
                min_value=0.0,
                step=0.1,
                value=current_cost_val,
            )

        if st.form_submit_button("Commit Movement Entry") and chosen_stock_item:
            db.execute_custom_query(
                "UPDATE inventory SET quantity_kg = quantity_kg + %s, cost_per_kg = %s WHERE item_name = %s",
                (stock_shift, updated_cost, chosen_stock_item),
                is_select=False,
            )
            st.success(f"Cloud Ledger updated for '{chosen_stock_item}'!")
            st.rerun()

with tab_modify:
    st.markdown("### Update Existing Commodity Configurations")
    if active_item_options:
        target_modify_item = st.selectbox(
            "Choose Ingredient to Modify:", active_item_options, key="modify_select"
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
                    "Inventory Adjustment (kg):", value=current_q, step=10.0
                )
            with mod_col2:
                new_reorder = st.number_input(
                    "Safety Threshold (kg):", value=current_r, step=10.0
                )
            with mod_col3:
                new_price = st.number_input(
                    "Cost per kg ($):", value=current_c, step=0.1
                )

            if st.form_submit_button("Save Altered Record") and target_modify_item:
                db.execute_custom_query(
                    "UPDATE inventory SET quantity_kg = %s, reorder_level_kg = %s, cost_per_kg = %s WHERE item_name = %s",
                    (new_qty, new_reorder, new_price, target_modify_item),
                    is_select=False,
                )
                st.success(f"✏️ Successfully updated '{target_modify_item}'!")
                st.rerun()
    else:
        st.info("No active materials available.")

with tab_status:
    st.markdown("### Change Ingredient Status Visibility")
    col_deact, col_react = st.columns(2)

    with col_deact:
        st.markdown("#### ⏸️ Archive Item")
        with st.form(key="deact_form"):
            if active_item_options:
                to_deactivate = st.selectbox(
                    "Select Ingredient to Hide:", active_item_options
                )
                if st.form_submit_button("Mark as Inactive") and to_deactivate:
                    db.execute_custom_query(
                        "UPDATE inventory SET is_active = 0 WHERE item_name = %s",
                        (to_deactivate,),
                        is_select=False,
                    )
                    st.success("Item archived.")
                    st.rerun()
            else:
                st.form_submit_button("Archive Disabled", disabled=True)

    with col_react:
        st.markdown("#### ▶️ Reactivate Item")
        with st.form(key="react_form"):
            inactive_options = (
                df_inactive["item_name"].tolist() if not df_inactive.empty else []
            )
            if inactive_options:
                to_reactivate = st.selectbox(
                    "Select Ingredient to Restore:", inactive_options
                )
                if st.form_submit_button("Restore to Active Duty") and to_reactivate:
                    db.execute_custom_query(
                        "UPDATE inventory SET is_active = 1 WHERE item_name = %s",
                        (to_reactivate,),
                        is_select=False,
                    )
                    st.success("Item restored!")
                    st.rerun()
            else:
                st.form_submit_button("Restore Disabled", disabled=True)

with tab_delete:
    st.markdown("### ⚠️ Permanent Record Removal")
    all_deletable_items = df_inv["item_name"].tolist() if not df_inv.empty else []

    with st.form(key="hard_delete_form"):
        if all_deletable_items:
            to_delete = st.selectbox("Select Commodity to Wipe:", all_deletable_items)
            confirm_checkbox = st.checkbox(
                "I confirm permanent deletion from the cloud."
            )

            if st.form_submit_button("Permanently Purge") and to_delete:
                if not confirm_checkbox:
                    st.error("❌ You must check the confirmation box.")
                else:
                    db.execute_custom_query(
                        "DELETE FROM inventory WHERE item_name = %s",
                        (to_delete,),
                        is_select=False,
                    )
                    st.success(f"💥 '{to_delete}' wiped from the cloud database.")
                    st.rerun()
        else:
            st.info("No records to delete.")

# --- DATAFRAME RENDERING ---
st.subheader("Active Feed Stock Valuation & Safety Parameters")
if not df_inv.empty:
    st.dataframe(df_inv, width="stretch", hide_index=True)
else:
    st.info("No active records to display.")
