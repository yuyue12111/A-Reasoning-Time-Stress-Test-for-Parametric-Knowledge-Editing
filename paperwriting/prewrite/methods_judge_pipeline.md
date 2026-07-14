<!-- 写作前材料(gap-review judge-methods-D2);折进 LaTeX 时复核数字;非写作真源 -->

# Judge Pipeline and Scoring Validity (methods home for §3.5 / supplementary)

*Purpose: give the LLM-judge machinery and the scorer-validity evidence a single
methods home. Two facts are currently structurally misplaced and are relocated here:
(i) the metric-validation Cohen's $\kappa{=}0.836$, today buried in §2 Related Work;
(ii) the **subject-scrub** decontamination step, which the draft's scoring section omits
(it names only word-boundary matching and the alias-length cutoff). This is prose for
folding into LaTeX; every number is traced to `paper/results.json`.*

---

## 1. Three decontamination filters on the generative scorer (not two)

Every hit test in the paper is run over text that has passed **three** decontamination
filters, applied in `src/metrics.py`. The draft's methods section documents only the
first two; the third is load-bearing and must be stated.

1. **Word-boundary matching** — reject sub-token matches (drafted, §3.4).
2. **Alias-length cutoff** — drop aliases shorter than four characters (drafted, §3.4).
3. **Subject-scrub** (`_without_subject`, `metrics.py:42`, applied at `metrics.py:148`
   for `score()` and identically in the per-case indicator paths). Before any $o_{\mathrm{old}}$/$o_{\mathrm{new}}$
   test, every case-insensitive occurrence of the prompt **subject string** is excised
   from both the answer and the chain.

   *Why it is required.* CounterFact objects are frequently substrings of the subject
   (e.g. subject *"Miami International Film Festival"* contains $o_{\mathrm{old}}{=}$*"Miami"*).
   A chain that merely **restates the prompt** would otherwise register a spurious CLR/RR
   hit — and a spurious ES miss on the "$\text{answer does not contain } o_{\mathrm{old}}$" clause —
   without ever recalling the old fact. Scrubbing the subject deletes restatement while
   preserving a genuine recall ("...located in *Miami*"). When no subject field is present
   the text is returned unchanged (backward compatibility).

   *Downstream validation (V1 / B8).* The CLR-polarity audit confirms subject restatement
   is exactly the dominant false-positive class in the *un-scrubbed* extractor: of 5 raw
   false positives, **4 are subject-restatement** (3 unanimous + 1 split vote), vs. 1
   quotation/meta and 1 negation-only. Because the paper-caliber CLR applies the scrub
   *first*, these vanish under the reported protocol: raw affirmative-recall precision
   $75.7\%$ ($n{=}37$, 28 genuine / 5 false-positive / 4 split) rises to $\approx\!94\%$
   genuine at paper caliber, leaving only a $\approx\!6\%$ polarity inflation (negation-form
   mentions such as "not French"; Wilson $\approx[1.7\%,20\%]$). Subject-scrub is thus the
   third leg of the decontamination story, validated by the same audit that certifies CLR
   polarity.

---

## 2. Two judge panels — do not conflate their $\kappa$

The paper uses LLM judges in **two structurally different roles**. They yield two
different agreement statistics; the draft currently lets one ($\kappa{=}0.836$) float in
Related Work, where a reader cannot tell it apart from the taxonomy's inter-judge $\kappa$.

| | **Panel A — scorer validation** (`metric_validation`, W2/E-SEMJUDGE) | **Panel B — route taxonomy** (`rq2_taxonomy`) |
|---|---|---|
| Reads | the **answer** | the **raw chain-of-thought** |
| Task | commit `OLD` / `NEW` / `NEITHER`; never told the edit's status | classify the route to $o_{\mathrm{old}}$ (4-way) |
| Validates | the answer-level metric ($\mathrm{RR}_s$) is not a substring artifact | *how* reverted chains reach $o_{\mathrm{old}}$ |
| Statistic | **Cohen's $\kappa$** (metric vs. judge) | **Fleiss' $\kappa$** (agreement *among* the 3 judges) |
| Value | $\kappa{=}0.836$ vs. $\mathrm{RR}_s$ | $0.52$ pooled / $0.59$ at 32B (contaminated prompt) |

