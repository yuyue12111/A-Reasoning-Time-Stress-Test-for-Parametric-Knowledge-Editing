#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W2-12/B1 — find real cases showing all three states of the main figure.

Required, on ONE case_id:
  N arm : B0 edit succeeds (b0ok)  ->  certification passes
  N arm : B3 chain mentions the old value AND the final answer reverts to it
  T arm : B3 final answer holds the new value

Scoring is delegated to cross_arm.per_case so the figure cannot disagree with
the table it sits next to.
"""
import glob, json, os, sys, re

sys.path.insert(0, "src")
import yaml
import cross_arm, metrics

SP = os.path.dirname(os.path.abspath(__file__)) + "/arms"
CFG = {arm: yaml.safe_load(open(f"{SP}/{f}"))
       for arm, f in [("N", "probe32b.yaml"), ("T", "probe32b_sup.yaml")]}

per = {arm: cross_arm.per_case(c, "ROME", "B3") for arm, c in CFG.items()}

cands = []
for cid, n in per["N"].items():
    t = per["T"].get(cid)
    if not t:
        continue
    if n.get("RR") is None:            # not b0ok -> certification did not pass
        continue
    if not (n["CLR"] == 1 and n["RR"] == 1):
        continue                       # need chain mention AND answer reversion
    if t.get("ES") != 1:
        continue                       # treated arm must hold the new value
    cands.append(cid)

print(f"cases satisfying all three states: {len(cands)}")

# --- pull the artefacts for each candidate -------------------------------
ds = CFG["N"]["dataset"]
cases = {c["case_id"]: c for c in
         (json.loads(l) for l in open(ds.get("fallback_path", ds["path"])))}
aliases = json.load(open("data/aliases.json"))


def row_of(cfg, cid, budget):
    pat = os.path.join(cfg["out_dir"],
                       f"{cfg['model_tag']}_ROME_{cfg['dataset']['tag']}_r*.jsonl")
    for f in sorted(glob.glob(pat)):
        for ln, line in enumerate(open(f), 1):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get("_meta") or d.get("error"):
                continue
            if (d.get("case_id") == cid and d.get("budget") == budget
                    and d.get("probe") == "efficacy" and d.get("decode") == "greedy"):
                return d, f, ln
    return None, None, None


rows = []
for cid in cands:
    c = cases[cid]
    s, o_old, o_new = c.get("s") or "", c["o_old"], c["o_new"]
    nb3, nf, nl = row_of(CFG["N"], cid, "B3")
    tb3, tf, tl = row_of(CFG["T"], cid, "B3")
    nb0, b0f, b0l = row_of(CFG["N"], cid, "B0")
    if not (nb3 and tb3 and nb0):
        continue
    cot = nb3.get("cot") or ""
    clean_cot = metrics._without_subject(cot, s)
    # where the old value first surfaces in the chain
    pos = None
    for al in [o_old] + aliases.get(o_old, []):
        m = re.search(re.escape(al), clean_cot, re.I)
        if m and (pos is None or m.start() < pos):
            pos = m.start()
    rows.append({
        "case_id": cid, "subject": s, "o_old": o_old, "o_new": o_new,
        "prompt": (nb3.get("q") or "")[:120],
        "chain_chars": len(cot), "chain_words": len(cot.split()),
        "old_first_at_char": pos,
        "old_at_frac": round(pos / max(len(clean_cot), 1), 3) if pos is not None else None,
        "N_B0_answer": (nb0.get("answer") or "").strip()[:80],
        "N_B3_answer": (nb3.get("answer") or "").strip()[:80],
        "T_B3_answer": (tb3.get("answer") or "").strip()[:80],
        "src_N_B3": f"{nf}:{nl}", "src_T_B3": f"{tf}:{tl}", "src_N_B0": f"{b0f}:{b0l}",
    })

rows.sort(key=lambda r: (abs(r["chain_words"] - 180), r["old_first_at_char"] or 9e9))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "b1_candidates.json")
json.dump(rows, open(out, "w"), ensure_ascii=False, indent=1)
print(f"wrote {out}  ({len(rows)} fully-resolved candidates)\n")
for r in rows[:12]:
    print(f"  case {r['case_id']:>4}  words={r['chain_words']:>4}  old@{r['old_at_frac']}  "
          f"{r['subject'][:26]:26} {r['o_old'][:18]:18} -> {r['o_new'][:18]}")
