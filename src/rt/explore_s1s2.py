"""Exploratory (post hoc): why the R1-Distill-Qwen-32B effect shrank from Study 1 to Study 2.

    PYTHONPATH=src ~/.venvs/why-rt/bin/python -m rt.explore_s1s2 \\
        [--s1 "<main checkout>/results 2"] [--g0 results/rt/g0] [--g0h100 results/rt/g0h100] \\
        [--s2 results/rt/s2] [--delta-logs results/rt/deltas_logs/s2]

The plan (E0-E5) was fixed before this ran: paperwriting/revision/explore_s1s2_plan.md.  Every
estimate uses rt.analysis (lexical, subject scrubbed; 10,000 case resamples, seed 42, percentile
95% CI; independent groups resampled within each group).  Nothing here is confirmatory.
Writes paperwriting/revision/explore_s1s2.{json,md}.
"""
import argparse
import glob
import json
import os
import random
from collections import Counter

from rt import analysis as A
from rt.study1 import _main_checkout

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TAG = "r1qwen32b"


def load(pattern, **defaults):
    files = sorted(glob.glob(pattern))
    if not files:
        raise SystemExit(f"no files: {pattern}")
    rows, audit = A.load_rows(files, defaults=defaults or None)
    return rows, [{"path": f["path"], "sha256": f["sha256"]} for f in audit["files"]]


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


# ---------------------------------------------------------------------------------------------
# Per-case values (the vectors the bootstrap resamples)
# ---------------------------------------------------------------------------------------------
def drop_vals(et, keep=None):
    return [et[c]["B0"]["es"] - et[c]["B3"]["es"] for c in A.paired_cases(et, "B0", "B3")
            if keep is None or keep(c)]


def erosion_given_b0(et, keep=None):
    """Among cases with ES@B0: 1 if the edit is lost at B3."""
    return [1 - et[c]["B3"]["es"] for c in A.paired_cases(et, "B0", "B3")
            if et[c]["B0"]["es"] and (keep is None or keep(c))]


def retention_vals(et, bt, keep=None):
    out = []
    for c in A.paired_cases(et, "B0", "B3"):
        if keep is not None and not keep(c):
            continue
        b = bt.get(c, {})
        if "B0" in b and "B3" in b and b["B0"]["old"] and et[c]["B0"]["es"]:
            out.append((1 - et[c]["B3"]["es"]) - (1 - int(b["B3"]["old"])))
    return out


def est(vals):
    e = A.bootstrap_mean(vals) if vals else {"point": None, "ci95": None, "p": None, "n": 0}
    return {"point": e["point"], "ci95": e["ci95"], "p": e["p"], "n": e.get("n", len(vals))}


def diff(a, b):
    return A.bootstrap_two_groups(a, b)


def run_summary(et, bt):
    return {"ES_B0": est([et[c]["B0"]["es"] for c in A.paired_cases(et, "B0", "B3")]),
            "ES_B3": est([et[c]["B3"]["es"] for c in A.paired_cases(et, "B0", "B3")]),
            "ES_drop": est(drop_vals(et)),
            "erosion_given_ES_B0": est(erosion_given_b0(et)),
            "erosion": A.erosion(et), "repair": A.repair(et),
            "retention_contrast": est(retention_vals(et, bt)),
            "base_chain_B3_names_old": est([bt[c]["B3"]["clr"] for c in sorted(bt) if "B3" in bt[c]]),
            "base_answer_B3_names_old": est([int(bt[c]["B3"]["old"]) for c in sorted(bt) if "B3" in bt[c]]),
            "base_answer_B0_names_old": est([int(bt[c]["B0"]["old"]) for c in sorted(bt) if "B0" in bt[c]])}


def _slim(e):
    return {k: e[k] for k in ("point", "ci95", "p", "n") if k in e}


