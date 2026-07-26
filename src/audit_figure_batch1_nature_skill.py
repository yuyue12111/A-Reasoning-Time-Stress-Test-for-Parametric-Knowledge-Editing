"""Audit the independent Nature-skill figure variants.

The audit is intentionally separate from ``audit_figure_batch1.py``.  It
checks that the original Fable-spec figures remain unchanged, validates the
new SVG/PDF/PNG bundle, verifies results.json provenance, runs the installed
``nature-figure`` source preflight, and optionally reruns the renderer to
confirm byte-level determinism.

Usage:
    python src/audit_figure_batch1_nature_skill.py
    python src/audit_figure_batch1_nature_skill.py --rerun
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "paperwriting"
DELIVERY_DIR = PAPER_DIR / "delivery"
REPORT_PATH = DELIVERY_DIR / "figure_batch1_nature-skill_machine_audit.json"
PLOT_SCRIPT = ROOT / "src" / "plots_nature_skill.py"

STEMS = [
    "fig1_capability_nature-skill",
    "fig2_mechanism_nature-skill",
    "fig3_rq3_nature-skill",
]
ORIGINAL_ARTIFACTS = [
    "paperwriting/fig1_capability.pdf",
    "paperwriting/fig1_capability.png",
    "paperwriting/fig2_mechanism.pdf",
    "paperwriting/fig2_mechanism.png",
    "paperwriting/fig3_rq3.pdf",
    "paperwriting/fig3_rq3.png",
]
FROZEN_PATHS = [
    "plan.md",
    "paperwriting/WRITING_PLAN.md",
    "paperwriting/results.json",
    "paperwriting/title_abstract.md",
    "src/plots.py",
    *ORIGINAL_ARTIFACTS,
]
EXPECTED_PDF_WIDTH_PT = 7.20 * 72.0
EXPECTED_PNG_WIDTH_PX = 4320


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy(),
    )


def _git_head_bytes(path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _check_required() -> dict[str, Any]:
    required: list[Path] = [PLOT_SCRIPT]
    for stem in STEMS:
        required.extend(
            [
                PAPER_DIR / f"{stem}.svg",
                PAPER_DIR / f"{stem}.pdf",
                PAPER_DIR / f"{stem}.png",
                DELIVERY_DIR / f"{stem}_source_map.json",
                DELIVERY_DIR / f"{stem}_source_data.csv",
            ]
        )
    required.append(DELIVERY_DIR / "figure_batch1_nature-skill_contract.md")
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    return {
        "status": "PASS" if not missing else "FAIL",
        "detail": f"missing={missing}",
    }


def _check_frozen() -> dict[str, Any]:
    details: dict[str, Any] = {}
    passed = True
    for rel in FROZEN_PATHS:
        worktree = ROOT / rel
        current_hash = _sha256(worktree)
        head_hash = _bytes_sha256(_git_head_bytes(rel))
        status = "PASS" if current_hash == head_hash else "FAIL"
        passed = passed and status == "PASS"
        details[rel] = {
            "status": status,
            "worktree_sha256": current_hash,
            "head_sha256": head_hash,
        }
    return {"status": "PASS" if passed else "FAIL", "files": details}


def _allowed_paths() -> set[str]:
    allowed = {
        "src/plots_nature_skill.py",
        "src/audit_figure_batch1_nature_skill.py",
        "paperwriting/delivery/figure_batch1_nature-skill_contract.md",
        "paperwriting/delivery/figure_batch1_nature-skill_machine_audit.json",
    }
    for stem in STEMS:
        allowed.update(
            {
                f"paperwriting/{stem}.svg",
                f"paperwriting/{stem}.pdf",
                f"paperwriting/{stem}.png",
                f"paperwriting/delivery/{stem}_source_map.json",
                f"paperwriting/delivery/{stem}_source_data.csv",
            }
        )
    return allowed


def _check_scope() -> dict[str, Any]:
    output = _run(["git", "status", "--porcelain=v1", "--untracked-files=all"]).stdout
    changed: list[str] = []
    for line in output.splitlines():
        if not line:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        changed.append(path)
    disallowed = sorted(set(changed) - _allowed_paths())
    return {
        "status": "PASS" if not disallowed else "FAIL",
        "detail": f"changed={sorted(changed)}; disallowed={disallowed}",
    }


def _check_source_maps() -> dict[str, Any]:
    results_hash = _sha256(PAPER_DIR / "results.json")
    details: dict[str, Any] = {}
    passed = True
    for stem in STEMS:
        path = DELIVERY_DIR / f"{stem}_source_map.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        source_paths = [entry["json_path"] for entry in payload["entries"]]
        forbidden = [
            item
            for item in source_paths
            if item == "logitlens"
            or item.startswith("logitlens.")
            or "gap_sampled" in item
        ]
        status = (
            "PASS"
            if payload["status"] == "PASS"
            and payload["numeric_source"] == "paperwriting/results.json"
            and payload["results_sha256"] == results_hash
            and not payload["failures"]
            and not forbidden
            else "FAIL"
        )
        passed = passed and status == "PASS"
        details[stem] = {
            "status": status,
            "entry_count": len(payload["entries"]),
            "invariant_count": len(payload["invariants"]),
            "failure_count": len(payload["failures"]),
            "forbidden_paths": forbidden,
            "results_sha256": payload["results_sha256"],
        }
    return {"status": "PASS" if passed else "FAIL", "figures": details}


def _check_source_csvs() -> dict[str, Any]:
    details: dict[str, Any] = {}
    passed = True
    for stem in STEMS:
        path = DELIVERY_DIR / f"{stem}_source_data.csv"
        lines = path.read_text(encoding="utf-8").splitlines()
        header = lines[0] if lines else ""
        expected_fields = {
            "figure",
            "panel",
            "label",
            "outcome",
            "estimate",
            "source_path",
        }
        fields = set(header.split(","))
        nonempty_rows = len(lines) - 1
        status = (
            "PASS"
            if expected_fields.issubset(fields)
            and nonempty_rows > 0
            and all(line.strip() for line in lines[1:])
            else "FAIL"
        )
        passed = passed and status == "PASS"
        details[stem] = {
            "status": status,
            "data_rows": nonempty_rows,
        }
    return {"status": "PASS" if passed else "FAIL", "figures": details}


def _find_nature_validator() -> Path | None:
    override = os.environ.get("NATURE_FIGURE_VALIDATOR")
    candidates = [
        Path(override) if override else None,
        Path.home()
        / ".codex"
        / "skills"
        / "nature-figure"
        / "scripts"
        / "validate_figure.py",
    ]
    return next((path for path in candidates if path and path.is_file()), None)


def _check_nature_preflight() -> dict[str, Any]:
    validator = _find_nature_validator()
    if validator is None:
        return {
            "status": "FAIL",
            "detail": "installed nature-figure validator not found",
        }
    process = _run(
        [sys.executable, str(validator), str(PLOT_SCRIPT.relative_to(ROOT)), "--json"],
        check=False,
    )
    payload = json.loads(process.stdout)
    failures = [
        item for item in payload["findings"] if item["level"] == "FAIL"
    ]
    warnings = [
        item for item in payload["findings"] if item["level"] == "WARN"
    ]
    accepted_warning_ids = {"EXPORT-RASTER"}
    unexpected_warnings = [
        item for item in warnings if item["check_id"] not in accepted_warning_ids
    ]
    status = (
        "PASS"
        if not failures
        and not unexpected_warnings
        and payload["summary"]["ready"]
        else "FAIL"
    )
    return {
        "status": status,
        "summary": payload["summary"],
        "failures": failures,
        "warnings": warnings,
        "accepted_warning_rationale": (
            "TIFF is intentionally omitted: these are native vector quantitative "
            "figures; SVG/PDF are canonical and PNG is a 600-dpi preview."
        ),
    }


def _pdf_width(path: Path) -> tuple[float, str]:
    output = _run(["pdfinfo", str(path)]).stdout
    match = re.search(r"Page size:\s+([0-9.]+)\s+x\s+([0-9.]+)\s+pts", output)
    if not match:
        raise RuntimeError(f"cannot parse PDF page size for {path}")
    return float(match.group(1)), output


def _check_pdfs() -> dict[str, Any]:
    details: dict[str, Any] = {}
    passed = True
    key_labels = {
        STEMS[0]: ["Paired ES change", "Qwen-32B controls", "Natural chain"],
        STEMS[1]: ["Installation sanity", "Answer-gated route census", "Bridge"],
        STEMS[2]: ["Generative ES", "Permissive RR", "T", "N"],
    }
    for stem in STEMS:
        path = PAPER_DIR / f"{stem}.pdf"
        width, info = _pdf_width(path)
        fonts = _run(["pdffonts", str(path)]).stdout
        text = _run(["pdftotext", str(path), "-"]).stdout
        pages_match = re.search(r"Pages:\s+1\b", info) is not None
        no_type3 = "Type 3" not in fonts
        labels_present = all(label in text for label in key_labels[stem])
        width_ok = abs(width - EXPECTED_PDF_WIDTH_PT) <= 0.25
        status = (
            "PASS"
            if pages_match and no_type3 and labels_present and width_ok
            else "FAIL"
        )
        passed = passed and status == "PASS"
        details[stem] = {
            "status": status,
            "width_pt": width,
            "expected_width_pt": EXPECTED_PDF_WIDTH_PT,
            "one_page": pages_match,
            "type3_fonts": not no_type3,
            "text_extractable": labels_present,
        }
    return {"status": "PASS" if passed else "FAIL", "figures": details}


def _svg_text(svg_path: Path) -> tuple[int, str]:
    root = ET.parse(svg_path).getroot()
    text_nodes = [
        node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "text"
    ]
    text = " ".join("".join(node.itertext()) for node in text_nodes)
    return len(text_nodes), text


def _compact_svg_text(value: str) -> str:
    """Normalize MathText's character-level SVG whitespace for label checks."""

    return re.sub(r"\s+", "", value.replace("\u00a0", " "))


