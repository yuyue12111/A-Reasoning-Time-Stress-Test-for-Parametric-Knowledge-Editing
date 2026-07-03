# 终极写作前评审(2026-07-03,charter 执行版 · 经对抗校验修订 v2)

**评审立场**:独立评审员,与建设 session 上下文隔离。唯一标准=以 `paper/results.json` 现证据面、假设写作执行完美,距 solid/strong accept 的 AAAI-27 论文还有多远。

**证据基础与方法**:results.json 全文精读(1600 行逐块);plan.md v1.50–v1.57 精读+更早扫读;depth-plan.md 四轮全读;draft.md 300 行全读;三份前置第一性 review + rereview-round2 全读;src/ 代码口径审计;本地 results/ 产物交叉复算(实际在盘:`a3/`、`a3_neutral/`、`mh/`、`necessity.json`、`percase_map.json`;charter §2-9 提到的 percase_clean.json/cap3_clean.json/m1_clrsplit.json **不在本 worktree**,相关结论以 results.json 蒸馏层+原始判官票复核);联网查新(6/24→7/3 + 4 HIGH 近邻 + AAAI-27 CFP/AIA rubric,检索日 2026-07-03,外部事实按 charter 纪律须在引用前逐篇 WebFetch 复验)。初稿完成后经 5 路对抗校验(逐数核对/charter 合规/判档过宽质疑/判档过严质疑/盲区猎捕),本版已吸收其全部确认项;**两条承重新发现(★)经本人+3 名独立校验员共 4 次重算,全部成立**。

**死线口径声明**:仓内权威(charter §1/CLAUDE.md)=abstract **7/20**、全文 **7/27**(UTC-12)、补充材料 +3 天。本次联网在 aaai.org CFP 页读到 7/21/7/28/7/31(单源、未经用户亲核)。**本报告一切"来得及吗"判断按仓内 7/20/7/27 执行**;CFP 亲核本就是行政线待办,若坐实 7/21/7/28 则全表多一天余量、结论只松不紧。

---

## ★ 两个本报告首次提出、四次独立复算确认的事实

**★1|results.json 的 `_bonus_CORRECTED` 本身是错的。** 它声称 edited CLR 0.545 是"b0ok 门口径、与 base CLR 0.829 分母错配,故 0.545<0.829 是分母 artifact"。四枚钉子:①`metrics.py:155-157`:`clr[b] += hit(cot,o_old)`、分母 `n[b]` 按全部 efficacy 行累加,**无 b0ok 门**(b0ok 只门 rr/rrs,:161-164;percase_emergence.py:223 同样无门);②0.545 三处同源且全为无门口径(rq3.baseline.CLR / sup_battery N 臂 / percase 32B cell 0.5455=108/198);③plan.md:82 记录的真 CLR_b0ok(32B)≈**0.45**,与 0.545 数值可分辨;④Cap3 配对数据自证 gap 真实:edited CLR 逐尺度恒低 base ≈0.29–0.49、不随尺度扩。即两数分母同构、可直接比较,**真实情况是编辑态 CLR 系统性低于 base 底噪且 gap 平**——这既是 Cap3 退役 CLR 涌现的依据,也顺带削弱"链是回退唯一主渠道"的强表述。若照 `_bonus_CORRECTED` 写论文,会与 Cap3 表自相矛盾;审稿人核代码会发现"更正"比被更正的原文错得更深。**同一错误口径共写在三处**:`_bonus_CORRECTED`、`base_probe.32B._interp`、`_adversarial_verified.CLR_denominator_artifact`——修须三处同改。(附带:所引 base_probe.py:63 行号差一行,cot_old 在 :62。)

**★2|S1 中性重跑的记录值无法从原始判官票复算,且 off-by-one 机制已定位。** 按 `chain_classify.aggregate_votes` 规则对 `results/a3_neutral/verdicts_all.jsonl`(33 链)重算:pooled n_in_pop=**17**{Bridge 14, Recall 2, RO 1}、14b in-pop={cf_14588, cf_15396, cf_6933(均 Bridge), cf_3883(Recall)}=4;而 summary.json 与 results.json 记 **16**{13,2,1}、14b n=3——**恰少一条 14b Bridge**。机制(校验员定位,与观测精确吻合):cf_6933 同 case 跨尺度重复入池(14b=Bridge、32b=Recall),生成脚本疑按 case_id 去重、32b 记录顶掉 14b 行;s1_record.py 不在仓(commit 2e50c86 提及未落库)。连带:"population 3/18 flip"的分母 18 疑同为 unique-id 计数(真实 in-pop 行数 19),敏感性分母须写明口径。方向无害(真值 Bridge 14/17=82.4% > 报告 81.2%,结论不翻),但"唯一真源"上有不可复算数。**连带发现**:7B Fleiss κ 两口径打架——results.json 记 null 并称"全一类未定义",但票面并非全一类(labels_7b.jsonl cf_17023=[Bridge,Bridge,Associative]),本地 summary_7b.json/table_rq2.tex 按正确算法给 **−0.091**;null+"全一类"是错的,且 LaTeX 表已与 results.json 分叉。

---

## A 判档

**Charter 口径判档(证据面 + 完美写作;纯措辞/文本项视为已被"完美写作"吸收):**

