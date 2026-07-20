import streamlit as st
import sys
import os

# This line finds the folder where the current file is located automatically
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
# sys.path.append(r"C:\Users\laphouse\MyHerdApp")
import working_before_merging_database as db
import pandas as pd

st.title("⚖️ Growth Performance Logs")
db.draw_home_button()

## 1. Fetch and Prepare Data
df_weights = db.get_table_data("weight_logs")

if not df_weights.empty:
    df_weights["weigh_date"] = pd.to_datetime(df_weights["weigh_date"])
    df_weights = df_weights.sort_values(by=["tag_no", "weigh_date"])

    # --- THE CLEAN UP CODE ---
    # This resets the internal "address" of the rows so the ghost column disappears
    df_weights = df_weights.reset_index(drop=True)
    # -------------------------

# 2. THE EDITOR
st.subheader("Edit Logs Directly")
edited_df = st.data_editor(
    df_weights,
    num_rows="dynamic",
    width="stretch",
    column_config={"id": st.column_config.NumberColumn("ID", disabled=True)},
)


# 3. SAVE CHANGES (The Logic)
if st.button("💾 Save Changes to Database"):
    try:
        with st.spinner("Processing..."):
            for i, row in edited_df.iterrows():
                # Helper function to extract numbers safely
                def safe_float(val):
                    try:
                        # If it's None, NaN, or Empty, return 0.0
                        if pd.isna(val) or val == "":
                            return 0.0
                        return float(val)
                    except:
                        return 0.0

                # Extract values using the safe helper
                w_kg = safe_float(row["weight_kg"])
                f_kg = safe_float(row["feed_consumed_since_last_kg"])
                f_cost = safe_float(row["feed_cost"])

                # Format dates (using .astype(str) to avoid series issues)
                d_date = pd.to_datetime(row["weigh_date"]).strftime("%Y-%m-%d")
                e_date = pd.to_datetime(row["entry_date"]).strftime("%Y-%m-%d")

                # Logic
                if pd.isna(row["id"]):
                    db.insert_weight_log(
                        str(row["tag_no"]),
                        w_kg,
                        f_kg,
                        f_cost,
                        d_date,
                        str(row["comments"]),
                        e_date,
                    )
                else:
                    db.update_weight_log(
                        int(row["id"]),
                        str(row["tag_no"]),
                        w_kg,
                        f_kg,
                        f_cost,
                        d_date,
                        str(row["comments"]),
                        e_date,
                    )

        st.success("✅ Database Updated Successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Save Failed: {e}")
