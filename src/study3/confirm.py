"""Study 3 confirmatory analysis (prereg-arr-addendum-s3.md §5–§6), frozen with registry entry 8.

    PYTHONPATH=src ~/.venvs/why-rt/bin/python -m study3.confirm \\
        --end experiments/rt/s3_end_of_generation.json --out paperwriting/revision/study3.json

Refuses to run unless the end-of-generation entry exists and lists every shard it reads with a matching
sha256 (addendum §4, stop rule).  Code check on seen data (not a test of anything):

    PYTHONPATH=src ~/.venvs/why-rt/bin/python -m study3.confirm --code-check-on-s2 --out /tmp/check.json

runs the same estimators on the Study 2 32B pool (run tag s2) and must reproduce explore_s1s2 E6
(well-known retention contrast +.242, strict +.091).

Conventions (parent prereg §4–§6, rt.analysis): lexical scoring with the subject scrubbed; 10,000 case
resamples, random.Random(42), cases in sorted case_id order, percentile 95% CI, two-sided p; error rows
skipped; rows of deltas whose rank-1 fit error exceeds 1e-4 excluded; completeness >= 98% of the manifest.
"""
import argparse
import glob
import hashlib
import json
import os
import random
import sys
from collections import Counter

from rt import analysis as A
from rt.study2 import FIT_TOL, read_fit_logs

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL = "r1qwen32b"
# The two sub-worlds of Study 3 (addendum §4).  Case ids are disjoint; the primary test pools the cases
# of every sub-world that meets the completeness rule.
WORLDS = (
    {"name": "fresh", "run_tag": "s3fresh", "manifest": "experiments/rt/pools/study2/manifest_r1qwen32b_fresh.jsonl",
     "qualify_dir": "experiments/rt/pools/study2", "delta_logs": "results/rt/deltas_logs/s3fresh"},
    {"name": "ext", "run_tag": "s3ext", "manifest": "experiments/rt/pools/study3/manifest_r1qwen32b_ext.jsonl",
     "qualify_dir": "experiments/rt/pools/study3", "delta_logs": "results/rt/deltas_logs/s3ext"},
)
RUN_TAG, MANIFEST = WORLDS[0]["run_tag"], WORLDS[0]["manifest"]
QUALIFY = "experiments/rt/pools/study2/qualify_{}.jsonl"
PROBE_MODELS = ("r1qwen1_5b", "r1qwen7b", "r1qwen14b", "r1llama8b")
HIGH_CUT = 0.75
MIN_COMPLETE_PCT = 98
ALPHA = 0.05
MIN_QUARTILE_N = 5


def _p(rel):
    return rel if os.path.isabs(rel) else os.path.join(REPO, rel)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------------------------------------
# Familiarity (addendum §3)
# ---------------------------------------------------------------------------------------------
def familiarity(case_ids, model, flags):
    """{case: (k, m, high)}: k of the m probe models (PROBE_MODELS minus ``model``) whose qualify
    ``old_hit`` is true; high iff k/m >= HIGH_CUT.  A missing flag counts as not known."""
    probes = [q for q in PROBE_MODELS if q != model]
    out = {}
    for c in case_ids:
        k = sum(bool(flags.get(q, {}).get(c, False)) for q in probes)
        out[c] = (k, len(probes), k / len(probes) >= HIGH_CUT)
    return out


def read_flags(models=PROBE_MODELS, qualify_dir="experiments/rt/pools/study2"):
    flags = {}
    for q in models:
        with open(_p(os.path.join(qualify_dir, f"qualify_{q}.jsonl"))) as fh:
            flags[q] = {r["case_id"]: bool(r["old_hit"]) for r in map(json.loads, fh)}
    return flags


# ---------------------------------------------------------------------------------------------
# Per-case values
# ---------------------------------------------------------------------------------------------
def retention_set(E, B, b0="B0", b1="B3"):
    """Sorted cases with all four efficacy rows, base naming o_old at b0 and the edit succeeding at b0."""
    return [c for c in A.paired_cases(E, b0, b1)
            if b0 in B.get(c, {}) and b1 in B[c] and B[c][b0]["old"] and E[c][b0]["es"]]


def retention_values(E, B, cases, strict=False, Ea=None, Ba=None, after="B3"):
    """Per case: edited lost − own lost.  Edited lost = not ES at ``after`` (strict: o_new absent);
    own lost = base answer at ``after`` does not name o_old.  ``Ea``/``Ba`` supply the 'after' rows
    from another probe (paraphrase control); cases without them are skipped."""
    Ea = E if Ea is None else Ea
    Ba = B if Ba is None else Ba
    vals, used = [], []
    for c in cases:
        if after not in Ea.get(c, {}) or after not in Ba.get(c, {}):
            continue
        e = Ea[c][after]
        lost_e = int(not e["new"]) if strict else 1 - e["es"]
        lost_b = 1 - int(Ba[c][after]["old"])
        vals.append(lost_e - lost_b)
        used.append(c)
    return vals, used


