---

# 第一性 solidity 审查 ·「越想越退」

立场:默认拒。我读了 `paper/draft.md`、`paper/results.json`,并逐口径核了 `src/`(logit_lens / necessity_check / metrics / chain_classify / suppress / think_budget / cross_arm / percase_emergence),不信 prose、只信代码算的是什么。下面每条都带 file:line 和 results.json 真数。

---

## 1. 盲猜 vs 实际

读数字前我对一篇"立得住"的版本的预期,和实际的差距:

|我审前预期承重结果应有的样子|实际有的|差距=信号|
|---|---|---|
|RQ2「非擦除」应是**链跑完后内部状态**仍编辑/或漂移的证据|`logit_lens.py:104–116` 是**重新施一遍编辑 + 喂裸 cloze(无链)** 的一次前向,`intact=gap[-1]>0`|旗舰机理是个**静态权重 sanity check**,与导致回退的那条链零关系|
|capability-emergent 在 6 点上会脆,但至少一个答案级指标显著|per-case 只有 **CLR** 活(slope 0.372),es_drop/rr 的 per-case slope 都含零(`emergence.percase`)|唯一活的指标(CLR)恰恰**不区分回退**(见下),且 p=0.0007 来自 **K=2 族**的 cluster bootstrap|
|修复 RR 0.193→0.085 看着强,猜 footprint 不大|b0ok≈119,loose 回退 **~23→~10**、strict(RRs 0.092→0.042)**~11→~5**|"腰斩回退"=挪动 **~6(严)/~13(松)条 case**|
|necessity 大概是 taxonomy 的重读|`necessity_check.py:45–48` 确实只重读 `labels_*.jsonl` 的 route;且 **held 14/14=100% clr**|比预期更糟:o_old 现于链在**回退(0.895)和非回退(1.00)里都满**=反向无区分力|
|判官面板我猜是中性的|**`chain_classify.py:25` 判官 prompt 仍把结论告诉判官**(见 §3 最弱项)|团队自己 depth-plan 点名要删的偏置句**没删**,却给姐妹面板删了|

一句话:**这篇真正立得住的是 RQ3(链级修复,代码可证答案段未触),不是它现在挂的头牌 RQ2(非擦除机理)。MECH-led reframe 把最强的腿(RQ3)和支撑最弱的腿(RQ2)绑成了一个头牌。**

---

## 2. 承重 claim 第一性体检

### Claim A —「回退不是擦除,是链内重推绕过完好编辑」(RQ2,头牌的机理腿)

- **要成立需要**:有一个能**区分回退 vs 非回退**的内部测量,显示回退特异地走了"链内重推"而非别的链动力学。
- **证据链断在哪**:
    1. `logit_lens.py` 探针**门控在 b0ok**(:43)+ 喂**无链 cloze**(:107)+ 读静态权重一次前向。ROME 的优化目标**就是**让 cloze 顶层出 o_new → `edit_intact_pct=1.0` 是**近乎恒真**,且它"排除"的假说(解码擦权重)在本设置下**物理不可能**(前向不改权重)。它对**held 案例会给一模一样的 ~100% + 同样中层 dip**(g8=−0.246/g12=−0.351 正落在 inject layer 12 = 编辑注入签名,不是回退相关物)。**没有任何非回退对照**(`depth-plan` B1 自己列为 TODO)。
    2. 中层"旧事实仍在"=**点估、无 n、无 CI**(`logitlens.gap_sampled` 是手填、无 jsonl;32B 回退 n=10)。
    3. taxonomy「90% Bridge / Recall=0 / Associative=0」是**被污染的判官**产的(见 §3)。
- **当前强度**:**major(威胁录用)**。作为头牌它过度承诺("we trace the cause");去掉污染和恒真后,RQ2 的真实内容退化为"编辑确实在权重里(平凡)+ 回退走 bridge(描述性、n=19、待去污)"。

### Claim B —「signed/specific/dose-controlled 链级修复 = 链(非擦除)驱动答案」(RQ3,真承重)

