"""Score the frozen P1 node×capacity fresh-B0 diagnostic (CPU only)."""
import argparse
import glob
import hashlib
import json
import math
import os
import random
import statistics

import metrics


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODES = ("A", "B")
TOPOLOGIES = ("single", "mp2")
RELOADS = (0, 1, 2)


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def answer_sha(answer):
    return hashlib.sha256((answer or "").encode("utf-8")).hexdigest()


def frozen_manifest():
    rows = [json.loads(line) for line in open(_abs("data/x1_replay_manifest.jsonl")) if line.strip()]
    return rows, {row["case_id"]: row["source"] for row in rows}


def case_map():
    return {row["case_id"]: row for row in
            (json.loads(line) for line in open(_abs("data/counterfact.jsonl")) if line.strip())}


def strict_b0(row, case, aliases):
    answer = metrics._without_subject(row.get("answer", ""), case.get("s") or "")
    old = bool(metrics.hit(answer, case["o_old"], aliases))
    new = bool(metrics.hit(answer, case["o_new"], aliases))
    return int(new and not old)


def result_pattern(node, topology, reload=None, smoke=False):
    suffix = f"node{node}_{topology}_smoke" if smoke else f"node{node}_{topology}_rep{reload}"
    return _abs(f"results/p1/r1qwen32b_ROME_p1_reload_{suffix}_r*of*.jsonl")


def load_cell(node, topology, reload=None, smoke=False):
    aliases = json.load(open(_abs("data/aliases.json")))
    cases = case_map()
    shards = sorted(glob.glob(result_pattern(node, topology, reload, smoke)))
    metas, errors, rows = [], [], {}
    for shard in shards:
        for line in open(shard):
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("_meta"):
                metas.append(rec)
            elif rec.get("error"):
                errors.append(rec)
            elif rec.get("budget") == "B0" and rec.get("probe") == "efficacy" \
                    and rec.get("decode", "greedy") == "greedy":
                if rec["case_id"] in rows:
                    raise ValueError(f"duplicate P1 row: {node}/{topology}/{reload}/{rec['case_id']}")
                case = cases[rec["case_id"]]
                diag = (rec.get("diagnostics") or {}).get("weight_delta")
                rows[rec["case_id"]] = {
                    "strict_b0": strict_b0(rec, case, aliases),
                    "answer": rec.get("answer") or "",
                    "answer_sha256": answer_sha(rec.get("answer") or ""),
                    "weight_delta": diag,
                    "weight_delta_error": (rec.get("diagnostics") or {}).get("weight_delta_error"),
                }
    return {"shards": shards, "metas": metas, "errors": errors, "rows": rows}


def topology_failures(cell, topology):
    failures = []
    if len(cell["metas"]) != len(cell["shards"]):
        failures.append(f"meta/shard mismatch {len(cell['metas'])}/{len(cell['shards'])}")
    for meta in cell["metas"]:
        actual = meta.get("actual_runtime") or {}
        is_mp = bool(actual.get("model_parallel"))
        if topology == "mp2":
            if not is_mp:
                failures.append("mp2 meta says model_parallel=false")
            if len(actual.get("hf_device_map_devices") or []) < 2:
                failures.append("mp2 meta lacks >=2 mapped devices")
        elif is_mp:
            failures.append("single meta says model_parallel=true")
        if not (meta.get("diagnostics") or {}).get("weight_delta"):
            failures.append("weight-delta diagnostics not frozen in meta")
    return failures


def paired_case_diff(A, B, case_ids, n_boot=10000, seed=42):
    ids = [cid for cid in case_ids if cid in A and cid in B]
    diffs = [A[cid] - B[cid] for cid in ids]
    if not ids:
        return {"n_cases": 0}
    point = sum(diffs) / len(diffs)
    rng = random.Random(seed)
    boots = sorted(sum(diffs[rng.randrange(len(diffs))] for _ in diffs) / len(diffs)
                   for _ in range(n_boot))
    return {"n_cases": len(ids), "mean": round(point, 6),
            "ci": [round(boots[int(.025*n_boot)], 6),
                   round(boots[min(int(.975*n_boot), n_boot-1)], 6)]}


def numeric_summary(values):
    values = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if not values:
        return {"n": 0}
    return {"n": len(values), "mean": sum(values) / len(values),
            "median": statistics.median(values), "min": min(values), "max": max(values)}


def delta_metric(row, metric):
    return (((row.get("weight_delta") or {}).get("aggregate") or {}).get(metric))


