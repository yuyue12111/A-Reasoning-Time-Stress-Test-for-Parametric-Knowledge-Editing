"""rt.analysis on small synthetic rows whose answers can be worked out by hand."""
import hashlib
import json
import os
import random
import tempfile

import cross_arm
from rt import analysis as A

CASES = {
    "c1": {"case_id": "c1", "s": "Miami Film Festival", "o_old": "Miami", "o_new": "Paris"},
    "c2": {"case_id": "c2", "s": "Danielle Darrieux", "o_old": "French", "o_new": "English"},
    "c3": {"case_id": "c3", "s": "Toyota", "o_old": "Japan", "o_new": "Germany"},
}


def o(new, old, clr=0, words=0):
    """A hand-made outcome, the shape case_table produces."""
    return {"new": bool(new), "old": bool(old), "es": int(bool(new) and not old), "clr": clr, "words": words}


def es(v):
    return o(1, 0) if v else o(0, 1)


def _write(lines):
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as fh:
        for x in lines:
            fh.write((x if isinstance(x, str) else json.dumps(x)) + "\n")
    return path


def _legacy(cid, budget, answer, cot="", probe="efficacy", **kw):
    return {"case_id": cid, "editor": "ROME", "budget": budget, "probe": probe, "decode": "greedy",
            "seed": None, "temperature": None, "q": f"q-{cid}", "cot": cot, "answer": answer, **kw}


def _v2(cid, budget, answer, cot="", arm="N", **kw):
    row = {"case_id": cid, "model_tag": "m", "editor": "ROME", "target_tag": "new", "budget": budget,
           "probe": "efficacy", "condition": "native", "arm": arm, "alpha": 1.0, "decode": "greedy",
           "seed": None, "temperature": None, "q": f"q-{cid}", "cot": cot, "answer": answer,
           "chain_end": "think_end", "n_chain_tokens": 3, "n_answer_tokens": 2, "delta_sha": "ab"}
    row.update(kw)
    return row


# ------------------------------------------------------------------------------------ loader
def test_loader_legacy_meta_errors_duplicates():
    meta = {"_meta": True, "model_tag": "r1x", "editor": "ROME"}
    r = _legacy("c1", "B0", "It is in Paris.")
    path = _write([meta, r, {"case_id": "c2", "error": "OOM"}, r, _legacy("c1", "B3", "Miami.")])
    try:
        rows, audit = A.load_rows([path])
        raw = open(path, "rb").read()
    finally:
        os.remove(path)
    assert len(rows) == 2
    f = audit["files"][0]
    assert f["sha256"] == hashlib.sha256(raw).hexdigest() and f["bytes"] == len(raw)
    assert f["counts"] == {"duplicate": 1, "error": 1, "legacy": 2, "meta": 1}
    assert audit["duplicate_audit"]["n_duplicate_rows_dropped"] == 1
    row = rows[0]
    assert row["schema"] == "legacy" and row["model_tag"] == "r1x" and row["editor"] == "ROME"
    assert (row["condition"], row["arm"], row["alpha"], row["probe"]) == ("native", "N", 1.0, "efficacy")
    assert row["source"]["line"] == 2


def test_loader_legacy_base_rows_and_defaults():
    base = {"case_id": "c1", "budget": "B0", "probe": "base", "decode": "greedy", "q": "q", "cot": "",
            "answer": "Miami"}
    path = _write([base])
    try:
        rows, _ = A.load_rows([path], defaults={"model_tag": "r1x"})
    finally:
        os.remove(path)
    r = rows[0]
    assert (r["probe"], r["editor"], r["condition"], r["arm"], r["alpha"]) == ("efficacy", "none", "base", None, None)
    assert r["model_tag"] == "r1x" and A.is_base(r)
    # defaults label a legacy file, but never override a field the row carries
    path = _write([_legacy("c1", "B3", "x", decode="sample", seed=1, temperature=0.6)])
    try:
        rows, _ = A.load_rows([path], defaults={"arm": "T", "decode": "greedy"})
    finally:
        os.remove(path)
    assert rows[0]["arm"] == "T" and rows[0]["decode"] == "sample" and not A.is_base(rows[0])


