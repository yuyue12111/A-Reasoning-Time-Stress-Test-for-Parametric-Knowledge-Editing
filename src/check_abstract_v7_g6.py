#!/usr/bin/env python3
"""Recompute the mechanical parts of the v7 G6 cold-read record.

Semantic reader/scorer labels remain judgments. This checker verifies their
provenance hashes, allocation, word counts, domains, and aggregate arithmetic.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

from check_abstract_v7 import extract_v5


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "paperwriting" / "delivery" / "abstract_v7_g6_raw.json"
TITLE_ABSTRACT = ROOT / "paperwriting" / "title_abstract.md"
V6 = ROOT / "paperwriting" / "delivery" / "abstract_v6_candidate.txt"
V7 = ROOT / "paperwriting" / "delivery" / "abstract_v7_candidate.txt"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    failures: list[str] = []

    v5 = extract_v5(TITLE_ABSTRACT.read_text(encoding="utf-8"))
    v6_bytes = V6.read_bytes()
    v7_bytes = V7.read_bytes()
    v6 = v6_bytes.decode("utf-8").strip()
    v7 = v7_bytes.decode("utf-8").strip()
    actual_versions = {
        "v5": {
            "normalized_text_sha256": sha256(v5.encode("utf-8")),
        },
        "v6": {
            "file_sha256": sha256(v6_bytes),
            "normalized_text_sha256": sha256(v6.encode("utf-8")),
        },
        "v7": {
            "file_sha256": sha256(v7_bytes),
            "normalized_text_sha256": sha256(v7.encode("utf-8")),
        },
    }
    recorded_versions = raw["protocol"]["version_sources"]
    for version, actual in actual_versions.items():
        for key, value in actual.items():
            if recorded_versions[version].get(key) != value:
                failures.append(f"{version} {key} mismatch")

    readers = raw["readers"]
    reader_ids = [row["reader_id"] for row in readers]
    if len(reader_ids) != len(set(reader_ids)):
        failures.append("duplicate reader_id")
    allocation = Counter(row["version"] for row in readers)
    if allocation != Counter({"v5": 4, "v6": 4, "v7": 4}):
        failures.append(f"unbalanced allocation: {dict(allocation)}")

    clarity: dict[str, list[int]] = defaultdict(list)
    for row in readers:
        observed_words = len(row["retelling"].split())
        if observed_words != row["retelling_word_count"]:
            failures.append(f"{row['reader_id']} word-count mismatch")
        if observed_words > 30:
            failures.append(f"{row['reader_id']} exceeds 30 words")
        if row["clarity"] not in {1, 2, 3, 4, 5}:
            failures.append(f"{row['reader_id']} invalid clarity")
        clarity[row["version"]].append(row["clarity"])

    scorer_totals: dict[str, dict[str, list[int]]] = {}
    valid_bounded_cloze_hits: dict[str, int] = {}
    expected_ids = {
        version: {row["reader_id"] for row in readers if row["version"] == version}
        for version in ("v5", "v6", "v7")
    }
    for scorer_name, scorer in raw["operational_scorers"].items():
        if scorer_name == "rubric":
            continue
        scorer_totals[scorer_name] = {}
        v7_bounded_hits = 0
        for version in ("v5", "v6", "v7"):
            block = scorer[version]
            item_ids = {key for key in block if key != "totals"}
            if item_ids != expected_ids[version]:
                failures.append(f"{scorer_name}/{version} reader set mismatch")
            aggregate = [0, 0, 0, 0, 0]
            for reader_id in sorted(item_ids):
                item = block[reader_id]
                atoms = item["atoms"]
                if len(atoms) != 5 or any(value not in {0, 1} for value in atoms):
                    failures.append(f"{scorer_name}/{reader_id} invalid atoms")
                    continue
                if any(flag not in {"U", "I", "M"} for flag in item["flags"]):
                    failures.append(f"{scorer_name}/{reader_id} invalid flags")
                aggregate = [a + b for a, b in zip(aggregate, atoms)]
                if version == "v7" and atoms[2] == 1 and "I" not in item["flags"]:
                    v7_bounded_hits += 1
            if aggregate != block["totals"]:
                failures.append(f"{scorer_name}/{version} total mismatch")
            scorer_totals[scorer_name][version] = aggregate
        valid_bounded_cloze_hits[scorer_name] = v7_bounded_hits

    if raw["decision"]["status"] != "NOT_PASSED_CLEAR_WIN_NOT_ESTABLISHED":
        failures.append("unexpected decision status")

    report = {
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "allocation": dict(sorted(allocation.items())),
        "clarity_scores": {key: clarity[key] for key in sorted(clarity)},
        "scorer_totals": scorer_totals,
        "v7_valid_bounded_cloze_hits": valid_bounded_cloze_hits,
        "decision": raw["decision"]["status"],
        "raw_record_sha256": sha256(RAW.read_bytes()),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
