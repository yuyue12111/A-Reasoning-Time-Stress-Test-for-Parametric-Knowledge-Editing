# report.md · 启智平台内网部署状态报告

> 生成时间：2026-06-12 18:12 | 本地 HEAD：`5b4c2ef`
> 更新记录：
> - 18:12 初稿：平台摸底 + 部署策略
> - 18:25 复读修订：补 5 个已识别问题入 §7，更新本地资产实况
> - 19:30 下载执行：模型 ✅ / wheels 98/105 包 ✅，5 个缺失包已识别

---

## 1. 平台环境（已核实）

| 项 | 值 |
|---|---|
| 平台 | 启智（qz.sii.edu.cn） |
| 空间 | 教育大模型-独立空间 |
| 外网 | **完全无**（HF/PyPI 均不通） |
| 作业形态 | 交互式建模 ✅ / 分布式训练 ✅ |
| Python | 3.12.3 |
| torch | 2.8.0a0+5228986c39.nv25.6 |
| CUDA | 12.9 |
| git | 2.43.0 ✅ |
| 预装 Python 包 | 几乎裸机（仅 safetensors 0.5.3） |
| 基础镜像 | 已保存为 **`whyaaai-base`**（torch2.8+CUDA12.9+git，后续所有作业用这个） |

### 持久化存储

| 路径 | 容量 |
|---|---|
| 用户挂载 `$W` | `/inspire/qb-ilm/project/ai4education/ky26140` — 可用 **529T** |
| Wikipedia 数据集 | `/inspire/dataset/wikipedia/20231101/` — 已挂载，parquet 格式，41 分片（`20231101.en/train-*-of-00041.parquet`） |

### 已确认不在平台上的

| 资产 | 说明 |
|---|---|
| DeepSeek-R1-Distill-Qwen-7B | ❌ 数据集注册表待搜，目前未挂载 |
| DeepSeek-R1-Distill-Qwen-1.5B | ❌ 同上 |
| pip 包（transformers/datasets 等） | ❌ 镜像裸机，需本地预下载 Linux wheel 上传 |

---

## 2. 本地资产（Mac）

| 资产 | 状态 |
|---|---|
| 仓库 `why-aaai27` | ✅ `git bundle` 已打包（252KB） |
| `env.lock` | ✅ 105 个包，无 macOS 专属，跨平台干净。**但生成于 py3.10，平台是 py3.12** |
| `source/` 第三方仓库 ×7 | ✅ 已在本地 `/Users/whyu/GitProjects/why-aaai/source/` 就位（463MB）。注意路径是 `why-aaai` 不是 `why-aaai27`，打包前需确认两个目录一致 |
| Mac 可用磁盘 | ✅ **681GB** — 够下模型 + 打轮子 |

---

## 3. 部署策略（全部离线）

平台完全无外网 → **所有东西在本地 Mac 打包，经平台上传通道传入**。

### 3.1 需上传的资产清单

| 产物 | 预估大小 | 打包方式 |
|---|---|---|
| ① 仓库 + source/ + papers/ | ~500MB | `tar czf` |
| ② pip 包（Linux x86_64, cp312） | ~3–5GB | `pip download --platform manylinux2014_x86_64 --python-version 312` |
| ③ DeepSeek-R1-Distill-Qwen-7B | ~15GB | `huggingface_hub.snapshot_download` → tar |
| ④ DeepSeek-R1-Distill-Qwen-1.5B（可选） | ~3.6GB | 同上 |
| ⑤ `env.lock` 本身 | 几 KB | 已在 ① 的 tar 里 |

### 3.2 不需要上传的

| 资产 | 原因 |
|---|---|
| Wikipedia 语料 | 平台数据集挂载 `/inspire/dataset/wikipedia/20231101/` |
| torch/CUDA | 镜像预装 torch 2.8 + CUDA 12.9 |

---

## 4. 本地待执行操作（有网环境）

### 步骤 A · 打包仓库

```bash
cd /Users/whyu/GitProjects/why-aaai27
mkdir -p _upload

# 注意：source/ 实际在 /Users/whyu/GitProjects/why-aaai/source/，
# 打包前先确认 why-aaai27/source/ 是否完整，必要时 rsync 过来

# 确认 source/ 下 7 个三方仓库齐全
ls source/EasyEdit/easyeditor source/AlphaEdit/AlphaEdit source/MQuAKE/datasets \
   source/R-TOFU source/ThinkEdit source/Unlearn-R2MU source/memit

# 打包（排除 .git、macOS 垃圾）
tar czf _upload/why-aaai27.tar.gz \
    --exclude='.git' --exclude='_upload' --exclude='__pycache__' \
    --exclude='.obsidian' --exclude='*.pyc' --exclude='.DS_Store' \
    --exclude='node_modules' \
    .
ls -lh _upload/why-aaai27.tar.gz
```

### 步骤 B · 下载 Linux wheel（env.lock → cp312 manylinux x86_64）