def components(E, B, cases, after="B3"):
    el = [1 - E[c][after]["es"] for c in cases]
    bl = [1 - int(B[c][after]["old"]) for c in cases]
    return {"n": len(cases), "edited_loss": A.bootstrap_mean(el) if el else None,
            "own_loss": A.bootstrap_mean(bl) if bl else None}


def slope(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else None


def bootstrap_slope(xs, ys, n_boot=A.N_BOOT, seed=A.SEED):
    """OLS slope of y on x with a case bootstrap in the given (sorted case) order."""
    n = len(xs)
    rr = random.Random(seed).randrange
    boots = []
    for _ in range(n_boot):
        idx = [rr(n) for _ in range(n)]
        s = slope([xs[i] for i in idx], [ys[i] for i in idx])
        if s is not None:
            boots.append(s)
    boots.sort()
    lo, hi = boots[int(.025 * len(boots))], boots[int(.975 * len(boots)) - 1]
    return {"point": slope(xs, ys), "ci95": [lo, hi], "n": n}


def primary_verdict(est):
    """Pass iff two-sided p <= ALPHA and the point estimate is > 0 (parent convention: p <= alpha)."""
    if not est or est.get("point") is None:
        return False
    return bool(est["p"] is not None and est["p"] <= ALPHA and est["point"] > 0)


def wording(status, h5_pass, strict_est):
    """Addendum §7 outcome table -> (title key, abstract variant)."""
    if status != "complete":
        return {"title": "title2", "abstract": "not_run", "rule": "H5 not tested"}
    if not h5_pass:
        return {"title": "title3", "abstract": "not_confirmed", "rule": "H5 failed"}
    if strict_est and strict_est.get("ci95") and strict_est["ci95"][0] > 0:
        return {"title": "title1", "abstract": "confirmed", "rule": "H5 passed; strict-count CI above 0"}
    return {"title": "title2", "abstract": "confirmed_lexical",
            "rule": "H5 passed; strict-count CI includes 0: say 'loses more often than its own answers', not 'undoes'"}


# ---------------------------------------------------------------------------------------------
# End-of-generation gate (addendum §4)
# ---------------------------------------------------------------------------------------------
def check_end_entry(end_path, files):
    if not end_path or not os.path.exists(end_path):
        raise SystemExit("refusing to run: no end-of-generation entry (prereg-arr-addendum-s3.md §4)")
    with open(end_path) as fh:
        entry = json.load(fh)
    listed = entry.get("shards", {})
    bad = []
    for f in files:
        rel = os.path.relpath(f, REPO)
        if listed.get(rel) != sha256(f):
            bad.append(rel)
    if bad:
        raise SystemExit(f"refusing to run: shards missing from or changed since the end-of-generation entry: {bad}")
    return entry


# ---------------------------------------------------------------------------------------------
def load_world(results, run_tag, model, cases, aliases, fit):
    files = {cond: sorted(glob.glob(os.path.join(results, f"{model}_{run_tag}_{cond}_r*of*.jsonl")))
             for cond in ("base", "rome_N")}
    rows = {}
    excl = Counter()
    for cond, fs in files.items():
        if not fs:
            raise SystemExit(f"no shards for {model}/{run_tag}/{cond} under {results}")
        rs, audit = A.load_rows(fs)
        for f in audit["files"]:
            excl["error_rows"] += f["counts"].get("error", 0)
        kept = []
        for r in rs:
            if (r["model_tag"], r["condition"]) != (model, cond):
                raise SystemExit(f"row {r['source']} is not {model}/{cond}")
            if cond == "rome_N":
                err = fit.get(r.get("delta_sha")) if fit is not None else None
                if fit is not None and err is None:
                    excl["rows_without_fit_record"] += 1
                if err is not None and err > FIT_TOL:
                    excl["fit_error_rows"] += 1
                    continue
            kept.append(r)
        rows[cond] = kept
    tabs = {}
    for cond in ("base", "rome_N"):
        for probe in ("efficacy", "para0"):
            tabs[(cond, probe)] = A.case_table(rows[cond], cases, aliases, probe=probe)
    return tabs, [f for fs in files.values() for f in fs], dict(excl)


def lp_index(log_paths):
    idx = {}
    for p in log_paths:
        with open(p) as fh:
            for line in fh:
                r = json.loads(line)
                if r.get("case_id") and r.get("lp_first") and r.get("status") == "ok":
                    idx[r["case_id"]] = r["lp_first"]
    return idx


def analyse(tabs, manifest, fam, lp=None):
    E, B = tabs[("rome_N", "efficacy")], tabs[("base", "efficacy")]
    Ep, Bp = tabs[("rome_N", "para0")], tabs[("base", "para0")]
    complete_cases = [c for c in manifest if c in E and c in B and all(b in E[c] and b in B[c] for b in ("B0", "B3"))]
    pct = 100 * len(complete_cases) / len(manifest) if manifest else 0
    status = "complete" if pct >= MIN_COMPLETE_PCT else "incomplete"
    ret = retention_set(E, B)
    hi = [c for c in ret if fam[c][2]]
    lo = [c for c in ret if not fam[c][2]]
    out = {"completeness": {"n_manifest": len(manifest), "n_complete": len(complete_cases), "pct": pct, "status": status,
                            "missing": sorted(set(manifest) - set(complete_cases))},
           "familiarity": {"n_high": sum(fam[c][2] for c in manifest), "n_low": sum(not fam[c][2] for c in manifest),
                           "retention_high": len(hi), "retention_low": len(lo)}}
    k_lex = A.bootstrap_mean(retention_values(E, B, hi)[0])
    k_strict = A.bootstrap_mean(retention_values(E, B, hi, strict=True)[0])
    h5 = primary_verdict(k_lex) if status == "complete" else False
    out["H5"] = {"estimate": k_lex, "pass": h5, "tested": status == "complete",
                 "definition": "retention contrast within well-known facts (lexical, registered endpoint)"}
    out["wording"] = wording(status, h5, k_strict)
    sec = {}
    sec["K_strict"] = k_strict
    sec["components_high"] = components(E, B, hi)
    sec["components_low"] = components(E, B, lo)
    rl, _ = retention_values(E, B, lo)
    rh, _ = retention_values(E, B, hi)
    sec["RC_low"] = A.bootstrap_mean(rl) if rl else None
    sec["D_high_minus_low"] = A.bootstrap_two_groups(rh, rl)
    # own-answer fragility: base knows the fact at B0 (no edit gate)
    known = [c for c in A.paired_cases(B, "B0", "B3") if B[c]["B0"]["old"]]
    own = lambda cs: [1 - int(B[c]["B3"]["old"]) for c in cs]
    sec["own_loss_low_minus_high"] = A.bootstrap_two_groups(own([c for c in known if not fam[c][2]]),
                                                            own([c for c in known if fam[c][2]]))
    # edited side
    paired = A.paired_cases(E, "B0", "B3")
    drop = lambda cs: [E[c]["B0"]["es"] - E[c]["B3"]["es"] for c in cs]
    ero = lambda cs: [1 - E[c]["B3"]["es"] for c in cs if E[c]["B0"]["es"]]
    sec["ES_drop_high_minus_low"] = A.bootstrap_two_groups(drop([c for c in paired if fam[c][2]]),
                                                           drop([c for c in paired if not fam[c][2]]))
    sec["erosion_given_ES_B0_high_minus_low"] = A.bootstrap_two_groups(ero([c for c in paired if fam[c][2]]),
                                                                       ero([c for c in paired if not fam[c][2]]))
    # dose-response over the retention set
    xs = [fam[c][0] for c in ret]
    ys, _ = retention_values(E, B, ret)
    sec["dose_response_slope"] = bootstrap_slope(xs, ys) if len(set(xs)) > 1 else None
    sec["RC_by_k"] = {k: {"n": sum(1 for x in xs if x == k),
                          "mean": (sum(y for x, y in zip(xs, ys) if x == k) / max(1, sum(1 for x in xs if x == k)))}
                      for k in sorted(set(xs))}
    # paraphrase control: same retention gate, 'after' = para0 at B0 (no thinking) and at B3
    for after in ("B0", "B3"):
        v, used = retention_values(E, B, hi, Ea=Ep, Ba=Bp, after=after)
        sec[f"K_paraphrase_{after}"] = A.bootstrap_mean(v) if v else None
        if after == "B0":
            vt, _ = retention_values(E, B, used)
            sec["K_thinking_minus_K_paraphrase_B0"] = A.bootstrap_mean([a - b for a, b in zip(vt, v)]) if v else None
            sec["paraphrase_B0_components_high"] = {
                "n": len(used), "edited_loss": A.bootstrap_mean([1 - Ep[c]["B0"]["es"] for c in used]) if used else None,
                "own_loss": A.bootstrap_mean([1 - int(Bp[c]["B0"]["old"]) for c in used]) if used else None}
    # robustness: quartiles over the whole manifest
    if lp:
        feats = {"post_edit_margin": lambda d: d["after"]["target"] - d["after"]["o_old"],
                 "base_confidence_old": lambda d: d["before"]["o_old"]}
        for name, g in feats.items():
            vals = sorted(g(lp[c]) for c in manifest if c in lp)
            if len(vals) < 4:
                continue
            cuts = [vals[int(len(vals) * f)] for f in (.25, .5, .75)]
            q = lambda c: sum(g(lp[c]) >= t for t in cuts) if c in lp else None
            per = {}
            for b in range(4):
                ch = [c for c in hi if q(c) == b]
                cl = [c for c in lo if q(c) == b]
                if len(ch) >= MIN_QUARTILE_N and len(cl) >= MIN_QUARTILE_N:
                    vh, _ = retention_values(E, B, ch)
                    vl, _ = retention_values(E, B, cl)
                    per[b] = {"n_high": len(ch), "n_low": len(cl), "K": sum(vh) / len(vh),
                              "RC_low": sum(vl) / len(vl), "D": sum(vh) / len(vh) - sum(vl) / len(vl)}
            n = sum(x["n_high"] + x["n_low"] for x in per.values())
            sec[f"within_{name}_quartiles"] = {
                "cuts": cuts, "quartiles": per, "dropped": [b for b in range(4) if b not in per],
                "D_adjusted": (sum((x["n_high"] + x["n_low"]) * x["D"] for x in per.values()) / n) if n else None,
                "note": "high-minus-low retention contrast within quartiles of the covariate, weighted by pooled n; "
                        "per-quartile K shows whether K > 0 holds at every edit strength"}
    sec["overall_descriptive"] = {"RC": A.bootstrap_mean(retention_values(E, B, ret)[0]) if ret else None,
                                  "ES_drop": A.bootstrap_mean(drop(paired)) if paired else None,
                                  "note": "descriptive; never pooled with the Study 2 32B pool"}
    out["secondary"] = sec
    return out


def _fmt(e):
    if not e or e.get("point") is None:
        return "—"
    ci = e.get("ci95") or [None, None]
    p = f", p={e['p']:.4f}" if e.get("p") is not None else ""
    return f"{e['point']:+.3f} [{ci[0]:+.3f}, {ci[1]:+.3f}]{p}, n={e.get('n')}"


def render_md(out):
    s = out["secondary"]
    L = ["# Study 3 confirmatory analysis (generated by src/study3/confirm.py)", "",
         f"Mode: {out['_meta']['mode']}. Completeness: {out['completeness']['n_complete']}/{out['completeness']['n_manifest']} "
         f"({out['completeness']['pct']:.1f}%, {out['completeness']['status']}).", "",
         f"**H5 (primary)** retention contrast within well-known facts: {_fmt(out['H5']['estimate'])} → "
         f"**{'PASS' if out['H5']['pass'] else ('FAIL' if out['H5']['tested'] else 'NOT TESTED')}**. "
         f"Wording: {out['wording']}", "",
         "| secondary | estimate |", "|---|---|"]
    for k in ("K_strict", "RC_low", "D_high_minus_low", "own_loss_low_minus_high", "ES_drop_high_minus_low",
              "erosion_given_ES_B0_high_minus_low", "K_paraphrase_B0", "K_paraphrase_B3", "K_thinking_minus_K_paraphrase_B0"):
        L.append(f"| {k} | {_fmt(s.get(k))} |")
    if s.get("dose_response_slope"):
        L.append(f"| dose_response_slope | {_fmt(s['dose_response_slope'])} |")
    return "\n".join(L) + "\n"


def world_completeness(tabs, manifest):
    E, B = tabs[("rome_N", "efficacy")], tabs[("base", "efficacy")]
    done = [c for c in manifest if c in E and c in B and all(b in E[c] and b in B[c] for b in ("B0", "B3"))]
    pct = 100 * len(done) / len(manifest) if manifest else 0
    return {"n_manifest": len(manifest), "n_complete": len(done), "pct": pct, "complete": pct >= MIN_COMPLETE_PCT}


def merge(tab_list):
    out = {}
    for tabs in tab_list:
        for key, t in tabs.items():
            dst = out.setdefault(key, {})
            overlap = set(dst) & set(t)
            if overlap:
                raise SystemExit(f"case ids in two sub-worlds: {sorted(overlap)[:5]}")
            dst.update(t)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/rt/s3")
    ap.add_argument("--end", default="experiments/rt/s3_end_of_generation.json")
    ap.add_argument("--cases", default="data/counterfact.jsonl")
    ap.add_argument("--aliases", default="data/aliases.json")
    ap.add_argument("--out", default="paperwriting/revision/study3.json")
    ap.add_argument("--code-check-on-s2", action="store_true",
                    help="run the estimators on the seen Study 2 32B pool (run tag s2); a code check, not a test")
    a = ap.parse_args(argv)
    cases = {}
    with open(_p(a.cases)) as fh:
        for line in fh:
            c = json.loads(line)
            cases[c["case_id"]] = c
    with open(_p(a.aliases)) as fh:
        aliases = json.load(fh)
    if a.code_check_on_s2:
        results = _p("results/rt/s2")
        worlds = ({"name": "s2", "run_tag": "s2", "manifest": "experiments/rt/pools/study2/manifest_r1qwen32b.jsonl",
                   "qualify_dir": "experiments/rt/pools/study2", "delta_logs": "results/rt/deltas_logs/s2"},)
    else:
        results, worlds = _p(a.results), WORLDS
    status, used_tabs, used_manifest, fam, lp, shard_files, excl = {}, [], [], {}, {}, [], {}
    log_record = {}
    for w in worlds:
        if not os.path.exists(_p(w["manifest"])):
            status[w["name"]] = {"status": "not_run", "reason": "manifest does not exist"}
            continue
        with open(_p(w["manifest"])) as fh:
            manifest = [json.loads(l)["case_id"] for l in fh if l.strip()]
        if not glob.glob(os.path.join(results, f"{MODEL}_{w['run_tag']}_base_r*of*.jsonl")):
            status[w["name"]] = {"status": "not_run", "reason": "no shards", "n_manifest": len(manifest)}
            continue
        logs = sorted(glob.glob(os.path.join(_p(w["delta_logs"]), f"{MODEL}_ROME_cf_r*.jsonl")))
        fit, _ = read_fit_logs(logs) if logs else (None, [])
        tabs, files, ex = load_world(results, w["run_tag"], MODEL, cases, aliases, fit)
        shard_files += files
        excl[w["name"]] = ex
        log_record[w["name"]] = [os.path.relpath(p, REPO) for p in logs]
        comp = world_completeness(tabs, manifest)
        status[w["name"]] = dict(comp, status="complete" if comp["complete"] else "incomplete",
                                 manifest=w["manifest"], manifest_sha256=sha256(_p(w["manifest"])))
        if comp["complete"]:
            used_tabs.append(tabs)
            used_manifest += manifest
            fam.update(familiarity(manifest, MODEL, read_flags(qualify_dir=w["qualify_dir"])))
            lp.update(lp_index(logs))
    entry = None if a.code_check_on_s2 else check_end_entry(_p(a.end), shard_files)
    if used_tabs:
        out = analyse(merge(used_tabs), used_manifest, fam, lp)
    else:
        out = {"completeness": {"status": "incomplete", "n_manifest": 0, "n_complete": 0, "pct": 0, "missing": []},
               "H5": {"estimate": None, "pass": False, "tested": False}, "wording": wording("incomplete", False, None),
               "secondary": {}}
    out["worlds"] = status
    out["_meta"] = {"mode": "code check on Study 2 32B (seen data)" if a.code_check_on_s2 else "confirmatory",
                    "worlds_in_primary": [w["name"] for w in worlds if status.get(w["name"], {}).get("status") == "complete"],
                    "shards": {os.path.relpath(f, REPO): sha256(f) for f in shard_files},
                    "delta_logs": log_record, "exclusions": excl, "end_of_generation": entry,
                    "code_sha256": {rel: sha256(_p(rel)) for rel in ("src/study3/confirm.py", "src/rt/analysis.py",
                                                                    "src/rt/study2.py", "src/metrics.py", "data/aliases.json")}}
    os.makedirs(os.path.dirname(_p(a.out)) or ".", exist_ok=True)
    with open(_p(a.out), "w") as fh:
        json.dump(out, fh, indent=1)
    with open(_p(a.out)[:-5] + ".md", "w") as fh:
        fh.write(render_md(out) if out.get("secondary") else "# Study 3: H5 not tested (no complete sub-world)\n")
    print(f"[study3] {out['_meta']['mode']}: worlds {out['_meta']['worlds_in_primary']} H5 {_fmt(out['H5']['estimate'])} "
          f"pass={out['H5']['pass']} strict {_fmt(out['secondary'].get('K_strict'))} -> {a.out}")


if __name__ == "__main__":
    main()
