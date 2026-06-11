"""本地 M5/MPS 迷你彩排（组里算力盲区时用）。纯 HF generate，绕开要 cuda 的权重编辑。

  Part A  think_budget B0–B4 在**真** R1-Distill-Qwen-1.5B 上的长度分布（task#07 part B，此前只 mock 过）。
  Part B  ICE 现象探针——上下文注入反事实 o_new，沿思考预算看是否回退真事实 o_old（第一个「越想越退」信号）。

注意（笔记里要写清）：
  · 本地为控时用**缩减预算上限** `LOCAL_CAPS`（非 H200 全量 B3=8192）；事实类 CoT 通常更短，B3 仍≈natural。
  · 1.5B 是最弱模型，信号会噪；这是「现象是否出现 + 端到端验证 harness」的彩排，不是主结果。
  · ICE（上下文注入）≠ 参数编辑（ROME/MEMIT）——是 plan §2.2 的非参对照；真·参数版要 EasyEdit（MPS 待验）。

运行：<editrev>/python src/local_probe.py --device mps
"""
import sys, os, json, argparse, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch
import think_budget as tb
import metrics
from transformers import AutoModelForCausalLM, AutoTokenizer

LOCAL_CAPS = {"B1": 128, "B2": 384, "B3": 768, "B4": 768}   # 本地缩减上限(MPS~7tok/s 控时)

LEN_QS = [
    "What is the capital of the country where the Eiffel Tower is located?",
    "If a train travels 60 km in 45 minutes, what is its speed in km/h?",
    "Is 91 a prime number? Briefly explain.",
    "Who wrote the play Romeo and Juliet?",
]

# (prompt, o_old=真事实, o_new=反事实)；选 1.5B 必知 o_old 的常识，让"回退"有去处
CASES = [
    ("The capital of France is", "Paris", "Rome"),
    ("The Eiffel Tower is located in the city of", "Paris", "Berlin"),
    ("The author of the play Romeo and Juliet is", "Shakespeare", "Dickens"),
    ("The largest planet in our solar system is", "Jupiter", "Mars"),
    ("The currency used in Japan is the", "yen", "euro"),
    ("The first President of the United States was", "Washington", "Lincoln"),
    ("Mount Everest is located in the country of", "Nepal", "Brazil"),
    ("The Mona Lisa was painted by", "Leonardo da Vinci", "Pablo Picasso"),
    ("The planet known as the Red Planet is", "Mars", "Venus"),
    ("The capital of Japan is", "Tokyo", "Beijing"),
    ("Water is composed of hydrogen and", "oxygen", "nitrogen"),
    ("The speed of light in a vacuum is approximately 300,000 kilometers per", "second", "hour"),
]


def ice_q(prompt, o_new):
    return (f'Suppose it is now a true fact that "{prompt} {o_new}." '
            f'Answer using this new fact. {prompt}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B")
    ap.add_argument("--device", default="mps")
    ap.add_argument("--dtype", default="float16")
    ap.add_argument("--budgets", nargs="+", default=["B0", "B3", "B4"])
    ap.add_argument("--out", default="results/local_probe")
    args = ap.parse_args()

    tb.CAP = LOCAL_CAPS                                       # override 本地缩减上限
    aliases = json.load(open("data/aliases.json"))

    dtype = getattr(torch, args.dtype)
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=dtype).to(args.device).eval()
    os.makedirs(args.out, exist_ok=True)
    logf = open(os.path.join(args.out, "probe.jsonl"), "w")
    gen = lambda q, b: tb.generate_with_budget(model, tok, q, b)[:2]   # (cot, ans)

    # ---- Part A: 长度分布 B0–B4 ----
    print(f"\n=== Part A: think_budget 长度分布 (真 {args.model.split('/')[-1]}, caps={LOCAL_CAPS}) ===")
    print(f"{'Q':<4}{'budget':<7}{'cot_tok':>9}{'ans_tok':>9}  wait  secs")
    for qi, q in enumerate(LEN_QS):
        for b in ["B0", "B1", "B2", "B3", "B4"]:
            t0 = time.time(); cot, ans = gen(q, b); dt = time.time() - t0
            nc, na = tb._ntok(tok, cot), tb._ntok(tok, ans)
            print(f"{qi:<4}{b:<7}{nc:>9}{na:>9}  {int(tb.WAIT.strip() in cot)}    {dt:.0f}")
            logf.write(json.dumps({"part": "A", "q": qi, "budget": b, "cot_tok": nc, "ans_tok": na}) + "\n"); logf.flush()

    # ---- Part B: ICE 现象探针 ----
    print(f"\n=== Part B: ICE 现象探针 (注入 o_new → 沿 {args.budgets} 看回退 o_old) ===")
    rows = []
    for (p, o_old, o_new) in CASES:
        _, base = gen(p, "B0")                               # 无 ICE @ B0：模型知不知道 o_old
        knows = bool(metrics.hit(base, o_old, aliases))
        rec = {"prompt": p, "o_old": o_old, "o_new": o_new, "knows_o_old": knows, "ice": {}}
        for b in args.budgets:
            cot, ans = gen(ice_q(p, o_new), b)
            rec["ice"][b] = {"es": bool(metrics.hit(ans, o_new, aliases) and not metrics.hit(ans, o_old, aliases)),
                             "revert": bool(metrics.hit(ans, o_old, aliases)),
                             "clr": bool(metrics.hit(cot, o_old, aliases)), "ans": ans.strip()[:60]}
        rows.append(rec); logf.write(json.dumps({"part": "B", **rec}) + "\n"); logf.flush()
        tag = " ".join(f"{b}:ES{int(rec['ice'][b]['es'])}/REV{int(rec['ice'][b]['revert'])}" for b in args.budgets)
        print(f"  {p[:34]:<36} know_old={int(knows)}  {tag}")

    # ---- 汇总（仅统计「知 o_old 且 B0 接受 ICE」的合格 case）----
    b0 = args.budgets[0]
    elig = [r for r in rows if r["knows_o_old"] and r["ice"][b0]["es"]]
    print(f"\n=== 汇总：合格 case（知 o_old 且 {b0} 接受 ICE）= {len(elig)}/{len(rows)} ===")
    print(f"{'budget':<8}{'ES':>7}{'RR(回退)':>11}{'CLR':>7}")
    for b in args.budgets:
        if not elig:
            break
        es = sum(r["ice"][b]["es"] for r in elig) / len(elig)
        rr = sum(r["ice"][b]["revert"] for r in elig) / len(elig)
        clr = sum(r["ice"][b]["clr"] for r in elig) / len(elig)
        print(f"{b:<8}{es:>7.2f}{rr:>11.2f}{clr:>7.2f}")
    print("\n假设(越想越退): ES 随预算↓、RR/CLR↑。1.5B+ICE 信号噪，仅作彩排首看，详见 analysis/07_local_probe.md")
    logf.close()


if __name__ == "__main__":
    main()
