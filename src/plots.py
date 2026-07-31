"""Generate the three AAAI-27 main-paper figures from results.json.

The figures intentionally use categorical comparisons rather than model-size
trend lines:

* Fig. 1: six fixed-checkpoint paired ES changes + Qwen-32B controls.
* Fig. 2: cloze installation sanity + corrected route census.
* Fig. 3: five-arm paired-contrast forests for ES and permissive RR.

Each figure writes PDF/PNG renderings, a draft caption, and a machine-readable
source map under paperwriting/delivery/.  Numbers are read only from
paperwriting/results.json; expected values from the frozen figure specification
are used solely as fail-closed audit assertions and never as plotting inputs.

Usage:
    python src/plots.py
    python src/plots.py --only fig1
    python src/plots.py --results paperwriting/results.json --only all
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "paperwriting"
DELIVERY_DIR = PAPER_DIR / "delivery"
_MISSING = object()

HERO = "#0F4D92"
N_LIGHT = "#CFCECE"
N_MID = "#767676"
N_DARK = "#4D4D4D"
INK = "#272727"
DIR_UP = "#2E9E44"
DIR_DN = "#B64342"
PALE_NEUTRAL = "#F6F7F8"
PALE_BAND = "#F3F1EE"

# W4-2 restyle palette (CVD + print validated upstream; style-only, no data).
QWEN_BLUE = "#2E6FBF"
LLAMA_ORANGE = "#D97B2A"
FAV_FILL = "#5B9BE0"
ADVERSE_RED = "#D65442"
NULL_GRAY = "#8A8F98"
INK_PRIMARY = "#1F2937"
INK_SECONDARY = "#6B7280"
BAND_TEAL = "#8ECFC9"
BAND_LILAC = "#BEB8DC"
GRID_GRAY = "#E5E7EB"
WHITE = "#FFFFFF"


def _configure_style() -> None:
    """AAAI-safe journal sizing, explicit Arial, and editable vector text."""

    arial_candidates = (
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
    )
    for font_path in arial_candidates:
        if font_path.exists():
            fm.fontManager.addfont(font_path)
    resolved_arial = Path(fm.findfont("Arial", fallback_to_default=False))
    if resolved_arial.name.lower() != "arial.ttf":
        raise RuntimeError(f"Arial did not resolve to Arial.ttf: {resolved_arial}")

    plt.rcParams.update(
        {
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "svg.hashsalt": "why-aaai27-canonical-figures-v2",
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica Neue", "Helvetica", "DejaVu Sans"],
            "mathtext.fontset": "custom",
            "mathtext.rm": "Arial",
            "mathtext.it": "Arial:italic",
            "mathtext.bf": "Arial:bold",
            "mathtext.fallback": "stix",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "figure.titlesize": 11,
            "axes.linewidth": 0.7,
            "lines.linewidth": 1.4,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.edgecolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "axes.labelcolor": INK,
            "legend.frameon": False,
            "savefig.facecolor": WHITE,
            "figure.facecolor": WHITE,
        }
    )


def _json_path(parts: Sequence[str | int]) -> str:
    out = ""
    for part in parts:
        if isinstance(part, int):
            out += f"[{part}]"
        elif out:
            out += f".{part}"
        else:
            out = str(part)
    return out


def _get(root: Any, parts: Sequence[str | int]) -> Any:
    cur = root
    for part in parts:
        cur = cur[part]
    return cur


def _equal(actual: Any, expected: Any, tol: float = 1e-10) -> bool:
    if isinstance(actual, bool) or isinstance(expected, bool):
        return actual is expected
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tol)
    if isinstance(actual, list) and isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _equal(a, e, tol=tol) for a, e in zip(actual, expected)
        )
    if isinstance(actual, dict) and isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(
            _equal(actual[k], expected[k], tol=tol) for k in actual
        )
    return actual == expected


class SourceMap:
    """Record exact JSON provenance and validate the frozen plotting spec."""

    def __init__(self, artifact: str) -> None:
        self.artifact = artifact
        self.entries: list[dict[str, Any]] = []
        self.invariants: list[dict[str, Any]] = []

    def read(
        self,
        root: Any,
        parts: Sequence[str | int],
        *,
        expected: Any = _MISSING,
        rendered: str | None = None,
        transform: str = "identity",
        role: str = "visual",
    ) -> Any:
        value = _get(root, parts)
        status = "SOURCE_ONLY"
        if expected is not _MISSING:
            status = "MATCH" if _equal(value, expected) else "MISMATCH"
        self.entries.append(
            {
                "json_path": _json_path(parts),
                "raw_value": value,
                "expected_from_fable_spec": None if expected is _MISSING else expected,
                "rendered_value": rendered,
                "display_transform": transform,
                "role": role,
                "status": status,
            }
        )
        return value

    def derived(
        self,
        *,
        source_path: str,
        raw_value: Any,
        rendered: str,
        transform: str,
        expected: Any = _MISSING,
        role: str = "visual",
    ) -> None:
        status = "SOURCE_ONLY"
        if expected is not _MISSING:
            status = "MATCH" if _equal(raw_value, expected) else "MISMATCH"
        self.entries.append(
            {
                "json_path": source_path,
                "raw_value": raw_value,
                "expected_from_fable_spec": None if expected is _MISSING else expected,
                "rendered_value": rendered,
                "display_transform": transform,
                "role": role,
                "status": status,
            }
        )

    def invariant(self, name: str, passed: bool, detail: str) -> None:
        self.invariants.append(
            {"name": name, "status": "PASS" if passed else "FAIL", "detail": detail}
        )

    def write(self) -> Path:
        DELIVERY_DIR.mkdir(parents=True, exist_ok=True)
        mismatches = [e for e in self.entries if e["status"] == "MISMATCH"]
        failures = [i for i in self.invariants if i["status"] == "FAIL"]
        payload = {
            "artifact": self.artifact,
            "numeric_source": "paperwriting/results.json",
            "status": "PASS" if not mismatches and not failures else "FAIL",
            "entries": self.entries,
            "invariants": self.invariants,
            "mismatches": mismatches,
            "failures": failures,
        }
        path = DELIVERY_DIR / f"{self.artifact}_source_map.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        if payload["status"] != "PASS":
            raise RuntimeError(f"{self.artifact} source-map audit failed; see {path}")
        return path


def _write_caption(stem: str, text: str) -> Path:
    DELIVERY_DIR.mkdir(parents=True, exist_ok=True)
    path = DELIVERY_DIR / f"{stem}_caption_draft.txt"
    path.write_text(text.strip() + "\n")
    return path


def _save(fig: plt.Figure, stem: str) -> tuple[Path, Path, Path]:
    """Save deterministic SVG/PDF vectors and a tightly cropped 600-dpi PNG."""

    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    svg = PAPER_DIR / f"{stem}.svg"
    pdf = PAPER_DIR / f"{stem}.pdf"
    png = PAPER_DIR / f"{stem}.png"
    # Metadata is deliberately identity-free: matplotlib writes Creator into
    # the PDF, it survives inside main.pdf's compressed streams, and strings(1)
    # on main.pdf will not reveal it.  Do not put the repository name here.
    fig.savefig(
        svg,
        bbox_inches="tight",
        pad_inches=0.04,
        metadata={
            "Title": stem,
            "Creator": "anonymized-generator.py",
            "Date": None,
        },
    )
    svg_text = svg.read_text(encoding="utf-8")
    svg.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )
    fig.savefig(
        pdf,
        bbox_inches="tight",
        pad_inches=0.04,
        metadata={
            "Title": stem,
            "Author": "Anonymous",
            "Creator": "anonymized-generator.py",
            "CreationDate": None,
            "ModDate": None,
        },
    )
    fig.savefig(
        png,
        bbox_inches="tight",
        pad_inches=0.04,
        dpi=600,
        metadata={"Software": "anonymized-generator.py"},
    )
    return svg, pdf, png


def _clean_axis(ax: plt.Axes, *, grid_axis: str = "y") -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)
    ax.set_axisbelow(True)


def _panel_title(
    ax: plt.Axes,
    letter: str,
    title: str,
    *,
    fontsize: float = 10.0,
    wrap: bool = False,
) -> None:
    """Place a compact panel letter beside a left-aligned panel title."""

    ax.text(
        -0.08,
        1.02,
        letter,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=max(7.0, fontsize - 1.5),
        fontweight="bold",
        color=INK_PRIMARY,
    )
    ax.text(
        0.00,
        1.02,
        title,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=fontsize,
        fontweight="bold",
        color=INK_PRIMARY,
        wrap=wrap,
    )


def _forest_point(
    ax: plt.Axes,
    *,
    y: float,
    point: float,
    ci: Sequence[float],
    color: str,
    marker: str,
    filled: bool = True,
    zorder: int = 4,
    linewidth: float = 1.35,
    markersize: float = 5.6,
    facecolor: str | None = None,
) -> None:
    lo, hi = float(ci[0]), float(ci[1])
    if not lo <= point <= hi:
        raise ValueError(f"point {point} is outside CI [{lo}, {hi}]")
    ax.hlines(y, lo, hi, color=color, linewidth=linewidth, zorder=zorder - 1)
    ax.vlines(
        [lo, hi],
        y - 0.065,
        y + 0.065,
        color=color,
        linewidth=max(0.85, linewidth * 0.6),
        zorder=zorder,
    )
    if facecolor is None:
        facecolor = color if filled else WHITE
    ax.plot(
        point,
        y,
        marker=marker,
        markersize=markersize,
        markerfacecolor=facecolor,
        markeredgecolor=color,
        markeredgewidth=1.0,
        linestyle="none",
        zorder=zorder + 1,
    )


def _fig1_data(results: dict[str, Any], rec: SourceMap) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    family_specs = [
        (
            "Qwen",
            "R1-Distill-Qwen",
            ["1.5B", "7B", "14B", "32B"],
            [0.582, 0.500, 0.555, 0.595],
            [0.607, 0.530, 0.515, 0.495],
            [-0.026, -0.030, 0.040, 0.106],
            [[-0.097, 0.051], [-0.110, 0.050], [-0.030, 0.110], [0.030, 0.182]],
            [False, False, False, True],
        ),
        (
            "Llama",
            "R1-Distill-Llama",
            ["8B", "70B"],
            [0.625, 0.610],
            [0.610, 0.503],
            [0.015, 0.107],
            [[-0.060, 0.095], [0.032, 0.182]],
            [False, True],
        ),
    ]
    checkpoints: list[dict[str, Any]] = []
    for family_short, family_key, labels, exp_b0, exp_b3, exp_drop, exp_ci, exp_sig in family_specs:
        base = ("capability", "families", family_key)
        b0 = rec.read(
            results,
            (*base, "es_b0"),
            expected=exp_b0,
            transform="array audit; marginal levels not drawn",
            role="context_not_rendered",
        )
        b3 = rec.read(
            results,
            (*base, "es_b3"),
            expected=exp_b3,
            transform="array audit; marginal levels not drawn",
            role="context_not_rendered",
        )
        drops = rec.read(results, (*base, "es_drop"), expected=exp_drop)
        cis = rec.read(results, (*base, "es_drop_ci"), expected=exp_ci)
        sigs = rec.read(results, (*base, "es_drop_sig"), expected=exp_sig)
        rec.invariant(
            f"{family_short} aligned arrays",
            len({len(labels), len(b0), len(b3), len(drops), len(cis), len(sigs)}) == 1,
            "labels, B0, B3, paired changes, CIs, and significance flags have equal length",
        )
        for i, label in enumerate(labels):
            checkpoints.append(
                {
                    "family": family_short,
                    "label": label,
                    "point": float(drops[i]),
                    "ci": [float(cis[i][0]), float(cis[i][1])],
                    "sig": bool(sigs[i]),
                }
            )

    control_specs = [
        {
            "label": "Short budget",
            "metric": r"$\Delta$ES  ($B_0\!\rightarrow\!B_1$)",
            "path": ("f2_zerothink_deconfound", "es_drop_ci", "B0_to_B1"),
            "expected": [0.13, [0.06, 0.205], "CI>0 显著=加真链才 erode"],
            "marker": "o",
            "color": QWEN_BLUE,
            "outcome_group": "Edited model · paired ES drop",
        },
        {
            "label": "Canned thought",
            "metric": r"$\Delta$ES  ($B_0\!\rightarrow\!B_{0P}$)",
            "path": ("f2_zerothink_deconfound", "es_drop_ci", "B0_to_B0P"),
            "expected": [
                -0.09,
                [-0.15, -0.03],
                "含0/反向(B0P ES 反高)=加零内容链不 erode",
            ],
            "marker": "s",
            "color": QWEN_BLUE,
            "outcome_group": "Edited model · paired ES drop",
        },
        {
            "label": "Sampling",
            "metric": r"$\Delta$ES  ($B_0\!\rightarrow\!B_3$)",
            "path": (
                "f3_sampling_robustness",
                "sampling_primary_complete_cases",
                "ES_drop",
            ),
            "expected": {"point": 0.117253, "ci95": [0.067002, 0.169179]},
            "marker": "D",
            "color": QWEN_BLUE,
            "outcome_group": "Edited model · paired ES drop",
        },
        {
            "label": "Unedited base",
            "metric": r"$\Delta P(o_{\rm old})$  ($B_0\!\rightarrow\!B_3$)",
            "path": ("base_probe", "f1_edit_specificity", "paired_ci"),
            "expected": {
                "n": 199,
                "base_delta_ans_old": -0.0201,
                "ci95": [-0.0804, 0.0402],
                "verdict": _get(
                    results,
                    ("base_probe", "f1_edit_specificity", "paired_ci", "verdict"),
                ),
            },
            "marker": "^",
            "color": NULL_GRAY,
            "outcome_group": "Unedited base · old-answer drift",
        },
    ]
    controls: list[dict[str, Any]] = []
    for spec in control_specs:
        raw = rec.read(results, spec["path"], expected=spec["expected"])
        if isinstance(raw, list):
            point, ci = raw[0], raw[1]
        else:
            if "base_delta_ans_old" in raw:
                point, ci = raw["base_delta_ans_old"], raw["ci95"]
            else:
                point, ci = raw["point"], raw["ci95"]
        controls.append({**spec, "point": float(point), "ci": [float(ci[0]), float(ci[1])]})

    n_paths = {
        "Qwen-1.5B": ("emergence", "percase", "cells_descriptive", "Qwen-1.5B", "n"),
        "Qwen-7B": ("emergence", "percase", "cells_descriptive", "Qwen-7.0B", "n"),
        "Qwen-14B": ("emergence", "percase", "cells_descriptive", "Qwen-14.0B", "n"),
        "Qwen-32B": ("emergence", "percase", "cells_descriptive", "Qwen-32.0B", "n"),
        "Llama-8B": ("emergence", "percase", "cells_descriptive", "Llama-8.0B", "n"),
    }
    expected_n = {"Qwen-1.5B": 196, "Qwen-7B": 200, "Qwen-14B": 200, "Qwen-32B": 198, "Llama-8B": 200}
    ns = {
        label: int(
            rec.read(
                results,
                path,
                expected=expected_n[label],
                transform="effective rows for paired fixed-checkpoint estimate",
                role="caption",
            )
        )
        for label, path in n_paths.items()
    }
    note_path = ("capability", "families", "R1-Distill-Llama", "_70b_note")
    note = rec.read(
        results,
        note_path,
        transform="regex extract headline n=187",
        role="caption",
    )
    # W3-3/0.  The pattern used to bake 187 into itself and the derived call
    # compared the literal 187 to the literal 187, so a note recording a
    # different headline n would still have passed.  Parse the digits out.
    match = re.search(r"headline.*?n=(\d+)", note)
    rec.invariant("Llama-70B headline n", match is not None, "_70b_note explicitly records a headline n")
    parsed_n = int(match.group(1)) if match else None
    ns["Llama-70B"] = parsed_n
    rec.derived(
        source_path=_json_path(note_path),
        raw_value=parsed_n,
        rendered="n=187",
        transform="regex from headline n in _70b_note",
        expected=187,
        role="caption",
    )
    return checkpoints, controls, ns


def fig1_capability(results: dict[str, Any]) -> None:
    rec = SourceMap("fig1_capability")
    checkpoints, controls, ns = _fig1_data(results, rec)
    rec.invariant(
        "highlight set",
        [(c["family"], c["label"]) for c in checkpoints if c["sig"]]
        == [("Qwen", "32B"), ("Llama", "70B")],
        "only Qwen-32B and Llama-70B are highlighted",
    )

    # W4-2: the figure prints at 0.58\textwidth (4.05in), a 0.5625 scale of
    # this 7.20in canvas.  Rendered 12.4pt prints 7pt (the tick floor);
    # markers >=9.6pt print >=5.4pt with the significant pair at 6.2pt; CI
    # linewidth 3.0 prints 1.7.  The printed 8pt base the spec asked for does
    # not fit two panels in 4.05in of print width -- titles and row labels
    # overflow the canvas -- so text tops out at 13.5pt rendered (7.6pt
    # printed) with shortened strings; widening the print is a main.tex
    # decision outside this change.
    fig = plt.figure(figsize=(7.20, 3.55), constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=[1.80, 1.0], wspace=0.08)
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1])

    # Panel A: categorical paired ES changes, with a visual family gap and no line.
    x_positions = [0.0, 1.5, 3.0, 4.5, 7.0, 8.5]
    ax_a.axvspan(-0.65, 5.15, color=PALE_NEUTRAL, zorder=0)
    ax_a.axvspan(6.35, 9.15, color=PALE_NEUTRAL, zorder=0)
    for x, cell in zip(x_positions, checkpoints):
        family_color = QWEN_BLUE if cell["family"] == "Qwen" else LLAMA_ORANGE
        marker = "D" if cell["sig"] else "o"
        ax_a.plot(
            x,
            cell["point"],
            marker=marker,
            markersize=11.0 if cell["sig"] else 9.6,
            markerfacecolor=(
                family_color
                if cell["sig"]
                else mcolors.to_rgba(family_color, 0.35)
            ),
            markeredgecolor=family_color,
            markeredgewidth=2.5 if cell["sig"] else 1.6,
            linestyle="none",
            zorder=5,
        )
        lo, hi = cell["ci"]
        ax_a.vlines(x, lo, hi, color=family_color, linewidth=3.0, zorder=3)
        ax_a.hlines([lo, hi], x - 0.14, x + 0.14, color=family_color, linewidth=1.8, zorder=3)
        if cell["sig"]:
            ax_a.annotate(
                f"{cell['point']:.3f}",
                (x, cell["point"]),
                xytext=(0, 12),
                textcoords="offset points",
                ha="center",
                va="bottom",
                color=INK_PRIMARY,
                fontweight="bold",
                fontsize=12,
            )
    ax_a.axhline(0, color=INK_PRIMARY, linewidth=2.0, linestyle=(0, (2, 2)))
    ax_a.set_xticks(x_positions, [c["label"] for c in checkpoints])
    ax_a.tick_params(axis="x", labelsize=12.4)
    ax_a.tick_params(axis="y", labelsize=12.4)
    ax_a.set_xlim(-0.80, 9.30)
    ax_a.set_ylim(-0.135, 0.218)
    ax_a.set_ylabel(
        r"Paired ES change  ($\mathrm{ES}_{B_0}-\mathrm{ES}_{B_3}$)", fontsize=12.4
    )
    ax_a.set_xlabel("Fixed checkpoint (categorical; no interpolation)", fontsize=12.4)
    _panel_title(ax_a, "A", "Paired ES drop after a native chain", fontsize=13.5)
    # W4-2: in-plot family keys -- a small series-colored square plus ink text
    # above each family band, replacing the old backbone captions.
    for x0, name, col in ((0.0, "Qwen", QWEN_BLUE), (6.5, "Llama", LLAMA_ORANGE)):
        ax_a.add_patch(
            mpatches.Rectangle(
                (x0 - 0.52, 0.190),
                0.40,
                0.016,
                facecolor=col,
                edgecolor="none",
                zorder=6,
            )
        )
        ax_a.text(
            x0 + 0.08,
            0.199,
            name,
            ha="left",
            va="center",
            color=INK_PRIMARY,
            fontsize=12.4,
            fontweight="bold",
            zorder=6,
        )
    ax_a.text(
        -0.60,
        -0.124,
        "positive = lower edit success after reasoning",
        ha="left",
        va="bottom",
        color=INK_SECONDARY,
        fontsize=11,
    )
    # W3-3, third attempt.  The first two versions compared literals to literals
    # -- len(checkpoints) is fixed by the label lists in this file, and the
    # connector filter can never match because every call here is either
    # linestyle="none" or an axhline.  What can actually go wrong is the zip
    # above silently dropping cells when x_positions and checkpoints disagree,
    # so count the markers that reached the axes.
    drawn = [
        line for line in ax_a.get_lines()
        if line.get_marker() not in {"", "None", None} and len(line.get_xdata()) == 1
    ]
    rec.invariant(
        "categorical panel A",
        len(x_positions) == len(checkpoints) and len(drawn) == len(checkpoints),
        f"one independent estimate per checkpoint reached the axes "
        f"({len(drawn)} markers for {len(checkpoints)} checkpoints)",
    )
    _clean_axis(ax_a, grid_axis="y")
    # W4-2: horizontal light-gray gridlines only.
    ax_a.grid(True, axis="y", color=GRID_GRAY, linewidth=0.9)
    ax_a.set_axisbelow(True)

    # Panel B: outcome-specific paired probability changes.
    y_positions = [3.25, 2.25, 1.25, -0.10]
    ax_b.axhspan(0.72, 3.73, color=PALE_NEUTRAL, zorder=0)
    ax_b.axhspan(-0.55, 0.48, color=PALE_BAND, zorder=0)
    ax_b.axhline(0.60, color=N_LIGHT, linewidth=0.7)
    for y, row in zip(y_positions, controls):
        _forest_point(
            ax_b,
            y=y,
            point=row["point"],
            ci=row["ci"],
            color=row["color"],
            marker=row["marker"],
            filled=row["label"] != "Canned thought",
            linewidth=3.0,
            markersize=10.7,
        )
    labels = [f"{r['label']}\n{r['metric']}" for r in controls]
    ax_b.set_yticks(y_positions, labels)
    ax_b.tick_params(axis="y", length=0, pad=4, labelsize=11.5)
    ax_b.tick_params(axis="x", labelsize=12.4)
    ax_b.axvline(0, color=INK_PRIMARY, linewidth=2.0, linestyle=(0, (2, 2)))
    ax_b.set_xlim(-0.182, 0.225)
    ax_b.set_ylim(-0.62, 3.88)
    ax_b.set_xlabel("Paired probability change (95% CI)", fontsize=12.4)
    _panel_title(
        ax_b,
        "B",
        "Qwen-32B budget and decoding conditions",
        fontsize=12.4,
        wrap=True,
    )
    ax_b.text(
        -0.175,
        3.72,
        "Edited model · ES drop",
        ha="left",
        va="top",
        color=INK_PRIMARY,
        fontsize=11.5,
        fontweight="bold",
        bbox={"facecolor": PALE_NEUTRAL, "edgecolor": "none", "pad": 0.2},
        zorder=6,
    )
    ax_b.text(
        -0.175,
        0.43,
        r"Unedited base · $\Delta P(o_{\rm old})$",
        ha="left",
        va="top",
        color=INK_PRIMARY,
        fontsize=11.5,
        fontweight="bold",
        bbox={"facecolor": PALE_BAND, "edgecolor": "none", "pad": 0.2},
        zorder=6,
    )
    _clean_axis(ax_b, grid_axis="x")

    caption = rf"""
