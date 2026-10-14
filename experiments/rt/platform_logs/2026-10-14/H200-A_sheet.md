# Execution sheet H200-A (8×H200 141 GB, offline): parent second window + exploratory content-vs-compute

Issued 2026-10-14. Rules: deviation D14, plan of record `paperwriting/revision/plan_2026-10-14.md` (registry 14).
Work is ordered by importance; the node runs it as waves W1 → W4, then the close-out.

**Role.** Execute only this sheet. Change nothing and suggest nothing. For anything the sheet does not cover, stop and
write ⏸. The node is offline and needs no credentials; if any step asks for a token or password, stop and report.

## §0 Rules that hold throughout

1. **Blinding.** Never open any answer, chain, hit or score of: `*_s2_rome_own_*`, `*_s2_rome_filler_*`,
   `*_s2_rome_swap_*`, `r1llama70b_s2_*`, the G10' shards (`*_s2_{rome_B0P,rome_B1,rome_a0.5,rome_a2,rome_a3,rome_samp,ike}_*`),
   `results/rt/s2x/`, `results/rt/s2retest/`, `results/rt/mech/`, and anything under `results/rt/s3*` (never touch those
   at all). You may look only at: row counts from `src/rtx/count_rows.py`, exit codes, GPU utilisation and memory,
   process lists, and log lines that show progress or a traceback. The one exception is the Llama-70B smoke in §3.
2. **Never delete, move or rewrite** any file under `$PROJH/results/rt/s2`, any delta, log or manifest. Shards are
   append-only; error rows stay.
3. **Before every GPU launch:** `pgrep -af "rt[.](run|mech)"` shows nothing on the target cards, and each target card
   has memory.used < 1 GB.
4. **Never install anything.** Never run `rt.study2`, `study3.*` or `rt.judge`.
5. **Persistence.** Work inside a tmux session (`tmux new -s h200`; reattach with `tmux attach -t h200`). Every GPU
   process is started with `nohup` and its own log in `logs/h200/`, so a lost terminal stops nothing.
6. **OOM ladder, per rank.** If one rank's process exits non-zero or its log shows CUDA out of memory, resume that rank
   alone with the identical command at the next rung (32B: 64000 → 40000 → 26000; 70B: 64000 → 34000 → 18000). After the
   last rung fails: ⏸ for that rank; the other ranks keep running.
7. **Hang rule.** No hang check before a process has logged its first chunk line. Afterwards, kill (that PID only) and
   resume once with the identical command only if its log has not advanced for 45 minutes and its cards read 0%
   utilisation in three checks over 10 minutes. Hangs again: ⏸.
8. **Any other crash** (a traceback that is not CUDA out-of-memory): resume once with the identical command. Crashes
   again: ⏸ for that item and continue with the next item of the sheet.
9. **Reports** go to `$POUT2/report_h200.md`; each block starts with `## <item> <✓|✗|⏸> <UTC time>`.

## Variables (export them in the tmux shell)

```
export PROJ200=/inspire/hdd/project/ai4education/public/why/why-arr-h200
export PROJH=/inspire/hdd/project/ai4education/public/why/why-arr-h100
export P4090=/inspire/hdd/project/ai4education/public/why/why-arr
export POUT2=/inspire/hdd/project/ai4education/public/why/platform_out_h200
export SHARE=/inspire/hdd/project/ai4education/public/why/xfer
export GP=/inspire/hdd/global_public/public_models
export M32=$GP/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B
export M70=$GP/deepseek-ai/DeepSeek-R1-Distill-Llama-70B
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PIP_NO_INDEX=1 PYTHONPATH=src
unset WHYAAAI_DTYPE WHYAAAI_DEVICE_MAP WHYAAAI_MODEL
```

## §1 Setup and checks (no GPU)

1. Shared storage is visible. Each must exist:
   `ls -d $PROJH/results/rt/s2 $P4090/deltas/r1qwen32b/ROME/cf $P4090/deltas/r1llama70b/ROME/cf $P4090/data/counterfact.jsonl $SHARE`
   and `ls $M32/*.safetensors | wc -l` and `ls $M70/*.safetensors | wc -l` are both > 0. Otherwise ⏸.
