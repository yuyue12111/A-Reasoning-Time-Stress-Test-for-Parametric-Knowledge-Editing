# interplan2.md · 启智**全离线**部署作战 v2 —— 给内网侧 agent/执行者

> 👤 **人工操作（登录/上传/建 Jupyter 实例/保存镜像）看 [`qz_quickstart.md`](qz_quickstart.md)**——那份是「切到内网照着点鼠标」的快速上手；本文是给 agent/执行者的技术作战层（Mac 打包细节 + 平台命令序列 + 雷点）。两者内容不重复、互指。
> **本文取代 `interplan.md` 的 §2–§7**（现场摸底推翻了 v1 的关键假设）；v1 仍有效的部分：§1 平台机制速览、§9 OpenAPI、§10 升级路径。科学序列权威照旧是 `RUNBOOK.md`，硬约束照旧 `CLAUDE.md`。
> **变了什么**：v1 假设存在「可上网 notebook-workspace」可在线备料——**现场证实整个平台完全无外网（HF/PyPI 全不通）**。部署改为**全离线**：Mac 侧打包 → 平台上传 → 解包落环境。现场实测全记录在 `report.md`（本文的事实基础，HEAD `5b4c2ef` 时点）。
> 读单：本文 → `report.md`（平台实测）→ `RUNBOOK.md`（跑什么/什么顺序/什么合格线）→ `CLAUDE.md`。

---

## 0. 态势速览（已核实事实，本节即真源）

**平台（report §1）**：

| 项 | 值 |
|---|---|
| 空间/挂载 | 教育大模型-独立空间；`$W = /inspire/qb-ilm/project/ai4education/ky26140`（可用 529T） |
| 外网 | **完全无**（两种作业形态都没有；v1 的「可上网空间」不存在） |
| 基础镜像 | 已存为 **`whyaaai-base`**：python 3.12.3 + torch 2.8.0a0+nv25.6 + CUDA 12.9 + git 2.43；pip 包近裸机 |
| Wikipedia | **平台已挂载** `/inspire/dataset/wikipedia/20231101/20231101.en/train-*-of-00041.parquet`（41 分片，正是我们 mom2 要的 dump）→ **不用上传 20GB 语料** |
| 模型 | 平台**没有** R1-Distill（注册表还没搜过——上场先搜，命中可省 11GB 上传，见 §6-④） |

**资产就位状态（Mac 侧）**：

| 资产 | 状态 |
|---|---|
| `_upload/models-7B.tar.gz` + `_upload/model_parts/` | ✅ 11.3GB 整包 + **6×2G 分片(part_aa..af)+PARTS.sha256**（整包上传实测**静默损坏**→必走分片逐片校验，§1-④/§2） |
| `_upload/wheels/`（cp312 linux） | ✅ **已修正**（100 wheel：pyarrow 24/antlr 4.9.3/av 17.1/opencv-headless 4.13；§1-② 三处坑已解，实测验证） |
| `env.platform.lock` | ✅ **已生成并入库**（repo 根，100 包；平台装环境**只认它**，别用 env.lock） |
| `_upload/why-aaai27.tar.gz` | ✅ 185M（含根 `.git`+source 七仓+数据+论文+qz_quickstart；HEAD `ab07da5`；已验证解开即用） |
| mom2 补丁离线分支 | ✅ 本轮已修：`vendor_patches/easyedit_mom2_dataset.py` **v2** 自动探测 `/inspire/dataset/wikipedia/...` 本地 parquet 直读、完全不碰 HF hub（report §7 问题 A 的修复；env `WHYAAAI_WIKI_PARQUET` 可显式指路径） |
| 1.5B 模型 | ⬜ 可选（3.6GB；只为平台上做小模型对照，pilot 不需要） |

**与 v1 的差异一览**：备料阶段从「平台可上网实例里下载」全部改到 Mac；环境从「pip install -r env.lock」改为「离线 wheels + env.platform.lock」；wiki 从「HF 下载」改为「平台挂载直读（patch v2）」；模型接线从 HF 缓存改为**绝对路径 override**。

## 1. Mac 侧收尾（上传前必做；有网环境）

