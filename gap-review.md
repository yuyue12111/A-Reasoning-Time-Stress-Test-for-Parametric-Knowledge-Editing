# gap-review · 写作前终审「缺失清单」(2026-07-07/08,charter 执行版)

**评审立场**:与建设过程隔离的独立终审(gap-review-charter.md 执行);唯一目标=AAAI-27(AIA track)录取;只写缺什么、该加什么。上轮 7/3 终审(终极review.md)的补集——已关账项(★1★2 修复、B1–B26 裁决、B27–B33 DROP、W 系列 prereg 终裁、CLR 涌现退役、MEMIT-32B 不可行)一律不翻案。
**方法**:本人亲读全部必读(results.json 2297 行逐块、plan v1.50–v1.64、终极review、prereg-wseries、analysis/10、draft.md 全文)+ 代码级口径核查(metrics.py/plots.py);多 agent 扫缺 workflow(10 路独立找缺 + 1 路完整性批评,~120 条原始 findings,174 万 token);top-5 每条一个对抗 agent 论证「其实不缺」(6 路,含补验;裁决全量收录)。外部引用均经本轮 WebSearch/WebFetch 验真(写作期入文前仍须按 E 节纪律逐篇复核)。
**总判(三句)**:①证据面无 ★1★2 级新致命伤;发现 1 处代码级统计口径 bug(F3 采样 CI 伪复制)与 3 处口径/记录级硬伤,全部零卡小时级可清。②最大的缺失类不是证据,是「7/3 后新证据(W 系列/B16/B22/F2 升格)的写作落点与规格」+「AIA track 专属材料(relevance/ethics/truth-framing)」——后者是全部缺件里唯一能单独致拒的类别。③top-5 全部零 GPU、合计 ~1.5 个工作日,可全部塞进既有 7/8–7/13 日历而不置换 B1/图1 打磨日。

---

## 一、top-5 必加(每条经一个对抗 agent 攻击;裁决与修正版如实收录)

> 对抗验证总结:6/6 WEAKEN(无 OVERTURN、无原样 UPHOLD)。对抗方的共同有效攻击=「已排产未到执行日 ≠ 缺失」与「体量虚高」;共同无效处=每条都有一块攻不破的真缺口。以下即为**吸收攻击后的修正版**,体量按对抗方核减后报。

