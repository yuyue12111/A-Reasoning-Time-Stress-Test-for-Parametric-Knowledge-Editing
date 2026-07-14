#!/usr/bin/env bash
# X1 Stage-0 on H200-A: seed-2 source audit -> mp2 smoke -> n=18 full -> judge prompt emit.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/x23_paths.sh"
cd "$PROJ"
PYTHON="${PYTHON:-python}"
CFG=experiments/x1_replay.yaml

export WHYAAAI_MODEL="$MODEL32"
export WHYAAAI_DTYPE=float32
export WHYAAAI_NO_BOS=1
export WHYAAAI_DEVICE_MAP=balanced
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONPATH=source/EasyEdit:src

mkdir -p results/logs results/x1
[[ -f "$WHYAAAI_MODEL/config.json" ]] || { echo "missing model: $WHYAAAI_MODEL" >&2; exit 1; }
for f in "$CFG" data/x1_replay_manifest.jsonl data/reverted_32b.jsonl \
         data/reverted_32b_f2b1.jsonl data/reverted_32b_samp.jsonl \
         experiments/probe32b_sample.yaml; do
  [[ -f "$f" ]] || { echo "missing X1 input: $f" >&2; exit 1; }
done

GPU_PAIRS=("0,1" "2,3" "4,5" "6,7")

run_four() {
  local suffix="$1" limit_arg="$2" name="$3" slot pids=()
  for slot in $(seq 0 3); do
    CUDA_VISIBLE_DEVICES="${GPU_PAIRS[$slot]}" "$PYTHON" src/x1_replay.py \
      --config "$CFG" --rank "$slot" --world 4 --device 0 \
      $limit_arg $suffix >>"results/logs/${name}_r${slot}.log" 2>&1 &
    pids+=("$!")
  done
  for slot in "${pids[@]}"; do wait "$slot"; done
}

echo "[X1] hard preflight: historical sample export must be exact seed-2 raw reconstruction"
"$PYTHON" src/verify_x1_sample_source.py \
  --config experiments/probe32b_sample.yaml \
  --historical data/reverted_32b_samp.jsonl \
  --seed 2 --out results/x1_sample_source_audit.json \
  | tee results/logs/x1_sample_source_audit.txt

"$PYTHON" src/x1_replay.py --config "$CFG" --rank 0 --world 4 --device 0 --dry-run \
  | tee results/logs/x1_replay_dryrun.txt

echo "[X1] mp2 smoke: frozen first 4 cases, one per pair worker"
run_four "--tag-suffix _smoke" "--limit 4" x1_replay_smoke
"$PYTHON" src/validate_x1_replay.py --config "$CFG" --suffix _smoke --expected-n 4 \
  --out results/x1_replay_smoke_audit.json

echo "[X1] full: all 18 frozen cases"
run_four "" "" x1_replay_full
"$PYTHON" src/validate_x1_replay.py --config "$CFG" --expected-n 18 \
  --out results/x1_replay_full_audit.json

"$PYTHON" src/score_x1_replay.py emit --config "$CFG" \
  --out-sample results/x1_replay_judge_sample.jsonl \
  --out-prompts results/x1_replay_judge_prompts.jsonl \
  | tee results/logs/x1_replay_rule_score.txt

echo "[X1] generation complete. Next: three independent answer-only judges over results/x1_replay_judge_prompts.jsonl"

