"""思考预算控制器 B0–B4 (plan §12.1)。prefill/模板字符串逐字提取自 R-TOFU，
完整审计见 analysis/03_rtofu.md。

口径锚点 (source/R-TOFU, base = DeepSeek-R1-Distill-Llama-8B)：
  - DefaultCoT 模板   test_cot.py:245
  - ZeroThink prefill test.py:16
  - LessThink prefill test.py:18
模板全角竖线 U+FF5C，与 DeepSeek 官方 chat_template 的 add_generation_prompt 分支
('<｜Assistant｜><think>\\n') 逐字一致。

注意点② 定案 (plan §12.1)：<think>/</think> 在 R1-Distill-Qwen-7B 与 -Llama-8B 的
tokenizer 里均**不是**特殊 token（不在 added_tokens_decoder；User/Assistant/BOS/EOS 才是），
故 </think> 走**文本检测**即可，无需 token-id StoppingCriteria。证据见 03_rtofu.md §4。
"""
import torch  # 保留：B4 若日后改 token-id StoppingCriteria / 下游 steering 钩子需要

# --- R-TOFU 逐字模板（全角竖线 U+FF5C，复制时勿替换成半角 |）---
TPL = "<｜User｜>{q}<｜Assistant｜><think>\n"                      # DefaultCoT  test_cot.py:245
ZEROTHINK = "<｜User｜>{q}<｜Assistant｜><think>\n\n</think>\n\n"    # ZeroThink   test.py:16
# R-TOFU 原版 LessThink 是“固定假思考”（单一字符串）；我们主协议把它推广为“思考至 N token
# 截断”（plan §2.4，即下方 B1/B2/B3 的 CAP 截断）。此常量仅留作消融/口径对照之用。
LESSTHINK_CANNED = ("<｜User｜>{q}<｜Assistant｜><think>\n"
                    "Okay, the user asked this, I can answer it without thinking much.\n"
                    "</think>\n\n")                               # LessThink   test.py:18

THINK_END = "</think>"
WAIT = "\nWait, let me double-check this."
CAP = {"B1": 256, "B2": 1024, "B3": 8192, "B4": 8192}

def _gen(model, tok, text, max_new):
    ids = tok(text, return_tensors="pt").to(model.device)
    out = model.generate(**ids, max_new_tokens=max_new, do_sample=False,
                         pad_token_id=tok.eos_token_id)
    # skip_special_tokens=True：<think>/</think> 非特殊 token 不会被剥离 (03_rtofu.md §4)，
    # 同时滤掉 <｜end▁of▁sentence｜> 等，避免污染 answer 的规则判分（与 R-TOFU test.py:39 一致）。
    return tok.decode(out[0][ids["input_ids"].shape[1]:],
                      skip_special_tokens=True)

def _ntok(tok, s):
    return len(tok(s, add_special_tokens=False)["input_ids"])

def generate_with_budget(model, tok, q, budget):
    """返回 (cot, answer, full_text)。budget ∈ {B0,B1,B2,B3,B4}"""
    if budget == "B0":                      # ZeroThink: 逐字复用 R-TOFU 闭合空思考块
        text = ZEROTHINK.format(q=q)
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
