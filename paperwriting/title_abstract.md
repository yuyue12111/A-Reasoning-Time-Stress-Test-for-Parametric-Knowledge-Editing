# title_abstract.md · W1 工作文件（**title 与 abstract v8.1 均已冻结**）

> **冻结状态**：Title 冻结；Abstract v8.1 内部终版冻结（188 词，SHA256 `0c85a03e…`）。OpenReview 当前仍是 v5；须等 D1–D8/R1 正文债务落地后一次性同步。
> **格式合规**：AAAI-27 Submission Instructions 无 250 词上限；OpenReview schema abstract `maxLength=5000` characters。
> 正文冻结前不再修改摘要；若正文债务暴露实质不一致，才按解冻流程重开审计。

> 纪律：本文件每个数字下表有 JSON path 对账；改数先改 `results.json` 永不反向。
> 禁语自查已过：无 invalid / capability-emergent / scaling-law 宣称 / 无 hedge 的 halves / mediation 类词。

## OpenReview 填报冻结记录（abstract registration，硬线 7/21）

- **Title**：冻结版逐字（见下节）。之后 PDF 标题必须与表单逐字一致（AI 辅助评审可机器比对）。
- **TL;DR（250 字符限）——最终版（2026-07-14 封版，Kimi 认输条#2 采 Codex 纠正）**：
    *An edit can pass direct-answer validation yet be overturned when the model reasons—while its edited association remains detectable at a cloze probe. Our stress test quantifies these reversions; think-span-only suppression lowers them.*（234 字符）
  - 纠正记录：原推荐版 "the edit itself remains detectable" 宽于证据上限（cloze 可探 ≠ 整个编辑 intact ≠ 排除功能性擦除，且 ROME 优化目标正是该 logit）——换 "its edited association remains detectable at a cloze probe" 逐字对齐；"thinking-budget" 由并排显示的 title 语义补全，不复述。三方确认后此为最后一个字节级动作，**锁不再开**。
  - 已作废旧版存档：Fable 228 字符版（detectable 措辞超限）；Codex 177 字符身份直陈版（丢 pass-yet-overturn beat）。
- **Abstract**：OpenReview 当前为 v5；内部终版为下文 v8.1。D1–D8/R1 在 §3–§5 落地并冻结前不得同步；届时只作一次表单替换与 byte-diff 核验。
- **Primary Topic（终裁，Codex 依官方 track scope 亲核 + Fable 同意）**：`PEAI: AI Evaluation, Auditing & Red Teaming`。不选 `PEAI: AI Alignment & Oversight`（会引来 oversight/governance 评审池）。
- **Secondary Topics（终裁：四项，第五留空；secondary 是双刃剑不为填满而填）**：
  ① ML: Machine Unlearning, Data Deletion & Model Editing ② ML: Reasoning & Test-Time Compute
  ③ NLP: Interpretability, Analysis & Evaluation (incl. Factuality & Hallucination) ④ PEAI: Safety, Robustness & Trustworthiness。
  不选 XAI（把火力引向我们主动降级的机理轴）；`NLP: (Large) Language Models` 仅作自愿第五项。
- **Reciprocal Reviewer**（7/21 后锁死）：先核 Haoyu Wang 是否满足 ≥2 一作/≥5 合著 archival 门槛并本人确认可承担 ≤6 篇；"no author qualifies" 是带 desk-reject 后果的声明，逐人核过才可选。
- 其余：作者列表=最终顺序（注册后通常锁死，勿留缺）、全员 profile 补齐（姓名/单位/单位邮箱/DBLP）、Country 按单位所在地、PDF/checklist/supplement 留空（7/28、7/31 分批传）、禁外部匿名仓库链接、License CC BY 4.0 默认。
- **提交后**：submission number + 确认截图记入行政台账（本文件追加一行即可）。

## Title（冻结，2026-07-14 用户拍板，Codex 提案 + Fable 复核同意）

> **Direct-Answer Edit Success Is Not Enough: A Reasoning-Time Stress Test for Parametric Knowledge Editing**