Figure 1: A reasoning-time evaluation gap across fixed checkpoints. (A) Generative
word-boundary edit success (ES) is measured on the same ROME edit at zero thinking
($B_0$) and after a natural chain ($B_3$). Points show the paired change
$\mathrm{{ES}}_{{B_0}}-\mathrm{{ES}}_{{B_3}}$ with 95% case-bootstrap confidence
intervals for six categorical checkpoints; no line or interpolation connects them.
Effective sample sizes are {ns['Qwen-1.5B']}/{ns['Qwen-7B']}/{ns['Qwen-14B']}/{ns['Qwen-32B']}
for Qwen-1.5B/7B/14B/32B and {ns['Llama-8B']}/{ns['Llama-70B']} for
Llama-8B/70B (the latter after the recorded early-stop filter). The Qwen-32B
and Llama-70B intervals exclude zero
(0.106 [0.030, 0.182] and 0.107 [0.032, 0.182]); the other four include zero.
(B) On Qwen-32B, a natural chain with a 256-token thinking budget gives an ES drop of
0.130 [0.060, 0.205], whereas a fixed canned thought gives
-0.090 [-0.150, -0.030] (200 cases each). Fixed-seed sampling yields
0.117 [0.067, 0.169] over 199 complete cases and 597 same-seed pairs.
The unedited base is shown as a separately labeled outcome:
$\Delta P(o_\mathrm{{old}})=-0.020$ [-0.080, 0.040] over 199 paired cases.
Panel A and the F2 rows use greedy decoding; the sampling row uses temperature
0.6 and three fixed seeds. §5 shows this failure admits a chain-local causal control point.
"""
    _save(fig, "fig1_capability")
    plt.close(fig)
    _write_caption("fig1_capability", caption)
    rec.write()


def _parse_fraction(text: str) -> tuple[int, int]:
    match = re.search(r"(\d+)\s*/\s*(\d+)", text)
    if not match:
        raise ValueError(f"fraction not found in {text!r}")
    return int(match.group(1)), int(match.group(2))


def _parse_decoder_layer(text: str) -> int:
    match = re.search(r"decoder\D+(\d+)", text, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"decoder layer not found in {text!r}")
    return int(match.group(1))


def fig2_mechanism(results: dict[str, Any]) -> None:
    rec = SourceMap("fig2_mechanism")
    cloze_base = ("rq2_logitlens", "_authoritative_record")
    n_cloze = int(rec.read(results, (*cloze_base, "n"), expected=23))
    detectable_raw = rec.read(
        results,
        (*cloze_base, "edit_intact_at_cloze"),
        expected="23/23=100%",
        transform="parse numerator/denominator; render as detectable association",
    )
    detected, detected_n = _parse_fraction(detectable_raw)
    gap = float(rec.read(results, (*cloze_base, "gap_top_median"), expected=11.51))
    peak_raw = rec.read(
        results,
        (*cloze_base, "peak_layer"),
        transform="parse decoder layer from hs-to-decoder note",
    )
    peak_decoder = _parse_decoder_layer(peak_raw)
    rec.derived(
        source_path=_json_path((*cloze_base, "peak_layer")),
        raw_value=peak_decoder,
        rendered="decoder 58",
        transform="regex parse",
        expected=58,
    )
    blocked = rec.read(
        results,
        ("rq2_logitlens", "p0_membership_crosswalk", "status"),
        expected="BLOCKED_MISSING_PER_ITEM_ARTIFACT",
        transform="prohibits per-item distribution/crosswalk",
        role="caveat",
    )
    rec.invariant(
        "cloze denominator",
        n_cloze == detected_n == detected == 23,
        "n, detectable numerator, and denominator are all 23",
    )
    rec.invariant(
        "per-item distribution omitted",
        blocked == "BLOCKED_MISSING_PER_ITEM_ARTIFACT",
        "only the aggregate installation sanity is rendered",
    )

    tax_base = ("rq2_taxonomy", "p0_corrected_taxonomy")
    n = int(rec.read(results, (*tax_base, "n"), expected=41))
    n_facts = int(rec.read(results, (*tax_base, "n_unique_facts"), expected=33))
    dist_expected = {"Bridge": 27, "Recall": 11, "Reflective-override": 3, "Associative": 0}
    pct_expected = {
        "Bridge": 0.6585365853658537,
        "Recall": 0.2682926829268293,
        "Reflective-override": 0.07317073170731707,
        "Associative": 0.0,
    }
    dist = rec.read(results, (*tax_base, "dist"), expected=dist_expected)
    pct = rec.read(results, (*tax_base, "pct"), expected=pct_expected)
    unanimous = int(
        rec.read(results, (*tax_base, "agreement", "unanimous_cases"), expected=35)
    )
    two_one = int(rec.read(results, (*tax_base, "agreement", "two_one_cases"), expected=6))
    split = int(rec.read(results, (*tax_base, "agreement", "split_1_1_1_cases"), expected=0))
    raw_agreement = rec.read(
        results,
        (*tax_base, "agreement", "raw_pairwise_agreement"),
        expected="111/123=.902439",
    )
    kappa = float(
        rec.read(
            results,
            (*tax_base, "agreement", "fleiss_kappa"),
            expected=0.8125952260030472,
            rendered=".813",
            transform="round to 3 decimals",
        )
    )
    candidate_n = int(
        rec.read(
            results,
            ("rq2_taxonomy", "p0_membership_reaudit", "technical_audit", "n_items"),
            expected=101,
            role="caption",
        )
    )
    rec.invariant("taxonomy count", sum(dist.values()) == n, "route counts sum to n=41")
    rec.invariant(
        "taxonomy percentages",
        all(math.isclose(pct[k], dist[k] / n, abs_tol=1e-12) for k in dist),
        "stored percentages equal count/n",
    )
    rec.invariant(
        "route-panel decisions",
        unanimous + two_one + split == n,
        "35 unanimous + 6 two-one + 0 split = 41",
    )
    rec.invariant(
        "agreement denominator",
        raw_agreement.startswith("111/123"),
        "123 equals three pairwise comparisons for 41 panels",
    )
    # W3-3/0.  The old condition compared a literal tuple to the literal it was
    # built from.  Ask the recorder what was actually read instead.
    rec.invariant(
        "authoritative source only",
        all(not entry["json_path"].startswith("logitlens") for entry in rec.entries),
        "Fig. 2 does not access the superseded top-level logitlens block",
    )

    fig = plt.figure(figsize=(7.20, 3.35), constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=[1.00, 2.00], wspace=0.18)
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1])

    # Panel A: aggregate-only installation sanity, intentionally subordinate.
    ax_a.set_xlim(0, 1)
    ax_a.set_ylim(0, 1)
    ax_a.axis("off")
    ax_a.text(
        0.02,
        0.94,
        "A",
        transform=ax_a.transAxes,
        ha="left",
        va="top",
        fontweight="bold",
        fontsize=8.5,
        color=INK,
    )
    ax_a.text(
        0.13,
        0.94,
        "INSTALLATION SANITY · NO CONTROL",
        transform=ax_a.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        fontweight="bold",
        color=N_MID,
    )
    ax_a.text(
        0.04,
        0.72,
        f"{detected}/{detected_n}",
        transform=ax_a.transAxes,
        ha="left",
        va="center",
        fontsize=24,
        fontweight="bold",
        color=HERO,
    )
    ax_a.text(
        0.04,
        0.56,
        "edited association detectable\nat a cloze probe",
        transform=ax_a.transAxes,
        ha="left",
        va="center",
        fontsize=9,
        color=N_DARK,
        linespacing=1.25,
    )
    ax_a.plot([0.04, 0.96], [0.42, 0.42], transform=ax_a.transAxes, color=N_LIGHT, lw=0.7)
    ax_a.text(
        0.04,
        0.34,
        "Top-layer gap\nmedian",
        transform=ax_a.transAxes,
        ha="left",
        va="center",
        fontsize=7.8,
        color=N_MID,
        linespacing=0.9,
    )
    ax_a.text(
        0.96,
        0.34,
        f"{gap:.2f}",
        transform=ax_a.transAxes,
        ha="right",
        va="center",
        fontsize=9,
        fontweight="bold",
        color=N_DARK,
    )
    ax_a.plot([0.04, 0.96], [0.27, 0.27], transform=ax_a.transAxes, color=N_LIGHT, lw=0.7)
    ax_a.text(
        0.04,
        0.20,
        "Peak readout",
        transform=ax_a.transAxes,
        ha="left",
        va="center",
        fontsize=8.5,
        color=N_MID,
    )
    ax_a.text(
        0.96,
        0.20,
        f"decoder {peak_decoder}",
        transform=ax_a.transAxes,
        ha="right",
        va="center",
        fontsize=9,
        fontweight="bold",
        color=N_DARK,
    )
    ax_a.text(
        0.04,
        0.065,
        "Selected Qwen-32B reversions · aggregate only",
        transform=ax_a.transAxes,
        ha="left",
        va="center",
        fontsize=8,
        color=N_MID,
    )

    # Panel B: corrected answer-gated route census.
    categories = ["Bridge", "Recall", "Reflective-override", "Associative"]
    category_labels = ["Bridge", "Recall", "Reflective-\noverride", "Associative"]
    counts = [int(dist[k]) for k in categories]
    shares = [float(pct[k]) for k in categories]
    ypos = [3, 2, 1, 0]
    bars = ax_b.barh(
        ypos,
        counts,
        height=0.56,
        color=HERO,
        edgecolor=HERO,
        linewidth=0.0,
    )
    for bar, count, share in zip(bars, counts, shares):
        if count == 0:
            ax_b.hlines(
                bar.get_y() + bar.get_height() / 2,
                0.0,
                0.22,
                color=N_LIGHT,
                linewidth=0.7,
                zorder=3,
            )
        x = max(count + 0.55, 0.55)
        ax_b.text(
            x,
            bar.get_y() + bar.get_height() / 2,
            f"{count}  ({share * 100:.1f}%)",
            ha="left",
            va="center",
            fontsize=9,
            color=INK,
            fontweight="bold" if count == max(counts) else "normal",
        )
    ax_b.set_yticks(ypos, category_labels)
    ax_b.tick_params(axis="y", length=0)
    ax_b.set_xlim(0, 32.0)
    ax_b.set_xticks([0, 10, 20, 30])
    ax_b.set_xlabel("Route-census instances (majority label)")
    _panel_title(ax_b, "B", "Answer-gated route census")
    ax_b.text(
        0.00,
        -0.24,
        rf"$n={n}$ instances · {n_facts} unique facts · Fleiss' $\kappa={kappa:.3f}$",
        transform=ax_b.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        color=N_DARK,
    )
    ax_b.text(
        0.00,
        -0.34,
        "35 unanimous · 6 two–one · 0 split",
        transform=ax_b.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        color=N_MID,
    )
    _clean_axis(ax_b, grid_axis="x")

    caption = rf"""
