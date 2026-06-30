# depth-plan.md · 提分作战(深度/效度,非广度)

**来源**：三审(Claude/Codex/DeepSeek)收敛弱点 → 10-agent 设计 panel(workflow `w536ljvnv`,2026-06-28)定稿。
**核心 recalibration**：**没有审稿人把广度(多编辑器/数据集/尺度)当 blocker** → 广度=门票,不加分。**提分全在深度/效度:因果对照、鲁棒、多跳。**
**统一汇报约定**：**effect-above-control** —— 每个指标都报"相对对照臂的差(带配对 CI)",任何 null 都变成一个量化 margin、而不是被迫收回的断言。

---

## 第二轮深度计划 (v2, 2026-06-30) —— W1/W2/W3 完成后的全文 re-review 重排【当前权威】

**DECISIVE tier 三件全 DONE**:W1 E-SUP-BATTERY(prereg 全中,T−P 特异)✅ / W2 E-SEMJUDGE(κ=0.836)✅ / W3 E-MULTIHOP(propagation-erosion 0.188 排零,与单跳同结构复现)✅。下方"DECISIVE/HIGH/INSURANCE tier"是**第一轮**记录(DECISIVE 已全清),本节取代其优先级。

**新 re-review(workflow `wa6rxz0qp`,3 审 borderline/borderline/weak-accept,raw 见 `rereview-round2.md`)的关键纠正**:
- **最大残余被重定**。不是预命名的"自然生成必要性"(那个**零卡可堵**),而是 **title 名词「capability-emergent」的统计骨架**(唯一 fatal,2 审):6 点 OLS 的 p<0.002 来自 point-resample 同 6 点 → fix(per-case 混合效应 + family 随机效应)**零卡、在盘数据上、abstract 关键**,原计划却错放进 7/27 GPU 窗后。
- **abstract 关键集 ≫ 我原来的 A1-A3**:漏掉 1 fatal + 3 major-threatens 的 fix,**全部零卡**。

### TIER A —— 零卡 / abstract 关键(7/20 前必落;数据在盘上,写分析码 → 平台跑或本地跑)
> 执行=我写码列改了哪些文件(不给 base64),用户上传/平台跑;纯文字 fix 我直接改 draft。
> **进度(6/30,ultracode 流水线 `wyd1uyje4`)**:✅ #1 代码就位(`percase_emergence.py`,自测 9/9,数字待平台跑) ✅ #5/#6/#9 draft 整合(全 approved 无过度让步) | 待跑:#2 必要性观察检验、#3 CLR robustness、#4 70B 敏感行(需平台 per-case 数据) | 待我本地:#7 TOST、#8 LaTeX+plots。

