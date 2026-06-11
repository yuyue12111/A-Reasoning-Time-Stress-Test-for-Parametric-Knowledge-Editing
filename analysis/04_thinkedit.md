# 04 · ThinkEdit 复现笔记（steering 机械 → Phase 4 主修补 F1 地基）

- **日期**: 2026-06-11 ｜ **状态**: 源码审计完成 ✅；通用 steering 工具 `src/steer.py` 已落 + mock 单测过 ✅；GPU 验证（GSM8K 方向有效性）待 H200
- **仓库**: `source/ThinkEdit`（Trustworthy-ML-Lab，EMNLP'25，2503.22048，12 py 高度聚焦）
- **base 模型**（`utils.py:18-26` `model_dict`）：R1-Distill-**Qwen-1.5B / Llama-8B / Qwen-14B / Qwen-32B**——**无 7B**（我们主模型是 Qwen-7B，见雷点 1）
- **任务（plan Phase 0 #04）**：通读方向抽取/头定位/权重编辑 → 改造为通用 steering 工具 `src/steer.py`
- **一句话**：ThinkEdit = 「抽一个线性方向 + 在残差流上加 α·方向」控制思考长度。机制干净可借；我们 F1 借**推理时 steering**（其 Eq.2）这一半，retarget 成「保护编辑事实」。

---

## 1. 代码结构（最小地图）

```
ThinkEdit/
├── extract_thinking_length_direction_gsm8k_{mlp,attn}.py  # Eq.1 方向抽取（long−short 均值差）
├── thinking_length_steering_gsm8k.py            # Eq.2 推理时 steering（forward hook 加 α·v）★F1 借这个
├── thinking_length_layerwise_steering_gsm8k.py  # 同上但逐层（定位哪层最有效=中层）
├── find_short_thinking_attn_heads.py            # 找 ~4% "短思考"头（按对短方向的贡献 top-k）
├── get_ThinkEdit_models.py                      # Eq.6 权重编辑（改选中头的 W_o，永久）
├── utils.py                                     # model_dict / get_think_length（token-id 级数 CoT 长度）
└── evaluate_*.py / generate_response_gsm8k.py / math_grader.py  # 评测（GSM8K/MATH 数学判分）
```

## 2. 核心机制（从代码出发，行号为证）

**① 方向抽取（Eq.1，`extract_...mlp.py:39-93`）**：
- 把预生成的 GSM8K 回答按 CoT 长度切两堆：`D_long`（>1000 tok）、`D_short`（<100 tok）。
- 每条：`<｜User｜>{q}<｜Assistant｜>{thinking}`，取 thinking 的 token 区间 `[start-1:end-1]`（next-token 对齐）上、逐层 hidden 均值；`hidden_states[1:]`（跳 embedding 层）。
- `v_ℓ = mean(hidden[long]) − mean(hidden[short])`，shape `[n_layers, hidden]`，存盘。attn 版同理但取 post-attention 残差。

**② 推理时 steering（Eq.2，`thinking_length_steering_gsm8k.py:44-61`）★**：
```python
def hook_fn(module, input, output):          # mlp 版
    return output + args.direction_weight * direction[layer_idx]
layer.mlp.register_forward_hook(...)         # attn 版改 output[0] 且保留 tuple 其余项
```
对**所有层全局**注入；`direction_weight`=α∈[−0.08,0.08]，α>0 思考变长、α<0 变短。**这就是我们 F1 要的原语**。

**③ 权重编辑（Eq.6，`get_ThinkEdit_models.py:31-60`）**：
- `heads` 是**写死的** (layer,head) 列表（每模型一套，~4% 头；由 `find_short_thinking_attn_heads.py` 的 top-k 离线找好）。
- `remove_projection_along_v`：`v̂=v/‖v‖; W_o ← W_o − outer(W_o·v̂, v̂)`，即把 W_o 沿方向的分量投掉；先 `v = −v`（投掉**短思考**分量）。**永久改权重**（0.2% 参数）。

## 3. 可复用资产 → `src/steer.py`（已落 + 单测过）

把 ①② 通用化进 `src/steer.py`：
- `Steerer(model, directions, alpha, site, layers)`：上下文管理器，forward hook 在 `layer.{mlp,self_attn}` 输出加 α·v；**推广**：任意方向、可选层子集、可选**位置掩码**（`set_positions`，ThinkEdit 是全局无掩码）。
- `extract_direction(model, tok, pairs_A, pairs_B)`：Eq.1 通用化（A−B 的逐层 span 均值差）。
- `src/test_steer.py` 4 测全过（全局/掩码/attn-site/层子集+符号/退出摘钩，editrev/torch、无 GPU）。

## 4. 给 F1 的接法（Phase 4，plan §4 F1）

