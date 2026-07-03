#!/usr/bin/env bash
# run_gpu_queue.sh —— v1.59 GPU 队列自动串跑(可断点续跑,抗夜间关机)
# ---------------------------------------------------------------------------
# 【单实例全跑(H200,推荐)】一条命令按 kill-risk 顺序跑完全部 4 件(M4→G1→B22→S10-lite):
#   cd <项目根>; nohup bash run_gpu_queue.sh all > logs/queue_all.log 2>&1 &
#   (8B/14B 在 H200 fp32 显存富裕,同实例串跑即可;M4/G1=kill-risk 排前。)
#
# 【双实例分跑(H100 回来后用)】各跑自己 lane、并行:
#   H200: nohup bash run_gpu_queue.sh h200 &   # M4 → B22
#   H100: nohup bash run_gpu_queue.sh h100 &   # G1 → S10-lite
#
# 抗关机:实例夜里被关 → 进程在 wait 处被杀 → 未写 .done → 重启实例后【再跑同一条命令】即从断点续
#   (harness 按 case_id 跳过已完成 case;已完成的整步靠 logs/<step>.done 跳过)。安全可重复执行。
# 前置:环境变量 W(模型根,如 /inspire/qb-ilm/project/ai4education/ky26140);从项目根运行。
# 监控:tail -f logs/queue_all.log;单步结果 logs/<step>_score.log;分片进度 logs/<step>_r?.log。
# ---------------------------------------------------------------------------
set -uo pipefail
LANE="${1:?用法: bash run_gpu_queue.sh all|h200|h100}"
: "${W:?环境变量 W 未设(模型根目录)}"
export WHYAAAI_DTYPE=float32          # 两 lane 都用 fp32(Hopper bf16 ROME/MEMIT compute_v NaN 风险;14B/8B 求稳)
export PYTHONPATH=source/EasyEdit
NGPU=8
mkdir -p logs

# 单实例互斥:防手滑同 lane 双开(flock 随进程死自动释放,关机重启后旧锁不挡)
exec 9> "logs/queue_${LANE}.lock"
if command -v flock >/dev/null 2>&1; then
  flock -n 9 || { echo "[$(date '+%F %T')] lane=${LANE} 已在运行(logs/queue_${LANE}.lock 被占),退出"; exit 1; }
fi

ts(){ date '+%F %T'; }
log(){ echo "[$(ts)] $*"; }

# 模型路径解析(照 run_a4_h200.sh 的验证器):不同尺度模型分散在 $W/models 与 GPFS public/whywhy/models
# (如 70B 不在 $W/models);且 hdd 上常有【config 残桩、无 safetensors】会骗过 -e 检查 → 必须验真权重。
_has_w(){ ls "$1"/*.safetensors >/dev/null 2>&1 || ls "$1"/*.bin >/dev/null 2>&1; }
resolve_model(){   # $1=模型名(如 DeepSeek-R1-Distill-Qwen-32B);echo 含真权重的目录,找不到返回 1
  local name="$1" cand
  # 显式 override:export WHYAAAI_MODEL_<名去横杠点>=<目录> 可点名指定某模型(多步各自指定)
  local ov_key="WHYAAAI_MODEL_${name//[-.]/_}"; local ov="${!ov_key:-}"
  if [[ -n "$ov" ]] && _has_w "$ov"; then echo "$ov"; return 0; fi
  for cand in \
      /inspire/hdd/global_public/public_models/deepseek-ai/"$name" \
      /inspire/hdd/global_public/public_models/*/"$name" \
      "$W/models/$name" \
      /inspire/qb-ilm/project/ai4education/public/whywhy/models/"$name" \
      /inspire/qb-ilm/project/ai4education/public/*/models/"$name" \
      /inspire/hdd/project/ai4education/*/models/"$name" \
      /inspire/hdd/project/ai4education/*/*/models/"$name"; do
    if _has_w "$cand"; then echo "$cand"; return 0; fi
  done
  return 1
}

# 分片完整性守门:所有 NGPU 分片文件存在且非空(catch 整个 rank 启动即死=OOM/坏路径;
# per-case 错误由 harness 写 error 行续跑、不算整片死)。返回 0=齐,1=缺。
check_shards(){   # $1=cfg $2=editor
  python - "$1" "$2" "$NGPU" <<'PY'
import sys, os, glob, yaml
cfg, editor, ng = sys.argv[1], sys.argv[2], int(sys.argv[3])
c = yaml.safe_load(open(cfg)); ds = c["dataset"]
pat = os.path.join(c["out_dir"], f"{c['model_tag']}_{editor}_{ds['tag']}_r*of{ng}.jsonl")
fs = [f for f in glob.glob(pat) if os.path.getsize(f) > 0]
print(f"  分片完整性 {len(fs)}/{ng} 非空  ({pat})")
sys.exit(0 if len(fs) >= ng else 1)
PY
}

