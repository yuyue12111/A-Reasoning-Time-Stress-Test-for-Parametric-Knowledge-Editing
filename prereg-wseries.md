# W 系列预注册(v1.0,2026-07-03 深夜)—— workspace 方法论进口三实验

**来源**:红队 workflow `w4cxg65vd`(4 审查面 → lead 综合;全文存 task output,本文件=**约束性冻结版**)。
**冻结纪律**:本文件 + W 系列代码在跑前 commit,prereg 记 commit hash;**跑后任何端点改动 → 该结果自动降 camera-ready**。
**地位**:W 系列=加法臂非承重墙(plan v1.60⑤);任何撤退裁决不影响写作窗(7/8 解冻/7/18 abstract/7/25 全文冻结)。
**排程**:代码+prereg 冻结 7/8 24:00 → W-A 跑 7/8–7/9 → W-B pilot 7/9、确证 7/10 → 分析 7/11–7/13 → **7/14 内审裁决**。

## 0 全局约定(冻结)

- 模型 R1-Distill-Qwen-32B / ROME layer-12 / 单条编辑协议 / B3 greedy / `WHYAAAI_DTYPE=float32`(H200)。
- **层索引**:`hidden_states[0]`=embedding,`hs[k]`=decoder 层 k−1 输出;**编辑层 12 ↔ hs[13]**;图轴/文字统一 decoder 层号;转换函数单测锁死。(现版 `logit_lens.py:110-120` 拿 hs 索引当层号,off-by-one,须修。)
- **铁律:永不跨层比裸 logit**。一切端点=层内位置内 **distractor 校准 z**:z(o_old)=(logit(o_old)−mean(logit(d₁..₂₀)))/std;20 个同 relation 干扰宾语(CF 同关系答案池,排 o_old/o_new/别名,首 token 无歧义,同类目)。
  **【冒烟修正(7/7,冻结前;理由记录)】**歧义判据只看**带前导空格变体**的首 token(正文自然形)——首版对无空格小写变体也判,BPE 短首片一票否决了大半候选(实测 151/200 case 同 relation 池短缺)。同 relation 仍不足 20 → **跨 relation 频率回填补满 20 并打标**(`_stats_n_same_relation` 逐 case 记同 relation 数);主分析全 case,`n_same_relation<10` 子集做敏感性(类目 priming 校准力弱者)。检测集(o_old 探针)不变仍用全变体。
- **只投影候选列**(~25 行 unembedding);全词表 rank 仅小样本描述图(k∈{1,5,50}),不做端点。
- **探针 token 集**(修 `first_tok` 单点简并):{o_old+全别名(**不做 ≥4 字符过滤**,与 metrics 判分口径注释区分)}×{±前导空格×首字母大小写} 首 token 取 max;o_old 首 token 与链中其它词共享/高频通用词片 → ambiguous 标记,主分析剔除,含/不含两版敏感性。
- 一切统计 **case 级**(位置级 ~5×10⁵/case 读数=伪重复,不做检验);配对 bootstrap 10k;跨 case BH-FDR q<0.05。
- **CONSORT 流水表强制**:入组→各门剔除计数→分析 n,逐 case 入 jsonl。

## 1 效度门(先于一切端点)

| 门 | 内容 | 阈值 |
|---|---|---|
| G1 模板保真 | teacher-force 前缀逐字节复刻产链模板(U+FF5C 全角竖线、WAIT 注入、cap 截断) | 逐字节 |
| G2 重编辑保真 | 重编辑后 B0 greedy 复现 b0ok | 通过率 ≥95%,失败剔除报数 |
| G3 回放保真 | teacher-forced 非强制位 argmax 与存盘链一致率 | case ≥95% 入组(分布全报;≥99% 子集敏感性) |
| G4 灵敏度-base | 未编辑基座 teacher-force,o_old 校准 max-stat 阳性率 | ≥70%,不过则 null 不可解释 |
| G5 灵敏度-premention | CLR1 链首提及前窗 [m−20,m−1] 检出率 | ≥80% PASS;<50% **W-A 作废**;50–80% 全线 suggestive |
| G6 环境同一性(W-B) | 复用 N/T 臂 `_meta` 逐项 diff(git hash/dtype/NO_BOS/模型路径/case 集/hparams) | 不合→同环境重跑 N |
| G7 方向质量(W-B) | **个体模板方向**两两 cos(pair_cos)≥0.6 | 剔除率 >20% → **方向法不成立,W-B 停** |

