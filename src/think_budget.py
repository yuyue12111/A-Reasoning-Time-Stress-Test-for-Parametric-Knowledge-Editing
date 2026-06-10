"""思考预算控制器 B0-B4 (plan §12.1, 模板实测自 R-TOFU). HF generate 实现."""
import torch

TPL = "<｜User｜>{q}<｜Assistant｜><think>\n"   # 全角竖线，DeepSeek 官方模板
THINK_END = "</think>"
WAIT = "\nWait, let me double-check this."
CAP = {"B1": 256, "B2": 1024, "B3": 8192, "B4": 8192}

def _gen(model, tok, text, max_new):
    ids = tok(text, return_tensors="pt").to(model.device)
    out = model.generate(**ids, max_new_tokens=max_new, do_sample=False,
                         pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][ids["input_ids"].shape[1]:],
                      skip_special_tokens=False)

def _ntok(tok, s):
    return len(tok(s, add_special_tokens=False)["input_ids"])

def generate_with_budget(model, tok, q, budget):
    """返回 (cot, answer, full_text)。budget ∈ {B0,B1,B2,B3,B4}"""
    if budget == "B0":                      # ZeroThink: 闭合空思考块
        text = TPL.format(q=q) + "\n" + THINK_END + "\n\n"
        ans = _gen(model, tok, text, 256)
        return "", ans, text + ans
    prefix, cot, waits = TPL.format(q=q), "", 0
    while True:
        chunk = _gen(model, tok, prefix + cot,
                     max(64, CAP[budget] - _ntok(tok, cot)))
        if THINK_END in chunk:              # 模型自行结束思考
            head = chunk.split(THINK_END)[0]
            if budget == "B4" and waits < 2:       # s1 式强制延长
                cot += head + WAIT; waits += 1; continue
            cot += head; break
        cot += chunk
        if _ntok(tok, cot) >= CAP[budget]: break   # B1/B2 截断 / 预算耗尽
    text = prefix + cot + "\n" + THINK_END + "\n\n"
    ans = _gen(model, tok, text, 256)
    return cot, ans, text + ans
