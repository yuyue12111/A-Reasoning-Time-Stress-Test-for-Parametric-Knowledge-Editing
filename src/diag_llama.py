"""一次性钉死 Llama 跑废的两个 bug(v2,只读探针,不写 results)。
跑:  export WHYAAAI_MODEL=<本地 R1-Distill-Llama-8B 路径>;  python src/diag_llama.py
四块输出 → 贴回:
  A) transformers 版本 + 编码是否把空格抓成 Ġ(编码 OK?);
  B) python decode vs rust backend decode 谁干净(给 decode 修法);
  C) 我们 ZEROTHINK 模板的 prompt token(特殊 token 是否单 id、模板对不对);
  D) 生成的【原始 token id/token】—— 看模型到底吐的是退化串还是正常词被坏 decode 显成垃圾。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch, transformers
from transformers import AutoModelForCausalLM, AutoTokenizer
import think_budget

m = os.environ["WHYAAAI_MODEL"]
t = AutoTokenizer.from_pretrained(m)

print("=== A) 版本 + 编码 ===")
print("transformers:", transformers.__version__, "| tok:", type(t).__name__, "fast:", t.is_fast)
ids = t("Hello world\nParis", add_special_tokens=False)["input_ids"]
print("enc ids   :", ids)
print("enc tokens:", t.convert_ids_to_tokens(ids), "  ← 有 Ġworld/Ċ = 编码抓到空格(锅在解码)")

print("=== B) python decode vs rust backend decode ===")
print("py  decode:", repr(t.decode(ids, skip_special_tokens=True)))
try:
    print("rust decode:", repr(t.backend_tokenizer.decode(ids, skip_special_tokens=False)))
except Exception as e:
    print("rust decode err:", repr(e))

print("=== C) 我们 ZEROTHINK 模板的 prompt token ===")
prompt = think_budget.ZEROTHINK.format(q="What is the capital of France?")
penc = t(prompt, return_tensors="pt")
ptoks = t.convert_ids_to_tokens(penc["input_ids"][0].tolist())
print("prompt tokens:", ptoks, "  ← <｜User｜>/<｜Assistant｜>/<think>/</think> 应各是单 token")

print("=== D) 生成原始 token(无 decode 干扰)===")
model = AutoModelForCausalLM.from_pretrained(m, dtype=torch.bfloat16).to("cuda:0").eval()
out = model.generate(**penc.to("cuda:0"), max_new_tokens=30, do_sample=False)
gen = out[0][penc["input_ids"].shape[1]:].tolist()
print("gen ids   :", gen)
print("gen tokens:", t.convert_ids_to_tokens(gen), "  ← 若是正常英文词=模型 OK(只是 decode 坏);若全是 .ĊĊ=真退化")
print("gen pydec :", repr(t.decode(gen, skip_special_tokens=True)))
print("\n判读:D 的 gen tokens 是正常词(Paris/capital...) → 模型好、只 decode 坏 → 修 decode 即全好;"
      "D 仍是 ./Ċ → 模型真退化 → 再查模板/ROME。B 的 rust decode 干净 → decode 修法=走 backend/后处理。")