1. **抽方向**：用 `extract_direction`，A=「忠于新事实 o* 的 CoT」、B=「质疑/回退旧答 o_old 的 CoT」（编辑前后模型各跑一批，或人造对照），得「强化编辑事实方向」（或反向得「质疑方向」用 −α 抑制）。
2. **条件注入**：`Steerer(site="attn", layers=中层)` + `set_positions(被编辑主体 s 提及后 k 个 token 的掩码)`——只在主体窗口注入 −α·(质疑方向) 或 +β·(新事实方向)。
3. **网格搜 α,β**：dev-100 上扫（**ThinkEdit 自证效果 model/task 依赖**，见 §6，不能假设单调有效）。
4. 增量解码的位置掩码需逐步维护（`steer.set_positions` docstring 已标）——F1 实现时补 stateful tracker。

## 5. 核心优缺点（从代码出发）

- ✅ **机制极简可信**：方向=两堆均值差、注入=一行 hook，无训练、无额外参数（steering 路线）；逐层版直接告诉我们中层最有效（省我们扫层）。
- ✅ **与我们 budget 控制互补**：论文 p4「Budget Control with Steering」明确论证 steering 比 s1 的 append-"Wait"/截断**更连贯**——正好支持我们 F1 用 steering（而 `think_budget` 用 s1 式做**自变量**，F1 用 steering 做**修补**，两者分工）。
- ⚠️ **效果 model/task 依赖（其自承）**：§3.3——qwen-1.5b 正向 steering 反而掉 10% acc；MATH-L5 上「更长≠更准」无清晰趋势。→ F1 的 α 必须按模型/任务网格搜，别假设单调。
- ⚠️ **方向/头不可跨模型复用**：heads 写死、direction 按模型存盘，且 **base 无 7B**——我们 7B 要**重抽方向 + 重找头**。
- ⚠️ 权重编辑版（Eq.6）是**永久改权重**，与我们 training-free F1 取向不同；可作 F2 式「编辑增强」对照，但主推 steering。

## 6. 雷点登记

1. **base 无 R1-Distill-Qwen-7B**（`utils.py:18-22` 只有 1.5B/14B/Llama-8B/32B）：`get_ThinkEdit_models.py` 的写死 heads + `directions/*.pt` **不能用于我们 7B**，必须在 7B 上重抽方向、重跑 top-k 找头。
2. **`<think>` 用 token-id 检测**（`steering.py:34-35` `encode("<think>")[0]`），与 R-TOFU/我们 `think_budget` 的**文本检测**口径不同（03 §4）——都可用（非特殊 token），但 7B 上若改走 token-id 要重验首 token 一致。
3. **全角竖线 U+FF5C**（`steering.py:74`、`extract:30-31`、已进 `steer.py`）：手敲模板重验。
4. **span 对齐 `[start-1:end-1]`**（next-token 偏移）：`steer.extract_direction` 已照搬，自己改抽取时别错位。
5. 采样 `do_sample=True` + seed 20：复现其数字要对齐随机源（我们 F1 评测自有 greedy+seed 规程）。

## 7. 论文宣称 vs 代码现实（读 PDF 2503.22048 后补，Prompt2「从代码出发不被包装影响」）

| 论文宣称（包装） | 代码 / 原文现实 | 判定 |
|---|---|---|
| 「reasoning length 是 hidden 里的**线性方向**，中层主导」 | 抽法=long/short 两堆均值差（一个特定 GSM8K >1000 vs <100 切分）；steering 确实改长度（Fig 3）。但**效果 model/task 依赖**（§3.3 自承 qwen-1.5b 掉 10%、MATH-L5 无单调） | **真但有条件**：线性方向能控长度，但"更长更准"非普适 |
| 「**4% 头 / 0.2% 参数** → +6.39% 短 / +3.34% 总」 | heads 写死（离线 top-k 找好）、edit=投掉 W_o 沿短方向分量，代码忠实 | 真，但**是其 GSM8K/MATH 数字，非我们任务**——我们借机制不借数字 |
| 「steering 比 budget-forcing 更连贯」(p4) | 是其**论证**（偏向自家 steering），非严格实验对照 | **支持我们 F1 选 steering** 的设计，但记住是 claim；我们 think_budget 仍用 s1 式做自变量 |
| 「first to systematically study 推理长度的内部表征」 | 方向抽取 + 逐层定位扎实 | 可信；其逐层「中层最有效」结论省我们 F1 的扫层成本 |

**一句话**：ThinkEdit 的 steering 机制干净、可直接改造（已落 `steer.py`），是我们 F1 的现成地基；但它的「线性方向普适控长度」「+x%」是其特定模型/任务下的结论，方向与头**不可跨模型复用**（我们 7B 要重抽），且效果需按 α 网格搜——不被其漂亮数字带偏，借的是**机械**不是**结论**。
