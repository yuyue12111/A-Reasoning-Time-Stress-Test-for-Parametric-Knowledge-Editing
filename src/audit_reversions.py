"""go/no-go ② 审计（plan §Phase 1）：抽『B0 编对、B{budget} 倒回 o_old』的回退案例，
查回退是否发生在**反思/自验证片段**之后（链内 o_old 首现位之前是否有反思标记）。

  python src/audit_reversions.py --config experiments/pilot.yaml --editor ROME --budget B3 [--n 30]

判分口径与 metrics 一致（去主体复述：_without_subject）。输出：回退条数 + 反思归因率 +
逐条 CoT 片段（o_old 首现处上下文 + 之前最近的反思标记）。≥60% 归因反思 → go/no-go ② 成立。
反思标记是粗近似（字符级），人工复核仍以打印的 CoT 片段为准（与 analysis/09 校准同源）。
"""
import argparse, json, glob, os, re, collections, yaml
import metrics

# R1-Distill CoT 常见反思/自验证触发语（粗集；命中=回退前出现过"回头检查"信号）
REFLECT = re.compile(
    r"(wait\b|let me (re|double|check|verify|think|make sure)|reconsider|actually\b|"
    r"hold on|hmm\b|but wait|on second thought|re-?(check|examine|evaluate|read)|"
    r"is that (right|correct)|i (think|recall|remember)|in fact\b|"
    r"double[- ]check|correction|mistake|wrong\b)", re.I)


def load_efficacy(cfg, editor):
    ds = cfg["dataset"]
    pat = os.path.join(cfg["out_dir"], f"{cfg['model_tag']}_{editor}_{ds['tag']}_r*.jsonl")
    shards = sorted(glob.glob(pat))
    if not shards:
        raise SystemExit(f"无结果文件：{pat}")
    by = collections.defaultdict(dict)                # case_id -> budget -> efficacy row(greedy)
    for s in shards:
        for l in open(s):
            d = json.loads(l)
            if d.get("probe") == "efficacy" and d.get("decode", "greedy") == "greedy":
                by[d["case_id"]][d["budget"]] = d
    return by


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--editor", required=True)
    ap.add_argument("--budget", default="B3", help="审计的思考档（默认 B3=自然）")
    ap.add_argument("--n", type=int, default=30, help="打印前 n 条 CoT（默认 30，go/no-go 审计量）")
    ap.add_argument("--aliases", default="data/aliases.json")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    ds = cfg["dataset"]
    cf = {c["case_id"]: c for c in (json.loads(l) for l in open(ds.get("fallback_path", ds["path"])))}
    aliases = json.load(open(args.aliases))
    by = load_efficacy(cfg, args.editor)

    revs = []; loose = 0
    cats = collections.Counter()
    for cid, bud in by.items():
        c = cf.get(cid)
        b0, bb = bud.get("B0"), bud.get(args.budget)
        if not c or not b0 or not bb:
            continue
        o_new, o_old, subj = c["o_new"], c["o_old"], c.get("s") or ""
        clean = lambda t: metrics._without_subject(t, subj)
        a0 = clean(b0["answer"])
        b0ok = metrics.hit(a0, o_new, aliases) and not metrics.hit(a0, o_old, aliases)
        if not b0ok:
            continue                                   # 只看 B0 编对的（回退分母）
        ab = clean(bb["answer"])
        has_new = metrics.hit(ab, o_new, aliases)
        has_old = metrics.hit(ab, o_old, aliases)
        if not has_old:
            continue                                   # 答案根本没提旧 → 无任何回退
        loose += 1                                      # loose 口径：答案出现 o_old（旧 RR 口径，含编辑守住者）
        # 三分桶（按答案【末次】提及定落定立场，修 flip 首现序 bug）：
        #   clean = 只含旧不含新（ES 镜像，最干净的回退）
        #   churn = 新旧都含、末次落旧（先 churn 后真回退）
        #   held  = 新旧都含、末次落新（编辑守住，旧只末尾顺带提/被否定 → 旧 flip 口径误算成回退）
        lm_new = metrics.last_mention(ab, o_new, aliases)
        lm_old = metrics.last_mention(ab, o_old, aliases)
        cat = "clean" if not has_new else ("churn" if lm_old > lm_new else "held")
        cats[cat] += 1
        cot = clean(bb["cot"] or "")
        op = metrics.first_mention(cot, o_old, aliases)    # 链内 o_old 首现位
        pre = cot[:op] if op >= 0 else cot
        marks = list(REFLECT.finditer(pre))
        revs.append({"cid": cid, "o_new": o_new, "o_old": o_old, "q": bb["q"], "cot": cot,
                     "ans": bb["answer"], "op": op, "cat": cat,
                     "mark": marks[-1].group(0) if marks else None})

    settled = [r for r in revs if r["cat"] in ("clean", "churn")]   # 答案真落定到旧
    n_ref = sum(r["mark"] is not None for r in settled)
    print(f"# 审计 editor={args.editor} budget={args.budget}  B0编对且答案现旧(loose)={loose} 条")
    print(f"#   分桶：clean(只旧不新)={cats['clean']}  churn(新旧都现·末次落旧)={cats['churn']}"
          f"  held(新旧都现·末次落新=编辑守住,旧仅顺带)={cats['held']}")
    print(f"#   → 真落定回退 clean+churn={len(settled)} 条；旧『flip 首现序』口径把 held 也误算进回退(虚高 {cats['held']} 条)")
    print(f"# 反思归因：{n_ref}/{len(settled)} = {n_ref / max(len(settled), 1):.0%}"
          f"（仅对真落定回退计；go/no-go ② 阈值 ≥60%；末次仍是粗判，以下全答案人工复核）\n")
    for r in revs[:args.n]:
        op, cot = r["op"], r["cot"]
        seg = ("..." + cot[max(0, op - 300):op + 110].replace("\n", " ") + "...") if op >= 0 else cot[:420]
        print("=" * 72)
        print(f"[{r['cid']}] ({r['cat']}) Q: {r['q']}")
        print(f"  新={r['o_new']}  旧={r['o_old']}  反思标记={r['mark']!r}")
        print(f"  链(o_old 处): {seg}")
        print(f"  答(全): {(r['ans'] or '').strip().replace(chr(10), ' ')[:500]}")


if __name__ == "__main__":
    main()