### 2a. Panel A — semantic validation of the strict reversion metric (relocate $\kappa{=}0.836$ here)

A neutral three-judge panel is prompted only to read an answer and decide whether it
commits to the `OLD` value, the `NEW` value, or `NEITHER` — never told that an edit was
applied or whether it held. Against our **strict, decontaminated** reversion metric
$\mathrm{RR}_s$ ($o_{\mathrm{old}}$ asserted **and** $o_{\mathrm{new}}$ absent) the panel agrees at
**Cohen's $\kappa{=}0.836$** (agreement $0.931$, precision $0.92$, recall $0.85$;
$n{=}87$ stratified answers; confusion TP$=23$/FP$=2$/FN$=4$/TN$=58$). The **loose** RR —
by design an upper bound that also counts "edit held but old value mentioned in passing" —
agrees far less (Cohen's $\kappa{=}0.389$, precision $0.48$; FP$=28$), and the judge
confirms this over-count is genuine. True reversion therefore lies **between** $\mathrm{RR}_s$
(lower bound) and RR (upper bound) — exactly the bracket the paper reports.
*Caveats to keep with the number:* judges are from our own model family (a shared-bias
caveat); $33$ further answers were dropped to transient API rate limits and, being mostly
non-reversions, would only raise agreement (so $0.836$ is a lower bound).

### 2b. Panel B — the taxonomy panel and its aggregation rule

Three independent judges label each chain from the **raw CoT** under a **strict precedence**
$\text{Reflective-override} > \text{Bridge} > \text{Recall} > \text{Associative}$, and must
**quote a verbatim span** for Recall/Bridge/Reflective-override — if none can be quoted, the
label defaults to Associative. Votes are aggregated (`aggregate_votes`, `chain_classify.py:131`):

- **held-precedence first**: if $\ge2$ judges mark the answer as committing to $o_{\mathrm{new}}$
  (or out-of-population), the case is `Excluded-held` and drops out of the taxonomy;
- else **majority** ($\ge2$ judges agreeing) sets the label;
- else a **3-way split** takes the **highest-precedence** label (min index in
  `[Reflective-override, Bridge, Recall, Associative]`).

An orthogonal binary **contests-edit** stance (chain verbatim calls $o_{\mathrm{new}}$ wrong)
is carried as a second column (pooled $15.8\%$), cross-cutting all four routes.

*Reporting $\kappa$ honestly at near-unanimous cells.* Fleiss' $\kappa$ is only interpretable
where categories vary. Under the contaminated (primed) prompt it is $0.52$ pooled and
$0.588$ at 32B; it is **undefined at 14B** (the sole dissenting vote is a held exclusion,
not a route) and **degenerate/negative at 7B** ($\kappa{=}-0.091$ with raw agreement
$\bar P{=}0.833$ — a single dissent against a $\approx\!85\%$-Bridge base rate drives
$\kappa$ negative). We therefore report $\kappa$ **alongside raw agreement** and treat
near-unanimous cells qualitatively; low-count routes are read as route frequencies and
pooled across scales.

---

## 3. Neutral de-biasing prompt and the contamination-rerun history

The taxonomy panel was run under **two prompt variants** (`src/chain_classify.py`,
`JUDGE_PROMPTS = {main, neutral}`), and the difference between their outputs is itself a
reported robustness check — a **precedence/priming ablation**.

- **Main (contaminated) prompt** (`JUDGE_PROMPT_TEMPLATE`): tells judges that a separate
  probe proves the edit is *still installed* and the chain is *"routing around an intact
  edit"*, and states the precedence explicitly. Both facts could prime the Bridge label.
- **Neutral prompt** (`JUDGE_PROMPT_NEUTRAL`): removes both. Judges are told to assume
  nothing about whether the edit is intact/weakened/erased, and that the four routes are
  *"EQUALLY admissible; do not favor any"* — the precedence tie-break is stripped.

**Rerun ledger** (all ROME $\times$ CounterFact, greedy, judge-gated committed reversions;
the two pools are reported **side by side and never merged**):

| Pool | $n$ | Bridge | Recall | Refl.-override | Associative | Fleiss $\kappa$ |
|---|---|---|---|---|---|---|
| Contaminated main (7B/14B/32B) | 19 | 17 (89.5%, CI [0.74,1.0]) | 0 | 2 (10.5%) | 0 | 0.52 pooled |
| **Neutral rerun (17-pool)** | 17 | 14 (82.4%) | 2 | 1 | 0 | 0.765 pooled / 0.827 @32B |
| **Widened B16 (50-pool)** | 50 | 34 (**68%**) | 11 (22%) | 4 (8%) | 1 (2%) | — |

Reading of the ledger:

- **Bridge dominance survives de-biasing** (89.5% → 82.4%), so it is not a priming
  artifact of the precedence-stated main prompt. Inter-judge agreement actually *rises*
  under the neutral prompt (pooled $\kappa$ $0.52 \to 0.765$; 32B $0.588 \to 0.827$;
  raw agreement $\bar P{=}0.922$).
- The **one qualitative change** is Recall $0 \to 2$: removing the anti-recall priming
  reveals flat recall as a **real minority route**, not an instrument-manufactured zero.
  This is confirmed at scale in the 50-pool (Recall 22%).
- **Population membership is judge-sensitive**: $3/18$ unique cases ($3/19$ by
  (scale, case) rows) flip between in-population and held across prompt variants — reported
  as a limitation, with the neutral run standing as a robustness appendix.
- The **Associative (residual catch-all) route is a near-empty minority**
  under judges (1/50 in the widened pool, and that one case is a 2–1 split), consistent
  with the widest-string census finding 0 of 17 committed reversions carrying no
  $o_{\mathrm{old}}$ trace. (Kept descriptive; full taxonomy claims live in §5.)

**Headline caliber (2026-07-08 ruling).** The contrib-2 route figure is the **50-pool
68% Bridge** (B16: 7 cells / 2 families / 3 decode-dose configs); the neutral **17-pool
82.4%** is reported as a *neutral-judge robustness companion*, in the same table but a
separate column — the two pools are never pooled into one number. The earlier "$\sim$81% /
$\sim$90% bridge" figures (contaminated 17/19 and the S1 draft) are superseded.

---

## 4. Judge as released instrument (compliance one-liner, D6)

The judges are LLM instruments (Claude, our own model family — the shared-bias caveat is
stated at every $\kappa$). Per AAAI-27 policy an LLM is **not a citable source**; the panel
therefore appears only as a released instrument: **model version, the full `main` and
`neutral` prompt templates, and the raw per-chain votes are released in the supplementary
material** (this also satisfies the AIA CFP's encouragement to release evaluation tooling).

---

### Cross-references for the LaTeX pass
- §3.4 (Word-Boundary Scoring): add subject-scrub as the third filter, or move all three
  filters here and retitle "Decontaminated Generative Scoring".
- §2 Related Work "Our boundary" paragraph: **remove** the $\kappa{=}0.836$ / $0.389$
  sentences (relocated to §2a above); leave only the one-line pointer to this section.
- §5 Taxonomy: the aggregation rule (§2b) and rerun ledger (§3) are the methods backing;
  keep the route *findings* in §5, the *pipeline* here.
- Fleiss-$\kappa$ table note in §5 must match §2b: undefined @14B, $-0.091$ @7B (not
  "undefined at 7B/14B"), report raw agreement alongside.
