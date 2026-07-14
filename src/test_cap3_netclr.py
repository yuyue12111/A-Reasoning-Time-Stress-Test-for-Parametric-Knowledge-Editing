"""Pure-CPU tests for BASE duplicate-world hardening and B15 provenance wiring."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b15_regress as b15
import cap3_netclr as cap3


CASES = [{"case_id": "cf_0", "s": "Subject", "o_old": "Paris", "o_new": "Rome"}]


def _write(path, rows, **json_kw):
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row, **json_kw) + "\n")


def test_base_equivalent_duplicates_are_deduplicated_and_audited():
    tmp = tempfile.mkdtemp()
    row_implicit = {"case_id": "cf_0", "budget": "B3", "probe": "base",
                    "answer": "Paris", "cot": "recall Paris"}
    row_explicit = {**row_implicit, "decode": "greedy", "seed": None,
                    "temperature": None}
    p0 = os.path.join(tmp, "r1qwen32b_BASE_cf200_r0of3.jsonl")
    p1 = os.path.join(tmp, "r1qwen32b_BASE_cf200_r1of3.jsonl")
    p2 = os.path.join(tmp, "r1qwen32b_BASE_cf200_r2of3.jsonl")
    _write(p0, [row_implicit])
    _write(p1, [row_implicit])
    _write(p2, [row_explicit], sort_keys=True, separators=(",", ":"))

    base_map, provenance = cap3.load_base_clr(
        [p0, p1, p2], CASES, {}, return_provenance=True)
    assert base_map == {(32.0, "Qwen", "cf_0"): {"base_clr": 1, "base_ans_old": 1}}
    audit = provenance["duplicate_world_audit"]
    assert audit["status"] == "PASS" and audit["n_unique_worlds"] == 1
    assert audit["n_duplicate_keys"] == 1
    assert audit["n_duplicate_rows_deduplicated"] == 2
    item = audit["duplicate_keys"][0]
    assert item["copies_total"] == 3
    assert item["byte_identical_duplicates"] == 1
    assert item["normalized_json_equal_duplicates"] == 1
    assert item["key"]["decode"] == "greedy" and item["key"]["seed"] is None
    assert [(source["path"], source["line"]) for source in item["sources"]]


def test_base_conflicting_duplicate_is_hard_failure_with_locations():
    tmp = tempfile.mkdtemp()
    row = {"case_id": "cf_0", "budget": "B3", "probe": "base",
           "decode": "greedy", "answer": "Paris", "cot": "Paris"}
    p0 = os.path.join(tmp, "r1qwen32b_BASE_cf200_r0of2.jsonl")
    p1 = os.path.join(tmp, "r1qwen32b_BASE_cf200_r1of2.jsonl")
    _write(p0, [row])
    _write(p1, [{**row, "answer": "Rome"}])
    try:
        cap3.load_base_clr([p0, p1], CASES, {})
    except ValueError as exc:
        msg = str(exc)
        assert "conflicting duplicate base world" in msg
        assert "differing_fields=['answer']" in msg
        assert f"{p0}:1" in msg and f"{p1}:1" in msg
    else:
        raise AssertionError("conflicting BASE world was silently last-write-wins")


def test_base_sampling_seeds_are_independent_and_require_selection():
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "r1qwen32b_BASE_cf200_r0of1.jsonl")
    rows = [
        {"case_id": "cf_0", "budget": "B3", "probe": "base", "decode": "sample",
         "seed": 0, "temperature": 0.6, "answer": "Paris", "cot": "Paris"},
        {"case_id": "cf_0", "budget": "B3", "probe": "base", "decode": "sample",
         "seed": 1, "temperature": 0.6, "answer": "Rome", "cot": ""},
    ]
    _write(path, rows)
    selected = cap3.load_base_clr([path], CASES, {}, decode="sample", seed=0)
    assert selected[(32.0, "Qwen", "cf_0")] == {"base_clr": 1, "base_ans_old": 1}
    try:
        cap3.load_base_clr([path], CASES, {}, decode="sample")
    except ValueError as exc:
        msg = str(exc)
        assert "multiple independent base trajectories" in msg
        assert "select seed explicitly" in msg
        assert f"{path}:1" in msg and f"{path}:2" in msg
    else:
        raise AssertionError("independent BASE sampling seeds were silently collapsed")


def test_default_return_and_b15_provenance_are_backward_compatible():
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "r1qwen32b_BASE_cf200_r0of1.jsonl")
    edited_path = os.path.join(tmp, "r1qwen32b_ROME_cf200_r0of1.jsonl")
    _write(path, [{"case_id": "cf_0", "budget": "B3", "probe": "base",
                   "answer": "Paris", "cot": "Paris"}])
    _write(edited_path, [{"case_id": "cf_0", "budget": "B3", "probe": "efficacy",
                          "answer": "Rome", "cot": ""}])
    base_map = cap3.load_base_clr([path], CASES, {})
    assert isinstance(base_map, dict) and (32.0, "Qwen", "cf_0") in base_map
    provenance = b15.input_provenance(
        {"duplicate_world_audit": {"n_duplicate_keys": 0}},
        {"duplicate_world_audit": {"n_duplicate_keys": 1}},
        [edited_path], [path])
    assert provenance["edited"]["duplicate_world_audit"]["n_duplicate_keys"] == 0
    assert provenance["base"]["duplicate_world_audit"]["n_duplicate_keys"] == 1
    assert provenance["edited_paths"] == [edited_path]
    assert provenance["base_paths"] == [path]
    assert provenance["edited_files"][0]["sha256"]
    assert provenance["base_files"][0]["sha256"]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("OK cap3_netclr: all tests passed")
