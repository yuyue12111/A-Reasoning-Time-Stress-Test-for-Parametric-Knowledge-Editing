# Engine v2 runs (REVISION.md §3–§4)

| File | What it runs |
|---|---|
| `study1_g0_r1qwen32b.yaml` | G0 parity gate: Study-1 32B pool (200), `base` + ROME `rome_N`, B0/B3, efficacy |
| `pool_screen.yaml` | Study-2 pool: used-id exclusion, 1600 candidates, per-model base B0 screen, first 400 qualified |
| `study2_r1qwen32b.yaml` | Study-2 32B: base, N/T/D/P/C arms, B0P, B1, α ∈ {0.5, 2, 3}, sampling ×4, IKE, MEMIT, AlphaEdit; stage 2: own/filler/swap chains |
| `pools/study1_cf200.jsonl` | Study-1 case order, rebuilt from the Study-1 shards (`rt.pool ids-from-shards`), with `.sha256` |

Code: `src/rt/engine.py` (batched two-phase generation), `src/rt/run.py` (config → jsonl), `src/rt/pool.py`
(pool). Each module docstring states its contract; `engine.py` lists every deviation from the legacy
`think_budget` generator.

## Before the first run

- **ΔW files** come from `src/rt/deltas.py` (built separately): `deltas/<model_tag>/<editor>/<target_tag>/<case_id>.pt`,
  format `rt-delta-v1`. A missing or mismatched delta (case, model tag, editor, target tag, module) becomes an
  error row for that case and condition, never a silent base-model row; rerunning retries it.
- **Model path**: `export WHYAAAI_MODEL=<local model dir>` (or set `model.path` in the YAML). The tokenizer is
  loaded with `AutoTokenizer` and passed through `r1_tokenizer.fix_r1_tokenizer`; the run refuses to start if a
  template marker (`<｜User｜>`, `</think>`, … or `<|im_start|>`/`<|im_end|>`) is not a single token.
- One process per GPU; `CUDA_VISIBLE_DEVICES=$r` makes the process see one card as `cuda`. Generation is bf16.
- `--dry-run` prints the plan (pending rows per condition, output paths) and checks resume compatibility
  without loading the model. `--limit N --run-tag <tag>_smoke` runs the first N cases of each shard into
  separate files. Look at a few smoke generations by eye before a long run.
- Memory: `max_batch_tokens` bounds rows × (longest prompt + new tokens). 128000 leaves headroom for the
  32B (65 GB bf16 weights + 256 KiB KV per token + prefill activations on a 141 GB H200); lower it if a chunk
  logs an OOM (failed chunks become `error_kind: engine` rows and are retried on the next launch; three
  failed chunks in a row stop the process). Batch size, token budget and chunking are not part of the resume
  hash, so they can be changed between launches.

All commands run from the project root on the 8×H200 node.

## G0 parity gate (R1-Distill-Qwen-32B)

Study 1 32B ran before manual BOS was added to `think_budget._gen`, so G0 runs without BOS.

```bash
cd <project root>
export WHYAAAI_MODEL=<models>/DeepSeek-R1-Distill-Qwen-32B
export WHYAAAI_NO_BOS=1                       # parity with Study 1 32B (2026-06-23, pre-BOS)
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
mkdir -p logs/rt
PYTHONPATH=src python -m rt.run --config experiments/rt/study1_g0_r1qwen32b.yaml --rank 0 --world 8 --dry-run
for r in $(seq 0 7); do
  CUDA_VISIBLE_DEVICES=$r PYTHONPATH=src nohup python -m rt.run \
    --config experiments/rt/study1_g0_r1qwen32b.yaml --rank $r --world 8 \
    > logs/rt/g0_r$r.log 2>&1 &
done; wait
unset WHYAAAI_NO_BOS
```

Outputs: `results/rt/g0/r1qwen32b_g0_{base,rome_N}_r{0..7}of8.jsonl`.

## Study-2 pool

```bash
# CPU, on the machine that holds the full history (results/); then commit experiments/rt/pools/study2/
PYTHONPATH=src python -m rt.pool build --config experiments/rt/pool_screen.yaml

# GPU, once per model (model_tag must be a key of `models:` in pool_screen.yaml)
export WHYAAAI_MODEL=<models>/DeepSeek-R1-Distill-Qwen-32B
for r in $(seq 0 7); do
  CUDA_VISIBLE_DEVICES=$r PYTHONPATH=src nohup python -m rt.pool screen \
    --config experiments/rt/pool_screen.yaml --model-tag r1qwen32b --rank $r --world 8 \
    > logs/rt/pool_r1qwen32b_r$r.log 2>&1 &
done; wait

# CPU: manifest_<tag>.jsonl (+ .sha256), qualify_<tag>.jsonl (every decision), summary_<tag>.json
PYTHONPATH=src python -m rt.pool qualify --config experiments/rt/pool_screen.yaml --model-tag r1qwen32b
```

For the 70B (two cards per process, four processes): `CUDA_VISIBLE_DEVICES=$((2*r)),$((2*r+1))` with
`--rank $r --world 4` (its `models:` entry sets `device_map: auto`). QwQ-32B and Qwen2.5-32B-Instruct use the
`qwq` and `instruct_cot` templates from their `models:` entries.

## Study 2, R1-Distill-Qwen-32B

```bash
export WHYAAAI_MODEL=<models>/DeepSeek-R1-Distill-Qwen-32B
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
# stage 1: everything except the supplied-chain conditions
for r in $(seq 0 7); do
  CUDA_VISIBLE_DEVICES=$r PYTHONPATH=src nohup python -m rt.run \
    --config experiments/rt/study2_r1qwen32b.yaml --rank $r --world 8 --stage 1 \
    > logs/rt/s2_stage1_r$r.log 2>&1 &
done; wait
# stage 2: own / filler / swap chains; needs rome_N B3 chains from all eight stage-1 shards
for r in $(seq 0 7); do
  CUDA_VISIBLE_DEVICES=$r PYTHONPATH=src nohup python -m rt.run \
    --config experiments/rt/study2_r1qwen32b.yaml --rank $r --world 8 --stage 2 \
    > logs/rt/s2_stage2_r$r.log 2>&1 &
done; wait
```

`--conditions rome_N,rome_T` restricts a launch to some conditions. Adding a condition to the YAML later
does not invalidate existing shards: each shard's resume hash covers only its own condition.

## Reading the outputs

Each condition has its own shards, `<out_dir>/<model_tag>_<run_tag>_<condition>_r<rank>of<world>.jsonl`.
Line 1 is the `_meta` header (git hash and dirty flag, config and code hashes, resolved condition spec,
environment, torch/transformers versions, model path/dtype/device map, template). Rows follow REVISION.md §4
plus `chain_batch_id`, `template`, and, where relevant, `bias` (arm target, token ids, penalty, whether it
acted, decode steps), `user_prefix` (IKE) and `given` (chain transform and source case). Error rows carry
`error_kind` and no `probe`, so `metrics` skips them.

```bash
PYTHONPATH=src python -c "
import glob, json, metrics
paths = sorted(glob.glob('results/rt/g0/r1qwen32b_g0_rome_N_r*of8.jsonl'))
open('/tmp/g0_rome_N.jsonl', 'w').writelines(l for p in paths for l in open(p))
cases = [json.loads(l) for l in open('data/counterfact.jsonl')]
aliases = json.load(open('data/aliases.json'))
print(metrics.score('/tmp/g0_rome_N.jsonl', cases, aliases))
print(metrics.drop_bootstrap('/tmp/g0_rome_N.jsonl', cases, aliases))"
```
