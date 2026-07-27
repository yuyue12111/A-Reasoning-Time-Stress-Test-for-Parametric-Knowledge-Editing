# AAAI-style Simulated Review Report 1 

_Unofficial assessment based on the rendered [main.pdf](/Users/whyu/GitProjects/why-aaai27/paperwriting/manuscript/main.pdf), manuscript source, [results.json](/Users/whyu/GitProjects/why-aaai27/paperwriting/results.json), current supplementary/checklist files, and repository implementation. No external literature search was used._

## 0. Paper Summary

The paper evaluates whether ROME knowledge edits that succeed under direct answering remain effective when R1-distilled models generate a native reasoning chain. Across six checkpoints, the largest Qwen and Llama models show approximately 0.106–0.107 drops in edit success; a think-span-only token-suppression intervention partly restores edited answers without directly modifying answer-stage logits. The main contribution is a paired reasoning-time stress-test protocol and a controlled intervention showing that the reasoning span is a causal control point, not a demonstrated natural-chain mechanism.

## 1. Title / Abstract / Main Paper Consistency Check

### Title Promise

The title promises evidence that direct-answer edit success is insufficient and introduces a reasoning-time stress test. That promise is substantially supported.

### Abstract Claims

The abstract claims:

- Six fixed checkpoints from two R1-distilled families.
- Qwen-32B and Llama-70B edit-success drops of 0.106 and 0.107.
- Qwen-32B permissive old-answer resurfacing of 19.3% and strict displacement of 9.2%.
- No detectable comparable drift in the unedited base model.
- A chain-local intervention that improves edit success from the placebo level while leaving answer-stage logits directly untouched.
- Signed, dose-graded behavior and near-null controls.

The reported numerical values match the manuscript’s result ledger.

### Main Paper Support

The main paper supports the central phenomenon and intervention contrast:

- Both largest checkpoints have cellwise unadjusted confidence intervals excluding zero.
- The within-edit paired protocol and one-case-at-a-time restoration are appropriate.
- The five-arm intervention provides untreated, treatment, reverse-sign, placebo, and same-relation comparisons.
- The failed 9/18 replay gate is disclosed, and the paper does not claim successful natural mediation.
- Strict and permissive reversion metrics are separated.

### Mismatches

1. **The target population is materially underdescribed.** The experiments use a model-based prefiltered CounterFact subset, not an ordinary CounterFact sample. [src/prefilter.py](/Users/whyu/GitProjects/why-aaai27/src/prefilter.py) retains cases for which the unedited Qwen-7B model at B3 already generates the old value; the same subset is reused across all checkpoints. The abstract and main paper only say “CounterFact.” This selection is directly related to the reversion phenomenon and can inflate old-answer availability.
    
2. **“Dose-graded” is too strong.** Only the chain-leakage manipulation check decreases monotonically with penalty strength. Edit success and permissive reversion are explicitly not ordered across penalty values.
    
3. **“Near-null controls” exceeds the statistical result.** The control contrasts are compatible with zero, but no equivalence margin was tested.
    
4. Section 5.3 states that neither control “moves the answer” and leaves endpoints unchanged, then correctly says the estimates are merely compatible with zero. These claims contradict each other.
    
5. “Causal diagnosis” sounds stronger than the evidence. The intervention demonstrates steerability/localization, while natural-chain mediation remains unidentified.
    

## 2. Reviewer 1 — Technical Soundness

### Summary

The paired experimental design is technically thoughtful, and the intervention establishes that changing the think span can alter the later answer without directly penalizing answer-stage logits. However, the undisclosed sample construction changes the estimand, important model-specific implementation details are missing, and the intervention does not isolate a semantic mechanism.

### Strengths

- Clear separation of generative edit success from EasyEdit’s logit-based rewrite accuracy.
- Same edit evaluated across reasoning budgets before restoration.
- Paired case-level analysis reduces between-edit confounding.
- Strict reversion is distinguished from a permissive lexical detector.
- Reverse-sign, placebo, and same-relation controls strengthen the intervention result.
- The failed mediation gate is reported rather than reinterpreted as success.
- Claims about model scaling are appropriately limited to six observed checkpoints.

### Weaknesses

#### Fatal Issues

1. **Undisclosed outcome-related sample selection.** The Qwen-7B/B3 old-recall prefilter conditions the dataset on behavior closely related to the principal outcome. Reusing this model-dependent subset for Qwen-32B and the Llama lineage also complicates cross-model interpretation. The present “on CounterFact” wording is materially misleading.
    
2. **The current supplement cannot support reproducibility claims.** The source [supplement.tex](/Users/whyu/GitProjects/why-aaai27/paperwriting/manuscript/supplement.tex) remains a placeholder skeleton, while the existing compiled supplement is an older one-page version.
    

These are rejection-level issues if unchanged, although neither implies that the reported numerical contrasts are fabricated.

#### Major Issues

1. The six checkpoint intervals are cellwise and unadjusted. Foregrounding the two significant largest-model cells is not protected by the statement that all cells were fixed.
    
2. Penalizing every selected alias first-token ID at every reasoning timestep is not sequence-conditioned semantic suppression. Token collisions or unrelated uses can be affected.
    
3. “Answer logits untouched” should be stated as “no direct answer-stage penalty.” Modified reasoning necessarily changes the hidden state and therefore later answer logits indirectly.
    
4. The placebo matches character length and frequency but not expected token activation, baseline probability mass, or intervention exposure. The competitor arm is rarely active in some transfer audits.
    
5. The native-chain condition has an 8192-token cap and harness-managed closure, but termination rates, forced closures, and realized lengths are not reported. The canned-thought experiment is also not length-matched.
    
6. Exact edit layers, layer-selection rules, clamp values, BOS differences, dtype differences, complete ROME/MEMIT hyperparameters, and model-specific deviations are deferred to a supplement that does not yet provide them.
    
7. The route taxonomy is outcome-conditioned, produced with one judge-model family, and lacks an independent human audit. The exact judge-model version is **Not sufficiently specified in the provided material**.
    
8. The permissive reversion detector has only 0.48 precision in the available judged subset. It should not carry equal rhetorical weight with the 0.92-precision strict endpoint.
    

#### Minor Issues

- “Causal diagnosis” should be “causal intervention” or “causal probe.”
- The 23/23 cloze result is selected, uncontrolled, nearly expected after a successful ROME edit, and missing its per-item artifact.
- MEMIT is used without a foundational citation.
- “Same protocol” obscures model-specific loading and editing differences.

### Questions for Authors

1. What exact population does the prefiltered dataset represent, and why was a Qwen-7B/B3 recall gate used for every checkpoint?
2. Do the Qwen-32B and Llama-70B gaps persist in an unfiltered or selection-independent CounterFact sample?
3. Which checkpoint comparisons were confirmatory, and how is multiplicity handled?
4. How many B3 generations self-terminated versus required harness closure?
5. How often did each control actually alter a selected token logit or generated token?
6. What are the complete model-specific ROME/MEMIT layers and hyperparameters?
7. What exact judge model and version produced the route and metric audits? **Not sufficiently specified in the provided material.**
8. Which placebo derivation is authoritative: the reported \(n=199\) arm or the reproducible \(n=200\) reconstruction?

### Required Fixes

- Disclose the prefilter in the abstract, data section, tables, and limitations; redefine all claims as conditional on that subset.
- If submission is deferred, add an unfiltered or stratified sensitivity analysis.
- Replace mechanistic language with a chain-local steerability claim.
- Add a complete model-by-model implementation table.
- Report B3 termination and realized-length statistics.
- Foreground strict reversion and clearly label permissive reversion as noisy.
- Reconcile and document the authoritative placebo artifact.

### Rating

Rating: **4 / 10**  
Confidence: **4 / 5**

### Score Justification

The core intervention contrast is credible and technically interesting, but the hidden population restriction directly affects interpretation of the headline phenomenon. Mechanistic language also remains stronger than the token-level intervention warrants.

### Why Not Higher?

A score above 5 would require a correctly defined target population, complete implementation details, and either a stronger intervention-exposure analysis or more conservative mechanistic claims.

### Why Not Lower?

The within-edit protocol, restoration discipline, paired statistics, signed intervention, and candid failed gate provide real technical substance. The evidence does not indicate that the central numerical contrast is erroneous.

## 3. Reviewer 2 — Experiments & Reproducibility

### Summary

The experimental program is more disciplined than the current submission package suggests: paired cases, frozen arms, restoration, case-clustered bootstrap intervals, and several negative results are handled carefully. Nevertheless, the present package is not reproducibility-ready, and the main phenomenon remains narrow and potentially selection-amplified.

### Strengths

- One-edit-at-a-time evaluation with mandatory restoration.
- Fixed sample sizes and paired case-level estimation.
- Six observed checkpoints are all reported, including null-compatible cells.
- The Qwen-32B result includes an unedited-base comparison.
- Three fixed sampling seeds support robustness to those particular seeds.
- The MEMIT and paraphrase studies are reported with important negative qualifications.
- The replay gate was preregistered and its failure honored.
- Numerical checks against the result ledger pass; no main-paper transcription error was found.

### Weaknesses

#### Fatal Issues

1. **The data-generating procedure is absent from the paper.** Reviewers cannot properly interpret the effect size without knowing that cases were selected using unedited Qwen-7B/B3 old-answer recall.
    
2. **The supplementary and checklist package is currently inconsistent.** The supplement is a stale one-page skeleton. Several “yes” answers in [ReproducibilityChecklist.tex](/Users/whyu/GitProjects/why-aaai27/paperwriting/manuscript/ReproducibilityChecklist.tex) promise code, run counts, hyperparameters, preprocessing details, and appendices that are not present in the reviewed package.
    

#### Major Issues

1. Only two of six checkpoint gaps have cellwise intervals excluding zero; no global or multiplicity-aware test is reported.
    
2. The headline gap uses one dataset and ROME. MEMIT shows intervention transfer but does not cleanly reproduce a statistically separated untreated reasoning gap.
    
3. The two model lineages share an R1 teacher/recipe, limiting claims of independent replication.
    
4. The primary placebo result is not byte-reproducible from retained shards: the paper reports \(n=199\), while available shards yield \(n=200\). Primary T–P conclusions survive, but one secondary P–N CLR conclusion changes qualitatively.
    
5. The Qwen-32B permissive reversion headline relies on a low-precision lexical matcher. Judge validation covers only 87/120 selected cases; 33 rate-limited cases are non-randomly missing.
    
6. The three-seed experiment uses fixed seeds and has one case missing all three B3 endpoints. It does not justify population-wide claims over sampling randomness.
    
7. Paraphrase construct validity is weak: only 30/40 audited strings passed the combined validity criteria, only 11/20 cases had both paraphrases valid, and agreement was moderate. No valid-only reanalysis is supplied.
    
8. General-benchmark cost estimates have intervals wider than the proposed equivalence gate, so absence of material cost is not established.
    

#### Minor Issues

- Hardware, software, dtype, BOS, and model-template differences are scattered rather than tabulated.
- The exact runtime environment and judge-model version are unavailable.
- Run-level seeds and provenance are promised rather than presently delivered.
- B0 edit success of approximately 0.50–0.625 is itself modest and should be contextualized.
- The Llama headline excludes 13 directionally degenerate rows, although the unfiltered sensitivity remains supportive.

### Missing Experiments

In priority order:

1. **Selection-independent sensitivity:** repeat the headline B0-to-B3 estimand on an unfiltered CounterFact sample, or stratify a frozen sample by whether it passes the Qwen-7B/B3 prefilter.
2. Second benchmark × second editor replication of the untreated reasoning gap.
3. Matched parent-versus-R1-distilled comparison to isolate the effect of reasoning post-training.
4. Length- and compute-matched chain control.
5. Intervention-exposure analysis showing how often T, P, and C are actually active.
6. Independent human or distinct-model validation of strict/permissive reversion and route labels.
7. Non-counterfactual corrective edits, since CounterFact makes the “old” answer true.

Given the current deadline and frozen scientific queue, these should not be improvised now. The first experiment is the priority if the submission is deferred.

### Reproducibility Concerns

- The current supplement does not contain the promised missingness table, regressions, replay-gate table, endpoint list, run counts, hyperparameters, or supplementary figures.
- The exact prefiltered dataset is not part of the reviewed package.
- The placebo arm has unresolved \(n=199\) versus \(n=200\) provenance.
- The judge-model version was not recorded.
- The B3 cap, forced-closure logic, and realized lengths are not reported.
- The compiled checklist is stale relative to the current source.
- Several results depend on raw server artifacts not present locally.

### Questions for Authors

1. How many raw CounterFact cases were examined and retained by the prefilter?
2. Were any checkpoint results examined before deciding to reuse that prefiltered subset?
3. Why should a Qwen-7B-conditioned subset define the Llama target population?
4. What is the family-wise interpretation of six unadjusted checkpoint intervals?
5. Can the \(n=199\) placebo arm be reconstructed exactly?
6. What proportion of B3 generations were truncated or manually closed?
7. What exact environment and judge versions are required for reproduction?
8. Why was no valid-only paraphrase analysis performed?

### Required Fixes

- Complete and recompile the supplement using existing audited evidence.
- Align every checklist answer with artifacts that actually exist.
- Disclose the complete selection procedure and denominators.
- Resolve or explicitly bound the placebo provenance discrepancy.
- Add full hyperparameter, seed, environment, and run-ledger tables.
- Add multiplicity-aware reporting or label checkpoint comparisons exploratory.
- Move strict reversion ahead of permissive reversion in interpretation.

### Rating

Rating: **5 / 10**  
Confidence: **5 / 5**

### Score Justification

The experiments are carefully executed and unusually candid, but the current paper/package prevents a reviewer from reconstructing the target population or the full protocol. The evidence supports a conditional phenomenon and intervention, not the broad generalization implied by “on CounterFact.”

### Why Not Higher?

The paper lacks selection-independent validation, a clean second-editor replication of the untreated gap, a complete supplement, and exact placebo provenance.

### Why Not Lower?

The central numbers are internally consistent, the paired design is strong, negative gates are reported honestly, and most major conclusions are already bounded more carefully than in a typical submission.

## 4. Reviewer 3 — Novelty, Significance & Related Work

### Summary

The qualitative observation that reasoning can undo an edit has close precedent acknowledged by the manuscript. The more distinctive contributions are the within-edit B0-to-native-chain estimand and the signed think-span intervention whose answer stage is not directly penalized.

### Strengths

- The paper does not present the qualitative phenomenon as wholly unprecedented.
- The paired estimand is cleaner than cross-model or single-budget evidence.
- The intervention battery is more informative than a single suppression arm.
- Failed natural mediation is disclosed and not converted into a positive claim.
- The topic is relevant to knowledge editing, reasoning-model evaluation, and test-time control.

### Weaknesses

#### Fatal Issues

No unconditional fatal novelty defect is established.

If this is submitted to an AI Alignment track, however, the track contribution is **Not sufficiently specified in the provided material**. The manuscript demonstrates suppression of the true CounterFact value in favor of a counterfactual edit. Its relevance to verified correction, unlearning, or safety maintenance is argued only by symmetry, not empirically demonstrated.

#### Major Issues

1. The manuscript itself cites close evidence that an R1-distilled model can reason back to outdated knowledge. Therefore, the observed failure mode is not the primary novelty.
    
2. The novelty argument relies on the conjunction that prior work has not combined all four properties. A feature checklist is weaker than identifying a new scientific conclusion enabled by the combination.
    
3. The mechanistic contribution is limited. Cloze evidence is uncontrolled, the route census is observational, and the replay mediation gate failed.
    
4. Think-span token suppression may be perceived as a straightforward span-restricted form of known decoding intervention. Positioning against broader reasoning-trace control and representation-steering work is incomplete.
    
5. Generality is narrow: one benchmark, one headline editor, two lineages sharing one teacher/recipe, and an edit-aware suppressor requiring aliases of the old value.
    
