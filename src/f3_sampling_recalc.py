"""Correct CPU-only recalculation for the F3 multi-seed sampling arm.

The legacy scorer flattened sample rows and used the first B0 row of a case as
the gate for every B3 seed; its paired ES-drop also kept only ``rows[0]``.
This module instead:

1. requires unique ``(case_id, seed, budget)`` efficacy rows;
2. pairs B0 and B3 within the same seed;
3. applies the B0-success gate to that same seed;
4. averages paired seeds within each case; and
5. bootstraps unique cases, never seed rows.

It is intentionally independent of ``metrics.score``/``drop_bootstrap`` but
reuses the canonical text matcher and subject scrub from ``metrics``.

Server usage::

    python src/f3_sampling_recalc.py \
      --config experiments/probe32b_sample.yaml --editor ROME \
      --boot 10000 --out results/f3_sampling_recalc.json \
      --include-case-summaries
"""

import argparse
import collections
import glob
import hashlib
import json
import os
import random

import yaml

import metrics


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRIC_NAMES = ("ES_B0", "ES_B3", "ES_drop", "RR_B3", "RRs_B3", "CLR_B0", "CLR_B3")


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _mean(values):
    return sum(values) / len(values) if values else None


def _rounded(value):
    return round(value, 6) if isinstance(value, float) else value


def select_cases(path, dataset_cfg, seed=42):
    """Match ``run_pilot.select_cases`` without importing the GPU runner."""
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    wanted = dataset_cfg.get("case_ids")
    if wanted:
        if len(wanted) != len(set(wanted)):
            raise ValueError("dataset.case_ids contains duplicates")
        by_id = {row["case_id"]: row for row in rows}
        missing = [cid for cid in wanted if cid not in by_id]
        if missing:
            raise ValueError(f"dataset.case_ids missing from source: {missing}")
        if dataset_cfg.get("n") not in (None, len(wanted)):
            raise ValueError("dataset.n must be absent or equal len(dataset.case_ids)")
        return [by_id[cid] for cid in wanted]
    random.Random(seed).shuffle(rows)
    n = dataset_cfg.get("n")
    return rows[:n] if n else rows


def resolve_inputs(config_path, editor, aliases_path="data/aliases.json", tag_suffix="", seeds=None):
    config_path = _abs(config_path)
    cfg = yaml.safe_load(open(config_path, encoding="utf-8"))
    ds = cfg["dataset"]
    primary = _abs(ds["path"])
    fallback = _abs(ds.get("fallback_path", ds["path"]))
    dataset_path = primary if os.path.exists(primary) else fallback
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"dataset not found: {primary} or {fallback}")
    cases = select_cases(dataset_path, ds, cfg.get("seed", 42))
    cmap = {row["case_id"]: row for row in cases}
    if len(cmap) != len(cases):
        raise ValueError("selected dataset contains duplicate case_id")

    sampling = cfg.get("sampling") or {}
    expected_seeds = list(seeds if seeds is not None else sampling.get("seeds", []))
    if not expected_seeds:
        raise ValueError("no sampling seeds configured; pass --seeds or use sampling.seeds")
    if len(expected_seeds) != len(set(expected_seeds)):
        raise ValueError(f"duplicate expected seeds: {expected_seeds}")

    tag = ds["tag"] + tag_suffix
    pattern = os.path.join(_abs(cfg["out_dir"]), f"{cfg['model_tag']}_{editor}_{tag}_r*.jsonl")
    shards = sorted(glob.glob(pattern))
    if not shards:
        raise FileNotFoundError(f"no result shards: {pattern}")
    aliases_path = _abs(aliases_path)
    aliases = json.load(open(aliases_path, encoding="utf-8"))
    return {
        "cfg": cfg,
        "config_path": config_path,
        "dataset_path": dataset_path,
        "cases": cases,
        "cmap": cmap,
        "expected_seeds": expected_seeds,
        "shards": shards,
        "aliases": aliases,
        "aliases_path": aliases_path,
        "glob": pattern,
    }


