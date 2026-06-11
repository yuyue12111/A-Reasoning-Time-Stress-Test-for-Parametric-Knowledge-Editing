# 01 · EasyEdit 复现笔记

- **日期**: 2026-06-10 ｜ **状态**: 源码审计完成 ✅；CPU/GPU 实跑待本地执行（原因见"环境记录"）
- **仓库**: `source/EasyEdit`（zjunlp，最后提交 2026-06-10，439 py，含 Dockerfile）

## 1. 环境记录与实跑决策

容器实测：无 torch、磁盘仅 9.5G 可用。装 CPU torch(~1G 依赖) + GPT-2-XL(6.4G fp32) + ROME 协方差统计(~0.7G) 会顶满磁盘且 CPU 编辑需 20–40 min，性价比为负。**决策：容器内只做源码审计；实跑冒烟在本地/H200 登录节点执行**，命令如下（预期 `rewrite_acc == 1.0`）：

```bash
cd /Users/whyu/GitProjects/why-aaai/source/EasyEdit
conda create -n editrev python=3.10 -y && conda activate editrev
pip install -r requirements.txt
python - <<'PY'
from easyeditor import BaseEditor, ROMEHyperParams
hp = ROMEHyperParams.from_hparams('./hparams/ROME/gpt2-xl')
hp.device = 'cpu'   # GPU 机器上改成卡号, e.g. 0
editor = BaseEditor.from_hparams(hp)
metrics, model, _ = editor.edit(
    prompts=['The Eiffel Tower is located in'],
    ground_truth=['Paris'], target_new=['Rome'], sequential_edit=False)
print(metrics)
PY
```

## 2. 代码结构（与本项目相关的最小地图）

```
easyeditor/
├── editors/editor.py        # BaseEditor.edit() 主入口；权重还原逻辑在此（见 §3）
├── models/rome/             # rome_main.py(编辑入口) / compute_u.py / compute_v.py(F3改动点)
├── models/memit/、models/alphaedit/   # 同构，layers 列表批量改写
├── util/nethook.py          # get_parameter 按名取权重——还原依赖它
└── evaluate/                # 自带 ES/Paraphrase/Locality 评测（我们只用其编辑，评测自建）
hparams/{ROME,MEMIT,AlphaEdit}/qwen2.5-7b.yaml   # 已确认存在
```

## 3. 核心机制审计（单条编辑协议的地基，源码行号为证）

1. **权重备份**: `rome_main.py:39-50` —— `weights_copy[w_name] = w.detach().clone()`，仅克隆被改写矩阵（ROME 1 个、MEMIT/AlphaEdit 5 个 down_proj），7B 下每个 ≈ 3584×18944×2B ≈ 130MB，5 层 ≈ 650MB 显存，可接受。
2. **还原**: `editor.py:265 / 408 / 460` 同一模式 —— `with torch.no_grad(): for k, v in weights_copy.items(): nethook.get_parameter(model, k)[...] = v`。**还原是精确的（逐元素拷回），不是近似**；循环正确性成立。
3. **edit() 返回三元组** `(all_metrics, edited_model, weights_copy)`（`editor.py:288`）——我们的 `edit_loop` 拿到 weights_copy 后自行控制还原时机（生成完所有预算档再还原）。
4. **F3 改动点**: `models/rome/compute_v.py:22,42,63` —— 优化 v 时在 `context_templates` 上平均目标概率；把推理风格前缀（"Let me think step by step. … the answer is"）注入该列表即可让 o* 在 think 分布内也最优。MEMIT/AlphaEdit 的 compute_v 同构。

## 4. 核心优缺点（从代码出发）

- ✅ 优点：还原机制干净、hparams 体系把三个编辑器统一到同一接口（矩阵实验零胶水）；当天仍在维护；Dockerfile 现成（云端逃生镜像基底）。
- ⚠️ 缺点/雷点：
  1. `editor.py` 文件级巨大（多套 edit_* 分支并存），调用时务必走 `edit(..., sequential_edit=False)` 单条路径，不要踩 batch_edit 分支的还原语义差异（**待实跑确认 batch 分支是否每条都还原**——pilot 前补验）。
  2. 自带 evaluate 的 ES 判分是 logits/prefix 匹配口径，与我们"生成式 + think 模板"口径不同——**绝不能混用其 rewrite_acc 与我们的 ES_b**，论文里两口径都报但分开命名。
  3. requirements 未钉版本上限，transformers 大版本漂移可能破坏 hook；环境一旦跑通立即 `pip freeze > env.lock`。
  4. mom2 统计按 model_name 缓存路径区分——R1-Distill 与 Qwen2.5 **必须分目录**，防止误用对方统计（stats_dir 显式分开）。

## 5. 可复用资产清单

- `BaseEditor` + 三套 hparams（改 model_name 即用）
- `nethook.get_parameter`（机理章节 logit lens 的 hook 也用它）
- Dockerfile（扩展为项目镜像）

## 6. 环境实跑记录（task 3，2026-06-10，本地 macOS arm64 / 26.5.1）

**最终可用环境**：Miniconda + conda env `editrev`(py3.10.20) + EasyEdit 全依赖（torch 2.9.1 / transformers 5.5.4 / … 共 105 包），`env.lock` 已落仓库根并 commit（CLAUDE.md 硬约束 6）。