def test_loader_v2_rows_and_missing_fields():
    path = _write([{"_meta": True, "git": "abc"}, _v2("c1", "B3", "Paris", arm="T", alpha=2.0)])
    try:
        rows, audit = A.load_rows([path])
    finally:
        os.remove(path)
    r = rows[0]
    assert r["schema"] == "v2" and r["arm"] == "T" and r["alpha"] == 2.0 and r["chain_end"] == "think_end"
    assert audit["files"][0]["counts"] == {"meta": 1, "v2": 1}
    bad = _v2("c1", "B3", "Paris")
    del bad["condition"]
    path = _write([bad])
    try:
        A.load_rows([path])
    except ValueError as e:
        assert "condition" in str(e)
    else:
        raise AssertionError("a v2 row without condition must be rejected")
    finally:
        os.remove(path)


def test_loader_conflicting_duplicate_fails():
    a, b = _legacy("c1", "B0", "Paris"), _legacy("c1", "B0", "Rome")
    p1, p2 = _write([a]), _write([b])
    try:
        A.load_rows([p1, p2])
    except ValueError as e:
        assert "conflicting duplicate" in str(e) and "answer" in str(e)
    else:
        raise AssertionError("conflicting duplicate worlds must fail")
    finally:
        os.remove(p1)
        os.remove(p2)


def test_both_schemas_score_identically():
    rows_l = [A.normalise_row(_legacy("c1", "B3", "Miami Film Festival moved to Paris.", cot="it was in Miami"))]
    rows_v = [A.normalise_row(_v2("c1", "B3", "Miami Film Festival moved to Paris.", cot="it was in Miami"))]
    tl, tv = A.case_table(rows_l, CASES, {}), A.case_table(rows_v, CASES, {})
    assert tl == tv == {"c1": {"B3": {"new": True, "old": False, "es": 1, "clr": 1, "words": 6}}}


def test_case_table_scoring_and_world_mixing():
    rows = [A.normalise_row(r, defaults={"arm": arm}) for r, arm in (
        (_legacy("c2", "B0", "She speaks English."), "N"),
        (_legacy("c2", "B0", "She speaks French, not English."), "T"),
        (_legacy("c3", "B0", "Japan"), "N"))]
    try:
        A.case_table(rows, CASES, {})
    except ValueError as e:
        assert "select one world" in str(e)
    else:
        raise AssertionError("two arms in one table must fail")
    t = A.case_table(rows, CASES, {}, arm="T")
    assert t == {"c2": {"B0": {"new": True, "old": True, "es": 0, "clr": 0, "words": 5}}}
    n = A.case_table(rows, CASES, {}, arm="N")
    assert n["c2"]["B0"]["es"] == 1 and n["c3"]["B0"] == {"new": False, "old": True, "es": 0, "clr": 0, "words": 1}


def test_name_containment_is_whole_word_case_insensitive():
    assert A.name_contains_old({"s": "Miami International Film Festival", "o_old": "Miami"})
    assert A.name_contains_old({"s": "BBC Radio 4", "o_old": "bbc"})
    assert not A.name_contains_old({"s": "Miamians United", "o_old": "Miami"})
    assert not A.name_contains_old({"s": "Toyota", "o_old": "Toy"})


def test_degenerate_cases_use_score_pilot_rule():
    rows = [{"case_id": "a", "answer": "717" * 20}, {"case_id": "b", "answer": "The capital of France is Paris."},
            {"case_id": "c", "answer": "Session " * 10}, {"case_id": "b", "answer": ""}]
    assert A.degenerate_cases(rows) == ["a", "c"]
    assert [r["case_id"] for r in A.drop_cases(rows, ["a", "c"])] == ["b", "b"]


