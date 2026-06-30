"""CLR scorer-robustness (depth-plan §第三轮 TIER-A #3).

承重指标 CLR(链泄漏)是 emergence 趋势的唯一铁腿(per-case cluster bootstrap 下仍显著,见
src/percase_emergence.py)。但 CLR 用的去污规则有一个未预注册的研究者自由度:别名长度 cutoff(<4 字符丢)。
审稿担心:这个 cutoff 可能差异化地缩小小模型 CLR、从而"制造"单调上升趋势。本脚本证明它没有——

  对每个尺度,在 alias cutoff ∈ {3,4,5}(论文口径=4)、含/不含别名、以及一个"灌水基线"
  (naive substring + 全别名,无词边界无 cutoff) 下重算 CLR@B3,输出:
    (a) CLR 随尺度单调上升在所有 cutoff 下都成立(趋势不是 cutoff 造的);
    (b) 灌水因子 = substr_all / wb_c4 ≈ 2× 且大致 scale-invariant(去污不差异化缩小小模型 CLR)。

口径完全复用 src/metrics.py 的 _without_subject / _wb / _BAD_ALIAS,与主表 CLR 同源,仅把
_safe_cands 的硬编码 >=4 参数化。尺度推断复用 src/percase_emergence.infer_tag_meta(含 genbench/
1_5b 守护)。

用法(平台,与 percase_emergence 同一 session):
  python src/clr_robustness.py --glob 'results/probe/*_ROME_cf*.jsonl' \
      --glob 'results/pilot/*r1qwen7b*ROME*.jsonl' --map percase_map.json \
      --out results/clr_robustness.json
自测: python src/clr_robustness.py --selftest
"""
import argparse, collections, glob as globlib, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics
import percase_emergence as pe

_KNOWN = {(1.5, "Qwen"), (7.0, "Qwen"), (14.0, "Qwen"), (32.0, "Qwen"), (8.0, "Llama"), (70.0, "Llama")}


def _cands(target, aliases, cutoff, use_aliases):
    out = [str(target)]
    if use_aliases:
        out += [a for a in aliases.get(target, [])
                if a and len(str(a).strip()) >= cutoff and not metrics._BAD_ALIAS.match(str(a))]
    return out


def hit_wb(text, target, aliases, cutoff, use_aliases=True):
    """词边界命中(论文口径),但 cutoff 可调、别名可关。"""
    t = (text or "").lower()
    return any(metrics._wb(c).search(t) for c in _cands(target, aliases, cutoff, use_aliases) if str(c).strip())


def hit_substr(text, target, aliases):
    """灌水基线:裸 substring + 全非平凡别名(无词边界、无长度 cutoff)= 去污前的旧口径。"""
    t = (text or "").lower()
    cs = [str(target)] + [a for a in aliases.get(target, [])
                          if a and not metrics._BAD_ALIAS.match(str(a))]
    return any(str(c).lower().strip() in t for c in cs if str(c).strip())


# 变体名 -> (cot, o_old, aliases) -> bool
VARIANTS = {
    "substr_all": lambda t, o, a: hit_substr(t, o, a),          # 灌水上界(去污前)
    "wb_c3": lambda t, o, a: hit_wb(t, o, a, 3, True),
    "wb_c4": lambda t, o, a: hit_wb(t, o, a, 4, True),          # ★ 论文口径
    "wb_c5": lambda t, o, a: hit_wb(t, o, a, 5, True),
    "wb_noalias": lambda t, o, a: hit_wb(t, o, a, 4, False),    # 仅 target 全名
}


