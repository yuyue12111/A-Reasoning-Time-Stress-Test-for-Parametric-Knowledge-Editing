"""S1 中性判官聚合器(规范版)—— 从 results/a3_neutral/verdicts_all.jsonl 再生 summary.json
并同步 results.json 的 rq2_taxonomy.neutral_rerun_S1。

================================================================================
为什么有这个文件(终极review ★2,2026-07-03)
================================================================================
S1 首版聚合脚本只存在于 session scratchpad(commit 2e50c86 提及未落库),且有 **off-by-one bug**:
聚合字典按 `case_id` 单键 → 跨尺度同 case 互相覆盖(cf_6933 在 14b=Bridge 全票、32b=Recall 全票,
32b 行顶掉 14b 行)→ 记录 pooled 16{13,2,1},真值 **17{14,2,1}**、14b in-pop 3→**4**。
本版按 **(scale, case_id) 双键** 聚合,消灭覆盖;跨尺度重复 case(cf_6933/cf_9255)显式记录。
"population flip" 分母双口径写明:按行 3/19、按 unique case_id 3/18。

7B Fleiss κ 口径(连带修复):results.json 曾记 null+"全一类未定义"——错,cf_17023 票=
[Bridge,Bridge,Associative] 非全一类;正确值 −0.091(仅 in-pop 4 case、路由类;近全 Bridge 边际下
Pe≈0.847,单票分歧即压负 → κ 负≠随机差,须与一致率 P̄=0.833 同报)。见 summary_7b.json
`fleiss_kappa_overall`。本脚本对中性票同口径计算各尺度 κ + P̄,供 table_rq2 中性版取数。

运行(幂等,只读 verdicts_all.jsonl + labels_*.jsonl):
  python src/s1_record.py            # 再生 summary.json + 更新 results.json + 打印中性版表
"""
import collections
import json
import os
import sys

ROUTES = ["Reflective-override", "Bridge", "Recall", "Associative"]
HELD = {"Excluded-held", "Excluded-degenerate"}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def aggregate_votes(votes):
    """3 票 → (primary, in_pop)。held 若 ≥2 票 commits_new / Excluded / not in_population。"""
    prims = [v.get("primary") for v in votes]
    held_v = sum(1 for v in votes
                 if v.get("commits_new") or v.get("primary") in HELD or not v.get("in_population"))
    if held_v >= 2:
        return "Excluded-held", False
    rv = [p for p in prims if p in ROUTES]
    prim = collections.Counter(rv).most_common(1)[0][0] if rv else "Associative"
    return prim, True


def fleiss_kappa_routes(vote_rows):
    """Fleiss κ,仅路由类(与 summary_7b.json `fleiss_kappa_overall` 同口径:in-pop case、
    类别=票面出现的路由)。近退化边际下对单票分歧极敏感 → 与 P̄(raw agreement)同报。"""
    rows = [vv for vv in vote_rows if vv]
    if not rows:
        return None, None
    k = len(rows[0])
    cats = sorted({p for vv in rows for p in vv})
    if len(cats) < 2:                      # 真·全一类:κ 未定义,P̄=1
        return None, 1.0
    tab = [[vv.count(c) for c in cats] for vv in rows]
    p_i = [(sum(x * x for x in row) - k) / (k * (k - 1)) for row in tab]
    pbar = sum(p_i) / len(rows)
    pj = [sum(row[j] for row in tab) / (len(rows) * k) for j in range(len(cats))]
    pe = sum(p * p for p in pj)
    if 1 - pe < 1e-12:
        return None, pbar
    return (pbar - pe) / (1 - pe), pbar


