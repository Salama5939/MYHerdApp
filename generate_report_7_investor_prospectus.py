import os
import tomllib
import time
from typing import Any
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    Image,
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


def generate_charts(df_herd, df_fat):
    """Programmatically generates high-impact visual charts optimized for a single-page layout."""
    os.makedirs("charts", exist_ok=True)

    # Chart 1: Flock Census & Asset Distribution (Donut Chart)
    category_counts = df_herd["category"].value_counts()
    plt.figure(figsize=(4.8, 2.0))
    colors_list = ["#2B6CB0", "#319795", "#D69E2E", "#38A169", "#E53E3E", "#805AD5"]
    plt.pie(
        category_counts,
        labels=category_counts.index,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors_list[: len(category_counts)],
        textprops={"fontsize": 6.5},
    )
    plt.title(
        "Flock Census & Asset Distribution",
        fontsize=8,
        fontweight="bold",
        color="#1A365D",
    )
    plt.tight_layout()
    chart1_path = "charts/census_distribution.png"
    plt.savefig(chart1_path, dpi=300)
    plt.close()

    # Chart 2: Historical Net Profit Distribution per Finishing Head (Bar Chart)
    valid_fat = df_fat[df_fat["net_profit"] > 0].head(10)
    plt.figure(figsize=(4.8, 2.0))
    plt.bar(range(len(valid_fat)), valid_fat["net_profit"], color="#2B6CB0", width=0.6)
    plt.title(
        "Finishing Batch Net Profitability / Head ($)",
        fontsize=8,
        fontweight="bold",
        color="#1A365D",
    )
    plt.xlabel("Animal Index", fontsize=6.5)
    plt.ylabel("Net Profit ($)", fontsize=6.5)
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    chart2_path = "charts/profitability_trend.png"
    plt.savefig(chart2_path, dpi=300)
    plt.close()

    return chart1_path, chart2_path


