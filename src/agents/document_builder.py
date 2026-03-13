"""
DivAi — Document Builder (Phase 5)

WHAT THIS FILE DOES:
  Takes ProposalContent (structured data from the Proposal Agent)
  and renders it into a formatted Word document using python-docx.

CONCEPT: python-docx Fundamentals
------------------------------------
python-docx lets you create and edit Word (.docx) files programmatically.
The key building blocks are:

  Document    The root object. Everything gets added to it.
  Paragraph   A block of text (can have mixed formatting within it).
  Run         A contiguous run of text with the same formatting.
              Multiple runs make up one paragraph.
  Heading     A paragraph with a special heading style (Heading 1, 2, 3).
  Table       Grid of cells, each containing paragraphs.
  Style       A named bundle of formatting (font, size, spacing, colour).

The rendering flow:
  ProposalContent fields
       |
       v
  document_builder.py reads each field
       |
       v
  python-docx methods add content with the right styles
       |
       v
  doc.save("proposal.docx") writes the file

CONCEPT: Styles in Word Documents
------------------------------------
Word documents use named styles, not inline CSS.
'Normal' = body text
'Heading 1' = top-level section heading
'Heading 2' = sub-section heading
'List Bullet' = bulleted list item
'List Number' = numbered list item
'Table Grid' = standard table style
When you apply a style, Word handles the font, size, spacing automatically.
"""

import os
import re
from datetime import date
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from agents.proposal_agent import ProposalContent, OUTPUT_DIR as DEFAULT_OUTPUT_DIR


# ---------------------------------------------------------------------------
# Colour palette — consistent brand feel throughout the document
# ---------------------------------------------------------------------------
# CONCEPT: RGBColor in python-docx
# Colours are specified as RGBColor(R, G, B) where each is 0-255.
# We define them once here so changing the palette is a single edit.

COLOUR_PRIMARY   = RGBColor(0x1A, 0x56, 0xDB)   # Deep blue — headings
COLOUR_ACCENT    = RGBColor(0x10, 0x7C, 0x41)    # Green — success/value items
COLOUR_MUTED     = RGBColor(0x6B, 0x72, 0x80)    # Grey — metadata text
COLOUR_TABLE_HDR = RGBColor(0x1E, 0x3A, 0x5F)    # Dark navy — table headers


# ---------------------------------------------------------------------------
# Helper functions — reusable formatting primitives
# ---------------------------------------------------------------------------

def add_heading(doc: Document, text: str, level: int = 1) -> None:
    """
    Add a styled section heading.

    CONCEPT: Heading Levels
    Level 1 = major section (e.g. "1. Executive Summary")
    Level 2 = sub-section within a major section
    python-docx maps these to Word's built-in Heading 1/2/3 styles.
    """
    para = doc.add_heading(text, level=level)
    # Override the heading colour to our brand blue
    for run in para.runs:
        run.font.color.rgb = COLOUR_PRIMARY


def add_body_text(doc: Document, text: str) -> None:
    """Add a normal body paragraph."""
    doc.add_paragraph(text, style="Normal")


def add_bullet(doc: Document, text: str) -> None:
    """Add a bulleted list item."""
    doc.add_paragraph(text, style="List Bullet")


def add_numbered(doc: Document, text: str) -> None:
    """Add a numbered list item."""
    doc.add_paragraph(text, style="List Number")


def add_section_divider(doc: Document) -> None:
    """Add visual spacing between sections."""
    doc.add_paragraph()  # Empty paragraph as spacer


def add_metadata_line(doc: Document, label: str, value: str) -> None:
    """
    Add a 'Label: value' line with the label in bold.

    CONCEPT: Runs for Mixed Formatting
    One paragraph can contain multiple "runs", each with different formatting.
    Here we use two runs: one bold (label) and one normal (value).
    """
    para = doc.add_paragraph()
    bold_run = para.add_run(f"{label}: ")
    bold_run.bold = True
    bold_run.font.color.rgb = COLOUR_MUTED
    value_run = para.add_run(value)
    value_run.font.color.rgb = COLOUR_MUTED


def add_effort_table(doc: Document, effort_rows: list) -> None:
    """
    Build the effort estimate table.

    CONCEPT: Tables in python-docx
    Tables are created with doc.add_table(rows, cols).
    The first row is typically a header row — we style it with a dark background.
    Each cell contains a paragraph, so you format text the same way as body text.

    row.cells[i] gives you cell i in that row.
    cell.paragraphs[0] gives you the first (and usually only) paragraph.
    para.add_run("text") adds text to the cell.
    """
    headers = ["Role", "Phase", "Weeks", "Hours", "Notes"]
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Style the header row
    hdr_row = table.rows[0]
    for i, header in enumerate(headers):
        cell = hdr_row.cells[i]
        para = cell.paragraphs[0]
        run = para.add_run(header)
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)  # White text
        # Set cell background to dark navy
        _set_cell_background(cell, "1E3A5F")

    # Add data rows
    total_hours = 0
    for row_data in effort_rows:
        row = table.add_row()
        values = [
            row_data.role,
            row_data.phase,
            str(row_data.weeks),
            str(row_data.hours),
            row_data.notes,
        ]
        for i, val in enumerate(values):
            row.cells[i].paragraphs[0].add_run(val)
        total_hours += row_data.hours

    # Add totals row
    total_row = table.add_row()
    total_run = total_row.cells[0].paragraphs[0].add_run("TOTAL")
    total_run.bold = True
    total_row.cells[3].paragraphs[0].add_run(str(total_hours)).bold = True


