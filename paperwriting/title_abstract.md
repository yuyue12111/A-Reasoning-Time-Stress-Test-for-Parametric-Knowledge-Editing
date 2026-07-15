# title_abstract.md · W1 工作文件（2026-07-14 起草；**title 已冻结**，abstract 为唯一版本）

> 纪律：本文件每个数字下表有 JSON path 对账；改数先改 `results.json` 永不反向。
> 禁语自查已过：无 invalid / capability-emergent / scaling-law 宣称 / 无 hedge 的 halves / mediation 类词。

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

## Abstract v3（唯一版本；2026-07-14 按 Codex 三审 REVISE-ONCE 修订，待终审冻结）

> Parametric knowledge edits are validated with direct answers; deployed reasoning models may
> reason before answering. We stress-test edits under a controlled thinking budget: the same ROME
> edit on CounterFact is scored at zero thinking and after a natural chain, across six fixed
> checkpoints of two DeepSeek-R1-distill families. Erosion concentrates at each family's largest
> checkpoint: paired edit success drops 0.106 [0.030, 0.182] (Qwen-32B) and 0.107 [0.032, 0.182]
> (Llama-70B); the old answer displaces the new one outright in 9.2% of zero-thinking successes and
> resurfaces in the final answer in 19.3% of them (strict scorer: Cohen's κ=0.836 vs. a neutral
> three-judge majority). On Qwen-32B, erosion is edit-specific (no detectable unedited-base drift),
> content-dependent (a canned thought fails to reproduce it), and stable across three fixed
> sampling seeds. Reverted answers coexist with a still-detectable cloze edit (23/23 examined); a
> three-judge census of 41 committed reversions (33 unique facts, κ=0.813) finds visible in-chain
> routes, predominantly Bridge and Recall. A signed, dose-graded suppression of the old answer's
> first tokens—think-span only, answer logits untouched—removes the thinking tax (paired
> edit-success gain 0.138 [0.082, 0.194]) and lowers loose reversion to 8.5% (paired −0.102
> [−0.170, −0.042]), beating an inert placebo and a same-relation competitor with near-null
> answer-level effects; the strict endpoint improves against both controls, though not detectably
> against no suppression. Edit-success gains replicate at 14B and transfer to MEMIT; strict
> transfer remains inconclusive. Direct-answer edit success is not enough: edit evaluation needs a
> reasoning-time stress test, and the failure it reveals admits a chain-local causal control point.

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
| resurfaces 19.3% overall（loose=答案现旧值，23/119，同分母含 strict） | `rq3.baseline.RR=.193` |
| strict scorer Cohen κ=0.836 vs 三判官多数票 | `metric_validation.vs_RRs_strict_decontam.cohen_kappa`（分层验证样本 n=87，`src/sj_validate.py`） |
| 0.106 [0.030,0.182] | `capability.families.R1-Distill-Qwen.es_drop[3]/.es_drop_ci[3]` |
| 0.107 [0.032,0.182] | `capability.families.R1-Distill-Llama.es_drop[1]/.es_drop_ci[1]` |
| no detectable drift（null 措辞，非 absence） | `base_probe.f1_edit_specificity.paired_ci`（−.0201 [−.0804,.0402] 含零） |
| canned thought 不复现 | `f2_zerothink_deconfound.arms`（B0P RR .040 vs B1 .208） |
| persists across three fixed sampling seeds | `f3_sampling_robustness.sampling_primary_complete_cases.ES_drop=.117[.067,.169]` |
| coexist with still-detectable cloze edit, 23 cases（无对照 sanity 措辞） | `rq2_logitlens`（n=23，installation sanity） |
| 41 / 33 facts / κ=.813 / Bridge 66% Recall 27% | `rq2_taxonomy.p0_corrected_taxonomy`（.6585/.2683） |
| removes the thinking tax（paired gain 0.138 [0.082,0.194]） | `cross_arm_paired_ci.T_minus_N.ES`；marginal 箭头 +0.106→−0.035 只进主文并与配对量并列 |
| lowers loose reversion to 8.5%（paired −0.102 [−0.170,−0.042]） | `cross_arm_paired_ci.T_minus_N.RR p=.001`；8.5%=`rq3.suppress.RR` |
| strict improves against **both** controls, not detectably vs. no suppression | T−P RRs `−.057 [−.114,−.010] p=.029` + T−C RRs `−.0566 [−.1132,−.0094] p=.0324`；T−N RRs p=.073→**禁 only-vs-competitor、禁 0.092→0.042 箭头** |
| competitor with near-null answer-level effects | `cross_arm_paired_ci.C_minus_N`（RRs −.0093 [−.0467,.028] p=.83）+ `sup_battery._C_arm_M4`；X2/X3 的 T=109/C=18 活跃度数据仅限 §5 对应协议使用 |
| Erosion concentrates at each family's largest checkpoint / On Qwen-32B 前缀 | 六格仅 2 格排零（`capability.families.*.es_drop_sig`）；F1/F2/F3 全为 32B 证据 |
| replicate at 14B / MEMIT strict inconclusive | `rq3.s10_14b_fix_replication.TminusN_paired_ci`（14B 无 C 臂，T−N）/ `x2...contrasts_B3.T_minus_C`（ES +.100 显著；RRs −.0268 [−.0804,.0268] 含零） |

## 刻意不进 abstract 的项（防问）

- **CLR**：干预与指标同 span 的部分循环性，正文降为 manipulation check——abstract 不给它露脸机会。
- **X1 FAIL**：§6 一句 + supplementary gate 表；abstract 不是披露位。
- **locality/genbench**：Loc 只是 target non-leakage、TOST 未认证——abstract 写了就要 hedge，不写最干净。
- **per-case slope**：supporting outcome，正文供货，abstract 不承载。
- **尺寸关联 hedge 句**（v2 起删除）："size association is supporting evidence, not a scaling law" 整句退场——abstract 不做任何尺寸关联 claim，无 claim 即无需 hedge；scope 由 "six fixed checkpoints from two families" 描述性携带（Codex 二审同意，Fable 采纳）。
