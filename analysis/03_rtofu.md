# 03 · R-TOFU 复现笔记（思考预算控制器的口径地基）

- **日期**: 2026-06-10 ｜ **状态**: 源码审计完成 ✅；tokenizer 特殊 token 问题已用 HF 配置离线定案 ✅；GPU 实跑（6 档长度分布）留待 task 7
- **仓库**: `source/R-TOFU`（ssangyeon，EMNLP'25，14 py，结构干净）
- **base 模型**: `deepseek-ai/DeepSeek-R1-Distill-Llama-8B`（`config/tofu.yaml:2`、`config/model_config.yaml:9`、`scripts/tofu/finetune.sh:17`）——**注意是 Llama-8B 蒸馏版，不是我们主模型 Qwen-7B**，tokenizer 不同，下文 §4 已分别核对
- **本笔记对应 plan**: §11.2（prefill 模板）、§12.1 注意点②（`<think>` 是否特殊 token → B4 检测走文本还是 token-id）；产出已回填进 `src/think_budget.py`

---

## 1. 环境与实跑决策

无需建环境即可完成 task 5 的两件事：①prefill 精确字符串——纯文本，读源码即得；②`<think>` 是否特殊 token——直接拉两个模型的 `tokenizer_config.json`（公开 JSON，无需下权重、无需 torch）核对 `added_tokens_decoder`。本机 system python 3.9.6 + 无 conda，装不了 EasyEdit/R-TOFU 的依赖（torch 2.9 / transformers 5.5 需 py≥3.10），故 R-TOFU 自身的 GPU 评测不在本机跑；6 档长度分布验证见 task 7（H200 窗口）。

## 2. 代码结构（与本项目相关的最小地图）

```
R-TOFU/
├── test.py         # 答案级评测：ZeroThink / LessThink 两策略
│   ├── apply_think_strategy()  L13-20   ← ZeroThink(L16)/LessThink(L18) prefill 在此
│   ├── generate_response()     L22-50   ← 返回 (cot, answer)，decode skip_special_tokens=True(L39)
│   └── rouge_answer_score()    L54-122  ← answer vs 参考的 ROUGE-L recall + cosine
├── test_cot.py     # CoT 级评测：DefaultCoT 一策略
│   ├── apply_think_strategy()  L243-247 ← DefaultCoT(L245) prefill
│   ├── extract_cot()           L249-254 ← 文本 find("<think>")/find("</think>") 切片
│   ├── generate_response()     L256-280 ← 同 test.py，decode skip_special_tokens=True(L272)
│   ├── rouge_cot_forget_score()L189-240 ← 生成 CoT vs 参考 CoT 的 ROUGE-L recall
│   ├── compute_cosine_similarity_score() L25-111 ← 句级 cosine(all-MiniLM-L6-v2)+ROUGE-L recall
│   └── evaluate_with_gpt()     L113-185 ← GPT-4o 打 0-1 "forgetting score"
├── config/{tofu,model_config}.yaml  # base 模型 = R1-Distill-Llama-8B
├── forget.py / trainer/             # unlearning 训练（我们不跑）
└── data/、dataset/、metrics/、utils/
```

只用 §3 的解码协议 + §5 的口径理解；训练侧（forget.py/trainer）与我们无关。

## 3. 思考预算 prefill —— 三个策略的逐字字符串（全角竖线 U+FF5C）

> 已逐字提进 `src/think_budget.py` 并用脚本校验 `== R-TOFU 源码`（byte-for-byte，含全角竖线、`\n` 数量）。

| 策略 | 源码位置 | 精确字符串（`{prompt}` 即问题） |
|---|---|---|
| **DefaultCoT** | `test_cot.py:245` | `<｜User｜>{prompt}<｜Assistant｜><think>\n` |
| **ZeroThink** | `test.py:16` | `<｜User｜>{prompt}<｜Assistant｜><think>\n\n</think>\n\n` |
| **LessThink** | `test.py:18` | `<｜User｜>{prompt}<｜Assistant｜><think>\nOkay, the user asked this, I can answer it without thinking much.\n</think>\n\n` |

与 DeepSeek 官方 `chat_template`（从 HF `tokenizer_config.json` 取）对齐确认：
- `add_generation_prompt` 分支输出 `<｜Assistant｜><think>\n` —— 与 DefaultCoT **逐字一致**；
- user 轮 `<｜User｜>` + content；模板开头 `{{bos_token}}` 且 `add_bos_token=true` → BOS 自动前置一次（R-TOFU 用 `tokenizer(modified_prompt)` 默认 `add_special_tokens=True` 同样前置一次，**不会重复**）；
- 无 system prompt（与 plan §11.2 一致）；
- 多轮历史里模板会 `content.split('</think>')[-1]` 丢掉思考——我们是单轮探针，无影响，但机理章节引用 CoT 时要知道官方默认不喂回思考。

