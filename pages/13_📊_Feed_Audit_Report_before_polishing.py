from datetime import datetime
import os
import tomllib
import pandas as pd
import psycopg2
import streamlit as st
from typing import Tuple

st.set_page_config(
    page_title="Feed Audit & Variance Report", page_icon="📊", layout="wide"
)


# --- 1. Database Connection Helper ---
def get_db_connection():
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    with open(secrets_path, "rb") as f:
        secrets = tomllib.load(f)
    db_url = secrets.get("FINANCE_DB_URL") or secrets.get("CONNECTION_STRING")
    return psycopg2.connect(db_url)


# --- 2. Data Fetching ---
@st.cache_data(ttl=60)
def fetch_audit_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    conn = get_db_connection()
    try:
        df_tx = pd.read_sql("SELECT * FROM financial_transactions WHERE approved = 1", conn)  # type: ignore
        df_weights = pd.read_sql("SELECT * FROM weight_logs", conn)  # type: ignore
        df_herd = pd.read_sql("SELECT * FROM herd", conn)  # type: ignore
    finally:
        conn.close()
    return df_tx, df_weights, df_herd


# --- 3. UI & Report Generation ---
st.title("📊 Biological Feed Variance & Audit Report")
st.markdown(
    "Comprehensive nutritional audit cross-checking your precise ingredient mix recipes against actual ledger expenses."
)

# --- SIDEBAR: Date Range & Parameters ---
st.sidebar.header("📋 Audit Date Range & Parameters")
start_date = st.sidebar.date_input("Start Date", value=datetime(2026, 1, 1))
end_date = st.sidebar.date_input("End Date", value=datetime.now().date())

days_diff = max(1, (end_date - start_date).days)
st.sidebar.info(
    f"📅 Active Audit Period: **{days_diff} days** ({start_date} to {end_date})"
)

st.sidebar.subheader("Nutritional Mix Profiles (per 100 kg)")
fat_mix_type = st.sidebar.selectbox("Fattening Mix", ["Fattening Mix"])
gen_mix_type = st.sidebar.selectbox("General/Breeding Mix", ["General Herd Mix"])

gen_daily_feed_per_head = st.sidebar.number_input(
    "General Herd Daily Intake (kg/head/day)", value=1.8, step=0.1
)

