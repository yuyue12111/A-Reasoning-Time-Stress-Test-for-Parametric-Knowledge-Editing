# Engine v2 · computing the edit deltas (`rt.deltas`)

`python -m rt.deltas run` makes one fp32 EasyEdit edit per case exactly as Study 1's `edit_loop`
did (same vendor patches, `sequential_edit=True`, one request), exports ΔW = W_edit − W_orig as
rank-1 factors to `deltas/<model_tag>/<editor>/<target_tag>/<case_id>.pt` and restores the model.
Generation later reads these files in bf16 through `rt.edit_hooks.EditBank`; no generation happens
here.  Hyperparameters: `experiments/rt/deltas_models.yaml` (rationale inline).  Authoritative
plan: `REVISION.md` §3–§5.

All commands run from the project root on the platform:

```bash
export PYTHONPATH=src:source/EasyEdit
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export WHYAAAI_WIKI_PARQUET=/inspire/dataset/wikipedia/20231101/20231101.en   # English only
M32=/inspire/hdd/global_public/public_models/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B
unset WHYAAAI_MODEL WHYAAAI_DTYPE      # rt.deltas sets the dtype itself (float32) and takes --model-path
mkdir -p results/rt/deltas_logs
```

`--model-path` must be the same string in every step for a model: EasyEdit names the mom2 files by
the path's last component, and the delta records carry it in their hparams hash.  The path must
contain `qwen` (Qwen family) or `llama` (Llama family), because EasyEdit picks its loader by
substring; `rt.deltas` refuses otherwise (symlink e.g. `.../Qwen-QwQ-32B` if needed).

## GPU classes (why)

| job | memory | layout on one 8×H200 node |
|---|---|---|
| ROME, R1-Qwen-32B / QwQ-32B / Qwen2.5-32B-Instruct, fp32 | 32.8B × 4 B = 131 GB (122 GiB) of weights; the ROME step itself needs a few GiB more (Study 1 ran it this way) | **H200 only** (141 GB); H100-80G cannot hold fp32 32B. 1 GPU per process → 8 shards |
| MEMIT / AlphaEdit, 32B, fp32 | weights + per-layer solves on 27648² matrices (MEMIT in float64: ~25 GB transient; AlphaEdit: P, cache, solve ~20 GB) — the 2026-07 single-GPU attempt OOMed | 2 H200 per process (`model_parallel: true`, `WHYAAAI_DEVICE_MAP=balanced`) → 4 shards |
| ROME, R1-Llama-70B, fp32 | 70.6B × 4 B = 282 GB | 4 H200 per process (model parallel) → 2 shards |
| ROME, 14B / 8B / 7B / 1.5B, fp32 | 59 / 32 / 30 / 7 GB | 1 GPU per process (H100 would also do) → 8 shards |
| `precompute-stats`, 32B, **bf16** | 65.5 GB of weights + ≤ 15 GB of fp32 moment matrices (5 layers) | 1 H200 per rank, 8 ranks split the samples |
| `alphaedit-P` | 5 SVDs of 27648² fp32 (~15 GB on the SVD device) | 1 GPU (or `--svd-device cpu`, slower) |

CPU RAM per AlphaEdit-32B process: P (5 × 3.06 GB) + `cache_c` (same) + mom2 cache ≈ 35–45 GB.

## Step 0 · pools (done for G0)

The G0 configs (deltas and generation) both read `experiments/rt/pools/study1_cf200.jsonl`: the
Study-1 32B pool in Study 1's own run order (seed-42 shuffle, cross-checked against the 14B, 8B,
sup and samp runs), with a `.sha256` sidecar.  `data/pools/study1_r1qwen32b_ids.json` is the same
200 ids in first-seen shard order, kept as the `export-pool` audit record (source hashes; every id
in CounterFact; efficacy prompts identical).  Study-2 pools are the jsonl manifests written by
`rt.pool qualify`; `rt.deltas` reads them directly.  To regenerate the audit record:

