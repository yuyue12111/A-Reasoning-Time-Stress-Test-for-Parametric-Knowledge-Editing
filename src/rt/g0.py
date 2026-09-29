"""G0 engine-parity gate (REVISION.md §4; prereg-arr.md §7).

Compares the engine-v2 rerun of Study 1's R1-Distill-Qwen-32B pool with Study 1 itself:

* PASS criterion 0: the rerun is complete -- at least 198 of Study 1's 200 cases carry both a B0
  and a B3 efficacy row in v2 (error rows are skipped by the loader, so a partial rerun is caught
  here instead of passing on a subset);
* PASS criterion 1: the v2 paired ES drop (B0 → B3, ROME N arm) lies inside Study 1's pre-registered
  95% CI [.030, .182] (fixed: computed once on all 200 Study-1 cases, never on the shared subset);
* PASS criterion 2: per-case ES at B0 agrees with Study 1 on at least 85% of shared cases.

What a failure means and what follows is fixed in REVISION.md §4 (G0 branches), committed before
the verdict was read.  The base-model B0 comparison is not diagnostic of the engine: Study 1's
unedited 32B base most likely ran with BOS, v2's without (REVISION.md §5).

Also reported, not gating: agreement at B3, byte-identical B0 answers, the unedited base's B0
agreement (isolates the generator from the delta pipeline), v2 reversion and retention contrast,
and how v2 chains ended.  Output is one JSON file; the exit code is 0 on PASS, 1 on FAIL.

    PYTHONPATH=src python -m rt.g0 \\
        --study1 'results/probe/r1qwen32b_ROME_cf200_r*of8.jsonl' \\
        --study1-base 'results/probe/r1qwen32b_BASE_cf200_r*.jsonl' \\
        --v2 'results/rt/g0/r1qwen32b_g0_rome_N_r*of8.jsonl' \\
        --v2-base 'results/rt/g0/r1qwen32b_g0_base_r*of8.jsonl' \\
        --out results/rt/g0/g0_verdict.json
"""
import argparse
import glob
import json
import os
import sys
from collections import Counter

from rt import analysis as A

MIN_B0_AGREEMENT = 0.85
MIN_SHARED = 198                 # of Study 1's 200 cases (criterion 0)
STUDY1_CI = (0.030, 0.182)       # Study 1's 95% CI of the 32B ROME N drop, fixed before the verdict


def _files(pattern):
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"no file matches {pattern!r}")
    return files


def _agreement(tab_a, tab_b, budget, key="es"):
    common = sorted(c for c in tab_a if budget in tab_a[c] and c in tab_b and budget in tab_b[c])
    same = sum(tab_a[c][budget][key] == tab_b[c][budget][key] for c in common)
    return {"budget": budget, "key": key, "n": len(common), "agree": same,
            "rate": same / len(common) if common else None}


def verdict(study1_rows, v2_rows, cases, aliases, study1_base=None, v2_base=None,
            min_shared=MIN_SHARED, study1_ci=STUDY1_CI):
    s1_all = A.case_table(study1_rows, cases, aliases)
    v2_all = A.case_table(v2_rows, cases, aliases)
    d1 = A.es_drop(s1_all)                                  # all Study-1 cases, never the subset
    lo, hi = study1_ci if study1_ci is not None else d1["ci95"]
    s1_ids = set(A.paired_cases(s1_all, "B0", "B3"))
    shared = s1_ids & set(A.paired_cases(v2_all, "B0", "B3"))
    s1, v2 = A.restrict(s1_all, shared.__contains__), A.restrict(v2_all, shared.__contains__)
    d2 = A.es_drop(v2)
    b0 = _agreement(s1, v2, "B0")
    out = {
        "study1_es_drop": d1, "study1_ci_used": [lo, hi], "v2_es_drop": d2,
        "completeness": {"study1_paired": len(s1_ids), "shared_paired": len(shared),
                         "missing": sorted(s1_ids - shared)[:20], "min_shared": min_shared},
        "criterion_0_complete": len(shared) >= min_shared,
        "criterion_1_drop_inside_study1_ci": lo <= d2["point"] <= hi,
        "b0_es_agreement": b0,
        "criterion_2_b0_agreement": (b0["rate"] or 0) >= MIN_B0_AGREEMENT,
        "b3_es_agreement": _agreement(s1, v2, "B3"),
        "b0_answer_parity": A.answer_parity(
            [r for r in study1_rows if r["case_id"] in shared], [r for r in v2_rows if r["case_id"] in shared]),
        "v2_rr": A.rr(v2), "v2_rr_strict": A.rr(v2, strict=True),
        "v2_chain_end": dict(Counter(r.get("chain_end") for r in v2_rows
                                     if r["budget"] == "B3" and r["probe"] == "efficacy")),
    }
    if study1_base is not None and v2_base is not None:
        sb = A.case_table(study1_base, cases, aliases)
        vb = A.case_table(v2_base, cases, aliases)
        out["base_b0_old_agreement"] = _agreement(sb, vb, "B0", key="old")
        out["base_note"] = ("not an engine diagnostic: Study 1's unedited base most likely ran with BOS, "
                            "v2's base without (REVISION.md §5)")
        out["v2_retention_contrast"] = A.retention_contrast(v2, vb)
        out["study1_retention_contrast"] = A.retention_contrast(s1, sb)
    out["pass"] = bool(out["criterion_0_complete"] and out["criterion_1_drop_inside_study1_ci"]
                       and out["criterion_2_b0_agreement"])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--study1", required=True)
    ap.add_argument("--v2", required=True)
    ap.add_argument("--study1-base")
    ap.add_argument("--v2-base")
    ap.add_argument("--cases", default="data/counterfact.jsonl")
    ap.add_argument("--aliases", default="data/aliases.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    cases = {c["case_id"]: c for c in (json.loads(l) for l in open(a.cases) if l.strip())}
    aliases = json.load(open(a.aliases))

    def rows(pattern):
        return A.load_rows(_files(pattern))[0] if pattern else None
    res = verdict(rows(a.study1), rows(a.v2), cases, aliases, rows(a.study1_base), rows(a.v2_base))
    res["inputs"] = {k: [A.file_record(f) for f in _files(v)] for k, v in
                     (("study1", a.study1), ("v2", a.v2), ("study1_base", a.study1_base),
                      ("v2_base", a.v2_base)) if v}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1, ensure_ascii=False, default=str)
    d1, d2, b0 = res["study1_es_drop"], res["v2_es_drop"], res["b0_es_agreement"]
    c = res["completeness"]
    print(f"[G0] complete {c['shared_paired']}/{c['study1_paired']} (>= {c['min_shared']})  "
          f"Study 1 drop {d1['point']:.3f} CI used {res['study1_ci_used']}  v2 drop {d2['point']:.3f} {d2['ci95']}  "
          f"B0 agreement {b0['agree']}/{b0['n']}  -> {'PASS' if res['pass'] else 'FAIL'}")
    sys.exit(0 if res["pass"] else 1)


if __name__ == "__main__":
    main()
