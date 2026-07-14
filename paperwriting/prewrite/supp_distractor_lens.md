<!-- 写作前材料(gap-review distractor-lens-D3);折进 LaTeX 时复核数字;非写作真源 -->

> ⚠️ **G5 CONSORT 行数字过期,以此更正为准(draft 于 硬伤4 正解落库之前)。** 权威源=`results.json wa_main._g5_硬伤4` + `prereg-wseries §7.5`:
> G5 冻结 prereg 判据=**distractor max-stat**(o_old 超全 20 distractor,精确 p=1/21),本地重算 = **19/65 = 29.2%**(a2rev 5/16、a2held 13/41、calib 1/8);实跑 100% 是**更松的 z≥2** 版。**29.2% < 50% 地板 = 冻结门不过**(非 suggestive、非"待回传重算"——数据本地已算)。max-stat 窗=el_idx(整个 eligible 前窗)非字面 [m-20,m-1],故真值 ≤29%。W-A 承重腿=A2 null(不依赖 G5)。CONSORT 表 G5 行须**并列** z≥2(100%)与冻结 max-stat(29.2%,门不过)两口径,勿只报 100%。

# Supplementary — Distractor-Calibrated Logit-Lens: Instrument Calibration and CONSORT (W-A)

> **Admission gate.** This appendix documents the calibration and reporting discipline of the W-A representational probe. **Its inclusion in the paper is gated on the 7/14 internal review admitting W-A** (`_pending_draft_edits` W-series placeholder; `wa_main._verdict_714`). If W-A is admitted, this is the *entirety* of the instrument's credibility record; if not, drop the appendix. Numbers below are pre-write and **must be re-checked against `results.json` when folded into LaTeX**.
>
> **Scope discipline (prereg-wseries §5).** All headline conclusions rest on *behavioral* endpoints (RR, ES); the lens is a representational-side convergent probe only. This appendix never uses the lens as a stand-alone claim vehicle. Forbidden framings ("we measured the workspace", "the edit never enters the workspace", data-as-subject planning/premeditation/ignition/traceless) do not appear.

---

## 1. Why distractor calibration (design rationale)

The RQ2 figure (main text) reads a raw per-layer gap $g_\ell = \mathrm{logit}_\ell(o_{\text{new}}) - \mathrm{logit}_\ell(o_{\text{old}})$. Raw logits are **not comparable across layers** (their scale drifts with depth), so a raw gap cannot support a cross-layer/position *spike* statistic. W-A upgrades to a **within-layer, within-position distractor-calibrated $z$**:

$$z(o_{\text{old}}) = \frac{\mathrm{logit}(o_{\text{old}}) - \mathrm{mean}\big(\mathrm{logit}(d_1),\dots,\mathrm{logit}(d_{20})\big)}{\mathrm{std}\big(\mathrm{logit}(d_1),\dots,\mathrm{logit}(d_{20})\big)}$$

computed independently at each layer/position from a pool of **20 same-relation distractor objects** $d_1{\dots}d_{20}$ (prereg-wseries §0). Calibration removes the depth-varying logit scale, making the negative-gap band and the spike detector comparable across the stack. **Iron rule: never compare raw logits across layers** — every W-A endpoint is a calibrated $z$.

**Layer/decoder index convention (prereg-wseries §0; fixes the main-text off-by-one, hard-bug-2).** `hidden_states[0]` = embedding; `hs[k]` = decoder layer $k{-}1$ output; the **edit layer 12 $\leftrightarrow$ hs[13]**. All W-A axes and text are stated in **decoder-layer** numbers. Only the ~25 candidate columns of the unembedding are projected (full-vocab rank is used solely for small-sample descriptive figures at $k\in\{1,5,50\}$, never as an endpoint).

## 2. Distractor-pool construction (20 same-relation)