def _set_cell_background(cell, hex_colour: str) -> None:
    """
    Set a table cell's background colour.

    CONCEPT: Direct XML Manipulation in python-docx
    Not everything is exposed via python-docx's Python API.
    For features like cell background colour, we manipulate the
    underlying XML directly using the docx.oxml module.
    The .docx format is just a ZIP file containing XML files —
    python-docx lets us edit that XML when needed.
    This is a common pattern when python-docx's API doesn't cover
    a formatting feature you need.
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_colour)
    tcPr.append(shd)


def add_risks_table(doc: Document, risks: list) -> None:
    """Build the risks table with likelihood colour coding."""
    headers = ["Risk", "Likelihood", "Mitigation"]
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"

    hdr_row = table.rows[0]
    for i, header in enumerate(headers):
        cell = hdr_row.cells[i]
        run = cell.paragraphs[0].add_run(header)
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        _set_cell_background(cell, "1E3A5F")

    likelihood_colours = {
        "Low": "E8F5E9", "Medium": "FFF8E1", "High": "FFEBEE"
    }

    for risk_item in risks:
        row = table.add_row()
        row.cells[0].paragraphs[0].add_run(risk_item.risk)
        like_cell = row.cells[1]
        like_cell.paragraphs[0].add_run(risk_item.likelihood).bold = True
        colour = likelihood_colours.get(risk_item.likelihood, "FFFFFF")
        _set_cell_background(like_cell, colour)
        row.cells[2].paragraphs[0].add_run(risk_item.mitigation)


# ---------------------------------------------------------------------------
# Main builder function
# ---------------------------------------------------------------------------

def build_proposal_docx(content: ProposalContent,
                         output_dir: str = DEFAULT_OUTPUT_DIR) -> str:
    """
    Build a complete proposal .docx from ProposalContent.

    Returns the path to the saved file.

    CONCEPT: Document Building Order
    Word documents are sequential — you build them top to bottom.
    The order here defines the document structure:
      cover → metadata → section 1 → section 2 → ... → section 13
    """
    doc = Document()

    # --- Page margins (make them slightly narrower for professional look) ---
    section = doc.sections[0]
    section.top_margin    = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin   = Inches(1.25)
    section.right_margin  = Inches(1.25)

    # =========================================================================
    # COVER PAGE
    # =========================================================================

    # Agency name
    agency_para = doc.add_paragraph()
    agency_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    agency_run = agency_para.add_run("DivAi Engineering")
    agency_run.font.size = Pt(11)
    agency_run.font.color.rgb = COLOUR_MUTED

    doc.add_paragraph()  # Spacer

    # Project title (large, centred, bold, blue)
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_para.add_run(content.project_title)
    title_run.font.size = Pt(26)
    title_run.font.bold = True
    title_run.font.color.rgb = COLOUR_PRIMARY

    doc.add_paragraph()

    # Subtitle
    subtitle_para = doc.add_paragraph()
    subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle_run = subtitle_para.add_run("Technical Project Proposal")
    subtitle_run.font.size = Pt(14)
    subtitle_run.font.color.rgb = COLOUR_MUTED

    doc.add_paragraph()
    doc.add_paragraph()

    # Metadata block
    add_metadata_line(doc, "Prepared for", content.client_name)
    add_metadata_line(doc, "Prepared by",  content.prepared_by)
    add_metadata_line(doc, "Date",         date.today().strftime("%d %B %Y"))
    add_metadata_line(doc, "Status",       "Draft — For Client Review")

    doc.add_page_break()

    # =========================================================================
    # SECTION 1 — Executive Summary
    # =========================================================================
    add_heading(doc, "1. Executive Summary")
    add_body_text(doc, content.executive_summary)
    add_section_divider(doc)

    # =========================================================================
    # SECTION 2 — Problem Statement
    # =========================================================================
    add_heading(doc, "2. Problem Statement")
    add_body_text(doc, content.problem_statement)
    add_section_divider(doc)

    # =========================================================================
    # SECTION 3 — Proposed Architecture
    # =========================================================================
    add_heading(doc, "3. Proposed Architecture")
    add_body_text(doc, content.proposed_architecture)
    add_section_divider(doc)

    # =========================================================================
    # SECTION 4 — Technical Stack
    # =========================================================================
    add_heading(doc, "4. Technical Stack")
    for choice in content.stack_choices:
        add_bullet(doc, choice)
    add_section_divider(doc)

    # =========================================================================
    # SECTION 5 — Phase Breakdown
    # =========================================================================
    add_heading(doc, "5. Phase Breakdown & Deliverables")
    for phase in content.phase_details:
        add_bullet(doc, phase)
    add_section_divider(doc)

    # =========================================================================
    # SECTION 6 — API Specifications
    # =========================================================================
    add_heading(doc, "6. API Specifications")
    add_body_text(doc, content.api_specifications)
    add_section_divider(doc)

    # =========================================================================
    # SECTION 7 — Security & Compliance
    # =========================================================================
    add_heading(doc, "7. Security & Compliance")
    add_body_text(doc, content.security_compliance)
    add_section_divider(doc)

    # =========================================================================
    # SECTION 8 — Testing Strategy
    # =========================================================================
    add_heading(doc, "8. Testing Strategy")
    add_body_text(doc, content.testing_strategy)
    add_section_divider(doc)

    # =========================================================================
    # SECTION 9 — Deployment & DevOps
    # =========================================================================
    add_heading(doc, "9. Deployment & DevOps")
    add_body_text(doc, content.deployment_devops)
    add_section_divider(doc)

    # =========================================================================
    # SECTION 10 — Effort Estimate Table
    # =========================================================================
    add_heading(doc, "10. Effort Estimate")
    if content.effort_rows:
        add_effort_table(doc, content.effort_rows)
    add_section_divider(doc)

    # =========================================================================
    # SECTION 11 — Investment Summary
    # =========================================================================
    add_heading(doc, "11. Investment Summary")
    add_body_text(doc, content.investment_summary)
    add_section_divider(doc)

    # =========================================================================
    # SECTION 12 — Assumptions & Risks
    # =========================================================================
    add_heading(doc, "12. Assumptions & Risks")
    if content.risks:
        add_risks_table(doc, content.risks)
    add_section_divider(doc)

    # =========================================================================
    # SECTION 13 — Next Steps
    # =========================================================================
    add_heading(doc, "13. Next Steps")
    for step in content.next_steps:
        add_numbered(doc, step)

    doc.add_paragraph()

    # Footer note
    footer_para = doc.add_paragraph()
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer_para.add_run(
        "This document was generated by DivAi — "
        "AI-powered business intelligence for software agencies."
    )
    footer_run.font.size = Pt(9)
    footer_run.font.color.rgb = COLOUR_MUTED
    footer_run.font.italic = True

    # =========================================================================
    # Save the document
    # =========================================================================
    os.makedirs(output_dir, exist_ok=True)

    # Build a safe filename from the project title
    safe_title = re.sub(r'[^a-zA-Z0-9\s-]', '', content.project_title)
    safe_title = re.sub(r'\s+', '_', safe_title.strip())[:50]
    filename = f"Proposal_{safe_title}_{date.today().strftime('%Y%m%d')}.docx"
    filepath = os.path.join(output_dir, filename)

    doc.save(filepath)
    print(f"[DocBuilder] Saved: {filepath}")
    return filepath


# ---------------------------------------------------------------------------
# Full proposal runner (content generation + document building)
# ---------------------------------------------------------------------------

def run_proposal_agent(solution: dict,
                        report: dict,
                        output_dir: str = DEFAULT_OUTPUT_DIR) -> dict:
    """
    End-to-end: generate content + build document.
    Returns paths dict for the pipeline state.
    """
    from agents.proposal_agent import generate_proposal_content

    # Step 1: Generate content with Claude
    content = generate_proposal_content(solution, report)

    # Step 2: Build the Word document
    docx_path = build_proposal_docx(content, output_dir)

    return {
        "docx": docx_path,
        "pdf": None,       # WeasyPrint PDF export — Phase 7
        "notion": None,    # Notion API export — Phase 7
        "title": content.project_title,
        "client": content.client_name,
        # Full proposal content serialised for in-app preview
        "content": content.model_dump(),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json, asyncio
    from agents.ingestion_agent import scrape_website
    from agents.analysis_agent import run_analysis_agent
    from agents.use_case_agent import run_use_case_agent
    from agents.solution_agent import run_solution_agent

    url = sys.argv[1] if len(sys.argv) > 1 else "https://stripe.com"

    print(f"\n{'='*60}")
    print(f"DivAi — Full Pipeline to Proposal")
    print(f"Target: {url}")
    print(f"{'='*60}")

    print("\n[1/5] Ingestion...")
    scrape = asyncio.run(scrape_website(url, "surface"))

    print("\n[2/5] Analysis...")
    report = run_analysis_agent(scrape).model_dump()

    print("\n[3/5] Use Cases...")
    use_cases = [uc.model_dump()
                 for uc in run_use_case_agent(report).use_cases]

    print("\n[4/5] Solutions...")
    solutions = [s.model_dump()
                 for s in run_solution_agent(use_cases).solutions]

    print("\n[5/5] Generating Proposal Document...")
    paths = run_proposal_agent(solutions[0], report)

    print(f"\n{'='*60}")
    print("PROPOSAL COMPLETE")
    print(f"{'='*60}")
    print(f"Title:  {paths['title']}")
    print(f"Client: {paths['client']}")
    print(f"File:   {paths['docx']}")
    print(f"\nOpen the .docx file to review the proposal.")
