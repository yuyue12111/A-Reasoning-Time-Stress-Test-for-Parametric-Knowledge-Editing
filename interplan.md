# interplan.md · 内网（启智平台）算力作战简报 —— 给内网侧 agent/执行者

> **你是谁、要干什么**：你在组内「启智」算力平台（qz.sii.edu.cn）一侧，手里有本仓库的完整拷贝。
> 你的任务：把 AAAI-27 项目「越想越退」的 **pilot 实验**（已在本地全链路验证过的现成脚本）在平台上跑完并把结果带回。
> **科学序列的权威是 `RUNBOOK.md`**（跑什么、按什么顺序、判什么合格线）；本文是它的**平台适配层**（启智上怎么开机器、怎么备料、表单怎么填）。两者冲突以 RUNBOOK/plan.md 为准。
> **读单**：本文 → `RUNBOOK.md` → `CLAUDE.md`（硬约束，必读）→ 卡住再查 `sumandplan1.md` §6.3 / `analysis/0x`。
> 平台细节出处：仓库根的两份组内教程《组内算力教程-交互式建模》《组内算力教程-分布式训练》（本文已蒸馏其要点，表单字段含义查原文）。

---

## 0. 任务背景（30 秒版）与成功判据

- 项目：量化参数知识编辑（ROME/MEMIT）在 R1 式推理模型上**随思考预算增加而被推翻**的现象。截止链上最近的硬节点是 **6/22 go/no-go**。
- 现状：**只欠 GPU 真跑**。harness 全部就位且经过本地真权重端到端验证（`analysis/08`）；三个会卡死窗口的 blocker 已离线修掉（qwen 路由、mom2 语料加载、采样/判分/溯源工具缺口）。
- **你的成功判据（按完成度递增）**：
  1. ✅ 最低：环境+模型+语料在平台上就位并通过离线自检（§3），单卡冒烟过（§4）——下个窗口随时能跑；
  2. ✅ 标准：mom2 + 预过滤 + layer 小扫 + **pilot 全量跑完**（§5），打分表出来（§6）；
  3. ✅ 完整：含 10% 边界校准 + 30 条回退审计材料，结果包回传（§7）。
- **不归你决定的事**：go/no-go 判定（用户拍板，plan §Phase 1 判据）；任何改 `plan.md` 的口径变更；花钱。

## 1. 启智平台速览（两教程蒸馏）

两种作业形态，怎么选：

| | 交互式建模 | 分布式训练 |
|---|---|---|
| 是什么 | Jupyter/VSCode 云 IDE，开箱即用 | 表单提交的批作业（shell 命令） |
| 用来做 | 备料/装环境/调试/单卡冒烟/CPU 打分 | **正式 8 卡跑**（mom2/扫层/pilot） |
| 入口 | 作业中心 → 交互式建模 → 新建 | 作业中心 → 分布式训练 → 新建训练任务 |
| 要点 | 镜像须含 Jupyter/VSCode；**低利用率会被自动回收** | 训练容错（失败自动重启 ≤10 次）、最大运行时长 |

**全局机制（两种作业通用）**：
- **网盘挂载**：每个项目下有「公共挂载 + 用户挂载」目录，**同项目所有实例/作业共享、持久化**（不靠保存镜像）。→ **仓库、模型、HF 缓存、results 全放这里**，实例被回收/作业被杀都不丢。
- **官方数据集**：表单里可勾选，容器内挂载于 `/inspire/dataset/<datasetid>/<versionid>`。
- **外网**：普通计算空间默认**无外网**；专门有一个 **「可上网 notebook-workspace」空间**，在那里的交互式实例 terminal 里可以 `curl`/`git clone`/`pip install`。→ 一切下载都在那边干。
- **优先级**：任务优先级 ≤ 所属项目优先级；**优先级 1–3 的任务可被高优任务打断**。选项目时表单会显示「单任务最大可用资源 / 优先级 / 项目剩余卡时」。
- **资源规则（分布式训练）**：1 节点可申请 1/2/4/8 卡；多节点必须每节点 8 卡。我们全部 **1 节点 × 8 卡**。
- **镜像**：官方镜像（如 `docker.sii.shaipower.online/inspire-studio/pytorch:25.06-py3`）/ 个人镜像（交互式实例里装好环境后「保存镜像」即得，下次任意作业可选）。
- **飞书通知**：表单里勾上「状态变更时进行飞书消息通知」——所有长作业都开。
- **OpenAPI（Alpha）**：可脚本化提交/查询/停止训练任务（§9），适合排队接力；不稳定，UI 为主。

