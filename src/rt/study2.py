"""Study 2 pre-registered analysis (prereg-arr.md §4-§7): completeness, H1, H2, H2b, H3, secondaries.

    PYTHONPATH=src ~/.venvs/why-rt/bin/python -m rt.study2 --results results/rt/s2 \\
        --out paperwriting/revision/study2.json [--md paperwriting/revision/study2.md] \\
        [--manifests experiments/rt/pools/study2] [--cases data/counterfact.jsonl] \\
        [--aliases data/aliases.json] \\
        [--delta-logs results/rt/deltas_logs/s2 results/rt/deltas_logs/s2_h2b] \\
        [--switch results/annot/study1/score.json \\
         --judged gemma='results/judge/gemma/s2*.jsonl' --judged mistral='results/judge/mistral/s2*.jsonl']

Inputs.  ``rt.run`` shards ``<model_tag>_<run_tag>_<condition>_r<k>of<n>.jsonl`` are grouped into
worlds (model_tag, run_tag, condition) by their ``_meta`` header.  Run tag ``s2`` is a model's main
pool (``manifest_<tag>.jsonl``), ``s2h2b`` the H2b unknown group (``manifest_<tag>_unknown.jsonl``);
any other run tag (smoke runs) is listed and ignored.

Order of operations (prereg §6):

1. Exclusions, counted per world: error rows (``error`` field; ``analysis.load_rows`` skips them),
   rows of edits whose rank-1 fit error exceeds 1e-4 (largest ``fit[L].rel_err`` of the rt.deltas
   log row whose ``sha`` is the row's ``delta_sha``), rows of cases outside the manifest.
2. Completeness: an estimate is computed only when at least 98% of its manifest's cases have
   every row it needs after the exclusions; it is then computed on exactly those cases and the
   missing ones are listed with it.  Otherwise the block is ``incomplete`` (``not_run`` when none
   of its conditions exists, ``no_manifest`` without a manifest) and carries no number.  A Holm
   family keeps its size: a member without an estimate enters with p = 1 and is not rejected.
3. Estimates, all from ``rt.analysis`` (Study 1's conventions: 10,000 resamples of cases in sorted
   case_id order, random.Random(42), percentile 95% CI, two-sided p; independent groups are
   resampled within each group).  Each is repeated without the cases ``score_pilot._is_degenerate``
   flags in any row of the worlds it reads (``without_degenerate``); the unfiltered one is primary.

Endpoints (prereg §4).  Lexical (``metrics.hit`` on the subject-scrubbed answer; ES = new and not
old; strict reversion RRs = old and not new) is primary unless ``--switch`` gives kappa_es and
kappa_rr >= .70 AND judge outputs are given (``--judged NAME=GLOB``, rt.judge files, averaged by
``judge.combine_judges``); then semantic ES (label NEW) and semantic reversion (label OLD) are
primary.  With judge outputs the other endpoint is reported too.  Locality rows are scored without
subject scrubbing, as ``metrics.score`` and ``judge.lexical_flags`` score them.

Output: one JSON (``_meta`` provenance, the endpoint decision, per-world exclusions and coverage,
one analysis per endpoint) and a short markdown summary.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
from collections import Counter

import metrics
from rt import analysis as A

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN, H2B = "s2", "s2h2b"
MANIFEST_NAME = {MAIN: "manifest_{}.jsonl", H2B: "manifest_{}_unknown.jsonl"}
R1 = ("r1qwen1_5b", "r1qwen7b", "r1qwen14b", "r1qwen32b", "r1llama8b", "r1llama70b")
H1_AT = ("r1qwen32b", "r1llama70b")
H2_AT = ("r1qwen14b", "r1qwen32b", "r1llama70b")
FOCUS = "r1qwen32b"
RECIPES = ("qwen2_5_32b_instruct", "qwq32b")
MIN_COMPLETE_PCT = 98
FIT_TOL = 1e-4
KAPPA_MIN = 0.70
SIG = 0.05
PREREG_PROMPT_SHA = "dc4649065540f3a92e08be083520b75c2e7a93697c7289ecf385cc5a8f96771c"
N_JUDGES = 2
DELTA_EDITORS = ("ROME", "MEMIT", "AlphaEdit")
H3_TESTS = (("T-P ES", "rome_T", "rome_P", "ES", 1), ("T-P RRs", "rome_T", "rome_P", "RRs", -1),
            ("D-P ES", "rome_D", "rome_P", "ES", -1))
ARM_SECONDARY = (("T-N", "rome_T", "rome_N"), ("D-N", "rome_D", "rome_N"), ("T-C", "rome_T", "rome_C"),
                 ("P-N", "rome_P", "rome_N"))
ARM_METRICS = ("ES", "RR", "RRs")
EDITORS_32B = ("memit_N", "alphaedit_N", "ike")
ALPHA_DOSE = (("rome_a0.5", 0.5, ("B0",)), ("rome_N", 1.0, ("B0", "B3")), ("rome_a2", 2.0, ("B0", "B3")),
              ("rome_a3", 3.0, ("B0", "B3")))
ES_TARGET = 0.80
RELIABILITY_SEEDS, EXTRA_SEED = (0, 1, 2), 3
GIVEN = ("rome_own", "rome_filler", "rome_swap")
REPAIR_PAIRS = (("r1qwen32b", "r1qwen1_5b"), ("r1llama70b", "r1llama8b"))
CODE = ("src/rt/study2.py", "src/rt/analysis.py", "src/metrics.py", "src/score_pilot.py", "src/rt/judge.py")


def _git(*args):
    try:
        return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return None


def _rel(path):
    a = os.path.abspath(path)
    return os.path.relpath(a) if a.startswith(os.getcwd() + os.sep) else a


def _record(path):
    return dict(A.file_record(path), path=_rel(path))


def _wid(w):
    return "/".join(w)


# ---------------------------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------------------------
def read_manifest(path):
    """Ordered case ids of a pool manifest; a ``.sha256`` sidecar must match (as rt.run.read_ids)."""
    side = path + ".sha256"
    if os.path.exists(side) and open(side).read().split()[0] != A.file_record(path)["sha256"]:
        raise ValueError(f"{path}: sha256 differs from {side}")
    ids = []
    for line in open(path):
        line = line.strip()
        if line:
            ids.append(json.loads(line)["case_id"] if line.startswith("{") else line)
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: duplicate case ids")
    return ids


def shard_header(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                h = json.loads(line)
                return h if h.get("_meta") else None
    return None


def discover(results):
    """{(model_tag, run_tag, condition): [files]} from the shards' ``_meta`` headers."""
    worlds, skipped = {}, []
    for path in sorted(glob.glob(os.path.join(results, "*.jsonl"))):
        h = shard_header(path)
        if h is None:
            if os.path.getsize(path) == 0:
                skipped.append({"path": _rel(path), "reason": "empty file"})
                continue
            raise ValueError(f"{path}: first line is not an rt.run _meta header")
        key = (h.get("model_tag"), h.get("run_tag"), h.get("condition"))
        if None in key:
            raise ValueError(f"{path}: header lacks model_tag/run_tag/condition")
        worlds.setdefault(key, []).append(path)
    return worlds, skipped


