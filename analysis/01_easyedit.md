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

## 6. 待办（实跑后回填）

- [ ] 本地 CPU 冒烟 rewrite_acc 结果
- [ ] H200 上 R1-Distill-Qwen-7B 单条 ROME + layers 三组扫描结果（plan §7 风险表合格线：ES≥90%, Locality≥85%）
- [ ] batch_edit 分支还原语义确认