**与我们设计的呼应**（为什么我们的脚本天然适配这平台）：
- jsonl 追加写 + 按 case_id 续跑 ⇄ 训练容错自动重启 / 被高优抢占 → **同命令重跑即续**，无脑安全；
- 单条 case 容错不拖垮分片 ⇄ 平台随时杀任务；
- 每分片首行溯源头（git hash/配置/seed）⇄ 多窗口、多作业拼接时审计来源。

## 2. 上场第一件事：现场核实清单（10 分钟，答案记进本文末尾「现场笔记」）

1. **项目配额**：新建表单里选你的项目，记下「单任务最大可用资源（GPU/CPU/内存）、可选优先级上限、剩余卡时」。GPU 型号（H200?）看资源规格下拉。**单任务最大 GPU <8 时，pilot 分片照常跑、world 改成对应卡数**（脚本支持任意 world）。
2. **官方数据集注册表**：搜有没有现成的 `DeepSeek-R1-Distill-Qwen-7B`（或 1.5B）模型与 `wikipedia` 类语料——**有就直接挂载，省 §3 的几十 GB 下载**（路径 `/inspire/dataset/...`，用法见 §3 末注）。
3. **网盘互通**：确认「可上网 notebook-workspace」里看到的挂载目录与你计算项目的挂载是否同一块（教程未明说）。**不通的话**：下载全部落在可上网侧 → 用平台文件管理/上传通道搬运，或问空间管理员要公共挂载。
4. **镜像清单**：官方镜像里挑 PyTorch ≥2.5 / python ≥3.10 的最新项（教程示例 `pytorch:25.06-py3` 即可）。
5. **优先级策略**：能选 ≥4 就选最高可选值（1–3 会被打断；打断不致命但浪费）。

## 3. Phase A · 备料（可上网 notebook-workspace，交互式建模，无 GPU/最小规格即可）

**表单速填**：实例名 `whyaaai-prep`；项目=可上网空间的项目；自动停止 8h；镜像=官方 PyTorch；Slurm **关**；飞书通知开。

> 持久化纪律：以下全部干在**网盘挂载目录**下（设 `$W` = 你的用户挂载根，如教程截图所示位置）。容器本地盘会随实例消失。

