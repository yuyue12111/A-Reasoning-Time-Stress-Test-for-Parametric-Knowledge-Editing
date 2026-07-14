## A. 总判

**Borderline，略偏 weak reject。** 核心理由：你们确实发现了一个可重复、部署相关的事实——真实推理内容会暴露局部参数编辑的不稳定性；也确实找到了一个能改变最终答案的链内因果操纵。但当前最强叙事把它进一步解释成“能力涌现的语义重推机制 + 通用修复”，这两步尚未被识别：现有证据仍可由“浅层编辑在长上下文中失势 + 对旧答案首词元施加全程词法约束”解释。

我作为拒稿人会给 borderline；作为合作者，我认为补对一个实验即可进入 accept 竞争区。

## B. 六个问题

### 1. 现象重要吗？

重要，但重要的是“编辑评测失真”，不是“思考竟然会恢复旧知识”本身。

强结论有四个：

- Qwen-32B 的生成式 ES drop 为 `0.106 [0.030,0.182]`，Llama-70B 为 `0.107 [0.032,0.182]`，两个高端 cell 独立排零。[results.json: capability (line 8)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:8)
- 这不是空 `<think></think>` wrapper 伪影：32B 的 RR 为 `B0=0`、固定无内容 B0P=`0.040`、真实 256-token 链 B1=`0.208`；B0→B1 ES drop=`0.130 [0.060,0.205]`。[results.json: f2 (line 1917)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:1917)
- 不是未编辑模型天然向旧答案漂移：32B base 的配对漂移为 `−0.020 [-0.080,+0.040]`，而 edited RR=`0.193`。[results.json: f1 (line 819)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:819)
- 不是 ROME 单点假象：MEMIT-14B ES drop=`0.090 [0.010,0.170]`，RR=`0.333 [0.250,0.426]`。[results.json: memit (line 2114)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:2114)

但 headline 的“约五分之一回退”是 loose 上界。32B 的 `RR=0.193`，严格 `RRs=0.092`；语义验证显示 loose RR precision 只有 `0.48`，RRs precision 为 `0.92`。[results.json: metric_validation (line 1711)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:1711) 因而真实 committed reversion 应被表述成约 `9%–19%` 的区间，而非精确的 19.3%。

正确零假设不只是“ES drop=0”，而是：

1. 相对未编辑 base，真实推理是否选择性损害编辑；
2. 相对等长、无语义推理的上下文，损害是否来自推理内容而非长上下文；
3. 在匹配 B0 编辑强度后，损害是否随独立测得的 reasoning capability 增长。

你们基本拒绝了第 1 个，部分拒绝了第 2 个，但还没有拒绝第 3 个；B0P 很短，并非 B3 等长 filler。

“capability-emergent”应降级。支持它的是 `es_drop` slope=`0.109 [0.036,0.175]`；RR slope CI 含零、`p=.052`，raw CLR 虽强，但扣除 base CLR 后 net-CLR slope=`0.0535 [-0.0083,0.1496]` 含零。[results.json: emergence (line 1192)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:1192) [results.json: cap3 (line 1577)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:1577)

而且统计自变量只在 6 个模型 cell 上变化。代码先形成 `(params,family,case_id)` 多尺度行，却在 family 内逐行重采样，没有把同一个 case 跨尺度作为整块保留；K 又只有 2。[percase_emergence.py (line 171)](/Users/whyu/GitProjects/why-aaai27/src/percase_emergence.py:171) [percase_emergence.py (line 343)](/Users/whyu/GitProjects/why-aaai27/src/percase_emergence.py:343) 这可以精确描述六个固定模型，却不能提供“模型能力总体规律”的 1194 个独立证据。

我的裁决：改称 **“size-associated high-end erosion across two R1-distilled families”**。它是可信现象；“capability-emergent”仍是骑线解释。

另一个 AIA 风险：CounterFact 中 `o_old` 通常是真事实，`o_new` 是反事实。模型“想回真相”在认识论上可能是好行为。你们证明的是安全干预/编辑控制通道不可靠，不是推理降低 truthfulness。

### 2. Novelty 真成立吗？

逐条看：

