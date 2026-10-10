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

## 2 Study 1 已确定的结果（`src/rt/study1.py` → `paperwriting/revision/study1.{json,md}`；六格点估计与 results.json 逐位一致，1.5B/14B/8B 的 CI 在第三位小数上不同）
| 量 | 结果 |
|---|---|
| Holm(6 格) ES 降幅 | 70B p=.0036（Holm .022），32B p=.0066（Holm .033）均过；其余四格不过 |
| 留存对比（base@B0 答旧 ∧ 编辑@B0 成功） | 编辑丢失 − 原生丢失：14B +.195 [.069,.322]，32B +.216 [.091,.341]，70B +.234 [.117,.351]。**已裁定（9/29，fp32 诊断 Y）**：Study 1 的 32B base 确实加了 BOS（v2 fp32 带 BOS 逐字节复现 Study 1 base 40/40，不带 BOS 仅 2/40），所以原 +.216 是跨格式配对（无 BOS 编辑组 × 有 BOS base）。格式一致的证据：Study 1 内有 BOS 编辑组（D/P/C 组）× 有 BOS base +.151 [.032,.269]（1.93×，审查报告数）；v2 G0 同一次运行、两边都无 BOS +.239 [.102,.375]（2.6×）。论文 32B 写"约 2×"，Study 1 表注明格式，Study 2 预注册的同批配对为准 |
| 名字泄题（主语名含旧值，46/200） | 32B RR .60（仅 10 条）vs 其余 .156；排除后 ES 降幅 32B .118，70B .117 未校正显著，Holm 后 p=.054 |
| 逐模型资格（各自 base@B0 知道旧值） | 32B .125 [.033,.217]，70B .153 [.076,.229]；小模型在"知道"层内仍≈0 |
| 侵蚀 / 修复 | 侵蚀 6 格全>0（.128→.207）；修复随规模降（1.5B .153 → 32B .101，70B .085） |
| 采样可靠性（32B） | B0 通过的编辑 61% 在 3 次推理采样中至少败 1 次；B0 重复采样噪声底 34%（61% 永远与 34% 一起写） |
| 先验知识分层（base@B0 是否答出旧值） | 答出组降幅 32B +.125、70B +.153；未答出组 32B +.043、70B −.047（各约 45 条），六格中五格 ≤0 → Study 2 的 H2b |
| 长度 / 国籍形容词 | 高端无答案变长；demonym 重打分不改结论 |
| 反面结果（不作证据） | base 的 thinking-to-recall 率 > 编辑回退率（case 构成不同）；"关系类型线索"方向相反（被名字泄题混杂） |
| 五臂运行环境（9/29 更正） | 分裂的实质是 BOS：N、T（及 X3 重跑）无 BOS，B0 彼此逐字节相同 200/200；D、P、C 与采样跑有 BOS（`_gen` 自 6/25 起默认加），彼此也 200/200；两组之间 12/200。同环境对比是 T−N 与 D−P、D−C、P−C；T−P、D−N 跨 BOS。干净证据：T−N ES +.138 [.082,.194]（study1.json），D−P ES −.225 [−.291,−.158]，P−C ES = .000（T−P 与 T−C 的 ES 同为 .121；C 不提供新信息）；P−N、C−N 的 CLR 显著（−.056、−.071）是 BOS 假象（只换 BOS 即复现 −.061）。D−P 与"只换 BOS"两个数来自审查报告，成文前在 rt.study1 里补算复核。placebo 臂磁盘数据已与 results.json 的 n=199 版本不同，旧版不可重建。32B ES 缺口无 BOS .106、有 BOS .110 |
结论：**permissive RR 19.3% 退出头条**；头条 = ES 缺口 + 留存对比 + 采样可靠性；Study 1 的因果证据报 T−N 与 D−P 并交代 BOS 分裂；Study 2 所有臂同一批生成。
（Holm/CI 以 study1.json 为准：统一按 case_id 排序重采样，与 cross_arm 一致。）

