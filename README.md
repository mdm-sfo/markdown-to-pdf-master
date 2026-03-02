# Markdown to PDF Master

Convert Markdown white papers into premium academic-style PDFs -- the kind that look like they came out of a Harvard PhD's office.

## Features

- **Academic Color Palette** -- Dark navy (#0D1B2A) headers, Harvard crimson (#8B1A1A) accents, off-white backgrounds
- **Professional Tables** -- Dark header rows, alternating row colors, proper padding, color-coded status indicators
- **Custom Flowables** -- Callout boxes with left accent bars, thin/thick rules, accent bars for section emphasis
- **Cover Page** -- Title, subtitle, thesis callout, and mini table of contents
- **Header/Footer** -- Running header with document title + date, page numbers, confidential classification
- **Scenario Matrices** -- Color-coded 2x2 risk grids (green/yellow/red tints)
- **Winners/Losers Tables** -- Two-column layout with green and crimson headers
- **Timeline Tables** -- Status-coded cascade tables with color-coded status (Complete/NOW/Pending)

## Design

| Element | Color | Hex |
|---------|-------|-----|
| Navy (headers, rules) | Dark Navy | `#0D1B2A` |
| Table Headers | Dark Blue | `#1B2A4A` |
| Accent (section bars) | Harvard Crimson | `#8B1A1A` |
| Highlight | Dark Goldenrod | `#B8860B` |
| Alternating Rows | Off-white | `#F0EDE6` |
| Body Text | Near Black | `#1A1A1A` |

## Quick Start

```bash
pip install reportlab
python generate_pdf.py
```

The script generates a PDF in the same directory. Modify `build_document()` to swap in your own content.

## Structure

```
generate_pdf.py          # Main script -- all styling + content
├── Color Palette        # Navy/crimson/gold constants
├── Custom Flowables     # ThinRule, ThickRule, AccentBar, CalloutBox
├── Styles               # 20+ ParagraphStyles for every element type
├── DocTemplate          # Cover page + normal page templates w/ headers/footers
├── Table Builders       # make_data_table, make_two_column_table, make_scenario_matrix, make_timeline_table
└── build_document()     # Content assembly -- swap this for your own paper
```

## Reusable Components

The script is designed so you can extract the styling toolkit and apply it to any white paper:

- **`build_styles()`** -- Returns a dict of 20+ paragraph styles
- **`make_data_table(headers, rows, col_widths, styles_dict)`** -- Any structured data table
- **`make_two_column_table(left_header, right_header, left_items, right_items, styles_dict)`** -- Comparison tables
- **`make_scenario_matrix(styles_dict)`** -- 2x2 risk/scenario grids
- **`make_timeline_table(rows, styles_dict)`** -- Status-tracked event sequences
- **`CalloutBox(text, width, style, bg_color, accent_color)`** -- Highlighted insight boxes
- **`AccentBar(width, color, thickness)`** -- Section emphasis bars

## Sample

The included `generate_pdf.py` contains a complete 17-page trading thesis on Private Credit & AI Infrastructure as a demonstration of the formatting capabilities.

## Requirements

- Python 3.8+
- ReportLab

## License

MIT
