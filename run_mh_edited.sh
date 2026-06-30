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
# recut:丢退化-new 模板(P140 宗教→Lu/Epworth 塌缩,占比>0.3)→ 干净残池 150(panel wq9e477xn 修)
[ -e data/mquake_gated_clean.jsonl ] || python src/multihop.py recut --pool data/mquake_gated.jsonl --out data/mquake_gated_clean.jsonl
echo "✓ MH 编辑态 2-hop  Llama-8B fp32  单卡×8  干净残池 $(wc -l <data/mquake_gated_clean.jsonl) 条  $(date +%F\ %H:%M)"

for r in $(seq 0 7); do
  PYTHONPATH=source/EasyEdit python src/run_pilot.py --config experiments/mquake8b_2hop.yaml --editor ROME \
      --rank "$r" --world 8 --device "$r" >"/tmp/mh_edit_r$r.log" 2>&1 &
  sleep 8
done
wait
echo "--- 各分片末行(应无 OOM/Traceback/nan/device mismatch) ---"; tail -n1 /tmp/mh_edit_r*.log
echo "===== 2-hop 打分(b0_prop 门上的 propagation-erosion + per-template)====="
python src/multihop.py score --edited 'results/probe/r1llama8b_ROME_mh2hop_r*of*.jsonl' --pool data/mquake_gated_clean.jsonl --out results/mh/score_2hop.json
echo "→ 看 n_b0_prop(编辑 B0 传到 2-hop 的数;<40=bounded-null→可能要 32B)+ propagation-erosion B0→B3 + per-template。陈旧 revert 只作次要括号。预注册三结局见 depth-plan。"
