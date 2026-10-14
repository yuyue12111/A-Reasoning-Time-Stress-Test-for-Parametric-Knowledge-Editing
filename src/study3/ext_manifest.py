"""Study 3 extension manifest (prereg-arr-addendum-s3.md §4): in candidate order, every candidate that
qualifies for R1-Distill-Qwen-32B in the extension screen AND is well-known (>= 3 of the 4 probe models'
``old_hit``).  Uses screen decisions only; no edited or reasoning output.

    PYTHONPATH=src ~/.venvs/why-rt/bin/python -m study3.ext_manifest
"""
import json
import os

from rt.pool import write_manifest
from study3.confirm import MODEL, PROBE_MODELS, familiarity, _p

POOL = "experiments/rt/pools/study3"


def main():
    dec = {}
    for tag in (MODEL,) + PROBE_MODELS:
        path = _p(os.path.join(POOL, f"qualify_{tag}.jsonl"))
        if not os.path.exists(path):
            raise SystemExit(f"missing {path}: screen and qualify every model first")
        with open(path) as fh:
            dec[tag] = [json.loads(l) for l in fh if l.strip()]
    order = [d["case_id"] for d in sorted(dec[MODEL], key=lambda d: d["cand_index"])]
    for tag in PROBE_MODELS:
        if {d["case_id"] for d in dec[tag]} != set(order):
            raise SystemExit(f"qualify_{tag}.jsonl does not cover the same 1600 candidates")
    flags = {q: {d["case_id"]: bool(d["old_hit"]) for d in dec[q]} for q in PROBE_MODELS}
    qualified = {d["case_id"] for d in dec[MODEL] if d["qualified"]}
    fam = familiarity(order, MODEL, flags)
    ids = [c for c in order if c in qualified and fam[c][2]]
    sha = write_manifest(_p(os.path.join(POOL, "manifest_r1qwen32b_ext.jsonl")), [{"case_id": c} for c in ids])
    print(f"[study3.ext_manifest] qualified {len(qualified)}, well-known and qualified {len(ids)} -> sha256 {sha[:12]}")


if __name__ == "__main__":
    main()
