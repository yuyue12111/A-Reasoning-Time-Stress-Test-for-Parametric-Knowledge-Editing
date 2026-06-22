"""未编辑基座知识基线（plan v1.22 · RQ2 强模型探针前置）。

不做任何编辑，跑**基座**模型在 B0/B3 下对 CF 题的作答，量化『基座本就知不知道旧事实 o_old』——
这是『思考唤回旧知识(CLR)』的**知识天花板**：
  · 若基座 o_old 命中率本就低（模型压根不记得这些 CF 实体）→ 低 CLR 主要是**模型知识瓶颈**、
    而非编辑稳健 → 支持换强推理模型（强模型探针的直接动机）；
  · 若基座 o_old 命中率高（知道）而编辑后链里反而少见 → 编辑**真把旧知识压住了** → 效应是真的。

  # 8 卡分片（基座生成、无编辑/无 mom2，比 pilot 轻）：
  for r in $(seq 0 7); do python src/base_probe.py --config experiments/pilot.yaml --rank $r --world 8 & done; wait
  # 汇总打分：
  python src/base_probe.py --config experiments/pilot.yaml --score

判分用 metrics.hit（去污词边界，与主结果同口径）。jsonl probe="base"。case 集取自已有 ROME 结果，
与 pilot 完全同批（避免抽样漂移）。H200 加 WHYAAAI_DTYPE=float32 与主结果 dtype 对齐。
"""
import argparse, json, os, glob, random, collections, yaml
import metrics


def load_cases(cfg):
    """与 pilot 完全相同的 case 集：从已有 ROME 结果 jsonl 取 case_id，再从清洗全量查 prompt/o_old/o_new。
    无结果则回退 seed 抽样 n 条。"""
    ds = cfg["dataset"]
    full = {json.loads(l)["case_id"]: json.loads(l) for l in open(ds.get("fallback_path", ds["path"]))}
    pat = os.path.join(cfg["out_dir"], f"{cfg['model_tag']}_ROME_{ds['tag']}_r*.jsonl")
    ids, seen = [], set()
    for s in sorted(glob.glob(pat)):
        for l in open(s):
            if '"case_id"' not in l:
                continue
            cid = json.loads(l).get("case_id")
            if cid and cid not in seen and cid in full:
                seen.add(cid); ids.append(cid)
    if ids:
        return [full[i] for i in ids]
    cases = list(full.values())
    random.Random(cfg.get("seed", 42)).shuffle(cases)
    return cases[: ds["n"]]


def out_path(cfg, rank):
    return os.path.join(cfg["out_dir"], f"{cfg['model_tag']}_BASE_{cfg['dataset']['tag']}_r{rank}.jsonl")


def score(cfg):
    aliases = json.load(open("data/aliases.json"))
    cmap = {c["case_id"]: c for c in load_cases(cfg)}
    pat = os.path.join(cfg["out_dir"], f"{cfg['model_tag']}_BASE_{cfg['dataset']['tag']}_r*.jsonl")
    rows = [json.loads(l) for s in sorted(glob.glob(pat)) for l in open(s) if '"probe"' in l]
    by = collections.defaultdict(collections.Counter)
    n = collections.Counter()
    for r in rows:
        c = cmap.get(r["case_id"])
        if not c:
            continue
        o_old, o_new, subj = c["o_old"], c["o_new"], c.get("s") or ""
        clean = lambda t: metrics._without_subject(t, subj)
        b = r["budget"]
        n[b] += 1
        by[b]["ans_old"] += metrics.hit(clean(r.get("answer", "")), o_old, aliases)   # 基座答案命中真事实=知道
        by[b]["cot_old"] += metrics.hit(clean(r.get("cot", "")), o_old, aliases)       # 基座链含真事实
        by[b]["ans_new"] += metrics.hit(clean(r.get("answer", "")), o_new, aliases)    # 反事实(无编辑应≈0,sanity)
    print(f"# 未编辑基座知识基线  model={cfg['hparams_overrides']['model_name']}  解码=greedy")
    print(f"{'budget':<7}{'n':>5}{'答=旧(知道)':>13}{'链含旧':>10}{'答=新(应≈0)':>13}")
    for b in sorted(n):
        rate = lambda k: by[b][k] / n[b] if n[b] else 0.0
        print(f"{b:<7}{n[b]:>5}{rate('ans_old'):>13.3f}{rate('cot_old'):>10.3f}{rate('ans_new'):>13.3f}")
    print("\n答=旧 = 基座本就知道真事实的比例（CLR 的知识天花板）。"
          "低 → 低回忆是模型知识瓶颈、支持换强模型；高 → 编辑真压住了旧知识。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--rank", type=int, default=0)
    ap.add_argument("--world", type=int, default=1)
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--budgets", default="B0,B3")
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config))
    if args.score:
        score(cfg)
        return

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import think_budget

    model_name = os.environ.get("WHYAAAI_MODEL") or cfg["hparams_overrides"]["model_name"]  # 离线平台:指本地绝对路径
    dtype = {"float32": torch.float32, "bfloat16": torch.bfloat16, "float16": torch.float16}.get(
        os.environ.get("WHYAAAI_DTYPE", "bfloat16"), torch.bfloat16)
    dev = f"cuda:{args.rank}" if args.world > 1 else "cuda"
    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=dtype).to(dev).eval()

    cases = load_cases(cfg)
    budgets = [b for b in args.budgets.split(",") if b]
    op = out_path(cfg, args.rank)
    os.makedirs(cfg["out_dir"], exist_ok=True)
    done = set()
    if os.path.exists(op):
        for l in open(op):
            try:
                d = json.loads(l)
                if "case_id" in d and "budget" in d:
                    done.add((d["case_id"], d["budget"]))
            except Exception:
                pass
    with open(op, "a") as f:
        for i, c in enumerate(cases):
            if i % args.world != args.rank:
                continue
            q = c["prompt"]
            for b in budgets:
                if (c["case_id"], b) in done:
                    continue
                try:
                    cot, ans, _ = think_budget.generate_with_budget(model, tok, q, b)
                    rec = {"case_id": c["case_id"], "budget": b, "probe": "base", "decode": "greedy",
                           "q": q, "cot": cot, "answer": ans}
                except Exception as e:
                    rec = {"case_id": c["case_id"], "budget": b, "error": repr(e)}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()


if __name__ == "__main__":
    main()