### ① 仓库打包（修正 report 步骤 A：保留根 .git）
```bash
cd /Users/whyu/GitProjects/why-aaai27
# 预检：source/ 七仓齐全（report 问题 C 是虚惊——本仓 source/ 一直完整，仍留此一行防呆）
ls source/EasyEdit/easyeditor source/AlphaEdit source/R-TOFU source/ThinkEdit \
   source/Unlearn-R2MU source/MQuAKE/datasets source/memit >/dev/null && echo SOURCE-OK
tar czf _upload/why-aaai27.tar.gz \
    --exclude='./source/*/.git' --exclude='./_upload' --exclude='./.obsidian' \
    --exclude='__pycache__' --exclude='*.pyc' --exclude='.DS_Store' \
    --exclude='./results' --exclude='./logs' --exclude='./whyaaai.bundle' .
```
要点：**根 `.git` 必须在包里**（平台侧 jsonl 溯源头 `git -C` 取 hash、跑完照常 commit、回传用 `git bundle`）；`source/*/.git` 剔除（几百 MB 且无用——EasyEdit 等的 HEAD 已记录在各 analysis 笔记）；`data/`（raw 51MB + 清洗 jsonl 26MB）与 `papers/` 随包带走，平台免再生。

### ② wheels 修正三件 — ✅ **已在 Mac 侧执行并验证**（2026-06-12，结果已落 `_upload/wheels/` + `env.platform.lock`）
执行结果：pyarrow 24.0.0 ✅、antlr4 4.9.3 ✅、av 17.1.0 + opencv-python-headless 4.13 ✅（共 **100 wheel**）。
重做命令（仅当需重建 wheels 时）：
```bash
cd /Users/whyu/GitProjects/why-aaai27/_upload
rm -f wheels/pyarrow-20*.whl wheels/antlr4_python3_runtime-4.1[0-9]*.whl
pip download pyarrow==24.0.0 --platform manylinux_2_28_x86_64 --python-version 312 \
    --implementation cp --only-binary=:all: --no-deps -d wheels/
pip wheel antlr4-python3-runtime==4.9.3 --no-deps -w wheels/        # 纯 py，sdist→py3-none-any
pip download av opencv-python-headless --platform manylinux_2_28_x86_64 --python-version 312 \
    --implementation cp --only-binary=:all: --no-deps -d wheels/    # 不锁版本：import-only，新版有 abi3 wheel
```

| 修正 | 为什么必须（均已核实） |
|---|---|
| pyarrow 20.0.0 → **24.0.0** | `datasets==4.8.5` 硬性要求 **`pyarrow>=21.0.0`**（dist-info 实查）；20.0.0 装上 `import datasets` 即崩。上轮误降级根因=`--platform manylinux2014` 太老（pyarrow≥21 只发 manylinux_2_28 wheel）。⚠️ report §8.2「24.0.0 不存在于 PyPI」系误诊——实测 24.0.0 在 PyPI 且有 cp312 manylinux_2_28 wheel |
| antlr4 4.13.2 → **4.9.3** | `omegaconf==2.3.0` 硬锁 `antlr4-python3-runtime==4.9.*`（实查 requires）；4.9.3 仅 sdist 无 wheel（故 `--only-binary` 上轮抓了 4.13）→ 本地 `pip wheel` 从 sdist 打纯 py wheel |
| av **17.1.0** + opencv-headless **4.13** | `import easyeditor` 经 `dataset/__init__→coco_caption→blip_processors→randaugment` **eager import av+cv2**（实测：屏蔽任一则 `from easyeditor import BaseEditor` 即 ImportError）。但三个 processor 模块对 av/cv2 **无模块级 API 调用**（实查）+ pilot 文本路径从不实例化 VLM processor → **任何可 import 的版本即可**，故取有 cp312/abi3 wheel 的新版（env.lock 的 14.2.0/opencv-python 无 cp312 manylinux_2_28 wheel）。headless 变体免 libGL，更适合无显示 GPU 节点 |

