# RUNBOOK · 算卡窗口操作手册（内网/无 Claude 也能照跑）

> 用途：拿到 8×H200 / 内网窗口时，**按本手册顺序执行即可**，不需要 Claude。
> 所有脚本已写好并过 mock 单测；本手册只讲「怎么按顺序跑 + 别踩哪些坑」。
> 命令默认在仓库根执行；凡涉及 `easyeditor` 的都要 `PYTHONPATH=.` 且 cwd 在 `source/EasyEdit`（见坑①）。

---

## 0. 现状（跑之前先知道）

- **已就位（本地、无需 GPU）**：数据清洗（`src/build_dataset.py`）、harness（`edit_loop`/`metrics`/`think_budget`/`run_pilot`/`prefilter`/`score_pilot`，全部 mock 单测过）、`experiments/pilot.yaml`、AlphaEdit P 生成脚本、`env.lock`。
- **本手册覆盖的 GPU 步骤**：环境 → 数据 → mom2 → **pilot（关键路径）** → 打分 → go/no-go；以及 Phase 2 的 AlphaEdit 预备、think_budget 真模型验证、（可选）CPU 冒烟。
- **跑前一个决策待定**（见 §9）：思考预算档 §2.4(6) vs §12.1(5) 不自洽，`pilot.yaml` 暂用 `B0/B3/B4`。

## 1. 环境（一次性，每台机器）

**优先复现既有环境**（`env.lock` 是 2026-06-11 跑通的 editrev/py3.10）：
```bash
conda create -n editrev python=3.10 pip -y -c conda-forge --override-channels
conda activate editrev            # 或用全路径 ~/miniconda3/envs/editrev/bin/python
pip install -r env.lock           # 若 env.lock 有 @file/本地路径报错，改用下一行
# 退路：pip install -r source/EasyEdit/requirements.txt
```
**5 个依赖坑**（已在本地踩过，照避，详见 `analysis/01_easyedit.md` §6）：
1. `conda create` 卡 ToS → 用 `-c conda-forge --override-channels`（上面已含）。
2. conda-forge 的 python 不自带 pip → `create` 时显式列 `pip`，或 `python -m ensurepip --upgrade`。
3. 系统 py 太旧（<3.10）装不了 torch2.9/transformers5.5 → 必须 ≥3.10 env。
4. `easyeditor` 是**本地包非 pip 安装**，且无 setup.py → 跑任何用到它的脚本要 `cd source/EasyEdit && PYTHONPATH=.`。
5. GPU 机改 device：脚本默认按 rank 给卡号（见 §4c）。

## 2. 数据（一次性；若 `data/*.jsonl` 不在）

```bash
mkdir -p data/raw
curl -fsSL -o data/raw/counterfact.json      https://memit.baulab.info/data/dsets/counterfact.json
curl -fsSL -o data/raw/zsre_mend_eval.json   https://memit.baulab.info/data/dsets/zsre_mend_eval.json
python src/build_dataset.py     # → data/{counterfact,zsre,mquake_cf_3k}.jsonl + data/aliases.json
```
（MQuAKE-CF-3k 随仓库克隆在 `source/MQuAKE/datasets/`。schema 与决策见 `analysis/06_data.md`。）

## 3. mom2 协方差统计（task#04，一次性/模型；约 4–6 GPU·h）

ROME/MEMIT 首次 `edit()` 会**自动**触发并缓存到 `stats_dir`。我们已把 R1-Distill 的 stats_dir
设为 `./data/stats_r1qwen`（与 Qwen2.5 分目录，**01 雷点 4**，勿混）。所以**不必单独跑** mom2——
跑 §4c 第一条 case 时自动算好；只是第一条会慢。若想预热，先用任意一条 case 单跑一次即可。

## 4. Pilot（关键路径，6/22 go/no-go）

配置在 `experiments/pilot.yaml`：R1-Distill-Qwen-7B × {ROME, MEMIT} × CounterFact-200 × {B0,B3,B4}。
`run_pilot.py` 会自动把 EasyEdit qwen2.5 yaml 的 `model_name` 改成 R1-Distill、`stats_dir` 分目录、按 rank 分卡——**不用手改 hparams**。

### 4a 预过滤（§2.3，先做，约 0.5–1 GPU·h）
只留「编辑前模型确实知道旧事实」的 case，否则「回退」无意义。
```bash
cd source/EasyEdit
PYTHONPATH=. python ../../src/prefilter.py --config ../../experiments/pilot.yaml --device 0
# → data/counterfact.prefiltered.jsonl（攒够 2×n=400 存活即停）
```
存活率预计 40–60%。`--budget B0` 更快但可能漏召；默认 B3（自然思考）最忠实。

### 4b layer 扫描（plan §7，**合格线 B0 下 ES≥90% & Locality≥85%**）
R1-Distill-Qwen-7B 基座是 Qwen2.5-**Math**-7B，现成 hparams 仅架构兼容。扫三组：
- 改 `experiments/pilot.yaml`：`editors.ROME.layers` 取 `[5]→[7]→[10]`（ROME 单层）；
  `editors.MEMIT.layers` 取 `[4,5,6,7,8]→[6,7,8,9,10]→[8,9,10,11,12]`。
- 每组先小样（如 n=50）跑 B0 看 efficacy(ES) 与 locality，过线再定。
- 选定后改回 `pilot.yaml` 定稿。

