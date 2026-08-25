import os
import tomllib
import time
from typing import cast
import pandas as pd
import psycopg2
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def get_db_connection():
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if not os.path.exists(secrets_path):
        secrets_path = os.path.join("..", ".streamlit", "secrets.toml")
    with open(secrets_path, "rb") as f:
        secrets = tomllib.load(f)
    db_url = secrets.get("FINANCE_DB_URL") or secrets.get("CONNECTION_STRING")
    if not db_url:
        raise ValueError("Database connection string not found in secrets.toml")
    return psycopg2.connect(db_url)


def run_all_reports():
    os.makedirs("reports", exist_ok=True)
    print("🚀 Starting Master Executive Report Generation Suite...")

    conn = get_db_connection()
    try:
        # 1. Breakeven & Restocking Report
        print("📄 Generating Report #1: Breakeven Purchase Price & Restocking...")
        df_recipes = pd.read_sql("SELECT * FROM feed_recipes;", conn) # type: ignore
        df_standards = pd.read_sql("SELECT * FROM feeding_standards;", conn) # type: ignore
        df_fat = pd.read_sql("SELECT * FROM view_fattening_performance;", conn) # type: ignore

        fat_mix_cost = float(
            cast(
                float,
                df_recipes.loc[
                    df_recipes["recipe_type"] == "Fattening",
                    "calculated_mix_cost_per_kg",
                ].values[0],
            )
        )
        fat_daily_ration = float(
            cast(
                float,
                df_standards.loc[
                    df_standards["category"] == "Fattening", "daily_ration_kg"
                ].values[0],
            )
        )
        daily_feed_cost = fat_mix_cost * fat_daily_ration
        avg_sale = float(df_fat[df_fat["total_sales"] > 0]["total_sales"].mean())

        scenarios = []
        for days in [90, 120, 150]:
            feed_cost_cycle = float(daily_feed_cost * days)
            max_p = float(avg_sale - feed_cost_cycle - 3000.0)
            scenarios.append(
                {
                    "days": f"{days} Days",
                    "cost": f"${feed_cost_cycle:,.2f}",
                    "max_p": f"${max_p:,.2f}",
                }
            )

        # Build Report 1 PDF
        doc = SimpleDocTemplate(
            "reports/Report_1_Breakeven_Restocking.pdf",
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        styles = getSampleStyleSheet()
        story = [
            Paragraph(
                "Jalila's Farm - Strategic Report #1: Breakeven Purchase Price & Restocking",
                styles["Heading1"],
            ),
            Spacer(1, 10),
        ]
        story.append(
            Paragraph(
                f"Average Market Sale Realization: ${avg_sale:,.2f} | Daily Feed Burn Rate: ${daily_feed_cost:.2f}/day",
                styles["Normal"],
            )
        )
        doc.build(story)

        # 2. Production Line Profitability Report
        print("📄 Generating Report #2: Production Line Profitability Analysis...")
        df_prod = pd.read_sql("SELECT * FROM view_production_line_profitability;", conn) # type: ignore
        doc = SimpleDocTemplate(
            "reports/Report_2_Production_Line_Profitability.pdf",
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        story = [
            Paragraph(
                "Jalila's Farm - Strategic Report #2: Production Line Profitability Analysis",
                styles["Heading1"],
            ),
            Spacer(1, 10),
        ]
        story.append(
            Paragraph(
                f"Total Segments Tracked: {len(df_prod)} categories/statuses analyzed live from Supabase.",
                styles["Normal"],
            )
        )
        doc.build(story)

        # 3. FCR & Cost-Per-Kg Report
        print("📄 Generating Report #3: Feed Conversion Ratio (FCR) Efficiency...")
        df_fcr = pd.read_sql("SELECT * FROM view_fcr_efficiency;", conn) # type: ignore
        doc = SimpleDocTemplate(
            "reports/Report_3_Feed_Conversion_Efficiency.pdf",
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        story = [
            Paragraph(
                "Jalila's Farm - Strategic Report #3: Feed Conversion Ratio (FCR) & Cost-Per-Kg",
                styles["Heading1"],
            ),
            Spacer(1, 10),
        ]
        story.append(
            Paragraph(
                f"Average FCR: {df_fcr['feed_conversion_ratio'].mean():.2f} kg feed / kg gain.",
                styles["Normal"],
            )
        )
        doc.build(story)

        # 4. Biological Asset Valuation Report
        print("📄 Generating Report #4: Biological Asset Valuation & Flock Dynamics...")
        df_herd = pd.read_sql("SELECT * FROM herd;", conn) # type: ignore
        df_births = pd.read_sql("SELECT * FROM birth_records;", conn) # type: ignore
        doc = SimpleDocTemplate(
            "reports/Report_4_Biological_Asset_Valuation.pdf",
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        story = [
            Paragraph(
                "Jalila's Farm - Strategic Report #4: Biological Asset Valuation & Flock Dynamics",
                styles["Heading1"],
            ),
            Spacer(1, 10),
        ]
        story.append(
            Paragraph(
                f"Total Active Headcount: {len(df_herd[df_herd['status']=='Active/Healthy'])} head.",
                styles["Normal"],
            )
        )
        doc.build(story)

        # 5. Reproductive & Mortality Audit Report
        print("📄 Generating Report #5: Reproductive & Mortality Dashboard...")
        doc = SimpleDocTemplate(
            "reports/Report_5_Reproductive_Mortality_Dashboard.pdf",
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        story = [
            Paragraph(
                "Jalila's Farm - Strategic Report #5: Reproductive & Mortality Leakage Dashboard",
                styles["Heading1"],
            ),
            Spacer(1, 10),
        ]
        story.append(
            Paragraph(
                f"Total Recorded Lambing Events: {len(df_births)} events.",
                styles["Normal"],
            )
        )
        doc.build(story)

        # 6. Off-Take Timing Calculator Report
        print("📄 Generating Report #6: Breakeven & Optimal Off-Take Timing...")
        df_timing = pd.read_sql("SELECT * FROM view_offtake_timing_optimization;", conn) # type: ignore
        doc = SimpleDocTemplate(
            "reports/Report_6_Offtake_Timing_Calculator.pdf",
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        story = [
            Paragraph(
                "Jalila's Farm - Strategic Report #6: Off-Take Timing Calculator",
                styles["Heading1"],
            ),
            Spacer(1, 10),
        ]
        story.append(
            Paragraph(
                f"Average Days on Feed: {df_timing['days_on_feed'].mean():.1f} days.",
                styles["Normal"],
            )
        )
        doc.build(story)

        print(
            "🎉 All 6 Strategic Reports successfully generated and archived in the 'reports/' folder!"
        )

    finally:
        conn.close()


if __name__ == "__main__":
    run_all_reports()
