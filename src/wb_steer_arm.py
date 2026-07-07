"""W-B · 表征级抑制修复(prereg-wseries §3;红队修正版)。

两步:
  extract  在【未编辑 base】上抽 per-case o_old 概念方向(o_old-语境 vs 匹配中性语境;
           禁 o_old-vs-o_new——那等于把答案写进残差流)。G7 门:留一模板两两 cos≥0.6;
           对 W_U[o_new 首 tok] 正交化为主版本;逐层单位化 + 层中位残差范数(α 定标用)。
  run      S(−α·v̂)/Pshuf(跨 case 循环换向=真概念错 case)/Splus(+α,符号对照) 三臂;
           edit→B0/B3 生成(steerer scope=think,mode=generated)→efficacy+locality(干预开)
           →restore。输出 edit_loop 同 schema jsonl(tag cf200wb*)→ score_pilot/cross_arm 直接吃。

用法(8×H200;32B fp32):
  # ① 方向抽取(base 模型,8 卡分片;→ results/wb/directions_r*.pt + G7 报告)
  for r in $(seq 0 7); do WHYAAAI_MODEL=... WHYAAAI_DTYPE=float32 python src/wb_steer_arm.py extract \
      --config experiments/probe32b.yaml --rank $r --world 8 --device $r & done; wait
  # ② pilot(n=30,α 扫;S 臂)→ 选 α*(退化<5% 且 LocAcc 掉<5pt 的最大档)
  ... run --arm S --alpha-pct 1 --n 30 …(2/5 同)
  # ③ 确证:S / Pshuf(n=200,α*);可选 Splus n=100
  for r in $(seq 0 7); do WHYAAAI_MODEL=... WHYAAAI_DTYPE=float32 PYTHONPATH=source/EasyEdit \
      python src/wb_steer_arm.py run --config experiments/probe32b.yaml --arm S --alpha-pct 2 \
      --rank $r --world 8 --device $r & done; wait
"""
import argparse, collections, glob as globlib, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics
from wa_probe import first_token_ids

TEMPLATES = [
    "A well-known answer in this category is {X}, according to many sources.",
    "People often mention {X} when discussing this topic.",
    "The quiz answer turned out to be {X}, which surprised nobody.",
    "In the encyclopedia, the entry for {X} is quite detailed.",
    "She wrote an essay about {X} last year.",
    "The documentary focused on {X} and its history.",
    "Among the listed options, {X} appeared first.",
    "Many students first learn about {X} in school.",
]


def _span_mean_hidden(model, tok, text, ent):
    """text 里实体 span(实体 token+后 3)的逐层 mean hidden → [nL, H](hs[k]=layer k-1 输出)。"""
    import torch
    i0 = text.index(ent)
    enc = tok(text, return_tensors="pt", return_offsets_mapping=True, add_special_tokens=True)
    offs = enc.pop("offset_mapping")[0].tolist()
    ids = {k: v.to(model.device) for k, v in enc.items()}
    span = [i for i, (a, b) in enumerate(offs) if a < i0 + len(ent) and b > i0]
    span = list(range(span[0], min(span[-1] + 4, len(offs)))) if span else []
    with torch.no_grad():
        hs = model(**ids, output_hidden_states=True).hidden_states[1:]     # 跳 embedding
    H = torch.stack([h[0, span].mean(0) for h in hs]).float().cpu()        # [nL,H]
    nrm = torch.stack([h[0, span].norm(dim=-1).median() for h in hs]).float().cpu()
    del hs
    return H, nrm