```bash
python -m rt.deltas export-pool --name study1_r1qwen32b --out data/pools/study1_r1qwen32b_ids.json \
  --shards "results 2/probe/r1qwen32b_ROME_cf200_r*of8.jsonl"
```

Study-2 pools come from `pool.py` (not yet written) in the same `{"case_ids": [...]}` format.

## Step 1 · G0 parity deltas: ROME, R1-Qwen-32B, Study-1 pool (8 × H200, ROME needs no stats)

```bash
python -m rt.deltas run --config experiments/rt/deltas_g0_r1qwen32b.yaml \
  --model-path $M32 --limit 8 --rank 0 --world 1 --device 0 --dry-run   # plan only
# 20-case smoke first (5 min): look at the log before launching the rest
for r in 0 1 2 3; do python -m rt.deltas run --config experiments/rt/deltas_g0_r1qwen32b.yaml \
  --model-path $M32 --limit 20 --rank $r --world 4 --device $r \
  > results/rt/deltas_logs/g0_smoke_r$r.out 2>&1 & sleep 20; done; wait
python -m rt.deltas summarize results/rt/deltas_logs/r1qwen32b_ROME_cf_r*of4.jsonl
# full pool; already-written cases are skipped (resume is by file), so the smoke cases are reused
for r in $(seq 0 7); do python -m rt.deltas run --config experiments/rt/deltas_g0_r1qwen32b.yaml \
  --model-path $M32 --rank $r --world 8 --device $r \
  > results/rt/deltas_logs/g0_r$r.out 2>&1 & sleep 20; done; wait
python -m rt.deltas summarize results/rt/deltas_logs/r1qwen32b_ROME_cf_r*of8.jsonl
```

Loads are staggered by 20 s (8 simultaneous 131 GB reads from GPFS have stalled before, RUNBOOK §8).
Expect ~30–60 s per case (Study-1 logs for fp32 ROME-32B) → 200 cases ≈ 15–25 min on 8 GPUs after
the ~3 min load.  A different `--world` for the full run only changes the shard log names; the
delta files are shared.

## Step 2 · mom2 statistics for MEMIT/AlphaEdit, then the AlphaEdit projector

Order matters: statistics must be complete (merged and verified) **before any MEMIT/AlphaEdit delta
shard starts**; `run` refuses to start without them, and inside an edit process EasyEdit is
forbidden from computing them (`vendor_patches/easyedit_mom2_cache_only.py`).

```bash
# 2a single process, CPU is enough: builds the datasets cache for the 41 English shards, checks the
#    corpus is English and that our sample order/tokenization equals EasyEdit's, prints file paths
python -m rt.deltas precompute-stats --model r1qwen32b --model-path $M32 --world 8 --prepare
# 2b 8 ranks x 1 H200, bf16 forward, fp32 sums; each rank takes every 8th group of 100 texts
for r in $(seq 0 7); do python -m rt.deltas precompute-stats --model r1qwen32b --model-path $M32 \
  --rank $r --world 8 --device $r > results/rt/stats_r$r.out 2>&1 & sleep 20; done; wait
# 2c single process, CPU: sum the partial files into EasyEdit's cache files, then ask EasyEdit's
#    own layer_stats to load each one with recomputation forbidden
python -m rt.deltas precompute-stats --model r1qwen32b --model-path $M32 --world 8 --merge
# 2d single process, 1 GPU: null-space projector for AlphaEdit (reads the merged statistics)
python -m rt.deltas alphaedit-P --model r1qwen32b --model-path $M32 --svd-device cuda:0
```

One pass traces all five layers (10–14) and stops after layer 14 (22 % of the network).  With
100,000 Wikipedia articles truncated at 4,096 tokens, a rank handles ~12,500 articles: expect
roughly 20–60 min per rank (bf16 forward plus fp32 `x.T @ x` on 27648-wide features with TF32
off; the `[mom2] k/125 groups` progress lines give the rate).  Resume: a rank whose partial files
exist is skipped; merged files are never recomputed.

