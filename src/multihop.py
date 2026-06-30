"""E-MULTIHOP/W3 · 多跳 2-hop runner —— base-floor 门 + hop-scorer(共用)。

问题升级:RQ1 从"token 匹配被编辑宾语"→**客观下游答案**(hop_answer_new vs hop_answer_old)。
- `--mode base`(未编辑,bf16 NaN-safe,单卡):对干净池逐 case 生成 hop_q 答案 → 评 hits_new/old。
  **门**:基座靠先验就答出 hop_answer_old(或 new)的 case = 先验主导(Trump/Galilee 尾)→ 必须丢,否则 null 无信息。
- 编辑态 2-hop:走现有 edit_loop(已加 hop probe)+ run_pilot,probes=[hop] → 本模块 `--mode score` 评其输出。
判分:_without_subject 去主体 + metrics.hit(对 hop_answer_new/old 字符串,词边界)。预注册三结局见 depth-plan.md。

用法:
  # base-floor 门(H200/4090,未编辑;先 Llama-8B):
  WHYAAAI_MODEL=$W/models/DeepSeek-R1-Distill-Llama-8B python src/multihop.py base \
      --pool data/mquake_clean.jsonl --budgets B0 B3 --rank $r --world 8 --out results/mh/base_8b_r$r.jsonl
  python src/multihop.py gate --base 'results/mh/base_8b_r*.jsonl' --pool data/mquake_clean.jsonl --out data/mquake_gated.jsonl
  # 编辑态 2-hop(run_pilot on mquake config,probes=[hop])后:
  python src/multihop.py score --edited 'results/probe/r1llama8b_ROME_mh*_r*of*.jsonl' --pool data/mquake_gated.jsonl
"""
import argparse, glob, json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics


def _fold(s):
    """NFKD 去变音符 + 小写(Grabar-Kitarović→grabar-kitarovic),修 hop_answer_new 漏检。"""
    return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()


def _hop_hit(ans, target):
    """hop 答案匹配:去变音符后词边界。短目标(<4 字,如 'Lu')要求紧邻上下文,防裸 \\bLu\\b 假阳。"""
    a, t = _fold(ans), _fold(target)
    if not t:
        return False
    if len(t) < 4:                       # 短码:'state Lu'/'in Lu'/'Lu was'… 才算,不接受散落的 Lu
        return bool(re.search(r"\b(?:of|in|the|at|state|city|town|to|from)\s+" + re.escape(t) + r"\b", a)
                    or re.search(r"\b" + re.escape(t) + r"\b\s*(?:is|was|,|\.|;|:|\))", a))
    return bool(re.search(r"\b" + re.escape(t) + r"\b", a))


def _score_one(ans, s, han, hao):
    # 不去主体(hop 答案≠编辑 subject);去变音符 + 短目标守护(panel wq9e477xn)。
    return int(_hop_hit(ans, han)), int(_hop_hit(ans, hao))


def cmd_base(args):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import think_budget
    from r1_tokenizer import fix_r1_tokenizer
    model_name = os.environ.get("WHYAAAI_MODEL") or args.model
    dtype = {"float32": torch.float32, "bfloat16": torch.bfloat16}.get(os.environ.get("WHYAAAI_DTYPE", "bfloat16"), torch.bfloat16)
    dev = f"cuda:{args.rank}" if args.world > 1 else "cuda"
    tok = fix_r1_tokenizer(AutoTokenizer.from_pretrained(model_name), model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=dtype).to(dev).eval()
    pool = [json.loads(l) for l in open(args.pool) if l.strip()]
    done = set()
    if os.path.exists(args.out):
        for l in open(args.out):
            try:
                d = json.loads(l); done.add((d.get("case_id"), d.get("budget")))
            except Exception:
                pass
    print(f"[multihop base] model={model_name} dtype={dtype} dev={dev} pool={len(pool)} budgets={args.budgets}")
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "a") as f:
        for i, c in enumerate(pool):
            if i % args.world != args.rank:
                continue
            for b in args.budgets:
                if (c["case_id"], b) in done:
                    continue
                try:
                    _, ans, _ = think_budget.generate_with_budget(model, tok, c["hop_q"], b, suppress=None, answer_cap=args.answer_cap)
                    hn, ho = _score_one(ans, c.get("s"), c["hop_answer_new"], c["hop_answer_old"])
                    rec = {"case_id": c["case_id"], "budget": b, "hits_new": hn, "hits_old": ho, "answer": ans}
                except Exception as e:
                    rec = {"case_id": c["case_id"], "budget": b, "error": repr(e)}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
    print(f"# → {args.out}")


def _load(pat):
    rows = []
    for sh in sorted(glob.glob(pat)):
        for l in open(sh):
            l = l.strip()
            if l:
                rows.append(json.loads(l))
    return rows


