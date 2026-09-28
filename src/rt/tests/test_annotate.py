"""Human annotation package: stratified sampling, blind CSVs, kappa, switch decision."""
import contextlib
import csv
import io
import json
import math
import os
import tempfile

from rt import annotate, judge
from rt.tests.test_judge import OracleScorer, header

# stratum sizes (budget, cell) -> N for the synthetic population
SIZES = {("B0", "new-only"): 60, ("B0", "old-only"): 20, ("B0", "both"): 8, ("B0", "neither"): 4,
         ("B3", "new-only"): 30, ("B3", "old-only"): 40, ("B3", "both"): 15, ("B3", "neither"): 7}


def population():
    """Cases and efficacy rows whose lexical cells realise SIZES exactly."""
    cases, rows, k = {}, [], 0
    for (budget, cell), N in sorted(SIZES.items()):
        for _ in range(N):
            cid = f"cf_{k}"
            cases[cid] = {"s": f"Person{k} Name", "o_new": f"Alpha{k}", "o_old": f"Beta{k}"}
            ans = {"new-only": f"Person{k} Name is Alpha{k}.", "old-only": f"It is Beta{k}.",
                   "both": f"Alpha{k} or Beta{k}.", "neither": "Unknown."}[cell]
            if k == 3:
                ans = "- " + ans                       # a cell a spreadsheet would read as a formula
            rows.append({"case_id": cid, "model_tag": "mtagzz", "editor": "ROME", "budget": budget,
                         "probe": "efficacy", "decode": "greedy", "q": f"Person{k} Name works for",
                         "cot": "chain", "answer": ans, "src": "shard.jsonl", "line": k})
            k += 1
    return cases, rows


def test_allocation_proportional_with_floor():
    assert annotate.allocate({"a": 1000, "b": 300, "c": 5}, 200, 10) == {"a": 150, "b": 45, "c": 5}
    assert annotate.allocate({"a": 900, "b": 90, "c": 10}, 100, 15) == {"a": 75, "b": 15, "c": 10}
    # hand-computed for SIZES, n=40, floor=3 (three rounds of floors, then largest remainder)
    assert annotate.allocate(SIZES, 40, 3) == {
        ("B0", "new-only"): 11, ("B0", "old-only"): 4, ("B0", "both"): 3, ("B0", "neither"): 3,
        ("B3", "new-only"): 6, ("B3", "old-only"): 7, ("B3", "both"): 3, ("B3", "neither"): 3}


def test_allocation_edges():
    assert annotate.allocate({"a": 3, "b": 4}, 10, 5) == {"a": 3, "b": 4}          # census
    for n in (3, 10, 57, 199, 561):
        alloc = annotate.allocate({"a": 500, "b": 60, "c": 2, "d": 0}, n, 1)
        assert sum(alloc.values()) == n and "d" not in alloc and min(alloc.values()) >= 1
        assert all(alloc[h] <= N for h, N in {"a": 500, "b": 60, "c": 2}.items())
    try:
        annotate.allocate({"a": 100, "b": 100, "c": 100}, 20, 10)
    except ValueError:
        return
    raise AssertionError("an infeasible floor must raise")


def test_stratified_sample_is_deterministic_unique_and_weighted():
    cases, rows = population()
    frame, n_empty = annotate.build_frame(rows, cases, {})
    assert n_empty == 0 and {h: len(v) for h, v in frame.items()} == SIZES
    s1, alloc, sizes = annotate.stratified_sample(frame, 40, 3, seed=1)
    s2, _, _ = annotate.stratified_sample(frame, 40, 3, seed=1)
    s3, _, _ = annotate.stratified_sample(frame, 40, 3, seed=2)
    ids = [s["item"]["item"] for s in s1]
    assert ids == [s["item"]["item"] for s in s2] and ids != [s["item"]["item"] for s in s3]
    assert len(set(ids)) == 40
    for h, n_h in alloc.items():
        got = [s for s in s1 if s["stratum"] == h]
        assert len(got) == n_h and all(s["item"]["lexical"]["cell"] == h[1] for s in got)
        assert all(math.isclose(s["weight"], sizes[h] / n_h) for s in got)
    assert math.isclose(sum(s["weight"] for s in s1), sum(SIZES.values()))


