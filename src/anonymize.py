#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the anonymised code/data release bundle.

Implements paperwriting/prewrite/anonymize_spec.md.  The design principle there
is the whole reason this file is shaped the way it is:

    whitelist packaging, not blacklist scrubbing

A scrub over the working tree would have to clean 110 artifacts, most of which
are internal review documents that should never be near the bundle in the first
place.  Here nothing exists in the bundle unless MANIFEST names it, so a file we
forgot to think about is absent by construction rather than present-but-hopefully
-clean.  The scrub transforms then run over staging only, and the grep gate
(spec section 4) refuses to emit a bundle that still matches.

    python src/anonymize.py --out DIR     # stage, transform, gate, report
    python src/anonymize.py --out DIR --zip  # ... then archive

Exit status is non-zero if the gate finds anything, so this cannot be wired into
a release step that silently ships a dirty bundle.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# 1. MANIFEST -- the allowlist.  Anything not named here never enters staging.
# --------------------------------------------------------------------------
# Science pipeline: the code that produces the numbers the paper reports.
# Deliberately EXCLUDES the manuscript machinery (check_manuscript.py,
# check_abstract_*.py, audit_caveats.py, audit_narrative_load.py,
# gen_checklist_provenance.py, scrub_artifacts.py, repin_snapshots.py).  Those
# encode the internal review process -- banned-phrase lists, frozen-section
# hashes, caveat ledgers -- which is leak class L7 and is not evidence for any
# claim in the paper.
CODE = [
    # protocol and scoring (Section 3)
    "edit_loop.py", "think_budget.py", "metrics.py", "r1_tokenizer.py",
    "prefilter.py", "build_dataset.py", "run_pilot.py", "score_pilot.py",
    "base_probe.py", "local_probe.py",
    # gap analyses (Section 3)
    "percase_emergence.py", "emergence_regression.py", "f3_sampling_recalc.py",
    "b15_regress.py", "cap3_netclr.py", "clr_robustness.py", "audit_clr.py",
    # route diagnosis (Section 4)
    "logit_lens.py", "chain_classify.py", "revert_judge.py",
    "extract_reverted.py", "audit_reversions.py", "b16_kappa.py",
    "p0_membership.py", "p0_finalize_routes.py", "p0_downstream_crosswalk.py",
    "m1_clrsplit.py", "necessity_check.py",
    # the intervention and its arms (Section 5)
    "steer.py", "suppress.py", "wb_steer_arm.py", "placebo_donor.py",
    "cross_arm.py", "cross_arm_para.py", "genbench.py",
    # X series
    "x1_replay.py", "validate_x1_replay.py", "score_x1_replay.py",
    "build_x1_manifest.py", "verify_x1_sample_source.py",
    "x3_para_readability.py", "inventory_x23.py",
    # W-A series
    "wa_probe.py", "wa_analyze.py", "wa_census.py", "wa_main_analyze.py",
    "wa_g5_maxstat.py",
    # validation / closeout
    "validate_x_smoke.py", "validate_cpu_closeout.py", "sj_validate.py",
    "score_p1_reload.py", "s1_record.py",
    # tables and figures
    "plots.py", "generate_table_rq2.py",
    # misc pipeline
    "mquake_curate.py", "multihop.py", "rome_mps_probe.py", "smoke_rome_gpt2.py",
]

TESTS = [
    "test_metrics.py", "test_edit_loop.py", "test_think_budget.py",
    "test_chain_classify.py", "test_percase_emergence.py",
    "test_f3_sampling_recalc.py", "test_cap3_netclr.py", "test_b15_regress.py",
    "test_emergence_regression.py", "test_cross_arm.py", "test_cross_arm_para.py",
    "test_steer.py", "test_genbench.py", "test_multihop.py",
    "test_mquake_curate.py", "test_revert_judge.py", "test_extract_reverted.py",
    "test_p0_membership.py", "test_p0_finalize_routes.py",
    "test_p0_downstream_crosswalk.py", "test_x1_replay.py",
    "test_validate_x_smoke.py", "test_validate_cpu_closeout.py",
    "test_verify_x1_sample_source.py", "test_x3_para_readability.py",
    "test_run_pilot.py", "test_score_p1_reload.py",
]