def collect_sample_rows(shards, expected_case_ids, expected_seeds, base="B0", target="B3"):
    """Collect matching rows and retain every occurrence for duplicate auditing."""
    expected_case_ids = set(expected_case_ids)
    expected_seeds = set(expected_seeds)
    occurrences = collections.defaultdict(list)
    audit = {
        "json_rows": 0,
        "meta_rows": 0,
        "error_rows": [],
        "ignored_rows": 0,
        "unexpected_case_rows": [],
        "unexpected_seed_rows": [],
        "unexpected_budget_rows": 0,
    }
    order = 0
    for shard in shards:
        for lineno, raw in enumerate(open(shard, encoding="utf-8"), 1):
            if not raw.strip():
                continue
            audit["json_rows"] += 1
            row = json.loads(raw)
            if row.get("_meta"):
                audit["meta_rows"] += 1
                continue
            if row.get("error"):
                audit["error_rows"].append({
                    "file": shard, "line": lineno, "case_id": row.get("case_id"),
                    "error": row.get("error"),
                })
                continue
            if row.get("decode", "greedy") != "sample" or row.get("probe") != "efficacy":
                audit["ignored_rows"] += 1
                continue
            cid = row.get("case_id")
            budget = row.get("budget")
            seed = row.get("seed")
            if cid not in expected_case_ids:
                audit["unexpected_case_rows"].append(
                    {"file": shard, "line": lineno, "case_id": cid, "seed": seed, "budget": budget})
                continue
            if seed not in expected_seeds:
                audit["unexpected_seed_rows"].append(
                    {"file": shard, "line": lineno, "case_id": cid, "seed": seed, "budget": budget})
                continue
            if budget not in (base, target):
                audit["unexpected_budget_rows"] += 1
                continue
            order += 1
            key = (cid, seed, budget)
            occurrences[key].append({
                "row": row, "file": shard, "line": lineno, "order": order,
                "row_sha256": hashlib.sha256(raw.rstrip("\r\n").encode("utf-8")).hexdigest(),
            })
    return occurrences, audit


def _row_indicators(row, case, aliases):
    subject = case.get("s") or ""
    answer = metrics._without_subject(row.get("answer", ""), subject)
    cot = metrics._without_subject(row.get("cot", ""), subject)
    hit_new = bool(metrics.hit(answer, case["o_new"], aliases))
    hit_old = bool(metrics.hit(answer, case["o_old"], aliases))
    return {
        "ES": int(hit_new and not hit_old),
        "hit_old": int(hit_old),
        "RRs": int(hit_old and not hit_new),
        "CLR": int(bool(metrics.hit(cot, case["o_old"], aliases))),
    }


def _case_summary(cid, seeds, rows, cmap, aliases, base, target):
    per_seed = []
    for seed in seeds:
        b0 = rows[(cid, seed, base)]["row"]
        bt = rows[(cid, seed, target)]["row"]
        i0 = _row_indicators(b0, cmap[cid], aliases)
        it = _row_indicators(bt, cmap[cid], aliases)
        b0ok = bool(i0["ES"])
        per_seed.append({
            "seed": seed,
            "ES_B0": i0["ES"],
            "ES_B3": it["ES"],
            "ES_drop": i0["ES"] - it["ES"],
            "RR_B3": it["hit_old"] if b0ok else None,
            "RRs_B3": it["RRs"] if b0ok else None,
            "CLR_B0": i0["CLR"],
            "CLR_B3": it["CLR"],
            "b0ok": b0ok,
        })
    summary = {
        "case_id": cid,
        "seeds": list(seeds),
        "n_complete_seed_pairs": len(per_seed),
        "n_b0ok_seed_pairs": sum(int(row["b0ok"]) for row in per_seed),
        "per_seed": per_seed,
    }
    for metric in METRIC_NAMES:
        values = [row[metric] for row in per_seed if row[metric] is not None]
        summary[metric] = _mean(values)
    return summary


def _bootstrap_metric(case_summaries, metric, n_boot=10000, seed=42, ci=0.95):
    rows = [row for row in case_summaries if row.get(metric) is not None]
    if not rows:
        return None
    values = [row[metric] for row in rows]
    point = _mean(values)
    if n_boot:
        rng = random.Random(seed)
        n = len(values)
        means = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(n_boot))
        lo_q, hi_q = (1 - ci) / 2, (1 + ci) / 2
        interval = [means[int(lo_q * n_boot)], means[min(int(hi_q * n_boot), n_boot - 1)]]
    else:
        interval = None
    if metric in ("RR_B3", "RRs_B3"):
        n_seed_pairs = sum(row["n_b0ok_seed_pairs"] for row in rows)
    else:
        n_seed_pairs = sum(row["n_complete_seed_pairs"] for row in rows)
    return {
        "point": _rounded(point),
        "ci95": [_rounded(x) for x in interval] if interval else None,
        "n_cases": len(rows),
        "n_seed_pairs": n_seed_pairs,
        "bootstrap_unit": "case_id",
        "case_value": "mean over same-seed B0/B3 pairs",
    }


