# depth-plan.md · 提分作战(深度/效度,非广度)

**来源**：三审(Claude/Codex/DeepSeek)收敛弱点 → 10-agent 设计 panel(workflow `w536ljvnv`,2026-06-28)定稿。
**核心 recalibration**：**没有审稿人把广度(多编辑器/数据集/尺度)当 blocker** → 广度=门票,不加分。**提分全在深度/效度:因果对照、鲁棒、多跳。**
**统一汇报约定**：**effect-above-control** —— 每个指标都报"相对对照臂的差(带配对 CI)",任何 null 都变成一个量化 margin、而不是被迫收回的断言。

---

## 第三轮 (v3, 2026-06-30) —— 第一性 review → 战略 reframe 设计锦标赛【当前权威·框架=MECH-led 已定】

> **进度(6/30)**:✅ **框架分叉已拍板 = MECH-led 混合**;✅ abstract/intro/contributions 全文 reframe 落地(自写 14 处 + 3 镜对抗验证 approved,plan v1.45)。**待**:percase_emergence 平台出数(灭 fatal)、RRs 进 Table 1、(全文级)§3/§4/§5 节序重排、fig floats、abstract trim 到 150 词。

**触发**:用户做完第一性 review(Codex + Claude,`codex和claude的第一性review.md`),两份独立收敛同一结论:**头牌选错了**。建议序 **机理/修复 > 评测效度 > capability-emergence**,草稿正好反过来。两条最尖锐共识:(i) **CLR 是唯一铁结果**(LOO+within-Qwen 都活,pooled slope 0.218 [0.121,0.315] R²0.91),却被当防御 fallback;title 承诺答案级 *undoing*(ES/RR,脆)→ **title 与铁证据错位=核心结构弱点**;(ii) 漏掉最高价值重构 = 把 x 轴从"想多少"改成 **knowledge-conflict / 竞争先验强度**(base-recall 0.59 只被防御性引用,从没正面 reframe)。

**设计锦标赛(workflow `wzn1zgi5g`,8 agent;⚠ novelty/priority 查重 agent 挂了=KC priority 风险未独立核,见下)**:4 套完整 reframe → 评委打分 + 尸检。**评委排序 MECH > EVAL > KC > MIN**(KC nov5/def2/dl2、MECH nov4/def5/dl5)。尸检:**KC 在 base-recall 回 null 时不存活**(它唯一承重确认实验),MECH/EVAL 两种 null 都活。

### ★ 推荐框架:MECH-led 混合(待用户拍板)
**头牌=机理/修复**(signed/specific/dose-controlled 链内因果干预 + logit-lens 非擦除 + training-free 修复)——**abstract 承重 claim 全站在 results.json 已跑数据上、零未跑依赖、GPU 滑窗杀不掉**。三件混合:
- **EVAL 的判官验证生成式+word-boundary 口径**做测量脊梁(κ=0.836、[RRs,RR] bracket、~2× 灌水校正),零成本硬化每个回退数。
- **capability-emergence 降为推论**("更强推理器更会检索被埋的先验"),由 **CLR**(唯一铁指标)扛 + per-case 回归(已建 `percase_emergence.py`,待跑)灭 n=6 OLS fatal。
- **KC(knowledge-conflict)留 Discussion 解释层 + 门控**:base-recall 0.59/0.67/0.755 作"为什么",**仅当 base-recall×回退 cross-tab 在 7/27 跑强才升头牌**。
- **拒 KC-as-headline**:依赖未跑实验,且**被两条在手事实反驳** —— taxonomy **Recall=0/19**(纯先验记忆该有 flat recall,实测全 Bridge=重构)+ 多跳侵蚀去向 **'neither' 8/9 非 o_old**(先验重主张该回 o_old)。**拒 MIN**:把最易攻击的 capability 头牌留在 marquee,正是两审点的错位。

**推荐头牌句**:On native R1-Distill reasoners, test-time reasoning reverts a successful edit not by erasing it (intact at cloze 100%,o_old 仍在中层 g8=−0.246/g12=−0.351) but by re-deriving the suppressed fact in the chain — and a signed/specific/dose-controlled chain-only suppression (answer span provably untouched) removes the thinking tax (ES@B3 0.495→0.631, RR 0.193→0.085) above an inert placebo floor (T−P 四指标排零) without hurting locality (0.958→0.964) or general ability。