- **要成立需要**:只动链、答案段证明未触、效应特异于 o_old、有剂量、有惰性 placebo floor。
- **证据链**:**代码全过**。`think_budget.py:87` 答案段 `use_sup = … and scope=='all'` → scope=think 下答案段 `lp=None` 逐字节原解码 → "答案未触"是**架构保证**不是断言;`cross_arm.py` 是**按 case 配对** bootstrap、b0ok 门跨臂一致;T−P 四指标排零(RR −0.095 p=.010 / ES +0.122 p=.002 / CLR −0.228 p<.001 / RRs −0.057 p=.029),P−N≈0(RR 恰 0.0),D−N 反号(ES −0.217),符号阶梯 D<N~P<T 如预注册;α-sweep Loc 全程 0.958。
- **断点**:(i) 这是**抑制下的充分性**,不是**自然生成的必要性**;(ii) 特异性只相对**惰性** placebo(`placebo_donor.py` 取别的 case 的 o_old,**从不取竞争答案 o_new**),D 只管符号;(iii) footprint ~6/~13 case。
- **当前强度**:**minor(不威胁,但窄)**。这是全篇最干净的一条;弱点都被 draft 显式 bound 了。**它没靠 RQ2 的 logit-lens**——这恰恰说明头牌该以 B 为中心,而非 A。

### Claim C —「erosion 随能力涌现(跨两族六尺度)」(支撑趋势)

- **要成立需要**:跨能力代理的斜率,其推断不靠"把两条短曲线当独立点"。
- **断点**:per-case「fatal 修复」用的是 **K=2 族 cluster bootstrap**(`percase_emergence.py:339` `rng.integers(0,2,2)`)。我枚举了组成:**25% 仅 Qwen / 25% 仅 Llama / 50% 双族**,且 drop-one family FE 把斜率识别成**族内**量 → **p=0.0007 是"族内池化斜率"冒充"跨族 scaling 检验"**。<5 cluster 的 cluster-robust 推断是公认不可靠的;真正独立单元是 6 个 model-mean 嵌 2 族。**唯一站得住的是 within-Qwen 4 点(0.365, p=0.01)+ 跨族对齐(描述性)**。而且——**活下来的 CLR 恰恰不区分回退**(held clr=1.00 > reverted 0.895),所以"能力越强 erosion 越重"在统计上其实是"能力越强**链里越爱提旧词**",离"答案被推翻"(RR/es_drop 都不显著)隔了一层。
- **当前强度**:**major→可降 minor**,前提是诚实降级为支撑趋势 + 砍掉 p=0.0007 这个会**反噬**的数(懂 cluster 推断的审稿人一眼看穿 2 族出 p<0.001 = 假精度)。

### Claim D —「生成式 word-boundary 口径 + κ=0.836 验证」(测量脊梁)

- **体检**:**站得住**,且我审前的"丢 33 条抬 κ"的怀疑**被证伪**——workflow 复核:33 条若全记 TN(多为非回退)则 κ **升到 0.853**,故 0.836 是**保守下界**。`metrics.py` 口径(_without_subject 去主体 + <4 字别名丢 + 词边界)干净。唯一残:κ 的绝对值受 rule_rr 分层的人工 prevalence 影响(验的是 rule-vs-judge 一致、非总体信度),且 abstract 里 0.836 裸引未带此 caveat;判官是 Claude 同族。
- **强度**:**minor**(测量端最稳的一块)。

---

## 3. 最弱的单个经验 claim(一句话)

> **「reversion 是重构性的——90% 经命名 bridge、无 flat recall、无 traceless 泄漏」(draft §1 contribution-2 / §5 Table 2 / necessity traceless=0)——因为产出这个分类的判官 prompt(`chain_classify.py:25`)在提问前就告诉判官"a separate probe proves the edit is STILL INSTALLED … the chain is ROUTING AROUND an intact edit, NOT recalling decayed weights"并要求"Make NO claim … the edit weakened",而 Recall(="recalling decayed weights")和 Associative/implicit-leak(="无声先验")正是这套措辞在语义上禁掉的两类 → Recall=0 / Associative=0 至少部分是仪器制造的,不是从链里发现的。**

为什么它最先被攻破:① 这是**自伤**——团队自己的 `depth-plan.md:113/158` 按 file:line 点名要删这三句,却**只删在 `revert_judge.py`(metric-validation 面板)、没删在 `chain_classify.py`(taxonomy 面板)**;② draft.md:73 还**主动宣称** metric-validation 面板"never told the edit's status"——一个面板标榜盲、另一个偷偷被灌结论,这种不对称一旦被审稿人发现,读作 cherry-picked neutrality,杀伤超出单条结果;③ 19 条里只有 1 个个体 Recall 票、32B 零个 Associative 票 = 判官几乎不碰那两类。**指纹清晰、零卡可复核、abstract 相关。**

