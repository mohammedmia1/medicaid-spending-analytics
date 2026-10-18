"""Readable static portfolio figures with explicit scope and denominators."""
from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

INK = "#173246"
TEAL = "#168578"
BLUE = "#3974a8"
MUTED = "#617582"


def style() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.spines.left": False, "axes.labelcolor": INK,
                         "text.color": INK, "xtick.color": MUTED, "ytick.color": INK,
                         "figure.facecolor": "#ffffff", "axes.facecolor": "#ffffff"})


def save(fig, folder: Path, filename: str) -> None:
    fig.savefig(folder / filename, dpi=160, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def figures(root: Path, results: dict, formulations, summary: dict) -> None:
    style()
    folder = root / "reports/figures"
    folder.mkdir(parents=True, exist_ok=True)
    product = results["product_spending"].head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(11, 7))
    values = product["reimbursement"] / 1e6
    ax.barh(np.arange(len(product)), values, color=TEAL, height=.65)
    ax.set_yticks(np.arange(len(product)), [f"{r.product_name} · {r.product_key}" for r in product.itertuples()])
    ax.set_xlim(0, values.max() * 1.22)
    for y, value in enumerate(values): ax.text(value + values.max() * .015, y, f"${value:,.0f}M", va="center", fontsize=10)
    ax.set_xlabel("Reported Medicaid reimbursement before rebates ($ millions)")
    ax.set_title("Where observed prescription spending concentrates", loc="left", pad=38, fontweight="bold", fontsize=19)
    ax.text(0, 1.02, "Top 10 product NDCs • 2024 Medicaid data • 11 states + Washington, DC", transform=ax.transAxes, color=MUTED)
    ax.grid(axis="x", alpha=.15); ax.set_axisbelow(True)
    fig.text(.01, -.02, "Product-level NDCs combine package sizes, not all strengths of a brand. Suppressed reimbursement is unavailable.", fontsize=9, color=MUTED)
    fig.tight_layout()
    save(fig, folder, "top_products.png")

    coverage = results["jurisdiction_coverage"].iloc[::-1]
    fig, axes = plt.subplots(1, 2, figsize=(13, 7), gridspec_kw={"width_ratios": [1.3, 1]})
    for ax, column, color, scale, label in [
        (axes[0], "reimbursement", BLUE, 1e9, "Observed reimbursement ($ billions, before rebates)"),
        (axes[1], "suppressed_record_share", TEAL, .01, "Suppressed share of source records (%)"),
    ]:
        values = coverage[column] / scale
        ax.barh(coverage["state"], values, color=color, height=.65)
        ax.set_xlabel(label, fontsize=10)
        ax.grid(axis="x", alpha=.15); ax.set_axisbelow(True)
    axes[1].set_xlim(0, 100)
    fig.suptitle("Coverage changes how spending comparisons should be read", x=.07, ha="left", fontsize=19, fontweight="bold")
    fig.text(.07, .91, "2024 Medicaid data • Absolute amounts are not adjusted for enrollment or drug mix", color=MUTED)
    fig.tight_layout(rect=[0, .04, 1, .89])
    fig.text(.07, .015, "Suppressed record share is not the share of dollars missing; suppressed amounts are unknown.", color=MUTED, fontsize=9)
    save(fig, folder, "jurisdiction_coverage.png")

    full = results["product_spending"]
    n = min(100, len(full))
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(full.head(n)["spend_rank"], full.head(n)["cumulative_share"] * 100, color=TEAL, linewidth=3)
    for rank in [10, 50, 100]:
        if rank <= n:
            value = full.iloc[rank - 1]["cumulative_share"] * 100
            ax.scatter(rank, value, color=INK, s=35)
            ax.annotate(f"Top {rank}: {value:.1f}%", (rank, value), xytext=(0, 12 if rank != 100 else -23), textcoords="offset points", ha="center", fontsize=10)
    ax.set_ylim(0, 100); ax.set_xlim(0, 110)
    ax.set_xlabel("Product NDCs ranked by reported reimbursement")
    ax.set_ylabel("Cumulative share of observed reimbursement (%)")
    ax.set_title("A small product set accounts for a large spending share", loc="left", fontsize=18, fontweight="bold", pad=32)
    ax.text(0, 1.02, "Denominator: all eligible observed reimbursement, including unmatched product metadata", transform=ax.transAxes, color=MUTED, fontsize=10)
    ax.grid(alpha=.15); fig.tight_layout()
    save(fig, folder, "spending_concentration.png")

    if not formulations.empty:
        top = formulations.head(8).iloc[::-1]
        fig, ax = plt.subplots(figsize=(12, 7))
        labels = [textwrap.fill(f"{r.ingredient} | {r.strength} {r.strength_unit} | {r.dosage_form}", 55) for r in top.itertuples()]
        values = top["positive_gross_gap"] / 1e6
        ax.barh(np.arange(len(top)), values, color=BLUE, height=.65)
        ax.set_yticks(np.arange(len(top)), labels, fontsize=9)
        ax.set_xlabel("Illustrative positive gross reimbursement gap ($ millions)")
        ax.set_title("Formulations to prioritize for further price review", loc="left", fontsize=19, fontweight="bold", pad=38)
        ax.text(0, 1.02, "NDA vs ANDA • Same recorded formulation, jurisdiction, quarter, and utilization type", transform=ax.transAxes, color=MUTED, fontsize=10)
        ax.grid(axis="x", alpha=.15); ax.set_axisbelow(True)
        fig.text(.01, -.02, "Screening only: therapeutic equivalence, unit type, rebate differences and feasibility are not verified. Not net savings.", fontsize=9, color=MUTED)
        fig.tight_layout()
        save(fig, folder, "formulation_gaps.png")

    # EPC tags overlap. A ranked bar chart avoids implying a partition of spending.
    epc = pd.read_csv(root / "reports/tables/epc_tag_spending.csv")
    epc = epc.loc[epc["epc_tag"].ne("No recorded EPC tag / unmatched")].head(8).iloc[::-1]
    fig, ax = plt.subplots(figsize=(12, 7))
    values = epc["tagged_reimbursement"] / 1e9
    positions = np.arange(len(epc))
    ax.barh(positions, values, color=TEAL, height=.62)
    ax.set_yticks(positions, [textwrap.fill(tag, 42) for tag in epc["epc_tag"]], fontsize=10)
    ax.set_xlim(0, values.max() * 1.2)
    for y, value in enumerate(values):
        ax.text(value + .035, y, f"${value:.2f}B", va="center", fontsize=10)
    ax.set_xlabel("Reported reimbursement associated with each tag ($ billions)")
    ax.set_title("The pharmacologic categories behind the dollars", loc="left", fontsize=19, fontweight="bold", pad=42)
    ax.text(0, 1.03, "Top 8 recorded EPC tags • 2024 • 11 states + Washington, DC", transform=ax.transAxes, color=MUTED, fontsize=10)
    ax.grid(axis="x", alpha=.15); ax.set_axisbelow(True)
    fig.tight_layout(rect=[0, .07, 1, 1])
    fig.text(.02, .025, "Tags overlap: one product can contribute to multiple bars. Do not add these amounts together.", fontsize=10, color=MUTED)
    save(fig, folder, "pharmacologic_classes.png")

    quarters = results["quarterly_spending"]
    applications = results["application_spending"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), gridspec_kw={"width_ratios": [1, 1.15]})
    values = quarters["reimbursement"] / 1e9
    axes[0].bar(quarters["quarter"], values, color=TEAL, width=.6)
    for quarter, value in zip(quarters["quarter"], values):
        axes[0].text(quarter, value + .12, f"${value:.2f}B", ha="center", fontsize=10)
    axes[0].set_xticks(quarters["quarter"], [f"Q{q}" for q in quarters["quarter"]])
    axes[0].set_ylim(0, values.max() * 1.22)
    axes[0].set_ylabel("Reported reimbursement ($ billions)")
    axes[0].set_title("Reporting quarter", loc="left", fontweight="bold", pad=14)
    top_categories = applications.head(3)
    labels = top_categories["application_type"].tolist() + ["Other / unmatched"]
    shares = (top_categories["spend_share"] * 100).tolist() + [(1 - top_categories["spend_share"].sum()) * 100]
    y = np.arange(len(labels))
    axes[1].barh(y, shares, color=[BLUE, BLUE, TEAL, "#a7b6bf"], height=.6)
    axes[1].set_yticks(y, labels); axes[1].invert_yaxis()
    axes[1].set_xlim(0, 70)
    for position, share in enumerate(shares):
        axes[1].text(share + .8, position, f"{share:.1f}%", va="center", fontsize=10)
    axes[1].set_xlabel("Share of reported reimbursement (%)")
    axes[1].set_title("Recorded application category", loc="left", fontweight="bold", pad=14)
    for ax in axes:
        ax.grid(axis="y" if ax is axes[0] else "x", alpha=.15); ax.set_axisbelow(True)
    fig.suptitle("Spending changes with the reporting and product mix", x=.06, ha="left", fontsize=19, fontweight="bold")
    fig.text(.06, .90, "2024 Medicaid extract • 11 states + Washington, DC • Before manufacturer rebates", fontsize=10, color=MUTED)
    fig.tight_layout(rect=[.02, .10, 1, .86], w_pad=3)
    fig.text(.06, .035, "Descriptive patterns, without enrollment or drug-mix adjustment. Application category is not a complete brand/generic label.", fontsize=9, color=MUTED)
    save(fig, folder, "spending_context.png")

    fig = plt.figure(figsize=(13, 7), facecolor="#f4f7f8")
    fig.text(.055, .91, "MEDICAID PRESCRIPTION SPENDING", fontsize=11, fontweight="bold", color=TEAL)
    fig.text(.055, .82, "Where Medicaid prescription spending goes", fontsize=25, fontweight="bold", color=INK)
    fig.text(.055, .75, "2024 Medicaid data | Python + SQL | Mohammed Mia", fontsize=13, color=MUTED)
    headline = summary["headline"]
    metrics = [(f"${headline['total_reimbursement']/1e9:.2f}B", "Observed reimbursement", "Before manufacturer rebates"),
               ("12", "Jurisdictions analyzed", "11 states + Washington, DC"),
               (f"{headline['top50_product_share']:.1%}", "Top 50 product share", "Of eligible observed reimbursement")]
    for i, (value, label, note) in enumerate(metrics):
        x = .055 + i * .31
        fig.text(x, .56, value, fontsize=39, fontweight="bold", color=INK)
        fig.text(x, .49, label, fontsize=14, fontweight="bold", color=INK)
        fig.text(x, .44, note, fontsize=11, color=MUTED)
    fig.text(.055, .30, "ANALYSIS AT A GLANCE", fontsize=11, fontweight="bold", color=TEAL)
    fig.text(.055, .23, "Product and class spending • Matched price review • Geographic context", fontsize=14, color=INK)
    fig.text(.055, .16, "Top product NDC: Biktarvy • $907.89M in reported reimbursement", fontsize=14, color=INK)
    fig.text(.055, .06, "Scope: 11 states + Washington, DC. Reimbursement is before rebates; suppressed amounts are unavailable.", fontsize=10, color=MUTED)
    save(fig, folder, "portfolio_overview.png")
