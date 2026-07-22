import os
import streamlit as st
import pandas as pd
import sys
import datetime
import database as db
from translations import init_language_state, t, apply_rtl_styling

# 🖥️ Force Wide Layout to use full screen space
st.set_page_config(page_title="Individual Performance Report", layout="wide")

# 🔒 SECURITY ACCESS LOCK & LANGUAGE INITIALIZATION
if "authenticated" not in st.session_state or not st.session_state.get(
    "authenticated", False
):
    st.warning("🔒 Access Denied. Please log in on the main Home Page first.")
    st.stop()

init_language_state()
apply_rtl_styling()

is_arabic = st.session_state.get("language", "English") == "العربية (Arabic)"

st.title(t("nav_7"))
db.draw_home_button()

# ===================================================
# 📂 Path management
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# ===================================================

# 1. FETCH DATA
df_herd = db.get_table_data("herd")

# Fetch the list dynamically
excluded = db.get_excluded_statuses()

# Filter herd data to remove excluded statuses
active_df = df_herd[~df_herd["status"].isin(excluded)]
active_tags = active_df["tag_no"].unique()

# Fetch weight logs and filter immediately
df = db.get_table_data("weight_logs")
df = df[df["tag_no"].isin(active_tags)]

if not df.empty:
    df["weigh_date"] = pd.to_datetime(df["weigh_date"])
    df = df.sort_values(["tag_no", "weigh_date"])

    # 2. SELECT TAG
    selected_tag = st.selectbox(
        "Select Tag #:" if not is_arabic else "اختر رقم الأذن:", df["tag_no"].unique()
    )
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
                target_str = (
                    "Target reached or no gain"
                    if not is_arabic
                    else "تم بلوغ الهدف أو لا توجد زيادة"
                )
        else:
            gained_per_day = 0
            grams_per_day = 0
            target_str = "Insufficient data" if not is_arabic else "بيانات غير كافية"

        # 5. DISPLAY REPORT
        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Total Weight Gained" if not is_arabic else "إجمالي الوزن المكتسب",
            f"{weight_gained:.2f} Kg",
        )
        col2.metric(
            "Gained per Day" if not is_arabic else "المعدل اليومي للزيادة",
            f"{grams_per_day:.0f} g/day",
        )
        col3.metric(
            "Target Date (40Kg)" if not is_arabic else "تاريخ المستهدف (40 كجم)",
            target_str,
        )

        st.subheader("Weight History" if not is_arabic else "سجل الأوزان")

        # Translate dataframe columns for display elegance if Arabic
        display_weight_df = tag_data[
            ["weigh_date", "weight_kg", "feed_consumed_since_last_kg"]
        ].copy()
        if is_arabic:
            display_weight_df = display_weight_df.rename(
                columns={
                    "weigh_date": "تاريخ الوزن",
                    "weight_kg": "الوزن (كجم)",
                    "feed_consumed_since_last_kg": "الأعلاف المستهلكة منذ آخر وزن (كجم)",
                }
            )

        st.dataframe(display_weight_df, use_container_width=True, hide_index=True)

    else:
        st.warning(
            "Need at least two weight entries for this tag to calculate performance."
            if not is_arabic
            else "تحتاج إلى سجلين وزن على الأقل لهذا الكود لحساب الأداء."
        )
else:
    st.info(
        "No active performance logs found for the current herd."
        if not is_arabic
        else "لم يتم العثور على سجلات أداء نشطة للقطيع الحالي."
    )