## 3 Study 2 设计（预注册要点；正式文本 `prereg-arr.md` 在任何 Study-2 delta 计算前冻结）
- **池**：CounterFact 21,919 条，剔除历史上用过的全部 case_id → seed 2027 洗牌 → 前 1600 为候选 →
  每个模型用自己的未编辑 base 在 B0 筛：旧值命中 ∧ 新值未命中（现行 matcher、去主语）∧ 主语名不含旧值 →
  每模型取前 400 条合格（顺序固定）。不再用任何 B3 输出选池。
- **模型**：R1-Distill Qwen 1.5B/7B/14B/32B、Llama 8B/70B（70B n=400，9/29 起；n=200 时功效约 2/3）；
  同骨干三种后训练：Qwen2.5-32B-Instruct（无推理训练，提示式 CoT）/ R1-Distill-Qwen-32B / QwQ-32B。
- **编辑器**：ROME（全部模型）；MEMIT、AlphaEdit（32B）；IKE 上下文编辑（32B，非参数对照）。
- **条件**：全部模型 B0/B3 × {efficacy, para0, locality}；32B-ROME 另加 B0P、B1、等长无内容填充、
  跨 case 换链、五臂 N/T/D/P/C（思考段 logit 惩罚 8；C 只作次要的特异性检查）、编辑强度 α∈{1,2,3}（α=0.5 只跑 B0）、
  B3 采样 4 seeds（统计量按 seed 0–2）、IKE 只跑 efficacy；H2b 未知组 300 条（base@B0 两值都没答出）跑 base 与 N。
  Qwen2.5-32B-Instruct / QwQ-32B 放最后，时间允许才跑。MEMIT/AlphaEdit 与 ROME 主跑解耦（统计量就绪后补跑）。
- **终点**：词汇 ES/RR^s（旧口径）+ 语义 ES/RR（双判官家族盲评 + 200 条人工双标）。
  预注册切换规则：**在 Study 1 标注包上判**（任何 Study 2 结局之前）：人判 κ≥.7 → 语义为主终点，否则词汇 strict 为主；
  10/5 AoE 前没有人工 κ → 词汇 strict 为主。Study 2 的 200 条只报 κ。另报 locality（邻居答对率 + 新值不泄漏）。
- **主假设**：H1 ES 降幅>0（32B、70B；Holm over 6）；H2 留存对比>0（14B、32B、70B；Holm over 6）；
  H2b 32B：已知组降幅 − 未知组降幅 > 0（单独一检）；H3 32B：T−P ES>0 且 RR<0，D−P ES<0（Holm over 3）。
  次要：T−N、D−N、T−C、P−N（带 CI，不作等价主张）、侵蚀/修复、编辑器、三种后训练、α 剂量、IKE、可靠性。探索：机制。
  （H3 最初在 9/28 写作 D−N，9/29 在任何 Study 2 数据之前改为 D−P：两个对比都以匹配的 placebo 为参照。）
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
**G0 引擎一致性门**：在 Study 1 的 32B 池（200 条）上用 v2 重跑 ROME N 臂 B0/B3（无 BOS，与 Study 1 的 N 臂同设置）。
准则 0：完整——Study 1 有配对的 198 条在 v2 里全部有 B0 和 B3（`rt.g0` 不再只在共有子集上判）；
准则 1：v2 降幅落在 Study 1 预先固定的 CI [.030, .182] 内（全部 198 条算的，不在子集上重算）；
准则 2：B0 逐 case ES 一致率 ≥85%。更正：85% 这个数其实是 BOS 翻转造成的一致率（N 与 D/P/C 之间 170/200），
不是重跑噪声；Study 1 的真重跑一致率是 100%。v2 相对 Study 1 同时换了 bf16 生成和严格 fp32 编辑
（Study 1 很可能跑在 TF32 下），引擎正确也可能过不了准则 2。v2 数字与旧 HF 数字永不混在同一对比。
base 的 B0 对比不能诊断引擎：Study 1 的 32B base 很可能加了 BOS，v2 的 base 没加。
**G0 分支（2026-09-29 在读判定之前提交）**。机制正确性已另行证实（批内每行只注入自己的编辑、hook 与直接改权重等价、
逐 case 按位还原：tiny 模型 + 真实 1.5B），G0 剩下的作用是把 Study 1 和 Study 2 接起来：
- 全过 → 冻结预注册，开跑 Study 2。
- 准则 0 不过 → 这是完整性问题，不是引擎结论：用更小的批补跑缺的 case，再判。
- 准则 1 过、准则 2 不过 → 用 fp32 生成跑 40 条诊断（同时带有/无 BOS 的 base）。一致率 ≥95%：差异来自 bf16 数值，
  照常跑 Study 2，两项一致率都报告。<95%：在同一台 4090 上用旧 HF 引擎跑同样 40 条，逐条对比新旧引擎，
  查清之后再决定。
