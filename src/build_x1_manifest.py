"""Build/verify the frozen X1 natural-chain replay source manifest.

Selection is deliberately two-stage and outcome-blind (plan v1.79 / prereg-x1.md):
1) choose the highest-priority source that exists for each case;
2) require that chosen source itself has >=2/3 pre-existing neutral committed-old votes.
A lower-priority source never rescues an ineligible higher-priority source.

Default prints the canonical JSONL manifest to stdout.  ``--check`` verifies the tracked manifest
byte-for-data equivalence without rewriting it.
"""
import argparse
import hashlib
import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = [
    ("main_b3_greedy", "data/reverted_32b.jsonl"),
    ("f2_b1_greedy", "data/reverted_32b_f2b1.jsonl"),
    ("f3_historical_sample_seed2", "data/reverted_32b_samp.jsonl"),
]
MAIN_JUDGES = "results/a3_neutral/verdicts_all.jsonl"
B16_JUDGES = "results/b16_verdicts.json"
DEFAULT_MANIFEST = "data/x1_replay_manifest.jsonl"


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_source(path):
    rows = []
    with open(_abs(path), encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            raw = raw.rstrip("\r\n")
            if not raw:
                continue
            row = json.loads(raw)
            rows.append({"row": row, "line": lineno, "raw_sha256": _sha(raw)})
    return rows


def _main_votes():
    out = {}
    for raw in open(_abs(MAIN_JUDGES), encoding="utf-8"):
        if not raw.strip():
            continue
        rec = json.loads(raw)
        if str(rec.get("scale", "")).lower() == "32b":
            out[rec["case_id"]] = rec.get("votes") or []
    return out


def _b16_votes():
    blob = json.load(open(_abs(B16_JUDGES), encoding="utf-8"))
    return {(r["cell"], r["case_id"]): r for r in blob["result"]["per_chain"]}


def judge_record(source, case_id, main_votes, b16_votes):
    if source == "main_b3_greedy":
        votes = main_votes.get(case_id, [])
        old_votes = sum(v.get("in_population") is True and not v.get("commits_new", False)
                        for v in votes)
        return {
            "judge_source": MAIN_JUDGES + "#scale=32b",
            "judge_votes": [v.get("primary") for v in votes],
            "old_commit_votes": old_votes,
            "n_judge_votes": len(votes),
            "eligible": len(votes) == 3 and old_votes >= 2,
        }
    cell = "qwen32b-F2B1" if source == "f2_b1_greedy" else "qwen32b-sample"
    rec = b16_votes.get((cell, case_id))
    labels = (rec or {}).get("votes") or []
    old_votes = sum(v not in ("Excluded-held", "Excluded-degenerate") for v in labels)
    return {
        "judge_source": f"{B16_JUDGES}#cell={cell}",
        "judge_votes": labels,
        "old_commit_votes": old_votes,
        "n_judge_votes": len(labels),
        "eligible": bool(rec and rec.get("in_pop") is True and len(labels) == 3 and old_votes >= 2),
    }


def build_manifest():
    loaded = [(label, path, read_source(path)) for label, path in SOURCES]
    maps = [(label, path, {x["row"]["case_id"]: x for x in rows})
            for label, path, rows in loaded]
    order = []
    for _, _, rows in loaded:
        for x in rows:
            cid = x["row"]["case_id"]
            if cid not in order:
                order.append(cid)

    main_votes, b16_votes = _main_votes(), _b16_votes()
    manifest, audit = [], []
    for cid in order:
        source_rank, (label, path, item) = next(
            (idx, (label, path, cmap[cid]))
            for idx, (label, path, cmap) in enumerate(maps, 1) if cid in cmap)
        row = item["row"]
        judge = judge_record(label, cid, main_votes, b16_votes)
        audit.append({"case_id": cid, "selected_source": label, "source_rank": source_rank,
                      "eligible": judge["eligible"], "old_commit_votes": judge["old_commit_votes"],
                      "n_judge_votes": judge["n_judge_votes"]})
        if not judge["eligible"]:
            continue
        if "</think>" in (row.get("cot") or ""):
            raise ValueError(f"source CoT unexpectedly contains </think>: {cid}")
        manifest.append({
            "case_id": cid,
            "source": label,
            "source_rank": source_rank,
            "source_path": path,
            "source_line": item["line"],
            "source_row_sha256": item["raw_sha256"],
            "cot_sha256": _sha(row.get("cot") or ""),
            "source_answer_sha256": _sha(row.get("answer") or ""),
            "source_cot_chars": len(row.get("cot") or ""),
            **{k: judge[k] for k in ("judge_source", "judge_votes", "old_commit_votes", "n_judge_votes")},
        })
    if len(order) != 33 or len(manifest) != 18:
        raise AssertionError(f"frozen X1 population drift: unique={len(order)} eligible={len(manifest)}")
    return manifest, audit


def canonical_lines(rows):
    return [json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for r in rows]


def check_manifest(path, expected):
    actual = [json.loads(line) for line in open(_abs(path), encoding="utf-8") if line.strip()]
    if actual != expected:
        for i, (a, e) in enumerate(zip(actual, expected), 1):
            if a != e:
                raise SystemExit(f"manifest mismatch at row {i}: case actual={a.get('case_id')} expected={e.get('case_id')}")
        raise SystemExit(f"manifest length mismatch: actual={len(actual)} expected={len(expected)}")
    print(f"PASS X1 manifest: {len(actual)} eligible rows, hierarchy/source hashes unchanged")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", nargs="?", const=DEFAULT_MANIFEST,
                    help="verify a tracked manifest (default data/x1_replay_manifest.jsonl)")
    ap.add_argument("--audit", action="store_true", help="print all 33 selection decisions to stderr")
    args = ap.parse_args()
    manifest, audit = build_manifest()
    if args.audit:
        for row in audit:
            print(json.dumps(row, ensure_ascii=False, sort_keys=True), file=sys.stderr)
    if args.check:
        check_manifest(args.check, manifest)
    else:
        for line in canonical_lines(manifest):
            print(line)


if __name__ == "__main__":
    main()
