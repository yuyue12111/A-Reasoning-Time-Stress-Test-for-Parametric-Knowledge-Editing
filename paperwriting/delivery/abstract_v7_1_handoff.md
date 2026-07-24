# Abstract v7.1 candidate · Fable handoff

> Status: **CANDIDATE ONLY — NOT ADOPTED**.
> The repository still records v5 as frozen; v6 and v7.1 are candidate files. Title, TL;DR, and the frozen v5 bytes were not changed. External OpenReview state is not locally verifiable.

## Candidate

> Parametric knowledge edits are validated with direct answers; deployed reasoning models may reason before answering. We stress-test the same ROME edit on CounterFact at zero thinking and after a natural chain, across six fixed checkpoints from two DeepSeek-R1-distill families. At the largest tested checkpoint in each family, paired edit success drops 0.106 on Qwen-32B and 0.107 on Llama-70B. On Qwen-32B, the old answer displaces the new one outright in 9.2% of zero-thinking successes and resurfaces in 19.3% of them. On Qwen-32B, erosion is edit-specific (no detectable unedited-base drift), not reproduced by a canned thought, and persists across three fixed sampling seeds. In examined Qwen-32B reversions, the edited association remains detectable at a cloze probe; separately, judges identify visible in-chain routes, motivating a chain-routing hypothesis. We next test for a chain-local control point: signed, dose-graded suppression of the old answer's first tokens only during thinking, with answer logits untouched. This offsets the observed thinking tax; marginal loose reversion drops 19.3%→8.5% (complete-case paired change −0.102); edit-success gains replicate at 14B and transfer to MEMIT; strict transfer remains inconclusive. Direct-answer edit success is not enough: edit evaluation needs a reasoning-time stress test, and the failure it reveals admits a chain-local causal control point.

Canonical file: `paperwriting/delivery/abstract_v7_1_candidate.txt`

- 200 whitespace-delimited words; 9 sentences.
- Sentence lengths: `15/24/19/21/22/23/24/28/24`.
- Seven result-quantity occurrences: `0.106, 0.107, 9.2%, 19.3%, 19.3%, 8.5%, −0.102`.
- File SHA256: `daab7b77177945cf316450f0cd58ec1c4747c3cf66e5e6dee9e778f76a1664ac`.
- Normalized-text SHA256: `0b70c13ef6c2c46f840c46a599c3bbab1fc59eb088b1f33be89e58cf0f40622f`.

## Recipe implementation

1. S1 restores the v5/v6 population-level CONTEXT opening byte-for-byte.
2. S2 preserves the v5/v6 experimental design while compressing its 32 words to 24; a literal copy would violate the 30-word sentence ceiling.
3. S3–S5 reuse v7's three low-density phenomenon/control beats.
4. S6 relocates the cloze observation from v7's failed opening. It limits that observation to examined Qwen-32B reversions and uses `separately` before the observational routing hypothesis.
5. S7 reuses v7's isolated intervention-design sentence.
6. S8 reuses v7's labeled marginal/paired beat, changing only the first colon to a semicolon so loose-RR quantities do not syntactically serve as the estimand for the edit-success tax.
7. S9 is the shared ending, byte-for-byte.

The machine-verifiable sentence lineage is in `abstract_v7_1_source_map.json`.

## Evidence and adoption status

Preflight status: **PASS**. The checker confirms structure, hashes, frozen local fields, banned-language absence, numeric subset, JSON evidence anchors, Qwen/selected-case scopes, and marginal/paired labels.

This is not an adoption decision:

- G5 remains blocked until D1–D7/R1 are written and frozen in the manuscript. V7.1 inherits the full v7 debt ledger; it closes none of those debts.
- D3 remains mandatory even though the cloze wording is bounded: cold readers across earlier panels repeatedly overread detectability as an intact/non-erased edit.
- G6 has not been run on this byte string. Old Codex/Fable panels are developmental evidence and cannot be recycled as a terminal test for v7.1.
- The current repository still freezes v5. Treating Fable's prose statement that v6 was adopted as repository state would be incorrect until a separate recorded unfreeze/freeze action occurs.

## Proposed fresh G6.1 (not yet run)

Use a single-version, between-reader design; never use side-by-side comparison. Each fresh reader sees exactly one anonymous abstract and answers one integrated prompt: in no more than 30 English words, retell the core finding **and its implication**, then rate clarity and name the first confusing phrase. Do not separately prompt for the main implication.

Blind scorers should code A1 direct/zero-thinking validation, A2 reasoning-time failure, A3 cloze-probe-bounded detectability, A4 chain-local intervention/control point, A5 stress-test implication, plus intactness overread and mediation overread flags. Pre-register the sample and win rule before launching; do not infer population significance from this diagnostic panel.

## Requested Fable review

1. Is S1–S2 now a clean CONTEXT→APPROACH opening without weakening the same-edit design?
2. Does S6 keep cloze detectability and route taxonomy separated enough, despite sharing one sentence?
3. Does the S8 semicolon correctly separate the unshown ES-tax claim from the displayed marginal/paired loose-RR beat?
4. If the candidate passes those questions, approve its exact hash for a fresh G6.1 protocol; do not yet sync OpenReview.

Reproduce the preflight with:

```bash
python3 src/check_abstract_v71.py
```