- **预算控制的 zero-vs-real-thinking 现象：成立，且是最强 novelty。** SCR/ReCoE 已观察真实生成和反思会破坏编辑，CRANE 已观察链拒斥编辑，ThinkEval 已研究多步泄漏；但你们加入了 F1/F2/F3、配对 ES drop、跨尺度量化和 MEMIT 复制，这是从案例升级为受控现象。[related_work.md (line 8)](/Users/whyu/GitProjects/why-aaai27/paper/related_work.md:8)
- **非擦除：不成立为独立 novelty。** Superficial Editing 已把“旧知识未被抹掉、编辑只是表层覆盖”作为核心结论。[related_work.md (line 9)](/Users/whyu/GitProjects/why-aaai27/paper/related_work.md:9) 你们最多贡献“它在 native R1 链中如何表现”的实例。
- **链内因果修复：有局部 novelty，但尚未成为通用方法贡献。** DISCO 已有 training-free 解码修复；你们的独特性是只动 think span、答案段不动，并有符号/剂量/对照电池。[related_work.md (line 10)](/Users/whyu/GitProjects/why-aaai27/paper/related_work.md:10) 但现实现是全链每步压旧答案的首词元，容易被评价为 lexical censor。
- **capability-emergent：检索意义上独有，证据意义上未钉死。** 它是“没人做过”，但还不是“你们证明了”。

最容易被说“已有”的是非擦除；最容易被说“已知结果的 20 行重组”的是修复。

当前数据支持的最强真故事不是“我们首次发现重推机制”，而是：

> 局部知识编辑在直接读出时有效，但真实 deliberation 会重新开放预训练旧答案的竞争通道；这个失败在高端 checkpoint 上达到可观量级，而旧答案的链内词法通道是一个可因果操纵的瓶颈。

### 3. 机理故事严不严？

没有闭环。真正因果的部分比论文声称的更窄。

1. **Logit-lens 是安装 sanity，不是回退机理。**
    
    代码重新施加编辑、喂裸 cloze，只比较 `o_new` 与 `o_old` 的首 subtoken；`intact` 仅定义为 `gap[-1] > 0`，并不等于完整 `o_new` 是 top-1 答案。[logit_lens.py (line 51)](/Users/whyu/GitProjects/why-aaai27/src/logit_lens.py:51) [logit_lens.py (line 104)](/Users/whyu/GitProjects/why-aaai27/src/logit_lens.py:104)
    
    更根本地，推理前向不会修改权重。“解码把 ROME 权重擦掉”本来就不是合理零假设。decoder 7–11 在 edit layer 12 上游仍偏好旧答案，也是局部编辑的预期签名，不证明真实链“读取了该 substrate”。权威结果本身也承认无对照、无 CI、近恒真设计。[results.json: logit-lens (line 2359)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:2359)
    
2. **Taxonomy 是有价值的描述，不是因果。**
    
    扩池后 50 条 committed reversions 中 Bridge 68%、Recall 22%、RO 8%、Associative 2%，κ=`0.790`。[results.json: taxonomy (line 1118)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:1118) 这说明多数链能给出可见的推导或回忆路径；但 Bridge 定义包含词源线索、类别、虚构中介等极宽范围，无法区分真实知识重构与事后 rationalization。
    
3. **M1 是最明显的“相关当因果”。**
    
    CLR0 baseline 层的 `N_RR=0`，没有下降空间；CLR1 层的 `N_RR=0.489`。所以“修复效应集中 CLR1”很大程度是地板效应。[results.json: M1 (line 597)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:597)
    
    2×2 又把 treatment 后的 CLR drop 当 mediator，而 suppressor机械地直接改变 CLR；代码只是比较 `(CLR dropped) × (RR fixed)`，没有随机化 mediator，也没有控制处理导致的其他链变化。[m1_clrsplit.py (line 47)](/Users/whyu/GitProjects/why-aaai27/src/m1_clrsplit.py:47) 这不是因果中介分析。
    
4. **W-B 反而提供了一个重要反例。**
    
    概念方向干预相对 shuffle 显著降低 CLR `−0.078 [-0.148,-0.008]`，但 RR `−0.024 [-0.098,+0.049]`、ES `+0.078 [-0.016,+0.172]` 均含零。[results.json: W-B (line 2169)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:2169) 即“少说旧答案”不必然“少回退”。这直接否定了把表面 CLR 当充分 mediator 的简单版本。
    

真正成立的因果命题是：

> 在 think span 中降低旧答案相关首词元的可用性，会改变链分布并改善最终答案。

