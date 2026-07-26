"""Render independent Nature-skill variants of the three main-paper figures.

This module is deliberately separate from ``src/plots.py``.  It reads only
``paperwriting/results.json`` and writes new ``*_nature-skill`` artifacts, so
the audited Fable-spec figures remain byte-for-byte untouched.

Outputs per figure:
    paperwriting/<stem>_nature-skill.svg   editable vector master
    paperwriting/<stem>_nature-skill.pdf   LaTeX-ready vector
    paperwriting/<stem>_nature-skill.png   600-dpi preview
    paperwriting/delivery/<stem>_nature-skill_source_map.json
    paperwriting/delivery/<stem>_nature-skill_source_data.csv

Usage:
    python src/plots_nature_skill.py
    python src/plots_nature_skill.py --only fig2
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "paperwriting"
DELIVERY_DIR = PAPER_DIR / "delivery"
RESULTS_PATH = PAPER_DIR / "results.json"

FIG_WIDTH_MM = 182.88  # AAAI double-column width.
FIG_WIDTH_IN = FIG_WIDTH_MM / 25.4
PNG_DPI = 600

# Restrained Nature/NMI-like family: one signal, one neutral, one warning.
INK = "#252A31"
SIGNAL = "#24557D"
SIGNAL_MID = "#6F96B3"
SIGNAL_SOFT = "#AFC3D2"
CONTROL = "#707985"
CONTROL_SOFT = "#A8AFB7"
WARNING = "#A96F2B"
ADVERSE = "#B14A3A"
PALE_NEUTRAL = "#F6F7F8"
PALE_BLUE = "#F1F6F9"
PALE_WARNING = "#FBF6EE"
RULE = "#D9DDE1"
WHITE = "#FFFFFF"


# Mandatory nature-figure editable-text and publication settings.
plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": [
            "Arial",
            "Helvetica",
            "DejaVu Sans",
            "Liberation Sans",
        ],
        "svg.fonttype": "none",
        "svg.hashsalt": "why-aaai27-nature-skill-v1",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "font.size": 7.5,
        "axes.titlesize": 8.6,
        "axes.labelsize": 7.5,
        "xtick.labelsize": 7.0,
        "ytick.labelsize": 7.2,
        "legend.fontsize": 7.0,
        "axes.linewidth": 0.75,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "legend.frameon": False,
        "savefig.facecolor": WHITE,
        "figure.facecolor": WHITE,
    }
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_path(parts: Sequence[str | int]) -> str:
    text = ""
    for part in parts:
        if isinstance(part, int):
            text += f"[{part}]"
        elif text:
            text += f".{part}"
        else:
            text = str(part)
    return text


def _get(root: Any, parts: Sequence[str | int]) -> Any:
    value = root
    for part in parts:
        value = value[part]
    return value


def _fmt_signed(value: float, digits: int = 3) -> str:
    return f"{value:+.{digits}f}".replace("-", "−")


def _format_size(value: float) -> str:
    return f"{value:g}B"


class Provenance:
    """Trace every rendered quantity directly to results.json."""

    def __init__(self, artifact: str, results_sha256: str) -> None:
        self.artifact = artifact
        self.results_sha256 = results_sha256
        self.entries: list[dict[str, Any]] = []
        self.invariants: list[dict[str, str]] = []
        self.source_rows: list[dict[str, Any]] = []

    def read(
        self,
        root: Any,
        parts: Sequence[str | int],
        *,
        role: str,
        rendered: str | None = None,
        transform: str = "identity",
    ) -> Any:
        value = _get(root, parts)
        self.entries.append(
            {
                "json_path": _json_path(parts),
                "raw_value": value,
                "rendered_value": rendered,
                "display_transform": transform,
                "role": role,
            }
        )
        return value

    def invariant(self, name: str, passed: bool, detail: str) -> None:
        self.invariants.append(
            {
                "name": name,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )

    def source_row(
        self,
        *,
        panel: str,
        label: str,
        outcome: str,
        estimate: float | int | str,
        ci_low: float | str = "",
        ci_high: float | str = "",
        n: int | str = "",
        source_path: str,
        notes: str = "",
    ) -> None:
        self.source_rows.append(
            {
                "figure": self.artifact,
                "panel": panel,
                "label": label,
                "outcome": outcome,
                "estimate": estimate,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "n": n,
                "source_path": source_path,
                "notes": notes,
            }
        )

    def write(self) -> tuple[Path, Path]:
        DELIVERY_DIR.mkdir(parents=True, exist_ok=True)
        failures = [item for item in self.invariants if item["status"] == "FAIL"]
        payload = {
            "artifact": self.artifact,
            "numeric_source": "paperwriting/results.json",
            "results_sha256": self.results_sha256,
            "status": "PASS" if not failures else "FAIL",
            "entries": self.entries,
            "invariants": self.invariants,
            "failures": failures,
        }
        json_path = DELIVERY_DIR / f"{self.artifact}_source_map.json"
        json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        csv_path = DELIVERY_DIR / f"{self.artifact}_source_data.csv"
        fieldnames = [
            "figure",
            "panel",
            "label",
            "outcome",
            "estimate",
            "ci_low",
            "ci_high",
            "n",
            "source_path",
            "notes",
        ]
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fieldnames,
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(self.source_rows)

        if failures:
            raise RuntimeError(f"{self.artifact}: provenance invariant failed")
        return json_path, csv_path


def _save_figure(fig: plt.Figure, stem: str) -> tuple[Path, Path, Path]:
    """Save exact-size deterministic SVG, PDF, and 600-dpi PNG."""

    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    svg_path = PAPER_DIR / f"{stem}.svg"
    pdf_path = PAPER_DIR / f"{stem}.pdf"
    png_path = PAPER_DIR / f"{stem}.png"

    fig.savefig(
        svg_path,
        metadata={
            "Title": stem,
            "Creator": "anonymized-generator.py",
            "Date": None,
        },
    )
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )
    fig.savefig(
        pdf_path,
        metadata={
            "Title": stem,
            "Author": "Anonymous",
            "Creator": "anonymized-generator.py",
            "CreationDate": None,
            "ModDate": None,
        },
    )
    fig.savefig(
        png_path,
        dpi=PNG_DPI,
        metadata={"Software": "anonymized-generator.py"},
    )
    return svg_path, pdf_path, png_path


def _style_axis(ax: plt.Axes) -> None:
    ax.spines["left"].set_color(INK)
    ax.spines["bottom"].set_color(INK)
    ax.tick_params(axis="both", colors=INK, width=0.7, length=3.0)
    ax.set_axisbelow(True)


def _panel_title(ax: plt.Axes, letter: str, title: str, *, x_letter: float = -0.13) -> None:
    ax.text(
        x_letter,
        1.045,
        letter,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9.2,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        -0.02,
        1.045,
        title,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.6,
        fontweight="bold",
        color=INK,
    )


def _forest_mark(
    ax: plt.Axes,
    *,
    y: float,
    point: float,
    ci: Sequence[float],
    color: str,
    filled: bool = True,
    marker_size: float = 5.0,
    line_width: float = 1.35,
) -> None:
    lo, hi = float(ci[0]), float(ci[1])
    if not lo <= point <= hi:
        raise ValueError(f"point {point} falls outside [{lo}, {hi}]")
    ax.hlines(y, lo, hi, color=color, linewidth=line_width, zorder=3)
    ax.plot(
        point,
        y,
        marker="o",
        markersize=marker_size,
        markerfacecolor=color if filled else WHITE,
        markeredgecolor=color,
        markeredgewidth=1.05,
        linestyle="none",
        zorder=4,
    )


def _zero_line(ax: plt.Axes) -> None:
    ax.axvline(
        0,
        color=INK,
        linewidth=0.8,
        linestyle=(0, (2.0, 2.2)),
        alpha=0.85,
        zorder=2,
    )


def _read_fig1(
    results: dict[str, Any], rec: Provenance
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    checkpoints: list[dict[str, Any]] = []
    for family_short, family_key in [
        ("Qwen", "R1-Distill-Qwen"),
        ("Llama", "R1-Distill-Llama"),
    ]:
        base = ("capability", "families", family_key)
        params = rec.read(results, (*base, "params_b"), role="row labels")
        b0 = rec.read(results, (*base, "es_b0"), role="paired-estimate context")
        b3 = rec.read(results, (*base, "es_b3"), role="paired-estimate context")
        drops = rec.read(results, (*base, "es_drop"), role="point estimates")
        cis = rec.read(results, (*base, "es_drop_ci"), role="95% confidence intervals")
        sigs = rec.read(results, (*base, "es_drop_sig"), role="visual emphasis")
        rec.invariant(
            f"{family_short} aligned arrays",
            len({len(params), len(b0), len(b3), len(drops), len(cis), len(sigs)}) == 1,
            "params, B0, B3, paired changes, CIs, and flags align",
        )
        for index, size in enumerate(params):
            point = float(drops[index])
            ci = [float(cis[index][0]), float(cis[index][1])]
            label = f"{family_short} {_format_size(float(size))}"
            rec.invariant(
                f"{label} CI contains estimate",
                ci[0] <= point <= ci[1],
                f"{point} in [{ci[0]}, {ci[1]}]",
            )
            checkpoints.append(
                {
                    "family": family_short,
                    "label": _format_size(float(size)),
                    "full_label": label,
                    "point": point,
                    "ci": ci,
                    "sig": bool(sigs[index]),
                }
            )
            rec.source_row(
                panel="a",
                label=label,
                outcome="paired generative ES change (B0-B3)",
                estimate=point,
                ci_low=ci[0],
                ci_high=ci[1],
                source_path=(
                    f"{_json_path((*base, 'es_drop'))}[{index}]; "
                    f"{_json_path((*base, 'es_drop_ci'))}[{index}]"
                ),
            )

    controls: list[dict[str, Any]] = []

    f2_base = ("f2_zerothink_deconfound", "es_drop_ci")
    for label, key, comparison, color, filled in [
        ("Natural chain", "B0_to_B1", "B0→B1", SIGNAL, True),
        ("Canned thought", "B0_to_B0P", "B0→B0P", CONTROL, False),
    ]:
        raw = rec.read(
            results,
            (*f2_base, key),
            role="control point and 95% confidence interval",
        )
        point = float(raw[0])
        ci = [float(raw[1][0]), float(raw[1][1])]
        controls.append(
            {
                "label": label,
                "comparison": comparison,
                "point": point,
                "ci": ci,
                "color": color,
                "filled": filled,
                "outcome": "ES",
            }
        )
        rec.source_row(
            panel="b",
            label=f"{label} ({comparison})",
            outcome="paired generative ES change",
            estimate=point,
            ci_low=ci[0],
            ci_high=ci[1],
            source_path=_json_path((*f2_base, key)),
        )

    sampling_path = (
        "f3_sampling_robustness",
        "sampling_primary_complete_cases",
        "ES_drop",
    )
    sampling = rec.read(
        results,
        sampling_path,
        role="fixed-seed robustness point and 95% confidence interval",
    )
    controls.append(
        {
            "label": "Sampling · 3 fixed seeds",
            "comparison": "B0→B3",
            "point": float(sampling["point"]),
            "ci": [float(sampling["ci95"][0]), float(sampling["ci95"][1])],
            "color": SIGNAL_MID,
            "filled": True,
            "outcome": "ES",
        }
    )
    rec.source_row(
        panel="b",
        label="Sampling · 3 fixed seeds (B0→B3)",
        outcome="paired generative ES change",
        estimate=float(sampling["point"]),
        ci_low=float(sampling["ci95"][0]),
        ci_high=float(sampling["ci95"][1]),
        source_path=_json_path(sampling_path),
        notes="fixed-seed robustness; not a seed-population estimate",
    )

    base_path = ("base_probe", "f1_edit_specificity", "paired_ci")
    base = rec.read(
        results,
        base_path,
        role="separate unedited-base outcome",
    )
    controls.append(
        {
            "label": "Unedited base",
            "comparison": "B0→B3",
            "point": float(base["base_delta_ans_old"]),
            "ci": [float(base["ci95"][0]), float(base["ci95"][1])],
            "color": WARNING,
            "filled": True,
            "outcome": "P_old",
        }
    )
    rec.source_row(
        panel="b",
        label="Unedited base (B0→B3)",
        outcome="paired change in old-answer probability",
        estimate=float(base["base_delta_ans_old"]),
        ci_low=float(base["ci95"][0]),
        ci_high=float(base["ci95"][1]),
        n=int(base["n"]),
        source_path=_json_path(base_path),
        notes="separate outcome; not commensurate with generative ES",
    )

    rec.invariant(
        "six fixed checkpoints",
        len(checkpoints) == 6,
        "four Qwen and two Llama checkpoints",
    )
    rec.invariant(
        "two emphasized checkpoint intervals",
        sum(int(row["sig"]) for row in checkpoints) == 2,
        "emphasis is read from es_drop_sig",
    )
    rec.invariant(
        "control outcomes split",
        [row["outcome"] for row in controls] == ["ES", "ES", "ES", "P_old"],
        "three edited-model ES rows and one separate base-probability row",
    )
    return checkpoints, controls


def figure1(results: dict[str, Any], results_sha256: str) -> None:
    stem = "fig1_capability_nature-skill"
    rec = Provenance(stem, results_sha256)
    checkpoints, controls = _read_fig1(results, rec)

    fig = plt.figure(figsize=(FIG_WIDTH_IN, 3.50))
    outer = fig.add_gridspec(
        1,
        2,
        width_ratios=[1.46, 1.0],
        left=0.075,
        right=0.99,
        top=0.88,
        bottom=0.16,
        wspace=0.12,
    )
    ax_a = fig.add_subplot(outer[0, 0])
    right = outer[0, 1].subgridspec(
        2,
        2,
        height_ratios=[3.05, 1.0],
        width_ratios=[0.84, 1.56],
        hspace=0.34,
        wspace=0.04,
    )
    ax_b_labels = fig.add_subplot(right[0, 0])
    ax_b = fig.add_subplot(right[0, 1])
    ax_b_base_labels = fig.add_subplot(right[1, 0])
    ax_b_base = fig.add_subplot(right[1, 1])

    # a — horizontal categorical forest: model size never carries geometry.
    y_positions = [5.45, 4.45, 3.45, 2.45, 0.95, -0.05]
    ax_a.axhspan(2.05, 6.10, color=PALE_NEUTRAL, zorder=0)
    ax_a.axhspan(-0.40, 1.40, color=PALE_BLUE, zorder=0)
    _zero_line(ax_a)
    for y, row in zip(y_positions, checkpoints):
        color = SIGNAL if row["sig"] else CONTROL
        _forest_mark(
            ax_a,
            y=y,
            point=row["point"],
            ci=row["ci"],
            color=color,
            filled=row["sig"],
            marker_size=5.3,
        )
        if row["sig"]:
            ax_a.text(
                row["ci"][1] + 0.007,
                y,
                _fmt_signed(row["point"]),
                ha="left",
                va="center",
                fontsize=7.0,
                fontweight="bold",
                color=SIGNAL,
            )
    ax_a.set_yticks(y_positions, [row["label"] for row in checkpoints])
    ax_a.tick_params(axis="y", length=0, pad=4)
    ax_a.set_xlim(-0.125, 0.218)
    ax_a.set_ylim(-0.48, 6.35)
    ax_a.set_xticks([-0.10, 0.00, 0.10, 0.20])
    ax_a.set_xlabel(r"Paired ES change, $B_0-B_3$ (95% CI)")
    ax_a.text(
        -0.117,
        5.98,
        "QWEN FAMILY",
        ha="left",
        va="top",
        fontsize=6.6,
        fontweight="bold",
        color=CONTROL,
    )
    ax_a.text(
        -0.117,
        1.30,
        "LLAMA FAMILY",
        ha="left",
        va="top",
        fontsize=6.6,
        fontweight="bold",
        color=SIGNAL_MID,
    )
    ax_a.text(
        0.215,
        -0.40,
        "more erosion →",
        ha="right",
        va="bottom",
        fontsize=6.4,
        color=CONTROL,
    )
    _panel_title(ax_a, "a", "Paired ES change at fixed checkpoints", x_letter=-0.12)
    _style_axis(ax_a)

    # b — edited-model ES controls, with the different base outcome isolated.
    es_rows = controls[:3]
    es_y = [1.70, 0.80, -0.10]
    ax_b_labels.set_xlim(0, 1)
    ax_b_labels.set_ylim(-0.45, 2.22)
    ax_b_labels.axis("off")
    ax_b_labels.text(
        -0.02,
        1.105,
        "b",
        transform=ax_b_labels.transAxes,
        ha="left",
        va="bottom",
        fontsize=9.2,
        fontweight="bold",
        color=INK,
        clip_on=False,
    )
    ax_b_labels.text(
        0.22,
        1.105,
        "Qwen-32B controls",
        transform=ax_b_labels.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.6,
        fontweight="bold",
        color=INK,
        clip_on=False,
    )
    ax_b_labels.text(
        0.02,
        2.10,
        r"EDITED MODEL · $\Delta$ES",
        ha="left",
        va="top",
        fontsize=6.3,
        fontweight="bold",
        color=CONTROL,
    )
    for y, row in zip(es_y, es_rows):
        ax_b_labels.text(
            0.98,
            y + 0.07,
            row["label"],
            ha="right",
            va="center",
            fontsize=7.1,
            color=INK,
        )
        ax_b_labels.text(
            0.98,
            y - 0.16,
            row["comparison"],
            ha="right",
            va="center",
            fontsize=6.7,
            color=CONTROL,
        )
    _zero_line(ax_b)
    for y, row in zip(es_y, es_rows):
        _forest_mark(
            ax_b,
            y=y,
            point=row["point"],
            ci=row["ci"],
            color=row["color"],
            filled=row["filled"],
            marker_size=5.1,
        )
        ax_b.text(
            0.243,
            y,
            _fmt_signed(row["point"]),
            ha="right",
            va="center",
            fontsize=6.8,
            color=row["color"],
            fontweight="bold" if row["filled"] else "normal",
        )
    ax_b.set_yticks([])
    ax_b.set_xlim(-0.18, 0.25)
    ax_b.set_ylim(-0.45, 2.22)
    ax_b.set_xticks([-0.10, 0.00, 0.10, 0.20])
    ax_b.set_xlabel(r"Edited model: $\Delta$ES (95% CI)", labelpad=2)
    _style_axis(ax_b)

    base_row = controls[3]
    ax_b_base_labels.set_facecolor(PALE_WARNING)
    ax_b_base_labels.set_xlim(0, 1)
    ax_b_base_labels.set_ylim(-0.55, 0.55)
    ax_b_base_labels.axis("off")
    ax_b_base_labels.text(
        0.98,
        0.10,
        base_row["label"],
        ha="right",
        va="center",
        fontsize=7.1,
        color=INK,
    )
    ax_b_base_labels.text(
        0.98,
        -0.18,
        base_row["comparison"],
        ha="right",
        va="center",
        fontsize=6.7,
        color=CONTROL,
    )
    ax_b_base.set_facecolor(PALE_WARNING)
    _zero_line(ax_b_base)
    _forest_mark(
        ax_b_base,
        y=0,
        point=base_row["point"],
        ci=base_row["ci"],
        color=WARNING,
        filled=True,
        marker_size=5.1,
    )
    ax_b_base.text(
        0.243,
        0,
        _fmt_signed(base_row["point"]),
        ha="right",
        va="center",
        fontsize=6.8,
        color=WARNING,
    )
    ax_b_base.set_yticks([])
    ax_b_base.set_xlim(-0.18, 0.25)
    ax_b_base.set_ylim(-0.55, 0.55)
    ax_b_base.set_xticks([-0.10, 0.00, 0.10, 0.20])
    ax_b_base.set_xlabel(r"Base: $\Delta P(o_{\rm old})$ (95% CI)", labelpad=2)
    _style_axis(ax_b_base)

    _save_figure(fig, stem)
    plt.close(fig)
    rec.write()


def _parse_fraction(text: str) -> tuple[int, int]:
    match = re.search(r"(\d+)\s*/\s*(\d+)", text)
    if not match:
        raise ValueError(f"cannot parse fraction from {text!r}")
    return int(match.group(1)), int(match.group(2))


def _parse_decoder_layer(text: str) -> int:
    match = re.search(r"decoder\D+(\d+)", text, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"cannot parse decoder layer from {text!r}")
    return int(match.group(1))


def figure2(results: dict[str, Any], results_sha256: str) -> None:
    stem = "fig2_mechanism_nature-skill"
    rec = Provenance(stem, results_sha256)

    cloze = ("rq2_logitlens", "_authoritative_record")
    n_cloze = int(rec.read(results, (*cloze, "n"), role="sanity sample size"))
    detected_text = rec.read(
        results,
        (*cloze, "edit_intact_at_cloze"),
        role="aggregate detectability",
        transform="parse numerator and denominator",
    )
    detected, detected_n = _parse_fraction(detected_text)
    gap = float(rec.read(results, (*cloze, "gap_top_median"), role="aggregate sanity"))
    peak_text = rec.read(
        results,
        (*cloze, "peak_layer"),
        role="aggregate sanity",
        transform="parse decoder layer",
    )
    peak = _parse_decoder_layer(peak_text)
    blocked = rec.read(
        results,
        ("rq2_logitlens", "p0_membership_crosswalk", "status"),
        role="omission guard",
    )
    rec.invariant(
        "aggregate cloze denominator",
        n_cloze == detected == detected_n,
        "sample size, numerator, and denominator agree",
    )
    rec.invariant(
        "per-item crosswalk remains unavailable",
        blocked == "BLOCKED_MISSING_PER_ITEM_ARTIFACT",
        "no per-item distribution is drawn",
    )
    rec.source_row(
        panel="a",
        label="installation sanity",
        outcome="edited association detectable at cloze",
        estimate=f"{detected}/{detected_n}",
        n=n_cloze,
        source_path=_json_path((*cloze, "edit_intact_at_cloze")),
        notes="aggregate only; no control",
    )
    rec.source_row(
        panel="a",
        label="installation sanity",
        outcome="median top-layer new-minus-old gap",
        estimate=gap,
        n=n_cloze,
        source_path=_json_path((*cloze, "gap_top_median")),
        notes="aggregate only; no control",
    )
    rec.source_row(
        panel="a",
        label="installation sanity",
        outcome="peak decoder layer",
        estimate=peak,
        n=n_cloze,
        source_path=_json_path((*cloze, "peak_layer")),
        notes="parsed from authoritative record",
    )

    tax = ("rq2_taxonomy", "p0_corrected_taxonomy")
    n = int(rec.read(results, (*tax, "n"), role="route-census denominator"))
    n_facts = int(rec.read(results, (*tax, "n_unique_facts"), role="fact denominator"))
    dist = rec.read(results, (*tax, "dist"), role="route counts")
    pct = rec.read(results, (*tax, "pct"), role="route percentages")
    agreement = rec.read(results, (*tax, "agreement"), role="agreement summary")
    categories = ["Bridge", "Recall", "Reflective-override", "Associative"]
    rec.invariant(
        "corrected route count",
        sum(int(dist[key]) for key in categories) == n,
        "displayed route counts sum to n",
    )
    rec.invariant(
        "stored percentages match counts",
        all(
            math.isclose(float(pct[key]), int(dist[key]) / n, abs_tol=1e-12)
            for key in categories
        ),
        "percentage=count/n for all four routes",
    )
    rec.invariant(
        "agreement decisions sum to n",
        int(agreement["unanimous_cases"])
        + int(agreement["two_one_cases"])
        + int(agreement["split_1_1_1_cases"])
        == n,
        "unanimous, two-one, and split decisions exhaust the census",
    )
    for category in categories:
        rec.source_row(
            panel="b",
            label=category,
            outcome="majority route count",
            estimate=int(dist[category]),
            n=n,
            source_path=f"{_json_path((*tax, 'dist'))}.{category}",
            notes=f"{100 * float(pct[category]):.1f}% of corrected taxonomy",
        )
    rec.source_row(
        panel="b",
        label="agreement",
        outcome="Fleiss kappa",
        estimate=float(agreement["fleiss_kappa"]),
        n=n,
        source_path=_json_path((*tax, "agreement", "fleiss_kappa")),
    )

    fig = plt.figure(figsize=(FIG_WIDTH_IN, 2.88), layout="constrained")
    fig.set_constrained_layout_pads(w_pad=0.035, h_pad=0.04, wspace=0.03, hspace=0.03)
    grid = fig.add_gridspec(1, 2, width_ratios=[0.80, 2.20], wspace=0.15)
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1])

    # a — subordinate aggregate sanity rail.
    ax_a.set_xlim(0, 1)
    ax_a.set_ylim(0, 1)
    ax_a.axis("off")
    card = FancyBboxPatch(
        (0.035, 0.055),
        0.93,
        0.84,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        facecolor=PALE_NEUTRAL,
        edgecolor=RULE,
        linewidth=0.75,
        transform=ax_a.transAxes,
    )
    ax_a.add_patch(card)
    ax_a.text(
        -0.02,
        1.045,
        "a",
        transform=ax_a.transAxes,
        ha="left",
        va="bottom",
        fontsize=9.2,
        fontweight="bold",
        color=INK,
    )
    ax_a.text(
        0.11,
        1.045,
        "Installation sanity",
        transform=ax_a.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.6,
        fontweight="bold",
        color=INK,
    )
    ax_a.text(
        0.09,
        0.815,
        "NO CONTROL · AGGREGATE ONLY",
        transform=ax_a.transAxes,
        ha="left",
        va="center",
        fontsize=6.2,
        fontweight="bold",
        color=WARNING,
    )
    ax_a.text(
        0.50,
        0.61,
        f"{detected}/{detected_n}",
        transform=ax_a.transAxes,
        ha="center",
        va="center",
        fontsize=16.0,
        fontweight="bold",
        color=SIGNAL,
    )
    ax_a.text(
        0.50,
        0.49,
        "detectable at cloze",
        transform=ax_a.transAxes,
        ha="center",
        va="center",
        fontsize=7.1,
        color=INK,
    )
    ax_a.plot(
        [0.13, 0.87],
        [0.40, 0.40],
        transform=ax_a.transAxes,
        color=RULE,
        linewidth=0.75,
    )
    ax_a.text(
        0.31,
        0.30,
        f"{gap:.2f}",
        transform=ax_a.transAxes,
        ha="center",
        va="center",
        fontsize=9.1,
        fontweight="bold",
        color=INK,
    )
    ax_a.text(
        0.31,
        0.205,
        "top-layer gap\n(median)",
        transform=ax_a.transAxes,
        ha="center",
        va="center",
        fontsize=5.9,
        color=CONTROL,
        linespacing=0.95,
    )
    ax_a.text(
        0.71,
        0.30,
        f"{peak}",
        transform=ax_a.transAxes,
        ha="center",
        va="center",
        fontsize=9.1,
        fontweight="bold",
        color=INK,
    )
    ax_a.text(
        0.71,
        0.205,
        "peak readout\ndecoder layer",
        transform=ax_a.transAxes,
        ha="center",
        va="center",
        fontsize=5.9,
        color=CONTROL,
        linespacing=0.95,
    )
    ax_a.text(
        0.50,
        0.105,
        "selected Qwen-32B reversions",
        transform=ax_a.transAxes,
        ha="center",
        va="center",
        fontsize=6.1,
        color=CONTROL,
    )

    # b — hero corrected route census.
    ypos = [3, 2, 1, 0]
    counts = [int(dist[key]) for key in categories]
    shares = [float(pct[key]) for key in categories]
    colors = [SIGNAL, SIGNAL_MID, SIGNAL_SOFT, WHITE]
    edges = [SIGNAL, SIGNAL_MID, SIGNAL_SOFT, CONTROL_SOFT]
    bars = ax_b.barh(
        ypos,
        counts,
        height=0.50,
        color=colors,
        edgecolor=edges,
        linewidth=0.9,
        zorder=3,
    )
    for bar, count, share in zip(bars, counts, shares):
        ax_b.text(
            max(count + 0.50, 0.55),
            bar.get_y() + bar.get_height() / 2,
            f"{count}  ({100 * share:.1f}%)",
            ha="left",
            va="center",
            fontsize=7.2,
            color=INK,
            fontweight="bold" if count == max(counts) else "normal",
        )
    ax_b.plot(
        0,
        0,
        marker="o",
        markersize=3.8,
        markerfacecolor=WHITE,
        markeredgecolor=CONTROL,
        markeredgewidth=0.9,
        linestyle="none",
        zorder=4,
    )
    ax_b.set_yticks(
        ypos,
        ["Bridge", "Recall", "Reflective-\noverride", "Associative"],
    )
    ax_b.tick_params(axis="y", length=0, pad=4)
    ax_b.set_xlim(0, 35)
    ax_b.set_ylim(-0.62, 3.55)
    ax_b.set_xticks([0, 10, 20, 30])
    ax_b.set_xlabel("Instances (majority route)")
    _panel_title(ax_b, "b", "Answer-gated route census", x_letter=-0.10)
    ax_b.text(
        0.00,
        1.005,
        (
            f"n={n} instances · {n_facts} facts · "
            rf"Fleiss' $\kappa={float(agreement['fleiss_kappa']):.3f}$"
        ),
        transform=ax_b.transAxes,
        ha="left",
        va="bottom",
        fontsize=6.8,
        color=CONTROL,
    )
    ax_b.text(
        0.00,
        -0.15,
        (
            f"{int(agreement['unanimous_cases'])} unanimous · "
            f"{int(agreement['two_one_cases'])} two–one · "
            f"{int(agreement['split_1_1_1_cases'])} split"
        ),
        transform=ax_b.transAxes,
        ha="left",
        va="top",
        fontsize=6.6,
        color=CONTROL,
    )
    _style_axis(ax_b)

    _save_figure(fig, stem)
    plt.close(fig)
    rec.write()


def _read_contrast(
    results: dict[str, Any],
    rec: Provenance,
    *,
    label: str,
    group: str,
    path: Sequence[str | int],
) -> dict[str, Any]:
    row: dict[str, Any] = {"label": label, "group": group}
    for metric in ["ES", "RR"]:
        metric_path = (*path, metric)
        raw = rec.read(
            results,
            metric_path,
            role=f"{metric} paired contrast point, CI, and p-value",
        )
        point = float(raw[0])
        ci = [float(raw[1][0]), float(raw[1][1])]
        rec.invariant(
            f"{label} {metric} CI contains estimate",
            ci[0] <= point <= ci[1],
            f"{point} in [{ci[0]}, {ci[1]}]",
        )
        row[metric] = {"point": point, "ci": ci}
        rec.source_row(
            panel="a" if metric == "ES" else "b",
            label=label,
            outcome=metric,
            estimate=point,
            ci_low=ci[0],
            ci_high=ci[1],
            source_path=_json_path(metric_path),
            notes=group,
        )
    return row


def figure3(results: dict[str, Any], results_sha256: str) -> None:
    stem = "fig3_rq3_nature-skill"
    rec = Provenance(stem, results_sha256)
    mean = ("rq3", "sup_battery", "contrasts_B3_mean_ci_p")
    cross = ("rq3", "sup_battery", "cross_arm_paired_ci")
    rows = [
        _read_contrast(
            results,
            rec,
            label="T − N",
            group="vs no suppression",
            path=(*mean, "T_minus_N"),
        ),
        _read_contrast(
            results,
            rec,
            label="D − N",
            group="vs no suppression",
            path=(*mean, "D_minus_N"),
        ),
        _read_contrast(
            results,
            rec,
            label="P − N",
            group="vs no suppression",
            path=(*mean, "P_minus_N"),
        ),
        _read_contrast(
            results,
            rec,
            label="C − N",
            group="vs no suppression",
            path=(*cross, "C_minus_N"),
        ),
        _read_contrast(
            results,
            rec,
            label="T − P",
            group="specificity",
            path=(*mean, "T_minus_P"),
        ),
        _read_contrast(
            results,
            rec,
            label="T − C",
            group="specificity",
            path=(*cross, "T_minus_C"),
        ),
    ]
    arm_n = rec.read(
        results,
        ("rq3", "sup_battery", "n"),
        role="arm-size footer",
    )
    rec.invariant(
        "six planned contrasts",
        len(rows) == 6,
        "four comparisons against N and two specificity contrasts",
    )
    rec.invariant(
        "strict endpoint absent",
        all(set(row.keys()) == {"label", "group", "ES", "RR"} for row in rows),
        "RRs is not read or plotted",
    )

    fig = plt.figure(figsize=(FIG_WIDTH_IN, 3.52))
    grid = fig.add_gridspec(
        1,
        3,
        width_ratios=[0.60, 1.0, 1.0],
        left=0.025,
        right=0.985,
        top=0.88,
        bottom=0.245,
        wspace=0.08,
    )
    ax_stub = fig.add_subplot(grid[0, 0])
    ax_es = fig.add_subplot(grid[0, 1])
    ax_rr = fig.add_subplot(grid[0, 2], sharey=ax_es, sharex=ax_es)

    y_positions = [5.35, 4.35, 3.35, 2.35, 0.65, -0.35]
    y_min, y_max = -0.78, 6.22
    upper_band = (1.82, 5.78)
    lower_band = (-0.70, 1.08)

    ax_stub.set_xlim(0, 1)
    ax_stub.set_ylim(y_min, y_max)
    ax_stub.axhspan(*upper_band, color=PALE_NEUTRAL, zorder=0)
    ax_stub.axhspan(*lower_band, color=PALE_BLUE, zorder=0)
    ax_stub.axis("off")
    for y, row in zip(y_positions, rows):
        ax_stub.text(
            0.97,
            y,
            row["label"],
            ha="right",
            va="center",
            fontsize=7.4,
            color=INK,
            fontweight="bold" if row["label"].startswith("T") else "normal",
        )
    ax_stub.text(
        0.03,
        5.67,
        "VS NO SUPPRESSION (N)",
        ha="left",
        va="top",
        fontsize=6.4,
        fontweight="bold",
        color=CONTROL,
    )
    ax_stub.text(
        0.03,
        0.97,
        "SPECIFICITY",
        ha="left",
        va="top",
        fontsize=6.4,
        fontweight="bold",
        color=SIGNAL_MID,
    )

    row_colors = {
        "T − N": SIGNAL,
        "D − N": ADVERSE,
        "P − N": CONTROL_SOFT,
        "C − N": CONTROL,
        "T − P": SIGNAL,
        "T − C": SIGNAL,
    }
    for ax, metric, letter, title in [
        (ax_es, "ES", "a", r"Generative ES at $B_3$"),
        (ax_rr, "RR", "b", r"Permissive RR at $B_3$"),
    ]:
        ax.axhspan(*upper_band, color=PALE_NEUTRAL, zorder=0)
        ax.axhspan(*lower_band, color=PALE_BLUE, zorder=0)
        _zero_line(ax)
        for y, row in zip(y_positions, rows):
            values = row[metric]
            _forest_mark(
                ax,
                y=y,
                point=values["point"],
                ci=values["ci"],
                color=row_colors[row["label"]],
                filled=True,
                marker_size=4.8,
                line_width=1.25,
            )
        ax.set_xlim(-0.32, 0.32)
        ax.set_ylim(y_min, y_max)
        ax.set_xticks([-0.30, -0.15, 0.00, 0.15, 0.30])
        ax.tick_params(axis="y", left=False, labelleft=False)
        _panel_title(ax, letter, title, x_letter=-0.10)
        _style_axis(ax)

    ax_es.text(
        0.00,
        1.005,
        "← worse retention",
        transform=ax_es.transAxes,
        ha="left",
        va="bottom",
        fontsize=6.2,
        color=CONTROL,
    )
    ax_es.text(
        1.00,
        1.005,
        "better retention →",
        transform=ax_es.transAxes,
        ha="right",
        va="bottom",
        fontsize=6.2,
        color=CONTROL,
    )
    ax_rr.text(
        0.00,
        1.005,
        "← less reversion",
        transform=ax_rr.transAxes,
        ha="left",
        va="bottom",
        fontsize=6.2,
        color=CONTROL,
    )
    ax_rr.text(
        1.00,
        1.005,
        "more reversion →",
        transform=ax_rr.transAxes,
        ha="right",
        va="bottom",
        fontsize=6.2,
        color=CONTROL,
    )

    fig.supxlabel(
        r"Paired arm difference at $B_3$ (95% bootstrap CI)",
        x=0.64,
        y=0.165,
        fontsize=7.5,
        color=INK,
    )
    fig.text(
        0.50,
        0.085,
        (
            f"Arm sizes:  N none ({int(arm_n['N'])})   ·   "
            f"T suppress old ({int(arm_n['T'])})   ·   "
            f"D suppress new ({int(arm_n['D'])})"
        ),
        ha="center",
        va="center",
        fontsize=6.5,
        color=INK,
    )
    fig.text(
        0.50,
        0.045,
        (
            f"P placebo ({int(arm_n['P'])})   ·   "
            f"C same-relation competitor ({int(arm_n['C'])})"
        ),
        ha="center",
        va="center",
        fontsize=6.5,
        color=CONTROL,
    )

    _save_figure(fig, stem)
    plt.close(fig)
    rec.write()


def _write_contract() -> Path:
    """Persist the Nature-skill design choices without changing manuscript text."""

    DELIVERY_DIR.mkdir(parents=True, exist_ok=True)
    path = DELIVERY_DIR / "figure_batch1_nature-skill_contract.md"
    path.write_text(
        """# Figure batch 1 · Nature-skill variant contract

