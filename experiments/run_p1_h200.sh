#!/usr/bin/env bash
# P1 node×capacity crossover runner. Run one topology per node, then swap nodes.
# Required: P1_NODE=A|B P1_TOPOLOGY=single|mp2. Optional P1_PHASE=smoke|full|analyze|all.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/x23_paths.sh"
cd "$PROJ"

PYTHON="${PYTHON:-python}"
P1_NODE="${P1_NODE:?set P1_NODE=A or B}"
P1_TOPOLOGY="${P1_TOPOLOGY:?set P1_TOPOLOGY=single or mp2}"
P1_PHASE="${P1_PHASE:-all}"
[[ "$P1_NODE" == A || "$P1_NODE" == B ]] || { echo "P1_NODE must be A or B" >&2; exit 2; }
[[ "$P1_TOPOLOGY" == single || "$P1_TOPOLOGY" == mp2 ]] || {
  echo "P1_TOPOLOGY must be single or mp2" >&2; exit 2; }

export WHYAAAI_MODEL="$MODEL32"
export WHYAAAI_DTYPE=float32
export WHYAAAI_NO_BOS=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
mkdir -p results/p1 results/logs

if [[ "$P1_TOPOLOGY" == single ]]; then
  CFG=experiments/p1_reload_single.yaml
  WORLD=8
  unset WHYAAAI_DEVICE_MAP || true
else
  CFG=experiments/p1_reload_mp2.yaml
  WORLD=4
  export WHYAAAI_DEVICE_MAP=balanced
fi

run_workers() {
  local suffix="$1" limit="${2:-}" workers="$3" slot rank dev pids=()
  for ((slot=0; slot<workers; slot++)); do
    rank=$slot
    if [[ "$P1_TOPOLOGY" == single ]]; then
      dev="$slot"
    else
      dev="$((2*slot)),$((2*slot+1))"
    fi
    cmd=("$PYTHON" src/run_pilot.py --config "$CFG" --editor ROME
         --rank "$rank" --world "$workers" --device 0 --tag-suffix "$suffix")
    if [[ -n "$limit" ]]; then cmd+=(--limit "$limit"); fi
    CUDA_VISIBLE_DEVICES="$dev" PYTHONPATH=source/EasyEdit "${cmd[@]}" \
      >>"results/logs/p1_${P1_NODE}_${P1_TOPOLOGY}${suffix}_r${rank}.log" 2>&1 &
    pids+=("$!")
  done
  for rank in "${pids[@]}"; do wait "$rank"; done
}

run_smoke() {
  # Two cases: cf_140(main) and cf_18471(F2). Use only the GPUs needed by those two workers.
  run_workers "_node${P1_NODE}_${P1_TOPOLOGY}_smoke" 2 2
  "$PYTHON" src/score_p1_reload.py --smoke \
    --node "$P1_NODE" --topology "$P1_TOPOLOGY" \
    --out "results/p1_smoke_${P1_NODE}_${P1_TOPOLOGY}.json"
}

run_full() {
  local rep
  for rep in 0 1 2; do
    run_workers "_node${P1_NODE}_${P1_TOPOLOGY}_rep${rep}" "" "$WORLD"
  done
}

run_analysis() {
  "$PYTHON" src/score_p1_reload.py --out results/p1_reload_summary_v2.json \
    | tee results/logs/p1_reload_summary_v2.txt
}

case "$P1_PHASE" in
  smoke) run_smoke ;;
  full) run_full ;;
  analyze) run_analysis ;;
  all) run_smoke; run_full ;;
  *) echo "P1_PHASE must be smoke|full|analyze|all" >&2; exit 2 ;;
esac
