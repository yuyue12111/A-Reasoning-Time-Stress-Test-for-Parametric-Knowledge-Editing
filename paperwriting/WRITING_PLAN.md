# WRITING_PLAN.md · 最终写作作战计划（plan v1.93 的执行层）

> 状态：**唯一有效的写作计划**（2026-07-14 仲裁定稿，整合三方审计 + GPT-5.6 复核裁决）。
> 数字唯一真源 = `paperwriting/results.json`（原 `paper/` 已更名，5 个 src 脚本路径已同步修复）。
> 铁律：任何数字/显著性/认证措辞先有 results.json JSON path 再落笔（plan v1.65/v1.69）；
> **投稿前科学队列 = 零**（不跑 B15 interaction、不烧 X-A 池、不加 seed/数据集/编辑器）。

## 0-bis. 正文叙事逻辑（矿场产出蒸馏 + 摘要程序实证；W2 起草期主动使用，W3 用 transfer_checklist §2–§5 复查）

> 来源：`prewrite/style_notes.md` / `prewrite/transfer_checklist.md`（14 篇同文体深读 + AAAI-25/26 AIA 全量 172 篇，
> 全部 PROVISIONAL_UNCERTIFIED 描述性透镜）+ 本仓库摘要程序 v1–v8.1 的 24+ 盲读实证。
> `prewrite/usage_protocol.md` 六禁令全程有效：透镜是修订层指引非模板，有意偏离+一句理由合法，冻结件无条件优先。

七条叙事逻辑（每条注出处）：
1. **先安装世界与旧假设，再谈自己**——首拍 CONTEXT/BACKGROUND（深读 12/14 摘要、14/14 引言）。§1 开场 = 编辑评测的现状与"直接回答成功⇒部署可靠"这个旧假设，不是我们的方法。
2. **铰链早置**——引言在 ~30% 处显式转向（HINGE 位置中位 0.296，14/14 存在）："部署的推理模型会思考，而认证发生在零思考"这一转折必须在 §1 前三分之一落地。
3. **先给结果的形状，再给细节**——RESULT_PREVIEW 14/14；§1 末的三拍预告（认证缺口/共存+假说/链内控制点），contribution list 可用（10/14）且 C2 首词 = 加粗的 "A chain-local causal control point."（M15 记忆锚令）。
4. **每句单一职责，假说与检验显式分层**——摘要程序 G6 实证：读者会尊重文本标出的证据位阶（v8 面板 4/4 自发复述 claim ceiling）。正文沿用 "motivating a hypothesis → We next test" 的显式铰链语法。
5. **数字只标承重节点，其余入表**——摘要程序的核心实证教训（clarity 被堆叠 estimand 从句钉死，删数字不减理解、只减疲劳）。正文散文承载模型与方向，CI/κ/分母/敏感性全部入 Table/脚注（M14/M16 配套）。
6. **限制直说不致歉**——DIRECT tone 14/14（与 HEDGED 共存 12/14）；dedicated section 10/14 但分布式合法——X1 FAIL 按令分布在 §4 机理讨论紧邻位，不是集中忏悔。
7. **结尾回扣重定义的问题**——末拍 IMPLICATION；全文最后一句含 verbatim 锚短语（M15 第 5 条）。

本文的叙事骨相（Idea2Story 三问的定稿答案）：**主角**=编辑认证证书；**旧假设**=直接回答的编辑成功⇒部署可靠；**重定义**=编辑评测必须包含 reasoning-time stress test，且失效存在链内因果控制点。各节子模型：§3=证书在思考中失效（受控且编辑特异）；§4=失效非擦除、有可见路由（假说位阶）+ X1 诚实披露；§5=链内存在有符号、有剂量的控制点（干预位阶）；§6/§7=边界与含义。
Fig.1 按语料形态走 **PRIMARY_RESULT**（7/14；method-pipeline 仅 2/14）= 认证缺口图，caption 自足（FULL 9/14 规格）。

