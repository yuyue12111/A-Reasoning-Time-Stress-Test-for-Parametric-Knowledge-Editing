"""验证 R1-Llama 分词器修复(fix_r1_tokenizer)端到端是否治本。
跑:  export WHYAAAI_MODEL=<本地 R1-Distill-Llama-8B 路径>;  python src/diag_llama.py
修复前 vs 修复后对照:编码保不保空格 / 模板 token 对不对 / 生成是不是正常英文。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from r1_tokenizer import fix_r1_tokenizer
import think_budget

m = os.environ["WHYAAAI_MODEL"]
s = "is the capital of France"

print("=== 修复前(原始 AutoTokenizer)===")
raw = AutoTokenizer.from_pretrained(m)
print("enc:", raw.convert_ids_to_tokens(raw(s, add_special_tokens=False)["input_ids"]))

print("=== 修复后(fix_r1_tokenizer)===")
tok = fix_r1_tokenizer(AutoTokenizer.from_pretrained(m), m)
print("enc:", tok.convert_ids_to_tokens(tok(s, add_special_tokens=False)["input_ids"]), " ← 应带 Ġ、空格回来")
rt = "What is the capital of France?\n</think>"
print("decode round-trip:", repr(tok.decode(tok(rt, add_special_tokens=False)["input_ids"])))
print("  </think> 可见?:", "</think>" in tok.decode(tok(rt, add_special_tokens=False)["input_ids"]))

print("\n=== 修复后 × 我们模板 × 未编辑基座 生成 ===")
model = AutoModelForCausalLM.from_pretrained(m, dtype=torch.bfloat16).to("cuda:0").eval()
for b in ["B0", "B3"]:
    cot, ans, _ = think_budget.generate_with_budget(model, tok, "What is the capital of France?", b)
    print(f"[{b}] cot_chars={len(cot)} | answer={repr(ans[:160])}")
print("\n判读:enc 带 Ġ + decode 含 </think> + 生成出现 'Paris'/正常英文 = 治本,可批量重跑 8B/70B。")
