# plan.md · AAAI-27 项目总计划

- **项目代号**: `why-aaai` / 内部名「越想越退」(Thinking Undoes Editing)
- **目标**: AAAI-27（2027-02-16/23, 蒙特利尔）。首选 **AI Alignment track**（编辑作为安全干预在 test-time compute 下失效），备选 Main Track
- **硬截止**: abstract **2026-07-20**，全文 **2026-07-27**，补充材料 +3 天（均 UTC-12；以官方 CFP 页为准，本周内再核对一次 track 专属日期）
- **页数约束**: 正文 7 页 + 参考文献；两阶段评审（Phase 1 两人工评审 + 一份 AI 生成非决策评审），故 **摘要/引言/图 1 必须在 Phase 1 就能独立讲完整个故事**
- **版本**: v1.3 (2026-06-10)。决策记录：方向 B′ 经地毯式查新确认窄切口可行（见 `analysis/00_shortlist.md`）；复现队列 7 项已确认；pilot go/no-go 机制生效
- **v1.1 变更**: ① 新增 §2.6 第 4 项混杂（批量编辑干扰）并确立**单条编辑为主协议**；② §5 算力账按单条编辑协议重算（70 → ~400 GPU·h，原估计依赖批量编辑+vLLM 假设，与主协议冲突）；③ 风险表补 R1-Distill-Qwen-7B 基座为 Qwen2.5-**Math**-7B 的超参移植风险与层扫描预案；④ 新增 §11 源码实测附录（hparams 路径、prefill 模板字符串、CPU 冒烟脚本，全部为 2026-06-10 源码确认）
- **v1.2 变更 (2026-06-10)**: ① **单条编辑协议获用户签字确认**（算力 420 GPU·h 预算生效）；② EasyEdit 权重还原机制审计完成（精确逐元素拷回，循环正确性成立，证据见 `analysis/01_easyedit.md` §3）；③ CPU 冒烟因容器磁盘/无 torch 改在本地执行（命令在 01 笔记 §1）；④ 新增 §12 Pilot harness 三模块完整实现代码
- **v1.3 变更 (2026-06-10)**: ① Phase 0 第 3 张复现笔记 `analysis/03_rtofu.md` 完成（R-TOFU 解码协议 + 口径审计）；②【§12.1 注意点② 定案】`<think>`/`</think>` 在 R1-Distill-Qwen-7B 与 -Llama-8B 的 tokenizer 中均**非**特殊 token（查 HF `tokenizer_config.json` 之 `added_tokens_decoder`）→ `</think>` 走文本检测，无需 token-id StoppingCriteria；③ `src/think_budget.py` 用 R-TOFU 逐字 prefill（ZeroThink/LessThink/DefaultCoT，byte-for-byte 校验）替换 v0 占位，`_gen` 解码改 `skip_special_tokens=True`；④【待用户拍板】预算档定义在 §2.4（6 档）与 §12.1 代码（B0–B4 5 档）间不自洽，详见 03 笔记 §9
- **v1.4 变更 (2026-06-10)**: ① task#02 AlphaEdit 笔记 `analysis/02_alphaedit.md` 完成——两实现算法逐行同构，唯一实质超参差异 **L2（EasyEdit=1 vs 官方=10）**；发现 **EasyEdit 内置版 P 预分配缺 qwen 分支的崩溃 bug**（上 Qwen/R1-Distill-Qwen 主模型前必打 vendor_patch，见 02 §4）；P 与 MEMIT 共享 mom2（task#04 一次 cov 喂两编辑器）；② task#07 `src/test_think_budget.py` 写好——mock 控制流 6 测全过（B0 空/截断 CAP/单调/B4 WAIT≤2，think_budget.py **首次实跑**通过），真模型长度分布层待 H200；③ task#03 本地环境就位（Miniconda+editrev py3.10，EasyEdit 全依赖装通，`env.lock` 105 包），踩坑见 01 §6（conda ToS / conda-forge 无 pip / easyeditor 需 PYTHONPATH）；冒烟（GPT-2-XL ROME）进行中；④ task#04（mom2@8×H200）按用户决定**延后**（需实验室专网）
- **v1.5 变更 (2026-06-11)**: ① task#06 数据提取完成——`src/build_dataset.py` 把 CounterFact(21,919)/zsRE(18,377)/MQuAKE-CF-3k(3,000) 清洗为统一 jsonl schema + `data/aliases.json`(1,285 实体)，数据卡 `analysis/06_data.md`；②【zsRE 映射决策】o_old=answers[0]→o_new=**alt**（反事实，与 CF 同语义，有真实 o_old），answers[1:] 是"其它可接受答案"非别名（已排除防判分污染）；③【确诊 pilot-blocker】EasyEdit `edit()` 必传 `subject=`（否则 ROME/MEMIT 取不到 subject 失败），且 `src/edit_loop.py` v0 读 `case['subject']` 而本 schema 字段是 `s`——两处随 Phase 1 接线修（详见 06 §5）；④ 大数据 jsonl/raw gitignore 靠脚本再生；Phase 0 复现笔记余 **04(ThinkEdit)/05(R²MU)** 两张
- **v1.6 变更 (2026-06-11)**: 算卡前 harness 加固——① `src/edit_loop.py` 修 5 个坑（`case['s']` 字段名、`edit()` 传 `subject=`、字符串 case_id 改按 enumerate 序号分片、HP_CLS 补 AlphaEdit/FT、单条 case 出错不拖垮整片且总还原），消除 06 §5 确诊的 pilot-blocker；② `src/metrics.py` 加固（`.get("probe")` 跳过错误标记行、`hit()` 容忍 None 目标）；③ 新增 mock 单测 `src/test_edit_loop.py`(7 测) + `src/test_metrics.py`(2 测，ES/RR/CLR 逐档手算核对)，均无 GPU/依赖、CPU 即过
- **v1.7 变更 (2026-06-11)**: 算卡前 pilot harness 串通（开窗即跑）——① `experiments/pilot.yaml`（R1-Distill-Qwen-7B × {ROME,MEMIT} × CF-200 × {B0,B3,B4}，8 卡分片）；② `src/run_pilot.py` 入口（seed42 确定性抽样、enumerate 分片、续跑、`--dry-run`；用 overrides 把 EasyEdit qwen2.5 yaml 的 model_name→R1-Distill + stats_dir 分目录 + 按 rank 设 device）；③ `src/prefilter.py`（§2.3 预过滤，复用已测 metrics.hit）；④ `edit_loop.run` 加 `overrides` 注入；⑤ `src/test_run_pilot.py`(4 测) + 干跑真配置通过；`results/` gitignore
- **v1.8 变更 (2026-06-11)**: ① 新增 `RUNBOOK.md`——算卡/内网窗口**自助操作手册**（环境→数据→mom2→pilot→打分→go/no-go + AlphaEdit/think_budget 预备 + 雷点速查 + §9 待拍板决策），内网无 Claude 也能照跑完 pilot；② `src/score_pilot.py` 一键打分（glob 分片→ES/RR/CLR，复用已测 metrics，附 go/no-go 判据）；③ CLAUDE.md 指向 RUNBOOK + plan 版本号订正
- **v1.9 变更 (2026-06-11)**: 按 Prompt2「读原文 + 从代码出发」给 01/02/03 各补「论文宣称 vs 代码现实」一节——① EasyEdit：易用=统一接口真但开箱有摩擦，"editing 超 FT reliability" 正是我们要在 think 预算下反证的对象；② AlphaEdit：**零空间阈值 论文脚注 10⁻² vs 代码 2e-2（2×）**、"一行代码"藏了 P 预计算、"+36.7%" 是 sequential（我们单条用不上）、L2 论文省略且两实现不一致；③ R-TOFU：**ZeroThink/LessThink 实为 Jiang et al. 2025 非 R-TOFU 原创**、方向与我们镜像成对、step-wise=句级参考 CoT 相似度、单 Llama 基座。Phase 0 复现笔记余 04(ThinkEdit)/05(R²MU)
- **v1.10 变更 (2026-06-11)**: task#04 ThinkEdit 完成（读 PDF 2503.22048 + 代码）——① 笔记 `analysis/04_thinkedit.md`（方向抽取 Eq1 / steering hook Eq2 / 权重编辑 Eq6 三机制 + 论文宣称 vs 代码现实）；② 通用 steering 工具 `src/steer.py`（`Steerer` 残差流方向注入 hook + 位置掩码条件化 + `extract_direction`，改造自 ThinkEdit 并推广出 F1 要的条件注入）+ `src/test_steer.py` 4 测过（editrev）；③ 关键雷点：ThinkEdit base **无 7B**，方向/头不可跨模型复用，我们 7B 须重抽。**Phase 0 复现笔记余 05(R²MU) 一张**
- **v1.11 变更 (2026-06-11)**: task#05 R²MU 审计完成（读 PDF 2506.12963 + 代码）——`analysis/05_r2mu.md`：① 代码健康度审计（无 requirements/README、自有 8 py vs vendored lm-eval 571 py、judge `temperature=0.0` 被注释→非定温、openai 旧 SDK、judge 模型 gpt-4o/o3/claude 三处不一致）；② 残留口径=LLM-judge **1–4**「推理链是否支持 gold」+ mismatch；③ 结论：口径**定义一致但数值不可独立复现**，只引定义不采数字；④ 三方残留口径分名（R²MU judge1–4 / R-TOFU judge0–1 / 我们 CLR 子串）。**Phase 0 六份复现笔记 01–06 全齐（W1 硬节点 6/17 提前达成）**

