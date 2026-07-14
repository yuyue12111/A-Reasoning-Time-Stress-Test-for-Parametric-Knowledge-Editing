"""CPU tests for the seed-paired F3 sampling recalculation."""

import json
import os
import sys
import tempfile

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import f3_sampling_recalc as f3


CASES = [
    {"case_id": "c1", "s": "", "o_old": "Paris", "o_new": "Rome"},
    {"case_id": "c2", "s": "", "o_old": "Paris", "o_new": "Rome"},
]


def _row(cid, seed, budget, answer, cot=""):
    return {"case_id": cid, "seed": seed, "budget": budget, "probe": "efficacy",
            "decode": "sample", "answer": answer, "cot": cot}


def _jsonl(rows):
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    return path


def test_same_seed_gate_and_case_aggregation():
    # c1 deliberately writes seed1 first. seed1 B0 fails, seed0 B0 succeeds;
    # the correct RR gate therefore keeps only seed0. The legacy first-row gate
    # drops all c1 target seeds and produces a different answer.
    rows = [
        _row("c1", 1, "B0", "Paris"),
        _row("c1", 1, "B3", "Paris", "Paris"),
        _row("c1", 0, "B0", "Rome"),
        _row("c1", 0, "B3", "Paris", "Paris"),
        _row("c2", 1, "B0", "Rome"),
        _row("c2", 1, "B3", "Rome"),
        _row("c2", 0, "B0", "Rome"),
        _row("c2", 0, "B3", "Rome"),
    ]
    path = _jsonl(rows)
    try:
        out = f3.analyze([path], CASES, {}, [0, 1], n_boot=400, bootstrap_seed=7,
                         include_case_summaries=True)
    finally:
        os.remove(path)

    assert out["status"] == "PASS"
    m = out["primary_complete_cases"]["metrics"]
    assert m["ES_B0"]["point"] == 0.75
    assert m["ES_B3"]["point"] == 0.5
    assert m["ES_drop"]["point"] == 0.25
    assert m["RR_B3"]["point"] == 0.5
    assert m["RRs_B3"]["point"] == 0.5
    assert m["CLR_B3"]["point"] == 0.5
    assert m["RR_B3"]["n_cases"] == 2
    assert m["RR_B3"]["n_seed_pairs"] == 3  # c1 seed0 + c2 seeds0/1

    old = out["old_first_row_sensitivity"]
    assert old["RR_B3_first_B0_gate_row_weighted"] == 0.0
    assert old["ES_drop_first_row"] == 0.0
    assert old["first_seed_histogram"]["B0"] == {"1": 2}
    c1 = next(row for row in out["case_summaries"]["primary_complete_cases"]
              if row["case_id"] == "c1")
    assert c1["n_b0ok_seed_pairs"] == 1
    assert [row["RR_B3"] for row in c1["per_seed"]] == [1, None]


def test_missing_pair_audit_and_complete_case_primary():
    rows = [
        _row("c1", 0, "B0", "Rome"), _row("c1", 0, "B3", "Rome"),
        _row("c1", 1, "B0", "Rome"), _row("c1", 1, "B3", "Paris"),
        _row("c2", 0, "B0", "Rome"), _row("c2", 0, "B3", "Rome"),
        _row("c2", 1, "B0", "Rome"),  # c2/seed1/B3 missing
    ]
    path = _jsonl(rows)
    try:
        out = f3.analyze([path], CASES, {}, [0, 1], n_boot=200, bootstrap_seed=3)
    finally:
        os.remove(path)

    assert out["status"] == "PASS_WITH_MISSING_PAIRS"
    audit = out["audit"]
    assert audit["complete_case_seed_pairs"] == 3
    assert audit["cases_with_all_expected_seeds"] == 1
    assert audit["cases_with_any_complete_pair"] == 2
    assert audit["complete_seed_count_histogram"] == {"1": 1, "2": 1}
    assert audit["missing_pairs"] == [
        {"case_id": "c2", "seed": 1, "missing_budgets": ["B3"]}
    ]
    assert out["primary_complete_cases"]["n_cases"] == 1
    assert out["available_pair_sensitivity"]["n_cases"] == 2
    assert out["per_seed_sensitivity"]["1"]["n_cases"] == 1


def test_duplicate_key_is_hard_failure():
    rows = [
        _row("c1", 0, "B0", "Rome"),
        _row("c1", 0, "B0", "Rome"),
        _row("c1", 0, "B3", "Paris"),
    ]
    path = _jsonl(rows)
    try:
        out = f3.analyze([path], CASES[:1], {}, [0], n_boot=0)
    finally:
        os.remove(path)

    assert out["status"] == "FAIL_DUPLICATE_KEYS"
    dup = out["audit"]["duplicate_keys"]
    assert len(dup) == 1
    assert (dup[0]["case_id"], dup[0]["seed"], dup[0]["budget"]) == ("c1", 0, "B0")
    assert dup[0]["byte_identical"] is True
    assert "primary_complete_cases" not in out