def _package(d, n=40, floor=3):
    cases, rows = population()
    frame, _ = annotate.build_frame(rows, cases, {})
    sample, _, _ = annotate.stratified_sample(frame, n, floor)
    return annotate.write_package(sample, d), rows


def _read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.reader(f))


def test_blind_csv_carries_no_metadata():
    with tempfile.TemporaryDirectory() as d:
        (key, manifest), rows = _package(d)
        a1, a2 = (_read_csv(os.path.join(d, f"items_{n}.csv")) for n in ("A1", "A2"))
        assert tuple(a1[0]) == annotate.BLIND_COLUMNS == tuple(a2[0])
        assert sorted(r[0] for r in a1[1:]) == sorted(r[0] for r in a2[1:])
        assert [r[0] for r in a1[1:]] != [r[0] for r in a2[1:]]          # own row order each
        with open(os.path.join(d, "items_A1.csv"), encoding="utf-8-sig") as f:
            text = f.read()
        leaks = ["mtagzz", "ROME", "B0", "B3", "cf_", "new-only", "old-only", "chain", "Person",
                 "shard", "greedy"] + [e["item"][:8] for e in key]
        assert not [s for s in leaks if s in text]
        by_id = {e["item_id"]: e for e in key}
        orders = set()
        for r in a1[1:]:
            e = by_id[r[0]]
            orders.add(tuple(e["order"]))
            assert r[3].strip() == e["values"][e["order"][0]] and r[4] == e["values"][e["order"][1]]
            assert r[5] == "" and "[SUBJECT]" in r[1]
            assert not r[2].startswith(("-", "=", "+", "@"))
        assert orders == {("NEW", "OLD"), ("OLD", "NEW")}
        assert annotate._cell("- x") == " - x" and annotate._cell("=1+1") == " =1+1"
        assert manifest["n"] == 40 and os.path.exists(os.path.join(d, "guide.md"))
        with open(os.path.join(d, "guide.md")) as f:
            guide = f.read()
        for word in ("negation", "demonym", "partial name", "Hedging", "refusal"):
            assert word.lower() in guide.lower()


# ---------------------------------------------------------------- kappa

A = ["NEW", "NEW", "NEW", "OLD", "OLD", "BOTH_UNCLEAR", "BOTH_UNCLEAR", "NEITHER", "NEITHER", "NEITHER"]
B = ["NEW", "NEW", "OLD", "OLD", "OLD", "BOTH_UNCLEAR", "NEITHER", "NEITHER", "NEITHER", "NEW"]


def test_kappa_hand_computed():
    # po = 7/10, pe = (3*3 + 2*3 + 2*1 + 3*3)/100 = .26  ->  .44/.74
    assert math.isclose(annotate.cohen_kappa(A, B, "label4"), 0.44 / 0.74)
    # NEW vs rest: po = .8, pe = .3*.3 + .7*.7 = .58  ->  .22/.42
    assert math.isclose(annotate.cohen_kappa(A, B, "es"), 0.22 / 0.42)
    # OLD vs rest: po = .9, pe = .2*.3 + .8*.7 = .62  ->  .28/.38
    assert math.isclose(annotate.cohen_kappa(A, B, "rr"), 0.28 / 0.38)
    assert annotate.cohen_kappa(A, A, "label4") == 1.0
    assert math.isnan(annotate.cohen_kappa(["NEW"] * 5, ["NEW"] * 5, "label4"))      # undefined


def test_weighted_kappa_equals_duplicated_items():
    w = [1, 2, 1, 1, 3, 1, 1, 1, 1, 2]
    dup_a = [x for x, k in zip(A, w) for _ in range(k)]
    dup_b = [x for x, k in zip(B, w) for _ in range(k)]
    for sp in annotate.SPACES:
        assert math.isclose(annotate.cohen_kappa(A, B, sp, w), annotate.cohen_kappa(dup_a, dup_b, sp))
        assert math.isclose(annotate.cohen_kappa(A, B, sp, [5] * 10), annotate.cohen_kappa(A, B, sp))


def test_bootstrap_resamples_within_strata():
    strata = ["x"] * 3 + ["y"] * 5 + ["z"] * 2
    idx = annotate._boot_index(strata, 50, seed=0)
    assert idx.shape == (50, 10)
    for row in idx:
        assert [strata[i] for i in row] == sorted(strata)
    assert (idx == annotate._boot_index(strata, 50, seed=0)).all()