def cmd_extract(args):
    import torch, yaml
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from r1_tokenizer import fix_r1_tokenizer
    cfg = yaml.safe_load(open(args.config))
    ds = cfg["dataset"]
    cases = [json.loads(l) for l in open(ds["path"] if os.path.exists(ds["path"]) else ds["fallback_path"])]
    if ds.get("n"):
        cases = cases[:ds["n"]]
    aliases = json.load(open(args.aliases))
    distract = json.load(open(args.distractors))
    dev = args.device if args.device is not None else args.rank
    cases = [c for i, c in enumerate(cases) if i % args.world == args.rank]
    name = os.environ["WHYAAAI_MODEL"]
    dtype = {"float32": torch.float32}.get(os.environ.get("WHYAAAI_DTYPE", "float32"), torch.float32)
    tok = fix_r1_tokenizer(AutoTokenizer.from_pretrained(name), name)
    model = AutoModelForCausalLM.from_pretrained(name, torch_dtype=dtype, device_map=f"cuda:{dev}").eval()
    W_U = model.lm_head.weight
    os.makedirs(args.out_dir, exist_ok=True)
    out, report = {}, collections.Counter()
    for c in cases:
        cid, o_old, o_new = c["case_id"], str(c["o_old"]), str(c["o_new"])
        dl = [d for d in distract.get(cid, []) if isinstance(d, str)][:len(TEMPLATES)]
        if len(dl) < len(TEMPLATES):
            report["skip_no_distractors"] += 1
            continue
        try:
            vt, nrms = [], []
            for t, dn in zip(TEMPLATES, dl):                     # A=o_old 语境,B=同模板中性实体(无 o_old/o_new)
                hA, _ = _span_mean_hidden(model, tok, t.format(X=o_old), o_old)
                hB, nB = _span_mean_hidden(model, tok, t.format(X=dn), dn)
                vt.append(hA - hB); nrms.append(nB)
            import torch as _t
            vt = _t.stack(vt)                                    # [T,nL,H]
            v = vt.mean(0)
            # G7 判据 = 个体模板方向两两 cos(展平层维)——真判别性指标。
            #   留一均值(loo_cos)因 8 选 7 高度重叠→恒≈0.95+、几乎不判别(冒烟 g7_fail=0/25 即此),
            #   降级为仅报告。个体方向各用不同中性实体→有真变异,pair_cos≥0.6 才是"概念方向主导模板噪声"。
            flat = (vt.reshape(len(TEMPLATES), -1))
            flat = flat / flat.norm(dim=-1, keepdim=True).clamp_min(1e-8)
            cm = flat @ flat.T
            T = cm.shape[0]
            pair_cos = float((cm.sum() - T) / (T * (T - 1)))     # ★G7 判据:个体两两 cos 均值
            loo = _t.stack([vt[[j for j in range(len(TEMPLATES)) if j != i]].mean(0).flatten()
                            for i in range(len(TEMPLATES))])
            loo = loo / loo.norm(dim=-1, keepdim=True).clamp_min(1e-8)
            n = loo.shape[0]
            loo_cos = float(((loo @ loo.T).sum() - n) / (n * (n - 1)))    # 仅报告(非判别)
            # 对 W_U[o_new 首 tok] 正交化(逐 id Gram-Schmidt);记录 pre-ortho cos
            pre = 0.0
            for tid in first_token_ids(tok, o_new, aliases, space_only=True):
                u = W_U[tid].float().cpu(); u = u / u.norm()
                pre = max(pre, float((v / v.norm(dim=-1, keepdim=True) @ u).abs().max()))
                v = v - (v @ u).unsqueeze(-1) * u
            v = v / v.norm(dim=-1, keepdim=True).clamp_min(1e-8)             # 逐层单位化
            out[cid] = {"v": v.half(), "pair_cos": pair_cos, "loo_cos": loo_cos, "cos_wu_onew_pre": pre,
                        "resid_med": _t.stack(nrms).median(0).values}
            report["ok"] += 1
            report["g7_fail"] += int(pair_cos < 0.6)             # ★门判个体 pair_cos
            print(f"[{cid}] pair_cos={pair_cos:.3f} loo_cos={loo_cos:.3f} preWUcos={pre:.3f}")
        except Exception as e:
            report["error"] += 1
            print(f"[fail] {cid}: {e}")
    __import__("torch").save(out, os.path.join(args.out_dir, f"directions_r{args.rank}of{args.world}.pt"))
    pcs = sorted(r["pair_cos"] for r in out.values())
    med = pcs[len(pcs) // 2] if pcs else None
    print("# extract:", dict(report), "  G7 剔除率(pair_cos<0.6)=", report["g7_fail"], "/", report["ok"],
          "(>20% → W-B 停,prereg G7)")
    print(f"# pair_cos 分布(判别性指标): min={pcs[0]:.3f} med={med:.3f} max={pcs[-1]:.3f}" if pcs else "# 无 case",
          "  ← 冻结前看这个决定 0.6 阈值是否合理(median 太低=概念方向法本身弱)")


def cmd_run(args):
    import torch, yaml
    import think_budget as tb
    from steer import Steerer
    from run_pilot import resolve
    from edit_loop import HP_CLS, restore, probes
    cfg = yaml.safe_load(open(args.config))
    dev = args.device if args.device is not None else args.rank
    R = resolve(cfg, args.editor, args.rank, args.world, dev)
    cases = R["cases"][:args.n] if args.n else R["cases"]
    mine = [c for i, c in enumerate(cases) if i % args.world == args.rank]
    if args.smoke:
        mine = mine[:args.smoke]
    dirs = {}
    for p in sorted(globlib.glob(os.path.join(args.dir_dir, "directions_r*.pt"))):
        dirs.update(torch.load(p, map_location="cpu"))
    order = sorted(dirs)                                           # Pshuf:循环移位=确定性 derangement
    shuf = {order[i]: order[(i + 1) % len(order)] for i in range(len(order))}
    hp = HP_CLS[args.editor].from_hparams(R["hparams"])
    for k, v in R["overrides"].items():
        setattr(hp, k, v)
    if os.environ.get("WHYAAAI_MODEL"):
        hp.model_name = os.environ["WHYAAAI_MODEL"]
    from vendor_patches.easyedit_qwen2_loader import apply as p1
    from vendor_patches.easyedit_mom2_dataset import apply as p2
    p1(); p2()
    from easyeditor import BaseEditor
    ed = BaseEditor.from_hparams(hp)
    model, tok = ed.model, ed.tok
    model.eval()
    nL = model.config.num_hidden_layers
    lo, hi = args.band
    tag = f"cf200wb{args.arm}{args.alpha_pct}"
    out = os.path.join(cfg["out_dir"], f"{cfg['model_tag']}_{args.editor}_{tag}_r{args.rank}of{args.world}.jsonl")
    os.makedirs(cfg["out_dir"], exist_ok=True)
    done = set()
    if os.path.exists(out):
        for l in open(out):
            try:
                done.add(json.loads(l)["case_id"])
            except Exception:
                pass
    sign = +1.0 if args.arm == "Splus" else -1.0
    with open(out, "a") as f:
        if not done:
            f.write(json.dumps({"_meta": True, "arm": args.arm, "alpha_pct": args.alpha_pct, "band": args.band,
                                "scope": "think", "site": "mlp", "mode": "generated", "tag": tag,
                                "dtype": os.environ.get("WHYAAAI_DTYPE"), "prereg": "prereg-wseries.md"}) + "\n")
        for c in mine:
            cid = c["case_id"]
            if cid in done:
                continue
            src = shuf.get(cid, cid) if args.arm == "Pshuf" else cid       # Pshuf:邻 case 的真方向
            rec = dirs.get(src) if dirs.get(src) else None
            if rec is None or rec.get("pair_cos", 0) < 0.6:               # G7 门:个体 pair_cos(非 loo_cos)
                f.write(json.dumps({"case_id": cid, "skip": "no_direction_or_G7"}) + "\n"); f.flush()
                continue
            v = rec["v"].float()                                           # [nL,H] 单位化
            scale = (args.alpha_pct / 100.0) * dirs[cid]["resid_med"].float()   # α 定标用【本 case】残差范数
            dmat = torch.zeros(nL, v.shape[1])
            for L in range(lo, min(hi + 1, nL)):
                dmat[L] = v[L] * scale[L]
            st = Steerer(model, dmat, alpha=sign, site="mlp", layers=list(range(lo, min(hi + 1, nL))),
                         mode="generated")
            wcopy = None
            try:
                _, _, wcopy = ed.edit(prompts=[c["prompt"]], ground_truth=[c["o_old"]],
                                      target_new=[c["o_new"]], subject=[c["s"]], sequential_edit=True)
                for b in ("B0", "B3"):
                    for ptype, q in probes(c, ["efficacy", "locality"]):
                        cot, ans, _ = tb.generate_with_budget(model, tok, q, b,
                                                              steerer={"steerer": st, "scope": "think"})
                        f.write(json.dumps({"case_id": cid, "editor": args.editor, "budget": b,
                                            "probe": ptype, "decode": "greedy", "seed": None,
                                            "temperature": None, "q": q, "cot": cot, "answer": ans},
                                           ensure_ascii=False) + "\n")
                f.flush()
                print(f"[{cid}|{args.arm}] done")
            except Exception as e:
                f.write(json.dumps({"case_id": cid, "error": repr(e)}) + "\n"); f.flush()
                print(f"[case-fail] {cid}: {e}")
            finally:
                if wcopy is not None:
                    restore(model, wcopy)
    print(f"# → {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract")
    e.add_argument("--config", required=True)
    e.add_argument("--aliases", default="data/aliases.json")
    e.add_argument("--distractors", default="data/wa_distractors.json")
    e.add_argument("--out-dir", default="results/wb")
    e.add_argument("--rank", type=int, default=0)
    e.add_argument("--world", type=int, default=1)
    e.add_argument("--device", type=int, default=None)
    r = sub.add_parser("run")
    r.add_argument("--config", required=True)
    r.add_argument("--editor", default="ROME")
    r.add_argument("--arm", choices=["S", "Pshuf", "Splus"], required=True)
    r.add_argument("--alpha-pct", type=float, required=True, help="α=层中位残差范数的百分比(prereg §3:pilot 扫 1/2/5)")
    r.add_argument("--band", type=int, nargs=2, default=[20, 44], help="注入层带(W-A onset 带出来后覆盖;fallback 20-44)")
    r.add_argument("--dir-dir", default="results/wb")
    r.add_argument("--n", type=int, default=0, help="pilot 用:只取前 n case(0=全部)")
    r.add_argument("--rank", type=int, default=0)
    r.add_argument("--world", type=int, default=1)
    r.add_argument("--device", type=int, default=None)
    r.add_argument("--smoke", type=int, default=0)
    args = ap.parse_args()
    (cmd_extract if args.cmd == "extract" else cmd_run)(args)


if __name__ == "__main__":
    main()