def gate_keep(base, pool):
    """纯函数(可单测):丢基座未编辑就已答出 hop_answer_old/new 的 case(先验主导)→ 留信息残池。
    返回 (keep_list, n_eval, n_bad)。"""
    bad, evaled = set(), set()
    for d in base:
        if d.get("error"):
            continue
        evaled.add(d["case_id"])
        if d.get("hits_old") or d.get("hits_new"):     # 基座未编辑就已答出新/旧 → 先验主导/不可分,丢
            bad.add(d["case_id"])
    keep = [c for cid, c in pool.items() if cid not in bad and cid in evaled]
    return keep, len(evaled), len(bad)


def cmd_gate(args):
    """未编辑 base-floor:丢基座靠先验就答出 hop_answer_old(或 new)的 case → 留信息残池。"""
    base = _load(args.base)
    pool = {c["case_id"]: c for c in (json.loads(l) for l in open(args.pool))}
    keep, n_eval, n_bad = gate_keep(base, pool)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        for c in keep:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"# base-floor 门:评估 {n_eval} case,先验主导(基座已答新/旧)丢 {n_bad} → 留 {len(keep)} 信息残池 → {args.out}")
    print(f"# 残池 = 基座答不出、只有编辑+推理才决定 hop 答案的 case(W3 真正有信息的 population)")


def recut_keep(rows, max_frac=0.30, min_n=20):
    """丢退化-new 模板(panel wq9e477xn):某 relation 的最常见 hop_answer_new 占比 > max_frac 且 n>=min_n
    = new-gold 塌缩(如 P140 宗教→Lu/Epworth 占 45%)→ 测的不是多样传播 → 丢出 headline。返回 (keep, dropped_relations)。"""
    from collections import Counter
    byr = {}
    for x in rows:
        byr.setdefault(x.get("r"), []).append(x)
    drop = set()
    for r, v in byr.items():
        c = Counter(str(x["hop_answer_new"]) for x in v)
        if len(v) >= min_n and c.most_common(1)[0][1] / len(v) > max_frac:
            drop.add(r)
    keep = [x for x in rows if x.get("r") not in drop]
    return keep, sorted(drop)


def cmd_recut(args):
    rows = [json.loads(l) for l in open(args.pool)]
    keep, drop = recut_keep(rows, args.max_frac, args.min_n)
    with open(args.out, "w") as f:
        for c in keep:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"# recut:{len(rows)}→{len(keep)}(丢退化-new relation {drop}:最常见 new-gold 占比>{args.max_frac})→ {args.out}")


def _boot_paired(flags, B=10000, seed=42):
    import random
    if not flags:
        return [None, None]
    rng = random.Random(seed); n = len(flags)
    xs = sorted(sum(flags[rng.randrange(n)] for _ in range(n)) / n for _ in range(B))
    return [round(xs[int(0.025 * B)], 3), round(xs[int(0.975 * B)], 3)]


def _score_block(cases_byid, recs, label):
    """对一组 case 算 b0_prop 门 + propagation-erosion + {stays/flips/neither} + 陈旧 revert 括号。"""
    by = {}                                   # cid -> {budget: (hn,ho)}
    for d in recs:
        c = cases_byid.get(d["case_id"])
        if not c:
            continue
        hn, ho = _score_one(d.get("answer"), c.get("s"), c["hop_answer_new"], c["hop_answer_old"])
        by.setdefault(d["case_id"], {})[d.get("budget")] = (hn, ho)
    hopES = {}                                # 边际 hop_ES per budget(全 case)
    for cid, bd in by.items():
        for b, (hn, ho) in bd.items():
            hopES.setdefault(b, []).append(hn and not ho)
    hopES = {b: round(sum(v) / len(v), 3) for b, v in hopES.items()}
    # b0_prop 门 = 编辑在 B0 传到 2-hop(答新且不旧)= headline b0ok 的多跳镜像
    b0 = [cid for cid, bd in by.items() if "B0" in bd and bd["B0"][0] and not bd["B0"][1]]
    out = {"label": label, "n_all": len(by), "hop_ES_marginal": hopES, "n_b0_prop": len(b0)}
    if b0 and "B3" in next(iter(by.values()), {}):
        lost = [0 if (by[c].get("B3", (0, 0))[0]) else 1 for c in b0]          # B3 丢了 hop_answer_new = 传播被侵蚀
        stays = sum(1 for c in b0 if by[c].get("B3", (0, 0))[0])
        flips = sum(1 for c in b0 if (not by[c].get("B3", (0, 0))[0]) and by[c].get("B3", (0, 0))[1])
        neither = len(b0) - stays - flips
        out["propagation_erosion_B0toB3"] = {"rate": round(sum(lost) / len(b0), 3), "ci": _boot_paired(lost),
                                             "decomp": {"stays_new": stays, "flips_to_old": flips, "neither": neither}}
        # 陈旧 revert 括号(MQuAKE ~2021 gold,不领先报)
        rr = sum(1 for c in b0 if by[c].get("B3", (0, 0))[1]) / len(b0)
        rrs = sum(1 for c in b0 if by[c].get("B3", (0, 0))[1] and not by[c].get("B3", (0, 0))[0]) / len(b0)
        out["stale_revert_bracket_B3"] = {"hop_RR": round(rr, 3), "hop_RRs": round(rrs, 3), "_note": "对 MQuAKE 陈旧下游 gold,不领先/不入 abstract"}
    return out


