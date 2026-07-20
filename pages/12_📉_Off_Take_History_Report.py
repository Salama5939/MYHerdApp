import streamlit as st
import pandas as pd
import sys
import os
import working_before_merging_database as db

st.set_page_config(page_title="Off-Take History", layout="wide")
st.title("📉 Off-Take History Report")
db.draw_home_button()


# ===================================================
# 📂 Path management
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# ===================================================

# 1. FETCH DATA
df_herd = db.get_table_data("herd")

if not df_herd.empty:
    # 2. DEFINE EXCLUSION LIST
    # These are the statuses that mean the animal is no longer in the active herd
    excluded_statuses = ["Died", "Slaughtered", "Sold", "Zakate", "Donate"]

    # 3. FILTER FOR OFF-TAKE
    # We select ONLY the rows where status is in our excluded list
    off_take_df = df_herd[df_herd["status"].isin(excluded_statuses)].copy()

    if not off_take_df.empty:
        # 4. SORTING
        # Sort by status so you see all 'Slaughtered' together, all 'Died' together, etc.
        off_take_df = off_take_df.sort_values(by="status")

        # 5. DISPLAY
        st.subheader(f"Total Animals Removed: {len(off_take_df)}")

        st.dataframe(off_take_df, width="stretch", hide_index=True)

        # Quick Summary
        summary = off_take_df["status"].value_counts().reset_index()
        summary.columns = ["Status", "Count"]

        st.markdown("### Summary by Reason")
        st.table(summary)

        st.info(
            "💡 Tip: This report serves as your audit trail. Cross-reference these tags with your manual logs to ensure your records are complete."
        )

    else:
        st.success("No off-take (Sold/Slaughtered/Died/Zakate/Donate) records found.")
else:
    st.warning("No data found in the 'herd' table.")
