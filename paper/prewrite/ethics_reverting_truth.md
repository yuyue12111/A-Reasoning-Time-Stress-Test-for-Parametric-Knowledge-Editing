<!-- 写作前材料(gap-review ethics-必4);折进 LaTeX 时复核数字;非写作真源 -->

# Ethics statement + reverting-to-truth defense (gap-review 必4 / red-team R1′)

**用途**：折进 LaTeX 的 Ethics Statement（AIA track），正面设防「你们在惩罚模型说真话、并工程化了一个压制真话链的工具」这一反转读法（红队新头号拒稿理由 R1′）。三件套=认识论对称 / dual-use / 边界。**只写连接组织、不重复数字**——所有量化证据以交叉引用（§K2′ 知识冲突、6-尺度 base-probe 表、部署门、taxonomy never-silent 结果、§RQ1 F1）承载，正文另处已报。

**三禁区自查（已遵守）**：
1. 不把 `N_RR|CLR0=0.000` 硬化为「可监控信号」——最后一句显式声明「不主张无痕即可作可靠监控」（守 B6 地板效应裁决）。
2. 不写「truth-restoration 被否掉」——F1 是 null，只写「base 无系统性向旧值漂移，与 truth-restoration 读法不一致」。
3. 默认不引 Korbak/Baker（不主动向审稿人递 CoT-monitorability 碰撞框架）；7/14 触发器另议。

**行政待查（标一句）**：待核实 AAAI-27 author kit 是否将 Ethics Statement 计入 7 页正文页限。惯例上 reproducibility checklist 不计页限，但 Ethics/Impact 段若嵌正文通常计入——以 CFP/author kit 为准，勿据惯例硬编排版预算。

---

## Ethics Statement（草稿 prose，可直接折进 LaTeX）

Because CounterFact injects a counterfactual over a real-world true value, a reader could reframe every reversion as the model restoring a truth we engineered away, and our chain-only repair as a tool for silencing true reasoning; we address this reading directly. Epistemically, the two readings are symmetric at the level of the frozen weights: a legitimate corrective update and an adversarial counterfactual edit are the same operation---a localized parameter change the network may later route around---and nothing in the mechanism distinguishes them. What our results characterize is prior-reassertion, not truth-tracking: the chain re-derives whatever the base network already encoded, reversion concentrates precisely where the base already holds the old value (the knowledge-conflict analysis, \S\ref{sec:kc}) and scales with base recall across the six-scale base-probe table (\S\ref{sec:base}), so it follows the strength of the pre-existing prior rather than its veracity. Consistent with this, the unedited base shows no systematic drift toward the old value under added thinking (\S\ref{sec:rq1}), which is not the behavior a truth-restoration account would predict.

This symmetry is inherently dual-use: the same chain-only suppressor we use to defend a correct edit could equally be aimed at a fact the model knows to be true, suppressing veridical content inside the reasoning trace \citep{lightedit2604,whyknow2603}. We therefore flag the intervention as a research diagnostic for isolating the mechanism, not as a deployment-ready capability.

Three properties bound this concern. The suppressor is edited-query-gated---it fires only on the specific (subject, relation) whose edit is being defended and leaves general-task accuracy unchanged at the point estimate (within our $\pm0.02$ gate on the point estimates, though not a certified equivalence; \S\ref{sec:deploy}), so it is not a general truth-suppression capability. It is an inference-time steering intervention rather than a training pressure: it updates no weights and applies no optimization toward concealment, so it induces no gradient toward learned deception. Finally, the natural failure it targets is legible---by a three-judge taxonomy the committed reversions we study are almost never silent (Associative $1/50$), each leaving a verbalized trace in the chain---whether a re-derivation of the old fact (the dominant Bridge route) or a direct recall (\S\ref{sec:taxonomy})---so the phenomenon surfaces in an auditable reasoning trace rather than as a hidden internal change; we make no claim that the absence of such a trace could itself serve as a reliable monitor.

---

## 交叉引用地图（写作时把 \S\ref 换成实际 label）

| prose 交叉引 | 指向 | results.json 承载数（正文另处报，此段不重复） |
|---|---|---|
| §kc（knowledge-conflict） | §K2′ / RQ2-KC 段 | `rq2_kc`：base-knows RR 0.250 vs base-unknown RR 0.032（8×） |
| §base（6-尺度 base 表） | §3/§7 base-probe 表 | `base_probe._six_scale_summary.answer_old_b0` 0.515→0.785 |
| §rq1（F1 无漂移） | §RQ1 反混淆句 | `base_probe.f1_edit_specificity.paired_ci`：Δ=−0.020 [−0.080,+0.040], n=199（含 0=null） |
| §deploy（部署门） | §6 部署门 | `rq3.genbench`：GSM8K Δ+0.005 / MATH 0.000 |
| §taxonomy（never-silent） | §5 taxonomy | `rq2_taxonomy.b16_widened_pool`（Associative 1/50）+ `wide_census_traceless`（0/17） |
| citations | 引用池 | LightEdit `2604.19089`（解码期抑制原知识=修复线最近邻）、Why-Models-Know `2603.26410` |

**引用 key 占位**：`\citep{lightedit2604}`=2604.19089、`\citep{whyknow2603}`=2603.26410（折进时用 bib 真 key，勿改 arXiv id）。这两条是 dual-use 句唯一载体，均在已验引用池内；未引 Korbak/Baker（守禁区 3）。