**Step 2x (once, recommended before 2b; 8 × H200 for ~10 min): end-to-end check against Study 1.**
`data/stats_r1qwen14b` holds the statistics EasyEdit computed lazily for Study 1's MEMIT-14B
(layers 7–11).  Rebuild layers 7–9 with this pipeline into a scratch directory and compare:

```bash
M14=/inspire/hdd/project/ai4education/ky26140/why/models/DeepSeek-R1-Distill-Qwen-14B
python -m rt.deltas precompute-stats --model r1qwen14b --editors MEMIT --model-path $M14 \
  --stats-dir data/stats_check14b --world 8 --prepare
for r in $(seq 0 7); do python -m rt.deltas precompute-stats --model r1qwen14b --editors MEMIT \
  --model-path $M14 --stats-dir data/stats_check14b --rank $r --world 8 --device $r & sleep 10; done; wait
python -m rt.deltas precompute-stats --model r1qwen14b --editors MEMIT --model-path $M14 \
  --stats-dir data/stats_check14b --world 8 --merge
for L in 7 8 9; do f=DeepSeek-R1-Distill-Qwen-14B/wikipedia_stats/model.layers.$L.mlp.down_proj_float32_mom2_100000.npz
  python -m rt.deltas compare-stats data/stats_check14b/$f data/stats_r1qwen14b/$f; done
```

Equal `count` proves the same sample, tokenization and truncation.  The header of the Study-1
MEMIT-14B run (2026-07-06) does not record the dtype; `experiments/memit14b.yaml` instructs
`WHYAAAI_DTYPE=float32`, so those statistics most likely come from an fp32 forward and `rel_fro`
then measures the bf16 deviation itself (had they come from a bf16 model, it would be at the level
of summation-order noise).  Record the three numbers in the reproducibility notes.

Output (exact EasyEdit names; MEMIT and AlphaEdit share them):
`data/stats_r1qwen32b/DeepSeek-R1-Distill-Qwen-32B/wikipedia_stats/model.layers.{10..14}.mlp.down_proj_float32_mom2_100000.npz`
(+ `.provenance.json`), and `data/stats_r1qwen32b/alphaedit/null_space_project_L10-14.pt` (+ `.json`
with the null-space dimension of every layer).

## Step 3 · 20-case smoke for every new editor or model (before its full run)

```bash
for ed in MEMIT AlphaEdit; do
  for r in 0 1 2 3; do CUDA_VISIBLE_DEVICES=$((2*r)),$((2*r+1)) WHYAAAI_DEVICE_MAP=balanced \
    python -m rt.deltas run --config experiments/rt/deltas_g0_r1qwen32b.yaml --editor $ed \
    --model-path $M32 --limit 20 --rank $r --world 4 --device 0 \
    > results/rt/deltas_logs/smoke_${ed}_r$r.out 2>&1 & sleep 30; done; wait
  python -m rt.deltas summarize results/rt/deltas_logs/r1qwen32b_${ed}_cf_r*of4.jsonl
done
```

Pass when (compare with the ROME-32B summary over the same 20 cases, i.e. `--limit 20` of step 1):
* 20/20 `ok`; `max_rank` 1; `editor_nan` 0 (no NaN in the printed optimisation losses);
* `median_p_target_after` comparable to ROME's (the edit takes on the edit prompt);
* AlphaEdit: `null_dim` in the projector sidecar strictly between 0 and 27648 on every layer
  (threshold 2e-2 was tuned on Llama3-8B/GPT-J; `null_dim` 0 makes every ΔW exactly zero, which
  shows up as `delta is identically zero` error rows);