裁决记录：原候选 A/B/C 全部弃用。关键理由（Codex 提出、Fable 确认为实质问题而非风格问题）：
"Thinking **Undoes** Editing" 隐含参数级擦除，与 §4 核心发现（编辑未被擦除，23/23 cloze 完好）自相矛盾；
"Certified" 暗示形式化认证体系；"Causal Handle" 进标题会把火力引向 X1 FAIL。
冻结版每词站在证据上限内：Direct-Answer Edit Success 精确指向被挑战口径；Is Not Enough 诚实且不承诺认证体系；
Reasoning-Time Stress Test 是最稳的贡献身份；Parametric 限定 ROME/MEMIT 类。
Trade-off 自觉：标题只覆盖 C1，C2/C3 隐身 = under-promise/over-deliver，Phase-1 无 rebuttal 下的正确方向。
次选（未启用，Can 必须保留）：*Thinking Can Undo Editing: A Reasoning-Time Stress Test for Parametric Knowledge Editing*。
"Thinking Undoes Editing" 降级为项目代号 + §1 开篇钩子（Codex 二审后弱化版，"routes around it" 超证据已弃）：
*"Does thinking undo editing? The edited association remains detectable at a cloze probe — yet native reasoning can reverse the final answer."*

## Abstract v8.1 —— **INTERNAL FINAL / FROZEN**

> An edit can pass direct-answer validation yet lose control of the final answer when the model
> reasons. We evaluate each ROME edit on CounterFact twice—at zero thinking and after a natural
> chain—across six fixed checkpoints from two DeepSeek-R1-distill families. At the largest tested
> checkpoint in each family, edit success drops by 0.106 on Qwen-32B and 0.107 on Llama-70B. Among
> zero-thinking successes on Qwen-32B, old answers resurface in 19.3% of reasoned final answers and
> displace new answers outright in 9.2%, while the unedited base shows no detectable old-answer
> drift. Yet in the Qwen-32B reversions we examined, the edited association remains detectable at
> a cloze probe; separately, route analysis finds visible in-chain paths to old answers, motivating
> a chain-routing hypothesis. We next test for a chain-local control point by suppressing
> old-answer first tokens only during Qwen-32B reasoning, leaving answer logits untouched. The
> signed, dose-graded intervention offsets the edit-success loss and lowers the resurfacing rate
> from 19.3% to 8.5%; placebo and same-relation controls have near-null answer-level effects.
> Direct-answer edit success is not enough: edit evaluation needs a reasoning-time stress test,
> and the failure it reveals admits a chain-local causal control point.

- Final file: `paperwriting/delivery/abstract_v8_candidate.txt`; SHA256 `0c85a03e9cd288b45d6f23502caf17b74e84c28dee0f3a2e62f9202ec4b81e5f`.
- 门状态：G1–G4 PASS；G6.2 无观察到的可读性回归；G5 的处置表 PASS、正文债务仍 OPEN，因此只冻结文本、不改外部表单。
- v8→v8.1：删除 `marginal/loose` 摘要术语和会制造边际/配对算术疑问的 `−0.102`；拆开干预设计与因果校准；删除冗余 `paired`（S2 的 `each ... twice` 已建立配对设计）；恢复 `edit evaluation` 辖域。

## Abstract v5 —— **OPENREVIEW CURRENT BASELINE / INTERNALLY SUPERSEDED**