# ------------------------------------------------------------------------------------ bootstrap
def test_bootstrap_equals_cross_arm_paired_diff():
    rng = random.Random(7)
    ids = [f"k{i:03d}" for i in range(57)]
    a = {i: {"ES": rng.randint(0, 1)} for i in ids}
    b = {i: {"ES": rng.randint(0, 1)} for i in ids}
    ref = cross_arm.paired_diff(a, b, "ES")
    got = A.bootstrap_mean([a[i]["ES"] - b[i]["ES"] for i in sorted(ids)])
    assert got["n"] == ref["n"] == 57
    assert round(got["point"], 4) == ref["mean"]
    assert [round(x, 4) for x in got["ci95"]] == ref["ci"]
    assert round(got["p"], 4) == ref["p"]


def test_bootstrap_deterministic_and_degenerate_inputs():
    vals = [1, 0, 0, 1, 1, -1, 0, 1]
    assert A.bootstrap_mean(vals) == A.bootstrap_mean(list(vals))
    ones = A.bootstrap_mean([1] * 9)
    assert ones["point"] == 1.0 and ones["ci95"] == [1.0, 1.0] and ones["p"] == 0.0
    zeros = A.bootstrap_mean([0] * 9)
    assert zeros["ci95"] == [0.0, 0.0] and zeros["p"] == 1.0
    assert A.bootstrap_mean([]) == {"point": None, "ci95": None, "p": None, "n": 0}
    floats = A.bootstrap_mean([0.5, 1.5, 2.5])
    assert abs(floats["point"] - 1.5) < 1e-12 and floats["p"] == 0.0


def test_bootstrap_two_groups():
    r = A.bootstrap_two_groups([1, 1, 1], [0, 0])
    assert r["point"] == 1.0 and r["ci95"] == [1.0, 1.0] and r["p"] == 0.0 and r["n"] == [3, 2]
    assert A.bootstrap_two_groups([1, 0, 1], [0, 1]) == A.bootstrap_two_groups([1, 0, 1], [0, 1])


def test_holm_step_down():
    h = A.holm({"a": 0.01, "b": 0.04, "c": 0.03, "d": 0.005})
    assert [h[k]["rank"] for k in "dacb"] == [1, 2, 3, 4]
    assert abs(h["d"]["p_holm"] - 0.02) < 1e-12 and abs(h["a"]["p_holm"] - 0.03) < 1e-12
    assert abs(h["c"]["p_holm"] - 0.06) < 1e-12 and abs(h["b"]["p_holm"] - 0.06) < 1e-12
    assert abs(h["d"]["threshold"] - 0.0125) < 1e-12 and abs(h["b"]["threshold"] - 0.05) < 1e-12
    # b's raw p is below its own threshold but step-down stopped at c
    assert [h[k]["reject"] for k in "dacb"] == [True, True, False, False]
    assert A.holm({"x": 0.6, "y": 0.9})["y"]["p_holm"] == 1.0


# ------------------------------------------------------------------------------------ estimators
TAB = {  # (ES@B0, ES@B3) = (1,0) (1,1) (0,1) (1,0); c5 has no B3
    "c1": {"B0": o(1, 0, words=4), "B3": o(0, 1, clr=1, words=10)},
    "c2": {"B0": o(1, 0, words=2), "B3": o(1, 0, clr=1, words=4)},
    "c3": {"B0": o(0, 1, words=6), "B3": o(1, 0, words=6)},
    "c4": {"B0": o(1, 0, words=8), "B3": o(1, 1, words=8)},
    "c5": {"B0": o(1, 0)},
}


def test_es_drop_rates_and_flows():
    d = A.es_drop(TAB)
    assert d["n"] == 4 and d["point"] == 0.25 and d["es_b0"] == 0.75 and d["es_b1"] == 0.5
    assert A.rate(TAB, "B0")["point"] == 0.8 and A.rate(TAB, "B0")["n"] == 5
    assert A.erosion(TAB)["point"] == 0.5 and A.repair(TAB)["point"] == 0.25
    assert A.erosion(TAB)["point"] - A.repair(TAB)["point"] == d["point"]
    assert A.clr(TAB)["point"] == 0.5 and A.clr(TAB)["n"] == 4


def test_rr_gate_and_strict():
    r = A.rr(TAB)          # gate: ES@B0 and a B3 row -> c1 (old only), c2 (new), c4 (both)
    assert r["n"] == 3 and abs(r["point"] - 2 / 3) < 1e-12
    s = A.rr(TAB, strict=True)
    assert s["n"] == 3 and abs(s["point"] - 1 / 3) < 1e-12


