"""A3/RQ2 §5 —— 从 headline 生成 jsonl 抽「回退案例」的思考链,产小 jsonl 供本地多判官分类。

回退案例(draft §5 定义)= B0(空思考)答出编辑值 o_new、B3(自然长思考)答案翻回旧值 o_old。
判据(efficacy 探针 + greedy,按 case_id 配 B0/B3,口径与 metrics/score_pilot 同源):
  B0 编辑成功 : hit(ans_b0, o_new) 且 not hit(ans_b0, o_old)        (ES 严格)
  B3 答案回退 : hit(ans_b3, o_old)                                  (RR 口径,§5「reverts」)
  clr 标记   : hit(cot_b3, o_old)                                  (链内是否显式泄漏 → 区分 explicit/implicit)
每条输出 {case_id,s,r,prompt,o_old,o_new,o_old_aliases,o_new_aliases,cot,answer,clr_in_cot,b3_has_new}。
clr_in_cot=False 即 RR-without-CLR(implicit/associative 路径,taxonomy 硬样本)。

CPU only、无 GPU、无模型加载 → 平台上与 GPU 跑并行,不抢卡。文件小(回退子集 ~30-60 条),下载/上传到本会话跑判官。
用法(项目根):
  python src/extract_reverted.py --config experiments/probe32b.yaml --editor ROME --out data/reverted_32b.jsonl
"""
import argparse, glob, json, os
import yaml
import metrics


def load_records(out_dir, model_tag, editor, tag, decode="greedy"):
    """glob 8 分片,取 efficacy 探针 + 指定 decode 臂,按 case_id→{budget→rec} 聚合(跳过 _meta/error 行)。"""
    pat = os.path.join(out_dir, f"{model_tag}_{editor}_{tag}_r*.jsonl")
    shards = sorted(glob.glob(pat))
    if not shards:
        raise SystemExit(f"没有结果文件：{pat}（先在平台跑 headline 32B，或确认 tag/out_dir）")
    by_case = {}
    for sh in shards:
        for line in open(sh):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get("_meta") or d.get("error"):
                continue
            if d.get("probe") != "efficacy" or d.get("decode", "greedy") != decode:
                continue
            by_case.setdefault(d["case_id"], {})[d["budget"]] = d
    return shards, by_case


def select_reverted(cases, by_case, aliases, b0="B0", b3="B3"):
    """纯函数(无 IO,可单测):由 cases 表 + {case_id→{budget→rec}} 选回退案例。
    返回 (rows, stats)。判据见模块 docstring;口径全走 metrics.hit(词边界+丢短码)。"""
    n_total = n_b0ok = 0
    rows = []
    for cid, recs in by_case.items():
        if b0 not in recs or b3 not in recs or cid not in cases:
            continue
        n_total += 1
        c = cases[cid]
        o_old, o_new = c["o_old"], c["o_new"]
        a0 = recs[b0].get("answer", "") or ""
        a3 = recs[b3].get("answer", "") or ""
        cot3 = recs[b3].get("cot", "") or ""
        if not (metrics.hit(a0, o_new, aliases) and not metrics.hit(a0, o_old, aliases)):
            continue                                         # B0 必须编辑成功(答新且不含旧)
        n_b0ok += 1
        if not metrics.hit(a3, o_old, aliases):              # §5 回退 = B3 答案含旧值
            continue
        rows.append({
            "case_id": cid, "s": c.get("s"), "r": c.get("r"), "prompt": c.get("prompt"),
            "o_old": o_old, "o_new": o_new,
            "o_old_aliases": c.get("o_old_aliases"), "o_new_aliases": c.get("o_new_aliases"),
            "cot": cot3, "answer": a3,
            "clr_in_cot": bool(metrics.hit(cot3, o_old, aliases)),      # False=RR-without-CLR(implicit 硬样本)
            "b3_has_new": bool(metrics.hit(a3, o_new, aliases)),        # 答案是否同时含新值(flip/并存)
        })
    n_implicit = sum(1 for r in rows if not r["clr_in_cot"])
    stats = {"n_total": n_total, "n_b0ok": n_b0ok, "n_rev": len(rows),
             "n_implicit": n_implicit, "n_explicit": len(rows) - n_implicit}
    return rows, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--editor", default="ROME")
    ap.add_argument("--out", required=True)
    ap.add_argument("--decode", default="greedy")
    ap.add_argument("--b0", default="B0", help="编辑成功档(默认 B0=空思考)")
    ap.add_argument("--b3", default="B3", help="回退档(默认 B3=自然长思考)")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    ds = cfg["dataset"]
    src = ds.get("fallback_path", ds["path"])               # o_old/o_new/s 全量查表源(同 score_pilot)
    cases = {c["case_id"]: c for c in (json.loads(l) for l in open(src))}
    aliases = json.load(open("data/aliases.json"))

    shards, by_case = load_records(cfg["out_dir"], cfg["model_tag"], args.editor, ds["tag"], args.decode)
    rows, st = select_reverted(cases, by_case, aliases, args.b0, args.b3)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"# 分片 {len(shards)}  有 B0&B3 的 case {st['n_total']}  其中 B0 编辑成功 {st['n_b0ok']}  → 回退(B3 含旧) {st['n_rev']}")
    print(f"# 回退中 implicit(链内无显式旧值, RR-without-CLR) {st['n_implicit']} / explicit(CLR) {st['n_explicit']}")
    print(f"# → {args.out}  (下载后上传到分类会话,跑多判官填 §5)")


if __name__ == "__main__":
    main()