def normalized_meta(meta):
    runtime = dict(meta.get("actual_runtime") or {})
    for key in ("parameter_device", "model_parallel", "hf_device_map_counts",
                "hf_device_map_devices", "edit_weight_devices"):
        runtime.pop(key, None)
    env = dict(meta.get("runtime_env") or {})
    for key in ("CUDA_VISIBLE_DEVICES", "WHYAAAI_DEVICE_MAP"):
        env.pop(key, None)
    return {"code_sha256": meta.get("code_sha256"), "software": meta.get("software"),
            "runtime_common": runtime, "runtime_env_common": env}


def weight_diagnostic_failures(row):
    wd = row.get("weight_delta") or {}
    failures = []
    if not isinstance(wd.get("n_weights"), int) or wd.get("n_weights", 0) <= 0:
        failures.append("invalid n_weights")
    if set((wd.get("per_weight") or {})) == set():
        failures.append("missing per_weight")
    for metric in ("delta_l2", "base_l2", "relative_l2", "max_abs_delta"):
        value = (wd.get("aggregate") or {}).get(metric)
        if value is None or not math.isfinite(float(value)):
            failures.append(f"nonfinite {metric}")
        elif metric != "max_abs_delta" and float(value) <= 0:
            failures.append(f"nonpositive {metric}")
    return failures