def cmd_score(args):
    """编辑态 2-hop:b0_prop 门(编辑 B0 传到 2-hop)上的 propagation-erosion(B0→B3 丢 hop_answer_new)+ 分解 + per-template。"""
    pool = {c["case_id"]: c for c in (json.loads(l) for l in open(args.pool))}
    recs = [d for d in _load(args.edited) if d.get("probe") == "hop" and d.get("decode", "greedy") == "greedy" and not d.get("error")]
    overall = _score_block(pool, recs, "POOLED(template-unweighted)")
    print(f"# 编辑态 2-hop · n_pool={len(pool)}")
    print(f"# [{overall['label']}] n_b0_prop={overall['n_b0_prop']}/{overall['n_all']}  hop_ES@budget={overall['hop_ES_marginal']}")
    pe = overall.get("propagation_erosion_B0toB3")
    if pe:
        print(f"#   ★propagation-erosion B0→B3 = {pe['rate']} {pe['ci']}  分解{pe['decomp']}")
        print(f"#   (次/陈旧)revert 括号 {overall['stale_revert_bracket_B3']['hop_RR']}/{overall['stale_revert_bracket_B3']['hop_RRs']}")
    if overall["n_b0_prop"] < 40:
        print(f"#   ⚠ n_b0_prop<40 → bounded-null/power 结果,非定量 erosion(可能 8B 多跳传播弱→考虑 32B,见 depth-plan 升级判据)")
    # per-template(relation)
    bytmpl = {}
    for cid, c in pool.items():
        bytmpl.setdefault(c.get("r"), {})[cid] = c
    per = {}
    print(f"# per-template(relation):")
    for r, cs in sorted(bytmpl.items(), key=lambda kv: -len(kv[1])):
        blk = _score_block(cs, [d for d in recs if d["case_id"] in cs], f"r={r}")
        per[r] = blk
        pe = blk.get("propagation_erosion_B0toB3")
        es0 = blk["hop_ES_marginal"].get("B0")
        print(f"#   r={r:<6} n={blk['n_all']:>3} hop_ES@B0={es0}  b0_prop={blk['n_b0_prop']:>3}  "
              f"{'prop-eros='+str(pe['rate'])+' '+str(pe['ci']) if pe else '(b0_prop 不足)'}")
    res = {"pooled": overall, "per_template": per, "_estimand": "propagation-erosion = 编辑在 B0 传到 2-hop 的 case 中,B3 思考后丢失 hop_answer_new 的比例(配对);陈旧 revert 仅作次要括号。"}
    if args.out:
        json.dump(res, open(args.out, "w"), ensure_ascii=False, indent=2)
        print(f"# → {args.out}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    b = sub.add_parser("base"); b.add_argument("--pool", default="data/mquake_clean.jsonl")
    b.add_argument("--model", default=None); b.add_argument("--budgets", nargs="+", default=["B0", "B3"])
    b.add_argument("--rank", type=int, default=0); b.add_argument("--world", type=int, default=1)
    b.add_argument("--answer_cap", type=int, default=512); b.add_argument("--out", required=True)
    g = sub.add_parser("gate"); g.add_argument("--base", required=True); g.add_argument("--pool", default="data/mquake_clean.jsonl"); g.add_argument("--out", default="data/mquake_gated.jsonl")
    rc = sub.add_parser("recut"); rc.add_argument("--pool", default="data/mquake_gated.jsonl"); rc.add_argument("--out", default="data/mquake_gated_clean.jsonl")
    rc.add_argument("--max-frac", dest="max_frac", type=float, default=0.30); rc.add_argument("--min-n", dest="min_n", type=int, default=20)
    s = sub.add_parser("score"); s.add_argument("--edited", required=True); s.add_argument("--pool", default="data/mquake_gated_clean.jsonl"); s.add_argument("--out", default=None)
    args = ap.parse_args()
    {"base": cmd_base, "gate": cmd_gate, "recut": cmd_recut, "score": cmd_score}[args.mode](args)


if __name__ == "__main__":
    main()