def clr_for_shard(path, cmap, aliases, decode="greedy", late="B3"):
    """返回 (n_eff, {variant: 命中计数})——【原始计数,不是率】,以便 main 按 (scale,family) 跨分片聚合。
    CLR=late efficacy 行里 hit(_without_subject(cot), o_old)。"""
    by = collections.defaultdict(lambda: collections.defaultdict(list))
    for line in open(path):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("probe") != "efficacy" or r.get("decode", "greedy") != decode:
            continue
        by[r["case_id"]][r.get("budget")].append(r)
    cnt = {v: 0 for v in VARIANTS}
    n = 0
    for cid, buds in by.items():
        c = cmap.get(cid)
        if not c:
            continue
        o_old, subj = c["o_old"], (c.get("s") or "")
        for e in buds.get(late, []):
            cot = metrics._without_subject(e.get("cot") or "", subj)
            n += 1
            for v, fn in VARIANTS.items():
                cnt[v] += int(fn(cot, o_old, aliases))
    return n, cnt


def _ols_slope(xs, ys):
    import numpy as np
    x = np.asarray(xs, float); y = np.asarray(ys, float)
    xc = x - x.mean()
    denom = float((xc * xc).sum())
    return float((xc * (y - y.mean())).sum() / denom) if denom else float("nan")


def _monotone(seq):
    s = [v for v in seq if v is not None]
    return all(b >= a - 1e-9 for a, b in zip(s, s[1:]))


def analyze(shard_clr):
    """shard_clr: list of (params_b, family, n_eff, {variant: clr})。返回每变体 slope + 单调 + 灌水因子。"""
    import math
    rows = sorted(shard_clr, key=lambda r: (r[1], r[0]))
    out = {"per_scale": [], "per_variant": {}, "inflation_substr_over_wb_c4": []}
    for pb, fam, n_eff, clr in rows:
        out["per_scale"].append({"params_b": pb, "family": fam, "n_eff": n_eff, "clr": clr})
        c4 = clr.get("wb_c4"); sa = clr.get("substr_all")
        out["inflation_substr_over_wb_c4"].append(
            {"params_b": pb, "family": fam, "factor": (sa / c4 if c4 else None)})
    logp = [math.log10(pb) for pb, _f, _n, _c in rows]
    for v in VARIANTS:
        ys = [c.get(v) for _p, _f, _n, c in rows]
        pooled = _ols_slope([lp for lp, y in zip(logp, ys) if y is not None],
                            [y for y in ys if y is not None])
        # 族内单调(各族按尺度升序)
        mono = {}
        for fam in ("Qwen", "Llama"):
            seq = [c.get(v) for p, f, n, c in rows if f == fam]
            if len([s for s in seq if s is not None]) >= 2:
                mono[fam] = _monotone(seq)
        out["per_variant"][v] = {"pooled_slope_on_log10params": pooled, "within_family_monotone": mono}
    return out


