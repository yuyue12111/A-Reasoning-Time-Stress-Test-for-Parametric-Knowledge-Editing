# S3-H v2: leader rulings on the orchestrator audit (2026-10-13)

These amend the execution sheet `S3-H_sheet.md` and nothing else. No frozen rule changes: not the Study 3 addendum,
configs, manifests or analysis code, and not D9–D11. The audit is in `orch_audit_2026-10-13.json` (50 confirmed
defects in the original `orch_s3h.py`). The candidate fix is `patched_v2/{orch_s3h.py, watchdog.py}`.

1. **§2.9, EasyEdit.**
   - The check uses the lean import that rt.deltas itself uses:
     `PYTHONPATH=src:source/EasyEdit python3 -c "from rt.deltas import ensure_easyedit_importable as f; s=f(); import easyeditor; from easyeditor.models.rome import rome_main; print('EASYEDIT_OK', s)"`.
   - **On failure, halt (⏸).** Never skip to §8, because D10 puts Study 3 first.
2. **§3 and §5, edits.**
   - **Smoke size.** `--limit 8` at world 4, or `--limit 4` at world 2, so that rank 0 edits 2 cases. rt.deltas applies
     the limit before sharding. This carries out D9(a)'s 2-case smoke.
   - **OOM fallback.** It triggers on the log text, whatever the exit code.
   - **summarize.** It receives an unquoted, shell-expanded `r1qwen32b_ROME_cf_r*of<world>.jsonl`.
   - **Fallback world.** It is persisted in `$SHARE/S3_D_SMOKE_OK`, and §5 inherits it.
   - **Log prefixes.** `s3d_fresh` and `s3d_ext`.
3. **§6, the generation smoke on two old facts.**
   - It runs **before §3**, because it uses only old Study 2 deltas, so the review overlaps the edits.
   - Its rows are copied to `$POUTH`.
   - **§7 waits for `$SHARE/S3_SMOKE_GO`**, or halts on `S3_SMOKE_NOGO`. The marker may be touched by the executor
     agent after reading only the `results/rt/s3smoke/` rows for coherent English, or by the leader.
4. **§8.1, the 70B smoke.**
   - The code counts rows and then waits for `$SHARE/G3_SMOKE_GO`.
   - The executor agent reads the 2 smoke cases for coherent English. These are second-window outcomes, read by the
     executor and not by the leader, and the parent2 entry records that reading.
   - The known R1-Llama tokenizer risks apply: missing spaces and a missing BOS.
5. **§8.4.**
   - Replaced by `parent2_end_of_generation.txt`, `$POUTH/results/rt/s2_window2/` and `$SHARE/PARENT2_END`. The code
     never writes `parent_end_of_generation.txt`, `PARENT_END` or `$POUTH/results/rt/s2`.
   - Before §8 starts, a D11 guard checks that the entry has exactly 120 H100 lines and that every one of those shards
     still matches its hash.
   - Before the go, confirm that the platform's `$POUTH/parent_end_of_generation.txt` has sha256
     `b192435ae7c98b41638b7a49c3fed86d464aa53d9ff123e485dfbd2ebe583b62` (registry entry 10).
6. **Watchdog.** Deploy the patched `watchdog.py`.
   - It saves `zero_streak` (v3 never did, so it could never detect a hang).
   - `GRACE_S=1800`: no hang counting for 30 min after a (re)start.
   - It keeps a shared lock with the orchestrator, uses 'restarting'/'paused' states, sends TERM then KILL, and pauses
     rather than restarting onto a busy card.
7. **§4, screens.** A rank whose log lacks the final `{'screen': N}` line is re-run once, which resumes it. Qualify must
   exit with rc 0. Anything else halts.
8. **Hardware.**
   - The run halts unless the node has 8 × 'NVIDIA H100 80GB HBM3'.
   - Any other hardware needs a deviation (D9 and addendum §4) before `H100_NAME` is changed.
9. **Resume.**
   - `$SHARE` markers decide which phases are skipped.
   - A fresh start halts if any `S3_*` marker exists without `S3_CODE_OK`.
   - The leader handles the 2026-12-31 23:59 UTC+8 stop and close-out, if the worlds are incomplete by then.
10. **Pre-go checks, run on the restored GPU image.**
    - `python3 -m py_compile orch_s3h.py watchdog.py`.
    - Launch shape: `bash -c 'cd /tmp || exit 1; nohup env X=1 sleep 20 > /dev/null 2>&1 < /dev/null & echo NEWPID=$!'`
      run under `subprocess.run(capture_output=True)` returns in < 1 s, and `/proc/<pid>/comm` is `sleep`.
    - The lean-import command from item 1.
    - The sha256 of `parent_end_of_generation.txt`, as in item 5.
    - No `S3_*`, `PARENT2_END` or `*_SMOKE_GO` marker exists in `$SHARE`.

## v3 rulings (2026-10-13, after the second verification round)

Round 2 (`orch_verify_v2_2026-10-13.json`) confirmed 12 more defects in `patched_v2`, fixed in `patched_v3`.

- **(a) Summarize at world 2.** At world 2, summarize reads the r*of4 smoke logs first and then the r*of2 logs. Every
  manifest case must count as ok exactly once.
- **(b) The D11 guard after `PARENT2_STARTED`.**
  - Before G10' first appends, a full hash check of the 120 registered H100 shards runs, and `PARENT2_STARTED` records
    their registered byte sizes.
  - From then on, every registered shard must begin with exactly its registered bytes (append-only).
  - A flipped byte, a truncation, or a change without the marker halts the run. This replaces "a restart after G10'
    halts".
- **(c) `G3_SMOKE_GO`.** The file must contain the executor agent's reading note, for example
  `reader=executor-agent utc=… verdict=coherent`. An empty file does not count. The note is copied into `parent2_end_of_generation.txt`.
- **Pre-go marker list.** The check also covers `S3_SMOKE_DONE`, `S3_D_SMOKE_W4_OOM`, `G3_SMOKE_GO/NOGO`,
  `PARENT2_STARTED/END` and `$POUTH/g3_smoke_reading.txt`. None of them may exist.
- **Pre-committed rule, set before round 3 runs.**
  - `patched_v3` gets a third, independent verification with a real end-to-end sandbox built from the real code bundle.
  - **If round 3 confirms any new blocker, the orchestrator is dropped.** The executor agent then runs S3-H v2 by hand,
    step by step.
  - Confirmed majors can be patched once more.
