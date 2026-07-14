"""Hard preflight: prove the historical X1 sampling export is the seed-2 arm.

The old extractor keyed sample rows only by case/budget, so seeds 0→1→2 overwrote one another.
This script reconstructs the reversion pool from raw F3 shards with an explicit seed=2 filter and
requires exact case-id, CoT, and answer equality with ``data/reverted_32b_samp.jsonl``.
"""
import argparse
import glob
import hashlib
import json
import os

import yaml

import metrics


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_seed_records(cfg, editor="ROME", seed=2):
    ds = cfg["dataset"]
    pat = os.path.join(_abs(cfg["out_dir"]), f"{cfg['model_tag']}_{editor}_{ds['tag']}_r*.jsonl")
    shards = sorted(glob.glob(pat))
    if not shards:
        raise FileNotFoundError(f"raw F3 shards missing: {pat}")
    by_case = {}
    duplicates = []
    for shard in shards:
        for lineno, line in enumerate(open(shard, encoding="utf-8"), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("_meta") or row.get("error") or row.get("probe") != "efficacy":
                continue
            if row.get("decode") != "sample" or row.get("seed") != seed:
                continue
            if row.get("budget") not in ("B0", "B3"):
                continue
            key = (row["case_id"], row["budget"])
            if key in by_case:
                duplicates.append({"key": key, "shard": shard, "line": lineno})
            by_case[key] = row
    if duplicates:
        raise ValueError(f"duplicate explicit-seed rows: {duplicates[:5]}")
    nested = {}
    for (cid, budget), row in by_case.items():
        nested.setdefault(cid, {})[budget] = row
    return shards, nested


def reconstruct(cfg, seed=2):
    ds = cfg["dataset"]
    source = ds.get("fallback_path", ds["path"])
    cases = {c["case_id"]: c for c in (json.loads(line) for line in open(_abs(source), encoding="utf-8"))}
    aliases = json.load(open(_abs("data/aliases.json"), encoding="utf-8"))
    shards, by_case = load_seed_records(cfg, seed=seed)
    out = {}
    for cid, recs in by_case.items():
        if "B0" not in recs or "B3" not in recs or cid not in cases:
            continue
        c = cases[cid]
        a0, a3 = recs["B0"].get("answer") or "", recs["B3"].get("answer") or ""
        if not (metrics.hit(a0, c["o_new"], aliases) and not metrics.hit(a0, c["o_old"], aliases)):
            continue
        if not metrics.hit(a3, c["o_old"], aliases):
            continue
        out[cid] = {"cot": recs["B3"].get("cot") or "", "answer": a3,
                    "b0_answer": a0, "seed": recs["B3"].get("seed")}
    return shards, out


def verify(config_path, historical_path, seed=2):
    cfg = yaml.safe_load(open(_abs(config_path), encoding="utf-8"))
    shards, reconstructed = reconstruct(cfg, seed=seed)
    historical = {r["case_id"]: r for r in
                  (json.loads(line) for line in open(_abs(historical_path), encoding="utf-8") if line.strip())}
    missing = sorted(set(historical) - set(reconstructed))
    extra = sorted(set(reconstructed) - set(historical))
    different = []
    for cid in sorted(set(historical) & set(reconstructed)):
        h, r = historical[cid], reconstructed[cid]
        if (h.get("cot") or "", h.get("answer") or "") != (r["cot"], r["answer"]):
            different.append(cid)
    status = "PASS" if not missing and not extra and not different and len(historical) == 14 else "FAIL"
    return {
        "status": status,
        "expected_seed": seed,
        "historical_rows": len(historical),
        "reconstructed_rows": len(reconstructed),
        "matched_rows": len(historical) - len(missing) - len(different),
        "missing": missing,
        "extra": extra,
        "different_cot_or_answer": different,
        "config": config_path,
        "config_sha256": sha256_file(_abs(config_path)),
        "historical": historical_path,
        "historical_sha256": sha256_file(_abs(historical_path)),
        "raw_shards": shards,
        "claim": "historical export is the explicit F3 sample seed-2 reversion pool",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="experiments/probe32b_sample.yaml")
    ap.add_argument("--historical", default="data/reverted_32b_samp.jsonl")
    ap.add_argument("--seed", type=int, default=2)
    ap.add_argument("--out", default="results/x1_sample_source_audit.json")
    args = ap.parse_args()
    result = verify(args.config, args.historical, args.seed)
    out = _abs(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(result, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