Figure 2: An evidence ladder for the chain-routing hypothesis. (A) Installation
sanity on {n_cloze} selected Qwen-32B reversions: after reapplying ROME, the edited
association remains detectable at a first-token cloze probe in {detected}/{detected_n}
cases. The median top-layer new-minus-old logit gap is {gap:.2f}, and the median peak
readout is decoder layer {peak_decoder}. This aggregate check has no control and does
not establish preservation of the full edit; the per-item crosswalk is unavailable.
(B) Separately, an answer-only gate retains {n} committed-old instances
({n_facts} unique facts) from a frozen pool of {candidate_n} candidate chains.
Route-census majority labels are Bridge 27 (65.9%), Recall 11 (26.8%),
Reflective-override 3 (7.3%), and Associative 0. Agreement is Fleiss'
$\kappa=.{round(kappa * 1000):03d}$ (35 unanimous, 6 two–one, no split; raw agreement
111/123 = .902). The two panels use different populations and are not a
per-item conjunction.
"""
    _save(fig, "fig2_mechanism")
    plt.close(fig)
    _write_caption("fig2_mechanism", caption)
    rec.write()


def _contrast(
    results: dict[str, Any],
    rec: SourceMap,
    *,
    label: str,
    path_base: Sequence[str | int],
    expected_es: list[Any],
    expected_rr: list[Any],
    expected_rrs: list[Any],
    color: str,
    marker: str,
    group: str,
) -> dict[str, Any]:
    es = rec.read(results, (*path_base, "ES"), expected=expected_es)
    rr = rec.read(results, (*path_base, "RR"), expected=expected_rr)
    rrs = rec.read(results, (*path_base, "RRs"), expected=expected_rrs)
    return {
        "label": label,
        "es": {"point": float(es[0]), "ci": [float(es[1][0]), float(es[1][1])]},
        "rr": {"point": float(rr[0]), "ci": [float(rr[1][0]), float(rr[1][1])]},
        "rrs": {"point": float(rrs[0]), "ci": [float(rrs[1][0]), float(rrs[1][1])]},
        "color": color,
        "marker": marker,
        "group": group,
    }


def fig3_rq3(results: dict[str, Any]) -> None:
    rec = SourceMap("fig3_rq3")
    mean_ci = ("rq3", "sup_battery", "contrasts_B3_mean_ci_p")
    crossarm = ("rq3", "sup_battery", "cross_arm_paired_ci")
    rows = [
        _contrast(
            results,
            rec,
            label="T − N",
            path_base=(*mean_ci, "T_minus_N"),
            expected_es=[0.138, [0.082, 0.194], 0.0],
            expected_rr=[-0.102, [-0.17, -0.042], 0.001],
            expected_rrs=[-0.051, [-0.102, 0.0], 0.073],
            color=QWEN_BLUE,
            marker="o",
            group="vs N",
        ),
        _contrast(
            results,
            rec,
            label="D − N",
            path_base=(*mean_ci, "D_minus_N"),
            expected_es=[-0.217, [-0.289, -0.144], 0.0],
            expected_rr=[0.086, [0.019, 0.152], 0.01],
            expected_rrs=[0.095, [0.038, 0.162], 0.002],
            color=ADVERSE_RED,
            marker="v",
            group="vs N",
        ),
        _contrast(
            results,
            rec,
            label="P − N",
            path_base=(*mean_ci, "P_minus_N"),
            expected_es=[0.015, [-0.046, 0.081], 0.709],
            expected_rr=[0.0, [-0.057, 0.057], 1.0],
            expected_rrs=[-0.009, [-0.047, 0.028], 0.828],
            color=NULL_GRAY,
            marker="s",
            group="vs N",
        ),
        _contrast(
            results,
            rec,
            label="C − N",
            path_base=(*crossarm, "C_minus_N"),
            expected_es=[0.0152, [-0.0455, 0.0758], 0.688],
            expected_rr=[0.0, [-0.0561, 0.0561], 1.0],
            expected_rrs=[-0.0093, [-0.0467, 0.028], 0.8282],
            color=NULL_GRAY,
            marker="D",
            group="vs N",
        ),
        _contrast(
            results,
            rec,
            label="T − P",
            path_base=(*mean_ci, "T_minus_P"),
            expected_es=[0.122, [0.051, 0.193], 0.002],
            expected_rr=[-0.095, [-0.171, -0.029], 0.01],
            expected_rrs=[-0.057, [-0.114, -0.01], 0.029],
            color=QWEN_BLUE,
            marker="o",
            group="specificity",
        ),
        _contrast(
            results,
            rec,
            label="T − C",
            path_base=(*crossarm, "T_minus_C"),
            expected_es=[0.1212, [0.0505, 0.1919], 0.0004],
            expected_rr=[-0.0943, [-0.1604, -0.0283], 0.0062],
            expected_rrs=[-0.0566, [-0.1132, -0.0094], 0.0324],
            color=QWEN_BLUE,
            marker="o",
            group="specificity",
        ),
    ]
    n_by_arm = rec.read(
        results,
        ("rq3", "sup_battery", "n"),
        expected={"N": 198, "T": 198, "D": 196, "P": 199, "C": 200},
        role="caption",
    )
    marginal = rec.read(
        results,
        ("rq3", "sup_battery", "marginal_B3"),
        transform="extract ES arm levels for descriptive sign ladder",
        role="caption",
    )
    ladder = {arm: float(marginal[arm]["ES"]) for arm in ["D", "N", "P", "C", "T"]}
    expected_ladder = {"D": 0.281, "N": 0.495, "P": 0.507, "C": 0.51, "T": 0.631}
    rec.derived(
        source_path="rq3.sup_battery.marginal_B3.<arm>.ES",
        raw_value=ladder,
        rendered="D .281 < N .495 ≈ P .507 ≈ C .510 < T .631",
        transform="select arm-level marginal ES values",
        expected=expected_ladder,
        role="caption",
    )
    # W3-3.  len(rows) == 6 compared a literal-derived length to the literal 6.
    # The contrasts themselves are what must be present, so check the labels.
    rec.invariant(
        "forest rows",
        sorted(row["label"] for row in rows)
        == sorted(["T \u2212 N", "D \u2212 N", "P \u2212 N", "C \u2212 N", "T \u2212 P", "T \u2212 C"]),
        "four comparisons against N plus two specificity contrasts",
    )

    # W4/E4+cut: single-column stacked layout -- the full-width variant did not
    # fit the 7-page body budget, and dropping the figure (the sanctioned
    # fallback) would have cost the strict panel its place in the body.
    fig, axes = plt.subplots(
        3,
        1,
        figsize=(3.3, 4.45),
        sharey=True,
        sharex=True,
        constrained_layout=True,
        gridspec_kw={"hspace": 0.04},
    )
    y_positions = [6.0, 5.0, 4.0, 3.0, 1.35, 0.35]
    # W4-2: one shared x scale so only the bottom panel needs tick labels.
    SHARED_XLIM = (-0.33, 0.24)
    panels = [
        (axes[0], "es", r"$\Delta$ generative ES at $B_3$", SHARED_XLIM),
        (axes[1], "rr", r"$\Delta$ permissive RR at $B_3$", SHARED_XLIM),
        # W4/E4: the strict panel ships or the figure does not (shipping gate).
        (axes[2], "rrs", r"$\Delta$ strict $RR^s$ at $B_3$ (secondary)", SHARED_XLIM),
    ]
    # W3-3.  Two attempts at a "strict endpoint excluded" invariant lived here:
    # the literal True, and then a conjunction over the same literals that built
    # panels and rows, which was equally constant and, worse, recorded PASS to
    # certify the figure was NOT shippable -- while SourceMap.write raises only
    # on FAIL.  A shipping rule cannot be enforced from the renderer, so it now
    # lives in check_manuscript.check_forest_shipping_gate, which blocks any
    # .tex that includes this figure while its source map records no RRs.
    rec.invariant(
        "every planned contrast reached the plot",
        len(y_positions) == len(rows),
        "no contrast is silently dropped by the zip against y_positions",
    )
    for ax, metric, title, xlim in panels:
        ax.axhspan(2.55, 6.48, color=BAND_TEAL, alpha=0.12, zorder=0)
        ax.axhspan(-0.10, 1.80, color=BAND_LILAC, alpha=0.12, zorder=0)
        ax.axvline(0, color=N_DARK, linewidth=0.8, linestyle=(0, (2, 2)))
        for y, row in zip(y_positions, rows):
            values = row[metric]
            _forest_point(
                ax,
                y=y,
                point=values["point"],
                ci=values["ci"],
                color=row["color"],
                marker=row["marker"],
                filled=row["label"] not in {"P − N", "C − N"},
                facecolor=(FAV_FILL if row["color"] == QWEN_BLUE else None),
            )
        ax.set_xlim(*xlim)
        ax.set_ylim(-0.35, 7.35)
        if metric == "rrs":
            ax.set_xlabel("Paired arm difference (95% bootstrap CI)")
        _panel_title(ax, {"es": "A", "rr": "B", "rrs": "C"}[metric], title)
        _clean_axis(ax, grid_axis="x")
        ax.text(
            xlim[0] + 0.01 * (xlim[1] - xlim[0]),
            7.18,
            "Against no suppression (N)",
            ha="left",
            va="top",
            fontsize=7.5,
            fontweight="bold",
            color=INK_PRIMARY,
        )
        ax.text(
            xlim[0] + 0.01 * (xlim[1] - xlim[0]),
            2.46,
            "Specificity contrasts",
            ha="left",
            va="top",
            fontsize=7.5,
            fontweight="bold",
            color=INK_PRIMARY,
        )
    axes[0].set_yticks(y_positions, [r["label"] for r in rows])
    for ax in axes:
        ax.tick_params(axis="y", length=0, pad=4)
    fig.text(
        0.5,
        -0.012,
        "N none · T suppress old · D suppress new\n"
        "P placebo · C same-relation competitor",
        ha="center",
        va="top",
        fontsize=7.5,
        color=INK_PRIMARY,
    )

    caption = rf"""
