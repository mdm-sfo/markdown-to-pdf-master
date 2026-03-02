#!/usr/bin/env python3
"""
md2pdf.py -- Convert Markdown white papers into premium academic-style PDFs.
Harvard PhD office aesthetic: clean typography, strong hierarchy, elegant tables.

Usage:
    python md2pdf.py input.md
    python md2pdf.py input.md --output output.pdf
    python md2pdf.py input.md -o output.pdf
"""

import sys
import os
import re
import argparse

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle,
    PageBreak, Frame, PageTemplate,
    BaseDocTemplate, NextPageTemplate, Flowable
)

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
    def __init__(self, text, width, style, bg_color=LIGHT_GRAY, accent_color=ACCENT):
        Flowable.__init__(self)
        self.text = text
        self.box_width = width
        self.style = style
        self.bg_color = bg_color
        self.accent_color = accent_color
        p = Paragraph(text, style)
        w, h = p.wrap(width - 24, 1000)
        self.box_height = h + 20

    def wrap(self, availWidth, availHeight):
        return self.box_width, self.box_height

    def draw(self):
        self.canv.setFillColor(self.bg_color)
        self.canv.roundRect(0, 0, self.box_width, self.box_height, 3, fill=1, stroke=0)
        self.canv.setFillColor(self.accent_color)
        self.canv.rect(0, 0, 4, self.box_height, fill=1, stroke=0)
        p = Paragraph(self.text, self.style)
        p.wrap(self.box_width - 24, self.box_height)
        p.drawOn(self.canv, 16, 10)


# ─── STYLES ──────────────────────────────────────────────────────────────────

def build_styles():
    s = {}

    s['title'] = ParagraphStyle(
        'Title', fontName='Helvetica-Bold', fontSize=22, leading=28,
        textColor=NAVY, spaceAfter=4, alignment=TA_LEFT,
    )
    s['subtitle'] = ParagraphStyle(
        'Subtitle', fontName='Helvetica', fontSize=11, leading=15,
        textColor=MUTED, spaceAfter=2, alignment=TA_LEFT,
    )
    s['h1'] = ParagraphStyle(
        'H1', fontName='Helvetica-Bold', fontSize=16, leading=22,
        textColor=NAVY, spaceBefore=18, spaceAfter=6, alignment=TA_LEFT,
    )
    s['h2'] = ParagraphStyle(
        'H2', fontName='Helvetica-Bold', fontSize=12.5, leading=17,
        textColor=DARK_BLUE, spaceBefore=14, spaceAfter=4, alignment=TA_LEFT,
    )
    s['h3'] = ParagraphStyle(
        'H3', fontName='Helvetica-Bold', fontSize=10.5, leading=14,
        textColor=MED_BLUE, spaceBefore=10, spaceAfter=3, alignment=TA_LEFT,
    )
    s['body'] = ParagraphStyle(
        'Body', fontName='Helvetica', fontSize=9.5, leading=14,
        textColor=TEXT_COLOR, spaceAfter=6, alignment=TA_JUSTIFY,
    )
    s['body_bold'] = ParagraphStyle(
        'BodyBold', fontName='Helvetica-Bold', fontSize=9.5, leading=14,
        textColor=TEXT_COLOR, spaceAfter=6, alignment=TA_LEFT,
    )
    s['bullet'] = ParagraphStyle(
        'Bullet', fontName='Helvetica', fontSize=9.5, leading=13.5,
        textColor=TEXT_COLOR, spaceAfter=3, leftIndent=16, bulletIndent=4,
        alignment=TA_LEFT,
    )
    s['sub_bullet'] = ParagraphStyle(
        'SubBullet', fontName='Helvetica', fontSize=9, leading=12.5,
        textColor=DARK_GRAY, spaceAfter=2, leftIndent=32, bulletIndent=20,
        alignment=TA_LEFT,
    )
    s['callout'] = ParagraphStyle(
        'Callout', fontName='Helvetica', fontSize=9.5, leading=14,
        textColor=TEXT_COLOR, alignment=TA_LEFT,
    )
    s['quote'] = ParagraphStyle(
        'Quote', fontName='Helvetica-Oblique', fontSize=9, leading=13,
        textColor=DARK_GRAY, leftIndent=20, rightIndent=20,
        spaceBefore=4, spaceAfter=4, alignment=TA_LEFT,
    )
    s['table_header'] = ParagraphStyle(
        'TableHeader', fontName='Helvetica-Bold', fontSize=8.5, leading=11,
        textColor=WHITE, alignment=TA_LEFT,
    )
    s['table_cell'] = ParagraphStyle(
        'TableCell', fontName='Helvetica', fontSize=8.5, leading=11.5,
        textColor=TEXT_COLOR, alignment=TA_LEFT,
    )
    s['table_cell_bold'] = ParagraphStyle(
        'TableCellBold', fontName='Helvetica-Bold', fontSize=8.5, leading=11.5,
        textColor=TEXT_COLOR, alignment=TA_LEFT,
    )
    s['source_header'] = ParagraphStyle(
        'SourceHeader', fontName='Helvetica-Bold', fontSize=9, leading=12,
        textColor=DARK_BLUE, spaceBefore=6, spaceAfter=2, alignment=TA_LEFT,
    )
    s['source_item'] = ParagraphStyle(
        'SourceItem', fontName='Helvetica', fontSize=8, leading=11,
        textColor=MUTED, spaceAfter=1, leftIndent=8, alignment=TA_LEFT,
    )
    s['code_line'] = ParagraphStyle(
        'CodeLine', fontName='Courier', fontSize=7.5, leading=10,
        textColor=TEXT_COLOR, alignment=TA_LEFT,
    )
    return s


# ─── PAGE TEMPLATE ───────────────────────────────────────────────────────────

class DocTemplate(BaseDocTemplate):
    def __init__(self, filename, doc_title="", **kwargs):
        BaseDocTemplate.__init__(self, filename, **kwargs)
        self.doc_title = doc_title

        frame = Frame(
            LEFT_MARGIN, BOTTOM_MARGIN,
            CONTENT_W, PAGE_H - TOP_MARGIN - BOTTOM_MARGIN,
            id='normal'
        )

        cover_template = PageTemplate(
            id='Cover', frames=[frame], onPage=self._cover_page
        )
        normal_template = PageTemplate(
            id='Normal', frames=[frame], onPage=self._normal_page
        )
        self.addPageTemplates([cover_template, normal_template])

    def _cover_page(self, canvas, doc):
        canvas.saveState()
        canvas.restoreState()

    def _normal_page(self, canvas, doc):
        canvas.saveState()

        # Top rule
        canvas.setStrokeColor(NAVY)
        canvas.setLineWidth(1.5)
        canvas.line(LEFT_MARGIN, PAGE_H - TOP_MARGIN + 12,
                    PAGE_W - RIGHT_MARGIN, PAGE_H - TOP_MARGIN + 12)

        canvas.setStrokeColor(RULE_COLOR)
        canvas.setLineWidth(0.5)
        canvas.line(LEFT_MARGIN, PAGE_H - TOP_MARGIN + 8,
                    PAGE_W - RIGHT_MARGIN, PAGE_H - TOP_MARGIN + 8)

        # Header text
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(LEFT_MARGIN, PAGE_H - TOP_MARGIN + 16, self.doc_title)

        # Bottom rule
        canvas.setStrokeColor(RULE_COLOR)
        canvas.setLineWidth(0.5)
        canvas.line(LEFT_MARGIN, BOTTOM_MARGIN - 8,
                    PAGE_W - RIGHT_MARGIN, BOTTOM_MARGIN - 8)

        # Page number
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(MUTED)
        canvas.drawCentredString(PAGE_W / 2, BOTTOM_MARGIN - 22,
                                 str(canvas.getPageNumber()))

        # Classification
        canvas.setFont('Helvetica', 6.5)
        canvas.setFillColor(HexColor("#999999"))
        canvas.drawRightString(PAGE_W - RIGHT_MARGIN, BOTTOM_MARGIN - 22,
                               "Confidential -- For Research Purposes Only")

        canvas.restoreState()


