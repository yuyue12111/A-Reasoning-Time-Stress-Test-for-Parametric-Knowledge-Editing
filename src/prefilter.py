"""§2.3 预过滤：只保留"模型编辑前确实知道旧事实"的 case
（pre-edit greedy(prompt) 命中 o_old），否则"回退"无从定义。需 GPU。

  cd source/EasyEdit
  PYTHONPATH=. python ../../src/prefilter.py --config ../../experiments/pilot.yaml --device 0

产物落到 cfg.dataset.path（默认 data/counterfact.prefiltered.jsonl），run_pilot 会自动优先用它。
判分复用已测的 metrics.hit + data/aliases.json；生成用 think_budget（默认 B3≈自然思考最忠实）。
"""
import argparse, json, os, random, yaml
import think_budget as tb
import metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--budget", default="B3", help="预过滤用的预算档（默认 B3≈自然；B0 更快但可能漏召）")
    ap.add_argument("--device", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None, help="候选上限（默认 3×n）")
    ap.add_argument("--aliases", default="data/aliases.json")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    ds = cfg["dataset"]
    raw = ds.get("fallback_path", ds["path"])
    out = ds["path"]
    n = ds.get("n", 200)
    limit = args.limit or 3 * n
    aliases = json.load(open(args.aliases))

    from transformers import AutoModelForCausalLM, AutoTokenizer
    model_name = cfg["hparams_overrides"]["model_name"]
    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto").to(f"cuda:{args.device}").eval()

    cands = [json.loads(l) for l in open(raw)]
    random.Random(cfg.get("seed", 42)).shuffle(cands)
    cands = [c for c in cands if c.get("o_old")][:limit]

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    kept = i = 0
    with open(out, "w", encoding="utf-8") as f:
        for i, c in enumerate(cands, 1):
            _, ans, _ = tb.generate_with_budget(model, tok, c["prompt"], args.budget)
            if metrics.hit(ans, c["o_old"], aliases):
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
                kept += 1
            if i % 25 == 0:
                print(f"  [{i}/{len(cands)}] kept {kept}", flush=True)
            if kept >= 2 * n:          # 攒够 2n 存活即停（省算力，留冗余给抽样）
                break
    print(f"[prefilter] kept {kept}/{i} -> {out}  (budget={args.budget}, 存活率 {kept/max(i,1):.0%})")


if __name__ == "__main__":
    main()
