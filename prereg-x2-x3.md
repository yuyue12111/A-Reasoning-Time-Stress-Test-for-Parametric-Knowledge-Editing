# X2/X3 incremental experiments · frozen preregistration

- Frozen: 2026-07-10, before any X2 T/C or X3 T/C outcome is inspected.
- Authority: `plan.md` v1.77 (original scientific freeze at v1.76; the v1.77 addendum below is scheduling-only); this file fixes operational details without raising any claim ceiling.
- Shared rules: CounterFact prefiltered order, seed 42, n=200, greedy, B0/B3, single edit → all probes/budgets → exact restore, fp32, `WHYAAAI_NO_BOS=1`, case-paired analysis, 10,000 bootstraps with seed 42. Smoke (`--limit 8 --tag-suffix _smoke`) is technical only and cannot select hyperparameters.

## X2 · MEMIT-14B repair replication

- Arms: N=`experiments/memit14b.yaml` (or the predeclared conditional fresh N), T=`memit14b_sup.yaml`, C=`memit14b_strongcomp.yaml`.
- Frozen edit state: MEMIT layers `[7,8,9]`, `v_loss_layer=47`, `stats_dir=./data/stats_r1qwen14b`; T/C use α=8, scope=`think`; C uses the already frozen `data/placebo_donors_strong.json`.
- Primary: paired T−C strict ES at B3; success requires its 95% CI >0.
- Joint specificity gate: C−N ES, RR, and RRs must be compatible with zero; T−N must point in the repair direction. RR/RRs/CLR are secondary; B0 byte identity is a construction check.
- Existing N may be reused only if `_meta` establishes code hash, dtype, BOS, model and software parity. Otherwise run `experiments/memit14b_freshn.yaml`; this decision is provenance-driven, not outcome-driven.
- If α=8 is null for both T−N and T−C, α=16 may be run once as a labelled diagnostic. It is never substituted for the primary or used to strengthen the main claim.

## X3 · ROME-32B active paraphrase

- Arms after the pre-full-run mp2 deviation: fresh N=`probe32b_freshn.yaml`, T=`probe32b_para_sup.yaml`, C=`probe32b_para_strongcomp.yaml`; all three use the same two-H200 model-parallel protocol and isolated `_mp2` tags. The legacy `probe32b.yaml` remains the Day-0/audit source only.
- Frozen edit state: ROME layer 12, `v_loss_layer=63`; T/C use α=8, scope=`think`, and literally `apply_to: [efficacy, para0, para1]`.
- Day-0, before T/C: report N PS at B0/B3, selected/observed case and row counts, missingness, and a seed-42 readability manifest of 20 original CounterFact paraphrases. No cases are removed from the primary based on this audit.
- Primary: T−C strict PS at B3 over matched para0+para1 rows. Pairing is by `(case_id, paraphrase_probe)` and bootstrap resamples whole `case_id` clusters, retaining both paraphrases.
- Joint gate: C−N PS CI contains zero and T−N points positive. The N-B0-successful paraphrase rows form a fixed pre-treatment subset for the secondary committed-old comparison at B3; if fewer than 140 unique cases pass, this secondary is directional only.
- No sequence-level rescue, prompt replacement, case filtering, α search, or added seed after seeing X3. Positive or negative X3 is add-only and cannot alter the abstract.
- The single-GPU capacity failure makes fresh N mandatory independent of B3 effects; legacy N is not mixed with mp2 T/C.

## Technical smoke gates

- All T/C rows record exact config/code provenance and `suppress_trace` (target, token IDs, selection, actual processor call count).
- X2 uses four sequential 8-GPU waves. X3 keeps logical `world=32` but uses eight waves of four two-GPU workers (6–7 cases per shard), preserving append-only/resumable shard size; launchers are `experiments/run_x2_h200.sh` and `experiments/run_x3_h200.sh`.
- B0 T/C must be byte-identical to N for matched probes. At B3, T must differ from N on at least one active row; an output-identical C is a warning, not a failure, if processor-call traces prove the control was actually wired (behavioral inertness is C's intended role).
- X2 additionally requires log evidence that all three mom2 layers loaded cached statistics, with no recomputation/error marker.
# 2026-07-11 X3 technical deviation (pre-full-run, outcome-blind)

The original single-H200 X3 smoke failed on `cf_975` after a successful ROME edit, when B3
generation requested 10.03 GiB with only 5.04 GiB free (133.93/139.81 GiB already allocated;
reserved-but-unused only 97.19 MiB). This is a capacity failure, not an endpoint or effect-driven
change. Before any X3 full run, all X3 arms are therefore moved to the same two-H200-per-process
fp32 protocol (`model_parallel: true`, `device_map=balanced`). The old single-GPU smoke is retained
but excluded. Fresh N/T/C use new `_mp2` tags, identical cases/order and unchanged B0/B3, layer 12,
penalty 8, think-only scope, and efficacy/para0/para1 probes. An n=8 smoke must complete the former
OOM case before n=200 starts. If this protocol still fails technically, X3 stops rather than changing
precision, budget length, KV-cache semantics, endpoints, or suppression strength.

# 2026-07-11 X3 execution scheduling addendum (after X2 completion, before X3 full analysis)

The two H200 instances share the same filesystem. After exactly one fresh-N/T/C mp2 smoke passes,
the unchanged logical `world=32` full run may be split across the two instances by non-overlapping
four-rank wave bases. The frozen default split is H200-B=`0 4 8 12` (logical ranks 0–15) and
H200-A=`16 20 24 28` (logical ranks 16–31). Each instance still runs four two-GPU workers per wave;
both run all three N/T/C arms and write only their assigned rank shards. This is scheduling-only:
configuration hashes, cases/order, model-parallel topology per worker, endpoints, and case-clustered
analysis are unchanged. A single post-run audit/score job is run only after all 32 shards of all arms
exist. X1 is not launched opportunistically before its own preregistration, source manifest, fixed-chain
runner, and judging protocol are frozen.
