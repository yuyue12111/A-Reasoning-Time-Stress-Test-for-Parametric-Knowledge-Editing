"""Pure-CPU tests for X3 case-clustered paraphrase analysis."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cross_arm_para as cap


def _arm(vals):
    # vals: {(cid,budget,probe): {PS,old_commit}}
    return {"indicators": vals}


def test_cluster_pairing_preserves_both_paraphrases():
    A = _arm({("c1", "B3", "para0"): {"PS": 1},
              ("c1", "B3", "para1"): {"PS": 1},
              ("c2", "B3", "para0"): {"PS": 0}})
    B = _arm({("c1", "B3", "para0"): {"PS": 0},
              ("c1", "B3", "para1"): {"PS": 0},
              ("c2", "B3", "para0"): {"PS": 1}})
    r = cap.paired_cluster_diff(A, B, n_boot=2000)
    assert r["n_cases"] == 2 and r["n_rows"] == 3
    assert abs(r["diff_A_minus_B"] - (1 / 3)) < 1e-6
    assert r["bootstrap_unit"] == "case_id"


def test_allowed_gate_is_fixed_row_subset():
    A = _arm({("c1", "B3", "para0"): {"old_commit": 0},
              ("c1", "B3", "para1"): {"old_commit": 1},
              ("c2", "B3", "para0"): {"old_commit": 0}})
    B = _arm({("c1", "B3", "para0"): {"old_commit": 1},
              ("c1", "B3", "para1"): {"old_commit": 0},
              ("c2", "B3", "para0"): {"old_commit": 1}})
    gate = {("c1", "para0"), ("c2", "para0")}
    r = cap.paired_cluster_diff(A, B, metric="old_commit", allowed_keys=gate, n_boot=1000)
    assert r["n_cases"] == 2 and r["n_rows"] == 2
    assert r["diff_A_minus_B"] == -1.0


def test_unmatched_rows_are_not_unpaired_pseudoreplication():
    A = _arm({("c1", "B3", "para0"): {"PS": 1},
              ("c1", "B3", "para1"): {"PS": 1}})
    B = _arm({("c1", "B3", "para0"): {"PS": 0}})
    r = cap.paired_cluster_diff(A, B, n_boot=500)
    assert r["n_cases"] == 1 and r["n_rows"] == 1
    assert r["diff_A_minus_B"] == 1.0


def test_sound_primary_decision_uses_only_T_minus_C_ci():
    contrasts = {
        "T-C": {"diff_A_minus_B": 0.06, "ci": [0.01, 0.11]},
        # Deliberately excludes zero: this makes the legacy joint gate fail, but cannot veto T-C.
        "C-N": {"diff_A_minus_B": 0.07, "ci": [0.03, 0.10]},
        "T-N": {"diff_A_minus_B": 0.13, "ci": [0.08, 0.18]},
    }
    decision, historical = cap.inference_decisions(contrasts, secondary_gate_cases=145)
    assert decision["status"] == "PASS"
    assert decision["x3_primary_confirmed"] is True
    assert decision["C_minus_N"]["compatibility_status"] == "NOT_COMPATIBLE_WITH_ZERO"
    assert decision["C_minus_N"]["equivalence"]["status"] == "NOT_TESTED"
    assert historical["x3_primary_pass"] is False
    assert historical["_role"] == "HISTORICAL_PREREGISTERED_GATE_AUDIT_ONLY"


def test_positive_T_minus_N_cannot_rescue_null_primary():
    contrasts = {
        "T-C": {"diff_A_minus_B": 0.02, "ci": [-0.01, 0.05]},
        "C-N": {"diff_A_minus_B": 0.00, "ci": [-0.03, 0.03]},
        "T-N": {"diff_A_minus_B": 0.08, "ci": [0.04, 0.12]},
    }
    decision, _historical = cap.inference_decisions(contrasts, secondary_gate_cases=150)
    assert decision["status"] == "FAIL"
    assert decision["x3_primary_confirmed"] is False
    assert decision["T_minus_N"]["point_estimate_positive"] is True
    assert decision["T_minus_N"]["ci_excludes_zero"] is True
    assert decision["T_minus_N"]["role"] == "non_gating_descriptive_contrast"


def test_equivalence_is_not_tested_without_explicit_margin_and_uses_tost_when_supplied():
    contrasts = {
        "T-C": {"diff_A_minus_B": 0.06, "ci": [0.01, 0.11]},
        "C-N": {"diff_A_minus_B": 0.00, "ci": [-0.025, 0.025]},
        "T-N": {"diff_A_minus_B": 0.06, "ci": [0.01, 0.11]},
    }
    no_margin, _ = cap.inference_decisions(contrasts, secondary_gate_cases=145)
    assert no_margin["C_minus_N"]["equivalence"]["status"] == "NOT_TESTED"

    with_margin, _ = cap.inference_decisions(
        contrasts, secondary_gate_cases=145, equivalence_margin=0.03,
        cn_equivalence={"ci": [-0.02, 0.02]})
    eq = with_margin["C_minus_N"]["equivalence"]
    assert eq["status"] == "EQUIVALENT" and eq["passed"] is True
    assert eq["margin"] == 0.03 and eq["ci90"] == [-0.02, 0.02]

    try:
        cap.inference_decisions(
            contrasts, secondary_gate_cases=145, equivalence_margin=0.0,
            cn_equivalence={"ci": [0.0, 0.0]})
    except ValueError as exc:
        assert "must be positive" in str(exc)
    else:
        raise AssertionError("non-positive post-hoc equivalence margin was accepted")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("ok", name)
    print("OK cross_arm_para: all tests passed")