2. `$PROJ200` must not exist yet (otherwise ⏸). `mkdir -p $POUT2`.
3. Code. `sha256sum $SHARE/h200_code.bundle` must equal the value the leader gives with this sheet. Then
   `git clone -b claude/paper-review-understanding-8732e6 $SHARE/h200_code.bundle $PROJ200 && cd $PROJ200`;
   `git rev-parse --short HEAD` must equal the commit the leader gives. Every later command runs from `$PROJ200`.
4. Links (nothing is copied; outputs of the registered conditions land beside the registered H100 shards):
   ```
   mkdir -p results/rt logs/h200
   ln -s $PROJH/results/rt/s2 results/rt/s2
   ln -s $P4090/deltas deltas
   ln -s $P4090/data/counterfact.jsonl data/counterfact.jsonl
   sha256sum data/counterfact.jsonl
   ```
   The sha256 must be `b55d369a0462cec47006e70292b5d166f6202b2fa757b8bc6ca6ec141683c036`.
5. Software must be exactly torch `2.8.0a0+5228986c39.nv25.06`, transformers `5.5.4`, tokenizers `0.22.1`,
   accelerate `1.13.0`, numpy `1.26.4`:
   `python3 -c "import torch,transformers,tokenizers,accelerate,numpy;print(torch.__version__,transformers.__version__,tokenizers.__version__,accelerate.__version__,numpy.__version__)"`
   Any difference: ⏸ and report the printed line (nothing can be installed on this node).
6. `python3 src/rt/tests/run_all.py; echo EXIT=$?` must show 193 passed and `EXIT=0`.
7. Engine hash; must print `CODE_HASH_OK`:
   `python3 -c "import json,rt.run as r; h=json.loads(open('results/rt/s2/r1qwen32b_s2_base_r0of8.jsonl').readline()); print('CODE_HASH_OK' if r.code_sha256()==h['code_sha256'] else 'CODE_HASH_MISMATCH')"`
8. Registered shards intact; must print nothing and end with `EXIT=0`:
   `grep -E '^[0-9a-f]{64}  /' experiments/rt/platform_logs/2026-10-13/parent_end_of_generation.txt | sha256sum -c --quiet; echo EXIT=$?`
9. Record the G10' shards before any append; must exit 0:
   ```
   python3 src/rtx/prefix_check.py record experiments/rt/platform_logs/2026-10-13/parent_end_of_generation.txt $(for c in rome_B0P rome_B1 rome_a0.5 rome_a2 rome_a3 rome_samp ike; do for r in 2 3 4 5 6 7; do echo results/rt/s2/r1qwen32b_s2_${c}_r${r}of8.jsonl; done; done) > $POUT2/g10_prefix.tsv; echo EXIT=$?
   cp -a $PROJH/results/rt/s2 $POUT2/backup_s2_before_h200
   ```
10. Nothing of the second window exists yet; this must print nothing:
    `ls results/rt/s2/ | grep -E "_s2_rome_(own|filler|swap)_|^r1llama70b_s2_"; ls -d results/rt/s2x results/rt/s2retest results/rt/mech 2>/dev/null`
11. Dry runs (no model load) must each list the conditions with `pending` counts and no error:
    ```
    for r in 0 7; do WHYAAAI_MODEL=$M32 python3 -m rt.run --config experiments/rt/study2_r1qwen32b.yaml --stage 2 --rank $r --world 8 --dry-run; done
    for r in 2 7; do WHYAAAI_MODEL=$M32 python3 -m rt.run --config experiments/rt/study2_r1qwen32b.yaml --conditions rome_B0P,rome_B1,rome_a0.5,rome_a2,rome_a3,rome_samp,ike --rank $r --world 8 --dry-run; done
    WHYAAAI_MODEL=$M32 python3 -m rt.run --config experiments/rt/x_given_r1qwen32b.yaml --stage 2 --rank 0 --world 8 --dry-run
    WHYAAAI_MODEL=$M70 python3 -m rt.run --config experiments/rt/study2_r1llama70b_eff.yaml --conditions base,rome_N --rank 0 --world 8 --dry-run
    ```
    The G10' dry runs must show `done` > 0 for each condition (they resume the H100 shards). A
    `resume signature mismatch`: ⏸.
