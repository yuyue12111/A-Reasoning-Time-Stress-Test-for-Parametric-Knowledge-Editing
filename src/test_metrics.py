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


def _scenario_pl(path):
    """带 para/locality + 采样臂的场景，手算核对 PS/Loc 与 decode 过滤（o_old=Paris, o_new=Rome）。"""
    rows = [
        # cf_0 greedy: efficacy 成功; para0 成功(Rome)/para1 回退(Paris); locality 未泄漏(Paris 不含 Rome)
        {"case_id": "cf_0", "budget": "B0", "probe": "efficacy", "decode": "greedy", "answer": "Rome",          "cot": ""},
        {"case_id": "cf_0", "budget": "B0", "probe": "para0",    "decode": "greedy", "answer": "It is Rome",     "cot": ""},
        {"case_id": "cf_0", "budget": "B0", "probe": "para1",    "decode": "greedy", "answer": "Paris actually", "cot": ""},
        {"case_id": "cf_0", "budget": "B0", "probe": "locality", "decode": "greedy", "answer": "Paris",          "cot": ""},
        # cf_0 采样臂: 应被 decode=greedy 过滤（否则 n/n_para 变大）
        {"case_id": "cf_0", "budget": "B0", "probe": "efficacy", "decode": "sample", "seed": 0, "answer": "Paris", "cot": ""},
        {"case_id": "cf_0", "budget": "B0", "probe": "para0",    "decode": "sample", "seed": 0, "answer": "Paris", "cot": ""},
        # cf_1 greedy: efficacy 成功; locality **泄漏**(answer 含 o_new=Rome) → Loc 不保持
        {"case_id": "cf_1", "budget": "B0", "probe": "efficacy", "decode": "greedy", "answer": "Rome",        "cot": ""},
        {"case_id": "cf_1", "budget": "B0", "probe": "locality", "decode": "greedy", "answer": "Now Rome too", "cot": ""},
    ]
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def test_paraphrase_locality_and_decode_filter():
    fd, path = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
    _scenario_pl(path)
    cases = [{"case_id": "cf_0", "o_old": "Paris", "o_new": "Rome"},
             {"case_id": "cf_1", "o_old": "Paris", "o_new": "Rome"}]
    out = metrics.score(path, cases, {})                 # 默认 greedy
    out_s = metrics.score(path, cases, {}, decode="sample")
    os.remove(path)

    # greedy: ES 两条都成功(n=2); PS=para0 成功/para1 失败=0.5(n_para=2); Loc=cf_0 保持/cf_1 泄漏=0.5(n_loc=2)
    assert out["B0"]["n"] == 2 and abs(out["B0"]["ES"] - 1.0) < 1e-9, f"ES/n: {out['B0']}"
    assert out["B0"]["n_para"] == 2 and abs(out["B0"]["PS"] - 0.5) < 1e-9, f"PS: {out['B0']}"
    assert out["B0"]["n_loc"] == 2 and abs(out["B0"]["Loc"] - 0.5) < 1e-9, f"Loc: {out['B0']}"
    # decode 过滤：sample 行只在 decode='sample' 时计入（cf_0 一条 sample efficacy，答 Paris → ES=0）
    assert out_s["B0"]["n"] == 1 and out_s["B0"]["ES"] == 0.0, f"sample 臂: {out_s['B0']}"
    assert out_s["B0"]["n_para"] == 1, f"sample para: {out_s['B0']}"


def test_none_metrics_when_probe_absent():
    # 只有 efficacy、无 para/locality（如 MQuAKE）→ PS/Loc 应为 None，不报错
    fd, path = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
    with open(path, "w") as f:
        f.write(json.dumps({"case_id": "m_0", "budget": "B0", "probe": "efficacy",
                            "answer": "Croatia", "cot": ""}) + "\n")
    out = metrics.score(path, [{"case_id": "m_0", "o_old": "USA", "o_new": "Croatia"}], {})
    os.remove(path)
    assert out["B0"]["PS"] is None and out["B0"]["Loc"] is None, f"无探针应 None: {out['B0']}"
    assert out["B0"]["n_para"] == 0 and out["B0"]["n_loc"] == 0


def test_flip_analysis():
    al = {"Mars": ["the Red Planet"]}
    # 07 案例：先新后旧（『Mars. However…Jupiter』）→ first=new,last=old,flipped,flip_pos 指向 Jupiter
    fa = metrics.flip_analysis("Mars. However the largest is Jupiter", "Mars", "Jupiter", al)
    assert fa["first"] == "new" and fa["last"] == "old" and fa["flipped"], f"先新后旧: {fa}"
    assert fa["flip_pos"] == fa["old_pos"] > fa["new_pos"], f"flip_pos 应=后现的 Jupiter 位: {fa}"
    # 先旧后新（链内自我纠正）→ first=old,last=new
    fb = metrics.flip_analysis("Jupiter, wait no, it is Mars", "Mars", "Jupiter", al)
    assert fb["first"] == "old" and fb["last"] == "new" and fb["flipped"], f"先旧后新: {fb}"
    # 干净命中 o_new（含别名）/ 干净命中 o_old / 都无
    assert metrics.flip_analysis("It is the Red Planet", "Mars", "Jupiter", al) \
        == {"first": "new", "last": "new", "flipped": False, "flip_pos": None,
            "new_pos": 6, "old_pos": None}, "别名命中 o_new 应 first=last=new 不翻转"
    fc = metrics.flip_analysis("definitely Jupiter", "Mars", "Jupiter", al)
    assert fc["first"] == "old" and not fc["flipped"], f"仅 o_old: {fc}"
    fd = metrics.flip_analysis("I have no idea", "Mars", "Jupiter", al)
    assert fd["first"] is None and not fd["flipped"], f"都无: {fd}"


