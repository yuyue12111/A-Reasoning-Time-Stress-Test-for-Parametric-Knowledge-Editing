"""emergence_regression 统计核单测(纯函数,无 GPU):OLS 还原已知 slope、bootstrap CI 套住、恰定不崩。
运行：python src/test_emergence_regression.py （或 pytest）。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emergence_regression as er


def test_ols_recovers_line():
    x = [0.0, 1.0, 2.0, 3.0, 4.0]
    y = [1.0, 3.0, 5.0, 7.0, 9.0]              # y = 2x + 1,完美直线
    o = er.ols(x, y)
    assert abs(o["slope"] - 2.0) < 1e-9 and abs(o["intercept"] - 1.0) < 1e-9
    assert abs(o["r2"] - 1.0) < 1e-9


def test_ols_exact_two_points_no_crash():
    o = er.ols([0.0, 1.0], [1.0, 4.0])          # 恰定(dof=0):slope 精确、不除零崩
    assert abs(o["slope"] - 3.0) < 1e-9 and o["dof"] == 0


def test_tci_and_excludes_zero():
    # slope 5, se 1, dof 4 → t=2.776 → CI [5-2.776, 5+2.776] 排零
    ci = er.t_ci(5.0, 1.0, 4)
    assert ci[0] > 0 and abs(ci[0] - (5 - 2.776)) < 1e-6
    ci2 = er.t_ci(0.5, 1.0, 4)                   # 含零
    assert ci2[0] < 0 < ci2[1]


def test_bootstrap_brackets_slope():
    x = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    y = [0.1, 2.0, 4.1, 5.9, 8.0, 10.1]         # slope≈2,带噪
    b = er.boot_slope_ci(x, y, B=2000, seed=1)
    assert b["ci"][0] < 2.0 < b["ci"][1], b
    assert b["p_slope_le_0"] < 0.05             # 强正斜率 → p 小


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print("ok", n)
    print("OK emergence_regression: all tests passed")
