import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# CONFIGURATION & CONNECTION SETTINGS
# ==========================================
DB_URL = os.getenv(
    "SUPABASE_DB_URL",
    "postgresql://postgres.gvsocmhaarkierzeprgw:zQyOU7vfN4t21Z60@aws-1-eu-west-2.pooler.supabase.com:6543/postgres",
)

PDF_FILENAME = "comprehensive_detailed_audit_report.pdf"
RECEIVED_CSV = "detailed_inventory_received.csv"
CONSUMPTION_CSV = "detailed_livestock_consumption.csv"
GENERAL_HERD_CSV = "general_herd_consumption_summary.csv"


def get_db_engine():
    """Create and return a SQLAlchemy engine connected to live Supabase."""
    return create_engine(DB_URL)


def fetch_all_data():
    """Fetch raw transaction, master, and financial tables from live Supabase database."""
    engine = get_db_engine()

    inventory_logs = pd.read_sql(
        "SELECT * FROM inventory_logs ORDER BY received_date DESC", engine
    )
    financial_transactions = pd.read_sql("SELECT * FROM financial_transactions", engine)
    weight_logs = pd.read_sql(
        "SELECT * FROM weight_logs ORDER BY weigh_date DESC", engine
    )
    herd = pd.read_sql("SELECT * FROM herd", engine)

    try:
        feeding_standards = pd.read_sql("SELECT * FROM feeding_standards", engine)
    except Exception:
        feeding_standards = pd.DataFrame()

    return inventory_logs, financial_transactions, weight_logs, herd, feeding_standards


def process_received_transactions(df_inv, df_fin_tx):
    """
    Process inbound received transactions by bridging English inventory logs
    with Arabic financial ledger descriptions to extract exact purchase amounts and unit costs.
    """
    if df_inv.empty:
        return pd.DataFrame()

    arabic_to_eng = {
        "برسيم حجازي": "Barseem Hegazy",
        "تبن سوداني": "Hay Bean",
        "تبن فاصوليا": "Hay Bean",
        "تبن": "Hay Bean",
        "ذرة": "Corn",
        "غلة": "Wheat",
        "قمح": "Wheat",
        "ردة": "Radda",
        "رده": "Radda",
        "صويا": "Soyabean",
    }

    fin_tx_purchases = df_fin_tx[
        (df_fin_tx["account_code"] == 5010) & (df_fin_tx["tx_flow"] == "DEBIT")
    ].copy()
    fin_tx_purchases["eng_item"] = fin_tx_purchases["description"].map(arabic_to_eng)

    df_inv["clean_item"] = df_inv["item_name"].str.strip()
    active_logs = df_inv[df_inv["quantity_change"] > 0].copy()

    matched_records = []
    used_indices = set()

    for _, log in active_logs.iterrows():
        d = str(log["received_date"])[:10]
        item = log["clean_item"]
        qty = float(log["quantity_change"])

        cands = fin_tx_purchases[
            (fin_tx_purchases["date"].astype(str).str.startswith(d))
            & (fin_tx_purchases["eng_item"] == item)
            & (~fin_tx_purchases.index.isin(used_indices))
        ]

        amount = 0.0
        if not cands.empty:
            match_row = cands.iloc[0]
            used_indices.add(match_row.name)
            amount = float(match_row["amount"])

        cost_per_kg = amount / qty if qty > 0 else 0.0

        matched_records.append(
            {
                "Date": d,
                "Item Name": item,
                "Qty Received (Kg)": qty,
                "Cost per Kg ($)": cost_per_kg,
                "Total Purchased Amount ($)": amount,
                "Comments": str(log["comments"]) if pd.notnull(log["comments"]) else "",
            }
        )

    formatted = pd.DataFrame(matched_records)
    formatted.to_csv(RECEIVED_CSV, index=False)
    return formatted


def process_consumption_transactions(df_weight):
    """Process and format outbound livestock consumption / weighing transactions (Stream A)."""
    if df_weight.empty:
        return pd.DataFrame()

    df_weight["weigh_date"] = pd.to_datetime(df_weight["weigh_date"], errors="coerce")
    df_weight = df_weight.sort_values(
        by=["weigh_date", "tag_no"], ascending=[False, True]
    )

    formatted = df_weight[
        [
            "weigh_date",
            "tag_no",
            "weight_kg",
            "feed_consumed_since_last_kg",
            "feed_cost",
            "comments",
        ]
    ].copy()
    formatted["weigh_date"] = (
        formatted["weigh_date"].dt.strftime("%Y-%m-%d").fillna("N/A")
    )
    formatted.rename(
        columns={
            "weigh_date": "Weigh Date",
            "tag_no": "Tag #",
            "weight_kg": "Weight (Kg)",
            "feed_consumed_since_last_kg": "Feed Consumed (Kg)",
            "feed_cost": "Feed Cost ($)",
            "comments": "Comments",
        },
        inplace=True,
    )

    formatted.to_csv(CONSUMPTION_CSV, index=False)
    return formatted


