# Pre-registration addendum · Study 3: edits to well-known facts (H5)

Parent: `prereg-arr.md` (frozen 2026-10-08, registry entry 1). This addendum supersedes the unfrozen H4
draft (`prereg-arr-addendum-salience.md`), which a red team found unfit to freeze
(`paperwriting/revision/narrative/panel_2026-10-10.md`). Every hypothesis of the parent stays as registered.

## 1 Purpose

The parent's confirmatory test at R1-Distill-Qwen-32B failed:
- H1, ES drop: .037 [−.010, .087];
- H2, retention contrast: +.029 [−.036, .097].

Analyses run after that failure (`paperwriting/revision/explore_s1s2.md`) found one pattern common to every run.
The pattern concerns facts that most smaller R1 distills also know ("well-known" facts). On those facts:
- the edited model loses about a third of its edits after thinking (.31–.39);
- the model's own answers are lost only 6–9% of the time.

The pattern holds in Study 1 (14B, 32B, 70B, and a 32B rerun on the Study 2 engine) and in the Study 2 32B pool.
On less familiar facts, the model's own answers are also fragile and the edit-specific excess shrinks or reverses.

H5 was formed from that data. It is tested here only on facts that played no part in forming it.

## 2 Data seen before this addendum

| data | status |
|---|---|
| Study 1 (all checkpoints and arms); the two G0 reruns of its 200 facts | seen; used to form H5 |
| Study 2 R1-Distill-Qwen-32B main pool: `base` and `rome_N`, all probes, B0 and B3 | seen; used to form H5. `study3.confirm --code-check-on-s2` was run on it to check the code: K = +.242 [.141, .343], strict count +.091 [.010, .172], as in E6. |
| Study 2 32B unknown group: 10 of 300 cases generated | row counts only; never scored |
| Study 2 14B: 2 smoke cases (cf_19672, cf_14142; run tag `s2smoke`) and 16 header-only `s2` shards | row counts only; never scored; not used here |
| rt.deltas logs of the 70B and 14B pools (fit statistics, `lp_first`) | fit errors read as summaries for D7; per-case values never tabulated against familiarity or any outcome |
| Screen decisions (`qualify_*.jsonl`) of the Study 2 candidates; familiarity counts of the pools | seen; selection data, not outcomes |
| **Any edit or generated row for the Study 3 worlds (§4)** | **none exists.** No W2 delta exists. No extension screen exists. |

## 3 Familiarity (frozen definition)

1. **Probe models.** Q = {r1qwen1_5b, r1qwen7b, r1qwen14b, r1llama8b}. For R1-Distill-Qwen-32B, all four are used.
2. **Knowledge flag.** `old_hit_q(c)` is the boolean field `old_hit` of case c in the pool screen's
   `qualify_<q>.jsonl` (base model, B0, greedy, engine v2). The fields `new_hit` and `qualified` are ignored. A missing
   flag counts as not known.
3. **Well-known.** A fact is well-known iff at least 3 of the 4 probe models have `old_hit` (share ≥ .75).
   Otherwise it is less familiar.
4. **History of the cut.** The cut at 3 of 4 was chosen after the Study 2 32B dose-response was seen (E6 → E6b). It is
   fixed here. The dose-response (secondary 7) shows whether the result hinges on it.

## 4 Worlds and procedure

The model is R1-Distill-Qwen-32B. The editor is ROME at the Study 2 settings. Two sub-worlds have disjoint facts and share
no fact with any pool whose outputs were seen.

**W2-fresh**
- Facts: the 309 candidates that qualified for 32B in the Study 2 screen but were not drawn into its 400-case manifest
  (`experiments/rt/pools/study2/manifest_r1qwen32b_fresh.jsonl`, in candidate order).
- Strata: 102 well-known, 207 less familiar.
- Edits: `deltas_s3_r1qwen32b_fresh.yaml`.
- Generation: `study3_r1qwen32b_fresh.yaml`, run tag `s3fresh`.

**W2-ext**
- Candidates: the next 1600 ids of the Study 2 seed-2027 shuffle (`experiments/rt/pools/study3/candidates.jsonl`).
  - The excluded-id set was rebuilt from local mirrors of the history. It reproduces the Study 2 build's `ids_sha256` exactly.
  - Positions 0–1599 of the 3200-long shuffle equal the Study 2 candidates one for one.