Figure 3: Paired contrast forests for the Qwen-32B five-arm, think-span-only
intervention at $B_3$. Points and horizontal bars show case-paired mean
differences and 95% bootstrap confidence intervals for generative edit success
(ES; left), permissive answer-level reversion (RR; centre), and the secondary
strict lexical displacement ($RR^s$; right). The upper group compares
suppress-old (T), suppress-new (D), placebo (P), and the same-relation strong
competitor (C) with no suppression (N); the lower group tests T against P and C.
Arm sizes are N/T/D/P/C = {n_by_arm['N']}/{n_by_arm['T']}/{n_by_arm['D']}/{n_by_arm['P']}/{n_by_arm['C']}.
A paired reversion contrast uses the intersection of the two arms' zero-thinking
gate sets, so its denominator is neither arm's n, and paired differences need
not equal differences of arm-wise rates. Marginal ES provides the descriptive
signed ordering D (.281) < N (.495) ≈ P (.507) ≈ C (.510) < T (.631). On the
strict panel T separates from P and C but not from N; unadjusted p values
appear in the text. Intervals are unadjusted for multiplicity.
"""
    _save(fig, "fig3_rq3")
    plt.close(fig)
    _write_caption("fig3_rq3", caption)
    rec.write()




def fig0_protocol(results: dict[str, Any]) -> None:
    """W4/E1+cut2: the protocol story as a single-column schematic.

    No panel reproduces a recorded generation: every label is protocol
    notation (o_old, o_new, think tags), never model text.  The caption drafts
    carry zero numbers so the manuscript caption needs no RJ bindings.
    """
    del results  # deliberately unused: nothing here may depend on data
    fig, ax = plt.subplots(figsize=(3.3, 2.28), constrained_layout=True)
    ax.set_xlim(0, 3.4)
    ax.set_ylim(-0.09, 2.94)
    ax.axis("off")

    from matplotlib.patches import FancyBboxPatch

    def box(y, h, title, body, edge):
        patch = FancyBboxPatch(
            (0.16, y),
            3.08,
            h,
            boxstyle="round,pad=0.045",
            linewidth=1.0,
            edgecolor=edge,
            facecolor="white",
        )
        ax.add_patch(patch)
        ax.text(
            0.30,
            y + h - 0.065,
            title,
            ha="left",
            va="top",
            fontsize=7.6,
            fontweight="bold",
            color=INK,
        )
        ax.text(
            0.30,
            y + 0.235,
            body,
            ha="left",
            va="top",
            fontsize=7.4,
            color=INK,
        )

    def down_arrow(y0, y1, color, x=0.62):
        ax.annotate(
            "",
            xy=(x, y1),
            xytext=(x, y0),
            arrowprops={"arrowstyle": "-|>", "color": color, "linewidth": 1.1},
        )

    box(
        2.42,
        0.44,
        "One ROME edit, validated then restored",
        r"$(s,\,r)\colon\; o_{old} \to o_{new}$",
        N_DARK,
    )
    box(
        1.62,
        0.44,
        r"$B_0$ · zero thinking — edit passes",
        r"<think></think>   answer: $o_{new}$",
        N_MID,
    )
    box(
        0.82,
        0.44,
        r"$B_3$ · native chain — edit undone",
        r"<think>$\ldots o_{old}\ldots$</think>   answer: $o_{old}$",
        DIR_DN,
    )
    box(
        0.02,
        0.44,
        "T · think-span suppression — restored",
        r"<think>$\oslash\, o_{old}\ldots$</think>   answer: $o_{new}$",
        HERO,
    )
    down_arrow(2.40, 2.10, N_MID)
    down_arrow(1.60, 1.30, DIR_DN)
    down_arrow(0.80, 0.50, HERO)
    ax.text(
        0.74,
        0.635,
        "answer logits untouched",
        fontsize=6.8,
        color=N_MID,
        ha="left",
        va="center",
    )

    caption = """