# ---------------------------------------------------------------------------------------------
# E4 helpers
# ---------------------------------------------------------------------------------------------
def poststratified(vals_by_rel, weights, n_boot=A.N_BOOT, seed=A.SEED):
    """sum_r w_r * mean(vals_r); bootstrap resamples cases within each relation."""
    rels = sorted(weights)
    point = sum(weights[r] * mean(vals_by_rel[r]) for r in rels)
    rr = random.Random(seed).randrange
    boots = []
    for _ in range(n_boot):
        s = 0.0
        for r in rels:
            v = vals_by_rel[r]
            s += weights[r] * sum(v[rr(len(v))] for _ in range(len(v))) / len(v)
        boots.append(s)
    boots.sort()
    return {"point": point, "ci95": [boots[int(.025 * n_boot)], boots[int(.975 * n_boot)]],
            "n_relations": len(rels), "n_cases": sum(len(vals_by_rel[r]) for r in rels)}


def auc(pos, neg):
    """P(score of an eroded case > score of a kept case), ties 1/2."""
    if not pos or not neg:
        return None
    wins = sum((p > q) + 0.5 * (p == q) for p in pos for q in neg)
    return wins / (len(pos) * len(neg))


def delta_index(paths):
    idx = {}
    for p in paths:
        with open(p) as fh:
            for line in fh:
                r = json.loads(line)
                if r.get("sha") and r.get("lp_first"):
                    idx[r["sha"]] = r
    return idx


