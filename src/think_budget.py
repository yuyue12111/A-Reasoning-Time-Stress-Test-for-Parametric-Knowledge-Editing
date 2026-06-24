"""思考预算控制器 B0–B4 (plan §12.1)。prefill/模板字符串逐字提取自 R-TOFU，
完整审计见 analysis/03_rtofu.md。

口径锚点 (source/R-TOFU, base = DeepSeek-R1-Distill-Llama-8B)：
  - DefaultCoT 模板   test_cot.py:245
  - ZeroThink prefill test.py:16
  - LessThink prefill test.py:18
模板全角竖线 U+FF5C，与 DeepSeek 官方 chat_template 的 add_generation_prompt 分支
('<｜Assistant｜><think>\\n') 逐字一致。

注意点② 定案 (plan §12.1，依据经 v1.14 核查订正)：<think>/</think> 在 R1-Distill-Qwen-7B
与 -Llama-8B 的 tokenizer 里是 **added_tokens 在册的原子 token（id 151648/151649，单 token），
但 special=false** —— 并非"普通 BPE 文本"，也并非特殊 token。关键后果不变：`skip_special_tokens=True`
**不剥离** special=false 的它们（实测 `decode("a<think>b</think>c", skip_special_tokens=True)` 原样保留），
故 </think> 走**文本检测**成立，无需 token-id StoppingCriteria。（既是单原子 token，token-id 检测**亦可行**，
留作 B4 备选。）真 eos 是 `<｜end▁of▁sentence｜>`(151643)。证据见 03_rtofu.md §4。
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
CAP = {"B1": 256, "B2": 1024, "B3": 8192, "B4": 8192, "B3M": 16384}   # B3M = genbench 专用长链档(MATH 链常 >8192 被截在 \boxed 前),不入 RQ1/RQ3 主口径锚点

def _gen(model, tok, text, max_new, do_sample=False, temperature=0.6, logits_processor=None):
    ids = tok(text, return_tensors="pt").to(model.device)
    kw = dict(max_new_tokens=max_new, pad_token_id=tok.eos_token_id, do_sample=do_sample)
    if do_sample:                           # 采样臂 (plan §2.5)：仅采样时才传 temperature
        kw["temperature"] = temperature
    if logits_processor is not None:        # RQ3 修复：旧知识抑制 (默认 None → generate 调用逐字节不变)
        from transformers import LogitsProcessorList
        kw["logits_processor"] = LogitsProcessorList([logits_processor])
    out = model.generate(**ids, **kw)
    # skip_special_tokens=True：<think>/</think> 非特殊 token 不会被剥离 (03_rtofu.md §4)，
    # 同时滤掉 <｜end▁of▁sentence｜> 等，避免污染 answer 的规则判分（与 R-TOFU test.py:39 一致）。
    return tok.decode(out[0][ids["input_ids"].shape[1]:],
                      skip_special_tokens=True)

def _ntok(tok, s):
    return len(tok(s, add_special_tokens=False)["input_ids"])

def generate_with_budget(model, tok, q, budget, do_sample=False, temperature=0.6, seed=None, suppress=None, answer_cap=256):
    """返回 (cot, answer, full_text)。budget ∈ {B0,B1,B2,B3,B4}。

    解码臂 (plan §2.5「每条 greedy + temperature 0.6 × 3 seeds」)：
      · do_sample=False（默认）→ greedy；首窗主口径，go/no-go 结论须在 greedy 下成立 (sumandplan §6.3)。
      · do_sample=True + seed → temperature 采样；seed 不为 None 时生成前 torch.manual_seed(seed)，
        使整条轨迹（CoT 截断循环 + B4 延长 + 作答）确定可复现（同 seed 同输入 → 同输出）。
    seed 仅控可复现性；3 个 seed = 每条 3 个采样样本（bootstrap CI 的重采样单元，plan §2.5）。
    """
    if seed is not None:
        torch.manual_seed(seed)
    def g(text, mx, use_sup=False):         # 闭包固化本次调用的解码臂，三处生成口径统一
        lp = suppress["processor"] if (use_sup and suppress) else None   # RQ3 抑制：按生成位点开关
        return _gen(model, tok, text, mx, do_sample=do_sample, temperature=temperature, logits_processor=lp)
    if budget == "B0":                      # ZeroThink: 逐字复用 R-TOFU 闭合空思考块
        text = ZEROTHINK.format(q=q)
        ans = g(text, answer_cap, use_sup=bool(suppress) and suppress["scope"] == "all")   # B0 无链；仅 scope=all 压答案
        return "", ans, text + ans
    prefix, cot, waits = TPL.format(q=q), "", 0
    while True:
        chunk = g(prefix + cot, max(64, CAP[budget] - _ntok(tok, cot)), use_sup=bool(suppress))   # 压链(think/all 都压)
        if THINK_END in chunk:              # 模型自行结束思考
            head = chunk.split(THINK_END)[0]
            if budget == "B4" and waits < 2:       # s1 式强制延长
                cot += head + WAIT; waits += 1; continue
            cot += head; break
        cot += chunk
        if _ntok(tok, cot) >= CAP[budget]: break   # B1/B2 截断 / 预算耗尽
    text = prefix + cot + "\n" + THINK_END + "\n\n"
    ans = g(text, answer_cap, use_sup=bool(suppress) and suppress["scope"] == "all")   # 答案段：仅 scope=all 压(think 只压链)
    return cot, ans, text + ans