def error_rows(files):
    """Error rows (``error`` field) of shards: case, kind, file and line."""
    out = []
    for path in files:
        with open(path, encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                if '"error"' in line:                       # cheap pre-filter; the parse decides
                    r = json.loads(line)
                    if r.get("error"):
                        out.append({"case_id": r.get("case_id"), "kind": r.get("error_kind"),
                                    "path": _rel(path), "line": i})
    return out


def read_fit_logs(paths):
    """{delta sha: largest rel_err over edited layers} from rt.deltas shard logs (the ``ok`` rows
    ``deltas.summarize`` reads), and a per-file record with status counts."""
    fit, files = {}, []
    for p in paths:
        counts, over = Counter(), []
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                r = json.loads(line)
                if r.get("_meta") or not r.get("case_id"):
                    continue
                counts[r.get("status")] += 1
                if r.get("status") == "ok" and r.get("sha"):
                    err = max(float(f["rel_err"]) for f in r["fit"].values())
                    fit[r["sha"]] = err
                    if err > FIT_TOL:
                        over.append(r["case_id"])
        files.append(dict(_record(p), counts=dict(counts), ok_fit_over_tol=sorted(set(over))))
    return fit, files


def _run_tag_of(src, model_tag, condition):
    m = re.match(rf"^{re.escape(model_tag or '')}_(.+)_{re.escape(condition or '')}_r\d+of\d+\.jsonl$",
                 src or "")
    return m.group(1) if m else None


def load_verdicts(specs):
    """Ensemble judge labels keyed like the generation rows.

    ``specs``: ["NAME=GLOB", ...], one per judge (rt.judge output files).  The judges' label
    probabilities are averaged by ``judge.combine_judges`` (a row a judge lacks gets no verdict).
    Key: (model_tag, run_tag, condition, case_id, budget, probe, decode, seed); the run tag is read
    from the generation file name the judge recorded (``row.src``).  Value: (label, item hash).
    """
    from rt import judge as J
    per, info = {}, {}
    for spec in specs:
        name, sep, pattern = spec.partition("=")
        if not sep or not name or not pattern:
            raise SystemExit(f"--judged wants NAME=GLOB, got {spec!r}")
        headers, rows = J.read_judged([pattern])
        views = [J.compat_view(h) for h in headers]
        prompts = sorted({v["prompt"] for v in views}, key=str)
        orders = sorted({v["orders"] for v in views}, key=str)
        per[name] = rows
        info[name] = {"pattern": pattern, "files": [_record(f) for f in J.expand([pattern])],
                      "n_rows": len(rows), "prompt_sha": prompts, "orders": orders,
                      "as_preregistered": prompts == [PREREG_PROMPT_SHA] and orders == [2]}
    combined = J.combine_judges(per, allow_partial=True)
    verdicts = {}
    for r in combined:
        rid = r["row"]
        key = (rid.get("model_tag"), _run_tag_of(rid.get("src"), rid.get("model_tag"), rid.get("condition")),
               rid.get("condition"), rid["case_id"], rid["budget"], rid["probe"],
               rid.get("decode") or "greedy", rid.get("seed"))
        if key in verdicts and verdicts[key] != (r["label"], r["item"]):
            raise ValueError(f"two different judged rows for {key}")
        verdicts[key] = (r["label"], r["item"])
    return verdicts, {"judges": info, "n_ensemble_rows": len(combined),
                      "as_preregistered": len(per) == N_JUDGES and all(v["as_preregistered"] for v in info.values())}


def endpoint_decision(switch_path, judged):
    """Prereg §4 switch: semantic ES and reversion are primary iff the mean kappa (judge ensemble vs
    each annotator, Study 1 items) is >= .70 for both ES and reversion; judge outputs must be given
    to score them.  Accepts {"kappa_es", "kappa_rr"} or an rt.annotate score report."""
    d = {"rule": f"semantic primary iff kappa_es >= {KAPPA_MIN} and kappa_rr >= {KAPPA_MIN} (mean over the two "
                 "annotators) and judge outputs are given; otherwise lexical ES and strict reversion",
         "threshold": KAPPA_MIN, "switch_file": None, "kappa_es": None, "kappa_rr": None,
         "judge_outputs_given": bool(judged)}
    if switch_path:
        s = json.load(open(switch_path))
        if "kappa_es" in s or "kappa_rr" in s:
            kes, krr = s.get("kappa_es"), s.get("kappa_rr")
        elif isinstance(s.get("switch"), dict):
            k = s["switch"].get("kappa") or {}
            kes, krr = k.get("es"), k.get("rr")
        else:
            raise SystemExit(f"{switch_path}: no kappa_es/kappa_rr and no rt.annotate switch.kappa")
        d.update(switch_file=_record(switch_path), kappa_es=kes, kappa_rr=krr)
    ok = all(k is not None and k >= KAPPA_MIN for k in (d["kappa_es"], d["kappa_rr"]))
    d["kappa_meets_threshold"] = ok
    d["primary"] = "semantic" if ok and judged else "lexical"
    if ok and not judged:
        d["note"] = ("kappa meets the threshold but no judge outputs were given: this run reports lexical "
                     "endpoints only; rerun with --judged for the pre-registered primary")
    return d


# ---------------------------------------------------------------------------------------------
# Tables and gates
# ---------------------------------------------------------------------------------------------
def locality_table(rows, cases, aliases, decode="greedy", seed=None):
    """{case_id: {budget: outcome}} of locality rows, scored as ``metrics.score`` does: the neighbour
    prompt is about another subject, so the answer is not subject-scrubbed."""
    tab = {}
    for r in rows:
        if r["probe"] != "locality" or r["decode"] != decode or (seed is not None and r.get("seed") != seed):
            continue
        c, a = cases[r["case_id"]], r.get("answer") or ""
        new, old = bool(metrics.hit(a, c["o_new"], aliases)), bool(metrics.hit(a, c["o_old"], aliases))
        slot = tab.setdefault(r["case_id"], {})
        if r["budget"] in slot:
            raise ValueError(f"two locality rows for case {r['case_id']} at {r['budget']}")
        slot[r["budget"]] = {"new": new, "old": old, "es": int(new and not old), "clr": 0, "words": len(a.split())}
    return tab


def completeness(ids, needs):
    """Cases of the manifest ``ids`` that have every needed row.  ``needs``: [(table, budgets)]."""
    ok = [c for c in ids if all(all(b in t.get(c, {}) for b in buds) for t, buds in needs)]
    n, k = len(ids), len(ok)
    return {"n_manifest": n, "n_complete": k, "share": k / n if n else None,
            "complete": n > 0 and 100 * k >= MIN_COMPLETE_PCT * n,
            "rule": f"at least {MIN_COMPLETE_PCT}% of the manifest's cases have every needed row",
            "missing": sorted(set(ids) - set(ok))}


def need(world, *budgets, probe="efficacy", decode="greedy", seed=None):
    return (world, probe, decode, seed, tuple(budgets))


class Study2:
    """Worlds of one results directory after the exclusions, their manifests and scored tables."""

    def __init__(self, results, manifests, cases, aliases, fit=None, verdicts=None):
        self.results, self.manifest_dir = results, manifests
        self.cases, self.aliases, self.fit, self.verdicts = cases, aliases, fit, verdicts
        found, self.skipped = discover(results)
        self.ignored = {_wid(k): [_rel(f) for f in v] for k, v in sorted(found.items()) if k[1] not in MANIFEST_NAME}
        self._manifests, self._tabs, self._judge = {}, {}, Counter()
        self.worlds = {k: self._load(k, v) for k, v in sorted(found.items()) if k[1] in MANIFEST_NAME}

    def manifest_path(self, model, run):
        return os.path.join(self.manifest_dir, MANIFEST_NAME[run].format(model))

    def manifest(self, model, run):
        key = (model, run)
        if key not in self._manifests:
            p = self.manifest_path(model, run)
            self._manifests[key] = read_manifest(p) if os.path.exists(p) else None
        return self._manifests[key]

    def has_model(self, model):
        return any(k[0] == model for k in self.worlds)

    def _load(self, key, files):
        rows, audit = A.load_rows(files)
        for r in rows:
            if (r["model_tag"], r["condition"]) != (key[0], key[2]):
                raise ValueError(f"row {r['source']} is ({r['model_tag']}, {r['condition']}) in a {key} shard")
        ids = self.manifest(key[0], key[1])
        idset = set(ids or ())
        errs = error_rows(files)
        kept, outside, fit_bad, unverified = [], Counter(), Counter(), 0
        for r in rows:
            if ids is not None and r["case_id"] not in idset:
                outside[r["case_id"]] += 1
                continue
            if r["editor"] in DELTA_EDITORS and self.fit is not None:
                err = self.fit.get(r.get("delta_sha"))
                if err is None:
                    unverified += 1
                elif err > FIT_TOL:
                    fit_bad[r["case_id"]] += 1
                    continue
            kept.append(r)
        has = {}
        for r in kept:
            has.setdefault((r["probe"], r["decode"], r.get("seed"), r["budget"]), set()).add(r["case_id"])
        n = len(ids) if ids is not None else None
        cov = {f"{p}/{d}{'' if s is None else f'/seed{s}'}/{b}":
               {"n": len(c), "share": len(c) / n if n else None,
                "complete": bool(n) and 100 * len(c) >= MIN_COMPLETE_PCT * n}
               for (p, d, s, b), c in sorted(has.items(), key=lambda kv: str(kv[0]))}
        fit_status = ("not an edited condition" if not any(r["editor"] in DELTA_EDITORS for r in rows)
                      else "no delta logs given: not applied" if self.fit is None else "applied")
        return {"rows": kept, "files": files, "record": {
            "files": [dict(f, path=_rel(f["path"])) for f in audit["files"]],
            "manifest": _rel(self.manifest_path(key[0], key[1])) if ids is not None else None,
            "n_manifest": n, "n_rows_loaded": len(rows), "n_rows_kept": len(kept),
            "duplicate_rows_dropped": audit["duplicate_audit"]["n_duplicate_rows_dropped"],
            "exclusions": {
                "error_rows": {"n": len(errs), "kinds": dict(Counter(e["kind"] for e in errs)),
                               "case_ids": sorted({e["case_id"] for e in errs if e["case_id"]})},
                "fit_error_over_1e-4": {"status": fit_status, "n_rows": sum(fit_bad.values()),
                                        "case_ids": sorted(fit_bad), "n_rows_without_fit_record": unverified},
                "outside_manifest": {"n_rows": sum(outside.values()), "case_ids": sorted(outside)}},
            "degenerate_case_ids": A.degenerate_cases(kept),
            "coverage": cov}}

    def degenerate(self, world):
        w = self.worlds.get(world)
        return set(w["record"]["degenerate_case_ids"]) if w else set()

    def table(self, world, probe="efficacy", decode="greedy", seed=None, ep="lexical", keep=None):
        """Scored {case_id: {budget: outcome}} of one world, optionally restricted to ``keep``."""
        key = (world, probe, decode, seed, ep)
        if key not in self._tabs:
            w = self.worlds.get(world)
            rows = w["rows"] if w else []
            if probe == "locality":
                tab = locality_table(rows, self.cases, self.aliases, decode, seed)
            else:
                tab = A.case_table(rows, self.cases, self.aliases, probe=probe, decode=decode, seed=seed)
            if ep == "semantic":
                tab = self._semantic(tab, rows, world, probe, decode, seed)
            self._tabs[key] = tab
        tab = self._tabs[key]
        return tab if keep is None else A.restrict(tab, keep.__contains__)

    def _semantic(self, lex, rows, world, probe, decode, seed):
        """Replace new/old/es by the judge ensemble's label (NEW / OLD); a row without a verdict, or
        whose verdict was given on different text (item hash), has no semantic outcome."""
        from rt import judge as J
        out = {}
        for r in rows:
            if (r["probe"] != probe or r["decode"] != decode or (seed is not None and r.get("seed") != seed)):
                continue
            v = self.verdicts.get(world + (r["case_id"], r["budget"], r["probe"], r["decode"], r.get("seed")))
            if v is None:
                self._judge["no_verdict"] += 1
                continue
            if v[1] != J.make_item(r, self.cases, self.aliases)["item"]:
                self._judge["item_mismatch"] += 1
                continue
            o = dict(lex[r["case_id"]][r["budget"]], new=v[0] == "NEW", old=v[0] == "OLD", es=int(v[0] == "NEW"))
            out.setdefault(r["case_id"], {})[r["budget"]] = o
        return out

    def gate(self, groups, compute, ep):
        """Completeness first, then ``compute(*keeps)`` on the complete cases of each group, then the
        same without the degenerate cases of the worlds read.  ``groups``: [((model, run), [need])]."""
        comps, keeps, worlds, status = [], [], [], "ok"
        rank = {"ok": 0, "incomplete": 1, "not_run": 2, "no_manifest": 3}
        for (model, run), needs in groups:
            ws = sorted({n[0] for n in needs})
            worlds += [_wid(w) for w in ws]
            ids = self.manifest(model, run)
            if ids is None:
                st, comp = "no_manifest", {"status": "no_manifest", "manifest": _rel(self.manifest_path(model, run))}
            elif not any(w in self.worlds for w in ws):
                st, comp = "not_run", {"status": "not_run", "absent": [_wid(w) for w in ws]}
            else:
                comp = completeness(ids, [(self.table(w, p, d, s, ep), b) for w, p, d, s, b in needs])
                comp["needs"] = [f"{_wid(w)} {p}/{d}{'' if s is None else f'/seed{s}'} {'+'.join(b)}"
                                 for w, p, d, s, b in needs]
                st = "ok" if comp["complete"] else "incomplete"
                keeps.append(set(ids) - set(comp["missing"]))
            comps.append(comp)
            status = max(status, st, key=rank.get)
        block = {"status": status, "worlds": worlds}
        if status == "ok":
            block.update(compute(*keeps))
            bad = [k & set().union(*(self.degenerate(n[0]) for n in needs)) for k, (_, needs) in zip(keeps, groups)]
            flagged = sorted(set().union(*bad))
            block["without_degenerate"] = (
                {"n_flagged": len(flagged), "flagged": flagged, **compute(*(k - b for k, b in zip(keeps, bad)))}
                if flagged else {"n_flagged": 0, "flagged": [], "identical_to_primary": True})
        block["completeness"] = comps[0] if len(comps) == 1 else comps
        return block


# ---------------------------------------------------------------------------------------------
# Estimators built from rt.analysis
# ---------------------------------------------------------------------------------------------
def holm_family(blocks, without_degenerate=False):
    """Holm over a fixed family {name: block}; a member without an estimate enters with p = 1."""
    ps, why = {}, {}
    for name, b in blocks.items():
        src = b
        if without_degenerate and b.get("status") == "ok" and not b["without_degenerate"].get("identical_to_primary"):
            src = b["without_degenerate"]
        p = src.get("p") if b.get("status") == "ok" else None
        if p is None:
            why[name] = b.get("status") if b.get("status") != "ok" else "no p (empty denominator)"
            p = 1.0
        ps[name] = p
    out = A.holm(ps, SIG)
    for name, w in why.items():
        out[name]["not_estimated"] = w
    return out


def verdict(block, h, sign=1):
    """Pass = Holm-rejected (two-sided) and the point estimate in the predicted direction."""
    pt = block.get("point") if block.get("status") == "ok" else None
    direction = pt is not None and sign * pt > 0
    return {"point": pt, "p_holm": h["p_holm"], "reject": h["reject"], "direction_ok": direction,
            "pass": bool(h["reject"] and direction), "predicted_sign": "+" if sign > 0 else "-"}


def arm_diff(ta, tb, metric, a, b, budget="B3", gate="B0"):
    """Paired arm difference at ``budget`` over ``analysis.arm_records`` (cross_arm's records); for
    RR/RRs a case must pass the ES gate at ``gate`` in both arms."""
    ra, rb = A.arm_records(ta, budget, gate), A.arm_records(tb, budget, gate)
    ids = [c for c in sorted(set(ra) & set(rb)) if ra[c][metric] is not None and rb[c][metric] is not None]
    g = f" and ES@{gate} in both arms" if metric in ("RR", "RRs") else ""
    out = A._est([ra[c][metric] - rb[c][metric] for c in ids],
                 f"cases scored at {budget} in both arms{g}; value = {metric}({a}) - {metric}({b})")
    n = len(ids)
    out["mean_a"] = sum(ra[c][metric] for c in ids) / n if n else None
    out["mean_b"] = sum(rb[c][metric] for c in ids) / n if n else None
    return out


def paired_rate_diff(ta, tb, budget, a, b):
    """Paired ES(a) - ES(b) at ``budget`` over cases scored in both conditions."""
    ids = [c for c in sorted(ta) if budget in ta[c] and budget in tb.get(c, {})]
    return A._est([ta[c][budget]["es"] - tb[c][budget]["es"] for c in ids],
                  f"cases with a row at {budget} in both conditions; value = ES({a}) - ES({b})")


def locality(edited, base, b="B3"):
    """Neighbour prompt at ``b``: correct = answer names o_old (a CounterFact neighbour's true value);
    not leaked = answer does not name o_new; edited and unedited model, and edited - base (correct)."""
    ids = [c for c in sorted(edited) if b in edited[c] and b in base.get(c, {})]
    den = f"cases with a locality row at {b} in the edited and the base run; value = "
    out = {"edited_correct": A._est([int(edited[c][b]["old"]) for c in ids], den + "edited answer names o_old"),
           "edited_not_leaked": A._est([int(not edited[c][b]["new"]) for c in ids],
                                       den + "edited answer does not name o_new"),
           "base_correct": A._est([int(base[c][b]["old"]) for c in ids], den + "base answer names o_old"),
           "base_not_leaked": A._est([int(not base[c][b]["new"]) for c in ids], den + "base answer does not name o_new")}
    out["correct_edited_minus_base"] = A._est([int(edited[c][b]["old"]) - int(base[c][b]["old"]) for c in ids],
                                              den + "edited correct - base correct")
    return out


def two_group_flow(ta, tb, flow, a, b, b0="B0", b1="B3"):
    """flow(a) - flow(b) for two disjoint-or-overlapping case pools, each resampled within itself."""
    f = A._FLOWS[flow]
    va = [f(ta[c][b0], ta[c][b1]) for c in A.paired_cases(ta, b0, b1)]
    vb = [f(tb[c][b0], tb[c][b1]) for c in A.paired_cases(tb, b0, b1)]
    out = A.bootstrap_two_groups(va, vb)
    out["denominator"] = (f"cases scored at {b0} and {b1} in each pool; each pool resampled within itself; "
                          f"value = {flow}({a}) - {flow}({b})")
    out["n_shared_cases"] = len(set(ta) & set(tb))
    return out


def alpha_for_target(points, target=ES_TARGET):
    """Smallest grid alpha whose ES point reaches ``target`` and the linear interpolation between
    the last grid point below it and that one.  ``points``: [(alpha, ES)] in increasing alpha."""
    prev = None
    for a, e in points:
        if e >= target:
            if prev is None:
                return {"grid_alpha": a, "interpolated_alpha": None, "note": f"reached at the smallest alpha {a:g}"}
            (a0, e0) = prev
            return {"grid_alpha": a, "interpolated_alpha": a0 + (target - e0) * (a - a0) / (e - e0)}
        prev = (a, e)
    return {"grid_alpha": None, "interpolated_alpha": None, "note": f"not reached up to alpha {points[-1][0]:g}"}


# ---------------------------------------------------------------------------------------------
# Blocks
# ---------------------------------------------------------------------------------------------
def checkpoint(st, tag, ep, full=True):
    """ES drop (H1) and retention (H2) of one model's main pool; with ``full`` the per-checkpoint
    secondaries (RR, RRs, erosion, repair, paraphrase, locality at B3)."""
    N, B = (tag, MAIN, "rome_N"), (tag, MAIN, "base")
    grp = lambda *needs: [((tag, MAIN), list(needs))]                                   # noqa: E731
    tN = lambda k, probe="efficacy": st.table(N, probe, ep=ep, keep=k)                   # noqa: E731
    eff = grp(need(N, "B0", "B3"))
    out = {"ES_drop": st.gate(eff, lambda k: A.es_drop(tN(k)), ep),
           "retention_contrast": st.gate(grp(need(N, "B0", "B3"), need(B, "B0", "B3")),
                                         lambda k: A.retention_contrast(tN(k), st.table(B, ep=ep, keep=k)), ep)}
    if not full:
        return out

    def para(k):
        est = A.es_drop(tN(k, "para0"))
        est["denominator"] = "cases with a para0 row at both B0 and B3; value = ES@B0 - ES@B3 (para0 probe)"
        return est
    out.update({
        "RR": st.gate(eff, lambda k: A.rr(tN(k)), ep),
        "RRs": st.gate(eff, lambda k: A.rr(tN(k), strict=True), ep),
        "erosion": st.gate(eff, lambda k: A.erosion(tN(k)), ep),
        "repair": st.gate(eff, lambda k: A.repair(tN(k)), ep),
        "paraphrase": st.gate(grp(need(N, "B0", "B3", probe="para0")), para, ep),
        "locality_B3": st.gate(grp(need(N, "B3", probe="locality"), need(B, "B3", probe="locality")),
                               lambda k: locality(tN(k, "locality"), st.table(B, "locality", ep=ep, keep=k)), ep)})
    return out


def h2b(st, ep):
    """H2b (32B): ES drop of rome_N in the main pool minus that in the unknown group; independent
    groups, cases resampled within each; one test at alpha .05 outside the Holm families."""
    main, unk = (FOCUS, MAIN, "rome_N"), (FOCUS, H2B, "rome_N")
    bmain, bunk = (FOCUS, MAIN, "base"), (FOCUS, H2B, "base")

    def compute(k_main, k_unk):
        a, b = st.table(main, ep=ep, keep=k_main), st.table(unk, ep=ep, keep=k_unk)
        drop = lambda t: [t[c]["B0"]["es"] - t[c]["B3"]["es"] for c in A.paired_cases(t, "B0", "B3")]  # noqa: E731
        est = A.bootstrap_two_groups(drop(a), drop(b))
        est["denominator"] = ("main-pool cases and unknown-group cases with efficacy rows at B0 and B3; groups "
                              "resampled separately; value = ES drop (main) - ES drop (unknown)")
        est["main_pool"], est["unknown_group"] = A.es_drop(a), A.es_drop(b)
        est["n_shared_cases"] = len(set(a) & set(b))
        ba, bb = st.table(bmain, ep=ep, keep=k_main), st.table(bunk, ep=ep, keep=k_unk)
        ka = [c for c in sorted(ba) if "B0" in ba[c]]
        kb = [c for c in sorted(bb) if "B0" in bb[c]]
        est["group_check_study2_base_B0"] = {
            "main_pool_base_names_old": {"k": sum(ba[c]["B0"]["old"] for c in ka), "n": len(ka), "n_group": len(k_main)},
            "unknown_group_base_names_neither": {"k": sum(not bb[c]["B0"]["old"] and not bb[c]["B0"]["new"] for c in kb),
                                                 "n": len(kb), "n_group": len(k_unk)},
            "note": "descriptive: the groups are defined by the pool screen; this reads the Study-2 base runs"}
        return est
    blk = st.gate([((FOCUS, MAIN), [need(main, "B0", "B3")]), ((FOCUS, H2B), [need(unk, "B0", "B3")])], compute, ep)
    ok = blk["status"] == "ok" and blk.get("p") is not None
    blk["test"] = {"alpha": SIG, "rule": "p <= .05 (two-sided) and point > 0; outside the Holm families",
                   "reject": ok and blk["p"] <= SIG, "direction_ok": ok and blk["point"] > 0,
                   "pass": ok and blk["p"] <= SIG and blk["point"] > 0}
    return blk


def h3(st, ep):
    """H3 (32B): T-P ES > 0, T-P RRs < 0, D-P ES < 0 at B3, paired within case; Holm over the three."""
    tests = {}
    for name, a, b, metric, _sign in H3_TESTS:
        wa, wb = (FOCUS, MAIN, a), (FOCUS, MAIN, b)
        tests[name] = st.gate([((FOCUS, MAIN), [need(wa, "B0", "B3"), need(wb, "B0", "B3")])],
                              lambda k, wa=wa, wb=wb, m=metric, a=a, b=b: arm_diff(
                                  st.table(wa, ep=ep, keep=k), st.table(wb, ep=ep, keep=k), m, a, b), ep)
    h, hd = holm_family(tests), holm_family(tests, without_degenerate=True)
    v = {name: verdict(tests[name], h[name], sign) for name, *_, sign in H3_TESTS}
    return {"tests": tests, "holm": h, "verdicts": v, "pass_all": all(x["pass"] for x in v.values()),
            "holm_without_degenerate": hd}


def arm_secondary(st, ep):
    out = {}
    for name, a, b in ARM_SECONDARY:
        wa, wb = (FOCUS, MAIN, a), (FOCUS, MAIN, b)
        out[name] = {m: st.gate([((FOCUS, MAIN), [need(wa, "B0", "B3"), need(wb, "B0", "B3")])],
                                lambda k, wa=wa, wb=wb, m=m, a=a, b=b: arm_diff(
                                    st.table(wa, ep=ep, keep=k), st.table(wb, ep=ep, keep=k), m, a, b), ep)
                     for m in ARM_METRICS}
    return out


def alpha_dose(st, ep):
    cells = {}
    for cond, alpha, buds in ALPHA_DOSE:
        w = (FOCUS, MAIN, cond)
        for b in buds:
            blk = st.gate([((FOCUS, MAIN), [need(w, b)])], lambda k, w=w, b=b: A.rate(st.table(w, ep=ep, keep=k), b), ep)
            cells[f"alpha={alpha:g}@{b}"] = dict(blk, alpha=alpha, budget=b, condition=cond)
    target = {}
    for b in ("B0", "B3"):
        pts = [(c["alpha"], c.get("point")) for c in cells.values() if c["budget"] == b]
        missing = [f"alpha={a:g}" for a, p in pts if p is None]
        target[b] = ({"status": "undetermined", "cells_without_estimate": missing} if missing
                     else dict(alpha_for_target(pts), status="ok"))
    return {"cells": cells, f"alpha_for_ES_{ES_TARGET:g}": target,
            "note": "alpha 1 is rome_N; alpha 0.5 runs at B0 only"}


def reliability(st, ep):
    """Per-edit reliability under sampling (analysis.sampling_reliability, Study 1's estimator):
    among rome_N greedy-B0 successes, P(>=1 of the seeds fails at B3) vs the same over B0 samples."""
    N, S = (FOCUS, MAIN, "rome_N"), (FOCUS, MAIN, "rome_samp")

    def run(seeds):
        needs = [need(N, "B0")] + [need(S, "B0", "B3", decode="sample", seed=s) for s in seeds]
        return st.gate([((FOCUS, MAIN), needs)], lambda k: A.sampling_reliability(
            st.table(N, ep=ep, keep=k), {s: st.table(S, "efficacy", "sample", s, ep=ep, keep=k) for s in seeds}), ep)
    w = st.worlds.get(S)
    temps = sorted({r["temperature"] for r in w["rows"] if r["decode"] == "sample"}, key=str) if w else []
    return {"seeds_0_2": run(RELIABILITY_SEEDS), "seed_3": run((EXTRA_SEED,)), "temperatures": temps,
            "greedy_gate": "rome_N greedy ES@B0 (rome_samp has no greedy rows)"}


def given(st, ep):
    ws = {c: (FOCUS, MAIN, c) for c in GIVEN}
    grp = lambda *needs: [((FOCUS, MAIN), list(needs))]                                   # noqa: E731
    out = {"ES_GIVEN": {c: st.gate(grp(need(w, "GIVEN")), lambda k, w=w: A.rate(st.table(w, ep=ep, keep=k), "GIVEN"), ep)
                        for c, w in ws.items()}, "contrasts": {}}
    for i, a in enumerate(GIVEN):
        for b in GIVEN[i + 1:]:
            out["contrasts"][f"{a}-{b}"] = st.gate(
                grp(need(ws[a], "GIVEN"), need(ws[b], "GIVEN")),
                lambda k, a=a, b=b: paired_rate_diff(st.table(ws[a], ep=ep, keep=k), st.table(ws[b], ep=ep, keep=k),
                                                     "GIVEN", a, b), ep)
    return out


def repair_comparisons(st, ep):
    out = {}
    for hi, lo in REPAIR_PAIRS:
        wh, wl = (hi, MAIN, "rome_N"), (lo, MAIN, "rome_N")
        blk = st.gate([((hi, MAIN), [need(wh, "B0", "B3")]), ((lo, MAIN), [need(wl, "B0", "B3")])],
                      lambda kh, kl, wh=wh, wl=wl, hi=hi, lo=lo: two_group_flow(
                          st.table(wh, ep=ep, keep=kh), st.table(wl, ep=ep, keep=kl), "repair", hi, lo), ep)
        blk["predicted_sign"] = "-"
        out[f"{hi}-{lo}"] = blk
    return out


def analyse(st, ep):
    """Every pre-registered estimate for one endpoint."""
    cps = {t: checkpoint(st, t, ep) for t in R1}
    h1 = {t: cps[t]["ES_drop"] for t in R1}
    h2 = {t: cps[t]["retention_contrast"] for t in R1}
    h1h, h2h = holm_family(h1), holm_family(h2)
    out = {"endpoint": ep, "checkpoints": cps}
    out["H1"] = {"family": "ES drop (B0 - B3, rome_N, efficacy, greedy) at the six R1 checkpoints; Holm",
                 "hypotheses_at": list(H1_AT), "holm": h1h,
                 "verdicts": {t: verdict(h1[t], h1h[t]) for t in H1_AT},
                 "holm_without_degenerate": holm_family(h1, True)}
    out["H2"] = {"family": "retention contrast at the six R1 checkpoints (conditioning on the Study-2 base "
                           "run's B0); Holm", "hypotheses_at": list(H2_AT), "holm": h2h,
                 "verdicts": {t: verdict(h2[t], h2h[t]) for t in H2_AT},
                 "holm_without_degenerate": holm_family(h2, True)}
    out["H2b"] = h2b(st, ep)
    out["H3"] = h3(st, ep)
    ero = {t: cps[t]["erosion"] for t in R1}
    out["secondary"] = {
        "arm_contrasts_32B": arm_secondary(st, ep),
        "erosion_ci_above_zero": {t: (b["ci95"][0] > 0 if b["status"] == "ok" and b.get("ci95") else None)
                                  for t, b in ero.items()},
        "repair_comparisons": repair_comparisons(st, ep),
        "editors_32B": {c: st.gate([((FOCUS, MAIN), [need((FOCUS, MAIN, c), "B0", "B3")])],
                                   lambda k, c=c: A.es_drop(st.table((FOCUS, MAIN, c), ep=ep, keep=k)), ep)
                        for c in EDITORS_32B},
        "post_training_recipes": {t: (checkpoint(st, t, ep, full=False) if st.has_model(t) else {"status": "not_run"})
                                  for t in RECIPES},
        "alpha_dose_32B": alpha_dose(st, ep),
        "sampling_reliability_32B": reliability(st, ep),
        "given_chain_32B": given(st, ep)}
    b32, b70 = h1["r1qwen32b"], h1["r1llama70b"]
    ci_ok = {t: (b["status"] == "ok" and b.get("ci95") is not None and b["ci95"][0] > 0) for t, b in
             (("r1qwen32b", b32), ("r1llama70b", b70))}
    out["submission_gate"] = {"rule": "H1 and H2 pass at 32B, and the primary endpoint's ES drop keeps a CI above "
                                      "zero at 32B and 70B (prereg §7)",
                              "H1_32B": out["H1"]["verdicts"]["r1qwen32b"]["pass"],
                              "H2_32B": out["H2"]["verdicts"]["r1qwen32b"]["pass"], "ES_drop_ci_above_zero": ci_ok}
    g = out["submission_gate"]
    g["pass"] = bool(g["H1_32B"] and g["H2_32B"] and all(ci_ok.values()))
    return out


# ---------------------------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------------------------
def _f(x, d=3):
    return "—" if x is None else f"{x:.{d}f}"


def _cell(b, d=3):
    b = b or {}
    if b.get("status", "ok") != "ok" or b.get("point") is None:
        c = b.get("completeness")
        c = c if isinstance(c, dict) else {}
        extra = f" {c['n_complete']}/{c['n_manifest']}" if "n_complete" in c else ""
        return f"— ({b.get('status', 'n=0')}{extra})"
    return f"{b['point']:.{d}f} [{b['ci95'][0]:.{d}f}, {b['ci95'][1]:.{d}f}]"


def _blocks(obj, path=""):
    """(path, block) for every gated block in an analysis tree."""
    if isinstance(obj, dict):
        if "status" in obj and "worlds" in obj:
            yield path, obj
        for k, v in obj.items():
            if k not in ("without_degenerate", "completeness"):
                yield from _blocks(v, f"{path}/{k}" if path else k)


def render_md(out):
    prim = out["primary"]
    L = ["# Study 2 (generated by `src/rt/study2.py`; numbers in `study2.json`)", "",
         f"Primary endpoint: **{prim}** ({out['endpoint_decision']['rule']}; kappa_es="
         f"{out['endpoint_decision']['kappa_es']}, kappa_rr={out['endpoint_decision']['kappa_rr']}). "
         "Bootstrap 10,000 case resamples, seed 42, percentile 95% CI, two-sided p, cases in sorted case_id "
         f"order. An estimate is shown only when ≥{MIN_COMPLETE_PCT}% of its manifest's cases have every row it "
         "needs; `—` gives the status and complete/manifest cases.", ""]
    for ep, an in out["analyses"].items():
        L += [f"## Hypotheses ({ep}{', primary' if ep == prim else ''})", "",
              "| test | checkpoint | n | ES@B0 | ES@B3 | estimate [95% CI] | p | Holm p | pass |",
              "|---|---|---|---|---|---|---|---|---|"]
        for fam, key in (("H1", "ES_drop"), ("H2", "retention_contrast")):
            for t in R1:
                b, h = an["checkpoints"][t][key], an[fam]["holm"][t]
                v = an[fam]["verdicts"].get(t)
                L.append(f"| {fam} | {t} | {b.get('n', '—')} | {_f(b.get('es_b0'))} | {_f(b.get('es_b1'))} | {_cell(b)} | "
                         f"{_f(b.get('p'), 4)} | {_f(h['p_holm'], 4)} | {'—' if v is None else ('✓' if v['pass'] else '✗')} |")
        b = an["H2b"]
        L.append(f"| H2b | {FOCUS} main − unknown | {b.get('n', '—')} | | | {_cell(b)} | {_f(b.get('p'), 4)} | "
                 f"(single test) | {'✓' if b['test']['pass'] else '✗'} |")
        for name, *_ in H3_TESTS:
            b, h, v = an["H3"]["tests"][name], an["H3"]["holm"][name], an["H3"]["verdicts"][name]
            L.append(f"| H3 {name} ({v['predicted_sign']}) | {FOCUS} | {b.get('n', '—')} | | | {_cell(b)} | "
                     f"{_f(b.get('p'), 4)} | {_f(h['p_holm'], 4)} | {'✓' if v['pass'] else '✗'} |")
        g = an["submission_gate"]
        L += ["", f"H1 at 32B/70B, H2 at 14B/32B/70B: pass = Holm-rejected over the six and in the predicted "
                  f"direction. H3 all three: {'✓' if an['H3']['pass_all'] else '✗'}. Submission gate (§7): "
                  f"{'PASS' if g['pass'] else 'FAIL'} (H1 32B {g['H1_32B']}, H2 32B {g['H2_32B']}, "
                  f"ES-drop CI > 0 {g['ES_drop_ci_above_zero']}).", ""]
    an = out["analyses"][prim]
    s = an["secondary"]
    L += [f"## Secondary ({prim})", "", "| per checkpoint | RR | RRs | erosion | repair | para0 ES drop | "
          "locality@B3 correct (edited − base) |", "|---|---|---|---|---|---|---|"]
    for t in R1:
        c = an["checkpoints"][t]
        loc = c["locality_B3"]
        L.append(f"| {t} | {_cell(c['RR'])} | {_cell(c['RRs'])} | {_cell(c['erosion'])} | {_cell(c['repair'])} | "
                 f"{_cell(c['paraphrase'])} | {_cell(loc.get('correct_edited_minus_base', loc))} |")
    L += ["", "| 32B arm contrast (B3) | ES | RR | RRs |", "|---|---|---|---|"]
    for name, ms in s["arm_contrasts_32B"].items():
        L.append(f"| {name} | " + " | ".join(_cell(ms[m]) for m in ARM_METRICS) + " |")
    L += ["", "| other | estimate [95% CI] |", "|---|---|"]
    for name, b in s["repair_comparisons"].items():
        L.append(f"| repair {name} (predicted −) | {_cell(b)} |")
    for c, b in s["editors_32B"].items():
        L.append(f"| ES drop {c} (32B) | {_cell(b)} |")
    for t, blk in s["post_training_recipes"].items():
        L.append(f"| {t} ES drop / retention | {_cell(blk.get('ES_drop', blk))} / "
                 f"{_cell(blk.get('retention_contrast', blk))} |")
    for k, b in s["alpha_dose_32B"]["cells"].items():
        L.append(f"| ES {k} | {_cell(b)} |")
    for b_, r in s["alpha_dose_32B"][f"alpha_for_ES_{ES_TARGET:g}"].items():
        L.append(f"| alpha for ES {ES_TARGET:g} @{b_} | grid {r.get('grid_alpha')}, interpolated "
                 f"{_f(r.get('interpolated_alpha'), 2)} ({r['status']}) |")
    for k in ("seeds_0_2", "seed_3"):
        r = s["sampling_reliability_32B"][k]
        L.append(f"| reliability {k}: fail at B3 / B0 noise floor / excess | "
                 + (" / ".join(_cell(r.get(x)) for x in ("fail_any_b1", "fail_any_b0_noise_floor", "excess"))
                    if r["status"] == "ok" else _cell(r)) + " |")
    for c, b in s["given_chain_32B"]["ES_GIVEN"].items():
        L.append(f"| ES after given chain {c} | {_cell(b)} |")
    for c, b in s["given_chain_32B"]["contrasts"].items():
        L.append(f"| given chain {c} | {_cell(b)} |")
    L += ["", "## Exclusions and completeness", "",
          "| world | manifest | rows kept | error rows | fit > 1e-4 (cases) | outside manifest | degenerate cases |",
          "|---|---|---|---|---|---|---|"]
    for wid, r in out["worlds"].items():
        e = r["exclusions"]
        L.append(f"| {wid} | {r['n_manifest']} | {r['n_rows_kept']} | {e['error_rows']['n']} | "
                 f"{len(e['fit_error_over_1e-4']['case_ids'])} ({e['fit_error_over_1e-4']['status']}) | "
                 f"{e['outside_manifest']['n_rows']} | {len(r['degenerate_case_ids'])} |")
    bad = [(p, b) for p, b in _blocks(an) if b["status"] != "ok"]
    L += ["", f"Estimates without a number ({prim}): {len(bad)}."]
    for p, b in bad:
        c = b.get("completeness")
        cs = c if isinstance(c, list) else [c]
        det = "; ".join(f"{x['n_complete']}/{x['n_manifest']} complete" if "n_complete" in x else x.get("status", "")
                        for x in cs if x)
        L.append(f"- `{p}`: {b['status']} ({det})")
    if out["ignored_worlds"]:
        L += ["", "Ignored run tags (not s2/s2h2b): " + ", ".join(sorted(out["ignored_worlds"]))]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------
def _expand_logs(items):
    out = []
    for it in items or ():
        out += sorted(glob.glob(os.path.join(it, "*.jsonl"))) if os.path.isdir(it) else sorted(glob.glob(it))
    return out


def run(results, manifests, cases_path, aliases_path, delta_logs=(), judged=(), switch=None):
    """The whole analysis as one dict (the CLI writes it and its markdown)."""
    cases = {c["case_id"]: c for c in (json.loads(l) for l in open(cases_path) if l.strip())}
    aliases = json.load(open(aliases_path))
    log_files = _expand_logs(delta_logs)
    fit, fit_files = read_fit_logs(log_files) if log_files else (None, [])
    verdicts, judge_info = load_verdicts(judged) if judged else (None, None)
    decision = endpoint_decision(switch, bool(judged))
    if decision["primary"] == "semantic" and not judge_info["as_preregistered"]:
        raise SystemExit("semantic endpoint is primary but the judge outputs are not the pre-registered ones "
                         f"({N_JUDGES} judges, prompt sha {PREREG_PROMPT_SHA[:12]}..., both option orders): "
                         f"{json.dumps(judge_info['judges'], default=str)[:2000]}")
    st = Study2(results, manifests, cases, aliases, fit, verdicts)
    eps = [decision["primary"]] + ([e for e in ("lexical", "semantic") if e != decision["primary"]] if judged else [])
    prereg = os.path.join(REPO, "prereg-arr.md")
    out = {"_meta": {
        "generator": "src/rt/study2.py", "git_head": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain", "--", "src")),
        "code_sha256": {p: A.file_record(os.path.join(REPO, p))["sha256"] for p in CODE},
        "prereg": dict(A.file_record(prereg), path="prereg-arr.md") if os.path.exists(prereg) else None,
        "inputs": {"results_dir": _rel(results), "cases": _record(cases_path), "aliases": _record(aliases_path),
                   "manifests": None, "delta_logs": fit_files, "judged": judge_info, "skipped_files": st.skipped},
        "bootstrap": {"n_boot": A.N_BOOT, "seed": A.SEED, "ci": A.CI, "unit": "case",
                      "ci_rule": "sorted replicate means at int(.025B), int(.975B)",
                      "p_rule": "2*min(#<=0, #>=0)/B, capped at 1", "case_order": "sorted case_id",
                      "independent_groups": "analysis.bootstrap_two_groups (each group resampled within itself)"},
        "completeness_rule": f">= {MIN_COMPLETE_PCT}% of the manifest's cases have every needed row",
        "fit_tolerance": FIT_TOL,
        "holm": "alpha .05; a family member without an estimate enters with p = 1 (family size unchanged)"},
        "endpoint_decision": decision, "primary": decision["primary"],
        "worlds": {_wid(k): w["record"] for k, w in st.worlds.items()},
        "ignored_worlds": st.ignored}
    out["analyses"] = {ep: analyse(st, ep) for ep in eps}
    out["_meta"]["inputs"]["manifests"] = {                   # every manifest the analysis read
        f"{m}/{r}": _record(st.manifest_path(m, r)) if ids is not None else None
        for (m, r), ids in sorted(st._manifests.items())}
    if verdicts is not None:
        out["_meta"]["inputs"]["judged"]["rows_without_semantic_outcome"] = dict(st._judge)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--results", default="results/rt/s2")
    ap.add_argument("--manifests", default="experiments/rt/pools/study2")
    ap.add_argument("--cases", default="data/counterfact.jsonl")
    ap.add_argument("--aliases", default="data/aliases.json")
    ap.add_argument("--delta-logs", nargs="*", default=["results/rt/deltas_logs/s2", "results/rt/deltas_logs/s2_h2b"],
                    help="rt.deltas shard-log directories or globs (fit-error exclusion)")
    ap.add_argument("--judged", action="append", default=[], help="NAME=GLOB of one judge's rt.judge outputs")
    ap.add_argument("--switch", default=None, help="JSON with kappa_es/kappa_rr (or an rt.annotate score report)")
    ap.add_argument("--out", default="paperwriting/revision/study2.json")
    ap.add_argument("--md", default=None, help="markdown summary (default: --out with .md)")
    a = ap.parse_args(argv)
    out = run(a.results, a.manifests, a.cases, a.aliases, a.delta_logs, a.judged, a.switch)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False, default=str)
        fh.write("\n")
    md = a.md or os.path.splitext(a.out)[0] + ".md"
    with open(md, "w") as fh:
        fh.write(render_md(out))
    an = out["analyses"][out["primary"]]
    if out["endpoint_decision"].get("note"):
        print(f"[study2] NOTE: {out['endpoint_decision']['note']}", file=sys.stderr)
    unfit = [w for w, r in out["worlds"].items()
             if r["exclusions"]["fit_error_over_1e-4"]["status"].startswith("no delta logs")]
    if unfit:
        print(f"[study2] NOTE: fit-error exclusion not applied (no delta logs) to {len(unfit)} edited worlds, "
              f"e.g. {unfit[0]}; pass --delta-logs", file=sys.stderr)
    print(f"[study2] primary={out['primary']} wrote {_rel(a.out)} and {_rel(md)}; "
          f"H1 {({t: v['pass'] for t, v in an['H1']['verdicts'].items()})} "
          f"H2 {({t: v['pass'] for t, v in an['H2']['verdicts'].items()})} "
          f"H2b {an['H2b']['test']['pass']} H3 {an['H3']['pass_all']} gate {an['submission_gate']['pass']}")


if __name__ == "__main__":
    sys.exit(main())
