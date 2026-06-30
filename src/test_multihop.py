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


def test_hop_hit_diacritic_and_shortguard():
    assert mh._hop_hit("head of state is Kolinda Grabar-Kitarović.", "Grabar-Kitarovic")   # 去变音符
    assert mh._hop_hit("Confucius worked in Lu.", "Lu")                                    # 短目标+上下文
    assert not mh._hop_hit("blah Lu blah random text", "Lu")                               # 短目标裸现→堵假阳
    assert not mh._hop_hit("the answer is Luxembourg", "Lu")                               # 非词边界


def test_recut_drops_degenerate_new_template():
    rows = [{"case_id": f"d{i}", "r": "P140", "hop_answer_new": "Lu"} for i in range(25)]   # 退化:全 Lu
    rows += [{"case_id": f"v{i}", "r": "P27", "hop_answer_new": f"Head{i}"} for i in range(25)]  # 多样
    keep, drop = mh.recut_keep(rows, max_frac=0.30, min_n=20)
    assert drop == ["P140"] and all(c["r"] == "P27" for c in keep) and len(keep) == 25


def test_score_block_b0prop_erosion():
    cases = {"c1": {"case_id": "c1", "s": "X", "hop_answer_new": "Justin Trudeau", "hop_answer_old": "Donald Trump"},
             "c2": {"case_id": "c2", "s": "Y", "hop_answer_new": "Leo Varadkar", "hop_answer_old": "Donald Trump"}}
    recs = [  # c1: B0 传到(答新)→ B3 丢(答旧)=erosion;c2: B0 没传到(答旧)→ 不进 b0_prop
        {"case_id": "c1", "budget": "B0", "probe": "hop", "answer": "It is Justin Trudeau."},
        {"case_id": "c1", "budget": "B3", "probe": "hop", "answer": "It is Donald Trump."},
        {"case_id": "c2", "budget": "B0", "probe": "hop", "answer": "It is Donald Trump."},
        {"case_id": "c2", "budget": "B3", "probe": "hop", "answer": "It is Donald Trump."}]
    blk = mh._score_block(cases, recs, "t")
    assert blk["n_b0_prop"] == 1, blk                       # 仅 c1 在 B0 传到
    pe = blk["propagation_erosion_B0toB3"]
    assert pe["rate"] == 1.0 and pe["decomp"]["flips_to_old"] == 1   # c1 B3 丢→翻旧


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
