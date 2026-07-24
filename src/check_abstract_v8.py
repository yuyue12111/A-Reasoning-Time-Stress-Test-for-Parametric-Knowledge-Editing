#!/usr/bin/env python3
"""Fail-closed G1/G2/G6.2a preflight for the v8.1 story abstract."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

from check_abstract_v7 import (
    EXPECTED_TITLE,
    EXPECTED_TLDR,
    EXPECTED_V5_NORMALIZED_SHA256,
    ROOT,
    RESULTS,
    TITLE_ABSTRACT,
    V6,
    close,
    extract_frozen_title,
    extract_frozen_tldr,
    extract_v5,
    get_path,
    sentence_split,
    sha256,
)


V8 = ROOT / "paperwriting" / "delivery" / "abstract_v8_candidate.txt"
LEDGER = ROOT / "paperwriting" / "delivery" / "abstract_v8_substance_ledger.json"
PROTOCOL = ROOT / "paperwriting" / "delivery" / "abstract_v8_g62_protocol.json"
SEMANTIC_AUDIT = ROOT / "paperwriting" / "delivery" / "abstract_v8_semantic_audit.json"
G62_AUDIT = ROOT / "paperwriting" / "delivery" / "abstract_v8_g62_audit.json"

EXPECTED_RESULT_OCCURRENCES = (
    "0.106", "0.107", "19.3%", "9.2%", "19.3%", "8.5%"
)
ALLOWED_MODEL_IDS = {"32B", "70B", "14B"}
REQUIRED_PHRASES = (
    "An edit can pass direct-answer validation yet lose control of the final answer when the model reasons",
    "We evaluate each ROME edit on CounterFact twice",
    "at zero thinking and after a natural chain",
    "six fixed checkpoints",
    "two DeepSeek-R1-distill families",
    "At the largest tested checkpoint in each family",
    "edit success drops by 0.106",
    "zero-thinking successes",
    "old answers resurface",
    "displace new answers outright",
    "no detectable old-answer drift",
    "Yet in the Qwen-32B reversions we examined, the edited association remains detectable at a cloze probe",
    "separately, route analysis finds visible in-chain paths to old answers",
    "motivating a chain-routing hypothesis",
    "We next test for a chain-local control point",
    "by suppressing old-answer first tokens",
    "only during Qwen-32B reasoning",
    "answer logits untouched",
    "The signed, dose-graded intervention",
    "placebo and same-relation controls",
    "offsets the edit-success loss",
    "lowers the resurfacing rate from 19.3% to 8.5%",
    "near-null answer-level effects",
    "not enough",
    "reasoning-time stress test",
    "admits a chain-local causal control point",
)
BANNED_PHRASES = (
    "thinking takes edits back", "nearly identical", "deployed reasoning models reason",
    "routes around it", "the edit is not gone", "survives", "intact", "not erased",
    "no such drift", "models never", "models rarely", "causes", "explains",
    "removes", "eliminates", "concentrates", "stable across", "overall",
    "only against", "inert placebo", "guaranteed upper bound", ".214",
)
LEDGER_MARKERS = (
    "[", "]", "κ", "23/23", "41/33", "0.138", "complete-case", "strict",
    "scorer", "panel", "judge", "majority",
)


def numeric_tokens(text: str) -> list[str]:
    return re.findall(r"(?<![A-Za-z0-9_.])(?:−|-)?\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?(?:%|B)?", text)


def result_occurrences(text: str) -> list[str]:
    options = sorted(set(EXPECTED_RESULT_OCCURRENCES), key=len, reverse=True)
    return re.findall("|".join(re.escape(x) for x in options), text)


def extract_internal_v81(markdown: str) -> str:
    tail = markdown.split("## Abstract v8.1", 1)[1]
    lines: list[str] = []
    started = False
    for line in tail.splitlines():
        if line.startswith("> "):
            started = True
            lines.append(line[2:])
        elif started:
            break
    if not lines:
        raise AssertionError("Could not extract internally frozen v8.1 abstract")
    return " ".join(lines)


def main() -> int:
    failures: list[str] = []
    title_md = TITLE_ABSTRACT.read_text(encoding="utf-8")
    v5 = extract_v5(title_md)
    v8_bytes = V8.read_bytes()
    v8 = v8_bytes.decode("utf-8").strip()
    sentences = sentence_split(v8)
    sentence_lengths = [len(sentence.split()) for sentence in sentences]
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    semantic_audit = json.loads(SEMANTIC_AUDIT.read_text(encoding="utf-8"))
    g62_audit = json.loads(G62_AUDIT.read_text(encoding="utf-8"))

    if len(v8.split()) > 190:
        failures.append(f"word count exceeds 190: {len(v8.split())}")
    if not 6 <= len(sentences) <= 8:
        failures.append(f"sentence count outside 6-8: {len(sentences)}")
    if max(sentence_lengths, default=0) > 30:
        failures.append(f"sentence exceeds 30 words: {sentence_lengths}")

    result_numbers = result_occurrences(v8)
    if tuple(result_numbers) != EXPECTED_RESULT_OCCURRENCES:
        failures.append(f"result-number sequence mismatch: {result_numbers}")
    all_numbers = numeric_tokens(v8)
    expected_result_counts = Counter(EXPECTED_RESULT_OCCURRENCES)
    observed_result_counts = Counter(result_numbers)
    model_ids = [token for token in all_numbers if token in ALLOWED_MODEL_IDS]
    residual = Counter(all_numbers)
    residual.subtract(observed_result_counts)
    for model_id in model_ids:
        residual[model_id] -= 1
    unexpected = sorted(token for token, count in residual.items() for _ in range(max(count, 0)))
    if observed_result_counts != expected_result_counts:
        failures.append("result-number multiset mismatch")
    if unexpected:
        failures.append(f"unexpected numeric tokens: {unexpected}")

    numeric_sentence_ids = [
        i for i, sentence in enumerate(sentences, 1) if result_occurrences(sentence)
    ]
    if numeric_sentence_ids != [3, 4, 7]:
        failures.append(f"numeric beats are not isolated to S3/S4/S7: {numeric_sentence_ids}")

    missing_required = [phrase for phrase in REQUIRED_PHRASES if phrase not in v8]
    banned_hits = [phrase for phrase in BANNED_PHRASES if phrase in v8.lower()]
    ledger_hits = [marker for marker in LEDGER_MARKERS if marker.lower() in v8.lower()]
    if missing_required:
        failures.append(f"missing required phrases: {missing_required}")
    if banned_hits:
        failures.append(f"banned phrase hits: {banned_hits}")
    if ledger_hits:
        failures.append(f"ledger-language hits: {ledger_hits}")

    evidence_checks = {
        "B1.Qwen32.drop=0.106": close(float(get_path(results, "capability", "families", "R1-Distill-Qwen", "es_drop", 3)), 0.106),
        "B1.Qwen32.model=32": get_path(results, "capability", "families", "R1-Distill-Qwen", "params_b", 3) == 32,
        "B1.Llama70.drop=0.107": close(float(get_path(results, "capability", "families", "R1-Distill-Llama", "es_drop", 1)), 0.107),
        "B1.Llama70.model=70": get_path(results, "capability", "families", "R1-Distill-Llama", "params_b", 1) == 70,
        "B2.strict=9.2%": close(float(get_path(results, "rq3", "sup_battery", "marginal_B3", "N", "RRs")), 0.092),
        "B2.loose=19.3%": close(float(get_path(results, "rq3", "sup_battery", "marginal_B3", "N", "RR")), 0.193),
        "B3.armwise_T=8.5%": close(float(get_path(results, "rq3", "sup_battery", "marginal_B3", "T", "RR")), 0.085),
        "base.old_answer_drift_ci_contains_zero": (
            float(get_path(results, "base_probe", "f1_edit_specificity", "paired_ci", "ci95", 0)) <= 0.0 <=
            float(get_path(results, "base_probe", "f1_edit_specificity", "paired_ci", "ci95", 1))
        ),
    }
    for name, ok in evidence_checks.items():
        if not ok:
            failures.append(f"evidence check failed: {name}")

    expected_claim_ids = {f"C{i:02d}" for i in range(1, 18)}
    claims = ledger["claims"]
    claim_ids = {claim["claim_id"] for claim in claims}
    mapping_checks = {
        "candidate_file_hash": ledger["candidate"]["file_sha256"] == sha256(v8_bytes),
        "candidate_normalized_hash": ledger["candidate"]["normalized_text_sha256"] == sha256(v8.encode("utf-8")),
        "claim_id_coverage": claim_ids == expected_claim_ids and len(claims) == len(expected_claim_ids),
        "claim_status_domain": all(c["status"] in {"present_in_prose", "moved_to_debt"} for c in claims),
        "hedge_domain": all(c["hedge_relation"] in {"same", "weaker"} for c in claims),
        "moved_claims_have_debt": all(c["status"] != "moved_to_debt" or c["debt_id"] for c in claims),
        "debt_id_coverage": set(ledger["debts"]) == {"D1","D2","D3","D4","D5","D6","D7","D8","R1"},
        "all_debts_open": all(d["status"] == "OPEN" for d in ledger["debts"].values()),
        "g5_blocked": ledger["g5"]["adoption_gate"] == "BLOCKED",
    }
    for name, ok in mapping_checks.items():
        if not ok:
            failures.append(f"mapping check failed: {name}")

    local_frozen_checks = {
        "title": extract_frozen_title(title_md) == EXPECTED_TITLE,
        "tldr": extract_frozen_tldr(title_md) == EXPECTED_TLDR,
        "v5": sha256(v5.encode("utf-8")) == EXPECTED_V5_NORMALIZED_SHA256,
        "v8.1_embedded": extract_internal_v81(title_md) == v8,
    }
    for name, ok in local_frozen_checks.items():
        if not ok:
            failures.append(f"local frozen field changed: {name}")

    protocol_checks = {
        "preregistered": protocol["status"] == "PREREGISTERED_FOR_FINAL_BYTES_BEFORE_FINAL_READERS",
        "v8_hash": protocol["versions"]["v8.1"]["file_sha256"] == sha256(v8_bytes),
        "v6_hash": protocol["versions"]["v6"]["file_sha256"] == hashlib.sha256(V6.read_bytes()).hexdigest(),
        "user_only_elegance": protocol["elegance_decider"] == "USER_ONLY",
    }
    for name, ok in protocol_checks.items():
        if not ok:
            failures.append(f"protocol check failed: {name}")

    semantic_checks = {
        "candidate_hash": semantic_audit["candidate_file_sha256"] == sha256(v8_bytes),
        "G3": semantic_audit["g3_substance"] == "PASS",
        "science": semantic_audit["independent_reviews"]["science"]["status"] == "PASS",
        "statistics": semantic_audit["independent_reviews"]["statistics"]["status"] == "PASS",
        "causal_scope": semantic_audit["independent_reviews"]["causal_scope"]["status"] == "PASS",
    }
    for name, ok in semantic_checks.items():
        if not ok:
            failures.append(f"semantic-audit check failed: {name}")

    g62_checks = {
        "candidate_hash": g62_audit["candidate_file_sha256"] == sha256(v8_bytes),
        "guard_pass": g62_audit["status"] == "PASS_NO_OBSERVED_REGRESSION_NOT_EQUIVALENCE",
        "user_authority_recorded": (
            g62_audit["interpretation_limit"].endswith("Elegance remains a user-only judgment.")
            and g62_audit["user_elegance_judgment"] == "APPROVED_FOR_INTERNAL_FREEZE_BY_USER_REQUEST"
            and protocol["user_decision"] == "APPROVE_INTERNAL_FREEZE; EXTERNAL_SYNC_REMAINS_G5_GATED"
        ),
    }
    for name, ok in g62_checks.items():
        if not ok:
            failures.append(f"G6.2-audit check failed: {name}")

    report = {
        "status": "PASS" if not failures else "FAIL",
        "candidate": {
            "path": str(V8.relative_to(ROOT)),
            "file_sha256": sha256(v8_bytes),
            "normalized_text_sha256": sha256(v8.encode("utf-8")),
            "word_count_whitespace": len(v8.split()),
            "sentence_count": len(sentences),
            "sentence_word_counts": sentence_lengths,
        },
        "result_number_occurrences": result_numbers,
        "result_number_count": len(result_numbers),
        "model_id_occurrences": model_ids,
        "unexpected_numeric_tokens": unexpected,
        "result_numeric_sentence_ids": numeric_sentence_ids,
        "missing_required_phrases": missing_required,
        "banned_phrase_hits": banned_hits,
        "ledger_language_hits": ledger_hits,
        "evidence_checks": evidence_checks,
        "substance_mapping_checks": mapping_checks,
        "local_frozen_field_checks": local_frozen_checks,
        "g62_protocol_checks": protocol_checks,
        "semantic_audit_checks": semantic_checks,
        "g62_audit_checks": g62_checks,
        "G1_numeric": "PASS" if not any("number" in f or "numeric" in f or "evidence" in f for f in failures) else "FAIL",
        "G2_language_and_form": "PASS" if not any("phrase" in f or "ledger-language" in f or "sentence" in f or "word count" in f for f in failures) else "FAIL",
        "G3_substance": semantic_audit["g3_substance"],
        "G4_hostile_read": semantic_audit["g4_hostile_read"],
        "G5": {"disposition_table":"PASS" if mapping_checks["debt_id_coverage"] else "FAIL", "manuscript_debts":"OPEN", "adoption_gate":"BLOCKED"},
        "G6_2": {"corpus_form":"PASS" if not failures else "FAIL", "llm_guard":g62_audit["status"], "user_elegance_judgment":g62_audit["user_elegance_judgment"]},
        "external_openreview_state": "NOT_VERIFIED_EXTERNAL",
        "failures": failures,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
