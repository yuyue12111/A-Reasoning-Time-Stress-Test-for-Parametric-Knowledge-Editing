# Execution sheet S3-G (8×RTX 4090 48 GB node): Study 3 in full

Issued 2026-10-14. Rules: `prereg-arr-addendum-s3.md` (frozen at 4b75d08), deviation D12 (`111ab67`), registry entry 12.
This sheet supersedes S3-H and its supplement. `orch_s3h.py` and `watchdog.py` are **not** used on this node.

**Role.** Execute only this sheet. Change nothing and suggest nothing. For anything the sheet does not cover, stop
and write ⏸. Never read, print or copy credential files, and never put a token in a command, URL or log. If any step
asks for a password or token, stop and report.

## §0 Rules that hold throughout

1. **Blinding.** Never open any answer, chain, hit or score in `results/rt/s3/` or `results/rt/pool_s3/`. You may look
   only at: row counts, error-row counts, the printed lines of `rt.pool qualify`, `study3.ext_manifest`,
   `rt.deltas summarize` and `study3.end_entry`, GPU utilisation and memory, process lists and log tails that show
   progress or tracebacks. The single exception is `results/rt/s3smoke/` (§5), whose two facts were analysed long ago.
2. **Before every GPU step:** `pgrep -f "rt[.](run|pool|deltas)"` prints nothing, and every target card has
   memory.used < 1 GB (`nvidia-smi --query-gpu=index,memory.used --format=csv`).
3. **Never delete or rewrite** a result file, delta, log or manifest. Error rows stay in the shards.
4. **Never run** `python3 -m study3.confirm`.
5. **Reports** go to `$POUT/report_4090_s3.md`. Each block starts with `## <item> <✓|✗|⏸> <UTC time>`.
6. **Hung process.** While a GPU step runs, check every 10 minutes. If a process's cards show 0% utilisation and its log
   has not advanced for 20 consecutive minutes, kill that one PID and resume the same command once. If it hangs again: ⏸.
7. **Any other crash** (traceback that is not CUDA out-of-memory): resume the same command once. If it crashes again: ⏸.

## Variables

```
PROJ=/inspire/hdd/project/ai4education/public/why/why-arr
PROJH=/inspire/hdd/project/ai4education/public/why/why-arr-h100
POUT=/inspire/hdd/project/ai4education/public/why/platform_out
SHARE=/inspire/hdd/project/ai4education/public/why/xfer
GP=/inspire/hdd/global_public/public_models
M32=$GP/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B
MW=/inspire/hdd/project/ai4education/public/why/models
```
`cd $PROJ; mkdir -p logs/s3; export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`. Every command below runs from
`$PROJ` in this shell. The allocator setting and the absence of HF offline flags match the Study 2 runs on this node.

## §1 Code and environment (no GPU)

1. `git status --porcelain --untracked-files=no` must print nothing. Otherwise ⏸.
2. `GIT_TERMINAL_PROMPT=0 git fetch origin claude/paper-review-understanding-8732e6 && git checkout -B claude/paper-review-understanding-8732e6 FETCH_HEAD`
   - Then `git merge-base --is-ancestor 111ab67 HEAD` must succeed.
   - **Only if the fetch fails:** verify `sha256sum $SHARE/s3_code_full.bundle` is
     `fdbcafa8a1efd86daf0cd1816ac96b6cda839bb2078073f049cfe1caacd4303f`, then
     `git fetch $SHARE/s3_code_full.bundle claude/paper-review-understanding-8732e6:refs/remotes/bundle/s3 && git checkout -B claude/paper-review-understanding-8732e6 refs/remotes/bundle/s3`;
     HEAD must then be `0be89c6`. Say in the report which path was used.
3. `git merge-base --is-ancestor 4b75d08 HEAD` must succeed.
4. This must print nothing:
   ```
   git diff --stat 4b75d08 HEAD -- prereg-arr-addendum-s3.md src/rt src/study3/confirm.py src/study3/end_entry.py src/study3/ext_manifest.py src/study3/tests experiments/rt/pools/study2/manifest_r1qwen32b_fresh.jsonl experiments/rt/pools/study3/candidates.jsonl experiments/rt/deltas_s3_r1qwen32b_fresh.yaml experiments/rt/deltas_s3_r1qwen32b_ext.yaml experiments/rt/study3_r1qwen32b_fresh.yaml experiments/rt/study3_r1qwen32b_ext.yaml experiments/rt/study3_smoke.yaml experiments/rt/pool_screen_s3.yaml
   ```