6. The scaling story is intentionally withdrawn: no ordered size trend is supported. This removes what might otherwise have been a stronger significance claim.
    

#### Minor Issues

- MEMIT lacks its foundational citation.
- Residual-old-knowledge work is discussed partly in the results rather than properly integrated into Related Work.
- “Signed, dose-graded” overstates the dose evidence.
- Generative evaluation and lexical-scoring validity need fuller positioning.
- “Symmetric results” can sound like independent replication despite the shared teacher/recipe.

### Novelty Assessment

- Reasoning-induced edit failure: **low novelty**.
- Residual old knowledge after editing: **low novelty**.
- Within-edit B0-to-native-chain stress test: **moderate methodological novelty**.
- Signed, think-span-only intervention: **moderate novelty and the strongest contribution**.
- Established natural-chain mechanism: **not demonstrated**.
- Overall: a careful new evaluation and causal-probe configuration, not a new editor, theory, benchmark, or established mechanism.

### Related Work Gaps

Without external literature search, specific missing papers cannot be named. Missing directions include:

- Reasoning-trace intervention and controlled decoding.
- Activation or representation steering during reasoning.
- Generative knowledge-editing evaluation and automatic-scoring validity.
- Residual-knowledge and superficial-edit mechanism studies.
- Persistence of correction or unlearning under reasoning, especially for an alignment-track submission.
- Foundational attribution for MEMIT.

### Significance Assessment

Significance is moderate for the general AAAI community: the stress test demonstrates that direct-answer evaluation can miss a practically relevant failure.

Significance is weaker for an alignment track because the demonstrated task suppresses a true old fact in favor of a counterfactual target. A symmetric safety motivation is plausible but not experimentally established.

### Questions for Authors

1. What exact conclusion is new relative to the closest reasoning-aware editing evaluation cited by the paper?
2. Is the primary novelty the paired estimand, the intervention, or their combination?
3. What reasoning-control work has previously confined interventions to the think span? **Not sufficiently specified in the provided material.**
4. What makes the proposed guard more general than alias-conditioned logit suppression?
5. Why retain “causal diagnosis” after the mediation gate failed?
6. If targeting alignment, what evidence supports an alignment use case beyond analogy?
7. Why is MEMIT used without its originating citation?

### Required Fixes

- Rewrite the novelty claim around the paired estimand, think-versus-answer-span contrast, and bounded transfer.
- Explicitly state that the qualitative failure phenomenon and residual old knowledge are precedented.
- Add a compact closest-work comparison.
- Cover reasoning-control, steering, evaluation-validity, and relevant correction/unlearning directions.
- Replace “dose-graded” with “signed, span-restricted.”
- Use “causal control point” or “causal probe,” not natural mechanism.
- Add a narrow alignment relevance paragraph only if submitting to that track.

### Rating

Rating: **5 / 10**  
Confidence: **4 / 5**

### Score Justification

The paper has a useful methodological contribution and a credible intervention result, but the qualitative phenomenon has close precedent, the mechanism remains unresolved, and empirical generality is narrow.

### Why Not Higher?

A 6 or 7 would require clearer distinction from reasoning-control work, broader evidence, or a successfully identified mechanism.

### Why Not Lower?

The paired stress test is rigorous, and the signed span-restricted intervention provides genuinely informative causal evidence beyond ordinary direct-answer benchmarking.

## 5. Reviewer 4 — Writing, Structure & Compliance

### Summary

The manuscript is technically dense but mostly coherent, and its limitations section is unusually candid. The main visual result is difficult to read, several sentences overstate null or dose evidence, and the supplementary/checklist package is not synchronized with the manuscript.

### Strengths

- Title is precise and appropriately narrower than a new-editing-method claim.
- The main PDF contains seven content pages plus a reference-only eighth page, with no visible clipping.
- No undefined references, overfull boxes, Type-3 fonts, or unembedded fonts were found.
- No visible author identity or revealing PDF metadata was found.
- Tables 1 and 3 are information-dense but interpretable.
- Limitations and ethics discussions are substantive.
- The failed replay gate and noisy metrics are disclosed rather than hidden.

### Weaknesses

#### Fatal Issues

1. **The supplementary material is unfinished.** The source is explicitly a skeleton, and the compiled version is stale and only one page. This leaves numerous promises in the main paper undischarged.
    
2. **The reproducibility checklist overstates current artifact availability.** Several “yes” answers are not supported by the files presently supplied.
    
3. If submitted to an alignment track, the manuscript lacks a clear, current track-relevance argument. **Not sufficiently specified in the provided material.**
    

#### Major Issues

1. Figure 1 is materially undersized. At normal page scale, model labels overlap, panel headings are cramped, and internal text is extremely small.
    
2. The abstract’s “dose-graded” and “near-null controls” wording exceeds the main-paper evidence.
    
3. Section 5.3 contradicts itself by stating that controls do not move the answer, then acknowledging that equivalence was not established.
    
4. The prose frequently reads like a response to anticipated reviews: caveat stacking, repeated scope disclaimers, and compressed defensive sentences reduce readability.
    
5. Critical protocol information is pushed to a supplement that does not contain it.
    
6. Table 3 is first discussed before its placement on the next page, increasing navigation burden.
    
7. The MEMIT citation omission is a visible scholarly-compliance problem.
    

#### Minor Issues

- The large footnote on page 2 is dense and disruptive.
- Several captions attempt to carry methods, caveats, and interpretation simultaneously.
- “We claim none,” “carries nothing here,” and similar formulations are rhetorically sharp but stylistically uneven.
- The references-only page has substantial unused space, suggesting that layout could be redistributed.
- There is no basis to infer AI authorship. However, the repetitive caveat-heavy style may feel machine-polished or rebuttal-driven; that is a writing issue, not evidence about authorship.

### Structure Problems

- The hidden sample-selection procedure belongs in Section 3.1, not only in future supplementary provenance.
- Intervention construction and causal interpretation are interwoven; the claims would be clearer if implementation, estimand, results, and interpretation were separated.
- The failed mediation gate should appear earlier in the causal-diagnosis narrative.
- Critical strict-metric results should precede the lower-precision permissive result.

### Writing Problems

- Replace categorical null language with “compatible with zero.”
- Replace “dose-graded” with “penalty-strength ladder” or “monotone leakage manipulation check.”
- Replace “causal diagnosis” with “causal intervention evidence.”
- Shorten long sentences carrying result, caveat, and defense simultaneously.
- Avoid repeatedly telling reviewers what the paper does not claim; state the positive claim once and delimit it precisely.

### Figure / Table / Algorithm Quality

- **Figure 1:** unacceptable at current size; redesign or use full-column width with simplified labels.
- **Table 1:** strong, but should identify the prefiltered target population in the caption.
- **Table 3:** statistically informative; distinguish unadjusted contrasts and null compatibility more visibly.
- **Algorithm:** no standalone algorithm is required, but pseudocode for the think-span intervention would materially improve reproducibility.

### AAAI Compliance Risks

- Formal year-specific AAAI policy compliance was not externally verified.
- No obvious anonymity leak was found.
- Main-page overflow was not observed.
- Current supplement/checklist synchronization is a serious package risk.
- Citation completeness is not adequate because MEMIT lacks its foundational reference.
- Ethics and limitations are present.
- If the selected track requires explicit alignment relevance, the current paper does not provide it.

### Questions for Authors

1. Which compiled supplement and checklist are intended for upload?
2. Why are artifact-availability questions marked “yes” when the current supplement is a skeleton?
3. Can Figure 1 be understood when printed at actual size?
4. Why state that controls do not move the answer without an equivalence test?
5. Why is the prefilter omitted from the data section?
6. What is the intended AAAI track, and where is its relevance established?

### Required Fixes

- Finish and recompile the supplement and checklist.
- Redesign Figure 1.
- Correct abstract and Section 5.3 overstatements.
- Add the prefilter to Section 3.1 and every population-level caption.
- Add the MEMIT citation.
- Conduct a final source/PDF synchronization and anonymity audit.
- Add a concise track-fit paragraph if needed.

### Rating

Rating: **4 / 10**  
Confidence: **5 / 5**

### Score Justification

The main text is scientifically serious, but the actual submission package is incomplete, the central figure is not publication-quality, and several visible wording inconsistencies undermine trust.

### Why Not Higher?

A reviewer cannot ignore a placeholder supplement, unsupported checklist answers, an unreadable principal figure, and a materially omitted sampling procedure.

### Why Not Lower?

The main PDF is otherwise polished, numerically consistent, anonymous, technically legible, and unusually candid about limitations.

## 6. Score Summary Table

|Reviewer|Role|Rating / 10|Confidence / 5|Main Positive|Main Negative|
|---|---|---|---|---|---|
|R1|Technical Soundness|4|4|Strong paired intervention design|Undisclosed outcome-related prefilter|
|R2|Experiments & Reproducibility|5|5|Disciplined paired experiments|Incomplete package and narrow validation|
|R3|Novelty & Related Work|5|4|Distinctive think-span causal probe|Close precedent and unresolved mechanism|
|R4|Writing & Compliance|4|5|Candid, numerically coherent manuscript|Skeleton supplement and poor Figure 1|

- **Average Rating:** 4.50
- **Median Rating:** 4.50
- **Lowest Rating:** 4
- **Highest Rating:** 5
- **Clear champion:** No
- **Strong reject voice:** Functionally yes: R1 and R4 are firm rejection voices. There is no calibration-level 1–3 score, but either reviewer could anchor a reject decision.

## 7. SPC/AC-style Meta-review

### Overall Assessment

This is a careful paper with a memorable stress-test setup and a potentially publishable think-span intervention. Its current presentation, however, overstates the population being studied and does not deliver the supplementary evidence needed to evaluate reproducibility. The panel would likely converge below the acceptance threshold.

### Consensus Strengths

- Clean within-edit B0-to-chain comparison.
- One-edit-at-a-time restoration.
- Strong signed and placebo intervention battery.
- Transparent reporting of failed mediation.
- Numerical consistency and careful separation of strict and permissive metrics.
- Appropriate restraint about scaling.

### Consensus Weaknesses

- Undisclosed Qwen-7B/B3 old-recall prefilter.
- Only two of six unadjusted checkpoint intervals exclude zero.
- One dataset and one headline editor.
- No established natural-chain mechanism.
- Low-precision permissive headline metric.
- Incomplete supplement and inconsistent checklist.
- Weak Figure 1 legibility.
- Incremental novelty relative to close cited work.

### Main Disagreement

The likely positive reviewers would emphasize the clean paired estimand and think-span intervention. Negative reviewers would argue that the selection procedure prevents a valid CounterFact-level interpretation and that the intervention demonstrates oracle steerability rather than a general mechanism or practical repair.

### Fatal Issues

1. The target population is described incorrectly or incompletely.
2. The supplement/checklist package is unfinished.
3. Conditional on an alignment-track submission, track relevance is not established.

### Fixable Issues

- Exact prefilter disclosure and conditional claim rewriting.
- Supplement and checklist completion.
- Figure 1 redesign.
- Removal of “dose-graded,” categorical-null, and mechanistic overstatements.
- Hyperparameter, environment, provenance, and judge documentation.
- MEMIT citation and related-work repositioning.

Selection-independent validation is fixable only if there is time for a proper new experiment; it should not be improvised immediately before submission.

### Rebuttal Potential

**Low after submission.** A rebuttal cannot credibly replace a missing supplement, undisclosed sampling frame, or absent sensitivity experiment. Potential becomes **Medium** only if these are corrected before reviewers see the paper.

### Phase-2 / Discussion Potential

**Weak.** There is no clear champion, and two independent reject rationales exist: scientific population validity and submission-package incompleteness.

### Final Decision Recommendation

**Likely Reject**

### Final AAAI Readiness Score

**46 / 100**

## 8. Priority Revision Plan

### P0 — Must Fix Before Submission

1. Disclose the exact Qwen-7B/B3 prefilter and redefine the estimand everywhere.
2. Remove broad “on CounterFact” language unless explicitly qualified.
3. Complete and compile the supplement from existing audited results.
4. Make the checklist match the artifacts actually supplied.
5. Redesign Figure 1 at readable scale.
6. Replace “dose-graded,” “near-null,” and categorical control-null statements.
7. Resolve or fully disclose the \(n=199\)/\(n=200\) placebo provenance issue.
8. Add complete model-specific hyperparameters and B3 termination details.
9. Add the missing MEMIT citation.
10. If targeting alignment, add a narrow evidence-bounded relevance paragraph; otherwise use the main-track framing.

### P1 — Strongly Recommended

- Add multiplicity-aware or global reporting for the six checkpoint cells.
- Foreground strict reversion; demote permissive reversion.
- Add a closest-work comparison table.
- Clarify that answer-stage logits are not directly penalized.
- Report control-intervention exposure.
- Separate intervention evidence from mechanism claims.
- Add judge prompts, missingness, and all available model/version provenance.
- Include the paraphrase validity limitations and lack of valid-only reanalysis prominently.

### P2 — Nice to Have

- Unfiltered/stratified CounterFact sensitivity.
- Second benchmark × second editor.
- Matched parent-versus-distilled comparison.
- Length-matched reasoning control.
- Independent human metric/route audit.
- Non-counterfactual corrective-edit evaluation.

## 9. One-week Emergency Revision Plan

**Day 1 — July 27:** Rewrite Section 3.1 and the abstract around the actual prefiltered population. Remove unsupported “dose-graded,” “near-null,” and categorical-null language. Redesign Figure 1.

**Day 2 — July 28:** Run the manuscript checker, compile from clean sources, perform visual/anonymity inspection, and submit the main paper only if every P0 main-text issue is closed. If the prefilter cannot be disclosed truthfully and clearly, defer.

**Day 3 — July 29:** Populate the supplement with existing missingness, regression, replay-gate, endpoint, and sensitivity tables.

**Day 4 — July 30:** Add complete hyperparameters, run ledger, B3 termination protocol, judge prompts/provenance, and the placebo discrepancy record.

**Day 5 — July 31:** Synchronize supplement, checklist, code/data manifest, and compiled PDFs. Verify every checklist “yes” against an actual artifact before upload.

**Day 6 — August 1:** Archive submitted hashes and prepare concise answers to likely questions about sample selection, multiplicity, permissive-metric precision, and mechanism scope.

**Day 7 — August 2:** Design the first post-submission or deferred experiment: selection-independent CounterFact sensitivity, followed by a second benchmark/editor replication.

## 10. Final Direct Answer

1. **Can this paper be submitted to AAAI now?**  
    **No.** The main scientific description omits the model-based sample prefilter, and the supplementary/checklist package is unfinished.
    
2. **What is the biggest risk if submitted now?**  
    A reviewer discovers that the headline population was selected for unedited Qwen-7B/B3 old-answer recall and concludes that “reasoning undoes editing on CounterFact” is selection-amplified or misleadingly scoped.
    
3. **What is the most likely reason for low scores?**  
    Incorrectly specified target population, followed by narrow generalization and incremental novelty—not writing quality alone.
    
4. **Which experiment group should be added first?**  
    An unfiltered or prospectively sampled CounterFact B0-to-B3 sensitivity, stratified by prefilter eligibility, at the headline checkpoints. Second priority is a second benchmark × second editor.
    
5. **Which section should be rewritten first?**  
    **Section 3.1, Data and Protocol.** Then update the abstract and introduction to match the corrected estimand.
    
6. **What score pattern does the current version look like?**  
    **4554**.
    
7. **After one serious revision, what is the highest realistic score pattern?**  
    **6666**, if the revision includes population-sensitivity evidence and a complete package. Document and prose fixes alone are more likely to produce approximately **5656**.
    
8. **Should the paper be split into main paper + appendix?**  
    **Yes, as main paper plus separate supplementary material.** The prefilter, core limitations, strict endpoint, and principal intervention evidence must remain in the main paper; detailed provenance and hyperparameters belong in the supplement.
    