> Parametric knowledge edits are validated with direct answers; deployed reasoning models may
> reason before answering. We stress-test edits under a controlled thinking budget: the same ROME
> edit on CounterFact is scored at zero thinking and after a natural chain, across six fixed
> checkpoints of two DeepSeek-R1-distill families. At the largest tested checkpoint in each family,
> paired edit success drops 0.106 [0.030, 0.182] (Qwen-32B) and 0.107 [0.032, 0.182] (Llama-70B).
> On Qwen-32B, the old answer displaces the new one outright in 9.2% of zero-thinking successes and
> resurfaces in the final answer in 19.3% of them (strict scorer: Cohen's κ=0.836 vs. a neutral
> three-judge majority); erosion is edit-specific (no detectable unedited-base drift),
> content-dependent (a canned thought fails to reproduce it), and persists across three fixed
> sampling seeds. At Qwen-32B, reverted answers coexist with a still-detectable cloze edit (23/23
> examined). Separately, neutral three-judge majority labels identify a visible in-chain route in
> all 41 committed reversions (33 unique facts), motivating a chain-routing hypothesis. We next
> test for a chain-local control point: a signed, dose-graded suppression of the old answer's first
> tokens (think-span only; answer logits untouched)
> offsets the observed thinking tax (paired edit-success gain 0.138 [0.082, 0.194]) and lowers
> loose reversion to 8.5% (paired −0.102 [−0.170, −0.042]), beating a placebo and a same-relation
> competitor with near-null answer-level effects; the strict endpoint improves against both
> controls, though not detectably against no suppression. Edit-success gains replicate at 14B and
> transfer to MEMIT; strict transfer remains inconclusive. Direct-answer edit success is not
> enough: edit evaluation needs a reasoning-time stress test, and the failure it reveals admits a
> chain-local causal control point.

### v4→v5 修订记录（Codex 五审 REVISE-MINOR 两项，修毕即冻结；Fable 独立核验均成立）
1. **"every one … shows" → "neutral three-judge majority labels identify … in all 41"**：41 条中 35 全票、6 条 2–1（其一为 Recall/Associative/Recall），且 neutral prompt 允许 Associative=no traceable route——成立的是"多数票标签均为可见路线"，不是"每条客观无争议地 shows"（v1.85① 台账：unanimous=35、2–1=6、split=0）。
2. **"rather than simple erasure" 拆缝**：23/23 cloze（Qwen-32B、无对照 installation sanity，真源禁 abstract 承重）与 41 条 taxonomy 的逐 case crosswalk 缺 raw artifact（`BLOCKED_MISSING_PER_ITEM_ARTIFACT`）——原句暗示同 case 合取"编辑完好+可见路线⇒排除 erasure"。改为三段结构：coexist（At Qwen-32B）→ **Separately** + census → "motivating a chain-routing hypothesis" → "**We next test** for a chain-local control point:"——观察性假说与因果检验显式分层，叙事反而更强（诊断→检验）。
3. 词数裁决：257→263 词合规（AAAI-27 无词数上限、OpenReview 5,000 字符；本版 1,871 字符），"(33 unique facts)" 保留。

### v3→v4 修订记录（Codex 四审，四阻断项全采纳；其中两项是 Fable v3 压词时自己引入的回归）
1. **范围钉死**：9.2%/19.3% 是 Qwen-32B 的 11/119、23/119——句子重排为 "(Llama-70B). On Qwen-32B, the old answer…"，且与 F1/F2/F3 控制句合并在同一个 On-Qwen-32B 辖域下（顺带省词）。
2. **"Erosion concentrates" 删除**（Fable v3 自引回归）：32B−14B 直接差 `.0657 [−.0303,.1616]` 含零，"concentrates" 隐含已证梯度——换回 Codex 版 "At the largest tested checkpoint in each family"。
3. **"removes" → "offsets the observed thinking tax"**：T−N ES 增益 `.138` CI 下界 `.082 <` 观测税 `.106`，且无残余税等价性检验——"removes" 是完全消除宣称，证据只支持 offset。thinking tax 标签保留（Codex 准）。
4. **"stable" → "persists"**（Fable v3 自引回归）：三个固定 seed 非 seed-population 稳定性结论，F3 块自禁外推。
5. 非阻断项：`inert placebo` → `a placebo`（null-compatible ≠ 认证 inert）；对账表 "19.3% overall" 行标同步为 "of them"。
6. **叙事铰链（Codex 四审建议，以替换而非加字实现）**：删 κ=.813 与 Bridge/Recall 标签（细节归 §5），census 句改 "every one of 41 … shows a visible in-chain route"，接铰链 "pointing to a chain-routing vulnerability rather than simple erasure"——"pointing to" 保持溯因位阶（taxonomy 观察性 + X1 FAIL 禁因果升格），修复句用 "then" 回扣诊断。
7. 词数 257（v3 247 + 铰链净成本 ~10）；Codex 四审已明示词数非问题、密度是问题——若终审仍要压，唯一建议牺牲项为 "(33 unique facts)"（主文披露即可）。