```bash
cd $W
# ① 仓库就位（本地已打包上传 git bundle 的话）：
git clone whyaaai.bundle why-aaai27 && cd why-aaai27
#    （或：本地侧把整个 why-aaai27 目录 tar 后经 notebook 上传按钮传入再解包；二选一）
# ② 第三方仓库（7 个浅克隆，幂等）：
bash setup_workspace.sh         # EasyEdit/AlphaEdit/R-TOFU/ThinkEdit/Unlearn-R2MU/MQuAKE/memit
# ③ 原始数据（若 data/ 未随包带来；带了就跳过）：
mkdir -p data/raw
curl -fsSL -o data/raw/counterfact.json    https://memit.baulab.info/data/dsets/counterfact.json
curl -fsSL -o data/raw/zsre_mend_eval.json https://memit.baulab.info/data/dsets/zsre_mend_eval.json
python src/build_dataset.py     # → data/{counterfact,zsre,mquake_cf_3k}.jsonl + aliases.json
# ④ Python 环境（pin 自 env.lock：torch2.9.1/transformers5.5.4/datasets4.8.5，无 mac 专属包）：
pip install -r env.lock         # 直接装进镜像环境；个别包冲突就放过它再补装核心四件
pip download -r env.lock -d $W/wheels   # 离线轮子备份（环境丢了能无网重装）
# ⑤ HF 资产（缓存全部指到网盘）：
export HF_HOME=$W/hf
python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download("deepseek-ai/DeepSeek-R1-Distill-Qwen-7B")    # ~15GB，主模型
snapshot_download("deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B")  # ~3.6GB，冒烟备用（可选）
PY
# ⑥ mom2 语料（MEMIT 必需；ROME 不需要）。注意：EasyEdit 原始 id 在 datasets≥3 已死，
#    仓库的 vendor_patch 会自动把它映射到 wikimedia/wikipedia/20231101.en（详见
#    src/vendor_patches/README.md §3）。这里预下载的就是映射后的目标（~20GB，耐心）：
python - <<'PY'
from datasets import load_dataset
ds = load_dataset("wikimedia/wikipedia", "20231101.en", split="train")
print("wikipedia rows:", len(ds))
PY
# ⑦ 离线自检（模拟计算空间无外网；全过才算备料完成）：
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
python - <<'PY'
from transformers import AutoTokenizer
from datasets import load_dataset
tok = AutoTokenizer.from_pretrained("deepseek-ai/DeepSeek-R1-Distill-Qwen-7B")
assert tok("</think>", add_special_tokens=False)["input_ids"] == [151649]
ds = load_dataset("wikimedia/wikipedia", "20231101.en", split="train")
print("OFFLINE OK", len(ds))
PY
# ⑧ 仓库自带 mock 测全过（无 GPU）：
for t in metrics edit_loop run_pilot; do python src/test_$t.py; done
python src/vendor_patches/test_qwen2_loader.py && python src/vendor_patches/test_mom2_dataset.py
python src/test_think_budget.py && python src/test_steer.py     # 这俩要 torch
```
**收尾**：实例停止时选「**保存镜像并停止**」→ 得到带全套依赖的个人镜像 `whyaaai-env`（后续所有作业直接选它，pip 那步永久免做）。
> §2-2 查到官方数据集已有模型/语料时：跳过对应下载，改在运行命令里 `export HF_HOME=...` 前用 `ln -s /inspire/dataset/<id>/<ver>/... $W/hf/...` 或直接把 `model_name` override 指到挂载路径（`experiments/pilot.yaml` 的 `hparams_overrides.model_name` 改成绝对路径即可）。

## 4. Phase B · 单卡冒烟（计算项目，交互式建模，1×GPU，预算 ≤2h）

**表单速填**：实例名 `whyaaai-smoke`；项目=计算项目；镜像=`whyaaai-env`；规格=1 GPU；自动停止 4h；Slurm 关；飞书开。

```bash
cd $W/why-aaai27 && export HF_HOME=$W/hf HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
# ① 预算控制器 7B 全量档长度分布（task#07 欠的 H200 件，顺手清）：
python src/test_think_budget.py --model deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --device cuda
# ② 参数编辑端到端冒烟（2 条 ROME，走与 pilot 完全相同的 edit_loop 路径，含两个 vendor patch）：
PYTHONPATH=source/EasyEdit python src/rome_mps_probe.py \
    --model deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --device cuda:0 --cases 2 --budgets B0 --fresh
#    期望：错误行=0；看逐 case 是否 ES（7B 生成式 B0 能不能编进去——layer 扫的前哨）。
#    注：该脚本用缩减思考上限（768），对 B0 无影响；正式 pilot 走 run_pilot 用全量 CAP。
# ③ mom2 预热（⚠️ 必须单进程先跑！8 进程并发首跑会同时触发 ~6 GPU·h 的协方差计算，浪费且可能写坏缓存）：
cd source/EasyEdit
PYTHONPATH=. python ../../src/run_pilot.py --config ../../experiments/pilot.yaml \
    --editor MEMIT --rank 0 --world 200 --device 0
#    world=200 → 本进程只分到 1 条 case；首条 MEMIT edit 自动算 mom2 并缓存到 data/stats_r1qwen（一次性，~6 GPU·h）。
#    跑完删掉这个热身分片（避免与正式 8 分片混入打分 glob）：
rm ../../results/pilot/r1qwen7b_MEMIT_cf200_r0of200.jsonl
```
②或③出错即停：把完整 traceback 存 `$W/why-aaai27/results/incident_<日期>.log`，回报（§10）。

