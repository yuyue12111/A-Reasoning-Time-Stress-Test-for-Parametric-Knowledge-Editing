"""Cap3 · net-CLR 涌现 slope + base-recall 分层控制 —— 把 CLR 涌现从 base 底噪里摘干净。

================================================================================
为什么必做(对抗验证 wz4rou8q3 之后从可选升必做)
================================================================================
`emergence.percase` 的 CLR slope(0.372 [0.149,0.800] excl0)是唯一显著的 per-case 涌现腿
(RR/es_drop 的 per-case slope 都含零、n.s.)。但它跑在 **raw edited CLR level** 上,而未编辑
base 的链含旧(base CLR)也随 scale 升(1.5B 0.582 / 8B 0.825 / 14B 0.860 / 32B 0.829)、
与之高度共线(base CLR ~ log-params r≈0.89)。所以"raw CLR 随能力涨"不能干净归因于
"编辑侵蚀随能力更严重"——大模型本就爱在链里提旧事实。

Cap3 逐 case 配对减掉 base 底噪:
    net_clr(case) = edited_CLR(case) − base_CLR(case)   ∈ {−1, 0, 1}   (同 case、同口径 metrics.hit)
再用 percase 的两级(family→case)cluster-robust 回归重估 6 尺度 slope:
  · net_clr slope 仍排零且正 → CLR 涌现在扣除 base 底噪后【存活】= 编辑特异的能力涌现(封死质疑);
  · net_clr slope 塌向零/含零 → raw CLR slope 大半是 base 先验共线 → CLR 涌现叙事须撤
    (范围:只 gate CLR 涌现叙事,**不** gate 头牌——F1/M1/32B cell-level ES 降幅独立成立)。

另两个稳健对照:
  · clr_on_baseCLR0:仅在 base 未泄漏(base_clr==0)的 case 上重估 **edited** CLR slope
    (M1 式分层控制:base 本不提 o_old 的 case 里,编辑后 CLR 是否仍随能力涨)。
  · clr_raw_matched:同 base-matched 子集上的 raw edited CLR slope(与 net_clr 同分母,供直接比对)。

口径:net_clr 逐 case 配对(edited case i 减 base case i),与 percase 的 clr 一样【不】做 b0ok 门
(percase.clr 也是全 case),故 net_clr slope 与 percase.clr slope 直接可比。分层/回归全复用
`percase_emergence.cluster_bootstrap_ci`(两级 bootstrap + family fixed-effect),不新造统计核。

================================================================================
用(平台;复用 emergence 的 6 尺度 edited 分片 + base_probe 写出的 *_BASE_* 分片,不用重跑)
================================================================================
  python src/cap3_netclr.py \
    --glob 'results/probe/r1qwen*_ROME_cf*_r*of8.jsonl' --glob 'results/probe/r1llama*_ROME_cf*.jsonl' \
    --base-glob 'results/probe/r1qwen*_BASE_*_r*.jsonl' --base-glob 'results/probe/r1llama*_BASE_*.jsonl' \
    --out results/cap3_netclr.json
本地自检(无平台数据):python src/cap3_netclr.py --selftest
"""
import argparse
import glob as globlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import percase_emergence as pe  # noqa: E402  复用 row loader + 两级 cluster-robust 回归

metrics = pe.metrics