## 0. 论文身份与主 claim（冻结）

**身份**：reasoning-time evaluation / safety stress test（评测证书失效边界），不是"现象+机理+修复"三段论。

**Title（2026-07-14 冻结）**：*Direct-Answer Edit Success Is Not Enough: A Reasoning-Time Stress Test for Parametric Knowledge Editing*（裁决记录见 `title_abstract.md`）。

**主 claim（英文措辞冻结，与 title 同步为 "not enough" 措辞）**：
> Direct-answer edit success is **not enough** to certify knowledge edits for reasoning-model
> deployment. We provide a controlled reasoning-time stress test, show the failure it reveals, and
> demonstrate that this failure admits a **chain-local causal control point**.

- 用 *not enough / insufficient*，禁用 *invalid*（很多部署确是直接回答；prior work 已批评 teacher-forcing 评测；我们证明的是"遗漏一类重要 failure mode"）；标题与散文均避免名词化 *certificate/certified* 以免暗示形式化认证体系（动词 certify 可用）。
- 独有性卖点不是"评测有效性"四个字（SCR/ReCoE/CRANE/Inverse-Scaling 都在附近），而是**六元合取**：
  ① single-edit + 生成式词界判分；② 同一编辑 B0→native chain 的 paired change；③ unedited-base/B0P/sampling 三重控制；④ 两族固定 checkpoint 高端点对称显著；⑤ 只动 think span、答案 logits untouched 的 signed 因果干预；⑥ ROME/MEMIT/active-paraphrase 的有限迁移。

## 1. 三条贡献与证据阶梯（每条注 JSON path）

### C1 · Reasoning-time evaluation gap（主贡献）
- Qwen-32B ES-drop `.106[.030,.182]`、Llama-70B `.107[.032,.182]`（`capability.families`，六格仅此两格显著，明写 fixed-checkpoint scope）
- 编辑特异：base drift `−.0201[−.0804,.0402]` null（`base_probe.f1_edit_specificity.paired_ci`）
- 内容驱动：B0/B0P/B1 RR `0/.040/.208`（`f2_zerothink_deconfound`；B0P=固定假思考，非等长 filler，如实写）
- 采样稳健：F3 以 ES-drop `.117[.067,.169]` 承重（`f3_sampling_robustness.sampling_primary_complete_cases`）；RR 若写必须精确注 estimand（equal-case conditional `.305` vs trajectory-weighted `87/350=.249`），不写"比旧值更强"
- B15 只说"二值 base-recall 不能完全解释"（`.1005→.0837`，衰减 16.7%，`b15_base_recall_control.b0_primary`）；known/unknown 分层**无 interaction 检验**，不写 effect modification
- per-case slope `.1094[.0417,.1770]` 与 RR slope `.6444[.1985,1.1427]` 均为 **supporting outcome**（同六 checkpoint、同事实池、RR 经 b0ok 门后 689 rows——不是"第二条独立趋势线"，不用于抬 capability 叙事）