> **G7 修正(7/7,冻结前;理由)**:原写"留一模板方向两两 cos"→ 实现为 8 选 7 **均值**方向的 cos,因高度重叠恒≈0.95+、几乎不判别(冒烟 g7_fail=0/25 即此假象)。改判**个体模板方向**(各用不同中性实体、有真变异)的两两 cos 均值 `pair_cos`——random≈0,≥0.6 才证"o_old 概念方向主导模板/实体噪声"。loo_cos 降级为仅报告。阈值 0.6 在冻结前看 pair_cos 实测 median 定夺(median 过低=概念方向法本身弱=W-B 的诚实负结果)。

## 2 W-A · 无声工作空间泄漏(链位置×逐层 lens)

**位置排除(token-id 级,宽表面形集;检测用严判据)**:①o_old 任一 surface form 的 token 位;②每次出现前 1 位(预测位);③无声分析中 o_old 首 token id 出现后的**全部后缀**(防 induction/copy 头);④**o_old⊂subject 的 case 整条剔除**;⑤o_old/主体提及 ±10 token 及题面复述区;⑥提及位在原文上算(排除式定位,offset_mapping 做 char→token)。o_new 邻近不剔除、由同类目 distractor 校准。

**spike 判据(看数据前冻结)**:层带由 10 个 calibration case 定(排除出推断集,fallback=decoder 16–48);case 单标量 S_max=带×窗合格位 max z;**零分布=20 distractor 轮流当伪目标算同一 max-stat**,case 阳性=o_old 超全部 20 个(精确 p=1/21≈0.048)。

- **A1 无声表征存在性**:总体=B3 全体 **string-CLR0(宽表面形集)∩ LLM-judge-clean** 链(judge=预注册 prompt 判"是否语义指涉 o_old";没跑判官只许写 no string-level trace)。判据=BH-FDR q<0.05 显著 case ≥3 **且**组阳性率 binomial 单侧 >4.8% + Wilson CI。null 只报灵敏度标定下的 Wilson 上界,**禁写"从不无声"**。claim=「言语化是门控而非存在性开关」。
  **【n 回填(wa_census 2026-07-03,32B ROME×cf200 greedy)】**n_paired=151(subject-overlap 整条剔除 47);b0ok=109/回退=17/held=92;**A1 主总体 CLR0_wide=35**(∩held 31/∩非b0ok 4);**CLR0_wide∩回退=0 → 按 prereg 宣告 traceless 回退本数据不可答(干净)**——且此即可报事实:最宽口径下 0/17 回退无痕,necessity 行为学底座加强(入 results.json `rq2_taxonomy.wide_census_traceless`)。A2 组:回退∩CLR1_wide n=17 vs **held∩CLR1_wide n=61**(比原估 14 大;taxonomy-judged 14 作标注子集);calibration 10 case 从 held∩CLR1 取(排除出推断集)。paper 口径 CLR0=87 vs 宽口径 35(宽集必要性自证)。
- **A2 anticipatory representation(纯描述,禁 planning/预谋因果措辞)**:回退 CLR1(≈17)vs held(14);前缀窗截止 o_old 首 token 出现位**前 5 token**;Mann-Whitney 回退>held 单侧 α=0.05 + AUC CI;lead-time 中位>0 Wilcoxon **且** distractor 无 anticipation(特异性)。
- **A3 edited−base 配对估计量(非检验)**:同链 Δz case 中位+CI;解读表钉死:edited≈base→关联在编辑通路外完好(绕过说);edited≪base→编辑广泛压制表征(回退需另释)。**base=ceiling 参照,不是 null**(base 里 o_old 是真事实)。
- **A4 编辑仍 installed(非 ROME 优化位)**:主体末 token/链末 token/答案槽的逐层 gap(o_new−o_old);回退链答案槽顶层 o_new 胜 ≥80%。
- **A5 桥实体(次)**:桥实体 token 位 z(o_old) vs 同链随机内容词位,配对 Wilcoxon;显著→与 taxonomy Bridge=14/17 焊接。
- **A6 回退 vs held 组间(仅探索)**:文本系统性不同=混淆;Fisher,差 ≥30pp 且 p<.05 才评论。

## 3 W-B · 表征级抑制修复(steer)