# ------------------------------------------------------------------------------
# base per-case CLR 加载(base_probe 写的 *_BASE_* 分片,probe="base")
# ------------------------------------------------------------------------------
def load_base_clr(base_paths, cases, aliases, tag_override=None, late="B3"):
    """读 base_probe 的 *_BASE_* 分片 → {(params_b, family, case_id): {base_clr, base_ans_old}}。

    base 记录 probe='base'(src/base_probe.py),逐 case 有 cot/answer;取 late(默认 B3)预算的
    链 o_old(=base CLR 底噪)与答 o_old(=base recall,做协变量)。完全复用 metrics.hit/_without_subject
    (与 edited 侧、与 base_probe 聚合口径一致)。scale/family 由 *_BASE_* 文件名的 model_tag 决定。"""
    cmap = {c["case_id"]: c for c in cases}
    m = {}
    skipped = []
    for path in base_paths:
        meta = pe.infer_tag_meta(pe._tag_from_path(path), tag_override)
        if meta is None:
            skipped.append(os.path.basename(path))
            continue
        pb, fam = meta
        with open(path) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("probe") != "base":          # 跳过 _meta / 错误行
                    continue
                if r.get("budget") != late:           # 只取 late(B3)的链
                    continue
                cid = r.get("case_id")
                if cid not in cmap:
                    continue
                c = cmap[cid]
                subj = c.get("s") or ""
                clean = lambda t: metrics._without_subject(t, subj)
                base_clr = 1 if metrics.hit(clean(r.get("cot", "")), c["o_old"], aliases) else 0
                base_ans_old = 1 if metrics.hit(clean(r.get("answer", "")), c["o_old"], aliases) else 0
                m[(float(pb), fam, cid)] = {"base_clr": base_clr, "base_ans_old": base_ans_old}
    if skipped:
        print(f"  [skip base] {len(skipped)} 个推不出 scale/family 的 base 分片已忽略："
              f"{', '.join(skipped[:6])}{' …' if len(skipped) > 6 else ''}", file=sys.stderr)
    return m


def augment_with_net_clr(rows, base_map):
    """给 edited rows 加 base_clr / net_clr(=edited clr − base_clr ∈{−1,0,1}) / base_ans_old。
    无 base 匹配的 row → 三者 None(不入 net_clr 回归)。返回匹配到 base 的 row 数。"""
    matched = 0
    for r in rows:
        key = (float(r["params_b"]), r["family"], r["case_id"])
        b = base_map.get(key)
        if b is None:
            r["base_clr"] = None
            r["net_clr"] = None
            r["base_ans_old"] = None
            continue
        matched += 1
        r["base_clr"] = b["base_clr"]
        r["base_ans_old"] = b["base_ans_old"]
        r["net_clr"] = r["clr"] - b["base_clr"]       # ∈ {−1, 0, 1}
    return matched


# ------------------------------------------------------------------------------
# 分析(全复用 pe.cluster_bootstrap_ci：两级 family→case bootstrap + family fixed-effect)
# ------------------------------------------------------------------------------
def analyze_cap3(rows, B=10000, seed=42, control_chain=True):
    out = {}
    sub = [r for r in rows if r.get("net_clr") is not None]       # base-matched
    sub0 = [r for r in rows if r.get("base_clr") == 0]            # base 未泄漏子集

    # ① 主结局:net_clr slope(连续 ∈{−1,0,1};减 base 底噪后的涌现)
    res = pe.cluster_bootstrap_ci(sub, "net_clr", binary=False, control_chain=control_chain, B=B, seed=seed)
    if res is None:
        out["net_clr"] = {"_error": "no net_clr rows(base 未匹配?检查 --base-glob 与 model_tag)"}
    else:
        res["_desc"] = ("net_clr = edited_CLR − base_CLR ∈{−1,0,1}(逐 case 配对减 base 底噪);"
                        "slope 仍排零且正 → CLR 涌现扣 base 后存活;含零 → raw CLR 涌现大半是 base 共线")
        res["_n"] = len(sub)
        res["statsmodels"] = pe.statsmodels_corroboration(sub, "net_clr", False, control_chain)
        out["net_clr"] = res

    # ② 分层控制:仅 base_clr==0 的 case 上重估 edited CLR slope
    res0 = pe.cluster_bootstrap_ci(sub0, "clr", binary=True, control_chain=control_chain, B=B, seed=seed + 1)
    if res0 is None:
        out["clr_on_baseCLR0"] = {"_error": "no base_clr==0 rows"}
    else:
        res0["_desc"] = "edited CLR slope,仅在 base 未泄漏(base_clr==0)的 case;仍排零=编辑 CLR 涌现非 base 先验"
        res0["_n"] = len(sub0)
        out["clr_on_baseCLR0"] = res0

    # ③ 对照:同 base-matched 子集上的 raw edited CLR slope(与 net_clr 同分母,供比对)
    resr = pe.cluster_bootstrap_ci(sub, "clr", binary=True, control_chain=control_chain, B=B, seed=seed + 2)
    if resr is not None:
        resr["_desc"] = "raw edited CLR slope(仅 base-matched case,与 net_clr 同分母,供直接比对基线)"
        resr["_n"] = len(sub)
        out["clr_raw_matched"] = resr

    # ④ 逐尺度 base 底噪 vs edited CLR(人读校验)
    cells = {}
    for r in sub:
        k = (r["family"], r["params_b"])
        c = cells.setdefault(k, {"n": 0, "clr": 0, "base_clr": 0, "net": 0})
        c["n"] += 1
        c["clr"] += r["clr"]
        c["base_clr"] += r["base_clr"]
        c["net"] += r["net_clr"]
    out["_per_scale"] = {
        f"{f}-{pb}B": {"n": c["n"], "edited_clr": round(c["clr"] / c["n"], 3),
                       "base_clr": round(c["base_clr"] / c["n"], 3), "net_clr": round(c["net"] / c["n"], 3)}
        for (f, pb), c in sorted(cells.items(), key=lambda kv: (kv[0][0], kv[0][1]))
    }
    return out