### v2→v3 修订记录（Codex 三审 REVISE-ONCE，全部采纳 + 两处 Fable 变体待 Codex 终审）
1. **事实错误修正（三审唯一硬错，已核实）**："strict improves **only** against the competitor control" 删除——T−P strict `−.057 [−.114,−.010] p=.029` 同样显著（`contrasts_B3_mean_ci_p.T_minus_P.RRs`）；改为 "improves against both controls, though not detectably against no suppression"（T−N p=.073）。
2. **估计量纪律**：删 marginal 箭头 +0.106→−0.035；修复句全部换配对量——thinking tax removal = T−N ES `+.138 [.082,.194]`、loose 修复 = T−N RR `−.102 [−.170,−.042]`。marginal 箭头移主文（与配对量并列呈现）。
3. **分母修正**："19.3% overall" → "in 19.3% of them"（23/119，条件于 zero-thinking successes，防全样本误读）。
4. **范围收紧**：泛化句改 "Erosion concentrates at each family's largest checkpoint"（六格仅两高端排零）；控制句加 "On Qwen-32B" 前缀（F1/F2/F3 均为 32B 证据）。
5. **competitor 锚点换正**：abstract 的 largely-inactive（X2/X3 跨协议活跃度数据）→ "with near-null answer-level effects"（主 ROME-32B 电池自身证据：C−N RRs `−.0093 [−.0467,.028] p=.83` + `_C_arm_M4`）；X2/X3 的 T=109/C=18 只在 §5 相应协议处使用。
6. **待 Codex 终审的两处 Fable 变体**：(a) "Erosion concentrates at…" 替代其 "At the largest tested checkpoint…erode"（等价范围、更顺）；(b) 保留 "thinking tax" 标签但括号内改配对增益（其建议句删掉了该标签）。
7. 词数 247（目标 235–240）：已砍 Bridge/Recall 百分比与 "anywhere"；再压需牺牲 (a) "(23/23 examined)" (b) 三判官归属细节 (c) route 名称之一——留 Codex/用户选。

### v1→v2 修订记录（Codex 二审裁决 + Fable 复核，全部纯文字零新数字）
1. "flips 9.2–19.3% back" → 拆开语义：strict=「displaces outright」(11/119)、loose=「resurfaces in the final answer」(23/119, overall 表明包含关系)——语义各自贴口径，叙事保留。
2. κ=.836 归属修正：strict 规则 vs 三判官多数票的 Cohen κ（分层验证样本细节留 §3/§5）。
3. **删除 0.092→0.042 箭头**（T−N strict −.0508 [−.1017, 0.000] p=.073 未排零，不许借 T−C 显著性）；修复句改由 T−N 自身显著的两条承重：ES +.1378 [.0816,.1939]、loose RR −.1017 [−.1695,−.0424] p=.001；strict 明写 "improves only against the competitor control"（T−C −.0566 [−.1132,−.0094] p=.0324）。
4. MEMIT 收窄："transfer to MEMIT, where strict transfer remains inconclusive"（X2 RRs −.0268 [−.0804,.0268] 含零）。
5. competitor 加 largely-inactive（B3 改变行 T=109 vs C=18）。
6. "never use" → "may reason before they answer"；"no such drift" → "no detectable drift"；"survives sampled decoding" → "persists across three fixed sampling seeds"；"The failure is not erasure" → "Reverted answers coexist with a still-detectable cloze edit"（23/23 是无对照 installation sanity）。
7. 删除 "size association is supporting evidence" 防御句——abstract 不再做任何尺寸关联 claim，无 claim 即无需 hedge；scope 由 "six fixed checkpoints from two families" 描述性携带。
8. §1 钩子同步弱化（见下）。

