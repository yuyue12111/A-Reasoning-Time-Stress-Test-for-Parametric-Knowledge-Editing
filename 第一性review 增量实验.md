# 还有哪些"有增量"的实验(严格定义:某个结果能翻转/杀死一条 claim 或补 load-bearing 缺口)

先说结论:**真正有增量的实验里,最狠的不是我上轮说的 E-CHAINSUB——而是"这现象到底是不是编辑特异的"这一层。盘上已有一个反向证据(未编辑基座随思考自己就往 o_old 漂 +0.08),它可能把整个"thinking undoes _editing_"打成"thinking destabilizes _answers_"。** 下面按 威胁承重 × 死线可完成 排。零卡的能进 7/20。

---

## 🥇 第一梯队 · 攻"现象根基"(最高威胁,大多便宜,此前没人正面打)

**F1 · 无编辑 thinking-tax 基线(单点最高杠杆)** — _头牌 · 7/20(7B/14B 部分在盘)/32B 7/27 · ~40 LOC + 数 H200-h_

- 设计:`base_probe.py`(已存在,无编辑、无 mom2)在**同一批 200 CF case** 上跑 B0/B3,32B(`WHYAAAI_DTYPE=float32` 防 Hopper NaN),同口径 `metrics.hit`/`_without_subject`。报**编辑 ES 降幅 − 基座 thinking-drift** 的 effect-above-control margin。
- **kill**:未编辑基座随思考也往 o_old 漂,幅度接近编辑 RR≈0.19 → "越想越退**编辑**"塌成"越想答案越不稳(有没有编辑都一样)",RR/ES 降幅大部分是基座属性换了个名。**confirm**:基座稳(drift ≪ 0.19)→ 编辑特异性坐实,下游全部更稳。
- **为什么 kill 真可能(不是空想)**:`results.json base_probe` 里 **7B 未编辑基座 answer_old 0.59→0.67(+0.08)、chain_old_b3=0.755**——思考已经在无编辑动力学下把答案往 o_old 拉了。RR 才 ~0.19,基座只要有 ~0.1 的自然漂移,编辑特异残差就被吃掉大半。**这个混淆盘上就有,不是假设。**
- 这条**超过 E-CHAINSUB**:E-CHAINSUB 精修一个"回退经链重推"的机理,但它默认现象是编辑特异的;F1 问的是**该不该有这个机理**。reviewer#2 会先跑 F1。

**F2 · ZEROTHINK 模板去混淆** — _头牌 · 7/20(n=100)· ~15 LOC + 4–5 H200-h_

- 设计:B0 现在是空 `<think></think>` 模板(`think_budget.py:23`)。加两臂:B0′=`LESSTHINK_CANNED`(代码里已有、没用)、B0″=最小自然链(复用 B1,CAP=32)。用 B0′ 重锚 ES 降幅与 b0ok 分母。
- **kill**:B0 空块 ES ≫ B0′/B0″ → 整个"税"部分是"退化零推理捷径 vs 任何真推理"的差=模板伪影。**为什么可能**:空块强制无 deliberation 直接解码,恰好偏向顶层占优的编辑(g64=11.6);任何真推理(哪怕一句)就可能触发部分重推(中层 g8/g12<0 预测短链也漏)→ B0′ 掉到 B0 和 B3 之间,抹平头牌差。

**F3 · 温度/seed 鲁棒性(声称做了却零上报)** — _头牌级(标"defense"但能 kill)· 7/20 sanity/7/27 全 · ~0 LOC_

- 设计:采样路径 `think_budget.py:58–71` + `metrics.score(decode='sample')` **全建好**,但 `results.json` **零个采样数**;draft §3.3 却写"0.6×3 sampling arm for robustness"。32B B0/B3 跑 temp=0.6 × seed{0,1,2},报 ES 降幅/RR/CLR 的 per-case CI。
- **kill**:采样下 RR/ES 降幅塌向零或反号 → 回退是单条贪心的脆性。**为什么可能**:RR≈0.19 是单条确定轨迹上的小效应,中层 gap 只有 −0.25~−0.35 近平局,微扰即翻;且 b0ok 本身贪心定义。**这是"声称做了但没报"的臂,审稿人必点。**

---

## 🥈 第二梯队 · 攻机理/修复头牌(多为零卡,7/20 可落)

**M1 · E-CLRZERO-SPLIT:按基线 CLR 分层修复效应** — _头牌 · 7/20 · 零卡再分析_

