"""W-A · 无声工作空间泄漏探针(prereg-wseries.md §1-§2 实现;红队 w4cxg65vd 修正版)。

对已存 B3 链 teacher-force 回(重编辑的 / 未编辑 base)模型,链位置×逐层投影**候选列**
(o_old 变体 + o_new + 20 同 relation distractor),出 distractor 校准 z 与 case 级 max-stat。

预注册要点(与 prereg 文件一一对应,跑后零改动):
  效度门 G1(模板逐字节:think_budget.TPL+BOS 逻辑复用)/ G2(重编辑后 B0 greedy 复现 b0ok)/
    G3(teacher-forced argmax 链内一致率,case ≥95% 入组)。
  排除(token-id/char 级,宽表面形集):subject 提及 ±10 tok;o_old 任何 char 级出现的 token、
    其前 1 位、及首次出现后的全部后缀(A1 总体=CLR0_wide 本就无出现,规则为 A2/calib 生效);
    o_old⊂subject 的 case 上游已整条剔除(wa_census)。
  校准:z(pos,L)=(logit(o_old)−mean(logit(d1..20)))/std(同层同位);case 统计量 S_max=带×合格位 max z;
    零分布=20 个 distractor 轮流当伪目标(null 池=其余 19),阳性 = S_max(o_old) > max_i S_max(d_i)(p=1/21)。
  层约定:hs[k]=decoder 层 k−1 输出(编辑层 12↔hs[13]);带默认 decoder 16–48(--band 覆盖;
    calibration case 只出带建议,不入推断)。逐层 S 曲线存盘,onset(C1)离线算。
  A4:subject 末 tok / 链末 tok / 答案槽 的逐层 gap(o_new−o_old)同存。

用法(平台 8×H200;32B fp32,逐 case 独立 → rank/world/device 分片,同 run_pilot 约定):
  # ① 构建 distractor 池(一次,CPU+tokenizer;入库锁定)
  WHYAAAI_MODEL=$W/models/DeepSeek-R1-Distill-Qwen-32B python src/wa_probe.py build-distractors
  # ② 冒烟(单卡 2 条,验证前向/显存/G3 门)
  WHYAAAI_MODEL=... WHYAAAI_DTYPE=float32 PYTHONPATH=source/EasyEdit python src/wa_probe.py run \
      --config experiments/probe32b.yaml --mode edited --smoke 2 --out results/wa/smoke.jsonl
  # ③ edited 态 8 卡(G1-G3 门内置;输出自动 _r{rank}of8.jsonl)
  for r in $(seq 0 7); do WHYAAAI_MODEL=... WHYAAAI_DTYPE=float32 PYTHONPATH=source/EasyEdit \
      python src/wa_probe.py run --config experiments/probe32b.yaml --mode edited \
      --rank $r --world 8 --device $r --out results/wa/edited.jsonl & done; wait
  # ④ base 态 8 卡(未编辑,同链;A3/G4)
  for r in $(seq 0 7); do WHYAAAI_MODEL=... WHYAAAI_DTYPE=float32 \
      python src/wa_probe.py run --config experiments/probe32b.yaml --mode base \
      --rank $r --world 8 --device $r --out results/wa/base.jsonl & done; wait
"""
import argparse, collections, glob as globlib, json, os, random, sys

# H200 离线实例:模型全在本地 $W/models,禁 transformers/hub 例行 HEAD 联网(否则 5 次重试白等)。
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics
from wa_census import wide_hit

# ---------------------------------------------------------------- 词形/探针集
def surface_variants(word, aliases):
    """宽表面形集:词+全别名(含<4字符)×{原样,lower,capitalize}。用于 char 级出现检测与探针 token。"""
    base = [str(word)] + [str(a) for a in aliases.get(str(word), []) if a]
    out = []
    for w in base:
        for v in (w, w.lower(), w.capitalize()):
            if v and v not in out:
                out.append(v)
    return out