# run_step NAME MODEL_SUBPATH EDITOR CONFIG PREHEAT(0/1) SCORE_CMD
run_step(){
  local name="$1" model="$2" editor="$3" cfg="$4" preheat="$5" scorecmd="$6"
  if [[ -f "logs/${name}.done" ]]; then log "SKIP ${name}(已 .done)"; return 0; fi
  log "START ${name}  model=${model} editor=${editor} cfg=${cfg} preheat=${preheat}"
  local resolved
  if resolved="$(resolve_model "$model")"; then
    export WHYAAAI_MODEL="$resolved"
    log "${name}: 模型解析 = $WHYAAAI_MODEL"
  else
    log "!! ${name}: 找不到 ${model} 的真权重(*.safetensors/*.bin)。试过 \$W/models、public/whywhy/models、public/*/models、hdd/*。"
    log "   定位: find /inspire -maxdepth 6 -type d -iname '*${model}*' 2>/dev/null | head"
    log "   手动: export WHYAAAI_MODEL_${model//[-.]/_}=<含 safetensors 的目录>  或直接改本脚本的候选根后重跑"
    return 1
  fi

  local start=0
  if [[ "$preheat" == "1" ]]; then    # MEMIT:mom2 预热=rank0 单进程先跑完,防 8 分片并发重复触发 mom2
    log "${name}: mom2 预热(rank0 单进程,可能数小时)..."
    python src/run_pilot.py --config "$cfg" --editor "$editor" --rank 0 --world "$NGPU" --device 0 \
      > "logs/${name}_r0.log" 2>&1
    log "${name}: rank0 完成(mom2 已缓存),启并发 rank1-$((NGPU-1))"
    start=1
  fi

  local r
  for r in $(seq "$start" $((NGPU-1))); do
    python src/run_pilot.py --config "$cfg" --editor "$editor" --rank "$r" --world "$NGPU" --device "$r" \
      > "logs/${name}_r${r}.log" 2>&1 &
  done
  wait
  log "${name}: 全分片结束"

  if ! check_shards "$cfg" "$editor"; then
    log "!! ${name} 分片不齐(某 rank 整片死,见 logs/${name}_r?.log)— 不打分不标 done,重跑本脚本会续"
    return 1
  fi
  log "${name}: 打分中..."
  if eval "$scorecmd" > "logs/${name}_score.log" 2>&1; then
    touch "logs/${name}.done"
    log "DONE  ${name}  → logs/${name}_score.log"
    tail -n 20 "logs/${name}_score.log" | sed 's/^/    /'
  else
    log "!! SCORE-FAIL ${name}(未标 done,重跑会重试)见 logs/${name}_score.log"
    return 1
  fi
}

log "════════ GPU 队列启动 lane=${LANE} (WHYAAAI_DTYPE=${WHYAAAI_DTYPE}, W=${W}) ════════"

# 各步定义(函数封装 → all/h200/h100 复用同一份定义,不重复;run_step 幂等按 .done 跳过)
step_m4(){  run_step m4_32b       "DeepSeek-R1-Distill-Qwen-32B" ROME  experiments/probe32b_sup_strongcomp.yaml 0 \
              'python src/score_pilot.py --config experiments/probe32b_sup_strongcomp.yaml --editor ROME'; }
step_g1(){  run_step g1_8b        "DeepSeek-R1-Distill-Llama-8B"  ROME experiments/mquake8b_2hop_sup.yaml 0 \
              'python src/multihop.py score --edited "results/probe/r1llama8b_ROME_mh2hopsup_r*of*.jsonl" --pool data/mquake_gated_clean.jsonl'; }
step_b22(){ run_step b22_memit32b "DeepSeek-R1-Distill-Qwen-32B" MEMIT experiments/memit32b.yaml 1 \
              'python src/score_pilot.py --config experiments/memit32b.yaml --editor MEMIT'
            log "注:若 b22_memit32b 因 OOM/mom2 失败,手动改跑 memit14b.yaml(见其头注)"; }
step_s10(){ run_step s10_14b      "DeepSeek-R1-Distill-Qwen-14B" ROME experiments/probe14b_sup.yaml 0 \
              'python src/score_pilot.py --config experiments/probe14b_sup.yaml --editor ROME'; }

case "$LANE" in
  all)    step_m4; step_g1; step_b22; step_s10 ;;   # 全放一实例,kill-risk(M4/G1)先,再 B22/S10
  h200)   step_m4; step_b22 ;;
  h100)   step_g1; step_s10 ;;
  *) log "未知 lane: ${LANE}(要 all / h200 / h100)"; exit 2 ;;
esac

log "════════ lane=${LANE} 队列结束。已完成步: $(ls logs/*.done 2>/dev/null | xargs -n1 basename 2>/dev/null | tr '\n' ' ') ════════"
log "未标 .done 的步 = 未完成或打分失败,重跑同一命令即续。结果贴给 Claude 落库。"
