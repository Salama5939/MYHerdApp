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


def generate_valuation_report():
    print("🔌 Connecting to live Supabase database for Biological Asset Valuation...")
    conn = get_db_connection()

    try:
        # Pull live data directly from Supabase tables
        df_herd = pd.read_sql("SELECT * FROM herd;", conn)  # type: ignore
        df_births = pd.read_sql("SELECT * FROM birth_records;", conn)  # type: ignore
    finally:
        conn.close()

    # Process Demographics from live data
    demo_df = (
        df_herd.groupby(["category", "status"]).size().reset_index(name="headcount")
    )
    total_active = int(df_herd[df_herd["status"] == "Active/Healthy"].shape[0])
    total_offtake = int(
        df_herd[df_herd["status"].isin(["Slaughtered", "Sold", "Zakate"])].shape[0]
    )
    total_died = int(df_herd[df_herd["status"] == "Died"].shape[0])
    total_births_count = (
        int(df_births["lambs_count"].sum()) if not df_births.empty else 0
    )

    # PDF Generation Setup
    pdf_filename = "Report_4_Biological_Asset_Valuation.pdf"
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
            "Jalila's Farm - Strategic Report #4: Biological Asset Valuation & Flock Dynamics",
            title_style,
        ),
        Paragraph(
            "Live Supabase Database Analysis | Flock Census, Demographics, Reproductive Pipeline & Mortality Audit",
            subtitle_style,
        ),
        HRFlowable(
            width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=8
        ),
    ]

    # Executive Summary
    story.append(
        Paragraph("1. Executive Summary & Flock Census Overview", heading_style)
    )
    story.append(
        Paragraph(
            "This report monitors the structural dynamics of your live Supabase livestock inventory, ensuring compliance with biological asset accounting standards. "
            "It tracks herd movements—active breeding capital, growing replacements, births, and mortality leaks—to provide the Board with complete transparency "
            "into the farm's biological engine.",
            body_style,
        )
    )

    # KPI Summary Table
    kpi_data = [
        [
            Paragraph("Flock Demographic Indicator", table_header),
            Paragraph("Total Headcount / Count", table_header),
            Paragraph("Operational Significance", table_header),
        ],
        [
            Paragraph("Active / Healthy Inventory", table_cell),
            Paragraph(f"{total_active} head", table_cell),
            Paragraph(
                "Currently on-farm (breeding stock and active fattening pens).",
                table_cell,
            ),
        ],
        [
            Paragraph("Completed Off-Take (Slaughtered/Zakate)", table_cell),
            Paragraph(f"{total_offtake} head", table_cell),
            Paragraph("Successfully marketed or processed livestock.", table_cell),
        ],
        [
            Paragraph("Recorded Mortality (Died)", table_cell),
            Paragraph(f"{total_died} head", table_cell),
            Paragraph(
                "Historical losses tracked through live inventory audits.", table_cell
            ),
        ],
        [
            Paragraph("Total Recorded Birth Events", table_cell),
            Paragraph(
                f"{len(df_births)} events ({total_births_count} lambs)", table_cell
            ),
            Paragraph(
                "Internal reproduction output supporting replacement pipeline.",
                table_cell,
            ),
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

    # Detailed Demographics Table
    story.append(
        Paragraph("2. Detailed Flock Census & Status Breakdown", heading_style)
    )
    demo_data = [
        [
            Paragraph("Animal Category", table_header),
            Paragraph("Status", table_header),
            Paragraph("Headcount", table_header),
            Paragraph("Asset Classification", table_header),
        ]
    ]

    for _, row in demo_df.iterrows():
        classification = (
            "Commercial Finishing"
            if "fattening" in str(row["category"]).lower()
            else "Breeding Capital Asset"
        )
        demo_data.append(
            [
                Paragraph(str(row["category"]), table_cell_bold),
                Paragraph(str(row["status"]), table_cell),
                Paragraph(f"{row['headcount']}", table_cell),
                Paragraph(classification, table_cell),
            ]
        )

    t2 = Table(demo_data, colWidths=[140, 110, 80, 210])
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
        Paragraph("3. Strategic Biological Asset Recommendations", heading_style)
    )
    story.append(
        Paragraph(
            "• <b>Reproductive Pipeline Balance:</b> Maintain a healthy ratio of pregnant ewes and active breeding ewes to guarantee a steady supply of feeder lambs.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Mortality Control:</b> Monitor live mortality rates closely through Supabase inventory audits to maintain optimal biosecurity.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Financial Statement Valuation:</b> Ensure biological assets are properly valued on the balance sheet at fair value less estimated point-of-sale costs in accordance with live accounting data.",
            body_style,
        )
    )

    doc.build(story)
    print(f"✅ Successfully generated {pdf_filename} from live Supabase data!")


if __name__ == "__main__":
    generate_valuation_report()
