"""Estimators over per-case records for Study 1 (reanalysis) and Study 2 (REVISION.md §1-§3).

Scoring is never re-implemented here.  A generation is scored with ``metrics.hit`` on
``metrics._without_subject(text, s)`` exactly as ``metrics.score`` does:

    new  = answer names o_new            old = answer names o_old
    ES   = new and not old               CLR = chain names o_old
    RR   = old at B3, among cases with ES at B0 (permissive; "old and not new" is RRs, strict)

Every estimator returns a dict with ``point``, ``ci95`` (percentile bootstrap), ``p`` (two-sided
bootstrap p against zero), ``n`` and ``denominator`` (which cases enter, in words).  The bootstrap
is the one ``cross_arm.paired_diff`` uses, so numbers from the two modules can be compared
directly: 10,000 resamples of cases, ``random.Random(42)``, the replicate means sorted, the CI read
at indices ``int(.025 B)`` and ``int(.975 B)``, ``p = 2 min(#{mean <= 0}, #{mean >= 0}) / B``.
Per-case values always enter in sorted ``case_id`` order (cross_arm's order), so an estimate does
not depend on how rows were sharded across files.  A conditional rate (RR, retention) resamples
only the cases that pass its gate, as ``metrics.score_bootstrap`` and ``cross_arm`` do.

Pipeline: ``load_rows`` (legacy or v2 jsonl, one normalised row shape, duplicate-world audit) ->
``case_table`` (one world, {case_id: {budget: outcome}}) -> the estimators below.
"""
import functools
import hashlib
import json
import os
import random
from collections import Counter

import numpy as np

import cross_arm
import metrics
from score_pilot import _is_degenerate

N_BOOT = 10000
SEED = 42
CI = 0.95

# ---------------------------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------------------------
# REVISION.md §4 row schema.  Legacy rows carry a subset; the rest are filled on load.
V2_FIELDS = ("case_id", "model_tag", "editor", "target_tag", "budget", "probe", "condition", "arm",
             "alpha", "decode", "seed", "temperature", "q", "cot", "answer", "chain_end",
             "n_chain_tokens", "n_answer_tokens", "delta_sha")
V2_MARKERS = ("model_tag", "condition", "arm", "alpha")      # no legacy row carries any of these
V2_REQUIRED = ("case_id", "model_tag", "editor", "budget", "probe", "condition", "arm", "decode",
               "answer")
WORLD_KEY = ("model_tag", "editor", "target_tag", "condition", "arm", "alpha", "case_id", "budget",
             "probe", "decode", "seed", "temperature", "q")
BASE_EDITORS = ("none", "base")


