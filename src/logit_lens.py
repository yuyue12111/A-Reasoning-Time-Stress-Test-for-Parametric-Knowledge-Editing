"""RQ2 机理 · logit-lens（plan v1.24 ⑤b）：旧知识在编辑后模型里"涌回"于哪一层。

对【回退案例】(B{budget} 答案落到 o_old)：逐条 ROME 编辑 → 对 prompt+cot+answer 做一次前向
(output_hidden_states) → 在【答案里 o_old 首现位的前一位】把**每一层**残差经 final-norm + lm_head
投到词表(logit-lens) → 记 o_old 与 o_new 首 token 的 logit 差 gap_L = logit_L(o_old) − logit_L(o_new)
与 o_old 的 rank。crossover 层 = gap_L 首次 > 0 的层。

ROME 编辑的是早中层(7B layer5 / 14B 9 / 32B 12)。若 o_old 仅在**更晚层**胜出(crossover ≫ 编辑层)，
即"编辑把 o_new 装进早层、后段推理在更晚层把 o_old 翻回来" → 图2 的机理叙事。

  PYTHONPATH=source/EasyEdit python src/logit_lens.py --config experiments/probe32b.yaml \
      --editor ROME --budget B3 [--n 30] [--cases cf_x,cf_y]

单进程单卡即可(逐条分析,不需 8 卡)。H200 上 32B 须 WHYAAAI_DTYPE=float32、WHYAAAI_MODEL=本地路径。
输出 results/<out_dir>/logitlens_<tag>_<editor>_<budget>.jsonl + 末尾聚合曲线。
"""
import argparse, json, os, glob, collections, yaml
import torch
import metrics
import think_budget
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
        if b0ok and metrics.hit(clean(bb["answer"]), c["o_old"], aliases):   # 回退:答案含旧
            out.append({**c, "_bb": bb})
        if len(out) >= limit and not only:
            break
    return out


