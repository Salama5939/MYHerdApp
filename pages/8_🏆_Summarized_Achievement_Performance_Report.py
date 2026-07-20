import streamlit as st
import pandas as pd
import sys
import os
import working_before_merging_database as db

st.set_page_config(page_title="Achievement Report", layout="wide")
st.title("🏆 Summarized Achievement Report")
db.draw_home_button()

# ===================================================
# 📂 Path management
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# ===================================================

# 1. FETCH DATA
df = db.get_table_data("weight_logs")
df_herd = db.get_table_data("herd")

if not df.empty and not df_herd.empty:
    # Filter out inactive animals
    excluded_statuses = ["Died", "Slaughtered", "Sold", "Zakate", "Donate"]
    active_tags = df_herd[~df_herd["status"].isin(excluded_statuses)]["tag_no"].unique()

    # Filter the weight logs to only include active tags
    df = df[df["tag_no"].isin(active_tags)]

    if not df.empty:
        df["weigh_date"] = pd.to_datetime(df["weigh_date"])

        # 2. CALCULATE ACHIEVEMENTS PER TAG
        # Sorting by tag_no AND id ensures first=earliest, last=latest
        df = df.sort_values(by=["tag_no", "id"])

        # Group and aggregate
        summary = (
            df.groupby("tag_no")
            .agg(
                Total_Weights_Recorded=("weight_kg", "count"),
                Starting_Weight=("weight_kg", "first"),
                Current_Weight=("weight_kg", "last"),
                Start_Date=("weigh_date", "first"),
                Last_Date=("weigh_date", "last"),
            )
            .reset_index()
        )

        # Clean up: Ensure the final report is sorted by Tag #
        summary = summary.sort_values(by="tag_no")

        # Calculate specific achievements
        summary["Total_Gain_Kg"] = (
            summary["Current_Weight"] - summary["Starting_Weight"]
        )
        summary["Status"] = summary["Current_Weight"].apply(
            lambda x: "✅ Target Reached (>=47kg)" if x >= 47 else "⏳ In Progress"
        )

        # 3. DISPLAY SUMMARY
        st.subheader("Herd Achievement Status")

        # Highlight the rows that have reached the target
        def highlight_rows(row):
            color = "#d4edda" if row["Status"] == "✅ Target Reached (>=47kg)" else ""
            return [f"background-color: {color}"] * len(row)

        styled_df = summary.style.apply(highlight_rows, axis=1)

        st.dataframe(styled_df, width=1200)

        # 4. PRINTABLE SUMMARY BUTTON
        st.info("💡 Tip: Use 'Ctrl + P' to print this summary report for your records.")

    else:
        st.warning("No performance logs available for currently active herd.")
else:
    st.warning("No performance logs or herd data available.")