# ─── TABLE BUILDER ───────────────────────────────────────────────────────────

def make_data_table(headers, rows, styles_dict):
    s = styles_dict
    header_cells = [Paragraph(esc(h), s['table_header']) for h in headers]
    data_rows = []
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            style = s['table_cell_bold'] if i == 0 else s['table_cell']
            cells.append(Paragraph(esc(str(cell)), style))
        data_rows.append(cells)

    table_data = [header_cells] + data_rows
    n_cols = len(headers)

    # Auto column widths: first column slightly wider, rest equal
    if n_cols == 1:
        col_widths = [CONTENT_W]
    elif n_cols == 2:
        col_widths = [CONTENT_W * 0.4, CONTENT_W * 0.6]
    elif n_cols <= 4:
        first_w = CONTENT_W * 0.30
        rest_w = (CONTENT_W - first_w) / (n_cols - 1)
        col_widths = [first_w] + [rest_w] * (n_cols - 1)
    else:
        first_w = CONTENT_W * 0.22
        rest_w = (CONTENT_W - first_w) / (n_cols - 1)
        col_widths = [first_w] + [rest_w] * (n_cols - 1)

    t = Table(table_data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEAD),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8.5),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, NAVY),
        ('LINEBELOW', (0, -1), (-1, -1), 1, NAVY),
    ]
    if len(table_data) > 2:
        style_cmds.append(('LINEBELOW', (0, 1), (-1, -2), 0.5, RULE_COLOR))
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), TABLE_ALT))

    t.setStyle(TableStyle(style_cmds))
    return t


def make_two_column_table(left_header, right_header, left_items, right_items, styles_dict):
    s = styles_dict
    max_rows = max(len(left_items), len(right_items))
    header = [Paragraph(esc(left_header), s['table_header']),
              Paragraph(esc(right_header), s['table_header'])]
    data = [header]
    for i in range(max_rows):
        left = Paragraph(esc(left_items[i]), s['table_cell']) if i < len(left_items) else Paragraph('', s['table_cell'])
        right = Paragraph(esc(right_items[i]), s['table_cell']) if i < len(right_items) else Paragraph('', s['table_cell'])
        data.append([left, right])

    col_w = CONTENT_W / 2
    t = Table(data, colWidths=[col_w, col_w], repeatRows=1)

    style_cmds = [
        ('BACKGROUND', (0, 0), (0, 0), HexColor("#1B5E20")),
        ('BACKGROUND', (1, 0), (1, 0), ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, NAVY),
        ('LINEBELOW', (0, -1), (-1, -1), 1, NAVY),
        ('LINEBEFORE', (1, 0), (1, -1), 0.5, RULE_COLOR),
    ]
    if len(data) > 2:
        style_cmds.append(('LINEBELOW', (0, 1), (-1, -2), 0.5, RULE_COLOR))
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), TABLE_ALT))

    t.setStyle(TableStyle(style_cmds))
    return t


# ─── MARKDOWN PARSER ─────────────────────────────────────────────────────────

def esc(text):
    """Escape text for ReportLab XML paragraphs."""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def _is_title_line(stripped):
    """Check if a stripped line looks like an ALL-CAPS title/label.
    Returns False for lines containing digits, %, or $ (data lines)."""
    if not stripped:
        return False
    if not stripped.isupper():
        return False
    if ':' in stripped:
        return False
    if len(stripped) >= 60:
        return False
    # Lines with numbers, percentages, dollar signs are data, not titles
    if re.search(r'[\d%$]', stripped):
        return False
    return True


def md_inline(text):
    """Convert markdown inline formatting to ReportLab XML."""
    # Escape ampersands first (but not already-escaped ones)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')

    # Bold + italic: ***text*** or ___text___
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
    text = re.sub(r'___(.+?)___', r'<b><i>\1</i></b>', text)

    # Bold: **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)

    # Italic: *text* or _text_ (but not inside words with underscores)
    text = re.sub(r'(?<!\w)\*([^\*]+?)\*(?!\w)', r'<i>\1</i>', text)
    text = re.sub(r'(?<!\w)_([^_]+?)_(?!\w)', r'<i>\1</i>', text)

    # Inline code: `text`
    text = re.sub(r'`([^`]+?)`', r'<font face="Courier" size="8">\1</font>', text)

    return text


def parse_pipe_table(lines):
    """Parse a markdown pipe table into headers and rows."""
    if len(lines) < 2:
        return None, None

    def split_row(line):
        line = line.strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        return [cell.strip() for cell in line.split('|')]

    headers = split_row(lines[0])

    # Check if line[1] is a separator (---|---|---)
    sep_line = lines[1].strip().replace(' ', '')
    if not re.match(r'^[\|\-\:]+$', sep_line):
        return None, None

    rows = []
    for line in lines[2:]:
        if line.strip():
            rows.append(split_row(line))

    return headers, rows


def is_winners_losers_block(lines):
    """Detect a two-column WINNERS/LOSERS style code block."""
    text = '\n'.join(lines)
    return ('WINNERS' in text and 'LOSERS' in text) or \
           ('Winners' in text and 'Losers' in text) or \
           ('WINNER' in text and 'LOSER' in text)


def parse_winners_losers(lines):
    """Parse a two-column WINNERS/LOSERS block from code fence content."""
    left_items = []
    right_items = []

    # Find the header line and separator
    start = 0
    for i, line in enumerate(lines):
        if '═' in line or '---' in line or '===' in line:
            start = i + 1
            break
        if 'WINNER' in line.upper() and 'LOSER' in line.upper():
            start = i + 1
            continue

    # Parse two-column lines (separated by large whitespace gaps)
    for line in lines[start:]:
        line = line.rstrip()
        if not line.strip() or '═' in line:
            continue

        # Try to split on multiple spaces (2+ spaces as column separator)
        parts = re.split(r'  {2,}', line)
        if len(parts) >= 2:
            left = parts[0].strip()
            right = parts[1].strip()
            if left:
                left_items.append(left)
            if right:
                right_items.append(right)
        elif line.strip():
            # Single item -- add to whichever side is shorter
            if len(left_items) <= len(right_items):
                left_items.append(line.strip())
            else:
                right_items.append(line.strip())

    # Merge consecutive lines that belong together (parenthetical continuations)
    left_items = _merge_continuation_lines(left_items)
    right_items = _merge_continuation_lines(right_items)

    return left_items, right_items