### ③ `env.platform.lock` — ✅ **已生成并随仓提交**（100 包，repo 根）
平台安装清单（由 wheels 实况生成 + 平台预装件/版本偏差说明）。**装环境只认它，别用 env.lock**（后者是 Mac/py3.10 口径、torch pin 2.9.1 装不上）。重新生成法见仓库 `env.platform.lock` 头注。
> commit 后须重跑 ①的 tar，让包里带上 `env.platform.lock` 与最新 HEAD。

### ④ 校验和 + 模型分片 — ✅ **已生成**（11G 整包上传实测会**静默损坏**，故模型必走分片）
- `MANIFEST.sha256`（repo tar + model tar + 100 wheel 的 sha256，平台解包前 `sha256sum -c` 总校验）。
- `_upload/model_parts/`：`models-7B.tar.gz` 切成 **6 个 2G 片 `part_aa..af` + `PARTS.sha256`**（Mac 已验 `cat` 还原 byte 级一致）。
  分片的意义：坏了能定位到 2G 的片、**只重传那片**，不赌 11G 一次成功。重建法：`cd _upload && split -b 2000m models-7B.tar.gz model_parts/models-7B.tar.gz.part_ && cd model_parts && shasum -a256 *.part_* > PARTS.sha256`。

### ⑤ 最终上传清单 → 目标皆 `$W`
| 文件 | 大小 | 平台落点 |
|---|---|---|
| `why-aaai27.tar.gz` | 185M | 解到 `$W/why-aaai27/` |
| `model_parts/`（6 片 + PARTS.sha256） | 11.3G | `$W/model_parts/` → 校验后 `cat` 成 `$W/models-7B.tar.gz` |
| `wheels/` 整目录（修正后 100 whl） | 279M | `$W/wheels/` |
| `MANIFEST.sha256` | 12K | `$W/`（解包前总校验） |

## 2. 平台侧落地（交互式建模，镜像 `whyaaai-base`，无 GPU 规格即可）

```bash
W=/inspire/qb-ilm/project/ai4education/ky26140
# ① 模型分片：逐片校验→只重传坏片→合并→总校验（详见 qz_quickstart.md 第 1 步）
cd $W/model_parts && sha256sum -c PARTS.sha256          # 哪片 FAILED 只重传那片，直到 6 片全 OK
cat models-7B.tar.gz.part_* > $W/models-7B.tar.gz
# ② 总校验 + 解包（tar 无外层目录，先建目录）
cd $W && sha256sum -c MANIFEST.sha256                   # why-aaai27 + models-7B 都应 OK
mkdir -p $W/why-aaai27 $W/models
tar xzf why-aaai27.tar.gz -C $W/why-aaai27
tar xzf models-7B.tar.gz  -C $W/models                  # → $W/models/DeepSeek-R1-Distill-Qwen-7B
# ③ 装环境（⚠️ 用 env.platform.lock，不是 env.lock）：
python -m pip install --no-index --find-links $W/wheels -r $W/why-aaai27/env.platform.lock
python -m pip freeze > $W/why-aaai27/env.qz.lock        # 平台环境留档，跑完随包回传
```

**接线三件**（一次性）：
1. **模型=绝对路径 override**：编辑 `$W/why-aaai27/experiments/pilot.yaml`：
   `hparams_overrides.model_name: /inspire/qb-ilm/project/ai4education/ky26140/models/DeepSeek-R1-Distill-Qwen-7B`
   （路径小写后仍含 `qwen` → qwen 路由 vendor patch 照常命中并修复；这正是设计内行为。）
2. **wiki**：patch v2 自动探测 `/inspire/dataset/wikipedia/20231101/20231101.en`；若实际挂载路径不同：
   `export WHYAAAI_WIKI_PARQUET=<实际目录或 glob>`（写进每个作业命令）。
3. **离线三件套**（写进**每个**作业命令行首）：
   `export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1`