---

## 1. 研究命题

### 1.1 一句话主张

参数知识编辑（ROME/MEMIT/AlphaEdit）在关闭思考时看似成功，但随着推理模型思考预算增加，模型在自验证/反思过程中会"想起"旧知识并推翻编辑——我们量化这条剂量-反应曲线，定位回退机理，并给出 training-free 的推理时保护方法。

### 1.2 研究问题与假设

| RQ | 内容 | 假设 | 证伪条件 |
|---|---|---|---|
| **RQ1 现象** | 编辑成功率 ES 是否随思考预算 b 单调下降？ | H1: ES(b) 显著递减，think 相对 no-think 降幅 ≥20pp | 降幅 <20pp 或无单调性 → 项目终止，转 fallback |
| **RQ2 机理** | 回退发生在推理链的哪类片段、由什么驱动？ | H2: 回退集中于自验证/反思片段（"wait/let me check"类），因编辑只改写了浅层 (s,r)→o* 映射，未触及分布式关联知识，反思触发旧知识的关联检索 | 回退位置随机分布、与反思标记无相关 → 机理章节降级为现象学描述，论文吸引力下降 |
| **RQ3 修补** | 能否不重训地保护编辑？ | H3: 在被编辑主体出现的位置做条件化表征引导（damping 反思方向 / 强化新事实方向）可恢复 ≥50% 的 ES 损失，且对 GSM8K/MATH 推理精度损伤 <2pp | 恢复 <30% 或推理损伤 >5pp → 修补章节退化为"编辑增强"方案 F2 |