def first_token_ids(tok, word, aliases, space_only=False):
    """探针 token 集(修 first_tok 单点简并):变体×{带/不带前导空格}首 token 集合。
    space_only=True → 只取带前导空格变体(正文自然形;歧义判据用它,否则无空格小写变体的
    BPE 短首片会一票否决大半候选——冒烟实测 151/200 case 池短缺的根因)。"""
    ids = set()
    for v in surface_variants(word, aliases):
        for pre in ((" ",) if space_only else ("", " ")):
            t = tok(pre + v, add_special_tokens=False)["input_ids"]
            if t:
                ids.add(t[0])
    return sorted(ids)


def is_ambiguous(tok, ids):
    """首 token 简并标记:任一首 token 解码后 ≤2 字符(去空格)= 高危共享词片。
    ⚠调用方对 distractor 应传 space_only=True 的 ids(正文自然形);检测集(o_old)仍用全变体。"""
    for i in ids:
        if len(tok.decode([i]).strip()) <= 2:
            return True
    return False


def char_occurrences(text, variants):
    """宽表面形在 text 的全部 char 区间(大小写不敏感 substring)。"""
    tl = text.lower()
    spans = []
    for v in variants:
        vl = v.lower()
        if not vl.strip():
            continue
        start = 0
        while True:
            i = tl.find(vl, start)
            if i < 0:
                break
            spans.append((i, i + len(vl)))
            start = i + 1
    return spans


# ---------------------------------------------------------------- distractor 池
def cmd_build_distractors(args):
    from transformers import AutoTokenizer
    print("# 加载 tokenizer(仅 CPU,不载权重)…", flush=True)
    tok = AutoTokenizer.from_pretrained(os.environ.get("WHYAAAI_MODEL") or args.model)
    aliases = json.load(open(args.aliases))
    pool_cases = [json.loads(l) for l in open(args.cases)]        # 候选池来源:全 CF(同 relation 候选丰富)
    by_rel = collections.defaultdict(list)                        # relation → 去重的 o_old 候选串(池只需唯一串)
    seen_rel = collections.defaultdict(set)
    for c in pool_cases:
        r, o = c.get("r") or "_", str(c["o_old"])
        if o.lower() not in seen_rel[r]:
            seen_rel[r].add(o.lower()); by_rel[r].append(o)
    # 目标 case:只给要探的子集建(默认 cf200 config;无 config 才退回全量)
    if args.config:
        ds = __import__("yaml").safe_load(open(args.config))["dataset"]
        tpath = ds["path"] if os.path.exists(ds["path"]) else ds.get("fallback_path", ds["path"])
        target = [json.loads(l) for l in open(tpath)]
        if ds.get("n"):
            target = target[:ds["n"]]
    else:
        target = pool_cases
    print(f"# 目标 case={len(target)}(候选池 relation 数={len(by_rel)},唯一候选串={sum(len(v) for v in by_rel.values())})", flush=True)

    memo = {}                                                     # str → (ids, ambiguous):跨 case 复用,杀掉几亿次重复 tokenize
    def ftids(v):
        if v not in memo:
            ids_all = first_token_ids(tok, v, aliases)                          # 检测/投影用全变体
            ids_sp = first_token_ids(tok, v, aliases, space_only=True)          # 歧义只判正文自然形(带空格)
            memo[v] = (ids_all, (not ids_sp) or is_ambiguous(tok, ids_sp))
        return memo[v]

    all_uniq = sorted({o for vs in by_rel.values() for o in vs})   # 跨 relation 回填池(频率代表已由去重前分布近似)
    rng = random.Random(42)
    out, n_short_samerel, n_backfilled = {}, 0, 0
    stats = {}
    for c in sorted(target, key=lambda x: x["case_id"]):
        o_old, o_new = str(c["o_old"]), str(c["o_new"])
        lo, ln = o_old.lower(), o_new.lower()

        def ok(v):
            vl = v.lower()
            if vl in (lo, ln) or vl in lo or lo in vl or vl in ln or ln in vl:
                return False
            ids, amb = ftids(v)
            return bool(ids) and not amb

        pool = [v for v in by_rel.get(c.get("r") or "_", []) if ok(v)]
        rng.shuffle(pool)
        n_same = min(len(pool), 20)
        if len(pool) < 20:                                         # 跨 relation 频率回填(prereg §0 注:打标)
            n_short_samerel += 1
            extra = [v for v in all_uniq if v not in pool and ok(v)]
            rng.shuffle(extra)
            pool = pool + extra[:20 - len(pool)]
            if len(pool) == 20:
                n_backfilled += 1
        out[c["case_id"]] = pool[:20]
        stats[c["case_id"]] = n_same
    out["_stats_n_same_relation"] = stats                          # 逐 case 同 relation 数(CONSORT/敏感性用)
    json.dump(out, open(args.out_distractors, "w"), ensure_ascii=False)
    full = sum(1 for k, v in out.items() if not k.startswith("_") and len(v) == 20)
    print(f"# distractor 池 → {args.out_distractors}  ({len(out)-1} case;满 20 个:{full};"
          f"同 relation 不足 20:{n_short_samerel}(其中回填补满 {n_backfilled});仍不足 20 的 run 时跳过)")
    print(f"# 敏感性备注:主分析全 case;n_same_relation<10 的 case 子集做敏感性(prereg §0)。")


