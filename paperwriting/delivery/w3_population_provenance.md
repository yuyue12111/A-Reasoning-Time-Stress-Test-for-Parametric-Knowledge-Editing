# What population the reported rates are rates of

W3-1. Reverse-engineered from the code and configs that produced the case set, so
that Section 3.1 can state the selection rule instead of leaving it implicit. This
file changes no reported number; it records where the estimand comes from.

---

## 1. The chain, step by step

| step | what happens | where |
|---|---|---|
| 1 | Cleaned CounterFact is read whole | `src/prefilter.py:57-58`, `data/counterfact.jsonl` (built by `src/build_dataset.py`) |
| 2 | Shuffled with a fixed seed (42) | `src/prefilter.py:59`, seed from `experiments/pilot.yaml:3` |
| 3 | Rows without an old value are dropped | `src/prefilter.py:60` |
| 4 | The first `3 x n = 600` survivors become the candidate frame | `src/prefilter.py:80` (`args.limit or 3 * n`), `n=200` from `pilot.yaml` |
| 5 | Each candidate is generated **once from the unedited model** at budget `B3` | `src/prefilter.py:119` (`tb.generate_with_budget(..., args.budget)`, default `B3` at `:66`) |
| 6 | A candidate is **kept iff the answer text matches an old-value alias** | `src/prefilter.py:120` (`metrics.hit(ans, c["o_old"], aliases)`) |
| 7 | Shards merge, dedupe by `case_id`, re-sort into the step-2 order, truncate to `2n = 400` | `src/prefilter.py:82-97` |
| 8 | **248 survived** | `plan.md` v1.19 (1), `analysis/10_pilot_rome_n200.md:4` |
| 9 | Every run re-shuffles those 248 with seed 42 and takes the first `n = 200` | `src/run_pilot.py:23-27` (`load_cases`) |

The model at step 5 is **DeepSeek-R1-Distill-Qwen-7B** (`pilot.yaml`
`hparams_overrides.model_name`) — the checkpoint the pilot ran on, not the
checkpoint any given later run uses.

Survival is `248 / 600 = 41.3%`, inside the `40-60%` band `plan.md:566` predicted
before the run. That agreement is the only independent corroboration of the 248;
`data/counterfact.prefiltered.jsonl` is gitignored and not in the workspace, so
the count is taken from the two run records above rather than recounted here.

## 2. One pool, six checkpoints

Every checkpoint config points at the same file and the same `n`, and each takes
the seed-42 prefix of it, so all six run **the identical 200 requests**:

| config | `dataset.path` | `n` | comment in file |
|---|---|---|---|
| `probe_qwen1_5b.yaml` | `data/counterfact.prefiltered.jsonl` | 200 | — |
| `pilot.yaml` (7B) | same | 200 | the file's own producer |
| `probe14b.yaml` | same | 200 | "复用 7B 预过滤集前 200(seed42 同序 → 与 7B 可比)" |
| `probe32b.yaml` | same | 200 | "与 14B/7B 同序可比(前 200 = 7B 全集)" |
| `probe_llama8b.yaml` | same | 200 | — |
| `probe_llama70b.yaml` | same | 200 | "与 7/14/32 同序可比" |

The comparability the configs claim is real. The cost is that the selection
predicate — *this* checkpoint knows the old value — was evaluated **only on the
7B**. At the other five the pool is not a knows-the-old-value set; it is a fixed
set of requests that one 7B checkpoint knew.

## 3. What this does to the estimand

Three consequences, in decreasing order of how much a reviewer will care.

1. **The rates are rates over this pool, not over CounterFact.** Edit success,
   reversion and leakage levels are all conditioned on step 6. A reader who takes
   `19.3%` as a CounterFact-wide resurfacing rate is reading it wrong, and nothing
   in the current text stops them.

2. **The selection budget coincides with one arm of the headline pair.** Step 5
   read a `B3` generation. The headline contrast is `B0` against `B3`. So the
   filter is not outside both arms: cases enter because the unedited model
   produced the old value *while thinking*. A pool chosen that way would, if
   anything, favour finding the drop we report. Nothing in the runs measures the
   size of that; the test would be a `B0`-gated filter, which was never run.

3. **The filter model is not the tested model.** For the two headline cells
   (Qwen-32B, Llama-70B) the pool encodes 7B knowledge. This cuts both ways and we
   do not claim a direction: a larger checkpoint likely knows a superset, so the
   pool is not obviously adverse, but it is also not a knows-the-old-value set for
   the cell being reported.

## 4. What Section 3.1 now says

Section 3.1 carries a `Which requests we test.` paragraph giving steps 2-6 and 9,
the 600 / 248 / 200 counts, the one-pool-six-checkpoints fact, and consequences 1
and 2 above. Consequence 3 is stated as the "one checkpoint's knowledge, reused
unchanged" clause rather than as a separate sentence, for space.

The numbers it prints are bound to `protocol.population` in
`paperwriting/results.json`, which is an M03-class restatement: every field is a
constant lifted from the code or config cited in the table above, except
`survivors`, which is the run record from step 8.

## 5. Edit hyperparameters, recorded here for the same reason

Not part of the population question, but the same class of unstated protocol
fact, and Section 3.1 now states it.

| checkpoint | ROME layer | how the layer was chosen | clamp |
|---|---|---|---|
| Qwen-1.5B | 5 | relative-depth rule (28 layers, same as 7B) | 4 |
| Qwen-7B | 5 | **scanned** `{5, 7, 10}`, n=40, B0: generative ES .55/.475/.40, only layer 5 reaching Loc .85 | 4 |
| Qwen-14B | 9 | relative-depth rule, `48 x 0.18` | 4 |
| Qwen-32B | 12 | relative-depth rule, `64 x 0.18` | 4 |
| Llama-8B | 6 | **scanned** layer `{5, 6, 7}` x clamp `{2, 3}`, n=60 | **2** |
| Llama-70B | 14 | relative-depth rule, `80 x 0.18` | 4 |

Sources: `editors.ROME.layers` in each `experiments/probe_*.yaml`;
`clamp_norm_factor` default 4 from `source/EasyEdit/hparams/ROME/qwen2.5-7b.yaml:11`
with the Llama-8B override at `experiments/probe_llama8b.yaml`; the two scans from
`plan.md` v1.18 (2) and v1.99 (2), the latter having already re-verified the claim
against the configs.

Two things follow that the manuscript did not say before this round.

* **Four of the six edit layers were never scanned.** They sit at one fixed
  fraction of the stack, transferred from the one checkpoint that was. The layer
  is therefore a per-checkpoint setting that co-varies with the checkpoint axis
  the headline is reported along.
* **The clamp is not uniform across the Llama lineage.** Llama-8B's scan moved it
  from 4 to 2 because the borrowed value cost locality; Llama-70B, a headline
  cell, kept 4 without a scan. `capability.families.R1-Distill-Llama._note`
  records that in-chain leakage was stable across clamp 2/3/4 (.31-.33), which
  bounds but does not eliminate the concern.

Neighbour-prompt target-value non-leakage, from
`capability.families.*._loc`: Qwen-1.5B .954, Qwen-32B .958, Llama-8B .835,
Llama-70B .930. Qwen-7B and Qwen-14B are `null` — **not recorded anywhere in the
workspace**, so the manuscript reports the four that exist and does not
reconstruct the two that do not. Llama-8B's .835 is below the .85 the layer scan
used as its own acceptance line; it was kept rather than retuned, which the
project recorded at the time as a deliberate refusal to tune to a threshold.