- Backend: Python/Matplotlib only.
- Export: exact 7.20-inch double-column width; editable SVG master, Type42 PDF,
  and 600-dpi PNG preview.
- Numeric source: `paperwriting/results.json` only; generated source maps and
  source-data CSVs are audit derivatives, never plotting inputs.
- Fig. 1: categorical checkpoint forest is the hero; no model-size geometry or
  connecting line. The unedited-base probability outcome is isolated from ES.
- Fig. 2: corrected route census is the hero; aggregate cloze sanity is a
  subordinate no-control rail. No visual connector implies per-item alignment.
- Fig. 3: one shared contrast-label column and a common numeric scale for ES/RR;
  RRs and marginal arm levels remain outside the figure.
- Palette: restrained signal blue, cool neutral controls, muted ochre warning,
  and muted red only for the adverse suppress-new contrast.
- Scope: these files are review candidates and do not replace the frozen
  Fable-spec renderings or manuscript captions.
""",
        encoding="utf-8",
    )
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        choices=("all", "fig1", "fig2", "fig3"),
        default="all",
        help="render one figure or the complete Nature-skill variant batch",
    )
    args = parser.parse_args()

    if not RESULTS_PATH.is_file():
        raise FileNotFoundError(RESULTS_PATH)
    results_sha256 = _sha256(RESULTS_PATH)
    with RESULTS_PATH.open(encoding="utf-8") as handle:
        results = json.load(handle)

    targets = {
        "fig1": figure1,
        "fig2": figure2,
        "fig3": figure3,
    }
    selected: Iterable[str] = targets if args.only == "all" else [args.only]
    for name in selected:
        targets[name](results, results_sha256)
        print(f"generated {name} nature-skill variant")
    _write_contract()


if __name__ == "__main__":
    main()
