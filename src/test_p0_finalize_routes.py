"""CPU checks for final P0 route aggregation."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p0_finalize_routes as p0r


def test_route_majority():
    assert p0r.route_majority(["Bridge", "Bridge", "Recall"]) == "Bridge"
    try:
        p0r.route_majority(["Bridge", "Recall", "Associative"])
    except ValueError as exc:
        assert "1-1-1" in str(exc)
    else:
        raise AssertionError("route split was accepted")


def test_route_agreement():
    rows = [{"votes": ["Bridge", "Bridge", "Bridge"]},
            {"votes": ["Recall", "Recall", "Bridge"]}]
    out = p0r.route_agreement(rows)
    assert out["unanimous_cases"] == 1 and out["two_one_cases"] == 1
    assert out["raw_pairwise_agreement"]["equal_pairs"] == 4
    assert out["raw_pairwise_agreement"]["all_pairs"] == 6


def test_require_frozen_vote_match():
    frozen = ["Bridge", "Recall", "Bridge"]
    assert p0r.require_frozen_vote_match("x", frozen, list(frozen)) == frozen
    for live in (["Bridge", "Bridge", "Recall"], ["Bridge", "Recall"],
                 ["Bridge", "Recall", "Excluded-held"]):
        try:
            p0r.require_frozen_vote_match("x", frozen, live)
        except ValueError:
            pass
        else:
            raise AssertionError(f"mismatched/invalid live votes accepted: {live}")


if __name__ == "__main__":
    test_route_majority(); print("ok majority")
    test_route_agreement(); print("ok agreement")
    test_require_frozen_vote_match(); print("ok frozen vote lock")