**LessThink 语义务必分清**（口径诚实点）：R-TOFU 的 LessThink 是**固定假思考**（一句写死的话直接闭合 `</think>`），不是"按 token 预算截断"。plan §2.4 把它**推广**成"思考至 N token 截断强制收尾"。因此：
- 我们的 **B0 = R-TOFU ZeroThink 逐字复刻**（`think_budget.ZEROTHINK`，已校验相等）；
- 我们的 **B1/B2/B3 是自家的截断式推广**，并非 R-TOFU 原物——论文/附录描述预算档时不能写"沿用 R-TOFU LessThink"，要写"generalize R-TOFU's LessThink to a token-budget truncation"；
- R-TOFU 原版 LessThink 串仍留作 `think_budget.LESSTHINK_CANNED` 供消融/对照。

## 4. ⭐ `<think>` 是否特殊 token —— plan §12.1 注意点② 定案

**结论：`<think>` 和 `</think>` 在两个模型上都不是特殊 token，B4 的 `</think>` 检测走文本即可，无需 token-id StoppingCriteria。**

证据链（两条独立佐证，互相印证）：

1. **HF tokenizer 配置（直接证据，离线可查）**：拉 `tokenizer_config.json` 检查 `added_tokens_decoder`——
   - `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B`（**我们的主模型**）：`<think>`/`</think>` **不在** `added_tokens_decoder`；在册的特殊 token 是 `<｜begin▁of▁sentence｜>`(bos)、`<｜end▁of▁sentence｜>`(eos)、`<｜User｜>`、`<｜Assistant｜>` 等。`<think>` 只作为普通文本出现在 `chat_template` 字符串里。
   - `deepseek-ai/DeepSeek-R1-Distill-Llama-8B`（R-TOFU 的 base）：同上，`<think>`/`</think>` 也不是特殊 token。
   - ⇒ 普通 BPE 文本，`skip_special_tokens` 取 True/False 都**不会**把 `<think>`/`</think>` 剥掉。

2. **R-TOFU 行为（间接佐证）**：`test.py:39`/`test_cot.py:272` 用 `skip_special_tokens=True` 解码**整段** `output_ids[0]`（含被 prefill 进 prompt 的 `<think>`），随后 `test.py:41-45` 仍能 `find("<think>")`/`find("</think>")` 切片。若它们是特殊 token，`skip_special_tokens=True` 会先剥掉、切片必然失败；R-TOFU 全流程依赖切片成功 ⇒ 反推它们是普通文本。两条证据一致。

**据此对 `src/think_budget.py` 的改动**（task 5 落地）：
- B4/截断检测保持 `THINK_END in chunk` 文本判断（与 R-TOFU 一致，已被其证明可用）；
- `_gen` 的解码从 v0 的 `skip_special_tokens=False` 改为 **`True`**：v0 当初设 False 的理由（"怕 `<think>` 被当特殊 token 剥掉"，plan §12.1 注意点①）已被上面证据证伪；改 True 可顺带滤掉 `<｜end▁of▁sentence｜>` 等，避免污染 answer 的规则判分（`metrics.hit` 子串匹配），且与 R-TOFU `test.py:39` 对齐。

**仍需在 H200 回填的留点**（非阻塞，task 7 顺带做）：
- 在真·R1-Distill-Qwen-7B tokenizer 上跑一句 `tok("</think>", add_special_tokens=False)` 看它切成几个 piece——只为登记，不影响文本检测正确性；
- 确认迭代式 think 循环里"模型自发 EOS 但未出 `</think>`"是否出现（skip_special_tokens=True 时 EOS 不在文本里，靠 `CAP` 兜底）；R1 系几乎必出 `</think>` 再作答，预计非问题。

## 5. 评测口径审计（防"被包装"，对照章节引用用）

R-TOFU 是 **unlearning** 基准，其 forget 指标全部是"被遗忘知识在输出里残留多少"，与我们 **editing** 的 ES/RR/CLR **口径不同，永不混排**（CLAUDE.md 硬约束 4）：