def file_record(path):
    """{path, sha256, bytes} of one input file."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return {"path": path, "sha256": h.hexdigest(), "bytes": os.path.getsize(path)}


def normalise_row(raw, meta=None, defaults=None, source=None):
    """One generation row in the v2 shape, whichever schema it was written in.

    v2 rows (any of ``model_tag/condition/arm/alpha`` present) must carry every required field and
    are copied as they are.  Legacy rows (edit_loop / base_probe) are completed field by field:
    a value in the row wins, then ``defaults`` (the caller's labels for the file, e.g.
    ``{"model_tag": "r1qwen32b", "arm": "T"}``), then the shard's ``_meta`` header for model_tag
    and editor, then the legacy meaning.  Legacy meanings: an edited row is condition "native",
    arm "N", alpha 1.0; a base_probe row (probe "base") is the unedited model answering the
    efficacy prompt, so it becomes probe "efficacy", editor "none", condition "base".
    """
    meta, defaults = meta or {}, defaults or {}
    where = f"{source[0]}:{source[1]}" if source else "<row>"
    if any(k in raw for k in V2_MARKERS):
        missing = [k for k in V2_REQUIRED if k not in raw]
        if missing:
            raise ValueError(f"v2 row missing required fields {missing} at {where}")
        row = {k: raw.get(k) for k in V2_FIELDS}
        row["schema"] = "v2"
    else:
        base = raw.get("probe") == "base"
        legacy = {"model_tag": meta.get("model_tag"),
                  "editor": "none" if base else meta.get("editor"),
                  "condition": "base" if base else "native",
                  "arm": None if base else "N",
                  "alpha": None if base else 1.0,
                  "decode": "greedy"}
        row = {}
        for k in V2_FIELDS:
            if k in raw:
                row[k] = raw[k]
            elif k in defaults:
                row[k] = defaults[k]
            else:
                row[k] = legacy.get(k)
        if base:
            row["probe"] = "efficacy"
        row["schema"] = "legacy"
    if not row.get("case_id") or not row.get("budget") or not row.get("probe"):
        raise ValueError(f"row without case_id/budget/probe at {where}")
    row["source"] = {"path": source[0], "line": source[1]} if source else None
    return row


def is_base(row):
    """True for a generation of the unedited model."""
    return row.get("condition") == "base" or str(row.get("editor") or "none").lower() in BASE_EDITORS


def load_rows(paths, defaults=None):
    """Read jsonl shards into normalised rows plus an input audit.

    ``_meta`` headers set model_tag/editor for the legacy rows that follow them; error rows and
    rows without a probe are counted and skipped.  A scientific world is keyed by ``WORLD_KEY``
    (model, editor, target, condition, arm, alpha, case, budget, probe, decode, seed, temperature,
    prompt).  A repeated key is dropped when its whole parsed row is identical to the first copy and
    is a hard error when any field differs (the rule of ``cross_arm._load_efficacy_worlds``).
    Returns ``(rows, audit)``; the audit lists every file with its sha256 and line counts.
    """
    rows, files, seen = [], [], {}
    for path in paths:
        rec, counts, meta = file_record(path), Counter(), {}
        with open(path, encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                raw = json.loads(line)
                if raw.get("_meta"):
                    meta = raw
                    counts["meta"] += 1
                    continue
                if raw.get("error"):
                    counts["error"] += 1
                    continue
                if not raw.get("probe"):
                    counts["no_probe"] += 1
                    continue
                row = normalise_row(raw, meta, defaults, (path, line_no))
                key = tuple(row[k] for k in WORLD_KEY)
                prior = seen.get(key)
                if prior is not None:
                    if raw != prior["raw"]:
                        changed = sorted(k for k in set(raw) | set(prior["raw"])
                                         if raw.get(k) != prior["raw"].get(k))
                        first = prior["row"]["source"]
                        raise ValueError(
                            f"conflicting duplicate world {dict(zip(WORLD_KEY, key))}: "
                            f"differing_fields={changed}; first={first['path']}:{first['line']}; "
                            f"duplicate={path}:{line_no}")
                    prior["copies"] += 1
                    counts["duplicate"] += 1
                    continue
                seen[key] = {"raw": raw, "row": row, "copies": 1}
                counts[row["schema"]] += 1
                rows.append(row)
        files.append({**rec, "counts": dict(sorted(counts.items()))})
    dups = [{"key": dict(zip(WORLD_KEY, k)), "copies": v["copies"]}
            for k, v in seen.items() if v["copies"] > 1]
    audit = {"files": files, "n_rows": len(rows),
             "duplicate_audit": {"status": "PASS", "world_key": list(WORLD_KEY),
                                 "n_duplicate_keys": len(dups),
                                 "n_duplicate_rows_dropped": sum(d["copies"] - 1 for d in dups),
                                 "duplicate_keys": dups}}
    return rows, audit


def select(rows, **fields):
    """Rows whose normalised fields equal every given value (e.g. ``arm="T", decode="greedy"``)."""
    return [r for r in rows if all(r.get(k) == v for k, v in fields.items())]


def degenerate_cases(rows):
    """Case ids with a degenerate answer anywhere in ``rows`` (any probe, budget or decode).

    This is ``src/score_pilot.py --drop-degenerate``: its ``_is_degenerate`` test applied to every
    row of a run's shards, and every row of a flagged case dropped.
    """
    return sorted({r["case_id"] for r in rows if _is_degenerate(r.get("answer") or "")})


def drop_cases(rows, case_ids):
    bad = set(case_ids)
    return [r for r in rows if r["case_id"] not in bad]


# ---------------------------------------------------------------------------------------------
# Scoring: one outcome per (case, budget)
# ---------------------------------------------------------------------------------------------
def score_row(row, case, aliases):
    """Outcome of one generation, scored with metrics.hit after metrics._without_subject."""
    s = case.get("s") or ""
    ans = metrics._without_subject(row.get("answer") or "", s)
    cot = metrics._without_subject(row.get("cot") or "", s)
    new = bool(metrics.hit(ans, case["o_new"], aliases))
    old = bool(metrics.hit(ans, case["o_old"], aliases))
    return {"new": new, "old": old, "es": int(new and not old),
            "clr": int(bool(metrics.hit(cot, case["o_old"], aliases))),
            "words": len((row.get("answer") or "").split())}


def case_table(rows, cases, aliases, probe="efficacy", decode="greedy", seed=None, **fields):
    """{case_id: {budget: outcome}} for one world.

    Rows are filtered by probe, decode, optional seed and any further normalised field
    (``arm="T"``, ``condition="base"`` ...).  After filtering, a case may have at most one row per
    budget; a second one means two worlds were mixed (two arms, two seeds ...) and raises.
    """
    tab = {}
    for r in rows:
        if r["probe"] != probe or r["decode"] != decode:
            continue
        if seed is not None and r.get("seed") != seed:
            continue
        if any(r.get(k) != v for k, v in fields.items()):
            continue
        cid = r["case_id"]
        if cid not in cases:
            raise KeyError(f"case {cid} is not in the case file")
        slot = tab.setdefault(cid, {})
        if r["budget"] in slot:
            src = r.get("source") or {}
            raise ValueError(f"two rows for case {cid} at {r['budget']} "
                             f"({src.get('path')}:{src.get('line')}); select one world "
                             "(arm/condition/alpha/seed)")
        slot[r["budget"]] = score_row(r, cases[cid], aliases)
    return tab


def restrict(tab, keep):
    """Sub-table of the cases for which ``keep(case_id)`` is true."""
    return {c: v for c, v in tab.items() if keep(c)}


def paired_cases(tab, *budgets):
    return [c for c in sorted(tab) if all(b in tab[c] for b in budgets)]


def name_contains_old(case):
    """Subject contains o_old as a whole word, case-insensitively (metrics' word-boundary rule)."""
    return bool(metrics._wb(case["o_old"]).search((case.get("s") or "").lower()))


# ---------------------------------------------------------------------------------------------
# Bootstrap (cross_arm.paired_diff's resampling, vectorised)
# ---------------------------------------------------------------------------------------------
@functools.lru_cache(maxsize=16)
def _indices(n, n_boot, seed):
    """Resample indices in exactly the order cross_arm.paired_diff draws them."""
    rr = random.Random(seed).randrange
    return np.array([rr(n) for _ in range(n * n_boot)], dtype=np.int64).reshape(n_boot, n)


def _ci_p(boots, n_boot, ci):
    boots = sorted(boots)
    if ci == CI:                                     # cross_arm's literal indices
        lo, hi = int(0.025 * n_boot), int(0.975 * n_boot)
    else:
        lo, hi = int((1 - ci) / 2 * n_boot), int((1 + ci) / 2 * n_boot)
    hi = min(hi, n_boot - 1)
    p = 2 * min(sum(b <= 0 for b in boots), sum(b >= 0 for b in boots)) / n_boot
    return [float(boots[lo]), float(boots[hi])], min(float(p), 1.0)


def _replicate_means(vals, idx):
    """Mean of every resample.  Integer data are summed exactly (identical to Python's sum)."""
    n = len(vals)
    if all(isinstance(v, (int, bool, np.integer)) for v in vals):
        sums = np.asarray(vals, dtype=np.int64)[idx].sum(axis=1)
        return [int(s) / n for s in sums]
    return [sum(vals[i] for i in row) / n for row in idx.tolist()]


def bootstrap_mean(values, n_boot=N_BOOT, seed=SEED, ci=CI):
    """Mean of per-case values with percentile CI and two-sided p against zero.

    Identical to ``cross_arm.paired_diff`` given the same values in the same order (it is the
    differences' mean there), before cross_arm's 4-decimal rounding.
    """
    vals = list(values)
    n = len(vals)
    if n == 0:
        return {"point": None, "ci95": None, "p": None, "n": 0}
    boots = _replicate_means(vals, _indices(n, n_boot, seed))
    ci95, p = _ci_p(boots, n_boot, ci)
    return {"point": sum(vals) / n, "ci95": ci95, "p": p, "n": n}


def bootstrap_two_groups(a, b, n_boot=N_BOOT, seed=SEED, ci=CI):
    """mean(a) - mean(b) for two disjoint case groups; each group resampled within itself."""
    a, b = list(a), list(b)
    na, nb = len(a), len(b)
    if not na or not nb:
        return {"point": None, "ci95": None, "p": None, "n": [na, nb]}
    rr = random.Random(seed).randrange
    boots = []
    for _ in range(n_boot):
        sa = sum(a[rr(na)] for _ in range(na))
        sb = sum(b[rr(nb)] for _ in range(nb))
        boots.append(sa / na - sb / nb)
    ci95, p = _ci_p(boots, n_boot, ci)
    return {"point": sum(a) / na - sum(b) / nb, "ci95": ci95, "p": p, "n": [na, nb]}


def _est(values, denominator, **extra):
    out = bootstrap_mean(values)
    out["denominator"] = denominator
    out.update(extra)
    return out


def holm(pvalues, alpha=0.05):
    """Holm step-down over {name: p}.  Per test: raw p, rank, threshold alpha/(m-rank+1),
    adjusted p = running max of (m-rank+1)*p capped at 1, and reject (adjusted p <= alpha)."""
    items = sorted(((k, p) for k, p in pvalues.items() if p is not None), key=lambda kv: (kv[1], kv[0]))
    m, running, out = len(items), 0.0, {}
    for i, (name, p) in enumerate(items):
        running = min(1.0, max(running, (m - i) * p))
        out[name] = {"p": p, "rank": i + 1, "m": m, "threshold": alpha / (m - i),
                     "p_holm": running, "reject": running <= alpha}
    return out


# ---------------------------------------------------------------------------------------------
# Edit efficacy and the ES gap
# ---------------------------------------------------------------------------------------------
def rate(tab, budget, key="es", denominator=None):
    """Share of cases with a row at ``budget`` whose outcome ``key`` holds."""
    cids = [c for c in sorted(tab) if budget in tab[c]]
    return _est([int(bool(tab[c][budget][key])) for c in cids],
                denominator or f"cases with a row at {budget}; value = {key}@{budget}")


def es_drop(tab, b0="B0", b1="B3"):
    """Paired ES(b0) - ES(b1) over cases scored at both budgets (positive = the edit is lost)."""
    cids = paired_cases(tab, b0, b1)
    e0 = [tab[c][b0]["es"] for c in cids]
    e1 = [tab[c][b1]["es"] for c in cids]
    out = _est([x - y for x, y in zip(e0, e1)],
               f"cases with an efficacy row at both {b0} and {b1}; value = ES@{b0} - ES@{b1}")
    n = len(cids)
    out["es_b0"] = sum(e0) / n if n else None
    out["es_b1"] = sum(e1) / n if n else None
    return out


def rr(tab, b0="B0", b1="B3", strict=False):
    """Reversion: the answer at b1 names o_old (strict: and not o_new), among cases with ES at b0."""
    cids = [c for c in paired_cases(tab, b0, b1) if tab[c][b0]["es"]]
    vals = [int(tab[c][b1]["old"] and not (strict and tab[c][b1]["new"])) for c in cids]
    what = "old and not new" if strict else "old"
    return _est(vals, f"cases with ES@{b0} and a row at {b1}; value = answer@{b1} names {what}")


def clr(tab, b1="B3"):
    """Chain leak: the chain at b1 names o_old, over all cases with a row at b1 (no gate)."""
    return rate(tab, b1, "clr", f"cases with a row at {b1}; value = chain@{b1} names o_old")


def erosion(tab, b0="B0", b1="B3"):
    """P(ES@b0 and not ES@b1) over cases scored at both budgets."""
    cids = paired_cases(tab, b0, b1)
    return _est([int(tab[c][b0]["es"] and not tab[c][b1]["es"]) for c in cids],
                f"cases with rows at {b0} and {b1}; value = ES@{b0} and not ES@{b1}")


def repair(tab, b0="B0", b1="B3"):
    """P(not ES@b0 and ES@b1) over cases scored at both budgets."""
    cids = paired_cases(tab, b0, b1)
    return _est([int(not tab[c][b0]["es"] and tab[c][b1]["es"]) for c in cids],
                f"cases with rows at {b0} and {b1}; value = not ES@{b0} and ES@{b1}")


_FLOWS = {"erosion": lambda o0, o1: int(o0["es"] and not o1["es"]),
          "repair": lambda o0, o1: int(not o0["es"] and o1["es"]),
          "es_drop": lambda o0, o1: o0["es"] - o1["es"]}


def flow_difference(tab_a, tab_b, flow="erosion", b0="B0", b1="B3"):
    """Paired difference of a per-case flow (erosion, repair or es_drop) between two checkpoints,
    over the cases both scored at both budgets: value = flow(a) - flow(b)."""
    f = _FLOWS[flow]
    cids = [c for c in paired_cases(tab_a, b0, b1) if b0 in tab_b.get(c, {}) and b1 in tab_b[c]]
    vals = [f(tab_a[c][b0], tab_a[c][b1]) - f(tab_b[c][b0], tab_b[c][b1]) for c in cids]
    return _est(vals, f"cases scored at {b0} and {b1} in both checkpoints; value = {flow}(a) - {flow}(b)")


# ---------------------------------------------------------------------------------------------
# Edited versus native answers
# ---------------------------------------------------------------------------------------------
def retention_contrast(edited, base, b0="B0", b1="B3"):
    """Edit specificity.  Cases where the base answers o_old at b0 and the edit succeeds at b0 (all
    four rows present).  value = 1{edited loses ES at b1} - 1{base stops answering o_old at b1},
    paired within case; also each loss rate and the 2x2 of (edited lost, base lost)."""
    cids = [c for c in paired_cases(edited, b0, b1)
            if b0 in base.get(c, {}) and b1 in base[c] and base[c][b0]["old"] and edited[c][b0]["es"]]
    e = [1 - edited[c][b1]["es"] for c in cids]
    b = [1 - int(base[c][b1]["old"]) for c in cids]
    den = (f"cases with base answer naming o_old at {b0} and edited ES at {b0} "
           f"(edited and base rows at {b0} and {b1})")
    out = _est([x - y for x, y in zip(e, b)], den + "; value = edited lost ES - base lost o_old")
    out["edited_loss"] = _est(e, den + f"; value = not ES@{b1} (edited)")
    out["base_loss"] = _est(b, den + f"; value = base answer@{b1} does not name o_old")
    out["table_2x2"] = {f"edited_lost={x},base_lost={y}": sum(1 for p, q in zip(e, b) if (p, q) == (x, y))
                        for x in (1, 0) for y in (1, 0)}
    return out


STRATA = {"known_B0_B3": (True, True), "known_B3_only": (False, True),
          "known_B0_only": (True, False), "unknown": (False, False)}


def knowledge_strata(edited, base, b0="B0", b1="B3"):
    """ES drop within strata of the base model's own knowledge of o_old at b0 and b1."""
    out = {}
    for name, (k0, k1) in STRATA.items():
        cids = {c for c in paired_cases(edited, b0, b1)
                if b0 in base.get(c, {}) and b1 in base[c]
                and bool(base[c][b0]["old"]) == k0 and bool(base[c][b1]["old"]) == k1}
        est = es_drop(restrict(edited, cids.__contains__), b0, b1)
        est["denominator"] = (f"base answer names o_old at {b0}={k0}, at {b1}={k1}; "
                              + est["denominator"])
        out[name] = est
    return out


def qualified_es_drop(edited, base, b0="B0", b1="B3"):
    """ES drop over cases whose own base model answers o_old at b0 (knows the fact it is editing)."""
    keep = {c for c in base if b0 in base[c] and base[c][b0]["old"]}
    est = es_drop(restrict(edited, keep.__contains__), b0, b1)
    est["denominator"] = f"base answer names o_old at {b0}; " + est["denominator"]
    return est


# ---------------------------------------------------------------------------------------------
# Failure anatomy, length, sampling reliability
# ---------------------------------------------------------------------------------------------
def _failure_kind(o):
    return "both" if (o["new"] and o["old"]) else ("old_only" if o["old"] else "neither")


def failure_anatomy(tab, b0="B0", b1="B3"):
    """What a failed answer at b1 contains: both values / o_old only / neither (a failure cannot
    name o_new alone).  Over all b1 failures and over erosion cases (ES@b0, not ES@b1)."""
    cids = paired_cases(tab, b0, b1)
    groups = {"b1_failures": [c for c in cids if not tab[c][b1]["es"]],
              "erosion": [c for c in cids if tab[c][b0]["es"] and not tab[c][b1]["es"]]}
    out = {}
    for g, members in groups.items():
        kinds = [_failure_kind(tab[c][b1]) for c in members]
        out[g] = {"n": len(members), "counts": {k: kinds.count(k) for k in ("both", "old_only", "neither")},
                  "shares": {k: _est([int(x == k) for x in kinds],
                                      f"{g} at {b1} (cases scored at {b0} and {b1}); value = answer is {k}")
                             for k in ("both", "old_only", "neither")}}
    return out


def answer_length(tab, b0="B0", b1="B3"):
    """Answer length in whitespace words at b0 and b1, and the paired difference (b1 - b0)."""
    cids = paired_cases(tab, b0, b1)
    w0 = [tab[c][b0]["words"] for c in cids]
    w1 = [tab[c][b1]["words"] for c in cids]
    out = _est([y - x for x, y in zip(w0, w1)],
               f"cases scored at {b0} and {b1}; value = words@{b1} - words@{b0}")
    out.update({"mean_b0": float(np.mean(w0)) if w0 else None, "mean_b1": float(np.mean(w1)) if w1 else None,
                "median_b0": float(np.median(w0)) if w0 else None,
                "median_b1": float(np.median(w1)) if w1 else None})
    return out


def sampling_reliability(greedy, sampled, b0="B0", b1="B3"):
    """Per-edit reliability under sampling.

    ``greedy``: case table of the run's greedy rows; ``sampled``: {seed: case table of that seed}.
    Cases: greedy ES at b0 and every seed scored at b0 and b1.  Reports P(at least one of the k
    sampled b1 runs fails ES), the same over the k sampled b0 runs (the resampling noise floor
    without reasoning), and their paired difference (the excess due to reasoning).
    """
    seeds = sorted(sampled)
    k = len(seeds)
    elig = [c for c in sorted(greedy) if b0 in greedy[c] and greedy[c][b0]["es"]]
    cids = [c for c in elig if all(b0 in sampled[s].get(c, {}) and b1 in sampled[s][c] for s in seeds)]
    fail1 = [int(any(not sampled[s][c][b1]["es"] for s in seeds)) for c in cids]
    fail0 = [int(any(not sampled[s][c][b0]["es"] for s in seeds)) for c in cids]
    den = f"cases with greedy ES@{b0} and all {k} sampled seeds scored at {b0} and {b1}"
    nfail = Counter(sum(1 for s in seeds if not sampled[s][c][b1]["es"]) for c in cids)
    return {"k": k, "seeds": seeds, "n_greedy_b0_success": len(elig),
            "n_excluded_incomplete_seeds": len(elig) - len(cids),
            "fail_any_b1": _est(fail1, den + f"; value = at least one of {k} sampled {b1} answers fails ES"),
            "fail_any_b0_noise_floor": _est(fail0, den + f"; value = at least one of {k} sampled {b0} answers fails ES"),
            "excess": _est([x - y for x, y in zip(fail1, fail0)], den + "; value = fail_any_b1 - fail_any_b0"),
            "fail_all_b1": _est([int(all(not sampled[s][c][b1]["es"] for s in seeds)) for c in cids],
                                den + f"; value = all {k} sampled {b1} answers fail ES"),
            "old_any_b1": _est([int(any(sampled[s][c][b1]["old"] for s in seeds)) for c in cids],
                               den + f"; value = at least one sampled {b1} answer names o_old"),
            "n_failures_b1_distribution": {str(i): nfail.get(i, 0) for i in range(k + 1)}}


# ---------------------------------------------------------------------------------------------
# Arms (cross_arm conventions)
# ---------------------------------------------------------------------------------------------
ARM_CONTRASTS = (("T", "N"), ("T", "P"), ("T", "C"), ("D", "N"), ("P", "N"), ("C", "N"))
ARM_METRICS = ("ES", "RR", "RRs")


def arm_records(tab, budget="B3", gate="B0"):
    """{case_id: {ES, RR, RRs, CLR}} at ``budget``: cross_arm.per_case's record, built from a case
    table.  RR/RRs are None unless the same arm's edit succeeded at ``gate``."""
    out = {}
    for c in sorted(tab):
        if budget not in tab[c]:
            continue
        o, g = tab[c][budget], tab[c].get(gate)
        ok = bool(g) and bool(g["es"])
        out[c] = {"ES": o["es"], "CLR": o["clr"],
                  "RR": int(o["old"]) if ok else None,
                  "RRs": int(o["old"] and not o["new"]) if ok else None}
    return out


def answer_parity(rows_a, rows_b, budget="B0", probe="efficacy", decode="greedy"):
    """Run-parity check: how many cases two runs answer byte-identically at one budget.

    At B0 a chain-scoped intervention cannot act, so two arms generated by the same code and
    environment should agree there on every case; disagreement means the arms differ in more than
    the intervention.  Returns n shared cases and the counts of identical answers and chains.
    """
    def index(rows):
        out = {}
        for r in rows:
            if r["budget"] == budget and r["probe"] == probe and r["decode"] == decode:
                if r["case_id"] in out:
                    raise ValueError(f"two rows for case {r['case_id']} at {budget}; select one world")
                out[r["case_id"]] = r
        return out
    a, b = index(rows_a), index(rows_b)
    common = sorted(set(a) & set(b))
    return {"budget": budget, "n": len(common),
            "identical_answer": sum(a[c].get("answer") == b[c].get("answer") for c in common),
            "identical_chain": sum(a[c].get("cot") == b[c].get("cot") for c in common)}


def arm_contrasts(records, contrasts=ARM_CONTRASTS, metric_names=ARM_METRICS, budget="B3", gate="B0"):
    """Paired arm differences via ``cross_arm.paired_diff`` (it rounds to 4 decimals).  A case
    enters when both arms scored it at ``budget``; for RR/RRs it must also pass both arms' ES gate
    at ``gate`` (the intersection of gates)."""
    out = {}
    for a, b in contrasts:
        if a not in records or b not in records:
            continue
        for m in metric_names:
            r = cross_arm.paired_diff(records[a], records[b], m, B_=N_BOOT, seed=SEED)
            gate_txt = (f" and ES@{gate} in both arms" if m in ("RR", "RRs") else "")
            out.setdefault(f"{a}-{b}", {})[m] = {
                "point": r.get("mean"), "ci95": r.get("ci"), "p": r.get("p"), "n": r["n"],
                "denominator": f"cases scored at {budget} in both arms{gate_txt}; value = {m}({a}) - {m}({b})"}
    return out
