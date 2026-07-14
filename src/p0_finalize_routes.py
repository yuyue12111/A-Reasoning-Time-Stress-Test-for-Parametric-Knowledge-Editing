"""Finalize the corrected P0 route taxonomy after all rescued rows receive neutral route votes."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os

import p0_membership as p0


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUTES = ("Reflective-override", "Bridge", "Recall", "Associative")


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def sha_file(path):
    h = hashlib.sha256()
    with open(_abs(path), "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def route_majority(votes):
    if len(votes) != 3 or any(v not in ROUTES for v in votes):
        raise ValueError(f"expected three valid route votes, got {votes}")
    counts = Counter(votes)
    primary, n = counts.most_common(1)[0]
    if n < 2:
        raise ValueError(f"route 1-1-1 split requires adjudication: {votes}")
    return primary


def route_agreement(items):
    vote_rows = [row["votes"] for row in items]
    n_items, n_raters = len(vote_rows), 3
    total, equal_pairs = Counter(), 0
    unanimous = two_one = 0
    for votes in vote_rows:
        counts = Counter(votes)
        total.update(votes)
        equal_pairs += sum(n * (n - 1) // 2 for n in counts.values())
        unanimous += len(counts) == 1
        two_one += len(counts) == 2
    denominator = n_items * 3
    pbar = equal_pairs / denominator
    pe = sum((total[route] / (n_items * n_raters)) ** 2 for route in ROUTES)
    kappa = (pbar - pe) / (1 - pe) if pe != 1 else None
    return {"unanimous_cases": unanimous, "two_one_cases": two_one,
            "split_1_1_1_cases": n_items - unanimous - two_one,
            "raw_pairwise_agreement": {"equal_pairs": equal_pairs,
                                         "all_pairs": denominator, "rate": pbar},
            "fleiss_kappa": kappa}


def require_frozen_vote_match(item_id, frozen_votes, live_votes):
    """Refuse to reuse a route panel unless it exactly matches the frozen P0 sample.

    The membership sample was created before the P0 answer-only votes and stores the
    three pre-existing route votes for every candidate.  Re-reading a mutable/live
    aggregation file without this comparison would make the final taxonomy depend on
    whatever happened to be on disk at finalize time.
    """
    frozen = list(frozen_votes or [])
    live = list(live_votes or [])
    if len(frozen) != 3 or any(v not in ROUTES for v in frozen):
        raise ValueError(f"{item_id}: invalid frozen existing_route_votes={frozen!r}")
    if len(live) != 3 or any(v not in ROUTES for v in live):
        raise ValueError(f"{item_id}: invalid live route votes={live!r}")
    if live != frozen:
        raise ValueError(
            f"{item_id}: live route votes differ from frozen membership sample: "
            f"frozen={frozen!r}, live={live!r}")
    return live


def load_rescue_votes(paths, expected_ids, merged_out):
    by_judge = []
    source = {}
    for judge, path in zip(("J1", "J2", "J3"), paths):
        rows = p0.read_jsonl_strict(path, judge, exact_keys=("item_id", "judgement"))
        p0.require_same_item_order(expected_ids, rows, judge)
        if len(rows) != len(expected_ids):
            raise ValueError(f"{judge}: expected {len(expected_ids)} rows, got {len(rows)}")
        for i, row in enumerate(rows):
            judgement = row["judgement"]
            if judgement.get("primary") not in ROUTES:
                raise ValueError(f"{judge}:{i + 1}: invalid route {judgement.get('primary')!r}")
            if judgement.get("in_population") is not True or judgement.get("commits_new") is True:
                raise ValueError(f"{judge}:{i + 1}: route judge contradicted frozen OLD membership")
        by_judge.append(rows)
        source[judge] = {"path": path, "sha256": sha_file(path)}

    with open(_abs(merged_out), "w", encoding="utf-8") as f:
        for i, item_id in enumerate(expected_ids):
            votes = [{"judge": judge, **by_judge[j][i]["judgement"]}
                     for j, judge in enumerate(("J1", "J2", "J3"))]
            f.write(json.dumps({"item_id": item_id, "votes": votes}, ensure_ascii=False) + "\n")
    return by_judge, source


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--membership-audit", default="results/p0_membership_audit.json")
    ap.add_argument("--judge1", default="results/p0_route_judge1.jsonl")
    ap.add_argument("--judge2", default="results/p0_route_judge2.jsonl")
    ap.add_argument("--judge3", default="results/p0_route_judge3.jsonl")
    ap.add_argument("--rescue-verdicts", default="results/p0_route_rescue_verdicts.jsonl")
    ap.add_argument("--a3-routes", default="results/a3_neutral/verdicts_all.jsonl")
    ap.add_argument("--b16-routes", default="results/b16_verdicts.json")
    ap.add_argument("--out", default="results/p0_corrected_taxonomy.json")
    args = ap.parse_args()

    membership = json.load(open(_abs(args.membership_audit), encoding="utf-8"))
    if membership["summary"].get("technical_status") != "PASS":
        raise ValueError("membership technical audit is not PASS")
    rows = membership["rows"]
    rescue_rows = [row for row in rows if row["route_action"] == "rejudge_route"]
    rescue_ids = [row["item_id"] for row in rescue_rows]
    judge_paths = [args.judge1, args.judge2, args.judge3]
    rescue_judges, rescue_sources = load_rescue_votes(
        judge_paths, rescue_ids, args.rescue_verdicts)

    a3 = {(str(row["scale"]).lower(), row["case_id"]): row for row in
          (json.loads(line) for line in open(_abs(args.a3_routes))
           if line.strip())}
    b16 = {(row["cell"], row["case_id"]): row for row in
           json.load(open(_abs(args.b16_routes), encoding="utf-8"))["result"]["per_chain"]}

    final = []
    for row in rows:
        if row["route_action"] == "reuse_route":
            if row["pool"] == "a3":
                live_votes = [vote.get("primary") for vote in
                              a3[(row["cell"], row["case_id"])]["votes"]]
            else:
                live_votes = list(b16[(row["cell"], row["case_id"])]["votes"])
            votes = require_frozen_vote_match(
                row["item_id"], row.get("existing_route_votes"), live_votes)
            source = "reused_preexisting_neutral_route_votes"
        elif row["route_action"] == "rejudge_route":
            i = rescue_ids.index(row["item_id"])
            votes = [judge[i]["judgement"]["primary"] for judge in rescue_judges]
            source = "fresh_p0_rescue_neutral_route_votes"
        else:
            continue
        final.append({"item_id": row["item_id"], "pool": row["pool"], "cell": row["cell"],
                      "case_id": row["case_id"], "vote_source": source,
                      "votes": votes, "primary": route_majority(votes)})

    counts = Counter(row["primary"] for row in final)
    per_cell = defaultdict(Counter)
    for row in final:
        per_cell[(row["pool"], row["cell"])][row["primary"]] += 1
    per_cell_rows = [{"pool": pool, "cell": cell,
                      "n": sum(c.values()),
                      "dist": {route: c[route] for route in ROUTES}}
                     for (pool, cell), c in sorted(per_cell.items())]
    result = {
        "status": "PASS", "corrected_taxonomy_status": "COMPLETE",
        "n_members": len(final),
        "dist": {route: counts[route] for route in ROUTES},
        "pct": {route: counts[route] / len(final) for route in ROUTES},
        "agreement": route_agreement(final),
        "per_pool_cell": per_cell_rows,
        "items": final,
        "source": {
            "membership_audit": {"path": args.membership_audit,
                                  "sha256": sha_file(args.membership_audit)},
            "reused_route_inputs": {
                "a3_neutral": {"path": args.a3_routes,
                               "sha256": sha_file(args.a3_routes)},
                "b16": {"path": args.b16_routes,
                        "sha256": sha_file(args.b16_routes)},
                "frozen_vote_lock": {
                    "status": "PASS",
                    "n_reused": sum(row["route_action"] == "reuse_route" for row in rows),
                    "rule": "live three-vote sequence must exactly equal membership-sample existing_route_votes",
                },
            },
            "rescue_judges": rescue_sources,
            "rescue_verdicts": {"path": args.rescue_verdicts,
                                  "sha256": sha_file(args.rescue_verdicts)},
        },
        "official_x1_gate": "UNCHANGED: preregistered 9/18 FAIL",
        "claim_ceiling": ("This is the final post-hoc corrected route taxonomy for the frozen 101-item "
                          "candidate pool after answer-only membership gating. It does not modify X1 or "
                          "authorize case filtering/five-arm continuation."),
    }
    json.dump(result, open(_abs(args.out), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(json.dumps({k: result[k] for k in
                      ("status", "corrected_taxonomy_status", "n_members", "dist", "pct", "agreement")},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
