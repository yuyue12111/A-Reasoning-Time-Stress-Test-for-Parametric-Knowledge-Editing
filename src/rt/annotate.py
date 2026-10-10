"""Human annotation package and agreement scoring for the semantic endpoint (REVISION.md §3).

``build`` draws a seed-fixed stratified sample of answer items (strata = budget B0/B3 × lexical
cell new-only/old-only/both/neither; proportional allocation with a per-stratum floor, capped by
stratum size) and writes, for each annotator, a blind CSV (item_id, question, answer, option_A,
option_B, label, comment) in its own row order; a one-page guide; a hidden key (the option order,
stratum, sampling weight, lexical flags and source rows of each item); and a manifest.  Items are
built by ``judge.make_item``, so annotators read exactly what the judge reads (subject scrubbed to
``[SUBJECT]``, R1 markers stripped) with the judge's primary option order.

``score`` computes Cohen's kappa between the two annotators, between each annotator and each
judge (and the two-judge ensemble, and the lexical rule as a reference rater), and between
judges, on three label spaces: the four labels, ES (NEW vs rest) and RR (OLD vs rest).  CIs are
percentile bootstraps that resample items within strata.  It also reports confusion matrices, the
lexical reversion rule's precision against the humans, and the pre-registered switch: the
semantic endpoint is primary iff the mean kappa of the ensemble against the two annotators is at
least 0.70 on both ES and RR (point estimates).

Run as ``PYTHONPATH=src python -m rt.annotate {build,score}``; see
``experiments/rt/README_judge.md``.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import os

from rt import judge

CELLS = ("new-only", "old-only", "both", "neither")
BUDGETS = ("B0", "B3")
BLIND_COLUMNS = ("item_id", "question", "answer", "option_A", "option_B", "label", "comment")
CELL_LABEL = {"new-only": "NEW", "old-only": "OLD", "both": "BOTH_UNCLEAR", "neither": "NEITHER"}
SPACES = ("label4", "es", "rr")
THRESHOLD = 0.70

GUIDE = """# Annotation guide: which value does the response commit to?

