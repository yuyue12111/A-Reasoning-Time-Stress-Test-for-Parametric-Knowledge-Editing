#!/usr/bin/env bash
# E-SUP-BATTERY/W1 · D(压 o_new)+ P(压 placebo)两对照臂 · 32B (H200, fp32, 单卡数据并行).
# N(cf200)+T(cf200sup)已在盘 → 本脚本只跑 D/P,再用 cross_arm 与 N/T 四臂配对出 headline 因果统计。
# 预注册见 prereg-esup.md(placebo 供体 data/placebo_donors.json 已 BLIND 锁定)。
# ★建议:先单跑 D、约 100 case 后就 cross_arm 看符号(符号错=近致命,最便宜先验);确认方向对再跑满 + P。
# 用法(项目根): bash run_esup_h200.sh        可中断续跑(jsonl 追加 + case_id 跳过)。
set -uo pipefail
: "${W:=$(dirname "$PWD")}"
: "${WHYAAAI_MODEL:=$W/models/DeepSeek-R1-Distill-Qwen-32B}"
export WHYAAAI_MODEL
export WHYAAAI_DTYPE=float32                                  # Hopper ROME compute_v 必 fp32;H200 单卡装 130G
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
[ -e "$WHYAAAI_MODEL/config.json" ] || { echo "✗ 模型缺:$WHYAAAI_MODEL"; exit 1; }
[ -e data/placebo_donors.json ] || { echo "✗ 缺 data/placebo_donors.json(先 python src/placebo_donor.py)"; exit 1; }
echo "✓ E-SUP-BATTERY D+P  fp32 单卡数据并行 world=8  $(date +%F\ %H:%M)"

for cfg in experiments/probe32b_sup_onew.yaml experiments/probe32b_sup_placebo.yaml; do
  tag=$(basename "$cfg" .yaml)
  echo "===== $(date +%H:%M) RUN $tag ====="
  for r in $(seq 0 7); do
    PYTHONPATH=source/EasyEdit python src/run_pilot.py --config "$cfg" --editor ROME \
        --rank "$r" --world 8 --device "$r" >"/tmp/esup_${tag}_r$r.log" 2>&1 &
    sleep 5
  done
  wait
  echo "--- $tag 末行(应无 OOM/Traceback/nan) ---"; tail -n1 /tmp/esup_${tag}_r*.log
  python src/score_pilot.py --config "$cfg" --editor ROME | tee "/tmp/esup_${tag}.score"   # 边际 ES/Loc 自检
done

echo "===== $(date +%H:%M) 跨臂配对统计(N/T/D/P) ====="
python src/cross_arm.py --editor ROME --budget B3 --out results/esup_crossarm.json \
  --arm N=experiments/probe32b.yaml \
  --arm T=experiments/probe32b_sup.yaml \
  --arm D=experiments/probe32b_sup_onew.yaml \
  --arm P=experiments/probe32b_sup_placebo.yaml
echo "→ 读 prereg-esup.md 决策规则:T−P 排零=o_old 特异;P−N≈0=非通用扰动;D 不改善=符号对。"