---

## 4. Solidity 实验计划(按 威胁录用 × 死线可完成 排序)

> 成本按**墙钟 + 工程量**算(算力免费、非约束)。

### 🔴 7/20 前(零/廉价卡 · abstract 关键 · 高威胁 · 全是防御但堵命门)

**S1 ·【最高优先·堵命门】中性 prompt 重跑 taxonomy 判官** — _防御_

- 做:删 `chain_classify.py:25` 那三句结论灌输 + 前置中性 OLD/NEW/NEITHER 门 + 加可用的 Recall/implicit-leak 选项,重跑 ~720 judge calls,重算 Bridge%/Recall/Associative + Fleiss κ。
- 预测:Bridge 仍占多数(其定义本就宽),但会冒出非零 Recall/Associative。
- **证实**:中性下 Bridge≥~70% 且 Recall/Associative 仍≈0 → "重构性、从不无声"被洗白,可放心写。**杀死**:Recall/Associative >~20% → 删掉 contribution-2 的"no flat recall, no traceless leak"和 necessity 的 traceless=0。
- 成本:**零卡**,~30 LOC,**赶 7/20**。

**S2 · logit-lens 加 held 对照 + per-case CI** — _防御 + 诚实_

- 做:`logit_lens.py` 去掉"仅回退"门,**同样探 held(非回退)案例**;报 reverted vs held 的 intact% 和逐层 g_l 的 per-case bootstrap CI(标 n)。
- 预测:held 也 ~100% intact、中层 dip 与 reverted 无差。
- **证实(预期)**:→ 必须把 intact=100% **从"机理证据"降级为"sanity check:编辑在权重里"**,中层 dip 若 CI 跨零或 held 相同则收回"old fact persists [回退特异]"。**杀死**:若 held intact 显著更低 → 反而有了真区分力(意外的好消息)。
- 成本:**~2–4 廉价 GPU-h**,~30 LOC,**7/20 可塞,否则 7/27**。

**S3 · 能力统计诚实降级**(纯分析) — _防御_

- 做:abstract/§4 以 **within-Qwen 4 点 CLR(p=0.01)+ 跨族对齐(描述性)**领衔;**删 K=2 的 p=0.0007**(改报"方向一致、非 scaling law");明说活下来的是 CLR(链泄漏)、答案级 RR/es_drop slope 不显著。
- 成本:零卡,**7/20**。

**S4 · 32B base_probe** — _防御_

- 做:`base_probe.py` 指向 32B 基座(Qwen2.5-32B)跑 base-recall;现在 `results.json base_probe` **只有 7B(0.59)**,而 knowledge-conflict 的"why"在 abstract/§1 是给 **32B** 头牌用的。
- 预测 ~0.5–0.7。**证实**:头牌模型上 base 确实回忆旧事实 → "为什么"有了头牌尺度的锚。
- 成本:**~2 廉价 GPU-h**,~0 LOC,**7/20**。

### 🟠 7/27(全文 · 真正的升级)

**S5 ·【头牌承重·单点最高杠杆】E-CHAINSUB 链替换中介** — _头牌_

