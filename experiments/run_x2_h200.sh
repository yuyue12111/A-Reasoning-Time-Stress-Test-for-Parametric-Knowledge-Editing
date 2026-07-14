#!/usr/bin/env bash
# X2/MEMIT-14B: smoke -> provenance decision -> T/C/(conditional fresh N) full -> analysis.
# Server paths are sourced from experiments/x23_paths.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/x23_paths.sh"
cd "$PROJ"
PYTHON="${PYTHON:-python}"
export WHYAAAI_MODEL="$MODEL14"
export WHYAAAI_WIKI_PARQUET="$WIKI_EN"

export WHYAAAI_DTYPE=float32
export WHYAAAI_NO_BOS=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
unset WHYAAAI_DEVICE_MAP || true
mkdir -p results/logs

[[ -f "$WHYAAAI_MODEL/config.json" ]] || { echo "missing model config: $WHYAAAI_MODEL/config.json" >&2; exit 1; }
[[ -f data/counterfact.prefiltered.jsonl ]] || { echo "missing prefiltered CounterFact" >&2; exit 1; }
[[ -f data/placebo_donors_strong.json ]] || { echo "missing strong donor map" >&2; exit 1; }
[[ $(find data/stats_r1qwen14b -type f -name '*.npz' 2>/dev/null | wc -l) -ge 3 ]] || {
  echo "X2 blocked: stats_r1qwen14b has fewer than three cached npz files" >&2; exit 1; }
compgen -G 'results/probe/r1qwen14b_MEMIT_cf200memit_r*.jsonl' >/dev/null || {
  echo "X2 blocked: existing MEMIT-14B N shards not found" >&2; exit 1; }

run_smoke() {
  local cfg="$1" name="$2" pids=() d
  for d in $(seq 0 7); do
    PYTHONPATH=source/EasyEdit "$PYTHON" src/run_pilot.py \
      --config "$cfg" --editor MEMIT --rank "$d" --world 8 --device "$d" \
      --limit 8 --tag-suffix _smoke >>"results/logs/${name}_r${d}.log" 2>&1 &
    pids+=("$!")
  done
  for d in "${pids[@]}"; do wait "$d"; done
}

run_full() {
  local cfg="$1" name="$2" base d rank pids
  for base in 0 8 16 24; do
    pids=()
    for d in $(seq 0 7); do
      rank=$((base + d))
      PYTHONPATH=source/EasyEdit "$PYTHON" src/run_pilot.py \
        --config "$cfg" --editor MEMIT --rank "$rank" --world 32 --device "$d" \
        >>"results/logs/${name}_r${rank}.log" 2>&1 &
      pids+=("$!")
    done
    for d in "${pids[@]}"; do wait "$d"; done
  done
}

if [[ "${X23_REUSE_TC_SMOKE:-0}" == "1" ]]; then
  echo "[X2] reusing existing T/C smoke shards; validator will verify completeness and exact hashes"
else
  run_smoke experiments/memit14b_sup.yaml x2_T_smoke
  run_smoke experiments/memit14b_strongcomp.yaml x2_C_smoke
fi

set +e
"$PYTHON" src/validate_x_smoke.py x2 \
  --arm N=experiments/memit14b.yaml \
  --arm T=experiments/memit14b_sup.yaml@_smoke \
  --arm C=experiments/memit14b_strongcomp.yaml@_smoke \
  --log 'results/logs/x2_T_smoke_r*.log' --log 'results/logs/x2_C_smoke_r*.log' \
  --out results/x2_smoke_audit.json
rc=$?
set -e

if [[ $rc -eq 2 ]]; then
  echo "[X2] legacy N lacks strict parity; running preregistered fresh-N smoke"
  run_smoke experiments/memit14b_freshn.yaml x2_Nfresh_smoke
  "$PYTHON" src/validate_x_smoke.py x2 \
    --arm N=experiments/memit14b_freshn.yaml@_smoke \
    --arm T=experiments/memit14b_sup.yaml@_smoke \
    --arm C=experiments/memit14b_strongcomp.yaml@_smoke \
    --log 'results/logs/x2_T_smoke_r*.log' --log 'results/logs/x2_C_smoke_r*.log' \
    --out results/x2_smoke_audit_freshn.json
  NCONF=experiments/memit14b_freshn.yaml
elif [[ $rc -eq 0 ]]; then
  NCONF=experiments/memit14b.yaml
else
  echo "[X2] smoke failed; full run not started" >&2
  exit "$rc"
fi
echo "$NCONF" > results/x2_n_config.txt

# Protect the main T-C endpoint first; run conditional fresh N afterward.
run_full experiments/memit14b_sup.yaml x2_T_full
run_full experiments/memit14b_strongcomp.yaml x2_C_full
if [[ "$NCONF" == *freshn* ]]; then
  run_full "$NCONF" x2_Nfresh_full
fi

"$PYTHON" src/validate_x_smoke.py x2 \
  --arm N="$NCONF" --arm T=experiments/memit14b_sup.yaml --arm C=experiments/memit14b_strongcomp.yaml \
  --log 'results/logs/x2_T_full_r*.log' --log 'results/logs/x2_C_full_r*.log' \
  --out results/x2_full_audit.json

"$PYTHON" src/score_pilot.py --config experiments/memit14b_sup.yaml --editor MEMIT --boot 10000 \
  | tee results/logs/x2_T_score.txt
"$PYTHON" src/score_pilot.py --config experiments/memit14b_strongcomp.yaml --editor MEMIT --boot 10000 \
  | tee results/logs/x2_C_score.txt
"$PYTHON" src/score_pilot.py --config "$NCONF" --editor MEMIT --boot 10000 \
  | tee results/logs/x2_N_score.txt
"$PYTHON" src/cross_arm.py --budget B3 --editor MEMIT \
  --arm N="$NCONF" --arm T=experiments/memit14b_sup.yaml \
  --arm C=experiments/memit14b_strongcomp.yaml --out results/x2_memit14b_crossarm.json \
  | tee results/logs/x2_crossarm.txt

echo "[X2] complete; N=$NCONF"
