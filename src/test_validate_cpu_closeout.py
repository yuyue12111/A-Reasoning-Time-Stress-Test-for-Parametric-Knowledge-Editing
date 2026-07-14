"""Standalone CPU tests for validate_cpu_closeout.py."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_cpu_closeout as vcc


UNIT = "unique case_id; retain all available scale/family rows"


def _metric(scope, point=0.1):
    return {"point": point, "ci95": [0.01, 0.2], "n_rows": 20,
            "n_case_blocks": 10, "bootstrap_unit": UNIT,
            "inference_scope": scope}


def _dup_audit(status="PASS"):
    return {"status": status,
            "world_key": ["case_id", "budget", "probe", "decode", "seed", "temperature"],
            "n_unique_worlds": 20, "n_duplicate_keys": 0,
            "n_duplicate_rows_deduplicated": 0, "duplicate_keys": []}


def _valid_objects():
    per_scope = "fact-sampling uncertainty conditional on six fixed checkpoints"
    cap3_scope = "fact-sampling uncertainty conditional on five matched fixed checkpoints"
    b15_scope = "fact-sampling uncertainty conditional on fixed checkpoints"
    percase = {
        "_config": {"n_rows_total": 20,
                    "scales_detected": {f"s{i}": "tag" for i in range(6)}},
        "_provenance": {"duplicate_world_audit": _dup_audit()},
        **{name: _metric(per_scope) for name in
           ("es_drop", "rr", "clr", "clr_density", "clr_rev")},
    }
    b15 = {
        "base_budget": "B0",
        "n_matched": 20, "scales_matched": [f"s{i}" for i in range(5)],
        "_provenance": {
            "edited": {"duplicate_world_audit": _dup_audit()},
            "base": {"duplicate_world_audit": {
                **_dup_audit(),
                "selected": {"budget": "B0", "probe": "base",
                             "decode": "greedy", "seed": None},
            }},
        },
        "baseline_matched": _metric(b15_scope),
        "b15_controlled": _metric(b15_scope),
        "strat_base_known": _metric(b15_scope),
        "strat_base_unknown": _metric(b15_scope),
    }
    cap3 = {
        "_provenance": {
            "edited": {"duplicate_world_audit": _dup_audit()},
            "base": {"duplicate_world_audit": _dup_audit()},
        },
        "net_clr": _metric(cap3_scope),
        "clr_on_baseCLR0": _metric(cap3_scope),
        "clr_raw_matched": _metric(cap3_scope),
        "_per_scale": {f"checkpoint-{i}": {"n": 10} for i in range(5)},
        "_family_row_sensitivity": {
            name: {"point": 0.1, "ci95": [-0.1, 0.3],
                   "bootstrap_unit": "family then row"}
            for name in ("net_clr", "clr_on_baseCLR0", "clr_raw_matched")
        },
        "_inference_scope": (
            "primary intervals resample unique case_id blocks and retain every available "
            "fixed-checkpoint row for that fact; uncertainty is conditional on the five matched "
            "observed checkpoints"),
    }
    f3 = {
        "status": "PASS",
        "protocol": {"decode": "sample", "probe": "efficacy",
                     "pair_key": ["case_id", "seed", "budget"],
                     "sample_seed_field": "seed", "b0_gate": "same case_id and same seed",
                     "case_aggregation": "mean over paired seeds", "bootstrap_unit": "unique case_id"},
        "audit": {"duplicate_keys": [], "unexpected_case_rows": [], "unexpected_seed_rows": [],
                  "expected_seeds": [0, 1, 2], "missing_pairs": [], "error_rows": []},
        "primary_complete_cases": {"n_cases": 10, "n_seed_pairs": 30, "metrics": {}},
    }
    x2 = {
        "arms_n": {"N": 20, "T": 20, "C": 20},
        "input_duplicate_audit": {arm: _dup_audit() for arm in ("N", "T", "C")},
        "contrasts": {"T-C": {"ES": {"n": 20, "mean": 0.1, "ci": [0.02, 0.2], "p": 0.01}}},
    }
    contrast = {"n_cases": 20, "n_rows": 40, "mean_A": .5, "mean_B": .4,
                "diff_A_minus_B": .1, "ci": [.02, .18], "bootstrap_p_two_sided": .01,
                "bootstrap_unit": "case_id", "paired_unit": "case_id+paraphrase_probe"}
    cn = {**contrast, "diff_A_minus_B": 0.0, "ci": [-.02, .02]}
    x3 = {
        "contrasts": {"T-C": contrast, "C-N": cn, "T-N": contrast},
        "decision": {"status": "PASS", "x3_primary_confirmed": True,
                     "criterion": "paired case-cluster bootstrap CI lower bound > 0",
                     "C_minus_N": {"role": "non_gating_diagnostic",
                                   "equivalence": {"status": "NOT_TESTED", "margin": None}},
                     "T_minus_N": {"role": "non_gating_descriptive_contrast"}},
        "historical_preregistered_gate": {"_role": "HISTORICAL_PREREGISTERED_GATE_AUDIT_ONLY"},
    }
    p0 = {"status": "PASS", "technical_status": "PASS", "official_x1_gate": "UNCHANGED",
          "logitlens": {"status": "PASS"}}
    return {"percase": percase, "b15": b15, "cap3": cap3,
            "f3": f3, "x2": x2, "x3": x3, "p0": p0}


def _write_fixture(objects, include_p0=True):
    tmp = tempfile.mkdtemp()
    paths = {}
    for name, value in objects.items():
        if name == "p0" and not include_p0:
            continue
        path = os.path.join(tmp, name + ".json")
        with open(path, "w") as f:
            json.dump(value, f)
        paths[name] = path
    if not include_p0:
        paths["p0"] = os.path.join(tmp, "missing-p0.json")
    return paths


def test_valid_closeout_passes_and_optional_p0_is_summarized():
    report = vcc.validate_paths(_write_fixture(_valid_objects()))
    assert report["status"] == "PASS", report
    assert not report["failures"]
    assert report["summary"]["percase"]["n_checkpoints"] == 6
    assert report["summary"]["cap3"]["n_matched_checkpoints"] == 5
    assert report["summary"]["cap3"]["family_row_sensitivity_role"] == "SENSITIVITY_ONLY"
    assert report["summary"]["x3"]["C_minus_N_equivalence"]["status"] == "NOT_TESTED"


def test_case_block_scope_and_duplicate_audit_fail_closed():
    objects = _valid_objects()
    objects["percase"]["es_drop"]["bootstrap_unit"] = "row"
    objects["b15"]["_provenance"]["edited"]["duplicate_world_audit"]["status"] = "FAIL"
    report = vcc.validate_paths(_write_fixture(objects))
    assert report["status"] == "FAIL"
    text = "\n".join(report["failures"])
    assert "percase.es_drop" in text and "b15._provenance.edited" in text


def test_b15_requires_b0_base_recall_and_base_duplicate_audit():
    objects = _valid_objects()
    objects["b15"]["base_budget"] = "B3"
    objects["b15"]["_provenance"]["base"]["duplicate_world_audit"]["selected"]["budget"] = "B3"
    objects["b15"]["_provenance"]["base"]["duplicate_world_audit"]["status"] = "FAIL"
    report = vcc.validate_paths(_write_fixture(objects))
    assert report["status"] == "FAIL"
    text = "\n".join(report["failures"])
    assert "b15.base_budget='B3'" in text
    assert "selected.budget='B3'" in text
    assert "b15._provenance.base" in text


def test_f3_same_seed_and_no_duplicate_protocol_is_enforced():
    objects = _valid_objects()
    objects["f3"]["protocol"]["b0_gate"] = "first row from any seed"
    objects["f3"]["audit"]["duplicate_keys"] = [{"case_id": "c", "seed": 0, "budget": "B0"}]
    report = vcc.validate_paths(_write_fixture(objects))
    assert report["status"] == "FAIL"
    text = "\n".join(report["failures"])
    assert "f3.protocol.b0_gate" in text and "duplicate_keys must be empty" in text


def test_cap3_primary_case_blocks_and_both_duplicate_audits_fail_closed():
    objects = _valid_objects()
    objects["cap3"]["net_clr"]["bootstrap_unit"] = "family then row"
    objects["cap3"]["_provenance"]["edited"]["duplicate_world_audit"]["status"] = "FAIL"
    objects["cap3"]["_provenance"]["base"]["duplicate_world_audit"]["status"] = "FAIL"
    objects["cap3"]["_per_scale"].pop("checkpoint-4")
    report = vcc.validate_paths(_write_fixture(objects))
    assert report["status"] == "FAIL"
    text = "\n".join(report["failures"])
    assert "cap3.net_clr" in text
    assert "cap3._provenance.edited" in text
    assert "cap3._provenance.base" in text
    assert "expected five matched fixed checkpoints" in text


def test_cap3_does_not_promote_family_row_sensitivity_when_primary_is_missing():
    objects = _valid_objects()
    del objects["cap3"]["clr_on_baseCLR0"]
    report = vcc.validate_paths(_write_fixture(objects))
    assert report["status"] == "FAIL"
    assert any("cap3.clr_on_baseCLR0: missing metric block" in failure
               for failure in report["failures"])


def test_x2_duplicate_audits_and_world_key_are_required():
    objects = _valid_objects()
    del objects["x2"]["input_duplicate_audit"]["C"]
    objects["x2"]["input_duplicate_audit"]["T"]["world_key"] = ["case_id", "budget"]
    report = vcc.validate_paths(_write_fixture(objects))
    assert report["status"] == "FAIL"
    text = "\n".join(report["failures"])
    assert "missing arms ['C']" in text and "must distinguish decode" in text


def test_x3_fake_equivalence_and_unsound_decision_are_rejected():
    objects = _valid_objects()
    objects["x3"]["decision"]["status"] = "FAIL"
    objects["x3"]["decision"]["C_minus_N"]["equivalence"] = {
        "status": "EQUIVALENT", "margin": .03, "ci90": [-.01, .01]}
    objects["x3"]["historical_preregistered_gate"]["_role"] = "PRIMARY"
    report = vcc.validate_paths(_write_fixture(objects))
    assert report["status"] == "FAIL"
    text = "\n".join(report["failures"])
    assert "derived 'PASS'" in text and "equivalence was certified" in text
    assert "not quarantined" in text


def test_missing_optional_p0_is_warning_not_failure():
    report = vcc.validate_paths(_write_fixture(_valid_objects(), include_p0=False))
    assert report["status"] == "PASS", report
    assert report["summary"]["p0"]["status"] == "MISSING_OPTIONAL"
    assert any("optional artifact not found" in warning for warning in report["warnings"])


TESTS = [
    test_valid_closeout_passes_and_optional_p0_is_summarized,
    test_case_block_scope_and_duplicate_audit_fail_closed,
    test_b15_requires_b0_base_recall_and_base_duplicate_audit,
    test_f3_same_seed_and_no_duplicate_protocol_is_enforced,
    test_cap3_primary_case_blocks_and_both_duplicate_audits_fail_closed,
    test_cap3_does_not_promote_family_row_sensitivity_when_primary_is_missing,
    test_x2_duplicate_audits_and_world_key_are_required,
    test_x3_fake_equivalence_and_unsound_decision_are_rejected,
    test_missing_optional_p0_is_warning_not_failure,
]


if __name__ == "__main__":
    for test in TESTS:
        test()
        print("ok", test.__name__)
    print("OK validate_cpu_closeout: all tests passed")
