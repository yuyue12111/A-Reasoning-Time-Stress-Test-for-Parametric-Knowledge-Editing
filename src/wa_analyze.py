"""W-A 离线分析(prereg-wseries §2 端点;纯 CPU/stdlib,平台或本地跑)。

读 results/wa/edited_r*of8.jsonl(+可选 base_r*of8.jsonl)→ 出:
  CONSORT 流水表(入组→G2/G3/ambiguous 剔除→分析 n);
  G4 灵敏度门(base 在 a2 组 o_old 阳性率 ≥70%);
  A1 无声表征存在性(a1 组阳性率 + Wilson CI + binomial vs 4.8%);
  A2 anticipatory(a2rev vs a2held 的前窗 max-z:Mann-Whitney 单侧 + AUC);
  A3 edited−base 配对 Δ(S_old)(同 case,中位 + bootstrap CI);
  C1 描述性 onset(per_layer_zold 越 2.0 的首层;o_old vs o_new)——探索档,非 prereg 距离判据。

用:python src/wa_analyze.py [--edited 'results/wa/edited_r*of8.jsonl'] [--base 'results/wa/base_r*of8.jsonl']
                            [--band 16 48] [--out results/wa/analysis.json]
"""
import argparse, collections, glob as globlib, json, math, random


def load(pat):
    rows = []
    for p in sorted(globlib.glob(pat)):
        for l in open(p):
            try:
                d = json.loads(l)
            except Exception:
                continue
            if not d.get("_meta"):
                rows.append(d)
    return rows


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (round((c - h) / d, 4), round((c + h) / d, 4))


def binom_sf(k, n, p0):                       # P(X>=k),精确
    return round(sum(math.comb(n, i) * p0 ** i * (1 - p0) ** (n - i) for i in range(k, n + 1)), 5)


def mann_whitney(a, b):                        # 单侧 P(a>b) via U + 正态近似(带 tie 校正)
    if not a or not b:
        return {"n_a": len(a), "n_b": len(b), "U": None, "p_a_gt_b": None, "auc": None}
    allv = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    ranks, i = {}, 0
    vals = [v for v, _ in allv]
    r = [0.0] * len(vals)
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[j + 1] == vals[i]:
            j += 1
        avg = (i + j) / 2 + 1
        for t in range(i, j + 1):
            r[t] = avg
        i = j + 1
    Ra = sum(r[idx] for idx, (_, g) in enumerate(allv) if g == 0)
    na, nb = len(a), len(b)
    Ua = Ra - na * (na + 1) / 2
    auc = Ua / (na * nb)
    mu = na * nb / 2
    sd = math.sqrt(na * nb * (na + nb + 1) / 12)
    z = (Ua - mu) / sd if sd > 0 else 0.0
    p = 0.5 * math.erfc(z / math.sqrt(2))      # 单侧 P(a>b)
    return {"n_a": na, "n_b": nb, "U": round(Ua, 1), "auc": round(auc, 3), "p_a_gt_b": round(p, 4)}