尚未成立的是：

> 自然回退由语义重推 `o_old` 经文本链中介而发生。

更简单的替代解释是：ROME 只强化窄 cloze readout；长上下文使该局部更新的相对影响下降。全链词元 penalty 改变了上下文分布，最终答案随新上下文改变，无需假定“语义重推路径已被识别”。

### 4. 修复有价值还是 trivial？

作为因果探针，有价值；作为部署修复，目前偏玩具。

强处非常明确：32B 的 T−C 为 ES `+0.121 [0.051,0.192]`、RR `−0.094 [-0.160,-0.028]`、RRs `−0.057 [-0.113,-0.009]`；14B 四指标也全排零，ES `+0.135`、RR `−0.101`。[results.json: T−C (line 382)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:382) [results.json: 14B (line 635)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:635) 20 行代码本身不是问题；简单干预也能是好科学。

问题在它实际上做了什么：

- 对所有安全 alias 的**首 token ID**，在链的每一步都减固定 penalty，而非只在完整 `o_old` 序列即将生成时抑制。[suppress.py (line 15)](/Users/whyu/GitProjects/why-aaai27/src/suppress.py:15) [suppress.py (line 39)](/Users/whyu/GitProjects/why-aaai27/src/suppress.py:39) 这会同时打击共享该 subtoken 的其他表达。
- P 臂按字符长度/经验字符串频率匹配，但干预变量是 tokenizer 首 token；两者没有真正匹配。[placebo_donor.py (line 20)](/Users/whyu/GitProjects/why-aaai27/src/placebo_donor.py:20)
- C 臂是随机抽一个同 relation 的答案，并未验证它在当前链中的 baseline logit 或出现概率真的“强”。[placebo_donor.py (line 55)](/Users/whyu/GitProjects/why-aaai27/src/placebo_donor.py:55)
- suppressor 默认只作用于 `efficacy` probe，paraphrase 和 locality probe 根本没有开启干预。[edit_loop.py (line 148)](/Users/whyu/GitProjects/why-aaai27/src/edit_loop.py:148) 因而 `Loc 0.958→0.964` 不是“修复开启后的 locality”。
- Loc 本身只检查邻域回答是否没有出现 `o_new`，并不检查邻域事实是否仍答对；输出垃圾同样可能算 Loc=1。[metrics.py (line 117)](/Users/whyu/GitProjects/why-aaai27/src/metrics.py:117) [metrics.py (line 171)](/Users/whyu/GitProjects/why-aaai27/src/metrics.py:171)
- Genbench 的 `single` 模式只取数据文件第一条 `o_old` 后就停止，即主要测试“压 French”对数学题是否有影响，而不是对 200 种 suppressor 的外推。[genbench.py (line 23)](/Users/whyu/GitProjects/why-aaai27/src/genbench.py:23) 完整 GSM8K/MATH n 只减少题目采样误差，不减少 target-token 间的不确定性；而 B26 的等价性也未认证。[results.json: B26 (line 720)](/Users/whyu/GitProjects/why-aaai27/paper/results.json:720)

因此应定位成 **mechanistic intervention / proof-of-concept mitigation**，不能称通用、deployment-ready repair。修复目前只在 Qwen 14B/32B、ROME、CounterFact、直接问法上成立；MEMIT 只复制了现象，没有复制修复。

### 5. 最大的瘸腿是哪一处？

**唯一最大瘸腿：没有识别出“语义链中介”，只识别出了“旧答案词法约束会改变答案”。**

这是比 K=2 或覆盖面更致命的原因：

- capability 可以诚实降为 supporting trend，32B/70B/MEMIT 的现象仍然成立；
- 单编辑器/数据集可以作为 proof-of-concept limitation；
- 但若语义机理不成立，MECH-led novelty 会退化成：SCR 已知现象 + Superficial Editing 已知非擦除 + 一个精确目标已知的 lexical penalty。

这正是最可能把论文压到 borderline/weak reject 的组合拳。

### 6. 下一个 solid 实验

排序为：**D1 语义中介 > D2 匹配 parent–distill 对照 > D3 修复外推与真实安全审计**。具体如下。

## C. 瘸腿排序

