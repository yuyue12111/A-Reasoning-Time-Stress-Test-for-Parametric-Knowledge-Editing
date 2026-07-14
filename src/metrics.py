"""生成式判分 (plan §2.5)：ES/RR/CLR + PS(改述泛化) + Loc(局部性)。规则判分 + 别名表。

口径=生成式 ES_b，**不等于** EasyEdit 自带 rewrite_acc（logits 口径），两者永不混排（CLAUDE.md 约束 4）。
消费 edit_loop 落的探针行：efficacy / para0,para1 / locality / open（open 仅供人工审计，不入指标）。
"""
import json, collections, re


_BAD_ALIAS = re.compile(r"^[\W\d_]*$")   # 纯标点/数字/空 → 丢

def _safe_cands(target, aliases):
    """候选 = target + 别名，但【丢掉长度<4 的别名】(ISO 国家码 IN/FR/ES/NO/W、语言码 fi/it/zh、
    emoji 旗 🇫🇮 等)。这些在纯 substring 判定下假阳泛滥：'in'(India)命中 'within/international'、
    'it'(Italian)命中 'it/with'、'es'(Spain)命中 'uses/cases'、'W'(Vienna)命中任何含 w 的文本
    → ES/RR/CLR 共用的 hit() 被系统性灌水(国家/语言类 o_old 的 CLR/RR≈100% 全是伪命中)。
    target 全名永远保留(即便短，如 'IBM')；别名要么 ≥4 字符、要么仍非纯标点。"""
    out = [target]
    out += [a for a in aliases.get(target, [])
            if a and len(str(a).strip()) >= 4 and not _BAD_ALIAS.match(str(a))]
    return out


def _wb(cand):
    """词边界正则 r'\bcand\b'（大小写不敏感由 text 预 lower 保证）。替换 substring `in`，
    修 'Microsoft' 误被 'ms' 命中 'items'、'Asia' 误被子串命中等。"""
    return re.compile(r"\b" + re.escape(str(cand).lower().strip()) + r"\b")


def hit(text, target, aliases):
    t = (text or "").lower()
    return any(_wb(c).search(t) for c in _safe_cands(target, aliases) if c)   # 词边界 + 丢短码


def hit_count(text, target, aliases):
    """target(含安全别名)在 text 中的词边界出现**总次数**(跨安全候选求和；口径与 hit 完全一致，
    只是数次数而非 0/1)。Cap1 的 CLR 密度分子——量『旧知识在链里浮现多少次』而非『是否浮现』，
    区分「能力=更高泄漏率」与「能力=只是链更长(表面积更大)」。别名重叠极少，求和近似出现次数。"""
    t = (text or "").lower()
    return sum(len(_wb(c).findall(t)) for c in _safe_cands(target, aliases) if c)


def _without_subject(text, subject):
    """判分前挖掉对主体的复述。o_old/o_new 常是主体子串（如主体 'Miami International Film
    Festival' 含 o_old 'Miami'）——模型推理开头复述题目会令 CLR/RR 假阳、ES 的『不含 o_old』假阴
    （6.16 eyeball 实锤：3/3 CLR 命中都是主体复述而非旧知识回忆）。大小写不敏感删除主体整串，
    只去复述、保留真正的『located in Miami』旧事实回忆；subject 空（如旧 mock 无 s 字段）则原样返回。"""
    if not text or not subject:
        return text or ""
    return re.sub(re.escape(subject), " ", text, flags=re.IGNORECASE)


def first_mention(text, target, aliases):
    """target(含安全别名)在 text 中最早出现的字符位置；无则 -1。词边界 + 丢短码(见 _safe_cands)。"""
    t = (text or "").lower()
    best = -1
    for c in _safe_cands(target, aliases):
        if not c:
            continue
        m = _wb(c).search(t)
        if m and (best < 0 or m.start() < best):
            best = m.start()
    return best