| R-TOFU 指标 | 定义（源码） | 与我们的关系 |
|---|---|---|
| answer ROUGE-L recall | 参考答案 vs 生成答案，`rougeL.recall`（`test.py:88-90`） | 软匹配；我们 ES 用 o*/o_old 别名子串硬判（`metrics.hit`），不可换算 |
| answer cosine | all-MiniLM-L6-v2 句向量余弦（`test.py:92-95`） | 仅作语义残留参考 |
| CoT ROUGE-L recall | 参考 CoT vs 生成 CoT（`test_cot.py:217-219`） | 与我们 CLR(=o_old 在 CoT 子串命中) **不同**：它是与参考 CoT 的相似度，不是旧知识命中率 |
| 句级 cosine + ROUGE-L | 把 CoT 切句两两取 max（`test_cot.py:61-88`） | 机理章节若要"CoT 片段级泄漏"可借其切句思路，但指标自定义 |
| GPT forgetting score | GPT-4o 打 0.00–1.00（`test_cot.py:146-166`） | LLM-judge 口径；我们若用 judge 复核需另立 prompt 并单独命名 |

雷点登记同时记下：仅评 `task_id == "1"` 的 forget 子集（`test.py:79`、`test_cot.py:207`）；`gpt_fn` 的 `api_key=""` 是占位（`test_cot.py:14`），跑其 GPT 评测要自填——我们不跑。

## 6. 解码细节差异（移植时对齐）

| 维度 | R-TOFU | 我们 `think_budget.py` | 处理 |
|---|---|---|---|
| 解码范围 | decode **整段** `output_ids[0]`（含 prompt）再切 `<think>` | 只 decode **新 token**（`out[0][prompt_len:]`） | 我们更干净；CoT 不含 prompt 回显 |
| skip_special_tokens | True | 已改 True（见 §4） | 对齐 |
| 采样 | `do_sample=False, temperature=1.0`（temp 被忽略=greedy） | `do_sample=False` | 一致；plan §2.5 的 0.6×3 seed 由上层传参，不在本控制器写死 |
| max_new | 2048 单次 | 迭代生成，`CAP` 控总长 + 答案段 256 | 我们要分档预算，故迭代 |
| 预算档 | 仅 Zero/Less/Default 三离散点 | B0–B4 五档（含 s1 式 extend） | extend(B4) 是我们加的，R-TOFU 无 |

## 7. 可复用资产清单

- 三个 prefill 模板 → 已进 `think_budget.{TPL, ZEROTHINK, LESSTHINK_CANNED}`，全角竖线已校验
- 文本切片抽 CoT 的写法（`find("<think>")…find("</think>")`）→ 我们 metrics/机理抽 CoT 时复用
- 句级切分做 CoT 片段相似度的思路（`PunktSentenceTokenizer` 切句两两取 max）→ Phase 3 片段归因可借

## 8. 雷点登记

1. **base 模型不是 Qwen**：R-TOFU 用 R1-Distill-**Llama**-8B；它的解码/口径可直接借，但任何与 tokenizer 细节绑定的结论（已在 §4 对 Qwen-7B 单独核过的除外）不要默认平移到我们的 Qwen-7B 主模型。
2. **LessThink ≠ 我们的 B1/B2/B3**（见 §3）：写作时别误称沿用，要标"推广"。
3. **全角竖线 U+FF5C**：`think_budget.py` 已校验无半角污染；后续任何手敲模板的地方都要重验。
4. **口径不混排**：R-TOFU 的 ROUGE/cosine/GPT-judge 是 unlearning 残留口径，我们的 ES/RR/CLR 是 editing 口径，论文里两套都报也要分开命名（呼应 01 笔记 §4 雷点 2）。

## 9. 遗留 / 待用户或后续阶段决策

- **预算档定义在 plan 内部不自洽**（需用户拍板，属 plan 级改动）：plan §2.4 列 6 档 `{0, 256, 1024, 4096, natural, extend}`，而 plan §12.1 的 harness 代码（=现 `think_budget.py`）是 B0–B4 五档 `{Zero, 256, 1024, 8192, 8192+extend}`，且 task 7 写"5 档"。差异：①§2.4 的 **4096** 在代码里没有独立档；②§2.4 的 **natural** 被 B3(cap=8192) 近似吞掉（CounterFact 类事实 CoT 通常远短于 8192，故 B3 实质≈natural，但它是"高上限截断"不是"真自然长度"）。**建议**：要么把代码对齐成 §2.4 的 6 档（加独立 4096 与真 natural=无上限），要么把 §2.4 改为与代码一致的 5 档——任选其一但需 +0.1 改 plan。本笔记暂不动 enum。
- §4 的 H200 回填留点（tokenizer piece 数、循环 EOS 兜底）——task 7 顺带验。
