#!/usr/bin/env python3
"""
Generate a premium academic-style PDF from the Private Credit & AI Infrastructure thesis.
Harvard PhD office aesthetic: clean typography, strong hierarchy, elegant tables, professional feel.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable, Frame, PageTemplate,
    BaseDocTemplate, NextPageTemplate, Flowable
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfgen import canvas
from reportlab.lib.fonts import addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ─── COLOR PALETTE (Dark, sophisticated academic) ────────────────────────────
NAVY       = HexColor("#0D1B2A")
DARK_BLUE  = HexColor("#1B2A4A")
MED_BLUE   = HexColor("#2C3E6B")
ACCENT     = HexColor("#8B1A1A")   # Deep crimson -- Harvard red
ACCENT2    = HexColor("#B8860B")   # Dark goldenrod for highlights
LIGHT_GRAY = HexColor("#F5F5F0")
MED_GRAY   = HexColor("#E8E6E0")
DARK_GRAY  = HexColor("#4A4A4A")
TEXT_COLOR  = HexColor("#1A1A1A")
MUTED      = HexColor("#6B6B6B")
TABLE_HEAD = HexColor("#1B2A4A")
TABLE_ALT  = HexColor("#F0EDE6")
RULE_COLOR = HexColor("#C0B8A8")
WHITE      = HexColor("#FFFFFF")

PAGE_W, PAGE_H = letter
LEFT_MARGIN = 1.0 * inch
RIGHT_MARGIN = 1.0 * inch
TOP_MARGIN = 0.85 * inch
BOTTOM_MARGIN = 0.9 * inch
CONTENT_W = PAGE_W - LEFT_MARGIN - RIGHT_MARGIN

# ─── CUSTOM FLOWABLES ────────────────────────────────────────────────────────

class ThinRule(Flowable):
    """A thin horizontal rule."""
    def __init__(self, width, color=RULE_COLOR, thickness=0.5):
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = 6

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 3, self.width, 3)


class ThickRule(Flowable):
    """A thick horizontal rule for major sections."""
    def __init__(self, width, color=NAVY, thickness=2):
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = 10

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 5, self.width, 5)


class AccentBar(Flowable):
    """A small accent bar for visual emphasis."""
    def __init__(self, width=40, color=ACCENT, thickness=3):
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = 8

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 4, self.width, 4)


class CalloutBox(Flowable):
    """A highlighted callout box with left accent bar."""
    def __init__(self, text, width, style, bg_color=LIGHT_GRAY, accent_color=ACCENT):
        Flowable.__init__(self)
        self.text = text
        self.box_width = width
        self.style = style
        self.bg_color = bg_color
        self.accent_color = accent_color
        # Calculate height
        p = Paragraph(text, style)
        w, h = p.wrap(width - 24, 1000)
        self.box_height = h + 20

    def wrap(self, availWidth, availHeight):
        return self.box_width, self.box_height

    def draw(self):
        # Background
        self.canv.setFillColor(self.bg_color)
        self.canv.roundRect(0, 0, self.box_width, self.box_height, 3, fill=1, stroke=0)
        # Left accent bar
        self.canv.setFillColor(self.accent_color)
        self.canv.rect(0, 0, 4, self.box_height, fill=1, stroke=0)
        # Text
        p = Paragraph(self.text, self.style)
        p.wrap(self.box_width - 24, self.box_height)
        p.drawOn(self.canv, 16, 10)


# ─── STYLES ──────────────────────────────────────────────────────────────────

def build_styles():
    styles = {}

    styles['title'] = ParagraphStyle(
        'Title',
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=28,
        textColor=NAVY,
        spaceAfter=4,
        alignment=TA_LEFT,
    )

    styles['subtitle'] = ParagraphStyle(
        'Subtitle',
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=MUTED,
        spaceAfter=2,
        alignment=TA_LEFT,
    )

    styles['thesis_line'] = ParagraphStyle(
        'ThesisLine',
        fontName='Helvetica-Oblique',
        fontSize=12,
        leading=18,
        textColor=DARK_BLUE,
        spaceBefore=8,
        spaceAfter=4,
        alignment=TA_LEFT,
        leftIndent=0,
    )

    styles['h1'] = ParagraphStyle(
        'H1',
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=22,
        textColor=NAVY,
        spaceBefore=18,
        spaceAfter=6,
        alignment=TA_LEFT,
    )

    styles['h2'] = ParagraphStyle(
        'H2',
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=17,
        textColor=DARK_BLUE,
        spaceBefore=14,
        spaceAfter=4,
        alignment=TA_LEFT,
    )

    styles['h3'] = ParagraphStyle(
        'H3',
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=MED_BLUE,
        spaceBefore=10,
        spaceAfter=3,
        alignment=TA_LEFT,
    )

    styles['body'] = ParagraphStyle(
        'Body',
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=TEXT_COLOR,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
    )

    styles['body_bold'] = ParagraphStyle(
        'BodyBold',
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=14,
        textColor=TEXT_COLOR,
        spaceAfter=6,
        alignment=TA_LEFT,
    )

    styles['bullet'] = ParagraphStyle(
        'Bullet',
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_COLOR,
        spaceAfter=3,
        leftIndent=16,
        bulletIndent=4,
        alignment=TA_LEFT,
    )

    styles['sub_bullet'] = ParagraphStyle(
        'SubBullet',
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=DARK_GRAY,
        spaceAfter=2,
        leftIndent=32,
        bulletIndent=20,
        alignment=TA_LEFT,
    )

    styles['callout'] = ParagraphStyle(
        'Callout',
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=TEXT_COLOR,
        alignment=TA_LEFT,
    )

    styles['callout_bold'] = ParagraphStyle(
        'CalloutBold',
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=14,
        textColor=ACCENT,
        alignment=TA_LEFT,
    )

    styles['table_header'] = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=WHITE,
        alignment=TA_LEFT,
    )

    styles['table_cell'] = ParagraphStyle(
        'TableCell',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=TEXT_COLOR,
        alignment=TA_LEFT,
    )

    styles['table_cell_bold'] = ParagraphStyle(
        'TableCellBold',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=TEXT_COLOR,
        alignment=TA_LEFT,
    )

    styles['table_cell_center'] = ParagraphStyle(
        'TableCellCenter',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=TEXT_COLOR,
        alignment=TA_CENTER,
    )

    styles['code_label'] = ParagraphStyle(
        'CodeLabel',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=MUTED,
        spaceBefore=2,
        spaceAfter=2,
        alignment=TA_LEFT,
    )

    styles['quote'] = ParagraphStyle(
        'Quote',
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=DARK_GRAY,
        leftIndent=20,
        rightIndent=20,
        spaceBefore=4,
        spaceAfter=4,
        alignment=TA_LEFT,
    )

    styles['source_header'] = ParagraphStyle(
        'SourceHeader',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=DARK_BLUE,
        spaceBefore=6,
        spaceAfter=2,
        alignment=TA_LEFT,
    )

    styles['source_item'] = ParagraphStyle(
        'SourceItem',
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=MUTED,
        spaceAfter=1,
        leftIndent=8,
        alignment=TA_LEFT,
    )

    styles['footer'] = ParagraphStyle(
        'Footer',
        fontName='Helvetica',
        fontSize=7.5,
        leading=9,
        textColor=MUTED,
        alignment=TA_CENTER,
    )

    styles['toc_h1'] = ParagraphStyle(
        'TOCH1',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=18,
        textColor=NAVY,
        leftIndent=0,
    )

    styles['toc_h2'] = ParagraphStyle(
        'TOCH2',
        fontName='Helvetica',
        fontSize=9,
        leading=15,
        textColor=TEXT_COLOR,
        leftIndent=16,
    )

    return styles


# ─── PAGE TEMPLATE ───────────────────────────────────────────────────────────

class DocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        BaseDocTemplate.__init__(self, filename, **kwargs)
        self.page_count = 0

        frame = Frame(
            LEFT_MARGIN, BOTTOM_MARGIN,
            CONTENT_W, PAGE_H - TOP_MARGIN - BOTTOM_MARGIN,
            id='normal'
        )

        # Cover page template (no header/footer)
        cover_template = PageTemplate(
            id='Cover',
            frames=[frame],
            onPage=self._cover_page
        )

        # Normal page template
        normal_template = PageTemplate(
            id='Normal',
            frames=[frame],
            onPage=self._normal_page
        )

        self.addPageTemplates([cover_template, normal_template])

    def _cover_page(self, canvas, doc):
        """Minimal cover page -- no header or footer."""
        canvas.saveState()
        canvas.restoreState()

    def _normal_page(self, canvas, doc):
        """Header rule + page number footer."""
        canvas.saveState()

        # Top rule
        canvas.setStrokeColor(NAVY)
        canvas.setLineWidth(1.5)
        canvas.line(LEFT_MARGIN, PAGE_H - TOP_MARGIN + 12,
                    PAGE_W - RIGHT_MARGIN, PAGE_H - TOP_MARGIN + 12)

        # Thin rule under header
        canvas.setStrokeColor(RULE_COLOR)
        canvas.setLineWidth(0.5)
        canvas.line(LEFT_MARGIN, PAGE_H - TOP_MARGIN + 8,
                    PAGE_W - RIGHT_MARGIN, PAGE_H - TOP_MARGIN + 8)

        # Header text
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(LEFT_MARGIN, PAGE_H - TOP_MARGIN + 16,
                          "Private Credit & AI Infrastructure: Trading Thesis & Risk Analysis")
        canvas.drawRightString(PAGE_W - RIGHT_MARGIN, PAGE_H - TOP_MARGIN + 16,
                               "March 2026")

        # Bottom rule
        canvas.setStrokeColor(RULE_COLOR)
        canvas.setLineWidth(0.5)
        canvas.line(LEFT_MARGIN, BOTTOM_MARGIN - 8,
                    PAGE_W - RIGHT_MARGIN, BOTTOM_MARGIN - 8)

        # Page number
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(MUTED)
        page_num = canvas.getPageNumber()
        canvas.drawCentredString(PAGE_W / 2, BOTTOM_MARGIN - 22, str(page_num))

        # Classification
        canvas.setFont('Helvetica', 6.5)
        canvas.setFillColor(HexColor("#999999"))
        canvas.drawRightString(PAGE_W - RIGHT_MARGIN, BOTTOM_MARGIN - 22,
                               "Confidential -- For Research Purposes Only")

        canvas.restoreState()


# ─── TABLE BUILDERS ──────────────────────────────────────────────────────────

def make_data_table(headers, rows, col_widths=None, styles_dict=None):
    """Create a beautifully styled data table."""
    s = styles_dict

    # Build header row
    header_cells = [Paragraph(h, s['table_header']) for h in headers]

    # Build data rows
    data_rows = []
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            if i == 0:
                cells.append(Paragraph(str(cell), s['table_cell_bold']))
            else:
                cells.append(Paragraph(str(cell), s['table_cell']))
        data_rows.append(cells)

    table_data = [header_cells] + data_rows

    if col_widths is None:
        col_widths = [CONTENT_W / len(headers)] * len(headers)

    t = Table(table_data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEAD),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),

        # Cell styling
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8.5),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_COLOR),

        # Alignment
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),

        # Grid
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, NAVY),
        ('LINEBELOW', (0, -1), (-1, -1), 1, NAVY),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, RULE_COLOR),
    ]

    # Alternating row colors
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), TABLE_ALT))

    t.setStyle(TableStyle(style_cmds))
    return t


def make_two_column_table(left_header, right_header, left_items, right_items, styles_dict):
    """Winners/Losers style two-column table."""
    s = styles_dict
    max_rows = max(len(left_items), len(right_items))

    header = [Paragraph(left_header, s['table_header']),
              Paragraph(right_header, s['table_header'])]

    data = [header]
    for i in range(max_rows):
        left = Paragraph(left_items[i], s['table_cell']) if i < len(left_items) else Paragraph('', s['table_cell'])
        right = Paragraph(right_items[i], s['table_cell']) if i < len(right_items) else Paragraph('', s['table_cell'])
        data.append([left, right])

    col_w = CONTENT_W / 2
    t = Table(data, colWidths=[col_w, col_w], repeatRows=1)

    style_cmds = [
        ('BACKGROUND', (0, 0), (0, 0), HexColor("#1B5E20")),  # Green header
        ('BACKGROUND', (1, 0), (1, 0), ACCENT),  # Red header
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, NAVY),
        ('LINEBELOW', (0, -1), (-1, -1), 1, NAVY),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, RULE_COLOR),
        ('LINEBEFORE', (1, 0), (1, -1), 0.5, RULE_COLOR),
    ]

    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), TABLE_ALT))

    t.setStyle(TableStyle(style_cmds))
    return t


def make_scenario_matrix(styles_dict):
    """Create the 2x2 scenario matrix."""
    s = styles_dict

    data = [
        ['', Paragraph('<b>CREDIT HOLDS</b>', s['table_header']),
         Paragraph('<b>CREDIT CRACKS</b>', s['table_header'])],
        [Paragraph('<b>DC PERMITS<br/>CLEAR</b>', s['table_header']),
         Paragraph('Base case. Buildout on time. GPU prices fall. GDP boost.', s['table_cell']),
         Paragraph('Moderate stress. Funded projects OK. Some delays from refi friction.', s['table_cell'])],
        [Paragraph('<b>DC PERMITS<br/>BLOCKED</b>', s['table_header']),
         Paragraph('Current reality. Buildout delayed. GPU prices stay high but credit market OK.', s['table_cell']),
         Paragraph('<b>WORST CASE.</b> Can\'t build AND can\'t fund. GPU crisis. GDP miss. Alt manager stocks crater.', s['table_cell_bold'])],
    ]

    col_w = [CONTENT_W * 0.2, CONTENT_W * 0.4, CONTENT_W * 0.4]
    t = Table(data, colWidths=col_w)

    t.setStyle(TableStyle([
        # Top-left empty cell
        ('BACKGROUND', (0, 0), (0, 0), TABLE_HEAD),
        # Headers
        ('BACKGROUND', (1, 0), (2, 0), TABLE_HEAD),
        ('BACKGROUND', (0, 1), (0, 2), TABLE_HEAD),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('TEXTCOLOR', (0, 1), (0, -1), WHITE),
        # Cells
        ('BACKGROUND', (1, 1), (1, 1), HexColor("#E8F5E9")),  # Green tint
        ('BACKGROUND', (2, 1), (2, 1), HexColor("#FFF8E1")),  # Yellow tint
        ('BACKGROUND', (1, 2), (1, 2), HexColor("#FFF8E1")),  # Yellow tint
        ('BACKGROUND', (2, 2), (2, 2), HexColor("#FFEBEE")),  # Red tint
        # Padding
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, NAVY),
    ]))
    return t


def make_timeline_table(rows, styles_dict):
    """Create a timeline/cascade table with status indicators."""
    s = styles_dict

    header = [Paragraph('#', s['table_header']),
              Paragraph('Status', s['table_header']),
              Paragraph('Event', s['table_header']),
              Paragraph('Timing', s['table_header'])]

    data = [header]
    for row in rows:
        cells = [
            Paragraph(str(row[0]), s['table_cell_bold']),
            Paragraph(str(row[1]), s['table_cell']),
            Paragraph(str(row[2]), s['table_cell']),
            Paragraph(str(row[3]), s['table_cell']),
        ]
        data.append(cells)

    col_w = [CONTENT_W * 0.06, CONTENT_W * 0.13, CONTENT_W * 0.55, CONTENT_W * 0.26]
    t = Table(data, colWidths=col_w, repeatRows=1)

    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEAD),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, NAVY),
        ('LINEBELOW', (0, -1), (-1, -1), 1, NAVY),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, RULE_COLOR),
    ]

    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), TABLE_ALT))
        # Color code status
        status_text = rows[i-1][1] if i-1 < len(rows) else ""
        if 'DONE' in status_text or 'Complete' in status_text:
            style_cmds.append(('TEXTCOLOR', (1, i), (1, i), HexColor("#1B5E20")))
        elif 'NOW' in status_text or 'Active' in status_text:
            style_cmds.append(('TEXTCOLOR', (1, i), (1, i), ACCENT))
        elif 'Pending' in status_text:
            style_cmds.append(('TEXTCOLOR', (1, i), (1, i), MUTED))

    t.setStyle(TableStyle(style_cmds))
    return t


# ─── BUILD DOCUMENT ──────────────────────────────────────────────────────────

def build_document():
    output_path = "/home/user/workspace/private-credit-infrastructure-thesis.pdf"
    doc = DocTemplate(
        output_path,
        pagesize=letter,
        title="Private Credit & AI Infrastructure: Trading Thesis & Risk Analysis",
        author="Perplexity Computer",
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
    )

    s = build_styles()
    story = []

    # ═══════════════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 1.8 * inch))
    story.append(ThickRule(CONTENT_W, NAVY, 3))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Private Credit &amp; AI Infrastructure",
        s['title']
    ))
    story.append(Paragraph(
        "Trading Thesis &amp; Risk Analysis",
        ParagraphStyle('TitleSub', parent=s['title'], fontSize=18, leading=24, textColor=MED_BLUE)
    ))
    story.append(Spacer(1, 8))
    story.append(ThinRule(CONTENT_W * 0.4, ACCENT, 1.5))
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        "Research Date: March 2, 2026 &nbsp;&nbsp;|&nbsp;&nbsp; Analysis Window: Last 30 Days",
        s['subtitle']
    ))
    story.append(Paragraph(
        "Companion to: AI Data Center Infrastructure Trading Thesis",
        ParagraphStyle('SubRef', parent=s['subtitle'], fontSize=9.5, textColor=HexColor("#888888"))
    ))
    story.append(Spacer(1, 30))
    story.append(ThickRule(CONTENT_W, NAVY, 1.5))
    story.append(Spacer(1, 20))

    # Thesis box
    story.append(CalloutBox(
        '<b>THE THESIS:</b> Private credit is the $3 trillion funding engine behind the $5 trillion '
        'AI data center buildout -- and it is showing cracks for the first time, just as the capital '
        'demands are accelerating.',
        CONTENT_W, s['callout'], LIGHT_GRAY, ACCENT
    ))
    story.append(Spacer(1, 30))

    # Mini TOC on cover
    toc_style = ParagraphStyle('MiniTOC', fontName='Helvetica', fontSize=9, leading=16,
                                textColor=DARK_GRAY, leftIndent=4)
    toc_header_style = ParagraphStyle('TOCHead', fontName='Helvetica-Bold', fontSize=10,
                                       leading=14, textColor=NAVY, spaceAfter=8)
    story.append(Paragraph("Contents", toc_header_style))
    story.append(ThinRule(CONTENT_W * 0.15, ACCENT, 1))
    story.append(Spacer(1, 6))

    toc_items = [
        "1. The Capital Stack: How the DC Buildout Gets Funded",
        "2. The Blue Owl Detonation (The Catalyst Event)",
        "3. The Shadow Default Problem",
        "4. The Maturity Wall: $12.7B Coming Due",
        "5. The Key Players and Their Exposure",
        "6. Jamie Dimon's 'Cockroaches' -- Howard Marks's 'Coal Mine'",
        "7. How This Connects to the DC Infrastructure Thesis",
        "8. Kalshi-Tradeable Angles",
        "9. Event Calendar: Known Catalysts",
        "10. Key Metrics to Monitor",
        "11. The Money Map: Who Wins, Who Loses",
        "12. The Contrarian Case",
    ]
    for item in toc_items:
        story.append(Paragraph(item, toc_style))

    story.append(NextPageTemplate('Normal'))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1: THE CAPITAL STACK
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("1. The Capital Stack: How the DC Buildout Gets Funded", s['h1']))
    story.append(AccentBar())
    story.append(Spacer(1, 8))

    # Capital requirements table
    story.append(Paragraph("AI Data Center Capital Requirements (2026--2030)", s['h2']))
    story.append(Spacer(1, 4))

    cap_table = make_data_table(
        headers=['Source', 'Amount', 'Notes'],
        rows=[
            ['Total Needed', '$5.0T', 'JPMorgan estimate'],
            ['Hyperscaler Cash', '~$2.5T', 'Equity, retained earnings'],
            ['Public Bond Markets', '~$1.5T', 'Investment-grade issuance'],
            ['Private Credit', '~$750B', 'THE LAYER UNDER STRESS'],
            ['ABS / Securitization', '~$250B', 'Structured products'],
        ],
        col_widths=[CONTENT_W * 0.3, CONTENT_W * 0.2, CONTENT_W * 0.5],
        styles_dict=s
    )
    story.append(cap_table)
    story.append(Spacer(1, 6))

    story.append(CalloutBox(
        '<b>2026 Issuance:</b> Morgan Stanley expects $250--300B from hyperscalers + JVs. '
        'JPMorgan expects ~$20B in AI-related leveraged finance. Over $200B already outstanding '
        'in AI-related private credit loans.',
        CONTENT_W, s['callout'], LIGHT_GRAY, ACCENT2
    ))
    story.append(Spacer(1, 10))

    # Financing evolution
    story.append(Paragraph("The Financing Evolution", s['h2']))
    story.append(Spacer(1, 4))

    evo_table = make_data_table(
        headers=['Period', 'Regime', 'Characteristics'],
        rows=[
            ['2020--2022', 'Equity-Funded', 'Hyperscalers paid cash. Low rates. Easy money. No stress.'],
            ['2023--2024', 'Shift to Debt', 'Scale demands exceeded cash. Private credit enters aggressively. Loose covenants. Aggressive EBITDA adjustments.'],
            ['2025--2026', 'Debt-Dominant', 'Complex structures emerge. Private credit + ABS + hyperscale JVs. $3T market size. First real stress test. Blue Owl detonates.'],
        ],
        col_widths=[CONTENT_W * 0.17, CONTENT_W * 0.18, CONTENT_W * 0.65],
        styles_dict=s
    )
    story.append(evo_table)
    story.append(Spacer(1, 6))

    # Arrow indicator
    story.append(Paragraph(
        '<font color="#8B1A1A"><b>WE ARE HERE</b></font> -- 2025--2026: Debt-dominant. First real stress test.',
        s['body_bold']
    ))
    story.append(Spacer(1, 10))

    # Who's Lending What
    story.append(Paragraph("Private Credit Exposure to DC/AI Infrastructure", s['h2']))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Direct DC Lending:</b>", s['body_bold']))
    for item in ['Infrastructure debt (land, construction, power)',
                 'Real estate debt (DC facilities as collateral)',
                 'Corporate direct lending (DC operators, builders)',
                 'Asset-based finance (equipment, servers, cooling)']:
        story.append(Paragraph(f'<bullet>&bull;</bullet> {item}', s['bullet']))

    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Indirect DC Exposure (the hidden risk):</b>", s['body_bold']))
    for item in ['Software/SaaS companies (25% of BDC portfolios) -- these serve DC customers; AI disrupts them',
                 'Power/utility project finance',
                 'Fiber/connectivity infrastructure',
                 'Construction/engineering firms']:
        story.append(Paragraph(f'<bullet>&bull;</bullet> {item}', s['bullet']))

    story.append(Spacer(1, 8))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2: BLUE OWL DETONATION
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("2. The Blue Owl Detonation (The Catalyst Event)", s['h1']))
    story.append(AccentBar())
    story.append(Spacer(1, 8))

    story.append(Paragraph("What Happened (February 19, 2026)", s['h2']))
    story.append(Spacer(1, 4))

    # Blue Owl Timeline
    owl_table = make_data_table(
        headers=['Date', 'Event'],
        rows=[
            ['Feb 19', 'Permanently halted quarterly redemptions at OBDC II. Executed $1.4B fire sale of assets. Offered one-time 30% NAV return, then locked the door. Tech vehicle OTIC: redemption requests hit ~15% of NAV.'],
            ['Feb 19', 'BDC sector trades down 3--5% in sympathy. Blackstone, Apollo tumble >5%.'],
            ['Feb 20', 'CNBC: "Canary in the coal mine."'],
            ['Feb 22', 'Bloomberg: "Blue Owl Redemptions Halt Intensifies Private Credit Fears." Fortune: "Shadow default rate is increasing."'],
            ['Feb 24', 'CNBC: "From Dimon\'s cockroaches to the Blue Owl freeze." UBS: worst-case defaults could reach 15%.'],
            ['Feb 26', 'Bloomberg: "Private Credit\'s Great Divide: Imminent Crisis or \'No Big Deal\'."'],
            ['Feb 27', 'Goldman: "We\'re unlike peers hit by redemptions." Reuters: "Blue Owl turmoil adds strain to $2T sector."'],
        ],
        col_widths=[CONTENT_W * 0.12, CONTENT_W * 0.88],
        styles_dict=s
    )
    story.append(owl_table)
    story.append(Spacer(1, 10))

    # Liquidity mismatch
    story.append(Paragraph("The Liquidity Mismatch That Killed It", s['h2']))
    story.append(Spacer(1, 4))

    mismatch_table = make_data_table(
        headers=['Asset Side', 'Liability Side'],
        rows=[
            ['Private loans', 'Retail investors'],
            ['3--7 year duration', 'Want quarterly liquidity'],
            ['Illiquid, no market', 'Expect to redeem at NAV'],
            ['Mark-to-model', 'Expect mark-to-market pricing'],
            ['Concentrated in tech', 'Diversification assumption'],
        ],
        col_widths=[CONTENT_W * 0.5, CONTENT_W * 0.5],
        styles_dict=s
    )
    story.append(mismatch_table)
    story.append(Spacer(1, 6))
    story.append(CalloutBox(
        '<b>When redemptions exceed the 5% gate:</b> fire sale or lock-in. Blue Owl hit BOTH.',
        CONTENT_W, s['callout'], HexColor("#FFEBEE"), ACCENT
    ))
    story.append(Spacer(1, 10))

    # Contagion Map
    story.append(Paragraph("Contagion Map", s['h2']))
    story.append(Spacer(1, 4))

    contagion_table = make_data_table(
        headers=['Ring', 'Scope', 'Impact'],
        rows=[
            ['Ring 1', 'Direct (immediate)', 'OWL stock cratered. OBDC II investors locked out. OTIC redemption requests spiked to 15% NAV.'],
            ['Ring 2', 'Sector (days)', 'BDC sector down 3--5%. BX, APO, ARES, KKR all sold off >5%. Goldman publicly distanced itself.'],
            ['Ring 3', 'Narrative (weeks)', '"Private credit bubble" headlines. Dimon + Howard Marks both warning publicly. UBS raised worst-case default estimate to 15%.'],
            ['Ring 4', 'Structural (months)', '$12.7B BDC maturity wall in 2026. Retail investors pulling from semi-liquid vehicles. Tighter underwriting leads to credit contraction.'],
        ],
        col_widths=[CONTENT_W * 0.10, CONTENT_W * 0.18, CONTENT_W * 0.72],
        styles_dict=s
    )
    story.append(contagion_table)
    story.append(Spacer(1, 10))

    # Reddit signal
    story.append(Paragraph("Market Sentiment (Reddit Signal)", s['h3']))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        '<i>r/stocks (200 upvotes, 55 comments):</i> "That\'s a horrible sign for private credit market. '
        'I hope things don\'t go \'08 like from here." -- "This is why private markets for retail investors '
        'has always been a rotten idea."',
        s['quote']
    ))
    story.append(Paragraph(
        '<i>r/Stocks_Picks (19 upvotes):</i> "The first major domino may have just fallen."',
        s['quote']
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3: SHADOW DEFAULT PROBLEM
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("3. The Shadow Default Problem: What the Numbers Say", s['h1']))
    story.append(AccentBar())
    story.append(Spacer(1, 8))

    story.append(Paragraph("Headline vs. Reality", s['h2']))
    story.append(Spacer(1, 4))

    default_table = make_data_table(
        headers=['Measure', 'Rate', 'Source'],
        rows=[
            ['Headline PC default rate', '<2%', 'What managers show LPs'],
            ['True rate (incl. selective)', '~5%', 'Fortune, Bernstein'],
            ['Leveraged loan default rate', '5.0%', 'Highest since 2008'],
            ['UBS worst-case (AI disruption)', '15%', 'Tail risk, unpriced'],
        ],
        col_widths=[CONTENT_W * 0.38, CONTENT_W * 0.15, CONTENT_W * 0.47],
        styles_dict=s
    )
    story.append(default_table)
    story.append(Spacer(1, 10))

    # PIK section
    story.append(Paragraph("A. Payment-in-Kind (PIK) -- The Silent Killer", s['h2']))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        'Borrower pays interest with MORE DEBT instead of cash. No default recorded. '
        'Loan balance grows. Ability to pay shrinks.',
        s['body']
    ))
    story.append(Spacer(1, 4))

    pik_table = make_data_table(
        headers=['Period', 'PIK Prevalence', 'Significance'],
        rows=[
            ['Q4 2021', '7.0% of deals had PIK', 'Baseline'],
            ['Q3 2025', '10.6% of deals (likely 12--15%)', 'Accelerating'],
            ['BDC Income', '8% of investment income via PIK', 'Cash quality declining'],
            ['"Bad PIK" (Q3 2025)', '57.2% of all PIKs', 'MAJORITY are distress-driven'],
        ],
        col_widths=[CONTENT_W * 0.22, CONTENT_W * 0.35, CONTENT_W * 0.43],
        styles_dict=s
    )
    story.append(pik_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Implications for DC Infrastructure:</b>", s['body_bold']))
    for item in ['DC-adjacent software companies cannot service debt',
                 'Lenders let them PIK instead of forcing default',
                 'Reported default rate stays low while actual credit quality deteriorates',
                 'When PIK loans finally cannot extend -- cliff event']:
        story.append(Paragraph(f'<bullet>&bull;</bullet> {item}', s['bullet']))

    story.append(Spacer(1, 10))

    # Amend-and-extend + selective defaults
    story.append(Paragraph("B. Amend-and-Extend", s['h2']))
    story.append(Paragraph(
        'Borrower cannot pay at maturity -- lender extends the loan, loosens covenants. '
        'No default recorded. Frequency is increasing materially per S&amp;P Global.',
        s['body']
    ))

    story.append(Spacer(1, 6))
    story.append(Paragraph("C. Selective Defaults", s['h2']))
    story.append(Paragraph(
        'Restructure one tranche while keeping others current. Not a "full default," but the '
        'borrower is in distress.',
        s['body']
    ))

    story.append(Spacer(1, 8))
    story.append(CalloutBox(
        '<b>The Distress Iceberg:</b> Reported defaults (&lt;2%) are just the visible tip. '
        'Below the surface: selective defaults, PIK conversions (57% are "bad PIKs"), '
        'amend-and-extend (growing rapidly), covenant waivers, and EBITDA add-backs. '
        'TRUE DISTRESS: ~5%.',
        CONTENT_W, s['callout'], HexColor("#FFF8E1"), ACCENT2
    ))

    story.append(Spacer(1, 8))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 4: MATURITY WALL
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("4. The Maturity Wall: $12.7B Coming Due", s['h1']))
    story.append(AccentBar())
    story.append(Spacer(1, 8))

    story.append(Paragraph("BDC Sector Refinancing Crunch", s['h2']))
    story.append(Spacer(1, 4))

    mat_table = make_data_table(
        headers=['Year', 'Unsecured Debt Maturing', 'YoY Change'],
        rows=[
            ['2025', '$7.3B', '--'],
            ['2026', '$12.7B', '+73%'],
            ['2027', 'TBD', 'Likely higher still'],
        ],
        col_widths=[CONTENT_W * 0.2, CONTENT_W * 0.4, CONTENT_W * 0.4],
        styles_dict=s
    )
    story.append(mat_table)
    story.append(Spacer(1, 8))

    # Refi cost shock
    story.append(Paragraph("Refinancing Cost Shock", s['h2']))
    story.append(Spacer(1, 4))
    refi_table = make_data_table(
        headers=['Metric', 'Value'],
        rows=[
            ['Original rate (2020--2022 vintage)', '4.1% -- 4.7%'],
            ['Current refi rate (2026)', '6.5% -- 7.0%'],
            ['Spread hit', '+250--300bps'],
        ],
        col_widths=[CONTENT_W * 0.55, CONTENT_W * 0.45],
        styles_dict=s
    )
    story.append(refi_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Impact chain:</b>", s['body_bold']))
    for item in ['Managers prioritize refi over new origination',
                 'Less capital for new DC infrastructure deals',
                 'Borrowers who cannot refi -- default or fire sale',
                 'Feedback loop: tighter credit -- more defaults -- tighter credit']:
        story.append(Paragraph(f'<bullet>&bull;</bullet> {item}', s['bullet']))

    story.append(Spacer(1, 10))

    # Software exposure
    story.append(Paragraph("The Software/SaaS Exposure Problem", s['h2']))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        'Software/SaaS represents approximately 25% of some BDC portfolios.',
        s['body']
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>What happened:</b>", s['body_bold']))
    for item in ['Loans underwritten on 30--40% revenue growth assumptions',
                 'AI disruption compresses margins for middleware/tools',
                 'Valuations compressed -- equity cushion eroded',
                 'Cash flows weakening -- PIK triggers activate']:
        story.append(Paragraph(f'<bullet>&bull;</bullet> {item}', s['bullet']))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>The DC connection:</b> Software companies are DC tenants and customers. "
                           "If they cannot pay rent, DC operator revenue drops. DC operators are themselves "
                           "financed by private credit. Credit stress cascades UP the stack: "
                           "tenant default -- operator stress -- lender losses. "
                           "UBS: if AI \"aggressively disrupts\" borrowers -- 15% defaults.", s['body']))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 5: KEY PLAYERS
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("5. The Key Players and Their Exposure", s['h1']))
    story.append(AccentBar())
    story.append(Spacer(1, 8))

    story.append(Paragraph("Private Credit Exposure by Firm", s['h2']))
    story.append(Spacer(1, 4))

    firm_table = make_data_table(
        headers=['Firm', 'Fee-Earning Assets from Credit', 'Base Fees from Credit', 'Total AUM', 'Risk Note'],
        rows=[
            ['Apollo (APO)', '86%', '72%', '$700B+', 'MOST exposed to credit stress'],
            ['Ares (ARES)', '66%', '65%', '$450B+', 'Significant exposure'],
            ['Blue Owl (OWL)', '53%', '61%', '$307B', 'EPICENTER -- already in crisis'],
            ['KKR', '48%', '30%', '$600B+', 'Moderate, diversified'],
            ['Blackstone (BX)', '34%', '25%', '$1.2T+', 'Most diversified; BCRED risk'],
        ],
        col_widths=[CONTENT_W * 0.15, CONTENT_W * 0.17, CONTENT_W * 0.15, CONTENT_W * 0.13, CONTENT_W * 0.40],
        styles_dict=s
    )
    story.append(firm_table)
    story.append(Spacer(1, 8))

    story.append(CalloutBox(
        '<b>BCRED = THE BIG ONE:</b> Largest retail-facing private credit fund. If BCRED gates '
        'like OBDC II -- 10x the blast radius. Blackstone will do everything to prevent this. '
        'But if redemption requests spike, this would be the "Lehman moment" for private credit.',
        CONTENT_W, s['callout'], HexColor("#FFEBEE"), ACCENT
    ))
    story.append(Spacer(1, 10))

    # Bank nexus
    story.append(Paragraph("The Interconnectedness Risk", s['h2']))
    story.append(Spacer(1, 4))

    nexus_table = make_data_table(
        headers=['Metric', '2021', '2026'],
        rows=[
            ['Bank loans to NDFIs (% of total)', '6% (~$660B)', '10% (~$1.1T)'],
        ],
        col_widths=[CONTENT_W * 0.5, CONTENT_W * 0.25, CONTENT_W * 0.25],
        styles_dict=s
    )
    story.append(nexus_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Scenario analysis:</b>", s['body_bold']))
    for item in ['If true default rate = 5%: ~$55B in bank-exposed losses. Not 2008-systemic, but enough for earnings misses.',
                 'If UBS worst case (15% defaults): ~$165B in bank-exposed losses. Gets FSOC attention. Triggers regulatory response.']:
        story.append(Paragraph(f'<bullet>&bull;</bullet> {item}', s['bullet']))

    story.append(Spacer(1, 8))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 6: COCKROACHES / COAL MINE
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("6. Jamie Dimon's 'Cockroaches' / Howard Marks's 'Coal Mine'", s['h1']))
    story.append(AccentBar())
    story.append(Spacer(1, 8))

    story.append(Paragraph("The Warning Timeline", s['h2']))
    story.append(Spacer(1, 4))

    cockroach_table = make_data_table(
        headers=['Date', 'Event', 'Signal'],
        rows=[
            ['Oct 2025', 'Tricolor (subprime auto) + First Brands (parts) -- both bankruptcy, fraud allegations. JPMorgan writes off $170M.', 'Dimon: "When you see one cockroach, there are probably more."'],
            ['Dec 2025', 'DOJ charges Tricolor executives. "Systematic fraud" since 2018.', 'Criminal escalation'],
            ['Feb 2026', 'Blue Owl halts redemptions.', 'Dimon: "I see people doing some dumb things." Compares to pre-2008.'],
            ['Feb 2026', 'Howard Marks (Oaktree) publishes: "Cockroaches in the Coal Mine."', 'Smart money positioned'],
            ['Feb 2026', 'UBS raises worst-case default forecast to 15%.', 'Institutional alarm'],
        ],
        col_widths=[CONTENT_W * 0.12, CONTENT_W * 0.52, CONTENT_W * 0.36],
        styles_dict=s
    )
    story.append(cockroach_table)
    story.append(Spacer(1, 8))

    story.append(CalloutBox(
        '<b>Pattern:</b> Fraud -- Liquidity event -- Contagion pricing -- More fraud surfaces -- '
        'Regulatory response. <b>We are between steps 3 and 4.</b>',
        CONTENT_W, s['callout'], HexColor("#FFF8E1"), ACCENT2
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        'When BOTH Jamie Dimon (JPMorgan) AND Howard Marks (Oaktree) are publicly warning '
        'using the same metaphor -- the smart money is already positioned.',
        ParagraphStyle('EmphBody', parent=s['body'], fontName='Helvetica-Bold', textColor=DARK_BLUE)
    ))

    story.append(Spacer(1, 8))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 7: DC INFRASTRUCTURE CONNECTION
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("7. How This Connects to the DC Infrastructure Thesis", s['h1']))
    story.append(AccentBar())
    story.append(Spacer(1, 8))

    story.append(Paragraph("The Feedback Loops", s['h2']))
    story.append(Spacer(1, 4))

    loops = [
        ('Loop 1: Direct Funding Stress',
         '$750B in private credit earmarked for DC buildout. If credit tightens -- fewer DC projects get funded. '
         'If funded projects default -- lender losses. Lenders pull back -- credit contraction. DC buildout slows -- '
         'less compute supply -- GPU prices stay high.'),
        ('Loop 2: Tenant Default Cascade',
         'Software/SaaS companies (25% of BDC portfolios). AI disrupts their business models. They cannot service '
         'private credit debt. They also cannot pay DC rent/cloud bills. DC operators lose revenue. DC operators\' '
         'OWN private credit comes under stress. Double hit: lender loses on BOTH the tenant AND the operator.'),
        ('Loop 3: Maturity Wall vs. CapEx Demand',
         '$12.7B in BDC debt maturing in 2026. Managers spend capacity refinancing existing debt. Less capital '
         'available for NEW DC infrastructure deals. DC projects that need financing -- delayed or cancelled. '
         'Adds to the 50% capacity slippage already in play.'),
        ('Loop 4: Regulatory Convergence',
         '300+ state DC bills + SEC/DOJ credit investigations. States restricting DC development (moratoriums). '
         'SIMULTANEOUSLY regulators scrutinizing DC financing. Double headwind: cannot build AND cannot fund. '
         'Worst case: FSOC designates private credit as systemic -- capital requirements -- credit contraction -- '
         'buildout stalls.'),
    ]

    for title, desc in loops:
        story.append(Paragraph(title, s['h3']))
        story.append(Paragraph(desc, s['body']))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 8))

    # Scenario matrix
    story.append(Paragraph("The Combined Risk Matrix", s['h2']))
    story.append(Spacer(1, 4))
    story.append(make_scenario_matrix(s))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        '<font color="#8B1A1A"><b>Current position: Bottom-left, drifting to bottom-right.</b></font>',
        s['body']
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 8: KALSHI TRADEABLE ANGLES
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("8. Kalshi-Tradeable Angles", s['h1']))
    story.append(AccentBar())
    story.append(Spacer(1, 8))

    # Stress cascade
    story.append(Paragraph("The Stress Cascade (Predictable Sequence)", s['h2']))
    story.append(Spacer(1, 4))

    cascade_table = make_timeline_table(
        rows=[
            ['1', 'Complete', 'Fraud surfaces (Tricolor, First Brands)', 'Oct--Dec 2025'],
            ['2', 'Complete', 'Retail fund gates (Blue Owl OBDC II)', 'Feb 19, 2026'],
            ['3', 'NOW', 'Contagion pricing (BDC sector selloff)', 'March 2026'],
            ['4', 'Pending', 'More redemption halts at semi-liquid funds', 'Q1--Q2 2026'],
            ['5', 'Pending', 'BDC maturity wall hits ($12.7B refi)', 'Throughout 2026'],
            ['6', 'Pending', 'Software/SaaS default wave', 'H2 2026'],
            ['7', 'Pending', 'Regulatory response (SEC rules, FSOC review)', 'Late 2026'],
            ['8', 'Pending', 'Bank writedowns on $1.1T NDFI exposure', '2027'],
        ],
        styles_dict=s
    )
    story.append(cascade_table)
    story.append(Spacer(1, 6))
    story.append(Paragraph('<b>Each stage = a tradeable event on Kalshi.</b>', s['body_bold']))
    story.append(Spacer(1, 10))

    # Trade A
    story.append(Paragraph("Trade A: Fed Rate Path (Tension Trade)", s['h3']))
    story.append(Spacer(1, 4))

    trade_a = make_data_table(
        headers=['Bull Case for Cuts', 'Bear Case for Cuts'],
        rows=[
            ['Private credit stress -- credit tightening -- economic slowdown -- Fed MUST cut',
             'Warsh as Fed chair (94%) = hawkish lean. Inflation still sticky. Fed prioritizes credibility.'],
        ],
        col_widths=[CONTENT_W * 0.5, CONTENT_W * 0.5],
        styles_dict=s
    )
    story.append(trade_a)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        '<b>Thesis:</b> Credit stress will FORCE cuts even under a hawkish chair. '
        '<b>Timing:</b> Watch for after each major blowup event (stages 4--5).',
        s['body']
    ))
    story.append(Spacer(1, 8))

    # Trade B
    story.append(Paragraph("Trade B: GDP / Recession Probability", s['h3']))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        '$3T in private credit funds economic activity across the mid-market. If credit contracts: '
        'mid-market companies cannot invest/hire, DC buildout slows (4% of GDP, 92% of growth), '
        'software sector sheds jobs, GDP estimates are too high.',
        s['body']
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Polymarket Signal:</b>", s['body_bold']))
    for item in ['US GDP Q1 2026 >3.5%: only 40% (down 12.5%)',
                 'Full year 2026 GDP: 68% in 1--2.5% range',
                 'Market is ALREADY pricing in slowdown']:
        story.append(Paragraph(f'<bullet>&bull;</bullet> {item}', s['bullet']))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        '<b>Thesis:</b> Maturity wall + credit contraction in H2 2026 -- recession risk rises sharply. '
        '<b>Timing:</b> H2 2026 as stages 5--6 unfold.',
        s['body']
    ))
    story.append(Spacer(1, 8))

    # Trade C
    story.append(Paragraph("Trade C: S&amp;P 500 / Financial Sector", s['h3']))
    story.append(Spacer(1, 4))
    trade_c = make_data_table(
        headers=['Firm', 'Credit Exposure', 'Risk Profile'],
        rows=[
            ['Apollo (APO)', '86%', 'Max downside per blowup'],
            ['Ares (ARES)', '66%', 'Significant'],
            ['Blue Owl (OWL)', '53%', 'Already pricing in distress'],
            ['Blackstone (BX)', '34%', 'Diversified BUT has BCRED risk'],
        ],
        col_widths=[CONTENT_W * 0.25, CONTENT_W * 0.25, CONTENT_W * 0.50],
        styles_dict=s
    )
    story.append(trade_c)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        '<b>Thesis:</b> Each new blowup event -- risk-off for financials. '
        '<b>Timing:</b> BDC earnings reports (quarterly), any new gate announcements.',
        s['body']
    ))

    story.append(Spacer(1, 8))

    # Trade D
    story.append(Paragraph("Trade D: Natural Gas + Energy (Infrastructure Workaround)", s['h3']))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        'DC operators cannot get grid power (8yr queue) -- build behind-the-meter gas plants as workaround. '
        'Need private credit to fund gas plants. If credit tightens -- cannot fund the workaround -- DC buildout '
        'stalls even harder. BUT: gas plants are tangible collateral. Private credit PREFERS hard assets over '
        'software loans. Capital may SHIFT from software lending to infra lending. Net effect: natural gas demand '
        'UP regardless.',
        s['body']
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        '<b>Thesis:</b> Structural floor under gas prices from DC demand. Even if software credit contracts, '
        'infra credit grows. <b>Timing:</b> Ongoing, accelerating through 2026--2027.',
        s['body']
    ))
    story.append(Spacer(1, 10))

    # Trade E
    story.append(Paragraph("Trade E: State Policy Events (Discrete Catalysts)", s['h3']))
    story.append(Spacer(1, 4))

    policy_table = make_data_table(
        headers=['State', 'Policy Event', 'Target Date'],
        rows=[
            ['Georgia', '1-year DC moratorium vote', 'Jul 1, 2026'],
            ['Denver', 'Formal moratorium vote', 'March 2026'],
            ['New York', '3-year moratorium proposal', 'TBD'],
            ['Oklahoma', 'Moratorium through Nov 2029', 'Active'],
            ['Vermont', 'Moratorium through Jul 2030', 'Active'],
            ['Missouri', 'Water/power reporting requirements', 'TBD'],
        ],
        col_widths=[CONTENT_W * 0.18, CONTENT_W * 0.52, CONTENT_W * 0.30],
        styles_dict=s
    )
    story.append(policy_table)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        'Additional catalysts: SEC enforcement actions (timing unknown), FSOC review (if stress '
        'escalates), Fed chair confirmation (Warsh, 94%).',
        s['body']
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        '<b>Thesis:</b> Each moratorium = DC supply reduction = GPU prices elevated = AI timeline slippage.',
        s['body']
    ))

    story.append(Spacer(1, 8))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 9: EVENT CALENDAR
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("9. Event Calendar: Known Catalysts", s['h1']))
    story.append(AccentBar())
    story.append(Spacer(1, 8))

    quarters = [
        ('Q1 2026 (NOW)', [
            'BDC Q4 earnings reports -- watch for: rising PIK percentages (currently 8% of income), NAV markdowns, additional redemption halts, "We\'re not like Blue Owl" disclaimers',
            'Denver moratorium formal vote (March)',
            'Fed chair nomination process',
            'More state DC legislation (300+ bills filed)',
        ]),
        ('Q2 2026', [
            'Maturity wall ramp ($12.7B needs refi). Loans originated at 4.1--4.7%, must refi at 6.5--7.0% (+250--300bps). Borrowers who cannot -- default or distressed exchange.',
            'BDC Q1 earnings -- PIK watch continues',
            'Georgia moratorium vote (Jul 1)',
            'Semi-liquid fund redemption cycle (quarterly)',
        ]),
        ('H2 2026', [
            'Software/SaaS default wave. AI disruption + growth deceleration. 25% of BDC portfolios exposed. UBS worst case: 15% default rate.',
            'SEC regulatory response (enforcement / rules)',
            'Possible FSOC review if stress escalates',
            'Congressional hearings (if politically useful)',
        ]),
        ('2027', [
            'Bank writedowns on $1.1T NDFI exposure',
            'DC projects that slipped from 2026 come online (or do not)',
            'SMR/nuclear timeline clarity',
            'Full credit cycle completion for private credit',
        ]),
    ]

    for period, items in quarters:
        story.append(Paragraph(period, s['h3']))
        for item in items:
            story.append(Paragraph(f'<bullet>&bull;</bullet> {item}', s['bullet']))
        story.append(Spacer(1, 6))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 10: KEY METRICS
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("10. Key Metrics to Monitor", s['h1']))
    story.append(AccentBar())
    story.append(Spacer(1, 8))

    metrics_table = make_data_table(
        headers=['Metric', 'Current', 'Watch Level', 'Crisis Level', 'Source'],
        rows=[
            ['PIK as % of BDC income', '8%', '>10%', '>15%', 'BDC quarterly filings'],
            ['"Bad PIK" percentage', '57.2%', '>65%', '>75%', 'Lincoln International'],
            ['Headline default rate', '<2%', '>3%', '>5%', 'S&amp;P/Moody\'s'],
            ['True default rate (w/ selective)', '~5%', '>7%', '>10%', 'Fortune/Bernstein'],
            ['Leveraged loan default rate', '5.0%', '>6%', '>8%', 'S&amp;P LCD'],
            ['BDC NAV discounts', 'Widening', '>10%', '>20%', 'Public markets'],
            ['Semi-liquid fund redemptions', 'Elevated', '>10% NAV', '>15% NAV', 'Fund filings'],
            ['Bank loans to NDFIs', '$1.1T (10%)', '>12%', '>15%', 'Fed data'],
            ['DC capacity under construction', '5.99 GW', '<5.5 GW', '<5 GW', 'Bloomberg'],
            ['H100 GPU rental index', '~$2.50', '>$3.00', '>$4.00', 'Polymarket/SDH100RT'],
        ],
        col_widths=[CONTENT_W * 0.24, CONTENT_W * 0.14, CONTENT_W * 0.14, CONTENT_W * 0.14, CONTENT_W * 0.34],
        styles_dict=s
    )
    story.append(metrics_table)

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 11: MONEY MAP
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("11. The Money Map: Who Wins, Who Loses", s['h1']))
    story.append(AccentBar())
    story.append(Spacer(1, 8))

    winners = [
        'Distressed debt funds (Oaktree, Apollo distressed)',
        'Banks w/ low NDFI exposure (JPMorgan -- warned early)',
        'Disciplined direct lenders (top-quartile underwriting)',
        'Short sellers of alt managers (OWL, APO, ARES)',
        'Cash-rich strategic acquirers (buy distressed assets cheap)',
        'Infrastructure-collateral lenders (hard assets, tangible value)',
        'Behind-the-meter power companies (GE Vernova, Bloom Energy)',
        'Liquid cooling leaders (Vertiv, CoolIT, LiquidStack)',
    ]
    losers = [
        'Retail investors in semi-liquid funds (OBDC II, potentially BCRED)',
        'Banks w/ high NDFI exposure (regional banks, warehouse lenders)',
        'Lenders who reached for yield (loose covenants, aggressive adds)',
        'Long holders at peak valuations (esp. Apollo at 86% credit)',
        'PE-backed companies needing refi (maturity wall victims)',
        'Software/SaaS-focused lenders (25% of BDC portfolios at risk)',
        'Grid-dependent DC developers (8yr interconnection queue)',
        'Air-cooled DC operators (stranded by density demands)',
    ]

    story.append(make_two_column_table('WINNERS', 'LOSERS', winners, losers, s))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 12: CONTRARIAN CASE
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("12. The Contrarian Case (Why It Might Not Blow Up)", s['h1']))
    story.append(AccentBar())
    story.append(Spacer(1, 8))

    contrarian_points = [
        ('<b>Strong bank capitalization:</b> Post-2008 reforms mean banks absorb losses better.', s['bullet']),
        ('<b>Floating rate:</b> Most PC is floating -- borrowers benefit if rates drop.', s['bullet']),
        ('<b>Sponsor support:</b> PE sponsors inject equity to prevent portfolio company defaults.', s['bullet']),
        ('<b>Selective, not systemic:</b> Blue Owl is a specific management problem, not market-wide.', s['bullet']),
        ('<b>Fed backstop:</b> If stress becomes systemic, Fed steps in (moral hazard, but real).', s['bullet']),
        ('<b>Fed Chair Powell:</b> Has stated he does not see a "broader problem."', s['bullet']),
        ('<b>Capital rotation:</b> Money leaves software-exposed BDCs -- flows to infra-collateralized deals.', s['bullet']),
    ]
    for text, style in contrarian_points:
        story.append(Paragraph(f'<bullet>&bull;</bullet> {text}', style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Why the Contrarian Case Is Weak for Trading Purposes", s['h2']))
    story.append(Spacer(1, 4))

    rebuttals = [
        'Strong bank capitalization does not help UNREGULATED non-bank lenders.',
        'Floating rate only helps if rates DROP -- Warsh as chair (94%) says they will not.',
        'PE sponsors support best assets, abandon the rest -- dispersion INCREASES.',
        '"Selective, not systemic" is what they said about Bear Stearns in Feb 2008.',
        'Fed backstop requires things to get WORSE before it activates.',
        'Powell said no "broader problem" BEFORE Blue Owl.',
        'Capital rotation takes quarters, not days -- the transition period IS the stress period.',
    ]
    for i, text in enumerate(rebuttals, 1):
        story.append(Paragraph(f'<b>{i}.</b> {text}', s['bullet']))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SOURCES
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Key Sources", s['h1']))
    story.append(AccentBar())
    story.append(Spacer(1, 10))

    source_sections = [
        ('Blue Owl / Contagion', [
            'Bloomberg: "Blue Owl Redemptions Halt Intensifies Private Credit Fears" (Feb 22)',
            'Bloomberg: "Blue Owl Redemption Halt Stirs Private Credit Unease" (Feb 19)',
            'CNBC: "\'Canary in the coal mine\': Blue Owl liquidity curbs fuel fears" (Feb 20)',
            'CNBC: "From Dimon\'s \'cockroaches\' to the Blue Owl freeze" (Feb 24)',
            'Fortune: "In the $3T private credit market, the \'shadow default\' rate is increasing" (Feb 22)',
        ]),
        ('Default Risk / Market Structure', [
            'Bloomberg: "UBS Now Sees Private Credit Defaults Reaching 15% in Worst Case" (Feb 24)',
            'Bloomberg: "Dimon\'s \'Dumb Things\' Remark Frames Debate Over Private Credit" (Feb 26)',
            'Bloomberg: "Private Credit\'s Great Divide: Imminent Crisis or \'No Big Deal\'"',
            'Bernstein: "Private Credit: Lessons from 2025\'s Default Wave"',
            'Fortune: "Private credit deals see a rise in \'bad PIKs\' showing cracks" (Nov 2025)',
            'PitchBook: "2026 US Distressed Credit Outlook: Bifurcation, maturity wall"',
            'S&amp;P Global: Private credit trends to watch in 2026',
        ]),
        ('Systemic Risk / Regulation', [
            'Boston Fed: "Could the Growth of Private Credit Pose a Risk to Financial System Stability?"',
            'Dallas Fed: "How AI debt financing impacts duration supply and interest rates" (Feb 10)',
            'Oaktree Capital (Howard Marks): "Cockroaches in the Coal Mine" memo',
            'Carlyle: "Credit in 2026: A Market That Demands Insight, Not Just Capital"',
            'Morgan Stanley / Loomis Sayles / Paul Weiss: 2026 Private Credit Outlooks',
        ]),
        ('DC Infrastructure Nexus', [
            'Bloomberg: "$3 Trillion AI Data Center Build-Out Becomes All-Consuming for Debt Markets" (Feb 2)',
            'iCapital: "Data Center Infrastructure: Moving from Cash to Debt"',
            'S&amp;P Global: "Key Data Center Financing Takeaways From PPIF 2026"',
            'JPMorgan: Global data center and AI infra spend to hit $5 trillion',
        ]),
        ('Prediction Markets', [
            'Polymarket: Fed Chair (Kevin Warsh 94%), S&amp;P 500 opens, US debt default, H100 GPU rental index',
            'Reddit: r/stocks, r/Stocks_Picks, r/StockMarket, r/ProfessorFinance, r/LeveragedFinance, r/investing',
        ]),
    ]

    for section_title, items in source_sections:
        story.append(Paragraph(section_title, s['source_header']))
        for item in items:
            story.append(Paragraph(f'<bullet>&bull;</bullet> {item}', s['source_item']))
        story.append(Spacer(1, 4))

    # ═══════════════════════════════════════════════════════════════════════════
    # BUILD
    # ═══════════════════════════════════════════════════════════════════════════
    doc.build(story)
    print(f"PDF generated: {output_path}")
    return output_path


if __name__ == "__main__":
    build_document()
