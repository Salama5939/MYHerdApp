import streamlit as st
import pandas as pd
import sys
import os
import database as db
from translations import init_language_state, t, apply_rtl_styling

st.set_page_config(page_title="Achievement Report", layout="wide")

# 🔒 SECURITY ACCESS LOCK & LANGUAGE INITIALIZATION
if "authenticated" not in st.session_state or not st.session_state.get(
    "authenticated", False
):
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

init_language_state()
apply_rtl_styling()

is_arabic = st.session_state.get("language", "English") == "العربية (Arabic)"

st.title(t("nav_8"))
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

        target_reached_text = (
            "✅ Target Reached (>=47kg)"
            if not is_arabic
            else "✅ تم بلوغ الهدف (>=47 كجم)"
        )
        in_progress_text = "⏳ In Progress" if not is_arabic else "⏳ قيد التنفيذ"

        summary["Status"] = summary["Current_Weight"].apply(
            lambda x: target_reached_text if x >= 47 else in_progress_text
        )

        # 3. DISPLAY SUMMARY
        st.subheader(
            "Herd Achievement Status" if not is_arabic else "حالة إنجاز القطيع"
        )

        # Highlight the rows that have reached the target
        def highlight_rows(row):
            color = (
                "#d4edda"
                if row["Status"]
                in ["✅ Target Reached (>=47kg)", "✅ تم بلوغ الهدف (>=47 كجم)"]
                else ""
            )
            return [f"background-color: {color}"] * len(row)

        styled_df = summary.style.apply(highlight_rows, axis=1)

        # Translate column headers for display elegance if Arabic
        if is_arabic:
            summary_display = summary.rename(
                columns={
                    "tag_no": "رقم الأذن",
                    "Total_Weights_Recorded": "إجمالي الأوزان المسجلة",
                    "Starting_Weight": "الوزن الابتدائي",
                    "Current_Weight": "الوزن الحالي",
                    "Start_Date": "تاريخ البداية",
                    "Last_Date": "التاريخ الأخير",
                    "Total_Gain_Kg": "إجمالي الزيادة (كجم)",
                    "Status": "الحالة",
                }
            )
            styled_df = summary_display.style.apply(highlight_rows, axis=1)

        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # 4. PRINTABLE SUMMARY BUTTON
        st.info(
            "💡 Tip: Use 'Ctrl + P' to print this summary report for your records."
            if not is_arabic
            else "💡 نصيحة: استخدم 'Ctrl + P' لطباعة تقرير الملخص هذا لسجلاتك."
        )

    else:
        st.warning(
            "No performance logs available for currently active herd."
            if not is_arabic
            else "لا توجد سجلات أداء متاحة للقطيع النشط حالياً."
        )
else:
    st.warning(
        "No performance logs or herd data available."
        if not is_arabic
        else "لا توجد سجلات أداء أو بيانات قطيع متاحة."
    )
