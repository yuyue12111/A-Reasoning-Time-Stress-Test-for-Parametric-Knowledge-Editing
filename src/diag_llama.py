"""定位 Llama 第二个 bug:tokenizer 已修好(空格回来),但我们模板仍退化。
三方对照:apply_chat_template(连贯基准)/ 我们 TPL / 我们 TPL+BOS,看差在哪、BOS 是否治本。
跑:  export WHYAAAI_MODEL=<本地 R1-Distill-Llama-8B>;  python src/diag_llama.py
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
q = "What is the capital of France?"


def gen(enc):
    enc = enc.to("cuda:0")
    o = model.generate(**enc, max_new_tokens=40, do_sample=False)
    return tok.decode(o[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)


print("=== 1) apply_chat_template(连贯基准)===")
act = tok.apply_chat_template([{"role": "user", "content": q}], add_generation_prompt=True,
                              return_tensors="pt", return_dict=True)
print("head tokens:", tok.convert_ids_to_tokens(act["input_ids"][0].tolist())[:10])
print("gen:", repr(gen(act)[:160]))

print("=== 2) 我们的 TPL(tok 默认 add_special_tokens)===")
oenc = tok(think_budget.TPL.format(q=q), return_tensors="pt")
print("head tokens:", tok.convert_ids_to_tokens(oenc["input_ids"][0].tolist())[:10])
print("gen:", repr(gen(oenc)[:160]))

print("=== 3) 我们的 TPL + 显式 BOS ===")
bos = tok.bos_token or "<｜begin▁of▁sentence｜>"
oenc2 = tok(bos + think_budget.TPL.format(q=q), return_tensors="pt", add_special_tokens=False)
print("head tokens:", tok.convert_ids_to_tokens(oenc2["input_ids"][0].tolist())[:10])
print("gen:", repr(gen(oenc2)[:160]))
print("\nbos_token=", repr(tok.bos_token), " add_bos_token=", getattr(tok, "add_bos_token", "?"))
print("判读:对比 1 与 2 的 head tokens 差在哪(多半是 1 有 <｜begin▁of▁sentence｜>、2 没有);"
      "若 3(加 BOS)生成连贯出现 Paris → 修法=模板补 BOS。")