9. **Should the authors continue targeting AAAI or redirect to another venue?**  
    Continue targeting AAAI only if all P0 issues are closed before upload. The paper currently fits the general technical track better than an alignment track. If the population disclosure and package cannot be completed, defer to a later venue rather than submit this version or make a last-minute venue change.


# AAAI-style Simulated Review Report 2
**Scope note:** unofficial, not affiliated with AAAI, not an acceptance predictor. Grounded only in `paperwriting/manuscript/main.tex` (310 lines), the compiled 8-page `main.pdf`, `refs.bib`, `supplement.tex`, and `ReproducibilityChecklist.tex`. No web search was run, so no specific missing papers are named — only missing directions. Line numbers refer to `main.tex`.

## 0. Paper Summary

The paper argues that standard parametric-knowledge-editing validation — ask the edited model the edited question — certifies edits under a condition (zero thinking) that deployed reasoning models never operate in. It evaluates each ROME edit on CounterFact twice, at a pre-closed empty think span (B₀) and after a native chain (B₃), one edit at a time with weight restore between requests, across six R1-distill checkpoints in two lineages. At the largest checkpoint of each family, paired generative edit success drops .106 [.030,.182] (Qwen-32B) and .107 [.032,.182] (Llama-70B); old answers resurface in 19.3% of already-successful edits on Qwen-32B. It then adds a logit penalty on the old value's first tokens **inside the think span only**, which raises edit success (+.138 vs no suppression) and halves resurfacing (19.3%→8.5%), against a matched placebo, a same-relation competitor, and a reverse-signed arm. A prospectively specified mediation experiment failed its own validity gate and the mediation claim is withdrawn.

## 1. Title / Abstract / Main Paper Consistency Check

### Title Promise

"Direct-Answer Edit Success Is Not Enough: A Reasoning-Time Stress Test for Parametric Knowledge Editing." Promises (a) a general inadequacy of direct-answer validation, and (b) a stress-test protocol as the deliverable.

### Abstract Claims

Six load-bearing claims: (1) ES drops .106/.107 at the largest checkpoint of each family; (2) 19.3% permissive resurfacing / 9.2% strict displacement on Qwen-32B; (3) "the unedited base shows no detectable old-answer drift"; (4) the edited association remains cloze-detectable and route analysis finds visible in-chain paths; (5) think-span suppression offsets the loss and lowers resurfacing 19.3%→8.5%; (6) "placebo and same-relation controls have near-null answer-level effects."

### Main Paper Support

Claims 1, 2, 5 are exactly supported — I verified them against Tables 1 and 3, and the arm-wise levels reconcile to attainable integer event counts (.595×200 = 119 gated cases; RR .193 = 23/119; RR<sup>s</sup> .092 = 11/119; ES .631×198 ≈ 125/198). Table 3's N arm (.495/.193) is byte-identical to Table 1's Qwen-32B cell, as line 250 claims. Table 2's census reconciles perfectly (27+11+3+0 = 41; 41+43+17 = 101; agreement 35×3+6×1 = 111/123). **The internal numeric hygiene of this paper is better than almost any submission I would expect to see.**

### Mismatches

Three, all in the direction of the abstract being stronger than the body:

- **Claim 3.** Abstract: "the unedited base shows no detectable old-answer drift." Body line 102: the paired interval "exists at this checkpoint only; the other five carry level differences without intervals, and those are not of one sign," and line 103: "we make no formal contrast." The abstract states as a general property what the body establishes at one checkpoint and explicitly declines to test.
- **Claim 6.** Abstract: controls "have near-null answer-level effects." Body line 255: "we set no equivalence margin, so they are not evidence of no effect." A reader of the abstract concludes specificity was demonstrated; the body says it was bounded, not demonstrated.
- **Title vs. Table 1.** The title's universal claim rests on 2 of 6 cells. Two cells (Qwen-1.5B, 7B) have _negative_ point estimates — edit success is **higher** after reasoning. The abstract's "At the largest tested checkpoint in each family" is a scope signal that a careful reader will decode and a skimming reviewer will not.

None of these is a misstatement. All three are the strongest defensible reading, and the body always retracts.

---

## 2. Reviewer 1 — Technical Soundness

### Summary

A carefully built measurement instrument attached to a claim it cannot quite carry. The protocol design — single edit applied and reverted, within-case pairing, generative rather than teacher-forced scoring, a primary contrast frozen with its donor list before any treated arm ran, byte-identity audits proving the B₀ rows are unaffected by a think-span processor — is materially better engineering than the editing literature's norm. The problem is the inferential step from "suppressing the old string in the chain changes the answer" to "a chain-local causal control point."

### Strengths

- The single-edit-then-restore loop with explicit non-contamination reasoning (line 66) is the right protocol and is stated precisely enough to reimplement.
- Conditioning reversion on B₀ success is argued to be **treatment-independent by construction** (line 212) — a think-scoped processor cannot act on an empty span — and then _verified empirically_ by byte-identity audits (600 B₀ probe rows, 0 differences). That is a real answer to the obvious collider objection, and most papers would not have thought to check.
- The five-arm design (none / old / new / matched placebo / same-relation competitor) with a reverse-signed arm is stronger than a two-arm ablation. The D arm moving both endpoints the other way (−.217 ES, +.086 RR) is genuine sign evidence.
- The scope ablation (line 210) is the right experiment to run against the tautology charge, even if it does not fully discharge it.

### Weaknesses

#### Fatal Issues

None that cannot be argued about. The tautology issue below is the closest.

#### Major Issues

**M1. The intervention penalizes the exact token strings whose presence/absence defines the endpoint.** ES = new alias present ∧ old alias absent; RR = old alias present. The T arm adds a logit penalty to the old value's alias first-tokens. The paper's defence (line 210) is three-part: different spans, a scope ablation, and leakage-as-manipulation-check. Part one is the weak link — an autoregressive model's answer is conditioned on its chain, so suppressing a string in the chain lowers its answer probability through ordinary context propagation. That is not the discovery of a control point; that is the definition of a language model. The scope ablation helps (answer-span penalty raises B₀ ES .580→.727, think-scoped leaves it untouched), and the competitor arm helps more. But the paper never closes the loop the cheap way: **it has a validated judge panel and never reports the T-vs-N contrast under the judge endpoint instead of the lexical one.** A semantic endpoint that moves under lexical think-span suppression would settle this in one table row.

**M2. What causal claim survives?** Line 261 concedes "every arm here is an intervened condition, so nothing shows the chain route is required in ordinary, uninterrupted generation." Combined with the withdrawn mediation claim (line 290), the paper establishes that intervening on chain content changes the answer — which is its own premise, not its finding. "Control point" is doing rhetorical work that "the chain is causally upstream of the answer, as expected" would do honestly.

**M3. B₃ is never numerically defined.** Line 66 states "Each budget caps the think span," and line 117 gives B₁ = 256 tokens. B₃ — the paper's central independent variable — has no stated cap anywhere in the paper. B₀P is "a fixed short canned thought," never quoted, never length-specified. The main experimental manipulation is not reimplementable from the manuscript.

**M4. Per-checkpoint edit layer is absent from the main text entirely.** ROME's edit layer is its single most consequential hyperparameter, and the paper's result pattern is "the two largest checkpoints behave differently from the four smaller ones." `supplement.tex` (lines 66–70) reveals layers were "empirically scanned on two checkpoints, set a priori by a fixed relative-depth rule on the others." That is a live confound for exactly the pattern being reported, and the main paper does not mention it exists.

**M5. ES_B₀ is .500–.625.** Under generative scoring, ROME "takes" on barely more than half the requests. Every reversion analysis conditions on that subset. The paper never discusses what a ~55% installation rate does to external validity, or whether the .106 drop is a distinct phenomenon or further decay of an edit that was marginal to begin with.

#### Minor Issues

- The case-sampling protocol is never stated in the body; "200" appears only in a caption and footnotes.
- "Locality is only a target-value non-leakage check on the neighbor answer" (line 70) — this is not locality in the sense the editing literature uses the word, and the paper is right to flag it, but a reviewer will note that no standard locality/portability metric is reported at all.
- Section 4.5's dose-limited concept-direction test is described but its endpoint "does not locate a distinct commitment layer" (line 196), leaving the reader unsure why it is in the main paper.

### Questions for Authors

1. What is B₃'s numeric token cap, and what exact string is B₀P?
2. Does the T-vs-N contrast survive when the answer is scored by your judge panel rather than by alias matching? You have the panel; this is the experiment that decides M1.
3. Which two checkpoints had layers empirically scanned, and what was the relative-depth rule for the rest? Were the two scanned checkpoints the two that show the effect?
4. How were the 200 CounterFact requests selected from the ~21k pool?
5. Is edit restore verified per-request (weight hash / logit check), or assumed from the harness?

### Required Fixes

State B₃ and B₀P numerically in §3.1. Move per-checkpoint layer selection into the main text with the scanned-vs-rule split disclosed. State the case-sampling frame in §3.1. Report a judge-scored T-vs-N row in Table 3. Soften "causal control point" to what line 261 permits.

### Rating

Rating: 5 / 10  
Confidence: 4 / 5

### Score Justification

The measurement apparatus is above the field's bar and the pre-registration discipline is real. But the paper's flagship inferential claim has an unresolved tautology exposure, its central independent variable is not numerically specified, and its most confounding hyperparameter is not mentioned in the main text.

### Why Not Higher?

The intervention's causal interpretation is not established, and the paper concedes as much at line 261. A soundness score above 5 requires that the headline mechanism claim be defensible; here the honest reading of the paper's own concessions is that it is not.

### Why Not Lower?

Nothing is wrong. The design is correct, the denominators are handled correctly (I checked every one), the collider risk is anticipated and empirically audited, and the arms are well chosen. This is a 5 because of what it fails to establish, not because of any error it makes.

---

## 3. Reviewer 2 — Experiments & Reproducibility

### Summary

Statistically careful to an unusual degree, and evidentially thin in exactly the places that decide acceptance: one dataset, one headline editor, one generation per headline cell, 2 of 6 cells significant, judges from a single model family with no human audit, a primary endpoint with .48 precision, and a supplement that does not yet exist.

### Strengths

- Paired case-bootstrap intervals throughout, complete-case discipline stated explicitly, and the repeated warning that paired changes need not equal differences of marginal levels (lines 94, 110, 250) — with the footnote at 250 doing the arithmetic to prove it (.495 + .138 ≠ .631).
- Every cell of the six is reported. No cherry-picking.
- The Llama-70B row discloses **both** the filtered (n=187, drop .107) and unfiltered (n=200, drop .110) analyses because "this filtering can be directional." That is the correct instinct and it is rare.
- The X1 replay gate failed 9/18 against a required 15, and the authors honored their own stop rule and withdrew the claim (lines 172–175, 290). This is the single most credible thing in the paper.

### Weaknesses

#### Fatal Issues

**F1. The supplement is an empty skeleton.** `supplement.tex` is 85 lines of section headings and one-to-three-sentence descriptions of what will eventually go in them. It contains no table, no figure, and no number. The main text defers to it in **eight** places, several load-bearing: the complete replay-gate table (line 177), the complete concept-direction endpoint set (line 195), hyperparameters and per-checkpoint edit layers (§S11), the judge-panel missingness pattern (line 72), the placebo arm's two derivations (line 257), the §3.3 regressions (lines 124–125), and both supplementary figures (line 278). One of its own comments concedes the stakes: _"A section that ships empty is a broken promise, not a formatting detail."_ As of today the submission is not self-contained, and Phase-1 has no rebuttal to repair it.

#### Major Issues

**F2. The endpoint that separates is unreliable; the endpoint that is reliable does not separate.** Permissive RR — which carries the abstract's 19.3%→8.5% — has available-case precision **.48** against the judge majority (lines 72, 266). Strict displacement has precision **.92** and gives T−N = −.051 [−.102, .000], p = .073 (line 266): it does not separate the treated arm from the untreated baseline in the main battery, and also fails under MEMIT (−.027, p = .400, line 274). The paper reports all of this at primary prominence, which is admirable, and it is still the finding a reviewer writes down.

**F3. Two of six cells, and two of the six point the other way.** Qwen-1.5B (−.026) and 7B (−.030) show edit success _higher_ after reasoning. I ran the multiplicity check a hostile reviewer would run: normal approximation from the reported intervals gives z = 2.73 (p ≈ .006) for Qwen-32B and z = 2.80 (p ≈ .005) for Llama-70B; Bonferroni across the 6-cell family leaves both at p < .05. **So the standard multiplicity attack fails and the authors should know that.** The residual critique is different and harder: the paper declines to claim a size trend (line 99), so it has two significant cells and no account of why those two, which leaves the contribution as a statement about two specific checkpoints.

**F4. One dataset, one editor, one generation.** CounterFact only. ROME headline; MEMIT enters only through a transfer run whose own fresh no-suppression arm gave an ES drop of +.060 [−.020,.140] — i.e. **no detectable reasoning-time gap in that cell**, so the intervention there repairs a gap that was not measured (line 274, honestly flagged). Headline cells are one greedy generation each; sampling robustness is three fixed seeds on one checkpoint.

**F5. Judge monoculture.** Both panels, the replay judges, and the paraphrase audit all use one external judge-model family (lines 72, 146), with no human-audited subsample (conceded, line 292). The validation panel returned votes for 87 of 120 items; 33 were lost to rate limits, concentrated in rule-negative rows. Every judge-derived quantity in the paper inherits this.

**F6. Self-admitted artifact failures.** Line 136: a required per-item artifact (`results/probe/logitlens_cf200_ROME_B3.jsonl`) is missing, so §4.1's 23/23 cannot be audited. Line 257: "The placebo arm is not byte-reproducible from the released shards." The placebo arm is the control in the **pre-specified primary contrast**. The paper argues the discrepancy moves quantities in the third decimal — likely true — but a reviewer reads "our primary contrast's control does not reproduce from our released data."

**F7. The paraphrase transfer is thin.** 30 of 40 paraphrases judged valid, 11 of 20 cases valid on both, κ = .444 — and "no row was filtered and no valid-subset re-analysis was run" (line 276). A +.055 [.020,.093] effect measured on a probe set with κ = .444 validity is not a transfer result yet.

#### Minor Issues

- Checklist 1.1 answers "yes" to "conceptual outline and/or pseudocode"; there is no algorithm environment or pseudocode anywhere. The "conceptual outline" reading is defensible via §5.1 prose, but the intervention deserves a 6-line algorithm block.
- Checklist 4.12 answers "yes" to appropriate statistical tests; the paper uses unadjusted bootstrap intervals and explicitly claims no multiplicity correction. Defensible, but a checklist auditor will pause.
- Table 2's A3 crosswalk (13 majority-OLD + 20 non-OLD = 33) does not visibly reconcile with the 41-instance census or the 101-item pool, and the relationship is not explained.

### Missing Experiments

1. **T-vs-N under the judge endpoint** (decides the tautology charge, §5.2). Uses an existing panel.
2. **A second dataset** — even 100 items from a non-CounterFact editing set, at one checkpoint.
3. **A length-matched content-free filler arm.** The paper names this gap itself (line 184: "an equal-length content-free filler remains untested") and it is the one experiment that would close the computational-buffer alternative it concedes at line 185.
4. **Realized chain-length audit under suppression** (line 186 concedes this was not done, which is why §4.4 constrains rather than eliminates the length account).
5. **A human-audited judge subsample** — 50 items would convert F5 from fatal to bounded.

### Reproducibility Concerns