- 降幅 < .030 → 停下，用 fp32 子集诊断。fp32 也没有缺口 → Study 1 的效应经不起重新生成，不赶 10/12。
- 降幅 > .182 → 先查长链 OOM 造成的选择性缺行并补跑；数据完整后仍 > .182 → 按准则 2 的 fp32 诊断处理。

## 5 保留的防雷规则
- 编辑调用 `sequential_edit=True`，`finally: restore` 不许删（见 CLAUDE.md 防雷清单）。
- DeepSeek 模板全角竖线；R1-Llama 分词器修复；Qwen2 loader 与 mom2 语料补丁。
- `source/` 只读，改动进 `src/vendor_patches/`。AlphaEdit 的 `cache_c` 每条 case 必须重置。
- 长任务 ≤2h 粒度、jsonl 追加、按 case_id 续跑；新环境跑通立即 `pip freeze`。
- 新模型首跑先肉眼看几条生成是人话。
- BOS（9/29 更正）：Study 1 的**头条格**无 BOS（32B N/T 臂；1.5B 特意设 WHYAAAI_NO_BOS=1 对齐），Llama 有 BOS（缺 BOS 会退化）；
  但 Study 1 的 32B D/P/C 臂与采样跑有 BOS（`_gen` 自 6/25 起默认加），32B base 很可能也有（fp32 诊断 Y 裁定）。
  Study 2 的规则：Qwen 系无 BOS、Llama 系有 BOS、ChatML 模板无 BOS——理由是对齐 Study 1 的头条格。
  稳健性：Study 1 的 32B ES 缺口无 BOS .106、有 BOS .110，BOS 不改结论。
- 生成配置（9/29，审查 M1）：checkpoint 自带的 generation_config 不进入 generate（Qwen2.5-Instruct 的 repetition_penalty
  1.05 曾会在贪心下生效）；采样参数显式传入并逐行记录（temperature .6 / top_p .95 / top_k 50 = Study 1 的实际设置）。
- 分词器（审查 M4）：R1-Llama 分词器修复失败直接报错；每个模型加载后做一次编码—解码往返检查。
- 冻结后到 Study 2 结束，`src/rt/` 不再改动（所有 Study 2 运行共用一个代码哈希）；确需改动走偏差记录。

## 6 预算与排期（~200 H200 卡时）
| 项 | 估计卡时 |
|---|---|
| ΔW（fp32）：32B 约 2,800 条 × ~45s；14B/小模型；70B 视 n | 35–60 |
| 生成（bf16 批量）：全部条件 | 15–30 |
| 判官、机制探针、G0 | 10–15 |
| 余量 | ~100 |

D1–2 引擎与分析代码 + 测试；D3 平台上 G0 + 选池 + 冻结预注册；D4–7 Study 2；D5–8 判官/人工标注/机制；
D8 过门决策；D8–13 成文；10/12 提交。
**先证据、后成文（用户决定，2026-09-29）**：全文重写在证据打磨到位之后才开始。没有这些证据支撑，重写也救不了；写作只是把证据讲清楚。此前只维护 `paperwriting/revision/outline.md`（主张层级与审稿意见的逐条对应），不动正文。

