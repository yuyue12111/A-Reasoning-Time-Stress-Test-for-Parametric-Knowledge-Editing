# ARR 修订计划（2026-09-28 起本项目唯一权威）

目标：ARR 2026-10-12 AoE（NAACL/COLING 2027 共用周期，12/23 meta-review 后再选投哪个）。
唯一原则：**让论文变好**。本文件取代 `plan.md`（历史档）与 `paperwriting/WRITING_PLAN.md`（AAAI 冲刺期写作计划）。

## 0 为什么改
- AAAI-27 Phase-1 拒（3/c4、6/c3）。决定性拒因是可读性（审稿原文 `official-review.md`）。
  实质意见：只有 2/6 显著且未做多重比较；池由 Qwen-7B@B3 筛；只有 ROME + CounterFact；edited vs base
  没有正式对比；permissive RR 精度 .48；漏引 MQuAKE / Ju et al. 2024。
- AAAI 期的约定（投稿前零新数字、逐句加固 caveat、fp32 HF 单条串行、每次运行一个 yaml）服务于"不留攻击面"，
  产出的是经得起逐句挑剔、却读不懂的论文。**全部作废**，除第 5 节保留的防雷规则。

## 1 论文的新骨架
两段式：**Study 1 = Discovery**（AAAI 已有数据，只做重分析）+ **Study 2 = Confirmatory**（预注册、新池、新引擎）。
主张层级（写作也按这个顺序）：
1. **缺口**：同一条编辑，零思考下通过，原生推理后失效（配对 ES 降幅，Holm 校正）。
2. **编辑特异**：推理后，编辑答案被放弃的比例是模型原生答案的 2–3 倍（留存对比）。
3. **规模结构**：侵蚀在所有尺度都存在；小模型的链同时在"修复"失败的编辑，修复随规模消失 → 净缺口在大模型浮现。
4. **链上因果控制点**：只在思考段压旧答案首 token，未触碰的答案被改变；压新答案方向相反；placebo/竞争者不动。
5. **机制**（视结果）：编辑在推理链里还"点火"吗（key-miss）？编辑越"合理"越稳吗（先验重申）？
自然链中介仍不声称；干预是双 oracle 的诊断探针，不是部署防御。

## 2 Study 1 已确定的结果（`src/rt/study1.py` → `paperwriting/revision/study1.{json,md}`；六格与 results.json 逐位一致）
| 量 | 结果 |
|---|---|
| Holm(6 格) ES 降幅 | 70B p=.0036（Holm .022），32B p=.0066（Holm .033）均过；其余四格不过 |
| 留存对比（base@B0 答旧 ∧ 编辑@B0 成功） | 编辑丢失 − 原生丢失：14B +.195 [.069,.322]，32B +.216 [.091,.341]，70B +.234 [.117,.351] |
| 名字泄题（主语名含旧值，46/200） | 32B RR .60 vs 其余 .156；排除后 ES 降幅 32B .118，70B .117 仍显著 |
| 逐模型资格（各自 base@B0 知道旧值） | 32B .125 [.033,.217]，70B .153 [.076,.229]；小模型在"知道"层内仍≈0 |
| 侵蚀 / 修复 | 侵蚀 6 格全>0（.128→.207）；修复随规模降（1.5B .153 → 32B .101，70B .085） |
| 采样可靠性（32B） | B0 通过的编辑 61% 在 3 次推理采样中至少败 1 次；B0 重复采样噪声底 34% |
| 长度 / 国籍形容词 | 高端无答案变长；demonym 重打分不改结论 |
| 反面结果（不作证据） | base 的 thinking-to-recall 率 > 编辑回退率（case 构成不同）；"关系类型线索"方向相反（被名字泄题混杂） |
| 五臂运行环境 | B0 处 T 与 N 逐字节相同 200/200（同一环境）；D/P/C 与 N 仅 12/200 相同、B0 ES 一致 85% → **只有 T−N 是同环境对比**，T−P/T−C/D−N 混入了环境差异；placebo 臂磁盘数据已与 results.json 的 n=199 版本不同，旧版不可重建 |
结论：**permissive RR 19.3% 退出头条**；头条 = ES 缺口 + 留存对比 + 采样可靠性；Study 1 的因果臂只以 T−N 为主，Study 2 所有臂必须同一次运行。
（Holm/CI 以 study1.json 为准：统一按 case_id 排序重采样，与 cross_arm 一致。）

