import streamlit as st
import pandas as pd
import plotly.express as px
import database
from datetime import datetime

# Configure page layout and visual alignment
st.set_page_config(page_title="Professional Herd Controller", layout="wide")
database.initialize_db()

# Navigation panel layout configuration
st.sidebar.title("Navigation Panel")
menu = st.sidebar.radio(
    "Go to module:",
    [
        "Strategic Dashboard",
        "Herd Registry & Intake",
        "Birth Event Registration",
        "Fattening Performance Log",
        "Feed Inventory Controller",
    ],
)

# MODULE 1: STRATEGIC DASHBOARD
if menu == "Strategic Dashboard":
    st.title("Strategic Herd Analysis Dashboard")

    # Retrieve core operational matrices
    df_herd = database.get_table_data("herd")
    df_inv = database.get_table_data("inventory")

    # Top Metrics Bar
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
        )

    # Layout Split for Deep Analysis Graphics
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
                labels={"item_name": "Ingredient", "quantity_kg": "Available (kg)"},
                color="quantity_kg",
                color_continuous_scale="Blues",
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No food stock entries tracked inside system registries.")

# MODULE 2: HERD REGISTRY
elif menu == "Herd Registry & Intake":
    st.title("Livestock Allocation Registry")

    with st.form("animal_registration_form"):
        col1, col2 = st.columns(2)
        with col1:
            tag_no = st.text_input("Official Ear Tag Identification Number (Unique):")
            category = st.selectbox(
                "Livestock Structural Category Matrix:",
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
                "Active Operational Health Status Notes:", value="Active/Healthy"
            )
            birth_date = st.date_input("Observed or Documented Birth Window Date:")

        submit = st.form_submit_button("Commit Animal Record to SQLite Database")
        if submit:
            if tag_no.strip() == "":
                st.error(
                    "Operation failed: Ear Tag Identification text field cannot remain empty."
                )
            else:
                success = database.add_animal(
                    tag_no.strip(), category, status, birth_date.isoformat()
                )
                if success:
                    st.success(
                        f"Tag ID {tag_no} logged successfully into core database matrix."
                    )
                else:
                    st.error(
                        "Database conflict: Tag ID already matches an entry inside database index records."
                    )

    st.subheader("Registered Herd Data Grid View")
    st.dataframe(database.get_table_data("herd"), use_container_width=True)

# MODULE 3: BIRTH EVENT REGISTRATION
elif menu == "Birth Event Registration":
    st.title("Maternal Birth Logging Interface")
    st.info(
        "System Action Note: Registering a birth event automatically transitions the mother from 'Pregnant' to 'Ewes' category and bulk logs offspring records with linked tags."
    )

    df_herd = database.get_table_data("herd")
    pregnant_list = (
        df_herd[df_herd["category"] == "Pregnant"]["tag_no"].tolist()
        if not df_herd.empty
        else []
    )

    if not pregnant_list:
        st.warning(
            "No livestock tracking indices are flagged as matching the 'Pregnant' category criteria."
        )
    else:
        with st.form("birth_event_form"):
            ewe_tag = st.selectbox(
                "Select Dam/Maternal Ear Tag Identifier:", pregnant_list
            )
            lamb_count = st.number_input(
                "Count of Born Offspring (Heads):", min_value=1, max_value=4, value=1
            )
            lamb_gender = st.selectbox(
                "Assign Offspring Demographics Target:",
                ["Small Sheep - Female", "Small Sheep - Male"],
            )

            submit_birth = st.form_submit_button(
                "Record Birth and Execute Category Adjustments"
            )
            if submit_birth:
                res = database.register_birth_event(ewe_tag, lamb_count, lamb_gender)
                if res:
                    st.success(
                        f"Maternal state changed for Ewe {ewe_tag}. {lamb_count} lambs generated inside active database profiles."
                    )
                else:
                    st.error(
                        "System transaction error: Processing database update failed."
                    )

# MODULE 4: FATTENING WEIGHT MONITOR
elif menu == "Fattening Performance Log":
    st.title("Performance Weight Journal & Growth Diagnostics")

    df_herd = database.get_table_data("herd")
    fattening_list = (
        df_herd[df_herd["category"] == "Fattening"]["tag_no"].tolist()
        if not df_herd.empty
        else []
    )

    if not fattening_list:
        st.info(
            "No livestock are currently allocated under the 'Fattening' category profile."
        )
    else:
        with st.form("weight_log_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                selected_tag = st.selectbox("Select Target Animal Tag:", fattening_list)
            with c2:
                current_w = st.number_input(
                    "Observed Scale Weight (kg):",
                    min_value=1.0,
                    max_value=250.0,
                    step=0.5,
                )
            with c3:
                feed_used = st.number_input(
                    "Dry Feed Content Eaten Since Last Evaluation (kg):",
                    min_value=0.0,
                    step=1.0,
                )

            submit_log = st.form_submit_button("Record Weight Log Entry")
            if submit_log:
                database.log_growth_metrics(selected_tag, current_w, feed_used)
                st.success(f"Weight profile logged for tracking ID {selected_tag}.")

        # Performance Calculations Engine Block
        st.subheader("Historical Scale Dynamic Metrics Journals")
        df_logs = database.get_table_data("weight_logs")
        if not df_logs.empty:
            # Group records to sort and isolate historical data points
            df_logs = df_logs.sort_values(by=["tag_no", "entry_date"])
            st.dataframe(df_logs, use_container_width=True)
        else:
            st.info(
                "No weight tracking telemetry saved inside the active journal database."
            )

# MODULE 5: INVENTORY CONTROL
elif menu == "Feed Inventory Controller":
    st.title("Physical Feed Inventory Controller")

    with st.form("inventory_adjustment_form"):
        item_name = st.text_input(
            "Ingredient Identifier Name (e.g., Alfalfa Hay, Soybean Meal, Yellow Corn):"
        ).strip()
        add_qty = st.number_input(
            "Quantity Volumetric Shift (Use positive values for purchases, negative for manual drawdowns):",
            value=0.0,
            step=10.0,
        )

        submit_inv = st.form_submit_button("Update Stock Ledger Entries")
        if submit_inv:
            if item_name == "":
                st.error("Item name field validation failed.")
            else:
                database.adjust_inventory_stock(item_name, add_qty)
                st.success(f"Stock ledger configuration adjusted for '{item_name}'.")

    st.subheader("Current Operational Warehouse Stock Ledger Balance Sheet")
    st.dataframe(database.get_table_data("inventory"), use_container_width=True)
