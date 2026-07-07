"""W-A 跑前普查(prereg-wseries §8-1,零 GPU)——A1 总体 n 的门。

数 32B headline(ROME×cf200,greedy)的 B3 链:
  string-CLR0(宽表面形集)全体 / ∩回退 / ∩held / ∩非b0ok,以及 o_old⊂subject 整条剔除数。
宽表面形集(WIDE,只用于普查/排除,与 paper 判分口径 metrics.hit 明确区分):
  o_old + 全别名(**不做 ≥4 字符过滤**)+ 大小写不敏感 **substring**(不要求词边界)。
同时报 paper 口径(metrics.hit,词边界+丢短码)的 CLR0 作对照。
结果回填 prereg-wseries.md §2-A1;CLR0_wide∩回退 n<5 → 按 prereg 声明 traceless 回退不可答。

用(平台,CPU):python src/wa_census.py [--glob 'results/probe/r1qwen32b_ROME_cf200_r*.jsonl'] [--out results/wa_census.json]
"""
import argparse, collections, glob as globlib, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics


def wide_hit(text, o_old, aliases):
    """宽口径:o_old+全别名(含 <4 字符)大小写不敏感 substring。剔除/普查用,判分勿用。"""
    t = (text or "").lower()
    cands = [str(o_old)] + [str(a) for a in aliases.get(o_old, []) if a]
    return any(str(c).lower() in t for c in cands if str(c).strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default="results/probe/r1qwen32b_ROME_cf200_r*.jsonl")
    ap.add_argument("--cases", default="data/counterfact.jsonl")
    ap.add_argument("--aliases", default="data/aliases.json")
    ap.add_argument("--out", default="results/wa_census.json")
    args = ap.parse_args()

    cases = {c["case_id"]: c for c in (json.loads(l) for l in open(args.cases))}
    aliases = json.load(open(args.aliases))
    by = collections.defaultdict(dict)
    for sh in sorted(globlib.glob(args.glob)):
        for line in open(sh):
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("probe") == "efficacy" and d.get("decode", "greedy") == "greedy" and d["case_id"] in cases:
                by[d["case_id"]][d["budget"]] = d

    rows = []
    n_subj_overlap = 0
    for cid, bud in by.items():
        c = cases[cid]
        b0, b3 = bud.get("B0"), bud.get("B3")
        if not b0 or not b3:
            continue
        s, o_old, o_new = c.get("s") or "", c["o_old"], c["o_new"]
        if str(o_old).lower() in str(s).lower():         # o_old⊂subject → W-A 整条剔除(prereg §2 规则④)
            n_subj_overlap += 1
            continue
        clean = lambda t: metrics._without_subject(t or "", s)
        a0, a3, cot3 = clean(b0["answer"]), clean(b3["answer"]), b3.get("cot", "")
        b0ok = metrics.hit(a0, o_new, aliases) and not metrics.hit(a0, o_old, aliases)
        reverted = bool(b0ok and metrics.hit(a3, o_old, aliases))
        held = bool(b0ok and not reverted)
        clr_wide = wide_hit(cot3, o_old, aliases)                       # 宽:substring+全别名
        clr_paper = bool(metrics.hit(metrics._without_subject(cot3, s), o_old, aliases))  # paper 口径对照
        rows.append({"case_id": cid, "b0ok": bool(b0ok), "reverted": reverted, "held": held,
                     "clr_wide": bool(clr_wide), "clr_paper": clr_paper})

    def n(pred):
        return sum(1 for r in rows if pred(r))

    def ids(pred, cap=30):
        xs = sorted(r["case_id"] for r in rows if pred(r))
        return xs[:cap] + (["…"] if len(xs) > cap else [])

    rep = {
        "n_paired": len(rows), "n_subject_overlap_excluded": n_subj_overlap,
        "b0ok": n(lambda r: r["b0ok"]), "reverted": n(lambda r: r["reverted"]), "held": n(lambda r: r["held"]),
        "CLR0_wide_all": n(lambda r: not r["clr_wide"]),
        "CLR0_wide_and_reverted": n(lambda r: not r["clr_wide"] and r["reverted"]),
        "CLR0_wide_and_held": n(lambda r: not r["clr_wide"] and r["held"]),
        "CLR0_wide_and_nonb0ok": n(lambda r: not r["clr_wide"] and not r["b0ok"]),
        "CLR0_paper_all": n(lambda r: not r["clr_paper"]),
        "CLR0_paper_and_reverted": n(lambda r: not r["clr_paper"] and r["reverted"]),
        "ids_CLR0_wide_reverted": ids(lambda r: not r["clr_wide"] and r["reverted"]),
        "ids_CLR0_wide_all": ids(lambda r: not r["clr_wide"]),
        "_verdict_hint": None,
    }
    small = rep["CLR0_wide_and_reverted"]
    rep["_verdict_hint"] = (
        f"CLR0_wide∩reverted = {small} → " +
        ("n<5:按 prereg 声明『traceless 回退本数据不可答』(算干净);A1 主总体=CLR0_wide 全体"
         f"(n={rep['CLR0_wide_all']}),claim=言语化是门控。" if small < 5 else
         f"n≥5:A1 可含回退子组分析(仍以 CLR0 全体 n={rep['CLR0_wide_all']} 为主总体)。"))
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(rep, open(args.out, "w"), ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in rep.items() if not k.startswith("ids_")}, ensure_ascii=False, indent=1))
    print("ids CLR0_wide∩reverted:", rep["ids_CLR0_wide_reverted"])
    print(f"→ {args.out}(回填 prereg-wseries.md §2-A1)")


if __name__ == "__main__":
    main()