5. Software must be exactly torch `2.8.0a0+5228986c39.nv25.06`, transformers `5.5.4`, tokenizers `0.22.1`,
   accelerate `1.13.0`, numpy `1.26.4`:
   `python3 -c "import torch,transformers,tokenizers,accelerate,numpy;print(torch.__version__,transformers.__version__,tokenizers.__version__,accelerate.__version__,numpy.__version__)"`
   - If torch differs: ⏸.
   - If only other packages differ or are missing: `python3 -m pip install --no-index --no-deps --find-links $SHARE/wheels -r env.platform.lock`, then repeat this step.
     If they still differ: ⏸.
6. `PYTHONPATH=src python3 src/rt/tests/run_all.py` must exit 0 with 193 passed. Check the exit code explicitly
   (do not pipe into `tail`).
7. `PYTHONPATH=src python3 -m unittest study3.tests.test_confirm` must print OK (9 tests).
8. Engine hash. This must print `CODE_HASH_OK`:
   ```
   PYTHONPATH=src python3 -c "import json,rt.run as r; h=json.loads(open('$PROJH/results/rt/s2/r1qwen32b_s2_base_r0of8.jsonl').readline()); print('CODE_HASH_OK' if r.code_sha256()==h['code_sha256'] else 'CODE_HASH_MISMATCH')"
   ```
9. `PYTHONPATH=src:source/EasyEdit python3 -c "import easyeditor"` must succeed. Otherwise ⏸.
10. Nothing from Study 3 may exist yet. This must print `fresh_deltas 0`, and both directories must be absent:
    ```
    python3 -c "import json,os; ids=[json.loads(l)['case_id'] for l in open('experiments/rt/pools/study2/manifest_r1qwen32b_fresh.jsonl') if l.strip()]; print('fresh_deltas', sum(os.path.exists(f'deltas/r1qwen32b/ROME/cf/{c}.pt') for c in ids))"
    ls -d results/rt/s3 results/rt/pool_s3 results/rt/deltas_logs/s3fresh results/rt/deltas_logs/s3ext
    ```
    (`ls` must report all four as missing.) Also `ls deltas/r1qwen32b/ROME/cf/cf_14142.pt deltas/r1qwen32b/ROME/cf/cf_15273.pt`
    must list both files (the two Study 2 32B edits the smoke in §5 uses).
11. Model files exist: `ls $M32/*.safetensors $MW/DeepSeek-R1-Distill-Qwen-14B/*.safetensors $MW/DeepSeek-R1-Distill-Qwen-1.5B/*.safetensors $MW/DeepSeek-R1-Distill-Qwen-7B/*.safetensors $MW/DeepSeek-R1-Distill-Llama-8B/*.safetensors | wc -l`
    must be greater than 0 for each path (check each path separately if the total looks short). Otherwise ⏸.
12. Report §1, then `touch $SHARE/S3G_CODE_OK`.

## §2 W2-fresh edits (fp32, 4 cards per process, world 2)

Environment for every edit step:
`export PYTHONPATH=src:source/EasyEdit WHYAAAI_DEVICE_MAP=balanced; unset WHYAAAI_DTYPE WHYAAAI_MODEL`

1. Smoke (rank 0 edits 2 cases; the limit applies before sharding):
   ```
   CUDA_VISIBLE_DEVICES=0,1,2,3 python3 -m rt.deltas run --config experiments/rt/deltas_s3_r1qwen32b_fresh.yaml --model-path $M32 --model-parallel --rank 0 --world 2 --device 0 --limit 4 > logs/s3/d_fresh_smoke.log 2>&1
   python3 -m rt.deltas summarize results/rt/deltas_logs/s3fresh/r1qwen32b_ROME_cf_r0of2.jsonl
   ```
   Pass: exit 0, `ok` 2, `editor_nan` 0, `max_rel_err` < 1e-4, `median_p_target_after` ≥ 0.9. Otherwise ⏸.
2. Full run (rank 0 resumes past its two smoke cases):
   ```
   CUDA_VISIBLE_DEVICES=0,1,2,3 nohup python3 -m rt.deltas run --config experiments/rt/deltas_s3_r1qwen32b_fresh.yaml --model-path $M32 --model-parallel --rank 0 --world 2 --device 0 > logs/s3/d_fresh_r0.log 2>&1 &
   sleep 90
   CUDA_VISIBLE_DEVICES=4,5,6,7 nohup python3 -m rt.deltas run --config experiments/rt/deltas_s3_r1qwen32b_fresh.yaml --model-path $M32 --model-parallel --rank 1 --world 2 --device 0 > logs/s3/d_fresh_r1.log 2>&1 &
   ```
   Wait until both exit (about 1 hour).
