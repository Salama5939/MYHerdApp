from datetime import datetime
import os
import tomllib
import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st
from typing import Tuple

# --- 1. Security, Language & Path ---
from translations import init_language_state, t, apply_rtl_styling

st.set_page_config(page_title="Feed Audit", page_icon="📊", layout="wide")

init_language_state()
apply_rtl_styling()

# --- 2. CSS Injection for Compact Metric Numbers ---
st.markdown(
    """
    <style>
        [data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
        }
    </style>
""",
    unsafe_allow_html=True,
)


# --- 3. Database Connection Helper ---
def get_db_connection():
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    with open(secrets_path, "rb") as f:
        secrets = tomllib.load(f)
    db_url = secrets.get("FINANCE_DB_URL") or secrets.get("CONNECTION_STRING")
    return psycopg2.connect(db_url)


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


# --- 4. UI Generation ---
st.title(t("feed_audit_title") or "📊 Biological Feed Variance & Audit Report")
st.markdown(
    t("feed_audit_desc")
    or "Comprehensive nutritional audit cross-checking recipes against actual expenses."
)

# --- SIDEBAR ---
st.sidebar.header(t("audit_params") or "📋 Audit Parameters")
start_date = st.sidebar.date_input(
    t("start_date") or "Start Date", value=datetime(2026, 1, 1)
)
end_date = st.sidebar.date_input(
    t("end_date") or "End Date", value=datetime.now().date()
)

days_diff = max(1, (end_date - start_date).days)
st.sidebar.info(
    f"{t('active_period') or '📅 Active Period'}: **{days_diff} {t('days') or 'days'}**"
)

st.sidebar.subheader(t("nutritional_mixes") or "Nutritional Mix Profiles")
fat_mix_type = st.sidebar.selectbox(
    t("fattening_mix") or "Fattening Mix", ["Fattening Mix"]
)
gen_mix_type = st.sidebar.selectbox(
    t("general_mix") or "General Herd Mix", ["General Herd Mix"]
)

fat_intake_pct = st.sidebar.slider(
    t("fat_intake_pct") or "Fattening Daily Intake (% Body Weight)", 2.0, 4.0, 3.0, 0.1
)
gen_daily_feed_per_head = st.sidebar.number_input(
    t("gen_intake_rate") or "General Herd Daily Intake (kg/head/day)",
    1.0,
    5.0,
    1.8,
    0.1,
)

