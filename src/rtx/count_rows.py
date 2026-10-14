"""Row counts for rt.run shards: counts only, never prints an answer, chain or score.

    python3 src/rtx/count_rows.py "<shard glob>" [--expect N]

Per file: valid rows (no ``error`` field), error rows, distinct valid keys (case, probe, budget, seed);
with ``--expect`` each file must have exactly N valid rows and as many distinct keys (PASS/FAIL).
Lives outside src/rt, so the engine's code_sha256 is unchanged.
"""
import argparse
import glob
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern")
    ap.add_argument("--expect", type=int, default=None)
    a = ap.parse_args()
    files = sorted(glob.glob(a.pattern))
    if not files:
        raise SystemExit(f"no file matches {a.pattern}")
    ok_all = True
    for f in files:
        valid, err, keys = 0, 0, set()
        with open(f) as fh:
            for line in fh:
                if not line.strip():
                    continue
                r = json.loads(line)
                if r.get("_meta") or r.get("_run"):
                    continue
                if r.get("error"):
                    err += 1
                    continue
                valid += 1
                keys.add((r.get("case_id"), r.get("probe"), r.get("budget"), r.get("seed")))
        verdict = ""
        if a.expect is not None:
            ok = valid == a.expect and len(keys) == a.expect
            ok_all &= ok
            verdict = " PASS" if ok else " FAIL"
        print(f"{f.split('/')[-1]}  valid {valid}  errors {err}  keys {len(keys)}{verdict}")
    if a.expect is not None:
        print("ALL PASS" if ok_all else "NOT COMPLETE")


if __name__ == "__main__":
    main()