def first_tok(tok, word):
    """词在句中(前置空格)的首 subword id。"""
    ids = tok(" " + word.strip(), add_special_tokens=False)["input_ids"]
    return ids[0] if ids else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--editor", default="ROME")
    ap.add_argument("--budget", default="B3")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--cases", default="", help="逗号分隔的 case_id;给了就只跑这些")
    ap.add_argument("--aliases", default="data/aliases.json")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    ds = cfg["dataset"]
    cf = {c["case_id"]: c for c in (json.loads(l) for l in open(ds.get("fallback_path", ds["path"])))}
    aliases = json.load(open(args.aliases))
    only = set(filter(None, args.cases.split(","))) or None
    cases = pick_reversion_cases(cfg, args.editor, args.budget, cf, aliases, args.n, only)
    if not cases:
        raise SystemExit("没挑到回退案例（先跑该 config 的 pilot/probe，确认 budget 与 editor 对）")

    # —— 建模 + 编辑器（复刻 edit_loop 的加载：overrides + WHYAAAI_MODEL + 两个 patch + sequential_edit）——
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
    TPL, END = think_budget.TPL, think_budget.THINK_END
    with open(out_path, "w") as f:
        for c in cases:
            o_new, o_old = c["o_new"], c["o_old"]
            bb = c["_bb"]
            ot, nt = first_tok(tok, o_old), first_tok(tok, o_new)
            if ot is None or nt is None:
                continue
            wcopy = None
            try:
                _, _, wcopy = ed.edit(prompts=[c["prompt"]], ground_truth=[o_old],
                                      target_new=[o_new], subject=[c["s"]], sequential_edit=True)
                # 重建生成序列(B0 无 cot;B{≥1} = prompt + cot + \n</think>\n\n + answer)
                if args.budget == "B0":
                    full = think_budget.ZEROTHINK.format(q=bb["q"]) + (bb["answer"] or "")
                else:
                    full = TPL.format(q=bb["q"]) + (bb["cot"] or "") + "\n" + END + "\n\n" + (bb["answer"] or "")
                ids = tok(full, return_tensors="pt").to(model.device)
                seq = ids["input_ids"][0]
                # 答案区起点 = </think> 之后；在答案区找 o_old 首 token 位
                astart = 0
                end_ids = tok(END, add_special_tokens=False)["input_ids"]
                for i in range(len(seq) - len(end_ids), -1, -1):
                    if seq[i:i + len(end_ids)].tolist() == end_ids:
                        astart = i + len(end_ids); break
                pos = next((i for i in range(astart, len(seq)) if int(seq[i]) == ot), None)
                if pos is None or pos == 0:
                    f.write(json.dumps({"case_id": c["case_id"], "skip": "o_old 首token 不在答案区"}) + "\n"); continue
                probe = pos - 1                       # 该位的隐状态预测下一 token(=o_old)
                with torch.no_grad():
                    hs = model(**ids, output_hidden_states=True).hidden_states   # (nL+1) × [1,seq,H]
                    vec = torch.stack([hs[l][0, probe] for l in range(len(hs))])  # [nL+1, H]
                    logits = model.lm_head(model.model.norm(vec)).float()         # [nL+1, vocab] logit-lens
                gap = (logits[:, ot] - logits[:, nt]).tolist()
                rank_old = [int((logits[l] > logits[l, ot]).sum()) for l in range(len(gap))]  # 0=top1
                cross = next((l for l, g in enumerate(gap) if g > 0), None)
                row = {"case_id": c["case_id"], "o_new": o_new, "o_old": o_old, "edit_layer": edit_layer,
                       "n_layers": nL, "probe_pos": probe, "answer_start": astart,
                       "gap_by_layer": [round(x, 3) for x in gap], "rank_old_by_layer": rank_old,
                       "crossover_layer": cross}
                rows.append(row)
                f.write(json.dumps(row, ensure_ascii=False) + "\n"); f.flush()
                print(f"[{c['case_id']}] 编辑层={edit_layer} crossover层={cross}/{nL}  o_old={o_old} o_new={o_new}")
            except Exception as e:
                f.write(json.dumps({"case_id": c["case_id"], "error": repr(e)}, ensure_ascii=False) + "\n")
                print(f"[case-fail] {c['case_id']}: {e}")
            finally:
                if wcopy is not None:
                    restore(model, wcopy)

    # —— 聚合：逐层平均 gap + crossover 分布 ——
    if rows:
        nLp = rows[0]["n_layers"] + 1
        mean_gap = [round(sum(r["gap_by_layer"][l] for r in rows) / len(rows), 3) for l in range(nLp)]
        cross = [r["crossover_layer"] for r in rows if r["crossover_layer"] is not None]
        cross.sort()
        med = cross[len(cross) // 2] if cross else None
        print(f"\n# logit-lens 聚合 editor={args.editor} budget={args.budget}  回退案例={len(rows)}  编辑层={edit_layer}/{rows[0]['n_layers']}")
        print(f"# crossover(o_old 反超 o_new)层: 中位={med}  范围=[{cross[0] if cross else '—'},{cross[-1] if cross else '—'}]  "
              f"无crossover(始终新赢){len(rows)-len(cross)}条")
        print(f"# 逐层平均 gap=logit(o_old)−logit(o_new)（负=新赢/正=旧赢；看从负转正的层）:")
        for l in range(0, nLp, max(1, nLp // 16)):
            bar = ("+" if mean_gap[l] >= 0 else "−") * min(20, int(abs(mean_gap[l]) * 2) + 1)
            print(f"  层{l:>3}: {mean_gap[l]:>8.3f} {bar}")
        print(f"\n机理读法: 编辑层≈{edit_layer} 处应是新赢(gap<0);若 crossover 中位 {med} ≫ {edit_layer}，"
              f"即旧知识在【更晚层】被推理翻回 → 'thinking undoes editing' 的层级证据。")
    print(f"\n写出 {out_path}（{len(rows)} 条）")


if __name__ == "__main__":
    main()