## 5. Phase C · 正式跑（分布式训练，1 节点 × 8 卡）

**表单速填**（每个子作业同模板）：计算类型组=§2-1 所记；项目=计算项目；**训练容错=开**；最大运行时长=见各步；框架=PyTorch；镜像=`whyaaai-env`（个人可见）；节点=1；GPU=8；CPU/内存=项目允许的上限或默认；共享内存 ≥16GB；飞书开；优先级=§2-5 所定。**执行命令**=下方各步命令块（整段贴入，行首加 `set -e` 已含）。

> 被抢占/容错重启/超时都不用慌：**同命令重跑即续跑**（done 集合自动跳过已完成 case）。
> 顺序照 RUNBOOK §4：预过滤 → layer 小扫 → pilot。mom2 已在 §4-③ 预热。

**步骤 C1 · 预过滤**（任务名 `whyaaai-prefilter`，时长上限 2h，其实单卡活、8 卡里只用 dev0）：
```bash
set -e; cd $W/why-aaai27/source/EasyEdit
export HF_HOME=$W/hf HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PYTHONPATH=. python ../../src/prefilter.py --config ../../experiments/pilot.yaml --device 0
# → data/counterfact.prefiltered.jsonl（攒够 2×n=400 存活即停；存活率预期 40–60%）
```

**步骤 C2 · layer 小扫**（任务名 `whyaaai-scan-<cfg>`，每组时长上限 3h；判据=**生成式 ES≥0.90 & Loc≥0.85 @B0**，详见 RUNBOOK §4b——**绝不用 rewrite_acc 判**）：
```bash
# 先在交互式实例里准备 6 份扫描配置（n=50、budgets 只留 [B0]、改 layers、out_dir 分开）：
#   cp experiments/pilot.yaml experiments/scan_rome_l5.yaml   # 然后编辑：
#   dataset.n: 50 ; budgets: [B0] ; out_dir: results/scan_rome_l5 ; editors.ROME.layers: [5]
#   ROME 扫 [5]/[7]/[10]；MEMIT 扫 [4-8]/[6-10]/[8-12]（见 RUNBOOK §4b）
set -e; cd $W/why-aaai27/source/EasyEdit
export HF_HOME=$W/hf HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
for r in $(seq 0 7); do
  PYTHONPATH=. python ../../src/run_pilot.py --config ../../experiments/scan_rome_l5.yaml \
      --editor ROME --rank $r --world 8 --device $r &
done; wait
cd ../.. && python src/score_pilot.py --config experiments/scan_rome_l5.yaml --editor ROME --boot 0
```
六组都打完分 → 选过线 layers 写回 `experiments/pilot.yaml` 定稿（没有任何一组过线 → **停**，按 §10 上报：plan 风险表预案是调 `v_lr/v_num_grad_steps` 或退 Qwen2.5-7B-Instruct，要用户知情）。