### 必1|写作队列归一 pass + W 系列落点记账(1.5–2h,7/8 B1 之前执行)
- **缺什么**:唯一活队列 `base_probe._pending_draft_edits`(18 条,7/3 后已吸收 12 条新块)之外,仍有三处跨源数字冲突/过期指令未归一,跨 session/compaction 写作时每处都是 ★1 式双源分叉雷:①S1 旧清单(`rq2_taxonomy.neutral_rerun_S1.draft_edits_pending` #1:contrib-2 写 "~81%")与 B16 条(#16:写 "68%")指向两个不同 headline,**取舍至今无人落笔**;②plan v1.62 仪器诚实节写「W-B G7 负结果一句」——已被 v1.63/64 事实推翻(G7 二跑 PASS,真负结果=确证臂 B1-FAIL dissociation),照抄=写出事实错误;③W-A 三件套/W-B 确证臂在队列里零条目(去向只散记在 `wa_main._verdict_714` 与 `wb_representation_repair.confirm_arms.verdict` 块内),写作 session 只读 pending 清单开写会漏掉 7/3 后最大一批新证据。另:v1.64 记「21 条」与实际 18+4 计数不符;旧 `logitlens` 顶层块与 `rq2_logitlens._authoritative_record` 并存无指针。
- **为什么动录取**:审稿人可见的数字不一致直接压 soundness 观感(Phase-1 有 AI 辅助评审逐字扫全文,见 §五-E2);W 系列证据丢失=机理柱白扔一层。
- **怎么加(对抗修正版:不新建第六个带数字文档、不加冕第三个「唯一真源」)**:①S1 4 条并入 `_pending_draft_edits`(#1/#2 标 superseded-by-B16;当场裁决 contrib-2 headline=50-池 68% 为主、17-池 82.4% 作中性重跑伴报一句,遵 b16 块「并列报不混池」);②补 3 条真无家项:B13 limitation 措辞、B12 一句、**W 系列占位条**(明写「内容待 7/14 内审裁决;勿按 v1.62 G7-负结果句写;W-B 真相=G7-PASS→确证 B1-FAIL;W-A 数字:G5 65/65=100%、A2 AUC .507 perm p=.487 n=[10,30]、A3 −0.075 含 0、G4 fail→A1 不可判」+ W-B appendix 三对比行);③旧 `logitlens` 块加 `_superseded_by` 指针;④plan.md 记 v1.65 五行「写作期取数纪律」:数字只从 results.json 数据块取、指令队列唯一化为 `_pending_draft_edits`、终极review C 节数字一律视为过期、变更日志是历史非指令。「answer commitment」命名层级(§5 vs contrib/abstract)归 7/14 内审裁决,默认不进 abstract/contrib(v1.60⑥ 红队裁决与 W-B prereg 措辞禁令为 standing ruling)。
- **对抗裁决**:G0=WEAKEN(「五套等权无人合并」被证不实——活队列健在;但三处冲突逐一取证成立=真 compaction 雷);T4=WEAKEN(「所有队列零 W 条目」部分不实——去向在块内有记;幸存=v1.62 过时指称+pending 零 W 条两点属实)。修正版即两裁决的 amended_recommendation 合并。

### 必2|F3 采样臂 CI 重采样单位修复(~3h,7/13 前;唯一证据侧必修件)
- **缺什么**:`score_bootstrap`(src/metrics.py:184-233)按**行**重采样:采样臂同 case 的 3 条 seed 链被当独立样本(`_indicators` 逐行 append、`ci_of` 逐行抽),b0ok 门只看 `eff0[0]`(seed/文件序依赖)→ `f3_sampling_robustness.sampling` 的 rr_ci_B3 [0.216,0.312] 与 clr_ci_B3 [0.482,0.563] 是伪复制口径,case 聚类后 CI 必加宽(点估不动)。**本人已代码级复核成立**。致命交叉点:draft.md:114 已白纸黑字承诺「bootstrap over edited facts (resampling n facts)」——采样 CI 一旦按 B14 指令入文,方法学声明 × 释出代码(B18 repro 包)互证为假;且 B16 自己立过「采样链按 case 聚类报 CI」的纪律(终极review B16 行)未回头执行到 F3 主数。
- **对抗修正(重要)**:es_drop 采样 0.090[0.010,0.171] **不受影响**——`drop_bootstrap`→`_es_by_case`(metrics.py:236-273)每 case 每档取 `rows[0]`,本就 case 级配对(代价是只用了首 seed 行,注明即可);「es_drop 转含零风险」是我初版表述的机制错误,撤回。0.264/饱和句现尚未入 draft,风险是前瞻性的。
- **怎么加**:给 score_bootstrap 加 case 聚类变体(case 整块重采样、3 seed 行保留块内;b0ok 门口径注明),只重算 F3 采样臂的 RR/CLR/边际 ES CI,results.json 双版并记+一句披露。预期:点估全不动、RR CI 加宽至约 [0.19,0.34] 以内、无措辞需降级、draft:114 声明与真源一致化。**过实验截止线①的 bug-修例外**(plan.md:263)。
- **原包裁掉的部分**(对抗方否决,不做):饱和句配对检验(等价主张靠不显著撑不住,反成攻击面→按终极review:175/B14 既有措辞纪律写描述版);族内单调置换检验+高低端 cell 对比(事后选检验=forking paths,且 B5 口径+7/12 族内配对 CI 已是 K=2-free 正交层);RRs[0]/n=198 并入既有 B17(7/10)/B14(7/13)执行。
- **对抗裁决**:T3=WEAKEN;幸存核心被对抗方原话确认为「写进纸面即为假陈述级别的 bug,防线攻不破——如实认输于此点」。

### 必3|AIA 搭桥三件套「任务卡显式化」(≤0.25 天 fold-in,骑既有 7/11–7/12 槽位)
- **缺什么**:draft 现文本确无 track 搭桥(alignment 出现处全为统计语境 cross-family alignment,draft.md:149/150/156;safety 两处是部署语境),三版 abstract 无 track 钩子,related_work.md 零 alignment 条目;而 CFP 亲核(本轮多源)坐实:AIA track 明文「must state their contributions and relevance to the track clearly」,relevance 是评审第一维,knowledge editing 不在关键词表——**这是全部缺件里唯一能单独造成 Phase-1 拒稿的类别**。7/11「relevance statement 草」在日历上有槽位,但两处**计划粒度缺口**是真的:(a) 7/12「abstract 三版」任务与全部 pending 条目对 abstract 只改数字,无「加 track 钩子」显式指令;(b) §7 部署含义五事实(F3 采样 0.264/F2 256-token 饱和/MEMIT RR 0.333/修复须落链位点/never-silent 49/50)各有排产位但无「收拢一处」的 checklist 行。
- **怎么加(对抗修正版)**:①7/11 relevance statement 照排(内容用终极review G 节骨架:编辑=部署中的对齐维护干预——纠错/去毒/unlearning;test-time compute 使其静默失效=部署期安全风险),表单 100 词版归 B18;②7/12 abstract 任务卡加一行:「选定稿尾句带 ~25 词 track 钩子」;③7/12 §7 任务卡加一行:「五个已排产事实在现有两个部署段(draft.md:291-295)内收拢成 3-4 句 AIA 含义陈述,不新增段落预算」;④§2 alignment 文献带照 7/11 原计划、维持两句制,本轮已验真的备选池择 3-4 条:R-TOFU(2505.15214,EMNLP-25 main,B0 模板出处=本就有引用义务)、Self-Jailbreaking(2510.20956)、H-CoT(2502.12893)、LRM-safety survey(2504.17704)、2509.18382、SafeThink(2602.11096)。⑤**撤销**原案的「mechanistic interpretability 正文塞词」:grep 证伪(draft.md:17/64/297 已有正向 mechanistic 用法),塞词=cargo cult+在 R3 火力点上自抬被审标准;该词仅在 OpenReview 表单关键词栏勾选。
- **对抗裁决**:T1=WEAKEN(①②被 7/11 日历逐字覆盖;④证据被 grep 证伪且有害;幸存=两处计划粒度缺口+「若 7/11-12 槽位实际未执行可重新升格」)。

### 必4|reverting-to-truth 正面处理 + ethics statement 升格前移(≤2h,7/11 与必3 同日)
- **缺什么**:全文对「reverting-to-truth 读法」零显式设防——CounterFact 的 o_old 是真实世界事实,AIA 原教旨审稿人可把全篇反转为「你们在惩罚模型说真话,并工程化了一个压制真话链的工具」;grep 全文仅 draft.md:189 一句沾边,两份 pending 清单零条目。修复段(对 CoT 施 logit 压制)与 CoT-monitorability 共识的表面张力真实存在,而 B18 的 ethics 现在只是无内容 checkbox。这是本轮红队重构的**新 R1′ 拒稿理由**(见 §四),AIA track=对齐原教旨审稿人浓度最高的池子。
- **怎么加(对抗修正版:≤2h 连接组织,不是 0.3 页新段)**:①B18「dual-use 伦理声明(顺手写)」升格为有内容的 ethics statement(8-10 句),撰写时点从 7/24-25 **前移到 7/11**(与 relevance statement 共享同一框架);②内容三件套、只写连接组织不重复数字:(a) 认识论对称 2-3 句(对冻结权重,合法更新与反事实编辑不可区分;机制=prior-reassertion 非 truth-tracking;交叉引用已排队的 K2′ 段与 6 尺度 base 表);(b) dual-use 1-2 句(同一机制可压制真知识);(c) 边界 2-3 句(edited-query-gated、推理期干预非训练压力、交叉引用已排队的 never-silent/traceless=0 结果=自然回退链本身可审计);③**三禁区**(违反=踩自家已关账裁决):不把 N_RR|CLR0=0.000 硬化为「可监控信号」(违 B6 地板效应软化裁决);不写「truth-restoration 力被否掉」(F1 是 null,只可写「base 无系统性漂移,与 truth-restoration 读法不一致」);7/14 裁决前不引 W-A G5,默认不引 Korbak/Baker(不主动向审稿人递碰撞框架);④升级触发器:7/14 内审红队若独立复现该攻击并判声明不够,再扩 0.2 页 Discussion 段并按纪律补引 Korbak 2507.11473/Baker 2503.11926。
- **对抗裁决**:T2=WEAKEN(「杀伤力最高」定级被 7/3 拒稿重演排序质疑;~80% 素材已有归宿;原 spec 两组件违反 B6/F1 已关账裁决——全部吸收;幸存=「零显式设防」事实成立+「AIA 池子该读法命中率非零、廉价短声明期望值为正」攻不破)。行政线顺手核实:AAAI ethics statement 是否计入 7 页页限。

### 必5|图1 打磨日(7/12)执行检查单 + MEMIT 分隔行(既排日内执行,不新增预算)
- **缺什么**:图1 重规格本身**不缺**(终极review C-§1+G 节+pending #14 三重落账,7/12 专属日)——缺的是执行层保证:src/plots.py 仍是 v1.27 骨架(fig1 现把 CLR 画成与 es_drop 并列主面板、无配对 CI、无 base 底噪线、无高端显著星标),与已裁规格全面不符;若打磨日只「调样式」不真重写,出图即与正文 CLR 退役声明自相矛盾(全项目视觉最漂亮的 CLR 单调曲线会被评审当涌现主证据)。MEMIT-14B 行有 pending #12 覆盖,但落表排版无 spec。
- **怎么加(对抗修正版=三行执行检查单)**:①按已裁规格**重写** plots.py fig1:es_drop 主板+族内配对 CI+Qwen-32B/Llama-70B 双星标(0.106/0.107),RR 单调曲线承重副板,CLR 仅作可选教学板且必带 base 底噪虚线(`base_probe._six_scale_summary.base_clr_b3` 0.582→0.905);caption 统计措辞按 B5 纪律(两高端 cell 承重、pooled slope .109 p=.003 标 supporting);70B 取数一律走 `capability.families` headline 口径(n=187)。②MEMIT-14B 照 pending #12 落 §4 capability 主表底部「Second editor (replication)」分隔行:layers[7,8,9]/n=200/ES 0.54→0.45/drop 0.090[0.010,0.170]*/CLR 0.465/RR 0.333[0.250,0.426]/Loc 0.965+一句 32B 双故障脚注;不画进家族曲线。③可选(有余量才做):F2 三臂(B0/B0P/B1)**分类轴**小柱状图替换可选 CLR 教学板(呼应 v1.62 F2 主角升格;标注 B3 跨 run,禁 dose-response 措辞)。**不做**(对抗方否决):Fix 第三板(fix 已由 abstract/§1/tab:rq3/α-sweep 四处承载,加图1=违反双板 float 账+制造「修复双尺度」overclaim 面);数值预算轴曲线(dose-response 词纪律+B0P 非预算档+跨 tag 混画)。
- **对抗裁决**:T5=WEAKEN(①④「已覆盖」、②「有害」;幸存=执行确认+排版实现+F2 可选板——F2 升格晚于 7/3 终审,构成其未权衡的新事实)。

---

## 二、新硬伤(证据/口径级;无 ★1★2 级致命,但每条给复算路径;不在任何既有排队清单)

**硬伤1|F3 采样臂 CI 伪复制**(=必2;唯一代码级)。复算:`python -c` 对 `results/…cf200samp` jsonl 按 case_id 聚类重跑 bootstrap;范围=`f3_sampling_robustness.sampling` 的 rr_ci_B3/clr_ci_B3/边际 ES CI;es_drop(`drop_bootstrap` 路径)与全部 greedy 臂(1 行/case)不受影响。

**硬伤2|logit-lens 负带 off-by-one(draft 6 处,B7 排队项不覆盖)**:`logitlens.layers_sampled` 是 hs 索引(gap 数组长 nL+1,src/logit_lens.py:133-137);按 prereg §0 钉死的 hs[k]=decoder k−1(编辑层 12↔hs[13]),负 gap 带(−0.246@hs8/−0.351@hs12)真值=**decoder 7–11,严格位于编辑层上游**;draft 五处写「layers 8–12, (right) around the edit layer (12)」(draft.md:34/45/65/183/298+图注 215-217)是口径错。已排队的 B7 修正(n=23/峰值层/降级)不含负带。修正后叙事反而更干净:「旧事实占优直到编辑层输入,在编辑层后翻正——与编辑恰在 12 层翻转读出一致」。顺手:终极review B7 行「56→60」与权威记录「decoder 58」两指令打架——统一从 `rq2_logitlens._authoritative_record` 出(60 vs 59 已裁定为网格 argmax vs 逐 case 中位、两统计量并存非矛盾,报哪个须显式定义)。
**硬伤3|主表 32B n 混用**:draft Table 1 32B 行写 n=200,真源=198(`emergence.percase.cells_descriptive['Qwen-32.0B'].n`=198、`rq3.sup_battery.n.N`=198;RR 0.1933=23/119、CLR 0.5455=108/198 都以 198 为底);同表 1.5B/70B 用的是有效 n=名义/有效两约定混用。修:Table 1 改 198+§3.6/§7 例外清单补一句+给 `rq3.n` 加 nominal 注。15 分钟。
**硬伤4|W-A G5 门操作化偏离冻结 prereg**:实跑 G5=wa_main_analyze.py:59 的「zpre_max≥2」阈值版,非 prereg 冻结的 distractor max-stat 版;v1.61 明令该操作化改动「开盲前写进 prereg」,prereg-wseries.md 至今只有 §7.5 G3s 修正、无 G5 条。z≥2 更松→G5=100% 或高估灵敏度。修:git 考古(commit 39ca2e9 前实现是否早于开盲)能证则补 amendment+时间戳;不能证则 W-A 报告句如实标「G5 operationalized post-hoc (conservative z≥2 variant)」并进 7/14 裁决材料。1h。
**卫生打包(sev2 级,一次 pass 清完,~2h)**:①`emergence.percase.n_rows`=1196 stale(cells 加总=1194,_status 自记 1194);②M1 分层加总 106+90=196 vs `_status` n=198 无注(N/T 配对交集,须注明);③draft L191/L205/L208「κ undefined at 7B」vs 修正后 7B κ=−0.091(★2 连带修复后 draft 句未跟);④`wb_representation_repair.confirm_arms.verdict`「答案级回退纹丝不动」须细分(RR 全含零 ✓,但 S−N 的 ES +.092[.007,.176] 排零——appendix 版措辞同步吸收);⑤run-ledger:results.json 现有四个互不相干的「0.208」(F3 greedy 对照/F2 B1/C 臂/P 臂 0.210)与 headline 0.193 并存,F2/F3 入文时每个重跑值旁强制「independent re-run, same protocol」注,T−N/T−C/S10 差值统一走配对口径,appendix 建 run-tag 台账表;⑥B16 verdict「RO 3/4 在 70B/32B 高能力 cell」应为 4/4(70B 3+32B 1),措辞校正;⑦v1.64「_pending_draft_edits 21 条」计数与实际 18+4 不符(必1 顺手修);⑧`base_probe.14B._interp`「edited RR 待回填」stale(rr=0.162 早在 families 块,5min 指针)。

---

## 三、全量缺失清单(合并去重后;每条:缺什么→怎么加/成本/落点)

### A|Novelty:存在但没被命名/没说满的独有点(charter 问 1)
- **A1 「presence ≠ commitment」综合段(承诺层线打包,写作 0.5 天,§5 收尾)**:五路证据已会师——W-A G5=100%+A2 干净 null(`wa_main`)、held 14/14 链含 o_old 不回退(`necessity.held`)、M1 修复效应精确集中 CLR1 基线(−.289 p=.0002 vs CLR0 +.014,`rq3.clr_split_M1`)、C 臂压强竞争者动 CLR 不动行为(`cross_arm_paired_ci.C_minus_N`)、W-B 压概念动言语化不动答案(`confirm_arms.B1_S_minus_Pshuf`)——但没有名字、没有综合段,读者只见零件。落点:§5 末 4-6 句三级阶梯(表征在场→言语化必要不充分→只有链的 commitment 驱动答案),小写 "answer commitment"(操作化定义已在 `rq2_taxonomy.gate` 的 judge-committed answer),避开 "commitment layer"(解剖学误读);W-A 按 suggest 档 hedge、W-B 只给 appendix 指针。**执行前提=7/14 内审通过 W-A 入文**(必1 的占位条);命名层级默认不进 abstract/contrib。同时引 arXiv 2606.13603(撞词立界,见 B3)与 2605.06723(pre-verbalization commitment,近邻)。
- **A2 F2 主角落地 spec(写作 0.5 天)**:v1.62 把 F2 升格为 automatic-vs-deliberate 解离主角+叙事组织句(「编辑修补自动通路,深思重推世界」),但 abstract 三版/contrib/骨架里零着陆指令。落点:§1 组织句开篇给 F2 数字(B0 0.000≈B0P 0.040≪B1 0.208,`f2_zerothink_deconfound`);§4 F2 从「一小段」升为带三臂数字的小节(视觉载体见必5③);contrib-1/2 吸收 automatic-vs-deliberate 措辞;**强制自曝**:`_honest_wrinkle`(B0P ES 0.715>B0 0.625)与 32B 单 cell 声明;引 System-1/2 综述一行+2606.25013 反向立界(见 B2)。
- **A3 「256-token 即饱和 ⇒ 不存在安全思考预算」部署推论(写作 2h)**:现只活在 `f2._bonus` 注记。落点:§4 F2 段+Discussion 部署句把「cap the thinking budget」列为被排除的缓解;措辞用描述版(「RR 已在 256 tokens 达 0.208,与自然长度 0.193 相当」),不做配对检验(对抗方裁:等价主张靠不显著撑不住)、abstract 是否收录待 7/13 数字冻结清单一并裁。
- **A4 跨编辑器「基质假说」hedge 段(写作 3h+可选零卡聚类升档)**:`wa_extensions` 的 ROME 压制表征(edited a1 0% vs base 32%)/MEMIT 保留(a2rev 61%=61%)恰对应行为 RR 0.162 vs 0.333——「编辑器留下多少 o_old 基质决定思考能重推多少」把 B22 从广度门票升为机理有预测力的验证。落点:Discussion 3-4 句(exploratory、n=10-23 链、unclustered 如实);appendix 三级表(ROME-14B/MEMIT-14B/Llama-8B=压制是连续量);§4 B22 行加半句「MEMIT erodes more, not less」;One Mask(2605.28839)立界一行(权重级共享机制 vs 链内表征级分化,层次不同不矛盾)。升档前提=C1 聚类统计。
- **A5 「知识是燃料、能力是引擎」合成段(写作 2h)**:B15 分层(base_known slope .127 排零 vs base_unknown .043 含零,`emergence.b15_base_recall_control.stratified`)+K2′(RR 25.0% vs 3.2%,`rq2_kc`)现在是两处彩蛋句,应合成一个 ~5 句命名段(§4 涌现段尾或 Discussion KC 段,**二选一,勿两处各半**):控燃料后引擎斜率不动(.0992 p=.0041)=非覆盖伪影;无燃料层无信号=侵蚀需要燃料;1/31 confabulation 注脚;同时挡住「所以还是知识覆盖驱动」的反向误读。
- **A6 W-B 首个负结果的正面价值提取(写作 1h;placement 守 prereg appendix 终裁)**:本轮查新确认无人做过「概念向量抑制修编辑回退」(SAKE 2503.01751/MEGA 2603.20795 是 steering 实现编辑,方向正交)→§6 修复段两三句 hedge:概念级抑制特异压低链内言语化(S−Pshuf CLR −.078 排零)而答案回退不动(RR 含零)=「首个记录的表征级修复失败」,反证 token/链级才是有效位点——把 R3′ 的「trivial fix」反转为发现;正文一句 cross-ref+appendix 全表(含 LocAcc 伤害端点与 S−N ES 排零细分)。
- **A7 方法学贡献打包=contrib-4 扩容(写作 0.5 天,不加第 5 条 contrib)**:contrib-4 从单点(word-boundary)扩为效度协议套件句(word-boundary+subject-scrub 判分、κ=0.836+V1 双重判官验证、中性去偏协议、单条编辑协议+还原验证、五臂 blind-seed battery、LEVEL-vs-CHANGE 反混淆),配一张 appendix methods-summary 表(claim×instrument×validation×residual bias)。AIA CFP 明文鼓励 evaluation tools release——这一条与 E4 的 release 承诺句互为表里。
- **A8 contrib 四条重切+abstract 三版全面重写(7/12 既排日执行)**:C1 机理 headliner(吸收旧 C2;taxonomy 50/7cell/2 族)+C2 因果修复(T−C 主报/剂量/M1/S10 跨尺度/部署门)+C3 capability 升格版(B15 预写已在 pending #14)+C4 测量与协议(A7)。abstract 三版全部 6/24 证据面(0.59 误锚/90% bridge/无 F2/采样/MEMIT/B15),且实测 200+ 词 vs 自标 ~150——150 词裁剪账+headline 口径裁决(greedy 0.193 vs 采样 0.264)绑定 7/13 冻结清单(H3)。
- **A9 更大 claim 裁决(不升)**:四个候选(「行为级编辑不约束推理层」/「TTC 是对齐干预的通用威胁面」/「编辑评测协议系统性高估」/两通路理论升头牌)全部裁 overclaim 或自拆立界(evaluation-reform 会把已让给 SCR 的 premise credit 收回来);hedged 定位版全部免费且已有落点(必3③ 部署句/A2 组织句/§7 Discussion 尾 3 句协议建议)。MECH-led 不动。命名资产:「thinking tax」无撞车(Safety Tax 方向相反,脚注区分);标题无撞名。

### B|查新与立界(检索日 2026-07-07,窗口 6/25→7/7;7/6 例行查新此前未执行,本轮补上)
- **B1 无新 HIGH 撞车**;三个独有点(budget-controlled zero-vs-long / capability-emergent erosion / chain-only causal repair)检索仍无人占据。SCR 仍 v1 引用 0;ThinkEval=TMLR v3(引期刊版);Superficial Editing 坐实 ACL 2025 main(2025.acl-long.868);CRANE 仍 v1(一处来源称投 ICIP-26,单源待 7/14 复核);2606.00570 坐实 ICML 2026(引作「编辑伤推理」反向互补句)。
- **B2 2606.25013《Do Thinking Tokens Help with Safety?》(Arora 组,6/23,前轮漏检)=F2 主角的反向框架**:安全域「拒绝决策首 token 已定、思考=prefix completion」——审稿人现成的「CoT 是事后补写」质疑。立界白捡 novelty:编辑域是反例域且我们有因果证据(压链 token→RR 减半)。落点:§2 alignment 带+F2 段各一组句。
- **B3 2606.13603《Beyond the Commitment Boundary》(6/11,漏检)撞词不撞主张**:他们=链内答案锁定时间点/其后链段 epiphenomenal;我们=表征-行为解离位点。不引=missing related work(若采用 commitment 用语);引了白捡「承诺是真实 locus」独立支持。落点:W-A 段+§2 各一句。
- **B4 workspace 论文 7/6 公开发布**(anthropic.com/research/global-workspace;jacobian-lens 7/2 开源 Apache-2.0;Nanda 完成 Qwen 3.6 27B 独立复现并发 LessWrong review 含三条方法学批评)。影响:①引用锚定公开版+开源 repo;②Nanda 的 Qwen 复现=仪器外部效度礼物(对象恰是 R1-Distill-Qwen 系);③仪器诚实节三句显式接招「hypothesis-generation-only」批评:我们全部结论锚定行为端点+G1–G7 效度门+预注册,lens 类探针只作表征侧汇聚证据(W-B dissociation 本身由行为端点 RR 判定)。**7/14 查新加词**:commitment boundary / prefix completion / refusal dilution / J-lens。
- **B5 引用工程**:「CoT Hijacking」一名下两篇须消歧(H-CoT 2502.12893 攻击者劫持 vs 2510.26418 v4);SafeThink 真名核正(2602.11096);LightEdit(2604.19089)=修复线最近邻补引(lifelong editing 解码期抑制原知识);One Mask/Illusion of Erasure(2606.23276)/2509.06861 按 F 节既定用途;2510.00625(Built on Sand)可选加厚静态回退带;2603.26410(Why Models Know But Don't Say)与 presence≠commitment 相邻,§2 半行可选。全部弹药入文前逐篇 WebFetch 复核(既定纪律)。

### C|承重柱补砖(charter 问 2;全部零卡/判官级,无一真缺)
- **C1 wa_extensions case 级聚类统计(零卡 2-3h,7/14 前)**:三处自标「待 case 级统计」(采样臂 3-seed 非独立/ROME-14B A3 配对 Δz/32B 正式判)——это A4 升档与 7/14 W-A 裁决的输入。
- **C2 B16 池配套(零卡 1-2h+写作)**:5 新 cell 的 Fleiss κ/一致率从在盘票据(results/b16_verdicts.json)补算(原池有 κ=0.765,50-池合并表无 κ=新 68% 分母无一致性证明);provenance 表(50 条各来自哪个 run/解码);headline 68%/82.4% 取舍已在必1 裁。
- **C3 MEMIT 线裁决包(顺序工单)**:①C1 零卡先行→②凭结果三选一:仅 Discussion hedged 段(零卡)/+MEMIT taxonomy cell(extract_reverted 现成,判官 calls)/+**MEMIT-14B 抑制 T 臂**(唯一建议保留的可选 GPU 件:1 run n≈200 数小时,7/22 写入截止可赶;真承重=「fix 是否 ROME 特有」是 R3′ 残余里唯一实验级洞;不跑则 §7 一句 hedged limitation)→③capability 表 MEMIT 行+float 落点随裁决定。
- **C4 小额回填(打包 0.5 天)**:B15 5→6 尺度一致性跑(7B base 分片已被 cap3 找回,glob 现成);clr_robustness 干净 glob 重跑(draft §4 以它作「cutoff 不制造趋势」承重句,现值来自宽 glob 池化 n_eff=1476 非 headline 口径);paraphrase bypass 零卡条件分析(T 臂 RR|残余CLR=1 vs =0,替代 draft L255/261 的 [pending] sequence-level 空头支票);B26 TOST 两版 fallback 文字预写(达/不达 ±0.02);F1 采样口径 scope 注(若 abstract 用 0.264:F1 对照只在 greedy 下测过,一句)。
- **C5 已确认有落点、不缺(核对过,防重复立项)**:K2′/G1/S10/B15/B16/B22/V1/B7/M4/J-lens Discussion——均已在 `_pending_draft_edits` 或 C 骨架。

### D|Methods:该写没写(charter 问 3;全部纯写作)
- **D1 prereg 可验物 supp 节(0.5-1 天,sev4)**:三版 abstract+§3.6+§6 反复主张 "pre-registered",论文却无任何可验物。supp 新增「Preregistration and validity gates」一节:battery 预测+placebo/C 臂 blind-seed 记录、S10 prereg 头注、prereg-wseries.md 冻结版+commit hash、G1–G7 门表(阈值/实测 PASS-FAIL,含 G7 两轮与硬边界)、端点改动自动降级政策句;§3.6 一句指针。这也是把 W-B 负结果写成「干净的预注册负结果」而非「失败实验」的前提。
- **D2 判官管线方法之家(0.5 天)**:κ=0.836 现埋在 §2 related work(结构错位);判官协议(3 判官/多数决/strict precedence/verbatim-span 强制/中性去偏 JUDGE_PROMPT_NEUTRAL/污染-重跑史)应有 §3.5 或 supp 小节;**subject-scrub 句**(metrics.py:148 `_without_subject` 剜除主体复述——判分第三承重件,draft 只写了词界+别名 cutoff 两件)补入 §3.5。
- **D3 distractor 校准 lens 附录预写(7/14 裁决前两版)**:20 同 relation distractor z-score+置换 max-stat 精确 p=1/21+token-id 级位置排除防 copy/induction 头+CONSORT——W-A 入文则这是其仪器可信度的全部。
- **D4 LEVEL-vs-CHANGE 统一命名段(2h)**:F1/cap3/B15 三件套是同一设计模式(base 的 LEVEL 混淆 vs edited 的 CHANGE 测量),pending 清单里是三条互不引用的散句,§3 或 §4 一段统一陈述+互指。
- **D5 工程可信度小件**:还原双验一行(每条编辑 restore 后 md5 验证,08 笔记已做,draft 零字——「restore 真还原了」现在是断言不是证据);sequential_edit 陷阱附录脚注(已有,保留);infra 污染防御(glob guard/provenance meta)=checklist 一行,不进正文。
- **D6 LLM 使用合规(0.5h)**:AAAI-27 政策亲核=AI 不得为作者、**不得作为 citable source**、judicious use 允许——判官须以 instrument 形态出现(§3 判官段一句:model version+full prompts+raw votes released in supplementary);repro checklist 预填 LLM 使用声明行。

### E|AAAI/AIA rubric 材料(charter 问 4)
- **E1 死线更新(多源亲核,关闭终极review 单源悬项)**:官方=abstract **7/21**、全文 **7/28**、supplementary+code **7/31**(均 UTC-12)。内部 7/18/7/25 冻结不动=各留缓冲。**checklist 随论文 7/28 单独上传且明文计入录取决策**。
- **E2 Phase-1 机制修正(推翻 C 节旧假设)**:CFP 原文=Phase-1 每篇 3 名人类审稿人+AI 生成评审辅助,**审全文**,SPC/AC 决定去留;**无 Phase-1 rebuttal**(唯一 rebuttal 窗 10/19-25 只给进入 Phase-2 的论文);「abstract 与全文实质变更可径直拒」条款存在。写作含义:①AI 评审逐字扫全文→[pending] 字样(现存 7+ 处)、text-vs-table 漂移、L156/158 统计倒置=Phase-1 生死件,B14/B1 死线绑死 7/13;②「先写糙 Phase-2 再修」策略不存在;③7/13 冻结检查表加「LLM 审稿模拟」一项(独立 agent 按「找数字不一致/未兑现承诺/过强措辞」出报告,与 7/14 红队并跑);④图1/intro 仍最重(人类注意力),但不再是「唯一」。
- **E3 页数与 supp 政策**:7 页正文+至多 2 页仅参考文献(共 9);**正文无 appendix 位**——C 节全部「下附录」项实际去向=supplementary(评审不强制阅读!)→「critical material 不得只在 supp」自查+**supp manifest**(材料→main/supp 归属两列表+正文指针,终极review ~10 处「下附录」逐条落位),与 B18 打包脚本同工单。
- **E4 checklist+release(3h)**:7/9 前预填 AuthorKit27 checklist 把 N 项变 todo;§1/§7 加 release 承诺句(code+去污判分器+budget harness+prereg 文档+judge prompts/votes——AIA CFP 明文 especially encouraged 的加分件,现在零字);data/LICENSES.md(CounterFact/MQuAKE/GSM8K/MATH/R1-distill 权重许可逐条);平台 per-case jsonl 回传排 7/20 前(避 7/31 尾峰)。
- **E5 匿名化清洗脚本(0.5 天,7/20 前非 7/24 临时)**:白名单式打包+scrub-grep 自检(`whyu|yuyue|linroger|/Users/|/inspire/|qb-ilm|w[a-z0-9]{8}|启智|终极review`);具体已知泄漏:results.json:764/852/912/1077/1662/1690(workflow id)、src/cap3_netclr.py:4、src/steer.py:40、src/wa_probe.py:1、paper/genbench_review.md:57(真名路径)、.git 元数据;results.json 不原样发布(导出英文化蒸馏版或只发 per-case jsonl+汇总表);SUPERSEDED/污染注记链在 supp 版清洗(审稿人视角工程)。
- **E6 LaTeX/AuthorKit 建仓(B18 上游件,7/8 起与写作并行)**:paper/ 现无 .tex 骨架、无 .bib(见 H4)。

### F|图表账(charter 问 5;必5 之外)
- **F1 fig_causal 双板**:五臂(N/T/D/P/C ES 符号阶梯 D 0.281<N 0.495≈P 0.507≈C 0.510<T 0.631)与 α-sweep(CLR 单调降+ES 峰+Loc 平线)合并为一张双板 float(原计划两张→一张,省 ~0.3 页)。
- **F2 taxonomy 表 7-cell 排版**:中性 17-池主列+B16 五 cell 汇总列+κ 行(C2 补算)+污染版整表下 supp;**paper/table_rq2.tex 仍是污染版旧数(Bridge 17/19=90%/Recall=0),它是论文直接输入文件,须重生成**(B3 未完成尾巴)。
- **F3 fig2(logit-lens)**:横轴转 decoder 口径(硬伤2);源 jsonl(results/probe/logitlens_cf200_ROME_B3.jsonl)不在本地仓,回传;无 held 臂→下 supp,§5 只留文字(既定 B23 无窗版)。
- **F4 capability 主表加 base 两列**(ans_old@B0/Δthink=特别裁定 2 已拍板,draft 表未含)+MEMIT 分隔行(必5②)。
- **F5 float 账 v2(净零纪律)**:figures 路自算「全加」版 2.0-2.3 页>1.5-1.8 预算——已裁减法:五臂+α-sweep 合一(F1)、budget 轴不独立成图(必5③ 可选板)、schematic 否决、W-A 降 supp 一表(per-case 数据不在本地,画不出有信息量正文版)、taxonomy 压单栏半宽。任何新 float 须在账上找到被替换者。
- **F6 plots.py 缺码清单**:现仅 fig1/fig2/fig3 三函数(v1.27);五臂/α-sweep/F2 板/taxonomy 表生成/capability 表生成全部无码——7/12 打磨日+B18 的真实工时底数。

### G|最强三条拒稿理由(7/8 证据面重构;旧 R1/R2/R3 已被 F 节立界+B22+B16+B9 拆掉大半)
- **R1′|alignment valence 反转(新,唯一零设防)**:「CounterFact 植入假事实,o_old 是真相;你们把『推理链恢复真相』命名为安全失效,再工程化一个在 CoT 里压制真话的工具——而你们自己的 W-A 证明模型仍表征该事实,这正是 CoT-monitorability 共识警告的干预类别。」AIA 单审稿人 framing+ethics 双失分可到 reject。**拆法=必4**(认识论对称+dual-use+边界;间接证据钉 K2′/delta_think/1-31 已在盘但须按三禁区措辞);实验级解药(WikiFactDiff 真方向编辑 pilot)已否决→camera-ready 备忘。
- **R2′|统计审稿人 vs 升格后的 capability 支柱**:「contrib-3 的推断底盘是 K=2 族 cluster bootstrap;B15 的控制跑在同一台机器上救不了它;剥掉只剩 2/6 cell 显著+rr p=.052+肉眼单调序。两个显著端点=大小模型有差,不是 growth。」压 soundness 至 borderline。**拆法(纯措辞,零新统计)**:B5 口径纪律本就是预承诺——contrib-3 升格句显式声明承重面=「两匹配高端 cell 各自显著且量级近同(0.106/0.107)+族内序+跨族对齐」,pooled slope 与 B15 回归降 supporting 并随行 K=2 caveat(先手缴械);7/12 图1 族内配对 CI 即视觉防线。新增置换检验/cell 对比已被对抗方否决(forking paths)。
- **R3′|「已知现象 × 合取新颖 × trivial fix」组合拳(modal 但防御最厚)**:「SCR 已示反思翻盘、CRANE 已命名链拒斥、Superficial Editing 已立非擦除、DISCO 已给 training-free 修复;剩下的是预算旋钮+尺度扫描+20 行 logit 罚,自验 T−N RRs p=.073,paraphrase 还挂 [pending];第二编辑器只有一尺度两个数,修复只验一个编辑器。」通常只压 borderline。**拆法**:T−C 主报(pending #13,RRs p=.032)+S10 四指标+W-B dissociation 反转「trivial」(A6:概念级失败反证 token/链级是非平凡的正确位点)+F2 解离主角+C4 paraphrase 条件分析替代 [pending]+α=0 RRs 回填(7/10 B17)+C3 的 MEMIT-fix 臂(唯一可选实验件)。
- 落选说明:MEMIT 覆盖单薄(被 R3′ 吸收,14B 定案有终极review 背书);W-A G4 连坐(prereg 已把 G4 只门 A1,写作按 prereg 报+一句防连坐即无面);8B Loc marginal(B19 已裁);SUPERSEDED 注记吓人(=E5 打包工程)。

### H|写作结构与流程(charter 问 7)
- **H1** =必1(队列归一)。
- **H2 camera-ready 承诺减法(1-2h)**:grep 实证 draft 5 处「reserved for camera-ready」(:13/17/21/252/301)——abstract 尾句以「还没做完」收尾=主动递 incompleteness。三版 abstract 删该句;全文收敛到 §7 唯一一处,措辞「named and bounded, not closed」;§6 L252 非独立性段压 1/3 并更新(E-CHAINSUB 循环性段落未反映 M1/W-A 已提供的部分中介证据)。
- **H3 abstract 冻结数字联动(7/13 产出)**:每个 abstract 数字→results.json 块路径→标 7/18 后不可变;选版(A/B/C)+150 词裁剪+headline 口径(0.193 vs 0.264,与硬伤1 重算结果联动)同日拍板。
- **H4 bib 完整性审计(2-3h,LaTeX 建仓时)**:承重的 causal-premise 引文是占位 bib key `anon2025fromreasoning`——本轮已验真真身=arXiv **2509.23676**《From Reasoning to Answer…》(claim 相符,可安全落靶);draft.md:68 具名的 Thinking-Intervention/SALT/ParamMute 三工作零引用(补引或删名);L64「A 2026 cluster on non-erasure」模糊句落到具体引文(One Mask/Illusion of Erasure);paper/ 无任何 .bib。
- **H5 net-zero 文字账**:本清单全部 sev4+ 正文加法须配对删除。现成冗余已定位:§1 honest-positioning(:39-40)/§2 summary-of-distinctions(:78-79)/§7 positioning(:300-301)三段几乎同一内容写三遍(~0.5 页,并为一处);§7 prompted-CoT 段(:286)按 B14 裁减半;新引用三档分级(正文 clause/脚注/bib-only),B 节 sev1-2 弹药默认 bib-only。
- **H6 §5 结构**:不做三层重排;「内部顺序+收尾综合段(A1)」最小改动承载 表征在场→链承诺→答案跟随,兼容 7/13 冻结。

### I|已否决建议(本轮对抗/批评裁决,防后续 session 复提)
1. WikiFactDiff 真方向编辑 pilot(拆 R1′ 的实验级方案)→ **否**,7/22 前墙钟+新轴新口径双高风险,80% 效果由必4 文字达成;进 camera-ready 备忘。
2. 图1 Fix 第三板 → **否**(fix 已由 abstract/§1/tab:rq3/fig_causal 四处承载;违反双板 float 账;14B 镜像点造「修复双尺度」overclaim 面——M1 中介明限 32B)。
3. 数值预算轴曲线图 → **否**(「dose-response」词纪律只留给 α-sweep;B0P 非预算档;跨 tag 混画踩 v1.56 教训);可选替代=必5③ 分类轴小板。
4. mechanism schematic 独立 float → **否**(超 float 账;fig:rq2 降 supp 后 §5 零视觉的问题由 A1 文字段+可选 W-A supp 表承担)。
5. mechanistic-interpretability 正文塞词 → **否**(cargo cult+R3 火力点自抬标准);表单关键词勾选。
6. 族内单调置换检验/高低端 cell 对比 → **否**(事后选检验=forking paths;新增 .042 边缘 p 稀释「Holm 下全活」底盘)。
7. 饱和句配对检验 → **否**(等价主张靠不显著撑不住);描述性措辞版。
8. sequence-level paraphrase ablation → **否**,零卡条件分析替代(C4)。
9. W-B 升正文 → **否**(prereg:75 终裁 appendix;升=踩「跑后改动自动降级」条款);正文一句 cross-ref 合法。
10. eval-protocol 建议成节/段落群 → **否**(超页+自拆 SCR premise 立界);Discussion ≤3 句。
11. 新建 paper/writing-spec-v2.md 并加冕「唯一写作真源」→ **否**(再造 ★1 复制面+第三真源声明);必1 的队列归一版替代。
12. Korbak/Baker 主动入引 → **默认否**(不递碰撞框架);7/14 触发器决定。

---

## 四、执行顺序建议(全部骑既有日历,不动冻结点)

- **7/7 深夜/7/8 晨(B1 之前)**:必1 队列归一 pass(1.5-2h)。
- **7/8**:B1(既定第一件)+必2 F3 CI 修(3h,亦属 bug-修例外)+硬伤3(15min)。
- **7/9–7/10**:硬伤2 logit-lens 口径统一(单一工单,一人执行:results.json 指针→draft 六处→fig2 规格)+硬伤4 G5 git 考古+卫生打包;C1/C2 零卡统计;B17(7/10 既排,含 RRs[0] 回填)。
- **7/11**:必3 relevance statement+§2 alignment 带(既排)+必4 ethics statement(前移至此)。
- **7/12**:必5 图1 打磨日执行单+abstract 三版重写(A8/H2)。
- **7/13**:H3 冻结数字清单+B14/[pending] 清零+E2 的 LLM 审稿模拟→初稿 v2 冻结。
- **7/14**:内审红队①+W 系列裁决(输入:C1 聚类统计+D3 附录预写+硬伤4 披露)+track 拍板+查新(B4 加词)。
- **7/14 后随裁决**:A1/A4/A6 承诺层线写作包;C3 MEMIT 线三选;E3/E4/E5/D1(B18 工程,前移件按各自死线)。

---

## 五、台账

- **扫缺**:workflow `wf_2a085242-f1e`,10 finders(novelty/litsweep/pillars/methods/rubric/figures/redteam/freethinker/coverage/fatal)+1 critic,~120 条原始 findings(全文存 session scratchpad `gap_findings_full.json`),1.76M tokens/243 tool calls,零失败。
- **对抗验证**:workflow `wf_a2802b13-caf`(T1–T5)+`wf_3ce395ee-d3c`(G0 补验),6/6 WEAKEN;每条裁决的 strongest_attacks/what_survives/amended_recommendation 已吸收进 §一,原文存各 workflow journal。
- **本人亲核件**:F3 伪复制(metrics.py:184-233 ✓)与 es_drop 反例(metrics.py:236-273 ✓,对抗方正确)、plots.py 骨架现状(135 行 ✓)、relevance 全仓无成文(grep ✓)、results.json 全量逐块读、draft.md 全文读。
- **外部验真(入文前仍须逐篇 WebFetch 复核)**:2606.25013 / 2606.13603 / 2605.06723 / 2509.23676 / 2505.15214(EMNLP-25)/ 2510.20956 / 2502.12893 / 2504.17704 / 2509.18382 / 2604.19089 / 2503.01751 / 2603.20795 / 2510.00625 / 2603.26410 / 2403.14364(WikiFactDiff)/ 2507.11473 / 2503.11926 / aaai.org CFP 三页 / anthropic.com workspace 发布页 / LessWrong Nanda review / aclanthology 2025.acl-long.868。
- **与 7/3 终审的关系**:B1–B26 裁决全部维持;两处**前提更新**(非翻案):①死线多源坐实 7/21/7/28/7/31(内部线不动,余量+1 天);②「Phase-1 只看 abstract/intro/图1」无 CFP 依据(实为 3 人审全文+AI 辅助、无 rebuttal)——全文一致性(B1/B14/[pending])从门面项升为 Phase-1 生死件,是本报告多处优先级判断的依据。
