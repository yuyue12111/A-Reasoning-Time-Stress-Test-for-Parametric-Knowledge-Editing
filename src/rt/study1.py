"""Study 1 reanalysis (REVISION.md §2): every estimate of rt.analysis over the AAAI-era rows.

    PYTHONPATH=src ~/.venvs/why-rt/bin/python -m rt.study1 [--results "<main checkout>/results 2"]

Reads the headline edited and base runs of six checkpoints, the 32B sampling run and the 32B
five-arm runs, and writes

    paperwriting/revision/study1.json   every number with n, its denominator and its inputs
    paperwriting/revision/study1.md     the short tables

Provenance: ``worlds`` lists each run's files (paths relative to the results root) with sha256;
every block names the worlds it read.  ``reproduction`` compares the results against
paperwriting/results.json and the numbers REVISION.md §2 quotes; a mismatch is reported, never
tuned away.  Llama-70B is analysed unfiltered (n=200, REVISION.md's convention) and under
``score_pilot.py --drop-degenerate`` (results.json's headline convention).
"""
import argparse
import glob
import json
import os
import subprocess
import sys

from rt import analysis as A

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# name, model_tag, results.json family, params_b, base_probe key, edited glob, base glob
CHECKPOINTS = (
    ("Qwen-1.5B", "r1qwen1_5b", "R1-Distill-Qwen", 1.5, "1.5B",
     "probe/r1qwen1_5b_ROME_cf200_r*.jsonl", "probe/r1qwen1_5b_BASE_cf200_r*.jsonl"),
    ("Qwen-7B", "r1qwen7b", "R1-Distill-Qwen", 7, "7B",
     "pilot/r1qwen7b_ROME_cf200_r*of8.jsonl", "pilot/r1qwen7b_BASE_cf200_r*.jsonl"),
    ("Qwen-14B", "r1qwen14b", "R1-Distill-Qwen", 14, "14B",
     "probe/r1qwen14b_ROME_cf200_r*.jsonl", "probe/r1qwen14b_BASE_cf200_r*.jsonl"),
    ("Qwen-32B", "r1qwen32b", "R1-Distill-Qwen", 32, "32B",
     "probe/r1qwen32b_ROME_cf200_r*.jsonl", "probe/r1qwen32b_BASE_cf200_r*.jsonl"),
    ("Llama-8B", "r1llama8b", "R1-Distill-Llama", 8, "8B",
     "probe/r1llama8b_ROME_cf200c2_r*.jsonl", "probe/r1llama8b_BASE_cf200c2_r*.jsonl"),
    ("Llama-70B", "r1llama70b", "R1-Distill-Llama", 70, "70B",
     "probe/r1llama70b_ROME_cf100_r*.jsonl", "probe/r1llama70b_BASE_cf100_r*.jsonl"),
)
FILTERED = "Llama-70B|drop_degenerate"
ARMS = {"N": "probe/r1qwen32b_ROME_cf200_r*.jsonl",
        "T": "probe/r1qwen32b_ROME_cf200sup_r*.jsonl",
        "D": "probe/r1qwen32b_ROME_cf200sup_onew_r*.jsonl",
        "P": "probe/r1qwen32b_ROME_cf200sup_placebo_r*.jsonl",
        "C": "probe/r1qwen32b_ROME_cf200sup_strong_r*.jsonl"}
ARM_TAGS = {"N": "cf200", "T": "cf200sup", "D": "cf200sup_onew", "P": "cf200sup_placebo",
            "C": "cf200sup_strong"}
SAMPLING = "probe/r1qwen32b_ROME_cf200samp_r*.jsonl"
FLOW_PAIRS = (("Qwen-32B", "Qwen-1.5B"), ("Qwen-32B", "Qwen-7B"), ("Qwen-32B", "Qwen-14B"),
              ("Llama-70B", "Llama-8B"))
CODE = ("src/rt/analysis.py", "src/rt/study1.py", "src/metrics.py", "src/cross_arm.py",
        "src/score_pilot.py")