Each row of your CSV has a **question** (often an unfinished sentence such as "The mother tongue
of [SUBJECT] is"), a **response** written by an AI system, and two candidate values,
**option_A** and **option_B**. Write one letter in the `label` column:

| Label | Use when the response ... |
|---|---|
| **A** | commits to option_A as its final answer |
| **B** | commits to option_B as its final answer |
| **C** | asserts both values, or wavers between them without settling (both / unclear) |
| **D** | gives a different value, no value, off-topic text, or a refusal (neither) |

`comment` is optional (use it for items you found hard). Work alone: do not discuss items with
the other annotator, and do not change the file in any other way. About 200 items take 1.5-2 hours.

## Rules
1. **Judge the response only.** Do not use what you know about the world and do not look
   anything up; either value may be the "true" one, and that does not matter here.
2. **Asserted, not mentioned.** A value mentioned only to be rejected ("not X"), corrected, or as
   background does not count.
3. **Settling.** If the response considers both values and then settles on one, label the one it
   settles on. If it never settles, or asserts both, label C.
4. **Forms of a value.** Abbreviations, full or partial names, translations and adjective or
   demonym forms count as the value ("Indian" counts as India). A partial name that fits A and B
   equally is C.
5. **Hedging.** "Probably", "I believe" and similar words do not matter when one value is given.
   Offering both as possibilities without choosing is C.
6. **[SUBJECT]** replaces the name of the entity the question is about; ignore it.
7. **Refusals and non-answers** ("I don't know", a description that never gives a value, a
   different question answered) are D.

## Examples (values invented)
| Question | A | B | Response | Label |
|---|---|---|---|---|
| The official language of [SUBJECT] is | Norwegian | Bulgarian | "Not Norwegian, but Bulgarian." | B (negation) |
| [SUBJECT] is located in | Norway | Bulgaria | "It is certainly not in Norway." | D (A rejected, nothing asserted) |
| [SUBJECT] is a citizen of | India | Canada | "[SUBJECT] is an Indian politician." | A (demonym) |
| [SUBJECT] was developed by | Nintendo | Microsoft Corporation | "Microsoft." | B (partial name) |
| [SUBJECT] works for | BBC One | BBC Two | "The BBC." | C (fits both) |
| [SUBJECT] plays the | piano | guitar | "Probably the guitar." | B (hedge, one value) |
| [SUBJECT] was born in | Paris | Berlin | "Either Paris or Berlin, I am not sure." | C (no choice) |
| [SUBJECT] is headquartered in | Paris | Berlin | "Paris. Wait, actually it is Berlin." | B (settles) |
| The mother tongue of [SUBJECT] is | French | English | "I have no information about this person." | D (refusal) |
| [SUBJECT] is located in | Norway | Bulgaria | "Sweden." | D (third value) |
"""


def _h(*parts):
    return hashlib.sha256(":".join(str(p) for p in parts).encode()).hexdigest()


def _cell(text):
    """A spreadsheet-safe cell: text starting with = + - @ gets a leading space (no formula)."""
    return " " + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


# ------------------------------------------------------------------ sampling

def build_frame(rows, cases, aliases, budgets=BUDGETS, probes=("efficacy",)):
    """Unique non-empty items per stratum (budget, lexical cell), each with its source rows."""
    frame, n_empty = {}, 0
    for r in rows:
        if r.get("probe") not in probes or r.get("budget") not in budgets:
            continue
        it = judge.make_item(r, cases, aliases)
        if it["empty"]:
            n_empty += 1
            continue
        h = (r["budget"], it["lexical"]["cell"])
        e = frame.setdefault(h, {}).setdefault(it["item"], {"item": it, "rows": []})
        e["rows"].append(judge.row_identity(r))
    return frame, n_empty


def allocate(sizes, n, floor=10):
    """Proportional allocation of ``n`` over strata, each at least ``min(floor, size)``.

    Strata whose proportional share exceeds their size are capped first, then strata below the
    floor are raised to it, and the rest is re-shared in proportion to size; shares are rounded
    by largest remainder (ties by stratum name), so the allocation sums to ``n`` exactly.
    """
    sizes = {h: N for h, N in sizes.items() if N > 0}
    total = sum(sizes.values())
    if n >= total:
        return dict(sizes)
    if sum(min(floor, N) for N in sizes.values()) > n:
        raise ValueError(f"floor {floor} × {len(sizes)} strata exceeds n={n}")
    fixed, q = {}, {}
    while True:
        free = {h: N for h, N in sizes.items() if h not in fixed}
        R = n - sum(fixed.values())
        tot = sum(free.values())
        if not free:
            break
        q = {h: R * N / tot for h, N in free.items()}
        high = [h for h in free if q[h] > sizes[h]]
        if high:
            fixed.update({h: sizes[h] for h in high})
            continue
        low = [h for h in free if q[h] < min(floor, sizes[h])]
        if not low:
            break
        fixed.update({h: min(floor, sizes[h]) for h in low})
    base = {h: int(math.floor(v)) for h, v in q.items()} if free else {}
    left = (n - sum(fixed.values())) - sum(base.values())
    for h in sorted(base, key=lambda h: (-(q[h] - base[h]), str(h)))[:max(left, 0)]:
        base[h] += 1
    alloc = {**fixed, **base}
    spare = lambda h: sizes[h] - alloc[h]  # noqa: E731
    while sum(alloc.values()) < n:           # only when every stratum ended up fixed
        h = max(sorted(alloc, key=str), key=spare)
        alloc[h] += 1
    while sum(alloc.values()) > n:
        h = max(sorted(alloc, key=str), key=lambda h: alloc[h] - min(floor, sizes[h]))
        alloc[h] -= 1
    return alloc


def stratified_sample(frame, n=200, floor=10, seed=judge.DEFAULT_SEED):
    """Seed-fixed stratified sample: [{stratum, weight, item, rows}], allocation, sizes.

    Within a stratum, items are taken in the order of sha256(seed:item); an item already drawn
    in another stratum (identical text at B0 and B3) is skipped.  ``weight`` = N_h / n_h.
    """
    sizes = {h: len(v) for h, v in frame.items()}
    alloc = allocate(sizes, n, floor)
    chosen, picked = [], set()
    for h in sorted(frame):
        got = []
        for iid in sorted(frame[h], key=lambda i: _h(seed, "sample", i)):
            if len(got) == alloc.get(h, 0):
                break
            if iid not in picked:
                picked.add(iid)
                got.append(iid)
        for iid in got:
            chosen.append({"stratum": h, "weight": sizes[h] / len(got), **frame[h][iid]})
    return chosen, alloc, sizes


def write_package(sample, out_dir, seed=judge.DEFAULT_SEED, judge_seed=judge.DEFAULT_SEED,
                  annotators=("A1", "A2"), extra_manifest=None):
    """Blind CSVs (one per annotator, own row order), guide, hidden key and manifest."""
    os.makedirs(out_dir, exist_ok=True)
    ordered = sorted(sample, key=lambda s: _h(seed, "ids", s["item"]["item"]))
    key = []
    for k, s in enumerate(ordered, 1):
        it = s["item"]
        order = judge.option_order(it["item"], judge_seed)
        key.append({"item_id": f"S{k:03d}", "item": it["item"], "order": list(order),
                    "stratum": {"budget": s["stratum"][0], "cell": s["stratum"][1]},
                    "weight": s["weight"], "values": it["values"], "lexical": it["lexical"],
                    "question": it["question"], "answer": it["answer"], "rows": s["rows"]})
    paths = {}
    for name in annotators:
        rows = sorted(key, key=lambda e: _h(seed, "csv", name, e["item"]))
        p = os.path.join(out_dir, f"items_{name}.csv")
        with open(p, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(BLIND_COLUMNS)
            for e in rows:
                w.writerow([e["item_id"]] + [_cell(t) for t in (
                    e["question"], e["answer"], e["values"][e["order"][0]],
                    e["values"][e["order"][1]])] + ["", ""])
        paths[name] = p
    with open(os.path.join(out_dir, "guide.md"), "w", encoding="utf-8") as f:
        f.write(GUIDE)
    kp = os.path.join(out_dir, "key_HIDDEN.jsonl")
    with open(kp, "w", encoding="utf-8") as f:
        for e in key:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    manifest = {"n": len(key), "seed": seed, "judge_seed": judge_seed, "annotators": list(annotators),
                "prompt_sha": judge.prompt_sha(), "key_sha": judge._file_sha(kp),
                "csv_sha": {n: judge._file_sha(p) for n, p in paths.items()},
                "guide_sha": judge._sha(GUIDE.encode()), **(extra_manifest or {})}
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return key, manifest


# ------------------------------------------------------------------ agreement

def read_key(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def read_labels(path, key):
    """{item_id: letter} from a filled CSV; every key item must carry exactly one of A-D.

    Only the ASCII columns item_id and label are read, so a file re-saved by a spreadsheet in a
    local code page or with ';' or tab as delimiter still scores.
    """
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        text = f.read()
    head = text.split("\n", 1)[0]
    delim = max((",", ";", "\t"), key=head.count)
    rows = list(csv.DictReader(io.StringIO(text, newline=""), delimiter=delim))
    rows = [{(k or "").strip(): v for k, v in r.items()} for r in rows]
    if not rows or "item_id" not in rows[0] or "label" not in rows[0]:
        raise ValueError(f"{path}: needs item_id and label columns")
    got = {(r["item_id"] or "").strip(): (r.get("label") or "").strip().upper() for r in rows}
    ids = [e["item_id"] for e in key]
    bad = [i for i in ids if got.get(i) not in ("A", "B", "C", "D")]
    unknown = sorted(set(got) - set(ids))
    if bad or unknown:
        raise ValueError(f"{path}: {len(bad)} items without a valid label A-D "
                         f"(first: {bad[:5]}), {len(unknown)} unknown ids")
    return {i: got[i] for i in ids}


def letters_to_labels(letters, key):
    """Human letters -> NEW/OLD/BOTH_UNCLEAR/NEITHER through each item's option order."""
    out = []
    for e in key:
        L = letters[e["item_id"]]
        out.append({"A": e["order"][0], "B": e["order"][1], "C": "BOTH_UNCLEAR",
                    "D": "NEITHER"}[L])
    return out


def judge_labels(judged_rows, key):
    """(labels, p) per key item from one judge's (or an ensemble's) output rows."""
    by = {}
    for r in judged_rows:
        by.setdefault(r["item"], r["p"])
    missing = [e["item_id"] for e in key if e["item"] not in by]
    if missing:
        raise ValueError(f"judge output lacks {len(missing)} key items (first: {missing[:5]})")
    ps = [by[e["item"]] for e in key]
    return [judge.decide(p) for p in ps], ps


def _codes(labels, space):
    import numpy as np
    if space == "label4":
        return np.array([judge.LABELS.index(x) for x in labels]), 4
    target = "NEW" if space == "es" else "OLD"
    return np.array([int(x == target) for x in labels]), 2


def _kappa_counts(C):
    """Cohen's kappa from confusion counts (..., K, K); NaN where chance agreement is 1."""
    import numpy as np
    C = np.asarray(C, dtype=float)
    n = C.sum(axis=(-2, -1))
    po = np.trace(C, axis1=-2, axis2=-1) / n
    pe = (C.sum(-1) * C.sum(-2)).sum(-1) / n ** 2
    with np.errstate(divide="ignore", invalid="ignore"):
        k = (po - pe) / (1 - pe)
    return np.where(np.abs(1 - pe) < 1e-12, np.nan, k)


def cohen_kappa(a, b, space="label4", weights=None):
    """Cohen's kappa of two label lists (optionally with item weights); NaN if undefined."""
    import numpy as np
    ca, K = _codes(a, space)
    cb, _ = _codes(b, space)
    w = np.ones(len(ca)) if weights is None else np.asarray(weights, dtype=float)
    C = np.zeros((K, K))
    np.add.at(C, (ca, cb), w)
    return float(_kappa_counts(C))


def confusion(a, b):
    import numpy as np
    C = np.zeros((4, 4), dtype=int)
    for x, y in zip(a, b):
        C[judge.LABELS.index(x), judge.LABELS.index(y)] += 1
    return {"rows": "first rater", "cols": "second rater", "labels": list(judge.LABELS),
            "matrix": C.tolist()}


def _boot_index(strata, n_boot, seed):
    """(n_boot, n) indices resampling items with replacement within each stratum."""
    import numpy as np
    rng = np.random.default_rng(seed)
    groups = {}
    for i, s in enumerate(strata):
        groups.setdefault(s, []).append(i)
    cols = []
    for s in sorted(groups):
        g = np.array(groups[s])
        cols.append(g[rng.integers(0, len(g), size=(n_boot, len(g)))])
    return np.concatenate(cols, axis=1)


def _boot_kappa(a, b, space, idx):
    import numpy as np
    ca, K = _codes(a, space)
    cb, _ = _codes(b, space)
    B = idx.shape[0]
    flat = (ca[idx] * K + cb[idx]) + (K * K) * np.arange(B)[:, None]
    C = np.bincount(flat.ravel(), minlength=B * K * K).reshape(B, K, K)
    return _kappa_counts(C)


def _ci(point, reps):
    import numpy as np
    r = reps[~np.isnan(reps)]
    lo, hi = (float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))) if len(r) else (None, None)
    return {"k": None if math.isnan(point) else point, "lo": lo, "hi": hi,
            "n_undefined": int(len(reps) - len(r))}


