# qz_quickstart.md · 切到内网后照这个走（人工操作·交互式建模/Jupyter）

> **给谁**：你（人，在启智 qz.sii.edu.cn 前面点鼠标）。**目标**：切到内网后，按本文从登录到「环境就位、能开跑」一次走通，不用再翻别的。
> **关系**：本文只讲**平台 UI 怎么操作**（建实例、上传、Jupyter 终端、保存镜像）；具体跑实验的命令序列在 `interplan2.md`（§3 冒烟 / §4 正式跑）+ `RUNBOOK.md`。先按本文把环境弄好，再进那两份。
> **手上的料**（Mac `_upload/` 已打包好，等你搬上平台）：

| 文件 | 大小 | 是什么 |
|---|---|---|
| `why-aaai27.tar.gz` | 185M | 整个项目（代码+source 七仓+数据+论文+根 .git，已验证解开即可用） |
| `models-7B.tar.gz` | 11G | DeepSeek-R1-Distill-Qwen-7B 主模型 |
| `wheels/`（100 个 .whl） | 279M | 平台离线装 Python 包用（已修正 pyarrow/antlr/av，平台 py3.12 适配） |
| `MANIFEST.sha256` | 12K | 上传完整性校验（解包前先核） |

---

## 第 0 步 · 心里有数（平台 3 个铁律）

1. **完全无外网**：平台连不了 HuggingFace/PyPI——所以上面 4 个文件必须**全靠上传**，装包靠 `wheels/`，模型/语料靠挂载或上传。
2. **网盘目录持久、其它会丢**：每个项目有「用户挂载」目录（你的是 `$W = /inspire/qb-ilm/project/ai4education/ky26140`，529T）。**只有放这里的东西，实例被回收/停掉都不丢**；容器里别处写的东西，实例一停就没。→ 所有东西都放 `$W` 下。
3. **实例闲置会被自动回收**：交互式建模实例利用率低会被平台自动停。长下载/长任务别开着走人；停止时记得「保存镜像」。

---

## 第 1 步 · 登录 + 把 4 个文件传到平台

1. 浏览器开 **qz.sii.edu.cn**，登录（空间：教育大模型-独立空间）。
2. **先建一个最小的交互式建模实例当「搬运+解包工」**（见第 2 步，GPU 选「无」或最小规格即可，省卡时）。
3. 实例跑起来后进 Jupyter（第 3 步），用**上传按钮**或平台**文件管理**把 4 个文件传到 `$W`：
   - 小的先传：`why-aaai27.tar.gz`(185M)、`wheels/`整目录、`MANIFEST.sha256`。
   - **`models-7B.tar.gz`(11G) 最后传**：浏览器上传大文件易断。**先试传一个小文件确认通道没问题**；若平台单文件上限 <11G（传到一半失败），回 Mac 把它切片再传：
     ```bash
     # Mac _upload/ 下切 5G 一片：
     split -b 5G models-7B.tar.gz models-7B.tar.gz.part_
     # 平台上传所有 part_ 后，在 $W 里合回去：
     cat models-7B.tar.gz.part_* > models-7B.tar.gz && rm models-7B.tar.gz.part_*
     ```
   > 上传中可在 Jupyter Notebook 页面底部看进度，显示 "Complete!" 才算完。

---

## 第 2 步 · 新建交互式建模实例（Jupyter）—— 表单逐字段填

**作业中心 → 交互式建模 → 右上角「新建交互式建模」**，右侧抽屉表单：

**第一部分·基本信息**
| 字段 | 第一次（搬运/装环境实例） | 说明 |
|---|---|---|
| 实例名称 | `whyaaai-prep` | 小写字母/数字/短横线，字母开头，空间内唯一 |
| 所属项目 | 你的项目 | 实例产生的文件存这个项目下；**记下表单里显示的「单任务最大可用资源 / 优先级上限 / 剩余卡时」** |
| 自动停止策略 | 开，设 **8 小时** | 防忘关浪费；不够再续 |