> **中心 = weak accept 上沿、贴 accept(solid)下沿。**
> **上行条件**(至 solid accept):(a) 证据侧零卡件落地——★1★2 修复、V1 极性验证、es_drop~base_recall 控制(B15)、机理池零 GPU 加宽(B16)、F1 配对 CI;且 (b) B22(MEMIT 现象复制)或等效广度证据落地。(a) 全零卡,(b) 需一个 GPU 窗。
> **下行尾部**(至 borderline,概率非零、不可忽略):抽到"编辑方向老手+统计审稿人"组合,同时按住 单编辑器×单数据集 + es_drop 涌现的知识覆盖归因质疑(B15 未做时无防) + "修复在自家验证过的严口径 RRs 上 T−N p=.073"三点。
> strong accept 在 7/27 前不可达(见 H2)。

**判档的证据底盘**(为什么中心不落 borderline):核心统计在严格多重比较下存活——M1 T−N|CLR1 p=.0002、battery T−N/T−P 的 ES 与 CLR p≤.002、Qwen-32B/Llama-70B 两 cell ES 降幅各自排零且量级对称(0.106/0.107)、multihop 0.188 排零、F2 B0→B1 0.130 排零;Holm ~15 项下这批全活,死的只有 pooled/within slope 的裸 p 与 rr/RRs 边缘项——"全文没有一个 p 站得住"式拒稿构造不出来。效应量按部署更现实的采样口径是 RR@B3 0.264 [0.216,0.312](非 greedy 0.193),且 256-token 短链即饱和——对"编辑作为安全干预在 test-time compute 下静默失效"的 AIA 框架不算温和。

**真证据缺口只有三个**(其余全是写法/卫生,完美写作前提下不压档):①单编辑器×单数据集(B22 可修一半);②logit-lens 无对照/无 CI/近恒真设计(B23 可修,或文本降级——降级后机理头牌少一块独立地基);③es_drop 涌现缺 base_recall 控制(B15,零卡,自家 `_adversarial_verified.Cap_upgrade` 判"必做"却只跑了 CLR 版)。

五维:

| 维度 | 判 | 一句依据 | 置信度 |
|---|---|---|---|
| Novelty | **中(偏上)** | 现象/机理/修复三类各有强近邻(SCR/Superficial Editing/DISCO/CRANE),但三个独有点——capability-emergent erosion、chain-only 因果干预、native R1×预算受控对比——查新至 7/3 无人占据;是"合取新颖"非"存在新颖" | 高(两轮联网核实) |
| Significance | **中上** | "more thinking → less safety"大叙事已词条化,本文是其在 knowledge-editing 域首个受控-预算+机理+修复实例;采样口径 1/4 编辑成功被自然思考翻回、短链即饱和=部署级量级;贴着"参数编辑本就不行"的边际递减区是唯一压分面 | 中高 |
| Soundness | **中上** | 单条协议、预注册四臂、F1/F2/F3 去混淆、M1、Cap3 自我退役、κ=0.836 构成同侪罕见的效度工程;三个真缺口(上列)决定其到不了"上" | 高 |
| Clarity 潜力 | **上** | 故事线(编辑完好→链内重推→答案跟链→只堵链答案就回来)可讲得干净;Phase-1 可满足,但图1 换腿后有视觉证据风险(C-4) | 中高 |
| Reproducibility | **中上** | results.json+溯源头+还原双验+mock 测试+prereg 在 AAAI 池里高于中位;扣分项全零卡可修(★2 不可复算、logitlens 无 n、s1_record.py 缺仓、stale 键);原始 jsonl 离线是既定架构、随投稿转移即可 | 高 |

---

## B 差距账

排序按 **Δ(录取概率)÷成本**;成本轴:零(纯本地/纯文本,小时级)/ GPU(需 H200/H100 窗)/ 写(写作工时)/ 天(墙钟,仅标非平凡项)。裁决:CLOSE(投稿前必须/应当)/ WINDOW(有 GPU 窗才做)/ DROP(不动针,放弃)。(三分法是对 charter 二分的有意扩展。)

### 第一梯队:零成本证据侧 + 必改文本(CLOSE)