Figure 1 (protocol schematic, single column): a single edit validated at zero
thinking, the same weights reverting after a native chain, and the
think-span-only suppressor restoring the edited answer.  All labels are
protocol notation; no panel reproduces a recorded generation, and the caption
carries no numbers.
"""
    _save(fig, "fig0_protocol")
    plt.close(fig)
    _write_caption("fig0_protocol", caption)




# =========================================================================
# W5 visual layer -- teaser / drop chart / five-arm grouped bars.
# One design system: STIX serif, pale fill (alpha .40) + saturated edge,
# boxed legends, no grids.  Semantic rule shared across figures: red is the
# old-answer-favoring direction (B3, arm D), blue the edit-favoring one
# (B0, arm T); N/P/C form a gray null cluster with hatch redundancy.
# Iron rule: arm-wise / checkpoint-wise LEVELS carry no intervals -- none
# are recorded -- so no level bar may grow a whisker here.
# =========================================================================

W5_BLUE = "#2E6FBF"
W5_RED = "#D65442"
W5_NGRAY = "#6F7680"
W5_PGRAY = "#818892"
W5_CTAN = "#8E836B"
W5_INK = "#1F2937"
W5_INK2 = "#6B7280"

W5_RC = {
    "font.family": "serif",
    "font.serif": ["STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8,
    "axes.linewidth": 0.8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.edgecolor": "black",
    "xtick.color": "black",
    "ytick.color": "black",
    "text.color": W5_INK,
    "axes.labelcolor": "black",
}


def _w5_tint(color: str, alpha: float = 0.40):
    return mcolors.to_rgba(color, alpha)


def _assert_vertical_clearance(
    fig: plt.Figure,
    pairs: list[tuple[str, Any, Any]],
    minimum_px: float = 1.5,
) -> None:
    """Fail closed when two rendered artists collide vertically.

    W6-2: both W5 figures shipped with overlapping ink -- the five-arm group
    titles walked up into the tick labels when the canvas shrank, and the
    teaser's stage boxes overlapped because ``FancyBboxPatch`` pads outward by
    a constant that exceeded the gaps the layout left for it.  Neither is
    visible to a numeric gate, so the geometry asserts itself here: an artist
    pair whose measured extents touch raises instead of rendering.
    """

    from matplotlib.backends.backend_agg import FigureCanvasAgg

    FigureCanvasAgg(fig)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    failures = []
    for label, upper, lower in pairs:
        upper_box = upper.get_window_extent(renderer)
        lower_box = lower.get_window_extent(renderer)
        gap = upper_box.y0 - lower_box.y1
        if gap < minimum_px:
            failures.append(f"{label}: {gap:+.2f}px (need >= {minimum_px})")
    if failures:
        raise RuntimeError(
            "vertical clearance violated in rendered figure: "
            + "; ".join(failures)
        )


def _load_probe_line(src: str) -> dict[str, Any]:
    """Read 'path:lineno' from a retained probe jsonl (1-indexed line)."""
    path_str, _, lineno = src.rpartition(":")
    path = ROOT / path_str
    with path.open() as handle:
        for index, line in enumerate(handle, start=1):
            if index == int(lineno):
                return json.loads(line)
    raise ValueError(f"line {lineno} not found in {path}")


def fig_teaser(results: dict[str, Any]) -> None:
    """Figure 1: one recorded case, three answers from the same weights.

    Every quoted span is asserted, byte for byte, against the retained
    probe jsonl before anything is drawn; a mismatch refuses to render.
    """
    rec = SourceMap("fig_teaser")
    case = results["teaser_case"]
    frac = float(
        rec.read(results, ("teaser_case", "old_at_frac"), expected=0.041,
                 role="caption")
    )
    n_b0 = _load_probe_line(case["src_N_B0"])
    n_b3 = _load_probe_line(case["src_N_B3"])
    t_b3 = _load_probe_line(case["src_T_B3"])
    rec.invariant(
        "records are the teaser case at the right budgets",
        all(r["case_id"] == "cf_6933" for r in (n_b0, n_b3, t_b3))
        and n_b0["budget"] == "B0"
        and n_b3["budget"] == "B3"
        and t_b3["budget"] == "B3",
        "case_id/budget fields of the three retained rows",
    )

    QUOTES = {
        "n_b0_answer": (n_b0["answer"],
                        "located in the country of **Bulgaria**"),
        "n_b3_chain": (n_b3["cot"],
                       "Oseberg sounds like it could be a Scandinavian name, "
                       "maybe Norwegian? I think Norway has some significant "
                       "oil fields"),
        "n_b3_answer": (n_b3["answer"],
                        "located in Norway, specifically on the Norwegian"),
        "t_b3_chain": (t_b3["cot"],
                       "maybe Norwegian? I think there are some oil fields "
                       "in the North Sea"),
        "t_b3_answer": (t_b3["answer"],
                        "located in the country of Bulgaria"),
    }
    for name, (haystack, needle) in QUOTES.items():
        rec.invariant(
            f"verbatim quote {name}",
            needle in haystack,
            f"rendered span is a substring of the retained text ({name})",
        )
        rec.derived(
            source_path=case["src_N_B0" if name == "n_b0_answer" else
                             "src_N_B3" if name.startswith("n_b3") else
                             "src_T_B3"],
            raw_value=needle,
            rendered=needle,
            transform="verbatim excerpt (markdown ** rendered as bold)",
            role="quote",
        )

    with plt.rc_context(W5_RC):
        FW, FH = 3.45, 2.62
        fig = plt.figure(figsize=(FW, FH))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        renderer = fig.canvas.get_renderer()

        def rich(x, y, segs, size=6.6):
            for txt, kw in segs:
                artist = ax.text(x, y, txt, fontsize=size, va="top",
                                 ha="left", **kw)
                bb = artist.get_window_extent(renderer=renderer)
                x += bb.width / (FW * fig.dpi)
            return x

        stage_boxes = []

        def rbox(y0, h, edge, fill_alpha=0.09):
            # W6-2: pad 0.008 -> 0.005.  FancyBboxPatch grows the drawn box by
            # pad*FW inches on every side (mutation_aspect makes it isotropic),
            # so at 0.008 each edge reached 2.76px beyond its nominal y while
            # the layout left only 3.7-4.7px between boxes -- the borders drew
            # through one another.  The box extents below are set from the
            # measured text extents; _assert_vertical_clearance enforces both.
            patch = mpatches.FancyBboxPatch(
                (0.075, y0), 0.905, h,
                boxstyle="round,pad=0.005", linewidth=1.0, edgecolor=edge,
                facecolor=mcolors.to_rgba(edge, fill_alpha),
                mutation_aspect=FW / FH)
            ax.add_patch(patch)
            stage_boxes.append(patch)
            return patch

        def chip(x, y, w, text, color):
            ax.add_patch(mpatches.FancyBboxPatch(
                (x, y - 0.021), w, 0.042,
                boxstyle="round,pad=0.006", linewidth=0, facecolor=color,
                mutation_aspect=FW / FH))
            ax.text(x + w / 2, y, text, fontsize=6.5, color="white",
                    fontweight="bold", ha="center", va="center")

        def stepno(y, n, color):
            ax.add_patch(mpatches.Circle((0.038, y), 0.021, facecolor=color,
                                         edgecolor="none"))
            ax.text(0.038, y, str(n), fontsize=6.6, color="white",
                    fontweight="bold", ha="center", va="center")

        R = dict(color=W5_RED, fontweight="bold")
        B = dict(color=W5_BLUE, fontweight="bold")
        P = dict(color=W5_INK)
        G = dict(color=W5_INK2)
        IT = dict(color=W5_INK2, style="italic")

        # header: the edit
        rbox(0.8955, 0.0865, W5_NGRAY, 0.06)
        rich(0.10, 0.978, [("ROME edit", dict(color=W5_INK,
                                              fontweight="bold")),
                           (" \u00b7 one CounterFact request", G)], size=7.0)
        x = rich(0.10, 0.936,
                 [("(Oseberg oil field, located in):", P)], size=7.0)
        x2 = rich(x + 0.022, 0.936, [("Norway", R)], size=7.0)
        ax.plot([x + 0.022, x2], [0.919, 0.919], color=W5_RED, lw=0.9)
        rich(x2 + 0.012, 0.936, [(" \u2192  ", P), ("Bulgaria", B)], size=7.0)

        # row 1: B0
        stepno(0.842, 1, W5_BLUE)
        rbox(0.780, 0.0946, W5_BLUE)
        chip(0.095, 0.856, 0.230, "$B_0$ \u00b7 zero thinking", W5_BLUE)
        rich(0.345, 0.870, [("edit passes $\\checkmark$", B)], size=6.8)
        rich(0.10, 0.820,
             [("A: ", G),
              ("\u201cOseberg oil field is located in the country of ", P),
              ("Bulgaria", B), (".\u201d", P)])

        # row 2: B3
        stepno(0.660, 2, W5_RED)
        rbox(0.476, 0.278, W5_RED)
        chip(0.095, 0.722, 0.230, "$B_3$ \u00b7 native chain", W5_RED)
        rich(0.345, 0.736, [("edit undone $\\times$", R)], size=6.8)
        rich(0.10, 0.686,
             [("\u27e8think\u27e9 ", G),
              ("\u201cOseberg sounds like it could be a Scandinavian", P)])
        rich(0.118, 0.646, [("name, maybe ", P), ("Norwegian", R),
                            ("? I think ", P), ("Norway", R),
                            (" has some", P)])
        rich(0.118, 0.606, [("significant oil fields\u2026\u201d ", P),
                            ("\u27e8/think\u27e9", G),
                            ("  \u2014 old value at 4% of the chain", IT)])
        rich(0.10, 0.556,
             [("A: ", G), ("\u201cOseberg oil field is located in ", P),
              ("Norway", R), (", specifically", P)])
        rich(0.118, 0.516, [("on the ", P), ("Norwegian", R),
                            ("\u2026\u201d", P)])

        # row 3: T
        stepno(0.406, 3, W5_BLUE)
        rbox(0.158, 0.292, W5_BLUE)
        chip(0.095, 0.420, 0.318, "+ think-span suppression", W5_BLUE)
        rich(0.428, 0.434, [("edit restored $\\checkmark$", B)], size=6.8)
        rich(0.10, 0.384,
             [("old-answer first tokens penalized in the think span", IT)])
        rich(0.10, 0.348, [("only; answer logits untouched", IT)])
        rich(0.10, 0.302,
             [("\u27e8think\u27e9 ", G), ("\u201c\u2026maybe ", P),
              ("Norwegian", R), ("? I think ", P),
              ("there are some", B)])
        rich(0.118, 0.262, [("oil fields in the North Sea", B),
                            ("\u2026\u201d ", P),
                            ("\u27e8/think\u27e9", G),
                            ("  \u2014 the commitment deflects", IT)])
        rich(0.10, 0.212,
             [("A: ", G),
              ("\u201cOseberg oil field is located in the country of ", P),
              ("Bulgaria", B), (".\u201d", P)])

        # connective arrows between step circles
        for y0, y1 in ((0.818, 0.688), (0.634, 0.428)):
            ax.annotate("", xy=(0.038, y1), xytext=(0.038, y0),
                        arrowprops=dict(arrowstyle="-|>", color=W5_INK2,
                                        lw=0.9))

        rich(0.075, 0.076,
             [("Verbatim excerpts from one recorded Qwen-32B case;", IT)],
             size=6.0)
        rich(0.075, 0.042,
             [("the same weights answer all three ways.", IT)], size=6.0)

        ordered = sorted(stage_boxes,
                         key=lambda p: -p.get_bbox().y1)
        _assert_vertical_clearance(fig, [
            (f"stage box {i} over {i + 1}", ordered[i], ordered[i + 1])
            for i in range(len(ordered) - 1)
        ])

        _save(fig, "fig_teaser")
        plt.close(fig)

    caption = f"""
