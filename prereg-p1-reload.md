# P1 · X1 fresh-B0 reload/capacity diagnostic · frozen preregistration

- Frozen: 2026-07-12, before any P1 model output is generated or inspected.
- Authority: `plan.md` v1.81.
- Purpose: diagnose why the frozen X1 source strata reproduced fresh-B0 installation unevenly. P1 is not an X1 rescue, cannot change the official 9/18 FAIL, and cannot authorize authored-chain arms.

## 1. Frozen cases

Use all 18 rows of `data/x1_replay_manifest.jsonl`, without filtering by X1 B0/replay outcome:

- main B3 greedy: 10 cases;
- F2-B1 greedy: 5 cases;
- historical sample seed2: 3 cases.

The runner verifies exact equality with the tracked manifest case IDs before loading a model. Membership validity is irrelevant to this diagnostic because the endpoint is edit installation at B0, not source-answer commitment.

## 2. Crossover design

Every case is run under all four node×topology cells, with three independent process/model reloads per cell:

| Round | H200-A | H200-B |
|---|---|---|
| 1 | single-H200 | 2×H200 balanced |
| 2 | 2×H200 balanced | single-H200 |

This gives `18 cases × 2 nodes × 2 topologies × 3 reloads = 216` case-edits. The two instances share storage but write node/topology/reload-specific tags and logs.

Frozen common protocol: DeepSeek-R1-Distill-Qwen-32B, ROME layer 12, `v_loss_layer=63`, fp32, `WHYAAAI_NO_BOS=1`, CounterFact prompt, greedy B0 only, efficacy probe only, one edit → one B0 answer → exact restore. No replay chain, suppression, alternative layer, seed, precision, answer cap, or case substitution is permitted.

Single topology uses one process per H200 (`world=8`). MP2 uses four processes over disjoint GPU pairs (`world=4`, `model_parallel=true`, `WHYAAAI_DEVICE_MAP=balanced`). Each reload starts new Python processes and therefore reloads model/editor state.

## 3. Frozen measurements

For every `(node, topology, reload, case_id)` record:

1. strict B0 success: subject-scrubbed answer contains `o_new` and not `o_old` under `metrics.hit`;
2. raw answer and SHA256;
3. per-edited-weight delta L2, relative L2, max-absolute delta, and aggregate summary computed in chunks;
4. config/code hash, model/tokenizer/runtime, editable-weight device, `hf_device_map`, CUDA-visible devices, and software versions.

Report strict-B0 rates and answer-hash stability by node, topology, source stratum, and case. Pair comparisons by case and reload.

## 4. Interpretation rules

- A topology attribution requires the MP2−single direction to agree on both nodes; the pooled node-stratified paired 95% CI is descriptive support, not a new paper endpoint.
- A difference that follows node rather than topology is a node/runtime effect.
- F2 remaining weaker in all four node×topology cells supports source-cohort/case fragility.
- A case whose strict flag or answer hash changes across the three reloads within the same node×topology cell is reload/numerical instability.
- Similar strict rates with different answer hashes indicate surface nondeterminism without installation failure.
- No result changes X1's official denominator, threshold, FAIL, or stop rule. No subset may be selected for further X1 work.

## 5. Technical gate

Before full P1, each node/topology launcher runs a two-case smoke containing one main and one F2 case. Smoke checks only model load, expected topology/device mapping, two non-empty B0 rows, diagnostic fields, zero errors, and restore completion. It cannot alter cases or protocol. If single-H200 B0 itself OOMs, record the technical failure and do not change dtype or topology to rescue that cell.
