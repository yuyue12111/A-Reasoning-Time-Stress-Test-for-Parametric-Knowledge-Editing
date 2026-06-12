"""生成式判分 (plan §2.5)：ES/RR/CLR + PS(改述泛化) + Loc(局部性)。规则判分 + 别名表。

口径=生成式 ES_b，**不等于** EasyEdit 自带 rewrite_acc（logits 口径），两者永不混排（CLAUDE.md 约束 4）。
消费 edit_loop 落的探针行：efficacy / para0,para1 / locality / open（open 仅供人工审计，不入指标）。
"""
import json, collections


def hit(text, target, aliases):
    cands = [target] + aliases.get(target, [])
    t = (text or "").lower()
    return any(c and c.lower() in t for c in cands)   # 跳过 None/空候选（如 zsRE o_old 缺失）


def first_mention(text, target, aliases):
    """target(含别名)在 text 中最早出现的字符位置；无则 -1。大小写不敏感。"""
    t = (text or "").lower()
    best = -1
    for c in [target] + aliases.get(target, []):
        if not c:
            continue
        i = t.find(c.lower())
        if i >= 0 and (best < 0 or i < best):
            best = i
    return best


def flip_analysis(text, o_new, o_old, aliases):
    """立场翻转分析 (plan §2.5 FlipPoint；07 教训：子串判分分不出"先新后旧"翻转，
    如『Mars. However…Jupiter』子串同时命中 o_new/o_old，纯 hit 判不出落定立场)。

    返回 dict：
      first/last ∈ {'new','old',None}  —— 链内/答案里最先/最后出现的立场（last=落定立场）
      flipped: bool                    —— o_new 与 o_old 都出现（链内立场翻转过）
      flip_pos: int|None               —— 翻转点=对立项(后现者)首现的字符位（机理 FlipPoint 的字符级近似）
      new_pos/old_pos: int|None        —— 各自首现位
    用途：CoT 上跑=机理片段归因(Phase 3 找回退发生位)；answer 上跑=首段断言判分 + 审计字段。
    """
    np_ = first_mention(text, o_new, aliases)
    op_ = first_mention(text, o_old, aliases)
    has_new, has_old = np_ >= 0, op_ >= 0
    none = {"first": None, "last": None, "flipped": False, "flip_pos": None, "new_pos": None, "old_pos": None}
    if not has_new and not has_old:
        return none
    if has_new and not has_old:
        return {**none, "first": "new", "last": "new", "new_pos": np_}
    if has_old and not has_new:
        return {**none, "first": "old", "last": "old", "old_pos": op_}
    first = "new" if np_ < op_ else "old"        # 先现者=首段立场
    last = "new" if np_ > op_ else "old"          # 后现者=落定立场（与 first 相反）
    return {"first": first, "last": last, "flipped": True,
            "flip_pos": max(np_, op_), "new_pos": np_, "old_pos": op_}


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
    esf = collections.Counter(); flip = collections.Counter()
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
                fa = flip_analysis(e["answer"], o_new, o_old, aliases)   # 07 教训：首段断言 + 翻转
                esf[b] += (fa["first"] == "new")     # ESf: 答案首段立场=编辑（容忍后续翻转）
                flip[b] += fa["flipped"]             # Flip: 答案内 o_new/o_old 都现（先新后旧/先旧后新）
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
    # ESf(首段断言) vs ES(严格)的差 + Flip 揭示"答案内越想越退"（首段是编辑、落定回旧）。
    return {b: {"ES": rate(es[b], n[b]), "RR": rr[b] / max(n_b0, 1), "CLR": rate(clr[b], n[b]),
                "ESf": rate(esf[b], n[b]), "Flip": rate(flip[b], n[b]),
                "PS": rate(ps[b], ps_n[b]), "Loc": rate(loc[b], loc_n[b]),
                "n": n[b], "n_para": ps_n[b], "n_loc": loc_n[b]}
            for b in sorted(set(n) | set(ps_n) | set(loc_n))}


def _indicators(jsonl_path, cases, aliases, decode):
    """逐 case 指标（供 bootstrap 重采样，plan §2.5「按编辑条目重采样」）。
    返回 budgets + 三个 dict：eff_es[b]/eff_clr[b]（该档 efficacy 案例的 0/1），rr_rev[b]（B0 成功案例的回退 0/1）。"""
    cmap = {c["case_id"]: c for c in cases}
    by = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(list)))
    for line in open(jsonl_path):
        r = json.loads(line)
        p = r.get("probe")
        if p and r.get("decode", "greedy") == decode:
            by[r["case_id"]][r["budget"]][p].append(r)
    eff_es = collections.defaultdict(list); eff_clr = collections.defaultdict(list)
    rr_rev = collections.defaultdict(list)
    for cid, buds in by.items():
        c = cmap[cid]; o_new, o_old = c["o_new"], c["o_old"]
        eff0 = buds.get("B0", {}).get("efficacy", [])
        b0ok = (bool(eff0) and hit(eff0[0]["answer"], o_new, aliases)
                and not hit(eff0[0]["answer"], o_old, aliases))
        for b, probe_rows in buds.items():
            for e in probe_rows.get("efficacy", []):
                eff_es[b].append(1 if (hit(e["answer"], o_new, aliases)
                                       and not hit(e["answer"], o_old, aliases)) else 0)
                eff_clr[b].append(1 if hit(e["cot"], o_old, aliases) else 0)
                if b0ok:
                    rr_rev[b].append(1 if hit(e["answer"], o_old, aliases) else 0)
    budgets = sorted(set(eff_es) | set(eff_clr) | set(rr_rev))
    return budgets, eff_es, eff_clr, rr_rev


def score_bootstrap(jsonl_path, cases, aliases, n_boot=10000, seed=42, decode="greedy", ci=0.95):
    """ES/RR/CLR 的 95% bootstrap CI（plan §2.5：按编辑条目重采样，n=10,000）。纯 stdlib(无 numpy)，
    与 metrics 的零重依赖一致。返回 {budget: {metric: (point, lo, hi)|None}}。
    ES/CLR 在该档 efficacy 案例上重采样；RR 在 B0 成功(b0ok)案例上重采样（分子分母同采）。
    单一 rng（seed 固定）顺序抽样 → 可复现；不同 metric 用不同抽样（顺序推进），互不耦合。"""
    import random
    budgets, eff_es, eff_clr, rr_rev = _indicators(jsonl_path, cases, aliases, decode)
    rng = random.Random(seed)
    lo_q, hi_q = (1 - ci) / 2, (1 + ci) / 2

    def ci_of(xs):
        m = len(xs)
        if not m:
            return None
        point = sum(xs) / m
        means = sorted(sum(xs[rng.randrange(m)] for _ in range(m)) / m for _ in range(n_boot))
        return (point, means[int(lo_q * n_boot)], means[min(int(hi_q * n_boot), n_boot - 1)])

    return {b: {"ES": ci_of(eff_es[b]), "CLR": ci_of(eff_clr[b]), "RR": ci_of(rr_rev[b])}
            for b in budgets}
