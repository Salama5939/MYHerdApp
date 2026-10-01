# ==============================================================================
# SCRIPT 2: Herd Inventory Audit & Strategic Action Plan Generator
# Output Files: Herd_Inventory_Audit_and_Strategic_Action_Plan.docx
#               Herd_Inventory_Audit_and_Strategic_Action_Plan.pdf
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
        start_page = getattr(self, "_startPage", None)
        if start_page is None:
            raise AttributeError("Canvas implementation does not expose _startPage")
        start_page()

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
            self.drawString(
                36, 11 * inch - 28, "HERD INVENTORY AUDIT & STRATEGIC ACTION PLAN"
            )
            self.setStrokeColor(colors.HexColor("#D9D9D9"))
            self.setLineWidth(0.5)
            self.line(36, 11 * inch - 32, 8.5 * inch - 36, 11 * inch - 32)
        page_text = f"Page {page_number} of {page_count}"
        self.drawRightString(8.5 * inch - 36, 25, page_text)
        self.drawString(36, 25, "CONFIDENTIAL — INVENTORY AUDIT & ACTION PLAN")
        self.setStrokeColor(colors.HexColor("#D9D9D9"))
        self.setLineWidth(0.5)
        self.line(36, 35, 8.5 * inch - 36, 35)
        self.restoreState()


