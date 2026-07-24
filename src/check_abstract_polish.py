#!/usr/bin/env python3
"""Fail-closed audit for the v5-to-v6 abstract polish candidate.

This checker does not approve or install v6. It verifies that the candidate is
exactly the three authorized local transformations and that their factual
preconditions still hold in paperwriting/results.json.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
TITLE_ABSTRACT = ROOT / "paperwriting" / "title_abstract.md"
RESULTS = ROOT / "paperwriting" / "results.json"
TAXONOMY = ROOT / "results" / "p0_corrected_taxonomy.json"
CANDIDATE = ROOT / "paperwriting" / "delivery" / "abstract_v6_candidate.txt"

EXPECTED_TITLE = (
    "Direct-Answer Edit Success Is Not Enough: A Reasoning-Time Stress Test "
    "for Parametric Knowledge Editing"
)
EXPECTED_TLDR = (
    "An edit can pass direct-answer validation yet be overturned when the model "
    "reasons—while its edited association remains detectable at a cloze probe. "
    "Our stress test quantifies these reversions; think-span-only suppression lowers them."
)
EXPECTED_TAXONOMY_SHA256 = (
    "c11c6a0e5a3ecddff6e18aca4f19cfd91c57d4ff88a83012c211b2aef8543290"
)

AUTHORIZED_REPLACEMENTS = (
    (
        "(23/23 examined).",
        "(23/23 examined; an installation sanity check).",
    ),
    (
        "Separately, neutral three-judge majority labels identify",
        "Separately, a second neutral three-judge panel's majority labels identify",
    ),
    (
        "competitor with near-null answer-level effects;",
        "competitor, both near-null at the answer level;",
    ),
)

BANNED = (
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
    "halves",
    "halves reversion",
    "first to discover",
    "preregistered",
    "edit intact",
    "not erased",
    "guaranteed upper bound",
    "removes",
    "concentrates",
    "stable across",
    ".214",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_v5(markdown: str) -> str:
    marker = "## Abstract v5"
    tail = markdown.split(marker, 1)[1]
    lines: list[str] = []
    started = False
    for line in tail.splitlines():
        if line.startswith("> "):
            started = True
            lines.append(line[2:])
        elif started:
            break
    if not lines:
        raise AssertionError("Could not extract frozen v5 block")
    return " ".join(lines)


def json_at(obj: object, *path: str) -> object:
    cur = obj
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            raise AssertionError(f"Missing JSON path: {'.'.join(path)}")
        cur = cur[key]
    return cur


def ci_contains_zero(record: object) -> bool:
    if not isinstance(record, list) or len(record) < 2:
        return False
    ci = record[1]
    return isinstance(ci, list) and len(ci) == 2 and ci[0] <= 0 <= ci[1]


def sentence_split(text: str) -> list[str]:
    return re.split(r"(?<=[.!?]) (?=[A-Z])", text)


def numeric_tokens(text: str) -> list[str]:
    return re.findall(
        r"(?<![A-Za-z0-9_.])(?:−|-)?\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?(?:%|B)?",
        text,
    )


def main() -> int:
    title_md = TITLE_ABSTRACT.read_text(encoding="utf-8")
    baseline = extract_v5(title_md)
    candidate_bytes = CANDIDATE.read_bytes()
    candidate = candidate_bytes.decode("utf-8").strip()
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    taxonomy_bytes = TAXONOMY.read_bytes()
    taxonomy = json.loads(taxonomy_bytes)

    failures: list[str] = []

    expected = baseline
    for old, new in AUTHORIZED_REPLACEMENTS:
        if expected.count(old) != 1:
            failures.append(f"authorized source fragment count != 1: {old}")
        expected = expected.replace(old, new)
    if candidate != expected:
        failures.append("candidate differs from the three authorized transformations")

    if EXPECTED_TITLE not in title_md:
        failures.append("frozen title changed or missing")
    if EXPECTED_TLDR not in title_md:
        failures.append("frozen TL;DR changed or missing")

    base_numbers = numeric_tokens(baseline)
    candidate_numbers = numeric_tokens(candidate)
    if base_numbers != candidate_numbers:
        failures.append("numeric token sequence changed")

    banned_hits = [phrase for phrase in BANNED if phrase in candidate.lower()]
    if banned_hits:
        failures.append(f"banned phrase hits: {banned_hits}")

    source_sha = sha256_bytes(taxonomy_bytes)
    case_ids = [item["case_id"] for item in taxonomy["items"]]
    tax_block = json_at(results, "rq2_taxonomy", "p0_corrected_taxonomy")
    if source_sha != EXPECTED_TAXONOMY_SHA256:
        failures.append("taxonomy source SHA256 drift")
    if len(taxonomy["items"]) != 41 or len(set(case_ids)) != 33:
        failures.append("taxonomy 41-row/33-fact derivation failed")
    if tax_block.get("n") != 41 or tax_block.get("n_unique_facts") != 33:
        failures.append("results.json taxonomy n/n_unique_facts mismatch")

    kappa = json_at(
        results, "metric_validation", "vs_RRs_strict_decontam", "cohen_kappa"
    )
    if kappa != 0.836:
        failures.append("strict validation kappa drift")

    cloze_n = json_at(results, "rq2_logitlens", "_authoritative_record", "n")
    if cloze_n != 23:
        failures.append("cloze sanity-check n drift")

    p_minus_n = json_at(
        results, "rq3", "sup_battery", "contrasts_B3_mean_ci_p", "P_minus_N"
    )
    c_minus_n = json_at(
        results, "rq3", "sup_battery", "cross_arm_paired_ci", "C_minus_N"
    )
    near_null_checks: dict[str, bool] = {}
    for arm, block in (("P_minus_N", p_minus_n), ("C_minus_N", c_minus_n)):
        for endpoint in ("ES", "RR", "RRs"):
            ok = ci_contains_zero(block[endpoint])
            near_null_checks[f"{arm}.{endpoint}"] = ok
            if not ok:
                failures.append(f"near-null answer-level precondition failed: {arm}.{endpoint}")

    baseline_sentences = sentence_split(baseline)
    candidate_sentences = sentence_split(candidate)
    if len(baseline_sentences) != 9 or len(candidate_sentences) != 9:
        failures.append("sentence count changed; optional S7 split must remain rejected")
    changed_sentences = [
        index + 1
        for index, (before, after) in enumerate(zip(baseline_sentences, candidate_sentences))
        if before != after
    ]
    if changed_sentences != [5, 6, 7]:
        failures.append(f"unexpected changed sentence set: {changed_sentences}")

    report = {
        "status": "PASS" if not failures else "FAIL",
        "baseline": {
            "source": "paperwriting/title_abstract.md::Abstract v5",
            "normalized_text_sha256": sha256_bytes(baseline.encode("utf-8")),
            "word_count_whitespace": len(baseline.split()),
            "sentence_count": len(baseline_sentences),
        },
        "candidate": {
            "path": str(CANDIDATE.relative_to(ROOT)),
            "file_sha256": sha256_bytes(candidate_bytes),
            "normalized_text_sha256": sha256_bytes(candidate.encode("utf-8")),
            "word_count_whitespace": len(candidate.split()),
            "sentence_count": len(candidate_sentences),
        },
        "authorized_transformations_only": candidate == expected,
        "changed_sentences": changed_sentences,
        "unchanged_sentences_byte_equal": [1, 2, 3, 4, 8, 9],
        "numeric_token_sequence_equal": base_numbers == candidate_numbers,
        "numeric_token_counts": dict(Counter(candidate_numbers)),
        "banned_phrase_hits": banned_hits,
        "m03": {
            "source_sha256": source_sha,
            "source_rows": len(taxonomy["items"]),
            "source_unique_item_ids": len({item["item_id"] for item in taxonomy["items"]}),
            "derived_unique_case_ids": len(set(case_ids)),
            "results_json_n_unique_facts": tax_block.get("n_unique_facts"),
        },
        "wording_preconditions": {
            "strict_validation_kappa": kappa,
            "cloze_sanity_n": cloze_n,
            "near_null_answer_level_ci_contains_zero": near_null_checks,
        },
        "failures": failures,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
