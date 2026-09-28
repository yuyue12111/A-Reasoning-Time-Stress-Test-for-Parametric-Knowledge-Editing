# Semantic endpoint: judges and human annotation (REVISION.md §3)

Code: `src/rt/judge.py` (judge, aggregation), `src/rt/annotate.py` (human package, kappa, switch).
Tests: `PYTHONPATH=src ~/.venvs/why-rt/bin/python src/rt/tests/run_all.py` (exit code is the verdict).

## What the judge does

Each (question, final answer) is labelled NEW / OLD / BOTH_UNCLEAR / NEITHER relative to the two
candidate values. The judge sees only the question and the final answer: no chain, arm, budget,
model, or which value is the edit. The subject's name is replaced by `[SUBJECT]` (so a subject
named after the old value is not a reversion, and the judge cannot use its own knowledge of the
fact) and R1 markers such as `</think>` are removed. The two values are options A/B in a per-item
order fixed by `sha256(seed:item)`; C = both/unclear, D = neither. The label is the argmax of the
option-letter probabilities read from the next token after the chat template, with no text
parsing. With `--orders 2` the swapped order is scored too and the two are averaged, which cancels
position bias. Per row: `strict_semantic_es` = 1{NEW}, `semantic_reversion` = 1{OLD}.

Prompt (`PROMPT_VERSION rt-judge-prompt-v1`, `prompt_sha dc4649065540...`):
system turn `You are a careful annotator. You follow the instructions exactly and reply with a
single letter.` + user turn `judge.USER_TEMPLATE`. Templates that reject or drop a system turn get
it prepended to the user turn instead (recorded as `system_mode`).

## Judges and hardware

Two families that are not under test (the tested models are Qwen and Llama based):

| judge | HF id | weights (bf16) | GPU |
|---|---|---|---|
| gemma | `google/gemma-3-27b-it` | ~55 GB | 1 × H200 |
| mistral | `mistralai/Mistral-Small-3.1-24B-Instruct-2503` | ~48 GB | 1 × H200 |

**H200, one card per judge, bf16.** Why H200: bf16 weights plus batch 32 of ~450-token prompts
fit with room, and the fp32 fallback (`--dtype float32`, ~108 GB for 27B) fits only on H200. An
H100-80G also works in bf16 with `--batch-size 16`. The Hopper bf16 NaN we know is in ROME's
`compute_v`, not in forward passes; the scorer still stops on any NaN log-probability and tells you
to rerun with `--dtype float32`.

Download (Gemma is gated: accept the Gemma terms on its HF page with the account whose token you use):

```bash
hf download google/gemma-3-27b-it --local-dir $W/models/gemma-3-27b-it
hf download mistralai/Mistral-Small-3.1-24B-Instruct-2503 --local-dir $W/models/Mistral-Small-3.1-24B-Instruct-2503 \
    --exclude "consolidated.safetensors"        # 48 GB duplicate for vLLM; not needed
```

Environment: the platform env (torch 2.9.1, transformers 5.5.4). `--device-map auto` needs
`accelerate`; without it use `--device-map cuda:0` (loads through CPU RAM first). Gemma 3 loads as
`Gemma3ForConditionalGeneration`, Mistral 3.1 (`mistral3`) as `Mistral3ForConditionalGeneration`;
only text is fed. If `mistral-common` is installed, transformers gives Mistral a
`MistralCommonBackend` tokenizer (no Jinja template); that path is handled too, but pick one
environment and keep it, because the tokenizer hash is part of the resume check.

```bash
cd <project root>
export PYTHONPATH=src
GEMMA=$W/models/gemma-3-27b-it
MISTRAL=$W/models/Mistral-Small-3.1-24B-Instruct-2503
# Study-1 rows (the six ROME cells and their BASE runs; the local copy lives in "results 2/")
S1=(--rows 'results/probe/r1qwen1_5b_ROME_cf200_r*.jsonl' --rows 'results/pilot/r1qwen7b_ROME_cf200_r*of8.jsonl'
    --rows 'results/probe/r1qwen14b_ROME_cf200_r*.jsonl'  --rows 'results/probe/r1qwen32b_ROME_cf200_r*.jsonl'
    --rows 'results/probe/r1llama8b_ROME_cf200c2_r*.jsonl' --rows 'results/probe/r1llama70b_ROME_cf100_r*.jsonl'
    --rows 'results/probe/r1qwen1_5b_BASE_cf200_r*.jsonl' --rows 'results/pilot/r1qwen7b_BASE_cf200_r*.jsonl'
    --rows 'results/probe/r1qwen14b_BASE_cf200_r*.jsonl'  --rows 'results/probe/r1qwen32b_BASE_cf200_r*.jsonl'
    --rows 'results/probe/r1llama8b_BASE_cf200c2_r*.jsonl' --rows 'results/probe/r1llama70b_BASE_cf100_r*.jsonl')
```

