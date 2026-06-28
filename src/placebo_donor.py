"""E-SUP-BATTERY/W1 · BLIND placebo 供体构建器(零卡,预注册件)。

为每个 CF case 指派一个【与 o_old 频率/长度匹配、但语义无关】的供体词,作为抑制特异性对照臂:
若压一个匹配的无关词也把回退压下去 → "fix 是通用链扰动",非 o_old 特异(W1 自伤);
若压无关词无效、只压 o_old 有效 → o_old 特异性坐实(报 effect-above-placebo 的 margin)。

匹配口径(诚实、确定性):
- 长度匹配:供体取另一 case 的 o_old 值,|len(donor)-len(o_old)|<=1(退化到<=2再到任意)。
- 频率代表:从全体 o_old 值【带重复】抽 → 常见对象(English/France…)按其经验频率被抽中 = 频率代表。
- 排他:donor 的小写 != 本 case 的 o_old/o_new,且互不为子串(防意外相关)。
- BLIND:seed 锁定、与任何 RR/打分无关;**产物 data/placebo_donors.json 入库即锁定其早于结果**(预注册)。
注:运行时 suppress.build_old_token_ids 对不同词几乎必得不同首 token id 集;供体值已与 o_old 不同即足。

用法:python src/placebo_donor.py [--cases data/counterfact.jsonl] [--out data/placebo_donors.json] [--seed 42]
"""
import argparse, json, random
from collections import defaultdict


def build(cases, seed=42):
    """cases: list of {case_id,o_old,o_new}。返回 {case_id: donor} + stats。确定性(seed+排序)。"""
    rng = random.Random(seed)
    by_len = defaultdict(list)                      # 长度 → o_old 值(带重复=频率代表)
    for c in cases:
        by_len[len(str(c["o_old"]))].append(str(c["o_old"]))

    def pool_for(L):                                # 长度 ±1 → ±2 → 全部,逐级放宽
        for tol in (1, 2, 99):
            p = [v for dl in range(-tol, tol + 1) for v in by_len.get(L + dl, [])]
            if p:
                return p
        return []

    donors, n_lenmatch, n_fallback = {}, 0, 0
    for c in sorted(cases, key=lambda x: x["case_id"]):     # 排序 → 与 seed 一起确定性
        o_old, o_new = str(c["o_old"]), str(c["o_new"])
        lo, ln = o_old.lower(), o_new.lower()
        L = len(o_old)
        cand = [v for v in pool_for(L)
                if (vl := v.lower()) not in (lo, ln)        # 不等于本 case 旧/新值
                and vl not in lo and lo not in vl           # 互不为子串(防相关)
                and vl not in ln and ln not in vl]
        if not cand:
            cand = [str(x["o_old"]) for x in cases if str(x["o_old"]).lower() not in (lo, ln)]
            n_fallback += 1
        donor = rng.choice(cand)
        if abs(len(donor) - L) <= 1:
            n_lenmatch += 1
        donors[c["case_id"]] = donor
    stats = {"n": len(donors), "n_len_matched_pm1": n_lenmatch, "n_fallback": n_fallback,
             "len_match_rate": round(n_lenmatch / max(len(donors), 1), 3)}
    return donors, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="data/counterfact.jsonl")
    ap.add_argument("--out", default="data/placebo_donors.json")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    cases = [json.loads(l) for l in open(args.cases) if l.strip()]
    donors, st = build(cases, args.seed)
    json.dump(donors, open(args.out, "w"), ensure_ascii=False, indent=0)
    print(f"# placebo 供体 {st['n']} 条 → {args.out}  (seed={args.seed} BLIND 锁定)")
    print(f"# 长度±1 匹配 {st['n_len_matched_pm1']}/{st['n']} = {st['len_match_rate']};fallback {st['n_fallback']}")
    ex = list(donors.items())[:5]
    bymap = {c["case_id"]: c for c in cases}
    for cid, d in ex:
        print(f"#   {cid}: o_old={bymap[cid]['o_old']!r} → placebo={d!r}")


if __name__ == "__main__":
    main()