| # | 缺口 | 动哪维 | Δ | 成本 | 裁决 |
|---|---|---|---|---|---|
| B1 | **draft 涌现统计叙事倒置**:主证据在 **L156**("we lead with CLR/RR rather than with the mostly-non-significant ES drop")与 **L158**(整段"only CLR survives");次证据 L46/L114。注意 draft 是**半新半旧**(L114 统计段已含两高端 cell 显著的 clean 口径)→ 修复须全文一致性扫描,非改三行;两份 pending 清单均未覆盖此项,且 `_pending_draft_edits` 末条 limitation 已被 7/2 重跑作废 | soundness+一致性 | 大 | 写 | CLOSE,写作解冻第一件事 |
| B2 | **results.json 卫生 pass**(写作期取数事故源,一次清完):①★1 三处同改(`_bonus_CORRECTED`/`32B._interp`/`_adversarial_verified.CLR_denominator_artifact`);②`_percase_replacement` stale 叙述;③`within_qwen_clr`(0.365 污染值)与 `within_Qwen_clr`(1.1819)双键并存;④n_rows 1196/1194;⑤cap3.`_gap`("70B base 未跑")与 `_70B_gap_closed`("已跑")互相矛盾;⑥`_pending_draft_edits` 末条过期;⑦70B 双口径并存无 headline 标注(cells_descriptive n=200: 0.11/0.1667/0.495 vs families n=187: 0.107/0.175/0.529——顺手用作 with/without filter 双报素材);⑧`_six_scale_summary._note` 的"均随 scale 单调升"过度概括(base CLR 14B 0.86>32B 0.829、Qwen 族内 .755→.86→.829 非单调) | soundness+repro | 中大 | 零 | CLOSE |
| B3 | **★2 修复**:重算并更正 neutral 记录(17{14,2,1}、14b=4;丢失条目=cf_6933@14b Bridge)、s1_record.py 落库、跨尺度同 case 去重口径写明、"3/18"敏感性分母定口径、7B κ 统一为 −0.091 并解释(边际近全 Bridge 时 κ 对单票分歧极敏感,负值≠随机差,报一致性%作伴)、table_rq2.tex 与 results.json 收敛 | repro+soundness | 中 | 零 | CLOSE |
| B4 | **RO 涌现叙事在中性口径下只剩 n=1**(cf_21770 中性判官 3 票 Bridge;rq2_taxonomy.findings 仍写"RO 仅 32B=capability-emergent",两份 pending 清单均未列)+ **necessity"19/19 re-derivation"继承污染 population**(中性下 2 条 Recall 非重推)→ 主张换轨为"committed 回退**从不 traceless**(中性口径下依然 0)+ 链内 o_old **必要不充分**(held 14/14 均含 o_old)"——这两句更强且免疫 S1 | soundness | 中 | 零 | CLOSE |
| B5 | **涌现统计的诚实表述**:K=2 族 cluster bootstrap 的 pooled p=.003 不是 population 意义 p 值(~50% draw 单族、三种估计对象混合);within-Qwen p=.0007 同样扛不住"4 个设计点上的 case 伪复制"批评(percase_emergence.py:407-409 自注单 cluster 退化为普通 case bootstrap)。**主表述=两高端 cell 各自显著(0.106[0.030,0.182]/0.107[0.032,0.182])+ 族内单调序 + 跨族量级对齐;pooled 与 within 斜率一律降描述性/supporting**。注意团队已预承诺此纪律(depth-plan:210"无论显著都 demote 裸 p"、:294 写 limitation)→ 这是执行既有承诺,非新让步;两族 per-family slope 恰好同值(0.0975/0.0977)+ LOPO 全正是现成的稳健性旁证 | soundness | 中 | 写 | CLOSE |
| B6 | **M1 措辞软化**:CLR0 层 N_RR=0.000=地板效应("效应集中 CLR1"部分机械);2×2 中介 clr_dropped 用 T 臂 CLR=post-treatment。软化为"修复效应与链中介一致,且基线无链内 o_old 时回退几乎不发生(N_RR|CLR0=0)";另 **K4(M1 仅 32B 单尺度)**:遵 `_adversarial_verified.M1_scope`,§7 limitation 加一句"fix 的 within-case 中介证据限 32B 单尺度",实验扩尺度 DROP(性价比拐点之外) | soundness | 中 | 写 | CLOSE |
| B7 | **logit-lens 记录缺口**:n 三处矛盾(plan v1.25=23 / rereview-round2=19 pooled / depth-plan **W5** 行 n≈10-17、W2 行 n=10),results.json 块无 n、无 CI、gap_sampled 手填、脚本不产该聚合;draft L183/L217 峰值层错标(真峰 g_60=17.803,g_56=11.548)。补 n/口径/commit 溯源进 results.json;56→60 | soundness+repro | 中 | 零 | CLOSE |
| B8 | **V1 CLR 极性判官验证**(~40 calls,零 GPU):代码确认无极性检查。**定价校正**:四处用途中三处对极性误判免疫或保守(M1 分层=稀释方向且实测分层差极端;RQ3 ΔCLR=构造性必降;taxonomy 判官读 raw CoT),真暴露面=描述性 CLR 水平值(6 尺度曲线、F2/F3 的 CLR 行)→ Δ 中小,但成本近零+堵"开箱即中"观感,仍值得 | soundness(测量) | 中小 | 零 | CLOSE |
| B9 | **机理描述性 n 的诚实呈现**:taxonomy/necessity/logit-lens/RQ3-footprint 共享同一 ~20 case 回退池——主动披露+全部 n+Wilson CI(~3 LOC),并把机理结论重心明写在干预证据(battery/M1/α-sweep,n≈100-200/臂)上、观察性明标 descriptive | soundness | 中 | 零 | CLOSE |
| B10 | **CRANE(2606.09033)补 §2 立界**(6/24 排查漏检):多模态、冲突源=视觉证据、无预算轴、无机理、修复需训练 | novelty+完备性 | 中大 | 写 | CLOSE |
| B11 | **K2′ 零卡半**:按 base recall≈0 分层现有 200 case 回退率,检验 abstract 已写入的 knowledge-conflict "why"(若无先验 case 也回退→KC 降为部分解释) | soundness(why) | 中 | 零 | CLOSE |
| B12 | M5 零卡前奏:现有 T−P 按 reflect_before_old/contests_edit 分层 | soundness | 小中 | 零 | CLOSE |
| B13 | **F1 配对 CI**(自家对抗验证判"必需"未做)+ cap3 net_clr 回填:7B base 分片在盘可回填(4→5 尺度);70B per-case base 行本地未证在盘、按平台侧回填处理(4→5 本地 + 70B 平台) | soundness | 小中 | 零(+一次平台回传) | CLOSE |
| B14 | **draft 数字级修正**:0.59→0.765(L13/17/21/44);BOS"within one case"→ES 1 case/CLR 2 case;70B with/without 双报兑现;"largest RR 0.193 never past 0.20"在 F3(采样 0.264)/F2(B1 0.208)入文后改写;clr_robustness 引用换 clean glob 重跑或降附录;全部 [pending] 字样清除(L69/255/261/277/283/292/295);L286 "the one control a skeptical reader will ask for / cleanest discriminating experiment"自递刀句改为并列 future work | soundness+clarity | 中 | 零/写 | CLOSE |
| B15 | **【新缺口,本轮对抗校验发现】es_drop 涌现缺 base_recall 控制**:`_adversarial_verified.Cap_upgrade` 明载"回归 erosion~capability\|base_recall"为必做,但 cap3 只跑了 CLR 三件套;base ans_old 随尺度 0.515→0.785 与 es_drop 斜率同向→审稿人可把"capability-emergent"改读为"**知识覆盖涌现**"(大模型本就更知 o_old=回退燃料更多)。零卡再分析:per-case es_drop~log10(params)+base_ans_old 协变量(或按 base 知识分层),数据与 Cap3 同源。**G 节的第二支柱升格以此为门**:通过→升格措辞成立;不过→保持 scale-consistent trend | soundness+novelty(第二支柱的命门) | **大** | 零 | CLOSE,证据侧最高优先 |
| B16 | **【B22-DROP 被推翻,零 GPU 池加宽】**:extract_reverted.py 为 CPU-only;原料已存在——F3 采样臂 B3 n=597(RR 0.264≈90+ 条 loose 回退链)、F2 B1 臂(RR 0.208)、8B/70B/1.5B headline 链(taxonomy 现只有 Qwen 三尺度,**无任何 Llama cell**);过中性判官(JUDGE_PROMPT_NEUTRAL 现成)~20→60-100 条 + 得 Llama 复制 cell。成本=一次平台文件回传+判官 calls(与 B8 同档)。诚实注记:采样链与 greedy 共享 case_id,按 case 聚类报 CI。直接拆 D-R3 的"20 case 撑四个结果" | soundness(机理分母) | **中大** | 零卡+回传+判官 calls | CLOSE(短等) |
| B17 | **RRs 进主表的配套纪律**(不配套=自伤):T−N 的 RRs=−0.051 p=.073 含零、T−P RRs p=.029 边缘,而"halves reversion"建在 loose RR 上、自家验证又证 loose 精度 0.48→组合可被打"验证过的口径上修复不显著"。写法:修复因果主张由答案级 ES 承载(T−N +0.138[0.082,0.194] p<.001),RR/RRs 作上下界括号,"halves reversion"显式绑定 loose 口径;α-sweep 若报 RRs 列须回填 α=0 基线(sup_battery N 臂 RRs=0.092)或去列 | soundness | 中 | 写 | CLOSE |
| B18 | **投稿工程包(K10 后半,原稿漏计)**:LaTeX 建仓(AAAI 两栏,draft 现为 markdown)、三图定稿(plots.py 仅骨架;图1 依赖 G 的换腿决定)、supplementary 打包+匿名化清洗(平台路径/用户名/平台 id)、双盲检查、reproducibility checklist、dual-use 伦理声明(AIA track 论文顺手写)。这是与全部 CLOSE 项同落一人的真实工时,须进解冻表 | 全维(不做=没有论文) | — | 写+天 | CLOSE |
| B19 | **K9 处置**(原稿漏行):8B Loc 0.835 marginal——draft 已诚实标注,裁决=维持现措辞;**连带**:多跳主实验恰在该 marginal 配置上跑→§4 多跳段加一句 Loc-marginal caveat(clamp∈{2,3,4} CLR 稳定作部分防御);7B/14B Loc 在 `_loc` 为 null→若主表上 Loc 列,两格标"not recorded"或回填 | soundness | 小 | 零/写 | CLOSE(纯文本) |
| B20 | **κ=0.836 上主表的两个随行 caveat**(metric_validation._status 自带,原稿漏):判官=Claude 同族(共享偏置);n=87/120(33 条 rate-limited、偏 rule_rr=0 侧→κ 是下界)。脚注一并给 | soundness | 小 | 写 | CLOSE |
| B21 | genbench 部署门的**绝对值残差**:off 臂 0.855/0.700 vs 参考 ~0.95/0.90 仍差 10-20pt,draft "confirms...artifact, not the model"说满了——正文注明残差与可能来源(子集难度/答案抽取/残余截断),或绝对值下附录只报 Δ | soundness | 小 | 写 | CLOSE |

