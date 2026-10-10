# 平台运行单（ARR 修订，引擎 v2）

按顺序执行；每步写明用什么卡、为什么、产出什么、过什么门。细节参数见各模块 README
（`README.md` 生成/选池，`README_deltas.md` 编辑增量，`README_judge.md` 判官，`README_mech.md` 机制）。
凡标 **回传** 的产出，下载到本地仓库对应路径后告诉我，我来分析和决策。

## 0 准备（一次）
```bash
cd /inspire/hdd/project/ai4education/ky26140/why/why-aaai27
source experiments/x23_paths.sh                     # PROJ / MODEL14 / MODEL32 / WIKI_EN
W=/inspire/hdd/project/ai4education/ky26140/why
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export WHYAAAI_WIKI_PARQUET=$WIKI_EN                # 只用英文维基（曾误匹配韩语）
mkdir -p logs/rt results/rt
PYTHONPATH=src python src/rt/tests/run_all.py       # CPU，~1 分钟；必须 "166 passed, 0 failed"
```
- 上传：`src/rt/`、`src/vendor_patches/`（新增 2 个补丁 + README）、`experiments/rt/`、`data/pools/`、`.gitignore`。
- 模型：已有 R1-Distill 六个；新下载 QwQ-32B、Qwen2.5-32B-Instruct、gemma-3-27b-it（需在 HF 上接受许可）、
  Mistral-Small-3.1-24B-Instruct-2503。**QwQ 的本地目录名必须含 `qwen`**（EasyEdit 按子串选加载器），
  例如 `ln -s $W/models/QwQ-32B $W/models/Qwen-QwQ-32B`。同一模型在所有步骤里用同一个路径字符串。
- 环境：沿用平台现有环境（torch 2.9.1、transformers 5.5.4、accelerate）。不需要 vLLM。

## 1 G0 引擎一致性门（H200 × 8，约 1.5 小时）——不过门不做 Study 2
为什么 H200：32B 在 fp32 下算编辑要 131 GB，只有 H200 放得下。
```bash
export PYTHONPATH=src:source/EasyEdit
unset WHYAAAI_MODEL WHYAAAI_DTYPE
# 1a 编辑增量：先 20 条 smoke，看日志再跑全量 200 条（README_deltas 第 1 步）
for r in 0 1 2 3; do python -m rt.deltas run --config experiments/rt/deltas_g0_r1qwen32b.yaml \
  --model-path $MODEL32 --limit 20 --rank $r --world 4 --device $r > logs/rt/g0d_smoke_r$r.out 2>&1 & sleep 20; done; wait
python -m rt.deltas summarize results/rt/deltas_logs/g0/r1qwen32b_ROME_cf_r*of4.jsonl
for r in $(seq 0 7); do python -m rt.deltas run --config experiments/rt/deltas_g0_r1qwen32b.yaml \
  --model-path $MODEL32 --rank $r --world 8 --device $r > logs/rt/g0d_r$r.out 2>&1 & sleep 20; done; wait
# 1b 生成（bf16，base + rome_N，B0/B3）
export WHYAAAI_MODEL=$MODEL32
for r in $(seq 0 7); do CUDA_VISIBLE_DEVICES=$r PYTHONPATH=src nohup python -m rt.run \
  --config experiments/rt/study1_g0_r1qwen32b.yaml --rank $r --world 8 > logs/rt/g0_r$r.log 2>&1 & done; wait
# 1c 判定（CPU）；退出码 0 = PASS
PYTHONPATH=src python -m rt.g0 --study1 'results/probe/r1qwen32b_ROME_cf200_r*of8.jsonl' \
  --study1-base 'results/probe/r1qwen32b_BASE_cf200_r*.jsonl' \
  --v2 'results/rt/g0/r1qwen32b_g0_rome_N_r*of8.jsonl' --v2-base 'results/rt/g0/r1qwen32b_g0_base_r*of8.jsonl' \
  --out results/rt/g0/g0_verdict.json
```
门：v2 降幅落在 Study 1 的 CI [.030, .182] 内，且 B0 逐 case 一致 ≥ 85%。**回传** `results/rt/g0/`。
开跑前先肉眼看 `results/rt/g0/*rome_N_r0of8.jsonl` 前几条生成是人话。