## 数字对账表（checker 输入）

| abstract 数字/措辞 | JSON path / 承重证据 |
|---|---|
| displaces outright 9.2%（strict=含旧不含新，11/119） | `rq3.sup_battery.marginal_B3.N.RRs=.092`；定义 `src/metrics.py`（RRs=old-without-new） |
| resurfaces in the final answer in 19.3% **of them**（loose=答案现旧值，23/119，同分母含 strict；禁 "overall"——防全样本 198 误读） | `rq3.baseline.RR=.193`（Qwen-32B only） |
| strict scorer Cohen κ=0.836 vs 三判官多数票 | `metric_validation.vs_RRs_strict_decontam.cohen_kappa`（分层验证样本 n=87，`src/sj_validate.py`） |
| 0.106 [0.030,0.182] | `capability.families.R1-Distill-Qwen.es_drop[3]/.es_drop_ci[3]` |
| 0.107 [0.032,0.182] | `capability.families.R1-Distill-Llama.es_drop[1]/.es_drop_ci[1]` |
| no detectable drift（null 措辞，非 absence） | `base_probe.f1_edit_specificity.paired_ci`（−.0201 [−.0804,.0402] 含零） |
| canned thought 不复现 | `f2_zerothink_deconfound.arms`（B0P RR .040 vs B1 .208） |
| persists across three fixed sampling seeds | `f3_sampling_robustness.sampling_primary_complete_cases.ES_drop=.117[.067,.169]` |
| coexist with still-detectable cloze edit, 23 cases（无对照 sanity 措辞） | `rq2_logitlens`（n=23，installation sanity） |
| 41 / 33 facts / κ=.813 / Bridge 66% Recall 27% | `rq2_taxonomy.p0_corrected_taxonomy.n=41` / `.n_unique_facts=33` / `.agreement.fleiss_kappa` / `.pct.Bridge` / `.pct.Recall` |
| **offsets** the observed thinking tax（paired gain 0.138 [0.082,0.194]） | `rq3.sup_battery.cross_arm_paired_ci.T_minus_N.ES`；**禁 removes**（增益 CI 下界 .082 < 观测税 .106，无残余税等价检验）；marginal 箭头 +0.106→−0.035 只进主文并与配对量并列 |
| a placebo（禁 inert 前缀） | `rq3.sup_battery.contrasts_B3_mean_ci_p.P_minus_N` 全含零 = null-compatible ≠ 认证 inert |
| majority labels identify a visible in-chain route in all 41 / "motivating a chain-routing hypothesis" | `p0_corrected_taxonomy`：41=Bridge 27+Recall 11+RO 3+Assoc 0，unanimous 35、2–1 6；**多数票口径**，禁 "every one shows"；"motivating a hypothesis"=溯因，禁升 "re-derivation causes"（X1 9/18 FAIL） |
| coexist 句与 census 句必须 "Separately" 分层 | 23-cloze↔41-taxonomy 逐 case crosswalk `BLOCKED_MISSING_PER_ITEM_ARTIFACT`（rq2_logitlens 附注）——禁同 case 合取表述"编辑完好+可见路线⇒排除 erasure" |
| lowers loose reversion to 8.5%（paired −0.102 [−0.170,−0.042]） | `rq3.sup_battery.cross_arm_paired_ci.T_minus_N.RR p=.001`；8.5%=`rq3.suppress.RR` |
| strict improves against **both** controls, not detectably vs. no suppression | T−P RRs `−.057 [−.114,−.010] p=.029` + T−C RRs `−.0566 [−.1132,−.0094] p=.0324`；T−N RRs p=.073→**禁 only-vs-competitor、禁 0.092→0.042 箭头** |
| competitor with near-null answer-level effects | `rq3.sup_battery.cross_arm_paired_ci.C_minus_N`（RRs −.0093 [−.0467,.028] p=.83）+ `rq3.sup_battery._C_arm_M4`；X2/X3 的 T=109/C=18 活跃度数据仅限 §5 对应协议使用 |
| Erosion concentrates at each family's largest checkpoint / On Qwen-32B 前缀 | 六格仅 2 格排零（`capability.families.*.es_drop_sig`）；F1/F2/F3 全为 32B 证据 |
| replicate at 14B / MEMIT strict inconclusive | `rq3.s10_14b_fix_replication.TminusN_paired_ci`（14B 无 C 臂，T−N）/ `x2...contrasts_B3.T_minus_C`（ES +.100 显著；RRs −.0268 [−.0804,.0268] 含零） |

