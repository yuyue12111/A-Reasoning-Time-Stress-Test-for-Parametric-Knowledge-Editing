# Section 5 adversarial findings (W3-2, 12-agent workflow)

Three hunters with distinct lenses (self-contradiction, exceeds-ceiling, term misuse) over
Section 5, deduplicated and re-verified by a fourth agent against results.json, the
preregistration files and provenance_manifest.md.  Twenty survivors, ranked.  Items 2, 10, 13
and 15 were fixed in this round; the rest are open.

## Verified survivors, ranked by likelihood of changing a reviewer's verdict

Working copy `/Users/whyu/GitProjects/why-aaai27/paperwriting/manuscript/main.tex` (modified vs HEAD; §5 = lines 174–250). Every claim below was re-read in that file and checked against `paperwriting/results.json`, `paperwriting/provenance_manifest.md`, `prereg-esup.md`, `prereg-x2-x3.md`, or `plan.md`. Three hunter items were dropped and eleven merged; see the closing paragraph.

**1. Preregistration timing is stated more broadly than the record supports (main.tex:180).** Defect: "in a protocol recorded with its donors before any suppressed arm ran" is false — `prereg-esup.md:3` locks the file only "早于任何 D/P GPU 结果" and `prereg-esup.md:8` lists the treated arm as `T = 压 o_old = 现 fix (probe32b_sup.yaml cf200sup, 已在盘)` (already on disk), while `plan.md:212` (v1.27, 2026-06-24) already records that arm's headline outcome ES .495→.631 / RR .193→.085 four days before the prereg commit `2420cb8` (2026-06-28). Preserve: that the T-versus-P *designation as primary*, and the placebo donor list, were fixed before the P and D arms ran — the true and still-strong version of the anti-cherry-pick claim.

**2. "Harness errors only" is contradicted by the paper's own provenance record (main.tex:184).** Defect: the arm-wise *n* spread in Table 2 (198/198/196/199/200, main.tex:200–204, matching `/rq3/sup_battery/n`) is attributed entirely to harness error, but `provenance_manifest.md:37-39` states the placebo shards hold 200 unique B3 cases with error and `_meta` rows already excluded and "There is no degenerate row to drop", and `:73-74` states the 199-vs-200 difference "has no mechanism visible in the retrieved artifacts" — while `/rq3/sup_battery/_C_arm_M4` records the C arm at errors=4 with *n*=200, so error count does not track *n* in either direction. Preserve: the disclosure five lines later that the placebo arm is not byte-reproducible, and the fact that the unexplained row sits in the arm feeding the pre-specified primary contrast.

**3. "Dose-graded" survives in the abstract, the contribution list and the §5.1 heading after the body has withdrawn it twice (main.tex:27, 56, 175).** Defect: the only dose-ordered quantity is CLR (.545/.444/.384/.268/.146/.082 at `/rq3/alpha_sweep/CLR`), which main.tex:182 explicitly designates "a manipulation check … not an outcome", while both declared endpoints are non-monotone (`/rq3/alpha_sweep` ES .495/.596/.606/.639/.688/.660; RR .193/.138/.155/.105/.069/.069) and main.tex:186 says so verbatim — "Edit success and permissive reversion are not ordered across those settings" — with the footnote calling it "a dose ladder rather than a calibrated dose-response" and main.tex:233 "a signed ladder rather than a calibrated dose". Preserve: the manipulation check *is* monotone across the five suppressed settings and every suppressed setting sits below the zero-penalty setting — real evidence that the penalty acted, and that penalty=8 was not selected on a spike.

**4. Instrument precision is used to answer a power question, and the cited statistic argues the other way (main.tex:238).** Defect: the sentence first attributes the strict T−N null to thinness (118 paired cases, event rates .092/.042 from Table 2) and then denies it is "simply noise" on the strength of precision — which bounds false positives among rule-positive rows, not sensitivity — while `/metric_validation` and main.tex:72 record the strict rule's *recall* as .85 against the permissive .96, the lower of the two. Preserve: the honest self-report that the strict endpoint runs below permissive reversion in every arm and is the thinnest place in the battery, and the disclosure of both matchers' precision/recall.

