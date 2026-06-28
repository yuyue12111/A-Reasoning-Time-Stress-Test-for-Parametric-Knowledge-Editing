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
import argparse, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics

ALIASES_EMPTY = {}        # hop 答案是下游实体,无别名表 → 纯词边界匹配字符串


def _score_one(ans, s, han, hao):
    # 不去主体:hop 答案是下游实体(≠ 编辑 subject),无主体复述污染;且去主体在 subject⊂hop_answer 时会误删。
    a = ans or ""
    hn = bool(metrics.hit(a, han, ALIASES_EMPTY))
    ho = bool(metrics.hit(a, hao, ALIASES_EMPTY))
    return int(hn), int(ho)


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


def cmd_score(args):
    """编辑态 2-hop 打分(run_pilot hop probe 输出):per-budget 2-hop ES(hits_new & not old)/ revert(hits_old)/ ES-drop。"""
    pool = {c["case_id"]: c for c in (json.loads(l) for l in open(args.pool))}
    recs = [d for d in _load(args.edited) if d.get("probe") == "hop" and d.get("decode", "greedy") == "greedy"]
    by = {}
    for d in recs:
        c = pool.get(d["case_id"])
        if not c:
            continue
        hn, ho = _score_one(d.get("answer"), c.get("s"), c["hop_answer_new"], c["hop_answer_old"])
        by.setdefault(d["budget"], []).append((hn, ho))
    print(f"# 编辑态 2-hop(n_pool={len(pool)}):per-budget hop-ES(下游答新且不旧)/ revert(下游答旧)")
    out = {}
    for b in sorted(by):
        v = by[b]; n = len(v)
        es = sum(hn and not ho for hn, ho in v) / n
        rev = sum(ho for _, ho in v) / n
        out[b] = {"n": n, "hop_ES": round(es, 3), "hop_revert": round(rev, 3)}
        print(f"#   {b}: n={n}  hop_ES={es:.3f}  hop_revert={rev:.3f}")
    if "B0" in out and "B3" in out:
        print(f"#   2-hop ES drop B0→B3 = {out['B0']['hop_ES']-out['B3']['hop_ES']:+.3f}（>0=多跳下思考也侵蚀编辑;预注册三结局见 depth-plan）")
    if args.out:
        json.dump(out, open(args.out, "w"), ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    b = sub.add_parser("base"); b.add_argument("--pool", default="data/mquake_clean.jsonl")
    b.add_argument("--model", default=None); b.add_argument("--budgets", nargs="+", default=["B0", "B3"])
    b.add_argument("--rank", type=int, default=0); b.add_argument("--world", type=int, default=1)
    b.add_argument("--answer_cap", type=int, default=512); b.add_argument("--out", required=True)
    g = sub.add_parser("gate"); g.add_argument("--base", required=True); g.add_argument("--pool", default="data/mquake_clean.jsonl"); g.add_argument("--out", default="data/mquake_gated.jsonl")
    s = sub.add_parser("score"); s.add_argument("--edited", required=True); s.add_argument("--pool", default="data/mquake_gated.jsonl"); s.add_argument("--out", default=None)
    args = ap.parse_args()
    {"base": cmd_base, "gate": cmd_gate, "score": cmd_score}[args.mode](args)


if __name__ == "__main__":
    main()