def _key(orders):
    cells = ["new-only", "new-only", "both", "old-only", "old-only", "both", "neither", "neither",
             "old-only", "both"]
    return [{"item_id": f"S{i:03d}", "item": f"h{i}", "order": list(orders[i]),
             "stratum": {"budget": "B3", "cell": cells[i]}, "weight": 1.0,
             "values": {"NEW": f"n{i}", "OLD": f"o{i}"},
             "lexical": {"cell": cells[i], "old_hit": cells[i] in ("old-only", "both"),
                         "new_hit": cells[i] in ("new-only", "both")}} for i in range(10)]


def _letters(labels, key):
    return {e["item_id"]: ("A" if lab == e["order"][0] else "B" if lab == e["order"][1]
                           else "C" if lab == "BOTH_UNCLEAR" else "D")
            for lab, e in zip(labels, key)}


def test_scoring_undoes_order_and_matches_hand_values():
    orders = [("NEW", "OLD") if i % 3 else ("OLD", "NEW") for i in range(10)]
    key = _key(orders)
    humans = {"A1": annotate.letters_to_labels(_letters(A, key), key),
              "A2": annotate.letters_to_labels(_letters(B, key), key)}
    assert humans["A1"] == A and humans["A2"] == B
    rows = [{"item": e["item"], "p": {k: (0.97 if k == lab else 0.01) for k in judge.LABELS}}
            for e, lab in zip(key, A)]
    judges = {"g": annotate.judge_labels(rows, key)}
    rep = annotate.score_package(key, humans, judges, n_boot=2000, seed=0)
    k = rep["kappa"]
    assert k["A1~g"]["label4"]["k"] == 1.0 and k["A1~ensemble"]["es"]["k"] == 1.0
    assert math.isclose(k["A1~A2"]["label4"]["k"], 0.44 / 0.74)
    assert math.isclose(k["A2~g"]["rr"]["k"], 0.28 / 0.38)
    m = rep["kappa_vs_humans"]["ensemble"]
    assert math.isclose(m["es"]["k"], (1 + 0.22 / 0.42) / 2)
    assert math.isclose(m["rr"]["k"], (1 + 0.28 / 0.38) / 2)
    lo, hi = k["A1~A2"]["label4"]["lo"], k["A1~A2"]["label4"]["hi"]
    assert lo <= k["A1~A2"]["label4"]["k"] <= hi
    sw = rep["switch"]
    assert sw["semantic_primary"] and sw["primary_endpoint"] == "semantic"
    conf = rep["confusion"]["A1~A2"]["matrix"]
    assert sum(map(sum, conf)) == 10 and conf[0][0] == 2 and conf[3][0] == 1
    assert rep["confusion"]["humans_agreed~g"]["n_items"] == 7
    lex = rep["lexical_reversion_rule"]
    assert math.isclose(lex["permissive"]["A1"]["precision"], 2 / 6)
    assert lex["permissive"]["A1"]["recall"] == 1.0
    assert lex["permissive"]["A2"]["precision"] == 0.5 and lex["permissive"]["agreed"]["precision"] == 0.5
    assert math.isclose(lex["strict"]["A2"]["precision"], 2 / 3)
    assert math.isclose(lex["strict"]["A2"]["recall"], 2 / 3)
    assert rep["label_counts"]["lexical"]["OLD"] == 3
    # a judge that agrees with A2 (B): mean kappa ES = (.5238 + 1)/2 = .762, RR = .868 -> passes
    rows_b = [{"item": e["item"], "p": {k2: (0.97 if k2 == lab else 0.01) for k2 in judge.LABELS}}
              for e, lab in zip(key, B)]
    rep_b = annotate.score_package(key, humans, {"m": annotate.judge_labels(rows_b, key)}, n_boot=200)
    assert rep_b["switch"]["semantic_primary"]
    assert math.isclose(rep_b["switch"]["kappa"]["es"], (1 + 0.22 / 0.42) / 2)
    # a judge that always says NEW carries no information: kappa 0 -> lexical stays primary
    rows_c = [{"item": e["item"], "p": {k2: (0.97 if k2 == "NEW" else 0.01) for k2 in judge.LABELS}}
              for e in key]
    rep_c = annotate.score_package(key, humans, {"c": annotate.judge_labels(rows_c, key)}, n_boot=200)
    assert not rep_c["switch"]["semantic_primary"]
    assert rep_c["switch"]["primary_endpoint"] == "lexical strict"
    assert rep_c["switch"]["kappa"] == {"es": 0.0, "rr": 0.0}


