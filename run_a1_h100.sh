#!/usr/bin/env bash
# A1 · genbench 部署口径门复测 · 32B (H100, bf16, 单卡数据并行) —— 审计 wfgmaerr3 最高杠杆项.
# 部署口径 = --mode single(单条 o_old,非 union 病态最坏界)+ --force_scope think(只压链,非 all)
#            + B3M=16384(MATH 长链防 boxed 前截断)+ answer_cap 512(答案重述不被截→基线不虚低)。
# ★ genbench 无 ROME 编辑(只是生成 + o_old logit 抑制器)→ bf16 生成 **不发散**(Hopper bf16 NaN 只发生在 ROME compute_v)
#   → 32B bf16=65G 单卡装得下 H100 80G:**不设 WHYAAAI_DTYPE(默认 bf16)、无 model_parallel、无 OOM**。
# 填 results.json.rq3.genbench(把 RQ3 安全门从 failed 最坏界 → 部署口径实测);判 |Δacc|≤0.02。
# 数据须在 GPFS:data/gsm8k_200.jsonl(每行{q,a}) + data/math500_100.jsonl(联网实例已 stage 过最坏界 run)。
# 用法(项目根,单行): bash run_a1_h100.sh   可中断续跑(done 集按 (bench,i) 跳过)。
set -uo pipefail

: "${W:=$(dirname "$PWD")}"
: "${WHYAAAI_MODEL:=$W/models/DeepSeek-R1-Distill-Qwen-32B}"
export WHYAAAI_MODEL
unset WHYAAAI_DTYPE                                           # 默认 bf16:genbench 无 compute_v → Hopper 不 NaN;65G 单卡免 OOM
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

CFG=experiments/probe32b_sup.yaml                            # penalty=8/scope=think(RQ3 同参);genbench 取其 suppress + dataset(o_old 源)
[ -e "$WHYAAAI_MODEL/config.json" ] || { echo "✗ 模型缺:$WHYAAAI_MODEL"; exit 1; }
for d in data/gsm8k_200.jsonl data/math500_100.jsonl; do
  [ -e "$d" ] || { echo "✗ 缺数据 $d —— 先从联网实例 stage 到 GPFS(同最坏界 run 用的那两个文件)"; exit 1; }
done
echo "✓ A1 genbench single+think  model=$WHYAAAI_MODEL  bf16 单卡×8  $(date +%F\ %H:%M)"

for r in $(seq 0 7); do
  python src/genbench.py --config "$CFG" --mode single --force_scope think \
      --gsm8k_budget B3 --math_budget B3M --answer_cap 512 --rank "$r" --world 8 >"/tmp/a1_r$r.log" 2>&1 &
  sleep 8
done
wait
echo "--- 各分片末行(应无 OOM/Traceback) ---"; tail -n1 /tmp/a1_r*.log
echo "===== SCORE(部署口径门) ====="
python src/genbench.py --config "$CFG" --mode single --force_scope think --score | tee /tmp/a1.score
echo "→ |Δacc|≤0.02 = 通过(RQ3 部署安全);填 results.json.rq3.genbench(gsm8k_off/on,math_off/on,gate_pass)"
