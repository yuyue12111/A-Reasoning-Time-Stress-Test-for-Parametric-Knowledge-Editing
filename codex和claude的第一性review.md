The draft is unusually self-aware, but the front matter still outruns the evidence.

**A. Over- And Under-Claims**  
**Over-claim: “systematically eroded.”** The abstract says edits are “systematically eroded” as CoT unfolds ([paper/draft.md (line 13)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:13)), and the intro says edits are “systematically pushed back” ([line 31 (line 31)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:31)). That is too broad. From the numbers, B3 helps or is flat in several regimes, and multi-hop marginal ES rises. The defensible claim is: **large single-hop ROME edits show significant B3 erosion; conditional B0-success cases can erode even when marginals improve.**

**Over-claim: capability as the “driver.”** The draft repeatedly says matched families “indicat[e] the driver is capability/scale” ([line 13 (line 13)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:13)) or “isolat[e] capability” ([line 17 (line 17)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:17)). Later it hedges correctly: “consistency statement, not a causal proof” ([line 272 (line 272)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:272)). The hedge is right; the abstract wording is not. Six model points, two Llama points, a 7B math-base confound, Llama hyperparam transfer, and dropped 70B degenerates do not isolate capability. Say “consistent with capability/scale” throughout.

**Over-claim: continuous thinking-budget axis.** Related work says the paper studies a “continuous thinking-budget axis ($B_0$--$B_4$)” ([line 61 (line 61)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:61)). The provided evidence is essentially B0 vs B3. Unless B1/B2/B4 curves are actually shown later, this is a wording bug. It should be “a zero-vs-long budget contrast.”

**Over-claim: causal mechanism is closed.** Abstract B says the intervention “causally confirms chain-internal re-derivation” ([line 17 (line 17)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:17)); RQ3 says “the answer reverts because the old fact is re-derived in the chain” ([line 249 (line 249)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:249)). But the draft itself admits the decisive mediation experiment is not run: “Cleanly breaking the circularity requires a chain-substitution mediation experiment” ([line 253 (line 253)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:253)). Current data support **a signed, specific intervention on a causal competitor**, not full proof that natural reversion is mediated by the textual chain.

**Over-claim: logit-lens rules out erasure.** “Logit-lens analysis on 32B rules this out” ([line 34 (line 34)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:34)) is too strong. The narrow result is good: cloze top-layer still predicts `o_new` in reverted cases ([line 181 (line 181)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:181)). But this is one model, small reverted-n, no per-case CI, and a cloze probe rather than the actual generation trajectory.

**Over-claim: zero-thinking “reports the trend backwards.”** The draft says zero-thinking evaluation “reports the trend backwards” ([line 31 (line 31)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:31)). That is rhetorically stronger than the numbers. B0 ES is not a clean increasing trend across all points. Safer: zero-thinking **misses the high-end thinking tax**.

**Under-claim: the control battery is the strongest paper.** The N/T/D/P battery is the highest truth-to-claim component: placebo inert, suppress-new harmful, suppress-old helpful ([line 251 (line 251)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:251)). In my derivation, this should carry the paper. The draft instead leads with capability-emergence, the most fragile part.

**Under-claim / missed axis: thinking is not the explanatory variable by itself.** The draft notes the key inversion in multi-hop: marginal hop-ES rises because B0 cannot express the hop ([line 168 (line 168)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:168)). It also notes base recall at 7B ([line 281 (line 281)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:281)). But it never reframes the x-axis as **availability of a competing prior / whether reasoning opens an alternate retrieval route**. That is a better scientific explanation than “more thinking hurts.”

**B. Part-6 Framing Tournament**  
They did not miss the three framings; they chose the riskiest one as the headline.

1. **Evaluation-validity framing:** present but demoted. They say zero-thinking misses the effect and word-boundary scoring matters ([lines 44–47 (line 44)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:44)). This is safer than the capability headline.
    
2. **Local-edits/global-reasoning conflict:** present and strong. RQ2/RQ3 are basically this framing. It should probably be the main story.
    
3. **Capability-emergent robustness failure:** chosen as headliner. This is novel, but the most attackable because the causal scale interpretation is undercontrolled.
    

