"""CPU tests for the P0 downstream crosswalk."""
import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p0_downstream_crosswalk as p0x


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def args_for_repo():
    return argparse.Namespace(
        membership_audit="results/p0_membership_audit.json",
        corrected_taxonomy="results/p0_corrected_taxonomy.json",
        x1_manifest="data/x1_replay_manifest.jsonl",
        x1_gate="results/x1_replay_gate.json",
        necessity="results/necessity.json",
        aliases="data/aliases.json",
        a3_labels_glob="results/a3/labels_*.jsonl",
        wa_edited_glob="results/wa/edited_r*of8.jsonl",
        logitlens="results/probe/logitlens_cf200_ROME_B3.jsonl",
        logitlens_expected_n=23,
        out="results/p0_downstream_crosswalk.json",
    )


def test_x1_source_mapping():
    assert p0x.x1_item_id({"source": "main_b3_greedy", "case_id": "cf_1"}) == "a3|32b|cf_1"
    assert p0x.x1_item_id({"source": "f2_b1_greedy", "case_id": "cf_2"}) == "b16|qwen32b-F2B1|cf_2"
    assert p0x.x1_item_id({"source": "f3_historical_sample_seed2", "case_id": "cf_3"}) == "b16|qwen32b-sample|cf_3"
    try:
        p0x.x1_item_id({"source": "invented", "case_id": "cf_4"})
    except ValueError as exc:
        assert "unknown X1 source" in str(exc)
    else:
        raise AssertionError("unknown X1 source arm was accepted")


def test_current_repo_crosswalk_numbers():
    report = p0x.build_report(args_for_repo())
    assert report["technical_status"] == "PASS"
    assert report["official_x1_gate"] == "UNCHANGED: preregistered 9/18 FAIL"
    assert report["x1"]["membership_counts"] == {"old": 13, "new": 0, "neither": 5}
    assert report["x1"]["by_source"]["main_b3_greedy"]["membership_counts"] == {
        "old": 6, "new": 0, "neither": 4}
    assert report["x1"]["by_source"]["f2_b1_greedy"]["membership_counts"] == {
        "old": 5, "new": 0, "neither": 0}
    assert report["x1"]["by_source"]["f3_historical_sample_seed2"]["membership_counts"] == {
        "old": 2, "new": 0, "neither": 1}

    n19 = report["necessity_and_a3"]["historical_necessity_19"]
    assert n19["p0_membership_counts"] == {"old": 13, "new": 3, "neither": 3}
    assert n19["corrected_old_subset"] == {
        "n": 13,
        "clr_in_cot": 13,
        "paper_clr_subject_scrubbed": 13,
        "routes": {"Reflective-override": 1, "Bridge": 10, "Recall": 2, "Associative": 0},
    }
    assert n19["paper_clr_subject_scrubbed"] == 17
    assert n19["membership_by_paper_clr"] == n19["membership_by_clr"]
    n33 = report["necessity_and_a3"]["all_a3_candidates_33"]
    assert n33["p0_membership_counts"] == {"old": 13, "new": 15, "neither": 5}
    assert n33["membership_by_clr"]["old"]["clr_in_cot"] == 13
    assert n33["membership_by_clr"]["non_old_combined"] == {"n": 20, "clr_in_cot": 18}
    assert n33["membership_by_paper_clr"] == n33["membership_by_clr"]
    assert n33["subject_scrub_changed_n"] == 0

    wa = report["wa"]["a2rev"]
    assert (wa["wa_n"], wa["overlap_n"]) == (16, 15)
    assert wa["overlap_membership_counts"] == {"old": 6, "new": 5, "neither": 4}
    assert wa["wa_cases_missing_from_p0_a3_32b"] == ["cf_12725"]
    assert wa["p0_a3_32b_cases_missing_from_wa_a2rev"] == ["cf_19889"]


def test_missing_logitlens_is_blocked_not_inferred():
    result = p0x.build_logitlens_crosswalk(
        "results/probe/definitely_missing_logitlens.jsonl", {}, {}, 23)
    assert result["status"] == "BLOCKED_MISSING_PER_ITEM_ARTIFACT"
    assert result["expected_authoritative_n"] == 23
    assert "cannot be recovered or guessed" in result["reason"]


def test_present_logitlens_uses_case_ids_without_guessing():
    fd, path = tempfile.mkstemp(suffix=".jsonl", dir=ROOT)
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8") as f:
            for i in range(23):
                f.write(json.dumps({
                    "case_id": f"cf_{i}",
                    "edit_intact_at_cloze": True,
                    "gap_top": float(i),
                }) + "\n")
        membership = {
            "a3|32b|cf_0": {"membership": "old"},
            "a3|32b|cf_1": {"membership": "neither"},
        }
        routes = {"a3|32b|cf_0": {"primary": "Bridge"}}
        out = p0x.build_logitlens_crosswalk(path, membership, routes, 23)
        assert out["status"] == "PASS" and out["n"] == 23
        assert out["p0_overlap_n"] == 2
        assert out["p0_overlap_membership_counts"] == {
            "old": 1, "new": 0, "neither": 1}
        assert out["not_in_p0_candidate_pool"] == [f"cf_{i}" for i in range(2, 23)]
        assert out["rows"][0]["corrected_route"] == "Bridge"
    finally:
        os.remove(path)


if __name__ == "__main__":
    test_x1_source_mapping(); print("ok x1 source mapping")
    test_current_repo_crosswalk_numbers(); print("ok current repo crosswalk")
    test_missing_logitlens_is_blocked_not_inferred(); print("ok missing logit-lens boundary")
    test_present_logitlens_uses_case_ids_without_guessing(); print("ok present logit-lens crosswalk")
