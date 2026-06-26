#!/usr/bin/env bash
# A4 · Llama-70B n=200 做厚头牌最弱锚(plan v1.31 必做)。H200 fp32 model_parallel 2 replica×4 卡。
# 断点续:tag cf100 + jsonl 追加 + case_id 跳过 → 跳过旧 n≈84、只补 100-199;被杀/被收重跑同命令接上(GPFS 持久)。
# 70B 走 Llama 原生 device_map(非 qwen 分支),但 edit_loop 仍 apply() 同一 patch → WHYAAAI_DTYPE/DEVICE_MAP 对它生效。
set -uo pipefail

: "${W:=$(dirname "$PWD")}"
# ⚠ 70B 权重(~140G bf16)装不下 ~80G hdd → 在 GPFS big disk(非 $W/models;hdd 上多半只有 config 残桩、无 safetensors)。
# 自动探测:必须有真权重(*.safetensors / *.bin),不能只看 config.json(残桩有 config 会骗过旧 guard)。
_has_w() { ls "$1"/*.safetensors >/dev/null 2>&1 || ls "$1"/*.bin >/dev/null 2>&1; }
if [ -n "${WHYAAAI_MODEL:-}" ] && _has_w "$WHYAAAI_MODEL"; then :; else
  WHYAAAI_MODEL=""
  for cand in \
      /inspire/qb-ilm/project/ai4education/public/whywhy/models/DeepSeek-R1-Distill-Llama-70B \
      /inspire/qb-ilm/project/ai4education/public/*/models/DeepSeek-R1-Distill-Llama-70B \
      "$W/models/DeepSeek-R1-Distill-Llama-70B"; do
    if _has_w "$cand"; then WHYAAAI_MODEL="$cand"; break; fi
  done
fi
export WHYAAAI_MODEL
export WHYAAAI_DTYPE=float32                                  # Hopper ROME compute_v 必 fp32
export WHYAAAI_DEVICE_MAP=balanced_low_0                      # 防 device_map='auto' 贪填 GPU0(280G 跨卡均摊+GPU0 留最空)
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

if [ -z "$WHYAAAI_MODEL" ] || ! _has_w "$WHYAAAI_MODEL"; then
  echo "✗ 70B 真权重(*.safetensors)找不到。试过 GPFS whywhy / public/*/models / \$W/models。"
  echo "  定位: find /inspire/qb-ilm/project/ai4education/public -maxdepth 5 -type d -iname '*Distill-Llama-70B*' 2>/dev/null"
  echo "  然后: WHYAAAI_MODEL=<含 safetensors 的目录> nohup bash run_a4_h200.sh ...(只 A4 单独跑;别用 chain 内联 env 会污染 A2 的 32B 路径)"
  exit 1
fi
echo "✓ A4 70B 权重=$WHYAAAI_MODEL  fp32 model_parallel 2×4 device_map=$WHYAAAI_DEVICE_MAP  $(date +%F\ %H:%M)"

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
