"""Aggregate the frozen X3 20-case paraphrase content audit on CPU.

This audit is descriptive only.  It never filters X3 cases or changes the
preregistered fresh-mp2 endpoint.
"""
import argparse
from collections import Counter
import hashlib
import json
import os


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = ("readable", "answerable_same_fact", "prefix_changes_requested_fact")
PROBES = ("para0", "para1")


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def sha_file(path):
    h = hashlib.sha256()
    with open(_abs(path), "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path):
    rows = []
    with open(_abs(path), encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                raise ValueError(f"{path}:{line_no}: blank line")
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def validate_judge(rows, manifest, judge):
    expected_ids = [row["case_id"] for row in manifest["records"]]
    got_ids = [row.get("case_id") for row in rows]
    if got_ids != expected_ids:
        raise ValueError(f"{judge}: case_id set/order differs from frozen manifest")
    if len(set(got_ids)) != len(got_ids):
        raise ValueError(f"{judge}: duplicate case_id")
    for row in rows:
        for probe in PROBES:
            label = row.get(probe)
            if not isinstance(label, dict):
                raise ValueError(f"{judge}:{row['case_id']}:{probe}: missing label object")
            for field in FIELDS:
                if type(label.get(field)) is not bool:
                    raise ValueError(
                        f"{judge}:{row['case_id']}:{probe}:{field}: expected boolean")
            if not isinstance(label.get("reason"), str) or not label["reason"].strip():
                raise ValueError(f"{judge}:{row['case_id']}:{probe}: empty reason")


def majority(votes):
    if len(votes) != 3 or any(type(v) is not bool for v in votes):
        raise ValueError(f"expected three boolean votes, got {votes}")
    return sum(votes) >= 2


def agreement(vote_rows):
    """Fleiss kappa and pairwise agreement for three raters, two categories."""
    if not vote_rows:
        raise ValueError("agreement requires at least one item")
    total = Counter()
    equal_pairs = unanimous = two_one = 0
    for votes in vote_rows:
        if len(votes) != 3 or any(type(v) is not bool for v in votes):
            raise ValueError(f"bad vote row {votes}")
        counts = Counter(votes)
        total.update(votes)
        equal_pairs += sum(n * (n - 1) // 2 for n in counts.values())
        unanimous += len(counts) == 1
        two_one += len(counts) == 2
    all_pairs = len(vote_rows) * 3
    pbar = equal_pairs / all_pairs
    denom = len(vote_rows) * 3
    pe = sum((total[value] / denom) ** 2 for value in (False, True))
    kappa = None if pe == 1 else (pbar - pe) / (1 - pe)
    return {
        "n_items": len(vote_rows),
        "unanimous": unanimous,
        "two_one": two_one,
        "raw_pairwise_agreement": {
            "equal_pairs": equal_pairs,
            "all_pairs": all_pairs,
            "rate": pbar,
        },
        "fleiss_kappa": kappa,
    }


def aggregate(manifest_path, judge_paths):
    manifest = json.load(open(_abs(manifest_path), encoding="utf-8"))
    if manifest.get("n") != 20 or len(manifest.get("records", [])) != 20:
        raise ValueError("frozen X3 content manifest must contain exactly 20 cases")
    if any(len(row.get("paraphrases", [])) != 2 for row in manifest["records"]):
        raise ValueError("every manifest case must contain para0 and para1")

    judges = []
    sources = {"manifest": {"path": manifest_path, "sha256": sha_file(manifest_path)}}
    for judge, path in zip(("J1", "J2", "J3"), judge_paths):
        rows = read_jsonl(path)
        validate_judge(rows, manifest, judge)
        judges.append(rows)
        sources[judge] = {"path": path, "sha256": sha_file(path)}

    records = []
    field_votes = {field: [] for field in FIELDS}
    per_judge = {judge: {field: Counter() for field in FIELDS}
                 for judge in ("J1", "J2", "J3")}
    for case_i, source_row in enumerate(manifest["records"]):
        item_labels = []
        for probe_i, probe in enumerate(PROBES):
            votes = []
            for judge_i, judge in enumerate(("J1", "J2", "J3")):
                label = judges[judge_i][case_i][probe]
                vote = {field: label[field] for field in FIELDS}
                vote.update({"judge": judge, "reason": label["reason"]})
                votes.append(vote)
                for field in FIELDS:
                    per_judge[judge][field][str(label[field]).lower()] += 1
            verdict = {field: majority([vote[field] for vote in votes]) for field in FIELDS}
            verdict["audit_valid"] = (
                verdict["readable"]
                and verdict["answerable_same_fact"]
                and not verdict["prefix_changes_requested_fact"]
            )
            for field in FIELDS:
                field_votes[field].append([vote[field] for vote in votes])
            item_labels.append({
                "probe": probe,
                "text": source_row["paraphrases"][probe_i],
                "votes": votes,
                "majority": verdict,
            })
        records.append({
            "case_id": source_row["case_id"],
            "paraphrases": item_labels,
            "both_paraphrases_audit_valid": all(
                label["majority"]["audit_valid"] for label in item_labels),
        })

    flattened = [label for row in records for label in row["paraphrases"]]
    majority_counts = {
        field: {
            "true": sum(label["majority"][field] for label in flattened),
            "false": sum(not label["majority"][field] for label in flattened),
        }
        for field in FIELDS
    }
    audit_valid = sum(label["majority"]["audit_valid"] for label in flattened)
    bad_ids = [f"{row['case_id']}|{label['probe']}"
               for row in records for label in row["paraphrases"]
               if not label["majority"]["audit_valid"]]
    result = {
        "status": "PASS",
        "audit_scope": "frozen seed-42 20-case/40-paraphrase Day-0 content audit",
        "n_cases": len(records),
        "n_paraphrases": len(flattened),
        "per_judge_true_false": {
            judge: {
                field: {"true": counts["true"], "false": counts["false"]}
                for field, counts in fields.items()
            }
            for judge, fields in per_judge.items()
        },
        "majority_counts": majority_counts,
        "audit_valid_paraphrases": audit_valid,
        "audit_invalid_paraphrases": len(flattened) - audit_valid,
        "audit_invalid_item_ids": bad_ids,
        "cases_with_both_paraphrases_audit_valid": sum(
            row["both_paraphrases_audit_valid"] for row in records),
        "agreement": {field: agreement(votes) for field, votes in field_votes.items()},
        "records": records,
        "source": sources,
        "claim_ceiling": (
            "Descriptive audit only. No row is removed, the preregistered X3 primary endpoint "
            "and PASS remain unchanged, and semantic validity is not inferred from lexical PS."
        ),
    }
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="results/x3_para_audit20.json")
    ap.add_argument("--judge1", default="results/x3_para_audit20_judge1.jsonl")
    ap.add_argument("--judge2", default="results/x3_para_audit20_judge2.jsonl")
    ap.add_argument("--judge3", default="results/x3_para_audit20_judge3.jsonl")
    ap.add_argument("--out", default="results/x3_para_audit20_labels.json")
    args = ap.parse_args()
    result = aggregate(args.manifest, [args.judge1, args.judge2, args.judge3])
    with open(_abs(args.out), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: result[k] for k in (
        "status", "n_cases", "n_paraphrases", "majority_counts",
        "audit_valid_paraphrases", "audit_invalid_paraphrases",
        "cases_with_both_paraphrases_audit_valid", "agreement")},
        ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