**自检五连（全过才算落地；CPU 即可）**：
```bash
cd $W/why-aaai27 && export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1
python -c "import torch,transformers,datasets,pyarrow;print(torch.__version__,transformers.__version__,datasets.__version__,pyarrow.__version__)"
python -c "from transformers import AutoTokenizer; t=AutoTokenizer.from_pretrained('$W/models/DeepSeek-R1-Distill-Qwen-7B'); assert t('</think>',add_special_tokens=False)['input_ids']==[151649]; print('MODEL OK')"
python -c "import sys;sys.path.insert(0,'src');from vendor_patches.easyedit_mom2_dataset import local_wiki_files as f;fs=f();assert fs and len(fs)==41,fs;print('WIKI OK',len(fs),'shards')"
for t in metrics edit_loop run_pilot; do python src/test_$t.py; done
python src/vendor_patches/test_qwen2_loader.py && python src/vendor_patches/test_mom2_dataset.py
python src/test_think_budget.py && python src/test_steer.py
cd source/EasyEdit && PYTHONPATH=.:$W/why-aaai27/src python -c "from vendor_patches.easyedit_qwen2_loader import apply as a1; from vendor_patches.easyedit_mom2_dataset import apply as a2; a1(); a2(); print('PATCH OK')"
```
**收尾**：实例「保存镜像并停止」→ 存为 **`whyaaai-env`**；后续所有作业用它（环境步永久免做）。

## 3. 跑 pilot —— **全程一个 8×H200 实例，一个终端走完（用户定：不切换、更快）**

**首选形态**：建**一个 8×H200 交互式建模实例**（镜像 `whyaaai-env`），冒烟→mom2→预过滤→layer 扫→pilot→打分**全在同一 Jupyter 终端顺序跑**。自动停止设够长（如 24h）；GPU 长期忙→不会被低利用率回收；万一停了同命令重跑即续。
> 前提：项目配额允许交互式 8 卡（建实例表单「单任务最大可用资源」≥8 GPU）。**仅当交互式不给 8 卡**才回退：pilot 用**分布式训练**作业（1 节点×8 卡，命令同，贴「执行命令」框，容错开/时长上限 8h），冒烟/mom2/打分仍小交互式实例——这才需要切换。

⚠️ **8 卡只加速 pilot 的 case 分片；mom2 是单 GPU 单进程的一次性活，必须先单进程喂出缓存再开 8 进程**，否则 8 进程各自重算协方差（每个数 GPU·h）+ 写坏缓存。顺序（行首均 `cd`+离线 export，`M=$W/models/DeepSeek-R1-Distill-Qwen-7B`）：

```bash
W=/inspire/qb-ilm/project/ai4education/ky26140; cd $W/why-aaai27
export HF_HOME=$W/hf HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1; M=$W/models/DeepSeek-R1-Distill-Qwen-7B

# ① 冒烟（~15min，用 1 张卡；先确认 7B 真能编+整链通，别让 pilot 跑一半才暴雷）
python src/test_think_budget.py --model $M --device cuda
PYTHONPATH=source/EasyEdit python src/rome_mps_probe.py --model $M --device cuda:0 --cases 2 --budgets B0 --fresh

# ② mom2 预热（⚠️ 单进程 1 卡！world=200 → 只跑 1 条 case，触发并缓存 mom2；H200 估 2–4h）
cd source/EasyEdit
PYTHONPATH=. python ../../src/run_pilot.py --config ../../experiments/pilot.yaml --editor MEMIT --rank 0 --world 200 --device 0
rm ../../results/pilot/r1qwen7b_MEMIT_cf200_r0of200.jsonl   # 删热身分片，防混入打分 glob

# ③ 预过滤（1 卡，~0.5–1h）
PYTHONPATH=. python ../../src/prefilter.py --config ../../experiments/pilot.yaml --device 0

# ④ layer 小扫（6 组：ROME [5]/[7]/[10]、MEMIT [4-8]/[6-10]/[8-12]；各 n=50 只 B0）+ ⑤ pilot —— **8 卡全开**：
for r in $(seq 0 7); do
  PYTHONPATH=. python ../../src/run_pilot.py --config ../../experiments/pilot.yaml --editor ROME --rank $r --world 8 --device $r &
done; wait
for r in $(seq 0 7); do
  PYTHONPATH=. python ../../src/run_pilot.py --config ../../experiments/pilot.yaml --editor MEMIT --rank $r --world 8 --device $r &
done; wait
```
layer 扫的 6 组配置怎么造、合格线判据、定稿回写 `pilot.yaml`——照 `RUNBOOK.md` §4b（**判生成式 ES≥0.90 & Loc≥0.85 @B0，永不混 rewrite_acc**）。pilot 跑完进 §5 打分。被抢占/超时同命令重跑即续。