### 1.3 贡献声明（论文三段式）

1. **现象**: 首个在真 LRM（R1-Distill 系 / Qwen3 think 开关）上对参数编辑方法的 think-budget 剂量-反应系统量化（ES(b)、条件回退率 RR(b)、链内泄漏 Leak(b) 三曲线 × 3 编辑器 × 3 模型）。
2. **机理**: 片段级定位 + 隐层探针证据链，证明回退由反思驱动的旧知识关联检索导致，而非随机解码噪声。
3. **方法**: training-free 的 edit-aware reasoning 保护（推理时条件化 steering），在不损害推理能力的前提下显著恢复编辑存续性。

### 1.4 与近邻的差异化（审稿人答辩预案，全部必引）

| 近邻 | 它做了什么 | 我们的差异（一句话答辩） |
|---|---|---|
| R²MU (2506.12963) | LRM 上 **unlearning** 的 CoT 残留 + 训练式修补 | 我们做 **editing**（改知识而非删知识，失效模式是"回退到旧答案"而非"泄漏被删内容"），且修补 training-free |
| R-TOFU (2505.15214) | LRM unlearning 基准，发现 ZeroThink/LessThink 暴露残留 | 我们借其解码协议作自变量，但研究对象（参数编辑）、因变量（编辑回退）、方向（**更多**思考导致失效，与其"更少思考暴露残留"互补成对）均不同 |
| ThinkEval/KnowGIC (2506.01386) | 用 CoT 构造知识图谱评测编辑的间接泄漏 | 它在标准模型上用 CoT prompting 构图做评测；我们在原生 LRM 上把思考预算作为连续自变量，并给出机理与修补 |
| KELE (2408.12456) | 残留旧知识致多跳回退（GPT-2/GPT-J 时代）+ 擦除式编辑 | 它是多跳问题结构导致的回退；我们是 test-time compute 本身导致的回退，且在 LRM 上 |
| 2602.02028 | 附录记录"推理中自我纠正回先验"案例，提出 background-story 训练式编辑 | 它的回退是轶事性观察 + 训练式修补；我们系统量化 + 机理 + training-free 修补 |
| ThinkEdit (2503.22048) / ReflCtrl (2512.13979) | 推理长度/反思行为可由表征工程控制 | 我们借其干预机械，但目标全新：保护编辑事实而非调节推理长度 |
| MQuAKE (2305.14795) | 多跳评测数据 | 仅作数据源与历史定位 |

---

## 2. 实验设计总则

### 2.1 模型矩阵

| 模型 | 角色 | think 控制方式 | 备注 |
|---|---|---|---|
| **DeepSeek-R1-Distill-Qwen-7B** | 主力 | ZeroThink（强制空 `<think>\n\n</think>`）↔ 自然思考 ↔ 强制延长 | Qwen2.5 架构，EasyEdit 兼容；R-TOFU 协议直接移植 |
| **Qwen3-8B** | 最干净的对照 | 官方 `enable_thinking` 开关，同权重同模板 | 排除"模板差异"混杂的关键证据；编辑兼容性 W1 验证 |
| **R1-Distill-Llama-8B** | 架构泛化 | 同 R1-Distill 协议 | Llama3 架构 |
| R1-Distill-Qwen-14B | 规模检查（仅主结果复测） | 同上 | 算力富余时跑 |

### 2.2 编辑器矩阵

| 编辑器 | 实现来源 | 备注 |
|---|---|---|
| **ROME** | EasyEdit | 单事实定位编辑，经典基线 |
| **MEMIT** | EasyEdit | 批量编辑，主力 |
| **AlphaEdit** | EasyEdit 内置版为主，官方仓库对照超参 | SOTA，零空间投影 |
| LoRA-FT 编辑 | EasyEdit (FT-L) | 微调式基线 |
| ICE（in-context editing） | 自实现（prompt 注入新事实） | 非参数对照：检验"上下文注入是否同样被反思推翻" |

前置依赖：为每个目标模型预计算 mom2 协方差统计（EasyEdit 自动缓存，约 4–6 GPU·h/模型，一次性）。

**协议决策（v1.1，影响全部算力与结论强度）**: 主实验采用**单条编辑协议**——每条 case 独立执行"编辑→全预算档生成→还原权重"，杜绝编辑间干扰混杂（KELE 与 MQuAKE 的规模化实验均表明批量编辑本身即放大失效，若用批量协议，审稿人无法区分回退归因于思考还是归因于批量干扰）。批量编辑（MEMIT/AlphaEdit @ batch=100）降级为一个附加消融（"批量×思考的交互效应"，半页），用 vLLM 评测。代价：主矩阵生成无法吃 vLLM 吞吐，按 HF batched generate 计价，见 §5。

### 2.3 数据

| 数据集 | 用途 | 规模 |
|---|---|---|
| **CounterFact**（memit 仓库） | 主编辑数据：ES/Paraphrase/Neighborhood | pilot 200 条 → 主实验 1,000 条 |
| zsRE（memit 仓库） | 第二编辑分布 | 主实验 500 条 |
| MQuAKE-CF-3k（MQuAKE 仓库） | 多跳扩展（portability 章节） | 500 条 |
| GSM8K-200 / MATH500-100 子集 | 修补方法对推理能力的副作用检查 | 固定抽样，种子 42 |

**预过滤（关键）**: 仅保留"模型在编辑前确实知道旧事实"的条目（pre-edit 对 (s,r) 的 greedy 输出 = o_old），否则"回退"无从定义。预计过滤后存活率 40–60%，故原始抽样×2 冗余。

### 2.4 思考预算操纵协议（自变量 b，6 档）

