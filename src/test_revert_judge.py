"""revert_judge 单测(纯函数,无 GPU/无判官调用):Cohen κ / 分层采样 / 验证聚合。
运行：python src/test_revert_judge.py （或 pytest）。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import revert_judge as rj


def test_cohen_kappa():
    assert rj.cohen_kappa([1, 1, 0, 0], [1, 1, 0, 0]) == 1.0           # 完美一致
    assert rj.cohen_kappa([1, 1, 0, 0], [0, 0, 1, 1]) < 0              # 完全反 → 负
    k = rj.cohen_kappa([1, 0, 1, 0, 1, 0], [1, 0, 1, 0, 0, 1])         # 部分
    assert -1 <= k <= 1


def test_stratified_balanced():
    rows = [{"case_id": f"p{i}", "rule_rr": 1, "o_old": "a", "o_new": "b", "answer": "x"} for i in range(50)]
    rows += [{"case_id": f"n{i}", "rule_rr": 0, "o_old": "a", "o_new": "b", "answer": "y"} for i in range(50)]
    s = rj.stratified_sample(rows, n_per=30)
    pos = sum(r["rule_rr"] for r in s)
    assert len(s) == 60 and pos == 30, "分层各 30 正/负"


def test_validate_perfect_agreement():
    # 规则与判官完全一致:2 回退(rule_rr=1,判官 truly_reverts=True)+ 2 未回退
    sample = {"a": {"case_id": "a", "rule_rr": 1}, "b": {"case_id": "b", "rule_rr": 1},
              "c": {"case_id": "c", "rule_rr": 0}, "d": {"case_id": "d", "rule_rr": 0}}
    def v(rev): return {"truly_reverts": rev, "committed": "old" if rev else "new", "confidence": 0.9}
    verdicts = {"a": [v(True)] * 3, "b": [v(True)] * 3, "c": [v(False)] * 3, "d": [v(False)] * 3}
    out = rj.validate(sample, verdicts)
    assert out["n"] == 4 and out["cohen_kappa_rule_vs_judge"] == 1.0
    assert out["confusion"] == {"rule+_judge+_TP": 2, "rule+_judge-_ruleFalsePos": 0,
                                "rule-_judge+_ruleFalseNeg": 0, "rule-_judge-_TN": 2}
    assert out["rule_RR_on_sample"] == out["judge_RR_on_sample"] == 0.5


def test_validate_rule_false_positive():
    # 规则说回退但判官多数说没(子串误命中=主体复述)→ FP 计数
    sample = {"a": {"case_id": "a", "rule_rr": 1}}
    def v(rev): return {"truly_reverts": rev, "committed": "old" if rev else "new", "confidence": 0.8}
    out = rj.validate(sample, {"a": [v(False), v(False), v(True)]})    # 多数 False
    assert out["confusion"]["rule+_judge-_ruleFalsePos"] == 1
    assert out["judge_RR_on_sample"] == 0.0 and out["rule_RR_on_sample"] == 1.0


def test_build_prompt_neutral():
    p = rj.build_prompt({"o_old": "French", "o_new": "English", "answer": "It is French."})
    assert "French" in p and "English" in p and "It is French." in p
    assert "edit is STILL INSTALLED" not in p and "routing around" not in p, "中性:不得含 taxonomy 带偏断言"


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print("ok", n)
    print("OK revert_judge: all tests passed")
