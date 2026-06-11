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


def run(cases, editor_name, hparams_path, budgets, out_path, rank=0, world=1):
    done = set()
    if os.path.exists(out_path):
        done = {json.loads(l)["case_id"] for l in open(out_path)}
    hp = HP_CLS[editor_name].from_hparams(hparams_path)
    ed = BaseEditor.from_hparams(hp)
    model, tok = ed.model, ed.tok
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
                        cot, ans, _ = generate_with_budget(model, tok, q, b)
                        f.write(json.dumps({"case_id": c["case_id"],
                            "editor": editor_name, "budget": b, "probe": ptype,
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