### C2 · Causal diagnosis, not natural mediation（第二贡献）
证据阶梯**分层报告**（诚实分层本身是 Alignment track 的审计味卖点）：
- logit-lens：installation sanity（n=23，重施编辑后裸 cloze 首 token pairwise gap，无对照）
- P0 taxonomy：观察性 route census——n=41 实例 / **33 个独立事实**、Bridge 27/Recall 11/RO 3/Assoc 0、κ=.813（`rq2_taxonomy.p0_corrected_taxonomy`）；CLR 无判别力（OLD 13/13 但非 OLD 18/20 也有 CLR，`p0_downstream_crosswalk`）
- M1：baseline-CLR stratified enrichment（CLR1 层 `−.289 p=.0002` vs CLR0 `+.014 p=.72`，CLR0 有 N_RR=0 地板，且无跨层 interaction，`rq3.clr_split_M1`）——只写样本内富集，不写 near-necessity/effect modification/mediation
- W-B：先报 prospectively specified 主对比 S−Pshuf RR null；再报 CLR `−.078` 排零、同对比 ES null、S−N ES `+.092` 排零；显著的 S−Pshuf LocAcc 只称“预设 harm metric 上的 secondary contrast”，不得冒充预指定 B2 对照（`wb_representation_repair.confirm_arms`）——合法结论仅为测得的旧对象表达下降未产生可检出的 confirmatory RR repair；`B1_S_minus_Pshuf` 的 B1 是端点标签，正文不得误写成思考预算
- T/D/P/C 五臂：**唯一真因果**，识别的是 chain-local old-token control point（`rq3.sup_battery`）
- **X1 正文披露（Kimi 终审加严）**：prospectively specified replay 载具门 9/18 FAIL、未救门（`x1_replay_gate.gate`）；披露必须站在机理章 routing-hypothesis 讨论的**紧邻位置**，作为"是否直接测过 fixed replay 载具稳定性"这一可预测追问的正面回答——不得藏 §7 limitations 尾部；完整 gate 表进 supplementary。cloze 检查在 §4 必须以 "installation sanity check" 身份 + 全 caveat（无对照/近恒真/条件于回退样本/crosswalk BLOCKED）呈现
- 合法机理句式：*failure coexists with an installed cloze edit; native chains frequently expose Bridge/Recall routes; an old-token-specific intervention in the chain causally changes the untouched answer.*
- 禁写：re-derivation **causes** the failure / 41/41 证明重推导 / content-driven mechanism 已闭合 / semantic mediation / commitment layer located

### C3 · Bounded mitigation transfer（第三贡献）
- ROME-32B：T−C 四端点排零（ES `+.1212` RR `−.0943` RRs `−.0566 p=.032`，`rq3.sup_battery.cross_arm_paired_ci`）；T−N 严口径 `p=.073` 如实报；回退 headline 将 strict/permissive 写成 nested operational endpoints，不写潜在真值的数学夹层或 bound；判官认证只作 available-case 估计并把 missingness sensitivity 放 supplementary（loose 判官精度仅 0.48，`metric_validation`）
- ROME-14B 复制：**T−N**（14B 无 C 臂，`rq3.s10_14b_fix_replication.TminusN_paired_ci`）
- MEMIT-14B X2：ES `+.100[.040,.160]` 正、**strict RRs null 并报**（`rq3.x2_memit14b_repair_replication.contrasts_B3.T_minus_C`）；现象行必须带 fresh-N 括注（es_drop `.060[−.020,.140]` ns，`_baseline_discrepancy`）
- X3：**active lexical paraphrase transfer**（T−C strict PS `+.055[.020,.0925]`），禁写 semantic paraphrase robustness；内容审计 30/40、11/20、κ=.444 如实报
- C 臂限定语：strong-competitor donor 解码期基本不活跃（B3 改变行 T=109 vs C=18；X3 215 vs 24，`audit.b3_different_probe_rows_vs_N`）→ 写 "above an inert and a largely-inactive strong-competitor control"
- Loc 只称 target-value non-leakage（`metrics.py` docstring 自认）；genbench 点估等价 + TOST 未认证（`rq3.genbench_b26_tost`），禁写 safety equivalence
- 定位 = mechanistic probe / edit-aware decoding guard，禁写通用方法或部署级修复

## 2. 图表计划

- **Fig.1 = 认证缺口图，不是 scaling 曲线**。Panel A：六个 fixed checkpoint 的 paired B0/B3 ES change（高端两点突出）；Panel B：32B 的 base/B0P/sampling 控制。raw CLR 与 scale 回归**不得**成为第一视觉。`plots.py` 已按承重规格重写（commit 99dbcfb），需按本节微调面板顺序。
- Fig.2：机理证据阶梯（cloze 完好 + 路由普查 + 五臂森林图可并入）。
- Table：RQ3 主表（N/T 对照 + 三轴迁移分层）；`table_rq2.tex` 需从 n=41 taxonomy 重生成（现为已作废 50-池版本）。
- 预注册 FAIL/gate 全表进 supplementary，正文各一句话（X1 FAIL、W-B null、G5 FAIL 均不可藏）。

