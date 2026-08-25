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


def generate_fcr_report():
    print("🔌 Connecting to live Supabase database for FCR analysis...")
    conn = get_db_connection()

    try:
        # Query our FCR view from Supabase
        query = "SELECT * FROM view_fcr_efficiency;"
        df = pd.read_sql(query, conn)  # type: ignore
    finally:
        conn.close()

    if df.empty:
        print("⚠️ Warning: No data returned from view_fcr_efficiency.")
        return

    # Calculate overall summary statistics
    avg_fcr = float(df["feed_conversion_ratio"].mean())
    avg_cost_per_kg = float(df["cost_per_kg_gained"].mean())
    avg_weight_gain = float(df["total_weight_gain_kg"].mean())
    total_animals = len(df)

    # PDF Generation Setup
    pdf_filename = "Report_3_Feed_Conversion_Efficiency.pdf"
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
            "Jalila's Farm - Strategic Report #3: Feed Conversion Ratio (FCR) & Cost-Per-Kg Gained",
            title_style,
        ),
        Paragraph(
            "Live Supabase Database Analysis | Livestock Nutritional Efficiency & Finishing Performance",
            subtitle_style,
        ),
        HRFlowable(
            width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=8
        ),
    ]

    # Executive Summary
    story.append(Paragraph("1. Executive Summary & Efficiency KPIs", heading_style))
    story.append(
        Paragraph(
            "Feed Conversion Ratio (FCR) measures how efficiently fattening stock converts feed intake into live body weight. "
            "Because feed accounts for the majority of fattening expenses, tracking FCR and cost-per-kg gained ensures that finishing operations "
            "remain cost-effective and profitable.",
            body_style,
        )
    )

    # KPI Summary Table
    kpi_data = [
        [
            Paragraph("Metric Description", table_header),
            Paragraph("Benchmark / Average Value", table_header),
            Paragraph("Operational Implication", table_header),
        ],
        [
            Paragraph("Total Evaluated Fattening Head", table_cell),
            Paragraph(f"{total_animals} animals", table_cell),
            Paragraph("Sample size of completed finishing batches.", table_cell),
        ],
        [
            Paragraph("Average Total Weight Gain", table_cell),
            Paragraph(f"{avg_weight_gain:.2f} kg / head", table_cell),
            Paragraph(
                "Average net weight put on during the finishing cycle.", table_cell
            ),
        ],
        [
            Paragraph("Average Feed Conversion Ratio (FCR)", table_cell),
            Paragraph(f"{avg_fcr:.2f} kg feed / kg gain", table_cell),
            Paragraph(
                "Total feed consumed divided by total liveweight gained.", table_cell
            ),
        ],
        [
            Paragraph("Average Cost per Kg Gained", table_cell),
            Paragraph(f"${avg_cost_per_kg:,.2f} / kg gain", table_cell),
            Paragraph(
                "Direct feed cost incurred to produce 1 kg of live weight.", table_cell
            ),
        ],
    ]
    t1 = Table(kpi_data, colWidths=[150, 130, 260])
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

    # Animal Level Performance Table (Top 15 for brevity)
    story.append(
        Paragraph(
            "2. Sample Individual Animal Performance (Top Finished Stock)",
            heading_style,
        )
    )
    detail_data = [
        [
            Paragraph("Tag #", table_header),
            Paragraph("Status", table_header),
            Paragraph("Start Wt (kg)", table_header),
            Paragraph("End Wt (kg)", table_header),
            Paragraph("Gain (kg)", table_header),
            Paragraph("Feed Used (kg)", table_header),
            Paragraph("FCR", table_header),
            Paragraph("Cost / Kg ($)", table_header),
        ]
    ]

    for _, row in df.head(15).iterrows():
        detail_data.append(
            [
                Paragraph(str(row["tag_no"]), table_cell_bold),
                Paragraph(str(row["status"]), table_cell),
                Paragraph(f"{row['starting_weight']:.1f}", table_cell),
                Paragraph(f"{row['ending_weight']:.1f}", table_cell),
                Paragraph(f"{row['total_weight_gain_kg']:.1f}", table_cell),
                Paragraph(f"{row['total_feed_consumed_kg']:.1f}", table_cell),
                Paragraph(f"{row['feed_conversion_ratio']:.2f}", table_cell),
                Paragraph(f"${row['cost_per_kg_gained']:,.2f}", table_cell),
            ]
        )

    t2 = Table(detail_data, colWidths=[45, 75, 70, 70, 65, 80, 50, 85])
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
    story.append(Paragraph("3. Strategic Nutritional Recommendations", heading_style))
    story.append(
        Paragraph(
            "• <b>Monitor Outliers:</b> Animals with high FCR ratios indicate inefficient feed conversion or potential health bottlenecks that require veterinary checkups.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Ingredient Cost Impact:</b> With feed mix costs averaging $13.21/kg, managing daily ration distribution strictly according to `feeding_standards` protects profit margins.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Optimal End-Point Timing:</b> Sell animals promptly once they reach target market weight, as holding them past peak FCR efficiency increases feed costs without proportional weight gains.",
            body_style,
        )
    )

    doc.build(story)
    print(f"✅ Successfully generated {pdf_filename} from live Supabase data!")


if __name__ == "__main__":
    generate_fcr_report()