# ---------------------------------------------------------------- 分组(复用 census 逻辑)
def load_groups(cfg, editor, cases, aliases, decode="greedy", seed_sel=None):
    ds = cfg["dataset"]
    pat = os.path.join(cfg["out_dir"], f"{cfg['model_tag']}_{editor}_{ds['tag']}_r*.jsonl")
    by = collections.defaultdict(dict)
    for sh in sorted(globlib.glob(pat)):
        for line in open(sh):
            try:
                d = json.loads(line)
            except Exception:
                continue
            if (d.get("probe") == "efficacy" and d.get("decode", "greedy") == decode
                    and (seed_sel is None or d.get("seed") == seed_sel) and d["case_id"] in cases):
                by[d["case_id"]][d["budget"]] = d
    groups = {"a1": [], "a2rev": [], "a2held": [], "calib": []}
    for cid in sorted(by):
        bud = by[cid]; c = cases[cid]
        b0, b3 = bud.get("B0"), bud.get("B3")
        if not b0 or not b3:
            continue
        s, o_old = c.get("s") or "", c["o_old"]
        if str(o_old).lower() in str(s).lower():
            continue                                          # subject-overlap 整条剔除
        clean = lambda t: metrics._without_subject(t or "", s)
        b0ok = metrics.hit(clean(b0["answer"]), c["o_new"], aliases) and not metrics.hit(clean(b0["answer"]), o_old, aliases)
        rev = bool(b0ok and metrics.hit(clean(b3["answer"]), o_old, aliases))
        clr_w = wide_hit(b3.get("cot", ""), o_old, aliases)
        rec = {"case_id": cid, "cot": b3.get("cot", ""), "answer": b3.get("answer", "")}
        if not clr_w:
            groups["a1"].append(rec)
        elif rev:
            groups["a2rev"].append(rec)
        elif b0ok:
            groups["a2held"].append(rec)
    groups["calib"] = groups["a2held"][:10]                   # 前 10 held∩CLR1 做 calibration(排除出推断)
    groups["a2held"] = groups["a2held"][10:]
    return groups


