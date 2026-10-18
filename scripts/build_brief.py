"""Create a visual executive brief following the five analytical questions."""
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
        ("BodyCustom", 9, 13, "Body", INK, 7),
        ("SectionCustom", 12, 16, "Strong", INK, 6),
        ("SmallCustom", 8, 11, "Body", MUTED, 5),
        ("CellCustom", 9, 13, "Body", INK, 0),
        ("MetricCustom", 25, 30, "Strong", INK, 0),
    ]:
        styles.add(ParagraphStyle(name, fontName=face, fontSize=size, leading=leading,
                                  textColor=color, spaceAfter=after,
                                  spaceBefore=6 if name == "SectionCustom" else 0))

    def p(text, style="BodyCustom"):
        return Paragraph(text, styles[style])

    def image(name, width, height):
        return Image(str(ROOT / "reports/figures" / name), width=width, height=height, kind="proportional")

    h = summary["headline"]
    story = [p("HEALTHCARE ANALYTICS / EXECUTIVE BRIEF", "Kicker"),
             p("Medicaid prescription spending<br/>From dollars to review priorities", "TitleCustom"),
             p("Mohammed Mia | Python + SQL | 2024", "SmallCustom")]
    metrics = [[p(f"${h['total_reimbursement']/1e9:.2f}B", "MetricCustom"),
                p(str(h["jurisdictions"]), "MetricCustom"),
                p(f"{h['top50_product_share']:.1%}", "MetricCustom")],
               [p("Reported reimbursement", "CellCustom"), p("Jurisdictions analyzed", "CellCustom"), p("Top 50 product share", "CellCustom")],
               [p("Before manufacturer rebates", "SmallCustom"), p("11 states + Washington, DC", "SmallCustom"), p("Of reported reimbursement", "SmallCustom")]]
    cards = Table(metrics, colWidths=[168, 168, 168])
    cards.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PALE),
                              ("LEFTPADDING", (0, 0), (-1, -1), 12),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                              ("TOPPADDING", (0, 0), (-1, 0), 12),
                              ("BOTTOMPADDING", (0, -1), (-1, -1), 9)]))
    story.extend([cards, Spacer(1, 9),
        p("The question I wanted to answer", "SectionCustom"),
        p("Where does Medicaid prescription spending concentrate, and which products deserve closer price review? I combined utilization records with FDA product information and followed five questions: product spending, pharmacologic categories, price differences, recorded alternatives, and geographic/reporting context."),
        p("Q1 / I started with the products behind the dollars", "SectionCustom"),
        image("top_products.png", 504, 270),
        p("Biktarvy product NDC 619582501 contributes <b>$907.89M</b>. The top 10 product NDCs account for <b>16.4%</b> of reported reimbursement, and the top 50 account for <b>37.1%</b>. I would begin detailed review with this concentrated product set."),
        p("A product NDC combines package sizes, not every strength of a brand. This is a product-level ranking within the included extract.", "SmallCustom"),
        PageBreak(),
        p("Q2 / PHARMACOLOGIC CONTEXT", "Kicker"),
        p("Understanding the categories<br/>behind individual products", "TitleCustom"),
        p("Product rankings identify dollar exposure. I then use the directory's recorded established pharmacologic class (EPC) tags to understand the categories represented among those dollars."),
        image("pharmacologic_classes.png", 504, 300),
        p("Products with the <b>GLP-1 Receptor Agonist</b> tag account for <b>$2.94B</b>. HIV-related reverse transcriptase inhibitors, atypical antipsychotics, and SGLT2 inhibitors also appear prominently. Another <b>$5.19B</b> has no recorded EPC tag or unmatched metadata; those dollars remain in overall spending."),
        p("A product can carry multiple tags. I do not add class totals together or interpret them as mutually exclusive budget shares.", "SmallCustom"),
        p("Q3 / How I move from spending to price review", "SectionCustom"),
        p("I compare NDA- and ANDA-listed prescription products within the same recorded formulation, jurisdiction, quarter, and utilization type. For each side I calculate <b>total reimbursement divided by total units</b>. This gives utilization its appropriate weight when the question concerns observed dollars."),
        p("The matched comparison covers <b>562 formulations and 6,675 reporting groups</b>. I use the observed price difference at NDA utilization to identify where a closer review could be worthwhile."),
        PageBreak(),
        p("Q3-Q4 / MATCHED PRICES AND RECORDED ALTERNATIVES", "Kicker"),
        p("Turning price differences<br/>into a focused review list", "TitleCustom"),
        image("formulation_gaps.png", 504, 285),
        p("Positive differences sum to a <b>$516.16M illustrative gross reimbursement gap</b>. Including negative differences gives a <b>$506.73M signed aggregate</b>. I calculate the positive amount within each reporting group before aggregating, and retain both measures."),
        p("The leading recorded formulation is cyclosporine ophthalmic emulsion at 0.5 mg/mL, with a <b>$44.50M</b> positive gap. Lisdexamfetamine dimesylate oral capsules at 30 mg and methylphenidate hydrochloride oral extended-release tablets at 36 mg have gaps of <b>$22.83M</b> and <b>$22.34M</b>."),
        p("Q4 / What a recorded match does and does not establish", "SectionCustom"),
        p("I retain ingredient, strength, strength unit, dosage form, and route in the matching rules. The cyclosporine result applies to that specific recorded formulation, not every product containing cyclosporine."),
        p("An exact descriptor match still needs verification of reimbursement units, applicable therapeutic-equivalence evidence, product availability, patient suitability, and net rebate economics. NDA and ANDA categories do not fully define brand/generic status."),
        p("My conclusion: these are investigation candidates. The gross gap is not a forecast of achievable or net savings.", "SmallCustom"),
        PageBreak(),
        p("Q5 / GEOGRAPHIC AND REPORTING CONTEXT", "Kicker"),
        p("Reading the findings<br/>in their reporting context", "TitleCustom"),
        image("jurisdiction_coverage.png", 504, 205),
        p("California contributes <b>56.5%</b> of this dataset's reimbursement. I interpret that as absolute spending concentration. Enrollment, patient and drug mix, utilization, and reporting completeness are not controlled. Suppressed record share is not missing dollar share.", "SmallCustom"),
        image("spending_context.png", 504, 190),
        p("Q3 has the highest reported reimbursement at <b>$7.63B</b>. NDA, BLA, and ANDA listings account for <b>58.1%</b>, <b>28.8%</b>, and <b>10.3%</b> of spending. These distributions describe the extract; they do not establish causal drivers.", "SmallCustom"),
        p("The decision I would take forward", "SectionCustom"),
        p("I would prioritize high-dollar products, organize the review with pharmacologic context, and investigate exact recorded formulation matches. I would validate comparability and net economics before evaluating an intervention."),
        p("Scope: 1,048,575 utilization records, including 543,945 with suppressed amounts. The extract reaches the worksheet row limit; complete national or within-jurisdiction coverage is not established. The directory is not a point-in-time 2024 snapshot.", "SmallCustom"),
        p('Sources: <link href="https://data.medicaid.gov/dataset/61729e5a-7aa8-448c-8903-ba3e0cd0ea3c">CMS 2024 utilization data</link>, <link href="https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory">FDA NDC Directory</link>. <link href="https://github.com/mohammedmia1/medicaid-spending-analytics">Repository, notebook, and methodology</link>.', "SmallCustom"),
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