**步骤 C3 · pilot 主跑**（任务名 `whyaaai-pilot-rome` / `-memit`，各时长上限 8h；两个作业可先后提交排队）：
```bash
set -e; cd $W/why-aaai27/source/EasyEdit
export HF_HOME=$W/hf HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
for r in $(seq 0 7); do
  PYTHONPATH=. python ../../src/run_pilot.py --config ../../experiments/pilot.yaml \
      --editor ROME --rank $r --world 8 --device $r &
done; wait
# MEMIT 作业同款，--editor MEMIT
```
产出：`results/pilot/r1qwen7b_{ROME,MEMIT}_cf200_r{r}of8.jsonl`（含完整 CoT——**一等资产**，丢了等于重烧卡时）。
首窗 greedy 主口径即可（`pilot.yaml` 的 `sampling.enabled=false` 保持默认）；窗口富余再开 `true` 补 0.6×3 采样臂（产出行带 `decode=sample`，打分自动分臂）。

## 6. Phase D · 打分 + 校准 + 审计（CPU，交互式实例或本地皆可）

```bash
cd $W/why-aaai27
python src/score_pilot.py --config experiments/pilot.yaml --editor ROME    # 默认 --boot 10000 出 95% CI
python src/score_pilot.py --config experiments/pilot.yaml --editor MEMIT
```
- 表头 `ES/ESf/RR/CLR/Flip/PS/Loc`+CI；口径解读已印在输出里。**ES_b 是生成式口径，与 EasyEdit 日志里的 rewrite_acc 永不混排**（CLAUDE.md 约束 4）。
- **10% 边界校准**：照 `analysis/09_flippoint_calibration.md` §3 逐步执行（选边界样本→人工三分类→必要时补 aliases 重打分），产出 `results/pilot/calibration_<editor>.md`。
- **30 条回退审计**：从 RR 命中的 case 里抽 30 条，逐条记：case_id / budget / FlipPoint（`metrics.flip_analysis` 的 flip_pos）/ 触发片段类型（反思「wait/check」类？关联检索类？其它）/ 一句话归因。这是 go/no-go 判据②的直接材料。

## 7. 回传与上报

**带回清单**（打成 `whyaaai-results-<日期>.tar.gz` 经平台下载/传输通道带出）：
`results/pilot/*.jsonl`（全部分片，含溯源头）｜`data/counterfact.prefiltered.jsonl`（**钉死 pilot 集**，必须带）｜两张打分表（文本即可）｜`calibration_*.md`｜审计 30 条记录｜若内网侧改过代码：`git bundle create whyaaai-back.bundle main`（内网照常 git commit，规范同 CLAUDE.md）。
**上报格式**（飞书给用户）：① 两编辑器打分表+CI 原样贴；② layer 扫结论（选了哪组、各组 ES/Loc）；③ 审计 30 条的归因比例（反思片段占比 ≥60%?）；④ 卡时消耗；⑤ 异常清单。**不替用户下 go/no-go 结论**，只摆判据材料（plan §Phase 1：RR(B3)≥0.20 或 ES 降幅≥20pp，且审计归因≥60%）。

## 8. 雷点合订（平台 × 项目，违反必翻车）

| 雷 | 处置 |
|---|---|
| 计算空间无外网 | 一切下载在「可上网 notebook-workspace」干完（§3）；计算作业全程 `*_OFFLINE=1` |
| 交互式实例低利用率自动回收 | 重物全放网盘挂载；停止时保存镜像；长下载挂 `nohup`+及时回来看 |
| 优先级 1–3 可被打断 | 尽量选 ≥4；被打断同命令重跑即续 |
| **mom2 并发首跑** | **必须 §4-③ 单进程预热后再开 8 分片**；热身分片 jsonl 记得删 |
| mom2 语料 id 在 datasets≥3 已死 | vendor_patch 自动映射 `wikimedia/wikipedia/20231101.en`（edit_loop 自动接入；`gen_alphaedit_P.py` 等新入口须先手动 `apply()`，见 vendor_patches/README §3） |
| qwen 路由 bug（fp32 TypeError） | vendor_patch 已自动接入（README §2）；任何**绕过 edit_loop** 手动 `BaseEditor.from_hparams` 的脚本须先 `vendor_patches.easyedit_qwen2_loader.apply()` |
| 合格线口径 | layer 扫/编辑质量一律看 `score_pilot` 的生成式 `ES`/`Loc`，**不看 rewrite_acc**（`analysis/08`：6/8 vs 0/8 脱节实证） |
| `source/` 只读 | 永不直接改；要改走 `src/vendor_patches/`+记录（CLAUDE.md 约束 3） |
| 全角竖线 | 模板 `<｜User｜>` 是 U+FF5C；任何手敲/复制处重验 |
| `finally: restore` | `edit_loop` 的还原逻辑不许动 |
| stats_dir 相对路径 | 相对 cwd（=source/EasyEdit）解析 → 实际落 `source/EasyEdit/data/stats_r1qwen`，在网盘上即持久；勿与 Qwen2.5 的 stats 混目录 |
| 环境漂移 | 若被迫改依赖版本：`pip freeze > env.cluster.lock` 一并带回，并在上报里注明 |

