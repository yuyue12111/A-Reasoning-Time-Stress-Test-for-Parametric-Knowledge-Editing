#!/usr/bin/env bash
# CPU-only statistical closeout.  No model loading and no GPU process is started.
# Run on the shared-disk CPU instance after uploading the changed src/experiments files.
set -euo pipefail

export PROJ="${PROJ:-/inspire/hdd/project/ai4education/ky26140/why/why-aaai27}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
MODE="${1:-full}"
if [[ "$MODE" != "full" && "$MODE" != "--b15-only" ]]; then
  echo "usage: bash experiments/run_cpu_closeout.sh [--b15-only]" >&2
  exit 2
fi
cd "$PROJ"

edited_globs=(
  'results/probe/r1qwen1_5b_ROME_cf200_r*.jsonl'
  'results/pilot/r1qwen7b_ROME_cf200_r*of8.jsonl'
  'results/probe/r1qwen14b_ROME_cf200_r*.jsonl'
  'results/probe/r1qwen32b_ROME_cf200_r*.jsonl'
  'results/probe/r1llama8b_ROME_cf200c2_r*.jsonl'
  'results/probe/r1llama70b_ROME_cf100_r*.jsonl'
)

# Preserve the historical five-checkpoint B15 estimand.  Qwen-7B BASE is deliberately
# not added post hoc; it can be audited separately before any six-checkpoint rerun.
base_globs=(
  'results/probe/r1qwen1_5b_BASE_cf200_r*.jsonl'
  'results/probe/r1qwen14b_BASE_cf200_r*.jsonl'
  'results/probe/r1qwen32b_BASE_cf200_r*.jsonl'
  'results/probe/r1llama8b_BASE_cf200c2_r*.jsonl'
  'results/probe/r1llama70b_BASE_cf100_r*.jsonl'
)

if [[ "$MODE" == "--b15-only" ]]; then
  required_globs=("${edited_globs[@]}" "${base_globs[@]}")
else
  required_globs=(
    "${edited_globs[@]}"
    "${base_globs[@]}"
    'results/probe/r1qwen32b_ROME_cf200samp_r*.jsonl'
    'results/probe/r1qwen14b_MEMIT_cf200memit_freshn_r*.jsonl'
    'results/probe/r1qwen14b_MEMIT_cf200memit_sup_r*.jsonl'
    'results/probe/r1qwen14b_MEMIT_cf200memit_strong_r*.jsonl'
    'results/probe/r1qwen32b_ROME_cf200para_freshn_mp2_r*.jsonl'
    'results/probe/r1qwen32b_ROME_cf200para_sup_mp2_r*.jsonl'
    'results/probe/r1qwen32b_ROME_cf200para_strong_mp2_r*.jsonl'
  )
fi

missing=0
for pattern in "${required_globs[@]}"; do
  if ! compgen -G "$pattern" >/dev/null; then
    echo "[CPU-CLOSEOUT][MISSING] $pattern" >&2
    missing=1
  fi
done
if [[ "$missing" -ne 0 ]]; then
  echo '[CPU-CLOSEOUT] required shared-disk raw inputs are incomplete; nothing was recomputed.' >&2
  exit 2
fi

preserve_b15_b3_sensitivity() {
  local current='results/b15_caseblock.json'
  local archived='results/b15_caseblock_B3_sensitivity.json'
  if [[ -f "$current" ]] && "$PYTHON_BIN" -c \
      'import json,sys; d=json.load(open(sys.argv[1])); p=d.get("_provenance",{}).get("base",{}).get("duplicate_world_audit",{}).get("selected",{}).get("budget"); sys.exit(0 if p=="B3" else 1)' \
      "$current"; then
    cp -p "$current" "$archived"
    echo "[CPU-CLOSEOUT] preserved prior B3 sensitivity: $archived"
  fi
}

if [[ "$MODE" == "--b15-only" ]]; then
  "$PYTHON_BIN" src/test_b15_regress.py
  "$PYTHON_BIN" src/test_validate_cpu_closeout.py
  b15_args=()
  for pattern in "${edited_globs[@]}"; do
    b15_args+=(--glob "$pattern")
  done
  for pattern in "${base_globs[@]}"; do
    b15_args+=(--base-glob "$pattern")
  done
  preserve_b15_b3_sensitivity
  "$PYTHON_BIN" src/b15_regress.py \
    "${b15_args[@]}" \
    --base-budget B0 \
    --boot 10000 \
    --out results/b15_caseblock.json
  "$PYTHON_BIN" src/validate_cpu_closeout.py \
    --percase results/percase_caseblock.json \
    --b15 results/b15_caseblock.json \
    --cap3 results/cap3_caseblock.json \
    --f3 results/f3_sampling_recalc.json \
    --x2 results/x2_memit14b_crossarm_v2.json \
    --x3 results/x3_para_crossarm_v2.json \
    --p0 results/p0_downstream_crosswalk.json \
    --out results/cpu_closeout_audit.json
  sha256sum results/b15_caseblock.json results/cpu_closeout_audit.json
  exit 0
fi

"$PYTHON_BIN" src/test_percase_emergence.py
"$PYTHON_BIN" src/test_b15_regress.py
"$PYTHON_BIN" src/test_f3_sampling_recalc.py
"$PYTHON_BIN" src/test_cross_arm_para.py
"$PYTHON_BIN" src/test_cross_arm.py
"$PYTHON_BIN" src/test_p0_finalize_routes.py
"$PYTHON_BIN" src/test_chain_classify.py

