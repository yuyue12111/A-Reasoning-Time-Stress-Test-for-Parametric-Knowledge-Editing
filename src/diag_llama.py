"""一次性定位 Llama 跑废的两个 bug(只读探针,不写 results)。
跑:  export WHYAAAI_MODEL=<本地 R1-Distill-Llama-8B 路径>;  python src/diag_llama.py
读三件事 → 贴回输出:
  A) 分词器 fast/slow + decode 是否把 Ġ/Ċ 还原成 空格/换行(bug#1 解码);
  B) 我们的 think_budget 模板在【未编辑基座】上是否连贯(隔离 bug#2 = 模板坏 vs ROME 编辑坏);
  C) 若 decode 脏,convert_tokens_to_string 是否干净(给修法方向)。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import think_budget

m = os.environ["WHYAAAI_MODEL"]
tok = AutoTokenizer.from_pretrained(m)

print("=== A) 分词器 + decode 解码 ===")
print("type:", type(tok).__name__, "| is_fast:", getattr(tok, "is_fast", "?"))
probe = "Hello world\nThe capital is Paris."
ids = tok(probe, add_special_tokens=False)["input_ids"]
dec = tok.decode(ids, skip_special_tokens=True)
print("decode round-trip:", repr(dec))
print("  → 脏(含 Ġ/Ċ)吗:", ("Ġ" in dec or "Ċ" in dec), "| ==原文吗:", dec == probe)
print("=== C) 备选解码路径(若上面脏,看这些干净否) ===")
toks = tok.convert_ids_to_tokens(ids)
print("convert_tokens_to_string:", repr(tok.convert_tokens_to_string(toks)))
print("decode(clean_up=True)   :", repr(tok.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)))

print("\n=== B) 我们的 think_budget 模板 × 未编辑基座(无 ROME) ===")
model = AutoModelForCausalLM.from_pretrained(m, dtype=torch.bfloat16).to("cuda:0").eval()
for b in ["B0", "B3"]:
    cot, ans, _ = think_budget.generate_with_budget(model, tok, "What is the capital of France?", b)
    print(f"[{b}] cot_chars={len(cot)} | answer={repr(ans[:160])}")
print("\n判读:B 段连贯出现 Paris = 模板 OK→bug#2 在 ROME 编辑(借 Qwen 超参在 Llama 上发散);"
      " B 段也是 . \\n\\n 垃圾 = 我们模板/分词对 Llama 不对。A/C 段定 decode 修法。")
