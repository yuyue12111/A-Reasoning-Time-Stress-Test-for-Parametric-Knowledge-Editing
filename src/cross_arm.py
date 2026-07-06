"""E-SUP-BATTERY/W1 · 跨臂配对差 bootstrap(headline 因果统计)。

`metrics`/`score_pilot` 只算组内速率;本模块做**组间、按 case_id 配对**的差 + CI —— 这才是 W1 对照的载重统计。
四臂(同 case_id 集、同 decode、scope=think、|α|=8,仅 suppress.source 不同):
  N=不压 / T=压 o_old(现 fix) / D=压 o_new(方向对照) / P=压 placebo(特异性对照)
预注册符号阶梯(B3,ES/ES升高、RR/CLR 下降方向):**D < N ~ P < T**(ES@B3);效应主报 **T−P(o_old 超 placebo 的 margin)**,非 T−N(o_old-vs-零)。

用法(打分后,纯 CPU):
  python src/cross_arm.py --budget B3 --editor ROME \
     --arm N=experiments/probe32b.yaml --arm T=experiments/probe32b_sup.yaml \
     --arm D=experiments/probe32b_sup_onew.yaml --arm P=experiments/probe32b_sup_placebo.yaml
"""
import argparse, glob, json, os, random
import yaml
import metrics

METRICS = ["ES", "RR", "RRs", "CLR"]


def per_case(cfg, editor, budget, decode="greedy"):
    """{case_id: {ES,RR,RRs,CLR}} on efficacy/greedy。**口径严格同 metrics.score**:
    _without_subject 挖主体复述(去污)+ RR/RRs 仅在 b0ok(B0 编辑成功)case 上有值(否则 None,不入分母);
    ES/CLR 在全 case 上。→ 边际数与 score_pilot 一致、跨臂配对差在 paper 口径。"""
    ds = cfg["dataset"]
    pat = os.path.join(cfg["out_dir"], f"{cfg['model_tag']}_{editor}_{ds['tag']}_r*.jsonl")
    cases = {c["case_id"]: c for c in (json.loads(l) for l in open(ds.get("fallback_path", ds["path"])))}
    aliases = json.load(open("data/aliases.json"))
    by = {}                                          # cid -> budget -> efficacy 行
    for sh in sorted(glob.glob(pat)):
        for line in open(sh):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get("_meta") or d.get("error") or d.get("probe") != "efficacy":
                continue
            if d.get("decode", "greedy") != decode or d["case_id"] not in cases:
                continue
            by.setdefault(d["case_id"], {})[d.get("budget")] = d
    out = {}
    for cid, buds in by.items():
        if budget not in buds:
            continue
        c = cases[cid]
        s, o_old, o_new = c.get("s") or "", c["o_old"], c["o_new"]
        clean = lambda t: metrics._without_subject(t or "", s)        # 去主体复述(同 metrics.score line140)
        ans, cot = clean(buds[budget].get("answer")), clean(buds[budget].get("cot"))
        ho, hn = bool(metrics.hit(ans, o_old, aliases)), bool(metrics.hit(ans, o_new, aliases))
        rec = {"ES": int(hn and not ho), "CLR": int(bool(metrics.hit(cot, o_old, aliases)))}
        b0 = buds.get("B0")                                          # b0ok 门(B0 答新且不含旧;scope=think 下 B0 跨臂同)
        b0ok = bool(b0) and metrics.hit(clean(b0.get("answer")), o_new, aliases) \
            and not metrics.hit(clean(b0.get("answer")), o_old, aliases)
        rec["RR"] = int(ho) if b0ok else None                        # RR/RRs 仅 b0ok case 有值(同 metrics rr_n 门)
        rec["RRs"] = int(ho and not hn) if b0ok else None
        out[cid] = rec
    return out


def marginal(A):
    out = {}
    for m in METRICS:
        vals = [v[m] for v in A.values() if v.get(m) is not None]
        out[m] = round(sum(vals) / len(vals), 4) if vals else None
    return out