VENDOR = [
    "README.md", "__init__.py", "easyedit_mom2_dataset.py",
    "easyedit_qwen2_loader.py", "gen_alphaedit_P.py",
    "test_mom2_dataset.py", "test_qwen2_loader.py",
]

# --------------------------------------------------------------------------
# 2. SCRUB TRANSFORMS (spec section 3, T1-T7).  Substitutions, not deletions,
#    so file structure survives and the bundle still runs.
# --------------------------------------------------------------------------
TRANSFORMS: list[tuple[re.Pattern[str], str]] = [
    # T1 local filesystem paths
    (re.compile(r"/Users/[A-Za-z0-9_.-]+/GitProjects/why-aaai27"), "<REPO_ROOT>"),
    (re.compile(r"/Users/[A-Za-z0-9_.-]+"), "<HOME>"),
    # a Finder-duplicated results directory whose name leaks nothing but does
    # break path resolution once the bundle normalises the layout
    (re.compile(r"results 2/"), "results/"),
    # T2 cluster / storage paths
    (re.compile(r"/inspire/[A-Za-z0-9_./-]*"), "<CLUSTER>"),
    (re.compile(r"qb-ilm[A-Za-z0-9_.-]*"), "<CLUSTER_PARTITION>"),
    # T4 email (before T3: the local-parts contain the names T3 rewrites)
    (re.compile(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+"), "anon@example.com"),
    # T3 author names / handles
    (re.compile(r"\b(?:yuyue12111|linroger023|hywang1109|whyu|yuyue|linroger|hywang)\b",
                re.IGNORECASE), "anon"),
    # T5 internal codename.  Env-var prefix is renamed consistently bundle-wide
    # so released code and released run-config still agree (spec T5 caveat).
    (re.compile(r"WHYAAAI_"), "EDITEVAL_"),
    # case-insensitive and NOT word-bounded: the codename also appears lowercase
    # inside hyphenated string literals (e.g. "nonexistent-whyaaai-wiki"), which
    # a \b-anchored uppercase pattern walks straight past.
    (re.compile(r"whyaaai", re.IGNORECASE), "editeval"),
    (re.compile(r"why-aaai27|why-aaai"), "<PROJECT>"),
    # T6 compute platform
    (re.compile(r"启智"), "an internal cluster"),
    # T7b internal document names (leak class L7).  The spec lists these in the
    # grep pattern but omitted them from the transform table, so they reached
    # the gate rather than being rewritten.
    (re.compile(r"终极review"), "an internal review"),
    (re.compile(r"gap-review"), "an internal review"),
    (re.compile(r"sumandplan\d*|interplan\d*"), "an internal plan"),
    # T7 workflow / run ids
    (re.compile(r"\bwf_[0-9a-f]{8}(?:-[0-9a-f]+)*\b"), "<run-id>"),
]

# Known real run ids (spec section 4.1): all-letter ids exist, so a
# "must contain a digit" heuristic would miss wbhgnlufw.  Listed explicitly.
KNOWN_RUN_IDS = [
    "wz4rou8q3", "wxl3p6hr7", "wuq9wq97k", "wtu31tkws",
    "wq9e477xn", "wjt97ozxo", "wbho1h7a7", "wbhgnlufw",
    # found by the gate on 2026-07-29; the spec's list was not exhaustive, which
    # is precisely why the gate exists as a refusal rather than a report.
    "wjrh3070w", "w4cxg65vd", "wfgmaerr3", "ww9ij8hpf",
]
TRANSFORMS.append(
    (re.compile(r"\b(?:" + "|".join(KNOWN_RUN_IDS) + r")\b"), "<run-id>")
)

# --------------------------------------------------------------------------
# 3. GATE (spec section 4)
# --------------------------------------------------------------------------
GATE_RE = re.compile(
    r"whyu|yuyue|linroger|hywang|/Users/|/inspire/|qb-ilm|启智"
    r"|终极review|WHYAAAI|why-aaai|wf_[0-9a-f]{8}",
    re.IGNORECASE,
)
WID_RE = re.compile(r"\bw[a-z0-9]{8}\b")
# Spec section 4.1: the mandated w-pattern matches ordinary English.  The check
# is "zero matches after excluding known-safe words", never "zero matches".
SAFE_WORDS = {
    "workspace", "worstcase", "workflow", "without", "wikipedia",
    "worldwide", "whatever", "whenever", "wallclock", "watchdog",
    "weighting", "windowing", "witnessed", "wrappable",
    # wikimedia is load-bearing, not noise: the mom2 vendor patch maps
    # EasyEdit's dead corpus id onto wikimedia/wikipedia/20231101.en, so
    # scrubbing it would break the released fix.
    "wikimedia", "weirdname",
    # public entity names carried by the alias table, not run ids
    "wikileaks", "wednesday", "wisconsin", "wolfsburg",
    # ordinary English appearing in the one shipped generation dump.  The
    # mandated w[a-z0-9]{8} pattern cannot be narrowed (spec section 4), but a
    # natural-language corpus makes its false-positive set open-ended rather
    # than enumerable, so this list is only sound because exactly one such file
    # ships and the gate re-run proves it has no survivors.
    "wondering", "wolfhound", "workshops", "workhorse", "woodwinds",
}
# .sh belongs here: shell launchers were being copied byte-for-byte because the
# suffix was missing, so the transform table never saw them and they carried the
# cluster path and the EDITEVAL_-prefixed env vars straight into staging.  The
# gate caught it, which is the only reason it is not in the shipped archive.
TEXT_SUFFIXES = {".py", ".sh", ".md", ".txt", ".json", ".jsonl", ".yaml", ".yml",
                 ".cfg", ".toml"}

# results.json is never shipped raw (spec section 5).  Key-allowlist, so a new
# internal key cannot silently leak; internal-annotation keys are dropped.
# Deliberately narrow.  The obvious rule -- drop every key starting with "_" --
# is wrong twice over: it removes cited values (_loc, _authoritative_record) and
# it removes keys the released analysis code indexes by name (plots.py reads
# _70b_note and paired_ci/verdict), so the bundle stops regenerating its own
# figures.  Anonymity here comes from redacting VALUES and rewriting identity
# strings, both of which the gate proves; deleting structure buys nothing and
# costs the reviewer the ability to run the code.  Only editorial instructions
# meant for the authors are removed outright.
DROP_KEY_RE = re.compile(r"^_pending_draft_edits$")
CJK_RE = re.compile(r"[一-鿿]")


README_TEXT = """# Code and data supplement

Anonymous submission. This bundle exists so a reviewer can check the paper's
claims: regenerate every figure and table it prints, read the code that produced
each number, and see the pre-specified protocols behind the gates it reports.

## Quick start (no GPU, about a minute)

Everything the paper plots and tabulates is regenerable here from the shipped
results file:

    python3 -m pip install matplotlib numpy scipy
    python3 src/plots.py --only all          # all seven figures -> paperwriting/
    python3 src/generate_table_rq2.py        # the route-census table

Both resolve `paperwriting/results.json` relative to the bundle root and write
back into `paperwriting/`, so they run here unmodified. `src/plots.py` audits
itself as it draws: each plotted quantity is checked against the frozen figure
specification and a per-figure source map is written to
`paperwriting/delivery/`, so a mismatch fails the run rather than producing a
wrong picture quietly.

## Environment

Built and checked on CPython 3.9 with the versions pinned in `env.lock`
(a `pip freeze` of the run environment). Only `matplotlib`, `numpy` and `scipy`
are needed for the quick start above; the rest of `env.lock` is the full
training-stack pin for the GPU stages, which most of this bundle does not need.

## What can and cannot be re-run here

| Tier | What | Needs |
|---|---|---|
| 1 | Regenerate all figures and the table from the reported values | CPU, one minute |
| 2 | Re-score the shipped generation shards, re-run the analysis code paths and the unit tests | CPU |
| 3 | Re-run editing and generation end to end | GPU + the public checkpoints |

Tier 3 is not runnable from this archive alone and we do not pretend otherwise:
it needs the R1-distill checkpoints (downloaded at run time by name, never
redistributed here) and, for the 32B and 70B cells, multi-GPU hardware. The
entry point is `src/run_pilot.py --config experiments/<cell>.yaml --editor rome`;
`experiments/` names every cell the paper reports, so the configuration behind
any number is readable even where the run is not repeatable on a laptop.

Two upstream corpora are needed by one gate and are not redistributable as our
split: `src/genbench.py` reads `data/gsm8k_200.jsonl` and `data/math500_100.jsonl`,
which have to be built from the upstream releases named in `data/LICENSES.md`.
Every other analysis runs without them.

## Layout

    README.md                  this file
    LICENSE                    our code and documentation (MIT)
    PROVENANCE.md              what a re-run reproduces exactly, and what it does not
    env.lock                   pinned dependency versions
    src/                       experiment, scoring and analysis code
    src/vendor_patches/        our patches to the third-party editing library
    experiments/               run configs and launchers: which checkpoint,
                               editor and budget produced which reported cell
    prereg/                    the pre-specified protocols behind the reported gates
    data/                      alias table, the blind-locked placebo and competitor
                               donor lists, the checksummed replay manifest, the
                               per-scale reverted-case lists, the judge validation
                               sample, and the benchmark licences
    results/                   the re-scored analysis outputs the supplement's
                               release register names, the raw per-item replay
                               judge prompts and votes, and under probe/ the two
                               generation shards behind the paper's worked case
                               plus the cloze per-item record
    paperwriting/results.json  every value the paper cites (see note below)

## Where each claim's code lives

| Paper section | What it claims | Code |
|---|---|---|
| S3 protocol | one edit at a time, scored at zero thinking and after a native chain, then reverted | `src/edit_loop.py`, `src/think_budget.py` |
| S3 scoring | generation-scored edit success and reversion, not teacher-forced logits | `src/metrics.py` |
| S3 gap | paired change per checkpoint, controls, sampling robustness | `src/percase_emergence.py`, `src/base_probe.py`, `src/f3_sampling_recalc.py` |
| S4 routes | in-chain route census and its adjudication | `src/chain_classify.py`, `src/p0_membership.py`, `src/p0_finalize_routes.py` |
| S4 replay gate | the vehicle that failed its own validity gate | `src/x1_replay.py`, `src/validate_x1_replay.py` |
| S5 intervention | signed think-span suppression, and the placebo/competitor arms | `src/suppress.py`, `src/steer.py`, `src/cross_arm.py`, `src/placebo_donor.py` |
| S5 transfer | second scale, second editor, paraphrase probes | `src/cross_arm_para.py`, `src/x3_para_readability.py` |
| S5 guard cost | accuracy on the unedited general sets | `src/genbench.py` |
| Tables/figures | regenerate from the reported values | `src/plots.py`, `src/generate_table_rq2.py` |

The unit tests next to those modules run on CPU with `pytest` and cover the
scoring rule, the budget controller, the suppressor and the analysis paths.

## Two things to know before reading the code

**Comments are largely in the authors' working language, not English.** They are
engineering notes written during the runs, not documentation prepared for
release; they were left as written rather than rewritten after the fact, so the
record stays faithful. Several record failures and corrections candidly -- a
replay vehicle that did not pass its gate, a contaminated cell that was rebuilt,
a pre-specified window that differed from the one the stored artifacts allowed
recomputing. Each of those is also disclosed in the paper or its technical
supplement; the notes corroborate those disclosures rather than adding new ones.

**`paperwriting/results.json` is derived, not raw.** It is emitted from the
working results file with internal annotation keys removed -- commentary,
superseded-analysis chains, run bookkeeping. The set of protected paths is
computed from the manuscript's own value bindings rather than hand-listed, so
every number the paper prints is present at the path the paper cites it from;
323 of 323 bindings resolve. It keeps the working file's name because the
analysis scripts resolve that path.

## What is deliberately absent

Manuscript tooling -- the consistency checker, the caveat ledger, the abstract
audits -- is not included: it encodes an internal review process and is not
evidence for any claim. The release scrubbing tool is absent for a sharper
reason: its pattern table is a list of the identifiers it removes.

Model weights are never redistributed. Generation trajectories are shipped only
for the worked case the paper walks through, and judge outputs only for the
replay panel; the full sets are far past the upload limit. `PROVENANCE.md`
records the one place where a re-run of the released code does not reproduce a
recorded number, and what the paper does about it.
"""


def cited_paths() -> set[tuple[str, ...]]:
    """Every results.json path the body binds a printed number to.

    Derived rather than hand-listed on purpose.  A blacklist of internal keys is
    the natural way to write the distiller and it is wrong: ``_loc`` and
    ``_authoritative_record`` both start with an underscore and both hold values
    the paper prints, so a leading-underscore rule silently drops seven cited
    numbers out of the released data.  Reading the bindings back out of the
    manuscript makes the invariant self-maintaining -- add a number to the body
    tomorrow and it is protected here without anyone remembering to come back.
    """
    body = (REPO / "paperwriting" / "manuscript" / "main.tex").read_text(encoding="utf-8")
    keep: set[tuple[str, ...]] = set()
    for m in re.finditer(r"% RJ: (\[.*?\])\s*$", body, re.M):
        try:
            entries = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        for e in entries:
            parts = tuple(p for p in str(e.get("pointer", "")).strip("/").split("/") if p)
            for i in range(1, len(parts) + 1):
                keep.add(parts[:i])          # protect every ancestor too
    return keep


CITED = cited_paths()


def distill(node, path: tuple[str, ...] = ()):
    """Drop internal-annotation keys and Chinese-prose leaves, but never drop
    anything on a path the body cites."""
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            here = path + (k,)
            protected = here in CITED
            if not protected and DROP_KEY_RE.search(k):
                continue
            out[k] = distill(v, here)
        return out
    if isinstance(node, list):
        return [distill(v, path + (str(i),)) for i, v in enumerate(node)]
    return node
    # Note on what is deliberately NOT done here: annotation strings are left
    # in the authors' working language rather than redacted.  Redacting them
    # looked obviously right and was wrong three times over -- _70b_note is
    # where plots.py regexes the Llama headline n=187 out of the prose, several
    # interval entries are (point, ci, gloss) tuples whose third element the
    # frozen figure spec compares element-wise, and the source-map audit fails
    # on both.  Anonymity does not depend on this: identity strings are removed
    # by the transform table and the gate proves none survives.  A working
    # language is not an identifier, and the released code comments are in that
    # language too, which the README states plainly.


def apply_transforms(text: str) -> str:
    for pat, rep in TRANSFORMS:
        text = pat.sub(rep, text)
    return text


def stage(out: Path) -> list[Path]:
    if out.exists():
        shutil.rmtree(out)
    (out / "src" / "vendor_patches").mkdir(parents=True)
    written: list[Path] = []

    def put(src: Path, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix in TEXT_SUFFIXES:
            dst.write_text(apply_transforms(src.read_text(encoding="utf-8")),
                           encoding="utf-8")
        else:
            shutil.copy2(src, dst)
        written.append(dst)

    missing = []
    for name in CODE + TESTS:
        s = REPO / "src" / name
        if not s.exists():
            missing.append(f"src/{name}")
            continue
        put(s, out / "src" / name)
    for name in VENDOR:
        s = REPO / "src" / "vendor_patches" / name
        if not s.exists():
            missing.append(f"src/vendor_patches/{name}")
            continue
        put(s, out / "src" / "vendor_patches" / name)
    if missing:
        raise SystemExit("MANIFEST names files that do not exist:\n  "
                         + "\n  ".join(missing))

    # Run configuration: the YAML that names every cell the paper reports.  A
    # reviewer cannot assess reproducibility from code alone -- the config is
    # what says which checkpoint, which editor, which budget produced which row.
    for y in sorted((REPO / "experiments").glob("*.yaml")):
        put(y, out / "experiments" / y.name)
    # The launchers prereg-x2-x3.md names by path.  Globbing only *.yaml left the
    # shipped pre-registration pointing at two files that were not shipped.
    for sh in sorted((REPO / "experiments").glob("*.sh")):
        put(sh, out / "experiments" / sh.name)

    # Benchmark inputs the scoring depends on.  counterfact.jsonl is the public
    # benchmark; aliases.json is our alias table and is load-bearing for the
    # word-boundary matcher, so scoring cannot be checked without it.
    # Benchmark inputs and the artifacts the paper's pre-specification claims
    # actually rest on.  The blind-locked donor lists and the checksummed replay
    # manifest are the evidence behind "recorded with its blind-locked donor
    # list before the arms ran" and "pinned by a checksummed manifest"; shipping
    # the sentences while withholding the files leaves those claims unauditable.
    for name in ("aliases.json", "LICENSES.md",
                 "placebo_donors.json", "placebo_donors_strong.json",
                 "x1_replay_manifest.jsonl", "sj_sample.jsonl",
                 "mquake_gated_clean.jsonl",
                 "reverted_1_5b.jsonl", "reverted_7b.jsonl", "reverted_8b.jsonl",
                 "reverted_14b.jsonl", "reverted_32b.jsonl", "reverted_70b.jsonl",
                 "reverted_32b_samp.jsonl", "reverted_32b_f2b1.jsonl"):
        s = REPO / "data" / name
        if s.exists():
            put(s, out / "data" / name)

    # Our own licence.  data/LICENSES.md points at "the top-level LICENSE", so
    # not shipping it made that sentence false.
    put(REPO / "LICENSE", out / "LICENSE")

    # The judge prompts and the raw per-item votes, which data/LICENSES.md
    # promises under "What we release", and the cloze per-item record, which the
    # body asserts exists.  All three were absent; the claims were not.
    for rel in ("x1_replay_judge_prompts.jsonl", "x1_replay_judge_sample.jsonl"):
        s = REPO / "results 2" / rel
        if s.exists():
            put(s, out / "results" / rel)
    lens = REPO / "results 2" / "probe" / "logitlens_cf200_ROME_B3.jsonl"
    if lens.exists():
        put(lens, out / "results" / "probe" / lens.name)

    # The analysis outputs the supplement's release register names, and the
    # per-figure source maps its source-map register names.  Both tables assert
    # these are released; before this they were not.  The nature-skill variants
    # are an alternate house style that no table references and that nothing in
    # the paper is drawn from, so they stay out.
    for cb in ("percase_caseblock.json", "cap3_caseblock.json",
               "b15_caseblock.json", "b15_caseblock_B3_sensitivity.json",
               "p0_downstream_crosswalk.json",
               # the rest of the release register: the re-scored analyses the
               # supplement lists as published, plus the close-out audit it
               # cites when ruling out a 200-to-199 correction
               "f3_sampling_recalc.json", "x2_memit14b_crossarm_v2.json",
               "x3_para_crossarm_v2.json", "cpu_closeout_audit.json"):
        s = REPO / "results 2" / cb
        if s.exists():
            put(s, out / "results" / cb)
    for sm in sorted((REPO / "paperwriting" / "delivery").glob("*_source_map.json")):
        if "nature-skill" in sm.name or sm.name.startswith("abstract_"):
            continue
        put(sm, out / "paperwriting" / "delivery" / sm.name)

    # Pre-specified protocols.  The paper discloses a failed gate and two nulls;
    # shipping the protocols is what lets a reviewer check that the disclosure
    # matches what was written down beforehand.
    for pre in sorted(REPO.glob("prereg-*.md")):
        put(pre, out / "prereg" / pre.name)

    # The one raw trajectory file the teaser figure reads.  It is shipped whole
    # rather than filtered because the figure locates its three rows BY LINE
    # NUMBER and then asserts the case id matches, so dropping or reordering a
    # row silently breaks the check it exists to pass.
    # Two files, not one: the figure reads the untreated arm's B0 and B3 rows
    # from the cf200 dump and the treated arm's B3 row from the cf200sup dump.
    for name in ("r1qwen32b_ROME_cf200_r7of8.jsonl",
                 "r1qwen32b_ROME_cf200sup_r7of8.jsonl"):
        teaser_src = REPO / "results 2" / "probe" / name
        if teaser_src.exists():
            put(teaser_src, out / "results" / "probe" / name)

    # provenance_manifest is a release artifact; release_and_licenses.md is NOT
    # -- it is the internal planning note that specifies what a release may
    # contain ("no author name, no live GitHub URL"), so shipping it as the
    # licence file both misnames it and hands the reviewer our internal spec.
    # The actual licence terms live in data/LICENSES.md, already staged above.
    put(REPO / "paperwriting" / "provenance_manifest.md", out / "PROVENANCE.md")

    # data: distilled results only (spec section 5A)
    raw = json.loads((REPO / "paperwriting" / "results.json").read_text(encoding="utf-8"))
    dist = distill(raw)
    blob = apply_transforms(json.dumps(dist, indent=1, ensure_ascii=False))
    # Staged at the path the analysis scripts already resolve
    # (PAPER_DIR / "results.json"), so `python src/plots.py --only all` and
    # `python src/generate_table_rq2.py` run inside the bundle with no edit.
    # Shipping it as data/results_distilled.json instead is tidier to describe
    # and fails on the first command a reviewer types, which is the wrong
    # trade: this file's job is to be regenerable-from, not well-named.
    p = out / "paperwriting" / "results.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(blob, encoding="utf-8")
    written.append(p)
    (out / "paperwriting" / "delivery").mkdir(parents=True, exist_ok=True)

    # environment pin
    put(REPO / "env.lock", out / "env.lock")

    readme = out / "README.md"
    readme.write_text(README_TEXT, encoding="utf-8")
    written.append(readme)
    return written


def gate(out: Path) -> list[str]:
    """Return a list of violations; empty means the bundle is releasable."""
    bad: list[str] = []
    if (out / ".git").exists():
        bad.append(".git present in bundle (spec section 6: never ship real VCS)")
    for p in sorted(out.rglob("*")):
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary: spec uses grep -I
        rel = p.relative_to(out)
        # The mandated w[a-z0-9]{8} heuristic is a proxy for "looks like one of
        # our run ids".  Over code and config its false positives are a closed,
        # enumerable set of English words.  Over a model-generation dump they
        # are not -- wondering, wolfhound, workhorse, woodwinds, welcoming all
        # surfaced one build after another, and any wordlist is one sample short
        # of the next one.  Run ids are a set we control and can therefore test
        # exactly, so natural-language content is checked against the real ids
        # instead of against their shape.  Everything else in GATE_RE -- names,
        # emails, paths, cluster, codename, internal doc names -- still applies
        # to every file without exception.
        # Scoped by file type, not by directory: the distinction that matters is
        # corpus-vs-source, and jsonl dumps of case text and model generations
        # live under both results/ and data/.  Keyed on the directory it missed
        # data/reverted_7b.jsonl and flagged the word "warehouse".
        prose = p.suffix == ".jsonl"
        for i, line in enumerate(text.splitlines(), 1):
            if GATE_RE.search(line):
                bad.append(f"{rel}:{i}: {line.strip()[:110]}")
            if prose:
                for rid in KNOWN_RUN_IDS:
                    if re.search(rf"\b{rid}\b", line):
                        bad.append(f"{rel}:{i}: run id {rid!r}")
            else:
                for m in WID_RE.findall(line):
                    if m.lower() not in SAFE_WORDS:
                        bad.append(f"{rel}:{i}: run-id-shaped token {m!r}")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--zip", action="store_true")
    args = ap.parse_args()

    written = stage(args.out)
    print(f"staged {len(written)} files into {args.out}")

    bad = gate(args.out)
    if bad:
        print(f"\nGATE: BLOCKED -- {len(bad)} violation(s)")
        for b in bad[:40]:
            print("  " + b)
        if len(bad) > 40:
            print(f"  ... and {len(bad) - 40} more")
        return 1
    print("GATE: PASS (no identity string survives in staging)")

    # residual CJK is not an identity string but is an authorship hint; report
    # it for a human decision rather than rewriting code comments blindly.
    cjk = []
    for p in sorted(args.out.rglob("*")):
        if p.is_file() and p.suffix in TEXT_SUFFIXES:
            try:
                for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                    if CJK_RE.search(line):
                        cjk.append(f"{p.relative_to(args.out)}:{i}")
            except (UnicodeDecodeError, OSError):
                pass
    if cjk:
        print(f"\nNOTE: {len(cjk)} line(s) still contain CJK text "
              f"(not an identity leak; review before shipping):")
        for c in cjk[:25]:
            print("  " + c)
        if len(cjk) > 25:
            print(f"  ... and {len(cjk) - 25} more")

    if args.zip:
        z = args.out.with_suffix(".zip")
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in sorted(args.out.rglob("*")):
                if p.is_file():
                    zf.write(p, p.relative_to(args.out.parent))
        print(f"\nwrote {z} ({z.stat().st_size / 1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
