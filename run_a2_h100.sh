#!/usr/bin/env bash
# A2 · RQ3 α-sweep + scope 消融 · 32B (H100, fp32) —— plan v1.31 / 审计 wfgmaerr3 必做项.
# 目的:证 penalty=8 非 cherry-pick(ΔRR/ΔCLR 随 α 单调 dose-response、Loc 守门跨 α 稳),
#       scope=all vs think 消融说明为何主报 think。6 点 back-to-back,各 n=100,仅 efficacy+locality。
# 用法(项目根 $W/why-aaai27 跑,单行): bash run_a2_h100.sh
# 可中断续跑:jsonl 追加写 + 已完成 case_id 自动跳过 → 被回收/杀掉后重跑同命令即从断点继续。
# 基线 α=0 = 复用 experiments/probe32b.yaml 的 cf200(suppress off,已在盘),分析时取前 100 case_id 配对,免再跑。
set -uo pipefail

: "${W:=$(dirname "$PWD")}"                                   # 项目根=$W/why-aaai27;未设则由 PWD 推断
: "${WHYAAAI_MODEL:=$W/models/DeepSeek-R1-Distill-Qwen-32B}"  # 离线本地 32B 绝对路径
export WHYAAAI_MODEL
export WHYAAAI_DTYPE=float32                                  # Hopper(H100/H200) ROME compute_v bf16→NaN,必 fp32
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True       # 32B fp32(~64G)+8192 KV 在 80G 卡偏紧,减碎片

if [ ! -e "$WHYAAAI_MODEL/config.json" ]; then
  echo "✗ 找不到 32B: $WHYAAAI_MODEL"
  echo "  → 先确认 H100 挂了共享盘且能 ls 到该目录;或 export WHYAAAI_MODEL=<本地 32B 绝对路径> 后重跑"
  exit 1
fi
echo "✓ model=$WHYAAAI_MODEL  dtype=float32  $(date +%F\ %H:%M)"

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
    sleep 15                                                  # 错峰加载(8×64G fp32 同时入内存会挤爆;稳过速)
  done
  wait
  echo "--- $tag 各分片末行(应无 Traceback/Killed/OOM) ---"; tail -n1 /tmp/a2_${tag}_r*.log
  echo "===== $(date +%H:%M) SCORE $tag ====="
  python src/score_pilot.py --config "$cfg" --editor ROME | tee "/tmp/a2_${tag}.score"
done

echo "===== ALL A2 DONE $(date +%F\ %H:%M) ====="
echo "###### dose-response 汇总(每点 B3 行:RR/CLR/Loc 随 α 变;B0 给 ES 降幅参照) ######"
for f in /tmp/a2_probe32b_a2_*.score; do echo "## $(basename "$f" .score)"; grep -E "^B0 |^B3 " "$f"; done
echo "对照基线(α=0,suppress off)= experiments/probe32b.yaml cf200 的 B3:RR 0.193 / CLR 0.545 / Loc 0.958"
