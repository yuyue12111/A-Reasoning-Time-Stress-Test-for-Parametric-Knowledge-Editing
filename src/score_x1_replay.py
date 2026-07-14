"""Score X1 replay outputs, emit blinded answer-only judge prompts, and aggregate the frozen gate."""
import argparse
import glob
import json
import math
import os

import yaml

import metrics
from revert_judge import build_prompt


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def read_full(config_path):
    cfg = yaml.safe_load(open(_abs(config_path), encoding="utf-8"))
    manifest = [json.loads(line) for line in open(_abs(cfg["manifest"]), encoding="utf-8") if line.strip()]
    tag = cfg["tag"]
    pat = os.path.join(_abs(cfg["out_dir"]), f"{cfg['model_tag']}_ROME_{tag}_r*of4.jsonl")
    rows = {}
    for shard in sorted(glob.glob(pat)):
        for line in open(shard, encoding="utf-8"):
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("status") == "ok":
                rows[rec["case_id"]] = rec
    return cfg, manifest, rows


def rule_rows(config_path):
    cfg, manifest, rows = read_full(config_path)
    aliases = json.load(open(_abs("data/aliases.json"), encoding="utf-8"))
    out = []
    for m in manifest:
        cid = m["case_id"]
        r = rows.get(cid)
        if not r:
            out.append({"case_id": cid, "missing": True, "b0_strict": False,
                        "replay_old_loose": False, "replay_old_strict": False, "replay_both": False})
            continue
        s, old, new = r.get("s") or "", r["o_old"], r["o_new"]
        clean = lambda x: metrics._without_subject(x or "", s)
        b0, replay = clean(r.get("b0_answer")), clean(r.get("replay_answer"))
        b0_old, b0_new = bool(metrics.hit(b0, old, aliases)), bool(metrics.hit(b0, new, aliases))
        rp_old, rp_new = bool(metrics.hit(replay, old, aliases)), bool(metrics.hit(replay, new, aliases))
        out.append({
            "case_id": cid, "missing": False, "o_old": old, "o_new": new,
            "replay_answer": r.get("replay_answer") or "",
            "b0_strict": bool(b0_new and not b0_old),
            "replay_old_loose": rp_old,
            "replay_old_strict": bool(rp_old and not rp_new),
            "replay_both": bool(rp_old and rp_new),
            "source": r.get("source"), "cot_sha256": r.get("cot_sha256"),
        })
    return cfg, out


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return [None, None]
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(max(0, center - half), 4), round(min(1, center + half), 4)]


def emit(args):
    _, rows = rule_rows(args.config)
    os.makedirs(os.path.dirname(_abs(args.out_sample)), exist_ok=True)
    with open(_abs(args.out_sample), "w", encoding="utf-8") as fs, \
            open(_abs(args.out_prompts), "w", encoding="utf-8") as fp:
        for row in rows:
            fs.write(json.dumps(row, ensure_ascii=False) + "\n")
            prompt_row = {"o_old": row.get("o_old"), "o_new": row.get("o_new"),
                          "answer": row.get("replay_answer") or ""}
            fp.write(json.dumps({"case_id": row["case_id"], "prompt": build_prompt(prompt_row)},
                                ensure_ascii=False) + "\n")
    n = len(rows)
    b0 = sum(r["b0_strict"] for r in rows)
    loose = sum(r["b0_strict"] and r["replay_old_loose"] for r in rows)
    strict = sum(r["b0_strict"] and r["replay_old_strict"] for r in rows)
    print(f"# X1 n={n}; fresh-B0 strict={b0}/{n}; rule conjunction loose={loose}/{n}, strict={strict}/{n}")
    print(f"# judge prompts -> {args.out_prompts}; frozen sample -> {args.out_sample}")


def load_verdicts(path):
    out = {}
    for line in open(_abs(path), encoding="utf-8"):
        if not line.strip():
            continue
        rec = json.loads(line)
        out[rec["case_id"]] = rec.get("votes") or []
    return out


def aggregate(args):
    sample = [json.loads(line) for line in open(_abs(args.sample), encoding="utf-8") if line.strip()]
    votes = load_verdicts(args.verdicts)
    per_case, success = [], 0
    for row in sample:
        valid = [v for v in votes.get(row["case_id"], [])
                 if v.get("committed") in ("old", "new", "neither")]
        counts = {label: sum(v.get("committed") == label for v in valid)
                  for label in ("old", "new", "neither")}
        judge_old = len(valid) >= 2 and counts["old"] >= 2
        ok = bool(row.get("b0_strict") and judge_old)
        success += int(ok)
        per_case.append({"case_id": row["case_id"], "b0_strict": bool(row.get("b0_strict")),
                         "n_valid_votes": len(valid), "vote_counts": counts,
                         "judge_old_majority": judge_old, "success": ok,
                         "rule_old_loose": bool(row.get("replay_old_loose")),
                         "rule_old_strict": bool(row.get("replay_old_strict")),
                         "rule_both": bool(row.get("replay_both"))})
    n = len(sample)
    required = math.ceil(0.8 * n)
    status = "PASS" if n == 18 and success >= required else "FAIL"
    result = {
        "status": status,
        "n_frozen": n, "success": success, "required": required,
        "success_rate": round(success / n, 4) if n else None,
        "wilson95": wilson(success, n),
        "b0_strict": sum(r["b0_strict"] for r in per_case),
        "judge_old_majority": sum(r["judge_old_majority"] for r in per_case),
        "rule_conjunction_loose": sum(r["b0_strict"] and r["rule_old_loose"] for r in per_case),
        "rule_conjunction_strict": sum(r["b0_strict"] and r["rule_old_strict"] for r in per_case),
        "both_answers": sum(r["rule_both"] for r in per_case),
        "insufficient_judge_votes": sum(r["n_valid_votes"] < 2 for r in per_case),
        "per_case": per_case,
        "claim_ceiling": ("PASS validates the fixed-replay vehicle only; it is not evidence for semantic sufficiency or natural mediation."
                          if status == "PASS" else
                          "FAIL invalidates this fixed-replay vehicle for the planned five-arm study; it does not refute chain-semantic effects in general."),
    }
    os.makedirs(os.path.dirname(_abs(args.out)), exist_ok=True)
    json.dump(result, open(_abs(args.out), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    e = sub.add_parser("emit")
    e.add_argument("--config", default="experiments/x1_replay.yaml")
    e.add_argument("--out-sample", default="results/x1_replay_judge_sample.jsonl")
    e.add_argument("--out-prompts", default="results/x1_replay_judge_prompts.jsonl")
    a = sub.add_parser("aggregate")
    a.add_argument("--sample", default="results/x1_replay_judge_sample.jsonl")
    a.add_argument("--verdicts", required=True)
    a.add_argument("--out", default="results/x1_replay_gate.json")
    args = ap.parse_args()
    (emit if args.mode == "emit" else aggregate)(args)


if __name__ == "__main__":
    main()
