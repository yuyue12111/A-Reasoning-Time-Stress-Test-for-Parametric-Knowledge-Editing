# Pre-registration · Study 2 (ARR revision)

**Status: DRAFT.** Frozen when the freeze entry of `prereg-arr-registry.md` (append-only) records this
file's SHA-256, the commit, the analysis code's SHA-256 and a third-party timestamp (OSF registration),
before the first Study-2 delta is computed. After freezing, this file never changes: deviations go to
`prereg-arr-deviations.md` (§8) and pool manifests are registered in the registry (§9).

## 1 Purpose
Study 1 (the AAAI data: six R1-distilled checkpoints, one 200-case pool selected with Qwen-7B at B3,
greedy HF generation) was exploratory: the scope "largest checkpoint per family", the retention
contrast and the name-containment exclusion were all chosen after seeing its data. Study 2 tests
those findings on fresh cases, with pools selected without any reasoning-time output, a new inference
engine, more editors and more post-training recipes.

## 2 Materials
- **Models.** DeepSeek-R1-Distill-Qwen 1.5B/7B/14B/32B; DeepSeek-R1-Distill-Llama 8B/70B;
  Qwen2.5-32B-Instruct (no reasoning post-training; prompted chain); QwQ-32B (RL-trained reasoning).
- **Editors.** ROME on every model; MEMIT and AlphaEdit on R1-Distill-Qwen-32B; in-context editing (IKE:
  the new fact stated in the user turn) on R1-Distill-Qwen-32B as a non-parametric reference.
  Hyperparameters: `experiments/rt/deltas_models.yaml` at the frozen commit.
- **Data.** CounterFact (21,919 cleaned cases, `data/counterfact.jsonl`).
- **Pool.** Remove every case_id used in any earlier run (list and sources in the pool summary) →
  shuffle with seed 2027 → first 1,600 candidates → for each model, its own unedited base answers the
  efficacy prompt at B0 (greedy); a case qualifies if the answer contains the old value, does not
  contain the new value (current matcher, subject scrubbed), and the subject name does not contain the
  old value as a whole word. Each model uses its first 400 qualified cases in candidate order (Llama-70B:
  first 400 as well; it was 200 until 2026-09-29, raised for power before any Llama-70B screen had been
  qualified). If fewer than 400 of the 1,600 candidates qualify for a model, the model uses every
  qualified case; no further candidates are drawn and the smaller n is reported. A fact used under
  another case id in an earlier run is excluded (`exclude_facts` in the pool configuration: cf_4298 =
  mquake_1366). No reasoning-time output is used for selection.
- **H2b group (R1-Distill-Qwen-32B).** From the same 1,600 candidates and the same base B0 screen, the
  first 300 in candidate order whose base answer names neither value (other rules as above): the
  "unknown" group for the prior-knowledge contrast (§5).
- *Record.* The shortfall rule and per-model manifest registration were added on 2026-09-29 after the
  32B screen had been qualified; the 70B size, the fact exclusion and the H2b group were added the same
  day after an independent review. At that point the only Study-2 data seen were the candidates' base
  B0 answers (screen data); no Study-2 case had been edited or generated at B3.

## 3 Procedure
- Engine v2 (`src/rt/`, REVISION.md §4): the edit's rank-1 update is computed by EasyEdit in fp32 and
  applied per batch row by a forward hook; generation is batched bf16. Each request sees only its own edit.
- BOS: none for Qwen-based R1 models, BOS for Llama-based ones, none for ChatML templates. This matches
  Study 1's headline cells (the 32B N and T arms ran without BOS). Correction of an earlier record:
  Study 1's D/P/C arms and sampling run, and most likely its unedited 32B base, ran with BOS
  (`think_budget._gen` added it by default from 2026-06-25); in Study 1 the 32B ES gap is .106 without
  BOS and .110 with it.