## 9. OpenAPI 速查（可选；Alpha，UI 为主，排队接力时用）

```bash
# 取 token（凭证向用户要，不要写进任何文件/历史）：
curl -sX POST https://qz.sii.edu.cn/auth/token -d '{"username":"<u>","password":"<p>"}'
# 提交训练任务（spec_id 获取技巧：先在 UI 建一个 demo 任务，用 detail 接口读它的 quota_id 即 spec_id）：
curl -sX POST https://qz.sii.edu.cn/openapi/v1/train_job/create -H 'Authorization: Bearer <token>' -d '{
  "name":"whyaaai-pilot-rome","logic_compute_group_id":"<lcg-…>","project_id":"<project-…>",
  "auto_fault_tolerance":true,"framework":"pytorch","command":"<§5 的命令块>","task_priority":4,
  "workspace_id":"<ws-…>","framework_config":[{"image":"<whyaaai-env 镜像名>","image_type":"SOURCE_PRIVATE",
  "instance_count":1,"shm_gi":16,"spec_id":"<spec-…>"}]}'
# 查询 / 停止：
curl -sX POST https://qz.sii.edu.cn/openapi/v1/train_job/detail -H 'Authorization: Bearer <token>' -d '{"job_id":"job-…"}'
curl -sX POST https://qz.sii.edu.cn/openapi/v1/train_job/stop   -H 'Authorization: Bearer <token>' -d '{"job_id":"job-…"}'
```

## 10. 卡住了怎么办（升级路径）

1. **自己先试**：平台报错查任务「事件/聚合日志」（资源不足→换规格/等队；镜像错→回 §3 重保存）；脚本报错对照 §8 雷点表与 `RUNBOOK.md` §8。
2. **可自主决定**：续跑/重试、换等价资源规格、调作业切分粒度、layer 扫顺序。
3. **必须上报用户（飞书）**：layer 扫全不过线（带各组 ES/Loc 表）；任何要改 `plan.md`/协议/口径的事；要花钱的事；预计赶不上 6/22 的风险。
4. 报障带上：作业 ID、`results/incident_*.log`（完整 traceback）、复现命令、当时的 git hash（`git -C $W/why-aaai27 rev-parse HEAD`）。

---

## 现场笔记（你来填）

- 项目名/ID：｜计算类型组：｜GPU 型号与单任务上限：｜剩余卡时：｜优先级上限：
- 官方数据集命中：模型 ☐ 有 ☐ 无（路径：）；wikipedia ☐ 有 ☐ 无（路径：）
- 可上网空间与计算项目网盘 ☐ 互通 ☐ 不互通（搬运方式：）
- `$W` 实际路径：｜镜像名：`whyaaai-env` = 
- 各步实际耗时/卡时：

*本文落笔 2026-06-12（HEAD `5b4c2ef`，plan v1.15）。蒸馏自仓库根两份组内教程；平台行为以现场实测为准，发现教程过时请回填本文并 commit。*
