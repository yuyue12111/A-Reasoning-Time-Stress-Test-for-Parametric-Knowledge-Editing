#!/usr/bin/env bash
# E-MULTIHOP/W3 · 编辑态 2-hop(Llama-8B,ROME 编辑→问 hop_q)—— 在 base-floor 门后的信息残池上跑.
# ⚠ 编辑态要 fp32:H200/H100(Hopper)上 ROME compute_v bf16 会 NaN(base-floor 无编辑才 bf16)。4090(Ada)可去掉 DTYPE 行用 bf16。
# 前置:先 bash run_mh_basefloor.sh 出 data/mquake_gated.jsonl(信息残池)。
# 用法(项目根): bash run_mh_edited.sh
set -uo pipefail
: "${W:=$(dirname "$PWD")}"
: "${WHYAAAI_MODEL:=$W/models/DeepSeek-R1-Distill-Llama-8B}"
export WHYAAAI_MODEL
export WHYAAAI_DTYPE=float32                              # Hopper ROME compute_v 必 fp32;8B fp32 ~32G 单卡(H200/H100 都装得下)
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
[ -e "$WHYAAAI_MODEL/config.json" ] || { echo "✗ 模型缺:$WHYAAAI_MODEL"; exit 1; }
[ -e data/mquake_gated.jsonl ] || { echo "✗ 缺 data/mquake_gated.jsonl —— 先 bash run_mh_basefloor.sh(base-floor 门)"; exit 1; }
echo "✓ MH 编辑态 2-hop  Llama-8B fp32  单卡×8  残池 $(wc -l <data/mquake_gated.jsonl) 条  $(date +%F\ %H:%M)"

for r in $(seq 0 7); do
  PYTHONPATH=source/EasyEdit python src/run_pilot.py --config experiments/mquake8b_2hop.yaml --editor ROME \
      --rank "$r" --world 8 --device "$r" >"/tmp/mh_edit_r$r.log" 2>&1 &
  sleep 8
done
wait
echo "--- 各分片末行(应无 OOM/Traceback/nan/device mismatch) ---"; tail -n1 /tmp/mh_edit_r*.log
echo "===== 2-hop 打分 ====="
python src/multihop.py score --edited 'results/probe/r1llama8b_ROME_mh2hop_r*of*.jsonl' --pool data/mquake_gated.jsonl --out results/mh/score_2hop.json
echo "→ 看 hop_ES(下游答新且不旧)/ hop_revert(下游答旧)/ 2-hop ES drop B0→B3。预注册三结局(更多/相同/无 erosion)见 depth-plan.md。"