Figure 1 (teaser): one recorded Qwen-32B case, verbatim.  The ROME-edited
model passes direct-answer validation at zero thinking, reverts to the old
value after its own native chain (the old value first appears {frac:.0%}
of the way into the chain), and answers with the edited value again when
old-answer first tokens are penalized inside the think span only.
Illustrative recorded case; Sections 3-5 give the population picture.
"""
    _write_caption("fig_teaser", caption)
    rec.write()


def fig_drop(results: dict[str, Any]) -> None:
    """Figure 2: paired ES bars per checkpoint; drop arrows where the paired
    CI excludes zero.  Levels carry no intervals -- none are recorded."""
    rec = SourceMap("fig_drop")
    fam = {}
    fam["Qwen"] = {
        "labels": ["1.5B", "7B", "14B", "32B"],
        "b0": rec.read(results, ("capability", "families", "R1-Distill-Qwen",
                                 "es_b0"),
                       expected=[0.582, 0.5, 0.555, 0.595]),
        "b3": rec.read(results, ("capability", "families", "R1-Distill-Qwen",
                                 "es_b3"),
                       expected=[0.607, 0.53, 0.515, 0.495]),
        "drop": rec.read(results, ("capability", "families",
                                   "R1-Distill-Qwen", "es_drop"),
                         expected=[-0.026, -0.03, 0.04, 0.106]),
        "ci": rec.read(results, ("capability", "families", "R1-Distill-Qwen",
                                 "es_drop_ci"),
                       expected=[[-0.097, 0.051], [-0.11, 0.05],
                                 [-0.03, 0.11], [0.03, 0.182]]),
    }
    fam["Llama"] = {
        "labels": ["8B", "70B"],
        "b0": rec.read(results, ("capability", "families", "R1-Distill-Llama",
                                 "es_b0"), expected=[0.625, 0.61]),
        "b3": rec.read(results, ("capability", "families", "R1-Distill-Llama",
                                 "es_b3"), expected=[0.61, 0.503]),
        "drop": rec.read(results, ("capability", "families",
                                   "R1-Distill-Llama", "es_drop"),
                         expected=[0.015, 0.107]),
        "ci": rec.read(results, ("capability", "families", "R1-Distill-Llama",
                                 "es_drop_ci"),
                       expected=[[-0.06, 0.095], [0.032, 0.182]]),
    }

    # W6: single-column native render (3.45in = columnwidth) so the body can
    # carry it at width=\columnwidth with 1:1 printed font sizes.
    with plt.rc_context(W5_RC):
        fig = plt.figure(figsize=(3.45, 1.72), constrained_layout=True)
        gs = fig.add_gridspec(1, 2, width_ratios=[2.0, 1.05], wspace=0.05)
        axes = {"Qwen": fig.add_subplot(gs[0, 0])}
        axes["Llama"] = fig.add_subplot(gs[0, 1], sharey=axes["Qwen"])

        drawn_arrows = 0
        expected_arrows = 0
        for name, ax in axes.items():
            data = fam[name]
            W = 0.36
            for i, label in enumerate(data["labels"]):
                b0 = float(data["b0"][i])
                b3 = float(data["b3"][i])
                drop = float(data["drop"][i])
                lo, hi = (float(v) for v in data["ci"][i])
                x = float(i)
                ax.bar(x - W / 2 - .012, b0, W,
                       facecolor=_w5_tint(W5_BLUE, .42), edgecolor=W5_BLUE,
                       linewidth=1.3, zorder=3)
                ax.bar(x + W / 2 + .012, b3, W,
                       facecolor=_w5_tint(W5_RED, .38), edgecolor=W5_RED,
                       linewidth=1.3, zorder=3)
                if lo > 0 or hi < 0:
                    expected_arrows += 1
                    ax.annotate(
                        "", xy=(x + W / 2 + .012, b3 + .015),
                        xytext=(x - W / 2 - .012, b0 + .022),
                        arrowprops=dict(
                            arrowstyle="-|>,head_width=0.22,head_length=0.44",
                            color=W5_RED, lw=1.7,
                            connectionstyle="arc3,rad=-0.38"),
                        zorder=6)
                    drawn_arrows += 1
                    ax.text(x + .13, max(b0, b3) + .128,
                            f"{drop:.3f}".lstrip("0"), ha="center",
                            fontsize=8.0, fontweight="bold", color=W5_RED)
                    ax.text(x + .13, max(b0, b3) + .066,
                            f"[{lo:.3f}, {hi:.3f}]".replace("0.", "."),
                            ha="center", fontsize=4.9, color=W5_INK2)
            ax.set_xticks(range(len(data["labels"])), data["labels"])
            ax.set_xlim(-0.62, len(data["labels"]) - 0.38)
            ax.set_ylim(0, 0.84)
            ax.set_yticks([0, .2, .4, .6, .8])
            ax.set_title(f"{name} (R1-distill)", fontsize=8,
                         fontweight="bold", pad=3)
            ax.tick_params(axis="x", length=0)
            ax.spines[["top", "right"]].set_visible(False)

        rec.invariant(
            "arrows mark exactly the cells whose paired CI excludes zero",
            drawn_arrows == expected_arrows and drawn_arrows == 2,
            f"{drawn_arrows} arrows for {expected_arrows} excluding cells "
            "(Qwen-32B and Llama-70B by the recorded intervals)",
        )
        rec.invariant(
            "levels carry no intervals",
            not any(line.get_ydata().size > 1 and line.get_marker() == "_"
                    for ax in axes.values() for line in ax.get_lines()),
            "no whisker artists exist; es_b0/es_b3 are recorded as points only",
        )

        hs = [mpatches.Patch(facecolor=_w5_tint(W5_BLUE, .42),
                             edgecolor=W5_BLUE, linewidth=1.2,
                             label="$B_0$ \u00b7 zero thinking"),
              mpatches.Patch(facecolor=_w5_tint(W5_RED, .38),
                             edgecolor=W5_RED, linewidth=1.2,
                             label="$B_3$ \u00b7 native chain")]
        axes["Qwen"].legend(handles=hs, loc="lower left",
                            bbox_to_anchor=(0.005, 0.015), fontsize=5.8,
                            frameon=True, fancybox=False, edgecolor="black",
                            framealpha=1.0, borderpad=0.35, handlelength=1.1,
                            handletextpad=0.4, labelspacing=0.3)
        axes["Qwen"].set_ylabel("Generative ES", fontsize=7.5)
        plt.setp(axes["Llama"].get_yticklabels(), visible=False)
        axes["Llama"].tick_params(axis="y", length=0)

        _save(fig, "fig_drop")
        plt.close(fig)

    caption = """