def score_package(key, humans, judges, n_boot=10000, seed=0, threshold=THRESHOLD):
    """Agreement report for ``humans`` ({name: labels}) and ``judges`` ({name: (labels, p)}).

    Adds the rater ``ensemble`` (mean of the judges' label probabilities; with one judge it is
    that judge) and ``lexical`` (new-only/old-only/both/neither -> NEW/OLD/BOTH_UNCLEAR/NEITHER).
    """
    hn = list(humans)
    if len(hn) != 2:
        raise ValueError("exactly two annotators are needed")
    raters = dict(humans)
    for name, (labs, _) in judges.items():
        raters[name] = labs
    if judges:
        ps = [p for _, p in judges.values()]
        ens = [{k: sum(p[i][k] for p in ps) / len(ps) for k in judge.LABELS}
               for i in range(len(key))]
        raters["ensemble"] = [judge.decide(p) for p in ens]
    raters["lexical"] = [CELL_LABEL[e["lexical"]["cell"]] for e in key]
    strata = [f"{e['stratum']['budget']}|{e['stratum']['cell']}" for e in key]
    weights = [e["weight"] for e in key]
    idx = _boot_index(strata, n_boot, seed)

    def pair(a, b):
        out = {}
        for sp in SPACES:
            k = cohen_kappa(raters[a], raters[b], sp)
            out[sp] = _ci(k, _boot_kappa(raters[a], raters[b], sp, idx))
            kw = cohen_kappa(raters[a], raters[b], sp, weights)
            out[sp]["k_popw"] = None if math.isnan(kw) else kw
        return out

    machine = [r for r in raters if r not in humans]
    report = {"n": len(key), "n_boot": n_boot, "raters": list(raters),
              "label_counts": {r: {L: labs.count(L) for L in judge.LABELS}
                               for r, labs in raters.items()},
              "kappa": {f"{hn[0]}~{hn[1]}": pair(hn[0], hn[1])}, "kappa_vs_humans": {},
              "confusion": {f"{hn[0]}~{hn[1]}": confusion(raters[hn[0]], raters[hn[1]])}}
    jn = list(judges)
    for i in range(len(jn)):
        for j in range(i + 1, len(jn)):
            report["kappa"][f"{jn[i]}~{jn[j]}"] = pair(jn[i], jn[j])
            report["confusion"][f"{jn[i]}~{jn[j]}"] = confusion(raters[jn[i]], raters[jn[j]])
    agreed = [i for i in range(len(key)) if raters[hn[0]][i] == raters[hn[1]][i]]
    for m in machine:
        per = {h: pair(h, m) for h in hn}
        for h in hn:
            report["kappa"][f"{h}~{m}"] = per[h]
        mean = {}
        for sp in SPACES:
            pts = [per[h][sp]["k"] for h in hn]
            reps = sum(_boot_kappa(raters[h], raters[m], sp, idx) for h in hn) / len(hn)
            mean[sp] = _ci(float("nan") if None in pts else sum(pts) / len(pts), reps)
        report["kappa_vs_humans"][m] = mean
        report["confusion"][f"humans_agreed~{m}"] = dict(
            confusion([raters[hn[0]][i] for i in agreed], [raters[m][i] for i in agreed]),
            n_items=len(agreed))
    report["lexical_reversion_rule"] = lexical_rule_vs_humans(key, raters, hn, agreed)
    report["switch"] = switch_decision(report, threshold)
    return report