- **方向(致命修正)**:v_old=mean h(含 o_old 语境)−mean h(**匹配中性语境**=同模板换第三方实体,无 o_old 无 o_new)。**禁 o_old-vs-o_new 差**(−α·v≡把答案写进残差流,中介 claim 一句被杀)。**对 W_U[o_new 首 tok] 正交化为主版本**;仅未正交化有效 → claim 死,如实记录。per-case 为唯一主臂(≥8 对模板,base 模型抽一次全臂复用,span=实体+后 3 token);全局池化方向降探索。
- **注入**:site=mlp;层带=W-A onset 带,fallback=decoder 20–44;α 以**层中位残差范数百分比**表达,pilot(n=30)扫 {1%,2%,5%},α\*=退化链率<5% 且 LocAcc 掉<5pt 的最大档,冻结进确证。
- **scope=think 增量解码(致命修正,`steer.py:52` 静默全局注入)**:①`generate_with_budget` 加 steerer 参数,只在链生成 g() 包 Steerer;②`steer.py` 加 `on_mismatch∈{inject,skip,error}`,禁静默 fallback;③`test_steer.py` 补 seq=1 步行为 + 答案段零 hook 两单测;④答案段 g() 前断言 `len(_handles)==0` 进日志;⑤裁决前人工抽查 10 条 S 臂生成。
- **臂**:N/T(复用,经 G6)/ **S**(−α\*·v̂_old)/ **P_shuf**(跨 case derangement 换向:真概念错 case,同范数同 α\* 同带=M4 C 臂的表征级同构);可选 S+(+α\*,n=100,符号对照)。n=200/臂(爆则 150,优先保 S/P_shuf)。
- **伤害端点(致命修正:Loc 对概念抑制全盲)**:**LocAcc=hit(邻域答案,o_old,aliases) 共主伤害端点**(CF 邻域真答案恰=o_old);S 臂 locality/para **干预开(主报)+干预关(下界)**两版。
- 端点:**B1 主**=S−P_shuf 的 RR@B3 配对差 CI 全<0 → 概念特异修复成立;**B2 共主**=LocAcc(N)−LocAcc(S,开) 点估<0.05 且 CI 上界<0.10;B3 次=S−N RR/RRs CI<0、ES CI>0+链长比/退化率;B4 符号=S+−N RR 点估>0;**B5 机理次**=`m1_clrsplit` 2×2 S vs N 的 RRfix|CLR-未降(n≥8 且 ≥0.25 → 概念通路超越字面 token-gate);B6 探索不裁决。
- **禁**:T vs S 效应量跨模态比较(logit penalty vs hidden α 量纲不可比,只许诚实脚注)。

## 4 W-C · 点写 vs 重推的读出几何(重铸版)

- **构念自命名 "L-onset"(logit-lens decoder-readability onset)**,首句硬 hedge(correlational readability proxy,非 J-lens 因果口径,tuned-lens 基向量漂移 caveat)。
- **「编辑层 12 vs band」单点对比、"编辑从没写进工作空间" 永久删除**(范畴错误:参数位置≠信息驻留;被自家 B23 顶层 o_new 可读打脸)。
- **C1 主**:配对 Δonset=onset(o_old|链内合格位,edited)−onset(o_new|cloze 末位,edited);onset=校准 z 首达 distractor-max 判据的 decoder 层;回退 n≥30,median>0 且配对 CI 排 0;held 同测报差。
- **C2 null 门**:频率匹配 control token + M4 strong 供体在同位集假 onset 率 <10% 且 o_old 显著早/强;**不过则 band 数字全禁入文**。
- **C3 因果附臂(唯一允许因果措辞;借 W-B 零新码)**:−α·v̂_old **in-band vs below-band** 两臂(等层数同 α 同 site,`steer.py` layers 现成),n≥100;in-band RR 降幅显著大于 below-band 且 Loc 不恶化;**方向反 → W-C 撤出正文**。
- C4 探索(浅点写签名,纯描述);C5 sanity(重编辑 cloze 复现 ≤5% 不一致;首 token 简并剔除;剔除后 n≥30);**C6 措辞端点**:禁词表 grep 逐条(见 §5)。

## 5 故事措辞纪律(与数据端点同等强制)

**三档**:可主张(C1+C2 过;因果半句仅 C3 过才加)/ suggest(C1+C2 过、C3 缺)/ **cite-as-frame**(任何档位;主语永远是 [cite],位置=Discussion+§2 一行立界)。
**全文禁词**:"we measured the workspace" / "the edit never enters the workspace" / 以我们数据为主语的 "ignition" / 移植他们模型的 onset 数字 / planning/premeditation(本轮)/ traceless(除非 A1 判官级门过)。
**§1 hook 维持现象主导**(红队砍掉 v1.60④ 原案的 workspace hook——借壳观感第一现场);§3–§5 写成零依赖该引用也自洽(F2/M1/B23/taxonomy 均先于 7/3 入库,commit 时间线自证独立性);workspace 映射只出现在 Discussion 一张对照表,每行标 correlational proxy;与 taxonomy 禁「矛盾」框架(两 construct 不同;若 lens 见无声表征 → 写成「表征常在→言语化是门控→行为回退」两段机制,加强主线)。

