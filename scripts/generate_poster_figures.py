#!/usr/bin/env python3
"""Generate poster figures for the reactomics paradigm shift."""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, FancyArrow
import numpy as np

OUT = Path(__file__).resolve().parents[1] / "assets" / "poster"
OUT.mkdir(parents=True, exist_ok=True)

# Palette aligned with existing pmd-orbitals figure
NAVY = "#1a365d"
TEAL = "#2b6cb0"
CORAL = "#c05621"
GREEN = "#276749"
PURPLE = "#6b46c1"
BG = "#f0f7fc"
PANEL = "#ffffff"
MUTED = "#4a5568"
EDGE = "#2c5282"
LIGHT = "#e2e8f0"


def save(fig, name: str):
    for ext in ("svg", "pdf", "png"):
        path = OUT / f"{name}.{ext}"
        fig.savefig(
            path,
            dpi=300,
            bbox_inches="tight",
            facecolor=fig.get_facecolor(),
            edgecolor="none",
            pad_inches=0.15,
        )
        print(f"wrote {path}")
    plt.close(fig)


def _panel(ax, x, y, w, h, title, title_color=NAVY, title_size=13):
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.8,
        edgecolor=EDGE,
        facecolor=PANEL,
        transform=ax.transAxes,
        clip_on=False,
    )
    ax.add_patch(box)
    ax.text(
        x + w / 2,
        y + h - 0.045,
        title,
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=title_size,
        fontweight="bold",
        color=title_color,
        fontfamily="DejaVu Sans",
    )
    return box


