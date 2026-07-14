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
"Thinking Undoes Editing" 降级为项目代号 + §1 开篇钩子，钩子反用立 C1+C2：
*"Does thinking undo editing? Not in the weights — the edit survives direct probing — but at the answer, where reasoning routes around it."*

## Abstract（唯一版本，~230 词）

> Parametric knowledge editing is validated almost exclusively in a regime that deployed reasoning
> models never use: answering with no thinking. We show this is not enough. On
> DeepSeek-R1-distilled reasoners (ROME on CounterFact), edits that pass zero-thinking evaluation
> erode once a genuine chain of thought unfolds: on R1-Distill-Qwen-32B, natural thinking flips
> 9.2–19.3% of previously successful edits back to the old answer (strict–loose scoring; the strict
> rate agrees with an independent judge, κ=0.836), and paired edit success drops by 0.106
> [0.030, 0.182] — mirrored at 0.107 [0.032, 0.182] on R1-Distill-Llama-70B. The unedited base shows
> no such drift, a canned non-reasoning thought does not reproduce it, and the effect survives
> sampled decoding. The failure is not erasure: cloze re-probing finds the edit still installed in
> all 23 reverted cases examined, while a neutral three-judge census of 41 committed reversions
> (33 unique facts; κ=0.813) finds visible in-chain routes, predominantly Bridge (66%) and
> Recall (27%). Suppressing only first-token variants of the old answer inside the thinking span —
> answer logits untouched — removes the thinking tax (+0.106 → −0.035) and reduces reversion
> (0.193→0.085 loose; 0.092→0.042 strict), outperforms both an inert placebo and a same-relation
> strong competitor, is signed and dose-controlled, and its answer-level gains replicate at 14B and
> with MEMIT. Evidence spans six fixed checkpoints of two R1-distill families on CounterFact; the
> size association is supporting evidence, not a scaling law. Edit evaluation should include
> reasoning-time stress tests; the failure they reveal admits a chain-local causal control point.

## 数字对账表（checker 输入）

| abstract 数字 | JSON path |
|---|---|
| 9.2% / 19.3%（strict/loose 回退夹层） | `rq3.sup_battery.marginal_B3.N.RRs=.092` / `rq3.baseline.RR=.193` |
| judge κ=0.836 | `metric_validation.vs_RRs_strict_decontam.cohen_kappa` |
| 0.106 [0.030,0.182] | `capability.families.R1-Distill-Qwen.es_drop[3]/.es_drop_ci[3]` |
| 0.107 [0.032,0.182] | `capability.families.R1-Distill-Llama.es_drop[1]/.es_drop_ci[1]` |
| base 无漂移 | `base_probe.f1_edit_specificity.paired_ci`（−.0201 [−.0804,.0402] 含零） |
| canned thought 不复现 | `f2_zerothink_deconfound.arms`（B0P RR .040 vs B1 .208） |
| 采样稳健 | `f3_sampling_robustness.sampling_primary_complete_cases.ES_drop=.117[.067,.169]` |
| 23/23 cloze 完好 | `rq2_logitlens`（n=23，installation sanity） |
| 41 / 33 facts / κ=.813 / Bridge 66% Recall 27% | `rq2_taxonomy.p0_corrected_taxonomy`（.6585/.2683） |
| +0.106→−0.035 | `rq3.baseline.ES_drop` / `rq3.suppress.ES_drop` |
| 0.193→0.085 / 0.092→0.042 | `rq3.baseline.RR`→`rq3.suppress.RR` / `marginal_B3.N.RRs`→`T.RRs` |
| placebo/strong-competitor 对照 | `rq3.sup_battery.cross_arm_paired_ci.T_minus_C`（四端点排零） |
| 14B / MEMIT 迁移 | `rq3.s10_14b_fix_replication.TminusN_paired_ci` / `x2_memit14b_repair_replication.contrasts_B3.T_minus_C`（正文须并报 strict null） |

## 刻意不进 abstract 的项（防问）

- **CLR**：干预与指标同 span 的部分循环性，正文降为 manipulation check——abstract 不给它露脸机会。
- **X1 FAIL**：§6 一句 + supplementary gate 表；abstract 不是披露位。
- **locality/genbench**：Loc 只是 target non-leakage、TOST 未认证——abstract 写了就要 hedge，不写最干净。
- **per-case slope**：supporting outcome，abstract 已用"six fixed checkpoints…supporting evidence"覆盖其全部合法含义。