def _selftest():
    # target 全名【永远保留】(即便短);cutoff 只过滤短【别名】。别名长度:French=6,Fra=3,FR=2,Hexagon=7。
    aliases = {"France": ["French", "Fra", "FR", "Hexagon"]}
    assert hit_wb("the french side", "France", aliases, 4, True) is True       # 'French'(6) 别名词边界命中
    assert hit_wb("the fra zone", "France", aliases, 3, True) is True          # 'Fra'(3) 在 cutoff=3 保留 → 命中
    assert hit_wb("the fra zone", "France", aliases, 4, True) is False         # 'Fra'(3) 在 cutoff=4 被丢 → 不命中
    assert hit_wb("the french side", "France", aliases, 4, False) is False     # 关别名 → 仅 'France' 全名 → 不中
    assert hit_wb("a frenchman walked", "France", aliases, 4, True) is False   # 词边界:'french' ≠ 'frenchman'
    assert hit_substr("a frenchman walked", "France", aliases) is True         # 灌水:裸 substring 'french' ⊂ 'frenchman'
    assert hit_substr("see france today", "France", aliases) is True           # target 子串命中
    print("ok clr_robustness selftest")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", action="append", default=[], help="per-case ROME×CF 分片(可多次);genbench/非编辑自动跳过")
    ap.add_argument("--cases", default="data/counterfact.jsonl")
    ap.add_argument("--aliases", default="data/aliases.json")
    ap.add_argument("--map", default=None, help="{文件名子串:[params_b,family]} 覆盖尺度推断(同 percase_emergence)")
    ap.add_argument("--decode", default="greedy")
    ap.add_argument("--late", default="B3")
    ap.add_argument("--out", default="results/clr_robustness.json")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        _selftest(); return

    paths = []
    for g in args.glob:
        paths += sorted(globlib.glob(g))
    paths = sorted(set(paths))
    if not paths:
        raise SystemExit(f"glob 没匹配到分片：{args.glob}")
    cmap = {c["case_id"]: c for c in (json.loads(l) for l in open(args.cases))}
    aliases = json.load(open(args.aliases))
    override = json.load(open(args.map)) if args.map else None

    # 跨分片【按 (params_b, family) 聚合原始计数】→ 每尺度一行(不是每分片一行)。
    agg = collections.defaultdict(lambda: {"n": 0, **{v: 0 for v in VARIANTS}})
    skipped = []
    for p in paths:
        meta = pe.infer_tag_meta(os.path.basename(p), override)
        if meta is None:
            skipped.append(os.path.basename(p)); continue
        pb, fam = meta
        n_eff, cnt = clr_for_shard(p, cmap, aliases, decode=args.decode, late=args.late)
        a = agg[(float(pb), fam)]; a["n"] += n_eff
        for v in VARIANTS:
            a[v] += cnt[v]
    shard_clr = [(pb, fam, a["n"], {v: (a[v] / a["n"] if a["n"] else None) for v in VARIANTS})
                 for (pb, fam), a in agg.items() if a["n"]]
    got = set((pb, fam) for pb, fam, _n, _c in shard_clr)
    if got - _KNOWN or _KNOWN - got:
        print(f"⚠ WARN cells: detected={sorted(got)} missing={sorted(_KNOWN - got)} "
              f"unexpected={sorted(got - _KNOWN)} → 趋势结论以最终 6-cell 为准。", file=sys.stderr)

    res = analyze(shard_clr)
    out = {"_note": "CLR scorer-robustness:别名 cutoff∈{3,4,5}+含/不含别名+灌水基线下重算 CLR@late。"
                    "证 (a) 单调上升对 cutoff 鲁棒、(b) ~2× 灌水因子大致 scale-invariant(去污不制造趋势)。"
                    "口径复用 metrics._without_subject/_wb/_BAD_ALIAS,仅参数化 >=4 cutoff。",
           "_config": {"glob": args.glob, "decode": args.decode, "late": args.late, "skipped": skipped},
           **res}
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(out, open(args.out, "w"), ensure_ascii=False, indent=2)

    print(f"# CLR scorer-robustness —— cells={sorted(got)}  variants={list(VARIANTS)}")
    hdr = f"{'scale':<12}{'n':>6}  " + "".join(f"{v:>12}" for v in VARIANTS)
    print(hdr)
    for r in res["per_scale"]:
        line = f"{r['family']+'-'+str(r['params_b'])+'B':<12}{r['n_eff']:>6}  " + \
               "".join(f"{(r['clr'][v] if r['clr'][v] is not None else float('nan')):>12.3f}" for v in VARIANTS)
        print(line)
    print("\n# pooled slope(CLR on log10 params)/族内单调 per variant:")
    for v, d in res["per_variant"].items():
        print(f"  {v:<12} slope={d['pooled_slope_on_log10params']:+.3f}  monotone={d['within_family_monotone']}")
    print("\n# 灌水因子 substr_all / wb_c4 (应≈2× 且各尺度相近=scale-invariant):")
    for r in res["inflation_substr_over_wb_c4"]:
        f = r["factor"]
        print(f"  {r['family']+'-'+str(r['params_b'])+'B':<12} {('%.2fx'%f) if f else 'NA'}")
    print(f"\n# → {args.out}")


if __name__ == "__main__":
    main()