def fig1_paradigm_shift():
    """Side-by-side: traditional metabolomics vs reactomics."""
    # Slightly shorter canvas → same text reads larger when scaled to poster width
    fig, ax = plt.subplots(figsize=(13, 6.4), facecolor=BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor(BG)

    ax.text(
        0.5,
        0.98,
        "Paradigm Shift: From Metabolites to Reactions",
        ha="center",
        va="top",
        fontsize=30,
        fontweight="bold",
        color=NAVY,
        fontfamily="DejaVu Sans",
        transform=ax.transAxes,
    )
    ax.text(
        0.5,
        0.895,
        "Reactomics treats chemical reactions as first-class analytes in untargeted MS data",
        ha="center",
        va="top",
        fontsize=16,
        color=MUTED,
        fontfamily="DejaVu Sans",
        transform=ax.transAxes,
    )

    # Left panel
    _panel(ax, 0.015, 0.04, 0.425, 0.80, "Traditional Metabolomics", title_size=22)

    left_xy = {
        "A": (0.10, 0.66),
        "B": (0.30, 0.72),
        "C": (0.15, 0.50),
        "D": (0.355, 0.54),
        "E": (0.11, 0.34),
        "F": (0.335, 0.365),
    }
    for label, (x, y) in left_xy.items():
        ax.scatter(
            [x],
            [y],
            s=1100,
            c=TEAL,
            edgecolors=NAVY,
            linewidths=2.4,
            zorder=5,
            transform=ax.transAxes,
        )
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            color="white",
            fontsize=20,
            fontweight="bold",
            transform=ax.transAxes,
            zorder=6,
        )

    # Caption band fills the lower panel (reduces empty white)
    ax.add_patch(
        FancyBboxPatch(
            (0.03, 0.055),
            0.395,
            0.22,
            boxstyle="round,pad=0.01,rounding_size=0.04",
            linewidth=0,
            facecolor="#edf2f7",
            transform=ax.transAxes,
            zorder=3,
        )
    )
    ax.text(
        0.228,
        0.22,
        "Metabolites as independent entities",
        ha="center",
        fontsize=16,
        color=MUTED,
        style="italic",
        transform=ax.transAxes,
        zorder=4,
    )
    ax.text(
        0.228,
        0.145,
        'Question: "Which metabolites differ?"',
        ha="center",
        fontsize=17,
        fontweight="bold",
        color=CORAL,
        transform=ax.transAxes,
        zorder=4,
    )
    ax.text(
        0.228,
        0.08,
        "Requires compound annotation",
        ha="center",
        fontsize=15,
        color=MUTED,
        transform=ax.transAxes,
        zorder=4,
    )

    # Arrow
    ax.annotate(
        "",
        xy=(0.555, 0.48),
        xytext=(0.45, 0.48),
        xycoords=ax.transAxes,
        textcoords=ax.transAxes,
        arrowprops=dict(arrowstyle="-|>", color=CORAL, lw=5.0, mutation_scale=34),
    )
    ax.text(
        0.502,
        0.555,
        "SHIFT",
        ha="center",
        va="bottom",
        fontsize=17,
        fontweight="bold",
        color=CORAL,
        transform=ax.transAxes,
    )

    # Right panel
    _panel(ax, 0.56, 0.04, 0.425, 0.80, "Reactomics", title_color=GREEN, title_size=22)

    right_xy = {
        "A": (0.645, 0.66),
        "B": (0.845, 0.72),
        "C": (0.695, 0.50),
        "D": (0.90, 0.54),
        "E": (0.655, 0.34),
        "F": (0.88, 0.365),
    }
    edges = [
        ("A", "B", "CH₂  14.0157", CORAL),
        ("A", "C", "O  15.9949", TEAL),
        ("C", "E", "H₂  2.0157", GREEN),
        ("B", "D", "H₂O  18.0106", PURPLE),
        ("C", "D", "CH₂  14.0157", CORAL),
        ("E", "F", "O  15.9949", TEAL),
    ]
    label_off = {
        ("A", "B"): (0.00, 0.03),
        ("A", "C"): (-0.04, 0.00),
        ("C", "E"): (-0.04, 0.00),
        ("B", "D"): (0.045, 0.00),
        ("C", "D"): (0.00, 0.035),
        ("E", "F"): (0.00, -0.05),
    }
    for a, b, lab, col in edges:
        x1, y1 = right_xy[a]
        x2, y2 = right_xy[b]
        ax.plot(
            [x1, x2],
            [y1, y2],
            color=col,
            lw=4.0,
            solid_capstyle="round",
            transform=ax.transAxes,
            zorder=2,
        )
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = label_off[(a, b)]
        ax.text(
            mx + dx,
            my + dy,
            lab,
            ha="center",
            va="center",
            fontsize=13,
            color=col,
            fontweight="bold",
            transform=ax.transAxes,
            zorder=4,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.95),
        )

    for label, (x, y) in right_xy.items():
        ax.scatter(
            [x],
            [y],
            s=1000,
            c="white",
            edgecolors=NAVY,
            linewidths=2.4,
            zorder=5,
            transform=ax.transAxes,
        )
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            color=NAVY,
            fontsize=18,
            fontweight="bold",
            transform=ax.transAxes,
            zorder=6,
        )

    ax.add_patch(
        FancyBboxPatch(
            (0.575, 0.055),
            0.395,
            0.22,
            boxstyle="round,pad=0.01,rounding_size=0.04",
            linewidth=0,
            facecolor="#edf2f7",
            transform=ax.transAxes,
            zorder=3,
        )
    )
    ax.text(
        0.772,
        0.22,
        "Reactions (PMDs) as first-class objects",
        ha="center",
        fontsize=16,
        color=MUTED,
        style="italic",
        transform=ax.transAxes,
        zorder=4,
    )
    ax.text(
        0.772,
        0.145,
        'Question: "Which reactions differ?"',
        ha="center",
        fontsize=17,
        fontweight="bold",
        color=GREEN,
        transform=ax.transAxes,
        zorder=4,
    )
    ax.text(
        0.772,
        0.08,
        "No compound ID required",
        ha="center",
        fontsize=15,
        color=MUTED,
        transform=ax.transAxes,
        zorder=4,
    )

    ax.text(
        0.5,
        0.008,
        "PMD-based reactomics · Communications Chemistry 2020 · pmd R package",
        ha="center",
        fontsize=13,
        color=MUTED,
        transform=ax.transAxes,
    )
    save(fig, "fig1_paradigm_shift")