**5. The abstract asserts the demonstration-of-no-effect reading §5.3 refuses (main.tex:27 vs 227).** Defect: "placebo and same-relation controls have near-null answer-level effects" attributes a magnitude the data do not bound — Table 2 gives P−N ES [−.046, .081] and C−N ES [−.046, .076] (main.tex:211–212), upper limits roughly two thirds of the treated T−P effect of +.122 — and main.tex:227 says "we set no equivalence margin, so these are failures to separate rather than demonstrations of no effect". Preserve: the abstract's ability to state that the controls do not separate from no suppression on any of the three endpoints, which is what the *p* values .709/1.00/.828 and .688/1.00/.828 actually license.

**6. A zero-touching interval is read as a real effect in §5.5 and as a failure to separate in §5.4 (main.tex:246 vs 238).** Defect: "on edit success that competitor is not a floor, at +.015 [.000,.035]" reads activity out of `/rq3/x2_memit14b_repair_replication/contrasts_B3/C_minus_N/ES`, which that run's own frozen gate classifies as compatible with zero (`/preregistered_decision` `"C_minus_N_ES_RR_RRs_compatible_with_zero": true`; `/sound_inference_decision` `"C_minus_N": "compatible with zero"`) and whose `p_bootstrap` of .0948 is the one *p* in the sentence not quoted, eight lines after −.051 [−.102, .000] with *p*=.073 is treated as reaching zero. Preserve: the genuine distinction the clause is reaching for — that the C−N *strict* contrast of .000 [.000, .000] is a degenerate boundary rather than an equivalence result, so the T−C null cannot be transferred to T−N by way of an "inert" C.

**7. "Stayed directional" hides a zero-crossing that the same section always states elsewhere (main.tex:248).** Defect: the secondary old-value comparison is `/rq3/x3_rome32b_active_paraphrase/fixed_N_B0_gate_secondary_old_only/T_minus_C` = −.0138 [−.042, .014], *p*=.4498, which the same file's `_status` calls "directional/null (110<140 cases)" and `/claim_ceiling` restricts to "只作 directional/null" — an interval §5.3 and §5.4 would call "compatible with zero" or "does not separate" when the arm at issue is a control. Preserve: the disclosure that the run delivered 110 of a preregistered 140-case floor, which is why the comparison is non-confirmatory in the first place.

**8. "Each with its own control" is false for the ROME-14B run (main.tex:243).** Defect: `/rq3/s10_14b_fix_replication/_status` records "N 臂=在盘 14B headline" and `/N_arm_headline/ES_B3` = .515, the same value as the Qwen-14B cell of `/capability/families` (`es_b3` = .515) reported in Table 1, so the "+.135 against no suppression" is a cross-run comparison against a reused earlier arm — whereas the MEMIT run in the next paragraph required a fresh N precisely because on-disk N failed provenance parity (`/rq3/x2_memit14b_repair_replication/source/n_config_reason`; `prereg-x2-x3.md:13`). Preserve: that the ROME-14B T arm was run at α=8, scope=think, *n*=200 under the headline protocol and is case-pairable, so the contrast remains paired even though the control is not fresh.

**9. The one strict separation offered against the battery's strict null was not a pre-specified endpoint there (main.tex:244).** Defect: −.040 [−.081, −.010] with *p*=.035 is presented as "strict separation where the Qwen-32B battery had none", but `plan.md:382` and `/rq3/s10_14b_fix_replication/_status` both record "prereg 主端点=ES@B3，不钉脆弱 b0ok-RR" — an unregistered secondary given the weight §5.4 reserves for pre-specified contrasts — and §5.5 more generally reports strict displacement for all three transfer runs while never reporting permissive reversion for any of them, though main.tex:180 declares permissive reversion primary and strict secondary. Preserve: the anti-cherry-pick posture of reporting the weak strict endpoint at all, and the fact that the ROME-14B ES contrast *is* the run's registered primary and does separate.

**10. "Changes direction" misdescribes the disclosure it points at (main.tex:229).** Defect: `provenance_manifest.md:28` and `:93-95` record P−N CLR as −.051 [−.102, .000] (*p*=.054) recorded and −.0556 [−.1061, −.0051] (*p*=.037) recomputed — the same negative sign in both derivations, with only the zero-crossing verdict differing — so the clause states a sign flip the record does not contain. Preserve: the reason the placebo's in-chain quantity is excluded from the body, namely that it is exactly the derivation-dependent number under dispute, and the pointer to the released provenance record carrying both columns.