## 6 7/14 内审裁决表(摘要;全文见 w4cxg65vd output)

- **W-A 干净**=冻结零改动+G1–G3 过(G3 中位≥95%、≥80% case)+G4≥70%+G5≥80%+n 跑前算出按降级规则+敏感性两版同向+措辞对齐。G5<50% 或 G2<80% → 探针无效整体 camera-ready 不做部分报告;CLR0∩回退 n<5 按 prereg 声明不可答(**算干净**)。
- **W-B 干净**=B1 CI<0 + B2 伤害门 + scope 完整性(单测/断言/抽查)+ G7<20% 正交化为主 + 退化<5% + G6。S−N 显著但 S−P_shuf 不显著 → appendix,正文禁 mediation;实施门爆 → W-B 整体撤 camera-ready(不牵连 W-A/W-C)。
- **W-C 干净**=C1 排 0 同向 + C2 过 + C5 过 + 正文只报配对 Δonset 分布(零单点对比)+ C6 grep 过;C3 没跑完=封顶描述档(不算脏);方向反=撤出正文,Discussion 只留 cite-as-frame 一句。

## 7 砍掉(fatal 修不动,不做)

原版 traceless-回退检验(总体≈空)/「编辑层 vs band」对比及其图 / planning 因果读法 / "we measured the workspace"+ignition+全 J-lens 复制 / 跨层裸 logit 与绝对 onset 深度 / 全词表 rank 端点 / T-S 效应量比较 / CLR0∩回退 的 W-B 推断 / "从不无声" evidence-of-absence / 全局池化方向作主臂 / §1 workspace hook。

## 7.5 扩展节(v1.63 扩展梯;主推断仍=greedy 32B W-A,扩展各带自门)

- **G3s(采样链保真门,7/7 登记)**:采样链的 G3(argmax≥95%)口径错配(temp 0.6 下 argmax 一致率天然 ~0.88 且高=保真好)→ 采样链改判 **存盘 token ∈ teacher-forced top-20 ≥95%**(G3s)。greedy 链仍用 G3。首轮 s0 数据(g3_pass=0)按 G3s 重判,exploratory 标签待 G3s 通过率出来后定。
- 扩展梯顺序:W-A×F3 采样(s0/s1/s2)→ W-A×MEMIT-14B → W-A×14B ROME → W-A×Llama-8B;各自 CONSORT 独立,不与主 W-A 混池。
- **G5 操作化偏离(7/8 事后登记,诚实标注;硬伤4)**:冻结 prereg 的 spike 判据(§本文 line 37)把 premention 检出钉为 **distractor max-stat**——o_old 的「带×窗 max-z」须超全部 20 个 distractor(每个 distractor 同法算,精确 p=1/21≈0.048)。但实跑 `src/wa_main_analyze.py`(键 `G5_base_premention_z2`)用的是 **固定 z≥2 阈值**(band[16,48] 的 `zpre_max≥2`),并非 max-stat。git 考古:该操作化随分析脚本 + `G5=100%` 结果在**同一 commit 39ca2e9(2026-07-07 15:37)落地**,无更早冻结 z≥2 的记录 → **无法证明 z≥2 早于开盲**。故按 v1.61「操作化改动开盲前须写进 prereg」纪律【不】追认为 prereg 变体;W-A 报告句如实标 **"G5 operationalized post-hoc (fixed z≥2 variant; the frozen criterion was a distractor max-stat)"**,`G5=100%` 读作「z≥2 口径下基座前窗普遍可探到 o_old」而非 prereg-认证的灵敏度门。**降级**:§6 表「W-A 干净」里的「G5≥80%」从硬门降为 **suggestive 支持**(A2 null / A3 / G4 走各自冻结口径,不受牵连)。**7/14 裁决材料**:若要 prereg-正确的 max-stat G5,须回传 `results/wa/base_r*of8.jsonl`(含 per-distractor `z_pre_by_layer`)按 max-stat 重算;在此之前 G5 只作 suggestive。

## 8 跑前零卡必做(今天)

1. **普查 n(A1 的门)**:`src/wa_census.py` 在平台跑(数据在平台),出 string-CLR0(宽表面形集)全体/∩回退/∩held 的 n → 回填本文件 §2-A1。
2. diff sup_battery N/T 臂 `_meta` 环境同一性(G6 前置)。
3. 构建 distractor 池(20/case,同 relation)与探针 token 集(含 ambiguous 标记)→ data/wa_distractors.json 入库。