**可复制的建环境 + 冒烟命令（已实跑、踩坑修正版）**：
```bash
# 1) Miniconda（batch，不改 shell profile）
curl -fsSL -o /tmp/mc.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
bash /tmp/mc.sh -b -p ~/miniconda3
# 2) env：从 conda-forge 建 + 显式带 pip（见坑 ①②）
~/miniconda3/bin/conda create -n editrev python=3.10 pip -y -c conda-forge --override-channels
PY=~/miniconda3/envs/editrev/bin/python
# 3) 依赖
$PY -m pip install -r source/EasyEdit/requirements.txt
# 4) 冒烟：PYTHONPATH=. 必需（坑 ④）；脚本内已 override model_name（坑 ⑤）
cd source/EasyEdit && PYTHONPATH=. $PY ../../src/smoke_rome_gpt2.py
$PY -m pip freeze > ../../env.lock
```

**冒烟结果**：ROME 单条编辑（`The Eiffel Tower is located in`，Paris→Rome）on GPT-2-XL @ CPU —— `rewrite_acc` = **运行中待回填**（GPT-2-XL 6.4GB 下载 + CPU ROME 进行中；预期 1.0，完成即回填本行并 commit）。

**依赖坑登记（5 个，全部已修，建环境照此避）**：

| # | 现象 | 根因 | 修法 |
|---|---|---|---|
| ① | `conda create` 报 ToS 未接受、退出码非 0 | 近期 Miniconda 把 defaults 频道 ToS 设为前置门槛 | `conda tos accept --override-channels --channel .../pkgs/main`（+`/pkgs/r`），或直接 `-c conda-forge --override-channels` 绕开 |
| ② | env 建好但 `No module named pip` | conda-forge 最小 python 不自带 pip | create 时显式列 `pip`，或 `$PY -m ensurepip --upgrade`（自带 wheel、免网） |
| ③ | 本机 system python 3.9.6 装不了依赖 | torch2.9 / transformers5.5 需 py≥3.10 | 必须 conda/pyenv 建 ≥3.10 env（本机无 conda/pyenv，故装 Miniconda） |
| ④ | `from easyeditor import …` → ModuleNotFoundError | easyeditor 是**本地包、非 pip 安装**；`python <脚本>` 只把脚本目录(src/)入 sys.path、不含 source/EasyEdit；且 EasyEdit **无 setup.py**，`pip install -e .` 也走不了 | 在 source/EasyEdit 下用 `PYTHONPATH=.` 运行（plan §11.3 命令已更正） |
| ⑤ | 加载模型 `HFValidationError: ./hugging_cache/gpt2-xl` | `hparams/ROME/gpt2-xl.yaml` 的 `model_name` 写死成本地缓存路径（不存在） | 脚本里 `hparams.model_name='gpt2-xl'` 覆盖、改从 HF Hub 拉（已落 `src/smoke_rome_gpt2.py`） |

## 7. H200 待回填（GPU 窗口）

- [ ] R1-Distill-Qwen-7B 单条 ROME + layers ∈ {[4-8],[6-10],[8-12]} 三组扫描（plan §7 合格线 ES≥90% & Locality≥85%）
- [ ] batch_edit 分支还原语义确认（pilot 前）
- [ ] AlphaEdit 上 Qwen 前先打 02 笔记的 P 预分配 qwen 补丁（否则首跑 P 崩）
- [x] §3 源码行号抽验（2026-06-10, HEAD 6a164f9）：`rome_main.py:50` clone、`editor.py:265/408/460` 还原、`editor.py:288` return triple **均未漂移**，与交接审计一致

## 8. 论文宣称 vs 代码现实（读 PDF 2308.07269 后补，Prompt2「从代码出发不被包装影响」）

论文把 EasyEdit 包装成「**易用 + 统一**的编辑框架」，并称「editing 在 reliability/generalization 上**超过 fine-tuning**」（LLaMA-2，§Abstract/§1）。逐条对代码核：

| 论文宣称（包装） | 代码现实（我审计所得） | 判定 |
|---|---|---|
| "easy-to-use / 开箱即用" | Editor/Method/Hparams/Evaluate 统一接口属实（矩阵实验零胶水，本笔记 §3/§5）；但**开箱有三处摩擦**：本地包需 `PYTHONPATH=.`（坑④）、hparams 的 `model_name` 写死不存在的本地路径（坑⑤）、requirements 无版本上限会漂移破 hook（§4 雷点 3） | **半真**：统一是真，frictionless 不是 |
| "modular / 自由组合" | hparams 体系确实把 ROME/MEMIT/AlphaEdit 收一个接口（改 model_name 即用） | 真 |
| Reliability 指标（其 `rewrite_acc`） | 是 **logits/prefix 匹配**口径（§4 雷点 2），不是生成式；与我们的 `ES_b`（生成式 + think 模板）**不同口径，永不混排**（CLAUDE.md 约束 4） | 真但**口径不可平移** |
| "editing **surpasses fine-tuning** in reliability/generalization"（LLaMA-2） | 这是 **no-think / 标准评测**下、用其口径得出的结论。**我们整个项目就在证伪它在 LRM think 场景下的'可靠'**——编辑随思考预算回退。论文的"可靠"不涉 test-time compute | **正是我们的张力点/卖点**：不被其"可靠"宣称带偏 |
| Table 1：方法能力/开销 | ROME **不支持 batch**（单条）、MEMIT 支持——**印证我们 ROME 走单条编辑协议合理**；Time/VRAM（LLaMA-7B,10 edits）：ROME 187.9s/31GB、MEMIT 169.3s/33GB，给 §5 算力账参照 | 真，可复用 |
| `keep_original_weight` 单条还原 | 还原精确（逐元素拷回，§3 已审计）；**但 batch 分支还原语义仍待验**（§7） | 单条真，batch 待验 |

**一句话**：EasyEdit 的"易用"是统一接口为真、开箱摩擦不少；"可靠超过 FT"是特定口径 + 非 LRM-think 场景下的宣称——恰是我们要在思考预算维度上系统反证的对象。作为**工具**可信（还原机制、hparams 体系扎实），作为**结论**不照搬。
