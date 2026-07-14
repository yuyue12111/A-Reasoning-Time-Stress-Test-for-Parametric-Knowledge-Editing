<!-- 写作前材料(gap-review level-change-D4);折进 LaTeX 时复核数字;非写作真源 -->

# LEVEL vs. CHANGE — 统一命名段(gap-review D4)

**做什么**：把 `_pending_draft_edits` 里三条互不引用的散句（F1 / cap3 / B15）合成**一段**统一陈述 + 互指。三者是同一个设计模式：**base 的 LEVEL 混淆**（知识天花板 + base-CLR 底噪，随 scale 升）vs **edited 的 CHANGE 测量**（B0→B3 降幅 / RR）。erosion 量的是 CHANGE，不是 LEVEL；LEVEL 上升是混淆原料，被三重中和。

**放哪**：建议进 §4（`sec:rq1`，capability-emergent erosion）作一个 anti-confound `\paragraph`，紧邻 6 尺度 base-probe 表（表本身可在 §3 `sec:setup` 或 §4）。也可整段进 §3 方法。此段落**吸收并替换**下列现有 pending 散句，写完后这些不再单独入文：
- F1 散句 = `base_probe.f1_edit_specificity` + B13 pending（"base 无系统性向 o_old 漂移，配对 CI 含零"）
- cap3 散句 = §RQ2 honest-restate pending（"CLR 涌现 base-floor 已闭，net-CLR 含零→退役"）
- B15 散句 = pending #14（contrib-3 升格版 "robust to per-case base-knowledge control"）
- RQ1 anti-confound pending（"LEVEL vs CHANGE + confound 预测的 rising base-Δ 未观察到"）

---

## 命名约定（写进正文一次，后文复用）

- **LEVEL**（静态属性，随能力/规模升）：
  - *knowledge ceiling* = 未编辑 base 对目标事实的回忆 `answer_old@B0`，1.5B→70B 单调升 **0.515 → 0.785**。
  - *base chain-leak floor* = 未编辑 base 链里提及旧事实的底噪 `base-CLR@B3`，**0.582 → 0.905**（随 scale 升，但**非严格单调**：Qwen-14B 0.860 > Qwen-32B 0.829；表述禁用"均单调"）。
- **CHANGE**（我们的 erosion 主张，思考对**已装好**的编辑造成的变化）：`B0→B3` 的 ES 降幅 / 回退率 RR（32B headline：RR 0.193、ES 降幅 0.106）。
- 一句核心：*larger models both **know** and **voice** the old fact more*（LEVEL 升）——这正是混淆原料；我们在三个 erosion 指标上分别把 LEVEL/CHANGE 拆开。

---

## drop-in 段落（paper-ready English prose，折 LaTeX 用）

