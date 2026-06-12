"""生成式判分 (plan §2.5)：ES/RR/CLR + PS(改述泛化) + Loc(局部性)。规则判分 + 别名表。

口径=生成式 ES_b，**不等于** EasyEdit 自带 rewrite_acc（logits 口径），两者永不混排（CLAUDE.md 约束 4）。
消费 edit_loop 落的探针行：efficacy / para0,para1 / locality / open（open 仅供人工审计，不入指标）。
"""
import json, collections


def hit(text, target, aliases):
    cands = [target] + aliases.get(target, [])
    t = (text or "").lower()
    return any(c and c.lower() in t for c in cands)   # 跳过 None/空候选（如 zsRE o_old 缺失）


def score(jsonl_path, cases, aliases, decode="greedy"):
    """每预算档返回 ES/RR/CLR + PS + Loc 及各自分母 n/n_para/n_loc。

    decode 过滤解码臂（默认 "greedy"——go/no-go 主口径，结论须在 greedy 下成立 sumandplan §6.3）；
    无 decode 字段的旧行视为 greedy（向后兼容）。传 decode="sample" 可单独看采样臂。

    指标语义 (plan §2.5)：
      ES  = 1{answer 命中 o_new 且不含 o_old}              （efficacy 探针）
      RR  = P(answer 含 o_old | B0 efficacy 成功)          （条件回退率，分母=B0 成功数 n_b0）
      CLR = 1{cot 含 o_old}                                 （链内旧知识泄漏，efficacy 的 cot）
      PS  = 1{para_answer 命中 o_new 且不含 o_old}          （改述泛化/portability，para* 探针）
      Loc = 1{locality_answer **不含** o_new}               （局部性：编辑未泄漏到邻域）
            —— 邻域 prompt 是同关系的其它主体(CF)或无关问题(zsRE)，编辑应不波及，
               故"邻域答案未出现 o_new"=局部性保持。合格线 plan §7：B0 下 ES≥90% & Loc≥85%。
    某档某指标无对应探针行时该指标返回 None（如 MQuAKE 无 paraphrases → PS=None）。
    """
    cmap = {c["case_id"]: c for c in cases}
    # case_id -> budget -> probe -> [rows]（para 多条；采样臂多条，下方按 decode 过滤）
    by = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(list)))
    for line in open(jsonl_path):
        r = json.loads(line)
        p = r.get("probe")
        if not p:                                    # 跳过 _meta 头 / edit_loop 错误标记行（无 probe 键）
            continue
        if r.get("decode", "greedy") != decode:      # 只算指定解码臂（默认 greedy）
            continue
        by[r["case_id"]][r["budget"]][p].append(r)

    es = collections.Counter(); rr = collections.Counter(); clr = collections.Counter()
    ps = collections.Counter(); loc = collections.Counter()
    n = collections.Counter(); ps_n = collections.Counter(); loc_n = collections.Counter()
    n_b0 = 0
    for cid, buds in by.items():
        c = cmap[cid]; o_new, o_old = c["o_new"], c["o_old"]
        eff0 = buds.get("B0", {}).get("efficacy", [])
        b0ok = (bool(eff0) and hit(eff0[0]["answer"], o_new, aliases)
                and not hit(eff0[0]["answer"], o_old, aliases))
        n_b0 += b0ok
        for b, probe_rows in buds.items():
            for e in probe_rows.get("efficacy", []):
                n[b] += 1
                es[b] += hit(e["answer"], o_new, aliases) and not hit(e["answer"], o_old, aliases)
                clr[b] += hit(e["cot"], o_old, aliases)
                if b0ok and hit(e["answer"], o_old, aliases):
                    rr[b] += 1                       # 条件回退（plan §2.5 定义）
            for pname, rows in probe_rows.items():
                if pname.startswith("para"):         # para0/para1（改述泛化）
                    for pr in rows:
                        ps_n[b] += 1
                        ps[b] += hit(pr["answer"], o_new, aliases) and not hit(pr["answer"], o_old, aliases)
            for lr in probe_rows.get("locality", []):
                loc_n[b] += 1
                loc[b] += not hit(lr["answer"], o_new, aliases)   # 编辑未泄漏到邻域=局部性保持

    rate = lambda num, den: (num / den if den else None)
    return {b: {"ES": rate(es[b], n[b]), "RR": rr[b] / max(n_b0, 1), "CLR": rate(clr[b], n[b]),
                "PS": rate(ps[b], ps_n[b]), "Loc": rate(loc[b], loc_n[b]),
                "n": n[b], "n_para": ps_n[b], "n_loc": loc_n[b]}
            for b in sorted(set(n) | set(ps_n) | set(loc_n))}