def fig2_pmd_detector():
    """Mass difference encodes a chemical reaction."""
    fig, ax = plt.subplots(figsize=(13, 6.5), facecolor=BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor(BG)

    ax.text(
        0.5,
        0.95,
        "Mass Spectrometry as a Chemical Reaction Detector",
        ha="center",
        va="top",
        fontsize=17,
        fontweight="bold",
        color=NAVY,
        transform=ax.transAxes,
    )
    ax.text(
        0.5,
        0.885,
        "A fixed paired mass distance (PMD) between two ions encodes a specific biotransformation",
        ha="center",
        va="top",
        fontsize=10,
        color=MUTED,
        transform=ax.transAxes,
    )

    # Stylized spectrum
    spectrum = FancyBboxPatch(
        (0.06, 0.18),
        0.52,
        0.62,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        linewidth=1.6,
        edgecolor=EDGE,
        facecolor=PANEL,
        transform=ax.transAxes,
    )
    ax.add_patch(spectrum)
    ax.text(
        0.32,
        0.74,
        "High-resolution MS spectrum",
        ha="center",
        fontsize=11,
        fontweight="bold",
        color=NAVY,
        transform=ax.transAxes,
    )

    # Baseline
    ax.plot([0.10, 0.54], [0.28, 0.28], color=NAVY, lw=1.4, transform=ax.transAxes)
    peaks = [
        (0.16, 0.42, "m/z₁"),
        (0.28, 0.68, "m/z₂\n(substrate)"),
        (0.42, 0.55, "m/z₃\n(product)"),
    ]
    for x, h, lab in peaks:
        ax.plot([x, x], [0.28, h], color=TEAL, lw=3.5, solid_capstyle="round", transform=ax.transAxes)
        ax.plot(x, h, "o", color=TEAL, markersize=7, transform=ax.transAxes)
        ax.text(x, h + 0.03, lab, ha="center", va="bottom", fontsize=8, color=NAVY, transform=ax.transAxes)

    # PMD bracket between peak 2 and 3
    ax.annotate(
        "",
        xy=(0.42, 0.32),
        xytext=(0.28, 0.32),
        xycoords=ax.transAxes,
        textcoords=ax.transAxes,
        arrowprops=dict(arrowstyle="<->", color=CORAL, lw=2.2),
    )
    ax.text(
        0.35,
        0.355,
        "PMD = |m/z₃ − m/z₂|",
        ha="center",
        fontsize=9,
        fontweight="bold",
        color=CORAL,
        transform=ax.transAxes,
    )
    ax.text(0.32, 0.22, "m/z →", ha="center", fontsize=9, color=MUTED, transform=ax.transAxes)

    # Right: reaction mapping table-like cards
    reactions = [
        ("2.0157 Da", "H₂", "Reduction", GREEN),
        ("14.0157 Da", "CH₂", "Methylation", CORAL),
        ("15.9949 Da", "O", "Oxidation", TEAL),
        ("18.0106 Da", "H₂O", "Hydration", PURPLE),
        ("79.9663 Da", "HPO₃", "Phosphorylation", NAVY),
        ("162.0528 Da", "C₆H₁₀O₅", "Glycosylation", "#9b2c2c"),
    ]
    ax.text(
        0.78,
        0.74,
        "PMD → Reaction",
        ha="center",
        fontsize=12,
        fontweight="bold",
        color=NAVY,
        transform=ax.transAxes,
    )
    y0 = 0.66
    for i, (pmd, formula, name, col) in enumerate(reactions):
        y = y0 - i * 0.08
        card = FancyBboxPatch(
            (0.62, y - 0.025),
            0.32,
            0.065,
            boxstyle="round,pad=0.01,rounding_size=0.03",
            linewidth=1.2,
            edgecolor=col,
            facecolor="white",
            transform=ax.transAxes,
        )
        ax.add_patch(card)
        ax.text(0.64, y + 0.008, pmd, ha="left", va="center", fontsize=8.5, fontweight="bold", color=col, transform=ax.transAxes)
        ax.text(0.76, y + 0.008, formula, ha="left", va="center", fontsize=8.5, color=NAVY, transform=ax.transAxes)
        ax.text(0.92, y + 0.008, name, ha="right", va="center", fontsize=8.5, color=MUTED, transform=ax.transAxes)

    ax.text(
        0.5,
        0.06,
        "Core insight: fixed Δm between ions = chemical reaction linking them",
        ha="center",
        fontsize=10,
        fontweight="bold",
        color=NAVY,
        transform=ax.transAxes,
    )
    ax.text(
        0.5,
        0.02,
        "Requires ~5 ppm accuracy (Orbitrap / FT-ICR / Q-TOF)",
        ha="center",
        fontsize=8,
        color=MUTED,
        transform=ax.transAxes,
    )
    save(fig, "fig2_pmd_as_reaction_detector")


def fig3_reaction_analyte():
    """Why reaction-level quantification is the omics shift."""
    fig, ax = plt.subplots(figsize=(14, 7.5), facecolor=BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor(BG)

    ax.text(
        0.5,
        0.96,
        "What Makes Reactomics an Omics: Reactions Are the Analytes",
        ha="center",
        va="top",
        fontsize=16,
        fontweight="bold",
        color=NAVY,
        transform=ax.transAxes,
    )
    ax.text(
        0.5,
        0.905,
        "Network construction alone is not enough — quantification at the reaction layer is the decisive shift",
        ha="center",
        va="top",
        fontsize=9.5,
        color=MUTED,
        transform=ax.transAxes,
    )

    # Three-step flow
    steps = [
        (0.06, "1. Peak list", "Untargeted LC-MS\nm/z + intensity\n(no IDs needed)", TEAL),
        (0.36, "2. PMD pairs", "Match Δm to curated\nreactions (O, CH₂, …)\nacross all peak pairs", CORAL),
        (0.66, "3. Reaction matrix", "getreact(): reaction × sample\nactivity scores for stats\n& comparison", GREEN),
    ]
    for x, title, body, col in steps:
        box = FancyBboxPatch(
            (x, 0.58),
            0.26,
            0.28,
            boxstyle="round,pad=0.02,rounding_size=0.06",
            linewidth=2,
            edgecolor=col,
            facecolor=PANEL,
            transform=ax.transAxes,
        )
        ax.add_patch(box)
        ax.text(x + 0.13, 0.80, title, ha="center", va="top", fontsize=12, fontweight="bold", color=col, transform=ax.transAxes)
        ax.text(x + 0.13, 0.68, body, ha="center", va="center", fontsize=9, color=MUTED, transform=ax.transAxes, linespacing=1.35)

    for x in (0.32, 0.62):
        ax.annotate(
            "",
            xy=(x + 0.035, 0.72),
            xytext=(x - 0.005, 0.72),
            xycoords=ax.transAxes,
            textcoords=ax.transAxes,
            arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=2.4, mutation_scale=16),
        )

    # Bottom: static vs dynamic
    ax.text(
        0.5,
        0.52,
        "Two regulation regimes → two quantitative readouts",
        ha="center",
        fontsize=12,
        fontweight="bold",
        color=NAVY,
        transform=ax.transAxes,
    )

    # Static panel
    sbox = FancyBboxPatch(
        (0.06, 0.08),
        0.40,
        0.40,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        linewidth=1.8,
        edgecolor=TEAL,
        facecolor=PANEL,
        transform=ax.transAxes,
    )
    ax.add_patch(sbox)
    ax.text(0.26, 0.43, "Static PMD", ha="center", fontsize=12, fontweight="bold", color=TEAL, transform=ax.transAxes)
    ax.text(
        0.26,
        0.375,
        "Substrate & product co-vary\n(stable conversion efficiency)",
        ha="center",
        fontsize=8.5,
        color=MUTED,
        transform=ax.transAxes,
        linespacing=1.25,
    )
    # Mini line chart: two parallel lines
    xs = np.linspace(0.12, 0.40, 6)
    s = np.array([0.22, 0.26, 0.24, 0.30, 0.28, 0.33])
    p = s + 0.06
    ax.plot(xs, s, "o-", color=TEAL, lw=2, markersize=5, transform=ax.transAxes, label="S")
    ax.plot(xs, p, "s-", color=CORAL, lw=2, markersize=5, transform=ax.transAxes, label="P")
    ax.text(0.41, 0.33, "P", color=CORAL, fontsize=8, fontweight="bold", transform=ax.transAxes)
    ax.text(0.41, 0.22, "S", color=TEAL, fontsize=8, fontweight="bold", transform=ax.transAxes)
    ax.text(
        0.26,
        0.14,
        "Quantify: intensity sum (S + P)\n⇒ upstream / downstream control",
        ha="center",
        fontsize=9,
        fontweight="bold",
        color=NAVY,
        transform=ax.transAxes,
        linespacing=1.3,
    )

    # Dynamic panel
    dbox = FancyBboxPatch(
        (0.54, 0.08),
        0.40,
        0.40,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        linewidth=1.8,
        edgecolor=CORAL,
        facecolor=PANEL,
        transform=ax.transAxes,
    )
    ax.add_patch(dbox)
    ax.text(0.74, 0.43, "Dynamic PMD", ha="center", fontsize=12, fontweight="bold", color=CORAL, transform=ax.transAxes)
    ax.text(
        0.74,
        0.375,
        "Substrate & product diverge\n(enzyme activity changes)",
        ha="center",
        fontsize=8.5,
        color=MUTED,
        transform=ax.transAxes,
        linespacing=1.25,
    )
    xs2 = np.linspace(0.60, 0.88, 6)
    s2 = np.array([0.28, 0.30, 0.29, 0.31, 0.30, 0.32])
    p2 = np.array([0.20, 0.24, 0.22, 0.34, 0.28, 0.36])
    ax.plot(xs2, s2, "o-", color=TEAL, lw=2, markersize=5, transform=ax.transAxes)
    ax.plot(xs2, p2, "s-", color=CORAL, lw=2, markersize=5, transform=ax.transAxes)
    ax.text(0.89, 0.36, "P", color=CORAL, fontsize=8, fontweight="bold", transform=ax.transAxes)
    ax.text(0.89, 0.32, "S", color=TEAL, fontsize=8, fontweight="bold", transform=ax.transAxes)
    ax.text(
        0.74,
        0.14,
        "Quantify: ratio (stable / variable)\n⇒ enzyme-level control",
        ha="center",
        fontsize=9,
        fontweight="bold",
        color=NAVY,
        transform=ax.transAxes,
        linespacing=1.3,
    )

    save(fig, "fig3_reaction_level_quantification")


def fig4_consequences():
    """Four practical consequences of the paradigm shift."""
    fig, ax = plt.subplots(figsize=(13.5, 6.8), facecolor=BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor(BG)

    ax.text(
        0.5,
        0.94,
        "Consequences of Treating Reactions as First-Class Objects",
        ha="center",
        va="top",
        fontsize=16,
        fontweight="bold",
        color=NAVY,
        transform=ax.transAxes,
    )

    cards = [
        (
            0.04,
            0.48,
            "Robust to annotation gaps",
            "PMDs are computed for any\npeak pair — annotated or not.\nMissing IDs no longer block\nbiological inference.",
            TEAL,
        ),
        (
            0.52,
            0.48,
            "Chemically interpretable",
            "Δm = 2.0157 → reduction\nΔm = 14.0157 → methylation\nThe network is readable\nwithout a lookup table.",
            CORAL,
        ),
        (
            0.04,
            0.06,
            "Comparable across systems",
            "Reaction networks can be\ncompared across conditions,\nspecies, and sample types\nin ways metabolite lists cannot.",
            GREEN,
        ),
        (
            0.52,
            0.06,
            "Links to pathway knowledge",
            "Connects to KEGG / HMDB /\nReactome when IDs exist,\nyet remains usable when\nannotation is incomplete.",
            PURPLE,
        ),
    ]
    for x, y, title, body, col in cards:
        box = FancyBboxPatch(
            (x, y),
            0.44,
            0.38,
            boxstyle="round,pad=0.02,rounding_size=0.07",
            linewidth=2,
            edgecolor=col,
            facecolor=PANEL,
            transform=ax.transAxes,
        )
        ax.add_patch(box)
        # accent bar
        bar = FancyBboxPatch(
            (x, y + 0.38 - 0.015),
            0.44,
            0.015,
            boxstyle="round,pad=0,rounding_size=0.01",
            linewidth=0,
            facecolor=col,
            transform=ax.transAxes,
        )
        ax.add_patch(bar)
        ax.text(x + 0.22, y + 0.30, title, ha="center", va="top", fontsize=12, fontweight="bold", color=col, transform=ax.transAxes)
        ax.text(x + 0.22, y + 0.14, body, ha="center", va="center", fontsize=9.5, color=MUTED, transform=ax.transAxes, linespacing=1.4)

    save(fig, "fig4_practical_consequences")


def fig5_unit_of_analysis():
    """Visual flip: unit of analysis from molecule to reaction."""
    fig, ax = plt.subplots(figsize=(12, 5.8), facecolor=BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor(BG)

    ax.text(
        0.5,
        0.93,
        "The Unit of Analysis Flips",
        ha="center",
        va="top",
        fontsize=17,
        fontweight="bold",
        color=NAVY,
        transform=ax.transAxes,
    )

    # Before
    left = FancyBboxPatch(
        (0.05, 0.18),
        0.38,
        0.62,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=2,
        edgecolor=TEAL,
        facecolor=PANEL,
        transform=ax.transAxes,
    )
    ax.add_patch(left)
    ax.text(0.24, 0.72, "BEFORE", ha="center", fontsize=10, fontweight="bold", color=MUTED, transform=ax.transAxes)
    ax.text(0.24, 0.65, "Unit = Molecule", ha="center", fontsize=14, fontweight="bold", color=TEAL, transform=ax.transAxes)

    # Stack of molecule cards
    for i, lab in enumerate(["Glucose", "Alanine", "ATP", "…"]):
        y = 0.52 - i * 0.08
        ax.add_patch(
            FancyBboxPatch(
                (0.12, y),
                0.24,
                0.065,
                boxstyle="round,pad=0.01,rounding_size=0.02",
                linewidth=1,
                edgecolor=TEAL,
                facecolor="#ebf8ff",
                transform=ax.transAxes,
            )
        )
        ax.text(0.24, y + 0.032, lab, ha="center", va="center", fontsize=9, color=NAVY, transform=ax.transAxes)

    ax.text(0.24, 0.24, "Reactions = secondary\n(edges between named nodes)", ha="center", fontsize=8.5, color=MUTED, transform=ax.transAxes)

    # Arrow
    ax.annotate(
        "",
        xy=(0.58, 0.50),
        xytext=(0.46, 0.50),
        xycoords=ax.transAxes,
        textcoords=ax.transAxes,
        arrowprops=dict(arrowstyle="-|>", color=CORAL, lw=3.5, mutation_scale=24),
    )
    ax.text(0.52, 0.56, "REACTOMICS", ha="center", fontsize=9, fontweight="bold", color=CORAL, transform=ax.transAxes)

    # After
    right = FancyBboxPatch(
        (0.57, 0.18),
        0.38,
        0.62,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=2,
        edgecolor=GREEN,
        facecolor=PANEL,
        transform=ax.transAxes,
    )
    ax.add_patch(right)
    ax.text(0.76, 0.72, "AFTER", ha="center", fontsize=10, fontweight="bold", color=MUTED, transform=ax.transAxes)
    ax.text(0.76, 0.65, "Unit = Reaction", ha="center", fontsize=14, fontweight="bold", color=GREEN, transform=ax.transAxes)

    for i, (lab, col) in enumerate(
        [
            ("Oxidation  +O", TEAL),
            ("Methylation  +CH₂", CORAL),
            ("Phosphorylation  +HPO₃", PURPLE),
            ("…", MUTED),
        ]
    ):
        y = 0.52 - i * 0.08
        ax.add_patch(
            FancyBboxPatch(
                (0.64, y),
                0.24,
                0.065,
                boxstyle="round,pad=0.01,rounding_size=0.02",
                linewidth=1.4,
                edgecolor=col,
                facecolor="#f0fff4",
                transform=ax.transAxes,
            )
        )
        ax.text(0.76, y + 0.032, lab, ha="center", va="center", fontsize=9, color=col, fontweight="bold", transform=ax.transAxes)

    ax.text(0.76, 0.24, "Molecules = endpoints\n(may remain unnamed)", ha="center", fontsize=8.5, color=MUTED, transform=ax.transAxes)

    ax.text(
        0.5,
        0.06,
        "If endpoints must be named before a reaction is counted, the workflow has not left traditional metabolomics.",
        ha="center",
        fontsize=9,
        style="italic",
        color=MUTED,
        transform=ax.transAxes,
    )
    save(fig, "fig5_unit_of_analysis")


def main():
    fig1_paradigm_shift()
    fig2_pmd_detector()
    fig3_reaction_analyte()
    fig4_consequences()
    fig5_unit_of_analysis()
    print(f"\nAll figures in {OUT}")


if __name__ == "__main__":
    main()
