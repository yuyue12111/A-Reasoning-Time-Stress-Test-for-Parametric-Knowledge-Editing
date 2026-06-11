"""ES/RR/CLR 计算 (plan §12.3, 指标定义见 plan §2.5). 规则判分 + 别名表."""
import json, collections

def hit(text, target, aliases):
    cands = [target] + aliases.get(target, [])
    t = (text or "").lower()
    return any(c and c.lower() in t for c in cands)   # 跳过 None/空候选（如 zsRE o_old 缺失）

def score(jsonl_path, cases, aliases):
    cmap = {c["case_id"]: c for c in cases}
    by = collections.defaultdict(dict)       # case_id -> budget -> efficacy行
    for line in open(jsonl_path):
        r = json.loads(line)
        if r.get("probe") == "efficacy":     # .get：跳过 edit_loop 的错误标记行（无 probe 键）
            by[r["case_id"]][r["budget"]] = r
    es = collections.Counter(); rr = collections.Counter()
    clr = collections.Counter(); n = collections.Counter(); n_b0 = 0
    for cid, buds in by.items():
        c = cmap[cid]
        b0ok = ("B0" in buds
                and hit(buds["B0"]["answer"], c["o_new"], aliases)
                and not hit(buds["B0"]["answer"], c["o_old"], aliases))
        n_b0 += b0ok
        for b, r in buds.items():
            n[b] += 1
            es[b] += (hit(r["answer"], c["o_new"], aliases)
                      and not hit(r["answer"], c["o_old"], aliases))
            clr[b] += hit(r["cot"], c["o_old"], aliases)
            if b0ok and hit(r["answer"], c["o_old"], aliases):
                rr[b] += 1                    # 条件回退（plan §2.5 定义）
    return {b: {"ES": es[b]/n[b], "CLR": clr[b]/n[b],
                "RR": rr[b]/max(n_b0, 1), "n": n[b]} for b in sorted(n)}