## 7 写作原则
主张先行，读者读完摘要能复述；每个设计决定一句"为什么"；限定条件集中进 Limitations（ACL 格式强制、不占页）；
按第 1 节层级组织；协议一张表、惩罚一行公式；图字号可读；Ethics 按 ACL 常规写（数据许可、误用、算力、标注者）。
必引补齐：MQuAKE、Ju et al. 2024、RippleEdits、Mirage of Model Editing、ThinkEval、CODE、Gao et al. 2026、
Superficial Editing。定位句：前人证明编辑不向外传播；我们证明推理时未编辑的邻域会向内回流，推翻编辑本身。

## 8 进度快照（随时可安全压缩上下文；最新在上）
- **2026-10-10 晚：叙事面板 + 预注册红队（`paperwriting/revision/narrative/panel_2026-10-10.{md,json}`）**。
  **更正下午的说法**：Study 1 里显著度造成的留存差主要来自 base 对冷门事实的原生答案思考后丢失（−.08～−.26），编辑丢失基本持平（+.01～+.12）；
  Study 1 各模型的高−低差都不显著（p .07–.28）；Study 2 里 31 条丢失的显著编辑中 15 条同时说出新旧两值（严格口径 +.091）；
  不思考、仅改述提问也出现同样的分化（+.152）→ 熟知事实的编辑脆弱并非思考特有。He et al. 2025 已报告 R1 蒸馏推理推翻编辑，Ma et al. 2024 已有流行度/改述脆弱性。
  五种叙事的"顶会契合度"只有 4.3–5.0。H4 草案不冻结（估计量错、W1/W3 事实重叠、缺停止规则等）。待用户决定论文定位（见对话）。
- **2026-10-10 探索性分析（事后，`aadf8a9`，`paperwriting/revision/explore_s1s2.{md,json}`，计划与追加见 `explore_s1s2_plan.md`）**：
  硬件不是原因（同批 case 4090 对 H100 降幅差 +.045 n.s.，留存 .239/.207；但 B3 结果只 81% 一致）；同硬件下池子差异真实（侵蚀 −.11 p=.018、留存 −.18 p=.019）；
  选池规则、base 推理召回旧值、关系构成、编辑强度都解释不了（编辑强度在 S2 AUC .66，但在 Study 1 case 上 .50）。
  **事实显著度能解释**（4 个小蒸馏模型中有几个在 B0 知道旧值）：S2 显著事实（3–4/4，n=156）ES 降幅 .115 p=.006、留存 +.242；
  其余（n=244）降幅 −.012、留存 −.090；差 +.332 p<.001；0→4 单调（编辑丢失 .13→.31 升，原生丢失 .39→.06 降）。
  Study 1 的 14B/32B/70B 同向（显著事实留存 +.28～+.32，CI 排零；其余 +.03～+.13）。Study 1 池 59% 显著，S2 39%。
  事后选的调节变量 → 只能作下一次预注册的主假设。70B 池 107 条显著、14B 65 条，编辑已完成未生成 → 可前瞻检验。
- **2026-10-10 11:50 平台已结束（10/8 ≈19:40），Study 2 只完成 32B base/rome_N**（`8997ddb`，偏差 D7，分片 sha 已入库）：
  **预注册检验：H1@32B ES 降幅 .037 [−.010, .087]，p=.14 ✗；H2@32B 留存对比 +.029 [−.036, .097]，p=.43，n=277 ✗**（Study 1：.106、+.216）。
  分解：侵蚀 .143（S1 .207）、修复 .105（.101）、编辑答案丢失 .199（.386）、原生答案丢失 .170（.170）→ 缩水全在"编辑答案被思考侵蚀"这一项；
  修复与原生丢失不变。复述探针 ES 降幅 −.083（思考反而帮忙），locality 无差。ES@B0 .71（S1 .60）。
  未跑：H2b（10/300）、H3、70B/14B/8B/7B/1.5B 生成、全部次要条件；编辑全部完成（70B 400/400），只差生成。
  **待用户决定**：10/12 是否投、投什么；能否在 10/12 前拿到约 3 小时 8×H100 跑 70B 生成（决定性的一格）。