- Screen: the five models in `pool_screen_s3.yaml` at B0, exactly as in Study 2. Then `rt.pool qualify` runs for each model.
- Facts: `python -m study3.ext_manifest` writes `manifest_r1qwen32b_ext.jsonl`. It keeps, in candidate order, every candidate
  that qualifies for 32B and is well-known.
  - Expected size: about 250.
  - Its sha256 is appended to the registry before any of its deltas are computed.
- Edits: `deltas_s3_r1qwen32b_ext.yaml`.
- Generation: `study3_r1qwen32b_ext.yaml`, run tag `s3ext`.

**Run order**
1. W2-fresh edits (4090) and the extension screens (4090; base models only, B0).
2. W2-fresh generation (H100) runs in parallel with W2-ext edits (4090).
3. W2-ext generation (H100).

**Hardware and layout**
- Edits: 4090 node, fp32, TF32 off, 4 cards per process, as for the Study 2 32B edits.
- Generation: H100 node, one GPU per process, `--world 8 --device cuda`.
  - Each rank generates `base` and `rome_N` in one invocation (`--conditions base,rome_N`), so all rows of a fact share a process.
  - OOM ladder as in deviation D6: 40000 → 26000 → 18000.
- If the H100 node is unavailable, a whole sub-world moves to the 4090 node (2 cards per process, `--device auto`). The
  move is recorded in the registry; single conditions are never moved.
- Every shard header's `code_sha256` must equal that of the Study 2 32B shards; this was verified at freeze. A mismatch
  stops the run.

**Smoke check.** This is the only look at generated text before the stop. It uses `study3_smoke.yaml`: the first two
facts of the Study 2 32B pool, which are already seen and already edited, under run tag `s3smoke`. Its rows may be read
by eye and never enter an analysis.

**Stop and analysis rule**
1. Generation ends when both sub-worlds are at 100%, or at **2026-12-31 23:59 UTC+8**, whichever comes first. Failed
   chunks are re-run until then without exception.
2. Before the stop, only row counts, error-row counts and GPU statistics are inspected. No answer, chain, hit or score of
   any Study 3 fact is read.
3. At the stop, `python -m study3.end_entry --stopped-at "<time>"` writes `experiments/rt/s3_end_of_generation.json`,
   which holds shard sha256s and per-world completeness from row counts only. The file is committed, pushed, and
   recorded in the registry.
4. `python -m study3.confirm` then runs once. It refuses to run without that entry, or if any shard has changed since.

## 5 Hypothesis and tests

**Conventions** (from the parent and `rt.analysis`):
- lexical scoring with the subject scrubbed, which is the parent's registered endpoint;
- error rows skipped; rows of deltas with a rank-1 fit error above 1e-4 excluded;
- 10,000 case resamples, `random.Random(42)`, cases in sorted case_id order, percentile 95% CI, two-sided p.

A sub-world enters the analysis only if at least 98% of its facts have all four efficacy rows (base and edited, B0 and
B3). The primary test pools the facts of every sub-world that meets this rule. If neither sub-world meets it, H5 is
not tested.

**Retention set.** Facts whose base answers o_old at B0 and whose edit succeeds at B0, with all four efficacy rows present.
For each fact, value = (edited answer no longer an edit success at B3) − (base answer no longer names o_old at B3).

**H5 (primary; one test).**
- Statistic: K is the mean value over well-known facts in the retention set (the retention contrast within
  well-known facts).
- Predicted: K > 0.
- Pass iff p ≤ .05 and K > 0.

**Secondary** (CIs, no pass/fail; the keys are in `src/study3/confirm.py`):
1. **K_strict.** The same as K, but an edit counts as lost only if the B3 answer does not name o_new. This licenses
   wording (§7).
2. **Components among well-known facts.** Edited-answer loss and own-answer loss.
3. **Less familiar facts.** RC_low, and D = K − RC_low (two groups).
4. **Own-answer fragility.** Own-answer loss for less familiar facts minus that for well-known facts. The facts are those
   the base knows at B0; there is no edit gate.
5. **Edited side.** ES drop and erosion given ES@B0, each well-known minus less familiar.
6. **Paraphrase control.** K with the paraphrase prompt (`para0`) as the "after" condition: at B0 (no thinking) and at B3.
   Also K(thinking) − K(paraphrase at B0), paired within facts.