My ranking remains: **mechanism/fix > evaluation-validity > capability-emergence**. The draft’s ranking is the reverse.

**C. Part-8 Experiments Vs Draft Limitations**

|My experiment|Draft concession?|Honest or dodge?|
|---|---|---|
|Semantic audit of ES/RR/CLR main cells|Partial only: strict RR judge validation is reported ([line 73 (line 73)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:73)).|Partial dodge. It validates strict reversion, not semantic ES-drop or CLR across main cells.|
|Per-case base recall / OLD-vs-NEW margin|No real concession; only aggregate 7B base recall is mentioned ([line 281 (line 281)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:281)).|Dodge/omission. This is central to capability-vs-retrievability.|
|Equal-length non-reasoning control|Not conceded. Prompted sibling CoT is named instead ([line 287 (line 287)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:287)).|Dodge/omission. Prompted-CoT sibling is useful but does not test length exposure.|
|Chain substitution / censoring mediation|Explicitly conceded as future/camera-ready ([line 253 (line 253)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:253)).|Honest in body, but contradicted by causal wording in abstract/intro.|
|High-quality edit control|Not conceded. They admit modest magnitudes ([line 275 (line 275)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:275)) but do not ask whether stronger B0 edits still erode.|Dodge/omission. Weak B0 ES is a major confound.|
|Second-model N/T/D/P battery|Conceded: “one operating point on one model” and 14B replication pending ([line 262 (line 262)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:262)); editor/dataset generalization pending ([line 284 (line 284)](/Users/whyu/GitProjects/why-aaai27/paper/draft.md:284)).|Honest. This is scoped correctly.|

Bottom line: the draft is strongest when it says **“old-token chain suppression is a signed, specific, dose-controlled intervention on Qwen-32B/ROME/CF.”** It is weakest when it says **“capability is the driver”** and **“causally confirms re-derivation.”** Those should be softened before submission.

以上为codex。

