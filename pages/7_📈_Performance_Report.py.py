import os
import streamlit as st
import pandas as pd
import sys
import datetime
import working_before_merging_database as db

st.title("📈 Individual Performance Report")
db.draw_home_button()

# ===================================================
# 📂 Path management
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# ===================================================

# 1. FETCH DATA
# First, fetch herd data to identify active tags

df_herd = db.get_table_data("herd")

# Old Code: This was the original way to filter out inactive animals, but it was commented out in favor of a more dynamic approach.
# These are the statuses that mean the animal is no longer in the active herd

# Fetch the list dynamically
excluded = db.get_excluded_statuses()

# Filter herd data to remove excluded statuses
active_df = df_herd[~df_herd["status"].isin(excluded)]
active_tags = active_df["tag_no"].unique()
# df = df[df["tag_no"].isin(active_tags)]

# Fetch weight logs and filter immediately
df = db.get_table_data("weight_logs")
df = df[df["tag_no"].isin(active_tags)]  # <--- THIS IS THE FIX

if not df.empty:
    df["weigh_date"] = pd.to_datetime(df["weigh_date"])
    df = df.sort_values(["tag_no", "weigh_date"])

    # 2. SELECT TAG
    selected_tag = st.selectbox("Select Tag #:", df["tag_no"].unique())
    tag_data = df[df["tag_no"] == selected_tag]

    if len(tag_data) >= 2:
        # 3. CALCULATIONS
        last_row = tag_data.iloc[-1]
        prev_row = tag_data.iloc[-2]

        weight_gained = last_row["weight_kg"] - prev_row["weight_kg"]
        days_between = (last_row["weigh_date"] - prev_row["weigh_date"]).days

        # Avoid division by zero
        if days_between > 0:
            gained_per_day = weight_gained / days_between  # in Kg per day
            grams_per_day = gained_per_day * 1000  # Convert to grams

            # 4. PROJECTION (Target 40kg)
            if last_row["weight_kg"] < 40 and gained_per_day > 0:
                days_to_target = (40 - last_row["weight_kg"]) / gained_per_day
                target_date = last_row["weigh_date"] + datetime.timedelta(
                    days=days_to_target
                )
                target_str = target_date.strftime("%Y-%m-%d")
            else:
                target_str = "Target reached or no gain"
        else:
            gained_per_day = 0
            grams_per_day = 0
            target_str = "Insufficient data"

        # 5. DISPLAY REPORT
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Weight Gained", f"{weight_gained:.2f} Kg")
        col2.metric("Gained per Day", f"{grams_per_day:.0f} g/day")
        col3.metric("Target Date (40Kg)", target_str)

        st.subheader("Weight History")
        st.dataframe(
            tag_data[["weigh_date", "weight_kg", "feed_consumed_since_last_kg"]]
        )

    else:
        st.warning(
            "Need at least two weight entries for this tag to calculate performance."
        )
else:
    st.info("No active performance logs found for the current herd.")