- **Pool.** For each case, 20 objects drawn from the CounterFact same-relation answer pool, **excluding** $o_{\text{old}}$, $o_{\text{new}}$, and their aliases; same semantic category; first token unambiguous (prereg-wseries §0).
- **Ambiguity criterion (smoke-fix, 7/7, frozen before data).** Ambiguity is judged **only on the leading-space variant's first token** (the natural in-text form). The first version, which also judged the no-space lowercase variant, let a short BPE first-piece veto most candidates (empirically 151/200 cases short of a same-relation pool of 20).
- **Backfill.** Where the same-relation pool is still $<20$, top up to 20 by cross-relation frequency and tag it (`_stats_n_same_relation` records the same-relation count per case). Main analysis uses all cases; the $n_{\text{same-relation}}<10$ subset is a sensitivity slice (weaker category priming).
- **Probe token set (detection).** $\{o_{\text{old}} + \text{all aliases (no } {\geq}4\text{-char filter, distinct from the metrics scorer)}\} \times \{\pm\text{leading space} \times \text{first-letter case}\}$, taking the max over the first tokens. If the $o_{\text{old}}$ first token is shared with other chain words or is a high-frequency generic piece, the case is **ambiguous-flagged**, excluded from the main analysis, and reported with/without as a sensitivity pair.

## 3. Position exclusion (token-id level; guards copy/induction heads)

Exclusion uses the **wide** surface-form set (conservative — removes more candidate leakage positions); detection of $o_{\text{old}}$ uses the **strict** criterion of §2 (avoids over-counting). Six exclusion classes (prereg-wseries §2):

1. Every token position of any $o_{\text{old}}$ surface form.
2. The position **immediately before** each occurrence (the prediction position).
3. In the silent (A1) analysis, **all suffix positions after the $o_{\text{old}}$ first-token id appears** — this is the explicit guard against induction/copy heads re-emitting $o_{\text{old}}$ downstream.
4. Cases where $o_{\text{old}} \subset \text{subject}$: **whole chain excluded**.
5. $\pm 10$ tokens around any $o_{\text{old}}$/subject mention, plus the prompt-restatement region.
6. Mention positions computed on the **original text** (exclusion-style localization; `offset_mapping` maps char$\to$token).

The $o_{\text{new}}$ neighborhood is **not** excluded — it is handled by same-category distractor calibration rather than masking.

## 4. Spike criterion and permutation max-stat (exact $p = 1/21$)

Frozen before seeing data (prereg-wseries §2):

- **Band.** Fixed from **10 calibration cases** (excluded from the inference set); fallback band = **decoder 16–48**.
- **Case scalar.** $S_{\max}$ = the max calibrated $z$ over qualifying (band $\times$ window) positions.
- **Null / permutation.** Each of the 20 distractors takes its turn as the pseudo-target and is scored by the *same* max-stat. A case is **positive iff $o_{\text{old}}$ exceeds all 20 distractors** — i.e. $o_{\text{old}}$ is the single largest of 21 exchangeable candidates, giving an **exact one-sided $p = 1/21 \approx 0.048$** per case.
- **Aggregation.** All statistics are **case-level** (position-level reads, ~$5\times10^5$/case, are pseudo-replication and get no test); paired bootstrap 10k; across cases **BH-FDR $q<0.05$**.

## 5. CONSORT — 32B primary analysis (ROME $\times$ CounterFact, greedy $B_3$)

Enrollment and gate attrition. *(Per-gate denominators differ because gates apply to different teacher-forced subsets; the full one-tree reconciliation of 151/102/82/29 is a fold-in check — numbers below are the reported per-gate denominators, stated honestly rather than forced into a clean tree.)*

