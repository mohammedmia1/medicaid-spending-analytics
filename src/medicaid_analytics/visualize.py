"""Readable static portfolio figures with explicit scope and denominators."""
from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

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


def figures(root: Path, results: dict, formulations, audit: dict) -> None:
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
    ax.text(0, 1.02, "Top 10 product NDCs • 2024 archived extract • 11 states + Washington, DC", transform=ax.transAxes, color=MUTED)
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
    fig.text(.07, .91, "2024 archived extract • Absolute amounts are not adjusted for enrollment or drug mix", color=MUTED)
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

    fig = plt.figure(figsize=(13, 7), facecolor="#f4f7f8")
    fig.text(.055, .91, "MEDICAID PRESCRIPTION SPENDING", fontsize=11, fontweight="bold", color=TEAL)
    fig.text(.055, .82, "A portfolio analysis that starts with the data audit", fontsize=25, fontweight="bold", color=INK)
    fig.text(.055, .75, "2024 archived extract | Python + SQL + Excel source reconciliation", fontsize=13, color=MUTED)
    headline = audit["headline"]
    metrics = [(f"${headline['total_reimbursement']/1e9:.2f}B", "Observed reimbursement", "Before manufacturer rebates"),
               ("12", "Jurisdictions retained", "11 states + Washington, DC"),
               (f"{headline['top50_product_share']:.1%}", "Top 50 product share", "Of eligible observed reimbursement")]
    for i, (value, label, note) in enumerate(metrics):
        x = .055 + i * .31
        fig.text(x, .56, value, fontsize=39, fontweight="bold", color=INK)
        fig.text(x, .49, label, fontsize=14, fontweight="bold", color=INK)
        fig.text(x, .44, note, fontsize=11, color=MUTED)
    fig.text(.055, .30, "WHAT THE REFINEMENT CHANGED", fontsize=11, fontweight="bold", color=TEAL)
    fig.text(.055, .23, "Verified source coverage • Reproduced original results • Preserved join totals", fontsize=14, color=INK)
    fig.text(.055, .16, "Separated exploratory reimbursement gaps from clinically feasible and net savings", fontsize=14, color=INK)
    fig.text(.055, .06, "Not a national estimate. Suppressed amounts are unavailable. Original group submission preserved separately.", fontsize=10, color=MUTED)
    save(fig, folder, "portfolio_overview.png")