def aggregate_cases(case_summaries, n_boot=10000, seed=42):
    return {
        metric: _bootstrap_metric(case_summaries, metric, n_boot=n_boot, seed=seed + i)
        for i, metric in enumerate(METRIC_NAMES)
    }


def per_seed_summary(rows, complete_pairs, cmap, aliases, expected_seeds, base, target):
    out = {}
    for seed in expected_seeds:
        cids = sorted(cid for cid, s in complete_pairs if s == seed)
        summaries = [_case_summary(cid, [seed], rows, cmap, aliases, base, target) for cid in cids]
        out[str(seed)] = {
            "n_cases": len(summaries),
            "n_b0ok_cases": sum(row["n_b0ok_seed_pairs"] for row in summaries),
            "metrics": {metric: _rounded(_mean([row[metric] for row in summaries
                                                  if row[metric] is not None]))
                        for metric in METRIC_NAMES},
        }
    return out


def old_first_row_sensitivity(rows, cmap, aliases, expected_case_ids, expected_seeds, base, target):
    """Reproduce the two legacy first-row choices as an explicit sensitivity."""
    first_seed_hist = {base: collections.Counter(), target: collections.Counter()}
    first_seed_mismatch = []
    first_drop = []
    b0_es_rows = []
    b3_es_rows = []
    b3_clr_rows = []
    rr_rows = []
    rrs_rows = []
    rr_case_ids = set()
    for cid in expected_case_ids:
        b0_entries = [rows[(cid, seed, base)] for seed in expected_seeds if (cid, seed, base) in rows]
        bt_entries = [rows[(cid, seed, target)] for seed in expected_seeds if (cid, seed, target) in rows]
        b0_entries.sort(key=lambda item: item["order"])
        bt_entries.sort(key=lambda item: item["order"])
        for item in b0_entries:
            b0_es_rows.append(_row_indicators(item["row"], cmap[cid], aliases)["ES"])
        for item in bt_entries:
            ind = _row_indicators(item["row"], cmap[cid], aliases)
            b3_es_rows.append(ind["ES"])
            b3_clr_rows.append(ind["CLR"])
        if not b0_entries:
            continue
        first_b0 = b0_entries[0]
        seed0 = first_b0["row"].get("seed")
        first_seed_hist[base][seed0] += 1
        ind0 = _row_indicators(first_b0["row"], cmap[cid], aliases)
        if bt_entries:
            first_bt = bt_entries[0]
            seedt = first_bt["row"].get("seed")
            first_seed_hist[target][seedt] += 1
            indt = _row_indicators(first_bt["row"], cmap[cid], aliases)
            first_drop.append(ind0["ES"] - indt["ES"])
            if seed0 != seedt:
                first_seed_mismatch.append({"case_id": cid, "first_seed_B0": seed0,
                                            "first_seed_target": seedt})
        if ind0["ES"]:
            rr_case_ids.add(cid)
            for item in bt_entries:
                ind = _row_indicators(item["row"], cmap[cid], aliases)
                rr_rows.append(ind["hit_old"])
                rrs_rows.append(ind["RRs"])
    return {
        "definition": ("legacy sensitivity only: first encountered B0 row gates every target seed; "
                       "ES-drop uses first encountered row at each budget"),
        "ES_B0_row_weighted": _rounded(_mean(b0_es_rows)),
        "ES_B3_row_weighted": _rounded(_mean(b3_es_rows)),
        "CLR_B3_row_weighted": _rounded(_mean(b3_clr_rows)),
        "ES_drop_first_row": _rounded(_mean(first_drop)),
        "RR_B3_first_B0_gate_row_weighted": _rounded(_mean(rr_rows)),
        "RRs_B3_first_B0_gate_row_weighted": _rounded(_mean(rrs_rows)),
        "n_drop_cases": len(first_drop),
        "n_rr_gate_cases": len(rr_case_ids),
        "n_rr_target_rows": len(rr_rows),
        "first_seed_histogram": {
            base: {str(k): v for k, v in sorted(first_seed_hist[base].items(), key=lambda kv: str(kv[0]))},
            target: {str(k): v for k, v in sorted(first_seed_hist[target].items(), key=lambda kv: str(kv[0]))},
        },
        "first_seed_mismatch_cases": first_seed_mismatch,
    }