1. **机理识别失败风险**：词法 suppressor 的成功尚不能证明语义重推中介；logit-lens/M1 也没有补上。
2. **capability 推断底盘**：参数量代理、6 个模型 cell、2 个族、不同编辑超参与 b0ok 选择总体；能支持固定模型描述，不能支持强 emergence。
3. **修复外部效度与安全测量**：ROME/CF/Qwen/direct-only；paraphrase 未开启干预，Loc 检查空泛，genbench 只覆盖单个 suppressor target。

## D. 下一步 solid 实验

### 1. 词法正交的 chain-replay / counterfactual mediation

假设：最终答案跟随链的**语义内容**，而非仅跟随是否允许生成 `o_old` 的字面 token。

设计：

- 取 32B、B0 成功的 80–100 个 case，编辑权重固定。
- 每 case 构造四个长度、风格匹配的 think prefix：
    - 原生回退链；
    - `OLD-semantic`：通过 bridge 推出旧事实，但不得出现 `o_old`、任何 alias 或其被 suppress 的 token；
    - `NEW-semantic`：同样结构地推到 `o_new`；
    - matched sham：无关但等长的推理。
- 所有臂均**关闭 suppressor**，答案段正常解码；主端点为 OLD-semantic vs NEW-semantic 的 committed old/new 差，并用中性语义判官验证链含义。
- 再交叉两个表面形式，检验同一语义换词后效应是否保持。

预期：

- 若 OLD-semantic 仍显著诱导旧答案、NEW-semantic 拉回新答案，机理从 lexical gate 升级为真正的链级语义中介，论文可到 accept。
- 若只有含字面 `o_old` 的链有效，当前贡献应降为 lexical decoding control。

成本：工程 1–2 天；32B 只生成短答案，8×H200 半天内可完成，赶 7/28 很现实。

### 2. 7B parent–distill 匹配对照，钉死“reasoning capability”

假设：侵蚀来自 R1 reasoning post-training，而非任意长上下文或弱编辑。

设计：

- 同源同规模对比 `Qwen2.5-Math-7B` 与 `R1-Distill-Qwen-7B`。
    
- 各自调层使 B0 ES、locality 和 cloze `log p(o_new)-log p(o_old)` margin 分布匹配。
    
- 三臂：直接回答、256-token 等长无语义 filler、256-token 真实 CoT。
    
- 主估计量是 difference-in-differences：
    
    `[(edited real-CoT − edited filler) − (base real-CoT − base filler)]_R1`  
    减去同一量在 parent 上的值。
    

预期：

- R1 显著更强：首次把“native reasoning training 使编辑更脆”从参数量相关提升为接近因果的 novelty。
- parent 与 R1 相同：应撤“capability-emergent”，改成更一般的 context-sensitive shallow editing。

成本：7B 很便宜；工程约半天至一天，8×H100/H200 约 4–8 小时。

### 3. `ROME/MEMIT × direct/paraphrase × active-safety` 修复压力测试

假设：修复命中的是编辑后的旧事实竞争通道，而非 ROME/direct-prompt 特定轨迹。

设计：

- 固定 Qwen-14B，编辑器为 ROME 与 MEMIT；每个 n=100–200。
- 臂为 N/T/C；query 为 efficacy、两条 paraphrase。
- 明确把 suppressor 开到 paraphrase 和 locality probes。
- locality 改报真实 `LocAcc`：邻域问题是否仍答出其正确旧值，而非仅“不含 o_new”。
- 加一个小型诊断子臂：当前 first-token penalty vs 完整序列/finite-state suppression，按 tokenizer 分词长度分层。

预期：

- 两编辑器、三种问法均有 T−C 改善且 active LocAcc 不降：修复从玩具升级为可发表的方法贡献。
- 仅 ROME/direct/first-token 有效：保留为机理探针，删除通用修复措辞。

成本：复用现成 14B/MEMIT harness；工程约 1 天，8×H200 约 8–16 小时。

不建议再做：

- 更多同族规模点；
- 更多 taxonomy/J-lens 描述；
- 更多 α 点；
- 继续给“压 French”的 GSM8K/MATH 增 n；
- 只跑一个 zsRE 现象复制而不同时测试修复或机制。

这些不会改变当前核心裁决。

## E. 如果只能做一件事

**做“无字面 `o_old` 的语义旧链 vs 语义新链”的 counterfactual chain replay；它是唯一能把这篇从“已知现象 + 有效 lexical patch”升级为“真正识别了推理链因果机制”的实验。**