Environment is anonymized to "Hopper-class"/"Ada-class" with a bfloat16→NaN workaround disclosed (line 296) — good. Lock file pinned and frozen. But: hyperparameters live only in an unwritten supplement; one artifact is missing; one arm does not byte-reproduce; and no code URL is present (correct for double-blind, but the checklist's "yes" answers depend entirely on the supplementary drop).

### Questions for Authors

1. When will the supplement have content, and which of the eight promises will it actually discharge?
2. Does the T-vs-N effect hold under the strict endpoint at any checkpoint other than Qwen-14B?
3. What fraction of the 33 missing judge votes were rule-positive?
4. Why is the MEMIT transfer presented as transfer when its own cell shows no gap to repair?
5. What is the sampling frame for the 200 cases, and is it fixed across all six checkpoints?

### Required Fixes

Ship the supplement with §S11 (hyperparameters/layers), the replay-gate table, and the concept-direction endpoint set at minimum. Add a judge-scored contrast row. Move F6's two artifact admissions into a single Reproducibility paragraph so they read as disclosure rather than as scattered concessions.

### Rating

Rating: 4 / 10  
Confidence: 4 / 5

### Score Justification

The statistics are handled correctly and the disclosure norms are exemplary, but the evidence base is one dataset, one editor, two significant cells, and a primary endpoint the authors themselves show is right 48% of the time — with the reliable endpoint failing to separate.

### Why Not Higher?

An accept needs the headline effect demonstrated on more than two checkpoints of one benchmark with one editor, and needs the reliable endpoint to move. Neither holds.

### Why Not Lower?

The analysis contains no error I could find, the pre-registered gate was honored at real cost, and every weakness above is disclosed by the authors rather than hidden. That is worth a point over a paper with the same evidence and worse manners.

---

## 4. Reviewer 3 — Novelty, Significance & Related Work

### Summary

The phenomenon is not new; the measurement of it is. The paper's own Related Work concedes that two cited works already observed editing failing under realistic decoding on reasoning models, including an R1-distilled checkpoint. What remains is a controlled paired design and a span-scoped decoding intervention. Both are real methodological contributions and both are incremental.

### Strengths

- The four-property delta at line 58 is honestly and precisely stated: budget-controlled paired contrast on one and the same edit; controls separating edit-specific erosion from base drift, canned thought, and sampling; symmetry at the largest checkpoint of two lineages; a signed dose-graded intervention confined to the think span. No prior work does all four jointly. That is a defensible novelty claim.
- Framing thinking budget as an _axis of edit evaluation_ rather than a confound is a genuinely useful reframe, and "evaluate the same edit twice" is the kind of protocol idea that gets adopted.
- The Ethical Statement's inversion — CounterFact edits overwrite true values, so every "reversion" is the model restoring a truth and the suppressor is a truth-silencing tool (line 305) — is the most intellectually honest ethics section I have read on an editing paper.

### Weaknesses

#### Fatal Issues

None.

#### Major Issues

**N1. The delta over cited prior work is methodological, not phenomenal.** Line 52 states that He et al. (2025) already "find parameter-based editing performs poorly there, including on an R1-distilled checkpoint whose reasoning reflects outdated knowledge and overturns the edit." Line 54 states that Huang et al. (2026) already observed "near-perfect teacher-forced accuracy alongside collapsing grounded success once the chain is examined." The paper's answer — prior evidence is "cross-model and single-configuration: it establishes that editing looks worse under realistic decoding, not how a single edit behaves as its own thinking budget changes" — is correct and is a refinement claim. A reviewer asks whether a refinement plus a 2-of-6 effect clears the AAAI bar.

**N2. MEMIT is used and never cited.** Verified: four textual mentions (lines 212, 259, 274, 286), zero `\cite` commands, no entry in `refs.bib`. The paper runs an entire transfer replication under an editing method it does not cite. This is trivially fixable and is exactly the signal reviewers read as scholarship quality.

**N3. Sixteen references.** For a knowledge-editing paper at a top venue this is thin, and the gaps are structural rather than cosmetic. Absent directions, described as families since I did not verify specific papers:

- Parameter-editing families beyond ROME/MEMIT (hypernetwork-based editors, memory- and adapter-based editors, fine-tuning-with-constraint baselines).
- Retrieval- and in-context-based editing as an alternative paradigm — engaged only via the one SCR citation.
- Multi-hop, ripple-effect, and portability benchmarks for edited knowledge.
- Survey and evaluation-critique literature on editing metrics — directly relevant to a paper whose thesis is that a metric is inadequate.
- **Chain-of-thought faithfulness / unfaithful-reasoning literature.** This is the most damaging omission. The paper's entire thesis is that the generated chain determines an answer in ways the answer-only probe cannot see; there is an established line of work on exactly whether and how chains determine answers, and it is absent. Section 4's route taxonomy (Bridge / Recall / Reflective-override / Associative) is a faithfulness taxonomy that does not cite the faithfulness literature.

**N4. The intervention is a known technique in a new place.** Span-scoped logit biasing / banned-token decoding is standard. The paper's own Related Work (line 56) lists three works that intervene on the answer distribution, and positions itself as "scoped to the think span." That is a genuine and clean distinction, but "same mechanism, different span" is a modest methodological claim on which to hang the paper's second contribution.

**N5. Section 4 costs ~1.5 of 7 pages and identifies nothing.** §4.1 is "close to tautological" with a missing artifact and "we place no quantitative weight on this observation downstream" (line 136). §4.2 "describes observed failures rather than a predictor or causal mediator" (line 148). §4.3's vehicle failed its gate and the mediation claim is withdrawn (line 175). §4.4 concludes the buffer account "remains a live alternative" (line 185). §4.5 "did not yield detectable confirmatory RR repair... and it does not locate a distinct commitment layer" (line 196). Every disclosure is right; the aggregate is a section titled "Causal Diagnosis" in which nothing is diagnosed, occupying the page budget §5 needs.

#### Minor Issues

- "Chain-routing hypothesis" is introduced (line 170) and never tested — by the paper's own account the test failed before it ran. Naming a hypothesis you cannot evaluate raises expectations you then have to withdraw.

### Novelty Assessment

**Moderate-incremental.** The paired budget-controlled protocol is the real contribution and it is new. The phenomenon is a sharpening of results already in the literature the paper itself cites. The intervention is a known decoding technique relocated to a new span, with an interesting but unresolved causal interpretation.

### Related Work Gaps

Five families listed in N3, plus the missing MEMIT citation. The Related Work section is well-written and does honest positioning against what it does cite — the problem is coverage, not framing.

### Significance Assessment

The protocol is the durable output: "evaluate the same edit at zero thinking and after a native chain, with restore between requests" is a recommendation the editing community could adopt tomorrow, and the paper makes it concrete. Against that, the paper positions the intervention as "a mechanistic probe and an edit-aware decoding guard, not a deployment-ready fix" (line 278), the mechanism is unidentified, and the effect is shown at two checkpoints. Who changes what they do after reading this? An editing-benchmark author adds a budget axis. That is a real but narrow consequence.

### Questions for Authors

1. Given lines 52 and 54, state in one sentence what a reader knows after this paper that they did not know after those two works.
2. Why is the chain-of-thought faithfulness literature absent from a paper about chains overturning answers?
3. Would §4 be stronger as three paragraphs plus supplement, with the reclaimed page spent on §5?

### Required Fixes

Cite MEMIT. Add the five missing related-work directions with real citations. Compress §4 hard. Make the protocol, not the phenomenon, the stated contribution in the Introduction.

### Rating

Rating: 4 / 10  
Confidence: 4 / 5

### Score Justification

A methodological refinement of a phenomenon the paper's own Related Work says was already observed, plus a known decoding technique in a new span, supported at two checkpoints, with a thin bibliography that omits the most on-point literature and the method it runs.

### Why Not Higher?

The novelty is real but sits at the level of "better measurement of a known effect." AAAI's bar for that requires the measurement to overturn something or to generalize broadly; here it does neither yet.

### Why Not Lower?

The paired-protocol idea is genuinely good and the positioning against prior work is honest rather than evasive — the paper does not pretend the phenomenon is new. That earns it a 4 rather than a 3.

---

## 5. Reviewer 4 — Writing, Structure & Compliance

### Summary

Compliant, anonymous, ethically thoughtful, honest to a degree I rarely see — and written in a register that will cost it points. The prose retracts part of nearly every claim in the same sentence that makes it. The result is a paper that is easy to trust and hard to read, with only one figure supporting two headline contributions.

### Strengths

- Format compliance is clean: 7 pages of technical content + 1 reference page (confirmed from `main.log`: "Output written on main.pdf (8 pages)"), AAAI-2027 style unmodified, `[submission]` option set, "Anonymous Submission."
- Ethical Statement (line 305) is specific, non-boilerplate, and correctly bounds its own zero-cell claim.
- Section 6 Limitations names six real limitations including the ones that hurt most (one editor, one dataset, lexical endpoints, unidentified mediation, judge monoculture).
- Table and figure captions are unusually informative — Table 1's caption discloses the n=187/n=200 filtering sensitivity inline, which most authors would bury.

### Weaknesses

#### Fatal Issues

None for compliance.

#### Major Issues

**W1. One figure for two contributions.** §5 — the chain-local control point, the paper's second headline claim and its only intervention — has no figure. The evidence ladder and five-arm forest are deferred to the supplement (line 278). I looked at the asset: `fig3_rq3_nature-skill.png` is a finished, publication-quality two-panel forest plot of all six arm contrasts with intervals, and it communicates §5.2–§5.3 better than Table 3 does. It is gated (per a comment in `supplement.tex`) on adding a strict-displacement panel — but all three RR<sup>s</sup> contrasts are **already in Table 3**, so that panel is a plotting change, not a new computation. This is the highest-value fix available in the time remaining.

**W2. §4.5 reports an entire experiment with no numbers.** Lines 194–196: "the pre-specified primary RR contrast was compatible with zero, even though the in-span CLR manipulation check fell; ES remained null-compatible. Against no steering, RR was null-compatible while ES was positive; a secondary concept-versus-shuffle contrast on the pre-specified LocAcc harm metric was negative. Each directional endpoint above has an interval excluding zero." Not one value. The final sentence appears to contradict the preceding ones unless the reader correctly infers that "directional endpoint" refers only to the non-null ones. A reviewer cannot evaluate this paragraph, and its destination — "The complete endpoint set is in the supplement" — is currently empty.

**W3. Hedge density.** Representative, all verbatim:

- "These are compatible with zero; we set no equivalence margin, so they are not evidence of no effect." (255)
- "That census is conditioned on reversion and is not a sample of unguarded use, so the zero bounds traceless reversion rather than excluding it; we do not claim that a trace is always present, and we do not claim that the absence of such a trace could serve as a monitor." (305)
- "Because these estimates come from separate runs with run-specific B₀ gates, we infer neither saturation nor an ordered trend." (184)
- "This juxtaposition is consistent with an edit-specific pattern, but the two quantities differ in event definition and denominator; we make no formal contrast." (103)

The first contribution bullet (line 41) is a single sentence carrying five clauses and three embedded caveats. That is where I would lose most reviewers, on page 1. My honest read: the epistemic discipline is a genuine virtue and a minority of reviewers will value it highly — but the cumulative effect is that a reader finishes §4 unable to state one positive finding, and finishes the paper unsure what was established. Much of this is fixable at zero cost to rigor by moving the caveat into a footnote or into §6 and letting the sentence assert.

**W4. Figure 1B mixes incommensurable quantities on one axis.** Three edit-success contrasts plus, "below a rule," the unedited base's ΔP(o_old) — "an outcome with a different event definition and denominator that is juxtaposed rather than contrasted" (line 110). The rule and the caption are an honest attempt to prevent the misreading, but placing a non-comparable quantity on a shared axis invites exactly the comparison the caption forbids. Either give it its own panel or drop it to the text.

#### Minor Issues

- Table 3's lower "Contrast" panel reuses the upper panel's column positions with different meanings (`main.tex` 224–244). I checked the rendered page 7: it reads acceptably, but ΔES sits under the _n_ column header, which briefly misleads.
- Line 136 exposes an internal path, `results/probe/logitlens_cf200_ROME_B3.jsonl`. Not a de-anonymization risk (no URL, no repo, no institution) — just unusual. Naming a missing file in a submission is more honest than most authors would be; I would keep it.
- `main.log` shows 10 underfull hboxes, no overfull. Cosmetic.
- CLR appears at line 70 with a definition, then not again until line 188 — a reminder gloss would help.

### Structure Problems

The page budget is misallocated: §4 (five subsections, ~1.5 pages) resolves nothing, while §5 (the intervention) has no figure and §3.1 (protocol) omits B₃'s cap, the layer selection, and the case-sampling frame.

### Writing Problems

See W3. Secondary: the Introduction's contribution bullets are the densest paragraphs in the paper, which inverts the usual guidance.

### Figure / Table / Algorithm Quality

Tables are excellent — well-captioned, correctly denominated, honest about which panel rests on which denominator. Figure 1 is clean apart from W4. No algorithm block exists despite the checklist's 1.1 "yes"; §5.1's intervention would fit in six lines of pseudocode.

### AAAI Compliance Risks

Page limit: compliant (7+1). Anonymity: compliant. Ethics statement: present and strong. Limitations: present and honest. Reproducibility checklist: filed, with three answers ("yes" to 1.1 pseudocode; "yes" to 4.12 statistical tests; "yes" to 3.2/3.3 data appendix) whose support currently lives in an unwritten supplement. **The single live compliance risk is that eight main-text promises point at a supplement that does not yet contain anything.**

### AI-Generated Writing Patterns

I do not think a reviewer will flag this as machine-written, and I would not. The register is idiosyncratic in a human direction — the caveats are load-bearing and specific to this paper's actual failures, not generic. If anything the risk runs the other way: the density and the repeated self-retraction read as a document written to survive an audit, which may make a reviewer wonder what the audit was.

### Questions for Authors

1. Can the five-arm forest ship in §5 with the RR<sup>s</sup> panel added from Table 3's existing values?
2. Will §4.5 carry numbers in the camera-ready?
3. What will the supplement contain on 7/31?

### Required Fixes

Add a §5 figure. Put numbers in §4.5 or cut it to two sentences. De-hedge the Introduction's contribution bullets. Move Figure 1B's base-model quantity out of the shared axis. Add a pseudocode block for §5.1.

### Rating

Rating: 4 / 10  
Confidence: 4 / 5

### Score Justification

Fully compliant and unusually honest, but the reading experience actively obscures the contribution, an entire experiment is reported without numbers, and the paper's second headline contribution has no visual support while a finished figure sits unused.

### Why Not Higher?

Clarity is a scored dimension, and a reviewer who cannot state the paper's finding after one pass will not champion it.

### Why Not Lower?

No compliance violation, a genuinely strong ethics statement, an honest limitations section, and table craft well above average.

---

## 6. Score Summary Table

|Reviewer|Role|Rating / 10|Confidence / 5|Main Positive|Main Negative|
|---|---|---|---|---|---|
|R1|Technical Soundness|5|4|Single-edit/restore paired protocol, collider risk empirically audited|Intervention penalizes the strings that define the endpoint; B₃ never defined|
|R2|Experiments & Reproducibility|4|4|Correct paired statistics, pre-registered gate honored at real cost|Supplement empty; separating endpoint has .48 precision, reliable one doesn't separate|
|R3|Novelty & Related Work|4|4|Budget-as-evaluation-axis protocol is genuinely new|Phenomenon already in cited prior work; MEMIT used but uncited; 16 refs|
|R4|Writing & Compliance|4|4|Compliant, strong ethics + limitations, excellent tables|Hedge density obscures contribution; §4.5 has no numbers; no §5 figure|

- **Average Rating:** 4.25
- **Median Rating:** 4
- **Lowest:** 4 · **Highest:** 5
- **Clear champion:** No. No reviewer is above threshold; R1 is closest and still at 5.
- **Strong reject voice:** No. Nothing at or below 3 — no reviewer found an error, only insufficiency.

---

## 7. SPC/AC-style Meta-review

### Overall Assessment

Four reviewers converge on the same shape: a well-built instrument, an honest research process, and a claim the evidence does not yet carry. Nobody found a mistake. That matters — this is not a paper with a bug, it is a paper whose authors have already discovered and disclosed its every weakness, and the disclosures add up to "we did not establish the mechanism, the effect appears at two checkpoints, our primary endpoint is unreliable and our reliable endpoint is null." A committee reads that and asks what is left to accept.

### Consensus Strengths

Methodological rigor and disclosure norms well above the field median; a genuinely useful protocol idea (evaluate the same edit at two budgets, with restore); a pre-registered gate that failed and was honored; internal numeric consistency I verified and could not break; an ethics statement that engages the actual dual-use structure.

### Consensus Weaknesses

Effect at 2 of 6 checkpoints with 2 pointing the other way; one dataset, one headline editor; mechanism unidentified by the paper's own account; primary endpoint precision .48 while the .92-precision endpoint fails to separate; judge monoculture with no human audit; the supplement — destination of eight main-text promises — is empty; the intervention's tautology exposure unresolved.

### Main Disagreement

R1 (5) treats the intervention as a sound experiment with an over-strong label; R3 (4) treats it as a known technique relocated. R4 would rate the paper higher if the same evidence were legible. There is no reviewer who thinks the paper is wrong, and none who thinks it is ready.

### Fatal Issues

1. **The supplement does not exist.** Eight promises, no content. Nothing else on this list is fatal _today_; this one is, unless it ships by 7/31.

### Fixable Issues

Everything else. Specifically fixable in the time available: cite MEMIT; define B₃ and B₀P; state the case-sampling frame; move layer selection into the main text; add the §5 forest figure; put numbers in §4.5; compress §4; de-hedge the Introduction. Not fixable in the time available: a second dataset, a second editor family, a human judge audit, the judge-scored endpoint contrast.

### Rebuttal Potential

**Low — structurally.** Phase-1 is 3 human reviewers plus AI-assisted review with **no rebuttal**. The submitted PDF has to answer these objections unaided. That converts several "the authors could explain this" items into unrecoverable ones. If a rebuttal existed, potential would be Medium: F2, F3, and M1 are all arguable on the existing data.

### Phase-2 / Discussion Potential

**Weak.** With a 4/4/4/5 spread and no champion, the paper does not enter substantive discussion. An SPC scanning for a defender finds none.

### Final Decision Recommendation

**Likely Reject** in the current version.

### Final AAAI Readiness Score

**52 / 100.** Method and integrity score high (roughly 75); evidence sufficiency (45), novelty delta (45), and communication (45) drag it down; the empty supplement is the single largest deduction against a submission-readiness score.

---

## 8. Priority Revision Plan

**Timing reality first:** today is 2026-07-27. The full paper is due **2026-07-28** (UTC-12) — roughly one working day. The internal freeze (7/25) has passed. Supplementary + code are due **2026-07-31**. So P0 must fit in a day, and the supplement gets three more.

### P0 — Must Fix Before Submission (≤1 day, no new computation)

1. **Cite MEMIT.** One bib entry, two `\citep` calls. You run the method in §5.5 and §6 and never cite it. Fifteen minutes; disproportionate reputational cost if left.
2. **Define B₃ and B₀P numerically in §3.1.** One sentence. Your central independent variable currently has no stated value.
3. **State the case-sampling frame in §3.1** — how many CounterFact requests, how selected, whether fixed across checkpoints. Currently only in a caption.
4. **Move per-checkpoint edit-layer selection into the main text**, including the scanned-on-two / relative-depth-rule-on-the-rest split. A reviewer who finds this only in the supplement will read it as buried; disclosed in §3.1 it is just a limitation.
5. **Put numbers in §4.5**, or cut it to two sentences pointing at the supplement. An experiment reported with zero values in a 7-page paper is worse than an experiment omitted.
6. **Add the five-arm forest to §5** with the RR<sup>s</sup> panel built from Table 3's existing contrasts. The figure is already drawn. Reclaim the space by compressing §4.1 and §4.3 — both currently spend a paragraph explaining why they prove nothing.

### P1 — Strongly Recommended (fits the 7/28–7/31 window)

7. **Ship the supplement with the four load-bearing sections**: §S11 hyperparameters/layers, the replay-gate table, the concept-direction endpoint set, and the placebo two-derivation provenance. The judge-missingness pattern and the §3.3 regressions can be thinner. If a section cannot be filled, delete the main-text promise that points at it rather than shipping an empty heading.
8. **De-hedge the Introduction's contribution bullets.** Line 41 is the paper's least readable paragraph and it is on page 1. Move its three caveats into footnotes; keep the claim. This costs no rigor and buys real reviewer goodwill.
9. **Add a pseudocode block for §5.1** — six lines, satisfies the checklist's 1.1 "yes" and makes the intervention unambiguous.
10. **Consolidate the two reproducibility admissions** (missing artifact, non-byte-reproducible placebo) into the §6 Reproducibility paragraph so they read as one disclosure rather than as two scattered concessions found mid-argument.
11. **Split Figure 1B's base-model quantity** onto its own strip or move it to text. The rule-and-caption defence works only for readers who read captions.

### P2 — Nice to Have (next version, not this one)

12. Report the **T-vs-N contrast under the judge endpoint** — this is the experiment that answers the tautology charge and it needs GPU time you do not have before 7/28.
13. A **length-matched content-free filler arm** (you name this gap yourself at line 184).
14. A **50-item human-audited judge subsample**.
15. A **second dataset** at one checkpoint.
16. Add the missing related-work directions, especially **chain-of-thought faithfulness** — your route taxonomy is a faithfulness taxonomy.

---

## 9. One-week Emergency Revision Plan

The requested seven-day plan does not fit the calendar; here it is mapped onto the days that actually exist, with the tail marked as post-deadline.

- **Day 1 (7/27, today):** P0 items 1–5. All text-only, no recomputation. Then rebuild the RR<sup>s</sup> panel onto the existing forest figure from Table 3's values.
- **Day 2 (7/28, deadline):** Insert the §5 figure, compress §4.1/§4.3 to make room, final consistency pass on every number touched, recompile, verify 7+1 pages, submit.
- **Day 3 (7/29):** Supplement §S11 (hyperparameters, per-checkpoint layers, run counts) and the replay-gate table. These are the two a reviewer is most likely to open.
- **Day 4 (7/30):** Supplement concept-direction endpoint set and placebo provenance (both derivations). Delete any remaining main-text promise you cannot discharge — but note the main text is frozen at submission, so this must instead be handled by making the supplement section explicit about what it cannot provide.
- **Day 5 (7/31):** Supplement figures + judge-missingness + §3.3 regressions; code and lock file; final supplementary upload.
- **Day 6–7 (post-deadline, for the next venue or camera-ready):** Run the judge-endpoint T-vs-N contrast and the length-matched filler arm. These are the two experiments that move the paper from 4 to 6.

---

## 10. Final Direct Answer

**1. Can this paper be submitted to AAAI now?**  
Yes, and you should — it is compliant and complete as a PDF. But submit it having done P0 items 1–5, which are all text edits achievable today. Submitting with MEMIT uncited and B₃ undefined would be an unforced error.

**2. What is the biggest risk if submitted now?**  
The empty supplement. Eight main-text promises point at material that does not exist, in a review round with no rebuttal. If 7/31 slips, every deferred item becomes an unanswerable objection.

**3. What is the most likely reason for low scores?**  
Insufficiency, not error. A reviewer will write: _the effect appears at 2 of 6 checkpoints on one dataset with one editor; the endpoint that separates has .48 precision and the reliable one does not separate; the mechanism is withdrawn by the authors._ Every clause of that sentence is constructible from your own text.

**4. Which experiment group should be added first?**  
The T-vs-N contrast scored by your existing judge panel instead of by alias matching. It uses infrastructure you already have, and it is the only experiment that answers the strongest attack on your flagship claim — that you penalized the tokens that define your endpoint. Second: the length-matched content-free filler arm.

**5. Which section should be rewritten first?**  
Section 4. It costs ~1.5 of 7 pages and concludes nothing by its own account. Compress it to one page — installation sanity as a footnote, the route census as one paragraph plus Table 2, the failed replay gate as three honest sentences, the length account as one — and give the reclaimed page to §5, which currently has no figure.

**6. What score pattern does the current version look like?**  
**5444.** No champion, no strong reject; four reviewers who respect the work and none who will defend it.

**7. After one serious revision, what is the highest realistic score pattern?**  
With P0+P1 only (text and figure work, no new runs): **5554** — better legibility, same evidence, still below threshold. With the P2 experiments — judge-scored endpoint, length-matched filler, a second dataset, a human judge subsample: **6656**, borderline-accept with a plausible champion. Getting to a confident accept needs the mechanism identified, which by your own §4.3 requires an experiment you have not designed yet.

**8. Should the paper be split into main paper + appendix?**  
It already is, and that is the problem — the split is currently one-directional. The main text is over-deferred: it promises eight things it does not carry, then reports §4.5 with no numbers because they went to a supplement that does not exist. Rebalance rather than split further: pull the layer-selection and sampling-frame facts _into_ the main text, push §4.1's tautological sanity check _out_.

**9. Should the authors continue targeting AAAI or redirect to another venue?**  
Submit to AAAI-27 — the deadline is tomorrow, the paper is compliant, and the expected outcome (borderline reject) costs you a review cycle that will be worth more than the delay. But plan for the redirect now. This paper's virtues — negative results honored, a pre-registered gate failed in public, measurement discipline as the actual contribution — are undervalued by a general AI venue and directly rewarded at evaluation-and-benchmarks-focused venues and at interpretability/analysis workshops. If AAAI rejects, do not weaken the honesty to fit a different venue; find the venue that scores it.

---

**One thing I want to say plainly, outside the reviewer voice.** The single most common failure mode in this literature is a paper that would have made these same concessions if anyone had checked, and did not. You checked, and you wrote the concessions down. The cost is that your paper reads like the audit report rather than the finding. The fix is not less honesty — it is putting each caveat where it belongs (footnote, Limitations) instead of inside the sentence that makes the claim. That change alone is worth more to your score than any experiment you could run before tomorrow.

# AAAI-style Simulated Review Report 3 

**Assessment basis.** This review uses the eight-page main manuscript and the accompanying internal results/provenance JSON. The JSON is treated as supporting evidence, not as a publication-ready supplementary document. External literature checking is used only in Reviewer 3 and is explicitly separated from manuscript-grounded assessment.

## 0. Paper Summary

The paper studies whether a parametric knowledge edit that succeeds under direct-answer evaluation remains effective when a reasoning model generates a chain before answering. It applies one ROME edit at a time to CounterFact requests and compares zero-thinking and native-chain generation across six DeepSeek-R1-distilled checkpoints, finding an approximately 10.6–10.7 percentage-point edit-success drop at Qwen-32B and Llama-70B. It then suppresses old-answer first tokens only during the reasoning span and shows that this intervention improves final-answer edit success without directly modifying answer-stage logits. The main empirical phenomenon is credible in the tested setting, but the causal mechanism and generality beyond counterfactual CounterFact edits remain unresolved.

---

## 1. Title / Abstract / Main Paper Consistency Check

### Title Promise

The title promises two things:

1. A broad evaluation conclusion: conventional direct-answer edit success is insufficient for parametric knowledge editing.
2. A reasoning-time stress-test methodology that exposes a hidden failure mode.

“Stress test” is an accurate description. The paper is not merely a benchmark because it also contains a signed think-span intervention. However, “parametric knowledge editing” is broader than the evidence: the primary phenomenon is demonstrated on CounterFact, primarily with ROME, and on two backbone lineages sharing the same DeepSeek-R1 teacher and distillation recipe.

A more accurate title would be:

> **Reasoning-Time Reversion in Parametric Knowledge Editing: A Paired Stress Test and Think-Span Intervention**

This title preserves the central contribution while avoiding the implication that all direct-answer evaluation has been invalidated across editors, datasets, and reasoning-model families.

### Abstract Claims

The abstract claims:

- Paired reasoning-time degradation at the largest tested Qwen and Llama checkpoints.
- A 19.3% permissive old-answer resurfacing rate and a 9.2% strict displacement rate on Qwen-32B.
- No detectable corresponding old-answer drift in the unedited Qwen-32B base model.
- Detectability of the edited association at a cloze probe in selected reversions.
- Visible in-chain routes toward the old answer.
- A think-only, signed intervention that lowers permissive resurfacing from 19.3% to 8.5%.
- Near-null answer effects from placebo and same-relation controls.
- A conclusion that the failure admits a chain-local causal control point.

### Main Paper Support

The main paper strongly supports the following narrower statement:

> For the tested CounterFact edits on the largest R1-distilled Qwen and Llama checkpoints, final generated answers are less likely to retain a successful ROME edit after native reasoning than under the paper’s zero-thinking condition; suppressing old-answer first-token generation during the think span causally changes final lexical answer behavior.

The manuscript is unusually explicit about the limits of its evidence. It states that:

- Only two of six fixed-checkpoint edit-success intervals exclude zero.
- The two model lineages share a teacher and reasoning recipe.
- Natural-chain mediation was not established because the replay vehicle failed.
- The canned-thought condition is not length matched.
- Realized chain lengths under suppression were not audited.
- The cloze result is a weak installation sanity check.
- Locality is only target-value non-leakage.
- Paraphrase validity is imperfect.
- General-task equivalence was not statistically certified.

### Mismatches

1. **General parametric-editing claim versus narrow empirical scope.**  
    The title and conclusion sound editor- and benchmark-general. The main result is principally ROME on CounterFact, with MEMIT supporting intervention transfer but not independently reproducing a significant fresh-baseline reasoning-time gap.
2. **The 19.3% headline is the least semantically precise endpoint.**  
    The paper reports that the permissive matcher has precision 0.48 and recall 0.96 against available judge-majority labels, while the strict endpoint has precision 0.92 and recall 0.85. The abstract includes both 19.3% and 9.2%, but the larger and less precise number dominates the narrative.
3. **“Chain-local causal control point” is supportable only under a narrow interpretation.**  
    The intervention proves that manipulating particular lexical tokens during chain generation can alter the final answer. It does not identify the natural mediation mechanism, show that the observed Bridge/Recall routes are necessary, or distinguish semantic suppression from sequence-level lexical priming and chain-length effects.
4. **The two lineages are not independent reasoning paradigms.**  
    They reduce backbone-specificity risk but not teacher-, distillation-, or reasoning-recipe-specificity.
5. **The cloze result is overprominent relative to its evidentiary weight.**  
    The paper itself calls it close to tautological, lacks a control and interval, and reports a missing per-item artifact. It should not appear in the abstract unless reframed explicitly as an installation check.
6. **Paraphrase “transfer” is active guarded application, not passive generalization.**  
    The suppressor is deliberately applied to the paraphrase probes. The paper eventually says this correctly, but the abstract could be read more broadly.
7. **The unedited-base drift result is a single-checkpoint control.**  
    The paired confidence interval is available for Qwen-32B only. It does not establish an across-model edit-versus-base interaction.

---

## 2. Reviewer 1 — Technical Soundness

### Summary

The paired within-edit protocol is technically coherent and substantially stronger than comparing unrelated edited and unedited model runs. The main phenomenon is credible in the tested cells. The central weakness is not whether the intervention changes the answer—it does—but whether the paper has identified a reasoning-specific, semantically meaningful control point rather than a lexically targeted autoregressive steering effect.

### Strengths

1. **Clean edit isolation.**  
    Each edit is applied independently and reverted before the next request, limiting cross-request contamination.
2. **Within-case comparison.**  
    Comparing B0 and B3 on the same edit and request is the correct design for measuring reasoning-time instability.
3. **Generated-text evaluation.**  
    The use of actual generated answers rather than only teacher-forced logits is appropriate for the deployment concern motivating the paper.
4. **Explicit endpoint hierarchy.**  
    Edit success, permissive resurfacing, strict displacement, and chain leakage are separately defined rather than conflated.
5. **Signed intervention design.**  
    The old-answer arm, new-answer reverse-sign arm, placebo arm, no-suppression arm, and same-relation competitor create a substantially stronger causal battery than a treated-versus-untreated comparison.
6. **Span separation.**  
    The primary suppressor acts during the think span and not while the scored answer is written. The scope ablation correctly shows why suppressing answer-stage logits would be a weaker causal diagnostic.
7. **Scientific restraint around failed identification.**  
    The preregistered replay gate failed at 9/18, and the paper stops the proposed mediation analysis rather than filtering successful cases or changing the gate. This is a major methodological strength.

### Weaknesses

#### Fatal Issues

**No conclusive fatal technical error is established from the provided material.**

There is, however, one conditional fatal risk: if “chain-local causal control point” is interpreted as evidence that naturally generated old-answer reasoning mediates the observed reversions, the claim is not supported. The paper must preserve the narrower claim that a token-level intervention confined to the chain can causally alter the final lexical answer.

#### Major Issues

1. **B0 is not clearly equivalent to standard direct-answer validation.**  
    B0 is a pre-closed empty think span, not obviously the same prompt and decoding protocol used in conventional CounterFact edit evaluation. The fact that a fixed canned thought materially improves edit success relative to B0 shows that apparently minor prompt-state differences can affect the result. A standard direct-answer prompt without synthetic think markup is required.
2. **B0 versus B3 bundles multiple treatments.**  
    B3 changes reasoning content, generation length, autoregressive state, forced think-span closure, and potentially truncation behavior. The paper acknowledges that the canned thought is not length matched and that realized chain lengths under suppression were not audited. Therefore, the current result identifies a native-chain generation effect, not a pure reasoning-content effect.
3. **Forced closure and early stopping are undercharacterized.**  
    The harness closes unclosed think spans. The paper should report, per checkpoint and condition, the fraction of generations that self-close, are forcibly closed, hit the token cap, or encounter degeneration. This is particularly important because the Llama-70B headline uses an early-stop-filtered analysis that may be directionally selected, even though the unfiltered sensitivity is similar.
4. **The intervention remains lexically entangled with the outcome.**  
    The tokens being penalized are derived from the old answer aliases that are also used by the answer-scoring instruments. Acting in a different span prevents direct score manipulation, but it does not eliminate sequence-level lexical priming, token-frequency, polysemy, or path-diversion explanations.
5. **No length-preserving or changed-row-matched active control is provided.**  
    The same-relation competitor is semantically stronger than a random placebo, but the internal results record notes that it is largely inactive in transfer runs and that the main battery lacks its own changed-row audit. A control should be calibrated to perturb approximately the same number of decoding steps or trajectories as the old-answer suppressor.
6. **The route taxonomy is observational and selection-conditioned.**  
    The 41 route instances are selected after an answer-only OLD gate from a frozen candidate pool and represent only 33 unique facts. The distribution is descriptive, can overweight repeated facts, and cannot establish route prevalence among all edits or causal mediation.
7. **The cloze probe does not materially support the mechanism.**  
    ROME directly optimizes the target association at the rewrite prompt. Showing new-token superiority in 23 selected reversions is therefore close to a manipulation check. The missing per-item artifact further prevents auditing case membership.
8. **Editor hyperparameter comparability is insufficiently visible.**  
    Model-specific ROME layers, clamping, BOS handling, dtype, and filtering can affect both B0 installation and B3 behavior. The main paper does not provide enough information to determine whether these choices were frozen using B0-only criteria or influenced by reasoning-time outcomes.

#### Minor Issues

1. The intervention should be stated as a formal decoding operator rather than only in prose.
2. The paper should specify how multi-token aliases, shared first tokens, capitalization, and tokenizer-specific variants are handled.
3. The competitor arm was added after the frozen four-arm protocol; this is disclosed but should be visually distinguished as confirmatory versus post hoc.
4. The dose ladder shows a monotone leakage reduction but not an ordered answer-level dose response. “Dose-graded intervention” is defensible for the manipulation check, not for the behavioral outcome.
5. Conditioning resurfacing on B0 success is appropriate, but cross-model resurfacing rates inherit different case compositions and should not be interpreted as directly comparable population rates.

### Questions for Authors

1. What is the exact difference between B0 and the standard direct-answer prompt normally used to certify a CounterFact edit?
2. What percentage of B3 chains self-close, are forcibly closed, or hit the 8,192-token cap for each model?
3. How were ROME layers and model-specific hyperparameters selected? Were any B3 outcomes inspected before choices were frozen?
4. How many decoding rows or token positions are actually changed by T, P, C, and D in the main Qwen-32B battery?
5. Does the T-versus-C effect remain after matching cases on realized chain length and number of changed decoding positions?
6. What happens if the old answer is referred to through a lexically disjoint description rather than its exact alias tokens?
7. Can a semantic old-answer representation be suppressed while preserving lexical access, or vice versa?
8. Is there a standard no-think prompt result without pre-inserted think delimiters?

### Required Fixes

1. Add a standard direct-answer baseline with no artificial empty-think wrapper.
2. Report full chain-length, self-closure, forced-closure, and truncation distributions.
3. Add a length-matched and activity-matched active control.
4. Narrow the causal claim to a **think-span lexical control point** unless semantic mediation is directly identified.
5. Move the route taxonomy and cloze sanity check out of the main causal chain of argument.
6. Add a formal equation and pseudocode for gating, token-set construction, and logit modification.
7. Report a unique-fact sensitivity for the route census.

### Rating

Rating: **6 / 10**  
Confidence: **4 / 5**

### Score Justification

The core paired observation and span-separated intervention are technically substantive and appear internally consistent. The paper earns a score above rejection because the intervention has signed controls, the failed mediation analysis is handled correctly, and key limitations are disclosed rather than hidden.

### Why Not Higher?

The present design does not isolate reasoning content from length and trajectory effects, and the intervention is lexically aligned with the evaluated old-answer aliases. The causal language is therefore close to the maximum allowed by the evidence. A clear accept would require a standard direct-answer baseline, chain-length/closure analysis, and at least one activity-matched or lexically orthogonal causal control.

### Why Not Lower?

The main result is not a simple correlation. The within-edit pairing, reverse-sign arm, span ablation, placebo, competitor, and transfer results collectively show that the final answer can be altered through a targeted intervention restricted to the chain.

---

## 3. Reviewer 2 — Experiments & Reproducibility

### Summary

The experimental program is extensive but narrower than its volume suggests. It contains many audits, controls, and sensitivity analyses, yet the central phenomenon is still primarily one dataset, one editor, one reasoning recipe, one lexical evaluation family, and one generation per primary cell. The internal provenance work is strong, but the public-facing reproducibility specification remains incomplete.

### Strengths

1. All six fixed checkpoints are reported rather than only significant cells.
2. Paired bootstrap intervals are used for within-case changes.
3. The Llama-70B filtered and unfiltered results are both reported.
4. The B0P/B1 experiment separates the empty wrapper from one fixed canned thought and a short native chain.
5. Greedy decoding is supplemented by a three-seed temperature-sampling analysis.
6. The unedited Qwen-32B base-model control does not show a matching shift toward the old answer.
7. The intervention is replicated at a second ROME scale, under MEMIT, and on supplied paraphrase probes.
8. Negative or null results are preserved, including the failed replay gate, the strict MEMIT endpoint, the concept-direction boundary test, imperfect paraphrase validity, and failed equivalence certification.
9. The internal JSON contains hash-based artifact tracking, duplicate-world audits, frozen estimands, explicit supersession records, and a passing CPU closeout. This is substantially better internal provenance than typical pre-submission work.

### Weaknesses

#### Fatal Issues

**No demonstrated data inconsistency invalidates the central results.**

A potentially submission-fatal reproducibility issue remains: the internal record states that the exact external judge-model version is not recorded. Because judge outputs support metric validation, route membership, route taxonomy, and replay outcomes, the model identifier, version, system prompt, temperature, and evaluation dates must either be recovered or the relevant judgments must be rerun with a fully specified instrument.

#### Major Issues

1. **CounterFact is the only primary edit dataset.**  
    CounterFact deliberately installs false counterfactuals over facts the model may already know. Reasoning may therefore be restoring strong world knowledge rather than exposing a generic failure of real knowledge correction. The ethical statement acknowledges this inversion, but the experiments do not resolve it.
2. **The headline phenomenon is mainly a ROME result.**  
    The fresh MEMIT no-suppression cell has a reasoning-time edit-success drop of 0.060 with an interval crossing zero. MEMIT supports transfer of the suppressor, not a clean independent replication of the primary phenomenon.
3. **Both lineages inherit the same reasoning teacher and recipe.**  
    Qwen-versus-Llama reduces backbone-specific risk but does not establish transfer across independently trained reasoning paradigms.
4. **The highest headline resurfacing number uses a low-precision matcher.**  
    The permissive endpoint has available-case precision 0.48. The strict endpoint is more semantically credible but smaller, and its T-versus-N intervention contrast does not exclude zero at Qwen-32B.
5. **Judge validation is incomplete and potentially dependent.**  
    Only 87 of 120 stratified items received votes, missingness is non-random with respect to the rule result, and the judges belong to one model family. There is no human-audited primary sample.
6. **One primary generation per edit/model/budget is fragile.**  
    Three fixed sampling seeds on Qwen-32B are useful but insufficient to characterize variability across seeds, prompts, decoding settings, and checkpoints.
7. **The CounterFact subset and prefiltering pipeline are not sufficiently specified in the main paper.**  
    The internal JSON refers to prefiltered, frozen seed-42 orderings, but a reviewer cannot reconstruct why particular requests were eligible from the manuscript alone.
8. **Multiplicity is undercontrolled.**  
    The paper reports six checkpoint cells, several endpoints, five arms, multiple pairwise contrasts, dose settings, transfer settings, and secondary analyses. It openly states that intervals and p-values are unadjusted, but the strict p-values around 0.03 are not robust to broad multiplicity control.
9. **Locality is not actually locality.**  
    The reported measure only checks whether the new target value leaks into a neighboring answer. It does not test whether the neighboring answer remains correct, unchanged, coherent, or non-refusal.
10. **General-task preservation is not statistically established.**  
    GSM8K and MATH point estimates are close, but the 90% intervals do not fit inside the ±0.02 equivalence margin. The paper describes this honestly, but these experiments cannot support a no-cost claim.
11. **The public artifact is not yet frozen into one authoritative release.**  
    The internal JSON contains superseded estimates, historical blocks, correction warnings, blocked components, pending draft edits, and alternative estimands. That is acceptable internally but unacceptable as a reviewer-facing supplement.
12. **Several artifact-level imperfections remain.**  
    These include the missing per-item logit-lens artifact, a one-row placebo provenance mismatch, an environment lock that predates rather than snapshots the runtime, and no byte-identity audit within the primary Qwen-32B battery itself.

#### Minor Issues

1. The route percentages should include a unique-fact sensitivity and uncertainty.
2. The paraphrase audit finds only 30/40 strings valid by majority and only 11/20 cases with both paraphrases valid; no valid-only sensitivity is supplied.
3. The Llama-70B filtering rule is directionally consequential even though the unfiltered estimate is similar.
4. The fixed three seeds do not justify a seed-population statement; the paper appropriately avoids one.
5. Hardware is described by accelerator class and memory rather than exact reproducible model, driver, CUDA, compiler, and kernel information in the main paper.
6. The paper reports pinned library versions but not enough detail to determine whether the lock file reflects actual run-time environments.

### Missing Experiments

The missing experiments should be prioritized as follows.

**First priority: non-counterfactual independent benchmark.**  
Run the same paired B0/B3 protocol on a benchmark where the new fact is an actual temporal correction, a synthetic authoritative update, or a fictional-world update rather than a deliberately false CounterFact replacement. This is the most important test of whether the phenomenon is knowledge-edit fragility rather than truth-restoration under contradiction.

**Second priority: complete semantic outcome adjudication.**  
For every primary Qwen-32B B0-success case, obtain complete OLD/NEW/NEITHER judgments from specified judges, with a human-audited subset. Make semantic strict reversion the primary outcome and lexical matchers secondary instruments.

**Third priority: construct-validity control matrix.**  
Compare:

- Standard direct answer.
- Empty think wrapper.
- Fixed canned thought.
- Length-matched content-free generation.
- Native reasoning at matched realized lengths.

Report self-closure, forced closure, and truncation.

**Fourth priority: independent reasoning-model family.**  
At least one reasoning model should not share the DeepSeek-R1 teacher/distillation recipe. A matched base-versus-reasoning-post-trained comparison would be especially informative.

**Fifth priority: second-editor phenomenon replication.**  
Demonstrate a significant B0-to-B3 gap under a second editor using a fresh, provenance-matched N arm—not merely transfer of the intervention.

**Sixth priority: real preservation metrics.**  
Use neighbor correctness, general capability, unrelated factual QA, paraphrase consistency, and behavioral-change measures rather than target-value non-leakage alone.

### Reproducibility Concerns

The following information must appear in a clean appendix or artifact manifest:

- Exact model repository identifiers and immutable revision hashes.
- Tokenizer revisions and BOS settings.
- Full prompts and chat templates for B0, B0P, B1, and B3.
- Think and answer token caps.
- Forced-close and truncation behavior.
- Exact CounterFact filtering and case IDs.
- ROME and MEMIT layers and every hyperparameter by model.
- Criterion and chronology used to select layers and suppression strength.
- Full alias lists and tokenized first-token sets.
- Random seeds, temperature, top-p, and stopping criteria.
- Exact judge model, version, prompts, decoding parameters, and raw votes.
- Error rows, missing rows, and exclusion rules.
- Runtime package, CUDA, driver, and hardware manifests.
- One authoritative results table with superseded estimates removed.

### Questions for Authors

1. Are the 200 CounterFact requests selected before any B3 generation or intervention outcome was inspected?
2. What precise filters define the final CounterFact cohort?
3. Can the exact judge-model version be recovered? If not, will all load-bearing judgment tasks be rerun?
4. Why should CounterFact truth restoration generalize to real temporal corrections?
5. Which ROME and MEMIT hyperparameters were tuned on B0 only, and which were chosen after viewing B3?
6. How many cases are truncated or forcibly closed under B3 at each checkpoint?
7. Does the strict semantic reversion result remain after complete human adjudication?
8. What result supports a general phenomenon under MEMIT, as opposed to intervention transfer under MEMIT?
9. Are all raw trajectories and case-level paired outcomes available for release?
10. How does the suppressor affect unrelated factual responses that happen to contain the same first-token IDs?

### Required Fixes

1. Add a non-counterfactual or real-update benchmark.
2. Replace the permissive 19.3% endpoint as the primary semantic headline.
3. Complete judge validation without rate-limit missingness and add human audit.
4. Freeze one reproducible artifact release with exact model and judge versions.
5. Report standard direct-answer, chain-length, forced-closure, and truncation controls.
6. Predefine a primary endpoint and family of confirmatory contrasts or report multiplicity-adjusted inference.
7. Report genuine neighbor correctness and broader preservation measures.
8. Clearly separate phenomenon replication from suppressor transfer.

### Rating

Rating: **5 / 10**  
Confidence: **5 / 5**

### Score Justification

The quantity and honesty of the experimental work are strong, but acceptance should depend on what the experiments establish, not how many analyses exist. The paper currently demonstrates a rigorous CounterFact/ROME/R1-distill phenomenon and a targeted lexical intervention. It does not yet establish that real knowledge corrections, independent reasoning paradigms, or parametric editing generally exhibit the same failure.

### Why Not Higher?

The central generalization remains untested, the highest resurfacing headline uses a low-precision metric, the primary judge instrument is incompletely reproducible, and the phenomenon is not cleanly replicated under a second editor.

### Why Not Lower?

The authors report all six cells, paired intervals, nulls, failed gates, imperfect audits, and transfer boundaries. The core numeric results appear internally consistent, and the intervention battery is materially stronger than a typical single-baseline ablation.

---

## 4. Reviewer 3 — Novelty, Significance & Related Work

### Summary

The paper’s novelty is moderate. The high-level observation that conventional edit success can fail under reasoning or realistic autoregressive inference is no longer new. The more distinctive contributions are the same-edit budget pairing and the signed, think-only intervention that affects an answer stage it does not directly modify.

### Strengths

1. **Same-edit budget pairing is a meaningful methodological refinement.**  
    It asks how one installed edit behaves as the generation regime changes, rather than comparing unrelated models, editors, or test sets.
2. **The intervention location is novel and conceptually clean.**  
    Prior decoding interventions often act on answer generation. Restricting the intervention to the reasoning span creates a sharper causal question.
3. **The sign-reversal arm strengthens specificity.**  
    Suppressing the new answer worsens outcomes while suppressing the old answer improves them.
4. **The paper does not pretend to have identified natural-chain mediation after the replay failure.**
5. **The evaluation concern is significant.**  
    Reasoning-oriented deployment creates a real mismatch if edits are certified only under direct answers.

### Weaknesses

#### Fatal Issues

**No fatal novelty failure is established.**

The novelty could nevertheless be judged below threshold if the paper is presented primarily as the discovery that reasoning can undo or fail to propagate knowledge edits. That broad observation is already present in closely related work.

#### Major Issues

1. **The headline phenomenon overlaps substantially with existing work.**  
    The paper’s own related-work section acknowledges prior demonstrations that parameter editing performs poorly under realistic autoregressive inference, that edits fail to propagate through reasoning, and that reasoning chains can reject injected facts.
2. **The manuscript does not sufficiently distinguish “failure to use an edit” from “reversion after successful direct recall.”**  
    This distinction is important and potentially novel, but it should be formalized in a comparison table rather than embedded in prose.
3. **The missing related work includes a directly named “Reasoning Gap.”**  
    A recent paper on mechanistic circuit-based knowledge editing explicitly frames the case where a model recalls an edited fact directly but fails to use it in multi-hop reasoning and proposes circuit-level repair. That work is not in the manuscript’s reference list and must be compared carefully.
4. **Other recent work trains models to integrate edited knowledge through chain-of-thought or multi-step reasoning.**  
    These methods differ from the paper’s diagnostic focus but directly affect its claim that reasoning-time use of edits is insufficiently studied.
5. **The intervention is more diagnostic than methodological.**  
    It requires the edited subject, relation, old-answer aliases, access to think-token logits, and active inference-time modification. Its significance is therefore mechanistic/evaluative rather than as a general editing method.
6. **CounterFact limits conceptual significance.**  
    In this benchmark, old-answer restoration can be interpreted as successful recovery of true world knowledge. Without real corrections or synthetic authoritative updates, the work may be read as documenting conflict rejection rather than general edit instability.
7. **The paper’s mechanistic middle is not resolved.**  
    The route taxonomy, cloze sanity, CLR enrichment, failed replay, and concept-direction null do not converge into an identified mechanism. The paper is strongest as a two-contribution paper, not a three-stage mechanism story.

#### Minor Issues

1. “Two lineages” should not be framed as two independent reasoning systems.
2. The paper should explicitly distinguish test-time compute, visible chain content, and latent computation.
3. “Chain routing” should remain a hypothesis label, not a mechanism name.
4. The paraphrase result is guarded active application and should not be called generalization without qualification.
5. The contribution list is too long and defensive; it obscures the genuinely novel part.

### Novelty Assessment

- **High-level phenomenon:** Low-to-moderate novelty. Reasoning-aware editing failure is established in prior work.
- **Paired budget-controlled protocol:** Moderate novelty.
- **Think-only signed intervention:** Moderate-to-high novelty.
- **Route taxonomy:** Low-to-moderate novelty and descriptive.
- **Natural mechanism identification:** Not achieved.
- **Overall novelty:** Sufficient for borderline acceptance if the paper is framed around the paired design and think-span intervention rather than around first discovery of a reasoning gap.

### Related Work Gaps

#### Manuscript-grounded assessment

The paper already cites work on realistic autoregressive evaluation, reasoning-based edit propagation, multimodal chain rejection, belief depth, test-time compute degradation, factual priming, and answer-stage decoding interventions. The related-work taxonomy is sensible but too compressed.

#### External literature check

Externally verified prior work strengthens the novelty concern:

- He et al. already evaluate knowledge editing on reasoning-oriented models under realistic autoregressive inference and report broad weaknesses of parameter-based editing.
- Hua et al. already study failure to propagate edits through reasoning tasks and analyze generated chains.
- CRANE explicitly contrasts high traditional/teacher-forced success with severe reasoning-chain failure and identifies chain rejection or shallow internalization in a multimodal setting.
- Gekhman et al. identify computational-buffer and factual-priming mechanisms by which reasoning changes factual recall, directly motivating the paper’s unresolved length/content alternatives.
- A recent mechanistic circuit-based editing paper explicitly defines a “Reasoning Gap” in which direct edited-fact recall succeeds but multi-hop use fails, and proposes circuit-guided repair. This appears directly relevant and is absent from the references.
- Recent approaches also train models to use updated knowledge through chain-of-thought or multi-step reasoning, which should be discussed as complementary solution directions.

The paper needs a structured related-work comparison with columns such as:

|Work family|Same edit paired across budgets|Explicit reasoning model|Direct success conditioned|Natural-chain analysis|Think-only intervention|Real/non-counterfactual updates|
|---|---|---|---|---|---|---|

Without that table, the claim “four properties are not addressed jointly” reads as assertion rather than demonstrated differentiation.

### Significance Assessment

The problem is relevant to AAAI: reasoning models are increasingly used under generation regimes unlike those in standard editing evaluations. A robust evaluation protocol that reveals direct-versus-reasoned instability would be useful.

The current significance ceiling is lowered by four factors:

1. The phenomenon is statistically clear only at the largest tested checkpoint in each family.
2. Both families share a reasoning teacher and recipe.
3. The dataset uses false counterfactual facts.
4. The suppressor requires oracle edit metadata and access to the visible think stream.

The work is significant as a **diagnostic study of edit robustness under explicit reasoning**, not yet as a general conclusion about deployed knowledge editing.

### Questions for Authors

1. What is the precise novelty relative to the recent “Reasoning Gap” and circuit-based editing literature?
2. Why is the unit of novelty a thinking-budget comparison rather than another form of reasoning-aware editing evaluation?
3. What real-world claim survives if CounterFact reasoning is simply restoring true knowledge?
4. Is the suppressor intended as a mechanistic probe, an evaluation instrument, or a practical guard? The paper currently occupies all three positions.
5. What does the paper add beyond the combination of realistic autoregressive evaluation and factual-priming results?
6. Would the same phenomenon occur for synthetic facts that have no competing pretrained world knowledge?
7. Why should AAAI readers view the route taxonomy as a central contribution after natural mediation remains unidentified?

### Required Fixes

1. Reframe the novelty around **paired within-edit reasoning-time robustness** and **span-separated causal intervention**.
2. Add the missing reasoning-gap and reasoning-integrated editing literature.
3. Include a direct comparison table against the closest works.
4. Add a non-counterfactual benchmark.
5. Demote route taxonomy and cloze probing to supporting diagnosis.
6. State clearly that the intervention is not a general editing method or deployment-ready defense.
7. Avoid suggesting first discovery of reasoning-time edit failure.

### Rating

Rating: **6 / 10**  
Confidence: **4 / 5**

### Score Justification

The high-level failure mode is incremental relative to the current literature, but the paired budget protocol and think-only signed intervention are sufficiently distinct to clear the novelty threshold narrowly.

### Why Not Higher?

The paper misses directly relevant 2026 work, relies on one counterfactual benchmark, and does not complete the proposed natural mechanism. Its most novel result is a targeted lexical intervention rather than a broadly applicable method.

### Why Not Lower?

The intervention genuinely asks a different causal question from answer-stage suppression, and the same-edit paired design is a meaningful improvement over broad benchmark comparisons.

---

## 5. Reviewer 4 — Writing, Structure & Compliance

### Summary

The manuscript is technically careful but excessively compressed. It reads like an internal audit record converted directly into a conference paper: nearly every sentence contains a result, denominator, caveat, exception, or scope restriction. The result is honest but difficult to parse, and the central contribution is obscured by secondary diagnostics.

### Strengths

1. The title, abstract, introduction, results, and conclusion broadly discuss the same problem.
2. The paper clearly distinguishes permissive and strict lexical endpoints.
3. Nulls and failed experiments are disclosed at unusually high prominence.
4. The limitations section is substantive rather than ceremonial.
5. The ethical statement directly addresses the fact that CounterFact reversions restore true values and that the suppressor can be interpreted adversarially.
6. The main PDF appears anonymized and contains no obvious author or institution disclosure.
7. Citations are stylistically consistent in the rendered manuscript.
8. Tables contain actual intervals and denominators rather than only point estimates.

### Weaknesses

#### Fatal Issues

**No fatal writing or anonymity violation is visible in the main PDF.**

The anonymized supplementary artifact and submission-specific compliance files were not provided. Their double-blind safety is therefore **Not sufficiently specified in the provided material**.

#### Major Issues

1. **The abstract is overloaded.**  
    It includes two model effects, two reversion rates, a base control, cloze probing, route analysis, intervention scope, two controls, and a causal conclusion. The reader must understand several operational endpoints before the paper defines them.
2. **The prose is audit-log dense.**  
    Phrases such as “juxtaposed rather than contrasted,” “scope statement, not a post-hoc selection,” “non-rescuing post-hoc audit,” “point-equivalence,” and repeated declarations of what is not claimed create a legalistic tone. The caution is appropriate; the volume of caution is not.
3. **The core narrative is diluted.**  
    Section 4 spends substantial main-text space on a weak cloze check, an outcome-conditioned taxonomy, a failed replay vehicle, the length-only account, CLR enrichment, and a null concept-direction experiment. The paper would be stronger if it admitted that the mechanism is open and moved most of this material to the appendix.
4. **Figure 1 is too small and visually overloaded.**  
    On page 4, panel labels, axis text, checkpoint labels, and control-condition labels are small at normal reading scale. Panel B places edited-model edit-success changes and an unedited-base old-answer change in one visual despite their different event definitions and denominators. The caption explains this, but the visual still invites comparison.
5. **Table 1 mixes different estimands and denominator conventions.**  
    It combines marginal ES levels, complete-pair changes, and B0-gated resurfacing rates. The caption is accurate but too much interpretive burden is delegated to it.
6. **Table 3 is statistically complete but not reader-efficient.**  
    Arm levels and six pairwise contrasts across three outcomes create a dense matrix. A forest plot of the three central contrasts would communicate the result faster, with the full table in the appendix.
7. **The intervention lacks a compact formal algorithm.**  
    A one-line equation and a five-step pseudocode block would be clearer than several paragraphs of operational description.
8. **The raw results JSON is not suitable as a supplementary artifact.**  
    It includes superseded records, correction notes, internal planning language, blocked components, mixed-language commentary, and pending draft instructions. A clean frozen artifact must be generated separately.
9. **The title is slightly broader than the evidence.**  
    The stress-test framing is good; the unqualified parametric-editing generalization is not.
10. **The abstract foregrounds the permissive endpoint without its precision caveat.**  
    The 19.3% figure is memorable but operationally noisy. The semantically cleaner 9.2% strict result or a complete judge-based result should lead.

#### Minor Issues

1. Too many acronyms and near-acronyms are introduced: ES, RR, RRs, CLR, B0, B0P, B1, B3, N, T, D, P, C.
2. Several paragraphs contain more than one logical function: result, limitation, contrast, and interpretation.
3. Footnotes carry important measurement information that belongs in the main prose or appendix.
4. “Bounded transfer, honestly bounded” sounds rhetorical rather than academic.
5. “The control point moves the untouched answer” is memorable but slightly promotional.
6. There is no high-level protocol diagram showing edit → B0/B3 → chain → answer → intervention.
7. The paper should avoid any wording that could imply access to private hidden chains in closed systems.

### Structure Problems

The manuscript should be reorganized around two claims:

1. **Reasoning-time robustness failure:** paired B0/B3 evidence and decisive controls.
2. **Think-span intervention:** signed five-arm evidence and bounded transfer.

The following should be compressed or moved:

- Cloze installation sanity: appendix.
- Full route taxonomy: appendix, with one main-text sentence.
- Failed replay details: appendix, with one main-text disclosure.
- CLR stratification and concept-direction boundary: appendix.
- Full multiplicity table: appendix.
- Hardware and artifact exceptions: reproducibility appendix.

The main paper should retain:

- One conceptual protocol figure.
- Table 1 or a cleaner equivalent.
- One five-arm forest plot.
- One transfer table.
- A concise limitations section.

### Writing Problems

The paper is not vague; it is overqualified. A sentence such as:

> “This juxtaposition is consistent with an edit-specific pattern, but the two quantities differ in event definition and denominator; we make no formal contrast.”

is technically responsible. Repeating that style throughout the paper makes the contribution feel less settled than it is.

The solution is not to remove caveats. The solution is to:

- Put the primary claim first.
- State the most important caveat once.
- Move detailed exceptions to a clearly indexed appendix.
- Use a claim-evidence-boundary table.

There is no specific evidence that the manuscript was AI-generated. The risk is stylistic: repeated symmetric caveats, exhaustive parentheticals, and “claim ceiling” language can read like machine-produced audit prose.

### Figure / Table / Algorithm Quality

**Figure 1, page 4:** Conceptually sound but too small. The categorical-axis warning is good. Panel B should be separated or visually recoded because the unedited-base quantity is not the same outcome as the edited-model ES changes.

**Table 1, page 3:** Numerically useful, but it needs explicit columns for attempted nnn, complete-pair nnn, and B0-gated nnn. The current footnote-based denominator explanation is too fragile.

**Table 2, page 4:** The route table should report both instance and unique-fact views. Percentages from 41 instances should not look like population estimates.

**Table 3, page 7:** Strong evidence, weak presentation. Keep N/T/D/P/C arm levels and T–P, T–C, D–N in the main paper; move P–N and C–N detail to the appendix or a forest plot.

**Algorithm quality:** No algorithm is provided. Add:

z~t(v)=zt(v)−α 1{t∈think span}1{v∈T(oold)}1{subject-relation gate active}.\tilde z_t(v) = z_t(v) - \alpha\, \mathbf{1}\{t\in\text{think span}\} \mathbf{1}\{v\in\mathcal{T}(o_{\text{old}})\} \mathbf{1}\{\text{subject-relation gate active}\}.z~t​(v)=zt​(v)−α1{t∈think span}1{v∈T(oold​)}1{subject-relation gate active}.

Then specify alias construction, tokenization, activation scope, and answer-stage deactivation.

### AAAI Compliance Risks

1. **Specific-year page-limit compliance:** Not sufficiently specified in the provided material. The PDF has seven pages of main content and one reference page, but no specific official-year rule is assumed here.
2. **Double blind:** The main PDF appears anonymized. The supplementary files, code repository, artifact metadata, and external-judge logs were not provided in submission form.
3. **Reproducibility checklist:** Not sufficiently specified in the provided material.
4. **Ethics statement:** Present and strong.
5. **Limitations statement:** Present and unusually detailed.
6. **Citation style:** Appears consistent.
7. **Artifact anonymity:** The raw internal JSON should not be submitted as-is.
8. **External judge disclosure:** Exact judge version is missing in the internal provenance record.
9. **AI-use disclosure:** Not sufficiently specified in the provided material; no claim is made that one is required under a particular AAAI year.

### Questions for Authors

1. What are the two sentences the reader should remember after reading the paper?
2. Why is the failed replay vehicle in the main paper rather than the appendix?
3. Can the abstract be rewritten around the strict or semantic endpoint rather than permissive RR?
4. Can Figure 1 be split into a primary gap figure and a separate controls figure?
5. Why is there no formal algorithm for the suppressor?
6. Will the public artifact remove all superseded estimates and internal planning comments?
7. Is the exact judge version recoverable?
8. Does the main submission include a reproducibility checklist and anonymized repository?

### Required Fixes

1. Rewrite the abstract to approximately 170–200 words with at most three headline numbers.
2. Reduce the paper to two principal claims.
3. Move most of Section 4’s diagnostics to the appendix.
4. Redraw Figure 1 with larger fonts and separate estimands.
5. Replace Table 3’s full contrast matrix with a forest plot plus a smaller table.
6. Add formal pseudocode and a logit-intervention equation.
7. Produce a clean, frozen, anonymized supplement.
8. Make strict or fully judged semantic reversion the leading endpoint.
9. Narrow the title or strengthen cross-benchmark evidence.

### Rating

Rating: **5 / 10**  
Confidence: **4 / 5**

### Score Justification

The manuscript is rigorous and honest, but it is harder to read than necessary and places too much internal audit machinery in the main narrative. The current structure makes a potentially clear result appear fragmented and overdefended.

### Why Not Higher?

The abstract, figures, tables, and Section 4 do not yet communicate the contribution at conference-paper efficiency. Important implementation details remain external while secondary diagnostic detail occupies main-text space.

### Why Not Lower?

The paper is professionally written, logically organized, anonymized in the main PDF, and unusually transparent about limitations, nulls, and ethical ambiguity.

---

## 6. Score Summary Table

|Reviewer|Role|Rating / 10|Confidence / 5|Main Positive|Main Negative|
|---|---|---|---|---|---|
|R1|Technical Soundness|6|4|Strong paired design and signed think-only intervention|Causal interpretation remains lexically and length confounded|
|R2|Experiments & Reproducibility|5|5|Extensive controls, sensitivities, and provenance audits|One counterfactual dataset, low-precision headline metric, incomplete judge reproducibility|
|R3|Novelty & Related Work|6|4|Same-edit budget axis and span-separated intervention are distinct|High-level reasoning-gap observation is already known; missing close 2026 work|
|R4|Writing & Compliance|5|4|Honest limitations, strong ethics, coherent organization|Overcompressed audit-log prose and publication-unready supplement structure|

**Average Rating:** 5.50 / 10  
**Median Rating:** 5.50 / 10  
**Lowest Rating:** 5 / 10  
**Highest Rating:** 6 / 10

**Clear champion:** No. No reviewer assigns a 7 or higher.

**Strong reject voice:** No score is 4 or below. However, R2 and R4 independently place the paper below threshold for different reasons, so the absence of a “strong reject” does not imply a favorable panel.

**Likely panel dynamic:** Two marginal accepts and two marginal rejects. Without a reviewer willing to champion the intervention as a major conceptual contribution, the default outcome is rejection.

---

## 7. SPC/AC-style Meta-review

### Overall Assessment

This is a technically serious paper with a credible central observation: in the tested large R1-distilled checkpoints, an edit that works under the paper’s zero-thinking condition can lose control after native chain generation. The think-span intervention provides real causal evidence that modifying chain generation can change the final answer without directly modifying answer-stage logits.

The submission is not currently a clear accept because its broad framing exceeds its empirical scope. The phenomenon is primarily established for ROME, CounterFact, and one shared reasoning recipe. The largest resurfacing number is operationally permissive, the natural mechanism remains unidentified, and the intervention is lexically targeted and oracle-gated.

### Consensus Strengths

1. Paired same-edit B0/B3 design.
2. Transparent reporting of all six cells.
3. Signed five-arm intervention.
4. Clear separation between think-stage and answer-stage manipulation.
5. Honest disclosure of failed replay identification.
6. Extensive internal provenance and sensitivity work.
7. Strong limitations and ethical statement.
8. Timely and relevant problem.

### Consensus Weaknesses

1. CounterFact-only primary evidence.
2. No real-update or non-counterfactual benchmark.
3. Two lineages share the same reasoning teacher and recipe.
4. Permissive RR has low semantic precision.
5. Incomplete and incompletely specified judge instrumentation.
6. No standard direct-answer baseline separate from the empty-think wrapper.
7. No length-matched filler or realized-chain-length analysis.
8. Lexical intervention remains entangled with lexical evaluation.
9. Natural-chain mediation is not identified.
10. Main paper is too dense and supplement-dependent.
11. Closely related 2026 work is missing.
12. No clear champion score.

### Main Disagreement

The likely disagreement is whether the think-only intervention is enough to elevate the work from an incremental evaluation paper to a substantial mechanistic contribution.

- Positive reviewers will argue that moving an untouched answer through a signed chain-only intervention is novel and important.
- Negative reviewers will argue that suppressing exact old-answer first tokens is an autoregressive lexical steering result, not evidence of the mechanism by which reasoning naturally defeats an edit.

The current manuscript does not decisively resolve that dispute.

### Fatal Issues

No demonstrated mathematical or empirical error invalidates the paper.

The following are potential decision-level blockers:

1. The causal wording is interpreted more broadly than the actual identification.
2. The CounterFact-only result is judged to be truth-restoration specific.
3. The permissive 19.3% endpoint is treated as semantic reversion.
4. The external judge version cannot be recovered or rerun.
5. The missing directly relevant literature creates a novelty objection.

### Fixable Issues

- Abstract and title scope.
- Primary endpoint framing.
- Main/appendix division.
- Figure and table readability.
- Formal suppressor definition.
- Exact reproducibility manifest.
- Complete semantic adjudication.
- Standard direct-answer and chain-length controls.
- Related-work comparison table.

The non-counterfactual benchmark and independent reasoning-family replication require meaningful new experiments, not merely rewriting.

### Rebuttal Potential

**Medium.**

A rebuttal could improve the outcome if:

- The exact judge model and full artifact details already exist but were omitted.
- Standard direct-answer, chain-length, or semantic-judge analyses have already been run.
- The authors can clearly distinguish their contribution from the closest reasoning-gap work.
- The supplement contains stronger non-CounterFact evidence than the main PDF.

A rebuttal cannot credibly repair the main external-validity gap if no non-counterfactual or independent-family results exist. It also cannot convert the failed replay experiment into natural-chain mediation evidence.

### Phase-2 / Discussion Potential

**Moderate.**

The score pattern is sufficiently close to threshold to enter discussion. The intervention could attract interest. However, there is no current champion, and the two marginal-reject reviews arise from orthogonal concerns—external validity and presentation/reproducibility—making a spontaneous upward consensus unlikely.

### Final Decision Recommendation

**Borderline Reject**

### Final AAAI Readiness Score

**58 / 100**

Interpretation:

- Technical seriousness: high.
- Core empirical credibility: moderate-to-high within scope.
- Mechanistic identification: moderate-to-low.
- External validity: low.
- Novelty differentiation: moderate.
- Reproducibility readiness: moderate.
- Presentation readiness: moderate-to-low.

---

## 8. Priority Revision Plan

### P0 — Must Fix Before Submission

1. **Add one non-counterfactual benchmark.**  
    Use real temporal corrections, synthetic authoritative updates, or fictional-world facts. Apply the same B0/B3 paired protocol and strict semantic scoring.
2. **Replace permissive RR as the principal reversion claim.**  
    Lead with complete OLD/NEW/NEITHER judgments or strict displacement. Keep 19.3% as a high-recall lexical sensitivity result.
3. **Close the B0/B3 construct-validity gap.**  
    Add:
    - Standard direct answer with no think wrapper.
    - Empty think wrapper.
    - Fixed canned thought.
    - Length-matched content-free filler.
    - Native chain.
    - Self-close, forced-close, truncation, and realized-length statistics.
4. **Narrow the causal claim.**  
    Until semantic mediation is identified, use:
    
    > “A think-span lexical intervention causally changes final answer behavior.”
    
    Do not imply that the natural Bridge/Recall routes have been proven causal.
    
5. **Freeze the reproducibility package.**  
    Recover or rerun the exact judge instrument. Publish one authoritative manifest and remove every superseded, pending, blocked, or internal-planning block.
6. **Rewrite the abstract and contribution statement.**  
    Reduce the paper to:
    - Paired reasoning-time robustness failure.
    - Signed think-span intervention.
7. **Update related work.**  
    Add the missing reasoning-gap, circuit-based, and reasoning-integrated editing literature and provide a structured comparison table.

### P1 — Strongly Recommended

1. Replicate the phenomenon under a fresh second editor with a significant B0/B3 gap.
2. Add a non-R1-distilled reasoning family.
3. Obtain a complete human-audited semantic sample.
4. Match the active control on changed decoding positions and chain length.
5. Report unique-fact route-taxonomy sensitivity.
6. Replace target-value non-leakage with actual neighbor correctness.
7. Add a hierarchical or omnibus analysis rather than emphasizing two significant cells among six.
8. Report model-specific ROME/MEMIT hyperparameters and selection chronology.
9. Elevate the existing multihop result only after clearly explaining the B0 structural disadvantage and template concentration.
10. Report intervention false-trigger and token-collision analysis.

### P2 — Nice to Have

1. Test lexically orthogonal old-answer references.
2. Evaluate hidden-chain or latent-reasoning settings where visible think tokens are unavailable.
3. Run more sampling seeds across more than one checkpoint.
4. Add automatic edit-query detection rather than oracle subject-relation gating.
5. Evaluate latency and decoding cost.
6. Test multi-edit and sequential-edit settings.
7. Add a broader semantic locality suite.
8. Investigate whether suppression changes chain length, style, uncertainty, or refusal behavior.
9. Replace route percentages with cluster-aware intervals.
10. Develop a deployment-oriented guard only after the diagnostic claim is settled.

---

## 9. One-week Emergency Revision Plan

### Day 1: Freeze the scientific story

- Define exactly two primary claims.
- Mark every result as confirmatory, prespecified, post hoc, diagnostic, or failed.
- Remove the cloze probe and route taxonomy from the abstract.
- Decide that strict semantic reversion, not permissive lexical RR, is the lead endpoint.
- Produce a single authoritative table mapping every manuscript number to one frozen artifact.
- Recover the exact judge model/version or schedule immediate reruns.

**End-of-day deliverable:** claim-evidence-boundary matrix and frozen results manifest.

### Day 2: Complete semantic validation

- Adjudicate every Qwen-32B B0-success final answer as OLD/NEW/NEITHER.
- Use fully specified judges and obtain a human-audited stratified subset.
- Report confusion matrices for permissive and strict lexical rules.
- Recalculate primary intervention effects using semantic labels where feasible.
- Audit all paraphrases or remove the paraphrase claim from the main paper.

**End-of-day deliverable:** complete semantic endpoint table with no rate-limit missingness.

### Day 3: Run the decisive construct-validity controls

Run on the primary Qwen-32B cohort:

1. Standard direct-answer prompt.
2. Empty think wrapper.
3. Canned thought.
4. Length-matched filler.
5. Native B1 and B3 chains.
6. T and activity-matched control under chain-length tracking.

Record self-closure, forced closure, cap hits, realized lengths, changed token positions, and final semantic outcomes.

**End-of-day deliverable:** one control matrix that determines whether the paper can retain “reasoning-time” and “causal control point” language.

### Day 4: Run or finalize the external-validity experiment

- Prioritize a real temporal, synthetic-authoritative, or fictional-world update set.
- Use the strongest feasible model and ROME; add MEMIT only if compute permits.
- Use B0/B3 pairing and strict semantic evaluation.
- If a clean new benchmark cannot be completed, validate and integrate the existing multihop analysis only as bounded evidence that erosion extends beyond exact single-hop cloze prompts.
- Do not add another route taxonomy or exploratory probe.

**End-of-day deliverable:** one independent benchmark table.

### Day 5: Statistical and reproducibility closeout

- Define one primary phenomenon endpoint and one primary intervention contrast.
- Add multiplicity-adjusted or hierarchical sensitivity results.
- Make the unfiltered Llama-70B analysis primary or justify filtering prospectively.
- Finalize exact model revisions, tokenizer settings, hyperparameters, seeds, prompts, hardware, software, and artifact hashes.
- Remove superseded blocks from the release artifact.
- Verify every table cell from raw case-level data.

**End-of-day deliverable:** clean supplementary package and independent number audit.

### Day 6: Rewrite and redraw

- Rewrite title, abstract, introduction, and conclusion.
- Reduce Section 4 to one short diagnostic subsection plus explicit statement that mediation remains open.
- Create:
    1. A conceptual B0/B3/intervention diagram.
    2. A larger gap figure.
    3. A five-arm forest plot.
    4. A compact transfer table.
- Move full contrast matrices and failed experiments to the appendix.
- Increase all figure text to normal two-column readability.

**End-of-day deliverable:** submission-length revised manuscript.

### Day 7: Red-team review

Have an independent reader answer:

- Is the primary endpoint semantic?
- Is the direct-answer baseline standard?
- Is reasoning separated from length and forced closure?
- Is the causal claim narrower than the evidence?
- Does a second benchmark support the conclusion?
- Is the closest 2026 work cited?
- Can every number be regenerated?
- Can the paper be summarized in two sentences without caveats?

Run a final simulated panel. Submit only if no reviewer remains at 4 or 5 for an issue requiring new experiments.

---

## 10. Final Direct Answer

### 1. Can this paper be submitted to AAAI now?

**No.** It is technically complete enough to upload, but strategically not ready. The current version is likely to receive split 5/6 scores and lose because it has no clear champion.

### 2. What is the biggest risk if submitted now?

A reviewer concludes that the paper combines an already-known reasoning/editing failure with a lexically targeted decoding intervention, while generalizing from false CounterFact edits to parametric knowledge editing broadly.

### 3. What is the most likely reason for low scores?

The most likely reason is **external-validity and construct-validity weakness**, not an obvious coding error:

- One counterfactual benchmark.
- Mostly one editor for the phenomenon.
- Shared R1 reasoning recipe.
- B0/B3 length and closure confounds.
- Low-precision permissive headline.
- Natural mechanism not identified.

### 4. Which experiment group should be added first?

**A non-counterfactual independent benchmark using strict semantic scoring.**

The minimum high-leverage battery is:

- Real temporal, synthetic-authoritative, or fictional-world edits.
- B0 versus B3 on the same edit.
- Standard direct-answer baseline.
- At least one large reasoning model.
- Strict OLD/NEW/NEITHER adjudication.
- Unedited-base control.

Immediately after that, run the length-matched reasoning-control battery.

### 5. Which section should be rewritten first?

**The abstract.**

It currently foregrounds the 19.3% permissive endpoint, gives too much weight to the cloze and route diagnostics, and compresses the causal boundary into one strong final sentence. Rewrite the abstract before changing the rest of the paper because it determines how every reviewer interprets the evidence.

### 6. What score pattern does the current version look like?

**6565**

- Technical: 6
- Experiments: 5
- Novelty: 6
- Writing/compliance: 5

This is a borderline-reject pattern with no champion.

### 7. After one serious revision, what is the highest realistic score pattern?

**7666** is the realistic ceiling after one substantial revision.

That requires:

- A successful non-counterfactual benchmark.
- Complete semantic validation.
- Standard direct-answer and length controls.
- A frozen reproducibility package.
- A much cleaner manuscript.

A **7766** pattern would require especially strong independent generalization or a more convincing semantic causal intervention.

### 8. Should the paper be split into main paper + appendix?

**Yes.**

The main paper should contain:

- Paired B0/B3 phenomenon.
- Decisive controls.
- Five-arm think-only intervention.
- One second benchmark or model/editor transfer.
- Concise limitations.

The appendix should contain:

- Route taxonomy.
- Cloze sanity check.
- Failed replay gate.
- Concept-direction null.
- Full dose ladder.
- All pairwise contrasts.
- Judge prompts and votes.
- Provenance manifests.
- General-benchmark boundaries.
- Every negative and superseded analysis.

### 9. Should the authors continue targeting AAAI or redirect to another venue?

**Continue targeting AAAI, but do not submit this version.**

The topic is suitable for AAAI, and the think-span intervention can support an AAAI-level contribution. If the authors cannot add a non-counterfactual benchmark and close the direct-answer/length-control gap, redirect to a more specialized knowledge-editing or language-model-analysis venue where a narrow but careful diagnostic paper faces a lower generality threshold.