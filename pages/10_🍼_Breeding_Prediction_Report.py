import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
import datetime
import working_before_merging_database as db

st.set_page_config(page_title="Breeding Prediction", layout="wide")
st.title("🍼 Breeding Prediction Report")
db.draw_home_button()


# ===================================================
# 📂 Path management
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# ===================================================

# 1. FETCH DATA
df = db.get_table_data("herd")

if not df.empty and "registration_date" in df.columns:
    # Convert to datetime
    df["registration_date"] = pd.to_datetime(df["registration_date"])

    # 2. FILTER FOR PREGNANT SHEEP
    # Debug line: Uncomment this to see what your categories actually look like
    # st.write("Categories found in data:", df['category'].unique())

    if "category" in df.columns:
        # .str.strip() removes extra spaces before/after the word
        # .str.lower() makes it all lowercase
        pregnant_df = df[
            df["category"].astype(str).str.strip().str.lower() == "pregnant"
        ].copy()
    else:
        st.error("Column 'category' not found in herd data.")
        pregnant_df = pd.DataFrame()

    if not pregnant_df.empty:
        # 3. CALCULATE DELIVERY METRICS
        # Gestation: 155 days (Midpoint of 150-160 range)
        gestation_days = 155
        pregnant_df["Expected_Delivery_Date"] = pregnant_df[
            "registration_date"
        ] + pd.Timedelta(days=gestation_days)

        # Calculate days remaining until delivery
        today = pd.Timestamp.now().normalize()
        pregnant_df["Days_Remaining"] = (
            pregnant_df["Expected_Delivery_Date"] - today
        ).dt.days

        # 4. ORGANIZE REPORT
        # Select and rename columns for clarity
        display_df = pregnant_df[
            ["tag_no", "registration_date", "Expected_Delivery_Date", "Days_Remaining"]
        ].copy()

        display_df.columns = [
            "Tag #",
            "Pregnancy Start Date",
            "Expected Delivery Date",
            "Days to Delivery",
        ]

        # Sort by expected date
        display_df = display_df.sort_values(by="Expected Delivery Date")

        # 5. DISPLAY
        st.subheader("Current Pregnant Herd")

        # Style the countdown
        st.dataframe(
            display_df.style.format(
                {
                    "Pregnancy Start Date": "{:%Y-%m-%d}",
                    "Expected Delivery Date": "{:%Y-%m-%d}",
                }
            ).background_gradient(subset=["Days to Delivery"], cmap="RdYlGn_r"),
            use_container_width=True,
            hide_index=True,
        )

        st.info(
            "💡 **Planning Note:** The expected delivery date is calculated using a 155-day gestation period. Please account for the natural 150-160 day variation."
        )

    else:
        st.success("No sheep currently marked as 'Pregnant' in the herd registry.")
else:
    st.warning(
        "Ensure your 'herd' table has a 'registration_date' column and contains data."
    )