### NO-REGRET fixes(fork-independent,现在/本周做)
1. **跑 `percase_emergence.py` → `results/percase_emergence.json`**(需平台 per-case jsonl;灭 n=6 OLS fatal + 出 within-Qwen CLR slope CI)——最高杠杆,无论选哪个 fork 都要,**本周做**。
2. **软化 abstract/intro 四处 over-claim**(纯文字):"systematically eroded"→限域;"driver/isolates"→"consistent with capability";"continuous B0–B4 axis"→"zero-vs-long B0/B3 contrast"(B1/B2 跑前去掉 continuous);"causally confirms chain-internal re-derivation"→"signed, specific intervention on a causal competitor above an inert placebo floor";"rules out erasure"→"not erased at cloze (n-bounded)";"reports the trend backwards"→"misses the high-end thinking tax"。(我前轮 #5 只软化了 §3/§4/§5,**abstract/intro 仍未软化**。)
3. **算术/标号对账**(纯文字):Table 1 旗舰格 0.595−0.495=0.100≠0.106 → 加注"ES降幅按 per-case 配对均值、非 rounded marginal 之差";line 159 within-Qwen CLR slope **0.22→0.261**(0.22 是 pooled,误植;真 within-Qwen=drop-Llama LOFO 0.261 [0.118,0.404])。
4. **RRs 进 Table 1**(需平台 per-case 重算 per-model RRs;κ=0.836 已验却没用在旗舰表)。
5. **§7 把 RQ2/RQ3 非独立性命名为有界 limitation**(前轮 #9 已加 §6 段→确保 abstract/body/§7 一致、明标 E-CHAINSUB 为 camera-ready)。

### REFRAME-DEPENDENT(仅当用户选 KC-as-headline + cross-tab 跑强)
abstract 重构成 KC 弧(base-recall 升 x 轴、capability 降 amplifier);base-recall×回退从 7/27 升级为 7/20 承重;title 改 knowledge-conflict;若等长 filler 控制显示非推理 filler 同样侵蚀→"reasoning"→"added inference context"。

### 实验计划(按 杠杆×成本×死线)
| 实验 | 角色 | 成本 | 死线 | 服务 claim |
|---|---|---|---|---|
| per-case 回归跑(`percase_emergence.py`) | 防御 | 零卡(平台数据) | 7/20 | 灭 n=6 fatal、capability 推论诚实 |
| RRs 进 Table 1 + CLR scorer-robustness(cutoff 3/4/5 per-scale) | 防御 | 零卡(平台数据) | 7/20 | 用已验指标、证 CLR 单调不靠 cutoff DOF |
| 自然生成 necessity 观察检验(17/19 Bridge span) | 防御 | 零卡 | 7/20 | 把"链内重推驱动回退"推向 in-the-wild,软化循环 |
| logit-lens **非回退对照** + per-case CI(池 17→40) | 防御 | 廉价 GPU ~2-4h | 7/27 | 中层 dip 是否回退特异(否则解释不了 WHICH 回退)+ 给 100% 加 n/CI |
| dose B1/B2 + **等长 filler 对照**(32B) | 防御 | 廉价 GPU | 7/27 | 诚实说"dose 单调"+ 分离推理内容 vs 上下文长度 |
| **base-recall×回退 cross-tab** | KC 头牌承重/MECH 升级门 | 廉价 GPU ~8h | 7/27 | KC 确认实验:先验强度 vs 想多少 |
| E-CHAINSUB 链替换中介(T0/T-clean/T-old) | 闭循环 | 贵 GPU 80-100 LOC | camera-ready | 唯一彻底破 RQ2/RQ3 循环=证自然必要性 |

### 用户决策点(只有你能定)
1. **框架分叉**:MECH-led(推荐)vs KC-as-headline-now vs EVAL-led vs MIN。
2. **Title**:现保留机理/修复向(可后改 KC)vs 现在就 commit knowledge-conflict。
3. **7/20 前要不要为 base-recall cross-tab 烧 H200**:推荐**否**(KC 赌注、滑窗风险;abstract 关键 compute≈零)。
4. E-CHAINSUB 是否现在 name 为 future + 机会性建解码路径(推荐:§7 name-and-bound、不阻塞 7/27)。

### 最大残余(全做完仍在)
**RQ2/RQ3 非独立性(循环)**:logit-lens"cloze 编辑完好"与"链抑制修答案"可能读同一 o_old/o_new logit 几何 → 即便 MECH 的干净因果也只是"强扰动+特异",非真中介;唯一能破的 E-CHAINSUB(证自然必要性)明确 camera-ready、现 harness 7/27 前跑不了。计划硬 bound(答案段不触 + N/T/D/P 符号特异 + inert placebo floor + 零卡自然 necessity 观察)但关不掉。次残余:头牌仍单模型/单编辑器/单数据集/单 α;capability 推论靠 6 点/2 族(Llama 仅 2 尺度)。**⚠ 待办**:KC priority 查重 agent 挂了 → 升 KC 前须补查 knowledge-conflict 框架是否已被占(context-vs-parametric conflict 文献近邻)。

---

## 第二轮深度计划 (v2, 2026-06-30) —— W1/W2/W3 完成后的全文 re-review 重排(优先级被第三轮取代,具体动作仍有效)

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


## 第四轮 (v4) —— 第一性 v2 solidity → 可执行实验计划【当前权威】

**来源**：6 条代码级断言逐条核验(4 verified / 2 partly,两 partly 均为字面-cosmetic 非实质)→ 两审收敛弱点融合 → 7 个实验(S1/S2/S5/S6/S7/S8/S9/S10)设计 + 逐个红队。**本节取代 v3 排程,作 7/20-7/27 唯一作战序。**
**口径铁律(每个实验都绑,违一即作废)**:① `edit_loop.py:147 ed.edit(sequential_edit=True)` 永不改 False(否则 EasyEdit 在 edit() 返回前还原权重→全程在基座生成,fb46107 污染源);② Hopper 编辑态 `WHYAAAI_DTYPE=float32`(bf16 ROME compute_v→NaN);③ 判分用 `metrics._without_subject`+word-boundary `\bcand\b`+丢<4-char 别名,RR/RRs 门 b0ok,**绝不**混 EasyEdit rewrite_acc(logits 口径);④ scope=='think' 经 `think_budget.py:87` 把答案段解码 lp=None→答案逐字节同基线(架构保证非经验);⑤ 新非-CF 分片 tag 必避 `infer_tag_meta` 黑名单(`percase_emergence.py:116` genbench/multihop/logitlens/steer/sweep/_a1.._a4),否则被并进 RQ1 容量斜率。

### (a) 收敛弱点表

| # | 弱点 | pinned claim | raised_by | sev | 已核验代码事实 | 谁更致命 | 两审互漏 |
|---|------|-------------|-----------|-----|---------------|---------|---------|
| W1 | **RQ2 taxonomy 判官 prompt 预设结论(自伤污染)** | "90% (17/19) reverted chains 经 NAMED Bridge 重导;Recall=0/Associative=0/traceless=0"(draft §1 contrib-2、§5 tab:taxonomy、necessity.json reversions.traceless=0) | both | **major** | `chain_classify.py:25` 逐字含 "edit STILL INSTALLED…ROUTING AROUND an intact edit, NOT recalling decayed weights…Make NO claim that…the edit weakened";中性兄弟 `revert_judge.py:20` 不复用且 docstring(:5-6)明说"避免带偏验证判官"。Recall=("recalling decayed weights")与 Associative=("unspoken prior")正是措辞语义禁掉的两类→Recall=0/Associative=0 至少部分仪器制造 | **Claude 更致命**:钉死非对称(`chain_classify:25` 污 vs `revert_judge:20` 中性,draft.md:73 宣传后者"never told edit's status")=审稿读作 cherry-picked neutrality,伤超单结果;depth-plan.md:113/158 自己点名删这些句子=自证 | Codex 漏:necessity 19/19 rederiv+traceless=0 继承**同一**污染源(`necessity_check.py:45-47` 直读 contaminated labels_*.jsonl);Claude 漏:无 |
| W2 | **logit-lens 非擦除探针近-tautological + 不可判别(无 held 对照/无 CI)** | "reverted 100% edit-intact 于 cloze + 旧事实 mid-stack(g8=-0.246/g12=-0.351)→ reversion 是推理重导非擦除"(draft §5,logitlens edit_intact_pct=1.0) | both | **major** | `logit_lens.py:104` 每 case 重灌 ROME(seq=True)→`:107` 喂裸 cloze(无链)单前向→`:116` intact=gap_top>0。`pick_reversion_cases`(:24,:43-44)只选 b0ok∧B3 含 o_old=纯回退池,**无 held 对照**;ROME 优化的正是 logit(o_new)@此 cloze→intact=1.0 物理几近必然 | **Claude 更致命**:点 mid-stack dip @inject layer12=注入签名非回退相关、held 上同样会出现;判明 tautology 比所述更强(静态权重前向原则上看不到 decode-time 效应) | 两审皆漏:`gap_sampled`(results.json:505)是手填 17-元向量、`logit_lens.py` **不 emit** edit_intact_pct/gap_sampled(grep 证),n=10(32B)无 per-case jsonl 无 CI——比任一审所述更具体 |
| W3 | **capability p=.0007 来自 K=2 族 cluster bootstrap(假精度)** | "erosion 随 capability 升,两族六尺度,per-case CLR slope 0.372[0.149,0.800] p=.0007"(draft §4,results.json percase) | both | **major** | `percase_emergence.py:339` 实为 `rng.integers(0,K,K)` K=len(fams)=2(非审稿引的硬编码 0,2,2,数值等价→verdict partly);drop-one family FE(:256-259)使 slope 为族内量;within_qwen_clr(:374)slope0.365 p=.01 是更干净腿 | **Codex 统计更精**(点 :339、demote 到 within-Qwen 4 点)/**Claude 后果更致命**(懂 cluster inference 的审稿一眼看穿 2 族给 p<.001=**数字 backfire**,须删非降) | 两审皆差**致命融合一步**:唯一存活的 CLR 同时是 necessity 证明**不可判别回退**的指标(held clr 14/14=1.00 ≥ reverted 0.895)→"capability-emergent"承重统计对标题承诺的答案级 undoing 反-判别(es_drop p=.188/rr p=.426 均含零) |
| W4 | **RQ2/RQ3 循环:两者读同一 o_old/o_new logit 几何;自然生成必要性未证** | "in-chain re-derivation(非擦除)governs the answer"=RQ2(cloze intact)+RQ3(链 fix)可能是一几何两读;自然必要性有界未闭(draft §6/§7) | both | major(draft 已自认→非 fatal) | scope=='think' 经 `think_budget.py:87` 答案段 lp=None→答案逐字节同基线=架构保证;E-CHAINSUB 在**答案位**作用(logit-lens 误测处:裸 cloze 无链),破循环 | 大致平手;Codex 加"neutral span selection"(bridge 实体须取去污判官输出否则 re-import :25 偏);Claude 加"residual no reframe can erase" | Codex 漏 Claude 的"同 ~20 case 四看";Claude 漏 Codex 的 neutral-span 警告 |
| W5 | **整机理核 = 一个 n≈20 的 32B 池复用四次** | logit-lens(n≈10-17)/taxonomy(19)/necessity(19)/RQ3 reverted(~11-23)同一 ~20 32B 回退 case 四视角 | **claude only** | major | results.json rq2_taxonomy.pooled n=19、necessity reversions n=19、logitlens 32B n≈10,重叠真实 | Claude 唯一:一个 n=20 池撑四"独立"结果审稿不信;加宽 17→100+(S6/extract_reverted)是单一最高乘子防御(同时硬化四腿) | **Codex 完全漏**——把四件当各自独立 fix,从未注意共分母。本轮最清晰的非对称盲点 |
| W6 | **生成式 word-boundary 判分 + κ=0.836 测量脊** | "去污 word-boundary 改 ~2x 泄漏膨胀;中性 3-判官 κ=0.836 strict reversion 验证"(draft §3,contrib-4) | both | **minor(solid)** | metric_validation n=87 vs_RRs_strict_decontam κ=0.836/agree=0.931/prec=0.92/rec=0.85/TP23 FP2 FN4 TN58。**关键**:κ 由**中性** sj_validate.py/revert_judge.py 产、**非**污染 taxonomy→头条回退测量验证干净 | 两审皆升档(33 drop 若全 TN→κ升 0.853→0.836 是保守下界);皆未杀 | Claude 独记残余(κ 绝对值依 rule_rr 分层先验、abstract 裸引 0.836 缺 caveat、判官同族);两审皆漏 deployment-gate 等价检验靠单位数 McNemar discordant(draft.md:292 自认"normal approx borderline") |
| W7 | **RQ3 链 fix 特异性仅相对 INERT placebo 非竞争答案;footprint 小** | "signed/specific/dose-controlled 链 fix;T-P 四指标排零,P-N≈0,D-N 反转,α-sweep Loc 平"(draft §6,rq3.sup_battery)=**两审皆认的真承重腿** | both | **minor** | `think_budget.py:87` 答案段 use_sup 门 scope=='all'→think 下答案逐字节未改=架构保证;B0 ES think0.580/all0.727 消融印证 | Claude 框最精(SUFFICIENCY-under-suppression 非自然 NECESSITY;特异仅对 INERT placebo;footprint ~6 strict/~13 loose)+应**re-center 头条于 RQ3** | Claude 漏 Codex 的第二 operating point(14B/70B)与等长 filler 控制(护"reasoning"词);Codex 未如 Claude 强调 :87 架构保证 |

**单点最弱(两审独立同点)= W1 的 traceless=0/Recall=0/Associative=0**:零 GPU、指纹清晰、任何审稿打开 prompt 文件即复现,且团队自己 depth-plan.md:113/158 点名删过却只修了中性兄弟。

### (b) 排序实验程序(威胁录用×死线可完成,🔴7/20 / 🟠7/27 分段)

> 排序原则:① 攻最弱且零/低成本者优先;② 头条承重腿(RQ3)的泛化与去循环优先;③ 地基(加宽池)是多个实验的前置乘子;④ 红队判"假确认/不可判别 null"风险高者降级或换更便宜杀法。

#### 🔴 7/20 前(abstract;全零卡或单卡轻量,墙钟≤1.5d/件)

---

**[S1] 中性重跑 taxonomy 判官** —— role=**防御**(攻单点最弱 W1)
- **目标 claim**:KILLS-or-CONFIRMS "reversion 重构性 Bridge 90%(17/19),Recall=0,Associative=0,traceless=0"。去 `chain_classify.py:25` 三句结论灌输,中性重判**同一批链**,测路由分布是否经得起去污(回退**计数**不动——已由中性 revert_judge.py κ=0.836 独立验)。
- **procedure(绑口径)**:STEP0 fork `JUDGE_PROMPT_NEUTRAL`(删 4 句污染、加中性 OLD/NEW/NEITHER 前置门、把 Recall/implicit-leak 升为一等可引选项);**`summarize/pool_summaries/fleiss_kappa/_boot_ci/latex_table/necessity_check` 100% 复用不动**。STEP1 **不重生成任何链**——`emit --reverted data/reverted_{scale}.jsonl`(已含 cot/answer/s/o_old/o_new,red-team 证 ~5 LOC 即可、非 30-50)重产中性 prompts 到 `results/a3_neutral/`。STEP2 **唯一非本地步**:喂同一 3-判官工作流(99 calls=33 case×3,非 brief 的 720)。STEP3 aggregate→pool→`necessity_check.py --a3 results/a3_neutral`。STEP4 per-case 一致性表(污染 vs 中性 primary,case_id-join)+路由迁移矩阵。
- **data**:IN(全本地)`results/a3/prompts_{7b,14b,32b}.jsonl`(裸 COT 嵌 prompt 字段)+`prefeat_{scale}.jsonl`+上游 `data/reverted_{scale}.jsonl`;OUT `results/a3_neutral/*` + `necessity_neutral.json` + 一致性表。**GPFS/GPU 不碰**。
- **predict 证实**:Bridge 仍主导(pooled ≥75%),Recall≈0,traceless≈0,per-case 一致性高→路由由链本身驱动(cf_19889 "pied=foot,gai=happy→French"等真桥),把单点最弱**硬化**为可发表去污表。**杀死**:中性下 Recall>0/Associative>0,Bridge 跌(90%→≤70%),一致性低→确认仪器制造,软化"重构性/no traceless leak"并传入 necessity(traceless 不再=0→撤"回退从不无声")。**即便杀也净正**(自己发现远胜审稿打开 :25)。
- **null 有信息**:**强**——分布不动=确认(paper 最需的硬化)、分布动=诚实自纠。唯一无信息=n=19 判官噪声,经同 3-判官多数+报 per-case 一致性缓解。
- **墙钟+LOC**:~1-1.5d / **LOW ~80-140 LOC,无新解码路径无新 harness**。
- **【both:本地写码 fork+一致性脚本 / 平台跑 99 judge calls】**
- **红队结论**:**RUN,但 3 项必改 + 1h 免费前筛门**。(真能杀✓)。**改①(闭 loophole-1)**:加**precedence-ablation 臂**——冻 `PREC`(Bridge>Recall,permissive Bridge def @:33-38)留着结构性 prime,"Bridge 存活"被排序混淆;须另跑 Recall-before-Bridge 或非-precedence 多标投票。**改②(闭口径张力)**:STEP0(b) 的 committed-value 前置门可经 `aggregate_votes:108` held≥2 分支移动 in_population→破"n=19 固定"与一致性 join;须**冻 in_population 到污染run 的 case_id 集只重标路由**,或显式报 n-drift。**改③(闭 loophole-2)**:报 per-case 一致性%+迁移矩阵为**主**,cross-prompt κ 为次带 caveat(Bridge base-rate 主导下 κ 退化到 ~0/undefined,即 7B κ=-0.091 病理)。**免费杀**:先人读 2/19 clr_in_cot=False 的链(draft 含糊为"Bridge via spelling cue"者),若任一肉眼即 traceless→claim 零成本死、S1 免跑。

---

**[S9] base-recall×reversion 混淆回归(去 Step2)** —— role=**防御**(攻 W3 capability 因果内容)
- **目标 claim**:CONFIRMS-OR-KILLS "capability(非 prior-strength/edit-weakness/chain-len)驱动 erosion"。去混淆:斜率是否只是"大模型更知 o_old(更多可泄)"或"ROME 在这些 case 落得更弱"或"链更长"。
- **procedure(绑口径)**:**红队改写版**——**删原 Step2 edit_margin**(自认近-tautological+方差可能为零+给 clr/es_drop 回归引入 b0ok 群体 NaN-drop 静默缩 n)。只做:Step1 `base_probe.py` 全 6 尺度跑(无编辑,bf16 安全,`{tag}_BASE_cf_r*.jsonl`,load_cases 同 case 集保证 join 精确)→per-case base_recall=`hit(_without_subject(base_B0,s),o_old)`∈{0,1};chain_len 已在 percase 长表。扩 `percase_emergence._design` 加 base_recall+chain_len 协变量(log_params 留 col1),family drop-one dummies 留,同 K=2 cluster bootstrap 跑 nested(带/不带协变量斜率对比)。
- **data**:IN 6 容量 ROME×CF 分片(GPFS);OUT `{tag}_BASE_cf_r*.jsonl` + `results/percase_emergence_confound.json`(**不**覆盖 headline)。
- **predict 证实**:加协变量后 **CLR** log_params 斜率仍正、p 小、CI 排零(0.372→~0.25-0.35),且 within-Qwen-only CLR 仍正排零→capability 做超出 base-knowledge 的实功。**杀死**:base_recall partial 后斜率塌向零/失符号稳定→"emergence"只是"大模型更知 o_old";或 chain_len 吸收(Codex 点的"是 reasoning 还是长度?"洞,S8 另补)。
- **null 有信息**:**强,杀向更值**——null=诚实 paper 改写为"reasoning 重导受权重仍持的冲突先验强度支配"(draft 已半说),换掉脆弱 p=.0007=预堵两审同点的 backfire。
- **墙钟+LOC**:本地 ~3-4h + 6 尺度 base_probe(轻,无编辑无 mom2,~2-4h 并行);**红队改后省掉整个 Step2 70B-fp32 重编辑 pass(LOC+墙钟瓶颈)**。改后 ~15-40 LOC。
- **【both:本地写码 join+回归 / 平台跑 6 尺度 base_probe】**
- **红队结论**:**不按原设计跑——跑去-Step2 廉价子集 + 重框问题**。(真能杀✗ 干净——K=2/6 distinct log_params 使 partial 斜率是族内、"CONFIRM"会把 within-Qwen 走私回 abstract 当跨族 p)。**口径 bug**:(A)`_design` 只过滤 outcome 非协变量→若非全 6 尺度跑 base_probe,join 出 NaN 协变量列进 lstsq 静默坏;(B)edit_margin 只定义在 b0ok→进 clr/es_drop 回归 NaN-drop 非-b0ok 行静默缩 n、偏离 headline n。**故删 Step2、全 6 尺度 base_probe、报 within-Qwen-only,无论显著都 demote 裸 p=.0007 为 within-Qwen 描述性单调趋势 + 采 Codex prior-conflict 重框**。NULL/PARTIAL 是有价值的、对齐审稿想要的 paper;CONFIRM 是陷阱。

---

**[S2-cheap] logit-lens 重制 reverted-arm CI(零 GPU 那半)** —— role=**防御/诚实仪器**(攻 W2)
- **目标 claim**:把"mid-stack 旧事实是回退特异 substrate"分解:CONFIRM 无污染的 edit-intact 半(带 per-case CI)、测第二半 held-vs-reverted mid-stack 对比。
- **procedure(绑口径)**:**红队拆分**——reverted-arm per-case bootstrap CI 是**~20 LOC 对已有 `logit_lens.py:120` 已写的 gap_by_layer[0..64] 的纯重制(零 GPU)**,先落地。held-arm(`pick_held_cases` 翻转 budget 条件:b0ok∧NOT hit(clean(bb),o_old))的前向(n≈6-13 新编辑)才需 GPU,**门控在 S6 加宽池之后**(held n<~6 则 Δgap 无界)。
- **data**:IN `results/probe/r1qwen32b_ROME_cf200_r*.jsonl`+原 logit-lens 输出;OUT 加 group∈{reverted,held}+`logitlens_control_summary.json`,手并入 results.json(替手填 gap_sampled)。
- **predict 证实**:L8-12 Δgap(held−reverted)CI 严格>0→真回退特异 substrate。**杀死**:Δgap CI 跨零→dip 是 inject-layer(12∈[8,12])artifact、held 同有→drop mid-stack substrate 头条、窄化 logit-lens 仅留"非擦除"、re-center 机理于 RQ3+E-CHAINSUB。
- **null 有信息**:**强**——~55-65% null(dip 居 edit_layer=12,held 极可能同 dip)是团队最缺的诚实有界负结果,逼正确 paper 动作(re-center RQ3)。
- **墙钟+LOC**:零-GPU 半 ~20 LOC 立即;held 半 ~40 LOC+小 GPU 窗(<1h,32B fp32 加载主导)。
- **【both:本地重制 CI(先) / 平台跑 held-arm(后,门控 S6)】**
- **红队结论**:**RUN 但降级为受控撤退非确认猎**。(真能杀✓ 仅特异性半,非 draft 已发的较弱绝对语句——draft §5:183/185 只说"reverted 里 trace 存在",故先**零成本软化** §5:183/185 去任何回退特异暗示)。**更便宜杀**:logit-lens 静态权重上特异性近-unfalsifiable(caveat#6+#8),纯论证即可删过-claim、零跑。口径:b0ok 划分干净(verified)、scope mismatch(生成式 held≠taxonomy judge-committed held)勿宣称同群体。

#### 🟠 7/27 前(全文;头条承重 + 地基,需 GPU 窗)

---

**[S6] 加宽 32B 回退池 17→100+** —— role=**地基**(撑"四独立结果",W5)
- **目标 claim**:CONFIRMS(硬化非杀)整机理核——用独立来源 100+ 32B 回退替换共享 n≈20 分母,给路由计数/edit-intact/traceless 各拿到足够窄的 Wilson/bootstrap CI。**只修分母不碰判官 prompt**(与 S1 正交,且是 S1/S2-held/necessity/S5 的前置乘子)。
- **procedure(绑口径)**:STEP0 `probe32b_wide.yaml`(clone probe32b.yaml,`dataset.n:1500`,**新 tag `cf1500`**——避黑名单;**红队强制加 `dataset.path: data/counterfact.prefiltered.cf1500.jsonl`**——否则 prefilter 覆盖共享 `data/counterfact.prefiltered.jsonl` 毁现有 cf200 headline 与全部 32B suppression 臂)。STEP1 8-shard prefilter(4090 bf16)。STEP2 头条 B0/B3 生成(32B `WHYAAAI_DTYPE=float32`,seq=True,per-case restore)。STEP3 `extract_reverted`(同 b0ok 门;**红队点:extract_reverted 用 RAW answer 无 `_without_subject`、logit_lens 有→两池非同 case 集,须统一 去主体 口径**)。STEP4-6 taxonomy/logit-lens/necessity 在加宽池重跑。
- **data**:IN `data/counterfact.jsonl`(21919,余量足);OUT `r1qwen32b_ROME_cf1500_r*.jsonl`/`data/reverted_32b_wide.jsonl`/`results/a3/labels_32b_wide.jsonl`/`necessity_wide.json`。
- **predict 证实**:n≈75-110,Bridge CI 下界 ≥0.55,traceless Wilson 上界 ≤0.05,edit_intact_pct CI 下界 ≥0.96。**杀死**:分布显著移(Bridge<50%/Associative>15%/traceless>10%/edit_intact 明显<1.0)→n=20 是小样 artifact、contrib-2 须从清晰类别降为带 hedge 分布。
- **null 有信息**:**强**——null=分布不动=目标(把"n=20 四看"变"n=100+带 CI")。
- **墙钟+LOC**:~12-18h GPU 关键路径(32B fp32 1500-case 生成主导)+~2h judge;**~5-10 LOC(纯 config),无新解码路径**。
- **【both:本地 config+extract / 平台跑 prefilter+生成+logit-lens】**
- **红队结论**:**SOFT-CONFIRM 但必改,勿按原样跑**。(真能杀✗ 设计如此 role=foundation)。**致命 口径 bug**:`prefilter.py` 写 `cfg.dataset.path`(每 config 硬编码 `data/counterfact.prefiltered.jsonl` 非 tag-keyed)→STEP0 只改 n/tag 不改 path→**`--merge` 覆盖 cf200 prefiltered 毁现有 headline+全 32B suppression 臂+毁 RR=0.193 可复现**;**修=STEP0 必设 cf1500 专属 dataset.path**。**第二 bug**:extract_reverted(无去主体)vs logit_lens(有去主体)b0ok 门不一致→两加宽池不同 case 集;须统一。**更便宜路**:为防御目标(裸计数→带 CI),先在**已有 n** 上算 Wilson/bootstrap CI(零 GPU ~3 LOC),只在审稿真要更大 n 时才花 GPU——且 cf400 即可翻倍 32B cell、~1/4 墙钟。**框架 bug**:只加宽 32b,pooled n=19(=4+5+10)与 17/19 不变除非 7b/14b 也重跑——勿宣称硬化 pooled 头条。

---

**[S5] E-CHAINSUB 链替换中介** —— role=**头牌**(破 RQ2/RQ3 同几何循环 W4)
- **目标 claim**:KILLS-OR-CONFIRMS "自然回退是中介答案的 in-chain 重导;链对答案翻 o_old 因果必要;RQ2+RQ3 非一静态几何两读"。冻单 ROME 编辑(三臂权重相同),只看 think 段决定答案分布:T0(模型自反链)/T-clean(仅复述编辑、无 o_old 无 bridge)/T-old(中性桥链重导 o_old)。在**答案位**作用(logit-lens 误测处)。
- **procedure(绑口径)**:新解码路径"给定 think 段→只解码答案"=`think_budget.py:86-87` 答案分支 5 行重组(`TPL.format(q)+think_seg+THINK_END`,`g(text,256,use_sup=False)`→lp=None 答案逐字节同基线=架构保证)。每 case 一编辑会话三解码,seq=True+per-case restore,`WHYAAAI_DTYPE=float32`。判分生产口径。新 harness `src/chainsub.py`,tag `chainsub_*` **加 `percase_emergence.py:116` 黑名单**。
- **data**:IN T0=`data/reverted_32b.jsonl` 的 cot;T-old bridge 实体源——**红队致命 bug 修后**:须真跑中性 revert_judge.py 持久化 per-case `quote` 造去污源,或盲于 taxonomy 手抽 bridge span;OUT `results/probe/chainsub_cf200_ROME_{32b,14b}.jsonl`。
- **predict 证实**:revert(T0)高、revert(T-clean)≈0、revert(T-old)高,答案首-token gap T-clean 正/T0&T-old 负——**冻同权重**→链内容(桥重导)翻答案非权重衰减,必要性在答案位证、循环破。**杀死**:三臂平(T0≈T-clean≈T-old)→答案由静态几何驱动、循环成立、中介头条塌(re-center RQ3-sufficiency only);或 T-clean 也高→非链中介;或 14B 失败→单尺度 artifact;或 T-old 不回退→桥非因果路、taxonomy Bridge 故事过陈述。
- **null 有信息**:**强**——平 null 把 draft 已自认开放限制(§6/§7)从软 hedge 变实测诚实边界,re-center 头条于干净 RQ3。
- **墙钟+LOC**:~1d 端到端(含池加宽)/ 新解码路径**薄**(5 行重组)+`chainsub.py` ~120-160 LOC。
- **【both:本地写 chainsub.py+T-clean/T-old 构造 / 平台跑池加宽+三臂解码】**
- **红队结论**:**CONDITIONAL——原样有致命 provenance bug,勿跑**。(原则上单点最高杠杆,但)**致命 bug**:T-old 去污规则"取中性判官 `quoted_span`"**事实反了**——`quoted_span` 字段**只存在于 `chain_classify.py:57`(污染 taxonomy)**;`verdicts_32b.jsonl` 即 chain_classify 输出(`:25` prime);中性 `revert_judge.py:32` emit 的是 `quote` 且**从不 per-case 持久化**(`results/sj/` 不存在)→从 verdicts_32b 取 = 源头 re-import "routing-around-intact-edit" prime,破循环本身循环。**修前置**:(a)真跑 revert_judge.py 持久化 quote,或(b)盲于 taxonomy 手抽桥 span;(c)`chainsub` 加 `:116` 黑名单(确需,当前无);(d)删"硬化擦除"宣称(within-case 同权重对照 tautological 继承 logit-lens edit_intact=1.0)。**更便宜杀**:`clr_in_cot` vs revert-rate 在已有 `reverted_*.jsonl` 上交叉表(~20 LOC 零 GPU)——clr_in_cot=False 的回退(o_old 不在链却答案翻)即 prima facie 答案非链中介,先门控 GPU 花费。**池现实**:可用 Bridge case ~8 非 ~20,池加宽是从零 GPU 头条 run+3-判官,非 config-only,重算 7/20 墙钟。

---

**[S10] RQ3 第二 operating point(14B,选 70B)** —— role=**防御**(护真承重腿 W7 泛化)
- **目标 claim**:KILLS-OR-CONFIRMS "链 fix 非单 32B/CF/α=8 点:signed+specific 控制(T-P 排零、P-N≈0、D-N 反转、Loc 持)在 14B(主)/Llama-70B(次)复现"。
- **procedure(绑口径)**:**复用 32B E-SUP-BATTERY 管线逐字**,只 3 小 config/operating-point。14B:`probe14b_sup{,_onew,_placebo}.yaml`(model_tag=r1qwen14b,v_loss_layer=47,layers:[9],scope:think,penalty:8)。N 臂若 `r1qwen14b_ROME_cf200_r*.jsonl` 已在 GPFS 则复用。**D=o_new 先跑 n≈100**(符号错 day-1 知,prereg 规则1)。BLIND-locked `data/placebo_donors.json`(覆盖全 21919 cf_*,**勿见结果后重生**)。`cross_arm.py` 读 prereg-esup.md 决策规则。
- **data**:IN GPFS 14B/70B 权重 + `data/counterfact.prefiltered.jsonl`(同 seed42 序);OUT `r1qwen14b_ROME_cf200sup{,_onew,_placebo}_r*.jsonl` + `results/esup_crossarm_14b.json`;新 config commit。
- **predict 证实**:14B prereg 符号梯 D≤N≈P<T 复现,T-P 同符号排零,P-N≈0,Loc 持→fix 是回退机理属性跨尺度(70B 则跨族)非单点 artifact。**杀死**:T-P 不排零(单尺度);P-N 排零(placebo 也帮→o_old-特异自伤);D-N 反符号(ES>0/RR<0,**near-fatal**,day-1 D@100 先探);Loc 塌;前置失败(B0 ES_b 低→b0ok 池小→欠功,非真杀,先扫层)。
- **null 有信息**:**有,带歧义消除**——真 null(健康 b0ok+Loc 持下 T-P 跨零)界定 fix 为 32B-特异、诚实可发;但**欠功 null(B0 ES_b 低)非信息**——须扫层至 B0 ES_b 可比 32B。
- **墙钟+LOC**:14B ~12-18h 墙钟(含 N 重跑+判分+cross_arm CPU);70B model_parallel ~1.5-2.5 墙钟-天;**≤180 LOC config,0 LOC Python,无新解码/harness/scorer**。
- **【both:本地写 3 config / 平台跑 T/D/P 三臂】**
- **红队结论**:**SOUND 但 mis-prioritized + over-scoped;重排序 + 绑主端点**。(真能杀✓ 在 robust 腿 ES@B3/CLR)。**loophole**:prereg 把 T-P 钉在 **b0ok-门控 RR/RRs**(项目自认脆弱的答案级指标),14B null 那里最可能(~30-45%)且设计自留逃生(扫层非真杀)→弱结果经 loophole 不干净证伪。**口径全清**(4/4 关键绑定 verified:seq=True@:147、scope=think@:74/87、cross_arm 去主体+b0ok 门、placebo_donors 覆盖全 cf_*)。**更便宜杀(同审稿线)**:α-sweep 在盘 config(`probe32b_a2_th_p{2,4,8,12,16}` α∈{2,4,8,12,16})——单调剂量响应 5 点是比一个新模型更强的"非单点"反驳,**纯重制零 GPU**,abstract-死线安全。**改**:①先做 α-sweep 重制(零卡先堵 α 轴);②14B 跑 T/P/N+day-1 D@100;③**prereg 钉 ES@B3 为主端点**(非门控 RR),门控-RR null 不能静默降级;④70B 仅 14B 7/22 前确认且 model_parallel compute_v 路径 1-case smoke 去险后才跑(否则最差 trade)。

#### 降级/不进本轮(红队后)

- **[S8] 等长 filler 控制** —— **REJECT for abstract,REWORK before camera-ready**。致命结构混淆:confirm 臂(true-B3)与两 kill 臂(F-other/F-neutral)同时差两变量(是否 reasoning ∧ o_old 是否在链),因设计硬连 CLR(filler)=0→"filler 不翻"被平凡"o_old 不在链"全解释,**不能判别"reasoning 重导此事实" vs "任何提 o_old 的链都翻"**。是降级版 E-CHAINSUB 缺判别臂(T-old:不相关链但含 o_old)。**更便宜赢**:重制已有判官标签(plan.md:134 证 32B 17/17 explicit-CLR、0 Recall/0 Associative=Bridge 路由)零卡已支持 prose claim。若要真因果,花 LOC 在**完整三臂 E-CHAINSUB(加 T-old)**,且须 S6 加宽池过 n≈17 后跑。
- **[S7] MEMIT 第二编辑器** —— **SOUND-WITH-FIX,camera-ready 优先级**。口径全清(seq=True/scope=think/fp32/b0ok/aliases verified)、极廉(~25-40 LOC YAML 零 Python)。**必改**:**勿只单层[12]跑 MEMIT**——MEMIT 本质多层(出厂 qwen yaml [4,5,6,7,8]),单层退化向 ROME 自身几何=混淆"非 ROME 特有"断言;须**原生多层带 跑**为主点、匹配单层仅作次对照。**更便宜**:先查 `analysis/10` 7B MEMIT 分片是否在平台存活、`score_pilot` 重制(零 GPU 部分 editor-generality 信号,带 7B=flat 尺度 caveat)。phenomenon 臂先发,fix-transfer 臂(~翻倍墙钟)camera-ready-optional。

### (c) 红队总结:被改/降级/有更便宜杀法

- **被改(必改后才跑)**:
  - **S1** +precedence-ablation 臂(`PREC` Bridge>Recall 是第二结构 prime,冻它则"Bridge 存活"被排序混淆)+冻 in_population case_id 集(committed-value 前置门经 held≥2 移动 n,破 join)+报一致性%非 κ(Bridge 主导下 κ 退化)。
  - **S5** 修反了的 provenance(`quoted_span` 只在污染 taxonomy;中性 `revert_judge` emit `quote` 且从不持久化)+`chainsub` 加黑名单+删"硬化擦除"宣称+重算池现实(~8 非 ~20)。
  - **S6** 修 `prefilter.py` path-collision(必设 cf1500 专属 `dataset.path`,否则覆盖共享 prefiltered 毁 headline+全 suppression 臂)+统一 extract_reverted(无去主体)vs logit_lens(有去主体)b0ok 门。
  - **S9** 删 Step2 edit_margin(近-tautological+方差或为零+给 clr/es_drop 引入 NaN-drop 静默缩 n)、全 6 尺度 base_probe、报 within-Qwen-only、demote 裸 p=.0007。
  - **S2** 拆零-GPU reverted-CI 半(先发)与 GPU held 半(后,门控 S6);先零成本软化 draft §5:183/185。
  - **S10** 先 α-sweep 重制堵 α 轴、prereg 钉 ES@B3 主端点、70B 去险后才跑。
- **被降级**:S8(REJECT-abstract→REWORK-camera-ready,缺判别臂);S7(camera-ready,必多层跑)。
- **有更便宜杀法(零/低 GPU 先做)**:
  - S1→1h 人读 2/19 clr_in_cot=False 链(可零成本杀 claim,免跑)。
  - S5→`clr_in_cot` vs revert-rate 交叉表 ~20 LOC 零 GPU(clr_in_cot=False 回退即答案非链中介证据)。
  - S6→已有 n 上算 Wilson/bootstrap CI ~3 LOC 零 GPU;真要大 n 则 cf400 非 cf1500(1/4 墙钟)。
  - S9→within_Qwen_clr 已在 percase_emergence.json,报它+chain_len partial=纯 paper-edit。
  - S10→α-sweep 在盘 config 重制,5 点剂量响应零 GPU 比一个新模型更强反驳。
  - S8→重制已有 Bridge/Recall=0 判官标签零卡支持 prose claim。

### (d) 单点最高杠杆 + 7/20 只能做一件

- **单点最高杠杆 = S1(中性重跑 taxonomy)**,且**其前置免费门(1h 人读 2/19 clr_in_cot=False 链)是整轮最高杠杆 1-小时动作**。理由:① 直击两审独立同点的**单点最弱 claim**(W1 traceless=0/Recall=0/Associative=0);② 零 GPU、指纹清晰、任何审稿打开 `chain_classify.py:25` 即复现——不修=送审样垃圾且自证(depth-plan.md:113/158 点名删过);③ 双向强信息(硬化或诚实自纠都净正);④ 输出直接替换污染表 + 一句"路由对去 edit-intact prime 中性重判鲁棒(Appendix κ=X)"中和审稿最强攻击。**注**:S6(加宽池)是更高**结构**乘子(同时硬化四腿),但它是地基非攻击、且需 GPU 窗 + 有 path-collision 致命 bug 待修;S1 是零卡即可落、攻最弱点的最高单点。
- **7/20 只能做一件 → 做 S1(且先跑其 1h 免费前筛)**。退而求其次同档零卡件:S9-去Step2(within-Qwen 重框 + 6 尺度 base_probe,堵 W3 backfire)与 S10 的 α-sweep 重制(零 GPU 堵"单点"α 轴)。三者皆零/轻卡、皆攻审稿要害、皆可 7/20 落地。**S5/S6 因 GPU 窗 + 待修致命 bug,推 7/27。**

### (e) 诚实边界(到 7/27 受墙钟/工程量限补不上的 → 写 limitation 非算力)

1. **自然(未干预)生成里的必要性不闭**:S5 修后证注入下可操控 + S2/S6 硬化"edit intact"分母,但**都不证 route-around 在自然生成里必要**;logit-lens 仍是单方法单前向静态权重探针(加宽后 n≥40 但原则上看不到 decode-time 效应)。死硬审稿可说"你扰了链/解码器、从没在 wild 观察机理"。**这是本 harness 在 7/27 前无可行实验能完全消的唯一残余**——写 §7 limitation。
2. **机理核 n 仍 32B-中心**:S6 加宽 32B→100+,但 7b/14b 仍 4/5 case,pooled 头条若要硬化须重跑全尺度(墙钟不够)→main-report 32B-wide,跨尺度路由分布明标 case-study 量级。
3. **capability 解构后是"prior-strength"非纯"compute"**:S9 后诚实表述为"reasoning 重导受权重仍持的冲突先验强度支配",**within-Qwen-only 单调趋势**(K=2 跨族 p 删);跨族"emergence"因仅 2 族永不达 cluster-robust 可靠区,写 limitation。
4. **"reasoning"词的等长-drift 排他性不闭**:S8 因结构混淆降级 camera-ready,7/27 前**不**有干净 filler 控制证"是 reasoning 非长上下文漂移";靠已有 Bridge 路由+0 Recall taxonomy(prose 高度)+ N/T/D/P battery 支撑,写"answer-level drift 排他留 future"。
5. **编辑器/数据集广度=门票非加分**:S7 推 camera-ready,主结果 ROME×CF;MEMIT 多层点若来得及加,否则明标"locate-then-edit 一族,跨编辑器留 open"。
6. **deployment-gate 等价靠单位数 McNemar**:`draft.md:292` 自认 normal-approx borderline,等价主张落"by-construction"论证非检验功效——两审皆漏,**主动写进 limitation 预堵**。
- **净**:全做完 = "符号/剂量/方向受控的 fix(两 operating point)+ 判官中性验证的指标 + 混淆受控的 within-Qwen RQ1 + 去污 taxonomy + 加宽机理池" = **accept 级深度档**;但**不闭"自然生成必要性"**(残余#1)——诚实声明,非靠更多 GPU 能补。


## 第五轮 (v5) —— "有增量"实验(严格:能翻转/杀死一条 claim 或补 load-bearing 缺口)【与 §第四轮 并列;7/20-7/27 增量层】

**来源**:第三份第一性 review(Claude「增量实验」,`第一性review 增量实验.md`)。它补上 §第四轮**完全漏掉的维度=现象是否【编辑特异】**。§第四轮审 RQ2/RQ3/capability 的内部效度;§第五轮问"该不该有这个现象/机理"。**去重**:M3=§四S1(中性重跑判官,同一件);Cap3≈§四S9(6 尺度 base_probe 去混淆);K1⊂F1(32B base_probe)。**取代**:F1 盖过 §四 的 E-CHAINSUB(S5)成新单点最高杠杆。

**premise 已逐条核盘(本地 grep 证)**:F1=`results.json base_probe` 7B answer_old **0.59→0.67(+0.08)**、chain_old_b3=0.755、**仅 7B、32B 缺**;`base_probe.py` 同口径 metrics.hit/_without_subject、case 集取自已有 ROME 结果=直接可跑。F2=`think_budget.py:23` ZEROTHINK 空块、`:26` LESSTHINK_CANNED 存在标"仅消融用"。F3=采样路径 `:34/:58` 全建、results.json **零采样数**、draft §3.3 宣称"0.6×3 sampling arm"。Cap1=chain_len 是 `:217` 空白分词近似。

### 🥇 第一梯队 · 攻现象根基(§四漏,最高威胁,多零/廉价卡,进 7/20)

- **[F1] 无编辑 thinking-tax 基线 —— 新单点最高杠杆 · 头牌 · 【本地扩 base_probe + 平台跑 32B】**
  - 目标 claim=KILLS-or-CONFIRMS「thinking undoes **EDITING**(编辑特异)」。`base_probe.py` 在**同一批 200 CF case** B0/B3 跑 32B 基座(`WHYAAAI_DTYPE=float32`),报 **编辑 ES 降幅/RR − 基座 P(o_old) 漂移** 的 effect-above-control margin。
  - **kill**:基座 P(o_old)@B0→B3 涨 ≈ 编辑 RR(0.19)→ 现象大半是基座"越想越偏先验"、编辑特异残差被吃掉。**confirm**:基座漂移 ≪ 0.19 → 编辑特异坐实、下游全硬。**盘上已有反向证据**:7B base +0.08 = 7B 编辑 RR 0.080(已相等!)。
  - **红队(我加)**:base 漂移**不自动 kill** —— 编辑态回退="丢失 B0 已装入的 o_new"(base 无 edit 可丢=不同事件);须报三量:base ΔP(o_old)、base ΔP(o_new)(应≈0)、edited RR;**只有 effect-above-control margin(edited RR − base ΔP(o_old))近零才真塌**。即便 margin 小,仍可守"编辑放大了基座漂移"的窄断言。null 双向皆高信息。~40 LOC + 数 H200-h(7B/14B 部分在盘,32B 关键)。
- **[F2] ZEROTHINK 模板去混淆 · 头牌 · 【本地 ~15 LOC + 平台 4-5 H200-h(n=100)】**
  - 目标=「税不是空块伪影」。加 B0′=LESSTHINK_CANNED(已有未用)、B0″=B1@CAP32 最小自然链,用 B0′ 重锚 ES 降幅与 b0ok 分母。**kill**:B0 空块 ES ≫ B0′/B0″ → 税部分是"退化零推理捷径 vs 任何真推理"的模板差(空块偏顶层编辑 g64=11.6;一句真推理即触部分重推 g8/g12<0)。**红队**:B0′ 也可能被截断长度混淆,须与 F1 同口径 b0ok。
- **[F3] 温度/seed 鲁棒性(声称做了却零上报)· 头牌级(标 defense 能 kill)· 【平台跑,~0 LOC】**
  - 32B B0/B3 temp=0.6 × seed{0,1,2},报 ES 降幅/RR/CLR per-case CI。**kill**:采样下 RR/ES 降幅塌向零/反号 → 回退是单条贪心脆性(中层 gap −0.25~−0.35 近平局,微扰即翻;b0ok 本身贪心定义)。**审稿必点"声称做了没报"**。零 LOC(路径全建)。

### 🥈 第二梯队 · 攻机理/修复头牌(多零卡,7/20)

- **[M1] E-CLRZERO-SPLIT:按基线 CLR 分层修复效应 · 头牌 · 【纯本地零卡再分析】· 修复因果最便宜的 kill**
  - 把已跑 N/T sup_battery(盘上 n=198)按 baseline-N 每 case **CLR=1 vs CLR=0** 分层,分别重算 T−N 的 RR/ES。机理预测效应集中 CLR=1、CLR=0 消失。**kill**:CLR=0 case(~45%)上 RR 降幅相当 → 修复非靠"堵链内重推"→ 直杀「in-chain re-derivation **governs** the answer」。红队补:per-case 2×2(CLR 降? × RR 降?)中介,RR 在"CLR 没降"case 也改善=答案与链解耦。**零卡、直击头牌因果、今天可跑**。
- **[M3] = §四 S1** 中性重跑 taxonomy 判官(去重,见 §四;1h 免费前筛已跑=两条 clr=False 均松散桥非 traceless、claim 未被免费杀、S1 值得跑)。
- **[M4] "强竞争者"placebo 第 5 臂(C)· 防御 · 【本地 ~30 LOC config + 平台 1 臂】**
  - 现 placebo 惰性(`placebo_donor.py` 取别 case 的 o_old、从不取 o_new);压**同 relation 的强错误答案**(CF 带 relation_id 可分组)。**kill**:C−N ≈ T−N → 修复是"压任何强竞争者"通用效应、T−P(惰性 floor)弱证 → 杀 o_old 特异性(论文自认残余)。
- **[M5] 反思标记抑制臂 · 头牌级 · 【本地 ~20-30 LOC + 平台 2-4 H200-h】**
  - 压"wait/actually/but"(reflect_before_old 在 32B 回退 9/10 真)而非 o_old 内容,报 R−P。**kill**:答案照样修好 → 是 override 动作非 o_old 内容驱动 → 窄化"re-derivation"。零卡前奏:现有 T−P 按 reflect_before_old/contests_edit 分层。
- **[V1] E-CLR-JUDGE:中性判官验 CoT scorer · 头牌 · 【平台 ~40 CoT judge calls】**
  - κ=0.836 **只验答案级 RRs、从没验 CoT scorer CLR**,而 CLR 是唯一存活 erosion 指标。`metrics.py:149` `hit(cot,o_old)` **无极性检查**→"it is **not** French but Bolton"记 CLR+。中性判官验 CLR 假阳率。**kill**:大量"被否定/顺带提及"假阳 → 裂 emergence 测量地基。零卡红队补 V2:κ 的"neither"判为不一致重算,掉则 0.836 被 easy-TN 撑。

### 🥉 第三梯队 · 攻 capability-emergent(全零卡再分析,7/20)

- **[Cap1] E-CHAINLEN-KILL · 头牌 · 【纯本地零卡 ~50 LOC】**:唯一存活 CLR slope 用**空白分词** chain_len(`percase_emergence.py:217`),CLR 近饱和二值(held 14/14=1.00)。换真 tokenizer chain_len + 二次项 + **CLR-每-token 密度**,slope CI 可能盖零 → "capability-emergent"塌成"大模型链更长、按概率更常提 o_old"。
- **[Cap2] E-CLR-DISCRIMINANT · 头牌 · 【纯本地零卡】**:CLR 门到**真回退**(CLR*)重测 slope。CLR* 变平而 raw-CLR 仍升 → "啰嗦随能力涨"、非 erosion。
- **[Cap3] = §四 S9 base-knowledge 混淆**(去重):6 尺度 base_probe 控 edited-CLR slope 的 base-recall-of-o_old。slope 塌 → "CLR 随能力涨"="大模型本就更知 o_old"(知识可得性非 erosion),比 chain-length 更致命。

### 度量/why/部署(各留一真 kill)

- **[K1] ⊂ F1**:32B base_probe(abstract 的 0.59 是 7B 数误引给 32B 头牌,必补;F1 顺带产)。**【平台】**
- **[K2] E-KC-NOPRIOR · 头牌 · camera-ready**:在**基座不知 o_old**(recall≈0)的事实上编辑还回退吗?回退→"weights still hold the prior"被 falsify=**confabulation 非 conflict**(Recall=0/19+Bridge-via-spelling 使 kill 真可能)。先用 32B base 分层现有 200,不够再补编辑臂。**【both】**
- **[G1] E-CONDC · 头牌 · 8B 先做可 7/20 · ~40 LOC 路径已通**:在 **o_old 是合法推理中间步**的多跳编辑 query 上开抑制器(precondition-c 盲区,draft §7:295 自认 [pending])。hop-ES 掉→杀"zero collateral by construction"(部署门看不到的编辑-query 侧伤害)。**【both】**

### DROP(结果预定/非增量 —— review 判定,我复核认同)
E-UNIONTHINK(被两先验夹住)、E-PROMPTEDCOT(§7:286 双向预认+LOC 最贵)、copy-from-subject(overlap_subject=0/10 已死)、E-CANDIDATE-COUNT(判官选择偏倚)、E-INFLATE-DIRECTION(confirm 近必然)、E-FALSENEG(落在 [RRs,RR] 括号内)、E-POSITION-SEGMENT(只收窄不翻)、更多编辑器/数据集/尺度/seed(门票)、single-fact 部署门扩 n(by-construction 恒真)。

### 单点最高杠杆(v5,取代 §四的 S5/E-CHAINSUB)
**F1(无编辑 thinking-tax 基线),尤其 32B base_probe(盘上缺、是全局最关键缺口)。** 理由:E-CHAINSUB 精修一个**假定为真**的机理;F1 问这机理**该不该存在**——7B 盘上 +0.08≈RR 0.080 是**已指向坏结果的在手证据**、kill 真可能且便宜。confirm→标题 claim 更硬、每条下游更硬;kill→撼动标题。**但**(我红队)F1 的 kill 需 effect-above-control margin 近零 + 账清"丢 o_new vs 提 o_old"两事件,非"base 漂移就塌"。

### 7/20 增量冲刺(全零/廉价卡,融合 §四+§五,按"能杀×便宜")
1. **F1-32B base_probe**(平台;补全局最关键缺口)+ 本地扩 base_probe 报三量 margin。
2. **M1 CLR-split**(纯本地零卡;杀修复因果)+ **Cap1/Cap2**(纯本地零卡;杀 capability)+ **F1-7B/14B margin 重表**(在盘)。
3. **M3=S1 中性判官**(平台 99 calls;免费前筛已过)+ **V1 CLR-judge**(平台 ~40 calls)。
4. **F3 采样鲁棒**(平台零 LOC;堵"声称做了没报")。
**7/27**:§四 S5(E-CHAINSUB,修 provenance 后)、S6(加宽池,修 path)、M2(答案位动态 logit-lens)、M4/M5/K2/G1。**诚实残余#1(自然必要性)仍不闭**。
