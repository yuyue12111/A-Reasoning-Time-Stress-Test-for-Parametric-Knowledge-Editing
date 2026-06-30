"""percase_emergence 数值核单测（纯 numpy，**无 GPU / 无平台数据**）。

合成逐 case 长表，喂进与论文同一条统计路径（两级 family→case cluster bootstrap）：
  1. 已知**正** log-params 斜率 + family 截距偏移 + chain_len 噪声协变量
     → 断言拟合斜率的 cluster-boot CI **排零** 且 **套住真值**。
  2. 真**零**斜率（结局与 log-params 无关）
     → 断言 CI **含零**（守住审稿人点名的 anti-conservative：不能把 6 点 bootstrap 那种
        「无中生有的显著」复刻出来）。
  3. 退化/边界：单尺度族在两级 bootstrap 下不崩；二元 logit 完全分离回退 LPM 不崩。
  4. 长表构建 load_percase_rows 与 metrics 口径一致（合成 jsonl 端到端，含去主体 + b0ok 门）。

运行：python3 src/test_percase_emergence.py
"""
import json
import os
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import percase_emergence as pe


# ------------------------------------------------------------------------------
# 合成长表生成器
# ------------------------------------------------------------------------------
def _synth_rows(true_slope, fam_offsets, n_per_cell=120, chain_noise=8.0,
                binary=False, seed=0):
    """造逐 case 行：对每个 (family, params_b)，结局期望 = base + true_slope*log10(params)
       + family_offset；chain_len 是与结局**无关**的协变量噪声（测控制不偷斜率）。
    binary=False → es_drop ∈ {−1,0,1}（这里用连续→四舍五入到 {−1,0,1} 不必要，直接连续即可，
                   回归是 OLS）；binary=True → clr ∈ {0,1}（伯努利，期望=sigmoid(...)）。
    返回 percase_emergence 期望的行 dict 列表。"""
    rng = np.random.default_rng(seed)
    grid = {"Qwen": [1.5, 7.0, 14.0, 32.0], "Llama": [8.0, 70.0]}
    rows = []
    for fam, sizes in grid.items():
        off = fam_offsets[fam]
        for pb in sizes:
            lp = np.log10(pb)
            for k in range(n_per_cell):
                cl = float(rng.normal(200, chain_noise))    # chain_len：与结局无关
                if binary:
                    eta = off + true_slope * lp + rng.normal(0, 0.3)
                    p = 1.0 / (1.0 + np.exp(-eta))
                    val = int(rng.random() < p)
                    rows.append({"case_id": f"{fam}_{pb}_{k}", "family": fam, "params_b": pb,
                                 "log_params": float(lp), "chain_len": cl,
                                 "clr": val, "rr": None, "es_drop": 0, "b0ok": True})
                else:
                    val = off + true_slope * lp + rng.normal(0, 0.25)
                    rows.append({"case_id": f"{fam}_{pb}_{k}", "family": fam, "params_b": pb,
                                 "log_params": float(lp), "chain_len": cl,
                                 "es_drop": float(val), "rr": None, "clr": 0, "b0ok": True})
    return rows


# ------------------------------------------------------------------------------
# 1. 已知正斜率 → CI 排零且套住真值
# ------------------------------------------------------------------------------
def test_positive_slope_excludes_zero_and_brackets_truth():
    true = 0.12
    rows = _synth_rows(true, {"Qwen": 0.0, "Llama": 0.15}, n_per_cell=150, seed=1)
    res = pe.cluster_bootstrap_ci(rows, "es_drop", binary=False, control_chain=True,
                                  B=2000, seed=7)
    assert res is not None
    lo, hi = res["ci95"]
    assert res["excludes_zero"], f"正斜率应排零，得 {res}"
    assert lo > 0, f"CI 下界应>0：{res['ci95']}"
    assert lo <= true <= hi, f"CI 应套住真值 {true}：{res['ci95']}"
    assert abs(res["point"] - true) < 0.05, f"点估应接近真值：point={res['point']} true={true}"
    assert res["p_slope_le_0"] < 0.05, f"强正斜率 p(≤0) 应小：{res['p_slope_le_0']}"
    assert res["n_families"] == 2 and res["kind"] == "ols"


