"""本地 M5/MPS **参数版 ROME** 首信号（sumandplan §6.1-③ / phase-1 §6 开放线程）。

local_probe.py 是 ICE(上下文注入)对照——诚实负(B0 即拒注入、答参数 o_old，压不动参数知识)；
本脚本是**真·参数编辑**版：EasyEdit ROME 在真 1.5B 权重上逐条编辑 → {B0,B3,B4} 全档生成
→ metrics.score，看 ES 随预算↓ / RR↑（ICE 测不出的真机制，plan §2.2）。复用 edit_loop.run
=端到端验证整条 pilot harness 在 MPS 上跑通（patch→edit→预算→restore→溯源头→打分）。

timebox（phase-1 §6 step 3）：通了写 analysis/08_rome_mps.md；撞 MPS 算子墙（compute_v 反传里
float64/算子缺口）就把雷点记清等 H200——edit_loop 单条容错保证首条失败不丢全部诊断（错误标记进 jsonl）。

为何 1.5B ROME 可离线跑：ROME hparams `mom2_adjustment:false` → 不需协方差(无 mom2 前置)；
1.5B 与 7B 同架构(28 层 qwen2) → 复用 `hparams/ROME/qwen2.5-7b.yaml`；qwen 路由 bug 由 edit_loop
自动接入的 vendor_patch 修掉(否则 from_hparams 即 fp32 TypeError)。
关键：device 必须是字符串 "mps"（int 会被 normalize_device 当 cuda:idx，phase-1 §6）。

运行（项目根，PYTHONPATH 指向 EasyEdit 使 easyeditor 可导入）：
  PYTHONPATH=source/EasyEdit <editrev>/python src/rome_mps_probe.py
  PYTHONPATH=source/EasyEdit <editrev>/python src/rome_mps_probe.py --budgets B0 B3   # 更快
  PYTHONPATH=source/EasyEdit <editrev>/python src/rome_mps_probe.py --cases 2 --budgets B0  # 最小冒烟(先验编辑能否跑)
"""
import sys, os, json, argparse

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)                      # 项目根；下方默认路径都相对它解析，免受 cwd 影响
sys.path.insert(0, _HERE)
import think_budget as tb
import metrics
import edit_loop

# local_probe.py 的 12 常识反事实中**适合 ROME 的 8 个**——subject 必须是 prompt 的明确实体子串
# （ROME fact_token=subject_last 在 subject 末 token 处插入；超级最/无实体主语的句子不适合，已剔除）。
CURATED = [
    ("France",          "The capital of France is",                   "Paris",             "Rome"),
    ("Eiffel Tower",    "The Eiffel Tower is located in the city of", "Paris",             "Berlin"),
    ("Romeo and Juliet","The author of the play Romeo and Juliet is", "Shakespeare",       "Dickens"),
    ("Japan",           "The currency used in Japan is the",          "yen",               "euro"),
    ("Mount Everest",   "Mount Everest is located in the country of", "Nepal",             "Brazil"),
    ("Mona Lisa",       "The Mona Lisa was painted by",               "Leonardo da Vinci", "Pablo Picasso"),
    ("Japan",           "The capital of Japan is",                    "Tokyo",             "Beijing"),
    ("Water",           "Water is composed of hydrogen and",          "oxygen",            "nitrogen"),
]
# 缩减预算上限（MPS ~7 tok/s 控时，与 local_probe 一致；事实类 CoT 通常更短，B3 仍≈natural）。
LOCAL_CAPS = {"B1": 128, "B2": 384, "B3": 768, "B4": 768}


def build_cases(n=None):
    cs = [{"case_id": f"rome_mps_{i}", "s": s, "prompt": p, "o_old": oo, "o_new": on}
          for i, (s, p, oo, on) in enumerate(CURATED)]
    return cs[:n] if n else cs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B")
    ap.add_argument("--device", default="mps")
    ap.add_argument("--hparams", default=os.path.join(_ROOT, "source/EasyEdit/hparams/ROME/qwen2.5-7b.yaml"))
    ap.add_argument("--budgets", nargs="+", default=["B0", "B3", "B4"])
    ap.add_argument("--layers", type=int, nargs="+", default=[5])
    ap.add_argument("--cases", type=int, default=None, help="只跑前 N 条（最小冒烟用）")
    ap.add_argument("--out", default=os.path.join(_ROOT, "results/rome_mps/probe.jsonl"))
    ap.add_argument("--fresh", action="store_true", help="删除旧 out 重跑（默认续跑）")
    args = ap.parse_args()

    tb.CAP = LOCAL_CAPS                              # 缩减上限（影响 edit_loop 经 think_budget 的生成）
    cases = build_cases(args.cases)
    aliases = json.load(open(os.path.join(_ROOT, "data/aliases.json")))
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    if args.fresh and os.path.exists(args.out):
        os.remove(args.out)
    # device 必须字符串 "mps"；stats_dir 与 7B/Qwen2.5 分目录（ROME mom2_adjustment:false 其实不读，留作卫生）
    overrides = {"model_name": args.model, "device": args.device,
                 "stats_dir": os.path.join(_ROOT, "data/stats_r1qwen15b"), "layers": args.layers}

    print(f"=== 参数版 ROME on {args.device} ({args.model.split('/')[-1]}) ===")
    print(f"cases={len(cases)} budgets={args.budgets} layers={args.layers} caps={LOCAL_CAPS}")
    print("（撞 MPS 算子墙时 edit_loop 单条容错，错误标记进 jsonl；timebox 见 analysis/08）\n")

    edit_loop.run(cases, "ROME", args.hparams, args.budgets, args.out, rank=0, world=1,
                  overrides=overrides, meta={"run_kind": "rome_mps_smoke", "model": args.model,
                                             "device": args.device, "caps": LOCAL_CAPS})

    # ---- 打分 + 逐 case efficacy 详情（人工核回退）----
    res = metrics.score(args.out, cases, aliases)
    fmt = lambda x: f"{x:>8.2f}" if isinstance(x, float) else f"{'—':>8}"
    print(f"\n{'budget':<8}{'n':>5}{'ES':>8}{'RR':>8}{'CLR':>8}")
    for b in res:
        r = res[b]
        print(f"{b:<8}{r['n']:>5}{fmt(r['ES'])}{fmt(r['RR'])}{fmt(r['CLR'])}")

    rows = [json.loads(l) for l in open(args.out)]
    rows = [r for r in rows if not r.get("_meta")]
    n_err = sum(1 for r in rows if r.get("error"))
    print(f"\n错误行={n_err}（>0 多半撞 MPS 算子墙 → 记雷点等 H200）  out={args.out}")
    print("\n逐 case efficacy 答案（B0=ZeroThink 看编辑是否落地；高预算看是否回退 o_old）：")
    for c in cases:
        line = [c["case_id"], f"{c['o_old']}→{c['o_new']}"]
        for b in args.budgets:
            ans = next((r["answer"] for r in rows
                        if r.get("case_id") == c["case_id"] and r.get("budget") == b
                        and r.get("probe") == "efficacy" and r.get("decode") == "greedy"), None)
            if ans is not None:
                es = metrics.hit(ans, c["o_new"], aliases) and not metrics.hit(ans, c["o_old"], aliases)
                rev = metrics.hit(ans, c["o_old"], aliases)
                line.append(f"{b}:{'ES' if es else ('REV' if rev else '??')}")
        print("  " + "  ".join(line))
    print("\n假设(越想越退): ES 随预算↓、RR/CLR↑。1.5B 信号噪，仅彩排首看，详见 analysis/08_rome_mps.md")


if __name__ == "__main__":
    main()