> \paragraph{Level versus change: neutralizing the base-knowledge confound.}
> Two base-model quantities rise with scale and could, in principle, masquerade as erosion. A base-knowledge probe on the \emph{unedited} weights (same word-boundary scoring) shows the target-fact recall ceiling climbing from $0.515$ (Qwen-1.5B) to $0.785$ (Llama-70B), and the base chain-leak floor---how often an \emph{unedited} chain mentions the old fact---climbing from $0.582$ to $0.905$ (rising with scale, though not strictly monotone: Qwen-14B $0.860 >$ Qwen-32B $0.829$). These are \emph{levels}: static properties of what a larger model knows and voices by default. Our erosion claim is a \emph{change}: the $B_0\!\to\!B_3$ drop that thinking inflicts on an \emph{installed} edit (ES drop / RR). A larger model that both knows and voices the old fact more is exactly the raw material of a confound, so we separate level from change on each erosion metric.
>
> \emph{(i) The reversion is not base thinking-drift.} On the unedited 32B base, letting the model think does \emph{not} systematically move probability toward the old fact: $\Delta P(o_\text{old})$ from $B_0$ to $B_3$ is $-0.020$ (per-case paired-bootstrap 95\% CI $[-0.080,+0.040]$, $n{=}199$, contains zero) against an edited reversion rate of $0.193$ (a margin of $\approx 0.21$). The base shows \emph{no systematic drift} toward $o_\text{old}$ under thinking---we do not claim it drifts \emph{away}, the CI is consistent with no drift---so the reversion cannot be attributed to a base-prior dynamic the edit merely rides on; it is edit-specific. Across the other five scales the base thinking-drift stays small ($|\Delta|\le 0.025$); the Qwen-7B point ($+0.08$) is the documented math-specialized-base outlier (margin $\approx 0$, \S\ref{sec:limitations}) and is excluded from this generalization rather than treated as support.
>
> \emph{(ii) The chain-leak trend is a base-floor artifact, so we read it as descriptive.} Pooled across scales the raw chain-leak slope is strongly positive ($1.13$, CI $[0.82,1.47]$), but once each case is netted against its \emph{own} base chain-leak floor the net-CLR slope collapses to $0.05$ (CI $[-0.02,0.12]$, $n{=}793$; the six-scale fit agrees, $0.05$, CI $[-0.01,0.15]$). The edited chain leaks the old fact at a roughly constant $\sim\!0.3$--$0.5$ \emph{below} its base floor---a gap that does not widen with capability. We therefore report the rising CLR as \emph{descriptive}, not as edit-specific emergence.
>
> \emph{(iii) The ES-drop emergence survives base-recall control.} The erosion metric that carries the capability trend is the ES drop, and it is \emph{not} a knowledge-coverage artifact: regressing the per-case ES drop on $\log_{10}$ parameters gives slope $0.101$ (CI $[0.030,0.168]$, $p{=}0.004$, matched $n{=}993$), essentially unchanged at $0.099$ ($p{=}0.004$) after adding per-case base recall (and chain length) as covariates. The trend concentrates where the base actually knows the old fact (slope $0.127$, CI $[0.038,0.209]$, excludes zero) and vanishes where it does not ($0.043$, CI $[-0.158,0.168]$, contains zero): base knowledge is the \emph{fuel}, capability the \emph{engine}---a mechanism-consistent pattern (nothing to re-derive $\Rightarrow$ nothing to erode), not a confound.
>
> Together these separate what we measure (the thinking-induced \emph{change} to an installed edit) from what merely rises with scale (the base \emph{level} of knowledge and default leakage): the RR effect is edit-specific (i), the CLR trend is demoted to descriptive as a base-floor artifact (ii), and the load-bearing ES-drop emergence is robust to per-case base-knowledge control (iii).

---

## 互指 / cross-reference map（防止再分叉）

| 支柱 | 中和的是哪种 LEVEL 混淆 | 口径/尺度 | 结论极性 | results.json 源 |
|---|---|---|---|---|
| **F1** | base 思考净漂 `delta_think`（会不会 base 一思考就自己漂向 o_old） | 32B 单尺度 + 6 尺度 delta_think 小 | **null**（Δ≈0 含零）→ RR edit-specific；**禁写"反向漂移"** | `base_probe.f1_edit_specificity.paired_ci` |
| **cap3** | base-CLR 底噪随 scale 升（CLR 涌现是不是底噪共线） | 4 尺度 n=793（6 尺度确认） | **退役**（net-CLR 含零）→ CLR 只作描述 | `emergence.cap3_netclr` |
| **B15** | base_recall（涌现是不是知识覆盖伪影） | 5 尺度 matched n=993 | **PASS**（控后 slope 不变）→ es_drop 涌现承重 | `emergence.b15_base_recall_control` |

**互指纪律**：正文这一段是三者的唯一落点；§4 capability 主张引 (iii)/B15，§5(RQ2) 的 CLR 措辞引 (ii)/cap3，§7 limitation 的 base-drift 句引 (i)/F1，均 cross-ref 本段而非各自复述数字。三处**同一段**、不再"各半"。

## 禁区自查（本段踩线点）
- F1 是 **null**：只写 "base 无系统性向 o_old 漂移（配对 CI 含零）"，**不写** "反向漂移 / away-drift"，**不写** "truth-restoration 被否"（F1 不背书任何 truth-tracking 读法）。
- cap3 = **诚实退役**：CLR 涌现降为描述，**不写** "CLR 涌现是 edit-specific / 已确认"；net-CLR 含零如实报。
- B15 = **PASS**，可用肯定语气（"robust to per-case base-knowledge control"），但涌现整体仍是 supporting trend（K=2 族边界见 §7），本段不升格为 scaling law。
- 数字只此段一处，跨节引用不复制数值（防跨源分叉）。