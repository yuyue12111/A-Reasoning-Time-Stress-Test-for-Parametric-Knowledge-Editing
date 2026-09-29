"""The G0 gate passes a rerun that matches Study 1 and fails one whose B0 answers drift."""
from rt import g0

CASES = {f"cf_{i}": {"case_id": f"cf_{i}", "s": f"Subject{i}", "o_old": "Norway", "o_new": "Bulgaria",
                     "prompt": f"Subject{i} is located in"} for i in range(40)}


def _rows(b0_new, b3_new):
    rows = []
    for i, cid in enumerate(CASES):
        for budget, new in (("B0", b0_new(i)), ("B3", b3_new(i))):
            rows.append({"case_id": cid, "budget": budget, "probe": "efficacy", "decode": "greedy",
                         "seed": None, "temperature": None, "q": CASES[cid]["prompt"], "cot": "",
                         "answer": "Bulgaria." if new else "Norway.", "model_tag": "m", "editor": "ROME",
                         "target_tag": "cf", "condition": "rome_N", "arm": "N", "alpha": 1.0,
                         "chain_end": "think_end" if budget == "B3" else None})
    return rows


def _norm(rows):
    from rt import analysis as A
    return [A.normalise_row(r) for r in rows]


def test_identical_rerun_passes():
    s1 = _norm(_rows(lambda i: i % 4 != 0, lambda i: i % 3 != 0))
    res = g0.verdict(s1, s1, CASES, {}, min_shared=40, study1_ci=None)
    assert res["pass"] and res["b0_es_agreement"]["rate"] == 1.0


def test_drifting_b0_fails():
    s1 = _norm(_rows(lambda i: i % 4 != 0, lambda i: i % 3 != 0))
    v2 = _norm(_rows(lambda i: i % 2 == 0, lambda i: i % 3 != 0))
    res = g0.verdict(s1, v2, CASES, {}, min_shared=40, study1_ci=None)
    assert not res["criterion_2_b0_agreement"] and not res["pass"]


def test_partial_rerun_fails_even_when_its_drop_fits():
    """A rerun that covers only part of the pool must fail, whatever its drop (review 2026-09-29)."""
    s1 = _norm(_rows(lambda i: i % 4 != 0, lambda i: i % 3 != 0))
    v2 = [r for r in s1 if int(r["case_id"].split("_")[1]) < 10]
    res = g0.verdict(s1, v2, CASES, {}, min_shared=38, study1_ci=None)
    assert not res["criterion_0_complete"] and not res["pass"]
    assert res["completeness"]["shared_paired"] == 10


def test_fixed_study1_ci_is_used():
    s1 = _norm(_rows(lambda i: i % 4 != 0, lambda i: i % 3 != 0))
    res = g0.verdict(s1, s1, CASES, {}, min_shared=40, study1_ci=(0.5, 0.6))
    assert res["study1_ci_used"] == [0.5, 0.6] and not res["criterion_1_drop_inside_study1_ci"]
    assert g0.STUDY1_CI == (0.030, 0.182) and g0.MIN_SHARED == 198
