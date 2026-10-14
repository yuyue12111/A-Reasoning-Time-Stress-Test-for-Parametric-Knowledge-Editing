# Execution sheet S3-H (H100 node) and supplement 1: the spec `orch_s3h.py` must implement

This archive copy (2026-10-13) is the reference for auditing the platform orchestrator. Rules: `prereg-arr-addendum-s3.md`
(Study 3 freeze, 4b75d08); deviations D9, D10 and D11 (`prereg-arr-deviations.md`).

## S3-H, issued 2026-10-12 (supersedes S3-B and the rest of the H-2 queue)

**Role.** Execute only this sheet. Change nothing and suggest nothing. For anything the sheet does not cover, stop
and write ⏸. The node is offline and needs no credentials; if a step asks for a token or password, stop and report.

**§0 Rulings.**
- Error rows pass by intent: every case needs a valid row. No result file is deleted or rewritten.
- The G7' re-run handling is acknowledged.

**§1 Rules that hold throughout.**
1. Never read any answer, chain or score of Study 3. Never read the answers or scores of the parent study
   (shards starting with s2). Only row counts, error-row counts, GPU utilisation and progress lines in logs may be
   looked at. The single exception is the §6 smoke, which uses two facts that were analysed long ago.
2. Before every GPU job:
   - `pgrep -f "rt[.](run|pool|deltas)"` must be empty;
   - every target card's memory.used must be < 1 GB.
3. Watchdog v3 keeps running.
4. Ladder after an exit that leaves a shard incomplete: 40000 → 26000 → 18000; for 70B, 34000 → 26000 → 18000.

**Variables.** PROJH and POUTH as already set on the node.
```
SHARE=/inspire/hdd/project/ai4education/public/why/xfer
GP=/inspire/hdd/global_public/public_models
M32=$GP/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B
M70=$GP/deepseek-ai/DeepSeek-R1-Distill-Llama-70B
P4090=/inspire/hdd/project/ai4education/public/why/why-arr
```
Environment: `cd $PROJH`; `export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PIP_NO_INDEX=1`.
Reports go to `$POUTH/report_h100.md`; each block's first line is `## <item> <✓|✗|⏸> <UTC time>`.

**§2 Stop G10' and sync the code.** Start only once `$SHARE/s3_code_full.bundle` exists.
1. `sha256sum $SHARE/s3_code_full.bundle` must be `fdbcafa8a1efd86daf0cd1816ac96b6cda839bb2078073f049cfe1caacd4303f`.
   Otherwise ⏸.
2. `pkill -f "python -m [r]t.run"`, then wait until all 8 cards are below 1 GB. G10' resumes later; none of its shards
   is deleted.
3. `git status --porcelain --untracked-files=no` must be empty. Otherwise ⏸.
4. Fetch and check out the bundle:
   ```
   git fetch $SHARE/s3_code_full.bundle claude/paper-review-understanding-8732e6:refs/remotes/bundle/s3 && git checkout -B claude/paper-review-understanding-8732e6 refs/remotes/bundle/s3
   ```
   HEAD must be `0be89c6`.
5. `git merge-base --is-ancestor 4b75d08 HEAD` must succeed.
6. `git diff --stat 4b75d08 HEAD -- <frozen list>` must print nothing. The frozen list:
   - `prereg-arr-addendum-s3.md`
   - `src/rt`
   - `src/study3/{confirm,end_entry,ext_manifest}.py` and `src/study3/tests`
   - `experiments/rt/pools/study2/manifest_r1qwen32b_fresh.jsonl` and `experiments/rt/pools/study3/candidates.jsonl`
   - `experiments/rt/deltas_s3_r1qwen32b_{fresh,ext}.yaml` and `experiments/rt/study3_r1qwen32b_{fresh,ext}.yaml`
   - `experiments/rt/study3_smoke.yaml` and `experiments/rt/pool_screen_s3.yaml`
7. Tests:
   - `src/rt/tests/run_all.py`: exit 0 and 193 passed;
   - `python3 -m unittest study3.tests.test_confirm`: OK.
8. The engine code hash must match the Study 2 32B shard header: `rt.run.code_sha256()` must equal the `code_sha256` in
   the header (first line) of `results/rt/s2/r1qwen32b_s2_base_r0of8.jsonl`. Print CODE_HASH_OK.
9. `PYTHONPATH=src:source/EasyEdit python3 -c "import easyeditor"` must succeed. If it fails, skip §3–§7 and go
   straight to §8, saying so in the report.
10. Nothing from Study 3 may exist yet:
    - the existing fresh deltas must number 0;
    - `results/rt/s3` must not exist;
    - `results/rt/pool_s3` must not exist.
11. When all of the above pass, `touch $SHARE/S3_CODE_OK`.

Edit environment: `export PYTHONPATH=src:source/EasyEdit WHYAAAI_DEVICE_MAP=balanced; unset WHYAAAI_DTYPE WHYAAAI_MODEL`.

**§3 W2-fresh edits (D9): 2 cards per process, world 4.**
1. Smoke:
   ```
   CUDA_VISIBLE_DEVICES=0,1 python3 -m rt.deltas run --config experiments/rt/deltas_s3_r1qwen32b_fresh.yaml --model-path $M32 --model-parallel --rank 0 --world 4 --device 0 --limit 2
   ```
   Then summarize. Pass: ok=2, editor_nan=0, max_rel_err<1e-4, median_p_target_after≥0.9. If it runs out of memory,
   switch to 4 cards per process, world 2, and smoke again. Any other failure: ⏸.
