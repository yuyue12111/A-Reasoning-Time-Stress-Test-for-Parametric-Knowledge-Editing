"""单条编辑协议主循环 (plan §12.2): edit -> 全档生成 -> finally restore。

分片: 按 enumerate 序号 `i % world == rank`（case_id 现为字符串如 'cf_0'，不能取模；
      各片须传**同序**的 cases，分区才是干净覆盖）。
续跑: out_path 里已出现的 case_id 跳过（含失败标记，避免无限重试）。
韧性: 单条 case 出错只记错误标记并继续，不拖垮整片（集群随时杀任务）。
"""
import json, os, torch
from easyeditor import (BaseEditor, ROMEHyperParams, MEMITHyperParams,
                        AlphaEditHyperParams, FTHyperParams)
from easyeditor.util import nethook
from think_budget import generate_with_budget

HP_CLS = {"ROME": ROMEHyperParams, "MEMIT": MEMITHyperParams,
          "AlphaEdit": AlphaEditHyperParams, "FT": FTHyperParams}
# 注：AlphaEdit 的 cache_c 是进程级全局且跨 edit() 累积（02 笔记 §5）——单条协议下接
# AlphaEdit 须每条 case 重置 cache_c，否则批量干扰从后门进来。pilot 只用 ROME/MEMIT，
# 故此处先不特判；接 AlphaEdit 时在这里加 reset。


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
        overrides=None, sampling=None):
    done = set()
    if os.path.exists(out_path):
        done = {json.loads(l)["case_id"] for l in open(out_path)}
    hp = HP_CLS[editor_name].from_hparams(hparams_path)
    for k, v in (overrides or {}).items():   # run_pilot 覆盖 model_name/stats_dir/device/layers
        setattr(hp, k, v)
    # pilot-blocker 修复：R1-Distill-Qwen 含 'qwen' 不含 'qwen2' → 落 editor.py 老 Qwen1 分支
    # （fp32 kwarg + 错 eos）。方案 A monkeypatch 必须在 from_hparams 加载模型之前生效（sumandplan §5）。
    from vendor_patches.easyedit_qwen2_loader import apply as apply_qwen_loader_patch
    apply_qwen_loader_patch()
    ed = BaseEditor.from_hparams(hp)
    model, tok = ed.model, ed.tok
    arms = decode_arms(sampling)                  # greedy(+采样臂)；每臂一行 jsonl
    with open(out_path, "a") as f:
        for i, c in enumerate(cases):
            if i % world != rank or c["case_id"] in done:
                continue
            wcopy = None
            try:
                _, _, wcopy = ed.edit(prompts=[c["prompt"]],
                                      ground_truth=[c["o_old"]],
                                      target_new=[c["o_new"]],
                                      subject=[c["s"]],          # ROME/MEMIT 必需
                                      sequential_edit=False)
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