Read the full draft (302 lines). The headline finding is exactly what I blind-guessed would be the weakest of my Part-6 framings: **"capability-emergent erosion"** — the n=6 scaling/emergence story (their contribution #1, all three abstract variants). The draft is also far more self-aware than most: it pre-empts a large fraction of my Phase-1 objections with explicit hedges (the ΔCLR circularity, the RQ2/RQ3 non-independence, the GSM8K −0.15, the clamp confound, the degenerate-drop bias, the o_old-supervision caveat). So the interesting findings are (i) the few places it still over-reaches _despite_ that candor, and (ii) the two deep objections it never names at all — both of which my independent derivation flagged as load-bearing.

---

## (a) Over- and under-claims vs. my derivation

### OVER-claims

**O1 — The abstract leads with the weakest metric.** All three abstracts and contribution #1 headline the _ES-drop_ emergence ("reaches $-10.6$pp (significant) at Qwen-32B," "emerges with capability"). But §4 itself concedes the ES-drop emergence is _not_ robust: "_The ES-drop and RR slopes are direction-robust but their significance leans on the cross-family pooling (their within-Qwen CIs contain zero), which is the honest reason we foreground CLR_" (line 159). So the title-level claim ("Thinking _Undoes_ Editing" = answer-level ES/RR loss) is carried in the abstract by the one metric that survives _only_ through the family-confounded 6-point regression. My Part 1 staked the paper on the suppression result precisely because ES-drop emergence is the fragile part; the draft puts the fragile part on the marquee.

**O2 — "Capability not math-specialization" rests on ~1 corroborating point, and the alignment is selective.** The draft calls cross-family agreement "_the headline structure of Table 1_" and "_a striking cross-family-symmetric result_" (line 151). But Llama has only two sizes, so the entire "family-level neutralization of the math confound" is two matched pairs — really one _significant_ corroboration (70B↔32B). And the alignment is cherry-picked by metric: it holds for CLR (0.340 vs 0.335; 0.529 vs 0.545) and top-end ES-drop (0.107 vs 0.106), but **RR does not align at the low end — 0.144 vs 0.080, ~1.8×** (the draft prints this at line 151 but still folds it under "align"). Crediting them: the discordant number is disclosed, so this is over-claim _in emphasis_, not concealment.

**O3 — "100% intact" and the logit-lens curve over-state precision from n≈10–17 with no CI.** Contribution #3 and the abstract assert "_the edit is intact at the cloze position (100% installed on reverted cases)_" and quote a g_L curve to three digits ($g_8{=}{-}0.246$, $g_{12}{=}{-}0.351$, $g_{56}{=}17.8$). The taxonomy table (line 204) shows the reverted population is n=4/5/10 (19 pooled); the raw curve has no n and no CI. Two distinct issues: (i) ruling out _erasure_ from "100% intact" is logically fine even on small n — but "100%" of ~10–17 cases reported bare in the abstract is false precision; (ii) the stronger claim — that the mid-layer negative dip is "_the substrate a multi-step chain can latch onto_" (line 184) — **needs a non-reverted control group** (is the dip specific to reverted cases, or universal across all edited cases including successes?). The draft never reports the non-reverted baseline, so the dip currently explains nothing about _why these cases reverted_. This is my Part-8 #6, and it is not flagged.

**O4 — "Causally confirms" overshoots the body's own concession.** Abstract B: "_since touching only the chain fixes the answer, it causally confirms chain-internal re-derivation_." But §6 (line 253) explicitly walks this back: the RQ2 probe and RQ3 fix "_may not be independent … both ultimately read off the same underlying logit geometry_," the clean test (E-CHAINSUB mediation) is "_reserved for the camera-ready_," and "_we … do not claim it is resolved._" The N/T/D/P battery legitimately establishes that _the intervention works and is o_old-specific_; it does **not** establish that _reversion is caused by in-chain re-derivation_ (the cloze-geometry confound). The abstract conflates "the fix is causal" with "the mechanism is proven."

**O5 — Table 1's flagship cell doesn't reconcile.** Line 136: ES@B0 0.595, ES@B3 0.495, ES drop **0.106**. But 0.595 − 0.495 = **0.100**. Every other row reconciles to ±0.001; only the single significant Qwen point is off by 0.006 (presumably ES cells rounded, drop from unrounded). It's minor, but it's the headline cell of the centerpiece table — a reviewer who subtracts will notice.

### UNDER-claims

**U1 — They bury their best result.** CLR is the only metric whose slope survives every leave-one-out _and_ within Qwen (slope 0.218, R²0.91; my recompute confirms). The draft treats it as the defensive fallback ("_the honest reason we foreground CLR_"). The sharper paper inverts the priority: the robust, publishable finding is "**reasoning re-surfaces the edited-away fact, and this scales cleanly with capability**" (a _leakage_ claim), with ES/RR answer-level "undoing" as the weaker downstream consequence at ≥32B only. As written, the title promises answer-level _undoing_ (ES/RR — fragile) while the bulletproof evidence is chain-level _leakage_ (CLR). That gap between title and robust evidence is the core structural weakness.

**U2 — The validated metric is not used where it matters.** [I]/§2 (line 73) shows strict RRs is trustworthy (κ=0.836, precision 0.92) and loose RR is not (precision 0.48 — "_half of loose-RR positives are false_"). Yet **Table 1's headline RR column is loose RR**, not RRs. They validated a better metric and then reported the worse one in the flagship table. They even say "_true reversion lies between RR_s and RR, exactly the bracket we report_" — but Table 1 reports only one end of the bracket. Adding a per-model RRs column is free (my Part-8 #1) and they don't.

**U3 — They under-sell the eval-validity contribution.** The judge-validated generative-vs-logit story ([I] + word-boundary 2×) is the single most bulletproof thing in the paper and needs zero new compute. It's relegated to contribution #4 / §2. (See (b).)

---

## (b) Missed framings from my Part 6

- **They elevated my down-ranked framing.** My Part 6 ranked the scaling/emergence framing (F4) _last_ (n=6, family-confounded, within-Qwen n.s.) and recommended leading with the fix (F3) or eval-validity (F2). The draft made "capability-emergent" the headline. My F1 (non-erasure mechanism), F2 (word-boundary/eval), and F3 (fix) all appear — but as _supporting_ contributions under the riskiest possible headline.
- **They entirely omitted the strongest reframe I proposed (Part 5): base-recall, not "amount of thinking," as the x-axis.** [K] (un-edited 7B recalls o_old at 0.59@B0 / 0.67@B3) is the natural motivation for "this is _knowledge conflict_ — the model's pre-edit belief reasserts; ROME counterfactuals are uniquely vulnerable because o_old is the truth the model already knows." The draft cites 0.59 **only defensively**, twice, to rebut "the small model never knew the fact" (lines 165, 280: "_not a knowledge bottleneck_"). It never engages the reframe, never frames reversion as prior-reassertion, and frames the mechanism as _reasoning dynamics_ ("routes around an intact edit") rather than _knowledge competition_. This is the highest-novelty framing available and it's not just missed — the one data point that motivates it is spent neutralizing a different objection.

---

## (c) My Part-8 experiments vs. the draft's stated limitations

|#|My experiment|Conceded in draft?|Honest or dodge|
|---|---|---|---|
|1|Strict-RRs in the headline table (free relabel)|**No** — RRs validated (§2) and used in the battery, but never added to Table 1; no limitation notes the omission|**Dodge by omission** — they own the better metric and don't propagate it to the flagship|
|2|Base-recall × reverted cross-tab (is it knowledge-conflict, not thinking?)|**No** — 0.59 cited only to defuse "didn't know the fact"|**Biggest dodge** — cites the exact number that motivates the alternative hypothesis, never tests or even names the hypothesis|
|3|Length/format control at 32B (filler-to-length vs real CoT)|**No** — the B0-vs-B3 = {content, length, format} confound is never named; the dose axis B1/B2 exists (line 97) but only B0/B3 are reported|**Dodge** — they have a 5-point budget axis and collapse it to two endpoints, hiding whether erosion is dose-monotone; the filler control is absent|
|3b|Native-CoT vs prompted-CoT (a _related_ control)|**Yes** — line 287, "_we have not tested … a non-native, prompt-induced CoT … the cleanest discriminating experiment_"|**Honest** — clearly named, not pre-judged. But it's a _different_ control from my length one and doesn't cover the length confound|
|4|Non-counterfactual / genuinely-novel edit set|**No** — scopes to CounterFact (line 283) but never concedes the effect may be specific to edits where o_old is pre-known|**Dodge by omission** (same blind spot as #2)|
|5|Suppressor replication off 32B/CF (70B, 14B, zsRE, MEMIT/AlphaEdit)|**Yes** — lines 228, 262, 284: "_one operating point on one model … one editor … one dataset_"; MEMIT/AlphaEdit flagged as priority; "_Replication on 14B … [pending]_"|**Honest** — explicit, repeated, not over-claimed|
|6|Logit-lens hardening (n, CI, non-reverted control)|**Partial** — line 298 scopes mechanism to logit-lens and "_do not claim this exhausts the mechanism_"; the deeper E-CHAINSUB mediation is conceded (line 253)|**Mixed** — honest that logit-lens is _partial_; **dodges** the specific weaknesses (no CI, n≈10–17, and especially no non-reverted control for the mid-layer dip)|

**Net read on (c):** the draft's concessions are genuinely honest exactly where it has _already done_ the harder version (the fix's narrow scope #5, the chain-causality mediation gap, the ΔCLR circularity, GSM8K −0.15, the clamp/degenerate caveats). The **dodges cluster on the two experiments that would threaten the _headline interpretation_** — base-recall (#2) and the length/dose control (#3). Both are cheap, both are un-run, and neither is named as a limitation. That asymmetry is itself a tell: the paper is scrupulous about caveats that bound _generality_ and silent about the two tests that could re-explain the _phenomenon_ (it's knowledge conflict, or it's context length, rather than "thinking"). If I were reviewing, those two omissions — plus the title/CLR mismatch (U1) — are where I'd push hardest.

One numeric flag to reconcile: §4 (line 159) reports the within-Qwen CLR slope as "0.22, CI [0.12,0.40]," but my OLS on the four Qwen points gives **0.261** (the 0.218/0.22 figure is the _all-six_ pooled slope). Worth checking whether line 159 accidentally quoted the pooled slope for the within-Qwen claim.


以上为claude。