def lexical_rule_vs_humans(key, raters, hn, agreed):
    """Precision/recall of the permissive (old mentioned) and strict (old-only) reversion rules."""
    out = {}
    for rule, flag in (("permissive", lambda e: e["lexical"]["old_hit"]),
                       ("strict", lambda e: e["lexical"]["cell"] == "old-only")):
        res = {}
        for ref in hn + ["agreed"]:
            ids = agreed if ref == "agreed" else range(len(key))
            gold = [(flag(key[i]), (raters[hn[0]] if ref == "agreed" else raters[ref])[i] == "OLD")
                    for i in ids]
            tp = sum(f and g for f, g in gold)
            fp = sum(f and not g for f, g in gold)
            fn = sum(g and not f for f, g in gold)
            res[ref] = {"precision": tp / (tp + fp) if tp + fp else None,
                        "recall": tp / (tp + fn) if tp + fn else None,
                        "tp": tp, "fp": fp, "fn": fn, "n": len(gold)}
        out[rule] = res
    return out


def switch_decision(report, threshold=THRESHOLD, rater="ensemble", spaces=("es", "rr")):
    """Pre-registered switch: semantic endpoint primary iff mean kappa(rater, each human) >= threshold
    on every space in ``spaces`` (point estimates; undefined kappa fails)."""
    vals = {sp: (report["kappa_vs_humans"].get(rater) or {}).get(sp, {}).get("k") for sp in spaces}
    ok = all(v is not None and v >= threshold for v in vals.values())
    return {"rule": f"semantic endpoint is primary iff the mean Cohen's kappa between the "
                    f"'{rater}' labels and each human annotator is >= {threshold} for "
                    f"{' and '.join(spaces)} (binary NEW-vs-rest / OLD-vs-rest; point estimates)",
            "rater": rater, "threshold": threshold, "kappa": vals, "semantic_primary": ok,
            "primary_endpoint": "semantic" if ok else "lexical strict"}


