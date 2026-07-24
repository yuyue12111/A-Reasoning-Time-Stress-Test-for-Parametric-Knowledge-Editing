#!/usr/bin/env python3
"""Fail-closed preflight for the v7.1 abstract candidate.

This validates a candidate and its source map. It does not certify G6, close
main-text disclosure debts, change the repository's frozen abstract, or verify
the external OpenReview form.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from check_abstract_v7 import (
    BANNED_PHRASES,
    EXPECTED_EFFECT_NUMBER_OCCURRENCES,
    EXPECTED_TITLE,
    EXPECTED_TLDR,
    EXPECTED_V5_NORMALIZED_SHA256,
    ROOT,
    TITLE_ABSTRACT,
    RESULTS,
    V6,
    all_numeric_tokens,
    close,
    effect_number_occurrences,
    extract_frozen_title,
    extract_frozen_tldr,
    extract_v5,
    get_path,
    sentence_split,
    sha256,
)


V7 = ROOT / "paperwriting" / "delivery" / "abstract_v7_candidate.txt"
V71 = ROOT / "paperwriting" / "delivery" / "abstract_v7_1_candidate.txt"
SOURCE_MAP = ROOT / "paperwriting" / "delivery" / "abstract_v7_1_source_map.json"

LOCKED_PHRASES = (
    "Parametric knowledge edits are validated with direct answers; deployed reasoning models may reason before answering.",
    "the same ROME edit on CounterFact at zero thinking and after a natural chain",
    "six fixed checkpoints from two DeepSeek-R1-distill families",
    "At the largest tested checkpoint in each family",
    "no detectable unedited-base drift",
    "persists across three fixed sampling seeds",
    "In examined Qwen-32B reversions",
    "the edited association remains detectable at a cloze probe",
    "separately, judges identify visible in-chain routes",
    "motivating a chain-routing hypothesis",
    "We next test for a chain-local control point",
    "signed, dose-graded suppression",
    "only during thinking, with answer logits untouched",
    "offsets the observed thinking tax",
    "marginal loose reversion",
    "complete-case paired change",
    "edit-success gains replicate at 14B and transfer to MEMIT",
    "strict transfer remains inconclusive",
    "not enough",
    "admits a chain-local causal control point",
)


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    failures: list[str] = []
    title_md = TITLE_ABSTRACT.read_text(encoding="utf-8")
    v5 = extract_v5(title_md)
    v6 = V6.read_text(encoding="utf-8").strip()
    v7 = V7.read_text(encoding="utf-8").strip()
    v71_bytes = V71.read_bytes()
    v71 = v71_bytes.decode("utf-8").strip()
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    source_map = json.loads(SOURCE_MAP.read_text(encoding="utf-8"))

    sentences = sentence_split(v71)
    sentence_word_counts = [len(sentence.split()) for sentence in sentences]
    if not 7 <= len(sentences) <= 9:
        failures.append(f"sentence count outside 7-9: {len(sentences)}")
    if len(v71.split()) > 200:
        failures.append(f"word count exceeds 200: {len(v71.split())}")
    if max(sentence_word_counts, default=0) > 30:
        failures.append(f"sentence exceeds 30 words: {sentence_word_counts}")

    missing_locked = [phrase for phrase in LOCKED_PHRASES if phrase not in v71]
    if missing_locked:
        failures.append(f"missing locked phrases: {missing_locked}")
    banned_hits = [phrase for phrase in BANNED_PHRASES if phrase in v71.lower()]
    if banned_hits:
        failures.append(f"banned phrase hits: {banned_hits}")
    if v71.startswith("Among examined reversions"):
        failures.append("rejected selected-set opening returned")

    effects = effect_number_occurrences(v71)
    if tuple(effects) != EXPECTED_EFFECT_NUMBER_OCCURRENCES:
        failures.append(f"effect-number sequence mismatch: {effects}")
    numeric_reference = (
        set(all_numeric_tokens(v5))
        | set(all_numeric_tokens(v6))
        | set(all_numeric_tokens(v7))
    )
    numeric_subset = set(all_numeric_tokens(v71)) <= numeric_reference
    if not numeric_subset:
        failures.append("candidate contains a numeric token absent from v5/v6/v7")

    qwen_drop = get_path(results, "capability", "families", "R1-Distill-Qwen", "es_drop", 3)
    llama_drop = get_path(results, "capability", "families", "R1-Distill-Llama", "es_drop", 1)
    strict_rate = get_path(results, "rq3", "sup_battery", "marginal_B3", "N", "RRs")
    loose_n = get_path(results, "rq3", "sup_battery", "marginal_B3", "N", "RR")
    loose_t = get_path(results, "rq3", "sup_battery", "marginal_B3", "T", "RR")
    paired_rr = get_path(results, "rq3", "sup_battery", "cross_arm_paired_ci", "T_minus_N", "RR", 0)
    base_drift_ci = get_path(results, "base_probe", "f1_edit_specificity", "paired_ci", "ci95")
    evidence_checks = {
        "B1.Qwen32.drop=0.106": close(float(qwen_drop), 0.106),
        "B1.Llama70.drop=0.107": close(float(llama_drop), 0.107),
        "B2.strict=9.2%": close(float(strict_rate), 0.092),
        "B2.loose=19.3%": close(float(loose_n), 0.193),
        "B3.armwise_T=8.5%": close(float(loose_t), 0.085),
        "B3.complete_case_paired=-0.102": close(float(paired_rr), -0.102),
        "control.base_drift_ci_contains_zero": float(base_drift_ci[0]) <= 0.0 <= float(base_drift_ci[1]),
    }
    for name, ok in evidence_checks.items():
        if not ok:
            failures.append(f"evidence check failed: {name}")

    # Guard the two distinct estimands against accidental arithmetic collapse.
    if "tax; marginal loose reversion drops 19.3%→8.5% (complete-case paired change −0.102)" not in v71:
        failures.append("marginal/paired separation fragment changed")

    source_map_checks = {
        "candidate_file_hash": source_map["candidate"]["file_sha256"] == sha256(v71_bytes),
        "candidate_normalized_hash": source_map["candidate"]["normalized_text_sha256"] == sha256(v71.encode("utf-8")),
        "v6_source_hash": source_map["source_versions"]["v6"]["file_sha256"] == file_sha(V6),
        "v7_source_hash": source_map["source_versions"]["v7"]["file_sha256"] == file_sha(V7),
        "sentence_count": len(source_map["sentences"]) == len(sentences),
    }
    mapped = {row["candidate_sentence_id"]: row for row in source_map["sentences"]}
    for index, sentence in enumerate(sentences, start=1):
        row = mapped.get(f"S{index}")
        ok = row is not None and row["candidate_text_sha256"] == sha256(sentence.encode("utf-8"))
        source_map_checks[f"S{index}_hash"] = ok
    for name, ok in source_map_checks.items():
        if not ok:
            failures.append(f"source-map check failed: {name}")

    frozen_checks = {
        "title": extract_frozen_title(title_md) == EXPECTED_TITLE,
        "tldr": extract_frozen_tldr(title_md) == EXPECTED_TLDR,
        "v5": sha256(v5.encode("utf-8")) == EXPECTED_V5_NORMALIZED_SHA256,
    }
    for name, ok in frozen_checks.items():
        if not ok:
            failures.append(f"frozen local field changed: {name}")

    report = {
        "status": "PASS" if not failures else "FAIL",
        "candidate": {
            "path": str(V71.relative_to(ROOT)),
            "file_sha256": sha256(v71_bytes),
            "normalized_text_sha256": sha256(v71.encode("utf-8")),
            "word_count_whitespace": len(v71.split()),
            "sentence_count": len(sentences),
            "sentence_word_counts": sentence_word_counts,
        },
        "effect_number_occurrences": effects,
        "effect_number_count": len(effects),
        "numeric_set_subset_of_v5_v6_v7": numeric_subset,
        "missing_locked_phrases": missing_locked,
        "banned_phrase_hits": banned_hits,
        "evidence_checks": evidence_checks,
        "source_map_checks": source_map_checks,
        "local_frozen_field_checks": frozen_checks,
        "external_openreview_state": "NOT_VERIFIED_EXTERNAL",
        "g5_adoption_gate": "BLOCKED_PENDING_MAIN_TEXT_DEBTS_D1_D7_AND_R1",
        "g6_status": "NOT_RUN_FOR_V7_1__FRESH_BLIND_PANEL_REQUIRED",
        "failures": failures,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