def test_switch_threshold_is_inclusive_and_undefined_fails():
    rep = {"kappa_vs_humans": {"ensemble": {"es": {"k": 0.7}, "rr": {"k": 0.9}}}}
    assert annotate.switch_decision(rep)["semantic_primary"]
    rep["kappa_vs_humans"]["ensemble"]["rr"]["k"] = None
    assert not annotate.switch_decision(rep)["semantic_primary"]


def test_read_labels_validates_and_tolerates_spreadsheet_resaves():
    key = _key([("NEW", "OLD")] * 10)
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "a.csv")
        with open(p, "w", encoding="gbk", newline="") as f:          # re-saved in a local code page
            f.write("item_id;question;answer;option_A;option_B;label;comment\r\n")
            for i, e in enumerate(key):
                f.write(f"{e['item_id']};问题;答案 é;x;y; {'abcd'[i % 4]} ;\r\n")
        got = annotate.read_labels(p, key)
        assert [got[e["item_id"]] for e in key] == ["ABCD"[i % 4] for i in range(10)]
        with open(p, "w", encoding="utf-8") as f:
            f.write("item_id,label\nS000,A\nS001,E\n")
        try:
            annotate.read_labels(p, key)
        except ValueError as err:
            assert "without a valid label" in str(err)
            return
    raise AssertionError("missing or invalid labels must raise")


# ---------------------------------------------------------------- command line, end to end

def test_cli_build_then_score():
    cases, rows = population()
    with tempfile.TemporaryDirectory() as d:
        shard = os.path.join(d, "mtagzz_ROME_syn_r0of1.jsonl")
        with open(shard, "w") as f:
            for r in rows:
                f.write(json.dumps({k: v for k, v in r.items() if k not in ("src", "line")}) + "\n")
        cpath = os.path.join(d, "cases.jsonl")
        with open(cpath, "w") as f:
            for cid, c in cases.items():
                f.write(json.dumps(dict(c, case_id=cid)) + "\n")
        apath = os.path.join(d, "aliases.json")
        with open(apath, "w") as f:
            json.dump({}, f)
        pkg = os.path.join(d, "pkg")
        with contextlib.redirect_stdout(io.StringIO()):
            annotate.main(["build", "--rows", shard, "--cases", cpath, "--aliases", apath,
                           "--n", "40", "--floor", "3", "--out-dir", pkg])
        key = annotate.read_key(os.path.join(pkg, "key_HIDDEN.jsonl"))
        out = os.path.join(d, "judge.jsonl")
        judge.judge_rows(judge.read_rows([shard]), judge.load_cases(cpath), {}, OracleScorer(), out,
                         header(), log=None)
        truth = [annotate.CELL_LABEL[e["lexical"]["cell"]] for e in key]   # oracle == lexical here
        for name in ("A1", "A2"):
            src = os.path.join(pkg, f"items_{name}.csv")
            with open(src, newline="", encoding="utf-8-sig") as f:
                table = list(csv.reader(f))
            lab = _letters(truth, key)
            for r in table[1:]:
                r[5] = lab[r[0]]
            with open(src, "w", newline="", encoding="utf-8-sig") as f:
                csv.writer(f).writerows(table)
        rep_path = os.path.join(d, "score.json")
        with contextlib.redirect_stdout(io.StringIO()):
            annotate.main(["score", "--package", pkg, "--ann", f"A1={pkg}/items_A1.csv",
                           "--ann", f"A2={pkg}/items_A2.csv", "--judged", f"oracle={out}",
                           "--n-boot", "200", "--out", rep_path])
        with open(rep_path) as f:
            rep = json.load(f)
        assert rep["n"] == 40 and rep["switch"]["semantic_primary"]
        assert rep["kappa"]["A1~oracle"]["label4"]["k"] == 1.0
        assert rep["kappa"]["A1~A2"]["label4"]["k"] == 1.0