# ------------------------------------------------------------------------------
# 2. 真零斜率 → CI 含零（守住 anti-conservative）
# ------------------------------------------------------------------------------
def test_zero_slope_ci_contains_zero():
    rows = _synth_rows(0.0, {"Qwen": 0.3, "Llama": 0.6}, n_per_cell=150, seed=2)
    res = pe.cluster_bootstrap_ci(rows, "es_drop", binary=False, control_chain=True,
                                  B=2000, seed=11)
    lo, hi = res["ci95"]
    assert lo <= 0 <= hi, f"真零斜率 CI 必须含零（防 anti-conservative）：{res['ci95']}"
    assert not res["excludes_zero"], f"真零斜率不应误报排零：{res}"


def test_zero_slope_binary_clr_ci_contains_zero():
    # 二元结局（CLR）真零斜率：logit 路径同样不能无中生有出显著
    rows = _synth_rows(0.0, {"Qwen": -0.2, "Llama": 0.4}, n_per_cell=200, binary=True, seed=3)
    res = pe.cluster_bootstrap_ci(rows, "clr", binary=True, control_chain=True,
                                  B=1500, seed=13)
    lo, hi = res["ci95"]
    assert lo <= 0 <= hi, f"真零斜率(二元)CI 必须含零：{res['ci95']}"
    assert res["kind"] in ("logit", "lpm")


def test_positive_slope_binary_clr_excludes_zero():
    rows = _synth_rows(0.9, {"Qwen": -0.5, "Llama": 0.0}, n_per_cell=200, binary=True, seed=4)
    res = pe.cluster_bootstrap_ci(rows, "clr", binary=True, control_chain=True,
                                  B=1500, seed=17)
    lo, hi = res["ci95"]
    assert lo > 0, f"强正(二元)斜率 CI 下界应>0：{res['ci95']}"
    assert res["excludes_zero"]


# ------------------------------------------------------------------------------
# 3. cluster bootstrap 确实在 family 层加方差（对比 naive case-only bootstrap CI 更宽）
# ------------------------------------------------------------------------------
def _case_only_ci_same_design(rows, outcome, B=2000, seed=7, ci=0.95):
    """对照：在【同样的 family-fixed 设计】上只重采样 case（所有 family 恒在、不抽 cluster）。
    与 cluster_bootstrap_ci 唯一的区别就是缺了第 1 级 family 重采样 → 用来隔离出
    『两级 bootstrap 额外注入的 between-family 方差』。"""
    sub = [r for r in rows if r.get(outcome) is not None]
    rng = np.random.default_rng(seed)
    m = len(sub)
    slopes = []
    for _ in range(B):
        idx = rng.integers(0, m, m)
        rs = [sub[j] for j in idx]
        bt = pe._design(rs, outcome, control_chain=True)
        if bt is None:
            continue
        Xb, yb, _, _ = bt
        if np.unique(Xb[:, 1]).size < 2:
            continue
        s, _k = pe._fit_slope(Xb, yb, binary=False)
        slopes.append(s)
    slopes = np.sort(np.asarray(slopes))
    lo, hi = np.percentile(slopes, [(1 - ci) / 2 * 100, (1 + ci) / 2 * 100])
    return float(hi - lo)


def test_cluster_bootstrap_wider_than_case_only():
    """两级（family→case）CI 应比【同设计但只重采样 case】的 CI 宽——two-level bootstrap 多注入了
    一层 between-family 方差。这正是对『6 点重采样把 6 个 cell-mean 当独立』的修补：family 数有限
    （=2）这一事实被如实编码进 CI（family 重采样 → CI 不会假装比实际更窄/更显著）。"""
    rows = _synth_rows(0.12, {"Qwen": 0.0, "Llama": 0.9}, n_per_cell=150, seed=5)
    cluster = pe.cluster_bootstrap_ci(rows, "es_drop", False, True, B=3000, seed=7)
    cw = cluster["ci95"][1] - cluster["ci95"][0]
    nw = _case_only_ci_same_design(rows, "es_drop", B=3000, seed=7)
    assert cw > nw, f"cluster CI 宽度 {cw:.4f} 应 > case-only(同设计) {nw:.4f}（两级注入 between-family 方差）"