def create_report_2_docx(
    filename="Herd_Inventory_Audit_and_Strategic_Action_Plan.docx",
):
    doc = docx.Document()
    for s in doc.sections:
        s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Inches(0.8)

    NAVY = RGBColor(31, 73, 125)
    GRAY = RGBColor(89, 89, 89)
    RED = RGBColor(192, 0, 0)

    # Title
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_after = Pt(2)
    r = p_title.add_run("HERD INVENTORY AUDIT & STRATEGIC ACTION PLAN")
    r.font.size, r.font.bold, r.font.color.rgb = Pt(18), True, NAVY

    # Subtitle
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(10)
    r = p_sub.add_run(
        "Inventory Reconciliation, Tag Traceability Protocol & Pre-Feed Transition Strategy"
    )
    r.font.size, r.font.italic, r.font.color.rgb = Pt(10), True, GRAY

    # Metadata Banner
    tb = doc.add_table(rows=1, cols=3)
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    widths = [Inches(2.2), Inches(2.4), Inches(2.2)]
    headers = [
        ("Audit Date", "September 30, 2026"),
        ("Reconciliation Target", "38 Uncounted Active Head"),
        ("Primary Goal", "100% Barn Verification & Feed Alignment"),
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
    r = h1.add_run("1. Executive Summary & Audit Mandate")
    r.font.size, r.font.bold, r.font.color.rgb = Pt(12), True, NAVY

    doc.add_paragraph(
        "Following the master stock take evaluation on September 22, 2026, this audit focuses directly on reconciling the inventory gap between system active records (171 head) and physically verified animals (133 head). Eliminating the 38 uncounted active head (22.2% of active system inventory) is a prerequisite before finalizing daily feed consumption budgeting and biological asset valuations."
    )

    # Audit Area Table
    tb_aud = doc.add_table(rows=5, cols=4)
    tb_aud.alignment = WD_TABLE_ALIGNMENT.CENTER
    aud_widths = [Inches(1.8), Inches(1.3), Inches(1.0), Inches(2.7)]
    aud_headers = [
        "Audit Area",
        "Discrepancy Volume",
        "Risk Level",
        "Root Cause & Impact Summary",
    ]
    for i, h in enumerate(aud_headers):
        cell = tb_aud.cell(0, i)
        cell.width = aud_widths[i]
        set_cell_background(cell, "1F497D")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.bold, r.font.size, r.font.color.rgb = (
            True,
            Pt(8.5),
            RGBColor(255, 255, 255),
        )

    aud_rows = [
        (
            "Uncounted Active Head",
            "38 head",
            "HIGH",
            "20 home-born lambs + 9 purchased + 4 opening + 5 lost tags missing physical tag count.",
        ),
        (
            "Duplicate Tag Entry",
            "1 tag (Tag 101)",
            "MEDIUM",
            "Tag 101 logged twice: Row 67 (Ewe/Opening) vs Row 68 (Pregnant/Purchased).",
        ),
        (
            "Lost Ear Tags",
            "5 head",
            "MEDIUM",
            "Tags 190, 359, 360, 385, 386 shed in pens during grazing/feeding; missing visual ID.",
        ),
        (
            "Re-tagged Off-Take",
            "4 head",
            "LOW",
            "Old Tag # 180, 29, 30, 36 harvested; re-tagging cross-reference requires log closure.",
        ),
    ]
    for r_idx, data in enumerate(aud_rows, 1):
        for c_idx, val in enumerate(data):
            cell = tb_aud.cell(r_idx, c_idx)
            cell.width = aud_widths[c_idx]
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
            if c_idx == 2 and "HIGH" in val:
                r.font.color.rgb, r.font.bold = RED, True
            elif c_idx == 0:
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Section 2
    h2 = doc.add_paragraph()
    h2.paragraph_format.space_before, h2.paragraph_format.space_after = Pt(8), Pt(4)
    r = h2.add_run("2. Uncounted Active Head Deep-Dive Analysis")
    r.font.size, r.font.bold, r.font.color.rgb = Pt(12), True, NAVY

    doc.add_paragraph(
        "A detailed breakdown of the 38 uncounted active animals by origin cohort and age/category highlights where inventory verification broke down during the September stock take:"
    )

    # Uncounted Breakdown Table
    tb_unc = doc.add_table(rows=6, cols=6)
    tb_unc.alignment = WD_TABLE_ALIGNMENT.CENTER
    unc_widths = [
        Inches(2.1),
        Inches(0.9),
        Inches(0.9),
        Inches(0.9),
        Inches(0.9),
        Inches(1.1),
    ]
    unc_headers = [
        "Cohort Origin",
        "(Small) Male",
        "Ewes",
        "(Small) Female",
        "Pregnant",
        "Total Uncounted",
    ]
    for i, h in enumerate(unc_headers):
        cell = tb_unc.cell(0, i)
        cell.width = unc_widths[i]
        set_cell_background(cell, "2E6B9E")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.bold, r.font.size, r.font.color.rgb = (
            True,
            Pt(8.5),
            RGBColor(255, 255, 255),
        )

    unc_data = [
        (
            "Home Production (Our Production)",
            "13 head",
            "0 head",
            "7 head",
            "0 head",
            "20 head (52.6%)",
        ),
        ("Purchased Stock", "0 head", "5 head", "0 head", "3 head", "9 head (23.7%)"),
        ("Lost Tag # Group", "4 head", "1 head", "0 head", "0 head", "5 head (13.2%)"),
        (
            "Opening Stock Group",
            "0 head",
            "4 head",
            "0 head",
            "0 head",
            "4 head (10.5%)",
        ),
        (
            "Total Uncounted Active",
            "17 head (44.7%)",
            "10 head (26.3%)",
            "7 head (18.4%)",
            "3 head (7.9%)",
            "38 head (100%)",
        ),
    ]
    for r_idx, data in enumerate(unc_data, 1):
        for c_idx, val in enumerate(data):
            cell = tb_unc.cell(r_idx, c_idx)
            cell.width = unc_widths[c_idx]
            is_tot = r_idx == 5
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
            if is_tot or c_idx in [0, 5]:
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Section 3
    h3 = doc.add_paragraph()
    h3.paragraph_format.space_before, h3.paragraph_format.space_after = Pt(8), Pt(4)
    r = h3.add_run("3. Strategic 4-Pillar Action Plan")
    r.font.size, r.font.bold, r.font.color.rgb = Pt(12), True, RED

    pillars = [
        (
            "PILLAR 1: Physical Pen Audit & Tagging Sweep (48-Hour Field Action)",
            "• Conduct a full physical pen sweep targeting the 17 missing male lambs and 7 female lambs in young stock pens.\n• Re-tag un-identified animals using new double-locking tags and log re-tag IDs immediately.",
        ),
        (
            "PILLAR 2: Tag Traceability & Duplicate Resolution SOP",
            "• Resolve Duplicate Tag 101: Verify physical tag 101 in pen (Row 68 Purchased Pregnant Ewe vs Row 67 Opening Ewe) and update sheet.\n• Close re-tag logs for harvested stock (Old Tag # 180, 29, 30, 36) to prevent phantom active listings.",
        ),
        (
            "PILLAR 3: Feed Budget Calibration (Pre-Feed Transition Rule)",
            "• Calibrate daily feed ration formulas strictly to the 133 physically verified active animals (√).\n• Do NOT allocate feed rations for the 38 uncounted animals until physical presence is confirmed in pen.",
        ),
        (
            "PILLAR 4: Breeding Pen Allocation & Fall Lambing Preparation",
            "• Confirm location of the 30 pregnant ewes (91.2% verified) and assign them to maternity pens for fall lambing.\n• Allocate permanent sires (Tags 105, 106) to active breeding groups.",
        ),
    ]
    for title, desc in pillars:
        p_p = doc.add_paragraph()
        p_p.paragraph_format.space_after = Pt(2)
        r = p_p.add_run(title)
        r.font.bold, r.font.size, r.font.color.rgb = True, Pt(9.5), NAVY
        p_d = doc.add_paragraph()
        p_d.paragraph_format.space_after = Pt(4)
        p_d.add_run(desc).font.size = Pt(8.5)

    # Section 4
    h4 = doc.add_paragraph()
    h4.paragraph_format.space_before, h4.paragraph_format.space_after = Pt(8), Pt(4)
    r = h4.add_run("4. Implementation Roadmap & Governance Matrix")
    r.font.size, r.font.bold, r.font.color.rgb = Pt(12), True, NAVY

    tb_rm = doc.add_table(rows=5, cols=5)
    tb_rm.alignment = WD_TABLE_ALIGNMENT.CENTER
    rm_widths = [Inches(1.8), Inches(1.1), Inches(1.2), Inches(1.4), Inches(1.3)]
    rm_headers = [
        "Action Item",
        "Timeframe",
        "Lead Role",
        "Key Deliverable",
        "Success Metric",
    ]
    for i, h in enumerate(rm_headers):
        cell = tb_rm.cell(0, i)
        cell.width = rm_widths[i]
        set_cell_background(cell, "1F497D")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.bold, r.font.size, r.font.color.rgb = (
            True,
            Pt(8.5),
            RGBColor(255, 255, 255),
        )

    rm_data = [
        (
            "Pen Sweep & Re-Tagging",
            "Days 1–2",
            "Farm Supervisor",
            "Updated Physical Tag List",
            "100% pen tag count matched",
        ),
        (
            "Duplicate Tag 101 Fix",
            "Day 2",
            "Data Analyst",
            "Cleaned Master Excel File",
            "0 duplicate tag records",
        ),
        (
            "Feed Ration Calibration",
            "Day 3",
            "Nutritionist / Mgr",
            "Revised Daily Feed Formula",
            "Rations scaled to 133 head",
        ),
        (
            "Maternity Pen Setup",
            "Days 4–5",
            "Flock Manager",
            "30 Pregnant Ewes Grouped",
            "Maternity pens prepped",
        ),
    ]
    for r_idx, data in enumerate(rm_data, 1):
        for c_idx, val in enumerate(data):
            cell = tb_rm.cell(r_idx, c_idx)
            cell.width = rm_widths[c_idx]
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
            if c_idx == 0:
                r.font.bold = True

    doc.save(filename)
    print(f"Successfully generated Word document: {filename}")


def create_report_2_pdf(filename="Herd_Inventory_Audit_and_Strategic_Action_Plan.pdf"):
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
    RED = colors.HexColor("#C00000")
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
    pillar_title_style = ParagraphStyle(
        "PillarTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=NAVY,
        spaceBefore=3,
        spaceAfter=1,
    )
    pillar_desc_style = ParagraphStyle(
        "PillarDesc",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=DARK,
        spaceAfter=3,
        leftIndent=8,
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
        Paragraph("HERD INVENTORY AUDIT & STRATEGIC ACTION PLAN", title_style),
        Paragraph(
            "Inventory Reconciliation, Tag Traceability Protocol & Pre-Feed Transition Strategy",
            subtitle_style,
        ),
        HRFlowable(
            width="100%", thickness=1.2, color=NAVY, spaceBefore=0, spaceAfter=6
        ),
    ]

    banner_data = [
        [
            Paragraph("<b>Audit Date:</b> September 30, 2026", tbl_cell),
            Paragraph(
                "<b>Reconciliation Target:</b> 38 Uncounted Active Head", tbl_cell
            ),
            Paragraph(
                "<b>Primary Goal:</b> 100% Barn Verification & Feed Alignment", tbl_cell
            ),
        ]
    ]
    banner_table = Table(banner_data, colWidths=[2.3 * inch, 2.5 * inch, 2.7 * inch])
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

    story.append(Paragraph("1. Executive Summary & Audit Mandate", h1_style))
    story.append(
        Paragraph(
            "Following the master stock take evaluation on September 22, 2026, this audit focuses directly on reconciling the inventory gap between system active records (171 head) and physically verified animals (133 head). Eliminating the 38 uncounted active head (22.2% of active system inventory) is a prerequisite before finalizing daily feed consumption budgeting and biological asset valuations.",
            body_style,
        )
    )

    aud_data = [
        [
            Paragraph("Audit Area", tbl_hdr),
            Paragraph("Discrepancy Volume", tbl_hdr),
            Paragraph("Risk Level", tbl_hdr),
            Paragraph("Root Cause & Impact Summary", tbl_hdr),
        ],
        [
            Paragraph("Uncounted Active Head", tbl_cell_bold),
            Paragraph("38 head", tbl_cell_ctr),
            Paragraph("<font color='#C00000'><b>HIGH</b></font>", tbl_cell_ctr),
            Paragraph(
                "20 home-born lambs + 9 purchased + 4 opening + 5 lost tags missing physical tag count.",
                tbl_cell,
            ),
        ],
        [
            Paragraph("Duplicate Tag Entry", tbl_cell_bold),
            Paragraph("1 tag (Tag 101)", tbl_cell_ctr),
            Paragraph("MEDIUM", tbl_cell_ctr),
            Paragraph(
                "Tag 101 logged twice: Row 67 (Ewe/Opening) vs Row 68 (Pregnant/Purchased).",
                tbl_cell,
            ),
        ],
        [
            Paragraph("Lost Ear Tags", tbl_cell_bold),
            Paragraph("5 head", tbl_cell_ctr),
            Paragraph("MEDIUM", tbl_cell_ctr),
            Paragraph(
                "Tags 190, 359, 360, 385, 386 shed in pens during grazing/feeding; missing visual ID.",
                tbl_cell,
            ),
        ],
        [
            Paragraph("Re-tagged Off-Take", tbl_cell_bold),
            Paragraph("4 head", tbl_cell_ctr),
            Paragraph("LOW", tbl_cell_ctr),
            Paragraph(
                "Old Tag # 180, 29, 30, 36 harvested; re-tagging cross-reference requires log closure.",
                tbl_cell,
            ),
        ],
    ]
    aud_table = Table(
        aud_data, colWidths=[1.8 * inch, 1.3 * inch, 1.0 * inch, 3.4 * inch]
    )
    aud_table.setStyle(
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
    story.append(aud_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("2. Uncounted Active Head Deep-Dive Analysis", h1_style))
    story.append(
        Paragraph(
            "A detailed breakdown of the 38 uncounted active animals by origin cohort and age/category highlights where inventory verification broke down during the September stock take:",
            body_style,
        )
    )

    unc_data = [
        [
            Paragraph("Cohort Origin", tbl_hdr),
            Paragraph("(Small) Male", tbl_hdr),
            Paragraph("Ewes", tbl_hdr),
            Paragraph("(Small) Female", tbl_hdr),
            Paragraph("Pregnant", tbl_hdr),
            Paragraph("Total Uncounted", tbl_hdr),
        ],
        [
            Paragraph("Home Production (Our Production)", tbl_cell_bold),
            Paragraph("13 head", tbl_cell_ctr),
            Paragraph("0 head", tbl_cell_ctr),
            Paragraph("7 head", tbl_cell_ctr),
            Paragraph("0 head", tbl_cell_ctr),
            Paragraph("20 head (52.6%)", tbl_cell_ctr_b),
        ],
        [
            Paragraph("Purchased Stock", tbl_cell_bold),
            Paragraph("0 head", tbl_cell_ctr),
            Paragraph("5 head", tbl_cell_ctr),
            Paragraph("0 head", tbl_cell_ctr),
            Paragraph("3 head", tbl_cell_ctr),
            Paragraph("9 head (23.7%)", tbl_cell_ctr_b),
        ],
        [
            Paragraph("Lost Tag # Group", tbl_cell_bold),
            Paragraph("4 head", tbl_cell_ctr),
            Paragraph("1 head", tbl_cell_ctr),
            Paragraph("0 head", tbl_cell_ctr),
            Paragraph("0 head", tbl_cell_ctr),
            Paragraph("5 head (13.2%)", tbl_cell_ctr_b),
        ],
        [
            Paragraph("Opening Stock Group", tbl_cell_bold),
            Paragraph("0 head", tbl_cell_ctr),
            Paragraph("4 head", tbl_cell_ctr),
            Paragraph("0 head", tbl_cell_ctr),
            Paragraph("0 head", tbl_cell_ctr),
            Paragraph("4 head (10.5%)", tbl_cell_ctr_b),
        ],
        [
            Paragraph("Total Uncounted Active", tbl_cell_bold),
            Paragraph("17 head (44.7%)", tbl_cell_ctr_b),
            Paragraph("10 head (26.3%)", tbl_cell_ctr_b),
            Paragraph("7 head (18.4%)", tbl_cell_ctr_b),
            Paragraph("3 head (7.9%)", tbl_cell_ctr_b),
            Paragraph("38 head (100%)", tbl_cell_ctr_b),
        ],
    ]
    unc_table = Table(
        unc_data,
        colWidths=[
            2.2 * inch,
            1.05 * inch,
            1.05 * inch,
            1.05 * inch,
            1.05 * inch,
            1.1 * inch,
        ],
    )
    unc_table.setStyle(
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
    story.append(unc_table)
    story.append(Spacer(1, 6))

    story.append(
        Paragraph(
            "3. Strategic 4-Pillar Action Plan",
            ParagraphStyle("H1Red", parent=h1_style, textColor=RED),
        )
    )
    pillars = [
        (
            "PILLAR 1: Physical Pen Audit & Tagging Sweep (48-Hour Field Action)",
            "• Conduct a full physical pen sweep targeting the 17 missing male lambs and 7 female lambs in young stock pens.<br/>• Re-tag un-identified animals using new double-locking tags and log re-tag IDs immediately.",
        ),
        (
            "PILLAR 2: Tag Traceability & Duplicate Resolution SOP",
            "• Resolve Duplicate Tag 101: Verify physical tag 101 in pen (Row 68 Purchased Pregnant Ewe vs Row 67 Opening Ewe) and update sheet.<br/>• Close re-tag logs for harvested stock (Old Tag # 180, 29, 30, 36) to prevent phantom active listings.",
        ),
        (
            "PILLAR 3: Feed Budget Calibration (Pre-Feed Transition Rule)",
            "• Calibrate daily feed ration formulas strictly to the 133 physically verified active animals (√).<br/>• Do NOT allocate feed rations for the 38 uncounted animals until physical presence is confirmed in pen.",
        ),
        (
            "PILLAR 4: Breeding Pen Allocation & Fall Lambing Preparation",
            "• Confirm location of the 30 pregnant ewes (91.2% verified) and assign them to maternity pens for fall lambing.<br/>• Allocate permanent sires (Tags 105, 106) to active breeding groups.",
        ),
    ]
    for title, desc in pillars:
        story.append(Paragraph(title, pillar_title_style))
        story.append(Paragraph(desc, pillar_desc_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("4. Implementation Roadmap & Governance Matrix", h1_style))
    rm_data = [
        [
            Paragraph("Action Item", tbl_hdr),
            Paragraph("Timeframe", tbl_hdr),
            Paragraph("Lead Role", tbl_hdr),
            Paragraph("Key Deliverable", tbl_hdr),
            Paragraph("Success Metric", tbl_hdr),
        ],
        [
            Paragraph("Pen Sweep & Re-Tagging", tbl_cell_bold),
            Paragraph("Days 1–2", tbl_cell_ctr),
            Paragraph("Farm Supervisor", tbl_cell_ctr),
            Paragraph("Updated Physical Tag List", tbl_cell),
            Paragraph("100% pen tag count matched", tbl_cell),
        ],
        [
            Paragraph("Duplicate Tag 101 Fix", tbl_cell_bold),
            Paragraph("Day 2", tbl_cell_ctr),
            Paragraph("Data Analyst", tbl_cell_ctr),
            Paragraph("Cleaned Master Excel File", tbl_cell),
            Paragraph("0 duplicate tag records", tbl_cell),
        ],
        [
            Paragraph("Feed Ration Calibration", tbl_cell_bold),
            Paragraph("Day 3", tbl_cell_ctr),
            Paragraph("Nutritionist / Mgr", tbl_cell_ctr),
            Paragraph("Revised Daily Feed Formula", tbl_cell),
            Paragraph("Rations scaled to 133 head", tbl_cell),
        ],
        [
            Paragraph("Maternity Pen Setup", tbl_cell_bold),
            Paragraph("Days 4–5", tbl_cell_ctr),
            Paragraph("Flock Manager", tbl_cell_ctr),
            Paragraph("30 Pregnant Ewes Grouped", tbl_cell),
            Paragraph("Maternity pens prepped", tbl_cell),
        ],
    ]
    rm_table = Table(
        rm_data, colWidths=[1.8 * inch, 1.1 * inch, 1.3 * inch, 1.7 * inch, 1.6 * inch]
    )
    rm_table.setStyle(
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
    story.append(rm_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF document: {filename}")


if __name__ == "__main__":
    create_report_2_docx()
    create_report_2_pdf()