# P0 downstream is optional here: the server may intentionally retain only the final
# crosswalk JSON, while its local-only A3/WA source archive is absent.  Do not let that
# block the six required CPU analyses.  If every dependency is present, test/recompute it.
p0_dependencies=(
  'results/a3/labels_7b.jsonl'
  'results/a3/labels_14b.jsonl'
  'results/a3/labels_32b.jsonl'
  'results/necessity.json'
  'data/x1_replay_manifest.jsonl'
  'results/x1_replay_gate.json'
  'results/wa/edited_r0of8.jsonl'
  'results/wa/edited_r1of8.jsonl'
  'results/wa/edited_r2of8.jsonl'
  'results/wa/edited_r3of8.jsonl'
  'results/wa/edited_r4of8.jsonl'
  'results/wa/edited_r5of8.jsonl'
  'results/wa/edited_r6of8.jsonl'
  'results/wa/edited_r7of8.jsonl'
)
p0_ready=1
for path in "${p0_dependencies[@]}"; do
  if [[ ! -f "$path" ]]; then
    p0_ready=0
  fi
done
if [[ "$p0_ready" -eq 1 ]]; then
  "$PYTHON_BIN" src/test_p0_downstream_crosswalk.py
else
  echo '[CPU-CLOSEOUT][SKIP-OPTIONAL] P0 downstream test: A3/WA source archive is incomplete on this server.' >&2
fi

percase_args=()
for pattern in "${edited_globs[@]}"; do
  percase_args+=(--glob "$pattern")
done
"$PYTHON_BIN" src/percase_emergence.py \
  "${percase_args[@]}" \
  --boot 10000 \
  --seed 42 \
  --out results/percase_caseblock.json

b15_args=()
for pattern in "${edited_globs[@]}"; do
  b15_args+=(--glob "$pattern")
done
for pattern in "${base_globs[@]}"; do
  b15_args+=(--base-glob "$pattern")
done
preserve_b15_b3_sensitivity
"$PYTHON_BIN" src/b15_regress.py \
  "${b15_args[@]}" \
  --base-budget B0 \
  --boot 10000 \
  --out results/b15_caseblock.json

"$PYTHON_BIN" src/cap3_netclr.py \
  "${b15_args[@]}" \
  --late B3 \
  --boot 10000 \
  --seed 42 \
  --out results/cap3_caseblock.json

"$PYTHON_BIN" src/f3_sampling_recalc.py \
  --config experiments/probe32b_sample.yaml \
  --editor ROME \
  --boot 10000 \
  --bootstrap-seed 42 \
  --include-case-summaries \
  --out results/f3_sampling_recalc.json

"$PYTHON_BIN" src/cross_arm_para.py \
  --arm N=experiments/probe32b_freshn.yaml \
  --arm T=experiments/probe32b_para_sup.yaml \
  --arm C=experiments/probe32b_para_strongcomp.yaml \
  --editor ROME \
  --budget B3 \
  --boot 10000 \
  --seed 42 \
  --out results/x3_para_crossarm_v2.json

"$PYTHON_BIN" src/cross_arm.py \
  --arm N=experiments/memit14b_freshn.yaml \
  --arm T=experiments/memit14b_sup.yaml \
  --arm C=experiments/memit14b_strongcomp.yaml \
  --editor MEMIT \
  --budget B3 \
  --out results/x2_memit14b_crossarm_v2.json

logitlens='results/probe/logitlens_cf200_ROME_B3.jsonl'
p0_crosswalk_ran=0
if [[ -f "$logitlens" && "$p0_ready" -eq 1 ]]; then
  "$PYTHON_BIN" src/p0_downstream_crosswalk.py \
    --logitlens "$logitlens" \
    --out results/p0_downstream_crosswalk.json
  p0_crosswalk_ran=1
elif [[ -f "$logitlens" ]]; then
  echo '[CPU-CLOSEOUT][BLOCKED-OPTIONAL] logit-lens raw exists, but P0 A3/WA dependencies are incomplete; crosswalk not rerun.' >&2
else
  echo "[CPU-CLOSEOUT][BLOCKED-OPTIONAL] $logitlens (P0 logit-lens crosswalk remains blocked)" >&2
fi

artifacts=(
  results/percase_caseblock.json
  results/b15_caseblock.json
  results/cap3_caseblock.json
  results/f3_sampling_recalc.json
  results/x3_para_crossarm_v2.json
  results/x2_memit14b_crossarm_v2.json
)
if [[ "$p0_crosswalk_ran" -eq 1 ]]; then
  artifacts+=(results/p0_downstream_crosswalk.json "$logitlens")
fi

echo '[CPU-CLOSEOUT] completed artifacts:'
sha256sum "${artifacts[@]}"

"$PYTHON_BIN" src/test_validate_cpu_closeout.py
"$PYTHON_BIN" src/validate_cpu_closeout.py \
  --percase results/percase_caseblock.json \
  --b15 results/b15_caseblock.json \
  --cap3 results/cap3_caseblock.json \
  --f3 results/f3_sampling_recalc.json \
  --x2 results/x2_memit14b_crossarm_v2.json \
  --x3 results/x3_para_crossarm_v2.json \
  --p0 results/p0_downstream_crosswalk.json \
  --out results/cpu_closeout_audit.json

sha256sum results/cpu_closeout_audit.json