def summarize_full():
    manifest, sources = frozen_manifest()
    expected = [row["case_id"] for row in manifest]
    cells, failures, warnings = {}, [], []
    for node in NODES:
        for topology in TOPOLOGIES:
            for reload in RELOADS:
                key = f"{node}/{topology}/r{reload}"
                cell = load_cell(node, topology, reload)
                missing = sorted(set(expected) - set(cell["rows"]))
                diag_errors = sorted(cid for cid, row in cell["rows"].items()
                                     if row.get("weight_delta_error") or not row.get("weight_delta"))
                diag_invalid = {cid: weight_diagnostic_failures(row)
                                for cid, row in cell["rows"].items()
                                if weight_diagnostic_failures(row)}
                if len(cell["shards"]) != (8 if topology == "single" else 4):
                    failures.append(f"{key}: shard count {len(cell['shards'])}")
                failures.extend(f"{key}: {msg}" for msg in topology_failures(cell, topology))
                if cell["errors"]:
                    failures.append(f"{key}: {len(cell['errors'])} error rows")
                if missing:
                    failures.append(f"{key}: missing {missing}")
                if diag_errors:
                    failures.append(f"{key}: diagnostic failures {diag_errors}")
                if diag_invalid:
                    warnings.append(f"{key}: invalid extended weight diagnostics {diag_invalid}")
                cells[key] = cell

    weight_extended_ready = all(
        row.get("weight_delta") and not row.get("weight_delta_error")
        and not weight_diagnostic_failures(row)
        for cell in cells.values() for row in cell["rows"].values())

    all_metas = [meta for cell in cells.values() for meta in cell["metas"]]
    normalized = [normalized_meta(meta) for meta in all_metas]

    def signature_count(key):
        return len({json.dumps(meta.get(key), sort_keys=True, ensure_ascii=False)
                    for meta in normalized})

    config_hashes = {topo: {meta.get("config_sha256") for key, cell in cells.items()
                            if f"/{topo}/" in key for meta in cell["metas"]}
                     for topo in TOPOLOGIES}
    weight_name_sets = {tuple(sorted((row.get("weight_delta") or {}).get("per_weight") or {}))
                        for cell in cells.values() for row in cell["rows"].values()}
    config_hash_parity = all(len({x for x in values if x}) == 1 and None not in values
                             for values in config_hashes.values())
    provenance_audit = {
        "code_sha256_signatures": signature_count("code_sha256"),
        "software_signatures": signature_count("software"),
        "model_runtime_common_signatures": signature_count("runtime_common"),
        "runtime_env_common_signatures": signature_count("runtime_env_common"),
        "config_sha256_by_topology": {k: sorted(x for x in v if x) for k, v in config_hashes.items()},
        "weight_name_sets": [list(names) for names in sorted(weight_name_sets)],
        "parity_pass": (signature_count("code_sha256") == 1
                        and signature_count("software") == 1
                        and signature_count("runtime_common") == 1
                        and signature_count("runtime_env_common") == 1
                        and config_hash_parity
                        and len(weight_name_sets) == 1),
        "restore_note": "P1 confirms the existing finally:restore path executed without row errors; it did not record a post-restore numerical checksum."
    }
    if not provenance_audit["parity_pass"]:
        warnings.append("Extended cross-cell provenance/weight-name parity is not exact. "
                        "This descriptive audit does not retroactively overturn the frozen "
                        "technical/behavioral endpoint; inspect provenance_audit before attribution.")

    strict = {key: {cid: row["strict_b0"] for cid, row in cell["rows"].items()}
              for key, cell in cells.items()}
    cell_summary = {}
    for key, vals in strict.items():
        by_source = {}
        for source in sorted(set(sources.values())):
            ids = [cid for cid in expected if sources[cid] == source and cid in vals]
            by_source[source] = {"success": sum(vals[cid] for cid in ids), "n": len(ids),
                                 "rate": sum(vals[cid] for cid in ids) / len(ids) if ids else None}
        diag_rows = [cell["rows"][cid] for cid in expected if cid in cell["rows"]]
        cell_summary[key] = {"success": sum(vals.values()), "n": len(vals),
                             "rate": sum(vals.values()) / len(vals) if vals else None,
                             "by_source": by_source,
                             "weight_delta": {
                                 metric: numeric_summary(delta_metric(row, metric) for row in diag_rows)
                                 for metric in ("delta_l2", "relative_l2", "max_abs_delta")}}

    # Average three reload flags per case, then pair topologies within node.
    topology = {}
    for node in NODES:
        means = {}
        for topo in TOPOLOGIES:
            means[topo] = {cid: sum(strict[f"{node}/{topo}/r{r}"][cid] for r in RELOADS) / 3
                           for cid in expected}
        topology[node] = paired_case_diff(means["mp2"], means["single"], expected)
    pooled_mp2 = {cid: sum(strict[f"{node}/mp2/r{r}"][cid]
                           for node in NODES for r in RELOADS) / 6 for cid in expected}
    pooled_single = {cid: sum(strict[f"{node}/single/r{r}"][cid]
                              for node in NODES for r in RELOADS) / 6 for cid in expected}
    topology["pooled_node_stratified"] = paired_case_diff(pooled_mp2, pooled_single, expected)

    node_effect = {}
    for topo in TOPOLOGIES:
        mean_a = {cid: sum(strict[f"A/{topo}/r{r}"][cid] for r in RELOADS) / 3
                  for cid in expected}
        mean_b = {cid: sum(strict[f"B/{topo}/r{r}"][cid] for r in RELOADS) / 3
                  for cid in expected}
        node_effect[topo] = paired_case_diff(mean_a, mean_b, expected)

    weight_topology, weight_node = {}, {}
    if weight_extended_ready:
        for node in NODES:
            means = {}
            for topo in TOPOLOGIES:
                means[topo] = {
                    cid: sum(delta_metric(cells[f"{node}/{topo}/r{r}"]["rows"][cid], "relative_l2")
                             for r in RELOADS) / 3 for cid in expected}
            weight_topology[node] = paired_case_diff(means["mp2"], means["single"], expected)
        pooled_mp2_w = {cid: sum(delta_metric(cells[f"{node}/mp2/r{r}"]["rows"][cid], "relative_l2")
                                  for node in NODES for r in RELOADS) / 6 for cid in expected}
        pooled_single_w = {cid: sum(delta_metric(cells[f"{node}/single/r{r}"]["rows"][cid], "relative_l2")
                                     for node in NODES for r in RELOADS) / 6 for cid in expected}
        weight_topology["pooled_node_stratified"] = paired_case_diff(
            pooled_mp2_w, pooled_single_w, expected)
        for topo in TOPOLOGIES:
            mean_a = {cid: sum(delta_metric(cells[f"A/{topo}/r{r}"]["rows"][cid], "relative_l2")
                               for r in RELOADS) / 3 for cid in expected}
            mean_b = {cid: sum(delta_metric(cells[f"B/{topo}/r{r}"]["rows"][cid], "relative_l2")
                               for r in RELOADS) / 3 for cid in expected}
            weight_node[topo] = paired_case_diff(mean_a, mean_b, expected)
    else:
        weight_topology = {"status": "unavailable_due_to_invalid_or_missing_diagnostics"}
        weight_node = {"status": "unavailable_due_to_invalid_or_missing_diagnostics"}

    reload_instability = {}
    for node in NODES:
        for topo in TOPOLOGIES:
            k = f"{node}/{topo}"
            unstable_flag, unstable_answer, unstable_weight = [], [], []
            for cid in expected:
                flags = [strict[f"{node}/{topo}/r{r}"][cid] for r in RELOADS]
                hashes = [cells[f"{node}/{topo}/r{r}"]["rows"][cid]["answer_sha256"] for r in RELOADS]
                weights = ([json.dumps(
                    cells[f"{node}/{topo}/r{r}"]["rows"][cid]["weight_delta"]["aggregate"],
                    sort_keys=True) for r in RELOADS] if weight_extended_ready else [])
                if len(set(flags)) > 1:
                    unstable_flag.append(cid)
                if len(set(hashes)) > 1:
                    unstable_answer.append(cid)
                if weights and len(set(weights)) > 1:
                    unstable_weight.append(cid)
            reload_instability[k] = {"strict_flag_changes": unstable_flag,
                                     "answer_hash_changes": unstable_answer,
                                     "weight_delta_changes": unstable_weight}

    case_summary = {}
    for cid in expected:
        records = [cells[f"{node}/{topo}/r{r}"]["rows"][cid]
                   for node in NODES for topo in TOPOLOGIES for r in RELOADS]
        case_summary[cid] = {
            "source": sources[cid],
            "strict_successes_over_12": sum(row["strict_b0"] for row in records),
            "unique_answer_hashes_over_12": len({row["answer_sha256"] for row in records}),
            "answer_exact_across_all_cells": len({row["answer_sha256"] for row in records}) == 1,
            "relative_l2": numeric_summary(delta_metric(row, "relative_l2") for row in records),
        }
    cross_cell_answer = {
        "cases_exact_across_all_12_runs": sum(v["answer_exact_across_all_cells"] for v in case_summary.values()),
        "cases_with_any_cross_cell_difference": [cid for cid, v in case_summary.items()
                                                 if not v["answer_exact_across_all_cells"]],
    }
    all_rows = [row for cell in cells.values() for row in cell["rows"].values()]
    weight_by_strict = {
        label: {metric: numeric_summary(delta_metric(row, metric) for row in all_rows
                                        if row["strict_b0"] == flag)
                for metric in ("delta_l2", "relative_l2", "max_abs_delta")}
        for label, flag in (("failed", 0), ("succeeded", 1))}

    return {"status": "PASS" if not failures else "FAIL", "failures": failures,
            "warnings": warnings,
            "extended_audit_status": "PASS" if not warnings else "WARN",
            "expected_cases": expected, "n_expected_case_edits": 216,
            "cell_summary": cell_summary, "topology_mp2_minus_single": topology,
            "node_A_minus_B": node_effect,
            "weight_relative_l2_mp2_minus_single": weight_topology,
            "weight_relative_l2_node_A_minus_B": weight_node,
            "weight_delta_by_strict_B0": weight_by_strict,
            "provenance_audit": provenance_audit,
            "reload_instability": reload_instability,
            "cross_cell_answer_stability": cross_cell_answer,
            "case_summary": case_summary,
            "claim_ceiling": "Diagnostic only; never changes the preregistered X1 FAIL or authorizes case filtering/five-arm continuation."}


