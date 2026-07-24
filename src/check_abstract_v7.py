#!/usr/bin/env python3
"""Fail-closed structural and evidence audit for the v7 abstract candidate.

The script validates a candidate only. It never edits the frozen abstract or
asserts that the main-text disclosure debts required for adoption are closed.
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
V6 = ROOT / "paperwriting" / "delivery" / "abstract_v6_candidate.txt"
V7 = ROOT / "paperwriting" / "delivery" / "abstract_v7_candidate.txt"

EXPECTED_TITLE = (
    "Direct-Answer Edit Success Is Not Enough: A Reasoning-Time Stress Test "
    "for Parametric Knowledge Editing"
)
EXPECTED_TLDR = (
    "An edit can pass direct-answer validation yet be overturned when the model "
    "reasons—while its edited association remains detectable at a cloze probe. "
    "Our stress test quantifies these reversions; think-span-only suppression lowers them."
)
EXPECTED_V5_NORMALIZED_SHA256 = (
    "80b2208d42f5dc6c33378e8ead282b7f9f5316e0d7b0053cbef3cb9405add223"
)

LOCKED_PHRASES = (
    "the edited association remains detectable at a cloze probe",
    "direct validation is not a reasoning-time stress test",
    "At the largest tested checkpoint in each family",
    "no detectable unedited-base drift",
    "persists across three fixed sampling seeds",
    "motivating a chain-routing hypothesis",
    "We next test for a chain-local control point",
    "offsets the observed thinking tax",
    "edit-success gains replicate at 14B and transfer to MEMIT",
    "not enough",
    "admits a chain-local causal control point",
    "strict transfer remains inconclusive",
)

BANNED_PHRASES = (
    "every one",
    "overall",
    "only against",
    "inert placebo",
    "rather than simple erasure",
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
    "first to discover",
    "preregistered",
    "edit intact",
    "not erased",
    "guaranteed upper bound",
    "removes",
    "concentrates",
    "stable across",
    "in the weights",
    ".214",
)

# Result quantities, not model identifiers or design counts. The plan's three
# beats require seven occurrences; counting 32B/70B/14B would make its own
# required wording incompatible with the stated 6–8 budget.
EXPECTED_EFFECT_NUMBER_OCCURRENCES = (
    "0.106",
    "0.107",
    "9.2%",
    "19.3%",
    "19.3%",
    "8.5%",
    "−0.102",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_v5(markdown: str) -> str:
    tail = markdown.split("## Abstract v5", 1)[1]
    lines: list[str] = []
    started = False
    for line in tail.splitlines():
        if line.startswith("> "):
            started = True
            lines.append(line[2:])
        elif started:
            break
    if not lines:
        raise AssertionError("Could not extract frozen v5 abstract")
    return " ".join(lines)


def extract_frozen_title(markdown: str) -> str:
    section = markdown.split("## Title", 1)[1].split("## Abstract v5", 1)[0]
    match = re.search(r"^> \*\*(.+)\*\*$", section, flags=re.MULTILINE)
    if not match:
        raise AssertionError("Could not extract frozen Title")
    return match.group(1)


def extract_frozen_tldr(markdown: str) -> str:
    section = markdown.split("TL;DR（250 字符限）", 1)[1].split("- **Abstract**", 1)[0]
    candidates = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("*An edit can pass") and "*（234 字符）" in stripped:
            candidates.append(stripped.split("*（234 字符）", 1)[0][1:])
    if len(candidates) != 1:
        raise AssertionError(f"Could not uniquely extract frozen TL;DR: {len(candidates)}")
    return candidates[0]


def sentence_split(text: str) -> list[str]:
    return re.split(r"(?<=[.!?]) (?=[A-Z])", text)


def all_numeric_tokens(text: str) -> list[str]:
    return re.findall(
        r"(?<![A-Za-z0-9_.])(?:−|-)?\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?(?:%|B)?",
        text,
    )


def effect_number_occurrences(text: str) -> list[str]:
    options = sorted(set(EXPECTED_EFFECT_NUMBER_OCCURRENCES), key=len, reverse=True)
    pattern = "|".join(re.escape(item) for item in options)
    return re.findall(pattern, text)


def get_path(obj: object, *path: object) -> object:
    cur = obj
    for key in path:
        if isinstance(key, int):
            if not isinstance(cur, list):
                raise AssertionError(f"Expected list at {path}")
            cur = cur[key]
        else:
            if not isinstance(cur, dict) or key not in cur:
                raise AssertionError(f"Missing JSON path: {'.'.join(map(str, path))}")
            cur = cur[key]
    return cur


def close(actual: float, expected: float, tolerance: float = 5e-4) -> bool:
    return abs(actual - expected) <= tolerance


def main() -> int:
    title_md = TITLE_ABSTRACT.read_text(encoding="utf-8")
    v5 = extract_v5(title_md)
    frozen_title = extract_frozen_title(title_md)
    frozen_tldr = extract_frozen_tldr(title_md)
    v6 = V6.read_text(encoding="utf-8").strip()
    v7_bytes = V7.read_bytes()
    v7 = v7_bytes.decode("utf-8").strip()
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    failures: list[str] = []

    sentences = sentence_split(v7)
    sentence_word_counts = [len(sentence.split()) for sentence in sentences]
    if not 7 <= len(sentences) <= 9:
        failures.append(f"sentence count outside 7–9: {len(sentences)}")
    if len(v7.split()) > 200:
        failures.append(f"word count exceeds 200: {len(v7.split())}")
    if max(sentence_word_counts, default=0) > 30:
        failures.append(f"sentence exceeds 30 words: {sentence_word_counts}")

    missing_locked = [phrase for phrase in LOCKED_PHRASES if phrase not in v7]
    if missing_locked:
        failures.append(f"missing locked phrases: {missing_locked}")
    banned_hits = [phrase for phrase in BANNED_PHRASES if phrase in v7.lower()]
    if banned_hits:
        failures.append(f"banned phrase hits: {banned_hits}")

    effects = effect_number_occurrences(v7)
    if tuple(effects) != EXPECTED_EFFECT_NUMBER_OCCURRENCES:
        failures.append(f"effect-number sequence mismatch: {effects}")
    if not 6 <= len(effects) <= 8:
        failures.append(f"effect-number occurrence count outside 6–8: {len(effects)}")

    v5v6_numeric_set = set(all_numeric_tokens(v5)) | set(all_numeric_tokens(v6))
    v7_numeric_set = set(all_numeric_tokens(v7))
    if not v7_numeric_set <= v5v6_numeric_set:
        failures.append(f"new numeric tokens: {sorted(v7_numeric_set - v5v6_numeric_set)}")

    # Exact evidence anchors and rounding rules for the three beats.
    qwen_drop = get_path(results, "capability", "families", "R1-Distill-Qwen", "es_drop", 3)
    llama_drop = get_path(results, "capability", "families", "R1-Distill-Llama", "es_drop", 1)
    strict_rate = get_path(results, "rq3", "sup_battery", "marginal_B3", "N", "RRs")
    loose_n = get_path(results, "rq3", "sup_battery", "marginal_B3", "N", "RR")
    loose_t = get_path(results, "rq3", "sup_battery", "marginal_B3", "T", "RR")
    paired_rr = get_path(
        results, "rq3", "sup_battery", "cross_arm_paired_ci", "T_minus_N", "RR", 0
    )
    base_drift_ci = get_path(
        results, "base_probe", "f1_edit_specificity", "paired_ci", "ci95"
    )
    evidence_checks = {
        "B1.Qwen32.drop=0.106": close(float(qwen_drop), 0.106),
        "B1.Llama70.drop=0.107": close(float(llama_drop), 0.107),
        "B2.strict=9.2%": close(float(strict_rate), 0.092),
        "B2.loose=19.3%": close(float(loose_n), 0.193),
        "B3.armwise_T=8.5%": close(float(loose_t), 0.085),
        "B3.complete_case_paired=-0.102": close(float(paired_rr), -0.102),
        "control.base_drift_ci_contains_zero": (
            float(base_drift_ci[0]) <= 0.0 <= float(base_drift_ci[1])
        ),
    }
    for name, ok in evidence_checks.items():
        if not ok:
            failures.append(f"evidence check failed: {name}")

    # Scope/estimand grammar checks that numeric equality alone cannot catch.
    required_scope_fragments = (
        "On Qwen-32B",
        "zero-thinking successes",
        "resurfaces in 19.3% of them",
        "examined reversions",
        "detectable at a cloze probe",
        "Separately",
        "answer logits untouched",
        "marginal loose reversion",
        "complete-case paired change",
    )
    missing_scope = [fragment for fragment in required_scope_fragments if fragment not in v7]
    if missing_scope:
        failures.append(f"missing scope/estimand fragments: {missing_scope}")
    if v7.count("On Qwen-32B") < 2:
        failures.append("Qwen-32B scope must explicitly govern both severity and controls")

    if frozen_title != EXPECTED_TITLE:
        failures.append("frozen title bytes changed")
    if frozen_tldr != EXPECTED_TLDR:
        failures.append("frozen TL;DR bytes changed")
    if sha256(v5.encode("utf-8")) != EXPECTED_V5_NORMALIZED_SHA256:
        failures.append("frozen v5 normalized bytes changed")

    report = {
        "status": "PASS" if not failures else "FAIL",
        "candidate": {
            "path": str(V7.relative_to(ROOT)),
            "file_sha256": sha256(v7_bytes),
            "normalized_text_sha256": sha256(v7.encode("utf-8")),
            "word_count_whitespace": len(v7.split()),
            "sentence_count": len(sentences),
            "sentence_word_counts": sentence_word_counts,
        },
        "effect_number_definition": (
            "result-quantity occurrences only; model identifiers and design counts excluded"
        ),
        "effect_number_occurrences": effects,
        "effect_number_count": len(effects),
        "all_digit_bearing_tokens": all_numeric_tokens(v7),
        "numeric_set_subset_of_v5_union_v6": v7_numeric_set <= v5v6_numeric_set,
        "missing_locked_phrases": missing_locked,
        "banned_phrase_hits": banned_hits,
        "missing_scope_or_estimand_fragments": missing_scope,
        "evidence_checks": evidence_checks,
        "frozen_title_exact": frozen_title == EXPECTED_TITLE,
        "frozen_tldr_exact": frozen_tldr == EXPECTED_TLDR,
        "frozen_v5_normalized_sha256_exact": (
            sha256(v5.encode("utf-8")) == EXPECTED_V5_NORMALIZED_SHA256
        ),
        "adoption_gate": "BLOCKED_PENDING_MAIN_TEXT_DEBTS_D1_D7_AND_R1",
        "failures": failures,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