12. Report §1, then `touch $SHARE/H200_SETUP_OK`.

## §2 W1 — content vs compute at 32B (all 8 cards, one per process; about 1 hour)

Each card runs the registered G11' rank, then the exploratory transplant rank of the same number:
```
for r in 0 1 2 3 4 5 6 7; do CUDA_VISIBLE_DEVICES=$r WHYAAAI_MODEL=$M32 nohup bash -c "python3 -m rt.run --config experiments/rt/study2_r1qwen32b.yaml --stage 2 --rank $r --world 8 --device cuda --batch-size 16 --max-batch-tokens 64000; echo G11_EXIT=\$?; python3 -m rt.run --config experiments/rt/x_given_r1qwen32b.yaml --stage 2 --rank $r --world 8 --device cuda --batch-size 16 --max-batch-tokens 64000; echo S2X_EXIT=\$?" > logs/h200/w1_r$r.log 2>&1 & sleep 30; done
```
Pass, when all eight have exited (a rank that failed follows rule 6 with the same two commands):
```
for c in rome_own rome_filler rome_swap; do python3 src/rtx/count_rows.py "results/rt/s2/r1qwen32b_s2_${c}_r*of8.jsonl" --expect 100; done
for c in rome_given_base base_own base_filler base_given_edit; do python3 src/rtx/count_rows.py "results/rt/s2x/r1qwen32b_s2x_${c}_r*of8.jsonl" --expect 100; done
```
Every block must end in `ALL PASS`. Report the `ALL PASS` lines and error-row totals, then `touch $SHARE/H200_W1_DONE`.

## §3 W2 — Llama-70B, registered parent primary (2 cards per process)

1. **Smoke** (the only rows you may read):
   ```
   CUDA_VISIBLE_DEVICES=0,1 WHYAAAI_MODEL=$M70 python3 -m rt.run --config experiments/rt/study2_r1llama70b_eff.yaml --conditions base,rome_N --run-tag s2smoke --limit 2 --rank 0 --world 8 --batch-size 16 --max-batch-tokens 64000 > logs/h200/70b_smoke.log 2>&1; echo EXIT=$?
   python3 src/rtx/count_rows.py "results/rt/s2/r1llama70b_s2smoke_*_r0of8.jsonl" --expect 4
   ```
   Pass: exit 0, `ALL PASS`, and the 8 `answer` fields are coherent English with normal spaces between words (no
   words run together), not empty, no repeated-token loops. In the report, name the 2 case_ids and paste the B3
   `answer` of `rome_N` for both. Any failure: ⏸ (skip §3 and continue with §4).
2. **Full run.** Four card pairs; each pair runs rank p, then rank p+4:
   ```
   for p in 0 1 2 3; do CUDA_VISIBLE_DEVICES=$((2*p)),$((2*p+1)) WHYAAAI_MODEL=$M70 nohup bash -c "python3 -m rt.run --config experiments/rt/study2_r1llama70b_eff.yaml --conditions base,rome_N --rank $p --world 8 --batch-size 16 --max-batch-tokens 64000; echo R${p}_EXIT=\$?; python3 -m rt.run --config experiments/rt/study2_r1llama70b_eff.yaml --conditions base,rome_N --rank $((p+4)) --world 8 --batch-size 16 --max-batch-tokens 64000; echo R$((p+4))_EXIT=\$?" > logs/h200/w2_pair$p.log 2>&1 & sleep 60; done
   ```
3. Pass when all have exited (failed ranks follow rule 6 on a free pair):
   `for c in base rome_N; do python3 src/rtx/count_rows.py "results/rt/s2/r1llama70b_s2_${c}_r*of8.jsonl" --expect 100; done`
   Both `ALL PASS` (8 files each). Report, then `touch $SHARE/H200_W2_DONE`.

## §4 W3 — G10' remainder (cards 0–5) + exploratory noise floor (cards 6–7)