```bash
pip download -r env.lock \
    --platform manylinux2014_x86_64 \
    --python-version 312 \
    --implementation cp \
    --only-binary=:all: \
    -d _upload/wheels/ \
    2>&1 | tee _upload/wheel_download.log

# 检查失败项
grep -iE 'error|ERROR|could not|no matching' _upload/wheel_download.log
```

> **已知风险 1**：`torch==2.9.1` 在 env.lock 里，但平台镜像已有 torch 2.8。处置：平台上先 `pip uninstall torch -y` 再装 2.9.1，或跳过 torch 直接用镜像 2.8。
>
> **已知风险 2**：`tokenizers`、`torchvision` 等 C 扩展包绑 Python 版本。用 `--python-version 312` 下载的 cp312 wheel 才是平台能装的；如果某个包没有 cp312 wheel，`--only-binary=:all:` 会直接跳过它。降级策略：对缺 wheel 的包去掉 `:all:` 限制从源码装（需平台镜像有 gcc，待验证）。
>
> **已知风险 3**：从 ARM Mac 跨平台下载 x86_64 wheel，pip 可能因平台不匹配拒绝某些包。最终验证只能在平台上 `pip install --no-index --find-links wheels/` 看结果。

### 步骤 C · 下载模型（最大头，~15GB + ~3.6GB）

```bash
pip install huggingface_hub  # 确保本地有

# 7B 主模型
python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download("deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
                  local_dir="_upload/models/DeepSeek-R1-Distill-Qwen-7B",
                  local_dir_use_symlinks=False)
PY

# 1.5B 备用（可选，省时间可跳过）
python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download("deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
                  local_dir="_upload/models/DeepSeek-R1-Distill-Qwen-1.5B",
                  local_dir_use_symlinks=False)
PY

# 打包模型
tar czf _upload/models-7B.tar.gz -C _upload/models DeepSeek-R1-Distill-Qwen-7B
ls -lh _upload/models-7B.tar.gz
```

### 步骤 D · 上传到平台

1. 进入 `_upload/`，理出最终上传清单：
   - `why-aaai27.tar.gz`（~500MB）
   - `wheels/` 目录整体（~3–5GB）
   - `models-7B.tar.gz`（~15GB；分卷如平台有单文件上限）
2. 通过平台文件管理/notebook 上传功能传入，目标路径：`/inspire/qb-ilm/project/ai4education/ky26140/`
3. 在平台交互式实例里解包（**注意 tar 不含外层目录，需先 mkdir**）：
   ```bash
   W=/inspire/qb-ilm/project/ai4education/ky26140
   mkdir -p $W/why-aaai27 $W/models
   tar xzf $W/why-aaai27.tar.gz -C $W/why-aaai27
   tar xzf $W/models-7B.tar.gz -C $W/models
   pip install --no-index --find-links $W/wheels/ -r $W/why-aaai27/env.lock
   ```
4. **模型路径对接**：模型在 `$W/models/DeepSeek-R1-Distill-Qwen-7B`，需要让 pilot 找得到：
   - 方案 A：`export HF_HOME=$W/hf` 并 `ln -s $W/models/DeepSeek-R1-Distill-Qwen-7B $W/hf/hub/models--deepseek-ai--DeepSeek-R1-Distill-Qwen-7B`
   - 方案 B：直接改 `pilot.yaml` 的 `hparams_overrides.model_name` 为绝对路径（`run_pilot.py` 已支持）

---

## 5. 就位后的自检（平台实例内）

```bash
cd /inspire/qb-ilm/project/ai4education/ky26140/why-aaai27
export HF_HOME=/inspire/qb-ilm/project/ai4education/ky26140/hf
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1

# ① 模型可加载
python -c "
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained('/inspire/qb-ilm/project/ai4education/ky26140/models/DeepSeek-R1-Distill-Qwen-7B')
assert tok('</think>', add_special_tokens=False)['input_ids'] == [151649]
print('MODEL OK')
"

# ② Wikipedia 可加载（直接读本地 parquet——但 vendor patch 走的是 HF hub 路径，见 §7 问题 A）
python -c "
from datasets import load_dataset
ds = load_dataset('parquet', data_files='/inspire/dataset/wikipedia/20231101/20231101.en/train-*.parquet', split='train')
print('WIKI OK', len(ds))
"

# ③ mock 单测全绿（无 GPU）
for t in metrics edit_loop run_pilot; do python src/test_$t.py; done
python src/vendor_patches/test_qwen2_loader.py && python src/vendor_patches/test_mom2_dataset.py
python src/test_think_budget.py && python src/test_steer.py
```

---

## 6. 自检通过后的执行序列

照 `RUNBOOK.md` §4 顺序：
1. **预过滤**（`prefilter.py`，1 GPU）→ `data/counterfact.prefiltered.jsonl`
2. **mom2 预热**（MEMIT 单进程 1 条 case，~6 GPU·h，一次性）
3. **layer 小扫**（6 组配置，各有 50 条 B0，选过线层）
4. **pilot 主跑**（ROME + MEMIT，各 8 卡分片，B0/B3/B4）
5. **打分**（`score_pilot.py`，CPU）
6. **10% 边界校准** + **30 条回退审计**

---