| 档位 | 实现 | 来源 |
|---|---|---|
| b=0 (ZeroThink) | 强制注入空思考块后直接答 | R-TOFU 协议 |
| b=256 / 1024 / 4096 (LessThink 系列) | 思考至 N token 截断，强制 `</think>` 收尾作答 | R-TOFU LessThink 推广 |
| b=natural | 自然解码 | — |
| b=extend (≈2×natural) | 抑制 `</think>`，注入 "Wait," 续写（budget forcing） | s1 (Muennighoff et al. 2025) |

### 2.5 指标定义

设编辑 e=(s,r,o_old→o*)，思考预算 b，模型回答 A(e,b)，思考链 C(e,b)：

- **ES(b)** = E_e[ 1{A(e,b)=o*} ]，编辑成功率曲线（主图 1）
- **RR(b)** = P( A(e,b)=o_old | A(e,0)=o* )，**条件回退率**——零思考下成功的编辑中，b 预算下回到旧答案的比例（主指标，剔除"本来就没编成功"的噪声）
- **Leak(b)** = P( o_old ∈ C(e,b) )，链内旧知识提及率
- **FlipPoint**: C 中模型立场从 o* 翻向 o_old 的首个 token 位置（机理用）
- **Locality / Portability**: CounterFact 标准 Neighborhood / Paraphrase 指标，确认编辑本身质量达标（达不到则该编辑器结果整体作废）
- **ΔReason**: 修补前后 GSM8K-200 与 MATH500-100 准确率变化（修补副作用）
- 统计：每条 greedy + temperature 0.6 × 3 seeds；置信区间 95% bootstrap（按编辑条目重采样，n=10,000）

### 2.6 混杂变量控制（审稿人最会捅的四刀）

1. **模板混杂**: think/no-think 必须使用**完全相同的 chat template**，仅思考块内容不同（ZeroThink 注入空块而非删除模板）。Qwen3 的官方开关提供同权重双模式的黄金对照。
2. **长度混杂**: "想得多→错得多"可能是长序列退化而非知识回退。对照组：对**未编辑**模型问同一批 (s,r)，测其答 o_old 的稳定性随 b 的变化——若未编辑模型稳定而编辑模型回退，则归因于编辑脆弱性。
3. **采样噪声**: 所有曲线同时报告 greedy 与 3-seed 采样均值±CI；结论必须在 greedy 下同样成立。
4. **批量编辑干扰**: 主结果一律单条编辑协议（见 §2.2）；批量场景单列为交互效应消融，绝不与主曲线混排。

---

## 3. 阶段计划

```mermaid
flowchart LR
    P0["Phase 0<br/>复现循环<br/>6/10-6/17"] --> P1["Phase 1<br/>Pilot<br/>6/18-6/22"]
    P1 -->|"go: RR降幅≥20pp<br/>且机理干净"| P2["Phase 2<br/>主实验矩阵<br/>6/23-7/3"]
    P1 -->|"no-go"| FB["Fallback<br/>方向A重启<br/>(预案见§9)"]
    P2 --> P3["Phase 3<br/>机理分析<br/>6/30-7/8"]
    P2 --> P4["Phase 4<br/>修补方法<br/>7/4-7/12"]
    P3 --> P5["Phase 5<br/>写作提交<br/>7/8-7/27"]
    P4 --> P5
```

### Phase 0 · 复现循环（step ③，6/10–6/17）

每个仓库一张任务卡，产出 `analysis/0X_<name>.md`，统一模板：环境搭建记录 → 代码结构图 → 冒烟测试结果 → 核心优缺点（**从代码出发**）→ 对本项目的可复用资产清单 → 雷点登记。

| # | 仓库 | 容器内做什么（CPU） | H200 上验证什么 | 完成标准 |
|---|---|---|---|---|
| 01 | EasyEdit | 装环境；GPT-2-XL 上 CPU 跑通 ROME 单条编辑全流程；通读 `easyeditor/models/{rome,memit}` 与 hparams 体系；确认 Qwen2.5 hparams 模板存在 | R1-Distill-Qwen-7B 单条 ROME 编辑 + mom2 缓存生成 | 笔记 + 可直接排队的编辑脚本 `src/edit_runner.py` |
| 02 | AlphaEdit | 对照 EasyEdit 内置 AlphaEdit 与官方仓库超参差异；审计零空间投影实现是否与论文公式一致 | 同一 100 条编辑两实现 ES 差 <2pp | 实现选型决议写入笔记 |
| 03 | R-TOFU | 精读 `test_cot.py` 与解码控制；提取 ZeroThink/LessThink 实现为独立模块 `src/think_budget.py`；审计其指标与论文表格口径 | 在未编辑 R1-7B 上验证 6 档预算控制器产出预期长度 | 预算控制器单测通过 |
| 04 | ThinkEdit | 通读方向抽取与 head 定位代码；改造为通用 steering 工具 `src/steer.py`（任意方向、条件化注入） | 复现其 GSM8K 短思考缓解的方向有效性（抽样 100 题） | steering 工具可用 |
| 05 | R²MU | **审计级**：核对其评测脚本与论文表格口径；记录其 CoT 残留度量定义以便对比章节引用 | 不跑训练 | 口径核对结论（一致/不一致及证据） |
| 06 | MQuAKE/memit | 数据提取：CounterFact、zsRE、MQuAKE-CF-3k 清洗为统一 jsonl schema `{case_id, s, r, o_old, o_new, paraphrases[], neighborhood[], hops[]}` | — | `data/` 下三个清洗后数据集 + 数据卡 |