* afterwards, once `engine.py` exists: B0 generative ES and locality on these 20 cases.
The same smoke (ROME) gates QwQ-32B and Qwen2.5-32B-Instruct (layer 12 is unvalidated there,
`verify:` in the models file); if an edit clearly fails to take, scan layers {10, 12, 16} and record
the choice in `prereg-arr.md` before any Study-2 delta is computed.

## Step 4 · full runs

Same commands as the smoke without `--limit` and with the Study-2 pool config.  Per case
(estimates, confirm in the smoke with `median_wall_s`): ROME-32B ~30–60 s (1 GPU), MEMIT/AlphaEdit-32B
~1–2 min (2 GPUs, 5 layers), ROME-70B ~1–2 min (4 GPUs), ROME ≤ 14B a few seconds to ~20 s.
Budget line in REVISION §6: ~2,800 32B deltas × ~45 s.

Plausibility-matched targets (`target_tag: plausible`):

```bash
python -m rt.targets --model r1qwen32b --model-path $M32 --pool data/pools/<pool>.json \
  --out results/rt/targets/r1qwen32b_plausible.jsonl            # 1 H200, bf16, minutes
python -m rt.deltas run --config <cfg>.yaml --target-tag plausible \
  --targets-file results/rt/targets/r1qwen32b_plausible.jsonl --model-path $M32 --rank ...
```

## What the files and logs contain

* delta (`torch.load`): `format` rt-delta-v1, `case_id`, `model_tag`, `editor`, `target`,
  `target_tag`, `module_tmp`, `layers {L: {A [1,in], B [out,1]}}` (fp32, ΔW = B @ A), `fit {L: rank,
  rel_err, tol, storage_floor, sigma, rel_delta}`, `diag` (log-probs of the first token and of the
  whole continuation for " "+target / o_new / o_old before and after the edit, the editor's printed
  losses, EasyEdit's own pre/post `rewrite_acc` — a teacher-forced logits metric that is never mixed
  with generative ES — the AlphaEdit cache reset, wall times), `request`, `hparams`, `hparams_sha`,
  `sha` (content hash checked by `load_delta`).
* shard log `results/rt/deltas_logs/<model>_<editor>_<tag>_r<k>of<n>.jsonl`: one `_meta` row per
  session (git, code hashes, config, pool hash, environment, preflight facts, loaded runtime), one
  `_templates` row (EasyEdit's sampled context templates), then one row per case: `ok` (path, sha,
  fit, first-token log-probs) or `error` (`stage` ∈ prepare / diag_before / edit / extract / factor /
  diag_after / save / restore).
* Resume is by file: an existing delta is skipped (after checking its hparams hash and target);
  cases with an error row are skipped unless `--retry-errors` (e.g. after an OOM).  A log written
  with another run signature (editor, hparams, factor settings) is refused.  A `restore` error means
  the weights could not be verified back to base: the shard stops by design.

## Deviations from Study 1 / the legacy loop

1. mom2 statistics come from a bf16 forward pass (fp32 accumulation), not from the fp32 model inside
   the first edit; computed data-parallel over 8 ranks and summed in float64.  Same corpus (English
   2023-11 Wikipedia, pinned), sample (seed 1, 100,000 articles), tokenization and truncation.
2. The edited weights are snapshotted to CPU and restored from the snapshot with a bitwise check, in
   addition to EasyEdit's `weights_copy` restore; an exception inside `edit()` is rolled back too.
3. AlphaEdit's `cache_c` is reset before every case (EasyEdit never resets it within a process).
4. All models are edited in fp32 (Study 1's headers do not record the dtype of the June small-model
   runs, which may have used bf16 on 4090 cards).
5. Delta files instead of in-place generation; no generation in this step.
6. `AlphaEdit` projector computed by `alphaedit-P` (default SVD on GPU; EasyEdit would compute it on
   CPU — and crashes on Qwen before getting there, vendor_patches/README §1); the sidecar counts the
   singular values within 1 % of the threshold so the backend choice can be audited.
