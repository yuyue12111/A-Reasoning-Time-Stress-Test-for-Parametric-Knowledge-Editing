"""E-SUP-BATTERY 统计核单测(纯函数,无 GPU):跨臂配对差 + 输入去重审计 + placebo 供体构建。
运行：python src/test_cross_arm.py （或 pytest）。
"""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cross_arm, placebo_donor


def _per_case_fixture(tmp):
    cases_path = os.path.join(tmp, "cases.jsonl")
    with open(cases_path, "w") as f:
        f.write(json.dumps({"case_id": "c0", "s": "Subject", "o_old": "Paris", "o_new": "Rome"}) + "\n")
    cfg = {"out_dir": tmp, "model_tag": "model", "dataset": {"tag": "tag", "path": cases_path}}
    return cfg


def _write(path, rows, **json_kw):
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row, **json_kw) + "\n")


def test_per_case_equivalent_duplicate_worlds_are_deduplicated_and_audited():
    tmp = tempfile.mkdtemp()
    cfg = _per_case_fixture(tmp)
    rows = [
        {"case_id": "c0", "budget": "B0", "probe": "efficacy", "decode": "greedy",
         "seed": None, "temperature": None, "answer": "Rome", "cot": ""},
        {"case_id": "c0", "budget": "B3", "probe": "efficacy", "decode": "greedy",
         "seed": None, "temperature": None, "answer": "Paris", "cot": "Paris"},
    ]
    p0 = os.path.join(tmp, "model_ROME_tag_r0.jsonl")
    p1 = os.path.join(tmp, "model_ROME_tag_r1.jsonl")
    p2 = os.path.join(tmp, "model_ROME_tag_r2.jsonl")
    _write(p0, rows)
    _write(p1, rows)  # byte-identical copies
    _write(p2, rows, sort_keys=True, separators=(",", ":"))  # parsed-row equivalent

    out, audit = cross_arm.per_case(cfg, "ROME", "B3", return_audit=True)
    assert out == {"c0": {"ES": 0, "CLR": 1, "RR": 1, "RRs": 1}}, out
    assert audit["status"] == "PASS" and audit["n_unique_worlds"] == 2
    assert audit["n_duplicate_keys"] == 2 and audit["n_duplicate_rows_deduplicated"] == 4
    for item in audit["duplicate_keys"]:
        assert item["copies_total"] == 3
        assert item["byte_identical_duplicates"] == 1
        assert item["normalized_json_equal_duplicates"] == 1
        assert [(source["path"], source["line"]) for source in item["sources"]]


def test_per_case_conflicting_duplicate_world_is_hard_failure_with_both_locations():
    tmp = tempfile.mkdtemp()
    cfg = _per_case_fixture(tmp)
    base = {"case_id": "c0", "budget": "B3", "probe": "efficacy", "decode": "greedy",
            "seed": None, "temperature": None, "answer": "Paris", "cot": "Paris"}
    p0 = os.path.join(tmp, "model_ROME_tag_r0.jsonl")
    p1 = os.path.join(tmp, "model_ROME_tag_r1.jsonl")
    _write(p0, [base])
    _write(p1, [{**base, "answer": "Rome"}])
    try:
        cross_arm.per_case(cfg, "ROME", "B3")
    except ValueError as exc:
        msg = str(exc)
        assert "conflicting duplicate world" in msg
        assert "differing_fields=['answer']" in msg
        assert f"{p0}:1" in msg and f"{p1}:1" in msg
    else:
        raise AssertionError("conflicting duplicate world was silently last-write-wins")