## 3. 禁语清单（对账时全文扫描，零命中才准冻结）

`invalid certificate` / `capability-emergent`（headline）/ `scaling law` / `fuel`、`vanishes`（B15 分层无 interaction 检验）/ `re-derivation causes` / `semantic mediation`、`mediates`、`necessity`（M1 本轮连 near-necessity 也不用，只写 sample-stratified enrichment）/ `semantic paraphrase robustness` / `equivalence certified`、`TOST-certified` / `prevents`、`blocks`、`robust to bypass` / 不带夹层限定的 `halves reversion` / `first to discover` / `preregistered` 用于任何无结果前冻结证据的分析 / **`edit intact`、`not erased`、`非擦除已证`**（cloze 可探 ≠ intact ≠ 排除功能性擦除；合法上限=*edited association remains detectable at a cloze probe*）/ **`guaranteed upper bound` 形容 loose RR**（recall=.96、FN=1 alias gap→非数学上界；夹层措辞用 conservative/permissive 口径）。

另（Kimi 交锋传导，2026-07-14）：F1 的 `effect_above_control=.214` **禁作正式 contrast**（编辑态 b0ok-门 loose RR 与未编辑基座全样本 drift 的事件定义/分母不同、无 interaction CI）——主文只并列报告两个量，不做差值宣称。

## 4. 日历（硬线：abstract 7/21、全文 7/28、supp+code 7/31，UTC-12；内部冻结 7/18 / 7/25）

| 段 | 日期 | 内容 | 完成判据 |
|---|---|---|---|
| D0 | 7/14–15 | ① 诚实 snapshot commit（见 §5）② LaTeX 主文件建立（AAAI 模板+骨架+bib 起步）③ Fig.1 面板顺序调整 | 主文件可编译 |
| W1 | –7/18 | ① 唯一 abstract v8.1 已按 story-first 形式内部冻结；删出的 uncertainty/measurement/strict/transfer 证据全部由 D1–D8/R1 强制落正文 ② 三贡献 claim hierarchy 定稿 ③ Fig.1 定稿 ④ §1 引言 | abstract 内部冻结；外部同步等 G5 |
| W2 | 7/19–23 | 主文四节顺序：§3 evaluation gap → §4 causal diagnosis → §5 bounded guard → §2 related work（SCR=2503.05212、ReCoE=Hua et al. 2401.17585 分拆；新增 Thinking-to-Recall 2603.09906 / LightEdit 2604.19089 / DeCK 2405.11613 / CRANE 2606.09033 / Inverse-Scaling 2507.14417 / belief-depth 2510.17941；维持 controlled-conjunction 定位）→ §6/§7 | 全文初稿 |
| W3 | 7/24–25 | **只做对账与 hostile review**：① 机器对账（写 checker：全文数字 ↔ results.json path 逐一校验）② 禁语扫描 ③ 判官式全文攻击 ④ abstract↔全文同源核对 | 全文内部冻结 7/25 |
| 缓冲 | 7/26–27 | 只修不加；任何新数字不进 | — |
| 提交 | 7/28 | 全文 + checklist | — |
| R | 7/29–31 | supplementary（prereg gate 全表含 X1/X2/X3/P0/P1 + provenance manifest）+ code 匿名化（按 `prewrite/anonymize_spec.md`、`release_and_licenses.md`）| **上传的 prereg 集合与正文披露逐一一致** |
| 检查点 | 7/22 | 全文完成度 <70% → 砍 supplementary 深度与图精修，**绝不砍对账** | — |
| 快扫 | 7/21 | 15 分钟增量查新，只为 §2 补引，不改主张 | — |