- 做:权重冻在单 ROME 编辑,写**新解码路径**:给定一段 think 内容 → 解码答案。三条匹配反事实链:**T0**(原生回退链)/**T-clean**(陈述编辑事实、无 o_old 无 bridge)/**T-old**(经命名 bridge 重推 o_old)。读 P(ans=o_new) vs P(ans=o_old)。n≈30–50 32B(先把回退池加宽,见 S6)。
- 预测:T-clean 把答案拉回 o_new(**必要性**)、T-old 在编辑在位时仍翻旧(**充分性**)。
- **证实**:两者都成立 → **破 RQ2/RQ3 同一 logit 几何循环**,在**答案位**(logit-lens 测错了位)直接证"链驱动答案",RQ2 从恒真/污染升级为真中介。**杀死**:T-clean 仍回退(答案不跟链)→"chain governs answer"塌,全篇退回"抑制有用"。
- 成本:**~80–100 LOC 新解码路径**(`generate_with_budget` 是循环生链、不接"给定 think 再解码",别低估)+ 中等 GPU(只解短答案、不生长链 → 墙钟小)。**约束是工程墙钟、不是卡。赶 7/27 可行,但工程要现在起。** bridge 实体从 S1 去污后的 Bridge-class quoted span 抽。

**S6 · 加宽 32B 回退池 17→100+** — _防御/地基_

- 做:`extract_reverted.py` 放宽 + 多跑 CounterFact;**一次同时硬化** logit-lens(S2)、taxonomy(S1)、necessity、并供 E-CHAINSUB(S5)群体。
- 关键洞:**当前整个机理核心(logit-lens n≈10–17、taxonomy n=19、necessity n=19、RQ3 回退 ~11–23)是同一批 ~20 条 32B 回退 case 看了四遍。** 一个 n=20 的池撑四个"独立"结果,审稿人一眼不信。
- 成本:廉价–中等 GPU,~40 LOC,**7/27**。

**S7 ·(保险,可选)一个 MEMIT 点** — _防御/门票_

- 算力免费下做一个 MEMIT×CounterFact×32B 复现修复/趋势 = 便宜保险。三审一致"广度=门票不加分",所以**不抢主线**,有余力再做。7/27。

---

## 5. 诚实边界(到 7/27 补不上 —— 受死线/工程量限,不是算力)

1. **完全自然(未注入链)生成里的因果必要性**:E-CHAINSUB(S5)用的是**构造链**,证的是"喂干净链则答案回 o_new"。真正"in-the-wild 必要性"要对自然链里的 bridge token 做 activation patching/中介分析——更大的工程(新 hook 路径),**死线内做不完**,写进 limitation(且这是 logit-lens 永远锚不到的那个分母)。
2. **prompted-CoT vs native-R1 的判别控制**:审稿人必问"指令模型 +'think step by step'是否同样 erosion"。`think_budget.py` 模板写死 R1 格式,要新非-R1 解码路径(~60–90 LOC)+ 新 32B-Instruct 加载 + 不可消的 prompt-格式 vs 推理-训练混淆 → **工程+混淆**双限,7/27 前给不出干净答案,只能写 scope。
3. **硬/自然多步推理上的 erosion**:现多跳(S 见 §下)是 easy 模板上的**衰减为噪声**,不是真多步推理 erosion;后者是独立研究。
4. **多跳口径的诚实纠偏**(便宜但必须做的文字):代码显示多跳"erosion"是 new-fact 衰减到 **neither 8/9**(hop_RR=0.021≈0),**不是 o_old 复辟**——与单跳"o_old 复辟 RR=0.144"是**不同事件**。把 draft.md:166/283 的"same within-case signature / replicates the mechanism"软化为"installed edit 的下游传播在思考后也衰减(经衰减、非复辟)";可守的窄断言"非纯单跳 cloze 伪影"成立。这条零卡、7/20 可改。

---

## 6. 单点最高杠杆

**S5(E-CHAINSUB),从 camera-ready 提前到 7/27。**

理由:它是唯一能把这篇从"**有意思的机理叙事 + 充分性修复**"变成"**有中介证据的机理**"的实验。① 它直击所有 review(含本轮)都指向的最深残余——RQ2/RQ3 读同一 logit 几何的**循环** + **自然必要性从未证**——而这是**任何 reframe 和文字软化都消不掉的**;② 它在**答案位**做因果(logit-lens 恰恰测错了位置:裸 cloze、无链),正面补上 RQ2 的空洞;③ 它的结果**不预定**——T-clean 可能拉不回 o_new,即它能**杀死**头牌,这正是好审稿人要的高信息量实验;④ 约束是**~100 LOC 解码路径 + 墙钟**,**不是算力**——以你们 8×H200/H100 全离线、解码只生短答案,卡时可忽略,真瓶颈是现在就得动工的工程。

次优 + 必做的最便宜项是 **S1(中性 prompt 重跑判官)**:零卡、堵的是一个**自伤式可复核污染**,且是 7/20 abstract 关口的命门。**若 7/20 只能做一件 → S1;若问哪一个实验让整篇 solid → S5。**

---

一句话总结给 AC:**这篇有一条代码可证的真东西(RQ3 链级修复),但把它和一条恒真/被污染/无区分力的机理腿(RQ2 非擦除)绑成头牌;要立住头牌,缺的不是更多广度,而是 E-CHAINSUB 这一个把"抑制有用"升级为"链中介答案"的反事实实验,外加把被自家 QA 漏掉的判官 prompt 污染洗掉。**

let me record the two non-obvious cross-file findings for future sessions.

Recalled a memory, saved 2 memories

The review is complete and the key cross-file findings are saved to memory. Summary of what the dig produced beyond the prior two rounds:

**The one sentence an AC rejects on:** the mechanistic headline ("reversion is _not_ erasure but in-chain re-derivation") is carried by three legs that each fail to _discriminate why a chain reverts_ — the logit-lens "intact at cloze 100%" is tautological on static edited weights gated to b0ok (`logit_lens.py:104`), `o_old`-in-chain is anti-discriminative (held 14/14=1.00 vs reverted 17/19=0.895 in `results.json`), and the Bridge/Recall/Associative taxonomy was produced by a judge prompt that _states the conclusion_ (`chain_classify.py:25`) — the exact bias the team's own depth-plan ordered deleted but fixed only on the sibling panel.

**What's actually solid:** RQ3 (the chain-only fix) — code-verified answer-span-untouched (`think_budget.py:87`), signed/specific/dose-controlled — and the κ=0.836 measurement spine (confirmed a _conservative lower bound_). The reframe correctly found the strength (RQ3) but over-promised on the weakness (RQ2).

**Highest leverage:** E-CHAINSUB pulled to 7/27 (constraint is ~100 LOC + wall-clock, not GPU); cheapest must-do for 7/20 is re-running the taxonomy judges with a neutral prompt.

One note: the `codex和claude的第一性review.md` file you pointed me to isn't in the repo — I worked from depth-plan.md §第三轮, which summarizes its conclusions. If you want me to read the original, drop it in and I'll cross-check whether any of its points change my ranking.

This is my scheduled fallback wakeup firing — but the work it was guarding is already done. The verification workflow (`wqclyiq3s`, 14 agents) completed last turn, I parsed all probe/refute outputs, and delivered the full decision-ready review. Nothing is left in flight.

Rather than regenerate the (long) review, here's the at-a-glance result so you don't have to scroll:

**Verdict:** the MECH-led reframe correctly identified the strength (RQ3 chain-only fix — code-verified answer-untouched at `think_budget.py:87`, signed/specific/dose-controlled) but bolted it to the weakest leg (RQ2 "non-erasure").

**Three deep holes, all missed by the prior two rounds, all verified from `src/`:**

1. **Taxonomy judge prompt still contaminated** — `chain_classify.py:25` tells judges _"the edit is STILL INSTALLED… ROUTING AROUND an intact edit, NOT recalling decayed weights"_ — the exact sentences `depth-plan.md:113/158` ordered deleted. Fixed on the sibling κ-panel, not this one. → Bridge=90%/Recall=0/Associative=0 is partly instrument-made. **(major, self-inflicted, zero-GPU fix)**
2. **RQ2 non-erasure is non-discriminative by construction** — fresh-cloze static-weight probe gated to b0ok (`logit_lens.py:104`); held clr=14/14=1.00 ≥ reverted 0.895; whole mechanistic core is the same ~20 32B cases viewed 4 ways. **(major as-framed)**
3. **capability p=0.0007 is from a K=2-family cluster bootstrap** = false precision that backfires; only within-Qwen CLR (p=0.01) defensible — and CLR doesn't discriminate reversion. **(major→minor if demoted)**

**Corrections to my own priors** (the adversarial pass earned its keep): κ=0.836 is a conservative _lower_ bound (drop-test refutes inflation), and RQ3's answer-untouched property is architecturally guaranteed, not just asserted.

**Single highest leverage:** E-CHAINSUB (T0/T-clean/T-old mediation) pulled from camera-ready to 7/27 — ~100 LOC decode path, GPU-cheap; constraint is engineering wall-clock. Cheapest 7/20 must-do: re-run taxonomy judges with a neutral prompt.

Want me to take any of this further — e.g. draft the neutral judge prompt + the S5 (E-CHAINSUB) decode-path spec, or pressure-test whether widening the reverted pool (S6) changes the κ/taxonomy/logit-lens numbers? Otherwise the review stands as delivered.

以上为claude。

**结论**  
按默认拒稿先验，现在这篇最强的是：`scope=think` 的 `o_old` 抑制是一个有效、方向正确、placebo 之上的 training-free 修复。最弱的是：自然回退的机制被证明为“链内重推 / Bridge re-derivation”。这个 claim 目前会被我优先攻击，因为 RQ2 taxonomy/necessity 用的判官 prompt 预设了机制。

**1. 盲猜 vs 实际**  
我的盲猜：ES/RR 的 capability story 会脆；真正有力的只会是“压旧答案 token 有效”；机制因果会卡在同一 `o_old/o_new` logit 几何循环上。

实际读数：

- RQ3 比预期强。T−P 全排零：ES `+0.122 [0.051,0.193]`，RR `-0.095 [-0.171,-0.029]`，RRs `-0.057 [-0.114,-0.010]`，CLR `-0.228 [-0.294,-0.162]`，且 D−N 反向显著恶化。见 [paper/results.json (line 267)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:267)。
- capability 已经从 fatal 降到可守：per-case cluster bootstrap 下 CLR slope `0.372 [0.149,0.800]`，但 ES-drop/RR slope 不显著。见 [paper/results.json (line 619)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:619)。所以它只能是 CLR leakage 趋势，不是 answer-level undoing scaling。
- metric validation 很强：strict RRs vs 中性判官 `κ=0.836`、precision `0.92`；loose RR precision 只有 `0.48`。见 [paper/results.json (line 882)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:882)。
- 机制证据比 prose 弱：logit-lens 块只有 `edit_intact_pct=1.0` 和均值曲线，没有 n、逐 case CI、非回退对照。见 [paper/results.json (line 481)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:481)。
- 新发现的更深洞：RQ2 taxonomy 的判官 prompt 明写 “edit is STILL INSTALLED / ROUTING AROUND an intact edit”，然后让判官 “name the ROUTE”。见 [src/chain_classify.py (line 25)](/Users/whyu/GitProjects/why-aaai27/src/chain_classify.py:25)。这会污染 `17/19 Bridge` 和 `19/19 rederiv_route` 的自然必要性结论。

**2. 承重 Claim 体检**

1. **“Reasoning erodes edits, capability-emergent.”**  
    需要：生成式编辑真实、B0/B3 配对、趋势不靠 scorer/6点 OLS。  
    当前：真实；CLR 趋势稳；ES/RR 不稳。  
    强度：major but not fatal。只能说“CLR leakage 随能力上升，answer-level undoing 在高端出现”。
    
2. **“Edit is intact, not erased.”**  
    需要：回退后 cloze 仍预测 `o_new`，且不是只在小 n/单探针成立。  
    当前：logit-lens 只给 `100%` 和均值曲线；代码确实只挑回退 case，并在 cloze 做 first-token gap。见 [src/logit_lens.py (line 24)](/Users/whyu/GitProjects/why-aaai27/src/logit_lens.py:24)。  
    强度：major。足够反驳“明显擦除”，不够支撑“中层旧事实是回退特异 substrate”。
    
3. **“Natural reversion is in-chain re-derivation.”**  
    需要：中性观察链，不预设路线；最好可反事实替换链。  
    当前：`necessity` 的 `19/19` 直接读 taxonomy 标签，见 [src/necessity_check.py (line 31)](/Users/whyu/GitProjects/why-aaai27/src/necessity_check.py:31)，而 taxonomy prompt 带机制假设。  
    强度：fatal/major，取决于正文强度。若头牌是机制，这会威胁录用。
    
4. **“Chain-only suppression is causal and useful.”**  
    需要：答案段未直接压、placebo、方向、剂量、locality。  
    当前：强。实现里 `scope=think` 只在链生成用 processor，答案段只有 `scope=all` 才压。见 [src/think_budget.py (line 76)](/Users/whyu/GitProjects/why-aaai27/src/think_budget.py:76) 和 [src/suppress.py (line 15)](/Users/whyu/GitProjects/why-aaai27/src/suppress.py:15)。  
    强度：solid for fix/sufficiency。它证明“链内压 `o_old` 会改善答案”，但不证明自然链文本是必要中介。
    

**3. 最弱的单个经验 Claim**  
“自然 committed 回退 `19/19` 都经可观察链内重推，且 `Associative=0`。”  
原因：这个数字来自非中性 taxonomy prompt；prompt 已把“routing around an intact edit”写进题干。审稿人一句话即可打穿：你不是发现 route，你让判官在 route 假设下选 route。

**4. Solidity 实验计划**

1. **E-CHAINSUB with neutral span selection**  
    实验：对 32B ROME/CF 回退 case，固定编辑权重，给定三类 think 段后只解码 answer：T0 原链、T-clean 陈述 edited fact 且无 `o_old/bridge`、T-old 经中性抽取的 bridge 推到 `o_old`。  
    预测：T-clean 显著拉回 `o_new`；T-old 在编辑仍 intact 时诱导 `o_old`；T0 replay 复现。  
    杀死：三链答案无差异，或 T-clean 仍旧、T-old 不能诱导旧。那 RQ3 是 token gate 修复，不是链中介机制。  
    成本：新解码路径 80–120 LOC；H200 fp32 4–8h for n=30–50；工程 1–2 天。赶 7/27；若压缩 n=19，可赶 7/20 后补。头牌承重。
    
2. **中性重跑 RQ2 taxonomy/necessity**  
    实验：仿 [src/revert_judge.py (line 20)](/Users/whyu/GitProjects/why-aaai27/src/revert_judge.py:20) 的中性风格，先问 OLD/NEW/NEITHER，再让判官在不提 “routing around/intact edit” 的 prompt 下抽取支持 final answer 的 span。  
    预测：Bridge/RO 仍 ≥70%，Associative/Recall 低，held 排除稳定。  
    杀死：Recall/Associative 大幅上升，或 committed population 大幅变化。  
    成本：零 GPU；50–80 LOC prompt/schema 改造 + judge workflow 半天。赶 7/20。头牌承重的前置防御。
    
3. **Logit-lens 加固：非回退对照 + CI**  
    实验：重跑并保存 raw jsonl；n≥40 reverted，匹配 non-reverted B0-success/held controls；画每层 gap 的 bootstrap CI。  
    预测：top-layer `o_new` intact 高比例；若要解释“why these revert”，中层 negative dip 应在 reverted 更强。  
    杀死：top-layer intact 不是高比例；或中层 dip 在 non-reverted 同样存在，则只能保“非擦除”，不能保“中层 substrate explains reversion”。  
    成本：2–4 H200h；30–50 LOC plot/aggregate。赶 7/27。防御但重要。
    
4. **Base-recall × reversion / edit-strength confound**  
    实验：对主矩阵每 case 跑 unedited base recall、edited B0 margin/rewrite margin，进 per-case regression：RR/CLR ~ scale + base_recall + edit_margin + chain_len。  
    预测：base_recall 正相关，但 scale/CLR slope 仍留显著残差。  
    杀死：base_recall/edit weakness 吃掉 capability slope。那“capability”应降为“stronger prior conflict”。  
    成本：6–10 H200h；60 LOC 合表。赶 7/27。防御。
    
5. **等长 non-reasoning filler 控制**  
    实验：B3 同长度但填无关链/模板 filler/另一 case chain，再 answer；与真实 CoT 比 ES/RR/CLR。  
    预测：真实 CoT > filler erosion。  
    杀死：filler 同样侵蚀，则不是 reasoning re-derivation，而是长上下文/解码漂移。  
    成本：新 budget path 80 LOC；8–12 H200h。赶 7/27。头牌防御。
    
6. **RQ3 第二 operating point**  
    实验：14B 或 Llama-70B 上跑 N/T/P，优先不做全广度，只复核 sign/placebo。  
    预测：T−P 同向，RR/ES 改善，Loc 平。  
    杀死：只有 32B/CF 成立，则 fix 是单点现象。  
    成本：已有 harness，6–12 H200h；低工程。7/27 防御。
    

**5. 诚实边界**  
到 7/27 仍补不上的不是算力，是工程/识别范围：多编辑器×多数据集完整外推、native R1 vs prompted-CoT sibling 的系统比较、真实部署 router false-positive 风险、以及多跳多模板多尺度机制。它们应作为 scope limitation。真正应该尽力补上的不是这些广度项，而是 E-CHAINSUB 和中性 taxonomy。

**6. 单点最高杠杆**  
如果只能做一个：**E-CHAINSUB with neutral span selection**。  
它同时回答最致命的问题：答案到底跟随链内容，还是只是 `o_old` token gate 改了分布？成功则机制头牌真正站住；失败则论文应退回“有效 chain-local decoding fix + measurement correction”，机制 claim 不能再承重。

以上为codex。