### Phase 1 · Pilot 与 go/no-go（6/18–6/22，硬节点 **6/22**）

- 配置: R1-Distill-Qwen-7B × {ROME, MEMIT} × CounterFact-200（预过滤后）× b∈{0, natural, extend} × {greedy, 0.6×3}
- 产出: ES/RR/Leak 三指标初表 + 30 条回退样本人工审计（审计字段：case_id, b, FlipPoint, 触发片段类型∈{自验证, 关联回忆, 重述质疑, 其他}, 摘录）
- **go 判据（两条同时满足）**: ① RR(natural) ≥ 20pp 或 ES 降幅 ≥20pp，至少在一个编辑器上成立且另一个方向一致；② 人工审计中 ≥60% 回退案例可归因于反思/自验证片段
- no-go → 当日启动 §9 fallback，沉没成本封顶 12 天
- H200 预算: 编辑 ~2 GPU·h + 生成 ~4 GPU·h + mom2 缓存 6 GPU·h ≈ **一次 4–6 小时的 8 卡窗口即可**；排不上队则按 §6 云端逃生

### Phase 2 · 主实验矩阵（6/23–7/3）

- 全矩阵: 3 模型 × 4 编辑器（ROME/MEMIT/AlphaEdit/FT-L）+ ICE 对照 × 6 档预算 × CounterFact-1000 + zsRE-500
- 每个 cell 产出标准 jsonl（含完整 CoT 文本，供 Phase 3 复用，**只生成一次**）
- 锁定主图: 图1 ES(b) 多编辑器曲线；图2 RR(b) + 未编辑对照；图3 Leak(b) 与 FlipPoint 分布
- 周中检查点 6/27: 若 Qwen3-8B 编辑兼容性失败（mom2/层定位问题），降级为 R1-Distill 双架构故事，Qwen3 仅 ICE 对照

### Phase 3 · 机理分析（6/30–7/8，与 Phase 2 尾部并行）

1. **片段归因**: 反思标记词典（wait/but/actually/let me verify/double-check/hmm/再想想…）自动标注 CoT 片段；统计 FlipPoint 落入反思片段的比例 vs 随机基线（置换检验 p<0.01）
2. **隐层证据**: 在 s 的提及位置逐层做 logit lens / 线性探针，度量 o_old 与 o* 的相对强度沿思考过程的演化；预期看到：编辑层之后 o* 占优 → 反思片段中 o_old 关联通路重新激活
3. **剂量机制**: RR 与反思片段数量/占比的回归（控制总长度），区分"想得久"与"反思多"两个因素

### Phase 4 · 修补方法（7/4–7/12）

按优先级实现与评测，主推 F1：

- **F1 Edit-aware steering（主方法）**: 用 ThinkEdit 管线在编辑前后模型上抽取"质疑-编辑事实"方向；推理时检测 s 的提及，仅在其后 k 个 token 窗口注入 −α·(质疑方向) 或 +β·(新事实方向)；α,β 在 dev-100 上网格搜索
- **F2 编辑增强（备选/叠加）**: MEMIT 批量编辑 {原事实 + K 条 paraphrase + 2-hop 蕴含}，正面提高编辑"深度"
- **F3 解码护栏（弱基线）**: 答案位置对 o_old 词元 logit-bias
- 评测: 保护后 ES(b)/RR(b) 恢复量；ΔReason（GSM8K-200/MATH500-100）；与 ICE、system-prompt 断言两个非参数基线对比；开销报告（额外延迟）

### Phase 5 · 写作与提交（7/8–7/27）

- 7/8 论文骨架（7 页布局：1 引言+图1 / 2 相关工作 / 3 设定与协议 / 4 现象 / 5 机理 / 6 方法 / 7 实验 / 8 结论）；图表清单冻结
- 7/14 全文 v1 内审；**增量查新第二轮**（关键词见 §8，重点扫 6/10 之后的新 arXiv）
- 7/18 v2 定稿；reproducibility checklist 填写；匿名代码仓整理（4open.science）
- **7/20 abstract 提交**（OpenReview；**全员本周内注册 OpenReview 账号**——新账号有人工审核延迟，这是隐形死线）
- 7/27 全文提交；+3 天补充材料（代码、完整 CoT 样本、审计表）

---

## 4. 时间线总览

| 周 | 日期 | 主线 | 硬节点 |
|---|---|---|---|
| W1 | 6/10–6/17 | Phase 0 复现循环（01→06） | 6/17 六份复现笔记齐 |
| W2 | 6/18–6/24 | Phase 1 pilot | **6/22 go/no-go** |
| W3 | 6/25–7/1 | Phase 2 主矩阵 | 6/27 Qwen3 兼容性检查点 |
| W4 | 7/2–7/8 | Phase 2 收尾 + Phase 3 机理 + Phase 4 启动 | 7/8 主图三张冻结 |
| W5 | 7/9–7/15 | Phase 4 修补 + 写作 v1 | 7/14 内审 + 二轮查新 |
| W6 | 7/16–7/22 | 打磨、checklist、匿名仓 | **7/20 abstract** |
| W7 | 7/23–7/27 | 全文终稿 | **7/27 全文**，7/30 补充材料 |

缓冲设计：Phase 2 的生成任务全部缓存 CoT 原文，Phase 3/4 不再消耗大额 GPU；W5 之后理论上零排队依赖。

---

## 5. 算力计划（8×H200 共享，排队不保证；v1.1 按单条编辑协议重算）