def _merge_continuation_lines(items):
    """Merge lines that start with ( into the previous line."""
    merged = []
    for item in items:
        if item.startswith('(') and merged:
            merged[-1] = merged[-1] + ' ' + item
        else:
            merged.append(item)
    return merged


def parse_ascii_table(lines):
    """Parse ASCII-formatted table from code block lines.
    Handles multi-line headers and column-aligned data."""

    # Find separator line (═══)
    sep_idx = None
    for i, line in enumerate(lines):
        if '═' in line and i > 0:
            sep_idx = i
            break

    if sep_idx is None:
        return None, None

    # Collect data rows (non-empty, non-separator, non-tree lines after separator)
    # Stop collecting at blank lines (which indicate end of table data)
    data_lines = []
    hit_blank = False
    for line in lines[sep_idx + 1:]:
        stripped = line.strip()
        if not stripped:
            hit_blank = True
            continue
        if hit_blank:
            # After a blank line, stop collecting unless this looks like continuation data
            # (has content at the same column positions). In practice, a blank line
            # usually separates the table from a following section.
            break
        if '═' in stripped:
            continue
        if stripped.startswith(('├', '│', '└')):
            continue
        # Skip lines that are ALL CAPS titles/labels (like section subheaders inside blocks)
        if _is_title_line(stripped):
            continue
        data_lines.append(line)

    if len(data_lines) < 2:
        return None, None

    # Detect column positions by analyzing alignment across all data lines
    # Find where columns start by looking at word-start positions that repeat
    max_len = max(len(l) for l in data_lines)
    if max_len < 30:
        return None, None

    # Build a map of character positions that are non-space across data lines
    # Columns start where there's a transition from space to non-space
    col_starts = set()
    for line in data_lines:
        for j in range(len(line)):
            if line[j] != ' ':
                # Is this a column start? (preceded by space or start of line)
                if j == 0 or (j > 0 and line[j-1] == ' ' and (j < 2 or line[j-2] == ' ')):
                    col_starts.add(j)

    if len(col_starts) < 2:
        return None, None

    # Sort and filter: keep positions that appear in multiple data rows
    pos_counts = {}
    for pos in col_starts:
        count = 0
        for line in data_lines:
            if pos < len(line) and line[pos] != ' ':
                # Check it's a real column start (preceded by 2+ spaces or at start)
                if pos == 0 or (pos >= 2 and line[pos-1] == ' ' and line[pos-2] == ' '):
                    count += 1
        pos_counts[pos] = count

    # Keep positions that appear in at least 40% of data rows
    threshold = max(2, len(data_lines) * 0.4)
    col_positions = sorted([p for p, c in pos_counts.items() if c >= threshold])

    # Merge positions that are too close (within 3 chars)
    merged = []
    for p in col_positions:
        if not merged or p - merged[-1] > 3:
            merged.append(p)
    col_positions = merged

    if len(col_positions) < 2:
        return None, None

    # Extract headers from lines between separator and first data row
    # Headers may span multiple lines (e.g. multi-line column names)
    # Find where the data actually starts (first line that has values at col positions)
    header_lines = []
    actual_data_start = sep_idx + 1

    for li in range(sep_idx + 1, len(lines)):
        line = lines[li]
        stripped = line.strip()
        if not stripped or '═' in stripped:
            continue
        if stripped.startswith(('├', '│', '└')):
            continue
        if _is_title_line(stripped):
            continue

        # Check: does this line have data at the first column position?
        # If the first col starts at 0 and this line has non-space at 0, it's data
        # If this line's content is only in the middle columns, it's a header continuation
        has_first_col = (len(line) > col_positions[0] and
                         line[col_positions[0]] != ' ')
        if has_first_col:
            # This is a data row -- everything before it is header
            actual_data_start = li
            break
        else:
            header_lines.append(line)

    # Recompute data_lines from actual_data_start
    # Stop at blank lines (which separate table from following sections)
    data_lines = []
    hit_blank = False
    for line in lines[actual_data_start:]:
        stripped = line.strip()
        if not stripped:
            hit_blank = True
            continue
        if hit_blank:
            break
        if '═' in stripped:
            continue
        if stripped.startswith(('├', '│', '└')):
            continue
        if _is_title_line(stripped):
            continue
        data_lines.append(line)

    if len(data_lines) < 2:
        return None, None

    # Build headers from column positions
    headers = []
    for k in range(len(col_positions)):
        start = col_positions[k]
        end = col_positions[k + 1] if k + 1 < len(col_positions) else max_len
        parts = []
        for hl in header_lines:
            segment = hl[start:end].strip() if start < len(hl) else ''
            if segment:
                parts.append(segment)
        header = ' '.join(parts) if parts else ''
        headers.append(header)

    # Extract data using column positions
    rows = []
    for line in data_lines:
        row = []
        for k in range(len(col_positions)):
            start = col_positions[k]
            end = col_positions[k + 1] if k + 1 < len(col_positions) else len(line)
            cell = line[start:end].strip() if start < len(line) else ''
            row.append(cell)
        if any(cell for cell in row):
            rows.append(row)

    if rows and len(headers) == len(rows[0]):
        return headers, rows
    return None, None