def _main_checkout():
    """The main checkout (results 2/ and data/counterfact.jsonl are untracked and live there)."""
    try:
        common = subprocess.run(["git", "-C", REPO, "rev-parse", "--path-format=absolute",
                                 "--git-common-dir"], capture_output=True, text=True, check=True)
        return os.path.dirname(common.stdout.strip())
    except Exception:
        return REPO


def _git(*args):
    try:
        return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return None


def _sha(path):
    return A.file_record(path)["sha256"]


class Study:
    def __init__(self, results, cases_path, aliases_path):
        self.root = results
        self.cases = {}
        with open(cases_path) as fh:
            for line in fh:
                c = json.loads(line)
                self.cases[c["case_id"]] = c
        with open(aliases_path) as fh:
            self.aliases = json.load(fh)
        self.worlds = {}

    def load(self, wid, pattern, **defaults):
        files = sorted(glob.glob(os.path.join(self.root, pattern)))
        if not files:
            raise SystemExit(f"no files for {wid}: {os.path.join(self.root, pattern)}")
        rows, audit = A.load_rows(files, defaults=defaults)
        for f in audit["files"]:
            f["path"] = os.path.relpath(f["path"], self.root)
        self.worlds[wid] = {"glob": pattern, "labels": defaults, **audit}
        return rows

    def table(self, rows, **kw):
        return A.case_table(rows, self.cases, self.aliases, **kw)


def checkpoint_block(etab, btab, universe, cases, worlds):
    """Every per-checkpoint estimate."""
    btab_u = A.restrict(btab, universe.__contains__)
    paired = A.paired_cases(etab, "B0", "B3")
    contains = {c for c in paired if A.name_contains_old(cases[c])}
    e_in = A.restrict(etab, contains.__contains__)
    e_out = A.restrict(etab, lambda c: c not in contains)
    rr_in = [int(etab[c]["B3"]["old"]) for c in sorted(contains) if etab[c]["B0"]["es"]]
    rr_out = [int(etab[c]["B3"]["old"]) for c in paired if c not in contains and etab[c]["B0"]["es"]]
    base_den = ("base efficacy rows at {b} whose case is in the edited run (the base run's own "
                "denominator, as src/base_probe.py --score); value = base answer names o_old")
    return {
        "worlds": worlds,
        "n_cases_edited": len(universe), "n_cases_paired": len(paired),
        "ES_B0": A.rate(etab, "B0"), "ES_B3": A.rate(etab, "B3"),
        "ES_drop": A.es_drop(etab),
        "RR": A.rr(etab), "RRs": A.rr(etab, strict=True), "CLR": A.clr(etab),
        "base_old_B0": A.rate(btab_u, "B0", "old", base_den.format(b="B0")),
        "base_old_B3": A.rate(btab_u, "B3", "old", base_den.format(b="B3")),
        "erosion": A.erosion(etab), "repair": A.repair(etab),
        "retention_contrast": A.retention_contrast(etab, btab),
        "qualified_ES_drop": A.qualified_es_drop(etab, btab),
        "knowledge_strata": A.knowledge_strata(etab, btab),
        "name_containment": {
            "rule": "subject contains o_old as a whole word, case-insensitive (metrics._wb)",
            "n_contains": len(contains), "n_paired": len(paired),
            "ES_drop_excluding": A.es_drop(e_out),
            "ES_drop_contains": A.es_drop(e_in),
            "RR_excluding": A.rr(e_out), "RRs_excluding": A.rr(e_out, strict=True),
            "RR_contains": A.rr(e_in),
            "RR_contains_minus_excluding": {
                **A.bootstrap_two_groups(rr_in, rr_out),
                "denominator": "cases with ES@B0 and a row at B3, split by name containment; "
                               "groups resampled separately; value = RR(contains) - RR(rest)"},
        },
        "failure_anatomy": A.failure_anatomy(etab),
        "answer_length": A.answer_length(etab),
    }