主矩阵规模控制（与协议联动的网格裁剪）：完整 6 档预算网格只给 **MEMIT 与 AlphaEdit**（headline 编辑器）；ROME / FT-L 跑 3 档（b∈{0, natural, extend}）；zsRE 只跑 MEMIT+AlphaEdit。单条 case 成本 ≈ 编辑 0.5–1 min + 生成（5 探针 × 档数，CapThink 档天然短，均摊 ≈2.5k token/条，HF batched generate）≈ 2–4 min。

| 任务 | 估算 | 形态 |
|---|---|---|
| mom2 统计 ×3 模型（一次性缓存） | ~15 GPU·h | 可中断，**今天提交排队** |
| Pilot（200 case × 2 编辑器 × 3 档） | ~15 GPU·h | 按 case_id 分 8 片 |
| 主矩阵·主力模型（CF-1000：MEMIT/AlphaEdit 全档 + ROME/FT-L 三档；zsRE-500 × 2 编辑器） | ~220 GPU·h | 切 ≤2h 任务，jsonl 续跑 |
| 副模型（R1-Distill-Llama-8B / Qwen3-8B：各 1–2 编辑器 × 300 case × 3 档） | ~50 GPU·h | 同上 |
| 未编辑对照 + ICE + 批量编辑消融（共享权重，**vLLM 可用**） | ~20 GPU·h | 单任务 |
| 机理（logit lens / 截断因果，复用 Phase 2 缓存 CoT） | ~30 GPU·h | 单卡碎片 |
| 修补（F1 方向抽取 + 网格搜索 + 三案评测@dev-100，终选案全量复测） | ~60 GPU·h | 分片 |
| **合计 + 15% buffer** | **~420 GPU·h ≈ 8 卡 × 53 h** | 6 周摊薄 ≈ 每周一个 8–10h 窗口，可行 |

纪律：① 任何任务可在 1 小时粒度中断续跑（编辑 delta、生成 jsonl、探针缓存三级落盘）；② 环境 Docker 化（基于 EasyEdit Dockerfile 扩展），保证 H200/云端/容器三处一致；③ **云端逃生**：截稿前 10 天若累计排队损失 >3 天，启用 RunPod/Lambda 8×H100（~$20/h），预算上限 $400 ≈ 160 GPU·h，**只保关键路径**（pilot 复核 + 主力模型 MEMIT/AlphaEdit 全档 + 终选修补），副模型与消融可降级为附录承诺。

---

## 6. 工程规范

```
why-aaai/
├── papers/          # 论文 PDF（repro_/ref_ 前缀）
├── source/          # 第三方代码（只读，不在内部改动）
├── analysis/        # 复现笔记 0X_*.md + 本计划衍生决议
├── src/             # 我们的代码：edit_runner / think_budget / steer / probes / metrics
├── data/            # 清洗后数据集 + 数据卡
├── experiments/     # 每实验一个 yaml 配置（模型/编辑器/预算/种子全显式）
├── results/         # jsonl 输出，命名 {model}_{editor}_{dataset}_{b}_{seed}.jsonl
└── paper/           # LaTeX（AAAI-27 author kit）
```

- 可复现三件套：全局种子显式、每个 jsonl 头部写入 git commit hash + 配置摘要、所有图表由 `src/plots.py` 从 results/ 一键再生
- 评测与生成解耦：CoT 文本是一等资产，先存后析
- 第三方代码只读引用，需要改的部分 fork 进 `src/vendor_patches/` 并记录 diff

---

## 7. 风险登记

| 风险 | 概率 | 缓解 |
|---|---|---|
| 撞车（6/10 后出现同命题论文） | 高 | 每周一 arXiv 增量扫描（§8 关键词）；若被抢现象，pivot 强调机理+修补（方法论文化）；若机理也被抢，剩余素材转 workshop |
| pilot 不成立 | 中 | §9 fallback，12 天沉没成本封顶 |
| ROME/MEMIT 在 R1-Distill 上编辑质量本身不达标（Locality 崩） | 中 | 注意 R1-Distill-Qwen-7B 基座是 Qwen2.5-**Math**-7B（非通用版），EasyEdit qwen2.5-7b hparams 仅架构兼容、超参未必最优：冒烟期做 layers ∈ {[4-8],[6-10],[8-12]} 小扫描，以 B0 下 ES≥90% 且 Locality≥85% 为合格线；仍不达标则先以 Qwen2.5-7B-Instruct（同架构非推理版）验证编辑质量基线，主模型改 Qwen3-8B |
| 排队完全拿不到卡 | 中 | 云端逃生 $400 预算；pilot 仅需一个 4–6h 窗口，优先抢 |
| Qwen3 编辑不兼容 | 中 | 6/27 检查点降级预案已写入 Phase 2 |
| 7 页装不下三段式 | 低 | 机理细节与第二数据集进附录；正文保 RQ1+RQ3 完整 |

## 8. 查新维护（每周一执行，30 分钟）

arXiv 关键词组：`knowledge editing + reasoning model`；`edit + chain-of-thought + revert/override`；`test-time compute + knowledge`；`unlearning + reasoning leakage`；`R1 + editing`。盯防对象：zjunlp（EasyEdit 组）、OPTML-Group、ai-isl（R-TOFU 组）、2602.02028 作者组的新作。

## 9. Fallback：方向 A 重启简案（仅 no-go 时启用）

推理链内部信号早停（hidden-state probe 预测链成败 → early-exit/重路由）。资产复用率高：think_budget 控制器、vLLM 管线、CoT 缓存、探针代码全部直接迁移；重启后 4 周压缩计划（1 周 pilot、2 周主实验、1 周写作），牺牲机理深度保 phenomenon+method 两段式。届时另出 plan_A.md。

---

