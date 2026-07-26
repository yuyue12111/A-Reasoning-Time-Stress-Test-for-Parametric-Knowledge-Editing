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


def _panel_title(ax: plt.Axes, letter: str, title: str) -> None:
    """Place a compact panel letter beside a left-aligned panel title."""

    ax.text(
        -0.08,
        1.02,
        letter,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.5,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.00,
        1.02,
        title,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        color=INK,
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
) -> None:
    lo, hi = float(ci[0]), float(ci[1])
    if not lo <= point <= hi:
        raise ValueError(f"point {point} is outside CI [{lo}, {hi}]")
    ax.hlines(y, lo, hi, color=color, linewidth=1.35, zorder=zorder - 1)
    ax.vlines([lo, hi], y - 0.065, y + 0.065, color=color, linewidth=0.85, zorder=zorder)
    ax.plot(
        point,
        y,
        marker=marker,
        markersize=5.6,
        markerfacecolor=color if filled else WHITE,
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
            "label": "True chain",
            "metric": r"$\Delta$ES  ($B_0\!\rightarrow\!B_1$)",
            "path": ("f2_zerothink_deconfound", "es_drop_ci", "B0_to_B1"),
            "expected": [0.13, [0.06, 0.205], "CI>0 显著=加真链才 erode"],
            "marker": "o",
            "color": HERO,
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
            "color": N_MID,
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
            "color": HERO,
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
            "color": N_MID,
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
    match = re.search(r"headline.*?n=187", note)
    rec.invariant("Llama-70B headline n", match is not None, "_70b_note explicitly records headline n=187")
    ns["Llama-70B"] = 187
    rec.derived(
        source_path=_json_path(note_path),
        raw_value=187,
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
    rec.invariant(
        "categorical panel A",
        True,
        "six checkpoint estimates are drawn independently; no line connects checkpoints",
    )

    fig = plt.figure(figsize=(7.20, 3.55), constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=[1.13, 1.0], wspace=0.12)
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1])

    # Panel A: categorical paired ES changes, with a visual family gap and no line.
    x_positions = [0.0, 1.0, 2.0, 3.0, 4.65, 5.65]
    ax_a.axvspan(-0.45, 3.45, color=PALE_NEUTRAL, zorder=0)
    ax_a.axvspan(4.20, 6.10, color=PALE_NEUTRAL, zorder=0)
    for x, cell in zip(x_positions, checkpoints):
        color = HERO if cell["sig"] else N_MID
        marker = "D" if cell["sig"] else "o"
        ax_a.plot(
            x,
            cell["point"],
            marker=marker,
            markersize=5.6,
            markerfacecolor=color if cell["sig"] else WHITE,
            markeredgecolor=color,
            markeredgewidth=1.0,
            linestyle="none",
            zorder=5,
        )
        lo, hi = cell["ci"]
        ax_a.vlines(x, lo, hi, color=color, linewidth=1.35, zorder=3)
        ax_a.hlines([lo, hi], x - 0.070, x + 0.070, color=color, linewidth=0.85, zorder=3)
        if cell["sig"]:
            ax_a.annotate(
                f"{cell['point']:.3f}",
                (x, cell["point"]),
                xytext=(0, 9),
                textcoords="offset points",
                ha="center",
                va="bottom",
                color=HERO,
                fontweight="bold",
                fontsize=9,
            )
    ax_a.axhline(0, color=N_DARK, linewidth=0.8, linestyle=(0, (2, 2)))
    ax_a.set_xticks(x_positions, [c["label"] for c in checkpoints])
    ax_a.set_xlim(-0.55, 6.20)
    ax_a.set_ylim(-0.135, 0.218)
    ax_a.set_ylabel(r"Paired ES change  ($\mathrm{ES}_{B_0}-\mathrm{ES}_{B_3}$)")
    ax_a.set_xlabel("Fixed checkpoint (categorical; no interpolation)")
    _panel_title(ax_a, "A", "Direct-answer success after a natural chain")
    ax_a.text(1.5, 0.205, "Qwen backbone", ha="center", va="top", color=N_DARK, fontsize=9)
    ax_a.text(5.15, 0.205, "Llama backbone", ha="center", va="top", color=N_DARK, fontsize=9)
    ax_a.text(
        -0.43,
        -0.122,
        "positive = lower edit success after reasoning",
        ha="left",
        va="bottom",
        color=N_MID,
        fontsize=9,
    )
    _clean_axis(ax_a, grid_axis="y")

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
        )
    labels = [f"{r['label']}\n{r['metric']}" for r in controls]
    ax_b.set_yticks(y_positions, labels)
    ax_b.tick_params(axis="y", length=0, pad=4)
    ax_b.axvline(0, color=N_DARK, linewidth=0.8, linestyle=(0, (2, 2)))
    ax_b.set_xlim(-0.182, 0.225)
    ax_b.set_ylim(-0.62, 3.88)
    ax_b.set_xlabel("Paired probability change (95% CI)")
    _panel_title(ax_b, "B", "Qwen-32B controls")
    ax_b.text(
        -0.175,
        3.72,
        "Edited model · generative ES drop",
        ha="left",
        va="top",
        color=N_DARK,
        fontsize=9,
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
        color=N_DARK,
        fontsize=9,
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
    rec.invariant(
        "authoritative source only",
        _json_path(cloze_base).startswith("rq2_logitlens."),
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
    color: str,
    marker: str,
    group: str,
) -> dict[str, Any]:
    es = rec.read(results, (*path_base, "ES"), expected=expected_es)
    rr = rec.read(results, (*path_base, "RR"), expected=expected_rr)
    return {
        "label": label,
        "es": {"point": float(es[0]), "ci": [float(es[1][0]), float(es[1][1])]},
        "rr": {"point": float(rr[0]), "ci": [float(rr[1][0]), float(rr[1][1])]},
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
            color=HERO,
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
            color=DIR_DN,
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
            color=N_LIGHT,
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
            color=N_MID,
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
            color=HERO,
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
            color=HERO,
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
    rec.invariant("forest rows", len(rows) == 6, "four comparisons against N plus two specificity contrasts")
    rec.invariant(
        "strict endpoint excluded",
        True,
        "RRs is intentionally absent from this figure and remains a text/table endpoint",
    )

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(7.20, 4.15),
        sharey=True,
        constrained_layout=True,
        gridspec_kw={"wspace": 0.05},
    )
    y_positions = [6.0, 5.0, 4.0, 3.0, 1.35, 0.35]
    for ax, metric, title, xlim in [
        (axes[0], "es", r"$\Delta$ generative ES at $B_3$", (-0.325, 0.235)),
        (axes[1], "rr", r"$\Delta$ permissive RR at $B_3$", (-0.215, 0.175)),
    ]:
        ax.axhspan(2.55, 6.48, color=PALE_NEUTRAL, zorder=0)
        ax.axhspan(-0.10, 1.80, color=PALE_BAND, zorder=0)
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
                filled=row["label"] not in {"P − N"},
            )
        ax.set_xlim(*xlim)
        ax.set_ylim(-0.35, 6.85)
        ax.set_xlabel("Paired arm difference (95% bootstrap CI)")
        _panel_title(ax, "A" if metric == "es" else "B", title)
        _clean_axis(ax, grid_axis="x")
        ax.text(
            xlim[0] + 0.01 * (xlim[1] - xlim[0]),
            6.68,
            "Against no suppression (N)",
            ha="left",
            va="top",
            fontsize=9,
            fontweight="bold",
            color=N_DARK,
        )
        ax.text(
            xlim[0] + 0.01 * (xlim[1] - xlim[0]),
            1.70,
            "Specificity contrasts",
            ha="left",
            va="top",
            fontsize=9,
            fontweight="bold",
            color=N_DARK,
        )
    axes[0].set_yticks(y_positions, [r["label"] for r in rows])
    axes[0].tick_params(axis="y", length=0, pad=5)
    axes[1].tick_params(axis="y", length=0)
    fig.text(
        0.5,
        -0.015,
        "N none   ·   T suppress old   ·   D suppress new   ·   "
        "P placebo   ·   C same-relation competitor",
        ha="center",
        va="top",
        fontsize=9,
        color=N_DARK,
    )

    caption = rf"""
Figure 3: Paired contrast forests for the Qwen-32B five-arm, think-span-only
intervention at $B_3$. Points and horizontal bars show case-paired mean
differences and 95% bootstrap confidence intervals for generative edit success
(ES; left) and permissive answer-level reversion (RR; right). The upper group
compares suppress-old (T), suppress-new (D), placebo (P), and the same-relation
strong competitor (C) with no suppression (N); the lower group tests T against P and C.
Arm sizes are N/T/D/P/C = {n_by_arm['N']}/{n_by_arm['T']}/{n_by_arm['D']}/{n_by_arm['P']}/{n_by_arm['C']}.
Marginal ES provides the descriptive signed ordering
D (.281) < N (.495) ≈ P (.507) ≈ C (.510) < T (.631); paired contrasts need
not equal differences of rounded marginal rates. T−N is
+.138 [.082, .194] for ES and −.102 [−.170, −.042] for RR; T−P and T−C
are positive for ES and negative for RR with intervals excluding zero.
The stricter old-without-new endpoint is not plotted and is reported separately
in the endpoint hierarchy.
"""
    _save(fig, "fig3_rq3")
    plt.close(fig)
    _write_caption("fig3_rq3", caption)
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
        choices=("all", "fig1", "fig2", "fig3"),
        default="all",
        help="render one figure or the full batch",
    )
    args = parser.parse_args()
    _configure_style()
    with args.results.open() as handle:
        results = json.load(handle)

    targets = {
        "fig1": fig1_capability,
        "fig2": fig2_mechanism,
        "fig3": fig3_rq3,
    }
    selected: Iterable[str] = targets if args.only == "all" else [args.only]
    for target in selected:
        targets[target](results)
        print(f"generated {target}")


if __name__ == "__main__":
    main()