**11. The competitor arm carries three mutually unsupportive evidential characterizations inside one subsection (main.tex:229, 231).** Defect: main.tex:229 says "the competitor is not inert" on a CLR contrast of −.071 [−.121, −.020] excluding zero, then declines to read its answer-level null as evidence of no effect while immediately cashing it as a bound on specificity, and main.tex:231 then calls the same arm "strong but largely inactive" on the basis of 18-of-200 and 24-of-400 changed rows in two *other* runs after conceding "This battery has no changed-row audit of its own" — and the subsection never says which characterization the specificity claim rests on. Preserve: the dissociation that is genuinely load-bearing (the C penalty visibly perturbs the chain here, yet the answer level does not move) and the honest statement that this battery lacks its own changed-row audit.

**12. "Does not turn on which control" is unqualified but true only of the two primary endpoints (main.tex:220 vs 238).** Defect: main.tex:238 reports the strict endpoint separating the treated arm from the placebo (*p*=.029, Table 2 line 208) and the competitor (*p*=.032, line 210) but not from no suppression (*p*=.073, line 209), so on one of the three endpoints the reading turns entirely on the control chosen. Preserve: the actual interval-width argument for ES and RR — T−P and T−N differ by less than the width of either interval (Table 2 lines 208–209), so the abstract's arm-wise levels are not an artifact of the control choice.

**13. The stated structural limitation is false as written, and the prediction it appeals to is never stated (main.tex:233).** Defect: "every arm here is an intervened condition" is contradicted by arm N, defined at main.tex:178 as "none (N)" penalized tokens and identified at main.tex:222 as the same unintervened Qwen-32B run as Table 1's largest Qwen cell; in the same line, "the four arms order as the frozen prediction stated" gives the reader no way to check what was predicted (`prereg-esup.md` fixes T < P ≈ N < D on RR/CLR and D ≤ N ≈ P < T on ES) and silently excludes C, which Table 2 includes in the same ordering. Preserve: the real limitation, which is that the causal demonstration requires an intervention and so cannot establish that the chain route is *required* in unintervened generation — the claim `prereg-esup.md` reserves under "不声称".

**14. "Dose-limited" is undefined and its actual limiter is nowhere in the text (main.tex:168, §4.4 — scope note: submitted as a §5 finding, lives in §4).** Defect: the qualifier is load-bearing, because it is what keeps the confirmatory RR null from counting against the chain-routing account, yet no dose is reported and the record shows the steering strength was capped at the smallest piloted level because α=2%/5% breached a pre-specified harm gate (`/wb_representation_repair/pilot_dose_response`: LocAcc .62/.39/.18, verdict "α*=1%"). Preserve: that the confirmatory null is reported as a null and not softened — the honesty of the negative result is the point of the paragraph.

**15. The 118 that carries the power argument cannot be found where it is cited (main.tex:238).** Defect: "count from the Section 4.4 re-analysis" points at §4.4, which reports only 106 CLR-positive and 90 CLR-zero cases (main.tex:165) and never states 118; the number lives only at `/rq3/clr_split_M1/mediation_2x2/n_b0ok`. Preserve: the deliberate choice not to publish per-arm strict event totals, which is why the denominator is quoted rather than the events.

**16. "Paired" switches axis and sign convention inside one sentence (main.tex:246).** Defect: "+.100 [.040,.160]" is cross-arm at fixed budget with positive = improvement, and "+.060 [−.020,.140]" three clauses later is cross-budget within one arm with positive = degradation (`/rq3/x2_memit14b_repair_replication/fresh_n_es_drop`), both labelled "paired" and both on ES. Preserve: the concession the second number exists to make — that the fresh N arm does not itself establish a reasoning-time drop in that cell, so the run transfers the intervention and not the gap.