1. **【最高·拆 fatal】E-DECONFOUND-NOW(零卡半)**:`emergence_regression.py` 升级——**per-CASE pooled 回归**(每行=一 edit-case×尺度,ES降幅/RR/CLR ~ log10(params) + `chain_len` 协变量 + **family 随机效应**,mixed-effects/GEE,**非**现 6 点 fixed-dummy `family_controlled`);报 log-params 固定效应 slope+CI 作**承重 emergence 统计**,把 6 点 OLS+point-bootstrap **降级为描述性图**。另报 **within-Qwen-only CLR slope 带 CI**(`results.json` 现 0.2611 / ci:null,n=4 fit 须补)。→ 直接灭唯一 fatal(stats+novelty 都 threatens、撑 title 名词)。**需 per-case jsonl(在平台/GPFS)**。
2. **【最高·堵命名残余】自然生成 NECESSITY 观察检验(零卡)**:在未干预 B3 链(gated 回退池)上,报 **P(回退 | 链含逐字 Bridge 重推子句) vs 无**(用 RQ2 判官已抽的 **17/19 Bridge span**),前景化 **Associative/implicit-leak=0/19**。然后把 draft 每处"the chain re-derives it / reasoning routes around it" **软化**为"in-chain re-derivation 出现在 N/19 自然回退中,且抑制它翻转答案"。→ mechanism #1 + novelty #3,两审同开此方;把"充分性(可 steer)"推向"自然文本里观察到 + 抑制翻转",最高杠杆缺失项。
3. **【堵承重指标】CLR scorer-robustness 表(零卡重打)**:CLR 及其 6 点 slope 在 alias cutoff **3/4/5** + 有/无 alias list、**per-scale** 重算;证 (a) 单调上升对所有 cutoff 成立、(b) ~2× 灌水因子近似 scale-invariant(去污不差异化缩小小模型 CLR);**明说 <4 字 cutoff 是否预注册**。→ CLR 是唯一单族存活指标(`lopo_all_exclude_zero` 仅 CLR true),未预注册 cutoff 是直击;W2 κ 验的是 reversion 非此 scorer。
4. **【护 2/6 framing】Llama-70B 敏感行进 Table 1(零卡重制表)**:ES降幅+RR **with/without 丢 13** 配对入表(现仅 §setup prose)+ **最坏行**(13 全记编辑失败的 floor)。最坏 70B CI 仍排零→保"双显著点";否则降级"1 显著点 + 70B 方向复现"。
5. **【免费文字 fix 打包】**(直接改 draft):(a) §3 Statistics 加 **confirmatory(RQ3 N/T/D/P 预注册)vs exploratory(RQ1 cells 描述性)** 一句 + 可选 Holm 校正 6 个 ES降幅 CI;(b) 软化"Reflective-override is itself capability-emergent"→"仅 32B 出现(2/10),consistent with 但不 establish";(c) 软化 §5"isolated o_old-specificity"→"specific to a meaningful competing target relative to an inert placebo floor";(d) 审 abstract/intro 无多跳泛化措辞、明标 W3 = single-template pilot。
6. **A1 W4 scope 段(零卡)**:claim 范围限 native-R1 推理器、点名 instruct+CoT 为审稿人会查的那个 future-work 控制;同段**收紧 title/scope 向"locate-then-edit on CounterFact"** + 点名单编辑器 MEMIT 复现为 future work。→ 同时预堵 W4(novelty minor)+ 单编辑器/数据集(stats+novelty major,缓解非闭)。
7. **A2 部署门 equivalence/CI 边界**:把"passes"换成 **Δacc 的 95% CI + TOST 最小可测退化**;**仅当**要把等价界压到 <0.02 才在 4090 bf16 廉价扩 GSM8K/MATH 的 n(离 H200 关键路径)。
8. **A3 draft→LaTeX 主工程 + `plots.py` 出图**:fig1 capability 曲线、**fig2 logit-lens gap 带 per-case bootstrap CI 带**(中层 dip 不能点估断言)、fig3 单跳 ES降幅 vs 多跳 propagation-erosion 配对。
9. **RQ2/RQ3 非独立性 name-and-bound 段(零卡)**:§4/§6 显式命名并 bound"edit-intact 与 fix-works 可能同一 logit 几何读两遍"的循环(现仅处理了更窄的 ΔCLR 同义反复)→ B2 的 H200 窗若滑过 7/27 的滑窗保险。

### TIER B —— 需 GPU 窗 / 全文 7/27(非 abstract)
- **B1**:reverted 池 17→40+ 重跑 logit-lens 出"≥40 中 100% intact" + **零卡 per-case g_l 分布 + 每层 bootstrap CI**(标 n);中层 dip CI 跨零→降级"margin not established mid-stack, consolidates late"。~2-4 H200-h,搭 B3 base_recall 同一 model-load 窗。
- **B2**:E-CHAINSUB 链替换中介(T0/T-clean/T-old;必要性=T-clean 拉回 o_new、充分性=T-old 编辑在位仍回退)。N~17-30 32B case study,明标。~3-5 H200-h + 80-100 LOC 新解码路径。破 RQ2/RQ3 循环;camera-ready,有 A-9 段做 fallback。
- **B3**:E-DECONFOUND GPU 半 —— 未编辑基座重生 `base_recall` 协变量(~8 GPU-h)加进 action-1 已零卡跑出的 per-case 回归;证 capability slope 在 chain_len+base_recall 双控下存活。搭 B1 同窗、不加关键路径。