def test_unexpected_seed_is_hard_provenance_failure():
    rows = [
        _row("c1", 0, "B0", "Rome"), _row("c1", 0, "B3", "Rome"),
        _row("c1", 9, "B0", "Rome"), _row("c1", 9, "B3", "Paris"),
    ]
    path = _jsonl(rows)
    try:
        out = f3.analyze([path], CASES[:1], {}, [0], n_boot=0)
    finally:
        os.remove(path)
    assert out["status"] == "FAIL_CASE_OR_SEED_DRIFT"
    assert len(out["audit"]["unexpected_seed_rows"]) == 2
    assert "primary_complete_cases" not in out


def test_bootstrap_resamples_four_cases_not_twelve_seed_rows():
    cases = [{"case_id": f"c{i}", "s": "", "o_old": "Paris", "o_new": "Rome"}
             for i in range(4)]
    rows = []
    for i, case in enumerate(cases):
        for seed in (0, 1, 2):
            rows.append(_row(case["case_id"], seed, "B0", "Rome"))
            rows.append(_row(case["case_id"], seed, "B3", "Paris" if i >= 2 else "Rome"))
    path = _jsonl(rows)
    try:
        a = f3.analyze([path], cases, {}, [0, 1, 2], n_boot=1200, bootstrap_seed=11)
        b = f3.analyze([path], cases, {}, [0, 1, 2], n_boot=1200, bootstrap_seed=11)
    finally:
        os.remove(path)

    assert a == b
    drop = a["primary_complete_cases"]["metrics"]["ES_drop"]
    assert drop["point"] == 0.5
    assert drop["n_cases"] == 4
    assert drop["n_seed_pairs"] == 12
    assert drop["bootstrap_unit"] == "case_id"
    assert a["audit"]["cases_with_all_expected_seeds"] == 4


def test_subject_scrub_matches_paper_metric():
    subject = "Miami International Film Festival"
    cases = [{"case_id": "c1", "s": subject, "o_old": "Miami", "o_new": "Latvia"}]
    rows = [
        _row("c1", 0, "B0", f"The {subject} is in Latvia", f"Question about {subject}"),
        _row("c1", 0, "B3", f"The {subject} is in Latvia", f"Question about {subject}"),
    ]
    path = _jsonl(rows)
    try:
        out = f3.analyze([path], cases, {}, [0], n_boot=0)
    finally:
        os.remove(path)
    m = out["primary_complete_cases"]["metrics"]
    assert m["ES_B0"]["point"] == 1.0
    assert m["ES_B3"]["point"] == 1.0
    assert m["CLR_B3"]["point"] == 0.0


def test_config_resolution_and_exact_shard_glob():
    with tempfile.TemporaryDirectory() as td:
        dataset = os.path.join(td, "cases.jsonl")
        aliases = os.path.join(td, "aliases.json")
        out_dir = os.path.join(td, "results")
        config = os.path.join(td, "f3.yaml")
        os.makedirs(out_dir)
        with open(dataset, "w", encoding="utf-8") as f:
            for case in CASES:
                f.write(json.dumps(case) + "\n")
        with open(aliases, "w", encoding="utf-8") as f:
            json.dump({}, f)
        cfg = {
            "model_tag": "model", "seed": 42, "out_dir": out_dir,
            "dataset": {"tag": "cf2samp", "path": dataset, "n": 2},
            "sampling": {"enabled": True, "seeds": [0, 1]},
        }
        with open(config, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f)
        shard = os.path.join(out_dir, "model_ROME_cf2samp_r0of1.jsonl")
        rows = []
        for case in CASES:
            for seed in (0, 1):
                rows += [_row(case["case_id"], seed, "B0", "Rome"),
                         _row(case["case_id"], seed, "B3", "Rome")]
        with open(shard, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")

        inputs = f3.resolve_inputs(config, "ROME", aliases_path=aliases)
        assert inputs["expected_seeds"] == [0, 1]
        assert inputs["shards"] == [shard]
        report = f3.analyze(inputs["shards"], inputs["cases"], inputs["aliases"],
                            inputs["expected_seeds"], n_boot=0)
        assert report["status"] == "PASS"
        assert report["primary_complete_cases"]["n_cases"] == 2


TESTS = [
    test_same_seed_gate_and_case_aggregation,
    test_missing_pair_audit_and_complete_case_primary,
    test_duplicate_key_is_hard_failure,
    test_unexpected_seed_is_hard_provenance_failure,
    test_bootstrap_resamples_four_cases_not_twelve_seed_rows,
    test_subject_scrub_matches_paper_metric,
    test_config_resolution_and_exact_shard_glob,
]


def _main():
    failed = 0
    for test in TESTS:
        try:
            test()
            print(f"  [PASS] {test.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"  [FAIL] {test.__name__}: {exc}")
    print("ALL PASS" if failed == 0 else f"FAILED ({failed})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
