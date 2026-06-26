#!/usr/bin/env bash
# A2 · RQ3 α-sweep + scope 消融 · 32B (H200, fp32, **单卡数据并行**) —— plan v1.31 / 审计 wfgmaerr3.
# H200 141G 单卡装得下 32B fp32(130G)→ 走 headline 同款单卡数据并行(world=8,每卡一片),**无 model_parallel/device_map 烦恼**。
# (H100 80G 装不下故才要 model_parallel,那条路见 git 历史 run_a2_h100.sh;H200 回来后首选本脚本。)
# 用法(项目根,单行): bash run_a2_h200.sh   可中断续跑(jsonl 追加 + case_id 跳过)。
set -uo pipefail

: "${W:=$(dirname "$PWD")}"
: "${WHYAAAI_MODEL:=$W/models/DeepSeek-R1-Distill-Qwen-32B}"
export WHYAAAI_MODEL
export WHYAAAI_DTYPE=float32                                  # Hopper ROME compute_v 必 fp32;H200 单卡 130G 装得下
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

[ -e "$WHYAAAI_MODEL/config.json" ] || { echo "✗ 模型缺:$WHYAAAI_MODEL"; exit 1; }
echo "✓ A2 H200  fp32 单卡数据并行 world=8  model=$WHYAAAI_MODEL  $(date +%F\ %H:%M)"

CFGS="experiments/probe32b_a2_th_p2.yaml \
experiments/probe32b_a2_th_p4.yaml \
experiments/probe32b_a2_th_p8.yaml \
experiments/probe32b_a2_th_p12.yaml \
experiments/probe32b_a2_th_p16.yaml \
experiments/probe32b_a2_all_p8.yaml"

for cfg in $CFGS; do
  tag=$(basename "$cfg" .yaml)
  echo "===== $(date +%H:%M) RUN $tag ====="
  for r in $(seq 0 7); do
    PYTHONPATH=source/EasyEdit python src/run_pilot.py --config "$cfg" --editor ROME \
        --rank "$r" --world 8 --device "$r" >"/tmp/a2_${tag}_r$r.log" 2>&1 &
    sleep 5
  done
  wait
  echo "--- $tag 各分片末行(应无 OOM/Traceback/nan) ---"; tail -n1 /tmp/a2_${tag}_r*.log
  echo "===== $(date +%H:%M) SCORE $tag ====="
  python src/score_pilot.py --config "$cfg" --editor ROME --drop-degenerate | tee "/tmp/a2_${tag}.score"
done

echo "===== ALL A2 DONE $(date +%F\ %H:%M) ====="
echo "###### dose-response 汇总(每点 B3 行:RR/CLR/Loc 随 α) ######"
for f in /tmp/a2_probe32b_a2_*.score; do echo "## $(basename "$f" .score)"; grep -E "^B0 |^B3 " "$f"; done
echo "对照基线(α=0,suppress off)= experiments/probe32b.yaml cf200 B3:RR 0.193 / CLR 0.545 / Loc 0.958"