```
for r in 2 3 4 5 6 7; do CUDA_VISIBLE_DEVICES=$((r-2)) WHYAAAI_MODEL=$M32 nohup python3 -m rt.run --config experiments/rt/study2_r1qwen32b.yaml --conditions rome_B0P,rome_B1,rome_a0.5,rome_a2,rome_a3,rome_samp,ike --rank $r --world 8 --device cuda --batch-size 16 --max-batch-tokens 64000 > logs/h200/w3_g10_r$r.log 2>&1 & sleep 30; done
for r in 0 1; do CUDA_VISIBLE_DEVICES=$((6+r)) WHYAAAI_MODEL=$M32 nohup python3 -m rt.run --config experiments/rt/x_retest_r1qwen32b.yaml --rank $r --world 2 --device cuda --batch-size 16 --max-batch-tokens 64000 > logs/h200/w3_retest_r$r.log 2>&1 & sleep 30; done
```
Pass when all have exited (expected valid rows per file: rome_B0P 100, rome_B1 100, rome_a0.5 50, rome_a2 100,
rome_a3 100, rome_samp 400, ike 100; ranks 0 and 1 were already complete on the H100):
```
for c in rome_B0P:100 rome_B1:100 rome_a0.5:50 rome_a2:100 rome_a3:100 rome_samp:400 ike:100; do python3 src/rtx/count_rows.py "results/rt/s2/r1qwen32b_s2_${c%%:*}_r*of8.jsonl" --expect ${c##*:}; done
for c in base rome_N; do python3 src/rtx/count_rows.py "results/rt/s2retest/r1qwen32b_s2retest_${c}_r*of2.jsonl" --expect 400; done
```
All `ALL PASS`. Report, then `touch $SHARE/H200_W3_DONE`.

## §5 W4 — exploratory mechanism probe (1–4 cards; start on any card that is idle once W3 is running)

1. Smoke: `CUDA_VISIBLE_DEVICES=<idle card> python3 -m rt.mech run --config experiments/rt/x_mech_s2_r1qwen32b.yaml --model $M32 --limit 3 --out "results/rt/mech/smoke_s2_r{rank}of{world}.jsonl" > logs/h200/mech_smoke.log 2>&1; echo EXIT=$?`
   If it fails: report the last 30 log lines, skip §5 (no ⏸), and go on.
2. Full, world 4 on four idle cards (or world 1 on one card if fewer are idle):
   `for r in 0 1 2 3; do CUDA_VISIBLE_DEVICES=<card_r> nohup python3 -m rt.mech run --config experiments/rt/x_mech_s2_r1qwen32b.yaml --model $M32 --rank $r --world 4 > logs/h200/mech_r$r.log 2>&1 & sleep 30; done`
   Report `wc -l results/rt/mech/s2_r1qwen32b_ROME_B3_r*of*.jsonl`, then `touch $SHARE/H200_W4_DONE`.

## §6 Close-out (when §2, §3 and §4 have passed, or at 2026-12-31 23:59 UTC+8)

```
python3 src/rtx/prefix_check.py verify experiments/rt/platform_logs/2026-10-13/parent_end_of_generation.txt $POUT2/g10_prefix.tsv; echo EXIT=$?
sha256sum $PROJH/results/rt/s2/*.jsonl > $POUT2/parent2_end_of_generation.txt
echo "# written $(date -u +%FT%TZ) on the H200 node; second window per D14; 70B smoke read by the executor: <the 2 case_ids>" >> $POUT2/parent2_end_of_generation.txt
cp -a $PROJH/results/rt/s2 $POUT2/results_rt_s2_after
cp -a results/rt/s2x results/rt/s2retest $POUT2/
[ -d results/rt/mech ] && cp -a results/rt/mech $POUT2/
cp -a logs/h200 $POUT2/logs_h200
touch $SHARE/PARENT2_END
```
The prefix check must print only `OK` lines and `EXIT=0`; otherwise ⏸ before writing the end entry. Report §6 with
`wc -l $POUT2/parent2_end_of_generation.txt`, then stop and wait for the next sheet.
