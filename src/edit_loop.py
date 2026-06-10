"""单条编辑协议主循环 (plan §12.2): edit -> 全档生成 -> finally restore. 分片: case_id % world == rank."""
import json, os, torch
from easyeditor import BaseEditor, ROMEHyperParams, MEMITHyperParams
from easyeditor.util import nethook
from think_budget import generate_with_budget

HP_CLS = {"ROME": ROMEHyperParams, "MEMIT": MEMITHyperParams}

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
    yield "open", f"Tell me about {case['subject']}."

def run(cases, editor_name, hparams_path, budgets, out_path, rank=0, world=1):
    done = set()
    if os.path.exists(out_path):
        done = {json.loads(l)["case_id"] for l in open(out_path)}
    hp = HP_CLS[editor_name].from_hparams(hparams_path)
    ed = BaseEditor.from_hparams(hp)
    model, tok = ed.model, ed.tok
    with open(out_path, "a") as f:
        for c in cases:
            if c["case_id"] % world != rank or c["case_id"] in done:
                continue
            _, _, wcopy = ed.edit(prompts=[c["prompt"]],
                                  ground_truth=[c["o_old"]],
                                  target_new=[c["o_new"]],
                                  sequential_edit=False)
            try:
                for b in budgets:
                    for ptype, q in probes(c):
                        cot, ans, _ = generate_with_budget(model, tok, q, b)
                        f.write(json.dumps({"case_id": c["case_id"],
                            "editor": editor_name, "budget": b, "probe": ptype,
                            "q": q, "cot": cot, "answer": ans},
                            ensure_ascii=False) + "\n")
                f.flush()
            finally:
                restore(model, wcopy)        # 任何异常也必须还原