## 刻意不进 abstract 的项（防问）

- **CLR**：干预与指标同 span 的部分循环性，正文降为 manipulation check——abstract 不给它露脸机会。
- **X1 FAIL**：§6 一句 + supplementary gate 表；abstract 不是披露位。
- **locality/genbench**：Loc 只是 target non-leakage、TOST 未认证——abstract 写了就要 hedge，不写最干净。
- **per-case slope**：supporting outcome，正文供货，abstract 不承载。
- **尺寸关联 hedge 句**（v2 起删除）："size association is supporting evidence, not a scaling law" 整句退场——abstract 不做任何尺寸关联 claim，无 claim 即无需 hedge；scope 由 "six fixed checkpoints from two families" 描述性携带（Codex 二审同意，Fable 采纳）。

## Kimi 独立终审（2026-07-14，第三方，先独立重算后读修订史）

- **裁决：Title FREEZE / Abstract FREEZE，零 blocking**。逐句 claim ledger 与 Codex/Fable 结论独立收敛（含两 κ 归属、near-null 换锚、T−P/T−C/T−N 分层、跨样本 Separately 纪律）。三方全体一致，冻结成立。
- 评分：清晰 8 / 惊讶 7 / 可信 9 / 记忆 7 / 顶会味 7。
- **解冻事件顺手采纳清单**（Kimi 三项 optional；单独不值得解冻，冻结期禁改）：
  1. S5 尾加 "(…; an installation sanity check)"（+4 词，preempt vacuity 攻击）；
  2. ~~S4 loose 显式标注 "(loose upper bound; …)"~~ **作废（Kimi 自撤，2026-07-14）**：`vs_RR_loose_decontam` recall=.96、FN=1（judge-true 回退被 loose 漏检=alias gap）→ loose **不是数学上界**，标注反引入新过度宣称；"resurfaces in the final answer" 原样最稳；
  3. S7 消歧 "…a placebo and a same-relation competitor, both near-null at the answer level;"。
- **两个校准分歧的终裁**：
  1. S5 去留（Kimi 主删）：**保留**。Kimi 记忆测试(G)自证"编辑仍完好"是应记住句的核心成分，删 S5 = 塌回"长推理掉点+补丁"故事；字面已三重弱化+分层。保险转为主文义务：§4 以 installation sanity check 身份+全 caveat 呈现 cloze 检查（WRITING_PLAN 已令）。
  2. X1 FAIL 显眼度（Kimi 加严）：**采纳**。披露位置从"正文一句"升级为"机理章 routing-hypothesis 讨论紧邻位置，作为『你直接测过链作为自然载具吗』的正面回答"（WRITING_PLAN 已令）。
- **W3 hostile-review 靶标（Kimi 供出的拒稿一句话，全文须逐分句预置回答）**：
  "A real but narrow evaluation gap on CounterFact/ROME; the mechanism is observational, the preregistered mediation test failed, and the fix is a decoding-time lexical patch whose strict endpoint is null against the natural baseline."
- 记忆落差修正令：chain-local causal control point（最硬 novelty）读者记忆排第三——§1 贡献列表与 §7 结论句上提该 beat（零新数字）。