## 3 Study 2 设计（预注册要点；正式文本 `prereg-arr.md` 在任何 Study-2 delta 计算前冻结）
- **池**：CounterFact 21,919 条，剔除历史上用过的全部 case_id → seed 2027 洗牌 → 前 1600 为候选 →
  每个模型用自己的未编辑 base 在 B0 筛：旧值命中 ∧ 新值未命中（现行 matcher、去主语）∧ 主语名不含旧值 →
  每模型取前 400 条合格（顺序固定）。不再用任何 B3 输出选池。
- **模型**：R1-Distill Qwen 1.5B/7B/14B/32B、Llama 8B/70B（70B 视预算 n=200–400）；
  同骨干三种后训练：Qwen2.5-32B-Instruct（无推理训练，提示式 CoT）/ R1-Distill-Qwen-32B / QwQ-32B。
- **编辑器**：ROME（全部模型）；MEMIT、AlphaEdit（32B）；IKE 上下文编辑（32B，非参数对照）。
- **条件**：全部模型 B0/B3 × {efficacy, para0, locality}；32B-ROME 另加 B0P、B1、等长无内容填充、
  跨 case 换链、五臂 N/T/D/P/C（思考段 logit 惩罚 8）、编辑强度 α∈{0.5,1,2,3}、B3 采样 4 seeds。
- **终点**：词汇 ES/RR^s（旧口径）+ 语义 ES/RR（双判官家族盲评 + 200 条人工双标）。
  预注册切换规则：人判 κ≥.7 → 语义为主终点，否则词汇 strict 为主。另报 locality（邻居答对率 + 新值不泄漏）。
- **主假设**：H1 ES 降幅>0（32B、70B；Holm over 6）；H2 留存对比>0（14B、32B、70B；Holm over 6）；
  H3 32B：T−P ES>0 且 RR<0，D−N ES<0。次要：侵蚀/修复、编辑器、三种后训练、α 剂量、IKE、可靠性。探索：机制。
- **决策门**：G0 引擎一致性（下节）；G2 语义缺口 CI 排零且 κ≥.7；G3 H1+H2 在 32B 过。
  G2 或 G3 不过 → 不赶 10/12，改投 ARR 一月（ACL 2027）。

## 4 引擎 v2（`src/rt/`）
核心观察：单条 ROME/MEMIT/AlphaEdit 编辑在每个被编辑层上是秩 1 的 ΔW = B·A（HF 权重布局 (out,in)）。
所以不必改权重：用 forward hook 在 down_proj 输出上按行加 α·(x·Aᵀ)·Bᵀ，**一个 batch 里每行带自己的编辑**，
单条编辑协议语义不变（每个请求只见自己的编辑），生成改为 bf16 批量（Hopper 的 NaN 出在 ROME compute_v，不在生成）。
ΔW 仍在 fp32 下由 EasyEdit 计算后导出。

| 模块 | 职责 |
|---|---|
| `edit_hooks.py` | `factor_delta`（ΔW→低秩 A/B + 拟合误差）、`EditBank`（按行/按位置注入编辑的 hook） |
| `deltas.py` | fp32 编辑 → 取 ΔW → 分解 → 存 `deltas/<model_tag>/<editor>/<target_tag>/<case_id>.pt` → restore；按 case 续跑 |
| `engine.py` | 批量两阶段生成：链阶段（停在 `</think>`/eos/上限，按行 logit bias）→ 答案阶段（无 bias，256）；B0/B0P/B1/B3/给定链 |
| `pool.py` | 新池筛选与冻结清单（含哈希） |
| `run.py` | 配置 → jsonl；行 schema 兼容 `metrics.py` |
| `analysis.py` | Study 1 重分析与 Study 2 全部估计量（配对 bootstrap、Holm） |
| `judge.py` / `annotate.py` | 语义判官（开源模型，logprob 选项打分）与人工标注表 |
| `mech.py` | 编辑激活追踪、按位置门控编辑（teacher-forced） |

delta 文件：`{"format":"rt-delta-v1","case_id","model_tag","editor","target","target_tag","module_tmp",
"layers":{L:{"A":fp32[r,in],"B":fp32[out,r]}},"fit":{L:{"sigma":[...],"rel_err":…}},"diag":{…}}`。
行 schema：`case_id, model_tag, editor, target_tag, budget, probe, condition, arm, alpha, decode, seed,
temperature, q, cot, answer, chain_end∈{think_end,eos,cap,given}, n_chain_tokens, n_answer_tokens, delta_sha`；
每个分片首行 `_meta` 头（git、代码哈希、配置、环境）。
**G0 引擎一致性门**：在 Study 1 的 32B 池（200 条）上用 v2 重跑 ROME N 臂 B0/B3（`WHYAAAI_NO_BOS=1`，与 Study 1 的 32B 同设置）：降幅落在 Study 1 的 CI 内、
B0 逐 case 一致率 ≥85%（Study 1 自身重跑一致率 85–100%）。不过门不跑 Study 2。v2 数字与旧 HF 数字永不混在同一对比。

