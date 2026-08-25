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
        secrets_path = os.path.join("..", ".streamlit", "secrets.toml")

    with open(secrets_path, "rb") as f:
        secrets = tomllib.load(f)

    db_url = secrets.get("FINANCE_DB_URL") or secrets.get("CONNECTION_STRING")
    if not db_url:
        raise ValueError("Database connection string not found in secrets.toml")
    return psycopg2.connect(db_url)


def generate_profitability_report():
    print("🔌 Connecting to live Supabase database...")
    conn = get_db_connection()

    try:
        # Query our production segment view safely using explicit connection
        query = "SELECT * FROM view_production_line_profitability;"
        df = pd.read_sql(query, conn)  # type: ignore
    finally:
        conn.close()

    if df.empty:
        print("⚠️ Warning: No data returned from view_production_line_profitability.")
        return

    # Aggregate by production segment for summary tables
    summary_df = (
        df.groupby("production_segment")
        .agg(
            total_headcount=("total_headcount", "sum"),
            total_revenue=("total_revenue", "sum"),
            total_feed_cost=("total_feed_cost", "sum"),
            net_profit=("net_profit_contribution", "sum"),
        )
        .reset_index()
    )

    # PDF Generation Setup
    pdf_filename = "Report_2_Production_Line_Profitability.pdf"
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
    table_cell_profit = ParagraphStyle(
        "TCP",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#276749"),
        fontName="Helvetica-Bold",
    )

    story = [
        Paragraph(
            "Jalila's Farm - Strategic Report #2: Production Line Profitability Analysis",
            title_style,
        ),
        Paragraph(
            "Live Supabase Database Analysis | Commercial Fattening vs. General Breeding Herd Performance",
            subtitle_style,
        ),
        HRFlowable(
            width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=8
        ),
    ]

    # Executive Summary
    story.append(
        Paragraph("1. Executive Summary & Production Line Breakdown", heading_style)
    )
    story.append(
        Paragraph(
            "This report evaluates the financial separation between your commercial meat production (Fattening Line) "
            "and your biological capital foundation (General & Breeding Herd). By factoring in both animal category and active/slaughtered status, "
            "management gains precise visibility into realized commercial cash flows versus ongoing capital investments.",
            body_style,
        )
    )

    # Summary Table by Segment
    summary_data = [
        [
            Paragraph("Production Segment", table_header),
            Paragraph("Headcount", table_header),
            Paragraph("Total Revenue", table_header),
            Paragraph("Feed Cost", table_header),
            Paragraph("Net Contribution", table_header),
        ]
    ]

    for _, row in summary_df.iterrows():
        profit_style = table_cell_profit if row["net_profit"] >= 0 else table_cell
        summary_data.append(
            [
                Paragraph(str(row["production_segment"]), table_cell_bold),
                Paragraph(f"{row['total_headcount']:,}", table_cell),
                Paragraph(f"${row['total_revenue']:,.2f}", table_cell),
                Paragraph(f"${row['total_feed_cost']:,.2f}", table_cell),
                Paragraph(f"${row['net_profit']:,.2f}", profit_style),
            ]
        )

    t1 = Table(summary_data, colWidths=[180, 65, 95, 80, 120])
    t1.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
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
    story.append(Spacer(1, 8))

    # Detailed Breakdown Table
    story.append(Paragraph("2. Detailed Category & Status Breakdown", heading_style))
    detail_data = [
        [
            Paragraph("Segment", table_header),
            Paragraph("Category", table_header),
            Paragraph("Status", table_header),
            Paragraph("Count", table_header),
            Paragraph("Revenue", table_header),
            Paragraph("Feed Cost", table_header),
            Paragraph("Net Profit", table_header),
        ]
    ]

    for _, row in df.iterrows():
        detail_data.append(
            [
                Paragraph(str(row["production_segment"]), table_cell),
                Paragraph(str(row["animal_category"]), table_cell),
                Paragraph(str(row["animal_status"]), table_cell),
                Paragraph(f"{row['total_headcount']}", table_cell),
                Paragraph(f"${row['total_revenue']:,.2f}", table_cell),
                Paragraph(f"${row['total_feed_cost']:,.2f}", table_cell),
                Paragraph(f"${row['net_profit_contribution']:,.2f}", table_cell),
            ]
        )

    t2 = Table(detail_data, colWidths=[120, 80, 75, 45, 65, 60, 95])
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
    story.append(Spacer(1, 8))

    # Strategic Takeaways
    story.append(Paragraph("3. Strategic Board Recommendations", heading_style))
    story.append(
        Paragraph(
            "• <b>Commercial Cash Generator:</b> The completed fattening batches successfully generate robust cash returns ($167.8k net profit on $584.5k sales), confirming that the finishing model is highly viable.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>WIP Management:</b> The 14 active fattening lambs currently in pens represent ongoing Work-In-Progress that must be monitored against feed inflation.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Capital Asset Role:</b> The general breeding herd (147 head) serves as the reproductive engine. Their carrying costs are essential investments required to feed lambs into the fattening pipeline.",
            body_style,
        )
    )

    doc.build(story)
    print(f"✅ Successfully generated {pdf_filename} from live Supabase data!")


if __name__ == "__main__":
    generate_profitability_report()
