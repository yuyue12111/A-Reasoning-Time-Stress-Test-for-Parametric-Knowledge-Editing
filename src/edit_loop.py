"""单条编辑协议主循环 (plan §12.2): edit -> 全档生成 -> finally restore。

分片: 按 enumerate 序号 `i % world == rank`（case_id 现为字符串如 'cf_0'，不能取模；
      各片须传**同序**的 cases，分区才是干净覆盖）。
续跑: out_path 里已出现的 case_id 跳过（含失败标记，避免无限重试）。
韧性: 单条 case 出错只记错误标记并继续，不拖垮整片（集群随时杀任务）。
"""
import importlib.metadata, json, math, os, platform, subprocess, sys, torch
from datetime import datetime, timezone
from easyeditor import (BaseEditor, ROMEHyperParams, MEMITHyperParams,
                        AlphaEditHyperParams, FTHyperParams)
from easyeditor.util import nethook
import think_budget
from think_budget import generate_with_budget

HP_CLS = {"ROME": ROMEHyperParams, "MEMIT": MEMITHyperParams,
          "AlphaEdit": AlphaEditHyperParams, "FT": FTHyperParams}
# 注：AlphaEdit 的 cache_c 是进程级全局且跨 edit() 累积（02 笔记 §5）——单条协议下接
# AlphaEdit 须每条 case 重置 cache_c，否则批量干扰从后门进来。pilot 只用 ROME/MEMIT，
# 故此处先不特判；接 AlphaEdit 时在这里加 reset。

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # src/ 的上一级=项目根


def git_provenance():
    """项目根的 git 提交哈希 + 脏标记（plan §6 可复现三件套）。失败回退 'unknown'/None。

    注意 cwd 可能在 source/EasyEdit（它自己也是 git 仓）——故显式 `git -C <项目根>`，否则记成 EasyEdit 的哈希。
    """
    def _g(*a):
        return subprocess.check_output(["git", "-C", _PROJECT_ROOT, *a],
                                       stderr=subprocess.DEVNULL, text=True).strip()
    try:
        return {"git": _g("rev-parse", "HEAD"), "git_dirty": bool(_g("status", "--porcelain"))}
    except Exception:
        return {"git": "unknown", "git_dirty": None}