def _verdict(out):
    nc = out.get("net_clr", {})
    if "_error" in nc:
        return "⚠ net_clr 无数据(base 未匹配)——检查 --base-glob 与 edited --glob 的 model_tag 是否同尺度。"
    excl = nc.get("excludes_zero")
    pt, ci = nc.get("point"), nc.get("ci95")
    c0 = out.get("clr_on_baseCLR0", {})
    if excl and pt and pt > 0:
        return (f"★Cap3 CONFIRM:net_clr slope={pt} {ci} 排零 → CLR 涌现扣除 base 底噪后【存活】,"
                f"编辑特异的能力涌现成立(base_clr==0 子集 slope={c0.get('point')} {c0.get('ci95')})。CLR 涌现叙事可留。")
    return (f"⚠Cap3 涌现塌陷:net_clr slope={pt} {ci} 含零 → raw CLR 涌现大半由 base 底噪共线解释,"
            f"CLR 涌现叙事须撤/降为纯描述(不 gate 头牌 F1/M1/32B ES 降幅)。base_clr==0 子集 slope={c0.get('point')} {c0.get('ci95')}。")


# ------------------------------------------------------------------------------
# selftest(无 GPU / 无平台数据):合成 edited rows + base_map,验证两情景 slope 方向
# ------------------------------------------------------------------------------
def _synth(edited_clr_slope, base_clr_slope, n_per_cell=120, seed=0):
    """造 6 cell 的 edited rows + 匹配 base_map:
       edited clr、base_clr 各按 sigmoid(off + slope*log10(params)) 伯努利抽;
       net_clr = edited_clr − base_clr。用来验证工具能否恢复 net slope 的正确方向。"""
    rng = np.random.default_rng(seed)
    grid = {"Qwen": [1.5, 7.0, 14.0, 32.0], "Llama": [8.0, 70.0]}
    rows, base_map = [], {}
    for fam, sizes in grid.items():
        off = 0.0 if fam == "Qwen" else 0.2
        for pb in sizes:
            lp = float(np.log10(pb))
            for k in range(n_per_cell):
                cid = f"{fam}_{pb}_{k}"
                pe_clr = 1.0 / (1.0 + np.exp(-(off - 0.5 + edited_clr_slope * lp + rng.normal(0, 0.3))))
                pb_clr = 1.0 / (1.0 + np.exp(-(off - 0.5 + base_clr_slope * lp + rng.normal(0, 0.3))))
                ec = int(rng.random() < pe_clr)
                bc = int(rng.random() < pb_clr)
                rows.append({"case_id": cid, "family": fam, "params_b": pb, "log_params": lp,
                             "chain_len": float(rng.normal(200, 8)), "clr": ec,
                             "es_drop": 0, "rr": None, "b0ok": True})
                base_map[(float(pb), fam, cid)] = {"base_clr": bc, "base_ans_old": bc}
    return rows, base_map


