import os
import tomllib
import time
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


def generate_timing_report():
    print("🔌 Connecting to live Supabase database for Off-Take Timing Optimization...")
    conn = get_db_connection()

    try:
        query = "SELECT * FROM view_offtake_timing_optimization;"
        df = pd.read_sql(query, conn)  # type: ignore
    finally:
        conn.close()

    if df.empty:
        print("⚠️ Warning: No data returned from view_offtake_timing_optimization.")
        return

    # Calculations
    avg_days = float(df["days_on_feed"].mean())
    avg_adg = float(df["adg_grams_per_day"].mean())
    avg_gain = float(df["total_gain_kg"].mean())
    avg_cost_gain = float(df["feed_cost_per_kg_gain"].mean())

    # PDF Generation Setup with File Lock Handling
    base_filename = "Report_6_Offtake_Timing_Calculator.pdf"
    pdf_filename = base_filename

    # Try saving; if file is locked by a PDF viewer, append timestamp
    try:
        with open(pdf_filename, "ab"):
            pass
    except PermissionError:
        timestamp = int(time.time())
        pdf_filename = f"Report_6_Offtake_Timing_Calculator_{timestamp}.pdf"
        print(
            f"⚠️ Warning: '{base_filename}' is currently open. Saving as '{pdf_filename}' instead."
        )

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
            "Jalila's Farm - Strategic Report #6: Breakeven & Optimal Off-Take Timing Calculator",
            title_style,
        ),
        Paragraph(
            "Live Supabase Database Analysis | Complete Flock Growth Velocity, Days on Feed & Optimal Market Selling Window",
            subtitle_style,
        ),
        HRFlowable(
            width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=8
        ),
    ]

    # Executive Summary
    story.append(
        Paragraph("1. Executive Summary & Growth Velocity KPIs", heading_style)
    )
    story.append(
        Paragraph(
            "Identifying the optimal off-take timing prevents animals from being held past their peak biological growth efficiency. "
            "Once daily weight gain velocity slows down while daily feed costs remain fixed, holding animals further erodes net profit margins.",
            body_style,
        )
    )

    # KPI Summary Table
    kpi_data = [
        [
            Paragraph("Performance Indicator", table_header),
            Paragraph("Average Benchmark Value", table_header),
            Paragraph("Operational Interpretation", table_header),
        ],
        [
            Paragraph("Average Days on Feed (DOF)", table_cell),
            Paragraph(f"{avg_days:.1f} days", table_cell),
            Paragraph(
                "Typical duration from initial feeder entry to market off-take.",
                table_cell,
            ),
        ],
        [
            Paragraph("Average Daily Gain (ADG)", table_cell),
            Paragraph(f"{avg_adg:.1f} grams / day", table_cell),
            Paragraph("Average daily liveweight accumulation velocity.", table_cell),
        ],
        [
            Paragraph("Average Total Weight Gain", table_cell),
            Paragraph(f"{avg_gain:.1f} kg / head", table_cell),
            Paragraph("Net weight added during the finishing cycle.", table_cell),
        ],
        [
            Paragraph("Average Feed Cost per Kg Gained", table_cell),
            Paragraph(f"${avg_cost_gain:,.2f} / kg", table_cell),
            Paragraph("Direct feed expenditure required per kg of growth.", table_cell),
        ],
    ]
    t1 = Table(kpi_data, colWidths=[170, 130, 240])
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

    # Detailed Complete Table (All Records)
    story.append(
        Paragraph(
            "2. Complete Finishing Batch Velocity Breakdown (All Stock Records)",
            heading_style,
        )
    )
    detail_data = [
        [
            Paragraph("Tag #", table_header),
            Paragraph("Status", table_header),
            Paragraph("DOF", table_header),
            Paragraph("Start Wt", table_header),
            Paragraph("End Wt", table_header),
            Paragraph("Gain", table_header),
            Paragraph("ADG (g/day)", table_header),
            Paragraph("Cost/Kg ($)", table_header),
        ]
    ]

    for _, row in df.iterrows():
        detail_data.append(
            [
                Paragraph(str(row["tag_no"]), table_cell_bold),
                Paragraph(str(row["status"]), table_cell),
                Paragraph(f"{row['days_on_feed']}", table_cell),
                Paragraph(f"{row['start_weight']:.1f}", table_cell),
                Paragraph(f"{row['end_weight']:.1f}", table_cell),
                Paragraph(f"{row['total_gain_kg']:.1f}", table_cell),
                Paragraph(f"{row['adg_grams_per_day']:.1f}", table_cell),
                Paragraph(f"${row['feed_cost_per_kg_gain']:,.2f}", table_cell),
            ]
        )

    t2 = Table(detail_data, colWidths=[45, 75, 45, 65, 65, 55, 75, 85], repeatRows=1)
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
    story.append(
        Paragraph("3. Strategic Off-Take Timing Recommendations", heading_style)
    )
    story.append(
        Paragraph(
            "• <b>Target Finishing Window:</b> Optimal market off-take occurs around 90 to 110 days on feed when finishing lambs reach peak muscle maturity before daily feed conversion efficiency flattens.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Avoid Diminishing Returns:</b> Holding animals past 120+ days increases total feed burn without generating proportional market value gains.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Market Synchronization:</b> Coordinate batch slaughter dates with high-demand market pricing windows to maximize total net margin per head.",
            body_style,
        )
    )

    doc.build(story)
    print(
        f"✅ Successfully generated complete multi-page PDF as '{pdf_filename}' from live Supabase data!"
    )


if __name__ == "__main__":
    generate_timing_report()
