# Mechanism probes (`src/rt/mech.py`)

Exploratory analysis for claim 5 of REVISION.md §1 ("does the edit still fire inside the chain?").
Both probes are teacher-forced over chains the edited model already produced in Study 1, so they
need no generation: a few forward passes per case.

## Premise

A single ROME edit is a rank-1 update ΔW = B·A on one `down_proj`. In a causal transformer the
residual stream at the question's tokens does not depend on what follows, so the edit fires
identically on the question at B0 and at B3 (checked in `test_question_activation_same_at_b0_and_b3`).
If the edited answer is lost after thinking, the loss comes from what the chain adds later:

- **(a) key-miss**: the chain mentions the subject again (a partial name, another context) and the
  `down_proj` input there does not align with the key direction A, so the edit does not fire;
- **(b) bridges**: the chain routes through facts the edit never touched;
- **(c) dilution**: the answer depends less on the question-position edit after a long chain.

## Probe (a): activation trace (`kind: "trace"`)

One forward pass over `[BOS] + TPL(q) + cot + "\n</think>\n\n" + answer` (the exact string the
answer phase of `think_budget.generate_with_budget` tokenized), with the edit applied. At every
position i and edited layer, the activation is

    a_i = (A·x_i) / (A·x_ref)

where x is the `down_proj` input and x_ref is taken at the last token of the subject's first
occurrence in the question. So a = 1 at the reference, and the edit adds a_i · B·(A·x_ref) at
position i: a ≈ 1 means the edit fires as it did on the question, a ≈ 0 means it is silent.

Recorded per case: the full per-position array (float16, base64; `mech.decode_a(row)`), the
reference token, every subject mention in chain and answer with a at its last token, the first
old-value and new-value mention in chain and answer, and a summary:

| field | meaning |
|---|---|
| `mentions[].kind` | `full` (whole subject, case-insensitive, whole word) or `partial` (any whole word of the subject with ≥4 characters, outside full mentions) |
| `values.{chain,answer}.{old,new}` | first mention under `metrics` rules: subject scrubbed, aliases of ≥4 characters, word boundaries |
| `summary.max_a` | max a over chain subject mentions |
| `summary.frac_high` | fraction of chain subject mentions with a ≥ `thr` (0.5) |
| `summary.a_last_before_old` | a at the last chain subject mention that ends before the first chain old-value mention |
| `summary.n_before_old` | number of chain subject mentions before that old-value mention |

For multi-layer edits (MEMIT) a mention's `a` is the mean over edited layers of rank component 0;
`a_by_layer` keeps each layer. For one-layer ROME tracing with or without the edit gives the same
x at the edited layer.

## Probe (b): positional gating (`kind: "gate"`)

Teacher-forced over `[BOS] + TPL(q) + cot + "\n</think>\n\n" + prompt`, where `prompt` is the
CounterFact prompt, so the next token is the value. The edit is switched on only at chosen
positions through `EditBank`'s `pos_mask`, and we read the log-probabilities of the first token of
`" " + o_new` and `" " + o_old` at the final position, and their margin (new − old).

Segments: **q** = every position before the chain (through `<think>\n`); **c** = the chain plus the
closing `\n</think>\n\n`; **p** = the answer prefix. A token that straddles a boundary belongs to the
later segment.

| mask | edit on at | question it answers |
|---|---|---|
| `none` | nowhere | unedited model on the edited model's chain |
| `all` | q + c + p | the edited model (= weights with ΔW merged) |
| `question_only` | q | does the question-position edit alone still carry to the answer? |
| `chain_and_answer_only` | c + p | does firing after the question suffice? |
| `answer_only` | p | the answer prefix restates the subject: does that restatement alone carry it? |
| `question_and_answer` | q + p | everything except the chain |

The same masks are run on the **B0 reference** (`ZEROTHINK` + prompt, i.e. an empty chain), the
row's `b0` block. Rows whose new and old values share a first token are flagged
`same_first_token` and excluded from readout (ii) (none of the 198 cases in the 32B cf200 pool,
checked with the R1-Distill-Qwen tokenizer).

Each row also carries `labels` from the Study-1 rows under `metrics` rules — `b0_ok`, `es`, `clr`,
`rr_loose`, `rr_strict`, `name_leak` (subject contains the old value) and `group`:
`reverted` (B0 success, B3 answer has o_old and not o_new), `held` (B0 success, B3 ES = 1),
`other`, `b0_fail` — and `route` from the route census when the case is in it.

## Commands

Inputs: delta files `<case_id>.pt` from `rt.deltas` for the Study-1 32B pool (fp32 ROME, layer 12,
target o_new), the Study-1 rows, `data/counterfact.jsonl`, `data/aliases.json`.