### 第二梯队:有 GPU 窗口才做(WINDOW),按值排序

| # | 缺口 | Δ | 成本 | 裁决 |
|---|---|---|---|---|
| B22 | **K1 单编辑器:MEMIT×CF 现象复制**(32B 首选、mom2 预计算不可行则 14B;n=200 B0/B3 只测 ES 降幅/RR;S7 红队:多层 [4,5,6,7,8] 配置勿单层) | **全表最大单项**(拆 D-R2) | GPU 1 窗 | WINDOW-第一 |
| B23 | **logit-lens held 对照臂 + per-case CI**(S2):红队估 55-65% 概率 held 同 dip——null 也有信息(诚实降级);顺带补未编辑 base 同 case gap 曲线对照(校验员点名的另一半:中层负 gap 仅 −0.25/−0.35 vs 峰 +17.8,量级本就弱) | 中大 | GPU 小窗 | WINDOW-第二;无窗则文本降级:logit-lens 从 abstract 承重降为 §5 支持观察,"100% intact"同句给 n 并定位为编辑安装 sanity |
| B24 | M4 强竞争者 placebo(C 臂 n=200) | 中 | GPU 1 臂 | WINDOW-第三;无窗则 limitation 明写 |
| B25 | G1 cond-c 盲区(8B multihop 路径 ~40 LOC) | 中小 | GPU 小窗 | WINDOW;无窗则"zero collateral by construction"降为带三前提条件句 |
| B26 | genbench 等价界加 n(TOST 达 ±0.02) | 小 | GPU 小窗 | WINDOW-末位 |