# ---------------------------------------------------------------- 探针主体
def cmd_run(args):
    import torch
    import think_budget as tb
    cfg = __import__("yaml").safe_load(open(args.config))
    cases = {c["case_id"]: c for c in (json.loads(l) for l in open(cfg["dataset"].get("fallback_path", cfg["dataset"]["path"])))}
    aliases = json.load(open(args.aliases))
    distract = json.load(open(args.out_distractors))
    if args.tag:                                              # 扩展梯:覆盖 dataset.tag(如 cf200samp / cf200memit)
        cfg["dataset"]["tag"] = args.tag
    groups = load_groups(cfg, args.editor, cases, aliases, decode=args.decode, seed_sel=args.seed_select)
    want = set(args.groups.split(","))
    todo = [(g, r) for g in ("a1", "a2rev", "a2held", "calib") if g in want for r in groups[g]]
    if args.smoke:
        todo = todo[:args.smoke]
    dev = args.device if args.device is not None else args.rank
    todo = [t for i, t in enumerate(todo) if i % args.world == args.rank]      # 8 卡分片(同 run_pilot 约定)
    if args.world > 1 and args.out.endswith(".jsonl"):
        args.out = args.out[:-6] + f"_r{args.rank}of{args.world}.jsonl"        # 每 rank 独立分片文件
    print(f"# groups: {{ {', '.join(f'{g}:{len(v)}' for g, v in groups.items())} }}  "
          f"本片={len(todo)}(rank {args.rank}/{args.world}, dev {dev})  mode={args.mode}  → {args.out}")

    # —— 模型加载:edited 复用 logit_lens 的 editor 通道;base 直接 AutoModel ——
    if args.mode == "edited":
        from run_pilot import resolve
        from edit_loop import HP_CLS, restore
        R = resolve(cfg, args.editor, args.rank, args.world, dev)
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
    else:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from r1_tokenizer import fix_r1_tokenizer
        name = os.environ.get("WHYAAAI_MODEL")
        dtype = {"float32": torch.float32}.get(os.environ.get("WHYAAAI_DTYPE", "float32"), torch.float32)
        tok = fix_r1_tokenizer(AutoTokenizer.from_pretrained(name), name)
        model = AutoModelForCausalLM.from_pretrained(name, torch_dtype=dtype, device_map=f"cuda:{dev}").eval()
        ed = None
    model.eval()
    W_U, norm = model.lm_head.weight, model.model.norm
    nL = model.config.num_hidden_layers
    lo_band, hi_band = args.band                              # decoder 层号(hs 索引 = 层号+1)

    bos = "" if os.environ.get("WHYAAAI_NO_BOS") else (tok.bos_token or "")   # G1:与 think_budget._gen 同逻辑
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    consort = collections.Counter()
    with open(args.out, "a") as f:
        f.write(json.dumps({"_meta": True, "mode": args.mode, "band": args.band, "groups": {g: len(v) for g, v in groups.items()},
                            "dtype": os.environ.get("WHYAAAI_DTYPE"), "model": os.environ.get("WHYAAAI_MODEL"),
                            "prereg": "prereg-wseries.md"}) + "\n")
        done = set()
        if os.path.exists(args.out):
            for l in open(args.out):
                try:
                    done.add(json.loads(l).get("case_id"))
                except Exception:
                    pass
        for gname, rec in todo:
            cid = rec["case_id"]
            if cid in done:
                continue
            c = cases[cid]
            o_old, o_new, subj, q = str(c["o_old"]), str(c["o_new"]), c.get("s") or "", c["prompt"]
            dl = distract.get(cid, [])
            if len(dl) < 20:
                consort["skip_distractor_short"] += 1
                continue
            oid = first_token_ids(tok, o_old, aliases)
            nid = first_token_ids(tok, o_new, aliases)
            amb = is_ambiguous(tok, oid)
            did = [first_token_ids(tok, dv, {}) for dv in dl]
            wcopy = None
            try:
                if args.mode == "edited":
                    _, _, wcopy = ed.edit(prompts=[q], ground_truth=[o_old], target_new=[o_new],
                                          subject=[subj], sequential_edit=True)
                    # G2:重编辑后 B0 greedy 复现 b0ok
                    _, a0, _ = tb.generate_with_budget(model, tok, q, "B0")
                    a0c = metrics._without_subject(a0, subj)
                    g2 = bool(metrics.hit(a0c, o_new, aliases) and not metrics.hit(a0c, o_old, aliases))
                    if not g2:
                        consort["fail_G2"] += 1
                        f.write(json.dumps({"case_id": cid, "group": gname, "gate": "G2_fail"}) + "\n"); f.flush()
                        continue
                # —— G1:逐字节复刻产链前缀;探针文本 = 前缀 + 存盘 cot ——
                prefix = bos + tb.TPL.format(q=q)
                text = prefix + rec["cot"]
                enc = tok(text, return_tensors="pt", add_special_tokens=False, return_offsets_mapping=True)
                offs = enc.pop("offset_mapping")[0].tolist()
                ids_t = enc["input_ids"].to(model.device)
                seq = ids_t.shape[1]
                chain_from = next((i for i, (s0, _) in enumerate(offs) if s0 >= len(prefix)), seq)
                # —— G3:teacher-forced argmax 一致率(链内,预测下一 token)——
                with torch.no_grad():
                    out = model(input_ids=ids_t, output_hidden_states=True)
                pred = out.logits[0, :-1].argmax(-1)
                tgt = ids_t[0, 1:]
                span = slice(max(chain_from - 1, 0), seq - 1)
                agree = float((pred[span] == tgt[span]).float().mean()) if seq - 1 > chain_from else 1.0
                g3 = agree >= 0.95
                # —— 排除掩码(char→token via offsets;text 原文上算)——
                eligible = [True] * seq
                for i in range(chain_from):
                    eligible[i] = False                                        # 只测链
                for (a, b) in char_occurrences(text, surface_variants(subj, {})):
                    for i, (s0, e0) in enumerate(offs):
                        if s0 < b + 0 and e0 > a:                              # 与 subject span 重叠
                            for j in range(max(0, i - 10), min(seq, i + 11)):
                                eligible[j] = False
                occ = char_occurrences(text[len(prefix):], surface_variants(o_old, aliases))
                first_m = None
                for (a, b) in sorted(occ):
                    a2, b2 = a + len(prefix), b + len(prefix)
                    toks = [i for i, (s0, e0) in enumerate(offs) if s0 < b2 and e0 > a2]
                    if toks and first_m is None:
                        first_m = min(toks)
                    for i in toks:
                        eligible[i] = False
                        if i - 1 >= 0:
                            eligible[i - 1] = False
                if first_m is not None:                                        # 首现后全部后缀剔除(防 induction)
                    for i in range(first_m, seq):
                        eligible[i] = False
                    win_lo, win_hi = max(chain_from, first_m - 20), max(chain_from, first_m - 5)
                    prewin = list(range(win_lo, win_hi))                       # A2 前窗 [m-20, m-5)
                else:
                    prewin = None
                el_idx = [i for i in range(seq) if eligible[i]]
                # —— 候选列投影:每层每合格位,o_old/o_new/d1..20 取各自变体 max ——
                cand_sets = [oid, nid] + did
                flat = sorted({i for s0 in cand_sets for i in s0})
                col = {i: k for k, i in enumerate(flat)}
                Wc = W_U[flat, :]                                              # [C,H]
                hs = out.hidden_states                                         # hs[k]=layer k-1 输出
                per_layer = []                                                 # 每 decoder 层:{z_old_max, z_d_max, n_pos}
                z_pre = []                                                     # A2 前窗 per-layer z_old_max
                probe_idx = el_idx if el_idx else []
                for L in range(nL):                                            # decoder 层号 L ↔ hs[L+1]
                    h = hs[L + 1][0]
                    logit = (norm(h[probe_idx]) @ Wc.T).float() if probe_idx else None   # [P,C]
                    row = {"L": L}
                    if logit is not None and len(probe_idx):
                        cl = []
                        for s0 in cand_sets:
                            cl.append(logit[:, [col[i] for i in s0]].max(-1).values)     # [P] per 候选
                        M = torch.stack(cl)                                    # [22,P]
                        d = M[2:]                                              # distractors
                        mu, sd = d.mean(0), d.std(0).clamp_min(1e-6)
                        z_all = (M - mu) / sd                                  # 22×P
                        row["z_old_max"] = float(z_all[0].max())
                        row["z_new_max"] = float(z_all[1].max())
                        # 置换 null:每个 distractor 当伪目标(null 池=其余 19)
                        zd = []
                        for k in range(20):
                            others = torch.cat([d[:k], d[k + 1:]])
                            zd.append(float(((d[k] - others.mean(0)) / others.std(0).clamp_min(1e-6)).max()))
                        row["z_d_max"] = zd
                    per_layer.append(row)
                    if prewin:
                        hpw = norm(h[prewin]) @ Wc.T
                        dpw = torch.stack([hpw[:, [col[i] for i in s0]].max(-1).values for s0 in cand_sets])
                        mu, sd = dpw[2:].mean(0), dpw[2:].std(0).clamp_min(1e-6)
                        z_pre.append(float(((dpw[0] - mu) / sd).max()))
                # case 级 max-stat(预注册带内)
                band = [r for r in per_layer if lo_band <= r["L"] <= hi_band and "z_old_max" in r]
                S_old = max((r["z_old_max"] for r in band), default=None)
                S_d = [max(r["z_d_max"][k] for r in band) for k in range(20)] if band else []
                positive = bool(S_old is not None and S_d and S_old > max(S_d))
                row = {"case_id": cid, "group": gname, "mode": args.mode, "ambiguous_1sttok": amb,
                       "g3_agree": round(agree, 4), "g3_pass": g3, "n_eligible": len(el_idx),
                       "n_chain_tok": seq - chain_from, "first_mention_tok": first_m,
                       "S_old": S_old, "S_d_max": (max(S_d) if S_d else None), "positive": positive,
                       "z_pre_by_layer": [round(z, 3) for z in z_pre] if prewin else None,
                       "per_layer_zold": [round(r.get("z_old_max", float("nan")), 3) for r in per_layer],
                       "per_layer_znew": [round(r.get("z_new_max", float("nan")), 3) for r in per_layer]}
                f.write(json.dumps(row, ensure_ascii=False) + "\n"); f.flush()
                consort[f"done_{gname}"] += 1
                del out, hs
                torch.cuda.empty_cache()
                print(f"[{cid}|{gname}] agree={agree:.3f} elig={len(el_idx)} S_old={S_old and round(S_old,2)} "
                      f"maxSd={S_d and round(max(S_d),2)} pos={positive}")
            except Exception as e:
                consort["error"] += 1
                f.write(json.dumps({"case_id": cid, "error": repr(e)}) + "\n"); f.flush()
                print(f"[case-fail] {cid}: {e}")
            finally:
                if wcopy is not None:
                    restore(model, wcopy)
    print("# CONSORT:", dict(consort))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build-distractors")
    b.add_argument("--cases", default="data/counterfact.jsonl", help="候选池来源(全 CF)")
    b.add_argument("--config", default="experiments/probe32b.yaml",
                   help="只给该 config 的探测子集(cf200)建 distractor;设空串则全量")
    b.add_argument("--aliases", default="data/aliases.json")
    b.add_argument("--out-distractors", default="data/wa_distractors.json")
    b.add_argument("--model", default=None)
    r = sub.add_parser("run")
    r.add_argument("--config", required=True)
    r.add_argument("--editor", default="ROME")
    r.add_argument("--mode", choices=["edited", "base"], required=True)
    r.add_argument("--rank", type=int, default=0)
    r.add_argument("--world", type=int, default=1)
    r.add_argument("--device", type=int, default=None, help="不给则用 rank 作卡号")
    r.add_argument("--groups", default="a1,a2rev,a2held,calib")
    r.add_argument("--band", type=int, nargs=2, default=[16, 48])
    r.add_argument("--aliases", default="data/aliases.json")
    r.add_argument("--out-distractors", default="data/wa_distractors.json")
    r.add_argument("--out", required=True)
    r.add_argument("--smoke", type=int, default=0)
    r.add_argument("--tag", default=None, help="覆盖 dataset.tag(扩展梯:cf200samp/cf200memit 等)")
    r.add_argument("--decode", default="greedy", help="sample=F3 采样链")
    r.add_argument("--seed-select", type=int, default=None, help="采样链只取该 seed(0/1/2 各跑一轮,输出分文件)")
    args = ap.parse_args()
    if args.cmd == "build-distractors":
        cmd_build_distractors(args)
    else:
        cmd_run(args)


if __name__ == "__main__":
    main()
