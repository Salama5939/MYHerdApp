from datetime import datetime
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
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    with open(secrets_path, "rb") as f:
        secrets = tomllib.load(f)
    db_url = secrets.get("FINANCE_DB_URL") or secrets.get("CONNECTION_STRING")
    return psycopg2.connect(db_url)


def generate_checklist_files():
    conn = get_db_connection()
    try:
        df_herd = pd.read_sql("SELECT * FROM herd", conn)  # type: ignore
        df_weights = pd.read_sql("SELECT * FROM weight_logs", conn)  # type: ignore
    finally:
        conn.close()

    # 1. Gather missing purchase price tags
    missing_purchase = df_herd[
        (df_herd["purchase_price"].isna()) | (df_herd["purchase_price"] == 0)
    ]["tag_no"].tolist()

    # 2. Gather missing offtake records
    offtake_animals = df_herd[
        df_herd["status"].isin(["Slaughtered", "Sold", "Died", "Zakate"])
    ]
    missing_sale_info = offtake_animals[
        (offtake_animals["sale_price"].isna())
        | (offtake_animals["sale_price"] == 0)
        | (offtake_animals["sale_date"].isna())
    ]

    # 3. Gather weight logs with missing feed cost
    missing_feed_cost = df_weights[
        (df_weights["feed_cost"].isna()) | (df_weights["feed_cost"] == 0)
    ][["id", "tag_no", "weigh_date"]].to_dict(orient="records")

    checklist_rows = []
    for tag in missing_purchase:
        checklist_rows.append(
            {
                "Category": "Herd Purchase Price",
                "Identifier": f"Tag #{tag}",
                "Details": "Missing/Zero Purchase Price",
                "Status": "[  ] Pending",
            }
        )

    for idx, row in missing_sale_info.iterrows():
        checklist_rows.append(
            {
                "Category": "Off-Take Sale Info",
                "Identifier": f"Tag #{row['tag_no']}",
                "Details": f"Status: {row['status']} (Missing Sale Price/Date)",
                "Status": "[  ] Pending",
            }
        )

    for item in missing_feed_cost:
        checklist_rows.append(
            {
                "Category": "Weight Log Feed Cost",
                "Identifier": f"Log ID {item['id']} (Tag #{item['tag_no']})",
                "Details": f"Weigh Date: {str(item['weigh_date'])[:10]} (Missing Feed Cost)",
                "Status": "[  ] Pending",
            }
        )

    df_checklist = pd.DataFrame(checklist_rows)
    df_checklist.to_csv("Farm_Data_Cleanup_Checklist.csv", index=False)

    # Build PDF
    pdf_filename = "Farm_Data_Cleanup_Checklist.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=12,
    )
    header_style = ParagraphStyle(
        "HHead",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.white,
        fontName="Helvetica-Bold",
    )
    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=colors.HexColor("#2D3748"),
    )

    story = [
        Paragraph("Jalila's Farm - Data Cleanup & Verification Checklist", title_style),
        Paragraph(
            "Checklist of missing purchase prices, off-take records, and weight log feed costs.",
            subtitle_style,
        ),
        HRFlowable(
            width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=10
        ),
    ]

    table_data = [
        [
            Paragraph("Task Category", header_style),
            Paragraph("Target Item / Identifier", header_style),
            Paragraph("Issue Details", header_style),
            Paragraph("Done", header_style),
        ]
    ]
    for row in checklist_rows:
        table_data.append(
            [
                Paragraph(row["Category"], cell_style),
                Paragraph(row["Identifier"], cell_style),
                Paragraph(row["Details"], cell_style),
                Paragraph(row["Status"], cell_style),
            ]
        )

    t = Table(table_data, colWidths=[120, 130, 200, 50])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F7FAFC")],
                ),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ]
        )
    )

    story.append(t)
    doc.build(story)
    print("Checklist PDF and CSV successfully generated!")


if __name__ == "__main__":
    generate_checklist_files()