**第二部分·资源配置**
| 字段 | 第一次填 | 说明 |
|---|---|---|
| 镜像 | **官方镜像** → PyTorch 最新项（如 `pytorch:25.06-py3`） | 第一次用官方镜像装环境；装好后保存成个人镜像 `whyaaai-env`，以后都用它 |
| 计算类型组 | 选有可用资源的组 | 资源不足会一直排队 |
| 计算资源规格 | **无 GPU 或最小规格** | 搬运/解包/装包/CPU 自检不需要 GPU，省卡时；正式跑才要 GPU |
| 共享内存 | 16G 左右 | 不超过实例内存 |
| 启用 Slurm 调度 | **关** | 机器学习任务不用 |
| 状态变更飞书通知 | **开** | 实例起来/失败会推飞书 |
| 任务优先级 | 选能选的**最高**（≥4 最好） | 1–3 会被高优任务打断 |

**第三部分·官方数据集**（重要，可省传 11G 模型）
- 在数据集挂载里**搜 `DeepSeek` / `Qwen`**：若平台已有 R1-Distill-Qwen-7B，勾上它（容器内路径 `/inspire/dataset/<id>/<ver>`），就**不用传 11G 模型**了（第 4 步的模型路径改指这里）。
- `wikipedia` 语料平台已挂在 `/inspire/dataset/wikipedia/20231101/`，**不用动**（我们的补丁会自动找到它）。

点「新建」→ 实例进入排队/创建/运行。状态变「运行中」后进第 3 步。

---

## 第 3 步 · 进 Jupyter，认准两样东西

1. 实例列表里点你的实例 → 打开 **Jupyter Notebook**（或 VSCode，随你）。右上角能看 CPU/内存/GPU 实时占用。
2. **开终端**：Jupyter 右上角 New → **Terminal**（VSCode 则 Terminal → New Terminal）。后面所有命令都在这里敲。
3. **认准网盘目录**：你的持久目录 `$W = /inspire/qb-ilm/project/ai4education/ky26140`。`cd $W` 看看上传的文件在不在。**所有解包、装环境、跑实验都在 `$W` 下做**（容器别处会丢）。
4. **上传按钮**：Jupyter 文件浏览器左上角有上传图标，用它把第 1 步那 4 个文件传到 `$W`（大文件按第 1 步处理）。

---

## 第 4 步 · 解包 + 装环境 + 自检（终端里逐段粘，全过才算就位）

```bash
W=/inspire/qb-ilm/project/ai4education/ky26140
cd $W

# ① 校验完整性（应全部 OK；有 FAILED 说明上传损坏，重传那个文件）
sha256sum -c MANIFEST.sha256

# ② 解包（tar 不带外层目录，先建目录）
mkdir -p $W/why-aaai27 $W/models
tar xzf why-aaai27.tar.gz -C $W/why-aaai27
tar xzf models-7B.tar.gz  -C $W/models          # → $W/models/DeepSeek-R1-Distill-Qwen-7B

# ③ 离线装 Python 环境（只认 env.platform.lock，别用 env.lock！torch 用镜像自带的）
cd $W/why-aaai27
python -m pip install --no-index --find-links $W/wheels -r env.platform.lock
python -m pip freeze > env.qz.lock              # 平台实际环境留档，跑完随结果带回

# ④ 离线开关（写进以后每个跑命令的开头，强制不连网）
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1

# ⑤ 自检五连（全 OK 才进下一步；任何一步报错把整段输出留好）
python -c "import torch,transformers,datasets,pyarrow;print('VER',torch.__version__,transformers.__version__,datasets.__version__,pyarrow.__version__)"
python -c "from transformers import AutoTokenizer;t=AutoTokenizer.from_pretrained('$W/models/DeepSeek-R1-Distill-Qwen-7B');assert t('</think>',add_special_tokens=False)['input_ids']==[151649];print('MODEL OK')"
python -c "import sys;sys.path.insert(0,'src');from vendor_patches.easyedit_mom2_dataset import local_wiki_files as f;fs=f();print('WIKI OK',len(fs) if fs else 0,'shards')"
for t in metrics edit_loop run_pilot; do python src/test_$t.py; done
python src/vendor_patches/test_qwen2_loader.py && python src/vendor_patches/test_mom2_dataset.py
python src/test_think_budget.py && python src/test_steer.py
```
- ③ 若个别包装报错：看是不是 torch 相关（torch 用镜像 2.8，env.platform.lock 已不含 torch，正常）；其它包报错把名字记下。
- ⑤ 的 `WIKI OK` 应显示约 **41 shards**（平台已挂 wikipedia）；显示 0 说明挂载路径不同 → `export WHYAAAI_WIKI_PARQUET=<实际 parquet 目录>` 再试。
- **模型路径接线**：编辑 `experiments/pilot.yaml`，把 `hparams_overrides.model_name` 改成
  `/inspire/qb-ilm/project/ai4education/ky26140/models/DeepSeek-R1-Distill-Qwen-7B`
  （若第 2 步勾了官方数据集模型，就改成那个 `/inspire/dataset/...` 路径）。