- 把已跑的 N/T sup_battery 按 baseline-N 每 case **CLR=1 vs CLR=0** 分层,分别重算 T−N 的 RR/ES。机理预测:效应应**集中在 CLR=1、在 CLR=0 消失**。
- **kill**:CLR=0 case(链从没提 o_old,占池 ~45%,headline CLR=0.545)上 RR 降幅**相当**→ 修复不是靠"堵链内重推"→ 直接杀"in-chain re-derivation **governs** the answer"。**为什么可能**:`suppress.py` 每一步都减 penalty、不管 o_old 有没有质量,贪心可能只因 o_old 被压低就改道。零 GPU(用在盘 T n=198 + N per-case)。**修复因果故事最便宜的 kill。**
- 更狠(红队补):在 N/T 上做 per-case **2×2(CLR 降了吗 × RR 降了吗)**中介——若 RR 在"CLR 没降"的 case 上也改善,答案改善与链内容**解耦**,同样杀。

**M2 · 答案位动态 logit-lens(跑完真链后)+ held 对照** — _头牌 · 7/27–camera-ready · 新解码路径_

- 现 `logit_lens.py:107–116` 探**裸 cloze、静态权重**(恒真)。改测**真回退链跑完后、答案起始位**的隐状态 gap——这是个**全新张量**。
- **kill**:答案位顶层 gap 转负 → 在**真正决定答案的位置**上编辑并非"intact",机理从"绕过完好编辑"翻成"in-context override"。这是我上轮 E-CHAINSUB 的**观察版**(便宜、不用注入链)。

**M3 · 中性 prompt 重跑 taxonomy 判官** — _防御 · 7/20 · 零卡 ~720 calls_

- `chain_classify.py:25` 仍灌"edit STILL INSTALLED…ROUTING AROUND…NOT recalling decayed weights"(depth-plan 点名要删、只删了 `revert_judge.py`)。中性 prompt 重判 n=19。
- **kill**:出现非零 Recall → falsify abstract 的"90% bridge, no flat recall"。n=4/5/10 极小,几条改判就翻。**打在 abstract 一句话上、零卡、最快。**

**M4 · "强竞争者"placebo 第 5 臂(C)** — _防御 · 7/27 · ~30 LOC + 1 臂_

- 现 placebo 是**惰性**词(`placebo_donor.py` 取别 case 的 o_old,从不取 o_new);压**同关系的强错误答案**(CF 带 relation_id 可分组)。
- **kill**:C−N ≈ T−N → 修复是"压任何强竞争者"的通用效应,T−P(惰性 floor)是弱证 → 杀 o_old 特异性(论文自认的残余)。

**M5 · 反思标记抑制臂** — _头牌级 · 7/27 · ~20–30 LOC + 2–4 H200-h_

- 压"wait/actually/but"(reflect_before_old 在 32B 回退中 9/10 为真)而非 o_old 内容,报 R−P。
- **kill**:答案照样修好 → 是**override 动作**而非 o_old 内容驱动回退 → 把"re-derivation"窄化。零卡前奏:把现有 T−P 按 `reflect_before_old`/`contests_edit` 分层。

---

## 🥉 第三梯队 · 攻 capability-emergent(全零卡,7/20)

**Cap1 · E-CHAINLEN-KILL** — _头牌 · 7/20 · 零卡 ~50 LOC_:唯一存活的 CLR slope 用的是**空白分词** chain_len(`percase_emergence.py:217`),而 CLR 是近饱和二值(held 14/14=1.00)。换真 tokenizer chain_len + 二次项 + **CLR-每-token 密度**,slope CI 可能盖零 → "capability-emergent"塌成"大模型链更长、按概率更常提 o_old"。

**Cap2 · E-CLR-DISCRIMINANT** — _头牌 · 7/20 · 零卡_:把 CLR 门到**真回退**(CLR*)重测 slope。CLR* slope 变平而 raw-CLR slope 仍升 → "啰嗦随能力涨",不是 erosion。

**Cap3 · base-knowledge 混淆(红队补)** — _头牌级 · 便宜_:6 尺度都跑 base_probe,把 edited-CLR slope 控制 base-recall-of-o_old。若 slope 塌 → "CLR 随能力涨"= "大模型本来就更知道 o_old"(知识可得性,非 erosion)。比 chain-length 更致命。

---

## 度量 & why & 部署(各留一个真 kill)