def main():
    os.chdir(ROOT)
    # ---- 中性 verdicts:键 = (scale, case_id),消灭跨尺度覆盖(★2 bug 修复点)----
    neutral, dupc = {}, collections.Counter()
    for l in open("results/a3_neutral/verdicts_all.jsonl", encoding="utf-8"):
        r = json.loads(l)
        prim, inp = aggregate_votes(r["votes"])
        neutral[(r["scale"], r["case_id"])] = {
            "primary": prim, "in_pop": inp, "votes": [v.get("primary") for v in r["votes"]]}
        dupc[r["case_id"]] += 1
    cross_dups = sorted(c for c, n in dupc.items() if n > 1)

    def dist(keys):
        c = collections.Counter(neutral[k]["primary"] for k in keys if neutral[k]["in_pop"])
        return sum(c.values()), dict(c)

    pooled_n, pooled_d = dist(list(neutral))
    per_scale = {}
    for sc in ("7b", "14b", "32b"):
        ks = [k for k in neutral if k[0] == sc]
        n, dd = dist(ks)
        kappa, pbar = fleiss_kappa_routes(
            [neutral[k]["votes"] for k in ks if neutral[k]["in_pop"]])
        per_scale[sc] = {"n_in_pop": n, "dist": dd,
                         "fleiss_kappa_inpop": None if kappa is None else round(kappa, 4),
                         "raw_agreement_pbar": None if pbar is None else round(pbar, 4),
                         "in_pop_ids": sorted(k[1] for k in ks if neutral[k]["in_pop"])}
    kap_all, pbar_all = fleiss_kappa_routes(
        [v["votes"] for v in neutral.values() if v["in_pop"]])

    # ---- 污染侧 in-pop(labels_*.jsonl),分母双口径 ----
    cont = set()
    for sc in ("7b", "14b", "32b"):
        for l in open(f"results/a3/labels_{sc}.jsonl", encoding="utf-8"):
            r = json.loads(l)
            if r.get("in_population"):
                cont.add((sc, r["case_id"]))
    flips = sorted(f"{c}@{s}" for (s, c) in cont
                   if (s, c) in neutral and not neutral[(s, c)]["in_pop"])

    summary = {
        "_note": ("S1/M3 中性重跑 taxonomy 判官(去 chain_classify:25 污染 + 去 Bridge-first prime,3 判官同 33 链)。"
                  "★2 修复版(终极review 2026-07-03):按 (scale,case_id) 双键聚合——首版按 case_id 单键,"
                  "cf_6933@14b(Bridge 全票)被 32b 行(Recall 全票)覆盖 → 曾记 pooled 16{13,2,1},真值 17{14,2,1}。"),
        "pooled_neutral": {"n_in_pop": pooled_n, "dist": pooled_d,
                           "Bridge_pct": round(pooled_d.get("Bridge", 0) / pooled_n, 3) if pooled_n else None,
                           "fleiss_kappa_inpop": None if kap_all is None else round(kap_all, 4),
                           "raw_agreement_pbar": None if pbar_all is None else round(pbar_all, 4)},
        "pooled_contaminated": {"n_in_pop_rows": len(cont), "n_in_pop_unique_ids": len({c for _, c in cont}),
                                "dist": {"Bridge": 17, "Reflective-override": 2, "Recall": 0, "Associative": 0}},
        "per_scale_neutral": per_scale,
        "cross_scale_duplicate_cases": cross_dups,
        "population_flip_to_held": {"flips": flips,
                                    "rate_by_rows": f"{len(flips)}/{len(cont)}",
                                    "rate_by_unique_ids": f"{len(flips)}/{len({c for _, c in cont})}",
                                    "_note": "分母双口径:行=(scale,case);unique=跨尺度去重 case_id。"},
        "verdict": (f"★S1(★2 修复后):(1) Recall 0→{pooled_d.get('Recall', 0)} = 'no flat recall' 部分仪器制造被证伪;"
                    f"(2) Bridge 仍主导({pooled_d.get('Bridge', 0)}/{pooled_n}≈{pooled_d.get('Bridge', 0)/pooled_n*100:.0f}% vs 污染 89%);"
                    f"(3) Associative=0 = 'committed 回退从不 traceless' 去污后依然成立;"
                    f"(4) population 判官敏感 {len(flips)}/{len(cont)} 行(unique 口径 {len(flips)}/18)。"),
    }
    with open("results/a3_neutral/summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # ---- 同步 results.json ----
    rj = "paper/results.json"
    pj = json.load(open(rj, encoding="utf-8"), object_pairs_hook=collections.OrderedDict)
    tax = pj["rq2_taxonomy"]
    node = tax.get("neutral_rerun_S1", collections.OrderedDict())
    node["_status"] = ("S1/M3 去污中性重跑(results/a3_neutral;src/chain_classify.py JUDGE_PROMPT_NEUTRAL)。"
                       "★2 修复版:src/s1_record.py 按 (scale,case) 双键再生,可复算。")
    node["pooled"] = summary["pooled_neutral"]
    node["per_scale"] = {sc: {"n_in_pop": v["n_in_pop"], "dist": v["dist"],
                              "fleiss_kappa_inpop": v["fleiss_kappa_inpop"],
                              "raw_agreement_pbar": v["raw_agreement_pbar"]}
                         for sc, v in per_scale.items()}
    node["cross_scale_duplicate_cases"] = cross_dups
    node["population_flip_to_held"] = summary["population_flip_to_held"]
    node["verdict"] = summary["verdict"]
    node["_offbyone_audit"] = ("首版聚合按 case_id 单键 → cf_6933@14b(Bridge 3/3)被 cf_6933@32b(Recall 3/3)覆盖,"
                               "曾记 pooled 16{13,2,1}/14b n=3;真值 pooled 17{14,2,1}/14b n=4。四次独立复算一致(终极review ★2)。")
    tax["neutral_rerun_S1"] = node
    json.dump(pj, open(rj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.load(open(rj, encoding="utf-8"))     # 可解析性自检

    print("pooled:", pooled_n, pooled_d, " κ_inpop:", kap_all and round(kap_all, 3), " P̄:", pbar_all and round(pbar_all, 3))
    for sc, v in per_scale.items():
        print(f"  [{sc}] n={v['n_in_pop']} {v['dist']} κ={v['fleiss_kappa_inpop']} P̄={v['raw_agreement_pbar']}")
    print("cross-scale dups:", cross_dups, " flips:", summary["population_flip_to_held"]["rate_by_rows"])
    print("→ results/a3_neutral/summary.json + paper/results.json rq2_taxonomy.neutral_rerun_S1 已再生")
    return 0


if __name__ == "__main__":
    sys.exit(main())
