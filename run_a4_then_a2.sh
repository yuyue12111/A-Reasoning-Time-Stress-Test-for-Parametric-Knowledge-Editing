#!/usr/bin/env bash
# 接力链:先跑 A4(70B,最耗时),完了自动恢复 A2(剩 th_p12/p16/all_p8,断点续跳过已完成 3 点)。
# 用法(项目根,后台,关终端不受影响):
#   nohup bash run_a4_then_a2.sh > /tmp/a4a2.log 2>&1 &
#   tail -f /tmp/a4a2.log            # 看进度
# 前提:A2 已停(pkill);A4/A2 都断点续 → 链中任一步被收/被杀,重跑本脚本从断点接上。
set -uo pipefail
cd "$(cd "$(dirname "$0")" && pwd)"

echo "[chain] $(date) ========== A4(70B n=200)开始 =========="
bash run_a4_h200.sh

echo "[chain] $(date) ========== A4 结束 → 接力恢复 A2(单卡数据并行,跳过已完成点) =========="
sleep 30                                                      # 等 70B 显存彻底释放再起 A2
bash run_a2_h200.sh

echo "[chain] $(date) ========== 全部完成(A4 + A2) =========="
echo "结果:A4 → /tmp/a4.score ; A2 6 点 → /tmp/a2_probe32b_a2_*.score"
