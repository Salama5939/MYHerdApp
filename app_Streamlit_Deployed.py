import streamlit as st
import pandas as pd
import plotly.express as px
import database
from datetime import datetime

# Configure page settings and default screen layout widths
st.set_page_config(page_title="Professional Herd Controller", layout="wide")
database.initialize_db()

# Construct Left Navigation sidebar menu controls
st.sidebar.title("Navigation Panel")
menu = st.sidebar.radio(
    "Go to module:",
    [
        "Strategic Dashboard",
        "Herd Registry & Intake",
        "Birth Event Registration",
        "Fattening Performance Log",
        "Feed Inventory Controller",
        "Data Entry Corrections",
    ],
)

# MODULE 1: Strategic Dashboard Operations View
if menu == "Strategic Dashboard":
    st.title("Strategic Herd Analysis Dashboard")

    df_herd = database.get_table_data("herd")
    df_inv = database.get_table_data("inventory")

    # Render upper KPI row metric indicator displays
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Head Count", len(df_herd))
    with c2:
        preg_count = (
            len(df_herd[df_herd["category"] == "Pregnant"]) if not df_herd.empty else 0
        )
        st.metric("Gestation Pipeline (Pregnants)", preg_count)
    with c3:
        low_stock = (
            len(df_inv[df_inv["quantity_kg"] <= df_inv["reorder_level_kg"]])
            if not df_inv.empty
            else 0
        )
        st.metric(
            "Low Feed Inventory Alerts",
            low_stock,
            delta=f"-{low_stock} Critical Items" if low_stock > 0 else "Normal",
            delta_color="inverse" if low_stock > 0 else "normal",
        )

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Herd Structural Composition Breakdowns")
        if not df_herd.empty:
            cat_counts = df_herd["category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Head Count"]
            fig = px.pie(
                cat_counts,
                values="Head Count",
                names="Category",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No livestock data currently inside database to render charts.")

    with col_right:
        st.subheader("Physical Feed Resource Balances (kg)")
        if not df_inv.empty:
            fig_bar = px.bar(
                df_inv,
                x="item_name",
                y="quantity_kg",
                labels={
                    "item_name": "Feed Ingredient",
                    "quantity_kg": "Available Stocks (kg)",
                },
                color="quantity_kg",
                color_continuous_scale="Blues",
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No food stock entries tracked inside system registries.")

# MODULE 2: Intake Registration Operations Form
elif menu == "Herd Registry & Intake":
    st.title("Livestock Registration Intake Portal")

    with st.form("animal_registration_form"):
        col1, col2 = st.columns(2)
        with col1:
            tag_no = st.text_input("Ear Tag Number (Must be completely unique):")
            category = st.selectbox(
                "Management Structural Group Assignment:",
                [
                    "Ewes",
                    "Fattening",
                    "Permanent Sire",
                    "Pregnant",
                    "Small Sheep - Female",
                    "Small Sheep - Male",
                ],
            )
        with col2:
            status = st.text_input(
                "Operational Health Status Note:", value="Active/Healthy"
            )
            birth_date = st.date_input(
                "Animal Birth Date (Official or closest estimate):"
            )

        submit = st.form_submit_button("Commit Animal Record to SQLite Database")
        if submit:
            if tag_no.strip() == "":
                st.error("Submission Denied: Ear tag identifier cannot be left blank.")
            else:
                success = database.add_animal(
                    tag_no.strip(), category, status, birth_date.isoformat()
                )
                if success:
                    st.success(
                        f"Success! Animal profile '{tag_no}' appended to permanent records."
                    )
                else:
                    st.error(
                        "Database Integrity Conflict: The inputted ear tag identifier already exists."
                    )

    st.subheader("Active Livestock Registry Data Sheet Ledger")
    st.dataframe(database.get_table_data("herd"), use_container_width=True)

# MODULE 3: Automated Birth Event Processing
elif menu == "Birth Event Registration":
    st.title("Automated Maternal Delivery Processing Hub")
    st.info(
        "System Note: Processing a birth automatically converts the maternal record back to 'Ewes' status and spawns structural linked profiles for the newborn offspring."
    )

    df_herd = database.get_table_data("herd")
    pregnant_list = (
        df_herd[df_herd["category"] == "Pregnant"]["tag_no"].tolist()
        if not df_herd.empty
        else []
    )

    if not pregnant_list:
        st.warning(
            "No livestock units currently flagged as 'Pregnant' inside index lists to execute delivery entries."
        )
    else:
        with st.form("birth_event_form"):
            ewe_tag = st.selectbox("Select Delivering Mother ID Tag:", pregnant_list)
            lamb_count = st.number_input(
                "Offspring Head Count Yield (Heads):", min_value=1, max_value=4, value=1
            )
            lamb_gender = st.selectbox(
                "Offspring Structural Target Category Group:",
                ["Small Sheep - Female", "Small Sheep - Male"],
            )

            submit_birth = st.form_submit_button(
                "Record Birth Delivery and Run Cascade Automation"
            )
            if submit_birth:
                res = database.register_birth_event(ewe_tag, lamb_count, lamb_gender)
                if res:
                    st.success(
                        f"Transaction Complete: Maternal record '{ewe_tag}' updated and {lamb_count} new lamb files initialized."
                    )
                else:
                    st.error(
                        "System Failure: Transaction aborted while processing internal structural tables."
                    )

# MODULE 4: Periodic Weight Logging Performance Metrics
elif menu == "Fattening Performance Log":
    st.title("Market Growth Group Weight Ledger")

    df_herd = database.get_table_data("herd")
    fattening_list = (
        df_herd[df_herd["category"] == "Fattening"]["tag_no"].tolist()
        if not df_herd.empty
        else []
    )

    if not fattening_list:
        st.info(
            "No active livestock units currently categorized inside the market growth group ('Fattening')."
        )
    else:
        with st.form("weight_log_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                selected_tag = st.selectbox(
                    "Select Target Feed Lot Animal Tag:", fattening_list
                )
            with c2:
                current_w = st.number_input(
                    "Observed Scale Weight Metric (kg):",
                    min_value=1.0,
                    max_value=250.0,
                    step=0.5,
                )
            with c3:
                feed_used = st.number_input(
                    "Cumulative Feed Mix Ingested Since Prior Weighing (kg):",
                    min_value=0.0,
                    step=1.0,
                )

            submit_log = st.form_submit_button("Record Weight Log Entry")
            if submit_log:
                database.log_growth_metrics(selected_tag, current_w, feed_used)
                st.success(
                    f"Weight log appended for lot record identification tag '{selected_tag}'."
                )

        st.subheader("Historical Timeline Logs For Market Growth Groups")
        df_logs = database.get_table_data("weight_logs")
        if not df_logs.empty:
            df_logs = df_logs.sort_values(by=["tag_no", "entry_date"])
            st.dataframe(df_logs, use_container_width=True)
        else:
            st.info("Weight timeline logs are currently completely empty.")

# MODULE 5: Warehouse Resource Inventory Balances
elif menu == "Feed Inventory Controller":
    st.title("Warehouse Feed Ingredient Stock Ledger Controller")

    with st.form("inventory_adjustment_form"):
        item_name = st.text_input(
            "Feed Ingredient Description (e.g., Soybean Meal, Alfalfa Hay, Crushed Corn):"
        ).strip()
        add_qty = st.number_input(
            "Inventory Balance Shift Shift Value (Use positive values for purchases, negative values for mix drawdowns):",
            value=0.0,
            step=10.0,
        )

        submit_inv = st.form_submit_button("Update Stock Ledger Account Balance")
        if submit_inv:
            if item_name == "":
                st.error(
                    "Update Denied: Ingredient name definition cannot be left blank."
                )
            else:
                database.adjust_inventory_stock(item_name, add_qty)
                st.success(
                    f"Warehouse Ledger Balance Updated for ingredient item '{item_name}'."
                )

    st.subheader("Active Feed Stock Valuation and Safety Buffer Parameters")
    st.dataframe(database.get_table_data("inventory"), use_container_width=True)

# MODULE 6: Interactive Data Corrections Spreadsheet Tool
elif menu == "Data Entry Corrections":
    st.title("🛠️ System Data Editor & Corrections Panel")
    st.warning(
        "Management Notice: Changing records here directly modifies permanent SQLite database rows. Use with caution."
    )

    table_choice = st.selectbox(
        "Select the Table you need to edit:",
        [
            "Herd Registry (herd)",
            "Weight Logs (weight_logs)",
            "Feed Inventory (inventory)",
        ],
    )

    db_table_map = {
        "Herd Registry (herd)": "herd",
        "Weight Logs (weight_logs)": "weight_logs",
        "Feed Inventory (inventory)": "inventory",
    }
    target_table = db_table_map[table_choice]
    df_current = database.get_table_data(target_table)

    if not df_current.empty:
        st.subheader(f"Interactive Spreadsheet View: {table_choice}")
        st.info(
            "Double-click any cell below to change a value, then click the save button below the table."
        )

        # Display editable grid spreadsheet element
        edited_df = st.data_editor(
            df_current,
            use_container_width=True,
            num_rows="dynamic",
            key=f"editor_{target_table}",
        )

        if st.button(f"Save Amendments to {target_table} Table"):
            conn = database.get_connection()
            try:
                # Safely overwrite the modifications back to SQL file rows
                edited_df.to_sql(target_table, conn, if_exists="replace", index=False)
                st.success(
                    f"Database Updated Successfully! Cleaned table saved to '{target_table}'."
                )
                database.initialize_db()
            except Exception as e:
                st.error(f"Failed to update database: {e}")
            finally:
                conn.close()
    else:
        st.info("This specific database table currently contains zero records to edit.")
