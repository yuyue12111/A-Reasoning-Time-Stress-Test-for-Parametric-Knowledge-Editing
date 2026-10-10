# Exploratory analysis: why the 32B effect shrank from Study 1 to Study 2 (plan, fixed before running)

Status: **exploratory, post hoc.** Written 2026-10-10 after the pre-registered Study 2 analysis of the
32B worlds (H1 .037 [−.010, .087], H2 +.029 [−.036, .097]; `study2.json`, commit `8967bf5`).
Nothing here changes the confirmatory verdicts. Code: `src/rt/explore_s1s2.py`; output
`explore_s1s2.{json,md}`. Conventions as in `rt.analysis`: lexical scoring with the subject scrubbed, 10,000 case
resamples, seed 42, percentile 95% CI; independent groups are resampled within each group.

## Data (all R1-Distill-Qwen-32B, greedy, efficacy probe, B0 and B3)

| label | cases | engine and hardware |
|---|---|---|
| S1 | Study 1 pool (200; 198 paired) | original HF pipeline (fp32 edits, H200), `results 2/probe` |
| G0-4090 | the same Study 1 cases | engine v2 bf16, 8×4090, 2026-09-29 (`platform_out/g0`) |
| G0-H100 | the same Study 1 cases | engine v2 bf16, H100, 2026-10-08 (`h100_out/results/rt/g0`) |
| S2 | Study 2 pool (400) | engine v2 bf16, H100, 2026-10-08 (`results/rt/s2`) |

## Questions and tests

- **E0, hardware.** Do G0-4090 and G0-H100 differ on the same cases? Paired case-level difference
  (4090 − H100) of ES drop, erosion, repair, plus retention contrast in each run.
  S2 ran on H100, so this bounds how much of the gap the hardware could explain.
- **E1, heterogeneity on matched hardware.** S2 − G0-H100, both v2 bf16 on H100, differing only in
  the case pool. Independent-group bootstrap difference of ES drop, retention contrast, erosion
  and repair; also S2 − G0-4090 and S2 − S1 for reference.
- **E2, the qualification rule.** Restrict the Study 1 cases to the ones Study 2's rule would admit:
  the same run's base answer names o_old and not o_new at B0, and the subject does not contain
  o_old. Recompute the ES drop and retention contrast in S1, G0-4090 and G0-H100.
- **E3, unedited reasoning recalls the old fact.** Moderator: the base chain at B3 names o_old (subject
  scrubbed). In S2, compare the moderator=1 and moderator=0 strata on erosion among cases with
  ES@B0 and on the ES drop, and compute the retention contrast within each stratum. Repeat in S1,
  G0-4090 and G0-H100. Report the moderator's prevalence in each pool, which is the composition
  argument. A secondary moderator is that the base answer names o_old at B3.
- **E4, relation mix.** Relation distribution of S1 and S2. Post-stratify the S2 ES drop to S1's
  relation weights over the relations both pools share, with a bootstrap within relations.
- **E5, edit strength (S2 only).** From the rt.deltas logs, take the first-token log-probabilities before and after the
  edit: target after, o_old after, and o_old before. Among cases with ES@B0, compare erosion
  across the medians of each, and report the AUC of each for erosion.

## How it bears on the decision

- If E0 shows a hardware difference as large as the gap, Study 2's 32B result is not interpretable
  as a pool effect.
- If E1 shows no significant difference, Study 1 and Study 2 are statistically compatible, and the
  pooled reading is "a smaller effect".
- If E2–E5 locate the shrinkage in an identifiable subpopulation, that is the next paper's
  hypothesis. It would then need confirming in a new pre-registered run, not claimed from this
  analysis.

## Addendum: added after E0–E5 were seen (2026-10-10)

- **E5b.** E5 found that the residual first-token log-probability of o_old after the edit predicts
  erosion in S2. Two follow-up tests use the G0 delta logs (the same deltas for G0-4090 and
  G0-H100):
  1. Does the predictor replicate on the Study 1 cases?
  2. Does its distribution explain the erosion gap? Apply S2's erosion rate in each quartile of
     the pooled predictor to the Study 1 cases' quartile shares, then compare the predicted
     erosion with the observed one.
  Both were chosen after seeing E5, so both are exploratory.
- **E6, fact salience** (added after E5b). Study 1's pool was selected by the unedited Qwen-7B
  naming o_old at B3. The Study 2 screen files record, for every candidate, whether each smaller
  model's base names o_old at B0. Within S2, compare cases the 7B knows with cases it does not,
  and cases known by all four small models (1.5B, 7B, 14B, 8B) with the rest. Measures: ES drop,
  erosion among cases with ES@B0, and retention contrast. Composition is the 7B-known share in S2
  versus in S1, where it is measured from Study 1's 7B base rows at B0 and B3. Exploratory.
- **E6b, salience on the Study 1 cases** (added after E6). The same split, high (3–4 of the 4
  small distills know the fact at B0, or 3 of 3 for 14B) versus low, on Study 1's 14B, 32B and 70B,
  and on the two G0 reruns. Salience is measured from Study 1's own base runs of 1.5B, 7B, 14B and
  Llama-8B. Exploratory.