### DROP(本轮明确不做 —— 审稿人无人当 hard blocker)
MEMIT/AlphaEdit/zsRE/更多尺度/更多 seed 充量;全套 W4 same-base instruct;W1 sibling 干扰臂 D′;tuned-lens/activation-patching 旁证;8B 多跳模板扩充(廉价但不值抢窗 vs B1/B2)。

### 诚实残余风险(v2 更新)
1. **(降级)自然生成必要性** —— 原列"无实验可消",re-review 指出 **action-2 零卡观察检验**可把它从"未证"推到"自然文本中 N/19 present 且抑制翻转";仍非随机干预的因果必要性(那需 B2 充分性 + 观察必要性合证),但不再是裸残余。
2. **多跳是模板 MQuAKE、单模板 P27 扛** —— 明标 single-template pilot;立"非单跳 cloze 伪影",不立硬多步推理 erosion。
3. **机理单方法 logit-lens** —— B1 加 per-case CI 后中层 claim 有界;tuned-lens/patching 旁证 DROP(成本不值)。
4. **净**:三审 borderline/borderline/weak-accept;**全部 threatens_acceptance 项的 fix 几乎都零卡**(fatal 统计骨架、必要性、CLR scorer、70B 敏感行)→ 7/20 前零卡冲刺可把 borderline 抬向 accept;GPU 窗(B1/B2/B3)是全文加固非 abstract 阻塞。

## 三审收敛弱点(优先级)
- **W1(≥2 审,最高)** 因果只靠 logit-lens;"in-chain re-derivation 驱动回退"有干预**缺对照臂**。
- **W2(≥2 审,最高)** 干预依赖已知 o_old / 疑似刷榜;别名/多 token/改述/间接表达鲁棒性未证;部署门要写到扎实。
- **W3(≥2 审)** 单跳;要多跳(负结果也有价值)。
- **W4(1 审,次)** 只 R1-distilled;对指令/非 CoT 模型意义?

## DECISIVE tier(真正提分的 3 件,进 7/20 abstract)

### E-SUP-BATTERY(W1 因果对照)—— 单点最高杠杆
- **设计**：headline 32B/CF,scope=think(efficacy-only 门 `edit_loop.py:150` 保 Loc 结构安全),|α|=8,按 case_id 配对。四臂:
  - **D=压 o_new(方向臂,决定性,先跑 n=100)**——若压 o_new 反而**降**回退=符号错=近乎致命 → 故 day-1 先验它。
  - N=不压 + T=压 o_old(现有 fix);**先核 N/T 在盘上是同一 case_id 集 + 同 decode**,否则重跑便宜臂。
  - **P=placebo(频率+长度匹配的无关 token,看 RR 前 BLIND 锁定)**。
  - 报**符号阶梯 D<N~P<T**(ES@B3/ES降幅/RR/CLR)+ **跨臂配对差 bootstrap(~50 LOC,新 headline 统计;`metrics` 内的只做组内不做组间)**。methods 里**预注册 D<N~P<T**;报 **o_old 相对 placebo 的 margin(T−P 配对 CI)**,不报 o_old-vs-零。
- **成本**：~12–18 H200-h(D+P+可选 sibling;N/T 盘上有、需版本核对)。+~30 LOC suppress.source 分支(o_old|o_new|placebo|sibling 走 yaml key)+~50 LOC 跨臂 bootstrap +~30 LOC 离线 BLIND placebo 供体构建器(零卡)。2–3 个克隆 yaml。无新模型加载、无 mom2。
- **null 风险(不对称)**：D 安全+诊断(符号错=致命,故先跑)。**P 是危险臂**:非零 placebo(压任意高频词也升 ES)= "fix 是通用扰动非 o_old 特异" = 自伤 W1。**预案**:placebo 当"链扰动 FLOOR"报,o_old 报其上 margin → 把吓人的 null 变成一个特异性数字。
- **第一步(零卡)**:写 BLIND placebo 供体构建器 + 跨臂配对 bootstrap joiner + suppress.source yaml 分支;**书面预注册 D<N~P<T + effect-above-placebo**。然后 H200-A day-1 跑 D@n=100。

