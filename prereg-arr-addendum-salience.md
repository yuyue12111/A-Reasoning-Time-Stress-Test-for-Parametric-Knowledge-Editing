# Pre-registration addendum · H4, fact salience (DRAFT, not frozen; NOT TO BE FROZEN AS WRITTEN)

> **Status 2026-10-10.** A red team found this draft unfit to freeze. See `paperwriting/revision/narrative/panel_2026-10-10.md`. The problems:
> - W1 and W3 share most of their facts with the pool that generated H4.
> - D mostly measures how fragile the model's own answers are, not loss of the edit.
> - There are no stop or no-peek rules.
> - The W2 configs are missing.
> - The 14B smoke rows are misreported.
>
> The estimand will be redesigned after the paper's framing is decided.

Parent: `prereg-arr.md` (frozen 2026-10-08, registry entry 1). This addendum adds one hypothesis and three
worlds. Every hypothesis in the parent stays as registered.

## 1 Why this addendum exists

The parent's confirmatory test at R1-Distill-Qwen-32B failed:
- H1 ES drop .037 [−.010, .087];
- H2 retention contrast +.029 [−.036, .097].

An exploratory analysis written afterwards (`paperwriting/revision/explore_s1s2.md`, commit `aadf8a9`) found
that the edit-specific loss sits in *salient* facts, meaning facts that most of the smaller R1 distills also know. The evidence:
- In the Study 2 32B pool, the retention contrast was +.242 for salient facts and −.090 for the rest.
- The same split held in the Study 1 cases at 14B, 32B and 70B.

H4 was formed from that data. It is therefore tested here only on worlds that have no generated row at
the time of freeze.

## 2 Data seen before this addendum

| data | status |
|---|---|
| Study 1 (all six checkpoints, all arms) and the two G0 reruns on its 200 cases | seen; used to form H4 |
| Study 2 R1-Distill-Qwen-32B main pool: `base`, `rome_N`, all three probes, B0 and B3 | seen; used to form H4 |
| Study 2 32B unknown group: 10 of 300 cases generated | row counts only, never scored |
| Study 2 14B: 2 smoke cases (run tag `s2smoke`) | row counts only, never scored; never analysed |
| salience counts of each pool (§3), from the screen files | seen; not outcomes |
| any generated row of the three H4 worlds (§4) | **none exists** |

## 3 Salience (frozen definition)

1. **Probe models.** Q = {r1qwen1_5b, r1qwen7b, r1qwen14b, r1llama8b}. For an evaluated model m, Q_m = Q \ {m}.
2. **Knowledge flag.** `old_hit_q(c)` is the Study 2 pool screen's verdict that probe model q's unedited base
   names o_old for case c at B0. It comes from the `qualify_<q>.jsonl` files (greedy, engine v2, `rt.pool`;
   committed in `a9b4139`; sha256 in §9).
3. **Salience.** s_m(c) = mean over q ∈ Q_m of old_hit_q(c).
4. **Strata.** **High** iff s_m(c) ≥ 0.75, i.e. 3–4 of 4 probe models, or 3 of 3 for 14B. **Low** otherwise.
   The strata are fixed now:

| world | high | low |
|---|---|---|
| W1 r1llama70b | 107 | 293 |
| W2 r1qwen32b fresh | 102 | 207 |
| W3 r1qwen14b | 65 | 335 |

## 4 Worlds

- **W1, R1-Distill-Llama-70B.**
  - Pool: the parent pool (manifest `807005f72193`, registry entry 3).
  - Edits: the existing ROME deltas (D70, 400/400).
  - Generation: `study2_r1llama70b_eff.yaml` (`base`, `rome_N`; efficacy; B0, B3; run tag `s2`).
  - Nothing changes, so the parent's H1 and H2 at 70B are tested on the same rows.
- **W2, R1-Distill-Qwen-32B, fresh pool.**
  - Pool: the 309 candidates that qualified for 32B in the parent screen but were not drawn into its 400-case manifest
    (candidate order; `manifest_r1qwen32b_fresh.jsonl`, sha256 `d5871494b789`). None has been edited or generated.
  - Edits: ROME with the settings of `deltas_s2_r1qwen32b.yaml`; only the manifest and the log directory change.
  - Generation: the stage-1 `base` and `rome_N` conditions of `study2_r1qwen32b.yaml`, efficacy probe only, B0 and B3,
    run tag `s3fresh`. The engine, template, BOS setting and decoding are identical to the parent's 32B run.