## 10. 立即行动（本周）

1. [ ] 全员注册 OpenReview（防新账号审核延迟）
2. [ ] 核对 AAAI-27 官方 CFP 的 Alignment track 专属日期与 author kit
3. [ ] Phase 0 启动：`analysis/01_easyedit.md`（容器内环境 + GPT-2 CPU 冒烟）
4. [ ] H200 排队申请：W2 一个 6 小时 8 卡窗口（pilot 用），W3 起每周两个窗口

---

## 11. 附录 · 源码实测事实（2026-06-10 确认，写代码时以此为准）

### 11.1 EasyEdit 关键路径（`source/EasyEdit/`，最后提交 2026-06-10）

- hparams 已存在且无需新写：`hparams/ROME/qwen2.5-7b.yaml`、`hparams/MEMIT/qwen2.5-7b.yaml`、`hparams/AlphaEdit/qwen2.5-7b.yaml`
- MEMIT/AlphaEdit 共同配置（移植到 R1-Distill 时仅改 `model_name`，其余先沿用再扫描）：`layers: [4,5,6,7,8]`；`rewrite_module_tmp: "model.layers.{}.mlp.down_proj"`；`mom2_dataset: wikipedia, n=100000, float32`；AlphaEdit 额外需要 `P_loc: ./null_space_project.pt`（首跑生成）
- 编辑 API（`edit.py` 实测）：`BaseEditor.from_hparams(hparams)` → `editor.edit(prompts, ground_truth, target_new, sequential_edit=False)`，返回 `(all_metrics, edited_model, weights_copy)`（editor.py:288）
- **权重还原机制（已审计确认，01 笔记 §3）**: `weights_copy` 仅克隆被改写矩阵（rome_main.py:39-50，MEMIT 5 层 ≈650MB 显存）；还原为逐元素精确拷回 `nethook.get_parameter(model, k)[...] = v`（editor.py:265 模式）。单条编辑循环 = edit → 全档生成 → restore，正确性成立

### 11.2 思考预算控制（`source/R-TOFU/` 实测）

- 聊天模板（`test_cot.py:243-245`，注意全角竖线）：`<｜User｜>{prompt}<｜Assistant｜><think>\n`，无 system prompt
- ZeroThink/LessThink 的 prefill 实现在 `test.py:15-20`（闭合 think 块预填充）；CoT 抽取按 `<think>…</think>` 切片（`test_cot.py:250-253`）
- ExtendThink 实现要点（s1 式）：流式监测 `</think>`，命中即替换为 `\nWait, let me double-check this.` 续写，最多 2 次
- **(v1.3 补)** base 模型 = `DeepSeek-R1-Distill-Llama-8B`（**非 Qwen**，`config/tofu.yaml:2`）；上述三 prefill 串已逐字校验进 `src/think_budget.py`；`<think>`/`</think>` 两模型均非特殊 token，B4 走文本检测——详见 `analysis/03_rtofu.md` §3–§4

### 11.3 Phase 0 容器冒烟脚本（完整代码，落 `src/smoke_rome_gpt2.py`）

```python
from easyeditor import BaseEditor, ROMEHyperParams

hparams = ROMEHyperParams.from_hparams('./hparams/ROME/gpt2-xl')
hparams.device = 'cpu'                      # 容器无 GPU
editor = BaseEditor.from_hparams(hparams)
metrics, edited_model, _ = editor.edit(
    prompts=['The Eiffel Tower is located in'],
    ground_truth=['Paris'],
    target_new=['Rome'],
    sequential_edit=False,
)
print(metrics)
```
运行：`cd source/EasyEdit && pip install -r requirements.txt && python ../../src/smoke_rome_gpt2.py`
预期：输出 metrics 中 `rewrite_acc == 1.0`（CPU 约 10–20 分钟）。任何依赖坑记入 `analysis/01_easyedit.md` 的雷点登记。

### 11.4 工作区同步纪律

本工作区存在多写入端（本地 Claude Code 会话 + 网页会话容器镜像）。规则：**plan.md 与 analysis/ 笔记以本地仓库为唯一真源**，容器侧产出一律经 outputs 交付后由人工合入本地并 git commit；版本号与变更记录写在 plan.md 头部，避免双端覆盖。

---

## 12. 附录 · Pilot Harness 完整实现（v0，三模块，落 `src/`）

约定：分片并行按 `case_id % 8 == GPU_RANK` 切 8 片，每片独占 1 卡；jsonl 追加写 + 启动时跳过已完成 case_id（可中断续跑）。代码以 §11 实测 API 为准，跑通后 `pip freeze > env.lock`。

### 12.1 `src/think_budget.py` — 思考预算控制器（B0–B4）

> **v1.3 注**：下方为 v0 基线快照；现行实现以 `src/think_budget.py` 为准（已按 `analysis/03_rtofu.md` §3–§4 用 R-TOFU 逐字 prefill 替换占位、`_gen` 解码改 `skip_special_tokens=True`）。

