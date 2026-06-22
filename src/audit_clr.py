"""CLR 语义审计（plan v1.22 ④a）：把 B{budget} 下 CLR 命中（推理链含 o_old，去污判分 + 挖主体复述）
的案例倒出『链窗口 + 最终答案 + 答案落点』，供人工/判官复核把头牌 CLR 从「旧词出现」收紧到
「链里真的重新检索并使用了旧事实」——分 recall(真回忆) / bridge(编造桥接调和编辑与旧事实) /
restate(只是复述题目) / compare(对比或否定提及) 四类，给清洗后 CLR。

  python src/audit_clr.py --config experiments/pilot.yaml --editor ROME --budget B3 [--n 40] [--all]

默认只看 B0 编对的案例（与 RR 同分母，「编辑取了、链仍重浮旧知识」最强口径）；--all 纳入全部。
判分口径与 metrics 一致（去污 hit 词边界 + 去主体 _without_subject）；CLR_all 应对齐 score_pilot 的 CLR。
每条还标 fate=答案落点（守住新 / churn / 回退旧），看泄漏的下游影响。
"""
import argparse, json, glob, os, collections, yaml
import metrics


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
    ap.add_argument("--n", type=int, default=40, help="打印前 n 条 CLR 命中链（默认 40，审计抽样量；--n 大可看全）")
    ap.add_argument("--all", action="store_true", help="纳入非 B0 编对的案例（默认只 B0 编对，与 RR 同分母）")
    ap.add_argument("--aliases", default="data/aliases.json")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    ds = cfg["dataset"]
    cf = {c["case_id"]: c for c in (json.loads(l) for l in open(ds.get("fallback_path", ds["path"])))}
    aliases = json.load(open(args.aliases))
    by = load_efficacy(cfg, args.editor)

    n_all = n_clr_all = n_b0 = n_clr_b0 = 0
    recs = []
    for cid, bud in by.items():
        c = cf.get(cid)
        b0, bb = bud.get("B0"), bud.get(args.budget)
        if not c or not bb:
            continue
        o_new, o_old, subj = c["o_new"], c["o_old"], c.get("s") or ""
        clean = lambda t: metrics._without_subject(t, subj)
        cot = clean(bb["cot"] or "")
        ans = clean(bb["answer"] or "")
        clr_hit = metrics.hit(cot, o_old, aliases)            # 去污 + 去主体后链是否含旧
        n_all += 1
        n_clr_all += clr_hit
        a0 = clean(b0["answer"]) if b0 else ""
        b0ok = bool(b0) and metrics.hit(a0, o_new, aliases) and not metrics.hit(a0, o_old, aliases)
        if b0ok:
            n_b0 += 1
            n_clr_b0 += clr_hit
        if not clr_hit or (not b0ok and not args.all):
            continue
        op = metrics.first_mention(cot, o_old, aliases)       # 链内 o_old 首现位
        has_new, has_old = metrics.hit(ans, o_new, aliases), metrics.hit(ans, o_old, aliases)
        if not has_old:
            fate = "守住(新)"
        elif not has_new:
            fate = "回退(旧)"
        else:
            fate = "churn(末" + ("旧" if metrics.last_mention(ans, o_old, aliases) > metrics.last_mention(ans, o_new, aliases) else "新") + ")"
        recs.append({"cid": cid, "o_new": o_new, "o_old": o_old, "q": bb["q"],
                     "cot": cot, "ans": bb["answer"], "op": op, "b0ok": b0ok, "fate": fate})

    rate = lambda a, b: (a / b if b else 0.0)
    print(f"# CLR 语义审计 editor={args.editor} budget={args.budget}")
    print(f"#   CLR_all (全样本,对齐 score_pilot)         = {n_clr_all}/{n_all} = {rate(n_clr_all, n_all):.3f}")
    print(f"#   CLR_b0ok(仅 B0 编对,'编辑取了、链仍重浮') = {n_clr_b0}/{n_b0} = {rate(n_clr_b0, n_b0):.3f}")
    print(f"#   倒出 {min(len(recs), args.n)}/{len(recs)} 条 CLR 命中链（默认仅 B0 编对；--all 含全部）供判"
          f"「recall 真回忆 / bridge 桥接 / restate 复述 / compare 对比否定」\n")
    for r in recs[:args.n]:
        op, cot = r["op"], r["cot"]
        seg = ("..." + cot[max(0, op - 320):op + 160].replace("\n", " ") + "...") if op >= 0 else cot[:480]
        print("=" * 72)
        print(f"[{r['cid']}] b0ok={r['b0ok']} fate={r['fate']}  Q: {r['q']}")
        print(f"  新={r['o_new']}  旧={r['o_old']}")
        print(f"  链(o_old 处): {seg}")
        print(f"  答: {(r['ans'] or '').strip().replace(chr(10), ' ')[:240]}")


if __name__ == "__main__":
    main()