### E-SEMJUDGE(W2 反刷榜,零卡)—— 硬门控:先重写判官 prompt
- **设计**：复用 3-Claude `chain_classify` Fleiss 面板,分层 ~120 链样本(32B B3 efficacy + 修复后)。**前置(非附加)**:重写 `chain_classify.py:25` 的 `JUDGE_PROMPT_TEMPLATE` —— **删掉断言"edit STILL INSTALLED / routing around intact edit / make NO claim edit weakened"那几句**(现行 prompt 是为 taxonomy 写的、会把回退验证判官**带偏成"验证样"垃圾**);**前置中性门**("最终答案 commit OLD/NEW/NEITHER?")+ `truly_reverts` 布尔,放路由问题之前;重跑 `test_chain_classify` mocks(Excluded-held 变主门)。报 rule-vs-judge κ + 2×2 混淆 + 假阳/假阴;若判官认为规则 RR 灌水,则在判官验证子集上重报 headline RR。
- **成本**：**零卡**。~720 judge calls(链在盘上)。~80 LOC(prompt 重写 + 中性门 + 分层采样 + Cohen-κ/混淆报告;`fleiss_kappa` 已有)。
- **null 风险**：**只在 prompt 修好后才 null-safe**。两残:(1) κ<0.5 = 指控自家构念 → 不论值都当一等结果报(camera-ready 前暴露是好事);(2) **κ 数字别排进 7/20 abstract** —— abstract 写条件句("我们用留出语义判官面板验证回退指标"),κ≥0.7 才填数,低 κ 走全文当构念信度讨论。
- **第一步(零卡)**:重写 prompt + 扩 schema + 重跑 mocks + stub 干跑 aggregate → 再发 ~720 calls。

### E-MULTIHOP(W3,从 rank4 升进 abstract 三件套)—— 硬门控:先跑未编辑 base-floor
- **设计**：先 curate:1093 单改写 MQuAKE-CF → **426 真干净 2-hop**(盘上已验:hop_answer_new≠o_new 且 subject 字面在 hops[0]);**丢 375 退化**(2-hop 答案就是被编辑宾语);报筛选准则。**再硬门控贵的 32B 编辑 pass**:先在干净池跑**未编辑 base-model 2-hop floor(~5h,无编辑/无 mom2)**,丢基座靠先验就答对的(Trump×152/华盛顿×141 尾,已验)。只在剩余残池:ROME 编单事实,B0+B3 同时生成 cloze(现路径)+ probe=hops[0](2-hop,**绝不点名 o_old**);按 case 配对 2-hop 答案的 ES降幅(对 hop_answer_new/old 判,659 单 token)。**跨族**:Llama-8B(4090 bf16)**先做=W3 最小可行答案**,32B(H200 fp32)仅当 8B 显示 case 内"单跳 vs 2-hop"差。预注册三结局(更多/相同/无 erosion)+ 解读;**预框"2-hop 更重"会暗削 chain-only fix → future work**。
- **成本**：~20–24 GPU-h(若 32B 跑;Llama-8B ~6 4090-h 单做=MVP)。+~120 LOC:(a) 2-hop probe 从 `edit_loop.probes()` 经 hops[0] 出(不同渲染、不点 o_old);(b) 新 hop-scorer 对 hop_answer_new/old(`score_pilot` 写死 o_new/o_old);(c) ~40 LOC curation+base-floor 筛;(d) answer_cap 升 512。
- **null 风险**：**不筛就跑=主动有害/无信息** —— 先验主导的原池上 null = "ROME 不传播到多跳"(已知、无聊),非"回退是 cloze 局部的"。base-floor+退化筛是**唯一**让 null 成为有信息边界的东西,**不可省、必须门控 32B 花费**(day-1 用 5 GPU-h 学到混淆,别在 14–18h 编辑 pass 后才发现)。
- **第一步(零卡)**:写 curation 筛 + 并行 hop-scorer(无需 GPU、给整件去风险)。