### 第三梯队:不动针,放弃(DROP)——17 天做减法比做加法重要

| # | 项 | 为什么不动针 |
|---|---|---|
| B27 | **E-CHAINSUB(S5)** | provenance bug 未修=实验自身循环(红队原话"破循环实验自身循环");name-and-bound 段已写好。**维持 camera-ready,投稿不做**——最大时间陷阱 |
| B28 | zsRE 主跑 / AlphaEdit / 更多尺度族 / B4 全曲线 / M1 扩尺度(K4)/ K2′ GPU 半 / M5 GPU 臂 | 三轮 review 共识:广度=门票不加分;MEMIT 一个点(B22)是性价比拐点,其后全平坦区 |
| B29 | ~~S6 池加宽~~ **GPU 重生成版**(cf1500,12-18h) | 被 B16 零 GPU 路径取代——原 DROP 理由只对重生成版成立 |
| B30 | 32B 多跳 | 预注册升级门未达(b0_prop 48<60、仅 P27 有功效),自家已裁定不升 |
| B31 | prompted-CoT vs native 对照 | depth-plan 已 DROP(双向预认+最贵);文本自洽修正在 B14 |
| B32 | FlipPoint token 级 / ESf 进主表 | 未验证指标,进正文只添攻击面 |
| B33 | 平滑 scaling law 化 | 自家红线正确,维持 |

---

## C 7 页砍单

**先立 float 账**(初稿漏算,对抗校验补):正文预算 7.0 页,其中 float 至少——图1(双板,~0.45 页)+ capability 主表(6 行跨双栏 table*,含 base 两列,~0.35)+ RQ3 headline 小表(~0.2)+ taxonomy 小表(~0.25)+ α-sweep 图或表(~0.3)≈ **1.5–1.8 页**。文字实际可用 ~5.3 页。据此三条压缩指令:①**battery 正文只报 T−P 与 P−N 两行结论+一句 D 反号**,四臂×四指标全表下附录;②fig:rq2(logit-lens 曲线)去留绑定 B23:有 held 臂→正文;无→附录,§5 只留文字;③taxonomy 表与 capability 表不合并,但 taxonomy 只报中性版一列+κ 行(污染版整表下附录)。

**正文骨架**:

- **§1 Intro + 图1**(1.2 页):现象→机理→修复→capability 四段+贡献 4 条。**图1 视觉风险(Phase-1 专属)**:es_drop 主板 6 点中 4 点 n.s.、低端两点为负,肉眼=噪声+两个高端点;而退役的 CLR 曲线恰是全项目视觉最漂亮的一条。缓解:主板画族内配对 CI+双高端显著点高亮;**RR 单调曲线(0.061→0.193 / 0.144→0.175)做视觉承重副板**;可选教学板=CLR 并画 base 底噪(讲"表观趋势被去混淆")。Phase-1 只看 abstract/intro/图1——这张图值一天打磨。
- **§2 Related**(0.8 页):四线+CRANE 立界+alignment 文献带接入(AIA rubric ②)。每线"已知→我们的边界"两句制。
- **§3 Setup**(1 页):BOS A/B、clamp 扫描、还原双验、B0P 构造细节下附录,正文各一句+指针;统计段按 B5 重写;配置异质性 preempt 预埋一句:"edit installation is matched at B0(六 cell ES@B0 0.50–0.625 平)——斜率不能由编辑强度异质性解释"。
- **§4 现象+capability**(1.3 页):capability 主表(+base ans_old@B0、base Δthink 两列=F1/LEVEL-CHANGE/7B 混淆/Cap3 动机一表四用;完整 base 表下附录);涌现统计(B5 口径);F2/F3 各一小段;CLR 退役五句话(下修版,见特别裁定 1);多跳一段(加 B19 caveat + "传播衰减非复辟"边界句:stale_revert 仅 0.021、8/9 去向 neither——主动把"标题在多跳上不成立"的敌意读法变成我们自己的边界陈述)。
- **§5 机理**(1.2 页):logit-lens 段按 B23 结果二选一(两版预写);taxonomy 主表=中性版(B3 修复后:Bridge 14/17≈82%、Recall 2、RO 1),正文一句敏感性("移除反 recall 措辞后 Recall 0→2、Bridge 仍主导、traceless 仍 0;population 判官敏感 3-4/18");necessity 换轨(B4):"从不 traceless + 链内 o_old 必要不充分"。
- **§6 修复**(1 页):headline 表+battery 压缩版+α-sweep+M1(B6 软化)+genbench 部署门(B21 残差注记)。RRs 进主表按 B17 纪律。
- **§7 Limitations**(0.5 页):单编辑器/数据集(B22 落地则改写);机理描述性 n 小+共享池;涌现推断的族数边界;自然必要性 name-and-bound;V1/B15 结果如实;fix 单尺度(K4);cond-c 三前提;7B 双重坏点;8B Loc marginal。