ORDER_NOTE = ("bootstrap-sequence dependent, point estimate matches: REVISION.md §2 came from an exploratory "
              "pass that resampled cases in shard-file order (random.Random(42); numpy default_rng(42) for the "
              "qualified CIs); study1 resamples in sorted case_id order as cross_arm does. Replaying the "
              "exploratory convention on the same per-case values returns the target exactly.")


def _close(computed, target, decimals):
    return computed is not None and abs(computed - target) <= 0.5 * 10 ** -decimals + 1e-9


def reproduce(out, published, esup=None):
    """Compare against results.json and REVISION.md §2.  Points must match at the published
    precision; CI endpoints and bootstrap p also depend on the order cases are resampled in."""
    checks = []
    cp = out["checkpoints"]

    def add(claim, source, computed, target, decimals, kind="point", note=""):
        if kind == "conclusion":
            ok = computed == target
        else:
            ok = _close(computed, target, decimals)
        if not ok and kind in ("p", "ci") and not note:
            note = ORDER_NOTE
        checks.append({"claim": claim, "source": source, "kind": kind, "target": target,
                       "computed": computed, "status": "MATCH" if ok else "DIFFERS", "note": note})

    fam = published["capability"]["families"]
    bp = published["base_probe"]
    for name, _tag, family, params, bkey, _e, _b in CHECKPOINTS:
        i = fam[family]["params_b"].index(params)
        cell = FILTERED if name == "Llama-70B" else name
        src = f"results.json capability.families[{family}] @ {params}B"
        note = "results.json headline uses the n=187 early-stop filter" if cell == FILTERED else ""
        for key, est, dec in (("es_drop", "ES_drop", 3), ("rr", "RR", 3), ("clr", "CLR", 3),
                              ("es_b0", "ES_B0", 3), ("es_b3", "ES_B3", 3)):
            add(f"{cell} {key}", src, cp[cell][est]["point"], fam[family][key][i], dec, note=note)
        add(f"{name} base answer_old_b0", f"results.json base_probe[{bkey}]",
            cp[name]["base_old_B0"]["point"], bp[bkey]["answer_old_b0"], 3)
    desc = published["emergence"]["percase"]["cells_descriptive"]["Llama-70.0B"]
    for key, est in (("es_drop", "ES_drop"), ("rr", "RR"), ("clr", "CLR")):
        add(f"Llama-70B (unfiltered) {key}", "results.json emergence.percase.cells_descriptive[Llama-70.0B]",
            cp["Llama-70B"][est]["point"], desc[key], 4 if key != "es_drop" else 3)
    add("Llama-70B filter drops 13 cases (n=187)", "results.json capability.families[R1-Distill-Llama].headline_n",
        cp[FILTERED]["n_cases_paired"], fam["R1-Distill-Llama"]["headline_n"][1], 0)

    rev = "REVISION.md §2"
    holm = out["holm_es_drop"]["70B_unfiltered"]
    for name, p in (("Llama-70B", 0.0024), ("Qwen-32B", 0.0082)):
        add(f"Holm ES drop {name} raw p", rev, holm[name]["p"], p, 4, "p")
        add(f"Holm ES drop {name} rejected at .05", rev, holm[name]["reject"], True, 0, "conclusion")
    others = [n for n in holm if n not in ("Llama-70B", "Qwen-32B")]
    add("Holm: only 70B and 32B rejected", rev, all(not holm[n]["reject"] for n in others), True, 0,
        "conclusion")
    for name, pt, lo, hi in (("Qwen-14B", .195, .057, .322), ("Qwen-32B", .216, .091, .341),
                             ("Llama-70B", .234, .117, .351)):
        r = cp[name]["retention_contrast"]
        add(f"retention {name} point", rev, r["point"], pt, 3)
        add(f"retention {name} CI low", rev, r["ci95"][0], lo, 3, "ci")
        add(f"retention {name} CI high", rev, r["ci95"][1], hi, 3, "ci")
    add("name containment count in the 200-case pool", rev, out["name_containment_pool"]["n_contains"], 46, 0)
    nc32 = cp["Qwen-32B"]["name_containment"]
    add("Qwen-32B RR among name-containment cases", rev, nc32["RR_contains"]["point"], .60, 2)
    add("Qwen-32B RR among the rest", rev, nc32["RR_excluding"]["point"], .156, 3)
    for name, pt in (("Qwen-32B", .118), ("Llama-70B", .117)):
        e = cp[name]["name_containment"]["ES_drop_excluding"]
        add(f"{name} ES drop excluding name containment", rev, e["point"], pt, 3)
        add(f"{name} ES drop excluding name containment: CI excludes 0", rev, e["ci95"][0] > 0, True, 0,
            "conclusion")
    for name, pt, lo, hi in (("Qwen-32B", .125, .040, .217), ("Llama-70B", .153, .076, .229)):
        q = cp[name]["qualified_ES_drop"]
        add(f"qualified ES drop {name} point", rev, q["point"], pt, 3)
        add(f"qualified ES drop {name} CI low", rev, q["ci95"][0], lo, 3, "ci")
        add(f"qualified ES drop {name} CI high", rev, q["ci95"][1], hi, 3, "ci")
    add("erosion Qwen-1.5B", rev, cp["Qwen-1.5B"]["erosion"]["point"], .128, 3)
    add("erosion Qwen-32B", rev, cp["Qwen-32B"]["erosion"]["point"], .207, 3)
    add("erosion CI excludes 0 in all six", rev,
        all(cp[n]["erosion"]["ci95"][0] > 0 for n, *_ in CHECKPOINTS), True, 0, "conclusion")
    for name, pt in (("Qwen-1.5B", .153), ("Qwen-32B", .101), ("Llama-70B", .085)):
        add(f"repair {name}", rev, cp[name]["repair"]["point"], pt, 3)
    s = out["sampling_reliability"]["primary"]
    add("sampling: P(>=1 of 3 sampled B3 fails | greedy B0 ok)", rev, s["fail_any_b1"]["point"], .605, 3)
    add("sampling: B0 noise floor", rev, s["fail_any_b0_noise_floor"]["point"], .339, 3)

    con = out["arm_contrasts"]["contrasts"]
    sb = published["rq3"]["sup_battery"]
    p_note = (f"results.json sup_battery counts P n={sb['n']['P']} and was computed from an earlier state of the "
              f"P shards; the local P shards hold {out['arm_contrasts']['marginal']['P']['n']} B3 cases and "
              "reproduce results 2/esup_crossarm.json exactly; dropping any one of the four OOM-retried P cases "
              "does not recover the results.json values")
    for block, pairs, dec, src in (
            (sb["cross_arm_paired_ci"], ("T-N", "C-N", "T-C"), 4, "results.json rq3.sup_battery.cross_arm_paired_ci"),
            (sb["contrasts_B3_mean_ci_p"], ("T-P", "D-N", "P-N"), 3, "results.json rq3.sup_battery.contrasts_B3_mean_ci_p")):
        for pair in pairs:
            key = pair.replace("-", "_minus_")
            for m in ("ES", "RR", "RRs", "CLR"):
                pt, _ci95, pv = block[key][m]
                note = p_note if "P" in pair else ""
                add(f"arm {pair} {m} point", src, con[pair][m]["point"], pt, dec, note=note)
                add(f"arm {pair} {m} p", src, con[pair][m]["p"], pv, dec, "p", note=note)
    if esup is not None:
        src = "results 2/esup_crossarm.json (cross_arm output on the local shards)"
        for pair, ms in esup["contrasts"].items():
            for m, r in ms.items():
                add(f"arm {pair} {m} point", src, con[pair][m]["point"], r["mean"], 4)
                add(f"arm {pair} {m} p", src, con[pair][m]["p"], r["p"], 4, "p")
                add(f"arm {pair} {m} n", src, con[pair][m]["n"], r["n"], 0)
    return checks


