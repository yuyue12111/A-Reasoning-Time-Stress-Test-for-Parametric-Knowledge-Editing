# -*- coding: utf-8 -*-
"""C2(gap-review):B16 池加宽 5 新 cell 的判官一致性——从在盘票据 results/b16_verdicts.json 补算
Fleiss κ + 原始一致率 P̄ + provenance,给 68% 合并池一个一致性基座(原 50-池合并表无 κ)。

  python src/b16_kappa.py            # 打印 + 出 results/b16_kappa.json

口径:①panel-wide=全 68 链 × 全类目(含 Excluded-held/degenerate)=判官"是否 in-pop + 路由"整体信度;
     ②in-pop routing=33 条 in-pop 链的票(含个别 Excluded 少数票),对齐原 17-池 fleiss_kappa_inpop=0.765 口径。
     纯 stdlib,零依赖。3 判官(n=3)。
"""
import json, os, collections

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fleiss(items):
    """items = [{cat: count}, ...],每项计数和=n 判官(此处 3)。返回 (kappa, Pbar, Pe, cats, N)。
    单一类目(Pe=1)→ kappa=None(未定义)。"""
    items = [it for it in items if sum(it.values()) > 1]
    N = len(items)
    if N == 0:
        return None, None, None, [], 0
    n = sum(items[0].values())
    cats = sorted({c for it in items for c in it})
    Ps = [(sum(it.get(c, 0) ** 2 for c in cats) - n) / (n * (n - 1)) for it in items]
    Pbar = sum(Ps) / N
    tot = N * n
    pj = {c: sum(it.get(c, 0) for it in items) / tot for c in cats}
    Pe = sum(v ** 2 for v in pj.values())
    kappa = None if abs(1 - Pe) < 1e-12 else (Pbar - Pe) / (1 - Pe)
    return kappa, Pbar, Pe, cats, N


def _counts(chains):
    return [collections.Counter(c["votes"]) for c in chains]


def main():
    d = json.load(open(os.path.join(_ROOT, "results", "b16_verdicts.json")))["result"]
    pc = d["per_chain"]
    inpop = [c for c in pc if c["in_pop"]]

    out = {"_status": "C2:B16 5 新 cell 判官一致性(src/b16_kappa.py 从 b16_verdicts.json 补算;3 中性判官)"}

    # ① 全 68 链 × 全类目(含 Excluded)——整体信度(含 in-pop 判定)
    k, pbar, pe, cats, N = fleiss(_counts(pc))
    out["panel_all_votes"] = {"n_chains": N, "categories": cats,
                              "fleiss_kappa": round(k, 4) if k is not None else None,
                              "raw_agreement_pbar": round(pbar, 4), "Pe": round(pe, 4)}
    # ② in-pop 路由(33 链;含个别 Excluded 少数票)——对齐原 17-池 inpop 口径
    k2, pbar2, pe2, cats2, N2 = fleiss(_counts(inpop))
    out["inpop_routing"] = {"n_chains": N2, "categories": cats2,
                            "fleiss_kappa": round(k2, 4) if k2 is not None else None,
                            "raw_agreement_pbar": round(pbar2, 4), "Pe": round(pe2, 4)}
    # 每 cell 原始一致率(P̄)+ in-pop κ(定义得了才报)
    percell = {}
    by_cell = collections.defaultdict(list)
    for c in pc:
        by_cell[c["cell"]].append(c)
    for cell, rows in by_cell.items():
        ip = [r for r in rows if r["in_pop"]]
        kc, pbc, _, _, nc = fleiss(_counts(ip))
        _, pball, _, _, _ = fleiss(_counts(rows))
        percell[cell] = {"n_chains": len(rows), "in_pop": len(ip),
                         "inpop_fleiss_kappa": round(kc, 4) if kc is not None else None,
                         "inpop_raw_agreement": round(pbc, 4) if pbc is not None else None,
                         "all_raw_agreement": round(pball, 4) if pball is not None else None}
    out["per_cell"] = percell
    # provenance:33 in-pop 链各来自哪个 cell(run/解码编码在 cell 名里)
    out["provenance_inpop"] = collections.Counter(c["cell"] for c in inpop)

    # ③ 合并 50-池(原 neutral 17 + 新 33)——给 68% headline 一个真·合并 κ
    neu_path = os.path.join(_ROOT, "results", "a3_neutral", "verdicts_all.jsonl")
    if os.path.exists(neu_path):
        neu = [json.loads(l) for l in open(neu_path) if l.strip()]
        neu_chains = [{"votes": [v.get("primary") for v in r["votes"]],
                       "in_pop": sum(1 for v in r["votes"] if v.get("in_population")) >= 2} for r in neu]
        new_chains = [{"votes": c["votes"], "in_pop": c["in_pop"]} for c in pc]
        comb = neu_chains + new_chains
        comb_ip = [c for c in comb if c["in_pop"]]
        kp, pbp, _, _, Np = fleiss(_counts(comb))
        ki, pbi, _, _, Ni = fleiss(_counts(comb_ip))
        kn, _, _, _, _ = fleiss(_counts([c for c in neu_chains if c["in_pop"]]))
        out["combined_50pool"] = {
            "panel_all_votes": {"n": Np, "fleiss_kappa": round(kp, 4), "raw_agreement_pbar": round(pbp, 4)},
            "inpop_routing": {"n": Ni, "fleiss_kappa": round(ki, 4), "raw_agreement_pbar": round(pbi, 4)},
            "neutral17_inpop_kappa_sanity": round(kn, 4) if kn is not None else None,
            "_note": "合并=原 neutral 17(a3_neutral/verdicts_all)+新 33(b16);neutral17 κ 应≈0.765(neutral_rerun_S1 记录)=复算自洽。"}

    dst = os.path.join(_ROOT, "results", "b16_kappa.json")
    json.dump(out, open(dst, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"\n写出 {dst}")


if __name__ == "__main__":
    main()
