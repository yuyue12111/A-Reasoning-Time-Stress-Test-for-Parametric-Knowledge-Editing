# AAAI-style Simulated Review Report 1 

## 0. Paper Summary

The paper argues that standard parametric-editing evaluation, which queries the edited model for a direct answer, does not certify that the edit survives the model's own reasoning. It applies one ROME edit at a time to CounterFact requests and scores each edit twice under a generative (not teacher-forced) criterion — at a pre-closed empty think span (`B_0`) and after a native chain (`B_3`) — across six fixed R1-distill checkpoints in two lineages. At the largest checkpoint of each lineage the paired edit-success drop is .106 (Qwen-32B) and .107 (Llama-70B); among Qwen-32B zero-thinking successes, old answers resurface in 19.3% of reasoned answers and displace the new answer in 9.2%. It then adds a think-span-only logit penalty on the old value's first tokens, in a five-arm battery (none / old / new / placebo / same-relation competitor), which raises paired edit success by +.122 over the placebo and lowers permissive reversion from .193 to .085, with near-null placebo and competitor arms and a sign-reversing new-answer arm. The paper explicitly withdraws its planned mediation claim: the mechanism is stated as unidentified (§4.2, §6).

## 1. Title / Abstract / Main Paper Consistency Check

### Title Promise

"Direct-Answer Edit Success Is Not Enough" promises a demonstrated inadequacy of the standard protocol. "A Reasoning-Time **Stress Test**" promises a graded protocol that varies reasoning load. The subtitle scopes to "Parametric Knowledge Editing" generally.

### Abstract Claims

1. Each ROME edit evaluated twice, six checkpoints, two R1-distill families.
2. Edit success drops .106 / .107 at the largest tested checkpoint in each family.
3. Qwen-32B: 19.3% permissive resurfacing, 9.2% strict displacement, "while the unedited base shows no detectable old-answer drift."
4. "The edited association remains detectable at a cloze probe."
5. "Route analysis finds visible in-chain paths to old answers, motivating a chain-routing hypothesis."
6. A "signed, dose-graded intervention offsets the edit-success loss and lowers the resurfacing rate from 19.3% to 8.5%; placebo and same-relation controls have near-null answer-level effects."

### Main Paper Support

Claims 2, 3 (first two numbers), and 6 are numerically supported and internally consistent — Table 1 (Qwen-32B .595/.495, drop .106 [.030,.182]; Llama-70B .610/.503, .107 [.032,.182]) and Table 2 (N: ES .495, RR .193, RR* .092; T: .631, .085, .042; T−P ΔES .122 [.051,.193], ΔRR −.095 [−.171,−.029]; P−N and C−N ≈ .015 / .000; D−N ΔES −.217, ΔRR +.086). I checked the arithmetic tie-points and they hold, including the disclosed non-additivity in fn11 (.495 + .138 ≠ .631). That internal discipline is genuinely above average.

### Mismatches

These are the four I would raise as a reviewer, and three of them are real:

- **M1 — "dose-graded" (claim 6) is not supported at the outcome level.** §5.1 states that across penalty strengths 0/2/4/8/12/16 the in-span leakage check declines monotonically (to .082) but "edit success and permissive reversion are **not ordered** across those settings," and fn10 says the five suppressed points come from a smaller separate run, none carries an interval, "so we read them as a dose ladder rather than a calibrated dose-response." The abstract's "dose-graded intervention" will be read by every reviewer as dose-response **on the outcome**. As written the word is earned only by the manipulation check. This is the single clearest overclaim in the abstract.
- **M2 — "no detectable old-answer drift" (claim 3) rests on one cell and a contrast the paper refuses to make.** §3.2 gives the base paired drift as −.0201 [−.0804,.0402] at n=199, then says "that paired interval exists at this checkpoint only; the other five carry level differences without intervals, and those are not of one sign," and "the two quantities differ in event definition and denominator; we make no formal contrast." Figure 1B plots the base under a rule as ΔP(o_old) and its own caption says it is "juxtaposed rather than contrasted." The abstract and §7 nevertheless present the base as a comparator. Either drop it from the abstract or say "at the largest Qwen checkpoint, no detectable drift, not formally contrasted."
- **M3 — the cloze probe (claim 4) is disclaimed by its own footnote.** fn5: "only an installation sanity check: no control, no interval, close to tautological because ROME optimizes the target logit at the rewrite prompt, and conditional on the selected reversion sample… we place no quantitative weight on this observation downstream." An abstract sentence should not carry weight the paper explicitly removes. As it stands a reviewer will call this a self-refuting sentence in the abstract.
- **M4 — the abstract does not disclose that 4 of 6 cells are null and 2 of those are signed the other way.** Table 1 is honest (1.5B −.026, 7B −.030, 14B +.040, Llama-8B +.015), and §3.2 explicitly declines a trend, but the abstract's "across six fixed checkpoints… At the largest tested checkpoint in each family, edit success drops by…" reads as six-checkpoint evidence for a two-checkpoint result. This is the presentation choice most likely to be labelled selective reporting, and it is cheap to fix in one clause.
- **Title-level:** "stress test" implies a load ladder; the main battery is a two-point contrast (`B_0` vs native `B_3`). `B_1` appears only in a separate control run (§3.3), and **`B_2` is never defined or reported anywhere in the paper** although the naming presupposes it. No monotone budget-response curve is presented. The title promises more protocol than §3 delivers.

---

## 2. Reviewer 1 — Technical Soundness

### Summary