- **W3, R1-Distill-Qwen-14B.**
  - Pool: the parent pool (manifest `8bcec4e89e29`).
  - Edits: the existing ROME deltas (D3).
  - Generation: `study2_r1qwen14b_eff.yaml`.
- **Run order:** W1, then W2, then W3. W2's edits may run on the 4090 node while W1 generates. Completion is
  decided by platform time only.

## 5 Hypotheses and tests

**Conventions.** These are the parent's (§4–§6):
- endpoint: lexical (the parent's switch rule resolved to lexical);
- the retention contrast (RC) and ES drop as defined there;
- 10,000 case resamples, seed 42, cases in sorted case_id order, percentile 95% CI, two-sided p;
- exclusions as in the parent's §6;
- completeness: a world enters only if ≥ 98% of its manifest cases have every row.

**H4 (primary; a single test).**
- For world m, D_m = RC_m(high) − RC_m(low).
- The test statistic is D̄, the unweighted mean of D_m over the **primary worlds W1 and W2** that are complete.
  - If exactly one is complete, D̄ is that world's D_m.
  - If neither is complete, H4 is not tested.
- The bootstrap resamples cases within each world × stratum.
- **Pass** iff p < .05 and D̄ > 0.

**Secondary** (CIs, no correction, no pass/fail):
1. D_m for each of W1, W2 and W3.
2. ES drop(high) − ES drop(low), per world and pooled as in H4.
3. The two components of D_m:
   - edited loss, high − low (predicted > 0);
   - base loss, high − low (predicted < 0).
4. Dose-response: RC by the number of probe models that know the fact (0–4; 0–3 for 14B), with a linear-trend
   estimate.
5. Robustness to the base model's own confidence: D_m stratified by quartile of the base's first-token
   log-probability of o_old before the edit (rt.deltas `lp_first.before.o_old`).
6. W2's overall ES drop and RC (descriptive).

The parent's H1 and H2 at 70B and 14B are evaluated as registered, on W1 and W3.

**Exploratory:** the 8B, 7B and 1.5B pools, if generated, with salience taken from the other probe models.

## 6 Expected effect and power

- **Expected size.** The exploratory estimates of D are .15–.33: Study 1, 14B .152, 32B .264, 70B .198; Study 2,
  32B .332. These were selected after the fact, so we plan for D = .15.
- **Standard error.** Values per case are in {−1, 0, 1} with SD ≈ .55, and the retention sets are about 60% of cases.
  This gives an SE of D̄ over W1 and W2 of about .055.
- **Power** (two-sided α = .05): about .75 at D = .15, and about .94 at D = .20.

## 7 Decision and reporting rules, fixed before any H4-world row exists

- **H4 passes.** The paper's central claim is that reasoning undoes edits of entrenched (salient) facts.
  - The parent's failed H1 and H2 at 32B are reported as registered.
  - Salience composition is offered as the explanation: exploratory in Study 1 and Study 2, confirmatory in W1 and W2.
- **H4 fails.** The salience finding is reported as exploratory and not replicated. The paper is framed around the
  registered results: the reasoning-time loss is smaller than Study 1 estimated, and not edit-specific on a fresh pool.
- **Pre-written abstracts.** Both versions of the abstract's result sentence are written and committed before any W1–W3 row is generated
  (`paperwriting/revision/narrative/`).
- **Reporting.** Every registered result is reported whatever its outcome.

## 8 Analysis code

`src/rt/salience.py` will read the same shard format through `rt.analysis`. It is written and tested before the
freeze, and its sha256 goes into the freeze entry.

## 9 Freeze record (to be completed at freeze)

**What the freeze is.** A commit containing:
- this file;
- `src/rt/salience.py` and its tests;
- the W2 manifest;
- the W2 delta and generation configs.

That commit is pushed to GitHub, and an append-only registry entry records the shas and the push time.
Before the freeze, no W2 delta and no W1–W3 generation exist.

**Inputs (sha256):**
- `qualify_r1qwen1_5b.jsonl` 423fdca0df00…
- `qualify_r1qwen7b.jsonl` ae3c30e9feec…
- `qualify_r1qwen14b.jsonl` bb184c023826…
- `qualify_r1llama8b.jsonl` 6dc506af4554…
- `candidates.jsonl` 0ef6625fe9d5…
- `manifest_r1llama70b.jsonl` 807005f72193…
- `manifest_r1qwen14b.jsonl` 8bcec4e89e29…
- `manifest_r1qwen32b_fresh.jsonl` d5871494b789…