def test_flow_difference_uses_shared_cases():
    other = {"c1": {"B0": es(1), "B3": es(1)}, "c3": {"B0": es(1), "B3": es(0)}, "c9": {"B0": es(1), "B3": es(0)}}
    e = A.flow_difference(TAB, other, "erosion")      # shared: c1 (1-0), c3 (0-1)
    assert e["n"] == 2 and e["point"] == 0.0
    r = A.flow_difference(TAB, other, "repair")       # c1 (0-0), c3 (1-0)
    assert r["point"] == 0.5


def test_retention_contrast():
    ed = {"k1": {"B0": es(1), "B3": es(0)}, "k2": {"B0": es(1), "B3": es(1)},
          "k3": {"B0": es(1), "B3": es(0)}, "k4": {"B0": es(1), "B3": es(0)},
          "k5": {"B0": es(0), "B3": es(0)}, "k6": {"B0": es(1), "B3": es(1)},
          "k7": {"B0": es(1), "B3": es(0)}}
    known, unknown = o(0, 1), o(0, 0)
    base = {"k1": {"B0": known, "B3": known}, "k2": {"B0": known, "B3": unknown},
            "k3": {"B0": known, "B3": unknown}, "k4": {"B0": unknown, "B3": known},
            "k5": {"B0": known, "B3": known}, "k6": {"B0": known, "B3": known},
            "k7": {"B0": known, "B3": known}}
    r = A.retention_contrast(ed, base)   # k1 +1, k2 -1, k3 0, k6 0, k7 +1 ; k4 base unknown, k5 edit failed
    assert r["n"] == 5 and abs(r["point"] - 0.2) < 1e-12
    assert abs(r["edited_loss"]["point"] - 0.6) < 1e-12 and abs(r["base_loss"]["point"] - 0.4) < 1e-12
    assert r["table_2x2"] == {"edited_lost=1,base_lost=1": 1, "edited_lost=1,base_lost=0": 2,
                              "edited_lost=0,base_lost=1": 1, "edited_lost=0,base_lost=0": 1}


def test_knowledge_strata_and_qualified():
    ed = {"a": {"B0": es(1), "B3": es(0)}, "b": {"B0": es(1), "B3": es(1)},
          "c": {"B0": es(0), "B3": es(1)}, "d": {"B0": es(1), "B3": es(0)}, "e": {"B0": es(1), "B3": es(0)}}
    k, u = o(0, 1), o(0, 0)
    base = {"a": {"B0": k, "B3": k}, "b": {"B0": k, "B3": k}, "c": {"B0": u, "B3": k},
            "d": {"B0": k, "B3": u}, "e": {"B0": u, "B3": u}}
    s = A.knowledge_strata(ed, base)
    assert (s["known_B0_B3"]["n"], s["known_B0_B3"]["point"]) == (2, 0.5)
    assert (s["known_B3_only"]["n"], s["known_B3_only"]["point"]) == (1, -1.0)
    assert (s["known_B0_only"]["n"], s["known_B0_only"]["point"]) == (1, 1.0)
    assert (s["unknown"]["n"], s["unknown"]["point"]) == (1, 1.0)
    q = A.qualified_es_drop(ed, base)                 # a, b, d
    assert q["n"] == 3 and abs(q["point"] - 2 / 3) < 1e-12


def test_failure_anatomy_and_length():
    f = A.failure_anatomy(TAB)                        # B3 failures: c1 (old only), c4 (both)
    assert f["b1_failures"]["n"] == 2 and f["b1_failures"]["counts"] == {"both": 1, "old_only": 1, "neither": 0}
    assert f["erosion"]["counts"] == {"both": 1, "old_only": 1, "neither": 0}
    assert f["b1_failures"]["shares"]["both"]["point"] == 0.5
    n = {"x": {"B0": o(1, 0), "B3": o(0, 0)}}
    assert A.failure_anatomy(n)["erosion"]["counts"]["neither"] == 1
    L = A.answer_length(TAB)                          # diffs 6, 2, 0, 0
    assert L["point"] == 2.0 and L["mean_b0"] == 5.0 and L["mean_b1"] == 7.0 and L["median_b1"] == 7.0


