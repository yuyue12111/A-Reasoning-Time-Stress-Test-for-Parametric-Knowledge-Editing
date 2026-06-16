"""单条编辑协议主循环 (plan §12.2): edit -> 全档生成 -> finally restore。

分片: 按 enumerate 序号 `i % world == rank`（case_id 现为字符串如 'cf_0'，不能取模；
      各片须传**同序**的 cases，分区才是干净覆盖）。
续跑: out_path 里已出现的 case_id 跳过（含失败标记，避免无限重试）。
韧性: 单条 case 出错只记错误标记并继续，不拖垮整片（集群随时杀任务）。
"""
import json, os, subprocess, torch
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


def provenance_header(extra=None):
    """jsonl 首行溯源头（plan §6：git hash + 配置摘要 + seed，须在第一批分片产出前就位，事后补不了）。
    `_meta:true` 标记 → metrics/score 按 `.get('probe')` 自动跳过、续跑按 `.get('case_id')` 自动跳过。"""
    return {"_meta": True, **git_provenance(),
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "think_budget_cap": getattr(think_budget, "CAP", None), **(extra or {})}


def restore(model, weights_copy):           # editor.py:265 同款
    with torch.no_grad():
        for k, v in weights_copy.items():
            nethook.get_parameter(model, k)[...] = v


def probes(case):                            # 探针：efficacy/paraphrase/locality/open
    yield "efficacy", case["prompt"]
    for i, p in enumerate(case.get("paraphrases", [])[:2]):
        yield f"para{i}", p
    if case.get("neighborhood"):
        yield "locality", case["neighborhood"][0]
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
        overrides=None, sampling=None, meta=None):
    done = set()
    if os.path.exists(out_path):             # 续跑跳过；用 .get 兼容 _meta 头行（无 case_id）
        done = {cid for l in open(out_path) if (cid := json.loads(l).get("case_id"))}
    had_content = os.path.exists(out_path) and os.path.getsize(out_path) > 0
    hp = HP_CLS[editor_name].from_hparams(hparams_path)
    for k, v in (overrides or {}).items():   # run_pilot 覆盖 model_name/stats_dir/device/layers
        setattr(hp, k, v)
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
    arms = decode_arms(sampling)                  # greedy(+采样臂)；每臂一行 jsonl
    with open(out_path, "a") as f:
        if not had_content:                       # 新分片：先写溯源头（plan §6，事后补不了）
            hdr = provenance_header({"editor": editor_name, "budgets": budgets,
                                     "rank": rank, "world": world, "overrides": overrides,
                                     "sampling": sampling, **(meta or {})})
            f.write(json.dumps(hdr, ensure_ascii=False) + "\n"); f.flush()
        for i, c in enumerate(cases):
            if i % world != rank or c["case_id"] in done:
                continue
            wcopy = None
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
                for b in budgets:
                    for ptype, q in probes(c):
                        for decode, seed, temp, gk in arms:
                            cot, ans, _ = generate_with_budget(model, tok, q, b, **gk)
                            f.write(json.dumps({"case_id": c["case_id"],
                                "editor": editor_name, "budget": b, "probe": ptype,
                                "decode": decode, "seed": seed, "temperature": temp,
                                "q": q, "cot": cot, "answer": ans},
                                ensure_ascii=False) + "\n")
                f.flush()
            except Exception as e:               # 坏 case 记标记后继续；续跑时被 done 跳过
                f.write(json.dumps({"case_id": c["case_id"], "error": repr(e)},
                                   ensure_ascii=False) + "\n"); f.flush()
                print(f"[case-fail] {c['case_id']}: {e}")
            finally:
                if wcopy is not None:            # 编辑成功过就必须还原（异常路径也还原）
                    restore(model, wcopy)