```python
import torch

TPL = "<｜User｜>{q}<｜Assistant｜><think>\n"   # 全角竖线，DeepSeek 官方模板
THINK_END = "</think>"
WAIT = "\nWait, let me double-check this."
CAP = {"B1": 256, "B2": 1024, "B3": 8192, "B4": 8192}

def _gen(model, tok, text, max_new):
    ids = tok(text, return_tensors="pt").to(model.device)
    out = model.generate(**ids, max_new_tokens=max_new, do_sample=False,
                         pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][ids["input_ids"].shape[1]:],
                      skip_special_tokens=False)

def _ntok(tok, s):
    return len(tok(s, add_special_tokens=False)["input_ids"])

def generate_with_budget(model, tok, q, budget):
    """返回 (cot, answer, full_text)。budget ∈ {B0,B1,B2,B3,B4}"""
    if budget == "B0":                      # ZeroThink: 闭合空思考块
        text = TPL.format(q=q) + "\n" + THINK_END + "\n\n"
        ans = _gen(model, tok, text, 256)
        return "", ans, text + ans
    prefix, cot, waits = TPL.format(q=q), "", 0
    while True:
        chunk = _gen(model, tok, prefix + cot,
                     max(64, CAP[budget] - _ntok(tok, cot)))
        if THINK_END in chunk:              # 模型自行结束思考
            head = chunk.split(THINK_END)[0]
            if budget == "B4" and waits < 2:       # s1 式强制延长
                cot += head + WAIT; waits += 1; continue
            cot += head; break
        cot += chunk
        if _ntok(tok, cot) >= CAP[budget]: break   # B1/B2 截断 / 预算耗尽
    text = prefix + cot + "\n" + THINK_END + "\n\n"
    ans = _gen(model, tok, text, 256)
    return cot, ans, text + ans
```

注意点（v1.3 定案，证据见 `analysis/03_rtofu.md` §4）：① 已查实 `<think>`/`</think>` **非**特殊 token（不在 R1-Distill-Qwen-7B / -Llama-8B 的 `added_tokens_decoder`），原 `skip_special_tokens=False` 的理由（怕被剥）作废，现行 `think_budget.py` 解码改 `skip_special_tokens=True`（顺带滤 EOS，避免污染规则判分）；② B4 的 `</think>` 检测**确定走文本**（`THINK_END in chunk`），无需 token-id 级 StoppingCriteria。

### 12.2 `src/edit_loop.py` — 单条编辑协议主循环

```python
import json, os, torch
from easyeditor import BaseEditor, ROMEHyperParams, MEMITHyperParams
from easyeditor.util import nethook
from think_budget import generate_with_budget

HP_CLS = {"ROME": ROMEHyperParams, "MEMIT": MEMITHyperParams}

def restore(model, weights_copy):           # editor.py:265 同款
    with torch.no_grad():
        for k, v in weights_copy.items():
            nethook.get_parameter(model, k)[...] = v

def probes(case):                            # 探针：efficacy/paraphrase/locality/open
    yield "efficacy", case["prompt"]
    for i, p in enumerate(case.get("paraphrases", [])[:2]):
        yield f"para{i}", p
    if case.get("neighborhood"):
        yield "locality", case["neighborhood"][0]
    yield "open", f"Tell me about {case['subject']}."

def run(cases, editor_name, hparams_path, budgets, out_path, rank=0, world=1):
    done = set()
    if os.path.exists(out_path):
        done = {json.loads(l)["case_id"] for l in open(out_path)}
    hp = HP_CLS[editor_name].from_hparams(hparams_path)
    ed = BaseEditor.from_hparams(hp)
    model, tok = ed.model, ed.tok
    with open(out_path, "a") as f:
        for c in cases:
            if c["case_id"] % world != rank or c["case_id"] in done:
                continue
            _, _, wcopy = ed.edit(prompts=[c["prompt"]],
                                  ground_truth=[c["o_old"]],
                                  target_new=[c["o_new"]],
                                  sequential_edit=False)
            try:
                for b in budgets:
                    for ptype, q in probes(c):
                        cot, ans, _ = generate_with_budget(model, tok, q, b)
                        f.write(json.dumps({"case_id": c["case_id"],
                            "editor": editor_name, "budget": b, "probe": ptype,
                            "q": q, "cot": cot, "answer": ans},
                            ensure_ascii=False) + "\n")
                f.flush()
            finally:
                restore(model, wcopy)        # 任何异常也必须还原
```

### 12.3 `src/metrics.py` — ES / RR / CLR 计算（规则判分 + 别名表）

```python
import json, collections

def hit(text, target, aliases):
    cands = [target] + aliases.get(target, [])
    return any(c.lower() in (text or "").lower() for c in cands)

def score(jsonl_path, cases, aliases):
    cmap = {c["case_id"]: c for c in cases}
    by = collections.defaultdict(dict)       # case_id -> budget -> efficacy行
    for line in open(jsonl_path):
        r = json.loads(line)
        if r["probe"] == "efficacy":
            by[r["case_id"]][r["budget"]] = r
    es = collections.Counter(); rr = collections.Counter()
    clr = collections.Counter(); n = collections.Counter(); n_b0 = 0
    for cid, buds in by.items():
        c = cmap[cid]
        b0ok = ("B0" in buds
                and hit(buds["B0"]["answer"], c["o_new"], aliases)
                and not hit(buds["B0"]["answer"], c["o_old"], aliases))
        n_b0 += b0ok
        for b, r in buds.items():
            n[b] += 1
            es[b] += (hit(r["answer"], c["o_new"], aliases)
                      and not hit(r["answer"], c["o_old"], aliases))
            clr[b] += hit(r["cot"], c["o_old"], aliases)
            if b0ok and hit(r["answer"], c["o_old"], aliases):
                rr[b] += 1                    # 条件回退（plan §2.5 定义）
    return {b: {"ES": es[b]/n[b], "CLR": clr[b]/n[b],
                "RR": rr[b]/max(n_b0, 1), "n": n[b]} for b in sorted(n)}
```

判分校准：抽 10% 边界样本人工/judge 复核（plan §2.5）；别名表 `data/aliases.json` 由 CounterFact 实体的 Wikidata 别名生成（06 号数据笔记任务）。

