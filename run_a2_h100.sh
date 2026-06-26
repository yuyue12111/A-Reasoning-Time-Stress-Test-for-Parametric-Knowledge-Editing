#!/usr/bin/env bash
# A2 · RQ3 α-sweep + scope 消融 · 32B (H100, fp32, **model_parallel 跨卡**) —— plan v1.31 / 审计 wfgmaerr3 必做项.
# ⚠ 为什么跨卡:32B fp32 ≈130G > H100 单卡 80G → 必须 device_map='auto' 把模型摊到多卡(单卡数据并行必 OOM)。
#   32B 比 70B 小 → 每 replica 只需 2 卡(130/2≈65G/卡,装得下 80G)→ 8 卡 = 4 replica × 2 卡 = 4× 吞吐。
#   config 已设 model_parallel: true;**不传 --device**(model_parallel 下 device_map 用 CUDA_VISIBLE_DEVICES 的全部卡)。
# 用法(项目根跑,单行): bash run_a2_h100.sh
# 可中断续跑:jsonl 追加 + case_id 跳过。**首次重跑前先清掉上次 OOM 的空文件**(见下 RESET)。
set -uo pipefail

: "${W:=$(dirname "$PWD")}"
: "${WHYAAAI_MODEL:=$W/models/DeepSeek-R1-Distill-Qwen-32B}"
export WHYAAAI_MODEL
export WHYAAAI_DTYPE=float32                                  # Hopper ROME compute_v bf16→NaN,必 fp32(跨卡空间足)
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

if [ ! -e "$WHYAAAI_MODEL/config.json" ]; then
  echo "✗ 找不到 32B: $WHYAAAI_MODEL —— 确认 H100 挂了共享盘 / export WHYAAAI_MODEL 后重跑"; exit 1
fi

# 卡分组:4 replica × 2 卡(默认,最快)。若任一分片仍 OOM(device_map 分配不均),改成 2 replica × 4 卡:
#   GROUPS=("0,1,2,3" "4,5,6,7")     # 2×4,32.5G/卡,绝对装得下但慢一半
GROUPS=("0,1" "2,3" "4,5" "6,7")
WORLD=${#GROUPS[@]}
echo "✓ model=$WHYAAAI_MODEL  fp32  model_parallel  ${WORLD} replica × $(( ${#GROUPS[0]} / 2 + 1 ))卡  $(date +%F\ %H:%M)"

# RESET(只在第一次从 OOM 残骸重跑时需要):清掉上次产生的空/半 jsonl,避免 meta 行混入。已有真数据想续跑就别清。
# rm -f results/probe/r1qwen32b_ROME_cf100sup_*_r*of*.jsonl

CFGS="experiments/probe32b_a2_th_p2.yaml \
experiments/probe32b_a2_th_p4.yaml \
experiments/probe32b_a2_th_p8.yaml \
experiments/probe32b_a2_th_p12.yaml \
experiments/probe32b_a2_th_p16.yaml \
experiments/probe32b_a2_all_p8.yaml"

for cfg in $CFGS; do
  tag=$(basename "$cfg" .yaml)
  echo "===== $(date +%H:%M) RUN $tag (world=$WORLD) ====="
  for r in $(seq 0 $((WORLD-1))); do
    CUDA_VISIBLE_DEVICES="${GROUPS[$r]}" PYTHONPATH=source/EasyEdit python src/run_pilot.py \
        --config "$cfg" --editor ROME --rank "$r" --world "$WORLD" >"/tmp/a2_${tag}_r$r.log" 2>&1 &
    sleep 20                                                  # 错峰:每 replica 跨卡加载 ~65G/卡,别同时挤
  done
  wait
  echo "--- $tag 各分片末行(应无 OOM/Traceback/device mismatch/nan) ---"; tail -n1 /tmp/a2_${tag}_r*.log
  echo "===== $(date +%H:%M) SCORE $tag ====="
  python src/score_pilot.py --config "$cfg" --editor ROME --drop-degenerate | tee "/tmp/a2_${tag}.score"
done

echo "===== ALL A2 DONE $(date +%F\ %H:%M) ====="
echo "###### dose-response 汇总(每点 B3 行:RR/CLR/Loc 随 α) ######"
for f in /tmp/a2_probe32b_a2_*.score; do echo "## $(basename "$f" .score)"; grep -E "^B0 |^B3 " "$f"; done
echo "对照基线(α=0,suppress off)= experiments/probe32b.yaml cf200 的 B3:RR 0.193 / CLR 0.545 / Loc 0.958"
