# X1 · lexical-orthogonal chain replay · frozen preregistration

- Frozen: 2026-07-11, before any fixed-chain replay answer is generated or inspected.
- Authority: `plan.md` v1.79. This file freezes the natural-chain replay validity gate only. The five authored arms remain forbidden until this gate passes and receive a separate pre-outcome freeze.
- Model/edit state: DeepSeek-R1-Distill-Qwen-32B, ROME layer 12, `v_loss_layer=63`, fp32, `WHYAAAI_NO_BOS=1`, one edit → fresh B0 answer + one fixed-chain replay answer → exact restore.
- Decode: greedy, answer cap 256 tokens. The source CoT is byte-for-byte prefilled; no CoT token is generated, removed, truncated, normalized, or rewritten.

## 1. Frozen source population

Only artifacts that existed by 2026-07-10 are eligible:

1. `data/reverted_32b.jsonl` — main B3 greedy.
2. `data/reverted_32b_f2b1.jsonl` — F2 B1 greedy.
3. `data/reverted_32b_samp.jsonl` — F3 historical sampling seed 2. The historical extractor overwrote
   `case_id→budget` in seed order 0→1→2 and omitted the seed field; `plan.md` v1.79 records this
   provenance correction from the earlier mistaken seed-0 label.

For every unique `case_id`, select the first source in that hierarchy **before** looking at source eligibility. The selected source itself must then have at least two of three pre-existing neutral-judge votes treating it as an in-population committed reversion. A lower-priority source cannot rescue a held, missing-vote, or otherwise ineligible selected source. This gives 18 cases from 33 unique candidates.

The immutable manifest is `data/x1_replay_manifest.jsonl`. Each row fixes the source path, 1-based line number, raw-row SHA256, CoT SHA256, source-answer SHA256, and judge provenance. `src/build_x1_manifest.py --check` must pass before smoke and full. In addition, `src/verify_x1_sample_source.py` must reconstruct seed-2 B0/B3 rows from the shared raw `cf200samp` shards and prove 14/14 historical exported rows have byte-identical CoT+answer. A failed or unavailable raw audit blocks X1 rather than changing seed or silently dropping the sampling tier. No case may be dropped after replay behavior is known.

## 2. Intervention and capacity protocol

For each manifest case:

1. Apply the same ROME edit as the 32B headline run.
2. Under that same edit state, run a fresh B0 answer with the canonical empty-think prompt, greedy decoding, and the same 256-token answer cap.
3. Construct the replay prompt as `<｜User｜>{prompt}<｜Assistant｜><think>\n{source_cot}\n</think>\n\n` under the existing NO_BOS convention.
4. Generate only the replay answer, greedily, for at most 256 tokens.
5. Record the exact source/COT hashes, tokenizer CoT length, B0 answer, replay answer, and provenance.
6. Restore the copied weights in `finally`, including either generation-error path.

The source chain may be as long as the original B3 chain. Capacity is therefore frozen at two H200s per process, four processes in parallel, `model_parallel=true`, and `WHYAAAI_DEVICE_MAP=balanced`. This is not a new scientific arm. A technical failure cannot be rescued by bf16, chain truncation, a different edit layer, a different answer cap, or source substitution.

## 3. Smoke and full run

- Smoke: frozen first four manifest rows, logical `world=4`, one row per two-GPU worker, isolated `_smoke` tag. It checks only manifest/hash integrity, both local GPUs in `hf_device_map`, editable-weight device audit, zero error rows, non-empty B0/replay answers, and the edit→B0→fixed-chain→answer→restore path. Smoke answers cannot change any parameter or inclusion decision; B0 success rate is not a smoke tuning gate.
- Full: all 18 rows, logical `world=4`, four two-GPU workers, append-only JSONL with case-level resume. Exactly one answer per case.
- Old single-GPU or self-generated-CoT attempts, if any, are audit-only and cannot be pooled.

## 4. Validity endpoint and decision

The primary case-level success is the conjunction of (a) fresh B0 strict edit success—B0 answer contains NEW and not OLD under the paper matcher—and (b) the replay answer's **final answer commitment** is OLD under three independent neutral answer judges. Judges see `o_old`, `o_new`, and the replay answer only; they do not see B0, the source chain, source answer, source route, arm name, rule score, or other judges. Each returns `old`, `new`, or `neither`; at least two OLD votes is one replay success. A 1–1–1 split, fewer than two OLD votes, or fewer than two valid judge responses is failure, not deletion.

- PASS: point estimate old-commit rate ≥0.80. With n=18 this requires at least 15/18 successes.
- FAIL: fewer than 15/18 successes, or fewer than 18 technically valid full rows without an outcome-blind technical rerun of the same case.
- Wilson and exact-binomial intervals are descriptive only; their lower bounds are not additional gates.
- Rule-based loose OLD and strict OLD-without-NEW rates are frozen sensitivity analyses. If OLD and NEW both occur, the judge's final-commitment decision is primary.

If FAIL, X1 stops and reports that fixed replay did not stably reproduce the original natural reversions. If PASS, this establishes only that fixed-chain replay is a valid experimental vehicle. It does not establish semantic sufficiency, natural-generation mediation, necessity, or any five-arm contrast.

## 5. Post-PASS boundary

Only after PASS may the team freeze and construct OLD-SEM, NEUTRAL, OLD-LEX, BRIDGE-LEX, and NEW-SEM under `plan.md` v1.69. Their authorship, lexical validators, blind fluency/NLL gates, retry policy, judge panel, and P1/P2 statistics must be committed before any authored-arm model output is inspected. No resistant-case expansion or source-pool enlargement is allowed.
