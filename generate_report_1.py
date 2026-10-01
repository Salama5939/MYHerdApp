# ==============================================================================
# SCRIPT 1: Flock Performance Evaluation Report Generator
# Output Files: Flock_Performance_Evaluation_Report.docx
#               Flock_Performance_Evaluation_Report.pdf
# ==============================================================================

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.pdfgen import canvas


def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=60, bottom=60, left=100, right=100):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        getattr(self, "_startPage")()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#595959"))
        page_number = getattr(self, "_pageNumber", 1)
        if page_number > 1:
            self.drawString(36, 11 * inch - 28, "FLOCK PERFORMANCE EVALUATION REPORT")
            self.setStrokeColor(colors.HexColor("#D9D9D9"))
            self.setLineWidth(0.5)
            self.line(36, 11 * inch - 32, 8.5 * inch - 36, 11 * inch - 32)
        page_text = f"Page {page_number} of {page_count}"
        self.drawRightString(8.5 * inch - 36, 25, page_text)
        self.drawString(36, 25, "CONFIDENTIAL — EXECUTIVE LIVESTOCK MANAGEMENT REPORT")
        self.setStrokeColor(colors.HexColor("#D9D9D9"))
        self.setLineWidth(0.5)
        self.line(36, 35, 8.5 * inch - 36, 35)
        self.restoreState()


