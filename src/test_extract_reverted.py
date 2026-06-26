"""extract_reverted.select_reverted 单测(纯函数,无 GPU/无 IO):验回退判据 + clr/implicit 标记。
运行：python src/test_extract_reverted.py （或 pytest）。
覆盖 4 类:explicit 回退(CLR)/implicit 回退(RR-without-CLR)/未回退(守住编辑)/B0 编辑失败(排除)。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_reverted

ALIASES = {}                                          # 空别名表足够:目标词均 >=4 字符、无别名命中

CASES = {
    "cf_t1": {"case_id": "cf_t1", "s": "Danielle Darrieux", "r": "P103",
              "prompt": "The mother tongue of Danielle Darrieux is", "o_old": "French", "o_new": "English"},
    "cf_t2": {"case_id": "cf_t2", "s": "X", "r": "P", "prompt": "Capital of X is", "o_old": "Paris", "o_new": "Berlin"},
    "cf_t3": {"case_id": "cf_t3", "s": "Y", "r": "P", "prompt": "Capital of Y is", "o_old": "Rome", "o_new": "Madrid"},
    "cf_t4": {"case_id": "cf_t4", "s": "Z", "r": "P", "prompt": "Lang of Z is", "o_old": "German", "o_new": "Dutch"},
}


def _r(b, cot, ans):
    return {"budget": b, "probe": "efficacy", "decode": "greedy", "cot": cot, "answer": ans}


BY_CASE = {
    # explicit 回退:B0 答 English(成功), B3 答 French 且 cot 含 French
    "cf_t1": {"B0": _r("B0", "", "The answer is English."),
              "B3": _r("B3", "Hmm, her mother tongue is French actually.", "Her mother tongue is French.")},
    # 未回退:B0 答 Berlin(成功), B3 仍答 Berlin -> 排除
    "cf_t2": {"B0": _r("B0", "", "Berlin."),
              "B3": _r("B3", "The capital is Berlin, the edited value.", "Berlin.")},
    # implicit 回退:B0 答 Madrid(成功), B3 答 Rome 但 cot 不含 'Rome' -> clr_in_cot False
    "cf_t3": {"B0": _r("B0", "", "Madrid."),
              "B3": _r("B3", "Let me think about Italy and its historic capital city.", "The capital is Rome.")},
    # B0 编辑失败:B0 答 German(非 Dutch) -> 整 case 排除
    "cf_t4": {"B0": _r("B0", "", "German."),
              "B3": _r("B3", "", "German.")},
}


def test_select_reverted_criteria():
    rows, st = extract_reverted.select_reverted(CASES, BY_CASE, ALIASES)
    ids = {r["case_id"] for r in rows}
    assert ids == {"cf_t1", "cf_t3"}, f"应只选 t1(explicit)+t3(implicit),得 {ids}"
    assert st["n_total"] == 4 and st["n_b0ok"] == 3 and st["n_rev"] == 2, st
    assert st["n_explicit"] == 1 and st["n_implicit"] == 1, st
    by = {r["case_id"]: r for r in rows}
    assert by["cf_t1"]["clr_in_cot"] is True, "t1 cot 含 French -> CLR True"
    assert by["cf_t3"]["clr_in_cot"] is False, "t3 cot 无 Rome -> implicit/RR-without-CLR"
    assert by["cf_t1"]["o_old"] == "French" and by["cf_t1"]["o_new"] == "English", "字段连表正确"


def test_skips_missing_budgets():
    only_b3 = {"cf_t1": {"B3": _r("B3", "x French x", "French")}}      # 缺 B0
    rows, st = extract_reverted.select_reverted(CASES, only_b3, ALIASES)
    assert rows == [] and st["n_total"] == 0, "缺 B0 档应跳过、不计入"


if __name__ == "__main__":
    test_select_reverted_criteria()
    test_skips_missing_budgets()
    print("OK extract_reverted: 2 tests passed")