if st.button(t("run_audit") or "Run Comprehensive Feed Audit", type="primary"):
    df_tx, df_weights, df_herd = fetch_audit_data()

    # 1. Corrected Dynamic Head Counts (Strictly positive counts)
    fat_head_count = 0
    gen_head_count = 0
    fat_tag_ids = []

    if not df_herd.empty:
        excluded = ["Died", "Slaughtered", "Sold", "Zakate", "Donate"]
        active = (
            df_herd[~df_herd["status"].isin(excluded)].copy()
            if "status" in df_herd.columns
            else df_herd.copy()
        )

        fat_mask = (
            active["category"]
            .astype(str)
            .str.lower()
            .str.contains("fattening", na=False)
        )
        gen_mask = ~fat_mask

        fat_head_count = int(fat_mask.sum())
        gen_head_count = int(gen_mask.sum())

        col_tag = next((c for c in ["tag_id", "tag"] if c in active.columns), None)
        if col_tag:
            fat_tag_ids = active[fat_mask][col_tag].tolist()

    # 2. Recipes
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

    fat_recipe, gen_recipe = mix_recipes[fat_mix_type], mix_recipes[gen_mix_type]

    # 3. Consumption Calculations
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

    fat_total_period = (total_fat_weight * (fat_intake_pct / 100.0)) * days_diff
    gen_total_period = gen_head_count * gen_daily_feed_per_head * days_diff

    fat_ing = {k: fat_total_period * (v / 100.0) for k, v in fat_recipe.items()}
    gen_ing = {k: gen_total_period * (v / 100.0) for k, v in gen_recipe.items()}

    # 4. Financial Calculations (GL 5010 Feed Filtered)
    period_feed_spent = 0.0
    total_spent_all = 0.0
    if not df_tx.empty:
        gl = df_tx[df_tx["account_code"].astype(str) == "5010"].copy()
        text_cols = [c for c in gl.columns if gl[c].dtype == object]
        feed_keywords = [
            "feed",
            "corn",
            "wheat",
            "soy",
            "bran",
            "radda",
            "barseem",
            "hay",
            "bean",
            "additive",
            "ذرة",
            "برسيم",
            "تبن",
            "صويا",
            "ردة",
            "علف",
        ]

        if text_cols:
            feed_mask = pd.Series(False, index=gl.index)
            for col in text_cols:
                feed_mask |= (
                    gl[col]
                    .astype(str)
                    .str.lower()
                    .str.contains("|".join(feed_keywords), na=False)
                )
            feed_tx = gl[feed_mask] if feed_mask.sum() > 0 else gl
        else:
            feed_tx = gl

        total_spent_all = float(feed_tx["amount"].sum())
        if "date" in feed_tx.columns:
            feed_tx["date"] = pd.to_datetime(feed_tx["date"], errors="coerce").dt.date
            period_feed_spent = float(
                feed_tx[
                    (feed_tx["date"] >= start_date) & (feed_tx["date"] <= end_date)
                ]["amount"].sum()
            )
        else:
            period_feed_spent = total_spent_all

    total_bio_kg = fat_total_period + gen_total_period
    avg_cost_kg = (period_feed_spent / total_bio_kg) if total_bio_kg > 0 else 0.0

    # --- UI DISPLAY ---
    st.markdown(
        f"### 📋 {t('summary_title') or 'Head Count & Total Consumption Summary'} ({days_diff} {t('days') or 'Days'})"
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        t("fattening_head_count") or "Fattening Head Count",
        f"{fat_head_count} {t('head') or 'head'}",
    )
    c2.metric(
        t("general_herd_head_count") or "General Herd Head Count",
        f"{gen_head_count} {t('head') or 'head'}",
    )
    c3.metric(
        t("fat_total_feed") or "Fattening Total Feed (Bio)",
        f"{fat_total_period:,.1f} kg",
    )
    c4.metric(
        t("gen_total_feed") or "General Herd Total Feed (Bio)",
        f"{gen_total_period:,.1f} kg",
    )

    st.markdown("---")
    st.markdown(
        f"### 🐑 {t('avg_intake_cost') or 'Average Fed Amount & Cost / Head / Day'}"
    )
    avg_c1, avg_c2, avg_c3, avg_c4 = st.columns(4)
    avg_fat_per_head_day = (
        (fat_total_period / fat_head_count) / days_diff if fat_head_count > 0 else 0
    )
    avg_c1.metric(
        t("fattening_intake") or "Fattening Avg Intake",
        f"{avg_fat_per_head_day:,.2f} kg",
    )
    avg_c2.metric(
        t("fattening_cost_head") or "Fattening Cost / Head",
        f"${(avg_fat_per_head_day * avg_cost_kg):,.2f}",
    )
    avg_c3.metric(
        t("general_intake") or "General Herd Avg Intake",
        f"{gen_daily_feed_per_head:,.2f} kg",
    )
    avg_c4.metric(
        t("general_cost_head") or "General Herd Cost / Head",
        f"${(gen_daily_feed_per_head * avg_cost_kg):,.2f}",
    )

    st.markdown("### 🔬 3. Detailed Ingredient Consumption")
    all_ingredients = sorted(
        list(set(list(fat_recipe.keys()) + list(gen_recipe.keys())))
    )
    df_report = pd.DataFrame(
        [
            {
                "Ingredient": ing,
                "Fattening (kg)": fat_ing.get(ing, 0.0),
                "General (kg)": gen_ing.get(ing, 0.0),
                "Total Standard (kg)": fat_ing.get(ing, 0.0) + gen_ing.get(ing, 0.0),
            }
            for ing in all_ingredients
        ]
    )
    st.dataframe(df_report, use_container_width=True)

    st.markdown("### 📈 4. Visual Comparison")
    fig = px.bar(
        df_report,
        x="Ingredient",
        y=["Fattening (kg)", "General (kg)"],
        barmode="stack",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### ⚖️ 5. Financial & Ledger Discrepancy Audit")
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Total Biological Expected", f"{total_bio_kg:,.1f} kg")
    col_b.metric("Avg Feed Cost / Kg", f"${avg_cost_kg:,.2f} / kg")
    col_c.metric("Period Feed Cost", f"${period_feed_spent:,.2f}")
    col_d.metric("Total Cumulative Purchases", f"${total_spent_all:,.2f}")