def parse_code_block_content(lines, styles_dict):
    """Analyze a code block and return appropriate flowables."""
    s = styles_dict
    text = '\n'.join(lines)

    # Skip empty blocks
    stripped_lines = [l for l in lines if l.strip()]
    if not stripped_lines:
        return []

    # Check for winners/losers pattern
    if is_winners_losers_block(lines):
        left, right = parse_winners_losers(lines)
        if left and right:
            return [make_two_column_table('WINNERS', 'LOSERS', left, right, s)]

    # Check for 2-column comparison pattern (ASSET SIDE / LIABILITY SIDE, BULL/BEAR, etc.)
    first_content = '\n'.join(stripped_lines[:5])
    two_col_match = re.search(r'([A-Z][A-Z\s/]+?):\s{2,}([A-Z][A-Z\s/]+?):', first_content)
    if two_col_match:
        left_header = two_col_match.group(1).strip()
        right_header = two_col_match.group(2).strip()
        left_items, right_items = _parse_two_column_block(lines, left_header, right_header)
        if left_items and right_items:
            return [make_two_column_table(left_header, right_header, left_items, right_items, s)]

    # Check for scenario matrix pattern (2x2 grid)
    if 'SCENARIO MATRIX' in text.upper() or ('CREDIT HOLDS' in text.upper() and 'CREDIT CRACKS' in text.upper()):
        result = _parse_scenario_matrix(lines, s)
        if result:
            return result

    # Check for labeled-section blocks (LOOP 1:, LOOP 2:, etc.)
    # These are blocks with titled subsections followed by tree content
    loop_labels = [l for l in stripped_lines if re.match(r'^LOOP \d', l.strip())]
    if len(loop_labels) >= 2:
        return _parse_labeled_sections_block(lines, s)

    # Check for ASCII art / iceberg diagrams
    art_lines = [l for l in stripped_lines if any(c in l for c in '╱╲█▓░')]
    if art_lines and len(art_lines) >= 2:
        return _render_ascii_art_block(lines, s)

    # Try key:value pairs BEFORE column-aligned table
    # (prevents column-aligned parser from misreading "key: value" blocks as multi-column)
    kv_pairs = _parse_key_value_block(lines)
    if kv_pairs and len(kv_pairs) >= 2:
        result = []
        # Add title from before separator
        for idx, line in enumerate(lines):
            if '═' in line:
                if idx > 0 and lines[idx - 1].strip():
                    result.append(Paragraph(md_inline(lines[idx - 1].strip()), s['h3']))
                    result.append(Spacer(1, 4))
                break
        headers = ['Item', 'Value']
        result.append(make_data_table(headers, kv_pairs, s))
        # Render non-kv content that follows: section labels, tree items, annotations
        # Build set of consumed kv keys to skip those lines
        kv_keys = set(p[0] for p in kv_pairs)
        sep_idx = -1
        for idx, line in enumerate(lines):
            if '═' in line:
                sep_idx = idx
                break
        if sep_idx >= 0:
            for line in lines[sep_idx + 1:]:
                stripped = line.strip()
                if not stripped:
                    continue
                # Skip lines that match kv pair keys
                is_kv = False
                if ':' in stripped:
                    m = re.match(r'^([^:\n]{2,40}):\s+', stripped)
                    if m and m.group(1).strip() in kv_keys:
                        is_kv = True
                if re.match(r'^\S.{2,30}\s{4,}.+$', stripped) and not stripped.startswith(('├', '└', '│')):
                    # Could be a whitespace-separated kv pair
                    m2 = re.match(r'^(\S.{2,30})\s{4,}', stripped)
                    if m2 and m2.group(1).strip() in kv_keys:
                        is_kv = True
                if is_kv:
                    continue
                # Skip continuation lines (deeply indented)
                indent = len(line) - len(line.lstrip())
                if indent >= 8:
                    continue
                # Skip ═══ separator lines
                if '═' in stripped:
                    continue
                # Render tree items (only if not already captured as kv pairs)
                if stripped.startswith(('├', '└')):
                    # Check if any kv pair has the ███ prefix (tree-item-with-value)
                    has_tree_kv = any(k.startswith('█') for k in kv_keys)
                    if has_tree_kv:
                        # Tree items were already absorbed into kv table, skip
                        continue
                    clean = re.sub(r'[├│└─┌┐┘┬┴┼]', '', stripped).strip()
                    clean = re.sub(r'^[\-\s]+', '', clean).strip()
                    if clean:
                        depth = 1 if '│   ' in line or '    └' in line or '    ├' in line else 0
                        style = s['sub_bullet'] if depth > 0 else s['bullet']
                        result.append(Paragraph(f'<bullet>&bull;</bullet> {md_inline(clean)}', style))
                    continue
                if stripped.startswith('│'):
                    continue
                # Section labels ending with :
                if stripped.endswith(':') and len(stripped) > 5:
                    result.append(Spacer(1, 4))
                    result.append(Paragraph(md_inline(stripped), s['body_bold']))
                    continue
                # Annotations with ^^^
                if stripped.startswith('^^^') or stripped.startswith('^--'):
                    clean = re.sub(r'^[\^]+[\-\s]*', '', stripped).strip()
                    result.append(Paragraph(
                        f'<font color="#8B1A1A"><b>{md_inline(clean)}</b></font>', s['body']
                    ))
                    continue
        return result

    # Try to parse as column-aligned ASCII table (multi-column with headers)
    ascii_headers, ascii_rows = parse_ascii_table(lines)
    if ascii_headers and ascii_rows and len(ascii_headers) >= 3:
        result = []
        # Add title from before separator
        for idx, line in enumerate(lines):
            if '═' in line:
                if idx > 0 and lines[idx - 1].strip():
                    result.append(Paragraph(md_inline(lines[idx - 1].strip()), s['h3']))
                    result.append(Spacer(1, 4))
                break
        result.append(make_data_table(ascii_headers, ascii_rows, s))
        # Add any trailing tree/text content after a blank line (e.g. KEY RISK:)
        after_blank = False
        for line in lines:
            if not line.strip():
                after_blank = True
                continue
            if after_blank:
                stripped = line.strip()
                if stripped.startswith(('├', '└')):
                    clean = re.sub(r'[├│└─┌┐┘┬┴┼]', '', stripped).strip()
                    clean = re.sub(r'^[\-\s]+', '', clean).strip()
                    if clean:
                        depth = 1 if '│   ' in line or '    └' in line or '    ├' in line else 0
                        style = s['sub_bullet'] if depth > 0 else s['bullet']
                        result.append(Paragraph(f'<bullet>&bull;</bullet> {md_inline(clean)}', style))
                elif stripped.startswith('│'):
                    clean = re.sub(r'[├│└─]', '', stripped).strip()
                    clean = re.sub(r'^[\-\s]+', '', clean).strip()
                    if clean:
                        result.append(Paragraph(f'<bullet>&bull;</bullet> {md_inline(clean)}', s['sub_bullet']))
                elif stripped.endswith(':'):
                    result.append(Spacer(1, 4))
                    result.append(Paragraph(md_inline(stripped), s['body_bold']))
                elif stripped:
                    result.append(Paragraph(md_inline(stripped), s['body']))
        return result

    # Check for tree structure (├── └── │)
    tree_lines = [l for l in lines if '├' in l or '└' in l or '│' in l]
    if tree_lines and len(tree_lines) >= 2:
        return _parse_tree_block(lines, s)

    # Check for numbered/status list (1. ✅, 2. ⏳, etc.)
    status_lines = [l for l in stripped_lines if re.match(r'^\d+\.?\s*(✅|⬅️|⏳|☐|☑|→|DONE|NOW|PENDING)', l.strip())]
    if status_lines and len(status_lines) >= 3:
        return _parse_status_list(lines, s)

    # Fall back to rendering as a styled code block / callout
    return _render_as_callout(lines, s)