The measurement protocol is well-conceived: one-edit-at-a-time with weight restore, a generative rather than teacher-forced criterion, within-case pairing on the same edit, and a clean separation of instruments (ES / RR permissive / RR* strict / CLR as manipulation check, with §3.1's explicit refusal to treat them as bounds on a latent semantic rate). The five-arm intervention in §5 is the strongest technical object in the paper. What is not sound is the _comparability of the edits across the six checkpoints_, and the paper's causal vocabulary outruns what it identifies.

### Strengths

- One-edit-at-a-time with restore, so no cross-request contamination; byte-identity audits (§3.1: 400 `B_0` tuples, 0 differences for treated-vs-none and for competitor-vs-none) establish treatment-independence of the conditioning gate by construction rather than by assertion. This is better hygiene than most editing papers show.
- Instrument separation is disciplined: CLR is declared a manipulation check, not an outcome (§5.1, §4.4); locality is explicitly narrowed to target-value non-leakage rather than sold as preservation (§3.1, §6).
- The intervention's control set is genuinely well-chosen: frequency- and length-matched placebo, same-relation strong competitor, and a reverse-direction (new-answer) arm whose sign flips both endpoints (Table 2, D−N: ΔES −.217, ΔRR +.086). Sign evidence plus two near-null controls is the right design.
- The scope ablation in §5.1 (answer-stage penalty raises zero-thinking success .580 → .727 over 100 cases; think-scoped leaves it untouched) does real work: it shows the penalty _can_ move the answer and that the reported version does not.

### Weaknesses

#### Fatal Issues

None that are unfixable in principle. I found no fatal internal contradiction, no invalid statistic, and no claim that the tables contradict. The severity is concentrated in confounds and in identification.

#### Major Issues

- **MJ1 — Edit configuration is not held constant, and the two headline cells are the two _untuned_ ones.** §3.1: the edit layer was scanned at Qwen-7B and Llama-8B only; the other four were "placed… unscanned at the same relative depth, .18 of the stack," and the update clamp lowered by the Llama-8B scan (4 → 2) was transferred to the other five. The two cells whose intervals exclude zero (Qwen-32B, Llama-70B) are both **unscanned**, and both **scanned** checkpoints show null-or-reversed drops (−.030, +.015). Whatever the truth, an obvious rival explanation is on the table: a worse-placed, weaker-clamped edit at the larger checkpoints is more fragile under any longer generation, and fragility-of-edit is confounded with reasoning. Nothing in the paper normalizes edit strength across checkpoints, and `ES_{B_0}` ranges .500–.625 without a matched-strength analysis. This, not the pool, is the objection I would lead with.
- **MJ2 — Locality is unrecorded at two of six checkpoints and below the pre-set acceptance line at a third, and both retained.** §3.1 reports non-leakage .958 (Qwen-32B), .954 (1.5B), .930 (Llama-70B), .835 (Llama-8B) — the last "below the .85 that scan used as its acceptance line, kept rather than retuned" — and "we did not record this level for the two middle Qwen checkpoints." So one third of the reported cells have no recorded locality at all, and one cell fails the authors' own gate. A reader cannot tell whether Qwen-7B/14B edits were even admissible.
- **MJ3 — "Causal control point" is asserted at a stronger grade than the identification supports.** The intervention is genuinely interventional and controlled, so "causal" for the _intervention_ is defensible. But "control **point**" implies a located locus, and §4 is titled "Visible Routes and an **Unidentified** Mechanism": the replay vehicle is a permanent FAIL (9/18 vs required 15), the mediation claim is withdrawn, §4.4's CLR stratification is admitted to be within-sample enrichment with a mechanically forced floor (CLR-zero stratum N-arm RR = 0, so nothing could decrease), and the concept-direction confirmatory arm failed with a **negative pre-registered co-primary harm endpoint on LocAcc**. What is established is: a think-span-only manipulation changes an answer-stage outcome. That is "an intervention point," not "a causal control point in the mechanism."
- **MJ4 — The forced think-span closure is unquantified.** §3.1: "Each budget caps the think span — 8192 tokens at `B_3` — and where the model has not closed it, the harness does." The rate of harness-forced closure is never reported. A truncated chain is a different object from a completed chain, and truncation rate plausibly rises with checkpoint size — the exact axis the headline lives on. Llama-70B's early-stop filtering (n=187 headline vs n=200 sensitivity) shows the authors know this class of artifact exists.
- **MJ5 — The guard requires the old value at decode time, which the paper acknowledges only in the Ethical Statement.** §5.1's processor penalizes "the first tokens of the old value's aliases," and the Ethical Statement says it "is edited-query gated, firing only on the subject and relation whose edit is defended." So the method is oracle-informed twice over (which query is edited, and what the suppressed answer is). §5.5's honesty about this ("active application to a paraphrase query, not portability to unguarded queries") is welcome, but the technical consequence should be stated in §5.1, not left to Ethics: this cannot be a defence, only a probe. The paper says as much once; it should say it where the method is defined.
- **MJ6 — Mixed numerical precision across hardware, with a 40-case cross-check.** §6: bfloat16 made the rank-one update diverge to NaN on the Hopper-class part, so that part ran float32 and the other bfloat16. Which checkpoints/cells ran in which precision is _Not sufficiently specified in the provided material_. A 40-case agreement check is thin cover for a headline effect of .106 with a lower interval bound of .030.

#### Minor Issues

- `B_2` is referenced by implication (the ladder `B_0 … B_3`) but never defined or reported.
- The penalty is never given a formal definition or pseudocode — magnitude 8 on "first tokens of the old value's aliases" is stated, but the alias set construction at inference, the tokenizer-boundary handling, and whether the penalty is additive on logits or on logprobs are not pinned down in the main text. For a paper whose contribution is a decoding-time processor, an algorithm box is expected.
- §5.1's pre-registration is partial by the authors' own account: "the treated and untreated arms already existed, so it fixed the comparator and the sign order ahead of the data, not the treated arm," and arm C "was added afterwards." Honest, but it means the primary contrast is prospective only in its comparator.
- The route taxonomy (Bridge / Recall / Reflective-override / Associative) is used as if grounded, but no circuits/mechanistic-recall literature is cited to license the category names (§4.1).
- §6 reports 90% intervals for the capability gate while the rest of the paper uses 95%; the level switch is unexplained.

### Questions for Authors

1. For Qwen-32B and Llama-70B, what is the edit's post-edit efficacy under a matched criterion, and does the `B_0 → B_3` drop survive conditioning on matched `ES_{B_0}` or on a per-checkpoint layer scan? Concretely: does the drop persist at Qwen-7B/Llama-8B if you place their edits at .18 unscanned, i.e. can you reproduce the scan-status confound as a manipulation?
2. What are the locality levels at Qwen-7B and Qwen-14B, and why was Llama-8B retained at .835 below your own .85 acceptance line?
3. What fraction of `B_3` generations required harness-forced closure at 8192, per checkpoint, and does the drop persist among naturally-closed chains only?
4. Which cells ran in float32 and which in bfloat16, and what is the paired drop on the 40-case cross-check subset in each precision?
5. Since the guard is edited-query gated (Ethical Statement), was the GSM8K/MATH capability check run with the gate **active** (in which case the penalty never fires and near-zero cost is true by construction) or with the penalty applied unconditionally?

### Required Fixes

- Report per-checkpoint edit configuration and efficacy in the main paper, and either scan all six or add an edit-strength-matched analysis for the two headline cells.
- Fill in locality for all six checkpoints; justify or drop Llama-8B.
- Report forced-closure rates and a naturally-closed-only sensitivity.
- Downgrade "causal control point" to an intervention/steerability claim, or supply an identification argument that survives §4.2's FAIL.
- Move the oracle-gating limitation from Ethics into §5.1.

### Rating

Rating: 5 / 10  
Confidence: 4 / 5

### Score Justification

The protocol design and the intervention battery are above the bar; the cross-checkpoint comparability of the edits and the identification of the mechanism are not. A 5 reflects a paper whose _measurement_ I trust more than its _attribution_.

### Why Not Higher?

Because the headline effect is confounded with untuned edit placement at exactly the two cells that carry it, locality is missing for a third of the cells, and the mechanism section ends in a withdrawn claim plus a failed pre-registered confirmatory arm with a negative harm endpoint.

### Why Not Lower?

Because nothing is hidden, the numbers are internally consistent, the intervention has real placebo/competitor/direction controls with near-null controls and a sign flip, and the byte-identity audits show the conditioning gate is treatment-independent by construction rather than by hope.

---

## 3. Reviewer 2 — Experiments & Reproducibility

### Summary

This is where the paper is weakest, and the authors have done my work for me: most of the fatal-adjacent problems are disclosed in the text. Disclosure, however, is not repair. The headline gap rests on 2 of 6 uncorrected cells, measured on a request pool whose selection rule the authors say "would if anything favour the drop we report," using a permissive instrument with precision .48, with one greedy generation per cell, one editor, one dataset, and a large fraction of the evidence outside the main paper.

### Strengths

- Within-case pairing on the same edit is the right unit, and paired case-bootstrap intervals are reported for every cell in Table 1, including the four nulls. Nothing is suppressed.
- A sampling robustness check exists: three fixed seeds, complete-case drop .117 [.067,.169] over 199/200 cases and 597/600 seed pairs (fn4), with the correct caveat that fixed seeds do not identify a seed population.
- The `B_0P` canned-thought arm is a genuinely informative control: it separates "empty think wrapper" from "think span containing content," and it moves ES the _opposite_ way from `B_1` (§3.3). That kills the simplest artifact story (that the pre-closed span itself is the cause).
- Reproducibility blemishes are volunteered rather than buried: the placebo arm not byte-reproducible from released shards, one extra row, "every T-versus-P quantity we report moves in the third decimal and no conclusion changes" (§5.3); arm-wise n differences called harness errors (§5.1); the pool predating a matcher fix (§3.1).

### Weaknesses

#### Fatal Issues

- **F1 — The request pool is selected by a criterion that coincides with one arm of the headline contrast, and the bias is unbounded by the authors' own statement.** §3.1: 600 CounterFact requests, read against **the unedited Qwen-7B checkpoint at `B_3`**, keeping 248 whose answer matched an old-value alias, then 200 reused at **all six checkpoints and both lineages**. The paper says it plainly: "what that one checkpoint knew fixes the pool everywhere"; "its condition coincides with one arm of the headline pair rather than sitting outside both, and a pool chosen for old-value retrieval under thinking would if anything favour the drop we report. **No `B_0`-gated pool was ever built, so nothing here sizes it.**" That is an admitted, directional, unsized selection effect on the paper's central number. I do not think a reviewer can be asked to accept a headline effect of .106 [.030,.182] whose sampling frame was chosen by old-value retrievability _under the very condition being compared_, with no bound on the inflation. Additionally the pool was built with a matcher later found to fire on short country and language codes and "never rebuilt, so requests entered it under a rule later found to fire on short country and language codes. Every rate we report uses the fixed matcher; membership of the pool does not." Two composed selection defects on the same pool.
- **F2 — The headline reversion number is produced by an instrument with precision .48.** fn2: the permissive rule has "precision/recall = .48/.96" against the three-judge majority, while the strict rule reaches .92. The abstract leads with the permissive 19.3% → 8.5%. Under a .48-precision instrument roughly half of flagged reversions may not be old-answer commitments. Worse, the higher-precision endpoint is exactly the one that **fails** against the untreated baseline: §5.4 reports strict displacement separating T from placebo (−.057, p = .029) and from competitor (−.057, p = .032) but from the untreated baseline only −.051 [−.102, **.000**] with p = .073. So the trustworthy instrument does not clear the most natural comparison, and the abstract reports the untrustworthy one. The judge panel is also incomplete (votes for 87 of 121 stratified items; 33 lost to rate limits; "missingness is concentrated among rule-negative rows" — i.e. concentrated exactly where precision is estimated) and uses a single external judge-model family for both panels with no human-audited subsample (§6), so "shared bias would not surface."

#### Major Issues

- **MJ7 — 2 significant cells out of 6, unadjusted, with two cells signed the other way, and the significance-carrying cells are also the largest.** §3.2 calls this "a scope statement, not a post-hoc selection," but the paper never states that the largest-checkpoint cells were designated as primary **before** the data. Contrast this with §5, where a primary contrast genuinely was fixed in advance — the authors know how to pre-specify, and they did not do it for the headline. Combined with `RR_{B_3}` rising non-monotonically across Table 1 (.061, .080, .162, .193, .144, .175) and the explicit refusal to infer a trend, what survives is: two cells.
- **MJ8 — No multiplicity control anywhere.** "All p values here are unadjusted and we claim no correction" (§5.4). Counting Table 1 (6 cells), Table 2 (6 contrasts × 3 endpoints), §5.5 transfers (3 settings × 2–3 endpoints), §4.4 strata, and §3.3 controls, the family is large. The strict endpoint at p = .073 and the MEMIT strict at p = .400 are then read as "thinnest where the effect is smallest," which is fair, but the ES results are not immunized by that framing.
- **MJ9 — One greedy generation per cell for the headline.** §3.1: "one generation per cell." The seed check (fn4) is on Qwen-32B only. For five of six checkpoints the reported cell is a single sample.
- **MJ10 — No non-reasoning control, which is the experiment the framing needs.** §3.2 concedes it: "separating reasoning post-training from backbone capability needs a matched parent–distill control, which remains future work." Both lineages "share one R1 teacher and distillation recipe" (§6), so the two-lineage agreement bounds backbone idiosyncrasy but not recipe specificity. As it stands, the paper demonstrates a **decoding-condition** effect within R1-distills, not that _reasoning_ undoes editing.
- **MJ11 — The length/compute-buffer alternative is live by the paper's own admission.** §4.3: `B_0P` "is not a length-matched filler"; the suppression comparison ".631 against… .595" is not length-matched because suppression may alter realized chain length; "an equal-length content-free filler remains untested… Accordingly, the content-independent computational-buffer account of Gekhman et al. (2026) remains a live alternative." A reviewer is entitled to ask why a single equal-length filler run — the cheapest experiment in this whole program — was not done.
- **MJ12 — Headline generality is one editor, one dataset, one recipe.** §6: "MEMIT enters only through the transfer replication; a second benchmark, edit family, and non-counterfactual edits are untested." And §5.5 is candid that the MEMIT-14B replication's own no-suppression arm gave a paired ES drop of +.060 [−.020,.140], "which does not itself establish a reasoning-time drop in that cell, so this transfers the intervention and not the gap." So the _gap_ is ROME-only, CounterFact-only.
- **MJ13 — No external baseline for the intervention.** §2 correctly distinguishes the three cited answer-stage decoding approaches from a think-span-scoped penalty, and §5.1's scope ablation is a good internal control. But there is no head-to-head against any existing mitigation, so a reader cannot tell whether think-span scoping buys anything a simpler answer-stage or re-editing baseline would not.
- **MJ14 — Small-n substructure carrying interpretive weight.** Cloze n=23; replay n=18 (with 14/18, 12/18, 13/18, 1/5 sub-counts); route census 41 instances from **33 unique facts** with no cluster adjustment mentioned; paraphrase audit 40 paraphrases with 30 valid, 11/20 cases valid on both, and κ = .444 — which is poor agreement for a claim reported as +.055 [.020,.093], with "no row was filtered and no valid-subset analysis was run."
- **MJ15 — The capability-cost claim is point-equivalence only.** §6 is explicit: .000 on 1319 GSM8K and −.010 on 500 MATH inside a 0.02 gate at the point estimate, "while the accompanying 90% intervals, [−.022,.022] and [−.061,.041], are wider than that gate. We report point-equivalence at the tested sets, not equivalence." The MATH interval is 3× the gate. Honest, but it means no equivalence is established.

#### Minor Issues

- §5.4's strict endpoint "rests on the 118 paired cases clearing the zero-thinking gate in both arms, for which we publish no per-arm event totals."
- §3.3's `B_1` permissive RR of .208 at 256 tokens sits _above_ Table 1's `B_3` RR of .193 at native budget. fn8 correctly forbids inference across runs, but the juxtaposition invites the reading that the effect saturates by 256 tokens — which would support MJ11's buffer account. A within-run ladder would settle it.
- §3.3 says the case-block fits are "not a second independent trend line; both are in the supplement" — so the only robustness evidence for the size association is unavailable to a main-paper reviewer.
- Table 1's Qwen-32B row is the one place marginal levels and paired drop disagree (.595 − .495 = .100 vs .106), disclosed via n=198 vs 200; correct, but it makes the table read as inconsistent on first pass.

### Missing Experiments

1. **A `B_0`-gated (or dual-gated) pool rebuild** with the fixed matcher, reporting the drop on both frames. This sizes F1. Highest priority in the paper.
2. **A matched parent–distill control** (same backbone, non-reasoning parent vs R1-distill child) — the experiment that licenses the word "reasoning."
3. **A within-run budget ladder** (`B_0`, `B_1`, `B_2`, `B_3`) under one gate, on one checkpoint, with intervals — this is what the title already promises.
4. **An equal-length, content-free filler at native chain length** — decides the computational-buffer account.
5. **Human-audited subsample** for the permissive/strict instruments, or promotion of the strict endpoint to primary.
6. **A second editor and a second dataset in the main battery**, not via transfer; and at minimum one non-counterfactual (real-update) edit set.
7. **One external mitigation baseline** at the answer stage, so the think-span scoping claim has a comparator.
8. **Naturally-closed-chain-only sensitivity** and per-checkpoint precision disclosure.

### Reproducibility Concerns

- No code/data pointer appears anywhere in the paper, yet the text repeatedly cites "the released lock file," "the released shards," "the released provenance record." A reviewer cannot reach any of them from `main.pdf`. Whether an anonymized artifact link exists is _Not sufficiently specified in the provided material_.
- Placebo arm not byte-reproducible from the released shards (§5.3).
- Pool membership not reproducible under the current matcher (§3.1).
- `results/probe/logitlens_cf200_ROME_B3.jsonl` exists but "was never crosswalked to the membership sample, so nothing lets a repeat audit sample overlap and membership composition or reproduce the case-level tally" (fn5).
- Mixed float32/bfloat16 across hardware parts, with no per-cell mapping.
- Hardware described only as "Hopper-class parts of 141 and 80 GB HBM and an Ada-class part of 24 GB" — anonymity-motivated, but it prevents a reader from telling which runs are which.

### Questions for Authors

1. What is the paired `B_0 → B_3` drop on a `B_0`-gated pool, or on the intersection of `B_0`- and `B_3`-gated pools? If you cannot rebuild, can you at least report the drop restricted to cases the _edited_ model answered with the old value at `B_0`, as a partial bound?
2. Was "largest checkpoint in each family" designated primary before the six cells were computed? If yes, where is it recorded; if no, will you report a corrected family-wise statement?
3. Will you promote the strict endpoint (precision .92) to primary and report the permissive rate as secondary, given fn2?
4. Of the 121 stratified validation items, how does precision change if the 33 rate-limited rows are imputed adversarially, given that missingness concentrates among rule-negative rows?
5. What is the equal-length content-free filler result at native chain length?

### Required Fixes

Items 1, 4, and 5 of _Missing Experiments_, plus promotion of the strict endpoint, plus an artifact pointer, plus a family-wise statement for Table 1.

### Rating

Rating: 4 / 10  
Confidence: 4 / 5

### Score Justification

An admitted, directional, unsized selection effect on the headline contrast, plus a headline instrument at precision .48 whose high-precision counterpart fails against the untreated baseline, plus 2-of-6 uncorrected cells, plus a live alternative explanation the authors name themselves. Individually survivable; jointly this is below the acceptance threshold.

### Why Not Higher?

Because the central empirical claim's sampling frame was selected under one arm of its own contrast and the paper states no bound on the resulting inflation.

### Why Not Lower?

Because the experimental _design_ of §5 is good, the reporting is unusually complete and honest (all six cells, all five arms, all null contrasts, disclosed reproducibility defects), and nothing I found contradicts anything else in the paper. This is a 4 for insufficiency, not a 3 for unsoundness or a 2 for misrepresentation.

---

## 4. Reviewer 3 — Novelty, Significance & Related Work

### Summary

The framing — that edit evaluation must be conditioned on the model's own reasoning-time decoding, and that direct-answer protocols certify something narrower than they appear to — is a good, timely, well-posed question for this community. The trouble is that the paper's own §2 tells me most of the observation is already in the literature, and what remains distinctive is a controlled paired contrast plus an intervention that the paper itself demotes to a probe.

### Strengths

- The problem is real and under-measured, and the community that builds editing benchmarks would benefit from this critique.
- The `B_0`/`B_0P`/`B_1` control structure (empty wrapper vs canned content vs short chain) is a genuinely more careful decomposition than "we evaluated under CoT."
- The think-span-scoped vs answer-scoped distinction (§2, §5.1) is a conceptually sharp move: it turns a decoding tweak into a localization question. That is the paper's best idea.
- Two lineages with symmetric largest-checkpoint results is more than most single-model editing papers offer.

### Weaknesses

#### Fatal Issues

None.

#### Major Issues

- **MJ16 — The novelty delta is narrower than the framing implies, by the paper's own §2.** §2 states that He et al. (2025) "benchmark editing under realistic autoregressive inference rather than teacher-forced decoding, across instruction-tuned and reasoning-oriented models, and find parameter-based editing performs poorly, including on an R1-distilled checkpoint whose reasoning reflects outdated knowledge and overturns the edit," and that Huang et al. (2026) "make the closest observation to ours, in the multimodal setting: near-perfect teacher-forced accuracy alongside collapsing grounded success once the chain is examined, and attributing it partly to chains that reject the injected fact." The paper's §2 "What this paper adds" is honest about the residue: budget-controlled paired contrast on one and the same edit; controls separating edit-specific erosion from base drift; symmetric results at two lineages; and the signed think-span intervention. That is a real contribution — a _measurement-discipline_ contribution — but it is a refinement of an observation that is already published, not a new phenomenon.
- **MJ17 — Significance is capped by the intervention's oracle gating.** The guard needs to know both that a query targets the edited subject/relation and what the old value's aliases are (§5.1, Ethical Statement). Under those conditions there are far cheaper remedies, and the paper agrees it is "a mechanistic probe and an edit-aware decoding guard, not a deployment-ready fix" (§5.5). So the contribution's value must be carried entirely by the diagnosis — and the diagnosis is the part §4 declares unidentified.
- **MJ18 — The mechanistic yield is close to zero net.** §4 delivers: a probe its own footnote calls "close to tautological"; an outcome-conditioned descriptive census (41 instances / 33 facts) that the text says "describes observed failures rather than a predictor or causal mediator"; a permanently FAILed replay vehicle with a withdrawn mediation claim; a CLR stratification admitted to be within-sample enrichment against a mechanical floor; and a failed pre-registered concept-direction experiment with a negative LocAcc harm endpoint. I respect the reporting enormously. But as a contribution assessment, §4 is 1.5 pages that end where they began, and a reviewer scoring significance has to price that.
- **MJ19 — Related work is thin for the claims being made.** Roughly 21 references, four short paragraphs. The bibliography is well-targeted at the immediate neighbourhood (editing evaluation, editing-specific decoding, one inverse-scaling result, one factual-priming mechanism) and every cite is used for a specific purpose, which is good practice. But for a paper about whether a model's _stated chain_ controls its _final answer_, several literature families are absent as directions (no specific papers named, since no search was performed): (i) chain-of-thought faithfulness — whether verbalized reasoning reflects the computation that produces the answer, which is the exact assumption §4.1's route census rests on; (ii) parametric-versus-contextual knowledge conflict, which is structurally the same competition the paper studies with the "context" internally generated; (iii) mechanistic factual-recall circuit work beyond ROME/MEMIT, needed to license the Bridge/Recall category names; (iv) constrained/guided decoding and logit-bias literature outside editing, which is the methodological home of the §5 processor; (v) unlearning and concept erasure, the mirror problem of suppressing an old value, and a source of directly relevant negative results about surface-level suppression; (vi) test-time-compute scaling and its reliability side effects, currently a single cite; (vii) statistical-multiplicity practice for ML evaluation, given §5.4's stance.

#### Minor Issues

- Two distinct He et al. 2025 entries are cited as "He, Song, and Sun (2025)" and "He et al. (2025)"; formally disambiguated, practically confusing in a paper this dense.
- The taxonomy (Bridge / Recall / Reflective-override / Associative) is introduced, populated (27/11/3/0), and then explicitly stripped of predictive or mediating status — so it reads as terminology without a downstream role.

### Novelty Assessment

**Moderate-low.** Not incremental in framing; incremental in phenomenon. The phenomenon "edits fail under real reasoning-time decoding" is attributed in §2 to prior work including on an R1-distill checkpoint. The novel objects are the paired budget-controlled contrast on one and the same edit, the base-drift and canned-thought controls, and the think-span-scoped signed intervention with placebo/competitor/direction arms. The intervention is the most novel single item and it is well-controlled.

### Related Work Gaps

See MJ19 — seven directions, described as families rather than named papers because no literature search was performed for this review.

### Significance Assessment

**Moderate for the benchmarking/evaluation subcommunity; low for practitioners.** If the measurement claim holds up after F1 and MJ10 are addressed, it should change how editing papers report results, which is a genuine service. Right now the actionable takeaway for a reader is "your protocol may be optimistic at large R1-distill checkpoints, by an amount we cannot separate from pool selection, edit tuning, or chain length." That is not yet enough to change practice.

### Questions for Authors

1. Precisely which claim in Huang et al. (2026) and He et al. (2025) does your paper contradict or strictly strengthen, stated as a one-sentence delta? Right now §2's "What this paper adds" lists methodological differences, not a disagreement.
2. Does the think-span-only result tell us anything a reader could not get from an answer-stage guard plus a chain-visibility statistic? If yes, that argument belongs in §1.
3. Would you be willing to reframe the paper as a measurement/benchmarking contribution (protocol + instrument validation + reporting standard) rather than a mechanism paper, given §4's own conclusion?

### Required Fixes

- State the delta against the two closest works as an explicit contrast, not a list of methodological differences.
- Add the missing related-work directions, especially CoT faithfulness and knowledge conflict, since §4.1's method presupposes the former.
- Either reframe §4 as a documented dead end in service of §5 (shorter, honest, well-signposted) or cut it to make room for the §5 evidence currently in the supplement.

### Rating

Rating: 5 / 10  
Confidence: 3 / 5

### Score Justification

A well-posed, timely question with an honest and partly novel measurement apparatus, whose phenomenon is substantially anticipated by cited work, whose mechanism section is a declared null, and whose method is declared non-deployable by its own authors.

### Why Not Higher?

Because §2 concedes the closest prior work already observed the collapse on an R1-distilled checkpoint, and the paper's remaining delta is methodological refinement plus a probe.

### Why Not Lower?

Because the framing is genuinely useful, the think-span/answer-stage distinction is a real conceptual contribution, and the five-arm battery with a sign-reversing arm is the kind of control discipline this subfield needs more of.

---

## 5. Reviewer 4 — Writing, Structure & Compliance

### Summary

Structurally the paper is in the right shape and the compliance items are present (limitations, ethics, anonymity). The dominant problem is register: the prose is written as an audit log, with load-bearing caveats pushed into thirteen footnotes, and it is at points genuinely hard to parse. Combined with four abstract-level mismatches and one figure carrying every visual, the paper actively hides its own best result.

### Strengths

- Seven-section structure is conventional and correct; §6 Limitations is unusually substantive; Ethical Statement is thoughtful and specific rather than boilerplate, and engages the actual dual-use structure of a suppression tool ("three properties bound this research diagnostic… It is edited-query gated… It steers at inference time, updating no weights and applying no optimization toward concealment").
- Anonymity is handled: "Anonymous submission," an anonymization footnote on page 1, no acknowledgements, no self-identifying citation phrasing that I could detect.
- Numbers in the running text match the tables, throughout. That is rarer than it should be.
- Table captions are informative and warn readers about the exact traps (Table 1: "ES levels are marginal; drops and intervals are within-case complete-pair estimates and need not equal marginal differences when rows are missing"; Table 2: "the two panels rest on different denominators; a paired reversion contrast uses the intersection of the two arms' gate sets").

### Weaknesses

#### Fatal Issues

None.

#### Major Issues

- **MJ20 — Four abstract/body mismatches, three material.** See §1 above: "dose-graded" (contradicted by §5.1 and fn10), "no detectable old-answer drift" (one cell, contrast disclaimed), the cloze probe (disclaimed by fn5), and silence on 4-of-6 null cells. In a Phase-1 process where reviewers read the abstract first and may weight it heavily, these are the most damaging sentences in the paper, and all four are fixable with one editing pass and zero new experiments.
- **MJ21 — Thirteen footnotes carrying primary content.** fn2 (the entire validation of both judge instruments, including the .48 precision that determines how the headline is read), fn4 (the whole sampling robustness result), fn5 (the disclaimer that voids an abstract claim), fn9 (the actual numbers behind §4.4), fn10 (the disclaimer that voids "dose-graded"), fn11–13 (non-additivity, bootstrap p's, changed-row audit). A reviewer skimming the body will miss every caveat that matters, then feel misled on discovering them. Anything that changes the reading of a headline number belongs in the body.
- **MJ22 — Register.** Representative: "So what that one checkpoint knew fixes the pool everywhere, and every level we report is a rate over this pool rather than over CounterFact." / "That bounds specificity rather than supplying evidence." / "so it carries nothing here." / "Each contrast is compatible with zero; we set no equivalence margin, so these are failures to separate rather than demonstrations of no effect." The last is _exactly right_ statistically and will still lose readers. The paper repeatedly uses "not X but Y" negation chains, nominalizations ("the answer-commitment validation panel," "the vehicle-validity gate," "the strict displacement endpoint"), and internal jargon (`B_0P`, F2-sourced, cellwise, "the harness does") without a glossary. Twelve or more coinages are introduced and used once. There is no obvious LLM-boilerplate signature — no filler transitions, no summary padding — but the uniform hedging cadence and the sheer density of qualifiers may read to some reviewers as heavily machine-polished, and the practical effect is the same: the contribution is buried.
- **MJ23 — One figure for the entire paper, and it is the wrong one to keep alone.** Figure 1 shows the six-cell paired drops (A) and three Qwen-32B conditions (B), while §5.5 says "the evidence ladder and five-arm forest are supplementary figures." The five-arm forest is the paper's best result and it is not in the paper. In the rendered PDF, Figure 1A's panel title and the two backbone legend labels visibly collide near the top-left ("Qwen backbone" / "Llama backbone" overlapping the panel heading), and panel B's "Edited model · generative ES drop" band label crowds the panel title. Whatever the source, this is not camera-ready.
- **MJ24 — No artifact pointer despite repeated appeals to released artifacts.** "the released lock file," "the released shards," "the released provenance record," and a bare internal path `results/probe/logitlens_cf200_ROME_B3.jsonl` (fn5). A reader has no way to reach any of it. Whether an anonymized repository link is planned is _Not sufficiently specified in the provided material_. Citing an internal filesystem path in a blind submission is also a small anonymity/professionalism smell.
- **MJ25 — Supplement dependence.** At least ten deferrals, several of which are the _only_ support for a body claim: the complete replay-gate table (§4.2), the complete endpoint set for the concept-direction test (§4.4), the case-block fits (§3.3), the missingness pattern (fn2), per-arm event totals (§5.4). If the supplement is late or thin, several body sentences become unverifiable assertions.

#### Minor Issues

- `B_2` never defined (also R1's point) — a reader tracking the budget ladder stops here.
- 90% intervals in §6 vs 95% everywhere else, unexplained.
- Section 4's title ("Visible Routes and an Unidentified Mechanism") advertises a null in the table of contents. Honest; also the first thing a skimming reviewer sees about the mechanism.
- §5.3's "The released provenance record gives both derivations" reads as an internal note to a co-author.
- "cellwise, unadjusted 95% paired case-bootstrap intervals" — the paper's own terminology is not defined until after first use in several places.

### Structure Problems

The page budget is misallocated. Approximately: §3 measurement 1.6 pages, §4 (net-null mechanism) 1.5 pages, §5 (the strongest contribution) 2 pages with its key figure absent, §2 0.8 pages, §6–§7 0.8 pages. Cutting §4 to half a page — "we tried three routes to a mechanism; the vehicle failed its pre-registered gate; here is what that rules out" — would free space for the five-arm forest, per-checkpoint edit configuration, and the caveats currently in fn2/fn5/fn10.

### Writing Problems

Sentence length and clause stacking; single-use coinages; caveats in footnotes; negation-chain constructions; absent glossary for the budget/arm notation. The paper needs one pass whose only goal is that a competent non-specialist can state the contribution after reading §1 and Table 2.

### Figure / Table / Algorithm Quality

Tables: strong content, honest captions, correct disclosure of denominator differences. Figure 1: label collisions in both panels; the categorical-axis warning in the axis label ("Fixed checkpoint (categorical: no interpolation)") is good practice. Algorithm: **absent** — there is no algorithm box or formal statement for the think-span logit-penalty processor, which is the paper's method. That is a notable omission for a method contribution.

### AAAI Compliance Risks

- **Page budget:** main technical content occupies pages 1–7 and references page 8, which is consistent with the conventional AAAI "technical content + separate reference allowance" structure. I cannot verify the exact AAAI-27 rule from the provided material — the authors must check the actual call, including whether the Ethical Statement counts inside the technical limit.
- **Reproducibility checklist:** _Not sufficiently specified in the provided material._ Nothing in the PDF indicates whether one is prepared.
- **Ethics statement:** present and substantive.
- **Limitations:** present (§6) and unusually complete.
- **Double-blind:** no author-identifying content detected; the internal file path is a minor smell, not a violation.
- **Appendix/supplement:** referenced throughout but not provided; if the venue's review does not guarantee reviewer access to it, several claims become unsupported.

### Questions for Authors

1. Will the abstract be corrected on the four mismatch points (dose-graded, base drift, cloze, 4-of-6 nulls)?
2. Where is the anonymized artifact link, and will fn5's per-item record be crosswalked before release?
3. Is the Ethical Statement counted inside or outside the page limit under the venue's rules, and has the checklist been drafted?

### Required Fixes

Abstract corrections; caveats out of fn2/fn5/fn10 into the body; five-arm forest into the paper; Figure 1 label collisions; algorithm box for the penalty; define `B_2` or drop the numbering; harmonize interval levels; artifact pointer.

### Rating

Rating: 4 / 10  
Confidence: 4 / 5

### Score Justification

Compliance items are in place and the tables are trustworthy, but four abstract-level mismatches, thirteen load-bearing footnotes, one collided figure, a missing algorithm box, and a page budget that spends its most space on a declared null add up to a presentation that a time-pressured reviewer will score below threshold regardless of the underlying science.

### Why Not Higher?

Because the abstract makes claims the body withdraws, and the paper's best evidence is in a supplement I was not given.

### Why Not Lower?

Because the structure, ethics, limitations, anonymity, and table craft are all genuinely competent, and every problem listed here is fixable by editing rather than by new work.

---

## 6. Score Summary Table

|Reviewer|Role|Rating / 10|Confidence / 5|Main Positive|Main Negative|
|---|---|---|---|---|---|
|R1|Technical Soundness|5|4|Well-controlled five-arm intervention with placebo, competitor, and sign-reversing arms|Headline cells are the two checkpoints with untuned edit hyperparameters; locality missing at 2/6|
|R2|Experiments & Reproducibility|4|4|All six cells and all null contrasts reported; disclosed reproducibility defects|Pool selected under one arm of the headline contrast, bias unsized; headline instrument precision .48|
|R3|Novelty & Related Work|5|3|Timely framing; think-span vs answer-stage distinction is a real idea|Closest prior work already observed the collapse on an R1-distill; §4 nets to a null; guard is oracle-gated|
|R4|Writing & Compliance|4|4|Substantive limitations and ethics; trustworthy tables|Four abstract/body mismatches; caveats in 13 footnotes; best figure in the supplement|

- **Average Rating:** 4.50
- **Median Rating:** 4.50
- **Lowest Rating:** 4 (R2, R4)
- **Highest Rating:** 5 (R1, R3)
- **Clear champion:** **No.** R1 and R3 are the closest to sympathetic, and neither reaches the threshold. Nobody in this panel would argue for acceptance in discussion.
- **Strong reject voice:** **No 2–3 voice.** R2's 4 is the anchor: "not good enough," not "unsound." That is the least favourable pattern for the authors — no champion to fight for it, and no obviously overreaching reject to argue against either.

---

## 7. SPC/AC-style Meta-review

### Overall Assessment

An honest, careful, unusually well-audited paper about a question worth asking, which does not currently establish its headline claim at the strength the title and abstract assert. The panel converges on one structural verdict: **the paper's transparency has outpaced its evidence.** Nearly every objection R1 and R2 raise is quoted from the paper's own text. That earns the authors credibility and simultaneously hands reviewers a ready-made rejection: F1 (pool selection favouring the reported drop, unsized), MJ11 (buffer account "remains a live alternative"), MJ10 (no matched parent–distill control, "remains future work"), and §4.2's permanent FAIL are all the authors' own sentences.

Two facts decide the outcome. First, the headline rests on 2 of 6 cells, uncorrected, with 2 cells signed the other way, measured on a pool whose selection rule "would if anything favour the drop we report." Second, the abstract's most quotable numbers (19.3% → 8.5%, "dose-graded") come from the instrument with precision .48 and from a ladder the paper says is not ordered on the outcome, while the high-precision endpoint does not separate the treated arm from the untreated baseline (p = .073).

### Consensus Strengths

- Important, well-posed evaluation-methodology question.
- §5's five-arm design with placebo, same-relation competitor, and reverse-direction arm; near-null controls and a clean sign flip.
- Exceptional reporting discipline: all cells, all nulls, internally consistent numbers, byte-identity audits, volunteered reproducibility defects.
- Substantive limitations and a genuinely engaged ethics statement.

### Consensus Weaknesses

- Admitted, directional, unsized pool-selection effect on the headline contrast (R2 fatal; R1 major).
- Headline reversion instrument at precision .48; strict endpoint fails against the untreated baseline.
- 2-of-6 cells, no multiplicity control, no pre-specified primary cell for the gap (while §5 shows the authors _can_ pre-specify).
- Mechanism explicitly unidentified: failed replay vehicle, withdrawn mediation claim, failed pre-registered concept-direction arm with negative LocAcc.
- No non-reasoning control, so "reasoning" is not isolated from decoding condition or chain length; buffer account live by admission.
- Headline is one editor, one dataset, one distillation recipe.
- Guard is oracle-gated, hence diagnostic only — the authors agree.
- Prose density, footnote-borne caveats, four abstract mismatches, one collided figure, no algorithm box, best figure in the supplement.

### Main Disagreement

R1 and R3 read §4's honesty as a virtue that partly offsets its emptiness; R2 and R4 price it as unrecovered cost. There is a second, sharper split: R1's lead objection is the **scan-status confound** (headline cells untuned) while R2's is the **pool confound**. These are different repairs, and the authors should note that satisfying one does not satisfy the other.

### Fatal Issues

Nothing unfixable. The nearest to fatal _for this submission cycle_ is the composed selection problem on the request pool (built under one arm of the headline contrast, with a matcher later found defective, never rebuilt, with no `B_0`-gated counterpart to size the bias). Absent a bound on that, the headline number is not defensible at the precision the abstract states it.

### Fixable Issues

Without new compute: all four abstract mismatches; promotion of the strict endpoint to primary; caveats out of footnotes; family-wise statement for Table 1; per-checkpoint edit configuration and locality table; forced-closure and precision disclosure; Figure 1 repair; algorithm box; five-arm forest into the body; §4 compressed; artifact pointer. With modest compute: `B_0`-gated pool re-analysis; equal-length filler; within-run budget ladder on one checkpoint; naturally-closed-only sensitivity. With real compute: matched parent–distill control; second editor and dataset in the main battery; human-audited instrument subsample.

### Rebuttal Potential

**Medium — conditional, and probably Low in practice.** Medium because most objections are about _framing and bounds_ rather than about wrong numbers, and a rebuttal that (a) reports a `B_0`-gated re-analysis, (b) promotes the strict endpoint, and (c) retracts "dose-graded" and the base-drift comparison could move a 4 to a 5 and a 5 to a 6. Low in practice for two reasons: the scan-status confound (R1 MJ1) and the missing non-reasoning control (R2 MJ10) cannot be answered with re-analysis, and if the venue's review track offers no author response, none of this reaches the reviewers at all. The authors should assume every fix must land **before** submission.

### Phase-2 / Discussion Potential

**Weak.** No champion, no strong-reject voice to provoke argument, average 4.5. Papers in this configuration are typically resolved without substantive discussion.

### Final Decision Recommendation

**Likely Reject.**

### Final AAAI Readiness Score

**48 / 100.** (Problem and framing ~16/20; experimental support ~9/25; novelty/significance ~11/20; rigor and honesty of reporting ~8/15; presentation and compliance ~4/20.)

---

## 8. Priority Revision Plan

### P0 — Must Fix Before Submission

1. **Bound the pool selection effect.** Re-analyse the headline drop on a `B_0`-gated pool, or on the intersection of `B_0`- and `B_3`-gated pools, and report both alongside the current frame. If a rebuild is impossible, report the drop restricted to cases the edited model answered with the old value at `B_0` and state that as a partial bound. Rebuild pool membership with the fixed matcher and report how many rows change.
2. **Fix the abstract.** Remove or requalify "dose-graded" (fn10 contradicts it); remove or requalify "the unedited base shows no detectable old-answer drift" (one cell; contrast disclaimed); remove the cloze-probe sentence (fn5 voids it); add one clause stating that the effect's interval excludes zero only at the largest checkpoint in each lineage.
3. **Promote the strict endpoint (precision .92) to primary** and demote the permissive 19.3% → 8.5% to secondary, disclosing precision .48 in the body. State explicitly that the strict contrast against the untreated baseline is −.051 [−.102,.000], p = .073.
4. **Add a per-checkpoint edit-configuration and locality table** (layer, scanned or placed, clamp, `ES_{B_0}`, non-leakage) and address in the body that the two headline cells are the unscanned ones. If the drop survives conditioning on matched edit strength, say so with numbers; if you cannot test it, name it as a limitation in §6 at the same prominence as the pool.
5. **State the family-wise position for Table 1.** Either a pre-specification record for "largest checkpoint in each lineage," or an explicit uncorrected-multiplicity statement in §3.2 next to the two intervals.
6. **Move the oracle-gating limitation into §5.1** and add one sentence in §1 saying the guard is not deployable, so no reader reaches §5.5 with the wrong expectation.
7. **Report forced-closure rate at 8192 per checkpoint** and a naturally-closed-only sensitivity for the two headline cells.
8. **Artifact pointer** (anonymized), and confirm the reproducibility checklist exists.

### P1 — Strongly Recommended

9. **Equal-length content-free filler at native chain length** on Qwen-32B — the cheapest way to close MJ11, which the paper itself calls a live alternative.
10. **Within-run budget ladder** (`B_0`, `B_1`, `B_2`, `B_3`, one gate, intervals) on Qwen-32B — delivers the "stress test" the title promises and resolves the `B_1` RR .208 vs `B_3` RR .193 tension.
11. **Compress §4 to ~0.5 pages** and use the space for the five-arm forest, the configuration table, and the fn2/fn5/fn10 caveats.
12. **Add an algorithm box** for the think-span penalty processor, including alias-set construction and tokenizer-boundary handling.
13. **Clarify the capability check**: gate active or penalty unconditional. If gated, the near-zero cost is definitional and must be described as such.
14. **Add the missing related-work directions**, especially CoT faithfulness (which §4.1's method presupposes) and parametric-vs-contextual knowledge conflict; state the one-sentence delta against the two closest prior works.
15. **One editing pass for readability**: caveats out of footnotes, coinages reduced, `B_2` defined or dropped, interval levels harmonized, Figure 1 label collisions fixed.

### P2 — Nice to Have

16. Human-audited subsample for the permissive/strict instruments; adversarial imputation of the 33 rate-limited validation rows.
17. Per-cell precision (float32/bfloat16) disclosure and precision-stratified headline.
18. One external mitigation baseline at the answer stage.
19. Cluster-robust treatment of the route census (41 instances, 33 facts).
20. Second-judge-family replication of at least one panel.

---

## 9. One-week Emergency Revision Plan

Assumes the current results are frozen and only re-analysis plus small runs are possible. Items needing GPU are marked.

**Day 1 — Abstract, title, and claim audit.** Rewrite the abstract against P0-2. Do a claim-by-claim sweep: for every numeric or evidential sentence in the abstract, §1 contributions, and §7, cite the table cell or section that supports it, and delete anything a footnote later disclaims. Decide on the title: if the budget ladder (Day 4) will not exist, replace "Stress Test" with something the two-point protocol earns.

**Day 2 — Pool re-analysis (no new generation).** From existing records, construct the `B_0`-gated and intersection frames and recompute the headline drop and Qwen-32B RR on each. Rebuild pool membership under the fixed matcher and report the row delta. Write the resulting bound into §3.1 and §3.2. If the drop shrinks materially, that determines whether this submission is viable at all — do this before spending effort on presentation.

**Day 3 — Endpoint and multiplicity restructure.** Promote strict displacement to primary throughout §5 and the abstract; surface precision .48/.92 in the body; add the family-wise statement to §3.2; harmonize interval levels; move fn2/fn5/fn10 content into the body. Build the per-checkpoint edit-configuration and locality table from existing logs, including the two unrecorded Qwen locality levels if the runs still exist (**GPU if they must be recomputed** — this is a cheap neighbour-prompt eval).

**Day 4 — Two small runs (GPU).** (a) Equal-length content-free filler at native chain length, Qwen-32B, same gate as the reported arms. (b) Within-run budget ladder `B_0`/`B_1`/`B_2`/`B_3` on Qwen-32B under one gate with paired intervals. Also compute forced-closure rates per checkpoint from existing generation logs (no GPU). These are the two experiments that convert admitted alternatives into bounded ones.

**Day 5 — Section surgery.** Compress §4 to half a page with an explicit "what this rules out" framing. Insert the five-arm forest as Figure 2 and fix Figure 1's label collisions. Add the algorithm box. Insert the oracle-gating limitation into §1 and §5.1. Clarify the capability-check gating.

**Day 6 — Related work and readability.** Add the missing directions with a one-sentence delta against the two closest works. Full readability pass: define `B_2` or drop it, cut single-use coinages, break the longest sentences, add a two-line notation glossary in §3.1. Target: a reader can state the contribution from §1 plus Table 2.

**Day 7 — Compliance and self-audit.** Reproducibility checklist; anonymized artifact link; verify page budget against the actual call including where the Ethical Statement counts; confirm the supplement contains every deferral the body names (replay-gate table, endpoint set, case-block fits, per-arm event totals, missingness pattern); final numbers-vs-tables consistency sweep, including the fn11-style non-additivity notes.

**Realistic outcome of this week:** P0-1 through P0-8 plus P1-9 through P1-15. It will **not** produce the matched parent–distill control, the second editor/dataset in the main battery, or the human-audited instrument. Those are the items that separate a 5 from a 7, and they are not one-week items.

---

## 10. Final Direct Answer

**1. Can this paper be submitted to AAAI now?**  
No — not in this form. It is a competent submission with an abstract that overstates it and a headline whose selection bias the paper itself declares unsized. Days 1–3 of the plan above (abstract correction, `B_0`-gated re-analysis, strict endpoint promoted) are the minimum. Those require almost no compute and change the review materially.

**2. Biggest risk if submitted now?**  
That reviewers reject it **using the paper's own sentences**. "A pool chosen for old-value retrieval under thinking would if anything favour the drop we report… nothing here sizes it" (§3.1), "the content-independent computational-buffer account… remains a live alternative" (§4.3), "we withdraw the planned natural-chain mediation claim" (§4.2), "remains future work" (§3.2). A reviewer needs twenty minutes to assemble a rejection from quotations. The secondary risk is that the abstract's "dose-graded" and cloze claims are found to be contradicted by the paper's own footnotes, which converts an honesty asset into a credibility liability.

**3. Most likely reason for low scores?**  
The headline effect appears in 2 of 6 cells, uncorrected, with 2 cells reversed, on a pool selected under one arm of its own contrast, measured by a .48-precision instrument, with no non-reasoning control and a live length/compute-buffer alternative. Reviewers will summarize that as "the central claim is not established."

**4. Which experiment group should be added first?**  
The `B_0`-gated (or intersection-gated) pool re-analysis. It is re-analysis rather than new compute, it attacks the one issue R2 calls fatal, and its outcome determines whether the rest of the revision is worth doing. Immediately after: the equal-length filler at native chain length, then the within-run budget ladder. If GPU is available for exactly one new run, make it the filler.

**5. Which section should be rewritten first?**  
The **abstract** — highest leverage per hour, and three of its sentences are currently contradicted by the paper's own footnotes. Then §3.1–§3.2 (state the pool bound and the family-wise position where the headline lives). Then §4, cut to half a page.

**6. What score pattern does the current version look like?**  
**5544** (this panel: 5, 4, 5, 4; average 4.5). In a three-reviewer configuration, most likely **554** or **544**. The defining feature is not the average but the shape: no champion, no strong reject, nobody motivated to argue in discussion.

**7. Highest realistic pattern after one serious revision?**

- **One week (P0 + most of P1, no new controls): 6, 5, 5, 6 → "6556."** Borderline. Presentation and claim discipline improve a lot; the pool bound helps; the scan-status confound and the missing non-reasoning control still cap R1/R2.
- **One month (add matched parent–distill control, a second editor and dataset in the main battery, human-audited instrument, budget ladder): 7, 6, 6, 7 → "7667."** That is a real accept candidate. An 8 is not reachable while the mechanism stays unidentified and the guard stays oracle-gated.

**8. Split into main paper + appendix?**  
It already is — the problem is the split is backwards. The main paper carries a 1.5-page declared-null mechanism section while the five-arm forest, the complete endpoint set, and the replay-gate table sit in the supplement. Rebalance: main paper keeps the protocol, the six cells, the configuration/locality table, and the full §5 battery **with its figure**; the supplement takes the audit minutiae, the route census detail, and the failed-vehicle diagnostics. Also stop relying on the supplement for anything that determines how a body number should be read.

**9. Continue targeting AAAI or redirect?**  
The topic fits AAAI, and the measurement-discipline contribution is one this community should see. But this paper's defence depends heavily on the authors being able to _explain their own caveats_ — and a review track without an author response removes exactly that. Two honest options:

- **Stay at AAAI** only if Days 1–3 are completed and the `B_0`-gated re-analysis does not shrink the effect. Expected outcome is still borderline-to-reject, but the paper stops being self-defeating and a sympathetic reviewer becomes possible.
- **Redirect** to a venue with an author-response phase, or one that explicitly values evaluation-methodology and negative results, and use the extra time for the matched parent–distill control and the second editor/dataset. That path has a materially higher expected acceptance and would let the paper be published as what it actually is: a strong measurement critique with an honest null mechanism, rather than a mechanism paper that fell short.

My recommendation: **do Days 1–3 regardless**, then decide on venue from the Day 2 number. If the `B_0`-gated drop holds near .10 with an interval excluding zero, AAAI is defensible. If it shrinks toward the four null cells, do not submit this cycle — the finding needs the parent–distill control before it can carry a paper.

# 防御性写作 Review Report — `paperwriting/manuscript/main.pdf`

**审阅对象**：main.pdf（8 页，正文 p.1–7，参考文献 p.8），2026-07-28 编译版 **判据**：用户提供的《发布会原则》12 条 + 默认决策规则 **方法**：7 个独立视角并行扫描 → 每个视角配 1 个对抗式验证 agent，专门反驳「这条 hedge 其实是承重的」→ 只保留能通过「不改任何一个事实即可修复」检验的条目 **产出规模**：139 条通过验证（71 CONFIRMED / 60 PARTIAL），8 条被验证驳回（承重，不得动），另有 30 条验证方补录

> **本报告的作用域限制（重要）** 按要求只读 main.pdf。因此本报告**无法判断**某条 caveat 是否是为了满足 `results.json` / D1–D8 债务台账 / 19 项 MAJOR 中的某条具体审计要求而写入的。所有「候选改写」都是**候选**，不是可直接粘贴的定稿——W2 的教训是处方句本身就是缺陷源。任何一条落地前必须：①对 `results.json` 复核数字；②确认被删的那句不是某条审计承诺的唯一兑现点。

---

## 一、总判定

这篇稿子的问题**不是防御过度的程度，而是防御成了文体本身**。

它已经越过了「严谨」，进入了「替审稿人写拒稿理由」。全篇没有一处虚假陈述——恰恰相反，诚实度极高——但诚实被组织成了一份**自我审计报告**，而不是一场发布会。

量化画像（跨方法交叉核对，两套独立计数一致）：

|指标|数值|
|---|---|
|否定/限制类 token（正文 7 页）|220 次|
|可辨识的**独立自我限制小句**|≈120 条，约 17 条/页|
|带自我限制小句的句子占比|§1 52%、§3 45%、§4 56%、§5 51%、§7 67%|
|§4 的 disclaimer : result 句数比|1.6 : 1（结果输）|
|§5 的 disclaimer : result 句数比|**2.0 : 1**（承载第二个 headline 的那节，说「不能证明什么」的句子是说「证明了什么」的两倍）|
|20 个（含次级）标题中读起来像 caveat 的|**7 个**（§4、§4.2、§4.3、§4.4、§5.3、§5.4、§6）|
|脚注|13 个，约 66 行 ≈ 0.6 页|
|§4 正文体量（除表图）|≈7.4k 字符，与 §3 持平（7.3k），是 §5 的 79%|

**一句话**：摘要是全文写得最好的部分（几乎没有自我否定），从引言开始崩塌，在 §5——也就是全文唯一的正面因果结果所在地——达到自伤峰值。**这篇论文承诺得很好，然后花五页收回承诺。**

净可回收版面：**约 0.5–0.6 页**（初扫估 1.1 页，对抗验证把承重披露还回去后砍掉约一半）。稿子正好卡在 7 页，这半页是真金白银。

---

## 二、三条结构主线（S 级，先改这三处，收益远大于逐句润色）

### S1 · §4 是全文最大的自伤面，且位置最要命

§4 夹在「问题」与「解法」之间——注意力最高的位置——却是按**失败清单**组织的：

- 标题本身命名了没做到的事：**"Visible Routes and an Unidentified Mechanism"**
- 开篇路线图主动预告失败：_"separating observational evidence, **a failed replay test**, and boundary evidence"_
- §4.2 标题：**"...and a Failed Replay Vehicle"**，正文 26 行 lab notebook（9/18、14/18、12/18、13/18、1/5，外加一个 _"non-rescuing post-hoc audit"_）
- §4.3 把对手的解释扶上位：_"the content-independent computational-buffer account of Gekhman et al. (2026) **remains a live alternative**"_——而这一小节的实际内容是本文自己的正面抑制结果
- §4.4 一个 null 实验独占编号小节，连预注册的 co-primary harm endpoint（LocAcc）为负都写进正文
- 收尾自我否定：_"The section's two observations are the cloze check and the answer-gated census. **Neither observation identifies natural-chain mediation.**"_

**内部矛盾（审稿人会抓的）**：脚注 5 说 cloze 检查 _"close to tautological"_、_"no control, no interval"_、_"we place no quantitative weight on this observation downstream"_——而这条观察**被提拔进了摘要**。你在摘要里卖的东西，自己在脚注里判了死刑。

**更刺眼的资源错配**：§4 全节最强的支持性证据——T-minus-N 在 CLR-positive 层的 **−.289 [−.444, −.156], p = .0002**，恰好落在「链条里能看见旧值」的地方——被埋在**脚注 9**；而一个 null 的 concept-direction 变体拿到了正文整段。

**处置**：

1. §4 → **"Visible Routes Back to the Old Answer"**；§4.2 → **"The Chain-Routing Hypothesis"**；删 §4.3 标题（内容并入 §5.1 一句）；§4.4 压成两句 + supplement 指针。
2. 删开篇路线图里的 _"a failed replay test"_ 短语（失败在 §4.2、§6 各披露一次，不缺这一次）。
3. §4.2 保留三件事、删掉其余：预注册过、门是 15/18 而实测 9/18、撤回 mediation claim。**9/18 vs 15 这个数字必须留**——它是全文最有信誉的一句话（事先设阈、逆自己利益执行）。删掉的是 14/18、12/18、13/18、1/5 与 "non-rescuing"。
4. fn9 的 −.289/p=.0002 提正文。
5. 删收尾的 _"Neither observation identifies natural-chain mediation."_——这是同一句话在 §4 内部的第 3 次、全文第 6 次。

回收 ≈ 25–30 行。**无一个数字改变，撤回声明与预注册 null 全部留在记录上。**

---

### S2 · 引言把两个贡献都亲手拆掉

**贡献 2 的落地句以自毁结尾**：

> _"...its strict displacement endpoint does not separate from the untreated baseline in the main battery or under the second editor, though it does in the second-scale run, **and we give that the same prominence as the effects that do**."_

最后半句**不是关于数据的陈述**，是关于「请读者如何加权本文」的元指令。它把一个**事先声明为 secondary** 的 endpoint 手动提拔成 co-headline。承重的部分（strict 是次要终点、对 untreated baseline 未分离）在 §5.4 有完整数字（−.051 [−.102, .000], p = .073）和 §5.5 的逐场景拆解——引言不需要再兑现一次。

**贡献 2 全段没有一个数字**。+.122、19.3%→8.5%、反号臂 −.217、三次迁移——一个都没进引言。

**引言第三段整段献给了一个撤回的 claim**，然后以 _"What survives is narrower and, we think, more useful"_ 收尾——本文对自己的定性是「一个失败项目的残余」，还给唯一该斩钉截铁的那句话加了个 _we think_。

**脚注 1 是 9 行的预先自我限制**，开头就是 _"Each of those is bounded."_——在贡献 1 落地的同一行，先告诉读者三个控制实验全都有限。逐条核查后：这 9 行**没有一个事实是唯一出处**（分别重复于 §3.3、fn4、§3.2、Fig.1 caption）。

**处置**：删 fn1 全文；贡献 2 补数字、把 strict 让位给 §5.4/§5.5 指针；第三段压成一句 _"Between the failure and the intervention sits an open diagnosis: native chains show visible routes back to the old value, but we do not identify natural-chain mediation (Section 4)."_；删 _"and, we think,"_。回收 ≈ 15 行 + 摘要 30 词。

---

### S3 · §5 举证倒挂：最强的结果得到最少的辩护

§5 是全文唯一的正面因果结果，也是**辩护最弱的一节**。

- **§5.2（钱在这里）≈19 行，§5.3（讲两个 null 控制臂能界定什么）≈44 行**，2.3 倍。
- §5.2 的 13 行里有 5 行在解释「读数不取决于选哪个对照」，然后指向一页之后的地方说「strict 那边取决于」。
- **优势从未被说出来（P6）**：为什么「只在 think span 里加惩罚、答案段一个 logit 都不碰，答案却动了」值得注意？为什么这不同于 §2 里那三种**作用在答案分布上**的 decoding 方法？§2 其实写对了这个 delta，但 §5.2 一个字都没接。
- **Table 2 的 caption 是 100% 记账**：六句话讲分母、配对、未校正多重性，**没有一句告诉读者这张表显示了什么**。这是第二贡献的旗舰表。
- §5.4 自造两句可引用的攻击语：_"the endpoint is **thinnest** where the effect is smallest"_、_"the strict endpoint is reported at the prominence of the primary ones **precisely because it is weakest**"_。前者是作者对自己 endpoint 的定性判词（不是测量量），后者是动机声明。删掉两句，没有任何陈述变假。
- §5.5 三次迁移都是**先给胜、立刻给让步**；最后一句 _"not a deployment-ready fix"_ 是在否认一个本文从没提出过的主张，且引言已经用 _"not a deployed defence"_ 否认过一次（全文共 5 处同义否认）。

**处置**：§5.3 的方向臂与特异性配对搬进 §5.2；§5.3 改题为「效应取决于惩罚哪些 token」；Table 2 caption 首句改为结论句；删 §5.4 两句判词；§5.5 开头补一句累计陈述。**净空间基本持平**（删的等于补的），但把八句现成的拒稿引语从审稿人手里拿走。

---

## 三、A 级单点（高危，逐条处置）

以下每条都已通过对抗验证：**删/改后无任何陈述变假**。

**A1 · 摘要导入一个自己后来撤回的诊断** — p.1

> _"**Yet** in the Qwen-32B reversions we examined, the edited association remains detectable at a cloze probe; separately, route analysis finds visible in-chain paths to old answers, **motivating a chain-routing hypothesis**."_

约 30 词（摘要的 15%）。`Yet` 把它框成对自己不利的转折；`motivating a chain-routing hypothesis` 埋下一个 §4.2 只能用「永久 Fail」回答的问题。而 cloze 那一半正是脚注 5 判定「不承载任何定量重量」的观察。 → **删 cloze 半句与 `Yet`**，保留 route 半句作为通往 §5 的桥；腾出的 30 词给干预的符号证据与三次迁移。

**A2 · §5.4 的两句自造判词** — p.6

> _"...so the endpoint is thinnest where the effect is smallest."_ _"...the strict endpoint is reported at the prominence of the primary ones precisely because it is weakest."_

前者把「嵌套 endpoint 的算术必然」（strict 要求 new value 缺席，当然低于 permissive）升级成对证据质量的判决；后者是动机陈述。两句都不是数据。 → 删。保留 _"All p values here are unadjusted"_ + 118 配对例数 + 区间 + p 值（全部承重）。

**A3 · 脚注 5 用八重否定拆掉摘要里的观察** — p.3

> _"This is **only** an installation sanity check: **no** control, **no** interval, **close to tautological** because ROME optimizes the target logit at the rewrite prompt, and conditional on the selected reversion sample. ... **nothing** lets a reader audit ... and we place **no** quantitative weight on this observation downstream."_

承重的是三件事：无对照无区间、conditional on selected sample、per-item 记录未 crosswalk（可复现性披露，必须留）。**不承重的是判词语域**：`only`、`close to tautological`、`nothing lets a reader`。机制（ROME 优化 rewrite prompt 的 target logit）留着——让读者自己得出「接近同义反复」的结论，比作者代劳强。 → 压缩至 4 行。

**A4 · §3.1 的忏悔簇** — p.2

> _"**No B0-gated pool was ever built, so nothing here sizes that.**"_ → **直接删**。本文从未暗示存在这样一个 pool，从未声称做过 pool-gating 敏感性分析，也没有任何估计量需要它。这句话凭空点名一个没人会想到的实验，宣布它不存在。纯自伤，零信息。

> _"The pool also **predates a fix to the matcher that built it**: it was selected before ... and **never rebuilt**, so requests entered it under a rule **later found to fire on** short country and language codes."_ → 披露承重（pool 成员资格用的是被取代的规则），**变更日志语域不承重**。改：_"Pool membership was fixed under an earlier matching rule, before word-boundary matching and a minimum alias length were added; every rate we report uses the current matcher."_

> _"the last below the .85 that scan used as its acceptance line, **and kept rather than retuned**"_ → `.85 acceptance line` 的对照必须留（否则 .835 没有标尺，且这是全文唯一出现 .85 的地方）；`kept rather than retuned` 同段已由「四个 checkpoint 未扫描、沿用同一相对深度」表达过。删后半句。

**A5 · §3.3 一句与本文自己的作用域声明打架** — p.3

> _"Binary unedited-base recall attenuates but does not eliminate **the fixed-checkpoint size association**, and case-block fits provide supporting outcomes ... **not a second independent trend line**; both are in the supplement."_

§3.2 说 _"we do not infer an ordered trend across checkpoints"_，§6 说 _"about six fixed checkpoints, not scale"_——这句却断言了一个 size association，然后花剩下的字解释它不算独立趋势线。**没有任何下游 claim 依赖它**（P8 判负），两个分析本来就在 supplement。 → 删，或退化成一句 supplement 指针。

**A6 · §2 主动提名自己的最近邻** — p.2

> _"Huang et al. (2026) **make the closest observation to ours**, in the multimodal setting: ..."_

后面的每一个事实（multimodal、near-perfect teacher-forced、collapsing grounded success、no budget axis）都该原样保留——包括 `collapsing`。要删的只是「本文自认最近邻」这个**排名判词**，以及把 delta 只写成差异、不写成优势。 → _"In the multimodal setting, Huang et al. (2026) report ... There the conflict is visual and there is no budget axis, so that design cannot show how a single text-only edit behaves as its own thinking budget changes."_

同段 **"Gekhman et al. (2026) supply the mechanism our diagnosis has to argue with"** — 自我加派一项举证义务。改为中性引述 + _"Section 4 takes up both accounts."_

**A7 · §2 唯一的定位声明写在负空间里** — p.2

> _"**Four properties are not addressed jointly by the work above:** ..."_

全篇唯一说「本文独特在哪」的句子，是用「别人没做什么」写的，留给读者自己推断本文做了。 → _"This paper brings together four properties the work above does not address jointly: ..."_ —— 比较性 claim 一字未变，只是先说正面。

**A8 · §6 是纯 limitation，没有 discussion，且六项重复计费** — p.7 标题 `Discussion & Limitations` 下面没有一句 discussion。而 pool filtering、judge-family bias、lexical endpoints、locality scope、mediation withdrawal、multiplicity **六项**在 §3–§5 已经说过一遍，这里是第二次收费。 → 改题为 **"Discussion"** 或 **"Scope and Discussion"**，开头补两句「这意味着什么」（评测实践该加一个 reasoning-time arm；think-span-only 能动答案说明失败点是可操作的），其余各条压成带 section 指针的单句。

**A9 · 把唯一的安全性正面结果写成了「代价」** — p.7

> _"Finally, **the guard's cost** on unedited queries sits inside a 0.02 absolute-accuracy gate ... .000 on 1319 GSM8K items and −.010 on 500 MATH items ... **while** the accompanying 90% intervals ... **are wider than that gate**. We report point-equivalence at the tested sets, **not equivalence**."_

1819 道题上测不出代价——这是干预的最佳安全证据——被写成一个以 "cost" 开头、以 "not equivalence" 结尾的段落。区间宽于门限这一事实**必须留**（不能声称等价），但可以放在句子后半而不是主句。 → _"The guard's cost on unedited queries is not detectable at the tested sets: .000 on 1319 GSM8K items and −.010 on 500 MATH items, both inside a 0.02 gate at the point estimate. The accompanying 90% intervals, [−.022, .022] and [−.061, .041], are wider than that gate, so this is point-equivalence at the tested sets and not an equivalence result."_

**A10 · 结论以双重否定开场、把第二贡献塞进一个让步小句** — p.7

> _"An edit that answers correctly on demand **has not been shown to survive** the reasoning the model will actually do."_ _"That failure **nonetheless** admits a chain-local causal control point."_

第一句的谨慎是有理由的（多数 edit 确实存活，B3 ES=.495 vs B0 .595，任何「edits do not survive」都是假的）——但存在量化的说法既真又强：_"An edit that passes direct-answer validation **can lose control of** the final answer once the model reasons."_ 最后一句给第二贡献 10 个词、藏在 `nonetheless` 后面，应展开成带数字的一到两句。

**A11 · Table 1 caption 里的道歉句自带答案却不说** — p.4

> _"...**because this filtering can be directional**, we also report the unfiltered n = 200 sensitivity, whose paired drop is .110 and permissive RR is .167."_

未过滤的 .110 **大于**报告的 .107——也就是说 early-stop 过滤**没有**抬高 headline。caption 提出了担忧、给了化解担忧的数字，却不告诉读者它化解了。 → 加四个词：_"...whose paired drop is .110—larger than the reported .107—and whose permissive RR is .167."_

**A12 · §5.3 把特异性胜利用失败语域交付** — p.6

> _"**Neither control separates** from no suppression on any of the three endpoints (Table 2)."_

真实结构是：treated 臂在三个 endpoint 上都与两个对照分离，而两个对照都贴着 no-suppression。这是**特异性证据**，是好消息。 ⚠️ **注意**：初扫 agent 给的改写句「while the treated arm moves all three」**是假的**——T-N 在 strict 上并未分离（−.051 [−.102, .000]）。验证 agent 拦下了这条。安全版本：_"The treated arm separates from both the placebo and the same-relation competitor on all three endpoints, while neither control separates from no suppression on any of them (Table 2)."_（对 P/C 的 T 对比确实三个 endpoint 全分离：T-P ΔRRs −.057 [−.114,−.010]，T-C −.057 [−.113,−.009]。） `we set no equivalence margin` 承重，保留。

**A13 · 冗余矩阵（同一 caveat 被收费多次）** 按 KEEP 列保留一处、其余删：

|#|caveat|出现次数|建议 KEEP|
|---|---|---|---|
|R9|mediation 未识别|**7 处**（intro / §4 标题 / §4.2 ×2 / §4.4 ×2 / §6）|§4.2 撤回句 + §6|
|R4|无 ordered trend / categorical|8 处|Fig.1 轴标 + §3.2 一句|
|R8|「不是可部署方案」|5 处|§5.5|
|R5|未校正多重性|5 处|Table 2 caption + §5.4 一句|
|R11|paired ≠ marginal|5 处（含 fn11 整整 4 行手算 _"and .495 plus +.138 does not equal .631"_）|两个表 caption；**fn11 整条删**|
|R1|permissive matcher precision .48|3 处|§5.4（唯一做论证工作的地方）；**§4.1 那处删**——把最不利的仪器数字搬进一个用不到它的小节，只为在同一句里与它划清界限|
|R2|单一 judge 模型族|3 处（fn2 与 fn6 近乎逐字重复，相隔一页）|§6|
|R6|base model「并列而非对比」|3 处|Fig.1 caption|
|R16|_"not a length-matched filler"_|**逐字 2 次**（§3.3、§4.3）|§3.3|

可回收 ≈ 45 正文行 + 12 脚注行。

**A14 · 脚注负载** — 13 条 / 66 行 ≈ 0.6 页 分类：(a) 承重 5 条 · (b) 可移 supplement 3 条 · (c) 纯自伤 4 条。 **建议整条删**：fn1（9 行，全部重复）、fn6（2 行，fn2 的逐字副本）、fn11（4 行，手算非恒等式）、fn7（2 行，已撤回 vehicle 的 κ）。 **建议压缩**：fn5（10→4 行）、fn2 的 missingness 叙述（−4 行）、fn13 结尾的 _"This battery has no changed-row audit of its own"_。 **必须留**：fn9（承载 −.289/+.014 实数）、fn3/fn4/fn12（数字）、fn10（dose ladder provenance）。

---

## 四、⚠️ 不要动（对抗验证判定为承重，删了会出事）

这一节和上面同样重要。以下 8 处被验证 agent **驳回**，理由充分：

1. **`"This is a diagnosis of where the failure is steerable, not a deployed defence."`**（intro 贡献 2 末句）——前三句刚宣称干预在三个对照上抬升 ES、降低 resurfacing，这句是当场的作用域锚。位置就是它的价值。
    
2. **`"the suppressor a tool for silencing true reasoning"`**（Ethical Statement 开篇）——伦理声明是全文**唯一**该反向操作的地方：先讲缓解、把 dual-use 读法软化，在伦理审稿人眼里叫 minimization，风险远大于一句可引用的措辞。而且下一句 _"it is no general truth-suppression capability"_ 是对**这个能力陈述**的反驳，改弱前句会让后句变成 non sequitur。 _（唯一可做的是**语序**：把三条 bounding properties 提到 "The dual-use reading is real" 之前，不增不删任何一句。）_
    
3. **`"Bfloat16 made the rank-one update diverge to NaN on the Hopper-class part..."`** ——两个部件跑不同数值精度是异常的方法学不对称；这个因果从句是把它从「随意选择」变成「被迫选择」的唯一说明。
    
4. **`"Intervals are unadjusted for multiplicity."`**（Table 2 caption）——§5.4 那句管的是 p values，不管 intervals。为省 6 个词去改另一小节的句子扩大其宾语，是真正的完整性编辑。
    
5. **`"while edit success and permissive reversion are not ordered across those settings."`**（§5.1 剂量梯）——与 fn10 不重复，fn10 讲的是三个设计事实。
    
6. **`"The gap also persists under temperature sampling across three fixed seeds."`** ——没有 hedge、没有自伤，只是短。把 fn4 提正文在 7 页极限下是净亏。
    
7. **hyperparameter 那段**（`.18 of the stack`、`.85 acceptance line`、update clamp 4→2、_"We did not record this level for the two middle Qwen checkpoints"_）——几乎每个从句都是**唯一披露**。`.85` 全文只此一处。
    
8. **`"Scoring is generative, not logit based"`** ——紧凑的操作性定义，不是 hedge。
    

另有两条初扫提出、验证方明确警告的**危险改写**：

- §5.3「treated arm moves all three」——**假**（见 A12）。
- §2 He et al. 那句 _"whose reasoning reflects outdated knowledge and overturns the edit"_ ——这是全文最威胁 novelty 的一段先行工作，**必须精确保留**。要处理的是本文 delta 的表述，不是弱化对方。

---

## 五、执行顺序建议

按「每小时收益」排序，不按章节顺序：

|优先级|动作|回收|风险|
|---|---|---|---|
|1|删 fn1、fn6、fn11、fn7；压 fn5|≈17 行|低（逐条已核过唯一性）|
|2|引言：贡献 2 补数字 + strict 让位；第三段压一句；删 _"we think"_|≈15 行|低|
|3|删 §5.4 两句判词 + §3.1「No B0-gated pool」+ §3.3 size association|≈8 行|低|
|4|§4 重命名 + §4.2 瘦身 + fn9 提正文 + 删 §4 收尾自我否定|≈25 行|**中**（需确认 §4.2 各数字不是某条预注册披露的唯一出处）|
|5|冗余矩阵 R1/R2/R4/R5/R8/R9/R16 逐项收敛到 KEEP 列|≈45 行|中（每处需确认 KEEP 位置真的在）|
|6|摘要删 cloze 半句 + `Yet`，腾出的词给符号证据/迁移|0（等量置换）|**中**（摘要有 v8.1 内部终版锁，需先解锁）|
|7|§5 举证重排：5.3→5.2 搬运、Table 2 caption 结论句、§5.5 开头累计句|≈0|中|
|8|§6 改题 + 补两句 discussion + 六项重复压缩；A9 正向化|≈5 行|低|
|9|伦理声明**仅调语序**（bounding 前置），一句不增不删|0|低|

前 3 项是纯净收益，可以立刻做。第 6 项与摘要锁冲突（plan v1.90③：正文完成前不动摘要）——**按现行纪律应排在正文冻结之后**。

---

## 六、一句话给计划 session

这篇稿子不需要更多证据，也不需要放松任何一条真实性纪律。它需要的是**把已有的真话重新排序**：让优势先说、让 caveat 只说一次、让标题命名做到的事而不是没做到的事，并把「请读者按这个权重读本文」这类元指令——它们不是数据——全部拿掉。**139 条里没有一条要求改动任何一个数字。**


# AAAI-style Simulated Review Report

> Unofficial pre-submission review. This is not an official AAAI review or an acceptance prediction. The assessment is based only on the provided eight-page PDF. No supplementary files, code, data, or external literature search were available.

## 0. Paper Summary

The paper tests whether a parametric knowledge edit that succeeds under direct answering remains effective after a reasoning model generates a native chain of thought. On a 200-request CounterFact pool, ROME edit success drops by 0.106 for Qwen-32B and 0.107 for Llama-70B, while the other four tested checkpoints do not show intervals excluding zero. The paper then suppresses old-answer first tokens only inside the Qwen reasoning span and reports improved edit success and reduced permissive old-answer resurfacing, arguing for a chain-local causal control point rather than an identified natural-chain mediation mechanism.

## 1. Title / Abstract / Main Paper Consistency Check

### Title Promise

The title promises a general evaluation lesson for parametric knowledge editing: direct-answer success is insufficient when edited models reason before answering.

### Abstract Claims

The abstract claims:

- a paired zero-thinking versus native-chain stress test across six checkpoints;
- approximately 10.6-10.7 percentage-point edit-success losses at Qwen-32B and Llama-70B;
- 19.3% permissive old-answer resurfacing and 9.2% strict displacement among Qwen-32B direct-answer successes;
- no detectable matching drift in the unedited Qwen-32B base;
- surviving edited association at a cloze probe and visible chain routes to old answers;
- a signed, multi-dose, think-span-only intervention that raises edit success and lowers permissive resurfacing from 19.3% to 8.5%;
- near-null answer-level placebo and same-relation controls.

### Main Paper Support

Table 1 supports the reported Qwen-32B and Llama-70B paired drops. Section 3 reports all six checkpoint cells and correctly states that only the two largest tested checkpoints have unadjusted 95% intervals excluding zero. Table 2 supports the direction of the five-arm Qwen-32B intervention. Sections 4 and 6 explicitly withdraw the natural-chain mediation claim after the replay vehicle fails its validity gate. The paper also discloses the weak permissive matcher precision, the strict-endpoint null against no suppression, the missing human audit, the narrow locality measure, and the single-dataset/single-editor scope of the headline gap.

### Mismatches

1. **The title and opening claim are broader than the demonstrated population.** The gap is statistically detectable in two of six fixed checkpoints, on one B3-selected CounterFact pool, with ROME as the only editor used to establish the gap. Both model lineages share an R1 teacher and distillation recipe.
2. **“The unedited base shows no detectable old-answer drift” does not establish edit-specific erosion.** The base analysis is available only at Qwen-32B, uses a different event definition and denominator, and is juxtaposed rather than tested through an edited-by-reasoning interaction.
3. **“Dose-graded” should not be read as a dose-response result.** Leakage declines with penalty strength, but edit success and reversion are not ordered across doses; the paper itself calls this a dose ladder.
4. **“Chain-local causal control point” is supportable only in the narrow intervention sense.** The experiment shows that an oracle, edit-aware manipulation inside the chain can causally change the later answer. It does not identify the naturally occurring mediator, show that the route is necessary, or exclude realized chain length as an alternative.
5. **The abstract gives the strongest results more prominence than their validation quality warrants.** The 19.3% resurfacing endpoint uses a permissive matcher with available-case precision of 0.48 against judge majority, whereas the stricter T-versus-N endpoint reaches zero in its interval.
6. **Calling the controls “near-null” is stronger than the reported inference.** Section 5.3 states that no equivalence margin was set, so the placebo and competitor results are failures to separate from zero, not evidence of negligible effects.
7. **The cloze observation is over-prominent in the abstract.** It is based on 23 selected reversions, lacks a control and interval, is close to what ROME optimizes, and cannot be completely crosswalked to the route sample.

## 2. Reviewer 1 — Technical Soundness

### Summary

The paired within-edit stress test is logically coherent, and the think-span intervention is carefully bounded: weights are restored between requests, answer logits are not directly penalized, and reverse-signed and token controls are included. The current version nevertheless cannot support a general claim that reasoning erodes editing because the evaluated population is selected through one arm of the comparison using an obsolete matcher, the edited-versus-unedited interaction is not tested, and the intervention demonstrates manipulability rather than natural-chain mediation.

### Strengths

- The same edit is evaluated at B0 and B3, reducing between-edit confounding.
- The paper defines ES, permissive RR, strict displacement, and CLR separately and explains their different denominators.
- All six checkpoint cells are reported, including null and reverse-direction cells.
- The intervention changes only the think span and includes no-suppression, old-answer, new-answer, placebo, and same-relation arms.
- The failed replay gate and null concept-direction result are disclosed rather than converted into a mechanism claim.
- Limitations distinguish a diagnostic control point from a deployment-ready defense.

### Weaknesses

#### Fatal Issues

1. **Outcome-adjacent sample selection threatens the headline estimand.** The 200-request pool is derived from cases where unedited Qwen-7B at B3 produced an old-value alias. B3 is one arm of the headline comparison. This defines a legitimate conditional population, but it can favor B3 old-value retrieval and cannot support an unconditional CounterFact or model-general claim. No independent, B0-gated, symmetric, or full-pool sensitivity is reported.
2. **Pool membership was created with a matcher later found to produce false hits and was never rebuilt.** Applying the corrected matcher only to outcome scoring does not repair contaminated inclusion. The magnitude and direction of the membership error are not quantified. The central result must survive a rebuilt pool before the main claim is technically secure.

#### Major Issues

1. **Edit specificity is not established.** The unedited-base check uses a different outcome and denominator at one checkpoint. A formal paired interaction on identical cases and metrics is required.
2. **The primary checkpoint emphasis is vulnerable to multiplicity.** Only two of six unadjusted checkpoint intervals exclude zero. The manuscript calls the largest-checkpoint scope non-post-hoc, but the provided material does not establish a prospective primary family or multiplicity plan.
3. **The causal claim is narrower than the terminology suggests.** Suppressing old-answer tokens in a live chain proves that this intervention can alter the later answer. It does not prove that spontaneous old-answer tokens mediate natural reversions, especially because the replay vehicle failed and CLR is non-sufficient.
4. **Length and computation remain confounded with content.** The canned thought is not length matched, and realized chain lengths after suppression were not audited. The intervention may alter both semantic content and the amount or trajectory of computation.
5. **The intervention is oracle and edit aware.** It requires the edited subject, relation, old-value aliases, and their first tokens. This is acceptable for a diagnostic probe but sharply limits claims of a generally usable guard.
6. **The primary intervention battery has unresolved gating and provenance.** Table 2 arm sizes range from 196 to 200 because of harness errors, RR contrasts use intersections of separately realized B0 gates, the battery lacks its own byte-identity audit, and the placebo analysis contains an unexplained extra row.
7. **Implementation fidelity is not auditable from the PDF.** Exact prompt templates, tokenization rules, model identifiers, complete editor settings, chain parsing, stop handling, alias construction, placebo selection, and processor logic are **Not sufficiently specified in the provided material**.

#### Minor Issues

- Only two checkpoints were layer-scanned; the remaining four inherit a relative-depth rule, and Llama-8B alone uses a different clamp.
- Locality is defined as target-value non-leakage rather than behavior preservation.
- The cloze sanity check is selected on 23 reversions, has no control or interval, and is close to the objective optimized by ROME.
- The route census is outcome conditioned and cannot estimate route prevalence in ordinary use.

### Questions for Authors

1. Do the Qwen-32B and Llama-70B gaps survive a corrected-matcher pool selected independently of both B0 and B3?
2. What is the paired edited-versus-unedited B0/B3 interaction on the same requests and the same old/new semantic endpoint?
3. Were the largest checkpoints and their two contrasts prospectively designated as the headline family? Where is that record?
4. How do results change after matching or conditioning on realized chain length?
5. What exact tokenization, alias aggregation, prompt, stop, and answer-extraction rules define the think-only intervention?
6. Can the control-point effect be reproduced without oracle access to the old value or with a detector learned on disjoint edits?
7. Can all Table 2 RR contrasts be recomputed on one immutable case set and one byte-identical B0 gate, with every event count shown?
8. In the three-seed sampling analysis, was resampling clustered by case across seeds rather than treating case-seed pairs as independent?

### Required Fixes

1. Rebuild the evaluation population with the corrected matcher and selection independent of the tested reasoning arms; report full-pool and alternative-gate sensitivities.
2. Add a same-case, same-endpoint edited-versus-unedited interaction at every checkpoint.
3. Restrict “causal control point” to intervention sufficiency unless a valid mediation experiment is added.
4. Add length-matched content controls and report realized chain length by arm.
5. Rerun Table 2 on one immutable case set with one shared B0 gate and reproducible row hashes.
6. Provide complete executable method details and resolve every harness/provenance discrepancy.

### Rating

Rating: 5 / 10  
Confidence: 4 / 5

### Score Justification

The paper contains a coherent paired design and a nontrivial signed intervention, but two design facts—the B3-conditioned pool and obsolete inclusion matcher—can determine whether the headline phenomenon is representative. The causal language is acceptable only under a narrow intervention interpretation.

### Why Not Higher?

The population construction, lack of a formal edited-versus-unedited interaction, unresolved length confounding, and incomplete reproducibility prevent the central interpretation from clearing the acceptance threshold.

### Why Not Lower?

The numerical definitions are internally consistent, the controls are more thoughtful than a simple before/after comparison, and the paper explicitly withdraws the mechanism claim that its failed experiment cannot support.

## 3. Reviewer 2 — Experiments & Reproducibility

### Summary

The experimental program is broad within one narrow setting: six checkpoints, paired B0/B3 evaluation, a five-arm Qwen-32B intervention, sampling and canned-thought checks, one second scale, one MEMIT intervention transfer, and a paraphrase probe. However, the main gap remains based on one dataset, one editor, a 200-item outcome-adjacent pool, mostly one generation per cell, lexical outcomes, and incomplete provenance.

### Strengths

- Case-paired estimates and confidence intervals are more informative than marginal accuracy alone.
- The paper reports all checkpoint cells and an unfiltered Llama-70B sensitivity.
- The five-arm design includes a reverse-signed direction arm and two distinct controls.
- Negative results, unadjusted multiplicity, non-equivalence of null controls, and failed replay are disclosed.
- Sampling at three fixed seeds and transfer to Qwen-14B/MEMIT provide useful, although limited, sensitivity evidence.

### Weaknesses

#### Fatal Issues

1. **The main pool must be rebuilt and rerun.** It was selected under B3 using a matcher later repaired for false short-code hits. Scoring with the new matcher cannot correct biased or contaminated membership.
2. **The primary resurfacing narrative is not semantically secure.** The permissive RR rule has available-case precision 0.48, only 87/120 validation items received judge votes, missingness is concentrated among rule-negative rows, and no human-audited sample is reported.

#### Major Issues

1. The headline gap is established with ROME and CounterFact only. MEMIT transfers the intervention but does not independently replicate the gap.
2. Both backbones share the same reasoning teacher/recipe; no matched parent-versus-distill control or second reasoning recipe is tested.
3. Greedy headline cells contain one generation per case. Case bootstrap captures case variation, not end-to-end run, sampling, or systems variation.
4. There are six checkpoint contrasts, multiple endpoints, five arms, strata, transfers, and robustness analyses with unadjusted intervals or p-values. No confirmatory family or hierarchical analysis is supplied.
5. The unedited-base control is limited to Qwen-32B and is not a matched interaction.
6. The fixed canned thought is not an equal-length content-free control, and realized chain lengths under suppression are not reported.
7. The paraphrase audit is weak: 30/40 were judged valid, only 11/20 cases were valid on both probes, kappa is 0.444, and no valid-subset analysis is reported.
8. Locality and utility coverage are insufficient. Target-value non-leakage can count refusal as success, and the GSM8K/MATH intervals are too wide to establish the stated equivalence gate.
9. Arm sizes differ because of harness errors; the placebo has an unexplained extra row and is not byte-reproducible from the released shards.
10. The three-seed sampling result does not say whether bootstrap resampling was clustered by case; otherwise the 597 case-seed pairs risk pseudoreplication.

#### Minor Issues

- Bootstrap replicate count, interval construction, and resampling details are **Not sufficiently specified in the provided material**.
- Some conditional contrast denominators and per-arm event totals are absent.
- The 41-instance route census is too small and selected to support prevalence or prediction claims.
- Exact compute time and total resource use are not reported.

### Missing Experiments

1. **First priority:** corrected-matcher, selection-independent reconstruction of the CounterFact pool, with full-pool, B0-gated, B3-gated, and symmetric pre-edit-knowledge sensitivities.
2. Formal same-case difference-in-differences between edited and unedited B0/B3 behavior.
3. Independent replication of the headline gap on a second dataset and under MEMIT or another editor.
4. Multiple end-to-end reruns and a larger predeclared seed set with run-level uncertainty.
5. Blinded human semantic annotation for primary ES/RR outcomes.
6. Equal-length filler, realized-length audit, and length-matched analysis.
7. A second reasoning recipe or matched base-versus-reasoning-distilled checkpoints.
8. Stronger locality, neighbor, OOD, multi-hop, and unguarded-query evaluation.

### Reproducibility Concerns

- Exact checkpoint identifiers, numerical seeds, chat templates, canned-thought text, sampling temperature/top-p, answer budgets, alias lists, judge model/prompts, and donor lists are **Not sufficiently specified in the provided material**.
- Complete ROME/MEMIT hyperparameters and bootstrap implementation are **Not sufficiently specified in the provided material**.
- Hardware is described only by accelerator class and memory; exact models, counts, runtime, and software stack are **Not sufficiently specified in the provided material**.
- The PDF refers to a supplement, lock file, provenance record, JSONL record, figures, and shards that were not provided and therefore cannot be audited.
- The unexplained row differences and non-byte-reproducible placebo analysis prevent exact reconstruction of Table 2.

### Questions for Authors

1. Do all headline and intervention effects survive a clean, arm-independent pool?
2. Which tests and endpoints were confirmatory, and what survives multiplicity adjustment?
3. Does the B0/B3 gap itself replicate under MEMIT and on a second benchmark?
4. Can human annotation validate the permissive RR rate and the paraphrase transfer?
5. What caused every missing/extra arm row, and can one canonical artifact reproduce all reported numbers?
6. How much variance appears across independent reruns, seeds, reasoning budgets, and decoding settings?

### Required Fixes

1. Rerun the clean-pool headline experiment before any other expansion.
2. Make a validated strict or human semantic outcome primary.
3. Add independent dataset/editor replication and run-level uncertainty.
4. Add a formal interaction and a multiplicity plan.
5. Repair provenance, publish exact denominators/event counts, and supply a complete reproducibility package.

### Rating

Rating: 4 / 10  
Confidence: 4 / 5

### Score Justification

The current experiments support a narrow descriptive result on the selected pool, not a robust general stress-test conclusion. The pool construction and permissive endpoint validity are outcome-determinative, while replication and reproducibility remain below the level needed for acceptance.

### Why Not Higher?

The central experiment needs a clean population, semantic validation, an independent gap replication, and a defensible statistical hierarchy.

### Why Not Lower?

The authors use appropriate within-case pairing, report important nulls, and include a thoughtfully signed intervention battery with several useful sensitivity checks.

## 4. Reviewer 3 — Novelty, Significance & Related Work

### Summary

The paper addresses a timely mismatch between how edits are certified and how reasoning models are deployed. Its strongest novelty is not the observation that autoregressive reasoning can overturn edits—closely related failure modes are already discussed in the cited work—but the paired reasoning-budget formulation and the signed intervention confined to the think span.

### Strengths

- The paired B0/B3 evaluation isolates a deployment-relevant axis for the same edit.
- The answer-untouched, reverse-signed intervention is a sharper contribution than another benchmark-only failure report.
- The paper distinguishes observation, failed mediation, and intervention sufficiency unusually clearly.
- If reproduced on an unbiased population, the stress test could become a useful addition to editing evaluation.

### Weaknesses

#### Fatal Issues

No novelty-fatal issue can be established from the provided PDF alone. An external literature search was not performed, so priority over uncited work cannot be verified.

#### Major Issues

1. The paper's own related-work section describes prior studies in which realistic autoregressive inference or reasoning exposes outdated knowledge and weakens editing. The incremental distinction is pairing one edit across budgets plus controls, not discovery of the broad phenomenon.
2. The think-span suppression uses oracle old-value knowledge and resembles test-time knowledge/logit steering in functional form. Its novelty is its restricted scope and causal use, not a deployable editing method.
3. The paper does not experimentally compare the stress test or guard against broader families of editors, reasoning-aware editors, retrieval/context methods, or editing-aware decoding methods under equal conditions.
4. The core empirical finding is narrow enough that significance depends heavily on clean replication. Two significant checkpoint cells from one selected pool do not yet establish a general evaluation failure.
5. The natural-chain mechanism remains unidentified. This limits the scientific depth of the “why” contribution and leaves the work between an evaluation note and a mechanistic paper.

#### Minor Issues

- The route taxonomy is descriptive and answer conditioned.
- The second editor and paraphrase studies transfer the intervention, not the core gap.
- No non-counterfactual corrective edits are tested, which weakens practical significance.

### Novelty Assessment

**Moderate.** The stress-test framing and paired design are useful but incremental relative to the cited evidence that reasoning or realistic decoding can reveal failed edits. The signed think-span-only intervention is the clearest original element, provided it is framed as a diagnostic causal probe.

### Related Work Gaps

The discussion should more systematically position the contribution against:

- alternative weight-editing, memory-based, retrieval-based, and context-based update families;
- reasoning-aware knowledge editing and multi-hop edit propagation;
- test-time logit steering and contrastive decoding for edited knowledge;
- causal mediation and representation-intervention work on reasoning traces;
- knowledge-conflict and factual-priming studies that separate retrieval, verbalization, and final commitment.

Specific missing papers are **Not sufficiently specified in the provided material**, because no external literature search was performed.

### Significance Assessment

**Potentially meaningful but not yet established.** A clean result would matter to researchers who validate edits only through direct answers. The current evidence is too conditional to justify a field-wide evaluation prescription, and the oracle guard has limited deployment significance.

### Questions for Authors

1. What exact claim remains novel after removing the already documented observation that reasoning can expose old knowledge?
2. Does the paired gap replicate under editors designed for sequential, multi-hop, or realistic autoregressive settings?
3. Can the intervention work without explicit old-answer aliases?
4. What evidence shows that this is more than lexical priming control inside a generated rationale?
5. Why should the community adopt this exact protocol rather than a broader semantic, task-level stress suite?

### Required Fixes

1. State the novelty as paired budget-controlled evaluation plus a think-span diagnostic intervention, not as first discovery of reasoning-time edit failure.
2. Add direct comparisons across editor/decoding families and a second benchmark.
3. Separate evaluation contribution, mechanistic hypothesis, and deployment guard in both claims and experiments.
4. Demonstrate significance on an arm-independent population and a semantic outcome.

### Rating

Rating: 5 / 10  
Confidence: 3 / 5

### Score Justification

The contribution is relevant and has a distinctive intervention, but the broad failure mode is close to evidence already cited by the paper. Significance is contingent on rerunning the central experiment under a valid population and broader settings.

### Why Not Higher?

The novelty boundary is narrow, the mechanism is unresolved, and the empirical scope is not yet sufficient to make the stress test a general community recommendation.

### Why Not Lower?

The paired reasoning-budget axis and answer-untouched signed intervention are concrete contributions beyond a routine application of existing editors.

## 5. Reviewer 4 — Writing, Structure & Compliance

### Summary

The manuscript is polished, unusually transparent, anonymous in the provided PDF, and visually free of rendering defects. Its main writing problem is excessive defensive density: long sentences, stacked caveats, footnote-heavy audit details, and repeated “not X, only Y” formulations obscure the main line and make the paper read like a rebuttal before review.

### Strengths

- Title, abstract, tables, and major numerical claims are mostly consistent.
- Sections 6 and the Ethical Statement are substantive rather than perfunctory.
- Negative results and invalidated mechanism claims are prominently disclosed.
- Table 1 and Table 2 are legible and numerically informative.
- All fonts are embedded; no clipping, overlap, broken glyphs, or margin overflow was found.
- The PDF metadata contains no author identity, and no affiliation, email, acknowledgement, personal URL, or identifying hyperlink appears.

### Weaknesses

#### Fatal Issues

No fatal visual or anonymity defect was found in the provided PDF. Compliance of unprovided supplementary material is **Not sufficiently specified in the provided material**.

#### Major Issues

1. The prose is too compressed and legally defensive. Essential claims, caveats, protocol details, and audit history compete within the same paragraphs.
2. The title, abstract, and conclusion generalize beyond the two significant cells and selected ROME/CounterFact setting.
3. Reproducibility-critical information is repeatedly deferred to a supplement, lock file, shards, or provenance record that is absent from the provided material.
4. The method is complex enough to need a compact algorithm or pipeline schematic. Prose alone makes B0/B0P/B1/B3, ES/RR/RRs/CLR, gating, and arm-specific denominators difficult to retain.
5. The abstract foregrounds the low-precision permissive endpoint without equally foregrounding its validation limitation.
6. Calling placebo and competitor effects “near-null” is not justified by failure-to-reject tests without an equivalence margin.

#### Minor Issues

- Figure 1 labels and panel titles are small; the panel-B label/title is cramped.
- Captions and footnotes are unusually long and dense.
- The Reproducibility paragraph has an awkward one-line continuation in the next column.
- The custom “distribution/citation prohibited” notice on page 1 is template dependent and should be removed unless explicitly permitted.
- The references page leaves substantial unused space; this is aesthetic, not substantive.

### Structure Problems

- Section 3 should lead with a clean estimand and population diagram before detailed caveats.
- The failed replay vehicle consumes substantial main-text attention despite producing no mechanism result.
- Audit/provenance exceptions are scattered across footnotes and Sections 4-6 rather than consolidated.
- The paper needs a clear separation among: (i) stress-test finding, (ii) observational diagnosis, (iii) failed mediation attempt, and (iv) intervention sufficiency.

### Writing Problems

- Many sentences carry several statistical, causal, and scope qualifications at once.
- Acronym density is high, especially around B0/B0P/B1/B3 and RR/RRs/CLR.
- Repeated meta-language such as “we infer neither,” “juxtaposed rather than contrasted,” and “not a second independent trend line” is precise but cumulatively exhausting.
- There is no reliable basis to claim AI-generated authorship. However, repetitive mirrored disclaimers, parenthetical scope policing, and uniformly compressed syntax can create that perception. This is a style risk, not evidence of tool use.

### Figure / Table / Algorithm Quality

- **Figure 1:** conceptually useful and vector-rendered, but labels should be enlarged and panel headings separated.
- **Tables 1-2:** readable and well captioned, but conditional denominators and event counts should be directly tabulated rather than explained across prose and footnotes.
- **Algorithm:** absent. Add pseudocode for pool construction, edit/apply/evaluate/revert, chain/answer parsing, and the think-span processor.

### AAAI Compliance Risks

- The PDF has eight letter-size pages: seven pages of main content and one references page. Whether this satisfies the applicable AAAI year's limit is **Not sufficiently specified in the provided material**.
- The main PDF appears double blind; supplementary anonymity cannot be audited.
- An Ethical Statement and a Discussion & Limitations section are present.
- No standalone reproducibility checklist is included. Whether one is required is **Not sufficiently specified in the provided material**.
- The repeatedly cited supplement was not provided. If it is not separately submitted, this is a major completeness failure.
- The custom first-page notice and any exact template deviations should be checked against the applicable author kit rather than assumed compliant.

### Questions for Authors

1. Will the complete, anonymized supplement and reproducibility artifacts accompany the submission?
2. Can the abstract and conclusion be rewritten around the conditional population and two supported cells?
3. Can the failed mechanism audit move to the appendix while the valid causal claim remains in the main paper?
4. Can all primary denominators, event counts, and confirmatory tests fit in one main-text table?
5. Has the final PDF been checked against the exact target year's page and template rules?

### Required Fixes

1. Rewrite the abstract, Section 3.1, and conclusion to narrow claims and make the estimand explicit.
2. Cut defensive audit prose from the main narrative and consolidate it in an appendix.
3. Add a pipeline schematic or pseudocode and a compact notation table.
4. Enlarge Figure 1 labels and shorten captions/footnotes.
5. Submit and cross-reference a complete anonymized supplement and verify exact template requirements.

### Rating

Rating: 6 / 10  
Confidence: 4 / 5

### Score Justification

The manuscript is professional, careful, and visually sound, but its defensive density and claim breadth reduce clarity. Exact venue compliance cannot be established from the PDF alone.

### Why Not Higher?

The main argument is harder to follow than necessary, and critical scope/reproducibility facts are split across footnotes and unavailable supporting files.

### Why Not Lower?

The writing is technically precise, negative evidence is candidly presented, the layout is clean, and no anonymity or rendering failure was found.

## 6. Score Summary Table

| Reviewer | Role | Rating / 10 | Confidence / 5 | Main Positive | Main Negative |
|---|---|---:|---:|---|---|
| R1 | Technical Soundness | 5 | 4 | Paired design and signed think-span intervention | B3-conditioned, stale-matcher pool undermines interpretation |
| R2 | Experiments & Reproducibility | 4 | 4 | Broad control battery and transparent null reporting | Main gap lacks clean-pool, semantic, and independent replication |
| R3 | Novelty & Related Work | 5 | 3 | Distinct paired stress test and answer-untouched intervention | Broad failure mode is close to cited prior evidence |
| R4 | Writing & Compliance | 6 | 4 | Polished, transparent, anonymous, visually clean | Dense defensive prose and unavailable supporting artifacts |

- Average Rating: **5.0 / 10**
- Median Rating: **5.0 / 10**
- Lowest Rating: **4 / 10**
- Highest Rating: **6 / 10**
- Clear champion: **No.** No reviewer reaches 7.
- Strong reject voice: **Yes in substance, from R2**, although the numerical score is a 4 rather than a 1-3 strong-reject rating.

## 7. SPC/AC-style Meta-review

### Overall Assessment

The paper has a credible idea, a careful paired design, and a stronger-than-usual signed intervention. It is not ready for acceptance because the central population was selected using the B3 condition and an obsolete matcher, while the most prominent resurfacing endpoint has weak semantic precision. These are not cosmetic defects: they determine what population the headline describes and whether “old knowledge resurfacing” is being measured correctly.

### Consensus Strengths

- Timely and practically relevant evaluation question.
- Same-edit B0/B3 pairing and weight restoration between requests.
- All checkpoint cells and several important null results are disclosed.
- Five-arm, reverse-signed think-span intervention is the strongest contribution.
- The paper correctly withdraws natural-chain mediation after a failed validity gate.
- Limitations, ethics, anonymity, and PDF rendering are handled well.

### Consensus Weaknesses

- B3-conditioned pool plus unrepaired matcher contamination.
- No clean edited-versus-unedited interaction on identical endpoints.
- Only two of six checkpoint intervals exclude zero, with no clear multiplicity hierarchy.
- One dataset and one editor establish the gap; both model lineages share a reasoning recipe.
- Permissive RR has low precision and no human validation.
- Length/content confounding and oracle dependence limit the control-point interpretation.
- Harness/provenance anomalies and absent supporting artifacts impede reproduction.

### Main Disagreement

The likely panel disagreement is whether the signed think-span intervention and unusually honest reporting compensate for the compromised headline population. A positive reviewer may view the work as a useful diagnostic paper with bounded claims. A negative reviewer will argue that the main stress-test result has not been established on a valid evaluation population and that the intervention is an oracle steering probe attached to a known class of failure.

### Fatal Issues

1. No corrected-matcher, arm-independent rerun of the headline experiment.
2. No reliable semantic validation for the prominently reported permissive resurfacing rate.
3. General claims exceed a result found in two cells of one selected dataset/editor setting.

### Fixable Issues

- Formal interaction analysis, multiplicity plan, exact event counts, and denominator reporting.
- Equal-length controls and realized chain-length audit.
- Second editor/dataset/recipe replication.
- Full reproducibility package and resolution of harness anomalies.
- Narrower title/abstract/conclusion and a simpler narrative.

### Rebuttal Potential

**Low.** A rebuttal can clarify that mediation is not claimed and can expose already-computed sensitivities, but prose cannot repair outcome-adjacent sample selection, matcher contamination, semantic endpoint validity, or missing replication. Those require new analysis or experiments.

### Phase-2 / Discussion Potential

**Weak.** The intervention may attract discussion, but there is no clear champion and the clean-pool objection can terminate the discussion. Potential becomes moderate only if a corrected, independently selected rerun is already available and preserves the effects.

### Final Decision Recommendation

**Likely Reject**

### Final AAAI Readiness Score

**52 / 100**

## 8. Priority Revision Plan

### P0 — Must Fix Before Submission

1. Rebuild the pool with the corrected matcher and a selection rule independent of B0/B3; rerun all six headline cells and report alternative-gate/full-pool sensitivities.
2. Run a same-case, same-semantic-endpoint edited-versus-unedited B0/B3 interaction across all checkpoints.
3. Replace permissive lexical RR as the narrative anchor with blinded human or high-quality independent semantic annotation; report strict endpoint event counts.
4. Replicate the B0/B3 gap itself on a second editor and a second dataset. Intervention transfer alone is insufficient.
5. Repair all missing/extra rows, freeze one canonical analysis, and make every table byte-reproducible.
6. Rewrite the title, abstract, Section 3.1, and conclusion after the clean rerun; do not preserve claims that the rerun does not support.

### P1 — Strongly Recommended

1. Predeclare a confirmatory test family; use multiplicity correction or a hierarchical case/checkpoint model.
2. Add independent reruns and enough sampling seeds to estimate run-level variance.
3. Add an equal-length content-free filler and report realized chain length per intervention arm.
4. Test a second reasoning recipe or matched parent-versus-distill checkpoints.
5. Strengthen locality, neighbor, OOD, multi-hop, and unguarded-query evaluation.
6. Provide exact model IDs, seeds, prompts, templates, aliases, editor configs, judge details, software, hardware, and scripts.

### P2 — Nice to Have

1. Add a one-panel pipeline diagram and short pseudocode.
2. Move the failed replay audit and extended provenance discussion to the appendix.
3. Add representative success, permissive false-positive, strict reversion, and intervention cases.
4. Enlarge Figure 1 labels, shorten captions, and reduce footnote density.

## 9. One-week Emergency Revision Plan

**Day 1:** Freeze the estimand, primary endpoints, pool rule, and multiplicity plan. Rebuild the pool with the corrected matcher and audit every inclusion.  
**Day 2:** Rerun the six-checkpoint B0/B3 headline plus identical unedited controls; compute the formal interaction and alternative-pool sensitivities.  
**Day 3:** Replicate the gap under MEMIT or another editor and on the most feasible second dataset; launch repeated-seed runs.  
**Day 4:** Complete blinded semantic annotation of all primary cases or a powered stratified sample; reconcile permissive, strict, and semantic outcomes.  
**Day 5:** Run equal-length filler and realized-chain-length analyses; repair row/provenance anomalies and regenerate canonical tables.  
**Day 6:** Redo the statistical hierarchy, event-count tables, and uncertainty reporting; cut claims that fail the clean analysis.  
**Day 7:** Rewrite the abstract, Section 3.1, discussion, and conclusion; assemble the anonymized supplement, reproduce every number from scratch, and perform final template/visual checks.

If compute cannot complete Days 2-3 within the week, postpone submission. Do not replace the missing rerun with additional prose.

## 10. Final Direct Answer

1. **Can this paper be submitted to AAAI now?** No.
2. **What is the biggest risk if submitted now?** The headline pool is selected through B3 and built with a matcher known to be faulty at inclusion time; reviewers can reasonably treat the central effect as population-dependent or biased.
3. **What is the most likely reason for low scores?** The paper makes a general reasoning-time editing claim without a clean population, matched edited-versus-unedited interaction, semantically reliable primary endpoint, or independent gap replication.
4. **Which experiment group should be added first?** A corrected-matcher, arm-independent pool rerun of the complete six-checkpoint headline, including formal edited-versus-unedited interactions and full/alternative-gate sensitivities.
5. **Which section should be rewritten first?** Section 3.1, “Protocol and Metrics.” The population, estimand, gates, endpoints, missingness, and confirmatory tests must be unambiguous before rewriting the abstract.
6. **What score pattern does the current version look like?** **5456** for Technical / Experiments / Novelty / Writing.
7. **After one serious revision, what is the highest realistic score pattern?** **6767**, if the clean-pool result survives, semantic validation succeeds, and the headline gap replicates independently. Without that, the ceiling remains approximately **6566**.
8. **Should the paper be split into main paper + appendix?** Yes. Keep the clean headline analysis, primary event counts, interaction, and key intervention controls in the main paper; move failed replay details, full audit trails, extra dose/transfer analyses, and exhaustive configurations to the appendix.
9. **Should the authors continue targeting AAAI or redirect to another venue?** Continue targeting AAAI only after the P0 reruns succeed. If they do not, reframe the work around the narrower diagnostic result and target a focused knowledge-editing or LLM-evaluation venue; sending the unchanged draft elsewhere will not solve the validity problem.