**17. The paraphrase headline and its own invalidation share a paragraph with no statement of which survives (main.tex:248).** Defect: +.055 [.020, .093] is computed over a probe set the paper's own blind audit finds valid in 30 of 40 paraphrases and both-valid in 11 of 20 cases at κ=.444, with "no row was filtered and no valid-subset re-analysis was run" — full disclosure, but the reader is left to decide whether the leading number is interpretable. Preserve: the disclosure itself and the "active application, not portability" framing, which is what `/rq3/x3_rome32b_active_paraphrase/claim_ceiling` permits.

**18. The definition of "manipulation check" does not cover two of its three uses (main.tex:182).** Defect: defined at main.tex:182 in penalty-specific terms ("whether the penalty acted inside the span"), it is first used at main.tex:168 for the concept-direction experiment, which applies a direction injection and no token penalty, and it cannot function as a check for arm C, since CLR counts old-value mentions while C penalizes competitor tokens — making the −.071 at main.tex:229 an off-target effect rather than evidence the C penalty fired, which is exactly what item 11 needs and main.tex:231 says the battery lacks. Preserve: the anti-tautology role of the designation — CLR is not an outcome and no endpoint claim rests on it.

**19. One of the "three properties" is analytic (main.tex:182).** Defect: the discriminating half of the scope ablation (.580 vs .727 at B₀) holds by construction, since main.tex:184 states that at B₀ "the think span is empty, so a think-scoped processor has nothing to act on", and at the reported budget the two scopes give .639 against .670 with an identical leakage check of .268 (`/rq3/alpha_sweep/scope_ablation`), which the sentence concedes. Preserve: the genuine content — that answer-scoped suppression inflates the B₀ level that the reversion gate conditions on, and think-scoping does not, so the gate is not contaminated by the treatment.

**20. Four terms carry multiple live senses with no definition; one hyperparameter is never named (bundle).** Defect: "arm-wise" means cross-arm at main.tex:74 ("arm-wise contrasts use case intersections") and per-arm marginal at main.tex:184, 216, 222; "gate" denotes the B₀ success gate (118, 158, 165, 216, 238), a judge membership filter (134), a preregistered stop rule (147, 150) and an equivalence threshold (264); "floor" denotes a control baseline (43, 180, 220), a degenerate zero (166, 246) and a preregistered minimum case count (248) — where it is doing the disclosure work of item 7; and the intervention's single hyperparameter is introduced only as "a fixed logit penalty" (178) with values 0–16 (186) and no symbol or units, while §3.1 calls an unrelated ROME hyperparameter "the update clamp" and moves it between 4 and 2. Preserve: each site's current numeric content and pointer bindings — this is a naming pass, not a claim change.

**Dropped as wording preference, not defect.** (a) The claimed §5.1-versus-§5.4 contradiction over reporting the strict endpoint prominently: main.tex:238 states the policy explicitly ("reported at the prominence of the primary ones precisely because it is weakest"), which is a disclosed choice, not a contradiction — its live residue is item 9. (b) The "complete-pair / complete-case / within-edit / within-case" naming complaint: each footnote states its own completeness axis (main.tex:122, 216, 222), so this is folded into item 20 rather than standing alone. (c) The hunters' framing of main.tex:227 as the surviving calibration example: that opener has already been repaired on disk to "failures to separate rather than demonstrations of no effect" — its live residue is the abstract, item 5.