def _parse_key_value_block(lines):
    """Extract key:value pairs from code block lines.
    Handles multi-line values, tree items with values, and continuation lines."""
    pairs = []
    non_blank = [l for l in lines if l.strip() and '═' not in l.strip()]

    # Reject blocks that look like ASCII art (iceberg, box drawing)
    art_chars = sum(1 for l in non_blank if any(c in l for c in '╱╲╭╮╰╯┌┐└┘████▓░'))
    if art_chars > len(non_blank) * 0.3:
        return []

    # Reject blocks with LOOP / multi-paragraph structure
    loop_labels = sum(1 for l in non_blank if re.match(r'^LOOP \d', l.strip()))
    if loop_labels >= 2:
        return []

    # Find the separator line -- everything before it is the title, skip it
    sep_idx = -1
    for i, line in enumerate(lines):
        if '═' in line:
            sep_idx = i
            break
    content_start = sep_idx + 1 if sep_idx >= 0 else 0

    for i, line in enumerate(lines):
        # Skip everything before (and including) the separator -- those are title lines
        if i <= sep_idx and sep_idx >= 0:
            continue
        stripped = line.strip()
        if not stripped or '═' in stripped or stripped.startswith('#'):
            continue
        # Skip title lines (all caps, no colon, short)
        if _is_title_line(stripped):
            continue

        # Skip lines that are clearly continuation text (indented significantly)
        indent = len(line) - len(line.lstrip())
        if indent >= 8 and pairs:
            # Continuation of previous value
            pairs[-1][1] = pairs[-1][1] + ' ' + stripped
            continue

        # Handle tree items with value data (├── Key   value)
        if stripped.startswith(('├', '└')):
            clean = re.sub(r'[├│└─┌┐┘┬┴┼]', '', stripped).strip()
            clean = re.sub(r'^[\-\s]+', '', clean).strip()
            if not clean:
                continue
            # Check for "key   value" pattern (4+ space gap)
            tree_match = re.match(r'^(.{2,30})\s{4,}(.+)$', clean)
            if tree_match:
                key = '\u2588\u2588\u2588 ' + tree_match.group(1).strip()
                val = tree_match.group(2).strip()
                pairs.append([key, val])
                continue
            # No value gap -- skip tree items that are just labels
            continue
        # Skip continuation tree lines
        if stripped.startswith('│'):
            continue

        # Match "Key: Value" patterns (at least one space after colon)
        match = re.match(r'^([^:├│└╱╲\n]{2,40}):\s+(.+)$', stripped)
        if match:
            key = match.group(1).strip()
            val = match.group(2).strip()
            pairs.append([key, val])
            continue
        # Match "Key    Value" with large whitespace gap (4+ spaces)
        match2 = re.match(r'^(\S[^\t]{2,30})\s{4,}(.+)$', stripped)
        if match2:
            key = match2.group(1).strip()
            val = match2.group(2).strip()
            pairs.append([key, val])

    if len(pairs) < 2:
        return []

    # Heuristic: if values consistently contain 3+ space-separated groups with
    # consistent column alignment, this is likely a multi-column ASCII table
    # being misread as key:value. Reject it so the ASCII table parser can try.
    # But first strip arrow annotations (← ...) which are just inline comments.
    multi_col_vals = 0
    for key, val in pairs:
        # Strip ← annotations before checking column structure
        clean_val = re.sub(r'\s*←.*$', '', val).strip()
        # Check if the clean value has multiple distinct groups separated by 3+ spaces
        groups = re.split(r'\s{3,}', clean_val)
        if len(groups) >= 2:
            multi_col_vals += 1
    if multi_col_vals >= len(pairs) * 0.5 and len(pairs) >= 3:
        return []

    return pairs


def _parse_two_column_block(lines, left_header, right_header):
    """Parse a two-column comparison block."""
    left_items = []
    right_items = []

    started = False
    for line in lines:
        if left_header in line and right_header in line:
            started = True
            continue
        if '═' in line:
            started = True
            continue
        if not started:
            continue
        if not line.strip():
            continue

        parts = re.split(r'  {2,}', line)
        if len(parts) >= 2:
            l = parts[0].strip()
            r = parts[1].strip()
            if l:
                left_items.append(l)
            if r:
                right_items.append(r)

    return left_items, right_items


def _parse_scenario_matrix(lines, s):
    """Parse a 2x2 scenario matrix into a proper grid table."""
    flowables = []

    # Extract title
    title = None
    for i, line in enumerate(lines):
        if '═' in line:
            if i > 0 and lines[i-1].strip():
                title = lines[i-1].strip()
            break

    if title:
        flowables.append(Paragraph(md_inline(title), s['h3']))
        flowables.append(Spacer(1, 4))

    # Find the column headers (CREDIT HOLDS, CREDIT CRACKS)
    # and row headers (DC PERMITS CLEAR, DC PERMITS BLOCKED)
    # Parse the 2x2 grid content
    text = '\n'.join(lines)

    # Find the header line with column labels
    col_headers = []
    row_data = []  # [(row_header, [cell1, cell2])]
    col_split_pos = None

    for line in lines:
        if 'CREDIT HOLDS' in line and 'CREDIT CRACKS' in line:
            # Find the position where columns split
            holds_pos = line.find('CREDIT HOLDS')
            cracks_pos = line.find('CREDIT CRACKS')
            col_headers = ['', 'CREDIT HOLDS', 'CREDIT CRACKS']
            col_split_pos = cracks_pos
            break

    if not col_split_pos:
        return _render_as_callout(lines, s)

    # Now parse the rows -- collect multi-line cells
    # Row 1: DC PERMITS CLEAR
    # Row 2: DC PERMITS BLOCKED
    current_row_header = None
    current_left = []
    current_right = []
    rows = []

    in_data = False
    for line in lines:
        if 'CREDIT HOLDS' in line and 'CREDIT CRACKS' in line:
            in_data = True
            continue
        if not in_data or '═' in line:
            continue

        stripped = line.strip()
        if not stripped:
            continue

        # Check for special annotation line
        if '←' in stripped or '→' in stripped:
            # This is the "WE ARE HERE" annotation -- skip for table, add after
            continue

        # Detect row header (starts at left margin, usually "DC PERMITS ...")
        if stripped.startswith('DC PERMITS'):
            # Save previous row if any
            if current_row_header and (current_left or current_right):
                rows.append((current_row_header,
                             ' '.join(current_left),
                             ' '.join(current_right)))

            # Extract the row sub-header on this line
            left_part = line[:col_split_pos].strip()
            right_part = line[col_split_pos:].strip() if col_split_pos < len(line) else ''

            # The row header is "DC PERMITS" + next word (CLEAR/BLOCKED)
            current_row_header = left_part
            current_left = []
            current_right = [right_part] if right_part else []
            continue

        # Check the next line after "DC PERMITS XXX" which has the secondary label
        # like "CLEAR" or "BLOCKED"
        if stripped in ('CLEAR', 'BLOCKED'):
            if current_row_header:
                current_row_header += ' ' + stripped
            # Also grab cell content from this line
            left_part = line[:col_split_pos].strip()
            right_part = line[col_split_pos:].strip() if col_split_pos < len(line) else ''
            # Only add the cell content, not the header label
            if left_part and left_part != stripped:
                current_left.append(left_part)
            if right_part:
                current_right.append(right_part)
            continue

        # Regular content line -- split at column position
        left_part = line[:col_split_pos].strip() if len(line) > 0 else ''
        right_part = line[col_split_pos:].strip() if col_split_pos < len(line) else ''

        if left_part:
            current_left.append(left_part)
        if right_part:
            current_right.append(right_part)

    # Save last row
    if current_row_header and (current_left or current_right):
        rows.append((current_row_header,
                     ' '.join(current_left),
                     ' '.join(current_right)))

    if not rows:
        return _render_as_callout(lines, s)

    # Build the table
    header = [Paragraph('', s['table_header']),
              Paragraph(esc('CREDIT HOLDS'), s['table_header']),
              Paragraph(esc('CREDIT CRACKS'), s['table_header'])]

    data = [header]
    for row_header, left_cell, right_cell in rows:
        data.append([
            Paragraph(esc(row_header), s['table_cell_bold']),
            Paragraph(esc(left_cell), s['table_cell']),
            Paragraph(esc(right_cell), s['table_cell']),
        ])

    col_w = [CONTENT_W * 0.22, CONTENT_W * 0.39, CONTENT_W * 0.39]
    t = Table(data, colWidths=col_w, repeatRows=1)

    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEAD),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, NAVY),
        ('LINEBELOW', (0, -1), (-1, -1), 1, NAVY),
        ('LINEBEFORE', (1, 0), (1, -1), 0.5, RULE_COLOR),
        ('LINEBEFORE', (2, 0), (2, -1), 0.5, RULE_COLOR),
    ]
    if len(data) > 2:
        style_cmds.append(('LINEBELOW', (0, 1), (-1, -2), 0.5, RULE_COLOR))
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), TABLE_ALT))

    t.setStyle(TableStyle(style_cmds))
    flowables.append(t)

    # Add the annotation line
    annotation = None
    for line in lines:
        if '←' in line or 'WE ARE' in line:
            annotation = line.strip()
            break
    if annotation:
        flowables.append(Spacer(1, 4))
        flowables.append(Paragraph(
            f'<font color="#8B1A1A"><b>{esc(annotation)}</b></font>',
            s['body']
        ))

    return flowables


