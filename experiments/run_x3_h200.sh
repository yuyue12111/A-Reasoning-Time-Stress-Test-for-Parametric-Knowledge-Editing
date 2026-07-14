#!/usr/bin/env bash
# X3/ROME-32B mp2 rescue: fresh N/T/C smoke -> split-safe full -> PS analysis.
# Modes: X3_PHASE=smoke|full|analyze|all.  For dual-node full, give disjoint
# four-rank wave bases via X3_BASES, e.g. "0 4 8 12" and "16 20 24 28".
# Server paths are sourced from experiments/x23_paths.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/x23_paths.sh"
cd "$PROJ"
PYTHON="${PYTHON:-python}"
export WHYAAAI_MODEL="$MODEL32"

export WHYAAAI_DTYPE=float32
export WHYAAAI_NO_BOS=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export WHYAAAI_DEVICE_MAP=balanced
mkdir -p results/logs

[[ -f "$WHYAAAI_MODEL/config.json" ]] || { echo "missing model config: $WHYAAAI_MODEL/config.json" >&2; exit 1; }
[[ -f data/counterfact.prefiltered.jsonl ]] || { echo "missing prefiltered CounterFact" >&2; exit 1; }
[[ -f data/placebo_donors_strong.json ]] || { echo "missing strong donor map" >&2; exit 1; }
GPU_PAIRS=("0,1" "2,3" "4,5" "6,7")
ALL_BASES=(0 4 8 12 16 20 24 28)
X3_PHASE="${X3_PHASE:-all}"
read -r -a FULL_BASES <<< "${X3_BASES:-${ALL_BASES[*]}}"

validate_bases() {
  local base allowed candidate
  [[ ${#FULL_BASES[@]} -gt 0 ]] || { echo "X3_BASES resolved to an empty list" >&2; exit 2; }
  for base in "${FULL_BASES[@]}"; do
    allowed=0
    for candidate in "${ALL_BASES[@]}"; do
      if [[ "$base" == "$candidate" ]]; then allowed=1; break; fi
    done
    [[ $allowed -eq 1 ]] || {
      echo "invalid X3 wave base '$base'; allowed: ${ALL_BASES[*]}" >&2; exit 2; }
  done
}

require_smoke_pass() {
  local audit="results/x3_smoke_audit.json"
  [[ -f "$audit" ]] || {
    echo "X3 full/analyze blocked: $audit is missing; run X3_PHASE=smoke once first" >&2; exit 2; }
  "$PYTHON" - "$audit" <<'PY'
import json, sys
path = sys.argv[1]
data = json.load(open(path))
if data.get("status") != "PASS":
    raise SystemExit(f"X3 smoke audit is not PASS: {data.get('status')!r}")
PY
}

run_smoke() {
  local cfg="$1" name="$2" pids=() slot
  for slot in $(seq 0 3); do
    CUDA_VISIBLE_DEVICES="${GPU_PAIRS[$slot]}" PYTHONPATH=source/EasyEdit "$PYTHON" src/run_pilot.py \
      --config "$cfg" --editor ROME --rank "$slot" --world 4 --device 0 \
      --limit 8 --tag-suffix _smoke >>"results/logs/${name}_r${slot}.log" 2>&1 &
    pids+=("$!")
  done
  for slot in "${pids[@]}"; do wait "$slot"; done
}

run_full() {
  local cfg="$1" name="$2" base slot rank pids
  for base in "${FULL_BASES[@]}"; do
    pids=()
    for slot in $(seq 0 3); do
      rank=$((base + slot))
      CUDA_VISIBLE_DEVICES="${GPU_PAIRS[$slot]}" PYTHONPATH=source/EasyEdit "$PYTHON" src/run_pilot.py \
        --config "$cfg" --editor ROME --rank "$rank" --world 32 --device 0 \
        >>"results/logs/${name}_r${rank}.log" 2>&1 &
      pids+=("$!")
    done
    for slot in "${pids[@]}"; do wait "$slot"; done
  done
}

NCONF=experiments/probe32b_freshn.yaml

run_smoke_phase() {
  echo "[X3] smoke: one shared fresh N/T/C mp2 gate; old single-GPU smoke is audit-only"
  run_smoke experiments/probe32b_freshn.yaml x3_Nfresh_mp2_smoke
  run_smoke experiments/probe32b_para_sup.yaml x3_T_mp2_smoke
  run_smoke experiments/probe32b_para_strongcomp.yaml x3_C_mp2_smoke
  "$PYTHON" src/validate_x_smoke.py x3 \
    --arm N=experiments/probe32b_freshn.yaml@_smoke \
    --arm T=experiments/probe32b_para_sup.yaml@_smoke \
    --arm C=experiments/probe32b_para_strongcomp.yaml@_smoke \
    --out results/x3_smoke_audit.json
  echo "$NCONF" > results/x3_n_config.txt
  echo "[X3] smoke PASS; full ranks may now be split across the two shared-disk instances"
}

run_full_phase() {
  validate_bases
  require_smoke_pass
  echo "[X3] full: logical world=32; this instance owns wave bases: ${FULL_BASES[*]}"
  run_full "$NCONF" x3_Nfresh_mp2_full
  run_full experiments/probe32b_para_sup.yaml x3_T_full
  run_full experiments/probe32b_para_strongcomp.yaml x3_C_full
  echo "[X3] assigned full waves complete: ${FULL_BASES[*]}"
}

run_analysis_phase() {
  require_smoke_pass
  "$PYTHON" src/validate_x_smoke.py x3 \
    --arm N="$NCONF" --arm T=experiments/probe32b_para_sup.yaml \
    --arm C=experiments/probe32b_para_strongcomp.yaml --out results/x3_full_audit.json

  "$PYTHON" src/score_pilot.py --config experiments/probe32b_para_sup.yaml --editor ROME --boot 10000 \
    | tee results/logs/x3_T_score.txt
  "$PYTHON" src/score_pilot.py --config experiments/probe32b_para_strongcomp.yaml --editor ROME --boot 10000 \
    | tee results/logs/x3_C_score.txt
  "$PYTHON" src/score_pilot.py --config "$NCONF" --editor ROME --boot 10000 \
    | tee results/logs/x3_N_score.txt
  "$PYTHON" src/cross_arm_para.py \
    --arm N="$NCONF" --arm T=experiments/probe32b_para_sup.yaml \
    --arm C=experiments/probe32b_para_strongcomp.yaml \
    --out results/x3_para_crossarm.json | tee results/logs/x3_crossarm.txt
  echo "[X3] complete; N=$NCONF"
}

case "$X3_PHASE" in
  smoke)
    run_smoke_phase
    ;;
  full)
    run_full_phase
    ;;
  analyze)
    run_analysis_phase
    ;;
  all)
    FULL_BASES=("${ALL_BASES[@]}")
    run_smoke_phase
    run_full_phase
    run_analysis_phase
    ;;
  *)
    echo "invalid X3_PHASE='$X3_PHASE'; expected smoke|full|analyze|all" >&2
    exit 2
    ;;
esac
