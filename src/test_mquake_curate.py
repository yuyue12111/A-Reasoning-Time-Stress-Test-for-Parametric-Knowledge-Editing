"""mquake_curate.curate 单测(纯函数,无 GPU):各筛选分支。
运行：python src/test_mquake_curate.py （或 pytest）。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mquake_curate as mc


def _row(cid, **kw):
    base = {"case_id": cid, "n_rewrites": "1", "s": "Ellie Kemper", "r": "P27",
            "prompt": "Ellie Kemper is a citizen of", "o_old": "United States", "o_new": "Croatia",
            "hops": "['Who is the head of state of the country where Ellie Kemper holds a citizenship?']",
            "hop_answer_new": "Kolinda Grabar-Kitarovic", "hop_answer_old": "Donald Trump"}
    base.update(kw); return base


def test_clean_passes():
    clean, st = mc.curate([_row("ok")])
    assert st["clean"] == 1 and len(clean) == 1
    assert clean[0]["hop_q"].startswith("Who is the head")        # hops[0] 提出
    assert clean[0]["hop_answer_old"] == "Donald Trump"


def test_drops():
    rows = [
        _row("multi", n_rewrites="2"),                            # 非单编辑
        _row("degen", hop_answer_new="Croatia"),                  # 2-hop 答案=o_new(退化)
        _row("indist", hop_answer_old="Kolinda Grabar-Kitarovic"),  # 新旧不可分
        _row("nosubj", hops="['Who leads the country of some other person?']"),  # subject 不在 hopq
    ]
    clean, st = mc.curate(rows)
    assert st["clean"] == 0
    assert st["drop_degenerate_hop_is_onew"] == 1
    assert st["drop_new_old_indistinct"] == 1
    assert st["drop_subj_not_in_hopq"] == 1


def test_parse_list_handles_str_and_list():
    assert mc._parse_list("['a', 'b']") == ["a", "b"]
    assert mc._parse_list(["x"]) == ["x"]


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print("ok", n)
    print("OK mquake_curate: all tests passed")