# ------------------------------------------------------------------------------
# 4. 退化/边界不崩
# ------------------------------------------------------------------------------
def test_single_scale_family_no_crash():
    # 一个族只有单尺度（log_params 无变化）：两级 bootstrap 抽到它时该次跳过，不崩
    rows = _synth_rows(0.1, {"Qwen": 0.0, "Llama": 0.0}, n_per_cell=40, seed=6)
    rows = [r for r in rows if not (r["family"] == "Llama" and r["params_b"] != 8.0)]
    res = pe.cluster_bootstrap_ci(rows, "es_drop", False, True, B=800, seed=9)
    assert res is not None and res["n_boot_effective"] > 0


def test_within_family_ci_qwen():
    rows = _synth_rows(0.2, {"Qwen": 0.0, "Llama": 0.3}, n_per_cell=120, binary=True, seed=8)
    wq = pe.within_family_ci(rows, "Qwen", "clr", binary=True, control_chain=True, B=1200, seed=19)
    assert wq is not None and "ci95" in wq and wq["n_rows"] > 0


# ------------------------------------------------------------------------------
# 5. load_percase_rows 端到端：合成 jsonl，验证镜像 metrics 口径（去主体 + b0ok 门）
# ------------------------------------------------------------------------------
def test_load_percase_rows_mirrors_metrics():
    # 造两个尺度分片（文件名带 model_tag），各 2 个 case，手算 es_drop/clr/rr/b0ok
    tmp = tempfile.mkdtemp()
    cases = [
        {"case_id": "cf_0", "s": "Danielle Darrieux", "o_old": "French", "o_new": "English"},
        {"case_id": "cf_1", "s": "Miami International Film Festival", "o_old": "Miami", "o_new": "Latvia"},
    ]
    cases_path = os.path.join(tmp, "cases.jsonl")
    with open(cases_path, "w") as f:
        for c in cases:
            f.write(json.dumps(c) + "\n")
    aliases_path = os.path.join(tmp, "aliases.json")
    json.dump({}, open(aliases_path, "w"))

    # 7B 分片：cf_0 B0 命中编辑(English)/B3 回退(French) → es_drop=1, b0ok=True, rr@B3=1, clr@B3=1
    #          cf_1 B0 命中(Latvia)/B3 守住(Latvia)，主体含 o_old 'Miami' 但去主体后不算 → es_drop=0
    shard7b = os.path.join(tmp, "r1qwen7b_ROME_cf_r0.jsonl")
    rows7 = [
        {"_meta": True, "editor": "ROME"},
        {"case_id": "cf_0", "budget": "B0", "probe": "efficacy", "decode": "greedy",
         "answer": "English", "cot": "it speaks English"},
        {"case_id": "cf_0", "budget": "B3", "probe": "efficacy", "decode": "greedy",
         "answer": "Actually French", "cot": "wait, it is French"},
        {"case_id": "cf_1", "budget": "B0", "probe": "efficacy", "decode": "greedy",
         "answer": "The Miami International Film Festival is in Latvia.", "cot": "Latvia"},
        {"case_id": "cf_1", "budget": "B3", "probe": "efficacy", "decode": "greedy",
         "answer": "The Miami International Film Festival is in Latvia.", "cot": "still Latvia"},
        # 干扰：非 efficacy / 采样臂 / 错误行 —— 都应被忽略
        {"case_id": "cf_0", "budget": "B0", "probe": "locality", "decode": "greedy", "answer": "French", "cot": ""},
        {"case_id": "cf_0", "budget": "B0", "probe": "efficacy", "decode": "sample", "seed": 0, "answer": "French", "cot": ""},
        {"case_id": "cf_9", "error": "boom"},
    ]
    with open(shard7b, "w") as f:
        for r in rows7:
            f.write(json.dumps(r) + "\n")

    # 32B 分片：cf_0 B0/B3 都守住 English → es_drop=0
    shard32b = os.path.join(tmp, "r1qwen32b_ROME_cf_r0.jsonl")
    rows32 = [
        {"_meta": True},
        {"case_id": "cf_0", "budget": "B0", "probe": "efficacy", "decode": "greedy", "answer": "English", "cot": "x"},
        {"case_id": "cf_0", "budget": "B3", "probe": "efficacy", "decode": "greedy", "answer": "English", "cot": "x"},
    ]
    with open(shard32b, "w") as f:
        for r in rows32:
            f.write(json.dumps(r) + "\n")

    cases_loaded = [json.loads(l) for l in open(cases_path)]
    aliases = json.load(open(aliases_path))
    rows, tags = pe.load_percase_rows([shard7b, shard32b], cases_loaded, aliases)

    idx = {(r["family"], r["params_b"], r["case_id"]): r for r in rows}
    # 7B cf_0：es_drop=1, b0ok=True, rr=1(B3 含 French), clr=1
    r = idx[("Qwen", 7.0, "cf_0")]
    assert r["es_b0"] == 1 and r["es_late"] == 0 and r["es_drop"] == 1, r
    assert r["b0ok"] is True and r["rr"] == 1 and r["clr"] == 1, r
    # 7B cf_1：去主体后 Miami 不算 → es_drop=0；b0ok=True；rr=0
    r1 = idx[("Qwen", 7.0, "cf_1")]
    assert r1["es_b0"] == 1 and r1["es_late"] == 1 and r1["es_drop"] == 0, r1
    assert r1["rr"] == 0, r1
    # 32B cf_0：es_drop=0
    r3 = idx[("Qwen", 32.0, "cf_0")]
    assert r3["es_drop"] == 0, r3
    # 采样臂被过滤：7B cf_0 只有一条 greedy B0（n 不因 sample 行翻倍）—— 体现在 es_b0 仍为 1（不是混入 French）
    assert r["es_b0"] == 1
    # chain_len 是正数（B3 cot 空白分词）
    assert r["chain_len"] > 0
    # tag 推断
    assert any("7.0B_Qwen" in k or "7B_Qwen" in k.replace(".0", "") for k in tags) or ("7.0B_Qwen" in tags)


