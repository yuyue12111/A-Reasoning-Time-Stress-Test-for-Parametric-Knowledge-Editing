<!-- 写作前材料(gap-review llm-compliance-D6);折进 LaTeX 时复核数字;非写作真源 -->

# Methods material — LLM-use compliance (gap-review D6)

**Purpose.** Prewrite prose for two folds: (a) one sentence in §3 that introduces every LLM judge as an *instrument* (model version + full prompts + raw votes released in supplementary), and (b) a pre-filled LLM-use declaration line for the AAAI-27 reproducibility checklist. Both discharge the AAAI-27 policy on LLM use: **AI is not an author, AI is not a citable source, judicious instrumental use is permitted.**

---

## 1. §3 judge sentence (drop-in; place where the judge panel first appears in the metric/§3 methods paragraph)

> Every LLM-derived label in this work is produced by a panel of independent judges (three for the taxonomy and reversion-validation panels; two-of-three majority also used for the CLR-polarity check) used strictly as a measurement instrument—never as an author and never cited as a source of facts; the exact model and version identifier, the full verbatim judging prompts (the descriptive route prompt and its edit-status-blind neutral variant), and the raw per-judge votes for every classified chain are released in the supplementary material, so that both the inter-judge reliability of the taxonomy (Fleiss' $\kappa{=}0.79$ over the widened committed-reversion pool; $0.52$ on the original narrow pool) and the judge-vs-rule scorer validation (the neutral panel agrees with the strict de-contaminated reversion rule at Cohen's $\kappa{=}0.836$, $n{=}87$) are independently recomputable.

*Notes for the LaTeX author.*
- The shared-model-family bias caveat is **already stated** in the current draft (§3 parenthetical and the §5 taxonomy paragraph); keep it—do not duplicate it here.
- Do **not** print a bare vendor/version string in the running text. Pin the exact model + snapshot/version identifier in the supplement only (safe for double-blind review and for reproducibility). The §3 body carries the instrument framing; the supplement carries the version.
- This sentence is consistent with the planned §1/§7 release commitment (code, de-contaminated scorer, budget harness, prereg docs, **judge prompts + votes**)—reuse the same supplementary manifest, do not create a second release list.

## 2. Reproducibility-checklist LLM-use declaration line (pre-filled for AuthorKit27)

> **LLM usage.** Large language models are used in this work **only as evaluation instruments**: LLM-judge panels for the chain-reversion taxonomy (§5) and for two scorer-validation studies (neutral OLD/NEW/NEITHER reversion validation and a CLR-polarity check, §3). For each, the model version, the full verbatim prompts, and the raw per-judge votes are released in the supplementary material, so every judge-derived statistic is recomputable. **No LLM is an author of this paper and no LLM output is used as a citable source**, consistent with the AAAI-27 policy on LLM use. Any incidental LLM assistance in drafting or code was minor, fully author-reviewed, and did not originate any scientific claim, result, or number reported herein.

*(If AuthorKit27 asks a yes/no "Did you use LLMs?" gate: answer **Yes — as documented evaluation instruments and, incidentally, for author-reviewed drafting/coding assistance**, then paste the paragraph above.)*

## 3. Inventory of LLM instruments to document in the supplement (completeness check for the release manifest)

All are the *same* three-judge, majority-vote / strict-precedence protocol; list each so the "prompts + votes" release is exhaustive:

| Instrument | Where used | What the supplement must contain |
|---|---|---|
| Route taxonomy panel (3 judges, strict precedence, verbatim-span required) | §5 (RQ2) | prompt, per-chain per-judge votes, aggregation rule, Fleiss $\kappa$ per scale |
| Neutral reversion-validation panel (edit-status-blind OLD/NEW/NEITHER) | §3 metric | neutral prompt, per-answer votes ($n{=}87$), confusion vs. $\mathrm{RR}_s$/RR |
| CLR-polarity check ($\geq 2$ judges over reverted chains) | §3 metric footnote | prompt, per-chain votes ($n{=}37$), polarity false-positive tally |
| Multi-hop scorer-audit panel | §RQ1 (2-hop) | prompt, scorer-correction decisions (diacritic / short-target false positives) |

## 4. AAAI-27 policy mapping (one line each; for the author's own sanity-check, not for the paper body)

- *AI ≠ author* → judges are apparatus; authorship line contains only human authors. ✔ (declaration §2)
- *AI ≠ citable source* → no LLM output appears in the bibliography; judge labels are reported as measurements with agreement statistics, not as cited facts. ✔ (§3 sentence + §2 declaration)
- *Judicious use permitted* → instrumental judging is disclosed and fully released; incidental drafting/coding assistance disclosed and author-reviewed. ✔ (§2 declaration)