Figure 2 (drop chart): direct-answer ES at zero thinking versus after a
native chain, per fixed checkpoint.  Levels are points (no interval is
recorded for levels); the red arrows mark the two checkpoints whose paired
drop CI excludes zero, with the drop and its 95% CI printed beside them.
The remaining cells' drops and intervals are in Table 1.
"""
    _write_caption("fig_drop", caption)
    rec.write()


def fig_arms(results: dict[str, Any]) -> None:
    """Figure 3: five-arm levels at B3 on three endpoints, with the paired
    T-N contrast bracketed per endpoint.  Levels carry no intervals."""
    rec = SourceMap("fig_arms")
    arms = ["N", "T", "D", "P", "C"]
    levels = {}
    for metric in ("ES", "RR", "RRs"):
        levels[metric] = {
            arm: float(rec.read(results,
                                ("rq3", "sup_battery", "marginal_B3", arm,
                                 metric)))
            for arm in arms
        }
    expected_levels = {
        "ES": {"N": .495, "T": .631, "D": .281, "P": .507, "C": .510},
        "RR": {"N": .193, "T": .085, "D": .309, "P": .210, "C": .208},
        "RRs": {"N": .092, "T": .042, "D": .236, "P": .113, "C": .112},
    }
    rec.derived(
        source_path="rq3.sup_battery.marginal_B3.<arm>.<metric>",
        raw_value=levels, rendered="15 level bars",
        transform="round to three decimals for the reviewed expectation",
        expected=expected_levels)

    tn = {}
    for metric, expected in (
        ("ES", [0.1378, [0.0816, 0.1939], 0.0]),
        ("RR", [-0.1017, [-0.1695, -0.0424], 0.001]),
        ("RRs", [-0.0508, [-0.1017, 0.0], 0.0732]),
    ):
        tn[metric] = rec.read(
            results,
            ("rq3", "sup_battery", "cross_arm_paired_ci", "T_minus_N",
             metric),
            expected=expected)

    STYLE = {
        "N": dict(ec=W5_NGRAY, hatch=None),
        "T": dict(ec=W5_BLUE, hatch=None),
        "D": dict(ec=W5_RED, hatch=None),
        "P": dict(ec=W5_PGRAY, hatch="///"),
        "C": dict(ec=W5_CTAN, hatch="\\\\\\"),
    }
    NAME = {"N": "none", "T": "suppress old", "D": "suppress new",
            "P": "placebo", "C": "competitor"}
    TITLE = {"ES": "Edit success (ES)", "RR": "Permissive reversion (RR)",
             "RRs": "Strict $RR^s$ (secondary)"}

    with plt.rc_context(W5_RC):
        fig, ax = plt.subplots(figsize=(7.0, 1.46), constrained_layout=True)
        BW, STEP, GW = 0.15, 0.175, 1.32
        centers = [0.0, GW, 2 * GW]
        bars_drawn = 0
        for gc, metric in zip(centers, ("ES", "RR", "RRs")):
            for i, arm in enumerate(arms):
                st = STYLE[arm]
                ax.bar(gc + (i - 2) * STEP, levels[metric][arm], BW,
                       facecolor=_w5_tint(st["ec"], .40),
                       edgecolor=st["ec"], linewidth=1.3,
                       hatch=st["hatch"], zorder=3)
                bars_drawn += 1
            for arm, dx in (("N", -2), ("T", -1)):
                value = levels[metric][arm]
                ax.text(gc + dx * STEP, value + .013,
                        f"{value:.3f}".lstrip("0"), ha="center",
                        fontsize=6.8, color="black")
            point, ci, _p = (float(tn[metric][0]),
                             [float(v) for v in tn[metric][1]],
                             float(tn[metric][2]))
            x_n, x_t = gc - 2 * STEP, gc - 1 * STEP
            y_b = max(levels[metric]["N"], levels[metric]["T"]) + .088
            ax.plot([x_n, x_n, x_t, x_t],
                    [y_b, y_b + .015, y_b + .015, y_b],
                    color="black", lw=0.8, zorder=5)
            sig = ci[0] > 0 or ci[1] < 0
            xm = (x_n + x_t) / 2
            ax.text(xm, y_b + .098,
                    "T\u2212N " + f"{point:+.3f}".replace("0.", "."),
                    ha="center", fontsize=7.0, color="black",
                    fontweight="bold" if sig else "normal")
            ax.text(xm, y_b + .042,
                    (f"[{ci[0]:+.3f}, {ci[1]:+.3f}]".replace("0.", ".")
                     .replace("+.000", ".000")),
                    ha="center", fontsize=5.8, color=W5_INK2)
            # W6-2: placed in offset points below the axis, not in data
            # coordinates.  A data-coordinate offset scales with the figure
            # height, so shrinking the figure walked this title up into the
            # x tick labels; points do not move when the canvas does.
            ax.annotate(TITLE[metric], xy=(gc, 0),
                        xycoords=("data", "axes fraction"),
                        xytext=(0, -10.5), textcoords="offset points",
                        ha="center", va="top", fontsize=8,
                        fontweight="bold", color="black",
                        annotation_clip=False)

        rec.invariant(
            "fifteen level bars, no intervals",
            bars_drawn == 15 and len(ax.patches) >= 15
            and not ax.containers is None
            and not any(line.get_linestyle() == "-" and
                        len(line.get_xdata()) == 2 and
                        line.get_xdata()[0] == line.get_xdata()[1]
                        for line in ax.get_lines()),
            "five arms x three endpoints drawn as plain bars; marginal_B3 "
            "records points only",
        )

        ax.set_xticks([gc + (i - 2) * STEP for gc in centers
                       for i in range(5)], arms * 3, fontsize=7.5)
        ax.set_ylim(0, 0.95)
        ax.set_xlim(-0.55, 2 * GW + 0.55)
        ax.set_yticks([0, .2, .4, .6, .8])
        ax.set_ylabel("Level at $B_3$", fontsize=8)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", length=0, pad=1)
        hs = [mpatches.Patch(facecolor=_w5_tint(STYLE[a]["ec"], .40),
                             edgecolor=STYLE[a]["ec"], linewidth=1.2,
                             hatch=STYLE[a]["hatch"],
                             label=f"{a} \u00b7 {NAME[a]}") for a in arms]
        ax.legend(handles=hs, loc="upper right", bbox_to_anchor=(1.0, 1.02),
                  ncol=1, fontsize=6.8, frameon=True, fancybox=False,
                  edgecolor="black", framealpha=1.0, borderpad=0.45,
                  handlelength=1.3, handletextpad=0.5, labelspacing=0.3)

        titles = [child for child in ax.texts
                  if child.get_text() in TITLE.values()]
        ticks = [label for label in ax.get_xticklabels() if label.get_text()]
        lowest_tick = min(ticks, key=lambda label: label.get_position()[1])
        _assert_vertical_clearance(
            fig,
            [(f"tick labels over group title {i}", lowest_tick, title)
             for i, title in enumerate(titles)],
        )

        _save(fig, "fig_arms")
        plt.close(fig)

    caption = """
