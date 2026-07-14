"""Repository-backed CPU tests for the frozen P0 candidate builder."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p0_membership as p0


def test_candidate_population_is_101_unique_instances():
    rows = p0.build_candidates()
    assert len(rows) == 101
    assert len({row["item_id"] for row in rows}) == 101
    assert sum(row["pool"] == "a3" for row in rows) == 33
    assert sum(row["pool"] == "b16" for row in rows) == 68
    assert sum(row["current_in_population"] for row in rows) == 50


def test_majority_and_route_actions_inputs():
    label, counts, n, split = p0.majority([
        {"committed": "old"}, {"committed": "old"}, {"committed": "neither"}])
    assert label == "old" and counts["old"] == 2 and n == 3 and not split
    label, _, _, split = p0.majority([
        {"committed": "old"}, {"committed": "new"}, {"committed": "neither"}])
    assert label == "neither" and split
    label, _, n, _ = p0.majority([{"committed": "old"}, {"committed": "new"}])
    assert label == "insufficient" and n == 2


def test_membership_agreement_is_item_clustered():
    rows = [
        {"votes": [{"committed": "old"}, {"committed": "old"}, {"committed": "old"}]},
        {"votes": [{"committed": "old"}, {"committed": "old"}, {"committed": "new"}]},
        {"votes": [{"committed": "old"}, {"committed": "new"}, {"committed": "neither"}]},
    ]
    out = p0.membership_agreement(rows)
    assert out["unanimous_cases"] == 1
    assert out["two_one_majority_cases"] == 1
    assert out["split_1_1_1_cases"] == 1
    assert out["raw_pairwise_agreement"] == {"equal_pairs": 4, "all_pairs": 9,
                                                "rate": 4 / 9}
    assert abs(out["fleiss_kappa"] - (-0.125)) < 1e-12


def test_strict_jsonl_rejects_duplicates_and_bad_judge_labels():
    with tempfile.TemporaryDirectory() as td:
        dup = os.path.join(td, "dup.jsonl")
        with open(dup, "w") as f:
            f.write(json.dumps({"item_id": "x"}) + "\n")
            f.write(json.dumps({"item_id": "x"}) + "\n")
        try:
            p0.read_jsonl_strict(dup, "dup")
        except ValueError as exc:
            assert "duplicate item_id" in str(exc)
        else:
            raise AssertionError("duplicate item_id was accepted")

        bad = [{"item_id": "x", "committed": "OLD", "reason": "x"}]
        try:
            p0.validate_judge_rows(bad, ["x"], "J1")
        except ValueError as exc:
            assert "invalid committed" in str(exc)
        else:
            raise AssertionError("invalid judge label was accepted")


if __name__ == "__main__":
    test_candidate_population_is_101_unique_instances(); print("ok population")
    test_majority_and_route_actions_inputs(); print("ok majority")
    test_membership_agreement_is_item_clustered(); print("ok agreement")
    test_strict_jsonl_rejects_duplicates_and_bad_judge_labels(); print("ok strict")