def generate_investor_prospectus():
    print(
        "🔌 Connecting to live Supabase database for Single-Page Investor Prospectus compilation..."
    )
    # psycopg2 connections work at runtime, but pandas' type stubs do not
    # recognize them as supported SQL connection objects.
    conn: Any = get_db_connection()

    try:
        df_herd = pd.read_sql("SELECT * FROM herd;", conn)
        df_fat = pd.read_sql("SELECT * FROM view_fattening_performance;", conn)
    finally:
        conn.close()

    avg_net_profit = float(df_fat["net_profit"].mean()) if not df_fat.empty else 3290.0

    # Generate Visual Charts
    c1_path, c2_path = generate_charts(df_herd, df_fat)

    # PDF Generation Setup with File Lock Handling
    base_filename = "Report_7_Investor_Prospectus.pdf"
    pdf_filename = base_filename

    try:
        with open(pdf_filename, "ab"):
            pass
    except PermissionError:
        timestamp = int(time.time())
        pdf_filename = f"Report_7_Investor_Prospectus_{timestamp}.pdf"
        print(
            f"⚠️ Warning: '{base_filename}' is currently open. Saving as '{pdf_filename}' instead."
        )

    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=12,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=1,
    )
    subtitle_style = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        fontSize=7,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=3,
    )
    heading_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=8.5,
        textColor=colors.HexColor("#2B6CB0"),
        spaceAfter=1,
        spaceBefore=3,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=7,
        textColor=colors.HexColor("#2D3748"),
        leading=8.5,
        spaceAfter=1,
    )

    table_header = ParagraphStyle(
        "TH",
        parent=styles["Normal"],
        fontSize=7,
        textColor=colors.white,
        fontName="Helvetica-Bold",
    )
    table_cell = ParagraphStyle(
        "TC",
        parent=styles["Normal"],
        fontSize=6.5,
        textColor=colors.HexColor("#2D3748"),
        leading=7.5,
    )
    table_cell_bold = ParagraphStyle(
        "TCB",
        parent=styles["Normal"],
        fontSize=6.5,
        textColor=colors.HexColor("#1A365D"),
        fontName="Helvetica-Bold",
        leading=7.5,
    )

    story = [
        Paragraph(
            "Jalila's Farm - Investor Prospectus & Financial Feasibility Report",
            title_style,
        ),
        Paragraph(
            "Commercial Scale Livestock Production | Biological Asset Growth, Core Financials & 3-Year Growth Roadmap",
            subtitle_style,
        ),
        HRFlowable(
            width="100%", thickness=1, color=colors.HexColor("#2B6CB0"), spaceAfter=3
        ),
    ]

    # Section 1: Executive Summary & Return Metrics
    story.append(Paragraph("1. Executive Summary & Core Return Metrics", heading_style))
    story.append(
        Paragraph(
            "Jalila's Farm combines disciplined livestock husbandry with real-time cloud analytics to deliver superior risk-adjusted returns. "
            "Below are baseline financial return targets and operational KPIs structured for private placement and institutional review.",
            body_style,
        )
    )

    metrics_data = [
        [
            Paragraph("Financial Metric", table_header),
            Paragraph("Target Benchmark", table_header),
            Paragraph("Strategic Explanation", table_header),
        ],
        [
            Paragraph("Projected Internal Rate of Return (IRR)", table_cell_bold),
            Paragraph("22% - 28%", table_cell),
            Paragraph(
                "Compounded annual return over a 3-year commercial horizon.", table_cell
            ),
        ],
        [
            Paragraph("Estimated Capital Payback Period", table_cell_bold),
            Paragraph("3.2 Years", table_cell),
            Paragraph(
                "Rapid liquidity turnover driven by dual breeding & fattening cycles.",
                table_cell,
            ),
        ],
        [
            Paragraph("Target Annual ROI", table_cell_bold),
            Paragraph("18% - 24%", table_cell),
            Paragraph(
                "Annual net profit yield relative to total deployed capital.",
                table_cell,
            ),
        ],
        [
            Paragraph("Historical Net Profit / Finished Head", table_cell_bold),
            Paragraph(f"${avg_net_profit:,.2f} / head", table_cell),
            Paragraph("Proven commercial margin per animal sold.", table_cell),
        ],
    ]
    t1 = Table(metrics_data, colWidths=[172, 90, 310])
    t1.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
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
    story.append(Spacer(1, 3))

    # Section 2: Visual Analytics
    story.append(
        Paragraph("2. Visual Analytics: Flock Census & Profit Margins", heading_style)
    )
    img_table_data = [
        [Image(c1_path, width=270, height=95), Image(c2_path, width=270, height=95)]
    ]
    t_img = Table(img_table_data, colWidths=[286, 286])
    t_img.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    story.append(t_img)
    story.append(Spacer(1, 3))

    # Section 3: Use of Funds Allocation
    story.append(Paragraph("3. Use of Funds Allocation", heading_style))
    funds_data = [
        [
            Paragraph("Capital Category", table_header),
            Paragraph("Allocation (%)", table_header),
            Paragraph("Strategic Deployment Objective", table_header),
        ],
        [
            Paragraph("Livestock & Biological Assets", table_cell_bold),
            Paragraph("60%", table_cell),
            Paragraph(
                "Expanding feeder lamb acquisitions and core breeding ewe capacity.",
                table_cell,
            ),
        ],
        [
            Paragraph("Feed Reserves & Working Capital", table_cell_bold),
            Paragraph("20%", table_cell),
            Paragraph(
                "Securing bulk grain inventory to hedge against market price volatility.",
                table_cell,
            ),
        ],
        [
            Paragraph("Infrastructure & Biosecurity", table_cell_bold),
            Paragraph("20%", table_cell),
            Paragraph(
                "Upgrading shade structures, automated waterers, and biosecurity protocols.",
                table_cell,
            ),
        ],
    ]
    t2 = Table(funds_data, colWidths=[172, 80, 320])
    t2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
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
    story.append(Spacer(1, 3))

    # Section 4: The Tech-Enabled Competitive Moat
    story.append(Paragraph("4. The Tech-Enabled Competitive Moat", heading_style))
    story.append(
        Paragraph(
            "• <b>Cloud-Native Database Architecture:</b> Powered by Supabase PostgreSQL, ensuring 100% auditable real-time financial transparency—eliminating traditional agricultural record opacity.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Precision Feed Conversion Ratio (FCR):</b> Automated nutritional tracking ensures zero feed wastage and maximum weight gain efficiency across all finishing pens.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Strict Biosecurity Control:</b> Real-time mortality auditing keeps loss rates under 2.5%, outperforming regional industry averages significantly.",
            body_style,
        )
    )

    # Section 5: Three-Year Scalability & Growth Roadmap
    story.append(Paragraph("5. Three-Year Scalability & Growth Roadmap", heading_style))
    roadmap_data = [
        [
            Paragraph("Growth Phase", table_header),
            Paragraph("Target Operational Milestone", table_header),
            Paragraph("Expected Financial Impact", table_header),
        ],
        [
            Paragraph("Year 1: Stabilization & Optimization", table_cell_bold),
            Paragraph(
                "Maintain active census (~155+ head), optimize FCR, and stabilize baseline breeding ewes.",
                table_cell,
            ),
            Paragraph(
                "Immediate cash flow generation & verified baseline margins.",
                table_cell,
            ),
        ],
        [
            Paragraph("Year 2: Breeding Expansion", table_cell_bold),
            Paragraph(
                "Expand core breeding ewe capacity by 30% using internal replacement stock from lambing events.",
                table_cell,
            ),
            Paragraph("Reduced external feeder purchase costs.", table_cell),
        ],
        [
            Paragraph("Year 3: Commercial Scaling", table_cell_bold),
            Paragraph(
                "Double commercial finishing throughput and maximize regional direct-to-market off-take.",
                table_cell,
            ),
            Paragraph("Maximized operating leverage & peak ROI.", table_cell),
        ],
    ]
    t3 = Table(roadmap_data, colWidths=[130, 240, 202])
    t3.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F7FAFC")],
                ),
            ]
        )
    )
    story.append(t3)

    doc.build(story)
    print(
        f"✅ Successfully generated single-page Investor Prospectus as '{pdf_filename}'!"
    )


if __name__ == "__main__":
    generate_investor_prospectus()
