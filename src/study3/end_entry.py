"""Write the Study 3 end-of-generation entry (prereg-arr-addendum-s3.md §4).  Counts and hashes only:
it never scores a row.

    PYTHONPATH=src ~/.venvs/why-rt/bin/python -m study3.end_entry --stopped-at "2026-..-.. ..:.. UTC+8" \\
        [--results results/rt/s3] [--out experiments/rt/s3_end_of_generation.json]
"""
import argparse
import glob
import json
import os
from collections import Counter

from study3.confirm import MIN_COMPLETE_PCT, MODEL, REPO, WORLDS, _p, sha256


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stopped-at", required=True, help="wall-clock time generation stopped (UTC+8)")
    ap.add_argument("--results", default="results/rt/s3")
    ap.add_argument("--out", default="experiments/rt/s3_end_of_generation.json")
    a = ap.parse_args(argv)
    entry = {"stopped_at": a.stopped_at, "worlds": {}, "shards": {}}
    need = {(c, b) for c in ("base", "rome_N") for b in ("B0", "B3")}
    for w in WORLDS:
        if not os.path.exists(_p(w["manifest"])):
            entry["worlds"][w["name"]] = {"status": "not_run", "reason": "manifest does not exist"}
            continue
        with open(_p(w["manifest"])) as fh:
            manifest = [json.loads(l)["case_id"] for l in fh if l.strip()]
        rows, errors, have = Counter(), Counter(), {}
        for cond in ("base", "rome_N"):
            for f in sorted(glob.glob(os.path.join(_p(a.results), f"{MODEL}_{w['run_tag']}_{cond}_r*of*.jsonl"))):
                entry["shards"][os.path.relpath(f, REPO)] = sha256(f)
                with open(f) as fh:
                    for line in fh:
                        r = json.loads(line)
                        if r.get("_meta"):
                            continue
                        if r.get("error"):
                            errors[cond] += 1
                            continue
                        rows["/".join((cond, str(r.get("probe")), str(r.get("budget"))))] += 1
                        if r.get("probe") == "efficacy":
                            have.setdefault(r["case_id"], set()).add((cond, r.get("budget")))
        done = [c for c in manifest if need <= have.get(c, set())]
        entry["worlds"][w["name"]] = {"run_tag": w["run_tag"], "manifest": w["manifest"], "manifest_sha256": sha256(_p(w["manifest"])),
                                      "n_manifest": len(manifest), "n_complete_efficacy": len(done),
                                      "complete": 100 * len(done) >= MIN_COMPLETE_PCT * len(manifest),
                                      "valid_rows": dict(sorted(rows.items())), "error_rows": dict(errors)}
    with open(_p(a.out), "w") as fh:
        json.dump(entry, fh, indent=1)
    print(f"[study3.end_entry] {len(entry['shards'])} shards; " +
          "; ".join(f"{k}: {v.get('n_complete_efficacy', 0)}/{v.get('n_manifest', 0)}" for k, v in entry["worlds"].items()) + f" -> {a.out}")


if __name__ == "__main__":
    main()