def process_general_herd_consumption(herd, feeding_standards):
    """
    Stream B: General Herd Daily Standard Rations & Ingredient Breakdown
    using exact user-defined daily rations and distinct fattening vs general recipe ratios.
    """
    if herd.empty:
        active_herd = pd.DataFrame({"tag_no": [1], "category": ["Ewes"]})
    else:
        active_herd = herd.copy()

    if "category" not in active_herd.columns:
        active_herd["category"] = "General Herd"

    daily_rations = {
        "Fattening": 3.00,
        "Ewes": 2.75,
        "Pregnant": 2.75,
        "Permanent Sire": 3.00,
        "Permanent Sires": 3.00,
        "Small - Female": 1.00,
        "Small - Male": 1.50,
        "(Small) (Female)": 1.00,
        "(Small) (Male)": 1.50,
        "Small-Female": 1.00,
        "Small-Male": 1.50,
        "Ewe": 2.75,
        "Ram": 3.00,
    }

    fattening_ratios = {
        "Wheat": 0.1112,
        "Corn": 0.1276,
        "Radda": 0.0343,
        "Soyabean": 0.0065,
        "Barseem Hegazy": 0.3600,
        "Hay Bean": 0.3600,
    }

    general_ratios = {
        "Wheat": 0.0000,
        "Corn": 0.0300,
        "Radda": 0.0000,
        "Soyabean": 0.0000,
        "Barseem Hegazy": 0.4700,
        "Hay Bean": 0.5000,
    }

    merged = active_herd.copy()
    merged["daily_ration_kg"] = merged["category"].map(daily_rations).fillna(2.00)

    category_summary = (
        merged.groupby("category")
        .agg(
            headcount=("tag_no", "count"),
            daily_ration_per_head=("daily_ration_kg", "first"),
        )
        .reset_index()
    )

    category_summary["total_daily_kg"] = (
        category_summary["headcount"] * category_summary["daily_ration_per_head"]
    )

    audit_days = 90.0
    category_summary["period_total_kg"] = (
        category_summary["total_daily_kg"] * audit_days
    )

    ingredients = ["Barseem Hegazy", "Corn", "Hay Bean", "Wheat", "Radda", "Soyabean"]

    for idx, row in category_summary.iterrows():
        cat = str(row["category"])
        period_kg = float(row["period_total_kg"])

        ratios = fattening_ratios if "Fattening" in cat else general_ratios

        for ing in ingredients:
            category_summary.loc[idx, ing] = period_kg * ratios.get(ing, 0.0)

    category_summary.to_csv(GENERAL_HERD_CSV, index=False)
    return category_summary


