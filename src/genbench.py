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


def old_ids(tok, src, aliases, mode="union"):
    """被编辑 o_old 的首-token id 集合。
    mode='union':并集全部被编辑事实(病态最坏界,同时压全部 o_old);
    mode='single':只取第 1 条 o_old(现实上界:模拟单条编辑的抑制器误施于通用 query)。"""
    from suppress import build_old_token_ids
    ids = set()
    for l in open(src):
        o_old = json.loads(l).get("o_old")
        if not o_old:
            continue
        ids |= build_old_token_ids(tok, o_old, aliases)
        if mode == "single":
            break
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


def out_path(cfg, rank, suffix=""):
    return os.path.join(cfg["out_dir"], f"{cfg['model_tag']}_GENBENCH{suffix}_r{rank}.jsonl")


def score(cfg, suffix=""):
    pat = os.path.join(cfg["out_dir"], f"{cfg['model_tag']}_GENBENCH{suffix}_r*.jsonl")
    rows = [json.loads(l) for s in sorted(glob.glob(pat)) for l in open(s) if '"bench"' in l]
    agg = collections.defaultdict(lambda: collections.Counter())
    for r in rows:
        b = r["bench"]
        agg[b]["n"] += 1
        agg[b]["off"] += bool(r.get("ok_off"))
        agg[b]["on"] += bool(r.get("ok_on"))
    print(f"# 通用能力门  model={cfg['hparams_overrides']['model_name']}  suppress={cfg.get('suppress')}  suffix={suffix or '(旧无后缀run)'}")
    print(f"{'bench':<8}{'n':>5}{'acc_off':>9}{'acc_on(抑制)':>16}{'Δ':>9}")
    for b in sorted(agg):
        s = agg[b]; off = s["off"] / s["n"]; on = s["on"] / s["n"]
        print(f"{b:<8}{s['n']:>5}{off:>9.3f}{on:>16.3f}{on - off:>+9.3f}")
    print("\nacc_off=不挂抑制(=部署时非编辑 query 的真实通用能力,应逼近模型公认水平);acc_on=按 suffix 配置抑制。"
          "Δ 门:|Δ|≤0.02。注:union+all=病态最坏界;single+think=现实上界(部署口径)。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--rank", type=int, default=0)
    ap.add_argument("--world", type=int, default=1)
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--aliases", default="data/aliases.json")
    ap.add_argument("--mode", choices=["union", "single"], default="union",
                    help="union=并集全部 o_old(病态最坏界);single=单条 o_old(现实上界:单编辑抑制器误施于通用 query)")
    ap.add_argument("--force_scope", choices=["all", "think"], default=None,
                    help="覆盖 config.suppress.scope;不给则用 config(probe32b_sup.yaml=think)")
    ap.add_argument("--gsm8k_budget", default="B3")
    ap.add_argument("--math_budget", default="B3M", help="MATH 链常 >8192,默认 B3M=16384 防截断")
    ap.add_argument("--answer_cap", type=int, default=512, help="答案段 token 上限(旧 256 截断答案重述→基线虚低)")
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config))
    scope = args.force_scope or cfg["suppress"].get("scope", "all")
    suffix = f"_{args.mode}_{scope}"          # 输出按 mode+scope 分文件 → 不同配置不串、不与旧污染run撞 done 集
    if args.score:
        score(cfg, suffix)
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
    ids = old_ids(tok, src, aliases, mode=args.mode)
    sup = {"processor": make_processor(ids, cfg["suppress"]["penalty"]), "scope": scope}
    print(f"[genbench] mode={args.mode} scope={scope} o_old_token数={len(ids)} "
          f"penalty={cfg['suppress']['penalty']} budget(gsm8k={args.gsm8k_budget},math={args.math_budget}) "
          f"answer_cap={args.answer_cap} dev={dev} suffix={suffix}")

    op = out_path(cfg, args.rank, suffix)
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
                bdg = args.gsm8k_budget if bench == "gsm8k" else args.math_budget
                try:
                    _, ans_off, _ = think_budget.generate_with_budget(model, tok, q, bdg, suppress=None, answer_cap=args.answer_cap)
                    _, ans_on, _ = think_budget.generate_with_budget(model, tok, q, bdg, suppress=sup, answer_cap=args.answer_cap)
                    rec = {"bench": bench, "i": i, "ok_off": correct(bench, ans_off, it["a"]),
                           "ok_on": correct(bench, ans_on, it["a"])}
                except Exception as e:
                    rec = {"bench": bench, "i": i, "error": repr(e)}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()


if __name__ == "__main__":
    main()