**三个特别裁定**:

1. **CLR 退役怎么讲:方法学卖点,5 句话,不值一个小节;措辞修正版**(初稿版含可证伪的"同样单调升"——base CLR 14B>32B 非单调):"链内泄漏率(CLR)在族内随尺度上升,但未编辑基座的链内底噪同样高且随尺度增长(0.582→0.905,个别点非单调);**逐 case 配对减除后,net-CLR 的尺度斜率含零、且编辑态恒低 base 约 0.3-0.5 的 gap 不随尺度扩**——我们据此把 CLR 从涌现证据退役为描述性指标;capability 信号由构造上编辑特异的 ES 降幅承载(base 无编辑可丢)。"退役论证只压配对 net-CLR,不用任何"单调"字样。放 §4,Cap3 全表下附录。**不要**在正文复盘"我们曾以为 CLR 涌现成立"的过程。
2. **6 尺度 base 表:值,但以并列方式**——base ans_old@B0/Δthink 两列并进 capability 主表,完整 base 表下附录。单独占正文一张表不值:它是防御性资产不是贡献。
3. **S1 软化篇幅:正文 ≤3 句 + 附录双列表**;主表用中性版(B3 修复后数字)。污染版当主数的方案不采——已知仪器污染的版本不该是主数。

**整个不讲**:genbench worst-case(一句+附录);MEMIT 旧污染时代数据;FlipPoint/ESf;layer 扫描史;两次基础设施污染事故过程(属于 repo);EasyEdit sequential_edit 陷阱(附录脚注级);KC-as-headline(维持 Discussion 层,措辞强度等 B11)。

---

## D 拒稿预演(3 条最可能 + 预备队)

**R1|"现象已知"**:SCR(2505.18690)**Table 4** 已在 R1-Distill-Llama-8B×ROME 上给出反思翻盘定性案例('Dagobert? Wait, no… should be Clovis I')并写明"internal reasoning reflects outdated knowledge, undermining the edit";CRANE 已命名"推理链拒斥注入编辑";ThinkEval 已做多步泄漏。
Preempt:①立界句(F 节成品,已修 dose-response 措辞):现有工作是**单解码配置下的定性观察**,我们给出预算受控的 zero-vs-long 对比+编辑特异对照+capability 涌现+因果修复——检索上站得住;②SCR 引为 premise 并注明口径不可比(其 Rel=72B judge 语义一致 vs 我们生成式 ES_b——引用时守口径纪律);③CRANE 立界(多模态/视觉冲突源/训练式修复);④ThinkEval 的 size 结论是"变大不改善"(平坦)、与我们符号相反——显式对比。

**R2|"单编辑器单数据集,ROME 特有?"**(AIA rubric ④ 标准动作)
Preempt:首选 B22;无窗则:①limitation 如实+点名 MEMIT 为最有信息量下一步;②外部证据借力(SCR 示多编辑器在推理模型上崩;Superficial Editing 证非擦除跨方法);③删 abstract "(ROME/MEMIT)"暗示性括号(L13);④补效应量反转句:"suppress 后 ES@B3 0.631 > ES@B0 0.595——思考+修复反超零思考",堵"ROME 在 B0 本就只 0.595,你们在烂方法上做二阶效应"的连带打法。

**R3|"机理证据薄:~20 条回退 case 撑 taxonomy/necessity/logit-lens/修复解读四个结果;logit-lens 重灌编辑后探 ROME 自己优化的 cloze logit,intact 100% 是构造使然、无 n 无 CI 无对照。"**
Preempt:①B16 零 GPU 池加宽(~20→60-100+Llama cell)是主动解;②B9 披露共享池+全 n+Wilson CI;③logit-lens 按 B23 二选一处理,"100%"同句给 n 并定位为安装 sanity;④两句构造性反驳预埋:"o_old 不在 prompt 中,链内 o_old 只能来自参数=参数起源 by construction";"held 14/14 链含 o_old 而不回退=答案跟随的是链的 commitment,非表面复述";⑤机理重心声明压在干预证据(battery/M1/dose)上,观察性明标 descriptive;⑥V1 结果如实。

**预备队**(非前三,一句 preempt 已备,不展开):统计审稿人的 K=2 攻击→B5 表述即防;"六 cell 配置异质性(edit layer/clamp/BOS 逐模型不同)驱动斜率"→§3 预埋的 ES@B0-matched 句即防;"部署门绝对值欠测"→B21 注记即防。

---

## E 写作解冻表

死线按仓内权威 7/20(abstract)/7/27(全文)/+3 天(supplementary)执行(CFP 网页读到晚一天的日期,待用户亲核,见头部声明)。倒推:**写作必须 ~7/8 开动**;并行结构=写作与零卡证据件同周推进,依赖关系如下(只列依赖,不排日程)。