## 5. 打分→校准→审计→回传

打分/校准/审计照 `interplan.md` §6（`score_pilot --boot 10000` → `analysis/09` 10% 校准 → 30 条审计）。
**回传包**（平台下载通道带出）：`results/pilot/*.jsonl` 全部分片｜`data/counterfact.prefiltered.jsonl`｜两张打分表｜`calibration_*.md`｜审计记录｜`env.qz.lock`｜内网侧 commit 后 `git -C $W/why-aaai27 bundle create whyaaai-back.bundle main`（根 .git 随 tar 已就位）。上报格式照 v1 §7（不替用户下 go/no-go 结论）。

## 6. 雷点增补（v2 特有；v1 §8 表仍全部有效）

| 雷 | 处置 |
|---|---|
| **NGC 容器 PIP_CONSTRAINT** | 镜像(torch nv25.6)钉死 `nvidia-ml-py==12.575.51` 配驱动 → 装 env.platform.lock 报 `ResolutionImpossible`。已从 lock 移除 nvidia-ml-py(只被 gpustat 用，容器自带)。若仍冲突：`PIP_CONSTRAINT= python -m pip install --no-index --find-links $W/wheels -r env.platform.lock`（忽略容器约束；我们不装 torch，安全） |
| **pyarrow≥21 硬地板** | `datasets 4.8.5` import 即检查；env.platform.lock 已钉 24.0.0——**绝不**装回 wheels 里的旧 20.0.0 |
| **torch 2.8 vs env.lock 2.9.1** | 接受镜像预装 2.8（transformers 5.5/accelerate 1.13 下限远低于此）；遇 torch API 缺口→存 incident 上报，**别**尝试离线装 torch |
| py3.12 vs 本地 py3.10 | wheels 全 cp312 已对齐；个别包 import 报 ABI/语法错→incident 上报 |
| antlr4 必须 4.9.3 | omegaconf 2.3.0 锁版；wheels 已含本地打的 py3-none-any |
| 装环境用错清单 | 平台只认 `env.platform.lock`；原 `env.lock` 是 Mac/py3.10 口径（torch pin 装不上） |
| tar 无外层目录 | 解包前 `mkdir -p`（§2 已含） |
| 上传损坏 | 解包前 `sha256sum -c MANIFEST.sha256` |
| **mom2 并发首跑** | 照 §3-③ 单进程预热；预热同时是 wiki parquet 直读的首次真验 |
| wiki 挂载路径变动 | `WHYAAAI_WIKI_PARQUET` 显式指（目录或 glob 均可） |
| 模型路径 override | 必须**绝对路径**（作业 cwd 在 source/EasyEdit，相对路径会解错） |

## 7. 现场仍需核实（v1 §2 清单的存量项）

① GPU 型号/单任务卡数上限/剩余卡时/优先级上限（建作业表单可见）→ 记现场笔记；② **数据集注册表搜 `DeepSeek`/`Qwen`**（命中 7B 则 §1 的 11GB 上传可免，model_name 直接指 `/inspire/dataset/...`）；③ 单文件上传上限（先小文件探路，决定是否启用 §1-④ 分卷）；④ 分布式训练作业是否挂同一块 `$W` 网盘（教程暗示同项目即同盘，首个 C1 作业开头 `ls $W/why-aaai27` 验证）。

---

## 现场笔记（执行中回填）

- GPU 型号/上限/卡时/优先级：
- 数据集注册表 DeepSeek 搜索结果：
- 单文件上传上限：｜分卷启用：☐
- 各阶段实际耗时：解包/装环境＝｜冒烟＝｜mom2＝｜C1＝｜C2＝｜C3-ROME＝｜C3-MEMIT＝
- 异常与处置：

*本文落笔 2026-06-12 晚（基于 report.md 18:12–19:30 实测 + 本轮 patch v2/wheels 修正方案）。与 report.md 冲突处以本文为准（report 是摸底快照，本文是修订后的作战版）。*