| Stage | Count | Source (`results.json`) |
|---|---|---|
| Enrolled (CF cases) | 200 (nominal) | `wa_main` / `wide_census_traceless` |
| Excluded — subject-overlap ($o_{\text{old}}\subset$ subject) | 47 | `wide_census_traceless.n_subject_overlap_excluded` |
| Paired census $n$ | 151 | `wide_census_traceless.n_paired` |
| — of which: b0ok / reverted / held | 109 / 17 / 92 | `wide_census_traceless.{b0ok,reverted,held}` |
| **G2** re-edit $B_0$ fidelity | 12/102 fail (~88% pass, $\geq$80% ✓) | `wa_main.gates.G2` |
| **G3** teacher-forced replay argmax | 19/82 fail, median .959 | `wa_main.gates.G3` |
| Ambiguity flag | **75/82 flagged** ⚠ over-marked | `wa_main.gates.amb_flag` |
| **G4** base sensitivity (o_old on CLR0 chains) | 4/29 = 13.8% $\ll$70% **FAIL** | `wa_main.gates.G4_base_a1` |
| **G5** pre-mention detection | 65/65 = 100% (post-hoc $z\geq2$) | `wa_main.gates.G5_premention` |

**Analysis populations (edited arm).**
- **A1** (silent representation, edited CLR0 chains): main (no-amb) 1/4; sensitivity (+amb) 2/16 = 12.5%, Wilson [.035,.360], binom $p=.175$. (`wa_main.A1`)
- **A2** (pre-mention window, reverted vs held): $n=[10,30]$; AUC $0.507$, perm $p=0.487$; median $z$ reverted 4.61 vs held 4.43. (`wa_main.A2`)
- **A3** (edited$-$base paired $\Delta z$): all $n=48$, median $-0.075$ [$-0.172,+0.016$] (contains 0); by group a2rev $n=8$ $-0.189$, a1 $n=16$ $-0.016$, a2held $n=20$ $-0.048$. (`wa_main.A3`)

**Two reporting caveats to carry verbatim.**
- **G5 operationalization (hard-bug-4).** Reported $65/65=100\%$ uses a **fixed $z\geq2$ variant**, not the frozen distractor max-stat ($p=1/21$). Git archaeology (commit 39ca2e9) cannot establish $z\geq2$ preceded unblinding, so G5 is reported **"operationalized post-hoc (fixed $z\geq2$ variant; the frozen criterion was a distractor max-stat)"** and **downgraded from a gate to suggestive support**. A prereg-correct max-stat G5 requires re-transferring `results/wa/base_r*of8.jsonl` (per-distractor $z$) for recomputation (prereg-wseries §7.5). A2-null / A3 / G4 use their own frozen calibers and are unaffected.
- **Ambiguity flag defect.** The $75/82$ flag is over-marked (an artifact of the all-variants criterion that predates the §2 distractor fix). Both versions are reported; the **ambiguity-included** population (e.g. A1 $n=16$) is primary; the instrument defect is noted.

## 6. CONSORT — cross-editor / cross-scale ladder (appendix exploratory)

