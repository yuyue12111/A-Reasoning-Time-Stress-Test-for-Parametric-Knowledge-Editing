#!/usr/bin/env bash
# E-MULTIHOP/W3 · base-floor 门(未编辑 Llama-8B,bf16)—— depth-plan.md 不可省的 day-1 门.
# 在 403 干净 2-hop case 上让**未编辑**基座答 hop_q → 丢"基座靠先验就答出 hop_answer_old/new"的(Trump/Galilee 尾)→ 信息残池(~100)。
# 无编辑 → 无 ROME compute_v → bf16 在 Hopper 也不 NaN;8B bf16 ~16G 单卡×8 数据并行。可断点续。
# 用法(项目根,H200 或 4090 都行): bash run_mh_basefloor.sh
set -uo pipefail
: "${W:=$(dirname "$PWD")}"
: "${WHYAAAI_MODEL:=$W/models/DeepSeek-R1-Distill-Llama-8B}"
export WHYAAAI_MODEL
unset WHYAAAI_DTYPE                                       # bf16:base-floor 无编辑,NaN-safe,8B 单卡省心
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
[ -e "$WHYAAAI_MODEL/config.json" ] || { echo "✗ 模型缺:$WHYAAAI_MODEL"; exit 1; }
[ -e data/mquake_clean.jsonl ] || { echo "✗ 缺 data/mquake_clean.jsonl —— 先 python src/mquake_curate.py(零卡)"; exit 1; }
echo "✓ MH base-floor  未编辑 Llama-8B bf16  单卡×8  $(date +%F\ %H:%M)"

mkdir -p results/mh
for r in $(seq 0 7); do
  python src/multihop.py base --pool data/mquake_clean.jsonl --budgets B0 B3 \
      --rank "$r" --world 8 --out "results/mh/base_8b_r$r.jsonl" >"/tmp/mh_base_r$r.log" 2>&1 &
  sleep 8
done
wait
echo "--- 各分片末行(应无 OOM/Traceback) ---"; tail -n1 /tmp/mh_base_r*.log
echo "===== 门控(丢先验主导)====="
python src/multihop.py gate --base 'results/mh/base_8b_r*.jsonl' --pool data/mquake_clean.jsonl --out data/mquake_gated.jsonl
echo "→ data/mquake_gated.jsonl = 信息残池(编辑态 2-hop 的 population)。下一步:run_pilot --config experiments/mquake8b_2hop.yaml(编辑态)→ src/multihop.py score"