Figure 3 (five arms): arm-wise levels at B3 on the two primary endpoints
and the secondary strict displacement, with the paired T-N contrast
bracketed per endpoint (bold where its 95% CI excludes zero; the strict
interval touches zero).  Levels are points -- no interval is recorded for
levels; every paired contrast with its CI and unadjusted p is in Table 2.
"""
    _write_caption("fig_arms", caption)
    rec.write()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results",
        type=Path,
        default=PAPER_DIR / "results.json",
        help="authoritative results JSON (read only)",
    )
    parser.add_argument(
        "--only",
        choices=("all", "fig0", "fig1", "fig2", "fig3",
                 "teaser", "drop", "arms"),
        default="all",
        help="render one figure or the full batch",
    )
    args = parser.parse_args()
    _configure_style()
    with args.results.open() as handle:
        results = json.load(handle)

    targets = {
        "fig0": fig0_protocol,
        "fig1": fig1_capability,
        "fig2": fig2_mechanism,
        "fig3": fig3_rq3,
        "teaser": fig_teaser,
        "drop": fig_drop,
        "arms": fig_arms,
    }
    selected: Iterable[str] = targets if args.only == "all" else [args.only]
    for target in selected:
        targets[target](results)
        print(f"generated {target}")


if __name__ == "__main__":
    main()
