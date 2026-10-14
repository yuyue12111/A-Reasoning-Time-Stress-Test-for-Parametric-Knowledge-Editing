# S3-G amendment 2 (2026-10-14, leader; deviation D13)

Applies from wherever you are now. Everything in S3-G and amendment 1 stays in force unless changed here.

## Part A: order until the pause

1. Finish §2 (W2-fresh edits) and §3 (screens, qualify, ext manifest, `S3_EXT_MANIFEST.txt`) as written.
2. **Then run §7 (W2-ext edits) immediately**, with the §2 environment and §7's pass criteria; `touch $SHARE/S3G_D_EXT_DONE`.
3. Copy all Study 3 deltas and delta logs to the output area, with a checksum list:
   ```
   mkdir -p $POUT/backup_s3_deltas/pt
   python3 -c "import json,shutil; ids=[json.loads(l)['case_id'] for f in ('experiments/rt/pools/study2/manifest_r1qwen32b_fresh.jsonl','experiments/rt/pools/study3/manifest_r1qwen32b_ext.jsonl') for l in open(f) if l.strip()]; [shutil.copy2(f'deltas/r1qwen32b/ROME/cf/{c}.pt', '$POUT/backup_s3_deltas/pt/') for c in ids]; print('copied', len(ids))"
   cp -a results/rt/deltas_logs/s3fresh results/rt/deltas_logs/s3ext $POUT/backup_s3_deltas/
   cd $POUT/backup_s3_deltas && sha256sum pt/*.pt > pt.sha256 && cd $PROJ
   ```
   Report the `copied` count (must equal 309 + the ext manifest's line count) and `wc -l $POUT/backup_s3_deltas/pt.sha256`.
4. **Then stop generation work. ⏸ GENERATION PAUSE.** Do not start §5, §6 or §8 until you receive **S3-G amendment 3**
   from the leader. It will name a commit; before any generation you will verify that commit is on origin and re-run §1
   steps 4–8. If the pause is still in force at **2026-10-17 23:59 UTC+8**, report ⏸ and wait for the leader's instruction.
   (If §6 had already started before you received this amendment, do not stop it: let §6 finish, then do steps 2–3 and
   pause before §8.)

## Part B: backlog during the pause (no Study 3 outcome is produced or read)

Do these in order while paused. They touch only seen Study 2 data, base models and downloads.

### B1. Node census (report the raw output)
```
nproc; free -g; df -h $PROJ $MW /inspire/hdd/global_public 2>/dev/null
ls /inspire/dataset/Wikipedia/20231101/20231101.en 2>&1 | head -3
ls -la data/stats_r1qwen14b 2>&1 | head -20
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv
```

### B2. Downloads (network, no token)
First check `df -h $MW` shows at least 150 GB free; otherwise ⏸. Run each in the background with its own log. If a repo
answers 401/403 or asks you to log in or accept terms, stop that download, do not supply any credential, and report it.
```
nohup python3 -c "from huggingface_hub import snapshot_download as s; s('mistralai/Mistral-Small-3.1-24B-Instruct-2503', local_dir='$MW/Mistral-Small-3.1-24B-Instruct-2503', ignore_patterns=['consolidated.safetensors'])" > logs/s3/dl_mistral.log 2>&1 &
nohup python3 -c "from huggingface_hub import snapshot_download as s; s('microsoft/phi-4', local_dir='$MW/phi-4')" > logs/s3/dl_phi4.log 2>&1 &
nohup python3 -c "from huggingface_hub import snapshot_download as s; s('Qwen/Qwen3-14B', local_dir='$MW/Qwen3-14B')" > logs/s3/dl_qwen3_14b.log 2>&1 &
```
When each finishes, report `ls $MW/<dir>/*.safetensors | wc -l` and `du -sh $MW/<dir>`. Do not install any package.

### B3. Judge run on seen Study 2 data (exploratory; GPU)
Environment: `export PYTHONPATH=src; unset WHYAAAI_DEVICE_MAP WHYAAAI_DTYPE WHYAAAI_MODEL`.
Only these shards may be given to the judge. Any other shard, in particular `*_s2_ike_*`, `*_s2_rome_B0P_*`,
`*_s2_rome_B1_*`, `*_s2_rome_a0.5_*`, `*_s2_rome_a2_*`, `*_s2_rome_a3_*`, `*_s2_rome_samp_*` and anything under
`results/rt/s3*`, must never be passed to `rt.judge` in any subcommand.
```
R=(--rows "$PROJH/results/rt/s2/r1qwen32b_s2_base_r*of8.jsonl" --rows "$PROJH/results/rt/s2/r1qwen32b_s2_rome_N_r*of8.jsonl"
   --rows "$PROJH/results/rt/s2/r1qwen32b_s2_rome_T_r*of8.jsonl" --rows "$PROJH/results/rt/s2/r1qwen32b_s2_rome_D_r*of8.jsonl"
   --rows "$PROJH/results/rt/s2/r1qwen32b_s2_rome_P_r*of8.jsonl" --rows "$PROJH/results/rt/s2/r1qwen32b_s2_rome_C_r*of8.jsonl"
   --rows "$PROJH/results/rt/s2/r1qwen32b_s2h2b_base_r*of8.jsonl" --rows "$PROJH/results/rt/s2/r1qwen32b_s2h2b_rome_N_r*of8.jsonl"
   --rows "results/rt/s2/r1qwen14b_s2_base_r*of8.jsonl" --rows "results/rt/s2/r1qwen14b_s2_rome_N_r*of8.jsonl"
   --rows "results/rt/s2/r1llama8b_s2_base_r*of8.jsonl" --rows "results/rt/s2/r1llama8b_s2_rome_N_r*of8.jsonl"
   --rows "results/rt/s2/r1qwen7b_s2_base_r*of8.jsonl" --rows "results/rt/s2/r1qwen7b_s2_rome_N_r*of8.jsonl"
   --rows "results/rt/s2/r1qwen1_5b_s2_base_r*of8.jsonl" --rows "results/rt/s2/r1qwen1_5b_s2_rome_N_r*of8.jsonl")
MI=$MW/Mistral-Small-3.1-24B-Instruct-2503; PH=$MW/phi-4; mkdir -p results/judge/mistral-small-3.1 results/judge/phi-4
```
(If any of these globs matches nothing on this node, report which one and ⏸.)

1. `show` (CPU): `python3 -m rt.judge show "${R[@]}" --model $MI --n 2` and the same with `$PH`. Report the printed
   `system_mode` and `tokens_p50`, and whether the Mistral rendering contains a date (it must not).
2. `selfcheck`: `CUDA_VISIBLE_DEVICES=0,1 python3 -m rt.judge selfcheck "${R[@]}" --model $MI --n 256` and
   `CUDA_VISIBLE_DEVICES=2 python3 -m rt.judge selfcheck "${R[@]}" --model $PH --n 256`.
   Pass: `letter_mass_p10` ≥ 0.9 and `label_flips_batch_vs_single` ≤ 2. If one fails, rerun its selfcheck once with
   `--assistant-prefix "Answer:"`; if it passes then, that prefix is used for all of that judge's runs. If it still fails,
   or the model does not load: ⏸ for that judge only, and continue with the other.
3. `run` (only judges that passed step 2), with `--orders 2`, one output file per shard:
   ```
   for k in 0 1 2; do CUDA_VISIBLE_DEVICES=$((2*k)),$((2*k+1)) nohup python3 -m rt.judge run "${R[@]}" --model $MI --orders 2 --shard $k/3 --out results/judge/mistral-small-3.1/s2allow_s$k.jsonl > logs/s3/judge_mi_s$k.log 2>&1 & sleep 120; done
   for k in 0 1; do CUDA_VISIBLE_DEVICES=$((6+k)) nohup python3 -m rt.judge run "${R[@]}" --model $PH --orders 2 --shard $k/2 --out results/judge/phi-4/s2allow_s$k.jsonl > logs/s3/judge_ph_s$k.log 2>&1 & sleep 60; done
   ```
   Add `--assistant-prefix "Answer:"` only for a judge that needed it in step 2. A run that dies: rerun the identical
   command (it resumes). Never run `rt.judge score` and never print verdicts.
4. When all runs have exited: `wc -l results/judge/*/s2allow_s*.jsonl`, then
   `mkdir -p $POUT/judge && cp -a results/judge/mistral-small-3.1 results/judge/phi-4 $POUT/judge/`. Report, then wait at ⏸.

## Part C: rules that change for §6 and §8 when they run (after amendment 3)

- **Start rung** 26000 for every rank (replaces 40000 in the §6/§8 commands).
- **Per-rank ladder** (replaces §6 step 2): when one rank's process exits non-zero or its log shows CUDA out of memory,
  resume that rank alone (same cards, same `--rank $r --world 4`) at 18000. If it fails again, resume it on 4 idle cards
  at 18000. If it fails again: ⏸. Other ranks keep running.
- **Hang rule** (replaces §0 rule 6): no hang check before a process has logged its first chunk; afterwards, kill and
  resume once only if its log has not advanced for 45 minutes and its cards read 0% in three checks over 10 minutes.