def _fmt(x, d=3):
    return "—" if x is None else f"{x:.{d}f}"


def _ci(e, d=3):
    if not e or e.get("point") is None:
        return "—"
    return f"{e['point']:.{d}f} [{e['ci95'][0]:.{d}f}, {e['ci95'][1]:.{d}f}]"


def render_md(out):
    cp, holm = out["checkpoints"], out["holm_es_drop"]
    L = ["# Study 1 reanalysis (generated by `src/rt/study1.py`; numbers in `study1.json`)", "",
         "Lexical scoring of `src/metrics.py`; bootstrap 10,000 case resamples, seed 42, percentile 95% CI, "
         "two-sided p = 2·min(#≤0, #≥0)/B, cases resampled in sorted case_id order. "
         "Llama-70B is shown unfiltered (n=200) and under `score_pilot.py --drop-degenerate` (n=187).", "",
         "## 1 ES gap per checkpoint (B0 → B3, paired)", "",
         "| checkpoint | n | ES@B0 | ES@B3 | ES drop [95% CI] | p | Holm p | RR | RRs | CLR | base old@B0 |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name in [c[0] for c in CHECKPOINTS] + [FILTERED]:
        b = cp[name]
        fam = "70B_filtered" if name == FILTERED else "70B_unfiltered"
        key = "Llama-70B" if name == FILTERED else name
        h = holm[fam].get(key, {})
        L.append(f"| {name} | {b['n_cases_paired']} | {_fmt(b['ES_B0']['point'])} | {_fmt(b['ES_B3']['point'])} | "
                 f"{_ci(b['ES_drop'])} | {_fmt(b['ES_drop']['p'], 4)} | {_fmt(h.get('p_holm'), 4)}"
                 f"{' ✓' if h.get('reject') else ''} | {_fmt(b['RR']['point'])} | {_fmt(b['RRs']['point'])} | "
                 f"{_fmt(b['CLR']['point'])} | {_fmt(b['base_old_B0']['point'])} (n={b['base_old_B0']['n']}) |")
    L += ["", "Holm over the six ES-drop tests (✓ = rejected at .05); the filtered row uses the family with "
          "70B filtered. base old@B0 is over the base run's B0 rows for that row's cases.", "",
          "## 2 Edit specificity, knowledge and name containment", "",
          "| checkpoint | retention: edited − native loss [CI] (n) | qualified ES drop [CI] (n) | "
          "name ⊃ o_old | ES drop excl. [CI] | RR contains / rest |",
          "|---|---|---|---|---|---|"]
    for name in [c[0] for c in CHECKPOINTS] + [FILTERED]:
        b = cp[name]
        r, q, nc = b["retention_contrast"], b["qualified_ES_drop"], b["name_containment"]
        L.append(f"| {name} | {_ci(r)} ({r['n']}) | {_ci(q)} ({q['n']}) | {nc['n_contains']}/{nc['n_paired']} | "
                 f"{_ci(nc['ES_drop_excluding'])} | {_fmt(nc['RR_contains']['point'])} / "
                 f"{_fmt(nc['RR_excluding']['point'])} |")
    L += ["", "Retention: cases where the base answers o_old at B0 and the edit succeeds at B0; "
          "value = 1{edited loses ES at B3} − 1{base stops answering o_old at B3}.", "",
          "## 3 Erosion and repair", "",
          "| checkpoint | erosion P(ES@B0 ∧ ¬ES@B3) | repair P(¬ES@B0 ∧ ES@B3) | ES drop in known-B0&B3 stratum (n) |",
          "|---|---|---|---|"]
    for name in [c[0] for c in CHECKPOINTS] + [FILTERED]:
        b = cp[name]
        k = b["knowledge_strata"]["known_B0_B3"]
        L.append(f"| {name} | {_ci(b['erosion'])} | {_ci(b['repair'])} | {_ci(k)} ({k['n']}) |")
    L += ["", "| paired on shared cases | Δ erosion | Δ repair |", "|---|---|---|"]
    for pair, v in out["flow_differences"].items():
        L.append(f"| {pair} | {_ci(v['erosion'])} (n={v['erosion']['n']}) | {_ci(v['repair'])} |")
    s = out["sampling_reliability"]["primary"]
    L += ["", "## 4 Sampling reliability (Qwen-32B, 3 seeds, T=0.6)", "",
          f"Among {s['fail_any_b1']['n']} edits with greedy ES@B0: at least one of 3 sampled B3 answers fails "
          f"{_ci(s['fail_any_b1'])}; the same over 3 sampled B0 answers (noise floor) "
          f"{_ci(s['fail_any_b0_noise_floor'])}; excess {_ci(s['excess'])} (p={_fmt(s['excess']['p'], 4)}).", "",
          "## 5 Arm contrasts (Qwen-32B, B3, cross_arm.paired_diff)", "",
          "| contrast | ES | RR | RRs | CLR |", "|---|---|---|---|---|"]
    for con, ms in out["arm_contrasts"]["contrasts"].items():
        cells = [f"{_ci(ms[m], 3)} p={_fmt(ms[m]['p'], 4)} n={ms[m]['n']}" for m in ("ES", "RR", "RRs", "CLR")]
        L.append(f"| {con} | " + " | ".join(cells) + " |")
    par = out["arm_contrasts"]["b0_parity"]["pairs"]
    L += ["", "B0 run parity (byte-identical B0 answers / shared cases; B0 has no chain, so a think-scoped "
          "suppressor cannot act there): " + "; ".join(f"{k} {v['identical_answer']}/{v['n']}" for k, v in par.items())
          + ". Arms that differ at B0 were generated in different environments, so their contrast mixes "
          "arm and run."]
    diffs = [c for c in out["reproduction"] if c["status"] != "MATCH"]
    L += ["", "## 6 Reproduction", "",
          f"{sum(c['status'] == 'MATCH' for c in out['reproduction'])} of {len(out['reproduction'])} checks match "
          "(results.json six headline cells and REVISION.md §2)."]
    if diffs:
        L += ["", "| claim | kind | target | computed |", "|---|---|---|---|"]
        for c in diffs:
            comp = c["computed"] if not isinstance(c["computed"], float) else round(c["computed"], 4)
            L.append(f"| {c['claim']} | {c['kind']} | {c['target']} | {comp} |")
        notes = sorted({c["note"] for c in diffs if c["note"]})
        L += [""] + [f"Note: {n}" for n in notes]
    return "\n".join(L) + "\n"


def main():
    main_repo = _main_checkout()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--results", default=os.path.join(main_repo, "results 2"))
    ap.add_argument("--cases", default=os.path.join(main_repo, "data", "counterfact.jsonl"))
    ap.add_argument("--aliases", default=os.path.join(REPO, "data", "aliases.json"))
    ap.add_argument("--published", default=os.path.join(REPO, "paperwriting", "results.json"))
    ap.add_argument("--out", default=os.path.join(REPO, "paperwriting", "revision", "study1.json"))
    args = ap.parse_args()

    st = Study(args.results, args.cases, args.aliases)
    out = {"_meta": {
        "generator": "src/rt/study1.py",
        "git_head": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain", "--", "src")),
        "code_sha256": {p: _sha(os.path.join(REPO, p)) for p in CODE},
        "results_root": os.path.basename(os.path.normpath(args.results)),
        "reference_inputs": {"cases": {"path": "data/counterfact.jsonl", "sha256": _sha(args.cases)},
                             "aliases": {"path": "data/aliases.json", "sha256": _sha(args.aliases)},
                             "published": {"path": "paperwriting/results.json", "sha256": _sha(args.published)}},
        "bootstrap": {"n_boot": A.N_BOOT, "seed": A.SEED, "ci": A.CI, "unit": "case",
                      "ci_rule": "sorted replicate means at int(.025B), int(.975B)",
                      "p_rule": "2*min(#<=0, #>=0)/B, capped at 1", "case_order": "sorted case_id",
                      "conditional_rates": "resample only the cases passing the gate"},
        "scoring": "metrics.hit on metrics._without_subject(text, s); ES = new and not old",
        "provenance": "each block's `worlds` names entries of the top-level `worlds` registry "
                      "(files relative to results_root, with sha256)"}}

    tabs, bases, universes = {}, {}, {}
    out["checkpoints"] = {}
    n32_rows = None
    for name, tag, *_rest, epat, bpat in CHECKPOINTS:
        erows = st.load(f"{name}/edited", epat, model_tag=tag)
        brows = st.load(f"{name}/base", bpat, model_tag=tag)
        if name == "Qwen-32B":
            n32_rows = erows
        etab, btab = st.table(erows), st.table(A.select(brows, condition="base"))
        universe = {r["case_id"] for r in erows}
        tabs[name], bases[name], universes[name] = etab, btab, universe
        out["checkpoints"][name] = checkpoint_block(etab, btab, universe, st.cases,
                                                    [f"{name}/edited", f"{name}/base"])
        if name == "Llama-70B":
            bad = A.degenerate_cases(erows)
            kept = A.drop_cases(erows, bad)
            ftab = st.table(kept)
            fu = {r["case_id"] for r in kept}
            blk = checkpoint_block(ftab, btab, fu, st.cases, [f"{name}/edited", f"{name}/base"])
            blk["filter"] = {"rule": "src/score_pilot.py --drop-degenerate: _is_degenerate on every row "
                                     "(any probe/budget) of the edited shards; all rows of a flagged case dropped",
                             "n_dropped": len(bad), "dropped_case_ids": bad}
            tabs[FILTERED], universes[FILTERED] = ftab, fu
            out["checkpoints"][FILTERED] = blk

    pool = set().union(*(universes[n] for n, *_ in CHECKPOINTS))
    hits = sorted(c for c in pool if A.name_contains_old(st.cases[c]))
    out["name_containment_pool"] = {"n_pool": len(pool), "n_contains": len(hits), "case_ids": hits,
                                    "rule": "subject contains o_old as a whole word, case-insensitive"}

    names = [n for n, *_ in CHECKPOINTS]
    out["holm_es_drop"] = {
        "family": "paired ES drop B0->B3 at the six checkpoints; alpha .05",
        "70B_unfiltered": A.holm({n: out["checkpoints"][n]["ES_drop"]["p"] for n in names}),
        "70B_filtered": A.holm({n: out["checkpoints"][FILTERED if n == "Llama-70B" else n]["ES_drop"]["p"]
                                for n in names}),
        "qualified_70B_unfiltered": A.holm({n: out["checkpoints"][n]["qualified_ES_drop"]["p"] for n in names}),
        "name_excluded_70B_unfiltered": A.holm(
            {n: out["checkpoints"][n]["name_containment"]["ES_drop_excluding"]["p"] for n in names}),
        "retention_70B_unfiltered": A.holm(
            {n: out["checkpoints"][n]["retention_contrast"]["p"] for n in names})}

    out["flow_differences"] = {}
    for hi, lo in FLOW_PAIRS:
        out["flow_differences"][f"{hi} - {lo}"] = {
            "worlds": [f"{hi}/edited", f"{lo}/edited"],
            **{f: A.flow_difference(tabs[hi], tabs[lo], f) for f in ("erosion", "repair", "es_drop")}}

    srows = st.load("Qwen-32B/sampling", SAMPLING, model_tag="r1qwen32b")
    greedy = st.table(srows)
    seeds = sorted({r["seed"] for r in srows if r["decode"] == "sample"})
    sampled = {s: st.table(srows, decode="sample", seed=s) for s in seeds}
    out["sampling_reliability"] = {
        "worlds": ["Qwen-32B/sampling"],
        "temperatures": sorted({r["temperature"] for r in srows if r["decode"] == "sample"}),
        "primary": A.sampling_reliability(greedy, sampled),
        "sensitivity_gate_headline_greedy_B0": A.sampling_reliability(tabs["Qwen-32B"], sampled),
        "greedy_B0_agreement_with_headline": {
            "n": len([c for c in greedy if "B0" in greedy[c] and "B0" in tabs["Qwen-32B"].get(c, {})]),
            "share_equal_ES": A.bootstrap_mean(
                [int(greedy[c]["B0"]["es"] == tabs["Qwen-32B"][c]["B0"]["es"]) for c in sorted(greedy)
                 if "B0" in greedy[c] and "B0" in tabs["Qwen-32B"].get(c, {})])["point"]}}

    arm_rows = {"N": n32_rows}
    arm_tabs = {"N": tabs["Qwen-32B"]}
    for arm, pat in ARMS.items():
        if arm != "N":
            arm_rows[arm] = st.load(f"Qwen-32B/arm_{arm}", pat, model_tag="r1qwen32b", arm=arm)
            arm_tabs[arm] = st.table(arm_rows[arm], arm=arm)
    parity = {f"{a}-{b}": {**A.answer_parity(arm_rows[a], arm_rows[b], "B0"),
                           "same_ES_B0": sum(arm_tabs[a][c]["B0"]["es"] == arm_tabs[b][c]["B0"]["es"]
                                             for c in arm_tabs[a] if "B0" in arm_tabs[a][c]
                                             and "B0" in arm_tabs[b].get(c, {}))}
              for a, b in (("T", "N"), ("D", "N"), ("P", "N"), ("C", "N"), ("P", "C"))}
    records = {a: A.arm_records(t) for a, t in arm_tabs.items()}
    marg = {a: {m: A.bootstrap_mean([v[m] for v in rec.values() if v[m] is not None])["point"]
                for m in ("ES", "RR", "RRs", "CLR")} | {"n": len(rec)} for a, rec in records.items()}
    # cross-check: our records equal cross_arm.per_case on the same shards
    import cross_arm
    cwd = os.getcwd()
    os.chdir(REPO)                                   # per_case reads data/aliases.json relative to cwd
    try:
        same = {}
        for arm, tag in ARM_TAGS.items():
            cfg = {"dataset": {"tag": tag, "path": args.cases}, "out_dir": os.path.join(args.results, "probe"),
                   "model_tag": "r1qwen32b"}
            same[arm] = cross_arm.per_case(cfg, "ROME", "B3") == records[arm]
    finally:
        os.chdir(cwd)
    out["arm_contrasts"] = {
        "worlds": ["Qwen-32B/edited"] + [f"Qwen-32B/arm_{a}" for a in ARMS if a != "N"],
        "arms": {"N": "no suppression (headline run)", "T": "suppress o_old in the chain",
                 "D": "suppress o_new in the chain", "P": "suppress a placebo token",
                 "C": "suppress a same-relation strong competitor"},
        "budget": "B3", "gate": "ES@B0 of the same arm",
        "marginal": marg,
        "records_identical_to_cross_arm_per_case": same,
        "b0_parity": {"rule": "B0 has no chain, so a think-scoped suppressor cannot act there: arms from the "
                              "same code and environment answer B0 byte-identically",
                      "pairs": parity},
        "contrasts": A.arm_contrasts(records, metric_names=("ES", "RR", "RRs", "CLR"))}

    out["worlds"] = st.worlds
    with open(args.published) as fh:
        published = json.load(fh)
    esup_path, esup = os.path.join(args.results, "esup_crossarm.json"), None
    if os.path.exists(esup_path):
        with open(esup_path) as fh:
            esup = json.load(fh)
        out["_meta"]["reference_inputs"]["esup_crossarm"] = {"path": "esup_crossarm.json", "sha256": _sha(esup_path)}
    out["reproduction"] = reproduce(out, published, esup)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    md = os.path.splitext(args.out)[0] + ".md"
    with open(md, "w") as fh:
        fh.write(render_md(out))
    n_diff = sum(c["status"] != "MATCH" for c in out["reproduction"])
    print(f"wrote {os.path.relpath(args.out, REPO)} and {os.path.relpath(md, REPO)}; "
          f"reproduction: {len(out['reproduction']) - n_diff} match, {n_diff} differ")
    for c in out["reproduction"]:
        if c["status"] != "MATCH":
            print(f"  DIFFERS {c['claim']}: target {c['target']} computed {c['computed']} ({c['kind']})")


if __name__ == "__main__":
    sys.exit(main())
