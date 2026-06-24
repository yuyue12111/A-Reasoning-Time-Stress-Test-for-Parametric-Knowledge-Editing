"""RQ3 安全门 · 通用能力(plan v1.27 ⑤;设计面板坑 #6)。

问:我们的 o_old 抑制修复伤不伤通用推理?
设计:**部署时修复只对被编辑的 query 生效**(非编辑 query 不挂 suppress → 通用能力按构造不受影响)。
本测给【最坏界】:在 GSM8K/MATH 上对【所有编辑 o_old 的并集 token】施 scope=all 抑制(远超实际部署),
看 acc 掉多少。若并集最坏界都 acc 几乎不掉 → 修复对通用推理的附带损害可忽略。

  # 8 卡分片(基座、不编辑):
  for r in $(seq 0 7); do python src/genbench.py --config experiments/probe32b_sup.yaml --rank $r --world 8 & done; wait
  # 汇总:
  python src/genbench.py --config experiments/probe32b_sup.yaml --score

数据(联网实例 stage 到 GPFS,见下):data/gsm8k_200.jsonl / data/math500_100.jsonl,每行 {"q":..,"a":..}。
penalty/scope 取自 config 的 suppress 块(与 RQ3 修复同参)。判分粗(相对 off/on Δ 才是重点)。
"""
import argparse, json, os, glob, re, collections, yaml
import metrics


BENCHES = {"gsm8k": "data/gsm8k_200.jsonl", "math": "data/math500_100.jsonl"}


def union_old_ids(tok, src, aliases):
    """所有编辑 o_old 的并集首-token id(最坏界:同时压全部被编辑事实)。"""
    ids = set()
    from suppress import build_old_token_ids
    for l in open(src):
        o_old = json.loads(l).get("o_old")
        if o_old:
            ids |= build_old_token_ids(tok, o_old, aliases)
    return ids


def gsm8k_gold(a):
    m = re.findall(r"-?\d[\d,]*", a.split("####")[-1])
    return m[-1].replace(",", "") if m else None


def last_number(text):
    m = re.findall(r"-?\d[\d,]*\.?\d*", text or "")
    return m[-1].replace(",", "").rstrip(".") if m else None


def boxed(text):
    """取最后一个 \\boxed{...} 内容;无则回退末数字。"""
    i = (text or "").rfind("\\boxed{")
    if i < 0:
        return last_number(text)
    j, depth, k = i + 7, 1, i + 7
    while k < len(text) and depth:
        depth += {"{": 1, "}": -1}.get(text[k], 0)
        k += 1
    return text[j:k - 1].strip()


def norm(s):
    return re.sub(r"\s|\$|\\left|\\right|\\,", "", str(s or "")).strip("{}").lower()


def correct(bench, gen, gold):
    if bench == "gsm8k":
        return last_number(gen) is not None and last_number(gen) == gsm8k_gold(gold)
    return norm(boxed(gen)) == norm(gold) and norm(gold) != ""


def out_path(cfg, rank):
    return os.path.join(cfg["out_dir"], f"{cfg['model_tag']}_GENBENCH_r{rank}.jsonl")


def score(cfg):
    pat = os.path.join(cfg["out_dir"], f"{cfg['model_tag']}_GENBENCH_r*.jsonl")
    rows = [json.loads(l) for s in sorted(glob.glob(pat)) for l in open(s) if '"bench"' in l]
    agg = collections.defaultdict(lambda: collections.Counter())
    for r in rows:
        b = r["bench"]
        agg[b]["n"] += 1
        agg[b]["off"] += bool(r.get("ok_off"))
        agg[b]["on"] += bool(r.get("ok_on"))
    print(f"# 通用能力门  model={cfg['hparams_overrides']['model_name']}  suppress={cfg.get('suppress')}")
    print(f"{'bench':<8}{'n':>5}{'acc_off':>9}{'acc_on(并集最坏界)':>20}{'Δ':>9}")
    for b in sorted(agg):
        s = agg[b]; off = s["off"] / s["n"]; on = s["on"] / s["n"]
        print(f"{b:<8}{s['n']:>5}{off:>9.3f}{on:>20.3f}{on - off:>+9.3f}")
    print("\nacc_off=不挂抑制(=部署时非编辑 query 的真实通用能力);acc_on=最坏界并集抑制。"
          "Δ 接近 0 → 修复附带损害可忽略(门:|Δ|≤0.02)。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--rank", type=int, default=0)
    ap.add_argument("--world", type=int, default=1)
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--aliases", default="data/aliases.json")
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config))
    if args.score:
        score(cfg)
        return

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import think_budget
    from suppress import make_processor

    model_name = os.environ.get("WHYAAAI_MODEL") or cfg["hparams_overrides"]["model_name"]
    dtype = {"float32": torch.float32, "bfloat16": torch.bfloat16}.get(os.environ.get("WHYAAAI_DTYPE", "bfloat16"), torch.bfloat16)
    dev = f"cuda:{args.rank}" if args.world > 1 else "cuda"
    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=dtype).to(dev).eval()

    aliases = json.load(open(args.aliases))
    src = cfg["dataset"].get("fallback_path", cfg["dataset"]["path"])
    ids = union_old_ids(tok, src, aliases)
    sup = {"processor": make_processor(ids, cfg["suppress"]["penalty"]), "scope": "all"}   # 最坏界:全程压并集
    print(f"[genbench] 并集 o_old token 数={len(ids)}  penalty={cfg['suppress']['penalty']}  dev={dev}")

    op = out_path(cfg, args.rank)
    os.makedirs(cfg["out_dir"], exist_ok=True)
    done = set()
    if os.path.exists(op):
        for l in open(op):
            try:
                d = json.loads(l); done.add((d.get("bench"), d.get("i")))
            except Exception:
                pass
    with open(op, "a") as f:
        for bench, path in BENCHES.items():
            ap_ = os.path.join(os.path.dirname(__file__), "..", path)
            ap_ = path if os.path.exists(path) else ap_
            if not os.path.exists(ap_):
                print(f"[genbench] 缺数据 {path}(先 stage)"); continue
            items = [json.loads(l) for l in open(ap_)]
            for i, it in enumerate(items):
                if i % args.world != args.rank or (bench, i) in done:
                    continue
                q = it["q"]
                try:
                    _, ans_off, _ = think_budget.generate_with_budget(model, tok, q, "B3", suppress=None)
                    _, ans_on, _ = think_budget.generate_with_budget(model, tok, q, "B3", suppress=sup)
                    rec = {"bench": bench, "i": i, "ok_off": correct(bench, ans_off, it["a"]),
                           "ok_on": correct(bench, ans_on, it["a"])}
                except Exception as e:
                    rec = {"bench": bench, "i": i, "error": repr(e)}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()


if __name__ == "__main__":
    main()