## HIGH tier(进全文 7/27,非 abstract)
- **E-DECONFOUND(能力去混淆)**:两个回归都报 —— (1) 现有 6 点 cell-mean log-params slope;(2) **新 per-CASE pooled 回归**(每行=一个 edit-case×尺度,数百行)带 **chain_len + base_recall 协变量**(6 点 cell-mean 加 2 协变量会把 df 从 4 压到 2、CI 爆=按构造失效,故必须 per-case)。+ 近零 LOC 稳健行:**leave-one-family-out**(去 Llama,Qwen-only slope 还排零?`per_family_slope` 已有)+ **leave-one-point-out**(去 70B/32B,p<0.002 还活?)。能力断言只在 per-case 偏斜率仍显著正 **且** 影响删除后存活才成立。成本 ~8 GPU-h(未编辑 base_probe,搭 E-MULTIHOP 的 32B base-floor 窗,同一模型加载、无编辑)。+~60–80 LOC。
- **E-CHAINSUB(链替换中介)**:权重冻在单 ROME 编辑;新模板化 think-段解码路径,在 T0(原生回退链)/T-clean(陈述编辑事实、无 o_old/bridge)/T-old(经命名 bridge 推 o_old)下贪心解码答案,读 P(ans=o_new) vs P(ans=o_old)。**破"RQ2 edit-intact 与 RQ3 fix-works 是同一 logit 事实的两读"的循环**。**降级为 camera-ready-only、明标 N~17–30 32B case study**(不掺 14B/7B)。bridge 实体不在 schema → 从 E-SEMJUDGE 产的 Bridge-class quoted_span 确定性抽,抽不出干净 bridge 的 case 排除(报排除数),不手搓。预注册:必要性=T-clean 把答案拉回 o_new;充分性=T-old 在编辑在位时仍回退。成本 ~3–5 H200-h + **~80–100 LOC 真·新解码路径**(`generate_with_budget` 是循环生成链、不接"给定 think 段再解码",别低估)。
- **加宽回退池(RQ2 分母)**:`extract_reverted.py` 放宽到"B3 偏 o_old"把 32B 回退 case 从 17→≥40–50,重跑 logit_lens → "100% of 17"→"100% of ≥40"。顺带供 E-CHAINSUB 群体(免跨模型池化)。~2–4 H200-h。

## INSURANCE tier(零/廉价卡,abstract 润色)
- **部署门 POWER/等价边界(W2 后半,零/廉价卡,进 abstract)**:Δ+0.005/0.000 是**欠功效 null**,审稿人一句"n 太小测不出伤害"就杀。改成 **Δacc 的等价/CI 边界**;现 n 框不紧就扩未编辑 GSM8K/MATH 样本(4090 bf16 便宜)到边界有意义。"无退化"必须是有界断言、非点估。
- **W4 scope 段(零卡,进 abstract)**:**绝不宣称未测的 native-R1 排他性**。写"现象在 native-R1 推理器上证实,指令+CoT 模型为 open future work"。零成本预堵整个 W4(审稿人跑 Qwen2.5-32B-Instruct+CoT 看到同样 erosion)。
- 一个 MEMIT(或第二尺度)复制中介结果 —— **仅当审稿人质疑 ROME 过泛化**才建;7/20 前主动花 H200 严格被深度项支配。
- 序列级 NoBadWords(o_old+别名+改述)—— 仅当顶项做完还有余;改述库有限/英文模板、永远不全闭"间接表达",而 E-SEMJUDGE 已立"指标非子串伪影"(更根本反驳)。

## DROP(明确不做)
- **E3 activation patching / causal tracing**(全套最重工程 ~80–120 LOC + 10–15 GPU-h)—— E-SUP-directional + E-CHAINSUB 已以低得多成本给内容级因果;简版 cloze knock-out 留作 reviewer-response 备用。
- 独立 sufficiency 注入臂 —— 被 E-CHAINSUB 的 T-old 臂以更干净对照结构吸收。
- **全部 W4 same-base 对照实验** —— 单审最低优先 + 需新非 R1 生成路径(~60–90 LOC,think_budget 写死 R1 模板)+ 新 32B-Instruct 加载 + 不可避的 prompt-format-vs-reasoning-training 混淆。用零成本 W4 scope 段替代。W1/W2/W3 早完再议。
- **全部 breadth-for-volume(MEMIT/AlphaEdit/zsRE/更多尺度/更多 seed)** —— 审稿一致 recalibration。
- 用 14B/7B 链填 E-CHAINSUB 的 N —— 混不同模型进 32B 断言(混淆非修);要么源头加宽 32B 池、要么明标 N~17–30 case study。
- κ 数字排进 7/20 abstract 当承诺值 —— 解耦 abstract 死线与可能指控自家指标的结果。

