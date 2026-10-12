"""Hero figure sketch (draft): one edit asked two ways, and edited vs own-answer loss by fact familiarity.

    <python with matplotlib> paperwriting/revision/narrative/fig/hero_sketch.py

Reads hero_data.json (written by the analysis snippet in REVISION §8, 2026-10-12; loaders of
src/rt/explore_s1s2.py). Colours: reference categorical slots 1-2 (validated: CVD dE 24.7, normal 33.6).
Identity is also carried by marker shape (circle = own answer, diamond = edited answer) for print/CVD.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
OWN, EDIT = "#2a78d6", "#eb6834"                 # series-1 blue, series-2 orange
INK, INK2, MUTED, RULE, BAND = "#0b0b0b", "#52514e", "#8a8984", "#d9d8d3", "#f1f0ec"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.2, "axes.edgecolor": RULE,
                     "axes.linewidth": 0.6, "xtick.color": INK2, "ytick.color": INK2})

data = json.load(open(os.path.join(HERE, "hero_data.json")))["runs"]
LABEL = {("Qwen-14B", "original"): "Study 1 · Qwen-14B", ("Qwen-32B", "original"): "Study 1 · Qwen-32B",
         ("Llama-70B", "original"): "Study 1 · Llama-70B", ("Qwen-32B", "v2, H100 (rerun)"): "Study 1 · Qwen-32B, rerun",
         ("Qwen-32B", "v2, H100"): "Study 2 · Qwen-32B (fresh)"}

fig = plt.figure(figsize=(6.8, 3.0))

# ---------------- panel (a): one edit, asked two ways ----------------
ax = fig.add_axes([0.005, 0.06, 0.34, 0.80]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
fig.text(0.012, 0.955, "a  One edit, asked two ways", weight="bold", color=INK, va="top", fontsize=7.8)
ax.text(0.02, 0.93, "Edit: capital of the Kingdom of Bohemia\nPrague → Santiago   (Qwen-32B, Study 2)",
        color=INK2, va="top", fontsize=6.8, linespacing=1.35)

def strip(y, h, title, body, answer, color, marker, verdict):
    ax.add_patch(FancyBboxPatch((0.02, y - h), 0.96, h, boxstyle="round,pad=0.0,rounding_size=0.02",
                                fc="white", ec=RULE, lw=0.6))
    ax.text(0.05, y - 0.03, title, weight="bold", color=INK, va="top", fontsize=7)
    if body:
        ax.text(0.05, y - 0.095, body, color=INK2, style="italic", va="top", fontsize=6.4, linespacing=1.35, wrap=True)
    ax.plot([0.07], [y - h + 0.055], marker=marker, color=color, ms=6.5, mec="white", mew=0.8)
    ax.text(0.11, y - h + 0.055, answer, color=INK, va="center", fontsize=7.2, weight="bold")
    ax.text(0.95, y - h + 0.055, verdict, color=INK2, va="center", ha="right", fontsize=6.6)

strip(0.80, 0.15, "Asked directly", None, "“Santiago de Chile.”", EDIT, "D", "edit holds")
strip(0.61, 0.47, "Thinks first",
      "“…I also recall that Chile has a region\ncalled the Kingdom of Bohemia… a small\narea in Santiago…”\n"
      "“…The capital of Bohemia itself was Prague.”",
      "“Prague.”", OWN, "o", "edit lost")
ax.text(0.02, 0.06, "Unedited model: Prague, asked directly and after thinking.", color=MUTED, fontsize=6.4, va="center")

# ---------------- panel (b): dumbbells ----------------
bx = fig.add_axes([0.545, 0.14, 0.395, 0.72])
order = [("Qwen-14B", "original"), ("Qwen-32B", "original"), ("Llama-70B", "original"),
         ("Qwen-32B", "v2, H100 (rerun)"), ("Qwen-32B", "v2, H100")]
by = {(r["model"], r["engine"]): r for r in data}
rows, y = [], 0.0
blocks = [("familiar", "Well-known facts (≥3 of 4 smaller distills know them)"),
          ("less_familiar", "Less familiar facts")]
for key, title in blocks:
    y -= 0.55
    bx.text(-0.47, y, title, color=INK, weight="bold", fontsize=7, va="center", ha="left",
            transform=bx.get_yaxis_transform())
    for i, k in enumerate(order):
        y -= 1.0
        if i == 4:
            y -= 0.35
        rows.append((y, key, k, i == 4))
    y -= 0.6
for y, key, k, s2 in rows:
    r = by[k][key]
    if s2:
        bx.add_patch(Rectangle((0, y - 0.48), 0.55, 0.96, fc=BAND, ec="none", zorder=0))
    bx.plot([r["own"], r["edited"]], [y, y], color="#b9b8b3", lw=1.6, zorder=1, solid_capstyle="round")
    bx.plot([r["own"]], [y], "o", color=OWN, ms=6.2, mec="white", mew=0.9, zorder=3)
    bx.plot([r["edited"]], [y], "D", color=EDIT, ms=5.8, mec="white", mew=0.9, zorder=3)
    lab = LABEL[k]
    bx.text(-0.012, y, lab, ha="right", va="center", fontsize=6.6, color=INK if s2 else INK2,
            weight="bold" if s2 else "normal", transform=bx.get_yaxis_transform())
    bx.text(0.552, y, f"n={r['n']}", ha="left", va="center", fontsize=6.0, color=MUTED)
bx.set_xlim(0, 0.55); bx.set_ylim(rows[-1][0] - 0.8, 0.2)
bx.set_yticks([]); bx.set_xticks([0, .1, .2, .3, .4, .5]); bx.set_xticklabels(["0", "10%", "20%", "30%", "40%", "50%"])
bx.tick_params(axis="x", length=0, labelsize=6.6, pad=2)
for s in ("left", "right", "top"):
    bx.spines[s].set_visible(False)
bx.grid(axis="x", color=RULE, lw=0.5); bx.set_axisbelow(True)
bx.set_xlabel("Share lost after thinking (facts the model knew, edit held when asked directly)",
              fontsize=6.4, color=INK2, labelpad=3)
fig.text(0.36, 0.955, "b  Edited answers vs the model's own answers, after thinking", weight="bold", color=INK, va="top", fontsize=7.8)
handles = [Line2D([], [], marker="o", ls="", color=OWN, mec="white", ms=6, label="model's own answer"),
           Line2D([], [], marker="D", ls="", color=EDIT, mec="white", ms=5.5, label="edited answer")]
bx.legend(handles=handles, loc="lower right", bbox_to_anchor=(1.12, 1.01), ncol=2, frameon=False, fontsize=6.6,
          handletextpad=0.3, columnspacing=1.0, borderaxespad=0.1)

for ext in ("png", "pdf"):
    fig.savefig(os.path.join(HERE, f"hero_sketch.{ext}"), dpi=240, facecolor="white")
print("wrote hero_sketch.png/.pdf")
