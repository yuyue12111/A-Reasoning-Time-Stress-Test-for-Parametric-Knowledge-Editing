"""论文出图(plan v1.27)。从 paper/results.json + (有则)logit-lens jsonl 出三图/表 → paper/*.pdf+png。

  python src/plots.py [--results paper/results.json] [--logitlens results/probe/logitlens_cf200_ROME_B3.jsonl]

图1 = capability 曲线(ES 降幅/CLR/RR × 模型规模,带 CI,ES 降幅标显著性);
图2 = logit-lens 逐层 gap=logit(o_new)−logit(o_old)(有 jsonl 走全分辨率+band,否则用 results.json 采样点);
图3 = RQ3 A/B(baseline vs suppress;genbench 填了就并入)。纯 CPU,只需 matplotlib。
"""
import argparse, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _save(fig, name):
    for ext in ("pdf", "png"):
        p = os.path.join(_ROOT, "paper", f"{name}.{ext}")
        fig.savefig(p, bbox_inches="tight", dpi=200)
    print(f"  写出 paper/{name}.pdf+png")


def fig1_capability(cap):
    x = cap["params_b"]
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    def band(key, label, color, marker):
        y = cap[key]; ci = cap[key + "_ci"]
        lo = [v - c[0] for v, c in zip(y, ci)]; hi = [c[1] - v for v, c in zip(y, ci)]
        ax.errorbar(x, y, yerr=[lo, hi], label=label, color=color, marker=marker, capsize=3, lw=2)
    band("clr", "CLR (chain leak)", "#1f77b4", "o")
    band("rr", "RR (answer reverts)", "#d62728", "s")
    band("es_drop", "ES drop (B0→B3)", "#2ca02c", "^")
    for xi, d, sig in zip(x, cap["es_drop"], cap["es_drop_sig"]):   # 显著性星标
        if sig:
            ax.annotate("*", (xi, d), textcoords="offset points", xytext=(4, 4), color="#2ca02c", fontsize=14)
    ax.axhline(0, color="gray", lw=0.8, ls=":")
    ax.set_xscale("log"); ax.set_xticks(x); ax.set_xticklabels([f"{p}B" for p in x])
    ax.set_xlabel("model size (R1-Distill-Qwen)"); ax.set_ylabel("rate")
    ax.set_title("Thinking erodes editing — capability-emergent")
    ax.legend(fontsize=8, frameon=False); ax.grid(alpha=0.25)
    _save(fig, "fig1_capability"); plt.close(fig)


def fig2_logitlens(ll, jsonl):
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    rows = []
    if jsonl and os.path.exists(jsonl):
        for l in open(jsonl):
            d = json.loads(l)
            if isinstance(d.get("gap_by_layer"), list):
                rows.append(d["gap_by_layer"])
    if rows:                                   # 全分辨率 + 95% band
        import statistics
        nL = len(rows[0]); xs = list(range(nL))
        mean = [statistics.mean(r[l] for r in rows) for l in range(nL)]
        lo = [sorted(r[l] for r in rows)[max(0, int(0.025 * len(rows)))] for l in range(nL)]
        hi = [sorted(r[l] for r in rows)[min(len(rows) - 1, int(0.975 * len(rows)))] for l in range(nL)]
        ax.fill_between(xs, lo, hi, color="#1f77b4", alpha=0.18)
        ax.plot(xs, mean, color="#1f77b4", lw=2, label=f"mean gap (n={len(rows)})")
        src = f"logit-lens jsonl (n={len(rows)})"
    else:                                      # 回退:results.json 采样点
        xs = ll["layers_sampled"]; ax.plot(xs, ll["gap_sampled"], color="#1f77b4", marker="o", lw=2, label="mean gap (sampled)")
        src = "results.json (sampled)"
    ax.axhline(0, color="gray", lw=0.8, ls=":")
    ax.axvline(ll["edit_layer"], color="#d62728", lw=1, ls="--", label=f"edit layer {ll['edit_layer']}")
    ax.set_xlabel("layer (logit-lens)"); ax.set_ylabel("logit(o_new) − logit(o_old)")
    ax.set_title(f"Edit intact at cloze ({ll['edit_intact_pct']:.0%} of reverted) — {src}")
    ax.legend(fontsize=8, frameon=False); ax.grid(alpha=0.25)
    _save(fig, "fig2_logitlens"); plt.close(fig)


def fig3_rq3(rq):
    keys = ["RR", "ES_B3", "CLR", "Loc"]
    base = [rq["baseline"][k] for k in keys]; sup = [rq["suppress"][k] for k in keys]
    gb = rq.get("genbench") or {}
    if gb.get("gsm8k_off") is not None:        # genbench 填了就并入
        keys += ["GSM8K", "MATH"]
        base += [gb["gsm8k_off"], gb["math_off"]]; sup += [gb["gsm8k_on"], gb["math_on"]]
    import numpy as np
    xi = np.arange(len(keys)); w = 0.38
    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    ax.bar(xi - w / 2, base, w, label="baseline", color="#999999")
    ax.bar(xi + w / 2, sup, w, label=f"+suppress (scope={rq['scope']})", color="#2ca02c")
    for i, (b, s) in enumerate(zip(base, sup)):
        ax.text(i - w / 2, b + .01, f"{b:.2f}", ha="center", fontsize=7)
        ax.text(i + w / 2, s + .01, f"{s:.2f}", ha="center", fontsize=7)
    ax.set_xticks(xi); ax.set_xticklabels(keys); ax.set_ylabel("rate")
    ax.set_title(f"RQ3 training-free fix ({rq['model']}, n={rq['n']})")
    ax.legend(fontsize=8, frameon=False); ax.grid(alpha=0.25, axis="y")
    _save(fig, "fig3_rq3"); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=os.path.join(_ROOT, "paper", "results.json"))
    ap.add_argument("--logitlens", default=os.path.join(_ROOT, "results", "probe", "logitlens_cf200_ROME_B3.jsonl"))
    args = ap.parse_args()
    R = json.load(open(args.results))
    print("出图 →")
    fig1_capability(R["capability"])
    fig2_logitlens(R["logitlens"], args.logitlens)
    fig3_rq3(R["rq3"])
    print("完成。genbench 数填进 results.json 后重跑即并入图3。")


if __name__ == "__main__":
    main()