def test_infer_tag_meta():
    assert pe.infer_tag_meta("r1qwen7b_ROME_cf_r0.jsonl") == (7.0, "Qwen")
    assert pe.infer_tag_meta("r1qwen1.5b_ROME_cf_r3.jsonl") == (1.5, "Qwen")
    assert pe.infer_tag_meta("r1llama70b_MEMIT_cf_r1.jsonl") == (70.0, "Llama")
    # 鲁棒解析：<n>b + 族关键词
    assert pe.infer_tag_meta("R1-Distill-Qwen-14B_x.jsonl") == (14.0, "Qwen")
    assert pe.infer_tag_meta("llama_8b_run.jsonl") == (8.0, "Llama")
    # override 优先
    assert pe.infer_tag_meta("weirdname.jsonl", {"weirdname": [99, "Qwen"]}) == (99.0, "Qwen")
    # 认不出 → None
    assert pe.infer_tag_meta("garbage.jsonl") is None
    # 坑①：下划线当小数点 "r1qwen1_5b" 必须读成 1.5（不是 5.0）
    assert pe.infer_tag_meta("r1qwen1_5b_ROME_cf200_r0of8.jsonl") == (1.5, "Qwen")
    # 坑②：非编辑 per-case 文件（含 model_tag 也要拒）—— GENBENCH/multihop/logitlens/sweep
    assert pe.infer_tag_meta("r1qwen32b_GENBENCH_r0.jsonl") is None
    assert pe.infer_tag_meta("r1llama8b_ROME_mh2hop_r0of8.jsonl") is None
    assert pe.infer_tag_meta("r1qwen32b_logitlens_r0.jsonl") is None
    # override 用下划线键也能匹配下划线文件名（归一后比对）
    assert pe.infer_tag_meta("r1qwen1_5b_x.jsonl", {"r1qwen1_5b": [1.5, "Qwen"]}) == (1.5, "Qwen")


TESTS = [
    test_positive_slope_excludes_zero_and_brackets_truth,
    test_zero_slope_ci_contains_zero,
    test_zero_slope_binary_clr_ci_contains_zero,
    test_positive_slope_binary_clr_excludes_zero,
    test_cluster_bootstrap_wider_than_case_only,
    test_single_scale_family_no_crash,
    test_within_family_ci_qwen,
    test_load_percase_rows_mirrors_metrics,
    test_infer_tag_meta,
]


def _main():
    fails = 0
    for t in TESTS:
        try:
            t()
            print(f"  [PASS] {t.__name__}")
        except AssertionError as e:
            fails += 1
            print(f"  [FAIL] {t.__name__}: {e}")
        except Exception as e:
            fails += 1
            print(f"  [ERR ] {t.__name__}: {e!r}")
    print("ALL PASS" if fails == 0 else f"FAILED ({fails})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(_main())