def generate_comprehensive_pdf(received_df, consumption_df, gen_herd_df):
    """Compile inbound receipts, individual consumption, and general herd standard rations into a multi-page PDF report."""
    print(f"\n[i] Generating comprehensive PDF report ({PDF_FILENAME})...")

    doc = SimpleDocTemplate(
        PDF_FILENAME,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=15,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=colors.HexColor("#2D3748"),
    )

    story.append(
        Paragraph("MyHerd & Finance — Comprehensive Detailed Audit Report", title_style)
    )
    story.append(
        Paragraph(
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Live Supabase Instance",
            subtitle_style,
        )
    )
    story.append(Spacer(1, 4))

    # Section 1: Inbound Deliveries
    story.append(
        Paragraph(
            "1. Detailed Inbound Inventory Deliveries (Received Transactions)",
            heading_style,
        )
    )
    if not received_df.empty:
        rec_slice = received_df.head(25)
        table_data = [
            ["Date", "Item Name", "Qty (Kg)", "Cost/Kg ($)", "Total ($)", "Comments"]
        ]
        for _, row in rec_slice.iterrows():
            table_data.append(
                [
                    str(row["Date"]),
                    str(row["Item Name"]),
                    f"{float(row['Qty Received (Kg)']):,.2f}",
                    f"{float(row['Cost per Kg ($)']):,.2f}",
                    f"{float(row['Total Purchased Amount ($)']):,.2f}",
                    str(row["Comments"]),
                ]
            )
        t_rec = Table(table_data, colWidths=[65, 110, 65, 70, 75, 155])
        t_rec.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7FAFC")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ]
            )
        )
        story.append(t_rec)
        if len(received_df) > 25:
            story.append(Spacer(1, 2))
            story.append(
                Paragraph(
                    f"<i>Note: Showing top 25 of {len(received_df)} records. Full dataset saved to {RECEIVED_CSV}.</i>",
                    body_style,
                )
            )

    story.append(Spacer(1, 10))

    # Section 2: Fattening Consumption (Stream A)
    story.append(
        Paragraph(
            "2. Detailed Livestock Consumption & Weighing Transactions (Stream A - Fattening Stock)",
            heading_style,
        )
    )
    if not consumption_df.empty:
        con_slice = consumption_df.head(25)
        con_data = [
            [
                "Weigh Date",
                "Tag #",
                "Weight (Kg)",
                "Feed Consumed (Kg)",
                "Feed Cost ($)",
                "Comments",
            ]
        ]
        for _, row in con_slice.iterrows():
            con_data.append(
                [
                    str(row["Weigh Date"]),
                    str(row["Tag #"]),
                    f"{float(row['Weight (Kg)']):,.1f}",
                    f"{float(row['Feed Consumed (Kg)']):,.1f}",
                    f"{float(row['Feed Cost ($)']):,.2f}",
                    str(row["Comments"]) if pd.notnull(row["Comments"]) else "",
                ]
            )
        t_con = Table(con_data, colWidths=[70, 45, 70, 105, 80, 170])
        t_con.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C5282")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7FAFC")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ]
            )
        )
        story.append(t_con)
        if len(consumption_df) > 25:
            story.append(Spacer(1, 2))
            story.append(
                Paragraph(
                    f"<i>Note: Showing top 25 of {len(consumption_df)} records. Full dataset saved to {CONSUMPTION_CSV}.</i>",
                    body_style,
                )
            )

    # Page break before Section 3
    story.append(PageBreak())

    # Section 3: General Herd Rations & Ingredients (Stream B)
    story.append(
        Paragraph(
            "3. General Herd Standard Ration Consumption & Ingredient Breakdown (Stream B)",
            heading_style,
        )
    )
    story.append(Spacer(1, 6))
    if not gen_herd_df.empty:
        gh_headers = [
            "Category",
            "Headcount",
            "Period Total (Kg)",
            "Barseem",
            "Corn",
            "Hay Bean",
            "Wheat",
            "Radda",
            "Soyabean",
        ]
        gh_data = [gh_headers]
        for _, row in gen_herd_df.iterrows():
            gh_data.append(
                [
                    str(row["category"]),
                    str(row["headcount"]),
                    f"{float(row['period_total_kg']):,.1f}",
                    f"{float(row['Barseem Hegazy']):,.1f}",
                    f"{float(row['Corn']):,.1f}",
                    f"{float(row['Hay Bean']):,.1f}",
                    f"{float(row['Wheat']):,.1f}",
                    f"{float(row['Radda']):,.1f}",
                    f"{float(row['Soyabean']):,.1f}",
                ]
            )
        t_gh = Table(gh_data, colWidths=[100, 50, 75, 55, 50, 55, 50, 45, 60])
        t_gh.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7FAFC")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ]
            )
        )
        story.append(t_gh)
        story.append(Spacer(1, 6))
        story.append(
            Paragraph(
                f"<i>Extended ingredient breakdown saved to {GENERAL_HERD_CSV}.</i>",
                body_style,
            )
        )

    doc.build(story)
    print(
        f"[v] Comprehensive PDF report successfully generated and saved as '{PDF_FILENAME}' in your project folder."
    )


def main():
    print("==================================================")
    print(" COMPREHENSIVE DETAILED REPORT GENERATOR (PYTHON)")
    print("==================================================")

    try:
        print(
            "[i] Fetching live transaction, inventory, and herd tables from Supabase..."
        )
        inv_logs, fin_tx, weight_logs, herd, feeding_standards = fetch_all_data()
        print("[v] Data fetched successfully.\n")

        received_df = process_received_transactions(inv_logs, fin_tx)
        consumption_df = process_consumption_transactions(weight_logs)
        gen_herd_df = process_general_herd_consumption(herd, feeding_standards)

        generate_comprehensive_pdf(received_df, consumption_df, gen_herd_df)

    except Exception as e:
        print(f"[X] ERROR: Failed to execute comprehensive report: {e}")

    print("\n==================================================")
    print("      COMPREHENSIVE REPORT GENERATION COMPLETED   ")
    print("==================================================")


if __name__ == "__main__":
    main()