- Decoding: the checkpoint's own generation_config is not applied; every decoding parameter is passed
  explicitly and recorded. Greedy is primary everywhere; sampling uses temperature 0.6, top-p 0.95,
  top-k 50 (Study 1's effective settings).
- Budgets: B0 = pre-closed empty think span; B3 = native chain capped at 8,192 tokens (closed by the
  harness if the model does not); B0P = fixed short canned thought; B1 = chain capped at 256 tokens.
  The answer is generated after `</think>` with a 256-token cap. Prompts reuse `src/think_budget.py`.
  For Qwen2.5-32B-Instruct, B0 is a direct answer and B3 a prompted step-by-step answer (template in the
  frozen config).
- Probes: efficacy, first paraphrase, first neighbourhood prompt.
- Conditions (R1-Distill-Qwen-32B, ROME): unedited base; N (no suppression); T/D/P/C think-span logit
  penalty (8) on the first tokens of old value / new value / frequency-length-matched placebo donor /
  same-relation competitor donor, efficacy probe only; B0P; B1; answers after the case's own chain,
  a length-matched content-free filler, and another case's chain; edit strength α ∈ {1, 2, 3} at B0/B3
  and α = 0.5 at B0 only; IKE (efficacy probe); 4 sampled B3 runs (seeds 0–3); MEMIT and AlphaEdit
  (N). H2b group: unedited base and N at B0/B3, efficacy probe. All other models: unedited base and N
  at B0/B3. Qwen2.5-32B-Instruct and QwQ-32B run last, after everything else; their results are
  reported if they run.

## 4 Endpoints
- **ES_b**: answer contains the new value and not the old one (lexical, `src/metrics.py`).
- **Semantic ES / reversion**: two judge families (google/gemma-3-27b-it, mistralai/Mistral-Small-3.1-24B-
  Instruct-2503; `src/rt/judge.py`, prompt sha256 `dc4649065540f3a92e08be083520b75c2e7a93697c7289ecf385cc5a8f96771c`)
  see only the question and the final answer, with the subject name masked; each item is scored under both
  option orders and the probabilities averaged; the two judges' probabilities are averaged, and an exact
  NEW/OLD tie counts as unclear. **Switch rule, decided on Study 1 before any Study-2 outcome is
  scored:** 200 Study-1 items (R1-Distill-Qwen-32B and Llama-70B, stratified by budget × lexical cell,
  floor 10 per stratum; the package in `results/annot/`) are labelled independently by two annotators
  under the same written rules, and the judges score the same rows. If the mean of Cohen's κ between the
  judge ensemble and each annotator is ≥ .70 for both the binary ES label and the binary reversion
  label, semantic ES and semantic reversion are the primary endpoints; otherwise the lexical ES and
  strict reversion (old present, new absent) are. If no human κ exists by 2026-10-05 AoE, the lexical
  endpoints are primary. A further 200 Study-2 items are labelled the same way; their κ is reported and
  does not change the choice.
- **Retention contrast**: among cases whose base answers old at B0 and whose edit succeeds at B0,
  P(edited loses success at B3) − P(base loses the old answer at B3), paired within case. "Base answers
  old at B0" is read from the Study-2 base run (same engine run as the edited rows), not from the screen.
- Secondary: permissive reversion (any old mention among B0 successes), erosion and repair, paraphrase
  success, locality (neighbour answer correct; new value not leaked).

## 5 Hypotheses and tests
Paired bootstrap over cases (10,000 resamples, seed 42), percentile 95% CI, two-sided p.
- **H1 (gap).** ES_B0 − ES_B3 > 0 at R1-Distill-Qwen-32B and R1-Distill-Llama-70B. Holm over the six
  R1 checkpoints.
- **H2 (edit specificity).** Retention contrast > 0 at 14B, 32B and 70B. Holm over the six R1 checkpoints.
- **H2b (prior knowledge, 32B).** The ES drop (N) in the main pool (base names the old value at B0)
  minus the ES drop in the H2b group (base names neither value) > 0. The groups are independent case
  sets: cases are resampled within each group. One test, α = .05, outside the Holm families.
  Rationale: if reasoning pulls the stored fact back, the drop concentrates where the model knows the
  old value; if edited answers are merely unstable under reasoning, it does not (Study 1, base names
  / misses the old value at B0: 32B +.125 vs +.043, 70B +.153 vs −.047, about 45 missing cases each;
  the missing group's drop is ≤ 0 in five of six checkpoints).
- **H3 (control point, 32B).** T − P: ES > 0 and reversion < 0; D − P: ES < 0. Holm over the three.
  Both contrasts use the frequency/length-matched placebo as reference, and every arm of a case runs in
  the same generation batch. (First written on 2026-09-28 as D − N; changed to D − P on 2026-09-29,
  before any Study-2 data, because P is the matched reference for both suppression targets. Study 1
  cannot estimate T − P or D − N cleanly: its N/T arms ran without BOS and its D/P/C arms with BOS.)
- **Secondary (reported whatever the outcome).** T − N, D − N and T − C (C: same-relation competitor,
  a specificity check); P − N with its CI (no equivalence claim); erosion > 0 at every checkpoint; repair lower at 32B
  than at 1.5B and at 70B than at 8B; ES drop under MEMIT, AlphaEdit and IKE at 32B; ES drop and
  retention contrast for Qwen2.5-32B-Instruct and QwQ-32B; ES at B0 and B3 as a function of α and the
  α needed for 80% ES at each budget; per-edit reliability under sampling (share of greedy-B0 successes
  that fail at B3 in at least one of seeds 0–2, against the same statistic on B0 samples as the noise
  floor; seed 3 reported separately); ES(B0) − ES(B0P) and ES(B0) − ES(B1) at 32B (a closed span with
  a canned thought; a 256-token chain); ES after own chain vs filler
  vs swapped chain; locality at B3.
- **Analysis conventions** (implemented in `src/rt/study2.py`, frozen with this file). A case missing
  or excluded (error row, fit error) counts against the 98% completeness rule. A Holm family keeps its
  size when a member has no estimate; that member enters with p = 1. A hypothesis passes when it is
  rejected (two-sided, after Holm where applicable) and its point estimate has the predicted sign. The
  H2b groups are the screen-defined main pool and unknown group; the Study-2 base run's B0 agreement
  with that definition is reported. Sampling reliability takes the greedy-B0 successes from rome_N.
  Repair across checkpoints (different pools) uses a two-group bootstrap. The α needed for 80% ES is
  the smallest grid α whose point estimate reaches .80, with linear interpolation, no CI. Locality:
  the neighbour answer names o_old and does not name o_new (subject not scrubbed). Degenerate-output
  filtering (secondary) drops a case if any row the estimate reads is flagged. Under the semantic
  endpoint, "base answers old" is the judges' OLD label.
- **Exploratory.** Edit-activation traces and positional gating (`src/rt/mech.py`); plausibility-target
  edits (`src/rt/targets.py`) if run.

## 6 Exclusions
Rows with generation errors, and edits whose rank-1 fit error exceeds 1e-4, are excluded and counted.
**Completeness:** before any estimate, every condition is checked against its manifest; chunks that
failed are re-run with a smaller batch; an estimate is reported only when at least 98% of the manifest's
cases have every row it needs, and the missing cases are listed with it.
Degenerate outputs are flagged with the existing detector (`src/score_pilot.py --drop-degenerate`);
results are reported with and without them, the unfiltered analysis being primary.

## 7 Gates
- **G0 (engine parity, before any Study-2 delta):** v2 rerun of Study 1's 32B pool (ROME, N, B0/B3):
  complete (all 198 paired Study-1 cases), ES drop inside Study 1's fixed 95% CI [.030, .182], per-case
  B0 agreement ≥ 85%. What each failure leads to was committed before the verdict (REVISION.md §4).
- **Submission gate:** H1 and H2 pass at 32B, and the semantic ES drop (or lexical, per the switch)
  keeps a CI above zero at 32B and 70B.

## 8 Deviations
Logged in `prereg-arr-deviations.md` with timestamp, reason and whether outcome data had been seen.

## 9 Freeze record
Kept in `prereg-arr-registry.md` (append-only), so this file does not change after freezing. The pool
procedure (candidates sha256, screen configuration, code) is frozen with this file. A manifest is a
deterministic output of that procedure on an unedited base, so manifests are not choices: each model's
manifest sha256 is appended to the registry before that model's first Study-2 delta is computed, and a
model whose screen finishes later does not hold back the others. The analysis code
(`src/rt/study2.py`) is frozen with this file and its sha256 recorded in the freeze entry.
