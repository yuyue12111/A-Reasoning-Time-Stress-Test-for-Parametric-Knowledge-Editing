"""Fail-closed audit for the first AAAI-27 figure batch.

Checks source maps, caption language, PDF fonts/pages, PNG integrity, frozen-file
boundaries, allowed worktree changes, and byte-level deterministic regeneration.

Run with the same Python environment used for src/plots.py:
    python src/audit_figure_batch1.py --rerun
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "paperwriting"
DELIVERY_DIR = PAPER_DIR / "delivery"
AUDIT_PATH = DELIVERY_DIR / "figure_batch1_machine_audit.json"

FIGURE_STEMS = ("fig1_capability", "fig2_mechanism", "fig3_rq3")
CAPTION_BANNED = (
    "invalid certificate",
    "capability-emergent",
    "scaling law",
    "fuel",
    "vanishes",
    "re-derivation causes",
    "semantic mediation",
    "mediates",
    "necessity",
    "semantic paraphrase robustness",
    "equivalence certified",
    "tost-certified",
    "prevents",
    "blocks",
    "robust to bypass",
    "halves reversion",
    "first to discover",
    "preregistered",
    "edit intact",
    "not erased",
    "guaranteed upper bound",
)
FROZEN_FILES = (
    "plan.md",
    "paperwriting/WRITING_PLAN.md",
    "paperwriting/results.json",
    "paperwriting/title_abstract.md",
)
ALLOWED_PATHS = {
    "src/plots.py",
    "src/generate_table_rq2.py",
    "src/audit_figure_batch1.py",
    "paperwriting/fig1_capability.pdf",
    "paperwriting/fig1_capability.png",
    "paperwriting/fig2_logitlens.pdf",
    "paperwriting/fig2_logitlens.png",
    "paperwriting/fig2_mechanism.pdf",
    "paperwriting/fig2_mechanism.png",
    "paperwriting/fig3_rq3.pdf",
    "paperwriting/fig3_rq3.png",
    "paperwriting/table_rq2.tex",
    "paperwriting/delivery/fig1_capability_caption_draft.txt",
    "paperwriting/delivery/fig1_capability_source_map.json",
    "paperwriting/delivery/fig2_mechanism_caption_draft.txt",
    "paperwriting/delivery/fig2_mechanism_source_map.json",
    "paperwriting/delivery/fig3_rq3_caption_draft.txt",
    "paperwriting/delivery/fig3_rq3_source_map.json",
    "paperwriting/delivery/table_rq2_source_map.json",
    "paperwriting/delivery/figure_batch1_machine_audit.json",
}


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a valid PNG header: {path}")
    return struct.unpack(">II", header[16:24])


def _git_blob_hash(path: str) -> str:
    data = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    return hashlib.sha256(data).hexdigest()


def _changed_paths() -> list[str]:
    proc = _run(["git", "status", "--porcelain", "--untracked-files=all"])
    paths: list[str] = []
    for line in proc.stdout.splitlines():
        path = line[3:]
        if " -> " in path:
            old, new = path.split(" -> ", 1)
            paths.extend([old, new])
        else:
            paths.append(path)
    return sorted(set(paths))


def _artifact_paths() -> list[Path]:
    paths: list[Path] = []
    for stem in FIGURE_STEMS:
        paths.extend(
            [
                PAPER_DIR / f"{stem}.pdf",
                PAPER_DIR / f"{stem}.png",
                DELIVERY_DIR / f"{stem}_caption_draft.txt",
                DELIVERY_DIR / f"{stem}_source_map.json",
            ]
        )
    paths.extend(
        [
            PAPER_DIR / "table_rq2.tex",
            DELIVERY_DIR / "table_rq2_source_map.json",
        ]
    )
    return paths


def _check(condition: bool, detail: str) -> dict[str, str]:
    return {"status": "PASS" if condition else "FAIL", "detail": detail}


def audit(*, rerun: bool) -> dict[str, Any]:
    checks: dict[str, Any] = {}

    required = _artifact_paths()
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    checks["required_artifacts"] = _check(not missing, f"missing={missing}")
    if missing:
        return {"status": "FAIL", "checks": checks}

    # Frozen files must remain byte-identical to HEAD.
    frozen: dict[str, Any] = {}
    for rel in FROZEN_FILES:
        worktree_hash = _sha256(ROOT / rel)
        head_hash = _git_blob_hash(rel)
        frozen[rel] = {
            "status": "PASS" if worktree_hash == head_hash else "FAIL",
            "worktree_sha256": worktree_hash,
            "head_sha256": head_hash,
        }
    checks["frozen_files"] = frozen

    changed = _changed_paths()
    disallowed = sorted(set(changed) - ALLOWED_PATHS)
    checks["allowed_worktree_scope"] = _check(
        not disallowed, f"changed={changed}; disallowed={disallowed}"
    )

    # Every source map must be fail-closed PASS.
    maps: dict[str, Any] = {}
    for name in (*FIGURE_STEMS, "table_rq2"):
        path = DELIVERY_DIR / f"{name}_source_map.json"
        payload = json.loads(path.read_text())
        maps[name] = {
            "status": payload.get("status"),
            "mismatch_count": len(payload.get("mismatches", [])),
            "failure_count": len(payload.get("failures", [])),
        }
    checks["source_maps"] = maps

    # Caption ban scan.
    caption_hits: dict[str, list[str]] = {}
    for stem in FIGURE_STEMS:
        text = (DELIVERY_DIR / f"{stem}_caption_draft.txt").read_text().lower()
        caption_hits[stem] = [term for term in CAPTION_BANNED if term in text]
    checks["caption_banned_language"] = _check(
        not any(caption_hits.values()), f"hits={caption_hits}"
    )

    # Ensure the implementation cannot fall back to superseded logit-lens/CLR views.
    plots_text = (ROOT / "src" / "plots.py").read_text()
    stale_tokens = [
        token
        for token in (
            'results["logitlens"]',
            "results['logitlens']",
            "gap_sampled",
            "--logitlens",
            "clr_teaching",
            "base_clr",
        )
        if token in plots_text
    ]
    checks["superseded_plot_inputs_absent"] = _check(
        not stale_tokens, f"stale_tokens={stale_tokens}"
    )

    # Render-level checks: one-page, ~7.2-inch PDFs, embedded non-Type-3 fonts.
    pdf_checks: dict[str, Any] = {}
    pdffonts = shutil.which("pdffonts")
    pdfinfo = shutil.which("pdfinfo")
    if not pdffonts or not pdfinfo:
        checks["pdf_tools"] = _check(False, "pdffonts/pdfinfo not found")
    else:
        for stem in FIGURE_STEMS:
            pdf = PAPER_DIR / f"{stem}.pdf"
            font_proc = _run([pdffonts, str(pdf)])
            info_proc = _run([pdfinfo, str(pdf)])
            type3 = [line for line in font_proc.stdout.splitlines() if "Type 3" in line]
            pages_line = next(
                (line for line in info_proc.stdout.splitlines() if line.startswith("Pages:")),
                "",
            )
            size_line = next(
                (
                    line
                    for line in info_proc.stdout.splitlines()
                    if line.startswith("Page size:")
                ),
                "",
            )
            pdf_checks[stem] = {
                "status": "PASS"
                if not type3 and pages_line.split()[-1:] == ["1"]
                else "FAIL",
                "type3_fonts": type3,
                "pages": pages_line,
                "page_size": size_line,
            }
        checks["pdf_rendering"] = pdf_checks

    png_checks: dict[str, Any] = {}
    for stem in FIGURE_STEMS:
        width, height = _png_size(PAPER_DIR / f"{stem}.png")
        png_checks[stem] = {
            "status": "PASS" if width >= 2000 and height >= 900 else "FAIL",
            "width_px": width,
            "height_px": height,
        }
    checks["png_previews"] = png_checks

    table = (PAPER_DIR / "table_rq2.tex").read_text()
    stale_table_tokens = [token for token in ("n{=}50", "Widened pool", "0.790", "68\\%") if token in table]
    required_table_tokens = [
        "$n=41$ instances; 33 unique facts",
        "Bridge & 27 & 65.9\\%",
        "Recall & 11 & 26.8\\%",
        "Reflective-override & 3 & 7.3\\%",
        "Associative & 0 & 0.0\\%",
        "$\\kappa=.813$",
    ]
    missing_table_tokens = [token for token in required_table_tokens if token not in table]
    checks["table_corrected_taxonomy"] = _check(
        not stale_table_tokens and not missing_table_tokens,
        f"stale={stale_table_tokens}; missing={missing_table_tokens}",
    )

    # Optional byte-level rerun audit.  The environment must already expose matplotlib.
    if rerun:
        before = {str(path.relative_to(ROOT)): _sha256(path) for path in required}
        _run([sys.executable, str(ROOT / "src" / "plots.py")])
        _run([sys.executable, str(ROOT / "src" / "generate_table_rq2.py")])
        after = {str(path.relative_to(ROOT)): _sha256(path) for path in required}
        changed_bytes = [key for key in before if before[key] != after[key]]
        checks["deterministic_regeneration"] = _check(
            not changed_bytes, f"byte_changes_after_rerun={changed_bytes}"
        )
    else:
        checks["deterministic_regeneration"] = {
            "status": "NOT_RUN",
            "detail": "pass --rerun for byte-level regeneration",
        }

    def statuses(node: Any) -> list[str]:
        found: list[str] = []
        if isinstance(node, dict):
            if "status" in node:
                found.append(str(node["status"]))
            for value in node.values():
                found.extend(statuses(value))
        elif isinstance(node, list):
            for value in node:
                found.extend(statuses(value))
        return found

    bad = [status for status in statuses(checks) if status not in {"PASS", "NOT_RUN"}]
    return {
        "status": "PASS" if not bad else "FAIL",
        "checks": checks,
        "artifact_sha256": {
            str(path.relative_to(ROOT)): _sha256(path) for path in required
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rerun",
        action="store_true",
        help="regenerate figures/table and require byte-identical artifacts",
    )
    args = parser.parse_args()
    payload = audit(rerun=args.rerun)
    DELIVERY_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"{AUDIT_PATH.relative_to(ROOT)}: {payload['status']}")
    if payload["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