3. `python3 -m rt.deltas summarize results/rt/deltas_logs/s3fresh/r1qwen32b_ROME_cf_r*of2.jsonl > $POUT/summarize_S3G_fresh.json`
   Pass: `cases` 309, `ok` 309, `errors` empty, `editor_nan` 0, `max_rank` 1, `max_rel_err` < 1e-4.
   If not: re-run both ranks of step 2 once with `--retry-errors` added, then summarize again. Still failing: ⏸.
4. Report §2 with the summarize numbers, then `touch $SHARE/S3G_D_FRESH_DONE`.

## §3 Extension screens (B0, base models only) and the extension manifest

Environment: `export PYTHONPATH=src; unset WHYAAAI_DEVICE_MAP WHYAAAI_DTYPE WHYAAAI_MODEL`.
Each model uses the layout of its own Study 2 screen. One model (or one pair in step 2) at a time; start the next only
when the previous one's processes have all exited.

1. 32B, world 4, 2 cards per process:
   ```
   for r in 0 1 2 3; do CUDA_VISIBLE_DEVICES=$((2*r)),$((2*r+1)) WHYAAAI_MODEL=$M32 nohup python3 -m rt.pool screen --config experiments/rt/pool_screen_s3.yaml --model-tag r1qwen32b --rank $r --world 4 > logs/s3/screen_r1qwen32b_r$r.log 2>&1 & sleep 90; done; wait
   ```
2. 14B (world 4, cards 0–3) and 1.5B (world 4, cards 4–7), side by side:
   ```
   for r in 0 1 2 3; do CUDA_VISIBLE_DEVICES=$r WHYAAAI_MODEL=$MW/DeepSeek-R1-Distill-Qwen-14B nohup python3 -m rt.pool screen --config experiments/rt/pool_screen_s3.yaml --model-tag r1qwen14b --rank $r --world 4 > logs/s3/screen_r1qwen14b_r$r.log 2>&1 & sleep 30; CUDA_VISIBLE_DEVICES=$((r+4)) WHYAAAI_MODEL=$MW/DeepSeek-R1-Distill-Qwen-1.5B nohup python3 -m rt.pool screen --config experiments/rt/pool_screen_s3.yaml --model-tag r1qwen1_5b --rank $r --world 4 > logs/s3/screen_r1qwen1_5b_r$r.log 2>&1 & sleep 30; done; wait
   ```
3. 7B, world 8:
   ```
   for r in 0 1 2 3 4 5 6 7; do CUDA_VISIBLE_DEVICES=$r WHYAAAI_MODEL=$MW/DeepSeek-R1-Distill-Qwen-7B nohup python3 -m rt.pool screen --config experiments/rt/pool_screen_s3.yaml --model-tag r1qwen7b --rank $r --world 8 > logs/s3/screen_r1qwen7b_r$r.log 2>&1 & sleep 30; done; wait
   ```
4. Llama-8B, world 8:
   ```
   for r in 0 1 2 3 4 5 6 7; do CUDA_VISIBLE_DEVICES=$r WHYAAAI_MODEL=$MW/DeepSeek-R1-Distill-Llama-8B nohup python3 -m rt.pool screen --config experiments/rt/pool_screen_s3.yaml --model-tag r1llama8b --rank $r --world 8 > logs/s3/screen_r1llama8b_r$r.log 2>&1 & sleep 30; done; wait
   ```
   A screen process that crashes with out-of-memory: resume the same rank once with the same command. Otherwise rule 7.
5. Qualify each model and copy each printed `[pool] ...` line into the report:
   ```
   for t in r1qwen32b r1qwen14b r1qwen1_5b r1qwen7b r1llama8b; do python3 -m rt.pool qualify --config experiments/rt/pool_screen_s3.yaml --model-tag $t; done
   ```
   Every model must report 1600 candidates. If `qualify` says candidates have no screen row: resume the missing ranks
   of that model with the same screen command, then qualify again.
6. `python3 -m study3.ext_manifest` and copy its printed line into the report. If the well-known-and-qualified count is
   below 50: ⏸ (that would point to a screen problem).
7. Before any extension edit, record the manifest's identity:
   ```
   echo "$(sha256sum experiments/rt/pools/study3/manifest_r1qwen32b_ext.jsonl | cut -d' ' -f1) n=$(wc -l < experiments/rt/pools/study3/manifest_r1qwen32b_ext.jsonl) $(date -u +%FT%TZ)" > $SHARE/S3_EXT_MANIFEST.txt
   cp -a experiments/rt/pools/study3 $POUT/pools_study3_4090
   touch $SHARE/S3_EXT_MANIFEST_DONE
   ```
   Report §3 with the content of `S3_EXT_MANIFEST.txt`.