def _parse_tree_block(lines, s):
    """Convert tree-structured code blocks into bullet lists."""
    flowables = []

    # Check for a title before the tree
    title = None
    tree_start = 0
    for i, line in enumerate(lines):
        if '═' in line:
            if i > 0 and lines[i - 1].strip():
                title = lines[i - 1].strip()
            tree_start = i + 1
            break
        if '├' in line or '└' in line:
            tree_start = i
            break

    if title:
        flowables.append(Paragraph(md_inline(title), s['h3']))
        flowables.append(Spacer(1, 4))

    for line in lines[tree_start:]:
        stripped = line.strip()
        if not stripped or '═' in stripped:
            continue

        # Determine indent level
        depth = 0
        if '│   └' in line or '│   ├' in line or '    └' in line or '    ├' in line:
            depth = 1

        # Clean the tree characters
        clean = re.sub(r'[├│└─┌┐┘┬┴┼]', '', stripped).strip()
        clean = re.sub(r'^[\-\s]+', '', clean).strip()
        if not clean:
            continue

        style = s['sub_bullet'] if depth > 0 else s['bullet']
        flowables.append(Paragraph(f'<bullet>&bull;</bullet> {md_inline(clean)}', style))

    return flowables


def _parse_labeled_sections_block(lines, s):
    """Parse code blocks that have labeled subsections (LOOP 1:, LOOP 2:, etc.)
    each followed by descriptive text and tree items."""
    flowables = []

    # Extract title
    title = None
    content_start = 0
    for i, line in enumerate(lines):
        if '═' in line:
            if i > 0 and lines[i-1].strip():
                title = lines[i-1].strip()
            content_start = i + 1
            break

    if title:
        flowables.append(Paragraph(md_inline(title), s['h3']))
        flowables.append(Spacer(1, 4))

    # Parse sections: each starts with a LABEL: line (e.g. LOOP 1: DIRECT FUNDING STRESS)
    current_label = None
    current_description = []
    current_items = []
    sections = []

    def flush_section():
        if current_label:
            sections.append({
                'label': current_label,
                'description': ' '.join(current_description),
                'items': list(current_items)
            })

    for line in lines[content_start:]:
        stripped = line.strip()
        if not stripped or '═' in stripped:
            continue

        # Detect section label (LOOP N: ..., RING N: ..., STEP N: ..., etc.)
        label_match = re.match(r'^(LOOP|RING|STEP|PHASE|STAGE)\s+\d+[A-Z]?:\s*(.+)$', stripped)
        if label_match:
            flush_section()
            current_label = stripped
            current_description = []
            current_items = []
            continue

        # Tree items
        if stripped.startswith(('├', '└', '│')):
            clean = re.sub(r'[├│└─┌┐┘┬┴┼]', '', stripped).strip()
            clean = re.sub(r'^[\-\s]+', '', clean).strip()
            if clean:
                depth = 1 if '│   ' in line or '    └' in line or '    ├' in line else 0
                current_items.append((clean, depth))
            continue

        # Description text
        if current_label is not None:
            current_description.append(stripped)

    flush_section()

    if not sections:
        return _render_as_callout(lines, s)

    # Render each section as a callout-style block
    for sec in sections:
        # Section label as bold header
        flowables.append(Paragraph(
            f'<font color="#8B1A1A"><b>{esc(sec["label"])}</b></font>',
            s['body_bold']
        ))
        # Description
        if sec['description']:
            flowables.append(Paragraph(md_inline(sec['description']), s['body']))
        # Tree items
        for item_text, depth in sec['items']:
            style = s['sub_bullet'] if depth > 0 else s['bullet']
            flowables.append(Paragraph(f'<bullet>&bull;</bullet> {md_inline(item_text)}', style))
        flowables.append(Spacer(1, 6))

    return flowables


def _parse_status_list(lines, s):
    """Parse a numbered status list into a timeline table."""
    rows = []
    for line in lines:
        stripped = line.strip()
        if not stripped or '═' in stripped:
            continue
        # Match: 1. ✅ Event text   Timing
        match = re.match(r'^(\d+)\.?\s*(✅|⬅️|⏳|☐|☑)\s*(.+)$', stripped)
        if match:
            num = match.group(1)
            status_emoji = match.group(2)
            rest = match.group(3).strip()
            status = {'✅': 'Complete', '⬅️': 'NOW', '⏳': 'Pending', '☐': 'Pending', '☑': 'Complete'}.get(status_emoji, status_emoji)

            # Try to split event and timing
            parts = re.split(r'  {2,}', rest)
            if len(parts) >= 2:
                event = parts[0].strip()
                timing = parts[1].strip()
            else:
                event = rest
                timing = ''
            rows.append([num, status, event, timing])

    if rows:
        return [_make_timeline_table(rows, s)]
    return []


def _make_timeline_table(rows, s):
    """Create a timeline table with status indicators."""
    header = [Paragraph('#', s['table_header']),
              Paragraph('Status', s['table_header']),
              Paragraph('Event', s['table_header']),
              Paragraph('Timing', s['table_header'])]

    data = [header]
    for row in rows:
        cells = [
            Paragraph(esc(str(row[0])), s['table_cell_bold']),
            Paragraph(esc(str(row[1])), s['table_cell']),
            Paragraph(esc(str(row[2])), s['table_cell']),
            Paragraph(esc(str(row[3])), s['table_cell']),
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
    ]
    if len(data) > 2:
        style_cmds.append(('LINEBELOW', (0, 1), (-1, -2), 0.5, RULE_COLOR))

    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), TABLE_ALT))
        status = rows[i - 1][1] if i - 1 < len(rows) else ""
        if 'Complete' in status or 'DONE' in status:
            style_cmds.append(('TEXTCOLOR', (1, i), (1, i), HexColor("#1B5E20")))
        elif 'NOW' in status:
            style_cmds.append(('TEXTCOLOR', (1, i), (1, i), ACCENT))
        elif 'Pending' in status:
            style_cmds.append(('TEXTCOLOR', (1, i), (1, i), MUTED))

    t.setStyle(TableStyle(style_cmds))
    return t