def test_sampling_seeds_are_distinct_trajectories_and_require_explicit_selection():
    tmp = tempfile.mkdtemp()
    cfg = _per_case_fixture(tmp)
    rows = []
    for seed, b3_answer in ((0, "Paris"), (1, "Rome")):
        rows.extend([
            {"case_id": "c0", "budget": "B0", "probe": "efficacy", "decode": "sample",
             "seed": seed, "temperature": 0.6, "answer": "Rome", "cot": ""},
            {"case_id": "c0", "budget": "B3", "probe": "efficacy", "decode": "sample",
             "seed": seed, "temperature": 0.6, "answer": b3_answer,
             "cot": ("Paris" if b3_answer == "Paris" else "")},
        ])
    path = os.path.join(tmp, "model_ROME_tag_r0.jsonl")
    _write(path, rows)

    seed0, audit0 = cross_arm.per_case(
        cfg, "ROME", "B3", decode="sample", seed=0, return_audit=True)
    seed1, audit1 = cross_arm.per_case(
        cfg, "ROME", "B3", decode="sample", seed=1, return_audit=True)
    assert seed0["c0"]["RR"] == 1 and seed1["c0"]["RR"] == 0
    assert audit0["n_unique_worlds"] == audit1["n_unique_worlds"] == 2
    assert audit0["n_duplicate_keys"] == audit1["n_duplicate_keys"] == 0
    try:
        cross_arm.per_case(cfg, "ROME", "B3", decode="sample")
    except ValueError as exc:
        msg = str(exc)
        assert "multiple independent trajectories" in msg and "select one with seed" in msg
        assert f"{path}:2" in msg and f"{path}:4" in msg
    else:
        raise AssertionError("multiple sampling seeds were silently collapsed")


def test_paired_diff_clean_separation():
    A = {f"c{i}": {"RR": 0, "ES": 1} for i in range(40)}     # T 臂:RR 全 0
    B = {f"c{i}": {"RR": 1, "ES": 0} for i in range(40)}     # N 臂:RR 全 1
    r = cross_arm.paired_diff(A, B, "RR")
    assert r["n"] == 40 and r["mean"] == -1.0
    assert r["ci"] == [-1.0, -1.0] and r["p"] <= 0.01        # 干净排零


def test_paired_diff_null_contains_zero():
    A = {f"c{i}": {"RR": i % 2} for i in range(40)}          # 交替
    B = {f"c{i}": {"RR": (i + 1) % 2} for i in range(40)}
    r = cross_arm.paired_diff(A, B, "RR")
    assert r["ci"][0] < 0 < r["ci"][1] or r["mean"] == 0, r  # 含 0 或均差 0


def test_paired_diff_intersection_only():
    A = {"a": {"RR": 1}, "b": {"RR": 1}, "x": {"RR": 1}}
    B = {"a": {"RR": 0}, "b": {"RR": 0}}
    r = cross_arm.paired_diff(A, B, "RR")
    assert r["n"] == 2, "只配对交集 case_id"


def test_placebo_donor_matched_and_disjoint():
    cases = [{"case_id": "cf_0", "o_old": "French", "o_new": "English"},
             {"case_id": "cf_1", "o_old": "Berlin", "o_new": "Madrid"},
             {"case_id": "cf_2", "o_old": "Russia", "o_new": "Brazil"},
             {"case_id": "cf_3", "o_old": "Mendel", "o_new": "Darwin"}]
    donors, st = placebo_donor.build(cases, seed=42)
    assert set(donors) == {"cf_0", "cf_1", "cf_2", "cf_3"} and st["n"] == 4
    by = {c["case_id"]: c for c in cases}
    for cid, d in donors.items():
        o_old, o_new = by[cid]["o_old"].lower(), by[cid]["o_new"].lower()
        assert d.lower() not in (o_old, o_new), f"{cid} 供体不得等于本 case 旧/新值"
        assert abs(len(d) - len(by[cid]["o_old"])) <= 2, "长度近匹配"


def test_placebo_deterministic():
    cases = [{"case_id": f"cf_{i}", "o_old": w, "o_new": "X" * len(w)}
             for i, w in enumerate(["French", "Berlin", "Russia", "Canada", "Brazil"])]
    d1, _ = placebo_donor.build(cases, seed=42)
    d2, _ = placebo_donor.build(cases, seed=42)
    assert d1 == d2, "同 seed 确定性(BLIND 锁定可复现)"


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print("ok", n)
    print("OK cross_arm + placebo_donor: all tests passed")