def _selftest():
    fails = 0
    # 情景 A:edited clr 与 base clr 同强正 slope → net_clr slope ≈ 0(涌现被 base 底噪吃掉)
    rows, bm = _synth(edited_clr_slope=0.9, base_clr_slope=0.9, seed=1)
    matched = augment_with_net_clr(rows, bm)
    assert matched == len(rows), f"应全匹配,得 {matched}/{len(rows)}"
    a = analyze_cap3(rows, B=1500, seed=7)
    lo, hi = a["net_clr"]["ci95"]
    if not (lo <= 0 <= hi):
        fails += 1; print(f"  [FAIL] 情景A net_clr 应含零(共线抵消): {a['net_clr']['ci95']}")
    else:
        print(f"  [PASS] 情景A(edited≈base slope): net_clr={a['net_clr']['point']} {a['net_clr']['ci95']} 含零 ✓")

    # 情景 B:edited clr 正 slope、base clr 平 → net_clr slope 正、排零(涌现存活)
    rows, bm = _synth(edited_clr_slope=1.0, base_clr_slope=0.0, seed=2)
    augment_with_net_clr(rows, bm)
    b = analyze_cap3(rows, B=1500, seed=9)
    if not (b["net_clr"]["excludes_zero"] and b["net_clr"]["point"] > 0):
        fails += 1; print(f"  [FAIL] 情景B net_clr 应正且排零: {b['net_clr']}")
    else:
        print(f"  [PASS] 情景B(base 平): net_clr={b['net_clr']['point']} {b['net_clr']['ci95']} 排零 ✓")

    # base_clr==0 分层非空 + net_clr ∈ {−1,0,1}
    assert b["clr_on_baseCLR0"].get("_n", 0) > 0, "base_clr==0 子集应非空"
    vals = {r["net_clr"] for r in rows if r["net_clr"] is not None}
    assert vals <= {-1, 0, 1}, f"net_clr 应 ∈{{−1,0,1}},得 {vals}"
    print(f"  [PASS] net_clr∈{{−1,0,1}} + base_clr==0 子集 n={b['clr_on_baseCLR0']['_n']} ✓")

    # load_base_clr round-trip(临时 base jsonl)
    import tempfile
    tmp = tempfile.mkdtemp()
    cases = [{"case_id": "cf_0", "s": "Danielle Darrieux", "o_old": "French", "o_new": "English"}]
    bp = os.path.join(tmp, "r1qwen32b_BASE_cf200_r0.jsonl")
    with open(bp, "w") as f:
        f.write(json.dumps({"_meta": True}) + "\n")
        f.write(json.dumps({"case_id": "cf_0", "budget": "B3", "probe": "base",
                            "answer": "It is French.", "cot": "recalling French roots"}) + "\n")
        f.write(json.dumps({"case_id": "cf_0", "budget": "B0", "probe": "base",
                            "answer": "English", "cot": ""}) + "\n")  # 非 B3,应忽略
    m = load_base_clr([bp], cases, {}, late="B3")
    if m.get((32.0, "Qwen", "cf_0")) == {"base_clr": 1, "base_ans_old": 1}:
        print("  [PASS] load_base_clr round-trip(B3 链/答含 French → base_clr=1,base_ans_old=1)✓")
    else:
        fails += 1; print(f"  [FAIL] load_base_clr: {m}")

    print("ALL PASS" if fails == 0 else f"FAILED ({fails})")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--glob", action="append", help="edited 逐 case jsonl 分片 glob(可多次;同 percase_emergence)")
    ap.add_argument("--base-glob", action="append", help="base_probe 的 *_BASE_* 分片 glob(可多次)")
    ap.add_argument("--cases", default="data/counterfact.jsonl")
    ap.add_argument("--aliases", default="data/aliases.json")
    ap.add_argument("--out", default="results/cap3_netclr.json")
    ap.add_argument("--decode", default="greedy")
    ap.add_argument("--base", default="B0")
    ap.add_argument("--late", default="B3")
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-chain-control", action="store_true")
    ap.add_argument("--map", default=None, help="JSON {文件名子串:[params_b,family]} 覆盖 model_tag 推断(edited+base 共用)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(_selftest())
    if not args.glob or not args.base_glob:
        raise SystemExit("需同时给 --glob(edited)与 --base-glob(base_probe *_BASE_*);自检用 --selftest")

    ed_paths = sorted({p for g in args.glob for p in globlib.glob(g)})
    base_paths = sorted({p for g in args.base_glob for p in globlib.glob(g)})
    if not ed_paths:
        raise SystemExit(f"edited glob 没匹配到分片：{args.glob}")
    if not base_paths:
        raise SystemExit(f"base glob 没匹配到分片：{args.base_glob}")
    cases = [json.loads(l) for l in open(args.cases)]
    aliases = json.load(open(args.aliases))
    tag_override = json.load(open(args.map)) if args.map else None

    rows, tags = pe.load_percase_rows(ed_paths, cases, aliases, decode=args.decode,
                                      base=args.base, late=args.late, tag_override=tag_override)
    if not rows:
        raise SystemExit("edited 侧无可配对逐 case 行(见 percase_emergence 的提示;--glob 指向 6 尺度 ROME×CF 分片)。")
    base_map = load_base_clr(base_paths, cases, aliases, tag_override=tag_override, late=args.late)
    matched = augment_with_net_clr(rows, base_map)
    print(f"edited rows={len(rows)}  base per-case={len(base_map)}  net_clr matched={matched} "
          f"({matched / len(rows) * 100:.0f}%)  尺度={sorted(set((r['params_b'], r['family']) for r in rows))}")
    if matched == 0:
        raise SystemExit("net_clr 零匹配:edited 与 base 分片的 (params_b, family, case_id) 对不上——"
                         "核对 base_probe tag/尺度与 edited 是否同源(同 200 case)。")

    out = analyze_cap3(rows, B=args.boot, seed=args.seed, control_chain=not args.no_chain_control)
    out["_meta"] = {"edited_shards": [os.path.basename(p) for p in ed_paths],
                    "base_shards": [os.path.basename(p) for p in base_paths],
                    "n_edited_rows": len(rows), "n_net_clr_matched": matched, "tags": tags}
    out["verdict"] = _verdict(out)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(out, open(args.out, "w"), ensure_ascii=False, indent=2)
    print("\n逐尺度(base-matched):")
    for k, v in out["_per_scale"].items():
        print(f"  {k:>12}: n={v['n']:>3}  edited_CLR={v['edited_clr']:.3f}  base_CLR={v['base_clr']:.3f}  net_CLR={v['net_clr']:+.3f}")
    print("\nnet_clr slope:", out["net_clr"].get("point"), out["net_clr"].get("ci95"),
          "excl0=", out["net_clr"].get("excludes_zero"))
    print("clr@base_clr==0 slope:", out["clr_on_baseCLR0"].get("point"), out["clr_on_baseCLR0"].get("ci95"))
    print("raw clr(matched) slope:", out.get("clr_raw_matched", {}).get("point"), out.get("clr_raw_matched", {}).get("ci95"))
    print("\n" + out["verdict"])
    print(f"\n→ {args.out}")


if __name__ == "__main__":
    main()