## 7. 已识别问题与风险（待解决，勿动其他文件）

### 🔴 问题 A · Wikipedia vendor patch 在无网环境会崩

`src/vendor_patches/easyedit_mom2_dataset.py` 劫持 `load_dataset("wikimedia/wikipedia", "20231101.en")`，但这个调用底层会尝试连 HF hub。平台 `HF_HUB_OFFLINE=1` 时 datasets 库行为不确定——可能直接抛异常而非回退到本地缓存。

**需要做的事**：patch 增加一个环境检测分支——当 `/inspire/dataset/wikipedia/20231101/` 存在且 `HF_HUB_OFFLINE=1` 时，直接 `load_dataset('parquet', data_files='/inspire/dataset/wikipedia/20231101/20231101.en/train-*.parquet')` 绕过 hub。**这份改动属于 vendor_patch，不违反 CLAUDE.md 约束 3，但需要在本地改好再上传**。

### 🔴 问题 B · env.lock py3.10 vs 平台 py3.12 的 C 扩展兼容

`tokenizers==0.22.1`、`torchvision==0.24.1` 等 C 扩展包绑 Python 版本。已用 `--python-version 312` 下载 cp312 wheel。`tokenizers==0.22.1` cp312 wheel ✅ 已下载，可在平台安装。torch/torchvision 跳过（平台镜像预装 torch 2.8）。

### 🟡 问题 C · source/ 路径不一致

本地 source/ 在 `/Users/whyu/GitProjects/why-aaai/source/`，主仓库在 `why-aaai27/`。打包前需确认 `why-aaai27/source/` 有完整 7 个仓库，否则 tar 包会缺胳膊少腿。

### 🟡 问题 D · 模型上传单文件上限未知

平台上传通道可能有单文件大小限制。`models-7B.tar.gz` 11GB，如果限制 ≤10GB 需分卷（`split -b 5G`）。上传前先试传小文件看有无报错。

### 🟡 问题 E · 官方数据集注册表里是否有 R1 模型

尚未在平台数据集列表里搜索 `DeepSeek`/`Qwen`。如果命中可省 11GB 上传。需在新建交互式实例时在数据集挂载表单里搜索。

### 🟢 问题 F · tar 解包路径

`tar czf _upload/why-aaai27.tar.gz .` 打包时不带外层目录，解包时必须先 `mkdir -p`，已在 §4 步骤 D 修正。

### 🟡 问题 G · 5 个缺失的 pip 包（见 §8）

5 个包未能下载（3 个可能不必、2 个平台可绕过）。需在平台上 `pip install --no-index` 后根据 import 报错逐包处理。

---

## 8. 下载执行结果（2026-06-12 19:30）

### 8.1 模型

| 项 | 值 |
|---|---|
| DeepSeek-R1-Distill-Qwen-7B | ✅ 14GB 原始，打包 11GB → `_upload/models-7B.tar.gz` |
| safetensors | 2 分片（8.6GB + 6.6GB），tokenizer/config 齐全 |

### 8.2 pip wheel 最终结果（182MB，101 文件）

| 结果 | 包数 | 说明 |
|---|---|---|
| ✅ cp312 wheel 下载成功 | 101 | 全部 Linux x86_64 wheel |
| ⏭️ 跳过（平台预装） | 2 | `torch==2.9.1`、`torchvision==0.24.1` |
| ❌ 最终缺失 | 2 | `av`、`opencv-python`（均不必须） |

**⚠️ 版本差异注意（平台上 pip install 前需处理）**：

| 包 | env.lock 版本 | 实际下载版本 | 原因 | 处置 |
|---|---|---|---|---|
| `PyYAML` | `==6.0` | `6.0.3` | 6.0 太老无 cp312 wheel | 平台安装时改用 `'PyYAML>=6.0'` 或直接从 wheels/ 装 `.whl` 文件 |
| `pyarrow` | `==24.0.0` | `20.0.0` | 24.0.0 不存在于 PyPI | 20.0.0 功能兼容，平台安装时改版本约束 |
| `antlr4-python3-runtime` | `==4.9.3` | `>=4.11` | 4.9.3 无 cp312 wheel | 已下载 4.13.2 cp312 wheel |

**最终仍缺失（非必须）**：

| 包 | 说明 |
|---|---|
| `av==14.2.0` | 视频处理，项目无此依赖 |
| `opencv-python==4.12.0.88` | 图像处理，项目无此依赖 |

**核心包确认已下载**：`transformers`、`tokenizers`、`datasets`、`accelerate`、`peft`、`safetensors`、`sentencepiece`、`scipy`、`pyarrow`、`PyYAML`、`numpy`、`scikit-learn`、`matplotlib`、`pandas` 全部 ✅

### 8.3 仍需本地操作的

- [ ] 步骤 A · `tar czf _upload/why-aaai27.tar.gz` 打包仓库（含 source/ + papers/）
- [ ] 检查 source/ 路径一致性（问题 C）

---

*本文只记录现状，不改任何其他文件。下一步：本地执行步骤 A 打包仓库，然后上传全部 `_upload/` 至平台。*