## 5 保留的防雷规则
- 编辑调用 `sequential_edit=True`，`finally: restore` 不许删（见 CLAUDE.md 防雷清单）。
- DeepSeek 模板全角竖线；R1-Llama 分词器修复；Qwen2 loader 与 mom2 语料补丁。
- `source/` 只读，改动进 `src/vendor_patches/`。AlphaEdit 的 `cache_c` 每条 case 必须重置。
- 长任务 ≤2h 粒度、jsonl 追加、按 case_id 续跑；新环境跑通立即 `pip freeze`。
- 新模型首跑先肉眼看几条生成是人话。
- BOS：Study 1 的 Qwen 全部（1.5B 特意设 WHYAAAI_NO_BOS=1 对齐）为无 BOS、Llama 为有 BOS（缺 BOS 会退化）；Study 2 沿用同一规则（Qwen 系无 BOS、Llama 系有 BOS；ChatML 模板无 BOS），使 Study 2 与 Study 1 只差引擎这一处。

## 6 预算与排期（~200 H200 卡时）
| 项 | 估计卡时 |
|---|---|
| ΔW（fp32）：32B 约 2,800 条 × ~45s；14B/小模型；70B 视 n | 35–60 |
| 生成（bf16 批量）：全部条件 | 15–30 |
| 判官、机制探针、G0 | 10–15 |
| 余量 | ~100 |

D1–2 引擎与分析代码 + 测试；D3 平台上 G0 + 选池 + 冻结预注册；D4–7 Study 2；D5–8 判官/人工标注/机制；
D8 过门决策；D8–13 成文；10/12 提交。写作从 D1 并行开始。

## 7 写作原则
主张先行，读者读完摘要能复述；每个设计决定一句"为什么"；限定条件集中进 Limitations（ACL 格式强制、不占页）；
按第 1 节层级组织；协议一张表、惩罚一行公式；图字号可读；Ethics 按 ACL 常规写（数据许可、误用、算力、标注者）。
必引补齐：MQuAKE、Ju et al. 2024、RippleEdits、Mirage of Model Editing、ThinkEval、CODE、Gao et al. 2026、
Superficial Editing。定位句：前人证明编辑不向外传播；我们证明推理时未编辑的邻域会向内回流，推翻编辑本身。

## 8 进度快照（随时可安全压缩上下文；最新在上）
- **2026-09-29（平台 8×4090-48G）**：B1/B2 金丝雀过；TF32 根因实测确认并修复（`ffaf713`）。
  r1qwen32b 选池完成：合格 710/1600，manifest 400（sha `dbdd75a9fc3e`，已入库；与 Study 1 零重叠；32 个关系，
  偏向 P17/P103/P1412 等 base 熟知的关系——论文须报池构成）。G1a（32B fp32 ROME，4 卡模型并行）3/3 通过：
  中位 22.7 s/条，单卡峰值 36 GB，p_target_after .985。→ 32B 全部 Study-2 编辑可在 4090 上完成。
  平台缺 HF token（env_report 3/4 均无）→ 下载匿名限速、Gemma 门控必失败；需用户在平台写 token。
  预注册补两条（仍为草稿）：合格不足 k 时用全部合格；manifest 为确定性产出，可在各模型首个 delta 前逐个登记。
  在飞：G1b（200 条）→ G2 生成 → G3 判定；其后 70B/Instruct/1.5B 选池与 70B fp32 编辑容量冒烟（决定是否需要 H200）。
- **2026-09-28**：引擎 v2 全部模块已合并（`src/rt/`：edit_hooks、engine、run、pool、deltas、mom2、targets、
  analysis、study1、judge、annotate、mech、g0），166 个 CPU 测试通过（`PYTHONPATH=src ~/.venvs/why-rt/bin/python
  src/rt/tests/run_all.py`）。Study 1 重分析入库（`paperwriting/revision/study1.{json,md}`）。
  平台运行单 `experiments/rt/RUNSHEET.md`；Study 2 配置八个模型齐全（生成 `study2_*.yaml`、增量 `deltas_s2_*.yaml`）。
  人工标注包（练习 20 + Study 1 验证 200）已生成于 `results/annot/`（答案键仅在本地）。
  **下一步（平台）**：G0 → 选池筛选 → 冻结 `prereg-arr.md` → Study 2 增量与生成 → 判官与人工标注。
  **下一步（本地）**：`src/rt/study2.py`（H1–H3 与次要假设的分析 CLI）；按 `paperwriting/revision/outline.md` 重写全文（ACL 模板）。