## 5. Provenance 政策（GPT-5.6 复核裁决采纳）

- **现在 commit 不能追溯性证明 preregistration**。禁止把 dirty tree 按想象的历史顺序拆成"当时的冻结 commit"，禁止任何形式的历史回填。
- 做法：**一次诚实 snapshot commit**（消息明写"snapshot as of 2026-07-14, not retroactive freeze evidence"）+ `paperwriting/provenance_manifest.md`（R 段完成），区分两类：
  - **真·结果前冻结证据**：results.json/audit 块内先于结果落账的 SHA256（如 x1 manifest、p0 判官文件）、服务器文件时间戳、平台日志——这些可称 *prospectively specified*；
  - **事后记录**：其余一律称 *pre-specified protocol recorded before analysis* 或直接说明 provenance 限制。
- 7/8 前已 commit 的 prereg（esup 等）保留 git hash 引用；X 系列以 SHA-in-artifact 链为准。

## 6. 叙事工具政策（Idea2Story, arXiv:2601.20833）

- 仅作**人工故事结构 checklist**（谁是主角 / 旧假设是什么 / 我们重定义了哪个问题）用于 W1 的引言与 abstract 打磨。
- **禁止**：跑其 pipeline、下载其仓库代码进本仓、让任何叙事工具接触数字真源（其示例 `final_story.json` 会在实验前生成虚构结果数字——与本项目数字铁律直接冲突）。
- 本项目的回答：主角=「编辑认证证书」；旧假设=「直接回答的编辑成功 ⇒ 部署可靠」；重定义=「编辑评测必须包含 reasoning-time stress test，且失败存在链内因果控制点」。

## 7. 投稿后轨道（S 轨，7/29 起，与本次提交完全隔离）

- **X-A 同快照五臂语义充分性**：独立研究轨。7/29 后才允许烧池（700–900 fresh CF×32B/ROME×B0+B3，双 8×H200 fp32 `WHYAAAI_DTYPE=float32`）；prereg v2 那时冻结并 commit（含 answer-only membership 前置门、P1/P2 端点、stop rules）。8/9 事后分解仅作内部 go 判断依据，**永不作为载具成功率证据报告**。产出用途：Phase-2 rebuttal（10/19–25，若进入且规则允许）→ camera-ready/扩展版 → 下一轮投稿升级件。
- 正文**不**把未运行的 X-A 设计列为贡献或"已冻结下一步"；§6 limitation 仅一句注明识别自然中介所需的实验形态（词法正交受控链替换）留作 future work。
- 其余 camera-ready 备忘照旧（J-lens 正式版、W-A 扩展、B23 held 臂等，plan 既有清单）。

## 8. 定稿判据（7/25 冻结时逐项打勾）

① checker 通过：全文每个数字有 results.json path；② 禁语清单零命中；③ X1 FAIL 可见且已防火墙（三句式+撤回句+controls-not-through-replay），并且 X2 strict null / X3 content audit / W-B null / G5 FAIL 全部可见；④ X2/X3 结果已写入（含 "repair not yet tested with MEMIT" 类过期句清零）；⑤ abstract 与全文数字逐一同源；⑥ taxonomy 全文统一 n=41/33 facts/κ=.813；⑦ Fig.1 第一视觉=认证缺口；⑧ related work 引用归属正确；⑨ provenance manifest 与上传 prereg 集合一致；⑩ 正文无未运行实验的结果性陈述。

## 9. 预期与止损

- 预期：模态面板 `5/6/6`，P(accept)≈45–50%；clear accept 需真语义中介或跨数据集强复制，**本窗口不现实，不追**。
- 止损：若 7/22 检查点触发，按 §4 降级；若期间发现新 HIGH 撞车，只改 §2 定位语，不改证据结构、不开实验。
