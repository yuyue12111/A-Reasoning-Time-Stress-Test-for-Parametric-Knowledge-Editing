"""CPU unit tests for the X3 paraphrase content audit aggregator."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x3_para_readability as x3


def test_majority():
    assert x3.majority([True, True, False]) is True
    assert x3.majority([False, True, False]) is False


def test_agreement():
    out = x3.agreement([[True, True, True], [False, False, True]])
    assert out["n_items"] == 2
    assert out["unanimous"] == 1
    assert out["two_one"] == 1
    assert out["raw_pairwise_agreement"]["equal_pairs"] == 4
    assert out["raw_pairwise_agreement"]["all_pairs"] == 6


def test_validate_rejects_non_boolean():
    manifest = {"records": [{"case_id": "c1"}]}
    rows = [{
        "case_id": "c1",
        "para0": {"readable": 1, "answerable_same_fact": True,
                  "prefix_changes_requested_fact": False, "reason": "x"},
        "para1": {"readable": True, "answerable_same_fact": True,
                  "prefix_changes_requested_fact": False, "reason": "x"},
    }]
    try:
        x3.validate_judge(rows, manifest, "J")
    except ValueError as exc:
        assert "expected boolean" in str(exc)
    else:
        raise AssertionError("non-boolean vote was accepted")


if __name__ == "__main__":
    test_majority(); print("ok majority")
    test_agreement(); print("ok agreement")
    test_validate_rejects_non_boolean(); print("ok validation")