- **2026-10-08 18:50**：G1''（32B base/rome_N 三探针）2400+2400 齐，✓按意图（OOM error 行保留、全部已重做，分析跳过 error 行）；
  D3–D6 签收（max_rel_err ≤ 4.6e-6）。H100 可能今天被回收 → 偏差 D6（`1ed7a23`）：H100 队列 G2''(H2b) → G7a(T,D,P) → G70 rank 锁
  → 小模型锁 → G7b(C) → G10' → G11'；4090：D70 → summarize → `D70_OK` → 小模型锁 → G70 rank 锁 → J；用户说"H100 已下线"时 4090 按 #8 的 T 段接管。
  批上限阶梯：进程退出且不齐 → 原 rank 续跑，32B/70B 首跑 40000/34000 → 26000 → 18000。新标记：H100_PATHS.txt、H100_<项>_DONE、D70_OK、
  LOCK_G70_r<k>of8、G70_r<k>of8_DONE、H100_GONE。生效单：H100 H-3，4090 #8。
- **2026-10-08 15:40 在飞状态（压缩前快照）**
  - **冻结**：`90c704b`（registry 条目 1–7；GitHub 推送 03:39:43Z/03:40:36Z）。偏差 D1–D5 见 `prereg-arr-deviations.md`（最新 `7dcafe4`）。
  - **已核验**：G0@4090 PASS（.131）；G0@H100 PASS（.086，187/198）；fp32 诊断 Y（引擎逐字节复现 Study 1）；
    D1 32B 主池 400/400、D2 未知组 300/300（本地 summarize 核过，提交 90c704b，p_after .99）。
  - **待核验**：D3 14B、D4 8B 400、D5 7B 318、D6 1.5B 212（4090 报已完成，日志未同步到本地 `platform_out/deltas_logs/s2/`）。
  - **4090 在跑**：D70（70B ROME，1 进程×8 卡，~4.5 h，完成放 `xfer/D70_DONE`）→ 小模型生成（抢占式锁 `xfer/LOCK_GS_<tag>`）→ J（mistral；gemma 403 仍在后台重试）。
    生效单：#6（+补充一/二）、#7（+补充一）。ST/D7/D8 取消（D4）。
  - **H100 在跑**：H-2（+补充一）：32B 每卡一进程 world 8 `--device cuda --batch-size 16 --max-batch-tokens 40000`：
    G1''（base,rome_N 三探针）→ G2''（H2b）→ G7'（T/D/P/C）→ G10'（次要 stage 1）→ G11'（stage 2，r*of8）→ 小模型（抢锁）；
    D70_DONE 出现即插入 G3''（70B eff，4 进程×2 卡，`--max-batch-tokens 34000`）。旧 world-2 半成品已移到 `results/rt/s2_archive_world2/`（不分析）。
    看门狗：GPU 利用率连续 10 分钟 0% 才判卡死（按行数判会误杀长链分块）。
  - **吞吐教训**：HF generate 受 CPU 限制，4 卡流水线的 H100 每进程 ≈ 4090（~4.5 链/分）；多进程单卡更快。
  - **沟通协议**：执行员只写回报文件（块首行 `## <项> <✓|✗|⏸> <时间>`）；用户同步后说"已同步"。
    本地位置：4090 → `../../platform_out/`（report_4090.md、deltas_logs/、summarize_*.json）；H100 → `../../reports/report_h100.md`（结果待同步）。
  - **下一步（leader）**：① 看 G1'' 启动 30 分钟后的行数估速度，必要时再砍；② 每批结果到本地后跑
    `PYTHONPATH=src python -m rt.study2 --results <本地 s2 结果目录> --out paperwriting/revision/study2.json --delta-logs <deltas_logs/s2> <deltas_logs/s2_h2b>`；
    ③ 把 Study 2 数字交给写作 session（10/7 起按"只用 Study 1"在重写，需留 Study 2 一节）。