def test_sampling_reliability():
    greedy = {"a": {"B0": es(1)}, "b": {"B0": es(1)}, "c": {"B0": es(0)}, "d": {"B0": es(1)}}
    sampled = {
        0: {"a": {"B0": es(1), "B3": es(0)}, "b": {"B0": es(1), "B3": es(1)}, "c": {"B0": es(1), "B3": es(1)},
            "d": {"B0": es(1), "B3": es(1)}},
        1: {"a": {"B0": es(1), "B3": es(1)}, "b": {"B0": es(0), "B3": es(1)}, "c": {"B0": es(1), "B3": es(1)},
            "d": {"B0": es(1)}},
        2: {"a": {"B0": es(1), "B3": es(0)}, "b": {"B0": es(1), "B3": es(1)}, "c": {"B0": es(1), "B3": es(1)},
            "d": {"B0": es(1), "B3": es(1)}},
    }
    r = A.sampling_reliability(greedy, sampled)       # c fails the greedy gate, d lacks seed 1 at B3
    assert r["k"] == 3 and r["n_greedy_b0_success"] == 3 and r["n_excluded_incomplete_seeds"] == 1
    assert r["fail_any_b1"]["n"] == 2 and r["fail_any_b1"]["point"] == 0.5          # a
    assert r["fail_any_b0_noise_floor"]["point"] == 0.5                              # b
    assert r["excess"]["point"] == 0.0 and r["fail_all_b1"]["point"] == 0.0
    assert r["n_failures_b1_distribution"] == {"0": 1, "1": 0, "2": 1, "3": 0}


def test_arm_records_and_intersection_of_gates():
    N = {"a": {"B0": o(1, 0), "B3": o(0, 1, clr=1)}, "b": {"B0": o(1, 0), "B3": o(1, 0)},
         "c": {"B0": o(0, 1), "B3": o(1, 0)}, "d": {"B0": o(1, 0)}}
    T = {"a": {"B0": o(1, 0), "B3": o(1, 0)}, "b": {"B0": o(0, 0), "B3": o(1, 1)},
         "c": {"B0": o(1, 0), "B3": o(1, 0)}, "d": {"B0": o(1, 0), "B3": o(1, 0)}}
    rn, rt = A.arm_records(N), A.arm_records(T)
    assert rn == {"a": {"ES": 0, "CLR": 1, "RR": 1, "RRs": 1}, "b": {"ES": 1, "CLR": 0, "RR": 0, "RRs": 0},
                  "c": {"ES": 1, "CLR": 0, "RR": None, "RRs": None}}
    assert rt["b"] == {"ES": 0, "CLR": 0, "RR": None, "RRs": None}
    con = A.arm_contrasts({"N": rn, "T": rt}, contrasts=(("T", "N"),), metric_names=("ES", "RR", "CLR"))["T-N"]
    # ES over a, b, c (d lacks B3 in N): (1-0) + (0-1) + (1-1) = 0
    assert con["ES"]["n"] == 3 and con["ES"]["point"] == 0.0
    # RR: only a passes both gates (b fails T's gate, c fails N's): 0 - 1
    assert con["RR"]["n"] == 1 and con["RR"]["point"] == -1.0
    assert con["CLR"]["point"] == round(-1 / 3, 4)
    assert "ES@B0 in both arms" in con["RR"]["denominator"]


def test_answer_parity():
    ra = [A.normalise_row(_legacy("c1", "B0", "x", cot="")), A.normalise_row(_legacy("c2", "B0", "y"))]
    rb = [A.normalise_row(_legacy("c1", "B0", "x", cot="")), A.normalise_row(_legacy("c2", "B0", "z")),
          A.normalise_row(_legacy("c3", "B0", "w"))]
    assert A.answer_parity(ra, rb) == {"budget": "B0", "n": 2, "identical_answer": 1, "identical_chain": 2}
