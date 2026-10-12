"""Draft figures for §3–§5 (placeholders built from the real numbers; restyle later).

    <python with matplotlib> paperwriting/revision/narrative/fig/section_figs.py

Inputs: paperwriting/revision/study1.json, explore_s1s2.json.  Palette: reference categorical slots 1–2
(validated pair); identity also carried by marker shape.  Hollow markers = exploratory, filled = pre-registered.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
REV = os.path.dirname(os.path.dirname(HERE))
OWN, EDIT, EDIT_LIGHT = "#2a78d6", "#eb6834", "#f4b39a"
INK, INK2, MUTED, RULE = "#0b0b0b", "#52514e", "#8a8984", "#d9d8d3"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.2, "axes.edgecolor": RULE, "axes.linewidth": 0.6,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.labelcolor": INK2})
s1 = json.load(open(os.path.join(REV, "study1.json")))["checkpoints"]
ex = json.load(open(os.path.join(REV, "explore_s1s2.json")))


def clean(ax, left=True):
    for s in ("top", "right") + (() if left else ("left",)):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(HERE, f"{name}.{ext}"), dpi=240, facecolor="white")
    plt.close(fig)


# ---------------- Figure 2: Study 1 ----------------
models = ["Qwen-1.5B", "Qwen-7B", "Qwen-14B", "Qwen-32B", "Llama-8B", "Llama-70B"]
fig, (a, b) = plt.subplots(1, 2, figsize=(6.6, 2.35), gridspec_kw={"wspace": 0.55})
for i, m in enumerate(models):
    d = s1[m]["ES_drop"]
    y = len(models) - 1 - i
    a.plot([d["es_b1"], d["es_b0"]], [y, y], color="#b9b8b3", lw=1.6, zorder=1)
    a.plot([d["es_b0"]], [y], "o", color=EDIT_LIGHT, ms=6, mec="white", mew=0.8, zorder=3)
    a.plot([d["es_b1"]], [y], "D", color=EDIT, ms=5.5, mec="white", mew=0.8, zorder=3)
    if m in ("Qwen-32B", "Llama-70B"):
        a.text(0.665, y, f"−{d['point']:.3f}*", va="center", fontsize=6.4, color=INK)
a.set_yticks(range(len(models))); a.set_yticklabels(models[::-1]); a.set_xlim(0.44, 0.7)
a.set_xlabel("Edit success", fontsize=6.6); clean(a); a.grid(axis="x", color=RULE, lw=0.5); a.set_axisbelow(True)
a.set_title("a  Edit success, asked directly (○) and after thinking (◆)", loc="left", fontsize=7.4, weight="bold", color=INK)

for i, m in enumerate(models):
    r = s1[m]["retention_contrast"]
    y = len(models) - 1 - i
    lo, hi = r["ci95"]
    sig = lo > 0
    b.plot([lo, hi], [y, y], color=EDIT if sig else "#b9b8b3", lw=1.4)
    b.plot([r["point"]], [y], "D", color=EDIT if sig else "white", mec=EDIT, ms=5.5, mew=1.0)
b.axvline(0, color=INK2, lw=0.7)
b.set_yticks(range(len(models))); b.set_yticklabels(models[::-1]); b.set_xlim(-0.25, 0.4)
b.set_xlabel("Excess loss: edited answers lost − own answers lost", fontsize=6.6); clean(b)
b.grid(axis="x", color=RULE, lw=0.5); b.set_axisbelow(True)
b.set_title("b  Excess loss after thinking (95% CI)", loc="left", fontsize=7.4, weight="bold", color=INK)
fig.text(0.01, 0.01, "* survives Holm correction over six models. Study 1 (exploratory).", fontsize=6, color=MUTED)
fig.subplots_adjust(left=0.1, right=0.98, top=0.86, bottom=0.24)
save(fig, "fig2_study1")

# ---------------- Figure 3: the replication ----------------
runs = [("Study 1 facts · original pipeline", "S1", False),
        ("Study 1 facts · rerun, replication engine", "G0-H100", False),
        ("Study 2 fresh facts · pre-registered", "S2", True)]
fig, axes = plt.subplots(1, 2, figsize=(6.6, 1.75), sharey=True, gridspec_kw={"wspace": 0.08})
for ax, key, title in ((axes[0], "ES_drop", "Drop in edit success after thinking"),
                       (axes[1], "retention_contrast", "Excess loss (edited − own)")):
    for i, (lab, k, reg) in enumerate(runs):
        e = ex["runs"][k][key]
        y = len(runs) - 1 - i
        ax.plot(e["ci95"], [y, y], color=EDIT, lw=1.4)
        ax.plot([e["point"]], [y], "D", color=EDIT if reg else "white", mec=EDIT, ms=6, mew=1.1)
        ax.text(e["ci95"][1] + 0.012, y, f"{e['point']:+.3f}", va="center", fontsize=6.4, color=INK)
    ax.axvline(0, color=INK2, lw=0.7); ax.set_xlim(-0.08, 0.42)
    ax.set_title(title, loc="left", fontsize=7.4, weight="bold", color=INK); clean(ax)
    ax.grid(axis="x", color=RULE, lw=0.5); ax.set_axisbelow(True)
axes[0].set_yticks(range(len(runs))); axes[0].set_yticklabels([r[0] for r in runs][::-1], fontsize=6.6)
fig.text(0.99, 0.02, "Qwen-32B; 95% CIs. Hollow: exploratory. Filled: pre-registered.", ha="right", fontsize=6, color=MUTED)
fig.subplots_adjust(left=0.30, right=0.97, top=0.82, bottom=0.2)
save(fig, "fig3_replication")

# ---------------- Figure 4: familiarity dose-response (Study 2) ----------------
byk = ex["E6_fact_salience"]["S2_by_n_small_models"]
ks = sorted(byk, key=int)
fig, (a, b) = plt.subplots(1, 2, figsize=(6.6, 2.2), gridspec_kw={"wspace": 0.35})
xs = [int(k) for k in ks]
a.plot(xs, [byk[k]["base_loss"] for k in ks], "-o", color=OWN, ms=6, mec="white", mew=0.8, lw=1.6, label="model's own answer")
a.plot(xs, [byk[k]["edited_loss"] for k in ks], "-D", color=EDIT, ms=5.5, mec="white", mew=0.8, lw=1.6, label="edited answer")
for k in ks:
    a.text(int(k), -0.055, f"n={byk[k]['n']}", ha="center", fontsize=5.8, color=MUTED)
a.set_ylim(-0.08, 0.45); a.set_xticks(xs); a.set_xlabel("Smaller R1 distills that know the fact (of 4)", fontsize=6.6)
a.set_ylabel("Lost after thinking", fontsize=6.6); clean(a); a.grid(axis="y", color=RULE, lw=0.5); a.set_axisbelow(True)
a.legend(frameon=False, fontsize=6.4, loc="upper center", bbox_to_anchor=(0.5, 1.02))
a.set_title("a  Edited vs own answers by familiarity", loc="left", fontsize=7.4, weight="bold", color=INK)
for k in ks:
    r = byk[k]["retention_contrast"]
    b.plot([int(k), int(k)], r["ci95"], color=EDIT, lw=1.4)
    b.plot([int(k)], [r["point"]], "D", color="white", mec=EDIT, ms=6, mew=1.1)
b.axhline(0, color=INK2, lw=0.7); b.axvspan(2.5, 4.5, color="#f1f0ec", zorder=0)
b.text(3.5, 0.47, "well-known", ha="center", fontsize=6.4, color=INK2)
b.set_xticks(xs); b.set_xlim(-0.5, 4.5); b.set_ylim(-0.55, 0.55)
b.set_xlabel("Smaller R1 distills that know the fact (of 4)", fontsize=6.6); b.set_ylabel("Excess loss (95% CI)", fontsize=6.6)
clean(b); b.grid(axis="y", color=RULE, lw=0.5); b.set_axisbelow(True)
b.set_title("b  Excess loss by familiarity", loc="left", fontsize=7.4, weight="bold", color=INK)
fig.text(0.99, 0.01, "Study 2 fresh facts, Qwen-32B. Familiarity defined after the replication failed (exploratory).",
         ha="right", fontsize=6, color=MUTED)
fig.subplots_adjust(left=0.08, right=0.98, top=0.86, bottom=0.22)
save(fig, "fig4_familiarity")
print("wrote fig2_study1, fig3_replication, fig4_familiarity")