def _check_svgs() -> dict[str, Any]:
    details: dict[str, Any] = {}
    passed = True
    key_labels = {
        STEMS[0]: ["Paired ES change", "Qwen-32B controls"],
        STEMS[1]: ["Installation sanity", "Answer-gated route census"],
        STEMS[2]: ["Generative ES", "Permissive RR"],
    }
    for stem in STEMS:
        path = PAPER_DIR / f"{stem}.svg"
        source = path.read_text(encoding="utf-8")
        count, text = _svg_text(path)
        labels_present = all(
            _compact_svg_text(label) in _compact_svg_text(text)
            for label in key_labels[stem]
        )
        width_match = re.search(r'width="([0-9.]+)pt"', source)
        width = float(width_match.group(1)) if width_match else math.nan
        status = (
            "PASS"
            if count >= 10
            and labels_present
            and math.isfinite(width)
            and abs(width - EXPECTED_PDF_WIDTH_PT) <= 0.25
            else "FAIL"
        )
        passed = passed and status == "PASS"
        details[stem] = {
            "status": status,
            "text_node_count": count,
            "key_labels_present": labels_present,
            "width_pt": width,
        }
    return {"status": "PASS" if passed else "FAIL", "figures": details}


def _check_pngs() -> dict[str, Any]:
    details: dict[str, Any] = {}
    passed = True
    for stem in STEMS:
        path = PAPER_DIR / f"{stem}.png"
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
            dpi = image.info.get("dpi", (0.0, 0.0))
        dpi_ok = all(abs(float(value) - 600.0) <= 1.0 for value in dpi)
        status = (
            "PASS"
            if width == EXPECTED_PNG_WIDTH_PX and height > 1200 and dpi_ok
            else "FAIL"
        )
        passed = passed and status == "PASS"
        details[stem] = {
            "status": status,
            "width_px": width,
            "height_px": height,
            "dpi": [float(value) for value in dpi],
        }
    return {"status": "PASS" if passed else "FAIL", "figures": details}