def create_report_1_docx(filename="Flock_Performance_Evaluation_Report.docx"):
    doc = docx.Document()
    for s in doc.sections:
        s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Inches(0.8)

    NAVY = RGBColor(31, 73, 125)
    GRAY = RGBColor(89, 89, 89)
    RED = RGBColor(192, 0, 0)

    # Header Title
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_after = Pt(2)
    r = p_title.add_run("FLOCK PERFORMANCE EVALUATION REPORT")
    r.font.size, r.font.bold, r.font.color.rgb = Pt(18), True, NAVY

    # Subtitle
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(10)
    r = p_sub.add_run(
        "Comprehensive Biological Throughput, Cohort Yield & Commercial Off-Take Audit (22/02/2026 – 22/09/2026)"
    )
    r.font.size, r.font.italic, r.font.color.rgb = Pt(10), True, GRAY

    # Metadata Banner Table
    tb = doc.add_table(rows=1, cols=3)
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    widths = [Inches(2.2), Inches(2.4), Inches(2.2)]
    headers = [
        ("Evaluation Date", "September 30, 2026"),
        ("Tracked Flock Volume", "222 Unique Head"),
        ("Audit Snapshot Scope", "5 Snapshots (7 Months)"),
    ]
    for idx, (label, val) in enumerate(headers):
        cell = tb.cell(0, idx)
        cell.width = widths[idx]
        set_cell_background(cell, "F2F5F9")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r1 = p.add_run(f"{label}\n")
        r1.font.size, r1.font.color.rgb = Pt(8.5), GRAY
        r2 = p.add_run(val)
        r2.font.size, r2.font.bold, r2.font.color.rgb = Pt(10.5), True, NAVY

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Section 1
    h1 = doc.add_paragraph()
    h1.paragraph_format.space_before, h1.paragraph_format.space_after = Pt(8), Pt(4)
    r = h1.add_run("1. Executive Summary & Key Performance Indicators")
    r.font.size, r.font.bold, r.font.color.rgb = Pt(12), True, NAVY

    p_body = doc.add_paragraph()
    p_body.paragraph_format.space_after = Pt(6)
    p_body.add_run(
        "This evaluation analyzes the biological productivity, cohort yields, commercial slaughter off-take, and mortality performance of the sheep flock over the 7-month auditing window from February 22, 2026 to September 22, 2026. Based on the revised master dataset of 222 tracked animals, the flock demonstrated strong reproductive growth and excellent commercial meat yield, alongside a low overall mortality rate."
    )

    # KPI Table
    tb_kpi = doc.add_table(rows=7, cols=4)
    tb_kpi.alignment = WD_TABLE_ALIGNMENT.CENTER
    kpi_widths = [Inches(1.6), Inches(1.5), Inches(1.2), Inches(2.5)]
    kpi_headers = [
        "Performance Domain",
        "Key Metric",
        "Audit Result",
        "Operational Assessment & Benchmark",
    ]
    for i, h in enumerate(kpi_headers):
        cell = tb_kpi.cell(0, i)
        cell.width = kpi_widths[i]
        set_cell_background(cell, "1F497D")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.bold, r.font.size, r.font.color.rgb = (
            True,
            Pt(8.5),
            RGBColor(255, 255, 255),
        )

    kpi_rows = [
        (
            "Gross Flock Expansion",
            "System Active Growth Rate",
            "+108.5%",
            "Expanded from 82 to 171 active system head. High biological capacity.",
        ),
        (
            "Verified Flock Expansion",
            "Confirmed Active Growth",
            "+62.2%",
            "Confirmed physical growth from 82 to 133 head present in barn pens.",
        ),
        (
            "Commercial Off-Take",
            "Slaughter & Sales Volume",
            "45 head (20.3%)",
            "39 fattening slaughters, 5 live sales, 1 Zakat. High revenue conversion.",
        ),
        (
            "Flock Biosecurity",
            "Cumulative Mortality Rate",
            "2.7% (6 head)",
            "Excellent health control. Well within commercial target (< 5.0%).",
        ),
        (
            "Reproductive Output",
            "Breeding Ewe Capacity",
            "81 head",
            "50 open/lactating ewes + 30 pregnant ewes entering fall lambing.",
        ),
        (
            "Physical Reconciliation",
            "Barn Count Match Rate",
            "78.0%",
            "Primary Risk: 38 active head unverified physically during Sept count.",
        ),
    ]
    for r_idx, data in enumerate(kpi_rows, 1):
        for c_idx, val in enumerate(data):
            cell = tb_kpi.cell(r_idx, c_idx)
            cell.width = kpi_widths[c_idx]
            set_cell_background(cell, "F9FAFB" if r_idx % 2 == 1 else "FFFFFF")
            set_cell_margins(cell, top=50, bottom=50, left=80, right=80)
            p = cell.paragraphs[0]
            p.alignment = (
                WD_ALIGN_PARAGRAPH.CENTER
                if c_idx in [1, 2]
                else WD_ALIGN_PARAGRAPH.LEFT
            )
            r = p.add_run(val)
            r.font.size = Pt(8)
            if c_idx == 2 and "78.0%" in val:
                r.font.color.rgb, r.font.bold = RED, True
            elif c_idx == 0:
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Section 2
    h2 = doc.add_paragraph()
    h2.paragraph_format.space_before, h2.paragraph_format.space_after = Pt(8), Pt(4)
    r = h2.add_run("2. Cohort Yield & Origin Comparative Analysis")
    r.font.size, r.font.bold, r.font.color.rgb = Pt(12), True, NAVY

    doc.add_paragraph(
        "A critical strength of the consolidated dataset is tracking origin cohorts: Purchased (89 head), Our Production (83 head), and Opening Stock (41 head). Evaluating cohorts independently reveals distinct operational functions and yield profiles across the flock:"
    )

    # Cohort Table
    tb_co = doc.add_table(rows=8, cols=5)
    tb_co.alignment = WD_TABLE_ALIGNMENT.CENTER
    co_widths = [Inches(2.0), Inches(1.2), Inches(1.2), Inches(1.2), Inches(1.2)]
    co_headers = [
        "Cohort Origin Category",
        "Purchased Stock",
        "Home Production",
        "Opening Stock",
        "Total Flock",
    ]
    for i, h in enumerate(co_headers):
        cell = tb_co.cell(0, i)
        cell.width = co_widths[i]
        set_cell_background(cell, "2E6B9E")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.bold, r.font.size, r.font.color.rgb = (
            True,
            Pt(8.5),
            RGBColor(255, 255, 255),
        )

    co_data = [
        (
            "Total Registered Head",
            "89 head (40.1%)",
            "83 head (37.4%)",
            "41 head (18.5%)",
            "222 head (100%)",
        ),
        (
            "Verified Active Present (√)",
            "49 head (55.1%)",
            "51 head (61.4%)",
            "33 head (80.5%)",
            "133 head (59.9%)",
        ),
        (
            "Commercial Slaughters",
            "28 head (31.5%)",
            "4 head (4.8%)",
            "3 head (7.3%)",
            "39 head (17.6%)",
        ),
        (
            "Live Sales & Zakat",
            "3 head (3.3%)",
            "2 head (2.4%)",
            "1 head (2.4%)",
            "6 head (2.7%)",
        ),
        (
            "Mortalities (Died)",
            "0 head (0.0%)",
            "6 head (7.2%)",
            "0 head (0.0%)",
            "6 head (2.7%)",
        ),
        (
            "Uncounted Active (×)",
            "9 head (10.1%)",
            "20 head (24.1%)",
            "4 head (9.8%)",
            "38 head (17.1%)",
        ),
        (
            "Primary Operational Role",
            "Market Finishing Yield",
            "Replacement Pipeline",
            "Breeding Foundation",
            "Integrated Production",
        ),
    ]
    for r_idx, data in enumerate(co_data, 1):
        for c_idx, val in enumerate(data):
            cell = tb_co.cell(r_idx, c_idx)
            cell.width = co_widths[c_idx]
            set_cell_background(
                cell,
                "F2F5F9" if r_idx == 7 else ("F9FAFB" if r_idx % 2 == 1 else "FFFFFF"),
            )
            set_cell_margins(cell, top=50, bottom=50, left=80, right=80)
            p = cell.paragraphs[0]
            p.alignment = (
                WD_ALIGN_PARAGRAPH.CENTER if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
            )
            r = p.add_run(val)
            r.font.size = Pt(8)
            if r_idx == 7 or c_idx == 0:
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    p_ins = doc.add_paragraph()
    p_ins.add_run("Key Cohort Findings:\n").font.bold = True
    bullets = [
        "Purchased Stock Drives Meat Revenue: 28 out of 39 total slaughters (71.8%) originated from purchased stock, achieving rapid finishing conversion.",
        "Home Production Expands Breeding Base: Home production generated 83 lambs, of which 51 are verified active in pens, building the future replacement base.",
        "Mortality Biosecurity Concentration: All 6 mortalities occurred strictly in home-born lambs (7.2% lamb mortality rate). Purchased and opening stock adults suffered 0% mortality.",
        "Tagging & Verification Discrepancy: Home production accounts for 20 out of 38 uncounted active head (52.6%), highlighting an urgent need for post-lambing ear-tagging discipline.",
    ]
    for b in bullets:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(2)
        p.add_run(b).font.size = Pt(8.5)

    # Section 3
    h3 = doc.add_paragraph()
    h3.paragraph_format.space_before, h3.paragraph_format.space_after = Pt(8), Pt(4)
    r = h3.add_run("3. Biological Productivity & Category Inventory Breakdown")
    r.font.size, r.font.bold, r.font.color.rgb = Pt(12), True, NAVY

    # Category Table
    tb_cat = doc.add_table(rows=8, cols=5)
    tb_cat.alignment = WD_TABLE_ALIGNMENT.CENTER
    cat_widths = [Inches(2.5), Inches(1.25), Inches(1.25), Inches(1.25), Inches(1.25)]
    cat_headers = [
        "Category Classification",
        "System Active (T5)",
        "Verified Present (√)",
        "Uncounted Active (×)",
        "Verification Rate",
    ]
    for i, h in enumerate(cat_headers):
        cell = tb_cat.cell(0, i)
        cell.width = cat_widths[i]
        set_cell_background(cell, "1F497D")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.bold, r.font.size, r.font.color.rgb = (
            True,
            Pt(8.5),
            RGBColor(255, 255, 255),
        )

    cat_rows = [
        ("Ewes (Open / Lactating)", "49 head", "39 head", "10 head", "79.6%"),
        ("Pregnant Ewes", "34 head", "31 head", "3 head", "91.2%"),
        ("(Small) Female Lambs", "37 head", "30 head", "7 head", "81.1%"),
        ("(Small) Male Lambs", "38 head", "21 head", "17 head", "55.3%"),
        ("Fattening Lambs", "10 head", "10 head", "0 head", "100.0%"),
        ("Permanent Sires (Rams)", "3 head", "2 head", "1 head", "66.7%"),
        ("Total Active Flock", "171 head", "133 head", "38 head", "77.8%"),
    ]
    for r_idx, data in enumerate(cat_rows, 1):
        for c_idx, val in enumerate(data):
            cell = tb_cat.cell(r_idx, c_idx)
            cell.width = cat_widths[c_idx]
            is_tot = r_idx == 7
            set_cell_background(
                cell, "F2F5F9" if is_tot else ("F9FAFB" if r_idx % 2 == 1 else "FFFFFF")
            )
            set_cell_margins(cell, top=50, bottom=50, left=80, right=80)
            p = cell.paragraphs[0]
            p.alignment = (
                WD_ALIGN_PARAGRAPH.CENTER if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
            )
            r = p.add_run(val)
            r.font.size = Pt(8)
            if is_tot or c_idx == 0:
                r.font.bold = True

    doc.save(filename)
    print(f"Successfully generated Word document: {filename}")


