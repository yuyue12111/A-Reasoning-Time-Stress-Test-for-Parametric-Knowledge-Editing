"""Technical audit for X1 fixed-chain replay smoke/full outputs."""
import argparse
import glob
import json
import os
import sys

import yaml

import x1_replay


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def validate(config_path, suffix="", expected_n=None, expected_shards=4):
    cfg = yaml.safe_load(open(_abs(config_path), encoding="utf-8"))
    tag = cfg["tag"] + suffix
    pat = os.path.join(_abs(cfg["out_dir"]), f"{cfg['model_tag']}_ROME_{tag}_r*of4.jsonl")
    shards = sorted(glob.glob(pat))
    failures, warnings, metas, successes, errors = [], [], [], {}, []
    if len(shards) != expected_shards:
        failures.append(f"expected {expected_shards} shards, found {len(shards)}: {pat}")
    for shard in shards:
        shard_meta = []
        for lineno, line in enumerate(open(shard, encoding="utf-8"), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("_meta"):
                shard_meta.append(row); metas.append(row); continue
            cid = row.get("case_id")
            if row.get("status") == "error":
                errors.append({"shard": shard, "line": lineno, **row}); continue
            if row.get("status") != "ok" or not cid:
                failures.append(f"malformed data row {shard}:{lineno}"); continue
            if cid in successes:
                failures.append(f"duplicate successful case row: {cid}")
            successes[cid] = row
        if len(shard_meta) != 1:
            failures.append(f"{shard}: expected exactly one _meta, got {len(shard_meta)}")

    manifest = [json.loads(line) for line in open(_abs(cfg["manifest"]), encoding="utf-8") if line.strip()]
    n = expected_n if expected_n is not None else len(manifest)
    expected = manifest[:n]
    expected_ids = {m["case_id"] for m in expected}
    missing, extra = sorted(expected_ids - set(successes)), sorted(set(successes) - expected_ids)
    if missing:
        failures.append(f"missing successful rows: {missing}")
    if extra:
        failures.append(f"unexpected successful rows: {extra}")
    mmap = {m["case_id"]: m for m in expected}
    for cid, row in successes.items():
        if cid not in mmap:
            continue
        m = mmap[cid]
        for key in ("source_path", "source_line", "source_row_sha256", "cot_sha256"):
            if row.get(key) != m.get(key):
                failures.append(f"{cid}: output {key} differs from manifest")
        if not str(row.get("b0_answer") or "").strip():
            failures.append(f"{cid}: empty B0 answer")
        if not str(row.get("replay_answer") or "").strip():
            failures.append(f"{cid}: empty replay answer")
        if not isinstance(row.get("fixed_cot_tokens"), int) or row["fixed_cot_tokens"] <= 0:
            failures.append(f"{cid}: invalid fixed_cot_tokens={row.get('fixed_cot_tokens')!r}")

    current_code = x1_replay.code_sha256()
    config_sha = x1_replay.sha256_file(_abs(config_path))
    manifest_sha = x1_replay.sha256_file(_abs(cfg["manifest"]))
    audit_sha = x1_replay.sha256_file(_abs(cfg["sample_source_audit"]))
    for meta in metas:
        if meta.get("config_sha256") != config_sha:
            failures.append("config SHA mismatch")
        if meta.get("manifest_sha256") != manifest_sha:
            failures.append("manifest SHA mismatch")
        if meta.get("sample_audit_sha256") != audit_sha:
            failures.append("sample audit SHA mismatch")
        if meta.get("code_sha256") != current_code:
            failures.append("X1 harness code SHA mismatch")
        if meta.get("effective_n") != n:
            failures.append(f"effective_n mismatch: {meta.get('effective_n')} != {n}")
        env, actual = meta.get("runtime_env") or {}, meta.get("actual_runtime") or {}
        if env.get("WHYAAAI_DTYPE") != "float32" or env.get("WHYAAAI_NO_BOS") != "1":
            failures.append(f"wrong dtype/NO_BOS runtime: {env}")
        if env.get("WHYAAAI_DEVICE_MAP") != "balanced":
            failures.append(f"WHYAAAI_DEVICE_MAP must be balanced: {env.get('WHYAAAI_DEVICE_MAP')}")
        if actual.get("model_parallel") is not True:
            failures.append("actual runtime did not use model_parallel=true")
        devices = set(actual.get("hf_device_map_devices") or [])
        if not {"0", "1"}.issubset(devices):
            failures.append(f"model not spread across both local GPUs: {sorted(devices)}")
        edit_devices = actual.get("edit_weight_devices") or {}
        if not edit_devices or any(str(v).startswith("ERROR:") for v in edit_devices.values()):
            failures.append(f"invalid editable-weight device audit: {edit_devices}")
        if meta.get("sample_audit_summary") != {
                "status": "PASS", "expected_seed": 2, "historical_rows": 14, "matched_rows": 14}:
            failures.append(f"wrong sample audit summary: {meta.get('sample_audit_summary')}")

    if errors:
        warnings.append(f"{len(errors)} prior error attempts exist; successful outcome-blind reruns may supersede them")
    status = "PASS" if not failures else "FAIL"
    return {"status": status, "failures": failures, "warnings": warnings,
            "tag": tag, "shards": len(shards), "expected_n": n,
            "successful_cases": len(successes), "missing": missing, "errors": len(errors)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="experiments/x1_replay.yaml")
    ap.add_argument("--suffix", default="")
    ap.add_argument("--expected-n", type=int, default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    result = validate(args.config, args.suffix, args.expected_n)
    if args.out:
        os.makedirs(os.path.dirname(_abs(args.out)), exist_ok=True)
        json.dump(result, open(_abs(args.out), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