def paired_diff(A, B, metric, B_=10000, seed=42):
    """按 case_id 配对的 (armA - armB) 均差 + 95% bootstrap CI + 双侧 p(重采样 case)。None(如非 b0ok 的 RR)跳过。"""
    ids = [i for i in sorted(set(A) & set(B)) if A[i].get(metric) is not None and B[i].get(metric) is not None]
    if not ids:
        return {"n": 0}
    diffs = [A[i][metric] - B[i][metric] for i in ids]
    n = len(diffs)
    mean = sum(diffs) / n
    rng = random.Random(seed)
    boots = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(B_))
    lo, hi = boots[int(0.025 * B_)], boots[int(0.975 * B_)]
    p = 2 * min(sum(b <= 0 for b in boots), sum(b >= 0 for b in boots)) / B_
    return {"n": n, "mean": round(mean, 4), "ci": [round(lo, 4), round(hi, 4)], "p": round(min(p, 1.0), 4)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", action="append", required=True, help="label=config.yaml(可多次)")
    ap.add_argument("--editor", default="ROME")
    ap.add_argument("--budget", default="B3")
    ap.add_argument("--decode", default="greedy")
    ap.add_argument("--out", default=None, help="可选:汇总 json 落盘")
    args = ap.parse_args()

    arms = {}
    for spec in args.arm:
        label, _, path = spec.partition("=")
        arms[label] = per_case(yaml.safe_load(open(path)), args.editor, args.budget, args.decode)
    print(f"# 跨臂配对差 @ {args.budget} {args.decode}  臂={list(arms)}  各 n={{ {', '.join(f'{k}:{len(v)}' for k,v in arms.items())} }}")
    print(f"\n# 各臂边际速率:")
    print(f"{'arm':<6}" + "".join(f"{m:>9}" for m in METRICS))
    for k, v in arms.items():
        mg = marginal(v)
        print(f"{k:<6}" + "".join(f"{(mg.get(m) if mg.get(m) is not None else float('nan')):>9.3f}" for m in METRICS))

    # 预注册关键对照(存在的臂才算)
    contrasts = [("T", "N", "fix 效应(o_old-vs-零,非主报)"), ("T", "P", "★o_old 超 placebo 的 margin(主报特异性)"),
                 ("D", "N", "★方向臂(压 o_new;符号错=近致命)"), ("P", "N", "placebo floor(链扰动,期望≈0)"),
                 ("C", "N", "强竞争者 floor(同 relation 强错答;M4,期望≈0=非通用)"),
                 ("T", "C", "★o_old 超强竞争者 margin(M4 最强特异性;T−C 排零=o_old 特异)")]
    summ = {"arms_n": {k: len(v) for k, v in arms.items()}, "marginal": {k: marginal(v) for k, v in arms.items()}, "contrasts": {}}
    print(f"\n# 配对对照(armA − armB,均差 [95%CI] p):")
    for a, b, desc in contrasts:
        if a in arms and b in arms:
            print(f"## {a}−{b}  {desc}")
            for m in METRICS:
                r = paired_diff(arms[a], arms[b], m)
                sig = "" if r.get("n", 0) == 0 else ("  ✅排零" if (r["ci"][0] > 0 or r["ci"][1] < 0) else "  ⚠含0")
                print(f"   {m:<5} {r.get('mean'):>8} {str(r.get('ci')):>20} p={r.get('p')}{sig}")
                summ["contrasts"].setdefault(f"{a}-{b}", {})[m] = r
    if args.out:
        json.dump(summ, open(args.out, "w"), ensure_ascii=False, indent=2)
        print(f"\n# → {args.out}")
    print("\n# 读法:T−P 的 RR/CLR 应负且排零(o_old 特异有效);P−N 应≈0(placebo 无效=非通用扰动);")
    print("#       D−N 的 ES 应≤0(压 o_new 不改善/恶化);符号阶梯 D<N~P<T 成立=W1 因果对照立。")


if __name__ == "__main__":
    main()
