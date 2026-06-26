#!/usr/bin/env bash
# A4 · Llama-70B n=200 做厚头牌最弱锚(plan v1.31 必做)。H200 fp32 model_parallel 2 replica×4 卡。
# 断点续:tag cf100 + jsonl 追加 + case_id 跳过 → 跳过旧 n≈84、只补 100-199;被杀/被收重跑同命令接上(GPFS 持久)。
# 70B 走 Llama 原生 device_map(非 qwen 分支),但 edit_loop 仍 apply() 同一 patch → WHYAAAI_DTYPE/DEVICE_MAP 对它生效。
set -uo pipefail

: "${W:=$(dirname "$PWD")}"
: "${WHYAAAI_MODEL:=$W/models/DeepSeek-R1-Distill-Llama-70B}"
export WHYAAAI_MODEL
export WHYAAAI_DTYPE=float32                                  # Hopper ROME compute_v 必 fp32
export WHYAAAI_DEVICE_MAP=balanced_low_0                      # 防 device_map='auto' 贪填 GPU0(280G 跨卡均摊+GPU0 留最空)
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

[ -e "$WHYAAAI_MODEL/config.json" ] || { echo "✗ 70B 模型缺:$WHYAAAI_MODEL"; exit 1; }
echo "✓ A4 70B n=200  H200 fp32 model_parallel 2 replica×4卡  device_map=$WHYAAAI_DEVICE_MAP  $(date +%F\ %H:%M)"

# 2 replica × 4 卡(70B fp32 280G 跨 4 卡=70G/卡;world=2 分 case)。若 OOM 退 1 replica×8 卡:
#   CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 ... --rank 0 --world 1(35G/卡最稳但最慢)。
CUDA_VISIBLE_DEVICES=0,1,2,3 PYTHONPATH=source/EasyEdit python src/run_pilot.py \
    --config experiments/probe_llama70b.yaml --editor ROME --rank 0 --world 2 >/tmp/a4_r0.log 2>&1 &
sleep 30                                                      # 错峰:两 replica 各跨 4 卡加载 70G/卡,别同时挤
CUDA_VISIBLE_DEVICES=4,5,6,7 PYTHONPATH=source/EasyEdit python src/run_pilot.py \
    --config experiments/probe_llama70b.yaml --editor ROME --rank 1 --world 2 >/tmp/a4_r1.log 2>&1 &
wait

echo "--- A4 分片末行(应无 OOM/device mismatch/nan) ---"; tail -n1 /tmp/a4_r*.log
echo "===== A4 SCORE(--drop-degenerate 兜 model_parallel 间歇数值不稳) ====="
python src/score_pilot.py --config experiments/probe_llama70b.yaml --editor ROME --drop-degenerate | tee /tmp/a4.score
echo "A4 done $(date +%F\ %H:%M)"