**现在已定稿、可写死**:
- capability 6-cell 表全数(70B 双口径按 B2⑦ 定 headline 后写)、F1(含"无系统性漂移"红线措辞)、F2、F3、base 6 尺度表;
- RQ3 全套(headline/battery/α-sweep/genbench 部署门+B21 注记/M1 按 B6 软化);RRs 按 B17 纪律进表;
- multihop(+B19 caveat+边界句);metric_validation(κ+B20 两 caveat);
- 涌现统计(B5 框架:两 cell+单调序+跨族对齐承重,斜率描述性);
- CLR 退役五句话(特别裁定 1 修正版);
- §2 related 骨架+CRANE 立界(全部外部引用在写作期逐篇 WebFetch 验真,尤其 ThinkEval diff 到 v3/TMLR、SCR Table 4 归属钉死在 2505.18690)。

**短等(零卡自产,不阻塞开写,回填即可;按依赖排)**:
- B3(S1 重算)→ §5 taxonomy 主表数字等这个,**它是 §5 唯一的数字闸门**;
- B15(es_drop~base_recall 控制)→ **G 升格与 contrib-3 措辞的闸门**:通过→"capability-emergent"升格版;不过→"scale-consistent trend"保守版(两版 contrib 预写);
- B16(池加宽+Llama cell)→ §5 的 n 与 R3-preempt 力度;
- B8(V1)→ CLR 相关句加验证注或如实报假阳率;
- B11(K2′ 分层)→ KC "why" 段措辞强度;
- B13(F1 CI+cap3 回填)→ limitation 措辞;
- B23 两版 §5 文案预写,结果到手选版。

**不等(不影响投稿文本,或已 DROP)**:
- B24/B25/B26:limitation 版文本先定稿;窗口出结果则替换是加法;
- B27–B33:全部按"named, bounded, not closed"或不出现处理;[pending] 字样清零(B14);
- B22(MEMIT):**唯一值得为之改写正文的未做项**——在写作定稿前出数则 §4 加一行+§7 改写;未出则按 R2 无窗版定稿。可做非必做:没有它论文站得住,有它最大单项提分。
- B18(投稿工程包):与写作并行的独立工作流,LaTeX 建仓和图1 打磨是其中仅有的两个上游件(图1 依赖 G 决定)。

**逐项判**:B15/B16/B3/B2=必做(证据侧);B8/B9/B11/B12/B13=必做(便宜+堵观感);B18=必做(工程);B22=可做-最高值;B23=可做-优先;B24/B25/B26=可做;B27-B33=放弃。

---

## F 查新(6/24 → 7/3 联网;检索日 2026-07-03;下轮 7/6 周一到期,并入 7/14 内审轮;所有外部事实引用前须 WebFetch 复验)

**结论:窗口内无新 HIGH 撞车;三个独有点至 7/3 均无人占据;6/24 排查漏检一篇 6/8 的 MED-HIGH 近邻(CRANE),必须补引。**

- **CRANE(arXiv:2606.09033,6/8,漏检)**:reasoning MLLM 编辑失效;"Cognitive Dissonance=推理链基于**视觉证据**主动拒绝注入编辑";teacher-forcing 100% vs Grounded Success 0%。撞概念不撞实验:多模态、无预算轴、无 capability scaling、无机理归因、修复=检索+训练式路由。漏检原因=6/24 词表无"reasoning MLLM",后续加词。作者含 Mengqi Zhang(Uncovering Overfitting 一线),该组持续产出,7/14 盯防。
- **4 HIGH 近邻现状**:**SCR(2505.18690)**仍 v1、0 引用、疑 ICLR-26 未中——可见度暂低;**其 RQ2 与 Table 4(R1-Distill-Llama-8B×ROME 反思翻盘案例)是 D-R1 的核心近邻证据,归属钉死在这一篇**。同组另一篇 **2606.00570**("参数编辑理论极限",dimensional collapse,无推理内容)已中 **ICML 2026**,会把审稿人引到这条线。**Superficial Editing=ACL 2025 main**(可见度最高),机理正面竞争:立界=静态 crafted-prompt 存在性 vs 我们 native CoT 内动态显形+预算依赖。**ThinkEval** 已中 TMLR、更到 v3(引用前 diff);其 size 结论与我们符号相反=对比资产。**DISCO**(ACL 2024 Findings)无更新;修复段一句正交性(答案级对比解码 vs 链内 token 级+因果探针双用),不必作 baseline 跑。
- **新增可引弹药**:One Mask(2605.28839,ACL 2026 Findings)=非擦除第三方佐证;Illusion of Erasure(2606.23276)可翻转为动机("模型自己的推理链=内生 indirect prompt,无需外部对抗者");2509.06861(test-time compute 不能新增参数外信息)与我们(thinking 主动侵蚀参数内新写入信息)构成互补对;CoT Hijacking/Self-Jailbreaking/TTT-undermines-guardrails=AIA rubric ② 的 alignment 文献接入点。
- **定位语句(§2 现象线立界,英文成品;已修 dose-response overclaim——预算轴证据是 B0/B1/B3 三点且 B1 即饱和,"dose-response"一词全文只留给 α-sweep)**:
  > Prior work has observed, at a single decoding configuration, that reasoning models can "reflect" their way back to pre-edit knowledge (SCR; CRANE for multimodal models, where the chain rejects edits on the strength of *visual* evidence; ThinkEval via externally constructed thought-graphs). We characterize this failure under a *budget-controlled* zero-vs-long thinking contrast — showing the erosion appears as soon as a genuine chain unfolds (saturating by 256 thinking tokens) — show with an unedited-base control that it is *edit-specific* rather than base drift, show it *grows with model capability* across two distillation families and six scales, and demonstrate a training-free, chain-only suppression that both repairs the answer and causally isolates in-chain re-derivation as the driver. None of these properties is addressed by prior editing-under-reasoning work.