def boot_median_ci(x, B=10000, seed=42):
    if not x:
        return (None, None, None)
    rng = random.Random(seed)
    n = len(x)
    meds = sorted((sorted(x[rng.randrange(n)] for _ in range(n)))[n // 2] for _ in range(B))
    return (round(sorted(x)[n // 2], 4), round(meds[int(0.025 * B)], 4), round(meds[int(0.975 * B)], 4))


def band_max(curve, lo, hi):
    vals = [v for i, v in enumerate(curve or []) if lo <= i <= hi and v is not None and not math.isnan(v)]
    return max(vals) if vals else None


def onset(curve, lo, hi, thr=2.0):
    for i, v in enumerate(curve or []):
        if lo <= i <= hi and v is not None and not math.isnan(v) and v >= thr:
            return i
    return None


def analyzed(rows, require_g3=True):
    """入分析:有 positive(非门失败/skip/error)且 非 ambiguous;require_g3=True 再要 g3_pass。
    ⚠base 态:链由 edited 模型生成、对 base 是 off-policy(base g3_agree 天然低)——**不 g3 过滤**;
    G3 只作 edited 的入组保真门(prereg §1)。base 只作同链参照(A3/G4),require_g3=False。"""
    out = collections.defaultdict(list)
    for r in rows:
        if r.get("positive") is None or "error" in r or "skip" in r or r.get("gate"):
            continue
        if r.get("ambiguous_1sttok"):
            continue
        if require_g3 and not r.get("g3_pass"):
            continue
        out[r.get("group")].append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edited", default="results/wa/edited_r*of8.jsonl")
    ap.add_argument("--base", default="results/wa/base_r*of8.jsonl")
    ap.add_argument("--band", type=int, nargs=2, default=[16, 48])
    ap.add_argument("--out", default="results/wa/analysis.json")
    args = ap.parse_args()
    lo, hi = args.band
    ed = load(args.edited)
    ba = load(args.base) if globlib.glob(args.base) else []

    # —— CONSORT ——
    con = collections.Counter()
    for r in ed:
        g = r.get("group", "?")
        con[f"entry_{g}"] += 1
        if r.get("gate") == "G2_fail":
            con["G2_fail"] += 1
        elif "skip" in r:
            con[f"skip_{r['skip']}"] += 1
        elif "error" in r:
            con["error"] += 1
        elif not r.get("g3_pass"):
            con["G3_fail"] += 1
        elif r.get("ambiguous_1sttok"):
            con["ambiguous_excl"] += 1
        else:
            con[f"analyzed_{g}"] += 1
    g3_vals = [r["g3_agree"] for r in ed if r.get("g3_agree") is not None]
    g3_med = sorted(g3_vals)[len(g3_vals) // 2] if g3_vals else None

    A = analyzed(ed, require_g3=True)                     # edited:入组门=G3 保真
    B = analyzed(ba, require_g3=False)                    # base:同链参照,不 g3 过滤(off-policy)
    pop = {r["case_id"] for grp in A.values() for r in grp}   # 分析总体=edited 过 G3 的 case
    bmap = {r["case_id"]: r for grp in B.values() for r in grp}
    res = {"consort": dict(con), "g3_agree_median": g3_med, "n_population": len(pop),
           "band": args.band, "n_edited_rows": len(ed), "n_base_rows": len(ba),
           "base_g3_median_offpolicy": (sorted(v)[len(v)//2] if (v:=[r["g3_agree"] for r in ba if r.get("g3_agree") is not None]) else None)}

    # —— G4 灵敏度(base 在 a2 组、限分析总体 的 o_old 阳性率;o_old 在 base 是真事实,应可探)——
    if ba:
        a2pop = [r["case_id"] for g in ("a2rev", "a2held") for r in A.get(g, [])]   # 限 edited 过门的 a2 case
        b_a2 = [bmap[cid] for cid in a2pop if cid in bmap]
        pos = sum(1 for r in b_a2 if r["positive"])
        res["G4_base_sensitivity"] = {"n": len(b_a2), "positive": pos,
                                      "rate": round(pos / len(b_a2), 3) if b_a2 else None,
                                      "pass_ge_0.70": bool(b_a2 and pos / len(b_a2) >= 0.70)}

    # —— A1 无声表征(a1 = CLR0_wide 组)——
    a1 = A.get("a1", [])
    k = sum(1 for r in a1 if r["positive"])
    n = len(a1)
    res["A1"] = {"n": n, "positive": k, "rate": round(k / n, 4) if n else None,
                 "wilson95": wilson(k, n), "binom_p_gt_4.8pct": binom_sf(k, n, 0.048) if n else None,
                 "verdict": None}
    if n:
        sig = binom_sf(k, n, 0.048) < 0.05
        res["A1"]["verdict"] = (
            f"阳性 {k}/{n}={k/n:.1%},Wilson{wilson(k,n)},binom vs 4.8% p={binom_sf(k,n,0.048)} → " +
            ("★显著:CLR0 链里 o_old 仍被亚言语表征 = 言语化是门控非存在开关" if sig else
             "不显著:按 G5 灵敏度标定报 Wilson 上界为无声泄漏率上界(禁写'从不无声')"))

    # —— A2 anticipatory(a2rev vs a2held 前窗 max-z)——
    def prewin_stat(r):
        return band_max(r.get("z_pre_by_layer"), lo, hi)
    rev = [v for r in A.get("a2rev", []) if (v := prewin_stat(r)) is not None]
    held = [v for r in A.get("a2held", []) if (v := prewin_stat(r)) is not None]
    mw = mann_whitney(rev, held)
    res["A2"] = {"stat": "前窗[m-20,m-5) band max-z", **mw,
                 "verdict": (None if mw["p_a_gt_b"] is None else
                             (f"★rev>held 单侧 p={mw['p_a_gt_b']} AUC={mw['auc']} → 回退链 o_old 表征在字面提及前更强(anticipatory,描述)"
                              if mw["p_a_gt_b"] < 0.05 else f"n.s.(p={mw['p_a_gt_b']}):无 anticipatory 差"))}

    # —— A3 edited−base 配对 Δ(S_old);base 用同链参照(不 g3 过滤,见 bmap)——
    if ba:
        diffs = []
        for grp in A.values():
            for r in grp:
                b = bmap.get(r["case_id"])
                if b and r.get("S_old") is not None and b.get("S_old") is not None:
                    diffs.append(r["S_old"] - b["S_old"])
        med, lo_ci, hi_ci = boot_median_ci(diffs)
        res["A3"] = {"n_paired": len(diffs), "median_delta": med, "ci95": [lo_ci, hi_ci],
                     "verdict": (f"Δz(edited−base) 中位={med} {[lo_ci,hi_ci]} → " +
                                 ("edited≈base:关联在编辑通路外完好(绕过说)" if med is not None and abs(med) < 0.5 else
                                  ("edited≪base:编辑广泛压制表征(回退需另释)" if med is not None and med < 0 else
                                   "edited>base:编辑反增 o_old 可读性(存疑,查)")))}

    # —— C1 描述性 onset(探索档)——
    def onset_stat(rows, key):
        os_ = [onset(r.get(key), lo, hi) for r in rows]
        os_ = [o for o in os_ if o is not None]
        return sorted(os_)[len(os_) // 2] if os_ else None
    allrev = A.get("a2rev", [])
    res["C1_descriptive"] = {"_note": "per_layer_zold/znew 越 2.0 的首 decoder 层中位(探索,非 prereg distractor-max onset)",
                             "onset_o_old_rev": onset_stat(allrev, "per_layer_zold"),
                             "onset_o_new_rev": onset_stat(allrev, "per_layer_znew")}

    json.dump(res, open(args.out, "w"), ensure_ascii=False, indent=2)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    print(f"\n→ {args.out}")


if __name__ == "__main__":
    main()
