"""Emit/aggregate the 101-row answer-only taxonomy membership re-audit."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os

from revert_judge import build_prompt


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALID_COMMITTED = ("old", "new", "neither")
JUDGE_ORDER = ("J1", "J2", "J3")
A3_SOURCES = {
    "7b": "data/reverted_7b.jsonl",
    "14b": "data/reverted_14b.jsonl",
    "32b": "data/reverted_32b.jsonl",
}
B16_SOURCES = {
    "qwen1.5b-greedy": "data/reverted_1_5b.jsonl",
    "llama8b-greedy": "data/reverted_8b.jsonl",
    "qwen32b-F2B1": "data/reverted_32b_f2b1.jsonl",
    "qwen32b-sample": "data/reverted_32b_samp.jsonl",
    "llama70b-greedy": "data/reverted_70b.jsonl",
}


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha_file(path):
    h = hashlib.sha256()
    with open(_abs(path), "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl_strict(path, label, exact_keys=None):
    rows, seen = [], set()
    for lineno, raw in enumerate(open(_abs(path), encoding="utf-8"), 1):
        if not raw.strip():
            raise ValueError(f"{label}:{lineno}: blank line")
        try:
            row = json.loads(raw)
        except Exception as exc:
            raise ValueError(f"{label}:{lineno}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{label}:{lineno}: expected object")
        if exact_keys is not None and set(row) != set(exact_keys):
            raise ValueError(f"{label}:{lineno}: keys={sorted(row)} expected={sorted(exact_keys)}")
        item_id = row.get("item_id")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError(f"{label}:{lineno}: missing item_id")
        if item_id in seen:
            raise ValueError(f"{label}:{lineno}: duplicate item_id {item_id}")
        seen.add(item_id)
        rows.append(row)
    return rows


def require_same_item_order(expected, rows, label):
    got = [row["item_id"] for row in rows]
    if got != expected:
        if set(got) != set(expected):
            missing = sorted(set(expected) - set(got))
            extra = sorted(set(got) - set(expected))
            raise ValueError(f"{label}: item_id set mismatch; missing={missing}, extra={extra}")
        first = next(i for i, (a, b) in enumerate(zip(expected, got)) if a != b)
        raise ValueError(f"{label}: item_id order mismatch at row {first + 1}: "
                         f"expected={expected[first]} got={got[first]}")


def validate_judge_rows(rows, expected_ids, label):
    if len(rows) != len(expected_ids):
        raise ValueError(f"{label}: expected {len(expected_ids)} rows, got {len(rows)}")
    require_same_item_order(expected_ids, rows, label)
    for i, row in enumerate(rows, 1):
        if row.get("committed") not in VALID_COMMITTED:
            raise ValueError(f"{label}:{i}: invalid committed={row.get('committed')!r}")
        if not isinstance(row.get("reason"), str) or not row["reason"].strip():
            raise ValueError(f"{label}:{i}: missing/non-string reason")


def source_rows(path):
    out = {}
    for lineno, raw in enumerate(open(_abs(path), encoding="utf-8"), 1):
        raw = raw.rstrip("\r\n")
        if not raw:
            continue
        row = json.loads(raw)
        if row["case_id"] in out:
            raise ValueError(f"duplicate case_id in {path}: {row['case_id']}")
        out[row["case_id"]] = {"row": row, "line": lineno, "raw_sha256": _sha(raw)}
    return out


def a3_current_inpop(votes):
    held = sum(bool(v.get("commits_new")) or v.get("in_population") is False for v in votes)
    return held < 2


def build_candidates():
    cache = {path: source_rows(path) for path in set(A3_SOURCES.values()) | set(B16_SOURCES.values())}
    rows = []
    for rec in (json.loads(line) for line in open(_abs("results/a3_neutral/verdicts_all.jsonl")) if line.strip()):
        scale, cid = str(rec["scale"]).lower(), rec["case_id"]
        path = A3_SOURCES[scale]
        src = cache[path].get(cid)
        if not src:
            raise ValueError(f"missing A3 source row: {scale}/{cid}/{path}")
        rows.append(_candidate("a3", scale, cid, path, src,
                               a3_current_inpop(rec.get("votes") or []),
                               [v.get("primary") for v in rec.get("votes") or []]))
    b16 = json.load(open(_abs("results/b16_verdicts.json")))["result"]["per_chain"]
    for rec in b16:
        cell, cid = rec["cell"], rec["case_id"]
        path = B16_SOURCES[cell]
        src = cache[path].get(cid)
        if not src:
            raise ValueError(f"missing B16 source row: {cell}/{cid}/{path}")
        rows.append(_candidate("b16", cell, cid, path, src, bool(rec.get("in_pop")),
                               list(rec.get("votes") or [])))
    keys = [r["item_id"] for r in rows]
    if len(rows) != 101 or len(set(keys)) != 101:
        raise AssertionError(f"P0 candidate drift: rows={len(rows)} unique={len(set(keys))}")
    return rows


def _candidate(pool, cell, cid, path, src, current_inpop, route_votes):
    row = src["row"]
    return {
        "item_id": f"{pool}|{cell}|{cid}", "pool": pool, "cell": cell,
        "case_id": cid, "source_path": path, "source_line": src["line"],
        "source_row_sha256": src["raw_sha256"],
        "answer_sha256": _sha(row.get("answer") or ""),
        "o_old": row["o_old"], "o_new": row["o_new"], "answer": row.get("answer") or "",
        "current_in_population": bool(current_inpop), "existing_route_votes": route_votes,
    }


def emit(args):
    rows = build_candidates()
    os.makedirs(os.path.dirname(_abs(args.sample)) or ROOT, exist_ok=True)
    with open(_abs(args.sample), "w", encoding="utf-8") as fs, \
            open(_abs(args.prompts), "w", encoding="utf-8") as fp:
        for row in rows:
            fs.write(json.dumps(row, ensure_ascii=False) + "\n")
            prompt = build_prompt({"o_old": row["o_old"], "o_new": row["o_new"],
                                   "answer": row["answer"]})
            fp.write(json.dumps({"item_id": row["item_id"], "case_id": row["case_id"],
                                 "prompt": prompt}, ensure_ascii=False) + "\n")
    print(json.dumps({"status": "PASS", "candidates": len(rows),
                      "current_in_population": sum(r["current_in_population"] for r in rows),
                      "sample": _abs(args.sample), "prompts": _abs(args.prompts)}, indent=2))


def merge(args):
    sample = read_jsonl_strict(args.sample, "sample")
    prompts = read_jsonl_strict(args.prompts, "prompts")
    if len(sample) != 101 or len(prompts) != 101:
        raise ValueError(f"frozen P0 expects 101 rows; sample={len(sample)} prompts={len(prompts)}")
    expected = [row["item_id"] for row in sample]
    require_same_item_order(expected, prompts, "prompts")
    for i, (srow, prow) in enumerate(zip(sample, prompts), 1):
        if srow.get("case_id") != prow.get("case_id"):
            raise ValueError(f"sample/prompts case_id mismatch at row {i}")

    judge_specs = [("J1", args.judge1), ("J2", args.judge2), ("J3", args.judge3)]
    judge_rows, judge_counts, source_audit = {}, {}, {}
    for judge, path in judge_specs:
        rows = read_jsonl_strict(path, judge, exact_keys=("item_id", "committed", "reason"))
        validate_judge_rows(rows, expected, judge)
        judge_rows[judge] = rows
        judge_counts[judge] = dict(Counter(row["committed"] for row in rows))
        source_audit[judge] = {"path": path, "sha256": _sha_file(path),
                               "rows": len(rows), "unique_item_ids": len({r['item_id'] for r in rows})}

    os.makedirs(os.path.dirname(_abs(args.out)) or ROOT, exist_ok=True)
    with open(_abs(args.out), "w", encoding="utf-8") as f:
        for i, item_id in enumerate(expected):
            votes = [{"judge": judge, "committed": judge_rows[judge][i]["committed"],
                      "reason": judge_rows[judge][i]["reason"]} for judge in JUDGE_ORDER]
            f.write(json.dumps({"item_id": item_id, "votes": votes}, ensure_ascii=False) + "\n")

    audit = {
        "status": "PASS", "n_items": len(expected),
        "sample": {"path": args.sample, "sha256": _sha_file(args.sample)},
        "prompts": {"path": args.prompts, "sha256": _sha_file(args.prompts)},
        "judges": source_audit, "per_judge_counts": judge_counts,
        "merged": {"path": args.out, "sha256": _sha_file(args.out)},
        "checks": {"json_valid": True, "unique_item_ids": True,
                   "exact_item_set_and_order": True, "valid_committed_only": True,
                   "nonempty_reasons": True, "format_pollution": False},
    }
    os.makedirs(os.path.dirname(_abs(args.audit_out)) or ROOT, exist_ok=True)
    json.dump(audit, open(_abs(args.audit_out), "w"), ensure_ascii=False, indent=2)
    print(json.dumps(audit, ensure_ascii=False, indent=2))


def majority(votes):
    valid = [v.get("committed") for v in votes if v.get("committed") in ("old", "new", "neither")]
    counts = {label: valid.count(label) for label in ("old", "new", "neither")}
    winners = [label for label, count in counts.items() if count >= 2]
    if len(valid) < 2:
        label = "insufficient"
    elif winners:
        label = winners[0]
    elif len(valid) < 3:
        label = "insufficient"
    else:
        label = "neither"
    return label, counts, len(valid), (len(valid) == 3 and len(set(valid)) == 3)


def membership_agreement(verdict_rows):
    per_judge = {judge: Counter() for judge in JUDGE_ORDER}
    total = Counter()
    unanimous = two_one = split = equal_pairs = 0
    majority_counts = Counter()
    for row in verdict_rows:
        labels = [vote["committed"] for vote in row["votes"]]
        for judge, label in zip(JUDGE_ORDER, labels):
            per_judge[judge][label] += 1
            total[label] += 1
        counts = Counter(labels)
        equal_pairs += sum(n * (n - 1) // 2 for n in counts.values())
        if len(counts) == 1:
            unanimous += 1
        elif sorted(counts.values()) == [1, 2]:
            two_one += 1
        else:
            split += 1
        label, _, _, _ = majority(row["votes"])
        majority_counts[label] += 1

    n_items, n_raters = len(verdict_rows), len(JUDGE_ORDER)
    pair_denominator = n_items * (n_raters * (n_raters - 1) // 2)
    p_bar = equal_pairs / pair_denominator if pair_denominator else None
    total_votes = n_items * n_raters
    p_e = sum((total[label] / total_votes) ** 2 for label in VALID_COMMITTED)
    kappa = ((p_bar - p_e) / (1 - p_e)) if p_bar is not None and p_e != 1 else None
    return {
        "per_judge_counts": {judge: {label: per_judge[judge][label]
                                      for label in VALID_COMMITTED} for judge in JUDGE_ORDER},
        "unanimous_cases": unanimous,
        "two_one_majority_cases": two_one,
        "split_1_1_1_cases": split,
        "unanimity_rate": unanimous / n_items if n_items else None,
        "raw_pairwise_agreement": {
            "equal_pairs": equal_pairs, "all_pairs": pair_denominator,
            "rate": p_bar,
        },
        "fleiss_kappa": kappa,
        "majority_counts": {label: majority_counts[label] for label in VALID_COMMITTED},
    }


def validate_merged_verdicts(rows, expected_ids):
    if len(rows) != len(expected_ids):
        raise ValueError(f"verdicts: expected {len(expected_ids)} rows, got {len(rows)}")
    require_same_item_order(expected_ids, rows, "verdicts")
    for i, row in enumerate(rows, 1):
        votes = row.get("votes")
        if not isinstance(votes, list) or len(votes) != 3:
            raise ValueError(f"verdicts:{i}: expected exactly three votes")
        judges = [vote.get("judge") for vote in votes]
        if judges != list(JUDGE_ORDER):
            raise ValueError(f"verdicts:{i}: judge order/identity mismatch: {judges}")
        for vote in votes:
            if vote.get("committed") not in VALID_COMMITTED:
                raise ValueError(f"verdicts:{i}: invalid committed={vote.get('committed')!r}")
            if not isinstance(vote.get("reason"), str) or not vote["reason"].strip():
                raise ValueError(f"verdicts:{i}: missing/non-string reason")


def freeze_rescue_prompts(rows, out_path):
    rescues = [row for row in rows if row["route_action"] == "rejudge_route"]
    os.makedirs(os.path.dirname(_abs(out_path)) or ROOT, exist_ok=True)
    if not rescues:
        open(_abs(out_path), "w", encoding="utf-8").close()
        return {"path": out_path, "sha256": _sha_file(out_path), "n": 0}

    from chain_classify import JUDGE_OUTPUT_SCHEMA, JUDGE_PROMPT_NEUTRAL, build_prompt

    with open(_abs(out_path), "w", encoding="utf-8") as f:
        for row in rescues:
            source_path, source_line = row["source_path"], row["source_line"]
            lines = open(_abs(source_path), encoding="utf-8").read().splitlines()
            if not (1 <= source_line <= len(lines)):
                raise ValueError(f"rescue {row['item_id']}: invalid source_line={source_line}")
            raw = lines[source_line - 1]
            if _sha(raw) != row["source_row_sha256"]:
                raise ValueError(f"rescue {row['item_id']}: source row SHA mismatch")
            source = json.loads(raw)
            if source.get("case_id") != row["case_id"]:
                raise ValueError(f"rescue {row['item_id']}: source case_id mismatch")
            prompt = build_prompt(source, JUDGE_PROMPT_NEUTRAL)
            if "STILL INSTALLED" in prompt or "ROUTING AROUND an intact edit" in prompt:
                raise ValueError(f"rescue {row['item_id']}: non-neutral route prompt contamination")
            f.write(json.dumps({
                "item_id": row["item_id"], "pool": row["pool"], "cell": row["cell"],
                "case_id": row["case_id"], "source_path": source_path,
                "source_line": source_line, "source_row_sha256": row["source_row_sha256"],
                "judge_protocol": "src/chain_classify.py:JUDGE_PROMPT_NEUTRAL",
                "prompt": prompt, "output_schema": JUDGE_OUTPUT_SCHEMA,
            }, ensure_ascii=False) + "\n")
    return {"path": out_path, "sha256": _sha_file(out_path), "n": len(rescues)}


def aggregate(args):
    sample_rows = read_jsonl_strict(args.sample, "sample")
    verdict_rows = read_jsonl_strict(args.verdicts, "verdicts", exact_keys=("item_id", "votes"))
    expected_ids = [row["item_id"] for row in sample_rows]
    if len(sample_rows) != 101:
        raise ValueError(f"frozen P0 expects 101 sample rows, got {len(sample_rows)}")
    validate_merged_verdicts(verdict_rows, expected_ids)
    vote_map = {row["item_id"]: row["votes"] for row in verdict_rows}

    out = []
    for row in sample_rows:
        item_id = row["item_id"]
        label, counts, n_valid, split = majority(vote_map[item_id])
        new_in = label == "old"
        old_in = row["current_in_population"]
        action = ("reuse_route" if old_in and new_in else
                  "drop" if old_in and not new_in else
                  "rejudge_route" if not old_in and new_in else "remain_excluded")
        out.append({**row, "membership_votes": vote_map[item_id],
                    "membership": label, "vote_counts": counts,
                    "n_valid_votes": n_valid, "split_1_1_1": split,
                    "corrected_in_population": new_in, "route_action": action})
    transition = defaultdict(Counter)
    for row in out:
        key = (row["pool"], row["cell"])
        transition[key]["n"] += 1
        transition[key]["current_in_population"] += int(row["current_in_population"])
        transition[key][f"majority_{row['membership']}"] += 1
        transition[key][row["route_action"]] += 1
    transition_rows = []
    for (pool, cell), counts in sorted(transition.items()):
        transition_rows.append({"pool": pool, "cell": cell, **{
            key: counts[key] for key in (
                "n", "current_in_population", "majority_old", "majority_new",
                "majority_neither", "reuse_route", "drop", "rejudge_route",
                "remain_excluded")}})

    drops = [row["item_id"] for row in out if row["route_action"] == "drop"]
    rescues = [row["item_id"] for row in out if row["route_action"] == "rejudge_route"]
    agreement = membership_agreement(verdict_rows)
    rescue_artifact = freeze_rescue_prompts(out, args.rescue_prompts_out)
    status = "ROUTE_REJUDGE_REQUIRED" if rescues else "PASS"
    summary = {
        "status": status, "technical_status": "PASS",
        "corrected_taxonomy_status": "PENDING_ROUTE_REJUDGE" if rescues else "COMPLETE",
        "n_candidates": len(out), "missing_verdicts": [],
        "current_in_population": sum(r["current_in_population"] for r in out),
        "corrected_old": sum(r["corrected_in_population"] for r in out),
        "membership_agreement": agreement,
        "drops": len(drops), "drop_item_ids": drops,
        "rescues_requiring_route_rejudge": len(rescues), "rescue_item_ids": rescues,
        "insufficient": sum(r["membership"] == "insufficient" for r in out),
        "per_pool_cell_transitions": transition_rows,
        "rescue_route_prompts": rescue_artifact,
        "official_x1_gate": "UNCHANGED: preregistered 9/18 FAIL",
        "claim_ceiling": ("Membership majority is complete for 101 items, but corrected route-taxonomy "
                          "counts/percentages remain pending until every rescued excluded row receives "
                          "three new neutral route votes."),
    }
    os.makedirs(os.path.dirname(_abs(args.out)) or ROOT, exist_ok=True)
    json.dump({"summary": summary, "rows": out}, open(_abs(args.out), "w"),
              ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    e = sub.add_parser("emit")
    e.add_argument("--sample", default="results/p0_membership_sample.jsonl")
    e.add_argument("--prompts", default="results/p0_membership_prompts.jsonl")
    m = sub.add_parser("merge")
    m.add_argument("--sample", default="results/p0_membership_sample.jsonl")
    m.add_argument("--prompts", default="results/p0_membership_prompts.jsonl")
    m.add_argument("--judge1", required=True)
    m.add_argument("--judge2", required=True)
    m.add_argument("--judge3", required=True)
    m.add_argument("--out", default="results/p0_membership_verdicts.jsonl")
    m.add_argument("--audit-out", default="results/p0_membership_raw_audit.json")
    a = sub.add_parser("aggregate")
    a.add_argument("--sample", default="results/p0_membership_sample.jsonl")
    a.add_argument("--verdicts", required=True)
    a.add_argument("--out", default="results/p0_membership_audit.json")
    a.add_argument("--rescue-prompts-out", default="results/p0_route_rescue_prompts.jsonl")
    args = ap.parse_args()
    {"emit": emit, "merge": merge, "aggregate": aggregate}[args.mode](args)


if __name__ == "__main__":
    main()