Reported for external-validity breadth only; **exploratory** (small $n$, chains unclustered; formal calls await the case-level A3 paired $\Delta z$, 7/14). Cross-model base-state $g3\_pass=0$ is constructive (a different model's argmax must replay low), so base states run on the G4/A3 caliber, not G3 (prereg-wseries §7.5 operationalization note).

| Arm | edited g3 (med) | G2 fail | A1 edit/base | A2-rev edit/base | A2-held edit/base | calib edit/base |
|---|---|---|---|---|---|---|
| Sampling-F3 (32B, s0/s1/s2)* | g3s 237/237 (min .994) | 34/271 ≈12.5% | 8/64 (single-state) | 4/39 | 12/110 | 1/24 |
| MEMIT-14B | 1.0 | 10/89 ≈11% | 5/26 / 11/36 | 14/23=61% / 14/23=61% | 7/22=32% / 8/22=36% | 1/8 / 3/8 |
| ROME-14B | .984 | 16/90 ≈18% | 0/22 / 10/31 | 2/10 / 5/10 | 5/34 / 12/40 | 3/8 / 4/9 |
| ROME-Llama-8B | .963 | 15/100 | 11/37=30% / 18/44=41% | 3/11 / 6/12=50% | 10/30 / 11/36 | 6/7 / 5/8 |

\*Sampling-F3 uses the G3s (top-20 membership $\geq$95%) gate for temperature-0.6 chains, since the argmax-based G3 mis-scores sampled chains (`wa_extensions.sampling_f3.g3s`, `g2_caveat`; prereg-wseries §7.5 G3s). Raw positive rate ~11% ≈ 2.3$\times$ the 4.8% null; formal call awaits case-level clustering (3 seed chains per case are non-independent).

**Cross-editor signal (exploratory, do not over-claim).** ROME-14B edited $\ll$ base (A1 0% vs 32%; a2rev 20% vs 50%) — ROME broadly suppresses the $o_{\text{old}}$ representation. MEMIT-14B edited $\approx$ base (a2rev 61% = 61%) — a bypass-direction pattern. Llama-8B sits between (edited slightly below base). This *may* couple to the behavioral RR (MEMIT 0.333 > ROME-14B 0.162), but $n$ is small and chains are unclustered; report as a suggestive within-model signal only. (`wa_extensions.rome14b.cross_editor_signal`, `.llama8b.note`)

## 7. What the instrument credibly buys (honest reading)

The lens yields three admissible outputs and one inadmissible one; behavioral endpoints (RR, ES) carry the load throughout.

- **A2 — clean null (admissible).** Reverted and held chains show **no difference** in pre-mention $o_{\text{old}}$ representation (AUC $0.507$, perm $p=0.487$). Read strictly as a null: **representational presence does not track the behavioral outcome** — the representation is comparably elevated whether or not the answer reverts. This converges, at the representational level, with M1 (in-chain content mediates the answer) and held-14/14 (necessary-not-sufficient). *(Optional, 7/14-gated cross-reference, no data as subject: independent work on commitment as the operative locus — 2606.13603 "Beyond the Commitment Boundary", 2605.06723 pre-verbalization commitment — is consistent with this presence-vs-outcome dissociation; cite-as-frame in Discussion only, per prereg-wseries §5.)*
- **A3 — bypass direction (admissible, hedged).** edited $\approx$ base (median $-0.075$, CI contains 0; slight negative trend) is consistent with 32B ROME leaving the associated knowledge intact outside the edited pathway.
- **G5 — suggestive only.** Pre-mention $o_{\text{old}}$ is broadly detectable under the $z\geq2$ variant, but as post-hoc operationalization it supports rather than gates.
- **A1 — inadmissible (G4 FAIL).** Base sensitivity on CLR0 chains is only 13.8% ($\ll$70%), so the silent-representation null is **uninterpretable**: we can **neither assert silent leakage exists nor claim reversions "always leave a trace"** (prereg-wseries §1/§6 discipline; the "reversions leave an auditable trace" reading is supported elsewhere by the judge-level taxonomy and the wide-string census (0/17), not by this lens).

The wide-string census (`wide_census_traceless`: CLR0-wide$\cap$reverted = **0/17**; CLR0-wide$\cap$held = 31/35) is a separate string-level result and is reported as a census, not as an A1 lens claim.

---

### Fold-in checklist (when moving to LaTeX)
1. Re-pull every count from the cited `results.json` path (values are pre-write).
2. State the layer axis in **decoder** index (hs[k]=decoder k−1; edit layer 12); do not repeat the main-text off-by-one.
3. Keep the two verbatim caveats (G5 post-hoc; amb-flag defect).
4. A1 = uninterpretable; never phrase as a positive silent-trace result.
5. A2 = null (presence ≠ outcome), not "commitment confirmed"; A3 = suggestive bypass direction.
6. Ladder table = exploratory; no cross-editor mechanism claim without case-level A3.
7. Whole appendix contingent on the 7/14 W-A admission ruling.