## 2 与 G0 并行、不占卡的事
- **选池候选（CPU，要有完整 `results/` 历史）**：`PYTHONPATH=src python -m rt.pool build --config experiments/rt/pool_screen.yaml`。
  **回传** `experiments/rt/pools/study2/`（我来提交）。
- **人工标注**：我已生成练习集（20 条）与 Study 1 验证集（200 条）；两位标注者各拿自己的 CSV + `guide.md`，
  互不讨论，约 1.5–2 小时/人。**回传**填好的两个 CSV。

## 3 G0 通过后（H200 × 1）
- **机制探针**（复用 1a 的增量，约 0.5 GPU 小时）：`README_mech.md` 的 smoke → 全量 → summarize。**回传** `results/rt/mech/`。
- **Study 1 判官**（每个判官 1 张 H200，两个并行，各 20–35 分钟；H100-80G 用 `--batch-size 16` 也行）：
  `README_judge.md` 第 0–3 步（先 `show` 看 prompt，再 `selfcheck`，再 `run --orders 2`，再 `score`）。**回传** `results/judge/`。

## 4 Study 2 选池筛选（每模型只跑 B0，便宜）
每个模型：`rt.pool screen`（`README.md` "Study-2 pool"）→ `rt.pool qualify`。
卡：32B/QwQ/Instruct 用 H200 × 8（bf16，1 卡/进程）；≤14B 可用 H100；70B 用 `device_map auto`，2 卡/进程。
**回传** `experiments/rt/pools/study2/manifest_*.jsonl`（+ `.sha256`、`summary_*.json`）。
**我收到后冻结 `prereg-arr.md`（填 §9 哈希），提交，再开始第 5 步。**

## 5 Study 2 编辑增量（fp32）
- ROME，全部 8 个模型：`python -m rt.deltas run --config experiments/rt/deltas_s2_<model>.yaml --model-path <路径> ...`
  - 32B / QwQ / Instruct：H200，1 卡/进程 × 8；QwQ 与 Instruct 先 `--limit 20` smoke，看编辑是否生效（第 12 层未验证）。
  - 14B / 7B / 1.5B / 8B：H100 或 H200，1 卡/进程。
  - 70B：fp32 282 GB → 4 张 H200/进程，2 个分片（最贵的一步，约 30 GPU 小时）。
- MEMIT / AlphaEdit（仅 32B）：先做协方差统计（`README_deltas.md` 第 2 步 2a→2b→2c→2d，建议先做 2x 与 Study 1 的 14B 统计对账），
  再 20 条 smoke（第 3 步），再全量（`--editor MEMIT` / `--editor AlphaEdit`，2 卡/进程 × 4）。
- 每批跑完：`python -m rt.deltas summarize results/rt/deltas_logs/s2/<model>_<editor>_cf_r*.jsonl`，全部 ok、rank 1、无 NaN。

## 6 Study 2 生成（bf16，H200）
- 32B：`README.md` "Study 2, R1-Distill-Qwen-32B"——stage 1（全部条件）跑完后再 stage 2（own/filler/swap）。
- 其余 7 个模型：`python -m rt.run --config experiments/rt/study2_<model>.yaml --rank r --world 8`（70B 用 2 卡/进程、world 4）。
- 每个新模型先 `--limit 2 --run-tag s2_smoke` 看生成是人话。**回传** `results/rt/s2/`。

## 7 Study 2 判官与人工标注
- 判官：同第 3 步，行换成 `results/rt/s2/*.jsonl`，分两片 `--shard 0/2`、`--shard 1/2`（每片 < 2 小时）。
- 我用 Study 2 的行生成 200 条标注包（预注册的切换规则基于它），两位标注者再标一次。

## 卡时估算（H200）
| 步骤 | GPU 小时 |
|---|---|
| G0（增量 + 生成） | ~5 |
| 机制探针 + Study 1 判官 | ~2 |
| 选池筛选（8 模型） | ~4 |
| 编辑增量：32B ROME/QwQ/Instruct ~20，MEMIT+AlphaEdit ~40，统计 ~12，70B ~30，小模型 ~3 | ~105 |
| Study 2 生成 | ~25 |
| Study 2 判官 | ~8 |
| 合计 | ~150（余 ~50） |
