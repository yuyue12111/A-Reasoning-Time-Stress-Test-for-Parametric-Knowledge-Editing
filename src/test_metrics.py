"""metrics ES/RR/CLR 判分单测（plan §2.5 定义，无依赖，纯 JSON）。

构造可手算的合成 jsonl，逐预算档核对 ES/CLR/RR/n；并验证别名命中、大小写不敏感、
None 目标、以及 edit_loop 的错误行/非 efficacy 探针被正确忽略。
运行：python src/test_metrics.py    （或 pytest src/test_metrics.py）
"""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics


def test_hit_alias_case_and_none():
    al = {"Rome": ["Roma", "Roman Empire"]}
    assert metrics.hit("I think it is roma now", "Rome", al)          # 别名 + 大小写
    assert metrics.hit("ROME!", "Rome", al)                          # 直接命中、大小写
    assert not metrics.hit("Paris", "Rome", al)                      # 不命中
    assert not metrics.hit("anything", None, al)                     # None 目标不报错、不命中
    assert not metrics.hit(None, "Rome", al)                         # None 文本不报错


def _scenario(path):
    rows = [
        # cf_0: B0 编成功(Rome)；B1 回退(Paris)；B2 别名命中(Roma=Rome)
        {"case_id": "cf_0", "budget": "B0", "probe": "efficacy", "answer": "Rome",          "cot": "x"},
        {"case_id": "cf_0", "budget": "B1", "probe": "efficacy", "answer": "Actually Paris", "cot": "wait, Paris"},
        {"case_id": "cf_0", "budget": "B2", "probe": "efficacy", "answer": "Roma",           "cot": "y"},
        # cf_1: B0/B1 都稳定输出 o_new(English)
        {"case_id": "cf_1", "budget": "B0", "probe": "efficacy", "answer": "English", "cot": "z"},
        {"case_id": "cf_1", "budget": "B1", "probe": "efficacy", "answer": "English", "cot": "z"},
        # 干扰行：非 efficacy 探针 + edit_loop 错误标记 —— 都应被忽略
        {"case_id": "cf_0", "budget": "B0", "probe": "locality", "answer": "Paris", "cot": ""},
        {"case_id": "cf_9", "error": "RuntimeError('boom')"},
    ]
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def test_score_exact():
    fd, path = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
    _scenario(path)
    cases = [{"case_id": "cf_0", "o_old": "Paris", "o_new": "Rome"},
             {"case_id": "cf_1", "o_old": "French", "o_new": "English"}]
    aliases = {"Rome": ["Roma"]}
    out = metrics.score(path, cases, aliases)
    os.remove(path)

    exp = {"B0": {"ES": 1.0, "CLR": 0.0, "RR": 0.0, "n": 2},
           "B1": {"ES": 0.5, "CLR": 0.5, "RR": 0.5, "n": 2},
           "B2": {"ES": 1.0, "CLR": 0.0, "RR": 0.0, "n": 1}}
    assert set(out) == set(exp), f"预算档不符: {set(out)}"
    for b, e in exp.items():
        for k, v in e.items():
            assert abs(out[b][k] - v) < 1e-9, f"{b}.{k} 期望 {v} 得 {out[b][k]}"


TESTS = [test_hit_alias_case_and_none, test_score_exact]


def _main():
    fails = 0
    for t in TESTS:
        try:
            t(); print(f"  [PASS] {t.__name__}")
        except AssertionError as e:
            fails += 1; print(f"  [FAIL] {t.__name__}: {e}")
    print("ALL PASS" if fails == 0 else f"FAILED ({fails})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(_main())