def software_provenance():
    """Small, read-only environment fingerprint for cross-arm parity audits."""
    packages = {}
    for name in ("transformers", "datasets", "numpy", "accelerate"):
        try:
            packages[name] = importlib.metadata.version(name)
        except Exception:
            packages[name] = None
    try:
        easyedit_git = subprocess.check_output(
            ["git", "-C", os.path.join(_PROJECT_ROOT, "source/EasyEdit"), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        easyedit_git = "unknown"
    return {
        "python": sys.version.split()[0], "platform": platform.platform(),
        "torch": getattr(torch, "__version__", None),
        "torch_cuda": getattr(getattr(torch, "version", None), "cuda", None),
        "packages": packages, "easyedit_git": easyedit_git,
    }


def model_runtime(model, tok, hp):
    """Record the actually loaded model/tokenizer state, not only requested env strings."""
    rec = {
        "requested_model": getattr(hp, "model_name", None),
        "model_class": type(model).__name__, "tokenizer_class": type(tok).__name__,
        "bos_token_id": getattr(tok, "bos_token_id", None),
        "eos_token_id": getattr(tok, "eos_token_id", None),
        "add_bos_token": getattr(tok, "add_bos_token", None),
    }
    cfg = getattr(model, "config", None)
    rec["loaded_model"] = getattr(cfg, "_name_or_path", None)
    params = getattr(model, "parameters", None)
    if callable(params):
        try:
            p = next(params())
            rec["parameter_dtype"] = str(getattr(p, "dtype", None))
            rec["parameter_device"] = str(getattr(p, "device", None))
        except Exception:
            pass
    rec["model_parallel"] = bool(getattr(hp, "model_parallel", False))
    device_map = getattr(model, "hf_device_map", None)
    if isinstance(device_map, dict):
        counts = {}
        for dev in device_map.values():
            key = str(dev)
            counts[key] = counts.get(key, 0) + 1
        rec["hf_device_map_counts"] = counts
        rec["hf_device_map_devices"] = sorted(counts)
    edit_devices = {}
    template = getattr(hp, "rewrite_module_tmp", None)
    for layer in (getattr(hp, "layers", None) or []):
        if not template:
            break
        name = f"{template.format(layer)}.weight"
        try:
            edit_devices[name] = str(nethook.get_parameter(model, name).device)
        except Exception as exc:
            edit_devices[name] = f"ERROR:{type(exc).__name__}"
    if edit_devices:
        rec["edit_weight_devices"] = edit_devices
    return rec


def provenance_header(extra=None):
    """jsonl 首行溯源头（plan §6：git hash + 配置摘要 + seed，须在第一批分片产出前就位，事后补不了）。
    `_meta:true` 标记 → metrics/score 按 `.get('probe')` 自动跳过、续跑按 `.get('case_id')` 自动跳过。"""
    runtime_env = {k: os.environ.get(k) for k in (
        "WHYAAAI_MODEL", "WHYAAAI_DTYPE", "WHYAAAI_NO_BOS",
        "WHYAAAI_WIKI_PARQUET", "WHYAAAI_DEVICE_MAP", "PYTORCH_CUDA_ALLOC_CONF",
        "CUDA_VISIBLE_DEVICES", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")}
    return {"_meta": True, **git_provenance(), "runtime_env": runtime_env,
            "software": software_provenance(),
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "think_budget_cap": getattr(think_budget, "CAP", None), **(extra or {})}


def restore(model, weights_copy):           # editor.py:265 同款
    with torch.no_grad():
        for k, v in weights_copy.items():
            nethook.get_parameter(model, k)[...] = v


def weight_delta_summary(model, weights_copy, chunk_elems=1_000_000):
    """Chunked edit-update norms without materializing a full weight-sized delta tensor.

    This is opt-in diagnostics for P1.  It records the actual post-edit parameter change before
    generation/restore and is deliberately absent from historical runs.
    """
    per_weight = {}
    total_delta_sq = total_base_sq = 0.0
    total_max = 0.0
    with torch.no_grad():
        for name, old in weights_copy.items():
            cur = nethook.get_parameter(model, name)
            cur_flat, old_flat = cur.reshape(-1), old.reshape(-1)
            delta_sq = base_sq = 0.0
            max_abs = 0.0
            for start in range(0, cur_flat.numel(), chunk_elems):
                stop = min(start + chunk_elems, cur_flat.numel())
                c = cur_flat[start:stop].float()
                o = old_flat[start:stop].to(device=c.device, dtype=c.dtype)
                d = c - o
                delta_sq += float((d * d).sum().item())
                base_sq += float((o * o).sum().item())
                if d.numel():
                    max_abs = max(max_abs, float(d.abs().max().item()))
            delta_l2 = math.sqrt(delta_sq)
            base_l2 = math.sqrt(base_sq)
            per_weight[name] = {
                "shape": list(cur.shape), "delta_l2": delta_l2,
                "base_l2": base_l2,
                "relative_l2": delta_l2 / base_l2 if base_l2 else None,
                "max_abs_delta": max_abs,
                "device": str(cur.device), "dtype": str(cur.dtype),
            }
            total_delta_sq += delta_sq
            total_base_sq += base_sq
            total_max = max(total_max, max_abs)
    total_delta = math.sqrt(total_delta_sq)
    total_base = math.sqrt(total_base_sq)
    return {
        "n_weights": len(per_weight), "per_weight": per_weight,
        "aggregate": {
            "delta_l2": total_delta, "base_l2": total_base,
            "relative_l2": total_delta / total_base if total_base else None,
            "max_abs_delta": total_max,
        },
    }


def _resume_signature(meta, editor_name, budgets, rank, world, overrides, sampling,
                      suppress_cfg, probe_sel, diagnostics_cfg):
    """Fields that must be identical before appending to an existing new-format shard."""
    return {"config_sha256": (meta or {}).get("config_sha256"),
            "code_sha256": (meta or {}).get("code_sha256"),
            "dataset": (meta or {}).get("dataset"), "run": (meta or {}).get("run"),
            "editor": editor_name, "budgets": budgets, "rank": rank, "world": world,
            "overrides": overrides, "sampling": sampling, "suppress": suppress_cfg,
            "probe_sel": probe_sel, "diagnostics": diagnostics_cfg}


def _assert_resume_compatible(out_path, expected):
    """Refuse stale-tag mixing before the expensive model load.

    Legacy callers without config/code hashes retain their old permissive behavior.  Every X2/X3
    run carries both hashes, so a stale/mutated shard cannot be silently resumed.
    """
    if not expected.get("config_sha256") or not expected.get("code_sha256"):
        return
    header = None
    for line in open(out_path):
        row = json.loads(line)
        if row.get("_meta"):
            header = row
            break
    if header is None:
        raise RuntimeError(f"refusing to append new-format run to headerless shard: {out_path}")
    got = {key: header.get(key) for key in expected}
    if json.dumps(got, sort_keys=True, ensure_ascii=False) != json.dumps(expected, sort_keys=True, ensure_ascii=False):
        changed = [key for key in expected if got.get(key) != expected.get(key)]
        raise RuntimeError(f"resume signature mismatch for {out_path}; changed={changed}. Use a new tag or restore exact files.")


def probes(case, which=None):                # 探针：efficacy/paraphrase/locality/open
    # which=None → 全 5 探针(7/14/32B 主口径,行为不变);which=list → 只跑选中的
    # (capability 锚点 8B/70B 用 [efficacy, locality]:图只用 ES/CLR/RR=efficacy + Loc=locality,
    #  para/open 不入任何作图指标 → 砍掉省 3 条 B3 长链/case ≈ 2.5×,不改任何已绘数值)。
    sel = set(which) if which else None
    def ok(name):
        return sel is None or name in sel or (name.startswith("para") and "paraphrase" in sel)
    if ok("efficacy"):
        yield "efficacy", case["prompt"]
    if case.get("hop_q") and ok("hop"):         # E-MULTIHOP/W3:编辑后问多跳题(hops[0],绝不点名 o_old)
        yield "hop", case["hop_q"]
    for i, p in enumerate(case.get("paraphrases", [])[:2]):
        if ok(f"para{i}"):
            yield f"para{i}", p
    if case.get("neighborhood") and ok("locality"):
        yield "locality", case["neighborhood"][0]
    if ok("open"):
        yield "open", f"Tell me about {case['s']}."


def decode_arms(sampling):
    """解码臂列表 [(decode, seed, temperature, gen_kwargs), ...]（plan §2.5「greedy + temp0.6×3 seeds」）。
    greedy 臂恒在（首窗主口径，sumandplan §6.3）；sampling={'temperature':t,'seeds':[..]} 时每 seed 追加采样臂。
    """
    arms = [("greedy", None, None, {})]
    if sampling:
        t = sampling.get("temperature", 0.6)
        for s in sampling.get("seeds", []):
            arms.append(("sample", s, t, {"do_sample": True, "temperature": t, "seed": s}))
    return arms


def run(cases, editor_name, hparams_path, budgets, out_path, rank=0, world=1,
        overrides=None, sampling=None, meta=None, suppress_cfg=None, probe_sel=None,
        diagnostics_cfg=None):
    done = set()
    if os.path.exists(out_path):             # 续跑跳过；用 .get 兼容 _meta 头行（无 case_id）
        done = {cid for l in open(out_path) if (cid := json.loads(l).get("case_id"))}
    had_content = os.path.exists(out_path) and os.path.getsize(out_path) > 0
    if had_content:
        _assert_resume_compatible(out_path, _resume_signature(
            meta, editor_name, budgets, rank, world, overrides, sampling, suppress_cfg, probe_sel,
            diagnostics_cfg))
    _aliases = json.load(open(os.path.join(_PROJECT_ROOT, "data/aliases.json"))) if suppress_cfg else None
    _sup_source = (suppress_cfg or {}).get("source", "o_old")   # o_old=现fix | o_new=方向对照 | placebo=特异性对照(E-SUP-BATTERY/W1)
    _placebo = None
    if suppress_cfg:                         # RQ3 修复(plan v1.27)：逐 case 现构抑制器;source 决定压哪个词
        from suppress import build_old_token_ids, make_processor
        if _sup_source == "placebo":         # BLIND 频率/长度匹配供体(src/placebo_donor.py 离线锁定,看 RR 前定)
            _pj = suppress_cfg.get("placebo_map", "data/placebo_donors.json")
            _placebo = json.load(open(os.path.join(_PROJECT_ROOT, _pj)))
    hp = HP_CLS[editor_name].from_hparams(hparams_path)
    for k, v in (overrides or {}).items():   # run_pilot 覆盖 model_name/stats_dir/device/layers
        setattr(hp, k, v)
    if os.environ.get("WHYAAAI_MODEL"):      # 离线平台:env 指本地模型绝对路径(HF id 离线不解析,与 base_probe 一致)
        hp.model_name = os.environ["WHYAAAI_MODEL"]
    # pilot-blocker 修复：R1-Distill-Qwen 含 'qwen' 不含 'qwen2' → 落 editor.py 老 Qwen1 分支
    # （fp32 kwarg + 错 eos）。方案 A monkeypatch 必须在 from_hparams 加载模型之前生效（sumandplan §5）。
    from vendor_patches.easyedit_qwen2_loader import apply as apply_qwen_loader_patch
    apply_qwen_loader_patch()
    # MEMIT/AlphaEdit-blocker 修复：layer_stats 写死的脚本式数据集 id 在 datasets≥3 必崩
    # （mom2 协方差语料）→ 映射到现行 parquet 仓。须在首次触发 mom2 的 edit() 前生效。
    from vendor_patches.easyedit_mom2_dataset import apply as apply_mom2_dataset_patch
    apply_mom2_dataset_patch()
    ed = BaseEditor.from_hparams(hp)
    model, tok = ed.model, ed.tok
    # R1-Llama 修复必须落在【真正用于生成/解码的 ed.tok】上:EasyEdit 的 llama 分支不走被 patch 的
    # AutoTokenizer → qwen2_loader 的 fix 漏掉 ed.tok（现象:生成连贯但 decode 仍 Ġ/Ċ → 判分炸)。
    # 这里直接对 ed.tok 兜底(fix_r1_tokenizer 幂等:非 Metaspace 原样、Qwen 零影响)。
    try:
        from r1_tokenizer import fix_r1_tokenizer
        tok = fix_r1_tokenizer(tok, hp.model_name)
        ed.tok = tok                                  # 同步回 ed,后续若有用 ed.tok 处一致
    except Exception as e:
        print(f"[edit_loop] r1_tokenizer 兜底修复跳过:{e!r}")
    arms = decode_arms(sampling)                  # greedy(+采样臂)；每臂一行 jsonl
    with open(out_path, "a") as f:
        if not had_content:                       # 新分片：先写溯源头（plan §6，事后补不了）
            hdr = provenance_header({"editor": editor_name, "budgets": budgets,
                                     "rank": rank, "world": world, "overrides": overrides,
                                     "sampling": sampling, "suppress": suppress_cfg,
                                     "diagnostics": diagnostics_cfg,
                                     "actual_runtime": model_runtime(model, tok, hp), **(meta or {})})
            f.write(json.dumps(hdr, ensure_ascii=False) + "\n"); f.flush()
        for i, c in enumerate(cases):
            if i % world != rank or c["case_id"] in done:
                continue
            wcopy = None
            _sup_target = None
            _sup_token_ids = []
            _diagnostics = None
            try:
                # ⚠ sequential_edit=True 是刻意的、不可改回 False（血泪雷点）：
                # EasyEdit 的 edit_requests 在 sequential_edit=False 时，会在 edit() **返回前**就把
                # ROME/MEMIT 权重还原回基座（editor.py:406-409 的末尾 else 分支 copy_to_param 回写）。
                # 那样我们随后的 generate_with_budget 全程在**未编辑的基座**上生成 —— 编哪层都一样、
                # 生成式 ES 测的全是基座（曾导致三层 md5 全等、08 的"rewrite_acc≫生成式 ES"被污染）。
                # sequential_edit=True 时 ROME/MEMIT 不在内部还原（editor.py:384-393），编辑保留到我们
                # 生成完，再由下方 finally:restore(model,wcopy) 做单条协议的还原。我们每次只传 1 条
                # request、每条 case 后必还原 → 无跨条累积，单条编辑协议成立。
                _, _, wcopy = ed.edit(prompts=[c["prompt"]],
                                      ground_truth=[c["o_old"]],
                                      target_new=[c["o_new"]],
                                      subject=[c["s"]],          # ROME/MEMIT 必需
                                      sequential_edit=True)
                if (diagnostics_cfg or {}).get("weight_delta"):
                    try:
                        _diagnostics = {"weight_delta": weight_delta_summary(
                            model, wcopy, int((diagnostics_cfg or {}).get("chunk_elems", 1_000_000)))}
                    except Exception as diag_exc:
                        _diagnostics = {"weight_delta_error": repr(diag_exc)}
                sup_eff = None              # RQ3：默认仅 efficacy 探针压;locality/para 不碰 → Loc 结构性安全
                # G1/B25(终极review):suppress.apply_to 可扩探针集(如 [efficacy,hop] 测 cond-c 盲区——
                # 多跳 query 上开抑制器,hop-ES 掉=部署门看不到的编辑侧伤害)。缺省 ["efficacy"]=历史行为不变。
                _sup_probes = set((suppress_cfg or {}).get("apply_to", ["efficacy"]))
                if suppress_cfg:
                    if _sup_source == "o_new":
                        _tgt, _al = c["o_new"], _aliases               # 方向对照:压编辑值 → 若反降回退=符号错(近致命)
                    elif _sup_source == "placebo":
                        _tgt, _al = (_placebo or {}).get(c["case_id"]), {}   # 无关匹配词,不带别名
                    else:
                        _tgt, _al = c["o_old"], _aliases               # 默认:压旧值=现 fix
                    if _tgt:
                        _ids = build_old_token_ids(tok, _tgt, _al)
                        _sup_target = str(_tgt)
                        _sup_token_ids = sorted(int(x) for x in _ids)
                        sup_eff = {"processor": make_processor(_ids, suppress_cfg["penalty"]),
                                   "scope": suppress_cfg.get("scope", "think")}
                for b in budgets:
                    for ptype, q in probes(c, probe_sel):
                        for decode, seed, temp, gk in arms:
                            _selected = bool(sup_eff is not None and ptype in _sup_probes)
                            _proc = sup_eff.get("processor") if _selected else None
                            _calls0 = getattr(_proc, "calls", None)
                            cot, ans, _ = generate_with_budget(model, tok, q, b,
                                suppress=(sup_eff if ptype in _sup_probes else None), **gk)
                            _calls1 = getattr(_proc, "calls", None)
                            _call_delta = (_calls1 - _calls0) if (
                                isinstance(_calls0, int) and isinstance(_calls1, int)) else None
                            rec = {"case_id": c["case_id"],
                                "editor": editor_name, "budget": b, "probe": ptype,
                                "decode": decode, "seed": seed, "temperature": temp,
                                "q": q, "cot": cot, "answer": ans}
                            if suppress_cfg:
                                rec["suppress_trace"] = {
                                    "source": _sup_source,
                                    "target": _sup_target,
                                    "token_ids": _sup_token_ids,
                                    "selected": _selected,
                                    "active": (_selected and (_call_delta is None or _call_delta > 0)),
                                    "processor_calls": _call_delta,
                                    "scope": suppress_cfg.get("scope", "think"),
                                    "penalty": suppress_cfg.get("penalty")}
                            if _diagnostics is not None:
                                rec["diagnostics"] = _diagnostics
                            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
            except Exception as e:               # 坏 case 记标记后继续；续跑时被 done 跳过
                f.write(json.dumps({"case_id": c["case_id"], "error": repr(e)},
                                   ensure_ascii=False) + "\n"); f.flush()
                print(f"[case-fail] {c['case_id']}: {e}")
            finally:
                if wcopy is not None:            # 编辑成功过就必须还原（异常路径也还原）
                    restore(model, wcopy)
