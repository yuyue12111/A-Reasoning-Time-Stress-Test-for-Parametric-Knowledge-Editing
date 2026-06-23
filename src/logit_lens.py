"""RQ2 机理 · logit-lens（plan v1.24 ⑤b，v2）：回退是"擦除编辑"还是"绕过完好的编辑"?

对【回退案例】(B{budget} 答案落到 o_old)：逐条 ROME 编辑 → 喂**原始 cloze**(c['prompt']，CF 题目
末位下一 token 就是宾语) → 一次前向(output_hidden_states) → 在 cloze 最后一位把**每一层**残差经
final-norm + lm_head 投词表(logit-lens) → gap_L = logit_L(o_new) − logit_L(o_old)。

判据：**即便该案例在 B3 思考下答案回退成 o_old，编辑位(cloze)是否仍预测 o_new?**
  · 若 gap 顶层 > 0(o_new 仍赢) → **编辑没被擦除、仍 installed**(且约在编辑层 ~12 成形)→
    回退是【推理绕过完好编辑】(链里用旁系知识重推 o_old、答案跟链),不是权重被思考改没。
这把"thinking undoes editing"的机理钉成「edit intact at cloze ＋ reasoning reconstructs old」。

  PYTHONPATH=source/EasyEdit python src/logit_lens.py --config experiments/probe32b.yaml \
      --editor ROME --budget B3 [--n 30] [--cases cf_x,cf_y]

单进程单卡。H200 上 32B 须 WHYAAAI_DTYPE=float32、WHYAAAI_MODEL=本地路径。
输出 results/<out_dir>/logitlens_<tag>_<editor>_<budget>.jsonl + 末尾聚合。
"""
import argparse, json, os, glob, collections, yaml
import torch
import metrics
from edit_loop import HP_CLS, restore


def pick_reversion_cases(cfg, editor, budget, cf, aliases, limit, only=None):
    """从已有结果挑回退案例：B0 编对(b0ok) 且 B{budget} 答案含 o_old(去污+去主体)。"""
    ds = cfg["dataset"]
    pat = os.path.join(cfg["out_dir"], f"{cfg['model_tag']}_{editor}_{ds['tag']}_r*.jsonl")
    by = collections.defaultdict(dict)
    for s in sorted(glob.glob(pat)):
        for l in open(s):
            d = json.loads(l)
            if d.get("probe") == "efficacy" and d.get("decode", "greedy") == "greedy":
                by[d["case_id"]][d["budget"]] = d
    out = []
    for cid, bud in by.items():
        if only and cid not in only:
            continue
        c = cf.get(cid); b0, bb = bud.get("B0"), bud.get(budget)
        if not c or not b0 or not bb:
            continue
        subj = c.get("s") or ""
        clean = lambda t: metrics._without_subject(t, subj)
        b0ok = metrics.hit(clean(b0["answer"]), c["o_new"], aliases) and not metrics.hit(clean(b0["answer"]), c["o_old"], aliases)
        if b0ok and metrics.hit(clean(bb["answer"]), c["o_old"], aliases):     # 回退:答案含旧
            out.append(c)
        if len(out) >= limit and not only:
            break
    return out