- **MECH-led 头牌仍清**:chain-only 因果干预与 capability-emergent erosion 检索上无人占;"training-free 推理期干预修安全"心智被 SafeThink(2602.11096,jailbreak 域)部分占据→修复不单独作头牌(与现 framing 一致)。

---

## G framing 复核

**裁决:维持 MECH-led;capability-emergence 的升格改为条件式——B15(base_recall 控制)通过才升并列第二支柱,否则保持 supporting trend。不翻头牌。**

6/30 定 MECH-led 时证据结构是"CLR 涌现成立、es_drop 死";7/2 后反转。这不推翻 MECH-led,两条独立理由仍立:①撞车结构——现象层被 SCR/CRANE/ThinkEval 占得最密,机理+因果修复是近邻最薄地带(F 节核实);②AIA rubric 明文接受 analysis novelty、mechanistic interpretability 是 track 关键词第二位=机理头牌有 CFP 级背书。(初稿第三条理由"capability 头牌=把统计最脆的盾放最前排"经对抗校验降权:K=2 批评的杀伤半径有限——两族斜率恰好同值、bootstrap 方向保守、且 B5 表述本就是既有纪律执行;但前两条已足够。)

**升格的条件与内容**:B15 通过(es_drop 斜率控 base_ans_old 后仍立)→ contrib-3 升格为"first quantitative characterization: edit erosion grows with model capability — edit-specific (unedited-base control) and consistent across two distillation families (matched high-end points independently significant at near-identical magnitude)";图1 主板换 es_drop(带 C-§1 的视觉缓解),RR 曲线做视觉副板。B15 不过→保持"scale-consistent supporting trend",图1 主板考虑保 RR。两版 contrib 预写,不烧写作窗。改动局限 abstract 一句+contrib-3+§4 主段+图1,不动章节次序、不动头牌。

若翻 phenomenon/capability-led:代价=abstract/intro/§4-§6 全序重排(烧掉写作窗大半)、头牌落在"现象已知"与涌现归因质疑的火力交叉点、丢 AIA 机理背书。不建议。

**Track 确认**:AIA track 合适(mechanistic interpretability + empirical robustness evaluation 双命中);knowledge editing 不在 AIA 关键词表→**relevance statement 必须显式搭桥**(编辑=部署中的对齐维护干预:纠错/去毒/unlearning;test-time compute 使其静默失效=部署期安全风险),§2 接入 alignment 文献带,否则 rubric ②失分。track 不可转投、Phase-1 reject 后无调整——一次性决策,建议 7/14 内审拍板并成文 relevance statement。

---

## H 总判(三句话)

1. **距 solid accept**:证据侧差五件全零卡的事(★1★2 修复、B15 base_recall 控制、B16 池加宽、B8 极性验证、B13 配对 CI)加一次把 clean 证据面如实搬进纸里的诚实重写(涌现换腿、CLR 退役五句、S1 中性转正、RRs 纪律、CRANE 立界)——这些落地后论文进入 solid accept 竞争区,其中 **B15 是第二支柱升格的命门、B16 是机理分母质疑的主动解**。
2. **距 strong accept**:差三件 7/27 内做不完的事——第二编辑器全轴+第二数据集、自然必要性闭环(E-CHAINSUB,provenance 前置未修)、机理池百级+held 对照的完整 logit-lens 统计;留 camera-ready/下一篇,本周期不追。
3. **单点最高杠杆**:有 H200 窗=**B22(MEMIT 现象复制)**,单项拆掉最可能拒稿理由且不动任何已写叙事;无窗=**B16(零 GPU 机理池加宽至 60-100+首个 Llama taxonomy cell)**——同为判官-call 成本档里,它比 V1 的录取增量大(V1 经重定价为中小:四处用途三处对极性误判免疫),且直接把 R3("20 case 撑四个结果")从 limitation 变成已解决。

---

*附:台账边界——本评审知悉且未重复 K1–K12 与三份前置 review 的已回应项(状态经 results.json 逐条核对;其中 K4/K9 在本版补齐处置行,K10 后半=投稿工程在 B18 补计)。本报告新增发现:★1(`_bonus_CORRECTED` 自身错误,三处需同改)、★2(S1 off-by-one+机制定位+7B κ 口径)、B15(es_drop 涌现缺 base_recall 控制)、B16(零 GPU 池加宽路径,推翻原 S6-DROP 的适用范围)、RO 涌现中性口径只剩 n=1、necessity 19/19 继承污染 population、draft L156/L158 涌现段倒置未被任何 pending 清单覆盖、logit-lens n 四处记录矛盾(23/19/10-17/无)、draft 峰值层 56→60、CRANE 漏检、K=2 与 within-Qwen 斜率的伪复制定价、M1 地板效应+post-treatment 折扣、RRs 修复对比 p=.073 的反面定价、图1 换腿视觉风险、七页 float 账、genbench 绝对值残差、`_pending_draft_edits` 自身部分过期。数字均以 results.json 复核为准;charter §3 与 results.json 无实质矛盾,唯"logit-lens 未入 results.json"不准确——块在(:514),缺的是 n/CI/口径/对照(定价 B7)。*