# ------------------------------------------------------------------ CLI

def cmd_build(args):
    probes = tuple(args.probes.split(","))
    rows = judge.read_rows(args.rows, probes=probes, where=args.where)
    cases, aliases = judge.load_cases(args.cases), judge.load_aliases(args.aliases)
    frame, n_empty = build_frame(rows, cases, aliases, tuple(args.budgets.split(",")), probes)
    sample, alloc, sizes = stratified_sample(frame, args.n, args.floor, args.seed)
    strata = {f"{b}|{c}": {"N": sizes.get((b, c), 0), "n": alloc.get((b, c), 0)}
              for b in args.budgets.split(",") for c in CELLS}
    _, manifest = write_package(
        sample, args.out_dir, args.seed, args.judge_seed, tuple(args.annotators.split(",")),
        {"floor": args.floor, "strata": strata, "n_empty_excluded": n_empty,
         "inputs": {"rows": [os.path.basename(f) for f in judge.expand(args.rows)],
                    "probes": probes, "where": args.where, "cases_sha": judge._file_sha(args.cases)}})
    print(json.dumps({"n": manifest["n"], "strata": strata}, indent=1))


def cmd_score(args):
    key = read_key(os.path.join(args.package, "key_HIDDEN.jsonl"))
    humans = {}
    for spec in args.ann:
        name, path = spec.split("=", 1)
        humans[name] = letters_to_labels(read_labels(path, key), key)
    judges = {}
    for spec in args.judged or []:
        name, pat = spec.split("=", 1)
        judges[name] = judge_labels(judge.read_judged([pat])[1], key)
    rep = score_package(key, humans, judges, args.n_boot, args.seed, args.threshold)
    for pair_name, v in rep["kappa"].items():
        print(f"{pair_name:28s} " + "  ".join(
            f"{sp} {v[sp]['k'] if v[sp]['k'] is None else round(v[sp]['k'], 3)}"
            f" [{v[sp]['lo'] and round(v[sp]['lo'], 3)}, {v[sp]['hi'] and round(v[sp]['hi'], 3)}]"
            for sp in SPACES))
    print(json.dumps(rep["switch"], indent=1))
    if args.out:
        with open(args.out, "w") as f:
            json.dump(rep, f, indent=1)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="rt.annotate", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--rows", action="append", required=True)
    b.add_argument("--cases", default=os.path.join(judge.ROOT, "data", "counterfact.jsonl"))
    b.add_argument("--aliases", default=os.path.join(judge.ROOT, "data", "aliases.json"))
    b.add_argument("--probes", default="efficacy")
    b.add_argument("--budgets", default=",".join(BUDGETS))
    b.add_argument("--where", action="append", default=[])
    b.add_argument("--n", type=int, default=200)
    b.add_argument("--floor", type=int, default=10)
    b.add_argument("--seed", type=int, default=judge.DEFAULT_SEED)
    b.add_argument("--judge-seed", type=int, default=judge.DEFAULT_SEED,
                   help="option order; keep equal to the judge's --seed")
    b.add_argument("--annotators", default="A1,A2")
    b.add_argument("--out-dir", required=True)
    b.set_defaults(fn=cmd_build)
    s = sub.add_parser("score")
    s.add_argument("--package", required=True)
    s.add_argument("--ann", action="append", required=True, help="name=filled.csv (twice)")
    s.add_argument("--judged", action="append", help="name=glob of judge output")
    s.add_argument("--n-boot", type=int, default=10000)
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--threshold", type=float, default=THRESHOLD)
    s.add_argument("--out", default=None)
    s.set_defaults(fn=cmd_score)
    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