def create_report_1_pdf(filename="Flock_Performance_Evaluation_Report.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    NAVY = colors.HexColor("#1F497D")
    SLATE = colors.HexColor("#2E6B9E")
    DARK = colors.HexColor("#262626")
    BG = colors.HexColor("#F2F5F9")

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=NAVY,
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "SubTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#595959"),
        spaceAfter=8,
    )
    h1_style = ParagraphStyle(
        "H1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=14,
        textColor=NAVY,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=DARK,
        spaceAfter=4,
    )
    bullet_style = ParagraphStyle(
        "Bullet", parent=body_style, leftIndent=10, spaceAfter=2.5
    )

    tbl_hdr = ParagraphStyle(
        "TH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10,
        textColor=colors.white,
        alignment=1,
    )
    tbl_cell = ParagraphStyle(
        "TC",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=DARK,
    )
    tbl_cell_bold = ParagraphStyle("TCB", parent=tbl_cell, fontName="Helvetica-Bold")
    tbl_cell_ctr = ParagraphStyle("TCC", parent=tbl_cell, alignment=1)
    tbl_cell_ctr_b = ParagraphStyle("TCCB", parent=tbl_cell_bold, alignment=1)

    story = [
        Paragraph("FLOCK PERFORMANCE EVALUATION REPORT", title_style),
        Paragraph(
            "Comprehensive Biological Throughput, Cohort Yield & Commercial Off-Take Audit (22/02/2026 – 22/09/2026)",
            subtitle_style,
        ),
        HRFlowable(
            width="100%", thickness=1.2, color=NAVY, spaceBefore=0, spaceAfter=6
        ),
    ]

    banner_data = [
        [
            Paragraph("<b>Evaluation Date:</b> September 30, 2026", tbl_cell),
            Paragraph("<b>Tracked Flock Volume:</b> 222 Unique Head", tbl_cell),
            Paragraph("<b>Audit Snapshot Scope:</b> 5 Snapshots (7 Months)", tbl_cell),
        ]
    ]
    banner_table = Table(banner_data, colWidths=[2.5 * inch, 2.7 * inch, 2.3 * inch])
    banner_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BG),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(banner_table)
    story.append(Spacer(1, 6))

    story.append(
        Paragraph("1. Executive Summary & Key Performance Indicators", h1_style)
    )
    story.append(
        Paragraph(
            "This evaluation analyzes the biological productivity, cohort yields, commercial slaughter off-take, and mortality performance of the sheep flock over the 7-month auditing window from February 22, 2026 to September 22, 2026. Based on the revised master dataset of 222 tracked animals, the flock demonstrated strong reproductive growth and excellent commercial meat yield, alongside a low overall mortality rate.",
            body_style,
        )
    )

    kpi_data = [
        [
            Paragraph("Performance Domain", tbl_hdr),
            Paragraph("Key Metric", tbl_hdr),
            Paragraph("Audit Result", tbl_hdr),
            Paragraph("Operational Assessment & Benchmark", tbl_hdr),
        ],
        [
            Paragraph("Gross Flock Expansion", tbl_cell_bold),
            Paragraph("System Active Growth Rate", tbl_cell),
            Paragraph("<b>+108.5%</b>", tbl_cell_ctr),
            Paragraph(
                "Expanded from 82 to 171 active system head. High biological capacity.",
                tbl_cell,
            ),
        ],
        [
            Paragraph("Verified Flock Expansion", tbl_cell_bold),
            Paragraph("Confirmed Active Growth", tbl_cell),
            Paragraph("<b>+62.2%</b>", tbl_cell_ctr),
            Paragraph(
                "Confirmed physical growth from 82 to 133 head present in barn pens.",
                tbl_cell,
            ),
        ],
        [
            Paragraph("Commercial Off-Take", tbl_cell_bold),
            Paragraph("Slaughter & Sales Volume", tbl_cell),
            Paragraph("<b>45 head (20.3%)</b>", tbl_cell_ctr),
            Paragraph(
                "39 fattening slaughters, 5 live sales, 1 Zakat. High revenue conversion.",
                tbl_cell,
            ),
        ],
        [
            Paragraph("Flock Biosecurity", tbl_cell_bold),
            Paragraph("Cumulative Mortality Rate", tbl_cell),
            Paragraph("<b>2.7% (6 head)</b>", tbl_cell_ctr),
            Paragraph(
                "Excellent health control. Well within commercial target (< 5.0%).",
                tbl_cell,
            ),
        ],
        [
            Paragraph("Reproductive Output", tbl_cell_bold),
            Paragraph("Breeding Ewe Capacity", tbl_cell),
            Paragraph("<b>81 head</b>", tbl_cell_ctr),
            Paragraph(
                "50 open/lactating ewes + 30 pregnant ewes entering fall lambing.",
                tbl_cell,
            ),
        ],
        [
            Paragraph("Physical Reconciliation", tbl_cell_bold),
            Paragraph("Barn Count Match Rate", tbl_cell),
            Paragraph("<font color='#C00000'><b>78.0%</b></font>", tbl_cell_ctr),
            Paragraph(
                "<font color='#C00000'><b>Primary Risk:</b> 38 active head unverified physically during Sept count.</font>",
                tbl_cell,
            ),
        ],
    ]
    kpi_table = Table(
        kpi_data, colWidths=[1.6 * inch, 1.6 * inch, 1.2 * inch, 3.1 * inch]
    )
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F9FAFB")],
                ),
                ("PADDING", (0, 0), (-1, -1), 3.5),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("2. Cohort Yield & Origin Comparative Analysis", h1_style))
    story.append(
        Paragraph(
            "A critical strength of the consolidated dataset is tracking origin cohorts: Purchased (89 head), Our Production (83 head), and Opening Stock (41 head). Evaluating cohorts independently reveals distinct operational functions and yield profiles across the flock:",
            body_style,
        )
    )

    co_data = [
        [
            Paragraph("Cohort Origin Category", tbl_hdr),
            Paragraph("Purchased Stock", tbl_hdr),
            Paragraph("Home Production", tbl_hdr),
            Paragraph("Opening Stock", tbl_hdr),
            Paragraph("Total Flock", tbl_hdr),
        ],
        [
            Paragraph("Total Registered Head", tbl_cell_bold),
            Paragraph("89 head (40.1%)", tbl_cell_ctr),
            Paragraph("83 head (37.4%)", tbl_cell_ctr),
            Paragraph("41 head (18.5%)", tbl_cell_ctr),
            Paragraph("222 head (100%)", tbl_cell_ctr_b),
        ],
        [
            Paragraph("Verified Active Present (√)", tbl_cell_bold),
            Paragraph("49 head (55.1%)", tbl_cell_ctr),
            Paragraph("51 head (61.4%)", tbl_cell_ctr),
            Paragraph("33 head (80.5%)", tbl_cell_ctr),
            Paragraph("133 head (59.9%)", tbl_cell_ctr_b),
        ],
        [
            Paragraph("Commercial Slaughters", tbl_cell_bold),
            Paragraph("28 head (31.5%)", tbl_cell_ctr),
            Paragraph("4 head (4.8%)", tbl_cell_ctr),
            Paragraph("3 head (7.3%)", tbl_cell_ctr),
            Paragraph("39 head (17.6%)", tbl_cell_ctr_b),
        ],
        [
            Paragraph("Live Sales & Zakat", tbl_cell_bold),
            Paragraph("3 head (3.3%)", tbl_cell_ctr),
            Paragraph("2 head (2.4%)", tbl_cell_ctr),
            Paragraph("1 head (2.4%)", tbl_cell_ctr),
            Paragraph("6 head (2.7%)", tbl_cell_ctr_b),
        ],
        [
            Paragraph("Mortalities (Died)", tbl_cell_bold),
            Paragraph("0 head (0.0%)", tbl_cell_ctr),
            Paragraph("6 head (7.2%)", tbl_cell_ctr),
            Paragraph("0 head (0.0%)", tbl_cell_ctr),
            Paragraph("6 head (2.7%)", tbl_cell_ctr_b),
        ],
        [
            Paragraph("Uncounted Active (×)", tbl_cell_bold),
            Paragraph("9 head (10.1%)", tbl_cell_ctr),
            Paragraph("20 head (24.1%)", tbl_cell_ctr),
            Paragraph("4 head (9.8%)", tbl_cell_ctr),
            Paragraph("38 head (17.1%)", tbl_cell_ctr_b),
        ],
        [
            Paragraph("Primary Operational Role", tbl_cell_bold),
            Paragraph("Market Finishing Yield", tbl_cell_ctr),
            Paragraph("Replacement Pipeline", tbl_cell_ctr),
            Paragraph("Breeding Foundation", tbl_cell_ctr),
            Paragraph("Integrated Production", tbl_cell_ctr_b),
        ],
    ]
    co_table = Table(
        co_data,
        colWidths=[2.1 * inch, 1.35 * inch, 1.35 * inch, 1.35 * inch, 1.35 * inch],
    )
    co_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), SLATE),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -2),
                    [colors.white, colors.HexColor("#F9FAFB")],
                ),
                ("BACKGROUND", (0, -1), (-1, -1), BG),
                ("PADDING", (0, 0), (-1, -1), 3.5),
            ]
        )
    )
    story.append(co_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Key Cohort Findings:</b>", body_style))
    story.append(
        Paragraph(
            "• <b>Purchased Stock Drives Meat Revenue:</b> 28 out of 39 total slaughters (71.8%) originated from purchased stock, achieving rapid finishing conversion.",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Home Production Expands Breeding Base:</b> Home production generated 83 lambs, of which 51 are verified active in pens, building the future replacement base.",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Mortality Biosecurity Concentration:</b> All 6 mortalities occurred strictly in home-born lambs (7.2% lamb mortality rate). Purchased and opening stock adults suffered 0% mortality.",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Tagging & Verification Discrepancy:</b> Home production accounts for 20 out of 38 uncounted active head (52.6%), highlighting an urgent need for post-lambing ear-tagging discipline.",
            bullet_style,
        )
    )
    story.append(Spacer(1, 6))

    story.append(
        Paragraph("3. Biological Productivity & Category Inventory Breakdown", h1_style)
    )
    cat_data = [
        [
            Paragraph("Category Classification", tbl_hdr),
            Paragraph("System Active (T5)", tbl_hdr),
            Paragraph("Verified Present (√)", tbl_hdr),
            Paragraph("Uncounted Active (×)", tbl_hdr),
            Paragraph("Verification Rate", tbl_hdr),
        ],
        [
            Paragraph("Ewes (Open / Lactating)", tbl_cell_bold),
            Paragraph("49 head", tbl_cell_ctr),
            Paragraph("39 head", tbl_cell_ctr),
            Paragraph("10 head", tbl_cell_ctr),
            Paragraph("79.6%", tbl_cell_ctr),
        ],
        [
            Paragraph("Pregnant Ewes", tbl_cell_bold),
            Paragraph("34 head", tbl_cell_ctr),
            Paragraph("31 head", tbl_cell_ctr),
            Paragraph("3 head", tbl_cell_ctr),
            Paragraph("91.2%", tbl_cell_ctr),
        ],
        [
            Paragraph("(Small) Female Lambs", tbl_cell_bold),
            Paragraph("37 head", tbl_cell_ctr),
            Paragraph("30 head", tbl_cell_ctr),
            Paragraph("7 head", tbl_cell_ctr),
            Paragraph("81.1%", tbl_cell_ctr),
        ],
        [
            Paragraph("(Small) Male Lambs", tbl_cell_bold),
            Paragraph("38 head", tbl_cell_ctr),
            Paragraph("21 head", tbl_cell_ctr),
            Paragraph("17 head", tbl_cell_ctr),
            Paragraph("55.3%", tbl_cell_ctr),
        ],
        [
            Paragraph("Fattening Lambs", tbl_cell_bold),
            Paragraph("10 head", tbl_cell_ctr),
            Paragraph("10 head", tbl_cell_ctr),
            Paragraph("0 head", tbl_cell_ctr),
            Paragraph("100.0%", tbl_cell_ctr),
        ],
        [
            Paragraph("Permanent Sires (Rams)", tbl_cell_bold),
            Paragraph("3 head", tbl_cell_ctr),
            Paragraph("2 head", tbl_cell_ctr),
            Paragraph("1 head", tbl_cell_ctr),
            Paragraph("66.7%", tbl_cell_ctr),
        ],
        [
            Paragraph("Total Active Flock", tbl_cell_bold),
            Paragraph("171 head", tbl_cell_ctr_b),
            Paragraph("133 head", tbl_cell_ctr_b),
            Paragraph("38 head", tbl_cell_ctr_b),
            Paragraph("77.8%", tbl_cell_ctr_b),
        ],
    ]
    cat_table = Table(
        cat_data,
        colWidths=[2.5 * inch, 1.25 * inch, 1.25 * inch, 1.25 * inch, 1.25 * inch],
    )
    cat_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -2),
                    [colors.white, colors.HexColor("#F9FAFB")],
                ),
                ("BACKGROUND", (0, -1), (-1, -1), BG),
                ("PADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(cat_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF document: {filename}")


if __name__ == "__main__":
    create_report_1_docx()
    create_report_1_pdf()