## 排程(2×H200 + 4090 + 零卡道,7/20 abstract / 7/27 全文)
- **零卡道(立即起,永不抢 Hopper)**:(a) E-SEMJUDGE 重写判官 prompt→重跑 mocks→发 720 calls;(b) E-SUP-BATTERY 三离线件 + 预注册;(c) E-MULTIHOP curation 筛 + hop-scorer;(d) E-DECONFOUND 在**已有 3 尺度**上先拟 per-case 协变量回归 + leave-one-family-out → **day-2 就知 RQ1 slope 在 chain_len/base_recall 控制下活不活,不花一个 32B GPU-h**。
- **H200-A**:E-SUP-BATTERY,**D=o_new 先跑 n=100**(符号错 day-1 知),再 P+可选 sibling。~12–18 GPU-h。
- **H200-B**:E-MULTIHOP **未编辑 base-floor 先跑**(门 + 丢先验尾),**同时产 E-DECONFOUND 的 32B base-recall 行**(搭便车)。只残池上编辑 32B pass。
- **4090(离 H200 路径)**:E-MULTIHOP Llama-8B(W3 MVP)+ 14B 未编辑 base_probe(E-DECONFOUND)。
- **关键修正**:**别让 E-DECONFOUND 的 32B 行成为 E-MULTIHOP 的阻塞依赖** —— base-floor 当独立 job 先跑、E-DECONFOUND 搭其输出,一个排队滑坡不会同时杀掉 W3 头条和 RQ1 去混淆。
- **唯一真 H200 关键路径对** = E-SUP-BATTERY + E-MULTIHOP 在两实例无相互依赖。

## 诚实残余风险(全做完仍在)
1. **必要性 vs 充分性**:E-SUP 证 fix 是 o_old 特异+符号正,E-CHAINSUB 证注入下可操控 —— 但都**不证 route-around 在自然(未干预)生成里是必要的**;logit-lens 仍锚 RQ2 "edit intact"分母(加宽后 n≥40 但仍单方法单前向探针)。死硬审稿人仍可说"你扰了解码器和链、从没在 wild 里观察到机理"。
2. **多跳是模板 MQuAKE、先验主导宾语**:筛掉退化+尾后,推理面仍温和合成 → 干净 W3 结果把现象**界定到 easy 2-hop 的 cloze-邻近**,不立硬/自然多步推理上的 erosion。
3. **placebo 是真硬币**:非零 placebo 逼诚实重框("o_old 特异" → "o_old-targeting 超链扰动 floor X")—— 可辩护且预注册,但严格弱于干净特异故事;**day-1 才知在哪个世界**。
- **净**:把 paper 从"一个 work 的旋钮 + n=17 单透镜机理"→"符号/剂量/方向受控的 fix + 判官验证的指标 + 客观下游 W3 结果 + 混淆受控的 RQ1" = **accept 级深度档**;但**不闭"自然生成里的必要性"** —— 这是本 harness 在 7/27 前没有可行实验能完全消的唯一残余。

## 前三步(全零卡、现在可起)
1. **重写 `src/chain_classify.py:25` 判官 prompt**(删 3 句带偏断言 + 加中性 OLD/NEW/NEITHER 门 + truly_reverts,扩 schema,重跑 mocks)—— E-SEMJUDGE 硬前置,不修就发 720 calls = 验证样垃圾。
2. **写 E-SUP-BATTERY 三离线件**(BLIND placebo 供体构建器 + 跨臂配对 bootstrap joiner + suppress.source yaml 分支)+ 书面预注册 D<N~P<T / effect-above-placebo。
3. **写 E-MULTIHOP curation 筛 + hop-scorer**,并**在已有 3 尺度跑 E-DECONFOUND per-case 协变量 + leave-one-family-out 预拟** → day-2 知 RQ1 slope 活不活。