### 4c 跑 pilot（8 卡分片，约 4–6 GPU·h）
```bash
cd source/EasyEdit
for r in $(seq 0 7); do
  PYTHONPATH=. python ../../src/run_pilot.py --config ../../experiments/pilot.yaml \
      --editor ROME --rank $r --world 8 --device $r &
done; wait
# MEMIT 同理（换 --editor MEMIT）
for r in $(seq 0 7); do
  PYTHONPATH=. python ../../src/run_pilot.py --config ../../experiments/pilot.yaml \
      --editor MEMIT --rank $r --world 8 --device $r &
done; wait
```
- 产出：`results/pilot/r1qwen7b_{ROME,MEMIT}_cf200_r{r}of8.jsonl`（含完整 CoT，一等资产）。
- **可中断续跑**：jsonl 追加写、已完成 case_id 自动跳过；被杀了重跑同命令即可。
- 单条 case 出错只记 `{"error":...}` 并继续，不拖垮整片。

### 4d 打分（CPU 即可，本地或机器上都行）
```bash
python src/score_pilot.py --config experiments/pilot.yaml --editor ROME
python src/score_pilot.py --config experiments/pilot.yaml --editor MEMIT
```
输出每档 ES / RR / CLR。**口径纪律**：这是生成式 `ES_b`，**绝不与 EasyEdit 自带 `rewrite_acc`（logits 口径）混排**（CLAUDE.md 约束 4）。

### 4e go/no-go 判据（plan §Phase 1，硬节点 6/22）
两条同时满足才 go：① `RR(B3=natural)≥0.20` 或 ES 自 B0 的降幅 ≥20pp（至少一个编辑器成立、另一个方向一致）；② 抽 30 条回退样本人工审计，≥60% 可归因反思/自验证片段。
不成立 → 当日启 plan §9 fallback（沉没成本封顶 12 天）。

## 5. AlphaEdit（Phase 2 用前必做；pilot 不需要）

EasyEdit 内置 AlphaEdit 对 qwen 有崩溃 bug（P 预分配缺 qwen 分支）。**先预生成 P**绕过：
```bash
cd source/EasyEdit
PYTHONPATH=. python ../../src/vendor_patches/gen_alphaedit_P.py \
    hparams/AlphaEdit/qwen2.5-7b.yaml --device 0      # → ./null_space_project.pt
```
- 之后 AlphaEdit `apply_` 发现文件存在直接 load、跳过 bug。详见 `src/vendor_patches/README.md`、`analysis/02_alphaedit.md` §4。
- 接 AlphaEdit 进 `edit_loop` 时需每条 case `reset_cache=True`（cache_c 跨 case 累积，02 §5）。
- **超参口径**：内置 `L2=1` vs 官方 `L2=10`；做两实现对照时先对齐。

## 6. think_budget 真模型长度验证（task#07 part B）

```bash
WHYAAAI_MODEL=deepseek-ai/DeepSeek-R1-Distill-Qwen-7B \
  python src/test_think_budget.py --model deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --device cuda
```
验证 5 档（B0 空 / B1·B2·B3 截断 / B4 延长）在未编辑模型上的长度分布与不变量。

## 7.（可选）CPU 冒烟，补 task#03 的 `rewrite_acc`

之前被杀。GPU 机上更快：
```bash
cd source/EasyEdit && PYTHONPATH=. python ../../src/smoke_rome_gpt2.py   # 预期 rewrite_acc==1.0
```
跑通把数字回填 `analysis/01_easyedit.md` §6。

## 8. 雷点速查（一页）

| 坑 | 说明 |
|---|---|
| 全角竖线 `<｜User｜>` U+FF5C | 模板里勿替换成半角 `|`；代码已校验，手敲处要重验 |
| `PYTHONPATH=.` | easyeditor 本地包，否则 ModuleNotFoundError |
| stats_dir 分目录 | R1-Distill 用 `./data/stats_r1qwen`，勿与 Qwen2.5 混（run_pilot 已设） |
| model_name override | hparams 默认指向 Qwen2.5，run_pilot 自动改 R1-Distill |
| AlphaEdit qwen P + cache_c | §5：先 gen P；接入时 reset_cache |
| 预算档 5 档 B0–B4 | §9 已定（v1.12）；pilot 用 B0/B3/B4 |
| 口径不混 | 生成式 ES_b ≠ EasyEdit rewrite_acc |
| `finally restore` | edit_loop 已保证异常也还原，勿删 |

## 9. 预算档决议（v1.12 已结案，跑前无待拍板项）

**✅ 已结案（plan v1.12，用户取 B）**：预算档统一为 **5 档 B0–B4**，与 `src/think_budget.py` 一致（去掉独立 4096，natural≈B3 的 cap=8192）。`pilot.yaml` 用 `B0/B3/B4`（≈ 0/natural/extend）；主矩阵 5 档全给 MEMIT/AlphaEdit、ROME/FT-L 跑 B0/B3/B4（plan §5）。**跑前已无待拍板项。**

## 10. 产出回传与记录

- `results/`（CoT jsonl）已 gitignore；跑完把它带回本地后按需 commit（或只 commit 打分表）。
- 打分结果 + go/no-go 结论写进 `analysis/`（新建 pilot 结果笔记）+ 更新 `plan.md`（版本 +0.1、写变更）。
- `data/counterfact.prefiltered.jsonl`（pilot 实际用的 case 集）建议 commit，**钉死 pilot 集**便于复现。

---
*手册随 harness 变化更新；与 plan 冲突时以 plan.md 为准（唯一权威计划）。*
