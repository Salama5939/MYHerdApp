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


def fetch_data():
    conn = get_db_connection()
    try:
        df_tx = pd.read_sql("SELECT * FROM financial_transactions WHERE approved = 1", conn)  # type: ignore
        df_weights = pd.read_sql("SELECT * FROM weight_logs", conn)  # type: ignore
        df_herd = pd.read_sql("SELECT * FROM herd", conn)  # type: ignore
    finally:
        conn.close()
    return df_tx, df_weights, df_herd


def generate_pdf():
    pdf_filename = "Feed_Audit_Board_Report.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1A365D"),
        alignment=1,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4A5568"),
        alignment=1,
        spaceAfter=15,
    )
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=12,
        spaceAfter=6,
    )
    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#2D3748"),
    )
    header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.white,
        fontName="Helvetica-Bold",
    )

    story = []

    # Fetch Data & Set Audit Period (e.g., Jan 1, 2026 to Today)
    df_tx, df_weights, df_herd = fetch_data()
    start_date = datetime(2026, 1, 1).date()
    end_date = datetime.now().date()
    days_diff = max(1, (end_date - start_date).days)

    # Head Counts
    fat_head_count, gen_head_count = 0, 0
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
        fat_head_count = int(fat_mask.sum())
        gen_head_count = int((~fat_mask).sum())
        col_tag = next((c for c in ["tag_id", "tag"] if c in active.columns), None)
        if col_tag:
            fat_tag_ids = active[fat_mask][col_tag].tolist()

    # Recipes & Calculations
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
            fw = df_weights[df_weights[t_col].isin(fat_tag_ids)].copy()
            if not fw.empty:
                if d_col:
                    fw[d_col] = pd.to_datetime(fw[d_col], errors="coerce")
                    total_fat_weight = float(
                        fw.sort_values(d_col).groupby(t_col).last()[w_col].sum()
                    )
                else:
                    total_fat_weight = float(fw.groupby(t_col)[w_col].last().sum())

    if total_fat_weight == 0.0:
        total_fat_weight = fat_head_count * 45.0

    fat_total_period = (total_fat_weight * 0.03) * days_diff
    gen_daily_feed = 1.8
    gen_total_period = gen_head_count * gen_daily_feed * days_diff

    fat_ing = {
        k: fat_total_period * (v / 100.0)
        for k, v in mix_recipes["Fattening Mix"].items()
    }
    gen_ing = {
        k: gen_total_period * (v / 100.0)
        for k, v in mix_recipes["General Herd Mix"].items()
    }

    # Financials
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
        ]
        if text_cols:
            mask = pd.Series(False, index=gl.index)
            for col in text_cols:
                mask |= (
                    gl[col]
                    .astype(str)
                    .str.lower()
                    .str.contains("|".join(feed_keywords), na=False)
                )
            feed_tx = gl[mask] if mask.sum() > 0 else gl
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
    avg_fat_day = (
        (fat_total_period / fat_head_count) / days_diff if fat_head_count else 0
    )

    # --- BUILD PDF LAYOUT ---
    story.append(Paragraph("Jalila's Farm - Executive Board Report", title_style))
    story.append(
        Paragraph(
            f"Biological Feed Variance & Financial Audit | Period: {start_date} to {end_date} ({days_diff} Days)",
            subtitle_style,
        )
    )
    story.append(
        HRFlowable(
            width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=10
        )
    )

    # Summary Table
    story.append(
        Paragraph("1. Flock Population & Total Consumption Summary", section_style)
    )
    summary_data = [
        [
            Paragraph("Category", header_style),
            Paragraph("Head Count", header_style),
            Paragraph("Total Biological Feed", header_style),
            Paragraph("Avg Daily Intake / Head", header_style),
        ],
        [
            Paragraph("Fattening Flock", cell_style),
            Paragraph(str(fat_head_count), cell_style),
            Paragraph(f"{fat_total_period:,.1f} kg", cell_style),
            Paragraph(f"{avg_fat_day:.2f} kg / day", cell_style),
        ],
        [
            Paragraph("General Herd", cell_style),
            Paragraph(str(gen_head_count), cell_style),
            Paragraph(f"{gen_total_period:,.1f} kg", cell_style),
            Paragraph(f"{gen_daily_feed:.2f} kg / day", cell_style),
        ],
    ]
    t1 = Table(summary_data, colWidths=[130, 90, 140, 140])
    t1.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
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
    story.append(t1)
    story.append(Spacer(1, 10))

    # Ingredients Table
    story.append(
        Paragraph("2. Detailed Ingredient-Level Standard Consumption", section_style)
    )
    all_ingredients = sorted(
        list(
            set(
                list(mix_recipes["Fattening Mix"].keys())
                + list(mix_recipes["General Herd Mix"].keys())
            )
        )
    )
    ing_data = [
        [
            Paragraph("Feed Ingredient", header_style),
            Paragraph("Fattening Mix (kg)", header_style),
            Paragraph("General Herd Mix (kg)", header_style),
            Paragraph("Total Standard (kg)", header_style),
        ]
    ]

    for ing in all_ingredients:
        f_val = fat_ing.get(ing, 0.0)
        g_val = gen_ing.get(ing, 0.0)
        ing_data.append(
            [
                Paragraph(ing, cell_style),
                Paragraph(f"{f_val:,.1f}", cell_style),
                Paragraph(f"{g_val:,.1f}", cell_style),
                Paragraph(f"{f_val + g_val:,.1f}", cell_style),
            ]
        )

    t2 = Table(ing_data, colWidths=[150, 110, 110, 130])
    t2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
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
    story.append(t2)
    story.append(Spacer(1, 10))

    # Financial Ledger Audit Table
    story.append(
        Paragraph(
            "3. Financial Ledger & Cost Efficiency Audit (GL 5010)", section_style
        )
    )
    fin_data = [
        [
            Paragraph("Metric Description", header_style),
            Paragraph("Audited Value", header_style),
        ],
        [
            Paragraph("Total Biological Expected Consumption", cell_style),
            Paragraph(f"{total_bio_kg:,.1f} kg", cell_style),
        ],
        [
            Paragraph("Average Feed Cost per Kg", cell_style),
            Paragraph(f"${avg_cost_kg:,.2f} / kg", cell_style),
        ],
        [
            Paragraph(f"Period Feed Cost ({days_diff} Days)", cell_style),
            Paragraph(f"${period_feed_spent:,.2f}", cell_style),
        ],
        [
            Paragraph("Total Cumulative Purchases (All-Time)", cell_style),
            Paragraph(f"${total_spent_all:,.2f}", cell_style),
        ],
        [
            Paragraph("Fattening Daily Cost / Head", cell_style),
            Paragraph(f"${avg_fat_day * avg_cost_kg:,.2f} / day", cell_style),
        ],
        [
            Paragraph("General Herd Daily Cost / Head", cell_style),
            Paragraph(f"${gen_daily_feed * avg_cost_kg:,.2f} / day", cell_style),
        ],
    ]
    t3 = Table(fin_data, colWidths=[250, 250])
    t3.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
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
    story.append(t3)

    # Build PDF document
    doc.build(story)
    print(f"Successfully generated {pdf_filename}!")


if __name__ == "__main__":
    generate_pdf()
