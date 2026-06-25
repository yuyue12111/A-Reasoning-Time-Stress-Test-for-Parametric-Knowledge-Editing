"""最终确认:tokenizer 修复 + _gen 补 BOS 后,完整 generate_with_budget 路径是否连贯。
跑:  export WHYAAAI_MODEL=<本地 R1-Distill-Llama-8B>;  python src/diag_llama.py
B0/B3 出现正常英文 + Paris + B3 的 </think> 正常闭合(cot 不再撞顶)= 治本,可批量重跑。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from r1_tokenizer import fix_r1_tokenizer
import think_budget

m = os.environ["WHYAAAI_MODEL"]
tok = fix_r1_tokenizer(AutoTokenizer.from_pretrained(m), m)
model = AutoModelForCausalLM.from_pretrained(m, dtype=torch.bfloat16).to("cuda:0").eval()

for q in ["What is the capital of France?", "The Eiffel Tower is located in the city of"]:
    print(f"\n### q = {q}")
    for b in ["B0", "B3"]:
        cot, ans, _ = think_budget.generate_with_budget(model, tok, q, b)
        print(f"[{b}] cot_chars={len(cot)} | answer={repr(ans[:180])}")
print("\n判读:answer 是正常英文、出现 Paris/地名、B3 的 cot_chars 不再≈8192 撞顶(说明 </think> 正常闭合)"
      " = Llama 路径治本,上传 think_budget.py 等 6 文件批量重跑 8B/70B。")