**Merges.** Items 4, 6, 7, 9 and 11 each absorb two hunter reports (a self-contradiction reading and an exceeds-ceiling reading of the same sentence); item 2 absorbs both "harness errors only" reports; item 3 absorbs the heading-level and abstract-level "dose-graded" reports; item 13 absorbs the "every arm is intervened" and "frozen prediction" reports on the same line."
  },
  "workflowProgress": [
    {
      "type": "workflow_phase",
      "index": 1,
      "title": "Evidence"
    },
    {
      "type": "workflow_phase",
      "index": 2,
      "title": "Classify"
    },
    {
      "type": "workflow_phase",
      "index": 3,
      "title": "Refute"
    },
    {
      "type": "workflow_phase",
      "index": 4,
      "title": "Hunt"
    },
    {
      "type": "workflow_phase",
      "index": 5,
      "title": "Synthesize"
    },
    {
      "type": "workflow_agent",
      "index": 1,
      "label": "A4:locality-budget",
      "phaseIndex": 1,
      "phaseTitle": "Evidence",
      "agentId": "a2539ca98765fcb33",
      "model": "claude-opus-5",
      "state": "done",
      "startedAt": 1785136982619,
      "queuedAt": 1785136982601,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "lastToolSummary": "All four recorded `_loc` values reproduce exactly from the …",
      "promptPreview": "You are auditing a repository at /Users/whyu/GitProjects/why-aaai27. IMPORTANT: work ONLY in that absolute path
(a stale git worktree exists elsewhere; ignore it). You are read-only: do not edit, write, or run
anything that mutates files. Ground every claim in a concrete file:line or a command you ran and its
output. If the evidence does not exist, say "unattributable" rather than inferring. Your …",
      "lastProgressAt": 1785137454220,
      "tokens": 162271,
      "toolCalls": 57,
      "durationMs": 471601,
      "resultPreview": "{"answer":"All four recorded `_loc` values reproduce exactly from the raw generation shards in the workspace, and they are NOT all at the same thinking budget: three are B0 and one (Qwen-32B) is B3. Per checkpoint — Qwen-1.5B .954 = **B0** (same run's B3 Loc = .913); Qwen-7B = not in results.json (null); Qwen-14B = not in results.json (null); Qwen-32B .958 = **B3** (same run's B0 Loc = .970, so .9…"
    },
    {
      "type": "workflow_agent",
      "index": 2,
      "label": "A3:pool-vintage",
      "phaseIndex": 1,
      "phaseTitle": "Evidence",
      "agentId": "aada8aa35000bc4f4",
      "model": "claude-opus-5",
      "state": "done",
      "startedAt": 1785136982620,
      "queuedAt": 1785136982602,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "lastToolSummary": "ESTABLISHED on all four links. The case pool `data/counterf…",
      "promptPreview": "You are auditing a repository at /Users/whyu/GitProjects/why-aaai27. IMPORTANT: work ONLY in that absolute path
(a stale git worktree exists elsewhere; ignore it). You are read-only: do not edit, write, or run
anything that mutates files. Ground every claim in a concrete file:line or a command you ran and its
output. If the evidence does not exist, say "unattributable" rather than inferring. Your …",
      "lastProgressAt": 1785137389751,
      "tokens": 104258,
      "toolCalls": 41,
      "durationMs": 407131,
      "resultPreview": "{"answer":"ESTABLISHED on all four links. The case pool `data/counterfact.prefiltered.jsonl` (248 survivors of a 600-candidate frame, then seed-42 sampled to 200) was produced by `src/prefilter.py` on or before 2026-06-17, and its keep/drop decision was made by `metrics.hit` in its pre-fix form — pure substring matching over the full alias table including 287 one-to-three-character ISO country/lan…"
    },
    {
      "type": "workflow_agent",
      "index": 3,
      "label": "A2:b0-filter",
      "phaseIndex": 1,
      "phaseTitle": "Evidence",
      "agentId": "a307f9de098fb855a",
      "model": "claude-opus-5",
      "state": "done",
      "startedAt": 1785136982620,
      "queuedAt": 1785136982602,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "lastToolSummary": "RUNBOOK.md:79's "B0 实测 ~50%" is a parenthetical claim abo…",
      "promptPreview": "You are auditing a repository at /Users/whyu/GitProjects/why-aaai27. IMPORTANT: work ONLY in that absolute path
(a stale git worktree exists elsewhere; ignore it). You are read-only: do not edit, write, or run
anything that mutates files. Ground every claim in a concrete file:line or a command you ran and its
output. If the evidence does not exist, say "unattributable" rather than inferring. Your …",
      "lastProgressAt": 1785137435562,
      "tokens": 162782,
      "toolCalls": 50,
      "durationMs": 452942,
      "resultPreview": "{"answer":"RUNBOOK.md:79's \\"B0 实测 ~50%\\" is a parenthetical claim about the PREFILTER SURVIVAL RATE measured with `--budget B0` — i.e. the fraction of candidate CounterFact requests the unedited Qwen-7B would have been kept by, had the keep-rule been evaluated on a zero-thinking generation. It is a documentation note with NO surviving run behind it: no log, no shard, no merged pool, no commit, no…"
    },
    {
      "type": "workflow_agent",
      "index": 4,
      "label": "A1:figure-sign",
      "phaseIndex": 1,
      "phaseTitle": "Evidence",
      "agentId": "a83bfc236a84ace95",
      "model": "claude-opus-5",
      "state": "done",
      "startedAt": 1785136982621,
      "queuedAt": 1785136982602,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "lastToolSummary": "Figure 1 panel A plots ES_B0 − ES_B3 (the paired DROP; posi…",
      "promptPreview": "You are auditing a repository at /Users/whyu/GitProjects/why-aaai27. IMPORTANT: work ONLY in that absolute path
(a stale git worktree exists elsewhere; ignore it). You are read-only: do not edit, write, or run
anything that mutates files. Ground every claim in a concrete file:line or a command you ran and its
output. If the evidence does not exist, say "unattributable" rather than inferring. Your …",
      "lastProgressAt": 1785137261316,
      "tokens": 98567,
      "toolCalls": 30,
      "durationMs": 278695,
      "resultPreview": "{"answer":"Figure 1 panel A plots ES_B0 − ES_B3 (the paired DROP; positive = edit success lost after reasoning), and the figure itself says so twice — the y-axis label carries the literal arithmetic \\"Paired ES change (ES_{B_0}−ES_{B_3})\\" (src/plots.py:564) and an in-axes gloss reads \\"positive = lower edit success after reasoning\\" (src/plots.py:572). Panel B carries NO arithmetic and no \\"posit…"
    },
    {
      "type": "workflow_agent",
      "index": 5,
      "label": "classify:section4-gates",
      "phaseIndex": 2,
      "phaseTitle": "Classify",
      "agentId": "a7a99487878109e31",
      "model": "claude-opus-5",
      "state": "done",
      "startedAt": 1785137454228,
      "queuedAt": 1785137454221,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "promptPreview": "You are auditing a repository at /Users/whyu/GitProjects/why-aaai27. IMPORTANT: work ONLY in that absolute path
(a stale git worktree exists elsewhere; ignore it). You are read-only: do not edit, write, or run
anything that mutates files. Ground every claim in a concrete file:line or a command you ran and its
output. If the evidence does not exist, say "unattributable" rather than inferring. Your …",
      "lastProgressAt": 1785137752488,
      "tokens": 84028,
      "toolCalls": 16,
      "durationMs": 298260,
      "resultPreview": "{"strings":[{"text":"This section assembles the diagnosis that motivates the primary intervention","verdict":"must_stay_in_body","role":"scope","reason":"main.tex:129 — this is the only sentence that subordinates the section to Section 5 (it motivates the intervention rather than establishing it), so without it a section titled \\\\section{Causal Diagnosis} reads as delivering the causal identificat…"
    },
    {
      "type": "workflow_agent",
      "index": 6,
      "label": "refute:body-only-reader",
      "phaseIndex": 3,
      "phaseTitle": "Refute",
      "agentId": "af90e31a068687064",
      "model": "claude-opus-5",
      "state": "done",
      "startedAt": 1785137752498,
      "queuedAt": 1785137752490,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "lastToolSummary": "Read §4 in full (paperwriting/manuscript/main.tex:126-172) …",
      "promptPreview": "You are auditing a repository at /Users/whyu/GitProjects/why-aaai27. IMPORTANT: work ONLY in that absolute path
(a stale git worktree exists elsewhere; ignore it). You are read-only: do not edit, write, or run
anything that mutates files. Ground every claim in a concrete file:line or a command you ran and its
output. If the evidence does not exist, say "unattributable" rather than inferring. Your …",
      "lastProgressAt": 1785138045856,
      "tokens": 87137,
      "toolCalls": 18,
      "durationMs": 293358,
      "resultPreview": "{"reasoning":"Read §4 in full (paperwriting/manuscript/main.tex:126-172) plus its upstream promises (main.tex:27 abstract, :45 intro, :72 route-panel footnote) and paperwriting/manuscript/supplement.tex:1-85, then checked each candidate against paperwriting/results.json and the checker in src/check_manuscript.py.\
\
All four candidates are refuted; none should move. Evidence:\
\
(1) /rq2_logitlens…"
    },
    {
      "type": "workflow_agent",
      "index": 7,
      "label": "refute:inference-chain",
      "phaseIndex": 3,
      "phaseTitle": "Refute",
      "agentId": "ab86d8449acd47909",
      "model": "claude-opus-5",
      "state": "done",
      "startedAt": 1785137752498,
      "queuedAt": 1785137752490,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "lastToolSummary": "Read Section 4 as it stands: main.tex:126-172 (footnote at …",
      "promptPreview": "You are auditing a repository at /Users/whyu/GitProjects/why-aaai27. IMPORTANT: work ONLY in that absolute path
(a stale git worktree exists elsewhere; ignore it). You are read-only: do not edit, write, or run
anything that mutates files. Ground every claim in a concrete file:line or a command you ran and its
output. If the evidence does not exist, say "unattributable" rather than inferring. Your …",
      "lastProgressAt": 1785138018861,
      "tokens": 89218,
      "toolCalls": 15,
      "durationMs": 266363,
      "resultPreview": "{"reasoning":"Read Section 4 as it stands: main.tex:126-172 (footnote at :129; route census at :134-141; replay at :146-153; length account at :155-162; boundary test at :164-172). Checked every candidate against (a) whether another BODY sentence carries the same information, (b) results.json, (c) supplement.tex, (d) src/check_manuscript.py.\
\
KEEP #1 — \\"audit sample overlap and membership compo…"
    },
    {
      "type": "workflow_agent",
      "index": 8,
      "label": "refute:history",
      "phaseIndex": 3,
      "phaseTitle": "Refute",
      "agentId": "a04ac70436363e4c3",
      "model": "claude-opus-5",
      "state": "done",
      "startedAt": 1785137752498,
      "queuedAt": 1785137752490,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "lastToolSummary": "All four candidates are REFUTED; each stays in the body. ME…",
      "promptPreview": "You are auditing a repository at /Users/whyu/GitProjects/why-aaai27. IMPORTANT: work ONLY in that absolute path
(a stale git worktree exists elsewhere; ignore it). You are read-only: do not edit, write, or run
anything that mutates files. Ground every claim in a concrete file:line or a command you ran and its
output. If the evidence does not exist, say "unattributable" rather than inferring. Your …",
      "lastProgressAt": 1785138182469,
      "tokens": 137535,
      "toolCalls": 35,
      "durationMs": 429971,
      "resultPreview": "{"refuted":true,"strings_that_must_stay":[{"text":"audit sample overlap and membership composition","inference_it_prevents":"That the n=23 cloze-intact sample is known to sit inside, or overlap, the answer-gated committed-OLD population of the census at main.tex:134 — i.e. that the edit was verified installed in the same reversions Section 4 then taxonomizes. main.tex:170 places the two observatio…"
    },
    {
      "type": "workflow_agent",
      "index": 9,
      "label": "hunt:contradiction",
      "phaseIndex": 4,
      "phaseTitle": "Hunt",
      "agentId": "af7cd2128cfd5e6e9",
      "model": "claude-opus-5",
      "state": "done",
      "startedAt": 1785138182479,
      "queuedAt": 1785138182471,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "promptPreview": "You are auditing a repository at /Users/whyu/GitProjects/why-aaai27. IMPORTANT: work ONLY in that absolute path
(a stale git worktree exists elsewhere; ignore it). You are read-only: do not edit, write, or run
anything that mutates files. Ground every claim in a concrete file:line or a command you ran and its
output. If the evidence does not exist, say "unattributable" rather than inferring. Your …",
      "lastProgressAt": 1785138701328,
      "tokens": 126860,
      "toolCalls": 12,
      "durationMs": 518849,
      "resultPreview": "{"findings":[{"category":"self_contradiction","quote":"So the competitor perturbs what the chain says, while at the answer level the comparison is compatible with zero, which we do not read as evidence of no effect.  That bounds specificity rather than supplying evidence: the evidence is the contrast fixed in advance, T versus P.","problem":"§5.3 (line 229): the sentence denies that the answer-lev…"
    },
    {
      "type": "workflow_agent",
      "index": 10,
      "label": "hunt:ceiling",
      "phaseIndex": 4,
      "phaseTitle": "Hunt",
      "agentId": "aee8be8c8c9ff5a76",
      "model": "claude-opus-5",
      "state": "done",
      "startedAt": 1785138182480,
      "queuedAt": 1785138182471,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "promptPreview": "You are auditing a repository at /Users/whyu/GitProjects/why-aaai27. IMPORTANT: work ONLY in that absolute path
(a stale git worktree exists elsewhere; ignore it). You are read-only: do not edit, write, or run
anything that mutates files. Ground every claim in a concrete file:line or a command you ran and its
output. If the evidence does not exist, say "unattributable" rather than inferring. Your …",
      "lastProgressAt": 1785138818439,
      "tokens": 155466,
      "toolCalls": 29,
      "durationMs": 635959,
      "resultPreview": "{"findings":[{"category":"exceeds_ceiling","quote":"The primary contrast was fixed in advance as T versus P---the old-answer effect above the placebo floor---in a protocol recorded with its donors before any suppressed arm ran.","problem":"The prereg that fixes T-versus-P (prereg-esup.md, committed 2026-06-28 as 2420cb8) states its own lock only as \\"早于任何 D/P GPU 结果\\" (earlier than any D/P results…"
    },
    {
      "type": "workflow_agent",
      "index": 11,
      "label": "hunt:terms",
      "phaseIndex": 4,
      "phaseTitle": "Hunt",
      "agentId": "addb1254324b1c4f7",
      "model": "claude-opus-5",
      "state": "done",
      "startedAt": 1785138182480,
      "queuedAt": 1785138182471,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "promptPreview": "You are auditing a repository at /Users/whyu/GitProjects/why-aaai27. IMPORTANT: work ONLY in that absolute path
(a stale git worktree exists elsewhere; ignore it). You are read-only: do not edit, write, or run
anything that mutates files. Ground every claim in a concrete file:line or a command you ran and its
output. If the evidence does not exist, say "unattributable" rather than inferring. Your …",
      "lastProgressAt": 1785138708033,
      "tokens": 128823,
      "toolCalls": 14,
      "durationMs": 525553,
      "resultPreview": "{"findings":[{"category":"self_contradiction","quote":"The signed, dose-graded intervention offsets the edit-success loss and lowers the resurfacing rate from 19.3\\\\% to 8.5\\\\%; placebo and same-relation controls have near-null answer-level effects.","problem":"\\"dose-graded\\" (abstract line 27; repeated as a contribution at line 56, \\"a signed, dose-graded intervention confined to the think span\\…"
    },
    {
      "type": "workflow_agent",
      "index": 12,
      "label": "synthesize:section5",
      "phaseIndex": 5,
      "phaseTitle": "Synthesize",
      "agentId": "af2a8aaf21d995bee",
      "model": "claude-opus-5",
      "state": "done",
      "startedAt": 1785138818442,
      "queuedAt": 1785138818441,
      "attempt": 1,
      "lastToolName": "Bash",
      "lastToolSummary": "cd /Users/whyu/GitProjects/why-aaai27 && python3 -c " impor…",
      "promptPreview": "You are auditing a repository at /Users/whyu/GitProjects/why-aaai27. IMPORTANT: work ONLY in that absolute path
(a stale git worktree exists elsewhere; ignore it). You are read-only: do not edit, write, or run
anything that mutates files. Ground every claim in a concrete file:line or a command you ran and its
output. If the evidence does not exist, say "unattributable" rather than inferring. Your …",
      "lastProgressAt": 1785139185081,
      "tokens": 114049,
      "toolCalls": 32,
      "durationMs": 366639,
      "resultPreview": "## Verified survivors, ranked by likelihood of changing a reviewer's verdict

Working copy `/Users/whyu/GitProjects/why-aaai27/paperwriting/manuscript/main.tex` (modified vs HEAD; §5 = lines 174–250). Every claim below was re-read in that file and checked against `paperwriting/results.json`, `paperwriting/provenance_manifest.md`, `prereg-esup.md`, `prereg-x2-x3.md`, or `plan.md`. Three hunter item…"
    }
  ],
  "totalTokens": 1450994,
  "totalToolCalls": 349