def _render_ascii_art_block(lines, s):
    """Render ASCII art (iceberg diagrams, box drawings) as a styled callout
    with line-by-line preserved formatting using monospace font."""
    flowables = []

    # Extract title if present (line before ═══)
    title = None
    content_start = 0
    for i, line in enumerate(lines):
        if '═' in line:
            if i > 0 and lines[i - 1].strip():
                potential_title = lines[i - 1].strip()
                if len(potential_title) < 80:
                    title = potential_title
                    content_start = i + 1
            else:
                content_start = i + 1
            break

    if title:
        flowables.append(Paragraph(md_inline(title), s['h3']))
        flowables.append(Spacer(1, 4))

    # Collect content lines, skipping separator lines
    content_lines = []
    for line in lines[content_start:]:
        stripped = line.strip()
        if '═' in stripped:
            # Keep short separators that are part of the art (e.g. ═══ within iceberg)
            if len(stripped) < 50:
                content_lines.append(line)
            continue
        content_lines.append(line)

    if not content_lines:
        content_lines = [l for l in lines if '═' not in l or len(l.strip()) < 50]

    # Render each line in monospace to preserve the art layout
    art_text_parts = []
    for line in content_lines:
        if not line.strip():
            continue
        escaped = esc(line.rstrip())
        # Replace spaces with non-breaking spaces for alignment
        escaped = escaped.replace('  ', '&nbsp;&nbsp;')
        art_text_parts.append(escaped)

    if art_text_parts:
        art_html = '<br/>'.join(art_text_parts)
        art_style = ParagraphStyle(
            'AsciiArt', fontName='Courier', fontSize=7.5, leading=10,
            textColor=TEXT_COLOR, alignment=TA_LEFT,
        )
        flowables.append(CalloutBox(
            f'<font face="Courier" size="7.5">{art_html}</font>',
            CONTENT_W, s['callout'], LIGHT_GRAY, ACCENT
        ))

    return flowables


def _render_as_callout(lines, s):
    """Render a code block as a styled callout box with preserved formatting."""
    flowables = []

    # Extract title if present (line before ═══)
    title = None
    content_start = 0
    for i, line in enumerate(lines):
        if '═' in line:
            if i > 0 and lines[i - 1].strip():
                potential_title = lines[i - 1].strip()
                if len(potential_title) < 80:
                    title = potential_title
                    content_start = i + 1
            else:
                content_start = i + 1
            break

    if title:
        flowables.append(Paragraph(md_inline(title), s['h3']))
        flowables.append(Spacer(1, 4))

    # Collect content lines
    content_lines = []
    for line in lines[content_start:]:
        stripped = line.strip()
        if '═' in stripped:
            continue
        content_lines.append(line)

    if not content_lines:
        content_lines = [l for l in lines if '═' not in l]

    # Render as bullet points where possible, otherwise as body text
    current_text = []

    def flush_text():
        if current_text:
            combined = ' '.join(current_text)
            flowables.append(Paragraph(md_inline(combined), s['body']))
            current_text.clear()

    for line in content_lines:
        stripped = line.strip()
        if not stripped:
            flush_text()
            continue

        # Tree items as bullets
        if stripped.startswith(('├──', '└──', '│', '- ', '• ')):
            flush_text()
            clean = re.sub(r'^[├│└─┌┐┘┬┴┼•\-\s]+', '', stripped).strip()
            if clean:
                depth = 1 if line.startswith('   ') or '│   ' in line else 0
                style = s['sub_bullet'] if depth else s['bullet']
                flowables.append(Paragraph(f'<bullet>&bull;</bullet> {md_inline(clean)}', style))
        elif stripped.startswith('^--') or stripped.startswith('^^'):
            flush_text()
            clean = re.sub(r'^[\^]+[\-\s]*', '', stripped).strip()
            flowables.append(Paragraph(f'<font color="#8B1A1A"><b>{md_inline(clean)}</b></font>', s['body']))
        else:
            current_text.append(stripped)

    flush_text()
    return flowables


# ─── MAIN PARSER ─────────────────────────────────────────────────────────────

def extract_metadata(lines):
    """Extract title, subtitle, and metadata from the top of the document."""
    title = ""
    subtitle_parts = []
    meta_end = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('# ') and not stripped.startswith('## '):
            title = stripped[2:].strip()
            meta_end = i + 1
            continue
        if i <= 5 and stripped.startswith('**') and ':' in stripped:
            # Metadata line like **Date:** 2026-03-02
            clean = re.sub(r'\*\*', '', stripped)
            subtitle_parts.append(clean)
            meta_end = i + 1
            continue
        if stripped == '---' and i <= 8:
            meta_end = i + 1
            break
        if stripped.startswith('## '):
            break

    subtitle = ' | '.join(subtitle_parts) if subtitle_parts else ''
    return title, subtitle, meta_end


def extract_sections(lines):
    """Extract ## section headings for the TOC (exclude 'Key Sources' / 'References')."""
    sections = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('## '):
            heading = stripped[3:].strip()
            lower = heading.lower()
            if lower.startswith('key source') or lower.startswith('reference') or lower.startswith('source'):
                continue
            sections.append(heading)
    return sections


def parse_markdown(md_text):
    """Parse markdown text into a list of (type, content) tuples."""
    lines = md_text.split('\n')
    title, subtitle, meta_end = extract_metadata(lines)
    sections = extract_sections(lines)

    elements = []
    elements.append(('meta', {'title': title, 'subtitle': subtitle, 'sections': sections}))

    i = meta_end
    in_code_block = False
    code_lines = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Code fence
        if stripped.startswith('```'):
            if in_code_block:
                elements.append(('code_block', code_lines))
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Horizontal rule
        if stripped == '---' or stripped == '***' or stripped == '___':
            # Skip -- we use section headings for visual breaks
            i += 1
            continue

        # Empty line
        if not stripped:
            i += 1
            continue

        # Headings
        if stripped.startswith('## ') and not stripped.startswith('### '):
            # Check if this is a "thesis" section (special callout)
            heading = stripped[3:].strip()
            if 'thesis in one' in heading.lower():
                # Next non-empty line is the thesis
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines):
                    elements.append(('thesis', lines[j].strip()))
                    i = j + 1
                    continue
            elements.append(('h2', heading))
            i += 1
            continue

        if stripped.startswith('### '):
            elements.append(('h3', stripped[4:].strip()))
            i += 1
            continue

        if stripped.startswith('#### '):
            elements.append(('h4', stripped[5:].strip()))
            i += 1
            continue

        # Pipe tables
        if '|' in stripped and not stripped.startswith('>'):
            table_lines = []
            j = i
            while j < len(lines) and '|' in lines[j].strip():
                table_lines.append(lines[j])
                j += 1
            if len(table_lines) >= 3:
                headers, rows = parse_pipe_table(table_lines)
                if headers and rows:
                    elements.append(('pipe_table', {'headers': headers, 'rows': rows}))
                    i = j
                    continue

        # Blockquotes
        if stripped.startswith('>'):
            quote_text = stripped[1:].strip()
            # Collect multi-line quote
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith('>'):
                quote_text += ' ' + lines[j].strip()[1:].strip()
                j += 1
            elements.append(('quote', quote_text))
            i = j
            continue

        # Bullet lists
        if stripped.startswith('- ') or stripped.startswith('* '):
            text = stripped[2:].strip()
            indent = len(line) - len(line.lstrip())
            elements.append(('bullet', {'text': text, 'indent': indent}))
            i += 1
            continue

        # Numbered lists
        match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if match:
            elements.append(('numbered', {'num': match.group(1), 'text': match.group(2)}))
            i += 1
            continue

        # Bold paragraph (starts with **...**)
        if stripped.startswith('**') and ':**' in stripped:
            elements.append(('bold_label', stripped))
            i += 1
            continue

        # Regular paragraph
        para_lines = [stripped]
        j = i + 1
        while j < len(lines):
            next_line = lines[j].strip()
            if not next_line or next_line.startswith('#') or next_line.startswith('```') or \
               next_line.startswith('- ') or next_line.startswith('* ') or \
               next_line.startswith('>') or next_line == '---' or '|' in next_line:
                break
            para_lines.append(next_line)
            j += 1

        elements.append(('paragraph', ' '.join(para_lines)))
        i = j

    return elements