7. **Dose-response.** OLS slope of the per-fact value on the number of probe models that know the fact (0–4), over the
   retention set, with a case bootstrap. The mean value at each count is also reported.
8. **Robustness.** Within quartiles (over the manifest) of the post-edit first-token margin (`lp_first.after.target −
   lp_first.after.o_old`) and of the base's pre-edit confidence (`lp_first.before.o_old`): K and RC_low per quartile,
   and D adjusted with pooled weights. A quartile with fewer than 5 facts in either stratum is dropped and reported.
9. **Overall RC and ES drop (descriptive).** These are never pooled with the Study 2 400-fact pool. Study 3 is never
   described as a retest of H1 or H2.

## 6 Power

The inputs are from Study 2 32B: per-fact SD .51 (lexical) and .40 (strict). 63% of well-known facts enter the
retention set.

| scope | facts in the retention set (well-known) | K, lexical: power at .10 / .15 / .20 / .24 | K_strict: power at .09 / .12 |
|---|---|---|---|
| W2-fresh only | ≈ 65 | .35 / .65 / .88 / .96 | .43 / .67 |
| W2-fresh + W2-ext | ≈ 220 | .82 / .99 / > .99 / > .99 | .91 / .99 |

The exploratory estimate (.24) was selected after the fact, so we plan for K = .15. The extension exists to make the
test decisive at that size.

## 7 Outcome → claim (fixed before any Study 3 row exists)

| outcome | title | abstract | what the paper may say |
|---|---|---|---|
| H5 passes and the K_strict CI is above 0 | *Reasoning Models Undo Edits to the Facts They Know Best* | "confirmed" variant | Reasoning undoes edits to well-known facts; the own-answer baseline shows it is specific to the edit. |
| H5 passes and the K_strict CI includes 0 | *Thinking Keeps What a Model Knows, Not What It Was Edited to Know* | "confirmed, lexical" variant | Thinking loses edits to well-known facts more often than the model's own answers. The share of lost edits whose answer names both values is stated. The word "undo" is not used. |
| H5 fails | *Which Knowledge Edits Survive Thinking?* | "not confirmed" variant | The well-known-fact pattern is exploratory and did not hold on new facts. The paper is framed around the registered results. |
| H5 not tested (no sub-world complete) | *Thinking Keeps What a Model Knows, Not What It Was Edited to Know* | "not run" variant | The pattern is described as found after the replication failed. This test is described as registered and pending. |

Further rules:
- If only W2-fresh enters the primary, the paper states the power of that test. A failure there is called
  inconclusive, not a failure to replicate.
- H5 tests the edit-specific loss within well-known facts on new facts. It does not test whether the share of
  well-known facts explains the Study 1 → Study 2 shrinkage; that stays an exploratory inference.
- Every registered result is reported whatever its outcome.

## 8 Analysis code and inputs (sha256 recorded in registry entry 8)

**Analysis:**
- `src/study3/confirm.py`, `src/study3/end_entry.py`, `src/study3/ext_manifest.py`, `src/study3/tests/test_confirm.py`.
- Imported: `src/rt/analysis.py`, `src/rt/study2.py` (for `read_fit_logs` and `FIT_TOL`), `src/metrics.py`.

**Data:**
- `data/aliases.json`, `data/counterfact.jsonl`.
- `experiments/rt/pools/study2/manifest_r1qwen32b_fresh.jsonl`, `experiments/rt/pools/study3/candidates.jsonl`.
- The four probe models' and 32B's `qualify_*.jsonl` (study2).

**Configs:**
- `deltas_s3_r1qwen32b_{fresh,ext}.yaml`, `study3_r1qwen32b_{fresh,ext}.yaml`, `study3_smoke.yaml`, `pool_screen_s3.yaml`.

The engine (`src/rt/*.py` and the files `rt.run` hashes) is unchanged since the Study 2 32B run. Its `code_sha256` map equals
that in the Study 2 32B shard headers.

## 9 Freeze

**What the freeze is:**
- the commit that contains this file and everything listed in §8;
- its push to GitHub;
- registry entry 8, which records the push time from the GitHub API.

Before the freeze, no Study 3 delta, screen or generated row exists.