if st.button("Run Comprehensive Feed Audit", type="primary"):
    df_tx, df_weights, df_herd = fetch_audit_data()

    # 1. Dynamic Head Counts
    fat_head_count = 0
    gen_head_count = 0
    fat_tag_ids = []

    if not df_herd.empty:
        excluded_statuses = ["Died", "Slaughtered", "Sold", "Zakate", "Donate"]
        if "status" in df_herd.columns:
            active_herd = df_herd[~df_herd["status"].isin(excluded_statuses)].copy()
        else:
            active_herd = df_herd.copy()

        fat_mask = (
            active_herd["category"]
            .astype(str)
            .str.lower()
            .str.contains("fattening", na=False)
        )
        gen_mask = ~fat_mask

        fat_head_count = int(fat_mask.sum())
        gen_head_count = int(gen_mask.sum())

        if "tag_id" in active_herd.columns:
            fat_tag_ids = active_herd[fat_mask]["tag_id"].tolist()
        elif "tag" in active_herd.columns:
            fat_tag_ids = active_herd[fat_mask]["tag"].tolist()

    # 2. Database-Aligned Mix Recipes per 100 kg
    mix_recipes = {
        "Fattening Mix": {
            "Corn": 14,
            "Wheat": 19,
            "Soybeans": 5,
            "Radda": 10,
            "Barseem Hegazy": 20,
            "Bean Hay": 32,
        },
        "General Herd Mix": {"Corn": 17, "Barseem Hegazy": 46, "Bean Hay": 37},
    }

    fat_recipe = mix_recipes[fat_mix_type]
    gen_recipe = mix_recipes[gen_mix_type]

    # 3. Consumption Calculations (Scaled by days_diff)
    total_fat_weight = 0.0
    if not df_weights.empty and fat_head_count > 0:
        w_col = next(
            (
                c
                for c in ["weight", "current_weight", "live_weight"]
                if c in df_weights.columns
            ),
            None,
        )
        t_col = next(
            (c for c in ["tag_id", "tag", "animal_id"] if c in df_weights.columns), None
        )
        d_col = next(
            (c for c in ["date", "log_date", "weigh_date"] if c in df_weights.columns),
            None,
        )

        if w_col and t_col and fat_tag_ids:
            fat_weights = df_weights[df_weights[t_col].isin(fat_tag_ids)].copy()
            if not fat_weights.empty:
                if d_col:
                    fat_weights[d_col] = pd.to_datetime(
                        fat_weights[d_col], errors="coerce"
                    )
                    latest_weights = (
                        fat_weights.sort_values(d_col).groupby(t_col).last()
                    )
                    total_fat_weight = float(latest_weights[w_col].sum())
                else:
                    total_fat_weight = float(
                        fat_weights.groupby(t_col)[w_col].last().sum()
                    )

    if total_fat_weight == 0.0:
        total_fat_weight = fat_head_count * 45.0

    fat_daily_total_all = total_fat_weight * 0.035
    fat_total_period = fat_daily_total_all * days_diff

    gen_total_period = gen_head_count * gen_daily_feed_per_head * days_diff

    fat_ing_totals = {k: fat_total_period * (v / 100.0) for k, v in fat_recipe.items()}
    gen_ing_totals = {k: gen_total_period * (v / 100.0) for k, v in gen_recipe.items()}

    # 4. Financial Calculations (GL 5010 - Filtered by Date Range vs Total)
    total_feed_spent_all = 0.0
    period_feed_spent = 0.0

    if not df_tx.empty:
        feed_tx = df_tx[df_tx["account_code"].astype(str) == "5010"].copy()
        total_feed_spent_all = float(feed_tx["amount"].sum())

        if "date" in feed_tx.columns:
            feed_tx["date"] = pd.to_datetime(feed_tx["date"], errors="coerce").dt.date
            period_tx = feed_tx[
                (feed_tx["date"] >= start_date) & (feed_tx["date"] <= end_date)
            ]
            period_feed_spent = float(period_tx["amount"].sum())
        else:
            period_feed_spent = total_feed_spent_all

    # --- COST EFFICIENCY CALCULATIONS ---
    total_bio_kg = fat_total_period + gen_total_period
    avg_cost_per_kg = (period_feed_spent / total_bio_kg) if total_bio_kg > 0 else 0.0

    avg_fat_per_head_day = (
        (fat_total_period / fat_head_count) / days_diff if fat_head_count > 0 else 0
    )
    fat_cost_per_head_day = avg_fat_per_head_day * avg_cost_per_kg
    gen_cost_per_head_day = gen_daily_feed_per_head * avg_cost_per_kg

    # --- UI DISPLAY ---
    st.markdown(f"### 📋 1. Head Count & Total Consumption Summary ({days_diff} Days)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fattening Head Count", f"{fat_head_count} head")
    c2.metric("General Herd Head Count", f"{gen_head_count} head")
    c3.metric("Fattening Total Feed (Bio)", f"{fat_total_period:,.1f} kg")
    c4.metric("General Herd Total Feed (Bio)", f"{gen_total_period:,.1f} kg")

    st.markdown("### 🐑 2. Average Fed Amount & Cost / Head / Day")
    avg_c1, avg_c2, avg_c3, avg_c4 = st.columns(4)
    avg_c1.metric("Fattening Avg Intake", f"{avg_fat_per_head_day:,.2f} kg / day")
    avg_c2.metric("Fattening Cost / Head", f"${fat_cost_per_head_day:,.2f} / day")
    avg_c3.metric("General Herd Avg Intake", f"{gen_daily_feed_per_head:,.2f} kg / day")
    avg_c4.metric("General Herd Cost / Head", f"${gen_cost_per_head_day:,.2f} / day")

    st.markdown("### 🔬 3. Detailed Ingredient-Level Standard Consumption")
    all_ingredients = sorted(
        list(set(list(fat_recipe.keys()) + list(gen_recipe.keys())))
    )

    data_rows = []
    for ing in all_ingredients:
        f_qty = fat_ing_totals.get(ing, 0.0)
        g_qty = gen_ing_totals.get(ing, 0.0)
        data_rows.append(
            {
                "Feed Ingredient": ing,
                "Fattening Mix (kg)": f_qty,
                "General Herd Mix (kg)": g_qty,
                "Total Biological Standard (kg)": f_qty + g_qty,
            }
        )

    df_report = pd.DataFrame(data_rows)
    st.dataframe(df_report, use_container_width=True)

    st.markdown("### ⚖️ 4. Financial & Ledger Discrepancy Audit")
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric(
        f"Total Biological Expected ({days_diff} Days)", f"{total_bio_kg:,.1f} kg"
    )
    col_b.metric("Avg Feed Cost / Kg", f"${avg_cost_per_kg:,.2f} / kg")
    col_c.metric(f"Period Feed Cost ({days_diff} Days)", f"${period_feed_spent:,.2f}")
    col_d.metric("Total Cumulative Purchases", f"${total_feed_spent_all:,.2f}")

    st.info(
        "💡 **Engineering Audit Insight:** This report contrasts your biological requirement over the selected "
        f"{days_diff} days ({total_bio_kg:,.1f} kg) against your period-filtered financial ledger expenses (${period_feed_spent:,.2f}), "
        f"yielding an average feed cost of ${avg_cost_per_kg:,.2f} per kg."
    )