# ─── DOCUMENT BUILDER ────────────────────────────────────────────────────────

def build_pdf(md_text, output_path):
    """Convert markdown text to a premium PDF."""
    elements = parse_markdown(md_text)
    s = build_styles()

    # Extract metadata
    meta = None
    for etype, content in elements:
        if etype == 'meta':
            meta = content
            break

    doc_title = meta['title'] if meta else 'Document'

    doc = DocTemplate(
        output_path,
        doc_title=doc_title,
        pagesize=letter,
        title=doc_title,
        author="Perplexity Computer",
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
    )

    story = []

    # ── COVER PAGE ──
    story.append(Spacer(1, 1.8 * inch))
    story.append(ThickRule(CONTENT_W, NAVY, 3))
    story.append(Spacer(1, 12))

    # Split title into lines if it's long
    if meta and meta['title']:
        title_text = meta['title']
        # Try to split on : or - for a subtitle effect
        if ':' in title_text:
            parts = title_text.split(':', 1)
            story.append(Paragraph(md_inline(parts[0].strip()), s['title']))
            sub_style = ParagraphStyle('TitleSub', parent=s['title'], fontSize=18, leading=24, textColor=MED_BLUE)
            story.append(Paragraph(md_inline(parts[1].strip()), sub_style))
        else:
            story.append(Paragraph(md_inline(title_text), s['title']))

    story.append(Spacer(1, 8))
    story.append(ThinRule(CONTENT_W * 0.4, ACCENT, 1.5))
    story.append(Spacer(1, 14))

    if meta and meta['subtitle']:
        story.append(Paragraph(md_inline(meta['subtitle']), s['subtitle']))

    story.append(Spacer(1, 30))
    story.append(ThickRule(CONTENT_W, NAVY, 1.5))
    story.append(Spacer(1, 20))

    # Check for thesis element
    for etype, content in elements:
        if etype == 'thesis':
            story.append(CalloutBox(
                f'<b>THE THESIS:</b> {md_inline(content)}',
                CONTENT_W, s['callout'], LIGHT_GRAY, ACCENT
            ))
            story.append(Spacer(1, 30))
            break

    # Table of contents
    if meta and meta['sections']:
        toc_style = ParagraphStyle('MiniTOC', fontName='Helvetica', fontSize=9,
                                    leading=16, textColor=DARK_GRAY, leftIndent=4)
        toc_header = ParagraphStyle('TOCHead', fontName='Helvetica-Bold', fontSize=10,
                                     leading=14, textColor=NAVY, spaceAfter=8)
        story.append(Paragraph("Contents", toc_header))
        story.append(ThinRule(CONTENT_W * 0.15, ACCENT, 1))
        story.append(Spacer(1, 6))
        for section in meta['sections']:
            story.append(Paragraph(md_inline(section), toc_style))

    story.append(NextPageTemplate('Normal'))
    story.append(PageBreak())

    # ── BODY ──
    is_sources_section = False

    for etype, content in elements:
        if etype == 'meta' or etype == 'thesis':
            continue

        if etype == 'h2':
            is_sources_section = 'source' in content.lower() or 'reference' in content.lower()
            story.append(Paragraph(md_inline(content), s['h1']))
            story.append(AccentBar())
            story.append(Spacer(1, 8))

        elif etype == 'h3':
            story.append(Paragraph(md_inline(content), s['h2']))
            story.append(Spacer(1, 4))

        elif etype == 'h4':
            story.append(Paragraph(md_inline(content), s['h3']))
            story.append(Spacer(1, 3))

        elif etype == 'paragraph':
            story.append(Paragraph(md_inline(content), s['body']))

        elif etype == 'bold_label':
            if is_sources_section:
                # Source section headers
                clean = re.sub(r'\*\*', '', content).rstrip(':')
                story.append(Paragraph(md_inline(clean), s['source_header']))
            else:
                story.append(Paragraph(md_inline(content), s['body_bold']))

        elif etype == 'bullet':
            text = content['text']
            indent = content.get('indent', 0)
            if is_sources_section:
                story.append(Paragraph(f'<bullet>&bull;</bullet> {md_inline(text)}', s['source_item']))
            elif indent > 2:
                story.append(Paragraph(f'<bullet>&bull;</bullet> {md_inline(text)}', s['sub_bullet']))
            else:
                story.append(Paragraph(f'<bullet>&bull;</bullet> {md_inline(text)}', s['bullet']))

        elif etype == 'numbered':
            story.append(Paragraph(f'<b>{content["num"]}.</b> {md_inline(content["text"])}', s['bullet']))

        elif etype == 'quote':
            story.append(Paragraph(f'<i>{md_inline(content)}</i>', s['quote']))

        elif etype == 'pipe_table':
            table = make_data_table(content['headers'], content['rows'], s)
            story.append(table)
            story.append(Spacer(1, 8))

        elif etype == 'code_block':
            code_flowables = parse_code_block_content(content, s)
            story.extend(code_flowables)
            story.append(Spacer(1, 8))

    doc.build(story)
    return output_path


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Convert Markdown white papers into premium academic-style PDFs.',
        epilog='Example: python md2pdf.py my-thesis.md -o my-thesis.pdf'
    )
    parser.add_argument('input', help='Path to the input Markdown file')
    parser.add_argument('-o', '--output', help='Output PDF path (default: same name as input with .pdf extension)')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}")
        sys.exit(1)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        base = os.path.splitext(args.input)[0]
        output_path = base + '.pdf'

    # Read input
    with open(args.input, 'r', encoding='utf-8') as f:
        md_text = f.read()

    print(f"Converting: {args.input}")
    print(f"Output:     {output_path}")

    result = build_pdf(md_text, output_path)
    print(f"Done! PDF generated: {result}")


if __name__ == '__main__':
    main()