def first_tok(tok, word):
    ids = tok(" " + word.strip(), add_special_tokens=False)["input_ids"]
    return ids[0] if ids else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--editor", default="ROME")
    ap.add_argument("--budget", default="B3")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--cases", default="")
    ap.add_argument("--aliases", default="data/aliases.json")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    ds = cfg["dataset"]
    cf = {c["case_id"]: c for c in (json.loads(l) for l in open(ds.get("fallback_path", ds["path"])))}
    aliases = json.load(open(args.aliases))
    only = set(filter(None, args.cases.split(","))) or None
    cases = pick_reversion_cases(cfg, args.editor, args.budget, cf, aliases, args.n, only)
    if not cases:
        raise SystemExit("没挑到回退案例（先跑该 config 的 pilot/probe，确认 budget 与 editor）")

    # —— 建模 + 编辑器（复刻 edit_loop 加载：overrides + WHYAAAI_MODEL + 两 patch）——
    from run_pilot import resolve
    R = resolve(cfg, args.editor, 0, 1, 0)
    hp = HP_CLS[args.editor].from_hparams(R["hparams"])
    for k, v in R["overrides"].items():
        setattr(hp, k, v)
    if os.environ.get("WHYAAAI_MODEL"):
        hp.model_name = os.environ["WHYAAAI_MODEL"]
    from vendor_patches.easyedit_qwen2_loader import apply as patch_qwen
    from vendor_patches.easyedit_mom2_dataset import apply as patch_mom2
    patch_qwen(); patch_mom2()
    from easyeditor import BaseEditor
    ed = BaseEditor.from_hparams(hp)
    model, tok = ed.model, ed.tok
    model.eval()
    edit_layer = (hp.layers or [None])[0]
    nL = model.config.num_hidden_layers

    out_path = os.path.join(cfg["out_dir"], f"logitlens_{ds['tag']}_{args.editor}_{args.budget}.jsonl")
    os.makedirs(cfg["out_dir"], exist_ok=True)
    rows = []
    with open(out_path, "w") as f:
        for c in cases:
            o_new, o_old = c["o_new"], c["o_old"]
            ot, nt = first_tok(tok, o_old), first_tok(tok, o_new)
            if ot is None or nt is None:
                continue
            wcopy = None
            try:
                _, _, wcopy = ed.edit(prompts=[c["prompt"]], ground_truth=[o_old],
                                      target_new=[o_new], subject=[c["s"]], sequential_edit=True)
                # 编辑位探针：原始 cloze，最后一位预测宾语(CF 题目设计如此)
                ids = tok(c["prompt"], return_tensors="pt").to(model.device)
                last = ids["input_ids"].shape[1] - 1
                with torch.no_grad():
                    hs = model(**ids, output_hidden_states=True).hidden_states   # (nL+1)×[1,seq,H]
                    vec = torch.stack([hs[l][0, last] for l in range(len(hs))])   # [nL+1,H]
                    logits = model.lm_head(model.model.norm(vec)).float()         # logit-lens 每层
                gap = (logits[:, nt] - logits[:, ot]).tolist()                    # o_new − o_old(编辑方向)
                rank_new = [int((logits[l] > logits[l, nt]).sum()) for l in range(len(gap))]
                formed = next((l for l, g in enumerate(gap) if g > 0), None)      # o_new 首次胜出层
                intact = gap[-1] > 0                                              # 顶层 o_new 仍赢 = 编辑没被擦
                row = {"case_id": c["case_id"], "o_new": o_new, "o_old": o_old, "edit_layer": edit_layer,
                       "n_layers": nL, "edit_intact_at_cloze": intact, "onew_formed_layer": formed,
                       "gap_top": round(gap[-1], 3), "rank_new_top": rank_new[-1],
                       "gap_by_layer": [round(x, 3) for x in gap]}
                rows.append(row)
                f.write(json.dumps(row, ensure_ascii=False) + "\n"); f.flush()
                print(f"[{c['case_id']}] 编辑层={edit_layer} o_new成形层={formed} 顶层gap={gap[-1]:.2f} "
                      f"编辑仍在={'是' if intact else '否'}  ({o_new}↔{o_old})")
            except Exception as e:
                f.write(json.dumps({"case_id": c["case_id"], "error": repr(e)}, ensure_ascii=False) + "\n")
                print(f"[case-fail] {c['case_id']}: {e}")
            finally:
                if wcopy is not None:
                    restore(model, wcopy)

    if rows:
        nLp = rows[0]["n_layers"] + 1
        intact_n = sum(r["edit_intact_at_cloze"] for r in rows)
        formed = sorted(r["onew_formed_layer"] for r in rows if r["onew_formed_layer"] is not None)
        med = formed[len(formed) // 2] if formed else None
        mean_gap = [round(sum(r["gap_by_layer"][l] for r in rows) / len(rows), 3) for l in range(nLp)]
        print(f"\n# logit-lens(编辑位/cloze) editor={args.editor} budget={args.budget}  回退案例={len(rows)}  编辑层={edit_layer}/{rows[0]['n_layers']}")
        print(f"# ★ 回退案例里编辑【仍 installed】(cloze 仍预测 o_new)= {intact_n}/{len(rows)} = {intact_n/len(rows):.0%}")
        print(f"#   o_new 成形层中位={med}(应≈编辑层 {edit_layer})；逐层平均 gap=logit(o_new)−logit(o_old):")
        for l in range(0, nLp, max(1, nLp // 16)):
            g = mean_gap[l]
            print(f"  层{l:>3}: {g:>8.3f} {('+' if g >= 0 else '−') * min(20, int(abs(g) * 2) + 1)}")
        print(f"\n机理读法: 这些案例 B3 思考后答案都回退成 o_old，但若编辑在 cloze 处【仍 installed {intact_n/len(rows):.0%}】"
              f"→ 回退**不是思考擦除了编辑权重**，而是**推理在链里用完好的旁系知识重推 o_old、答案跟了链** = 'thinking undoes editing' 的机理。")
    print(f"\n写出 {out_path}（{len(rows)} 条）")


if __name__ == "__main__":
    main()