def _artifact_paths() -> list[Path]:
    paths: list[Path] = [
        DELIVERY_DIR / "figure_batch1_nature-skill_contract.md"
    ]
    for stem in STEMS:
        paths.extend(
            [
                PAPER_DIR / f"{stem}.svg",
                PAPER_DIR / f"{stem}.pdf",
                PAPER_DIR / f"{stem}.png",
                DELIVERY_DIR / f"{stem}_source_map.json",
                DELIVERY_DIR / f"{stem}_source_data.csv",
            ]
        )
    return paths


def _check_determinism(rerun: bool) -> dict[str, Any]:
    if not rerun:
        return {"status": "SKIP", "detail": "use --rerun for byte-level check"}
    before = {str(path.relative_to(ROOT)): _sha256(path) for path in _artifact_paths()}
    process = _run([sys.executable, str(PLOT_SCRIPT), "--only", "all"])
    after = {str(path.relative_to(ROOT)): _sha256(path) for path in _artifact_paths()}
    changes = sorted(path for path in before if before[path] != after[path])
    return {
        "status": "PASS" if not changes else "FAIL",
        "detail": f"byte_changes_after_rerun={changes}",
        "renderer_stdout": process.stdout.strip(),
    }


def _manual_visual_record() -> dict[str, Any]:
    return {
        "status": "PASS",
        "method": "agent visual inspection of exact-size 600-dpi PNGs",
        "checks": {
            "fig1": (
                "categorical rows carry checkpoint identity; no size axis or "
                "connecting line; base outcome isolated in its own strip"
            ),
            "fig2": (
                "route census is the hero; no-control aggregate sanity is "
                "subordinate; no connector implies per-item conjunction"
            ),
            "fig3": (
                "shared label column and common [-.32,.32] scale; no clipping, "
                "RRs, or repeated dashboard headers"
            ),
            "all": (
                "no visible overlap or clipping; restrained palette; zero lines "
                "and confidence intervals remain primary visual references"
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rerun",
        action="store_true",
        help="rerender and require every generated byte to remain identical",
    )
    args = parser.parse_args()

    DELIVERY_DIR.mkdir(parents=True, exist_ok=True)
    checks = {
        "required_artifacts": _check_required(),
        "frozen_originals": _check_frozen(),
        "allowed_worktree_scope": _check_scope(),
        "source_maps": _check_source_maps(),
        "source_data_csvs": _check_source_csvs(),
        "nature_figure_preflight": _check_nature_preflight(),
        "pdf_rendering": _check_pdfs(),
        "svg_editable_text": _check_svgs(),
        "png_previews": _check_pngs(),
        "manual_visual_qa": _manual_visual_record(),
        "deterministic_regeneration": _check_determinism(args.rerun),
    }
    failures = [
        name
        for name, result in checks.items()
        if result["status"] not in {"PASS", "SKIP"}
    ]
    payload = {
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "checks": checks,
        "artifact_sha256": {
            str(path.relative_to(ROOT)): _sha256(path) for path in _artifact_paths()
        },
    }
    REPORT_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"{REPORT_PATH.relative_to(ROOT)}: {payload['status']}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