2. Full run: ranks r=0..3 on cards (0,1) (2,3) (4,5) (6,7), with `--rank $r --world 4`. Wait for every exit code to
   be 0.
3. `summarize "results/rt/deltas_logs/s3fresh/r1qwen32b_ROME_cf_r*.jsonl" > $POUTH/summarize_S3_fresh.json`. Pass:
   - cases=309 and ok=309;
   - errors empty and editor_nan=0;
   - max_rank=1 and max_rel_err<1e-4.
   On failure, re-run once with `--retry-errors`; if it still fails, ⏸.
4. `touch $SHARE/S3_D_FRESH_DONE`.

**§4 Extension screens: 5 base models, B0 only, 1 card per process, world 8.**
1. Take each model's path from the header (`['model']['path']`) of
   `$P4090/results/rt/pool/<tag>_pool_screen_r0of*.jsonl`. Order: r1qwen32b, r1qwen14b, r1llama8b, r1qwen7b, r1qwen1_5b.
   If any path is missing, ⏸.
2. Screen one model at a time, ranks r=0..7:
   ```
   CUDA_VISIBLE_DEVICES=$r WHYAAAI_MODEL=<path> PYTHONPATH=src python3 -m rt.pool screen --config experiments/rt/pool_screen_s3.yaml --model-tag <tag> --rank $r --world 8
   ```
   Then run `rt.pool qualify --model-tag <tag>` and report its line.
3. Run `python3 -m study3.ext_manifest` and report its line.
4. Before any work under §5, write the manifest's identity:
   - `echo "<sha256sum of experiments/rt/pools/study3/manifest_r1qwen32b_ext.jsonl> n=<lines> <UTC time>" > $SHARE/S3_EXT_MANIFEST.txt`;
   - `cp -a experiments/rt/pools/study3 $POUTH/pools_study3`;
   - `touch $SHARE/S3_EXT_MANIFEST_DONE`.

**§5 W2-ext edits.** As §3 steps 2–4, with these changes:
- config `deltas_s3_r1qwen32b_ext.yaml` and log prefix `s3d_ext`;
- summarize to `$POUTH/summarize_S3_ext.json`;
- cases = ok = the number of lines in `manifest_r1qwen32b_ext.jsonl`.

Then `touch $SHARE/S3_D_EXT_DONE`.

Generation environment: `export PYTHONPATH=src; unset WHYAAAI_DEVICE_MAP`.

**§6 Smoke on two facts already analysed.**
```
CUDA_VISIBLE_DEVICES=0 WHYAAAI_MODEL=$M32 python3 -m rt.run --config experiments/rt/study3_smoke.yaml --conditions base,rome_N --rank 0 --world 1 --device cuda --batch-size 16 --max-batch-tokens 40000
```
Pass:
- exit 0;
- `results/rt/s3smoke/` holds 8 data rows each for base and rome_N, with 0 errors;
- the English is coherent. Only `results/rt/s3smoke/` may be read.

**§7 Study 3 generation: 8 processes × 1 card, fresh first, then ext.**
1. For ranks r=0..7:
   ```
   CUDA_VISIBLE_DEVICES=$r WHYAAAI_MODEL=$M32 python3 -m rt.run --config experiments/rt/study3_r1qwen32b_<fresh|ext>.yaml --conditions base,rome_N --rank $r --world 8 --device cuda --batch-size 16 --max-batch-tokens 40000
   ```
2. Track progress only with `study3.end_entry --stopped-at progress --out /tmp/s3_progress.json`, and read only
   n_complete_efficacy, valid_rows and error_rows from it.
3. Pass, fresh: n_complete_efficacy=309 and every condition/probe/budget has 309 valid rows. Then
   `touch $SHARE/S3_G_FRESH_DONE`.
4. Pass, ext: the same, with the ext manifest's line count. Then `touch $SHARE/S3_G_EXT_DONE`.
5. Close-out, when both sub-worlds are complete or at 2026-12-31 23:59 UTC+8, whichever comes first:
   - run `study3.end_entry --stopped-at "<now UTC+8>"`;
   - `cp -a results/rt/s3 $POUTH/results/rt/`;
   - copy `s3_end_of_generation.json` to `$POUTH`;
   - `touch $SHARE/S3_END`;
   - never run `study3.confirm`.

**§8 Rest of the parent queue (order fixed by D10).**
1. G3'' (70B; world 8; 2 cards per process; 4 slots, two waves).
   - Smoke: `--run-tag s2smoke --limit 2 --max-batch-tokens 34000` on rank 0 with cards 0,1. Pass: 4 rows each for
     base and rome_N, coherent English.
   - Full: each rank k with `--rank $k --world 8 --max-batch-tokens 34000`.
   - Pass: base and rome_N have 100 valid rows each per rank.
2. G10': resume with the original command.
3. G11': as in H-2 originally, using r*of8.
4. Parent close-out: `sha256sum results/rt/s2/*.jsonl > $POUTH/parent_end_of_generation.txt`, the date, a copy to
   `$POUTH`, and `touch $SHARE/PARENT_END`.

## Supplement 1 (2026-10-13, CPU image; D11)

1. The parent end-of-generation entry was written now from the CPU image (done 03:03:37Z). D11 makes it the
   registered end point.
2. Parent items generated in any later window (70B, the rest of G10', G11') are a **second window**:
   - §8.4 must **not** overwrite `parent_end_of_generation.txt` or reuse the `PARENT_END` marker;
   - the second window needs its own end entry, for example `parent2_end_of_generation.txt` and `PARENT2_END`.
3. Do not restart the orchestrator until the leader has audited it and sends the go.