def analyze(shards, cases, aliases, expected_seeds, base="B0", target="B3",
            n_boot=10000, bootstrap_seed=42, include_case_summaries=False):
    cmap = {case["case_id"]: case for case in cases}
    expected_case_ids = [case["case_id"] for case in cases]
    occurrences, row_audit = collect_sample_rows(
        shards, expected_case_ids, expected_seeds, base=base, target=target)

    duplicate_keys = []
    unique_rows = {}
    for key, entries in sorted(occurrences.items()):
        if len(entries) != 1:
            duplicate_keys.append({
                "case_id": key[0], "seed": key[1], "budget": key[2],
                "occurrences": [{k: item[k] for k in ("file", "line", "order", "row_sha256")}
                                for item in entries],
                "byte_identical": len({item["row_sha256"] for item in entries}) == 1,
            })
        else:
            unique_rows[key] = entries[0]

    expected_pairs = [(cid, seed) for cid in expected_case_ids for seed in expected_seeds]
    missing_pairs = []
    complete_pairs = set()
    for cid, seed in expected_pairs:
        missing = [budget for budget in (base, target) if (cid, seed, budget) not in unique_rows]
        if missing:
            missing_pairs.append({"case_id": cid, "seed": seed, "missing_budgets": missing})
        else:
            complete_pairs.add((cid, seed))

    complete_seeds_by_case = {
        cid: [seed for seed in expected_seeds if (cid, seed) in complete_pairs]
        for cid in expected_case_ids
    }
    full_case_ids = [cid for cid in expected_case_ids
                     if complete_seeds_by_case[cid] == list(expected_seeds)]
    available_case_ids = [cid for cid in expected_case_ids if complete_seeds_by_case[cid]]
    coverage_hist = collections.Counter(len(complete_seeds_by_case[cid]) for cid in expected_case_ids)
    seed_coverage = {
        str(seed): {
            base: sum((cid, seed, base) in unique_rows for cid in expected_case_ids),
            target: sum((cid, seed, target) in unique_rows for cid in expected_case_ids),
            "complete_pairs": sum((cid, seed) in complete_pairs for cid in expected_case_ids),
        }
        for seed in expected_seeds
    }
    audit = {
        **row_audit,
        "expected_cases": len(expected_case_ids),
        "expected_seeds": list(expected_seeds),
        "expected_case_seed_pairs": len(expected_pairs),
        "unique_matched_rows": len(unique_rows),
        "duplicate_keys": duplicate_keys,
        "missing_pairs": missing_pairs,
        "complete_case_seed_pairs": len(complete_pairs),
        "cases_with_all_expected_seeds": len(full_case_ids),
        "cases_with_any_complete_pair": len(available_case_ids),
        "complete_seed_count_histogram": {str(k): v for k, v in sorted(coverage_hist.items())},
        "seed_coverage": seed_coverage,
    }

    if duplicate_keys:
        return {"status": "FAIL_DUPLICATE_KEYS", "audit": audit,
                "claim_ceiling": "No estimate is emitted because duplicate case/seed/budget keys are ambiguous."}
    if row_audit["unexpected_case_rows"] or row_audit["unexpected_seed_rows"]:
        return {
            "status": "FAIL_CASE_OR_SEED_DRIFT",
            "audit": audit,
            "claim_ceiling": ("No estimate is emitted because sample rows do not match the frozen "
                              "case/seed set from the config."),
        }

    full_cases = [_case_summary(cid, expected_seeds, unique_rows, cmap, aliases, base, target)
                  for cid in full_case_ids]
    available_cases = [_case_summary(cid, complete_seeds_by_case[cid], unique_rows, cmap, aliases, base, target)
                       for cid in available_case_ids]
    if not full_cases:
        status = "FAIL_NO_FULL_SEED_CASES"
    elif missing_pairs:
        status = "PASS_WITH_MISSING_PAIRS"
    else:
        status = "PASS"
    report = {
        "status": status,
        "protocol": {
            "base_budget": base,
            "target_budget": target,
            "decode": "sample",
            "probe": "efficacy",
            "pair_key": ["case_id", "seed", "budget"],
            "sample_seed_field": "seed",
            "b0_gate": "same case_id and same seed",
            "case_aggregation": "mean over paired seeds",
            "bootstrap_unit": "unique case_id",
            "n_boot": n_boot,
            "bootstrap_seed": bootstrap_seed,
        },
        "audit": audit,
        "primary_complete_cases": {
            "definition": "cases with both budgets for every expected seed",
            "n_cases": len(full_cases),
            "n_seed_pairs": sum(row["n_complete_seed_pairs"] for row in full_cases),
            "metrics": aggregate_cases(full_cases, n_boot=n_boot, seed=bootstrap_seed),
        },
        "available_pair_sensitivity": {
            "definition": "cases with at least one same-seed B0/target pair; case means use available pairs only",
            "n_cases": len(available_cases),
            "n_seed_pairs": sum(row["n_complete_seed_pairs"] for row in available_cases),
            "metrics": aggregate_cases(available_cases, n_boot=n_boot, seed=bootstrap_seed),
        },
        "per_seed_sensitivity": per_seed_summary(
            unique_rows, complete_pairs, cmap, aliases, expected_seeds, base, target),
        "old_first_row_sensitivity": old_first_row_sensitivity(
            unique_rows, cmap, aliases, expected_case_ids, expected_seeds, base, target),
        "claim_ceiling": ("Primary inference is over complete cases with equal seed coverage. Available-pair and "
                          "legacy-first-row results are sensitivities, not replacements for the primary estimand."),
    }
    if include_case_summaries:
        report["case_summaries"] = {
            "primary_complete_cases": full_cases,
            "available_pair_cases": available_cases,
        }
    return report


