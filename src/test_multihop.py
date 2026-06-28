"""multihop scorer/gate 单测(纯函数,无 GPU):hop 答案评分 + base-floor 门。
运行：python src/test_multihop.py （或 pytest）。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import multihop as mh


def test_score_hop_new_vs_old():
    s, han, hao = "Ellie Kemper", "Kolinda Grabar-Kitarovic", "Donald Trump"
    assert mh._score_one("The head of state is Kolinda Grabar-Kitarovic.", s, han, hao) == (1, 0)  # 答新
    assert mh._score_one("The head of state is Donald Trump.", s, han, hao) == (0, 1)               # 答旧(回退)
    assert mh._score_one("It is someone else entirely.", s, han, hao) == (0, 0)                      # 都不沾


def test_score_multiword_and_both_present():
    s, han, hao = "Ellie Kemper", "Kolinda Grabar-Kitarovic", "Donald Trump"
    # 多词答案词边界匹配;新旧都现 → hn=ho=1(下游判 ES=hits_new&not old=0,revert=1)
    hn, ho = mh._score_one("Croatia's head is Kolinda Grabar-Kitarovic, not Donald Trump.", s, han, hao)
    assert hn == 1 and ho == 1


def test_gate_drops_prior_dominated():
    pool = {"a": {"case_id": "a"}, "b": {"case_id": "b"}, "c": {"case_id": "c"}}
    base = [
        {"case_id": "a", "budget": "B3", "hits_new": 0, "hits_old": 1},   # 基座已答旧=先验主导→丢
        {"case_id": "b", "budget": "B3", "hits_new": 1, "hits_old": 0},   # 基座已答新→丢
        {"case_id": "c", "budget": "B3", "hits_new": 0, "hits_old": 0},   # 基座答不出→留(有信息)
    ]
    keep, n_eval, n_bad = mh.gate_keep(base, pool)
    assert n_eval == 3 and n_bad == 2
    assert [c["case_id"] for c in keep] == ["c"]


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print("ok", n)
    print("OK multihop: all tests passed")
