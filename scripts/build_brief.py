"""Generate the two-page executive brief from verified analysis outputs."""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
INK = colors.HexColor("#173246")
TEAL = colors.HexColor("#168578")
MUTED = colors.HexColor("#617582")
PALE = colors.HexColor("#f0f5f6")


def main():
    audit = json.loads((ROOT / "reports/audit.json").read_text())
    font = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if font.exists():
        pdfmetrics.registerFont(TTFont("Body", str(font)))
        pdfmetrics.registerFont(TTFont("Strong", str(font.with_name("DejaVuSans-Bold.ttf"))))
    else:
        pdfmetrics.registerFont(pdfmetrics.Font("Body", "Helvetica", "WinAnsiEncoding"))
        pdfmetrics.registerFont(pdfmetrics.Font("Strong", "Helvetica-Bold", "WinAnsiEncoding"))
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("TitleCustom", fontName="Strong", fontSize=22, leading=26, textColor=INK, spaceAfter=10))
    styles.add(ParagraphStyle("Kicker", fontName="Strong", fontSize=9, leading=12, textColor=TEAL, spaceAfter=9))
    styles.add(ParagraphStyle("BodyCustom", fontName="Body", fontSize=9.5, leading=13.5, textColor=INK, spaceAfter=7))
    styles.add(ParagraphStyle("SectionCustom", fontName="Strong", fontSize=12, leading=16, textColor=INK, spaceBefore=6, spaceAfter=5))
    styles.add(ParagraphStyle("SmallCustom", fontName="Body", fontSize=8, leading=11, textColor=MUTED, spaceAfter=5))
    styles.add(ParagraphStyle("CellCustom", fontName="Body", fontSize=9, leading=13, textColor=INK))
    styles.add(ParagraphStyle("MetricCustom", fontName="Strong", fontSize=25, leading=30, textColor=INK))
    story = []

    def p(text, style="BodyCustom"):
        return Paragraph(text, styles[style])

    story.extend([p("HEALTHCARE ANALYTICS / EXECUTIVE BRIEF", "Kicker"),
                  p("Medicaid prescription spending<br/>2024 archived extract", "TitleCustom"),
                  p("Mohammed Mia | Python, SQL and source-data reconciliation", "SmallCustom"),
                  Spacer(1, 8)])
    metrics = [[p("$27.54B", "MetricCustom"), p("12", "MetricCustom"), p("37.1%", "MetricCustom")],
               [p("Observed reimbursement", "CellCustom"), p("Retained jurisdictions", "CellCustom"), p("Top 50 product share", "CellCustom")],
               [p("Before manufacturer rebates", "SmallCustom"), p("11 states + Washington, DC", "SmallCustom"), p("Of observed reimbursement", "SmallCustom")]]
    cards = Table(metrics, colWidths=[168, 168, 168])
    cards.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PALE), ("LEFTPADDING", (0, 0), (-1, -1), 12),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, 0), 12),
                              ("BOTTOMPADDING", (0, -1), (-1, -1), 9)]))
    story.extend([cards, Spacer(1, 10), p("The business question", "SectionCustom"),
                  p("Where does reported prescription spending concentrate, and which comparable products merit further price review? The analysis first validates source coverage, then provides reproducible spending and investigation-priority outputs."),
                  Image(str(ROOT / "reports/figures/top_products.png"), width=470, height=299),
                  p("Biktarvy product NDC 619582501 contributes $907.89M. The top 10 product keys account for 16.4% of observed reimbursement. Product keys combine package sizes but do not combine all strengths of a brand.", "SmallCustom"),
                  p("Decision implication", "SectionCustom"),
                  p("Start reviews with high-dollar products. California supplies 56.5% of this extract's dollars; coverage, enrollment and drug mix must inform jurisdiction comparisons."),
                  PageBreak()])
    story.extend([p("ANALYTICAL RELIABILITY / WHAT CHANGED", "Kicker"),
                  p("Audit and decision boundaries", "TitleCustom"),
                  p("The original submission is preserved; scope and assumptions are corrected in this separate portfolio version."),
                  p("Verified source and join controls", "SectionCustom")])
    rows = [[p("Control", "CellCustom"), p("Evidence", "CellCustom")],
            [p("Source coverage", "CellCustom"), p("1,048,575 records; only 11 states and DC. The worksheets reach Excel's maximum populated row.", "CellCustom")],
            [p("Suppression", "CellCustom"), p("543,945 records have suppressed amounts. Missing dollars remain unknown, not zero-filled.", "CellCustom")],
            [p("Original preservation", "CellCustom"), p("Original and cleaned row fingerprints reconcile. Original papers and notebooks retain their byte-level hashes.", "CellCustom")],
            [p("Metadata join", "CellCustom"), p("Many-to-one left join preserves row count and spending; 424 conflicting directory keys are excluded from enrichment.", "CellCustom")],
            [p("Metadata coverage", "CellCustom"), p("99.42% of reported dollars have unambiguous product metadata. Unmatched dollars stay in overall totals.", "CellCustom")]]
    table = Table(rows, colWidths=[126, 378])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), PALE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                              ("LINEBELOW", (0, 0), (-1, -1), .5, colors.HexColor("#dce5e8")),
                              ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                              ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story.extend([table, p("Original result reconciliation", "SectionCustom"),
                  p("The original Q3 median and weighted scenarios reproduce to the cent. The saved class-adjusted output is <b>$987.70M</b>, compared with approximately $1.2B in the paper. Ingredient-only comparisons and unsupported adoption assumptions mean those scenarios do not establish actual savings."),
                  p("A narrower secondary screen", "SectionCustom"),
                  p("The refinement matches recorded ingredient, strength, unit, form and route within jurisdiction, quarter and utilization type. Across <b>562 formulations and 6,675 paired strata</b>, it identifies a <b>$516.16M illustrative positive gross reimbursement gap</b> between NDA- and ANDA-listed products."),
                  p("<b>This is a price-review screen, not verified substitution potential or net savings.</b> Therapeutic equivalence, reimbursement unit types, rebate effects, practical availability and patient suitability are unverified. Application category is not a definitive brand/generic flag."),
                  p("Sources and attribution", "SectionCustom"),
                  p('Supplied CMS 2024 utilization/FDA directory workbook extracts. Official definitions: <link href="https://www.medicaid.gov/faq/2020-04-09/92001">CMS reimbursement FAQ</link>, <link href="https://www.medicaid.gov/medicaid/prescription-drugs/state-drug-utilization-data/state-drug-utilization-data-faq">CMS SDUD FAQs</link>, <link href="https://www.fda.gov/drugs/development-approval-process-drugs/orange-book-preface">FDA Orange Book Preface</link>.', "SmallCustom"),
                  p("Original ASU group: Annie Qin, Marcello Borromeo, Dhruv Nair and Mo Mia. Subsequent individual portfolio refinement by Mohammed Mia, developed with AI assistance.", "SmallCustom")])

    def footer(canvas, doc):
        canvas.setStrokeColor(colors.HexColor("#dce5e8")); canvas.line(54, 40, 558, 40)
        canvas.setFont("Body", 8); canvas.setFillColor(MUTED)
        canvas.drawString(54, 26, "2024 archived extract | Not a national estimate | Not net spending")
        canvas.drawRightString(558, 26, str(doc.page))

    doc = SimpleDocTemplate(str(ROOT / "reports/EXECUTIVE_BRIEF.pdf"), pagesize=(612, 792),
                            rightMargin=54, leftMargin=54, topMargin=42, bottomMargin=52,
                            title="Medicaid Prescription Spending - Executive Brief", author="Mohammed Mia")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print("Wrote EXECUTIVE_BRIEF.pdf")


if __name__ == "__main__":
    main()