def test_score_esf_and_flip():
    # 答案『Mars. However…Jupiter』：严格 ES=0（含 o_old），但 ESf=1（首段=Mars），Flip=1
    fd, path = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
    with open(path, "w") as f:
        f.write(json.dumps({"case_id": "c0", "budget": "B3", "probe": "efficacy",
                            "answer": "Mars. However the largest is Jupiter", "cot": ""}) + "\n")
    out = metrics.score(path, [{"case_id": "c0", "o_old": "Jupiter", "o_new": "Mars"}], {})
    os.remove(path)
    assert out["B3"]["ES"] == 0.0, f"严格 ES 应 0（答案含 o_old）: {out['B3']}"
    assert out["B3"]["ESf"] == 1.0, f"ESf 应 1（首段=Mars）: {out['B3']}"
    assert out["B3"]["Flip"] == 1.0, f"Flip 应 1（两立场都现）: {out['B3']}"


def test_subject_substring_guard():
    """o_old 作主体子串时不污染判分（6.16 eyeball：主体复述 ≠ 旧知识回忆）。
    主体 'Miami International Film Festival' 含 o_old 'Miami'。"""
    fd, path = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
    rows = [
        # c0: 编辑生效——o_old(Miami)只在主体里出现，真断言是 o_new(Latvia)；cot 仅复述题目
        {"case_id": "c0", "budget": "B0", "probe": "efficacy",
         "answer": "The Miami International Film Festival is located in Latvia.",
         "cot": "where the Miami International Film Festival is located, I recall it"},
        # c1: 真回退——答案在主体外又现 o_old(located in Miami)；cot 真回忆旧知识
        {"case_id": "c1", "budget": "B0", "probe": "efficacy",
         "answer": "The Miami International Film Festival is located in Miami, Florida.",
         "cot": "it is actually located in Miami, not Latvia"},
    ]
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    subj = "Miami International Film Festival"
    cases = [{"case_id": "c0", "s": subj, "o_old": "Miami", "o_new": "Latvia"},
             {"case_id": "c1", "s": subj, "o_old": "Miami", "o_new": "Latvia"}]
    out = metrics.score(path, cases, {})
    os.remove(path)
    # c0: ES=1(主体里的 Miami 不算)/CLR=0(仅复述)；c1: ES=0(主体外 Miami=回退)/CLR=1(真回忆) → 聚合 0.5/0.5
    assert out["B0"]["n"] == 2, f"n: {out['B0']}"
    assert abs(out["B0"]["ES"] - 0.5) < 1e-9, f"ES 应 0.5（c0 生效/c1 回退）: {out['B0']}"
    assert abs(out["B0"]["CLR"] - 0.5) < 1e-9, f"CLR 应 0.5（c0 仅复述/c1 真回忆）: {out['B0']}"
    # 关键反证：不挖主体则 c0 会被误判（ES=0 假阴 + CLR=1 假阳）——确认 guard 生效
    cases_nos = [{"case_id": "c0", "o_old": "Miami", "o_new": "Latvia"}]  # 无 s → 不挖
    fd2, p2 = tempfile.mkstemp(suffix=".jsonl"); os.close(fd2)
    with open(p2, "w") as f:
        f.write(json.dumps(rows[0]) + "\n")
    bad = metrics.score(p2, cases_nos, {}); os.remove(p2)
    assert bad["B0"]["ES"] == 0.0 and bad["B0"]["CLR"] == 1.0, f"无 guard 应假阴/假阳: {bad['B0']}"


def test_score_bootstrap():
    # 复用 _scenario 的 cf_0/cf_1：B0 ES 点估=1.0；B1 ES 点估=0.5；CI 含点估、且确定性(同 seed 同值)
    fd, path = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
    _scenario(path)
    cases = [{"case_id": "cf_0", "o_old": "Paris", "o_new": "Rome"},
             {"case_id": "cf_1", "o_old": "French", "o_new": "English"}]
    aliases = {"Rome": ["Roma"]}
    bs = metrics.score_bootstrap(path, cases, aliases, n_boot=500, seed=1)
    bs2 = metrics.score_bootstrap(path, cases, aliases, n_boot=500, seed=1)
    os.remove(path)
    # 点估与 metrics.score 一致
    assert abs(bs["B0"]["ES"][0] - 1.0) < 1e-9, f"B0 ES 点估应 1.0: {bs['B0']['ES']}"
    assert abs(bs["B1"]["ES"][0] - 0.5) < 1e-9, f"B1 ES 点估应 0.5: {bs['B1']['ES']}"
    # CI 区间含点估、lo≤hi、∈[0,1]
    for b in bs:
        for m in ("ES", "RR", "CLR"):
            t = bs[b][m]
            if t is None:
                continue
            pt, lo, hi = t
            assert 0 <= lo <= pt <= hi <= 1, f"{b}.{m} CI 异常(应 0≤lo≤点估≤hi≤1): {t}"
    # 确定性：同 seed 同结果
    assert bs == bs2, "同 seed 的 bootstrap 应可复现"


TESTS = [test_hit_alias_case_and_none, test_score_exact,
         test_paraphrase_locality_and_decode_filter, test_none_metrics_when_probe_absent,
         test_flip_analysis, test_score_esf_and_flip, test_subject_substring_guard,
         test_score_bootstrap]


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