def _parse_seeds(text):
    if text is None:
        return None
    values = [part.strip() for part in text.split(",") if part.strip()]
    return [int(value) for value in values]


def _compact(report, out_path=None):
    compact = {
        "status": report["status"],
        "audit": {key: report["audit"].get(key) for key in (
            "expected_cases", "expected_seeds", "expected_case_seed_pairs",
            "complete_case_seed_pairs", "cases_with_all_expected_seeds",
            "cases_with_any_complete_pair", "complete_seed_count_histogram",
            "seed_coverage", "duplicate_keys", "missing_pairs", "error_rows",
            "unexpected_case_rows", "unexpected_seed_rows")},
    }
    for key in ("primary_complete_cases", "available_pair_sensitivity",
                "per_seed_sensitivity", "old_first_row_sensitivity"):
        if key in report:
            compact[key] = report[key]
    if out_path:
        compact["out"] = out_path
    return compact


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--editor", default="ROME")
    ap.add_argument("--aliases", default="data/aliases.json")
    ap.add_argument("--tag-suffix", default="")
    ap.add_argument("--seeds", default=None, help="comma-separated override, e.g. 0,1,2")
    ap.add_argument("--base", default="B0")
    ap.add_argument("--target", default="B3")
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--bootstrap-seed", type=int, default=42)
    ap.add_argument("--include-case-summaries", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    try:
        inputs = resolve_inputs(args.config, args.editor, aliases_path=args.aliases,
                                tag_suffix=args.tag_suffix, seeds=_parse_seeds(args.seeds))
    except (FileNotFoundError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED_INPUT", "error": str(exc)},
                         ensure_ascii=False, indent=2))
        return 2
    report = analyze(
        inputs["shards"], inputs["cases"], inputs["aliases"], inputs["expected_seeds"],
        base=args.base, target=args.target, n_boot=args.boot,
        bootstrap_seed=args.bootstrap_seed, include_case_summaries=args.include_case_summaries)
    report["source"] = {
        "config": os.path.relpath(inputs["config_path"], ROOT),
        "config_sha256": _sha256(inputs["config_path"]),
        "dataset": os.path.relpath(inputs["dataset_path"], ROOT),
        "dataset_sha256": _sha256(inputs["dataset_path"]),
        "aliases": os.path.relpath(inputs["aliases_path"], ROOT),
        "aliases_sha256": _sha256(inputs["aliases_path"]),
        "glob": inputs["glob"],
        "shards": [{"path": os.path.relpath(path, ROOT), "sha256": _sha256(path),
                    "bytes": os.path.getsize(path)} for path in inputs["shards"]],
    }
    if args.out:
        out_path = _abs(args.out)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write("\n")
        shown_out = os.path.relpath(out_path, ROOT)
    else:
        shown_out = None
    print(json.dumps(_compact(report, shown_out), ensure_ascii=False, indent=2))
    return 0 if report["status"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