- **V1 · E-CLR-JUDGE**(_头牌 · 7/20 · 廉价判官_):κ=0.836 **只验了答案级 RRs,从没验 CoT scorer CLR**;而 CLR 是唯一存活的 erosion 指标。`metrics.py:149` `hit(cot,o_old)` **无极性检查**→"it is **not** French but Bolton"记 CLR+。中性判官若确认大量"被否定/顺带提及"假阳 → 裂 emergence 的测量地基。~40 CoT 判官调用。(红队补 V2:把 κ 的"neither"判为**不一致**重算,若掉→0.836 是被 easy TN 撑的,零判官调用。)
- **K1 · 32B base_probe(聚合)**(_防御 · 7/20 · 便宜_):abstract 的 0.59 **是 7B 数**给 32B 头牌用=误引,必补。**K2 · E-KC-NOPRIOR**(_头牌 · camera-ready_):在**基座不知道 o_old**(recall≈0)的事实上,编辑还回退吗?回退→"weights still hold the prior"被 falsify=**confabulation 非 conflict**。Recall=0/19 + Bridge-via-spelling 使 kill 真可能;先用 32B base 列分层现有 200,不够再补编辑臂。
- **G1 · E-CONDC**(_头牌 · 8B 先做可 7/20 · ~40 LOC,路径已通_):在 **o_old 是合法推理中间步**的多跳编辑 query 上开抑制器(precondition-c 盲区,draft §7:295 自认 [pending])。hop-ES 掉→杀"zero collateral by construction"(部署门看不到的编辑-query 侧伤害)。
  
  ## 明确 DROP(结果预定/非增量 —— 别做)

|实验|为什么不是增量|
|---|---|
|**E-UNIONTHINK**(union+scope=think 部署)|被 union+all(−0.15)与 single+think(+0.005)**先验夹住**;安全 claim 是 by-construction,两种结果都不翻|
|**E-PROMPTEDCOT**(prompted-CoT vs native-R1)|draft §7:286 **双向预认**、贡献已 firewall;任何结果只碰已弃 framing;且 LOC 最贵|
|**copy-from-subject / prompt-mask**(rival a)|`overlap_subject=0/10`、`alias_gap=0/10`@32B —— 主体复制路已死,confirm 近必然|
|**E-CANDIDATE-COUNT**(多数投票 rival)|判官池选择偏倚(¬clr≈0);且方向已被 held clr(1.00)>reverted(0.895)反证|
|**E-INFLATE-DIRECTION**(~2× 去污方向审计)|删的按定义就是 <4 字短码/子词,confirm 近必然,加支持点非 kill|
|**E-FALSENEG**(词边界漏真回退)|语言/国名整词永远保留、只掉 fr/es/it;且轻度 FN 只把真值推向 RR=**落在已报 [RRs,RR] 括号内**|
|**E-POSITION-SEGMENT**(早/晚链分段压)|只**收窄**机理、翻不了充分性;却吃掉唯一的新解码路径 LOC|
|**更多编辑器/数据集/尺度/seed**|门票,不加分;一个 MEMIT 点只作便宜保险、非信息增量|
|**single-fact 部署门扩 n**|by-construction 恒真 null,扩 n 不产信息|

## 单点最高杠杆

**F1(无编辑 thinking-tax 基线)。** 改了我上轮的答案(E-CHAINSUB)。理由:E-CHAINSUB 精修一个假定为真的机理;F1 问的是**这机理该不该存在**——盘上 7B 基座 +0.08 的自然 o_old 漂移是一个**已经指向坏结果的在手证据**,kill 真可能、且便宜(~40 LOC、数 H200-h、7B/14B 部分已在盘)。结果二选一都极高信息量:基座漂移≈编辑降幅 → 撼动标题 claim;基座稳(≪0.19)→ 编辑特异性坐实、每条下游都更硬。**7/20 前若只做一件 = F1;其次 M1(零卡杀修复因果)+ Cap1/Cap2(零卡杀 capability)+ M3/V1(零卡硬化机理与度量)。**

## 一句话综合(按"杀不掉的原因"分三类)

|类别|条目|不限时能杀吗|
|---|---|---|
|**资源限**(工程 LOC / 墙钟)|#1 E-CHAINSUB、#3 自然链 patching|**能**——建好 harness、跑大 n 即可(#3 最干净、on-policy;#1 是 off-policy 版)|
|**可识别性限**(结构混淆)|#2 匹配对(编辑装配混淆)|**能,但时间不够**——必须额外"等化编辑装配"重设计,否则混淆与时间无关地留着|
|**逻辑限**(无可证伪靶)|#4 native-R1 排他性|**不能**——除非先把 scope 词改成"必要性"断言;否则任何结果都翻不了被辩护的 claim|

以上为claude。