def last_mention(text, target, aliases):
    """target(含别名)在 text 中最晚出现的字符位置；无则 -1。大小写不敏感。
    与 first_mention 配套：判『答案落定立场』须比【末次】提及，不能只比首现序——
    否则『new→old→new』会因 old 的首现晚于 new 而被误判为最终回退。
    词边界 + 丢短码同 hit。"""
    t = (text or "").lower()
    best = -1
    for c in _safe_cands(target, aliases):
        if not c:
            continue
        last = -1
        for m in _wb(c).finditer(t):
            last = m.start()
        if last > best:
            best = last
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
    nl_ = last_mention(text, o_new, aliases)
    ol_ = last_mention(text, o_old, aliases)
    last = "new" if nl_ > ol_ else "old"           # 末次提及者=落定立场（不必与 first 相反）
    return {"first": first, "last": last, "flipped": True,
            "flip_pos": max(np_, op_), "new_pos": np_, "old_pos": op_}


def score(jsonl_path, cases, aliases, decode="greedy"):
    """每预算档返回 ES/RR/CLR + PS + Loc 及各自分母 n/n_para/n_loc。

    decode 过滤解码臂（默认 "greedy"——go/no-go 主口径，结论须在 greedy 下成立 sumandplan §6.3）；
    无 decode 字段的旧行视为 greedy（向后兼容）。传 decode="sample" 可单独看采样臂。

    指标语义 (plan §2.5)：
      ES  = 1{answer 命中 o_new 且不含 o_old}              （efficacy 探针）
      RR  = P(answer 含 o_old | B0 成功)              loose 口径=上界（含"守住+顺带提旧"的假阳）
      RRs = P(answer 含 o_old 且不含 o_new | B0 成功)   strict 口径=下界（ES 镜像，最干净的回退）
      CLR = 1{cot 含 o_old}                                 （链内旧知识泄漏，efficacy 的 cot）
      PS  = 1{para_answer 命中 o_new 且不含 o_old}          （改述泛化/portability，para* 探针）
      Loc = 1{locality_answer **不含** o_new}               （仅衡量目标值未直接泄漏到邻域）
            —— 该指标不检查邻域答案是否正确/与编辑前一致；拒答、错答、乱码也可能得 1。
               因此科学命名应为 target-value non-leakage，不能单独宣称完整 locality preservation。
               层选择纪律 plan v1.18/§7：
               在 Loc≥85% 前提下取生成式 B0 ES 最高层；旧 ES≥90% 是 rewrite_acc 数字误植。
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
    rr_n = collections.Counter()      # RR 分母按**行**：b0ok 案例的每条 efficacy 生成
    rrs = collections.Counter()       # RRs=严口径回退：答案含旧【且不含新】(ES 镜像,排除"守住+顺带提旧")
    # （采样臂每 case 有多个 seed 行，分母不可用案例数 n_b0，否则分子按行/分母按案例 → RR 虚高 >1）
    for cid, buds in by.items():
        c = cmap[cid]; o_new, o_old = c["o_new"], c["o_old"]
        clean = lambda t: _without_subject(t, c.get("s") or "")    # 挖主体复述（见 _without_subject）
        eff0 = buds.get("B0", {}).get("efficacy", [])
        a0 = clean(eff0[0]["answer"]) if eff0 else ""
        b0ok = (bool(eff0) and hit(a0, o_new, aliases) and not hit(a0, o_old, aliases))
        for b, probe_rows in buds.items():
            for e in probe_rows.get("efficacy", []):
                ans, cot = clean(e["answer"]), clean(e["cot"])
                n[b] += 1
                es[b] += hit(ans, o_new, aliases) and not hit(ans, o_old, aliases)
                clr[b] += hit(cot, o_old, aliases)
                fa = flip_analysis(ans, o_new, o_old, aliases)   # 07 教训：首段断言 + 翻转（主体已挖）
                esf[b] += (fa["first"] == "new")     # ESf: 答案首段立场=编辑（容忍后续翻转）
                flip[b] += fa["flipped"]             # Flip: 答案内 o_new/o_old 都现（先新后旧/先旧后新）
                if b0ok:                             # 条件回退（plan §2.5）：分母分子都按行
                    rr_n[b] += 1
                    rr[b] += bool(hit(ans, o_old, aliases))                                       # loose(上界)
                    rrs[b] += bool(hit(ans, o_old, aliases) and not hit(ans, o_new, aliases))     # strict(下界)
            for pname, rows in probe_rows.items():
                if pname.startswith("para"):         # para0/para1（改述泛化）
                    for pr in rows:
                        pa = clean(pr["answer"])
                        ps_n[b] += 1
                        ps[b] += hit(pa, o_new, aliases) and not hit(pa, o_old, aliases)
            for lr in probe_rows.get("locality", []):
                loc_n[b] += 1
                loc[b] += not hit(lr["answer"], o_new, aliases)   # 编辑未泄漏到邻域=局部性保持

    rate = lambda num, den: (num / den if den else None)
    # ESf(首段断言) vs ES(严格)的差 + Flip 揭示"答案内越想越退"（首段是编辑、落定回旧）。
    return {b: {"ES": rate(es[b], n[b]), "RR": rate(rr[b], rr_n[b]), "RRs": rate(rrs[b], rr_n[b]), "CLR": rate(clr[b], n[b]),
                "ESf": rate(esf[b], n[b]), "Flip": rate(flip[b], n[b]),
                "PS": rate(ps[b], ps_n[b]), "Loc": rate(loc[b], loc_n[b]),
                "n": n[b], "rr_n": rr_n[b], "n_para": ps_n[b], "n_loc": loc_n[b]}
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
        clean = lambda t: _without_subject(t, c.get("s") or "")    # 与 score() 同口径挖主体
        eff0 = buds.get("B0", {}).get("efficacy", [])
        a0 = clean(eff0[0]["answer"]) if eff0 else ""
        b0ok = (bool(eff0) and hit(a0, o_new, aliases) and not hit(a0, o_old, aliases))
        for b, probe_rows in buds.items():
            for e in probe_rows.get("efficacy", []):
                ans, cot = clean(e["answer"]), clean(e["cot"])
                eff_es[b].append(1 if (hit(ans, o_new, aliases)
                                       and not hit(ans, o_old, aliases)) else 0)
                eff_clr[b].append(1 if hit(cot, o_old, aliases) else 0)
                if b0ok:
                    rr_rev[b].append(1 if hit(ans, o_old, aliases) else 0)
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


def _indicators_by_case(jsonl_path, cases, aliases, decode):
    """Like _indicators but keeps each case's rows grouped (does NOT flatten across cases).
    For SAMPLING arms (temp>0, multi-seed) a case contributes several correlated chains;
    the row-level score_bootstrap resamples those rows as if independent → pseudo-replication
    → CI too narrow. This grouping feeds score_bootstrap_clustered, whose resampling unit is
    the case (block), not the row.
    Returns budgets, and three per-budget dicts {case_id: [0/1 indicators for that case's rows]}
    for ES / CLR / RR. b0ok gate uses B0 first-row (eff0[0]) IDENTICALLY to _indicators, so the
    pooled point estimate matches score_bootstrap exactly — only the CI changes. ⚠eff0[0] is
    seed/file-order dependent on sampling arms; recorded as a caveat, not changed (changing it
    would move the reported point estimate)."""
    cmap = {c["case_id"]: c for c in cases}
    by = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(list)))
    for line in open(jsonl_path):
        r = json.loads(line)
        p = r.get("probe")
        if p and r.get("decode", "greedy") == decode:
            by[r["case_id"]][r["budget"]][p].append(r)
    es_by = collections.defaultdict(dict); clr_by = collections.defaultdict(dict)
    rr_by = collections.defaultdict(dict)
    for cid, buds in by.items():
        c = cmap[cid]; o_new, o_old = c["o_new"], c["o_old"]
        clean = lambda t: _without_subject(t, c.get("s") or "")
        eff0 = buds.get("B0", {}).get("efficacy", [])
        a0 = clean(eff0[0]["answer"]) if eff0 else ""
        b0ok = (bool(eff0) and hit(a0, o_new, aliases) and not hit(a0, o_old, aliases))
        for b, probe_rows in buds.items():
            es_l = []; clr_l = []; rr_l = []
            for e in probe_rows.get("efficacy", []):
                ans, cot = clean(e["answer"]), clean(e["cot"])
                es_l.append(1 if (hit(ans, o_new, aliases) and not hit(ans, o_old, aliases)) else 0)
                clr_l.append(1 if hit(cot, o_old, aliases) else 0)
                if b0ok:
                    rr_l.append(1 if hit(ans, o_old, aliases) else 0)
            if es_l:  es_by[b][cid] = es_l
            if clr_l: clr_by[b][cid] = clr_l
            if rr_l:  rr_by[b][cid] = rr_l
    budgets = sorted(set(es_by) | set(clr_by) | set(rr_by))
    return budgets, es_by, clr_by, rr_by


def score_bootstrap_clustered(jsonl_path, cases, aliases, n_boot=10000, seed=42, decode="greedy", ci=0.95):
    """CASE-CLUSTER bootstrap CI for ES/RR/CLR (resampling unit = case, not row).
    Use this for SAMPLING arms: same-case multi-seed chains are correlated, so the row-level
    score_bootstrap under-counts variance (pseudo-replication → CI too narrow). Here we resample
    CASES with replacement (m draws over the m observed cases) and pool ALL rows of each drawn
    case, then take the pooled proportion. The point estimate = pooled mean over every row = the
    exact same number score_bootstrap reports; only the interval widens to reflect the true number
    of independent clusters (cases, not seed-rows). For greedy arms (1 row/case) this returns the
    same interval as score_bootstrap (clusters==rows). Pairs with drop_bootstrap, which is already
    case-level (rows[0] per case) and unaffected by this bug. See gap-review 必2 / 硬伤1."""
    import random
    budgets, es_by, clr_by, rr_by = _indicators_by_case(jsonl_path, cases, aliases, decode)
    rng = random.Random(seed)
    lo_q, hi_q = (1 - ci) / 2, (1 + ci) / 2

    def ci_of(case_map):
        cids = list(case_map)
        if not cids:
            return None
        all_rows = [x for cid in cids for x in case_map[cid]]
        point = sum(all_rows) / len(all_rows)
        m = len(cids)
        means = []
        for _ in range(n_boot):
            num = den = 0
            for _ in range(m):
                rows = case_map[cids[rng.randrange(m)]]
                num += sum(rows); den += len(rows)
            means.append(num / den if den else 0.0)
        means.sort()
        return (point, means[int(lo_q * n_boot)], means[min(int(hi_q * n_boot), n_boot - 1)],
                {"n_cases": m, "n_rows": len(all_rows)})

    return {b: {"ES": ci_of(es_by[b]), "CLR": ci_of(clr_by[b]), "RR": ci_of(rr_by[b])}
            for b in budgets}


def _es_by_case(jsonl_path, cases, aliases, decode="greedy"):
    """{case_id: {budget: 0/1}} 的 efficacy ES（去主体口径），供配对降幅 bootstrap。"""
    cmap = {c["case_id"]: c for c in cases}
    by = collections.defaultdict(lambda: collections.defaultdict(list))
    for line in open(jsonl_path):
        r = json.loads(line)
        if r.get("probe") == "efficacy" and r.get("decode", "greedy") == decode:
            by[r["case_id"]][r["budget"]].append(r)
    es = collections.defaultdict(dict)
    for cid, buds in by.items():
        c = cmap[cid]; o_new, o_old = c["o_new"], c["o_old"]
        clean = lambda t: _without_subject(t, c.get("s") or "")
        for b, rows in buds.items():
            ans = clean(rows[0]["answer"])
            es[cid][b] = 1 if (hit(ans, o_new, aliases) and not hit(ans, o_old, aliases)) else 0
    return es


def drop_bootstrap(jsonl_path, cases, aliases, base="B0", n_boot=10000, seed=42, decode="greedy", ci=0.95):
    """ES 降幅 ES(base)−ES(b) 的**配对** bootstrap CI（按 case 重采样，同 case 的两档同采）。
    比边际 CI 更准地判"越想越退"显著性：配对消除 case 间方差（两个边际 CI 重叠 ≠ 降幅不显著）。
    返回 {b: (point, lo, hi)}；point>0 = 思考后 ES 下降。降幅 CI 全 >0 → 显著回退。"""
    import random
    es = _es_by_case(jsonl_path, cases, aliases, decode)
    rng = random.Random(seed)
    lo_q, hi_q = (1 - ci) / 2, (1 + ci) / 2
    budgets = sorted({b for v in es.values() for b in v} - {base})
    out = {}
    for b in budgets:
        pairs = [(es[cid][base], es[cid][b]) for cid in es if base in es[cid] and b in es[cid]]
        m = len(pairs)
        if not m:
            out[b] = None; continue
        point = sum(a0 - ab for a0, ab in pairs) / m
        means = sorted(sum((lambda p: p[0] - p[1])(pairs[rng.randrange(m)])
                           for _ in range(m)) / m for _ in range(n_boot))
        out[b] = (point, means[int(lo_q * n_boot)], means[min(int(hi_q * n_boot), n_boot - 1)])
    return out