## §4 (reserved: none)

## §5 Generation smoke (two old Study 2 facts)

Environment for every generation step: `export PYTHONPATH=src; unset WHYAAAI_DEVICE_MAP WHYAAAI_DTYPE`.
```
CUDA_VISIBLE_DEVICES=0,1 WHYAAAI_MODEL=$M32 python3 -m rt.run --config experiments/rt/study3_smoke.yaml --conditions base,rome_N --rank 0 --world 1 --device auto --batch-size 16 --max-batch-tokens 40000 > logs/s3/gen_smoke.log 2>&1
```
Pass, all of:
- exit 0;
- `results/rt/s3smoke/` holds, for each of `base` and `rome_N`, 8 rows without `error` (2 facts × efficacy, para0 × B0, B3);
- read the 16 rows' `answer` fields: each is coherent English that answers the question (no repeated-token loops, no
  empty answers). Paste the B3 `answer` of both facts for `rome_N` into the report.

Any failure: ⏸.

## §6 W2-fresh generation (2 cards per process, world 4)

```
for r in 0 1 2 3; do CUDA_VISIBLE_DEVICES=$((2*r)),$((2*r+1)) WHYAAAI_MODEL=$M32 nohup python3 -m rt.run --config experiments/rt/study3_r1qwen32b_fresh.yaml --conditions base,rome_N --rank $r --world 4 --device auto --batch-size 16 --max-batch-tokens 40000 > logs/s3/gen_fresh_r$r.log 2>&1 & sleep 90; done
```
1. **Progress** (any time; counts only):
   `python3 -m study3.end_entry --stopped-at progress --out /tmp/s3_progress.json`
   Read only its printed line and, from the file, `n_complete_efficacy`, `valid_rows` and `error_rows` per world.
2. **Out-of-memory ladder.** When all four processes have exited, run the progress command. If fresh is not
   309/309 complete: run the same four commands again with `--max-batch-tokens 26000` (ranks with nothing left exit
   at once). After those exit, if still incomplete: again with `18000`. After those exit, if still incomplete: run each
   rank with remaining work, one at a time, on 4 cards (`CUDA_VISIBLE_DEVICES=0,1,2,3`, same `--rank $r --world 4`,
   `--max-batch-tokens 18000`). Still incomplete: ⏸.
3. **Pass:** `n_complete_efficacy` 309 for fresh, and each of the 8 `valid_rows` keys of fresh
   (`base|rome_N` × `efficacy|para0` × `B0|B3`) is 309. Report §6 with the printed line and the error-row counts, then
   `touch $SHARE/S3G_G_FRESH_DONE`.

## §7 W2-ext edits

As §2 steps 2–4 (environment of §2), with these changes:
- config `experiments/rt/deltas_s3_r1qwen32b_ext.yaml`, logs `logs/s3/d_ext_r$r.log`;
- no smoke (the same code and settings passed in §2);
- summarize `results/rt/deltas_logs/s3ext/r1qwen32b_ROME_cf_r*of2.jsonl` to `$POUT/summarize_S3G_ext.json`;
- pass: `cases` = `ok` = the line count of `experiments/rt/pools/study3/manifest_r1qwen32b_ext.jsonl`, other criteria as §2.

Then `touch $SHARE/S3G_D_EXT_DONE`.

## §8 W2-ext generation

As §6, with `experiments/rt/study3_r1qwen32b_ext.yaml` and logs `logs/s3/gen_ext_r$r.log`. Pass: the ext world's
`n_complete_efficacy` and each of its 8 `valid_rows` keys equal the ext manifest's line count. Then
`touch $SHARE/S3G_G_EXT_DONE`.

## §9 Close-out (when §6 and §8 have passed, or at 2026-12-31 23:59 UTC+8, whichever comes first)

```
python3 -m study3.end_entry --stopped-at "$(TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M') UTC+8"
mkdir -p $POUT/results/rt $POUT/deltas_logs
cp -a results/rt/s3 results/rt/s3smoke $POUT/results/rt/
cp -a results/rt/pool_s3 $POUT/results/rt/
cp -a results/rt/deltas_logs/s3fresh results/rt/deltas_logs/s3ext $POUT/deltas_logs/
cp experiments/rt/s3_end_of_generation.json $POUT/
cp -a logs/s3 $POUT/logs_s3
touch $SHARE/S3_END
```
Report §9 with the printed line of `end_entry`. Do **not** run `study3.confirm`. Then stop and wait for the next sheet.
