# Pre-registration · Study 2 (ARR revision)

**Status: DRAFT.** Frozen when this file's SHA-256, the commit hash and the pool manifests' SHA-256
are recorded in §9 and the first Study-2 delta file carries a later server timestamp. After freezing,
any change is a logged deviation (§8), never an edit to this text.

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
  first 200). No reasoning-time output is used for selection.

## 3 Procedure
- Engine v2 (`src/rt/`, REVISION.md §4): the edit's rank-1 update is computed by EasyEdit in fp32 and
  applied per batch row by a forward hook; generation is batched bf16. Each request sees only its own edit.
- BOS as in Study 1: none for Qwen-based R1 models, BOS for Llama-based ones, none for ChatML templates.
- Budgets: B0 = pre-closed empty think span; B3 = native chain capped at 8,192 tokens (closed by the
  harness if the model does not); B0P = fixed short canned thought; B1 = chain capped at 256 tokens.
  The answer is generated after `</think>` with a 256-token cap. Prompts reuse `src/think_budget.py`.
  For Qwen2.5-32B-Instruct, B0 is a direct answer and B3 a prompted step-by-step answer (template in the
  frozen config).
- Probes: efficacy, first paraphrase, first neighbourhood prompt.
- Conditions (R1-Distill-Qwen-32B, ROME): unedited base; N (no suppression); T/D/P/C think-span logit
  penalty (8) on the first tokens of old value / new value / frequency-length-matched placebo donor /
  same-relation competitor donor, efficacy probe only; B0P; B1; answers after the case's own chain,
  a length-matched content-free filler, and another case's chain; edit strength α ∈ {0.5, 1, 2, 3};
  IKE; 4 sampled B3 runs (temperature 0.6, seeds 0–3). All other models: unedited base and N at B0/B3.
- Decoding: greedy is primary everywhere.

## 4 Endpoints
- **ES_b**: answer contains the new value and not the old one (lexical, `src/metrics.py`).
- **Semantic ES / reversion**: two judge families (`src/rt/judge.py`), blind to model, arm and budget;
  200 items double-annotated by humans. **Switch rule:** if Cohen's κ between the human consensus and the
  judge majority is ≥ .70, semantic ES and semantic reversion are the primary endpoints; otherwise the
  lexical ES and strict reversion (old present, new absent) are.
- **Retention contrast**: among cases whose base answers old at B0 and whose edit succeeds at B0,
  P(edited loses success at B3) − P(base loses the old answer at B3), paired within case.
- Secondary: permissive reversion (any old mention among B0 successes), erosion and repair, paraphrase
  success, locality (neighbour answer correct; new value not leaked).

## 5 Hypotheses and tests
Paired bootstrap over cases (10,000 resamples, seed 42), percentile 95% CI, two-sided p.
- **H1 (gap).** ES_B0 − ES_B3 > 0 at R1-Distill-Qwen-32B and R1-Distill-Llama-70B. Holm over the six
  R1 checkpoints.
- **H2 (edit specificity).** Retention contrast > 0 at 14B, 32B and 70B. Holm over the six R1 checkpoints.
- **H3 (control point, 32B).** T − P: ES > 0 and reversion < 0; D − N: ES < 0. Holm over the three.
- **Secondary (reported whatever the outcome).** Erosion > 0 at every checkpoint; repair lower at 32B
  than at 1.5B and at 70B than at 8B; ES drop under MEMIT, AlphaEdit and IKE at 32B; ES drop and
  retention contrast for Qwen2.5-32B-Instruct and QwQ-32B; ES at B0 and B3 as a function of α and the
  α needed for 80% ES at each budget; per-edit reliability under sampling; ES after own chain vs filler
  vs swapped chain; locality at B3.
- **Exploratory.** Edit-activation traces and positional gating (`src/rt/mech.py`); plausibility-target
  edits (`src/rt/targets.py`) if run.

## 6 Exclusions
Rows with generation errors, and edits whose rank-1 fit error exceeds 1e-4, are excluded and counted.
Degenerate outputs are flagged with the existing detector (`src/score_pilot.py --drop-degenerate`);
results are reported with and without them, the unfiltered analysis being primary.

## 7 Gates
- **G0 (engine parity, before any Study-2 delta):** v2 rerun of Study 1's 32B pool (ROME, N, B0/B3):
  the ES drop lies inside Study 1's 95% CI and per-case B0 agreement is ≥ 85%.
- **Submission gate:** H1 and H2 pass at 32B, and the semantic ES drop (or lexical, per the switch)
  keeps a CI above zero at 32B and 70B.

## 8 Deviations
Logged in `prereg-arr-deviations.md` with timestamp, reason and whether outcome data had been seen.

## 9 Freeze record
| item | value |
|---|---|
| commit | — |
| this file sha256 | — |
| pool manifests sha256 | — |
| first Study-2 delta timestamp (server) | — |