---

## 第 5 步 · 保存镜像，以后免装环境

自检全过后，**停止这个实例时选「保存镜像并停止」**，命名 **`whyaaai-env`**。
以后建任何实例（冒烟、正式跑）都在「镜像」里选 `whyaaai-env`（个人可见镜像）——第 4 步的 ③ 装环境就永久免做了。

---

## 第 6 步 · 开跑（到这就「能跑」了）

环境就位后照 `interplan2.md`：
- **单卡冒烟**（interplan2 §3）：再建一个交互式实例，镜像选 `whyaaai-env`、规格 **1 GPU**，跑 7B 长度分布 + 2 条 ROME 端到端 + **mom2 单进程预热**（⚠️ 必须单进程先跑，别 8 卡并发，否则重复算 6 小时协方差）。
- **正式 8 卡跑**（interplan2 §4 / RUNBOOK §4）：用**分布式训练**作业（不是交互式建模），1 节点×8 卡，预过滤 → layer 小扫 → pilot。命令块整段贴进作业表单的「执行命令」。
- **打分/审计/回传**（interplan2 §5）：CPU 即可，交互式实例里跑 `score_pilot.py`。

被打断/超时/被抢占都不怕：**同命令重跑即自动续跑**（已完成的 case 自动跳过）。

---

## Jupyter 平台·常用操作速查

| 想干啥 | 怎么做 |
|---|---|
| 开终端 | Jupyter: New → Terminal；VSCode: Terminal → New Terminal |
| 传文件 | Jupyter 文件浏览器左上「上传」图标；底部看进度到 "Complete!" |
| 看资源占用 | 实例界面右上角（CPU/内存/GPU 实时） |
| 实例被自动回收了 | 重物都在 `$W` 网盘不丢；重新「启动」已停实例，或新建选 `whyaaai-env` 镜像 |
| 保存当前环境 | 停止时选「保存镜像并停止」；或运行中手动「保存镜像」（另存为，下次需在编辑里手动选） |
| 切换/查看实例镜像 | 实例「已停止」状态下点「编辑」可换镜像 |
| 大文件下载（仅可上网空间，本平台无） | 本平台无外网，忽略教程里的 curl 下载法 |
| 看 GPU 任务进度 | 分布式训练作业：详情页「实例/日志/资源视图」；交互式：终端里看脚本 stdout |

---

## 卡住了

1. 先看实例/作业的「事件」「日志」（资源不足→换规格/等队；ImportError→第 4 步③重装或记包名）。
2. 复现性证据：留好报错整段 + `git -C $W/why-aaai27 rev-parse HEAD`（应为 `ddfcfeb` 或之后）。
3. 要改实验口径/协议、或赶不上 6/22、或要花钱 → 飞书找用户拍板（别自己改 `plan.md`）。
4. 详细雷点表见 `interplan2.md` §6 + `interplan.md` §8。

---
*Mac `_upload/` 打包于 2026-06-13（HEAD `ddfcfeb`，plan v1.17）。本文＝人工 UI 操作；实验命令在 interplan2.md/RUNBOOK.md。*