- **2026-10-08（唯一实验日）**：平台 9/29 后空转 9 天；7 个模型选池已完成（32B 400 + 未知组 300、70B 400、14B 400、8B 400、
  7B 318、1.5B 212，回传在平台 platform_out/pools_study2/，**待同步到本地后冻结**）；E70：70B fp32 编辑在 8×4090 可行（31–52 s/条）；
  ST（32B 协方差）因两个队列并发 OOM 失败；Gemma 403。新增 8×H100-80G（**离线**），4090 可上网。
  分工：4090 = 全部编辑（32B 主池/未知组/14B/8B/7B/1.5B → ST → MEMIT → AlphaEdit）+ 给 H100 下 wheel + Gemma；
  H100 = 70B 编辑 + 全部生成（先在 H100 上重跑 G0）。两机通过 GPFS 上的 xfer/ 标记文件协调（D1_DONE…D8_DONE、D70_DONE、
  FREEZE_PULLED、H100_ENV_OK）；H100 代码目录 why-arr-h100 从 4090 目录本地克隆，deltas 软链到 4090。
  执行单：4090 #6、H100 H-1（含离线修订）。回报文件：platform_out/report_4090.md、platform_out_h100/report_h100.md。
  预注册已写入一日运行顺序与硬件分工（`e5748e3`）；冻结 = 同步池文件 → 提交池 + registry freeze 条目 → 推送。
- **2026-09-29 夜：fp32 诊断 Y**（Study 1 的 32B 前 40 条，B0，v2 引擎 fp32）：无 BOS 的 rome_N 逐字节复现 Study 1 的 N 臂 37/40，
  带 BOS 的 rome_N 复现 P 臂 39/40，带 BOS 的 base 复现 Study 1 base 40/40（不带 BOS 仅 2/40）。
  → ① v2 引擎在 fp32 下与旧 HF 流程逐字节一致（跨 H200→4090 硬件），G0 里 B0 文本只有 90/198 相同完全来自 bf16；
  ② 五臂分裂与 base 的 BOS 状态实锤；③ 32B 留存对比已按格式重述（§2）。论文方法附录可写"引擎逐字节验证"。
- **2026-09-29 夜：G0 PASS**（198/198 齐全；v2 降幅 .131 [.056,.207] 落在 [.030,.182]；B0 ES 一致 186/198；
  B3 一致 163/198；B0 答案逐字相同 90/198）。v2 自身格式一致（base 与编辑组都无 BOS）的留存对比 +.239 [.102,.375]，
  Study 1 为 +.216 → 32B 留存对比不是 BOS 假象。G2b 曾有一个长链分块 OOM（2 卡/进程，全卡峰值 46–47 GB），
  4 卡补跑齐 → Study 2 的 32B 生成改为 2 进程 × 4 卡（r*of2）。X：cf_17023 在批大小 1 下同样落入身份模板 → 模型行为，非引擎 bug。
- **2026-09-29 晚（审查之后）**：独立审查的结论已裁决并落地（`a16746b`→`49f1729`）：G0 判定程序补完整性准则、
  固定 CI，分支方案先于判定提交；M1 解码参数不再继承 checkpoint、M4 分词器报错 + 往返检查；H3 = T−P、D−P；H2b 先验知识对照
  （32B 未知组 300）；70B n=400；排除 cf_4298；切换规则移到 Study 1 标注包（10/5 前无 κ → 词汇为主）；BOS 记录更正；
  `src/rt/study2.py` 合并（193 测试过），分析约定写进预注册。
  **冻结前还差**：G0 判定（+ fp32 诊断 Y）、32B 重新 qualify 的 manifest、用户的 OSF 登记、标注者与止损日期。
  平台：G2b 在跑；同步点在 G2b 之后；Instruct/QwQ 选池推迟。
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
  **下一步（本地）**：`src/rt/study2.py`（H1–H3 与次要假设的分析 CLI）；证据到位后按 `paperwriting/revision/outline.md` 重写全文（ACL 模板，见 §6）。
