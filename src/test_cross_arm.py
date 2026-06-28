"""E-SUP-BATTERY 统计核单测(纯函数,无 GPU):跨臂配对差 + placebo 供体构建。
运行：python src/test_cross_arm.py （或 pytest）。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cross_arm, placebo_donor


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