# ---------------------------------------------------------------------------------------------
def main():
    main_repo = _main_checkout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--s1", default=os.path.join(main_repo, "results 2"))
    ap.add_argument("--g0", default=os.path.join(REPO, "results/rt/g0"))
    ap.add_argument("--g0h100", default=os.path.join(REPO, "results/rt/g0h100"))
    ap.add_argument("--s2", default=os.path.join(REPO, "results/rt/s2"))
    ap.add_argument("--delta-logs", default=os.path.join(REPO, "results/rt/deltas_logs/s2"))
    ap.add_argument("--g0-delta-logs", default=os.path.join(REPO, "results/rt/deltas_logs/g0"))
    ap.add_argument("--pools", default=os.path.join(REPO, "experiments/rt/pools/study2"))
    ap.add_argument("--cases", default=os.path.join(main_repo, "data", "counterfact.jsonl"))
    ap.add_argument("--aliases", default=os.path.join(REPO, "data", "aliases.json"))
    ap.add_argument("--out", default=os.path.join(REPO, "paperwriting/revision/explore_s1s2.json"))
    args = ap.parse_args()

    cases = {}
    with open(args.cases) as fh:
        for line in fh:
            c = json.loads(line)
            cases[c["case_id"]] = c
    with open(args.aliases) as fh:
        aliases = json.load(fh)

    specs = {
        "S1": (os.path.join(args.s1, "probe/r1qwen32b_ROME_cf200_r*.jsonl"),
               os.path.join(args.s1, "probe/r1qwen32b_BASE_cf200_r*.jsonl"), {"model_tag": TAG}),
        "G0-4090": (os.path.join(args.g0, "r1qwen32b_g0_rome_N_r*of4.jsonl"),
                    os.path.join(args.g0, "r1qwen32b_g0_base_r*of4.jsonl"), {}),
        "G0-H100": (os.path.join(args.g0h100, "r1qwen32b_g0h100_rome_N_r*of2.jsonl"),
                    os.path.join(args.g0h100, "r1qwen32b_g0h100_base_r*of2.jsonl"), {}),
        "S2": (os.path.join(args.s2, "r1qwen32b_s2_rome_N_r*of8.jsonl"),
               os.path.join(args.s2, "r1qwen32b_s2_base_r*of8.jsonl"), {}),
    }
    E, B, files, erows = {}, {}, {}, {}
    for k, (ep, bp, d) in specs.items():
        er, ef = load(ep, **d)
        br, bf = load(bp, **d)
        erows[k] = er
        E[k] = A.case_table(er, cases, aliases)
        B[k] = A.case_table(br, cases, aliases)
        files[k] = {"edited": ef, "base": bf}

    out = {"_meta": {"plan": "paperwriting/revision/explore_s1s2_plan.md", "status": "exploratory, post hoc",
                     "conventions": "rt.analysis lexical; 10,000 resamples, seed 42, percentile 95% CI",
                     "files": files}}
    out["runs"] = {k: run_summary(E[k], B[k]) for k in specs}

    # E0: hardware, same cases
    a, b = E["G0-4090"], E["G0-H100"]
    shared = [c for c in A.paired_cases(a, "B0", "B3") if c in b and "B0" in b[c] and "B3" in b[c]]
    out["E0_hardware"] = {
        "n_shared": len(shared),
        "paired_4090_minus_H100": {f: _slim(A.flow_difference(a, b, f)) for f in ("es_drop", "erosion", "repair")},
        "agreement_ES_B0": mean(int(a[c]["B0"]["es"] == b[c]["B0"]["es"]) for c in shared),
        "agreement_ES_B3": mean(int(a[c]["B3"]["es"] == b[c]["B3"]["es"]) for c in shared),
        "agreement_base_old_B3": mean(int(B["G0-4090"][c]["B3"]["old"] == B["G0-H100"][c]["B3"]["old"])
                                      for c in shared if c in B["G0-4090"] and c in B["G0-H100"]),
        "retention_4090_minus_H100": diff(retention_vals(a, B["G0-4090"]), retention_vals(b, B["G0-H100"])),
    }

    # E1: heterogeneity S2 vs Study-1 cases
    out["E1_heterogeneity"] = {}
    for ref in ("G0-H100", "G0-4090", "S1"):
        out["E1_heterogeneity"][f"S2_minus_{ref}"] = {
            "ES_drop": diff(drop_vals(E["S2"]), drop_vals(E[ref])),
            "erosion_given_ES_B0": diff(erosion_given_b0(E["S2"]), erosion_given_b0(E[ref])),
            "repair": diff([int(not E["S2"][c]["B0"]["es"] and E["S2"][c]["B3"]["es"]) for c in A.paired_cases(E["S2"], "B0", "B3")],
                           [int(not E[ref][c]["B0"]["es"] and E[ref][c]["B3"]["es"]) for c in A.paired_cases(E[ref], "B0", "B3")]),
            "retention_contrast": diff(retention_vals(E["S2"], B["S2"]), retention_vals(E[ref], B[ref])),
        }

    # E2: Study 2's qualification rule applied to each run's own base rows
    def qualifies(bt):
        return lambda c: (c in bt and "B0" in bt[c] and bt[c]["B0"]["old"] and not bt[c]["B0"]["new"]
                          and not A.name_contains_old(cases[c]))
    out["E2_qualification_rule"] = {}
    for k in specs:
        q = qualifies(B[k])
        out["E2_qualification_rule"][k] = {
            "n_admitted": sum(1 for c in A.paired_cases(E[k], "B0", "B3") if q(c)),
            "n_paired": len(A.paired_cases(E[k], "B0", "B3")),
            "ES_drop": est(drop_vals(E[k], q)),
            "erosion_given_ES_B0": est(erosion_given_b0(E[k], q)),
            "retention_contrast": est(retention_vals(E[k], B[k], q))}

    # E3: moderator = the unedited model's own B3 chain (or answer) names o_old
    out["E3_base_recall_moderator"] = {}
    for mod, key in (("base_chain_B3_names_old", "clr"), ("base_answer_B3_names_old", "old")):
        block = {}
        for k in specs:
            bt = B[k]
            m1 = lambda c, bt=bt: c in bt and "B3" in bt[c] and bool(bt[c]["B3"][key])
            m0 = lambda c, bt=bt: c in bt and "B3" in bt[c] and not bt[c]["B3"][key]
            block[k] = {
                "prevalence_among_paired": mean(int(m1(c)) for c in A.paired_cases(E[k], "B0", "B3")
                                               if c in bt and "B3" in bt[c]),
                "m1": {"ES_drop": est(drop_vals(E[k], m1)), "erosion_given_ES_B0": est(erosion_given_b0(E[k], m1)),
                       "retention_contrast": est(retention_vals(E[k], bt, m1))},
                "m0": {"ES_drop": est(drop_vals(E[k], m0)), "erosion_given_ES_B0": est(erosion_given_b0(E[k], m0)),
                       "retention_contrast": est(retention_vals(E[k], bt, m0))},
                "m1_minus_m0": {"ES_drop": diff(drop_vals(E[k], m1), drop_vals(E[k], m0)),
                                "erosion_given_ES_B0": diff(erosion_given_b0(E[k], m1), erosion_given_b0(E[k], m0))}}
        out["E3_base_recall_moderator"][mod] = block

    # E4: relation mix
    def by_rel(et, keep=None):
        d = {}
        for c in A.paired_cases(et, "B0", "B3"):
            if keep is None or keep(c):
                d.setdefault(cases[c]["r"], []).append(et[c]["B0"]["es"] - et[c]["B3"]["es"])
        return d
    s1r, s2r = by_rel(E["S1"]), by_rel(E["S2"])
    g0r = by_rel(E["G0-H100"])
    shared_rel = sorted(set(s1r) & set(s2r))
    n1 = sum(len(s1r[r]) for r in shared_rel)
    n2 = sum(len(s2r[r]) for r in shared_rel)
    w_s1 = {r: len(s1r[r]) / n1 for r in shared_rel}
    w_s2 = {r: len(s2r[r]) / n2 for r in shared_rel}
    out["E4_relation_mix"] = {
        "S1_relations": dict(Counter({r: len(v) for r, v in s1r.items()}).most_common()),
        "S2_relations": dict(Counter({r: len(v) for r, v in s2r.items()}).most_common()),
        "shared_relations": shared_rel,
        "S1_cases_in_shared_relations": n1, "S2_cases_in_shared_relations": n2,
        "S2_drop_reweighted_to_S1_mix": poststratified({r: s2r[r] for r in shared_rel}, w_s1),
        "S2_drop_own_mix_shared_relations": poststratified({r: s2r[r] for r in shared_rel}, w_s2),
        "G0H100_drop_reweighted_to_S2_mix": poststratified({r: g0r[r] for r in shared_rel if r in g0r},
                                                           {r: w_s2[r] / sum(w_s2[q] for q in shared_rel if q in g0r)
                                                            for r in shared_rel if r in g0r}),
        "per_relation": {r: {"S1_n": len(s1r.get(r, [])), "S1_drop": mean(s1r.get(r, [])),
                             "S2_n": len(s2r.get(r, [])), "S2_drop": mean(s2r.get(r, []))}
                         for r in sorted(set(s1r) | set(s2r), key=lambda r: -(len(s1r.get(r, [])) + len(s2r.get(r, []))))},
    }

    # E5: edit strength (S2)
    idx = delta_index(sorted(glob.glob(os.path.join(args.delta_logs, f"{TAG}_ROME_cf_r*.jsonl"))))
    sha_of = {}
    for r in erows["S2"]:
        if r.get("delta_sha"):
            sha_of.setdefault(r["case_id"], r["delta_sha"])
    et = E["S2"]
    feats = {"lp_target_after": lambda lp: lp["after"]["target"],
             "lp_old_after": lambda lp: lp["after"]["o_old"],
             "lp_old_before": lambda lp: lp["before"]["o_old"],
             "lp_old_drop": lambda lp: lp["before"]["o_old"] - lp["after"]["o_old"]}
    e5 = {"n_with_log": 0}
    rows5 = []
    for c in A.paired_cases(et, "B0", "B3"):
        if not et[c]["B0"]["es"]:
            continue
        rec = idx.get(sha_of.get(c))
        if rec is None:
            continue
        lp = rec["lp_first"]
        rows5.append((c, 1 - et[c]["B3"]["es"], {f: g(lp) for f, g in feats.items()}))
    e5["n_with_log"] = len(rows5)
    for f in feats:
        vals = sorted(x[2][f] for x in rows5)
        med = vals[len(vals) // 2]
        hi = [x[1] for x in rows5 if x[2][f] >= med]
        lo = [x[1] for x in rows5 if x[2][f] < med]
        e5[f] = {"median": med,
                 "auc_eroded_higher": auc([x[2][f] for x in rows5 if x[1]], [x[2][f] for x in rows5 if not x[1]]),
                 "erosion_high_minus_low": diff(hi, lo)}
    out["E5_edit_strength_S2"] = e5

    # E5b (added after E5 was seen): does lp_old_after replicate on the Study-1 cases, and does its
    # distribution explain the S2 vs Study-1 erosion gap?  G0-4090 and G0-H100 use the same deltas.
    gidx = delta_index(sorted(glob.glob(os.path.join(args.g0_delta_logs, f"{TAG}_ROME_cf_r*.jsonl"))))

    def strength_rows(k, index):
        sha = {}
        for r in erows[k]:
            if r.get("delta_sha"):
                sha.setdefault(r["case_id"], r["delta_sha"])
        t, rows = E[k], []
        for c in A.paired_cases(t, "B0", "B3"):
            rec = index.get(sha.get(c))
            if t[c]["B0"]["es"] and rec is not None:
                rows.append((rec["lp_first"]["after"]["o_old"], 1 - t[c]["B3"]["es"]))
        return rows

    s2rows = strength_rows("S2", idx)
    cut = sorted(x for x, _ in s2rows)[len(s2rows) // 2]
    e5b = {"cut_lp_old_after_S2_median": cut}
    for k in ("G0-H100", "G0-4090"):
        g = strength_rows(k, gidx)
        pooled = sorted(x for x, _ in s2rows + g)
        q = [pooled[int(len(pooled) * f)] for f in (.25, .5, .75)]
        b_of = lambda x: sum(x >= t for t in q)
        def predicted(srows, grows):
            s_bin = {}
            for x, y in srows:
                s_bin.setdefault(b_of(x), []).append(y)
            share = Counter(b_of(x) for x, _ in grows)
            n = sum(share.values())
            return sum(share[b] / n * mean(s_bin[b]) for b in share if b in s_bin)
        obs_g, obs_s, pred = mean(y for _, y in g), mean(y for _, y in s2rows), predicted(s2rows, g)
        rr = random.Random(A.SEED).randrange
        boots = []
        for _ in range(A.N_BOOT):
            sr = [s2rows[rr(len(s2rows))] for _ in s2rows]
            gr = [g[rr(len(g))] for _ in g]
            boots.append((predicted(sr, gr) - mean(y for _, y in sr), mean(y for _, y in gr) - predicted(sr, gr)))
        ci = lambda v: [sorted(v)[int(.025 * A.N_BOOT)], sorted(v)[int(.975 * A.N_BOOT)]]
        e5b[k] = {
            "n": len(g), "median_lp_old_after": sorted(x for x, _ in g)[len(g) // 2],
            "share_above_S2_median": mean(int(x >= cut) for x, _ in g),
            "auc_eroded_higher": auc([x for x, y in g if y], [x for x, y in g if not y]),
            "erosion_high_minus_low_at_S2_median": diff([y for x, y in g if x >= cut], [y for x, y in g if x < cut]),
            "pooled_quartile_cuts": q,
            "erosion_observed": obs_g, "erosion_S2_observed": obs_s,
            "erosion_predicted_from_S2_rates_by_quartile": pred,
            "explained_gap": {"point": pred - obs_s, "ci95": ci([b[0] for b in boots])},
            "unexplained_gap": {"point": obs_g - pred, "ci95": ci([b[1] for b in boots])},
            "share_of_gap_explained": (pred - obs_s) / (obs_g - obs_s) if obs_g != obs_s else None}
    e5b["S2_median_lp_old_after"] = cut
    out["E5b_strength_vs_gap"] = e5b

    # E6 (added after E5b was seen): fact salience.  Study 1's pool was selected by the unedited
    # Qwen-7B naming o_old at B3; Study 2's 1600 candidates were screened at B0 by every model's
    # own base (rt.pool qualify files), so for each S2 case we know which smaller models know it.
    known = {}
    for tag in ("r1qwen1_5b", "r1qwen7b", "r1qwen14b", "r1llama8b", "r1llama70b"):
        with open(os.path.join(args.pools, f"qualify_{tag}.jsonl")) as fh:
            for line in fh:
                r = json.loads(line)
                known.setdefault(r["case_id"], {})[tag] = bool(r["old_hit"])
    small = ("r1qwen1_5b", "r1qwen7b", "r1qwen14b", "r1llama8b")
    k7 = lambda c: known.get(c, {}).get("r1qwen7b")
    score = lambda c: sum(known.get(c, {}).get(t, False) for t in small)
    s2c = A.paired_cases(E["S2"], "B0", "B3")
    s1_7b, _ = load(os.path.join(args.s1, "pilot/r1qwen7b_BASE_cf200_r*.jsonl"), model_tag="r1qwen7b")
    t7 = A.case_table(s1_7b, cases, aliases)
    s1c = A.paired_cases(E["S1"], "B0", "B3")
    e6 = {"S2_share_known_by_7B_at_B0": mean(int(bool(k7(c))) for c in s2c),
          "S1_share_known_by_7B_at_B0": mean(int(t7[c]["B0"]["old"]) for c in s1c if c in t7 and "B0" in t7[c]),
          "S1_share_known_by_7B_at_B3": mean(int(t7[c]["B3"]["old"]) for c in s1c if c in t7 and "B3" in t7[c]),
          "S2_known_by_n_small_models": dict(sorted(Counter(score(c) for c in s2c).items()))}
    for name, keep1 in (("known_by_7B", lambda c: bool(k7(c))), ("known_by_all_4_small", lambda c: score(c) == 4),
                        ("known_by_ge_2_small", lambda c: score(c) >= 2)):
        keep0 = lambda c, f=keep1: not f(c)
        e6[name] = {
            "n1": sum(1 for c in s2c if keep1(c)), "n0": sum(1 for c in s2c if keep0(c)),
            "yes": {"ES_drop": est(drop_vals(E["S2"], keep1)), "erosion_given_ES_B0": est(erosion_given_b0(E["S2"], keep1)),
                    "retention_contrast": est(retention_vals(E["S2"], B["S2"], keep1))},
            "no": {"ES_drop": est(drop_vals(E["S2"], keep0)), "erosion_given_ES_B0": est(erosion_given_b0(E["S2"], keep0)),
                   "retention_contrast": est(retention_vals(E["S2"], B["S2"], keep0))},
            "yes_minus_no": {"ES_drop": diff(drop_vals(E["S2"], keep1), drop_vals(E["S2"], keep0)),
                             "erosion_given_ES_B0": diff(erosion_given_b0(E["S2"], keep1), erosion_given_b0(E["S2"], keep0)),
                             "retention_contrast": diff(retention_vals(E["S2"], B["S2"], keep1),
                                                        retention_vals(E["S2"], B["S2"], keep0))}}
    def loss_parts(et, bt, keep):
        S = [c for c in A.paired_cases(et, "B0", "B3") if keep(c) and "B0" in bt.get(c, {}) and "B3" in bt[c]
             and bt[c]["B0"]["old"] and et[c]["B0"]["es"]]
        el = [1 - et[c]["B3"]["es"] for c in S]
        bl = [1 - int(bt[c]["B3"]["old"]) for c in S]
        return {"n": len(S), "edited_loss": mean(el), "base_loss": mean(bl),
                "retention_contrast": est([x - y for x, y in zip(el, bl)])}

    e6["S2_by_n_small_models"] = {
        s: {**loss_parts(E["S2"], B["S2"], lambda c, s=s: score(c) == s),
            "ES_B0": mean(E["S2"][c]["B0"]["es"] for c in s2c if score(c) == s),
            "ES_drop": mean(E["S2"][c]["B0"]["es"] - E["S2"][c]["B3"]["es"] for c in s2c if score(c) == s)}
        for s in range(5)}
    e6["S2_high_salience_3to4_vs_0to2"] = {
        "high": loss_parts(E["S2"], B["S2"], lambda c: score(c) >= 3),
        "low": loss_parts(E["S2"], B["S2"], lambda c: score(c) <= 2),
        "high_minus_low_retention": diff(retention_vals(E["S2"], B["S2"], lambda c: score(c) >= 3),
                                         retention_vals(E["S2"], B["S2"], lambda c: score(c) <= 2)),
        "high_ES_drop": est(drop_vals(E["S2"], lambda c: score(c) >= 3)),
        "low_ES_drop": est(drop_vals(E["S2"], lambda c: score(c) <= 2)),
        "high_erosion_given_ES_B0": est(erosion_given_b0(E["S2"], lambda c: score(c) >= 3)),
        "low_erosion_given_ES_B0": est(erosion_given_b0(E["S2"], lambda c: score(c) <= 2))}
    out["E6_fact_salience"] = e6

    # E6b (added after E6 was seen): the same salience split on the Study 1 cases.  Salience = share of
    # the other small R1 distills (1.5B, 7B, 14B, Llama-8B, excluding the model itself) whose Study-1
    # base run names o_old at B0; high = share >= .75 (3-4 of 4; 3 of 3 for 14B).
    s1_small = {"r1qwen1_5b": "probe/r1qwen1_5b_BASE_cf200_r*.jsonl", "r1qwen7b": "pilot/r1qwen7b_BASE_cf200_r*.jsonl",
                "r1qwen14b": "probe/r1qwen14b_BASE_cf200_r*.jsonl", "r1llama8b": "probe/r1llama8b_BASE_cf200c2_r*.jsonl"}
    K = {}
    for t, p in s1_small.items():
        rows, _ = load(os.path.join(args.s1, p), model_tag=t)
        K[t] = A.case_table(rows, cases, aliases)

    def s1_share(c, excl=None):
        v = [K[t][c]["B0"]["old"] for t in K if t != excl and c in K[t] and "B0" in K[t][c]]
        need = 3 if excl else 4
        return sum(v) / len(v) if len(v) == need else None

    e6b = {"S1_share_high": mean(int(s1_share(c) >= .75) for c in s1c if s1_share(c) is not None),
           "S2_share_high": mean(int(score(c) >= 3) for c in s2c)}
    s1_models = {"Qwen-14B": ("r1qwen14b", "probe/r1qwen14b_ROME_cf200_r*.jsonl", "probe/r1qwen14b_BASE_cf200_r*.jsonl", "r1qwen14b"),
                 "Llama-70B": ("r1llama70b", "probe/r1llama70b_ROME_cf100_r*.jsonl", "probe/r1llama70b_BASE_cf100_r*.jsonl", None)}
    tabs = {"Qwen-32B S1": (E["S1"], B["S1"], None), "Qwen-32B G0-H100": (E["G0-H100"], B["G0-H100"], None),
            "Qwen-32B G0-4090": (E["G0-4090"], B["G0-4090"], None)}
    for name, (tag, ep, bp, excl) in s1_models.items():
        er_, _ = load(os.path.join(args.s1, ep), model_tag=tag)
        br_, _ = load(os.path.join(args.s1, bp), model_tag=tag)
        tabs[f"{name} S1"] = (A.case_table(er_, cases, aliases), A.case_table(br_, cases, aliases), excl)
    for name, (et_, bt_, excl) in tabs.items():
        hi = lambda c, x=excl: s1_share(c, x) is not None and s1_share(c, x) >= .75
        lo = lambda c, x=excl: s1_share(c, x) is not None and s1_share(c, x) < .75
        e6b[name] = {"high": loss_parts(et_, bt_, hi), "low": loss_parts(et_, bt_, lo),
                     "high_minus_low_retention": diff(retention_vals(et_, bt_, hi), retention_vals(et_, bt_, lo))}
    out["E6b_salience_in_study1"] = e6b

    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=False)
    write_md(out, args.out[:-5] + ".md")
    print(f"[explore] wrote {args.out} and .md")



def write_md(o, path):
    """Short markdown summary of explore_s1s2.json (every number read from the JSON)."""
    f = lambda e: "—" if not e or e.get("point") is None else f"{e['point']:+.3f} [{e['ci95'][0]:+.3f}, {e['ci95'][1]:+.3f}]"
    fp = lambda e: f(e) + (f", p={e['p']:.3f}" if e and e.get("p") is not None else "")
    L = ["# Exploratory: why the 32B effect shrank from Study 1 to Study 2 (post hoc)", "",
         "Plan and addenda: `explore_s1s2_plan.md` (E5b, E6, E6b were added after earlier results were seen). "
         "Numbers: `explore_s1s2.json`. Nothing here is confirmatory.", "",
         "| run | ES@B0 | ES drop | erosion given ES@B0 | repair | retention contrast |", "|---|---|---|---|---|---|"]
    for k, r in o["runs"].items():
        L.append(f"| {k} | {r['ES_B0']['point']:.3f} | {f(r['ES_drop'])} | {f(r['erosion_given_ES_B0'])} | "
                 f"{r['repair']['point']:.3f} | {f(r['retention_contrast'])} |")
    e0 = o["E0_hardware"]
    L += ["", f"**E0 hardware** (same {e0['n_shared']} cases, 4090 − H100): ES drop {fp(e0['paired_4090_minus_H100']['es_drop'])}; "
          f"B0 outcome agreement {e0['agreement_ES_B0']:.3f}, B3 {e0['agreement_ES_B3']:.3f}; retention {fp(e0['retention_4090_minus_H100'])}."]
    h = o["E1_heterogeneity"]["S2_minus_G0-H100"]
    L += ["", f"**E1 matched hardware** (S2 − G0-H100): ES drop {fp(h['ES_drop'])}; erosion given ES@B0 {fp(h['erosion_given_ES_B0'])}; "
          f"repair {fp(h['repair'])}; retention {fp(h['retention_contrast'])}."]
    L += ["", "**E2 Study 2's qualification rule on the Study 1 cases**: " + "; ".join(
        f"{k} {v['n_admitted']}/{v['n_paired']}: drop {f(v['ES_drop'])}, retention {f(v['retention_contrast'])}"
        for k, v in o["E2_qualification_rule"].items())]
    m = o["E3_base_recall_moderator"]["base_chain_B3_names_old"]
    L += ["", "**E3 base chain at B3 names o_old** (erosion given ES@B0, moderator 1 − 0): " + "; ".join(
        f"{k} prevalence {v['prevalence_among_paired']:.2f}, {fp(v['m1_minus_m0']['erosion_given_ES_B0'])}" for k, v in m.items())]
    e4 = o["E4_relation_mix"]
    L += ["", f"**E4 relation mix**: S2 drop reweighted to S1's relation mix {f(e4['S2_drop_reweighted_to_S1_mix'])}; "
          f"G0-H100 reweighted to S2's mix {f(e4['G0H100_drop_reweighted_to_S2_mix'])}."]
    e5, e5b = o["E5_edit_strength_S2"], o["E5b_strength_vs_gap"]
    L += ["", f"**E5/E5b edit strength** (first-token log p(o_old) after the edit): S2 AUC {e5['lp_old_after']['auc_eroded_higher']:.3f}, "
          f"high − low erosion {fp(e5['lp_old_after']['erosion_high_minus_low'])}; on the Study 1 cases AUC "
          f"{e5b['G0-H100']['auc_eroded_higher']:.3f} (G0-H100), share of the erosion gap explained {e5b['G0-H100']['share_of_gap_explained']:.2f}."]
    e6, e6b = o["E6_fact_salience"], o["E6b_salience_in_study1"]
    L += ["", "## E6/E6b fact salience (number of the small distills 1.5B, 7B, 14B, Llama-8B whose base names o_old at B0)", "",
          "| S2 salience | n (retention set) | edited loss | base loss | retention contrast | ES@B0 | ES drop |", "|---|---|---|---|---|---|---|"]
    for s, v in e6["S2_by_n_small_models"].items():
        L.append(f"| {s} of 4 | {v['n']} | {v['edited_loss']:.3f} | {v['base_loss']:.3f} | {f(v['retention_contrast'])} | "
                 f"{v['ES_B0']:.3f} | {v['ES_drop']:+.3f} |")
    hl = e6["S2_high_salience_3to4_vs_0to2"]
    L += ["", f"S2, high (3–4) vs low (0–2): ES drop {fp(hl['high_ES_drop'])} vs {fp(hl['low_ES_drop'])}; erosion given ES@B0 "
          f"{f(hl['high_erosion_given_ES_B0'])} vs {f(hl['low_erosion_given_ES_B0'])}; retention {f(hl['high']['retention_contrast'])} vs "
          f"{f(hl['low']['retention_contrast'])}, difference {fp(hl['high_minus_low_retention'])}.", "",
          f"Share of high-salience cases: Study 1 {e6b['S1_share_high']:.2f}, Study 2 {e6b['S2_share_high']:.2f}.", "",
          "| Study 1 cases | high: n, edited loss, base loss, retention | low: n, retention | high − low |", "|---|---|---|---|"]
    for k, v in e6b.items():
        if isinstance(v, dict):
            L.append(f"| {k} | {v['high']['n']}, {v['high']['edited_loss']:.3f}, {v['high']['base_loss']:.3f}, {f(v['high']['retention_contrast'])} | "
                     f"{v['low']['n']}, {f(v['low']['retention_contrast'])} | {fp(v['high_minus_low_retention'])} |")
    with open(path, "w") as fh:
        fh.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
