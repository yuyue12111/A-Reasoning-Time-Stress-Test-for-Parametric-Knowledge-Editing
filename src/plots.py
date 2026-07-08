"""论文出图(plan v1.66 / gap-review 必5 重写)。从 paper/results.json + (有则)logit-lens jsonl 出图/表 → paper/*.pdf+png。

  python src/plots.py [--results paper/results.json] [--logitlens ...] [--clr-teaching]

图1(重写,承重规格)= **ES 降幅主板**(族内配对 CI + Qwen-32B/Llama-70B 双星标,承重)
                    + **RR 单调副板**(承重支撑)
                    + **CLR 可选教学板**(`--clr-teaching`;必带 base 底噪虚线=edited CLR 贴 base 底噪→net-CLR≈0 退役)。
   ——旧版把 CLR 画成与 ES 降幅并列主面板,会被审稿人当涌现主证据(与 CLR 退役裁决自相矛盾);故 CLR 降为默认不出的教学板。
图2 = logit-lens 逐层 gap=logit(o_new)−logit(o_old)。⚠横轴是 hs 索引(硬伤2:负带真值=decoder 7–11 编辑层上游),
      draft 口径统一在 硬伤2 修;此处按 hs 采样点画,标注编辑层。
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


def _families(cap):
    """返回 [(family_name, series_dict), ...]。新式 capability.families 优先;
    旧式(顶层直接放 params_b/es_drop/... 数组)向后兼容=单族。忽略 _ 前缀的注释键。"""
    fams = cap.get("families")
    if isinstance(fams, dict):
        return [(k, v) for k, v in fams.items() if not k.startswith("_") and isinstance(v, dict)]
    if "params_b" in cap:
        return [("R1-Distill-Qwen", cap)]
    return []


# 每族一种 (颜色, marker, 线型);跨族区分靠颜色,跨指标靠分面板
_FAM_STYLE = [("#1f77b4", "o", "-"), ("#ff7f0e", "s", "--"), ("#9467bd", "D", "-.")]


def _pkey(p):
    """param(float)→ base_clr_b3 的 scale 键:1.5→'1.5B'、7→'7B'、70→'70B'(:g 去尾零)。"""
    return f"{p:g}B"


def _series(ax, x, y, ci, **kw):
    """画一条带(可选)非对称 CI 误差棒的线;缺 CI 就退化成普通线。"""
    if ci and len(ci) == len(y):
        lo = [v - c[0] for v, c in zip(y, ci)]; hi = [c[1] - v for v, c in zip(y, ci)]
        ax.errorbar(x, y, yerr=[lo, hi], capsize=3, **kw)
    else:
        ax.plot(x, y, **kw)


def fig1_capability(cap, base_clr=None, clr_teaching=False):
    """capability-emergent 跨族图(gap-review 必5 承重规格):
      主板 = ES 降幅(族内配对 CI + 高端显著 cell 双星标 0.106/0.107)——承重;
      副板 = RR 单调曲线(带 CI)——承重支撑;
      [可选] 教学板 = CLR(edited)vs base 底噪(虚线)——edited 贴 base 底噪→net-CLR≈0,退役,默认不出。
    单族数据不崩;族里缺某指标/CI 跳过。70B 取数走 capability.families headline(n=187)。"""
    fams = _families(cap)
    allx = sorted({p for _, s in fams for p in s.get("params_b", [])})
    ncol = 3 if (clr_teaching and base_clr) else 2
    wr = [1.55, 1.05, 1.05][:ncol]
    fig, axes = plt.subplots(1, ncol, figsize=(4.15 * ncol + 0.4, 3.7),
                             gridspec_kw={"width_ratios": wr})
    ax_es, ax_rr = axes[0], axes[1]

    # ── 主板:ES 降幅(承重)──
    for (fname, s), (color, marker, ls) in zip(fams, _FAM_STYLE):
        x = s.get("params_b"); y = s.get("es_drop")
        if not x or not y:
            continue
        _series(ax_es, x, y, s.get("es_drop_ci"), label=fname, color=color, marker=marker, ls=ls, lw=2)
        for xi, d, sig in zip(x, y, s.get("es_drop_sig", [False] * len(x))):   # 高端显著 cell 双星标+值
            if sig:
                ax_es.annotate(f"$\\star$ {d:.3f}", (xi, d), textcoords="offset points",
                               xytext=(6, 6), color=color, fontsize=11, fontweight="bold")
    ax_es.axhline(0, color="gray", lw=0.8, ls=":")
    ax_es.set_ylabel(r"ES drop  (ES$_{B_0}$ $-$ ES$_{B_3}$)")
    ax_es.set_title("Edit erosion — load-bearing\n(significant only at matched high-end cells)", fontsize=9)

    # ── 副板:RR 单调(承重支撑)──
    for (fname, s), (color, marker, ls) in zip(fams, _FAM_STYLE):
        x = s.get("params_b"); y = s.get("rr")
        if not x or not y:
            continue
        _series(ax_rr, x, y, s.get("rr_ci"), label=fname, color=color, marker=marker, ls=ls, lw=2)
    ax_rr.set_ylabel(r"RR  (answer reverts to $o_\mathrm{old}$)")
    ax_rr.set_title("Reversion rate — monotone (supporting)", fontsize=9)

    # ── 可选教学板:CLR vs base 底噪(退役证据)──
    if clr_teaching and base_clr:
        ax_clr = axes[2]
        for (fname, s), (color, marker, ls) in zip(fams, _FAM_STYLE):
            x = s.get("params_b"); y = s.get("clr")
            if not x or not y:
                continue
            ax_clr.plot(x, y, label=f"{fname} (edited)", color=color, marker=marker, ls=ls, lw=2)
            bf = [base_clr.get(_pkey(p)) for p in x]
            if all(v is not None for v in bf):
                ax_clr.plot(x, bf, label=f"{fname} (base floor)", color=color, ls=":",
                            lw=1.6, marker="x", alpha=0.85)
        ax_clr.set_ylim(0, 1)
        ax_clr.set_ylabel(r"CLR  (chain leak of $o_\mathrm{old}$)")
        ax_clr.set_title("CLR vs base noise floor — teaching\n(edited tracks base $\\Rightarrow$ net-CLR$\\approx$0, retired)", fontsize=9)

    for ax in axes:                                   # x 轴统一 log + 尺度刻度
        if allx:
            ax.set_xscale("log"); ax.set_xticks(allx); ax.set_xticklabels([f"{p:g}B" for p in allx], fontsize=8)
        ax.set_xlabel("model size (params, log)"); ax.grid(alpha=0.25)
    axes[0].legend(fontsize=7, frameon=False, loc="upper left")
    if clr_teaching and base_clr:
        axes[2].legend(fontsize=6, frameon=False, loc="upper left")
    fig.suptitle("Thinking erodes editing — capability-emergent (cross-family)", y=1.02, fontsize=11)
    fig.tight_layout()
    _save(fig, "fig1_capability"); plt.close(fig)
    _print_fig1_caption()


def _print_fig1_caption():
    """打印建议 LaTeX caption(B5 纪律;写进 .tex 前复核数字)——图本身保持干净,统计措辞随文走。"""
    print("  [fig1 建议 caption(B5 纪律,入 .tex 前逐字复核)]:")
    print("    Thinking erodes parametric edits, and the erosion is capability-emergent. "
          "Main: ES drop (ES@$B_0$ $-$ ES@$B_3$) across two R1-distilled families "
          "(Qwen 1.5--32B, Llama 8--70B), with within-family paired 95\\% bootstrap CIs. "
          "The drop is individually significant only at the two matched high-end cells "
          "(Qwen-32B 0.106 [0.030,0.182]; Llama-70B 0.107 [0.032,0.182], $n{=}187$) --- "
          "these are the load-bearing evidence. Secondary: reversion rate RR rises monotonically. "
          "The pooled per-case capability slope (0.109, $p{=}.003$) is SUPPORTING, not six independent "
          "per-cell tests (no family-wise correction claimed). We read this as a capability contrast, "
          "not a smooth scaling law. [CLR teaching panel, if shown: edited CLR tracks the unedited base "
          "noise floor (0.58$\\to$0.91); net-CLR$\\approx$0, so CLR is retired as emergence evidence.]")


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
    ap.add_argument("--clr-teaching", action="store_true",
                    help="fig1 加 CLR 教学板(带 base 底噪虚线;默认关=省 float 预算、避免 CLR 被当涌现主证据)")
    args = ap.parse_args()
    R = json.load(open(args.results))
    base_clr = ((R.get("base_probe", {}) or {}).get("_six_scale_summary", {}) or {}).get("base_clr_b3")
    print("出图 →")
    fig1_capability(R["capability"], base_clr=base_clr, clr_teaching=args.clr_teaching)
    fig2_logitlens(R["logitlens"], args.logitlens)
    fig3_rq3(R["rq3"])
    print("完成。genbench 数填进 results.json 后重跑即并入图3;fig1 CLR 教学板用 --clr-teaching 开。")


if __name__ == "__main__":
    main()