Default probes are `efficacy,base,para0,para1,locality` (`--probes all` adds `open`). Study 1 is
10,357 rows / 10,163 distinct items (efficacy+base only: 4,981 / 4,916).

## Step 0: look at the prompt (CPU, tokenizer only, 1 min)

```bash
python -m rt.judge show "${S1[@]}" --model $GEMMA --n 2
python -m rt.judge show "${S1[@]}" --model $MISTRAL --n 2
```

Check: the rendered text ends in the generation prompt (`<start_of_turn>model\n` for Gemma,
`[/INST]` for Mistral); `system_mode` is `system` for both (Gemma 3 folds the system turn into the
first user turn itself); the Mistral text contains our system prompt and **no date** (its default
system prompt, which carries today's date, must be overridden); every letter has its own token
ids; `tokens_p50` is ~400-450.

## Step 1: self-check on GPU (H200, ~5 min including load)

```bash
CUDA_VISIBLE_DEVICES=0 python -m rt.judge selfcheck "${S1[@]}" --model $GEMMA --n 256
CUDA_VISIBLE_DEVICES=1 python -m rt.judge selfcheck "${S1[@]}" --model $MISTRAL --n 256
```

Pass if `letter_mass_p10 >= 0.9` (the model really answers with a letter; if not, retry with
`--assistant-prefix "Answer:"`, which then must be used for the whole run), `label_flips_batch_vs_single`
is 0-2 of 256 and `max_abs_dp` is small (bf16 batching noise). `prompts_per_s_batched` gives the
runtime: rows x orders / prompts_per_s.

## Step 2: judge (one H200 per judge, both in parallel)

```bash
CUDA_VISIBLE_DEVICES=0 python -m rt.judge run "${S1[@]}" --model $GEMMA   --orders 2 \
    --out results/judge/gemma3-27b/study1.jsonl &
CUDA_VISIBLE_DEVICES=1 python -m rt.judge run "${S1[@]}" --model $MISTRAL --orders 2 \
    --out results/judge/mistral-small-3.1/study1.jsonl &
wait
```

Study 2 (v2 rows, REVISION.md §4 schema) is the same with its shards, e.g.
`--rows 'results/rt/study2/*.jsonl'`. Split long runs into jobs of at most 2 h with
`--shard 0/2 --out .../study2_s0.jsonl` and `--shard 1/2 --out .../study2_s1.jsonl`.

Expected runtime (estimate; calibrate with Step 1): a 24-27B model in bf16 HF runs about 10-20
prompts/s on one H200 at ~450 tokens. Study 1 with `--orders 2` is ~20k prompts, so 20-35 min per
judge. Study 2 (~50k rows) is ~100k prompts, so 1.5-3 h per judge: use two shards.

Resume: rerun the identical command. Rows already in the file are skipped, verdicts are cached by
item, a torn last line from a killed job is cut off, and a run whose judge, tokenizer, template,
prompt, seed or orders differ from the file header is refused (write a new file). If a row shard
was regenerated rather than appended, start a new output file (`run` warns about stale rows).

## Step 3: semantic endpoints

```bash
python -m rt.judge score --judged 'gemma=results/judge/gemma3-27b/study1*.jsonl' \
    --judged 'mistral=results/judge/mistral-small-3.1/study1*.jsonl' --out results/judge/study1_semantic.json
```

Per condition (model_tag, editor, target_tag, dataset, condition, arm, alpha, decode, temperature)
and budget: semantic ES = P(NEW), RR = P(OLD | first B0 efficacy row NEW), i.e. the gating of
`metrics.score`; PS on para rows; Loc = P(not NEW) and Loc_correct = P(OLD) on locality rows; the
four-label shares per probe (e.g. `base`); and the lexical ES/RR/RRs/PS/Loc from the same rows
(identical to `metrics.score`). The two judges are combined by averaging their label probabilities
(argmax; an exact NEW/OLD tie is BOTH_UNCLEAR). The file also reports `split_rate` (judges'
argmax differ) and `order_consistency` (per judge, the two orders agree). In code:
`judge.combine_judges`, `judge.semantic_score`, `judge.semantic_by_case` (per-case indicators for
paired and cluster bootstraps).

## Human annotation (200 items, two annotators)

Build the package from the rows the switch is about (Study 2 efficacy rows; the judges must have
judged the same rows):

```bash
python -m rt.annotate build --rows 'results/rt/study2/*.jsonl' --where editor=ROME \
    --n 200 --floor 10 --out-dir results/annot/study2      # add --where filters to pick the condition
```

Strata are budget (B0, B3) x lexical cell (new-only, old-only, both, neither); allocation is
proportional to stratum size with at least 10 per stratum; the draw is fixed by `--seed` (2027).
Output: `items_A1.csv`, `items_A2.csv` (same items, own row order), `guide.md`, `key_HIDDEN.jsonl`,
`manifest.json`. Annotators see the same text as the judge, in the judge's primary option order.

Hand-off:
1. Give annotator 1 `items_A1.csv` + `guide.md`, annotator 2 `items_A2.csv` + `guide.md`. Never
   share `key_HIDDEN.jsonl` or `manifest.json`, and do not tell them where the answers come from.
2. Practice first on 20 items from a different pool (e.g. `build --rows <Study-1 ROME 32B> --n 20
   --floor 2 --seed 1 --out-dir results/annot/practice`), go through the guide together, and
   discuss only the practice items.
3. They label independently: one letter A-D in `label` per row (Excel, WPS or Google Sheets are
   fine; keep the columns; only `item_id` and `label` are read, so a re-save in another encoding
   or with `;` still scores). About 1.5-2 h each.

Score:

```bash
python -m rt.annotate score --package results/annot/study2 \
    --ann A1=returned/items_A1.csv --ann A2=returned/items_A2.csv \
    --judged 'gemma=results/judge/gemma3-27b/study2*.jsonl' \
    --judged 'mistral=results/judge/mistral-small-3.1/study2*.jsonl' \
    --out results/annot/study2/score.json
```

Reports Cohen's kappa (4 labels; ES = NEW vs rest; RR = OLD vs rest) for A1~A2, each human vs each
judge, the ensemble and the lexical rule, and judge~judge, with 95% bootstrap CIs (items resampled
within strata, 10,000 draws) and a design-weighted point estimate `k_popw`; confusion matrices;
precision/recall of the permissive and strict lexical reversion rules against the humans; and the
switch.

**Switch (to freeze in `prereg-arr.md`):** the semantic endpoint is primary iff the mean Cohen's
kappa between the ensemble label and each of the two annotators is >= 0.70 for both ES and RR
(binary, unweighted, point estimates on the 200-item sample); otherwise lexical strict is primary.
Also freeze: judges and their `hf.revision` (in each output header), `prompt_sha`, `--orders 2`,
`--seed 2027`, ensemble = mean probability, tie = BOTH_UNCLEAR, sample n = 200, floor = 10.

## Output row (one per input row)

`row_key`, `item` (content hash of what the judge saw), `row` (case_id, model_tag, editor, budget,
probe, condition, arm, alpha, decode, seed, temperature, delta_sha, src, line, ...), `values`,
`lexical` (new_hit, old_hit, cell), `scrubbed`, `truncated`, `source` (`judge` or `empty`),
`orders`, `p_letter` (A-D renormalised, per order), `logp_letter` (raw), `letter_mass`,
`render_sha`, `n_tokens`, `p` (NEW/OLD/BOTH_UNCLEAR/NEITHER, averaged over orders), `label`,
`margin`, `strict_semantic_es`, `semantic_reversion`. Line 1 is the provenance header (judge path,
class, config/tokenizer/chat-template hashes, HF revision and weight etags when downloaded with
`hf download --local-dir`, prompt, seed, orders, code hash, git); each invocation appends a `_run`
line.

## Known limits

- Only the full subject name is hidden; a surname alone ("Mendel's work") stays visible to judges
  and annotators alike.
- For locality rows the neighbour's name is not hidden (it is not in the case record); the lexical
  Loc there is unscrubbed too, as in `metrics.py`.
- bf16 batching changes probabilities slightly; Step 1 measures how often that flips a label.
