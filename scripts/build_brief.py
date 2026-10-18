"""Create the executive spending brief from the analysis summary and figures."""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
INK = colors.HexColor("#173246")
TEAL = colors.HexColor("#168578")
MUTED = colors.HexColor("#617582")
PALE = colors.HexColor("#f0f5f6")


def main():
    summary = json.loads((ROOT / "reports/analysis_summary.json").read_text())
    font = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if font.exists():
        pdfmetrics.registerFont(TTFont("Body", str(font)))
        pdfmetrics.registerFont(TTFont("Strong", str(font.with_name("DejaVuSans-Bold.ttf"))))
    else:
        pdfmetrics.registerFont(pdfmetrics.Font("Body", "Helvetica", "WinAnsiEncoding"))
        pdfmetrics.registerFont(pdfmetrics.Font("Strong", "Helvetica-Bold", "WinAnsiEncoding"))
    styles = getSampleStyleSheet()
    for name, size, leading, face, color, after in [
        ("TitleCustom", 22, 26, "Strong", INK, 10),
        ("Kicker", 9, 12, "Strong", TEAL, 9),
        ("BodyCustom", 9.5, 13.5, "Body", INK, 7),
        ("SectionCustom", 12, 16, "Strong", INK, 5),
        ("SmallCustom", 8, 11, "Body", MUTED, 5),
        ("CellCustom", 9, 13, "Body", INK, 0),
        ("MetricCustom", 25, 30, "Strong", INK, 0),
    ]:
        styles.add(ParagraphStyle(name, fontName=face, fontSize=size, leading=leading,
                                  textColor=color, spaceAfter=after,
                                  spaceBefore=6 if name == "SectionCustom" else 0))

    def p(text, style="BodyCustom"):
        return Paragraph(text, styles[style])

    headline = summary["headline"]
    story = [p("HEALTHCARE ANALYTICS / EXECUTIVE BRIEF", "Kicker"),
             p("Medicaid prescription spending<br/>Where the dollars go", "TitleCustom"),
             p("Mohammed Mia | Python + SQL | 2024", "SmallCustom"), Spacer(1, 8)]
    metrics = [[p(f"${headline['total_reimbursement']/1e9:.2f}B", "MetricCustom"),
                p(str(headline["jurisdictions"]), "MetricCustom"),
                p(f"{headline['top50_product_share']:.1%}", "MetricCustom")],
               [p("Reported reimbursement", "CellCustom"), p("Jurisdictions analyzed", "CellCustom"), p("Top 50 product share", "CellCustom")],
               [p("Before manufacturer rebates", "SmallCustom"), p("11 states + Washington, DC", "SmallCustom"), p("Of reported reimbursement", "SmallCustom")]]
    cards = Table(metrics, colWidths=[168, 168, 168])
    cards.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PALE),
                              ("LEFTPADDING", (0, 0), (-1, -1), 12),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                              ("TOPPADDING", (0, 0), (-1, 0), 12),
                              ("BOTTOMPADDING", (0, -1), (-1, -1), 9)]))
    story.extend([cards, Spacer(1, 10), p("The question I wanted to answer", "SectionCustom"),
                  p("Which products account for Medicaid prescription spending, and where do comparable formulations have different reimbursement per unit? I built a Python and SQL workflow to prepare the data, analyze concentration, and identify products for further price review."),
                  Image(str(ROOT / "reports/figures/top_products.png"), width=470, height=299),
                  p("Biktarvy product NDC 619582501 contributes $907.89M. The top 10 product NDCs account for 16.4% of reported reimbursement. Product keys combine package sizes, not every strength of a brand.", "SmallCustom"),
                  p("What I would prioritize", "SectionCustom"),
                  p("Start detailed reviews with the concentrated high-dollar product set. The top 50 product NDCs account for 37.1% of reported reimbursement, providing a focused starting point for healthcare finance analysis."),
                  PageBreak(), p("JURISDICTIONS / PRODUCT PRICE COMPARISONS", "Kicker"),
                  p("Comparing spending and prices", "TitleCustom"),
                  p("I compare reported amounts alongside source coverage, then examine recorded formulation matches. The calculations support review priorities; clinical substitutability and net savings need separate evidence."),
                  Image(str(ROOT / "reports/figures/jurisdiction_coverage.png"), width=504, height=242),
                  p("California contributes 56.5% of this dataset's reimbursement. This is an absolute spending share, without enrollment or drug-mix adjustment. Suppressed record percentages do not estimate missing dollar shares.", "SmallCustom"),
                  p("How I compare recorded formulations", "SectionCustom"),
                  p("I match ingredient, strength, strength unit, dosage form, and route within the same jurisdiction, quarter, and utilization type. I compare NDA- and ANDA-listed prescription products using total reimbursement divided by total units, with a marketing-date overlap check."),
                  p("Across <b>562 formulations and 6,675 matched reporting groups</b>, positive differences sum to a <b>$516.16M illustrative gross reimbursement gap</b>. The signed aggregate, including negative differences, is $506.73M."),
                  p("This is a price-review screen, not achievable or net savings. Application categories do not fully define brand/generic status. Rebate effects, reimbursement unit types, therapeutic equivalence, patient suitability, and practical availability remain unverified."),
                  p("Data and calculation notes", "SectionCustom"),
                  p("The extract covers 11 states and DC. It contains 1,048,575 utilization records, including 543,945 with suppressed amounts. I leave those amounts missing. Product descriptions cover 99.42% of reported dollars; unmatched spending remains in totals. Tests check joins, eligibility, weighting, and formulation matching."),
                  p("Sources and acknowledgments", "SectionCustom"),
                  p('Sources: <link href="https://data.medicaid.gov/dataset/61729e5a-7aa8-448c-8903-ba3e0cd0ea3c">CMS 2024 utilization data</link>, <link href="https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory">FDA NDC Directory</link>, <link href="https://www.medicaid.gov/faq/2020-04-09/92001">CMS reimbursement definitions</link>. See the repository methodology for scope and matching details.', "SmallCustom"),
                  p("Academic collaborators: Annie Qin, Marcello Borromeo, Dhruv Nair, and Mo Mia (Mohammed Mia), ASU CIS 450.", "SmallCustom")])

    def footer(canvas, doc):
        canvas.setStrokeColor(colors.HexColor("#dce5e8")); canvas.line(54, 40, 558, 40)
        canvas.setFont("Body", 8); canvas.setFillColor(MUTED)
        canvas.drawString(54, 26, "2024 Medicaid data | 11 states + Washington, DC | Reimbursement before rebates")
        canvas.drawRightString(558, 26, str(doc.page))

    doc = SimpleDocTemplate(str(ROOT / "reports/EXECUTIVE_BRIEF.pdf"), pagesize=(612, 792),
                            rightMargin=54, leftMargin=54, topMargin=42, bottomMargin=52,
                            title="Medicaid Prescription Spending - Executive Brief", author="Mohammed Mia")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print("Wrote EXECUTIVE_BRIEF.pdf")


if __name__ == "__main__":
    main()
