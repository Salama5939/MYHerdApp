import streamlit as st
import sys
import os
import pandas as pd
from datetime import timedelta
import working_before_merging_database as db

st.set_page_config(page_title="Breeding Readiness", layout="wide")
st.title("📅 Breeding Readiness Report")
db.draw_home_button()


# ===================================================
# 📂 Path management
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# ===================================================

# 1. FETCH DATA
df_births = db.get_table_data("birth_records")

if not df_births.empty:
    df_births["birth_date"] = pd.to_datetime(df_births["birth_date"])

    # 2. GET LATEST BIRTH PER EWE
    # We group by ewe_tag_no to find the latest date
    latest_births = df_births.groupby("ewe_tag_no")["birth_date"].max().reset_index()

    # 3. CALCULATE READINESS DATE
    # Adding 3 months (approx 90 days)
    latest_births["Ready_to_Breed_Date"] = latest_births["birth_date"] + pd.DateOffset(
        months=3
    )
    latest_births["Ready_to_Breed_Date"] = pd.to_datetime(
        latest_births["Ready_to_Breed_Date"]
    )

    # 4. CALCULATE STATUS
    today = pd.Timestamp.now().normalize()
    latest_births["Days_Until_Ready"] = (
        latest_births["Ready_to_Breed_Date"] - today
    ).dt.days

    def get_status(days):
        if days <= 0:
            return "✅ Ready Now"
        if days <= 7:
            return "⚠️ Ready in < 1 Week"
        return "⏳ Resting"

    latest_births["Status"] = latest_births["Days_Until_Ready"].apply(get_status)

    # 5. DISPLAY
    st.dataframe(
        latest_births.sort_values("Days_Until_Ready").style.format(
            {"birth_date": "{:%Y-%m-%d}", "Ready_to_Breed_Date": "{:%Y-%m-%d}"}
        ),
        width="stretch",
        hide_index=True,
    )

    st.info(
        "💡 **Planning Note:** This report shows the 3-month recovery mark. Check this list during your weekly rounds to select ewes for the ram."
    )

else:
    st.warning("No birth records found to calculate readiness.")