def summarize_smoke(node, topology):
    cell = load_cell(node, topology, smoke=True)
    expected = {"cf_140", "cf_18471"}
    missing = sorted(expected - set(cell["rows"]))
    diag_bad = [cid for cid, row in cell["rows"].items()
                if row.get("weight_delta_error") or not row.get("weight_delta")]
    failures = []
    if cell["errors"]:
        failures.append(f"{len(cell['errors'])} error rows")
    failures.extend(topology_failures(cell, topology))
    if missing:
        failures.append(f"missing {missing}")
    if diag_bad:
        failures.append(f"diagnostics missing {diag_bad}")
    if any(not row.get("answer") for row in cell["rows"].values()):
        failures.append("empty answer")
    return {"status": "PASS" if not failures else "FAIL", "node": node,
            "topology": topology, "failures": failures, "cases": sorted(cell["rows"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--node", choices=NODES)
    ap.add_argument("--topology", choices=TOPOLOGIES)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if args.smoke:
        if not args.node or not args.topology:
            raise SystemExit("--smoke requires --node and --topology")
        result = summarize_smoke(args.node, args.topology)
    else:
        result = summarize_full()
    os.makedirs(os.path.dirname(_abs(args.out)) or ROOT, exist_ok=True)
    json.dump(result, open(_abs(args.out), "w"), ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