```bash
cd <project root>
# H200 x1: 32B in bf16 is 64 GB of weights, forward passes only (the Hopper bf16 NaN is in ROME's
# compute_v, which runs in rt.deltas under fp32, not here).
PYTHONPATH=src python -m rt.mech run --config experiments/rt/mech_r1qwen32b_rome.yaml \
    --model $W/models/DeepSeek-R1-Distill-Qwen-32B
# 3-case smoke first (see "Verify on GPU"):
PYTHONPATH=src python -m rt.mech run --config experiments/rt/mech_r1qwen32b_rome.yaml \
    --model $W/models/DeepSeek-R1-Distill-Qwen-32B --limit 3 --out results/rt/mech/smoke_r{rank}of{world}.jsonl
# fp32 cross-check on 5 cases, H200 x2 (fp32 weights are 131 GB; device_map auto splits them):
PYTHONPATH=src python -m rt.mech run --config experiments/rt/mech_r1qwen32b_rome.yaml \
    --model $W/models/DeepSeek-R1-Distill-Qwen-32B --dtype float32 --limit 5 \
    --out results/rt/mech/fp32check_r{rank}of{world}.jsonl
# readouts (CPU):
PYTHONPATH=src python -m rt.mech summarize "results/rt/mech/r1qwen32b_ROME_cf200_B3_r*of*.jsonl" \
    > results/rt/mech/r1qwen32b_ROME_cf200_B3_readouts.json
```

Output: one jsonl per shard (`--rank/--world`), a `_meta` header (git commit and dirty flag,
SHA-256 of `mech.py`/`edit_hooks.py`/`metrics.py`/`think_budget.py`, config, loaded dtype and
device map, BOS, software versions), then one row per (case, budget, kind). Reruns skip rows
already written (error rows too, unless `retry_errors: true`) and refuse an output whose header
signature (model, dtype, deltas, masks, alpha, BOS, ...) differs from the config. Cases without a
delta file are skipped without a row.

BOS: the Study-1 Qwen chains were generated without BOS, so the config sets `bos: false` to
reproduce the context that produced them. Leave `bos` unset to follow `think_budget._gen`
(BOS unless `WHYAAAI_NO_BOS`), e.g. for Study-2 chains from engine v2.

## Cost

The 198 cases with a greedy B3 chain in the 32B cf200 pool have chains of at most 1,397 tokens.
Per case: one trace pass (one row, ≤ ~1.7k tokens), one gate pass after the chain (six mask rows)
and one B0 gate pass (six short rows) — about 12k token-positions. The whole pool is a few minutes
of H200 time after model load; budget 0.5 GPU-hour including the smoke and the fp32 check.

## Pre-declared readouts (exploratory; REVISION.md §3 "探索：机制")

Population: B3 greedy rows with `group ∈ {reverted, held}`; name-leak cases (subject contains the
old value) are excluded by default, as in Study 1 (`summarize --keep-name-leak` to include them).
Intervals are 95% percentile bootstraps over cases (2,000 draws). No test is corrected or claimed
confirmatory; these readouts describe mechanism, they do not gate any claim.

**(i) Key-miss before the old value.** Among chains whose first old-value mention is preceded by at
least one chain subject mention, the indicator is `a_last_before_old < 0.5` (the last subject
mention before the old value did not fire the edit). Readout: its rate in reverted chains minus
its rate in held chains (`readout_i.diff_reverted_minus_held`), with both rates and n.
Reported alongside: the share of chains whose old value appears with no subject mention before it
(`old_without_prior_mention`), and `frac_high` / `max_a` over all chain subject mentions.
Interpretation: a positive difference whose interval excludes 0 supports (a); a difference near 0
with most mentions at a ≥ 0.5 says the edit does fire in the chain, so (a) is not the route.

**(ii) Where the edit must fire.** With effect(mask) = margin(mask) − margin(none) after the chain:

| quantity | field |
|---|---|
| effect of the full edit after the chain | `effect_chain.all` |
| effect of the question-position edit alone | `effect_chain.question_only` |
| share carried by later positions | `all_minus_question_only` |
| full-edit effect lost from B0 to after the chain | `b0_all_minus_chain_all` |
| question-only effect lost from B0 to after the chain | `b0_q_minus_chain_q` |

reported per group. Interpretation:
- `question_only` ≈ `all` after the chain: firing at later positions adds nothing, and the edit's
  reach from the question is what decides the answer.
- `question_only` well below `all`, and `chain_and_answer_only` (or `answer_only`) close to `all`:
  the edit must fire after the question — at chain or answer-prefix mentions — so a key-miss in the
  chain (readout i) can explain reversion.
- `all` itself well below its B0 value in reverted cases (`b0_all_minus_chain_all` > 0) even though
  the edit fires everywhere: the chain's content outweighs the edit — bridges (b) or dilution (c),
  not key-miss. `b0_q_minus_chain_q` > 0 isolates (c) for the question-position edit.
Route-census labels (`route`: Bridge / Recall / Reflective-override) exist for only a few of these
cases; report them descriptively.

## Verify on GPU before the full run

1. Smoke (3 cases): every trace row has `a` = 1 at `ref_tok`, and `ref_text` is the last piece of
   the subject in the question; no `error` rows; no NaN in `ref_z` or margins.
2. The edit works through the hooks in this context: on B0-success cases, `b0.masks.all.margin` >
   `b0.masks.none.margin` for nearly all rows (the edited model prefers o_new at B0).
3. bf16 vs fp32 on 5 cases: |Δa| at mentions below ~0.05 and |Δmargin| below ~0.1 nats; if larger,
   run the pool in fp32 on two GPUs.
4. The delta files are the Study-1 edits: deltas from `rt.deltas` are recomputed in fp32, so check
   the G0 gate (REVISION.md §4) passed for this pool before reading readout (ii) as Study-1's edit.

Known limits: the chain is re-tokenized from text, not the generated token ids (the answer phase
of Study 1 did the same); the gate reads only the first value token; partial mentions do not
cover pronouns (the per-position arrays allow that analysis later).
