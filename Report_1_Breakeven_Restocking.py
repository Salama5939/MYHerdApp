import os
import tomllib
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
    """Connects directly to your live Supabase database using Streamlit secrets."""
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if not os.path.exists(secrets_path):
        # Fallback path if running from a subfolder
        secrets_path = os.path.join("..", ".streamlit", "secrets.toml")

    with open(secrets_path, "rb") as f:
        secrets = tomllib.load(f)

    db_url = secrets.get("FINANCE_DB_URL") or secrets.get("CONNECTION_STRING")
    return psycopg2.connect(db_url)


def generate_breakeven_report():
    print("🔌 Connecting to live Supabase database...")
    conn = get_db_connection()

    try:
        # Fetch live data directly from Supabase tables and views
        # pandas accepts DB-API connections at runtime; the psycopg2 connection
        # type is not included in pandas' static ``read_sql`` annotations.
        df_recipes = pd.read_sql("SELECT * FROM feed_recipes;", conn)  # type: ignore[arg-type]
        df_standards = pd.read_sql("SELECT * FROM feeding_standards;", conn)  # type: ignore[arg-type]
        df_fat = pd.read_sql("SELECT * FROM view_fattening_performance;", conn)  # type: ignore[arg-type]
    finally:
        conn.close()

    # Calculations (using dynamic live data)
    fat_mix_row = df_recipes.loc[
        df_recipes["recipe_type"] == "Fattening", "calculated_mix_cost_per_kg"
    ]
    fat_mix_cost = float(str(fat_mix_row.values[0])) if not fat_mix_row.empty else 0.0

    fat_std_row = df_standards.loc[
        df_standards["category"] == "Fattening", "daily_ration_kg"
    ]
    fat_daily_ration = (
        float(str(fat_std_row.values[0])) if not fat_std_row.empty else 0.0
    )

    daily_feed_cost = fat_mix_cost * fat_daily_ration

    valid_fat = df_fat[df_fat["total_sales"] > 0]
    avg_sale = float(valid_fat["total_sales"].mean()) if not valid_fat.empty else 0.0

    # Restocking Scenarios
    scenarios = []
    for days in [90, 120, 150]:
        feed_cost_cycle = float(daily_feed_cost * days)
        target_profit = 3000.0  # Target net profit per head
        max_purchase_price = float(avg_sale - feed_cost_cycle - target_profit)
        scenarios.append(
            {
                "Cycle Days": f"{days} Days",
                "Total Feed Cost": f"${feed_cost_cycle:,.2f}",
                "Target Profit": f"${target_profit:,.2f}",
                "Max Purchase Price": f"${max_purchase_price:,.2f}",
            }
        )

    # PDF Generation
    pdf_filename = "Report_1_Breakeven_Restocking.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=15,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=10,
    )
    heading_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#2B6CB0"),
        spaceAfter=6,
        spaceBefore=10,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=colors.HexColor("#2D3748"),
        leading=11,
        spaceAfter=6,
    )
    table_header = ParagraphStyle(
        "TH",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=colors.white,
        fontName="Helvetica-Bold",
    )
    table_cell = ParagraphStyle(
        "TC", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#2D3748")
    )
    table_cell_bold = ParagraphStyle(
        "TCB",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#1A365D"),
        fontName="Helvetica-Bold",
    )

    story = [
        Paragraph(
            "Jalila's Farm - Strategic Report #1: Breakeven Purchase Price & Restocking Schedule",
            title_style,
        ),
        Paragraph(
            "Live Supabase Data Analysis | Fattening Economics, Feed Cost Structure, and External Restocking Thresholds",
            subtitle_style,
        ),
        HRFlowable(
            width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=8
        ),
    ]

    story.append(Paragraph("1. Executive Summary & Strategic Rationale", heading_style))
    story.append(
        Paragraph(
            "To prevent fattening pens from sitting empty while waiting for internal flock reproduction (which requires an 8-month gestation and weaning cycle), "
            "commercial farm management relies on a hybrid model combining internal breeding with targeted external feeder lamb acquisitions. "
            "This report pulls live data from your Supabase database to establish financial guardrails—specifically feed costs, daily ration economics, and maximum allowable purchase prices—to "
            "ensure that every external restocking batch delivers a guaranteed net profit margin.",
            body_style,
        )
    )

    story.append(
        Paragraph(
            "2. Current Fattening Feed Cost Structure (Live Database)", heading_style
        )
    )
    cost_data = [
        [
            Paragraph("Parameter", table_header),
            Paragraph("Value", table_header),
            Paragraph("Operational Impact", table_header),
        ],
        [
            Paragraph("Fattening Feed Mix Cost", table_cell),
            Paragraph(f"${fat_mix_cost:.3f} / kg", table_cell),
            Paragraph("Pulled live from Supabase `feed_recipes` table.", table_cell),
        ],
        [
            Paragraph("Daily Ration Target", table_cell),
            Paragraph(f"{fat_daily_ration} kg / head / day", table_cell),
            Paragraph(
                "Pulled live from Supabase `feeding_standards` table.", table_cell
            ),
        ],
        [
            Paragraph("Daily Feed Cost per Head", table_cell),
            Paragraph(f"${daily_feed_cost:.2f} / day", table_cell),
            Paragraph(
                "Direct daily operational burn rate per animal in pen.", table_cell
            ),
        ],
        [
            Paragraph("Historical Avg Market Sale", table_cell),
            Paragraph(f"${avg_sale:,.2f}", table_cell),
            Paragraph(
                "Pulled live from Supabase `view_fattening_performance` view.",
                table_cell,
            ),
        ],
    ]
    t1 = Table(cost_data, colWidths=[140, 110, 290])
    t1.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F7FAFC")],
                ),
            ]
        )
    )
    story.append(t1)
    story.append(Spacer(1, 6))

    story.append(
        Paragraph("3. Restocking Breakeven Purchase Price Scenarios", heading_style)
    )
    story.append(
        Paragraph(
            "When purchasing external feeder lambs, the <b>Maximum Allowable Purchase Price</b> is calculated as: "
            "<i>Expected Market Sale Price minus Total Cycle Feed Cost minus Target Net Profit ($3,000)</i>.",
            body_style,
        )
    )

    scen_data = [
        [
            Paragraph("Cycle Duration", table_header),
            Paragraph("Total Feed Cost", table_header),
            Paragraph("Target Net Profit", table_header),
            Paragraph("Max Allowable Purchase Price", table_header),
        ]
    ]
    for s in scenarios:
        scen_data.append(
            [
                Paragraph(s["Cycle Days"], table_cell),
                Paragraph(s["Total Feed Cost"], table_cell),
                Paragraph(s["Target Profit"], table_cell),
                Paragraph(s["Max Purchase Price"], table_cell_bold),
            ]
        )

    t2 = Table(scen_data, colWidths=[110, 120, 120, 190])
    t2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F7FAFC")],
                ),
            ]
        )
    )
    story.append(t2)
    story.append(Spacer(1, 6))

    story.append(Paragraph("4. Strategic Restocking Recommendations", heading_style))
    story.append(
        Paragraph(
            "• <b>Maintain 85% Pen Utilization:</b> Do not let pens sit empty. Time external purchases to coincide with post-weaning seasonal price dips in the local livestock market.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Strict Cost Ceiling:</b> Never pay more than the calculated Max Purchase Price for feeder lambs, factoring in live feed ingredient costs from Supabase.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Inventory Alignment:</b> Before bringing in new feeder batches, verify your warehouse inventory levels in Supabase.",
            body_style,
        )
    )

    doc.build(story)
    print(f"✅ Successfully generated {pdf_filename} from live Supabase data!")


if __name__ == "__main__":
    generate_breakeven_report()
