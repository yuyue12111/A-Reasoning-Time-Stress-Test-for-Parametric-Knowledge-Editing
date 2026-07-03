# 终极写作前评审 · Charter(2026-07-03 立,plan v1.57 时点)

## 0. 你是谁、唯一标准

你是**独立评审员**(与建设 session 上下文隔离的 fresh eyes)。本仓库是 AAAI-27 投稿「越想越退 / Thinking Undoes Editing」:量化 ROME 参数编辑在 R1 蒸馏推理模型上随思考预算被推翻的现象+机理+training-free 修补。

**唯一标准,一切输出服务于它:距离一篇 solid accept / strong accept 的 AAAI 论文还有多远、还差多少。**

角色约束:
- **只读 + 联网搜**。不修任何现有文件;唯一的写 = 把评审报告写到仓库根 `终极review.md`(新文件)。
- **不写执行计划/甘特**——那是建设 session 拿你的报告后的活。你只判距离、排差距、给砍单。
- 评的是「**以 results.json 的证据面,假设写作执行完美,能写出的最好论文**」;`paper/draft.md` 是 6/24 的 stale 快照(落后全部近两周结果),只作对照物(哪里 overclaim/哪里欠账),**不评它的现有文字质量**。
- 数字一律以 `paper/results.json` 复核为准;若本 charter 与 results.json 矛盾,以 results.json 为准并在报告里标出。

## 1. 死线与格式(判"来得及吗"用)

- abstract **2026-07-20**、全文 **2026-07-27**(UTC-12),补充材料 +3 天。今天 7/3 → 17/24 天。
- 正文 **7 页 + 参考文献**;两阶段评审:**Phase 1 只看 abstract/intro/图1,必须独立讲完整个故事**。首选 AI Alignment track(编辑作为安全干预在 test-time compute 下失效),备选 Main Track。
- 资源现实(判可行性):全离线 GPU 平台(H200 fp32/H100),用户人肉传文件、手动排队;写作目前冻结(你的报告是解冻门);LaTeX 未建(draft 是 markdown);plots.py 骨架有、图未定稿。

## 2. 读单(按序;全部在仓库根或所注路径)

1. `CLAUDE.md` — 项目约定、硬约束、**口径纪律**(EasyEdit rewrite_acc ≠ 生成式 ES_b,永不混排;单条编辑协议)。
2. `plan.md` 头部 v1.x 变更日志 — **v1.50 起精读到 v1.57**(第五轮增量实验的全过程:F1/F2/F3/M1/Cap1-3/S1 + 污染 bug + clean 重跑);更早条目扫读即可。§8=查新维护。
3. `paper/results.json` — **唯一数据真源,逐块读**。重点:`emergence.percase`(clean)、`emergence.cap3_netclr`、`base_probe`(6 尺度+`f1_edit_specificity`+`_adversarial_verified`+`_six_scale_summary`+`_pending_draft_edits`)、`f2_zerothink_deconfound`、`f3_sampling_robustness`、`rq3`(suppress 各臂+`clr_split_M1`)、`rq2_taxonomy`(含 `neutral_rerun_S1`)、`multihop`、`metric_validation`、`genbench`。
4. `depth-plan.md` — 四轮 review→实验的血统(§第二~五轮),含每项的 kill 判据与红队注记。
5. 三份前置第一性 review(**已被 §四/§五 回应,别重复它们的工作**):`codex和claude的第一性review.md`、`第一性review v2..md`、`第一性review 增量实验.md`。
6. `paper/related_work.md` — 6/24 撞车排查详录(4 HIGH 近邻)。
7. `paper/draft.md` — ⚠stale,只作对照。
8. `analysis/00–09_*.md`、`RUNBOOK.md`、`sumandplan1.md` — 按需。
9. 本地 `results/` 有分析产物可 spot-check(`percase_clean.json`、`cap3_clean.json`、`m1_clrsplit.json`、`necessity.json`、`a3_neutral/`、`mh/`);**原始 per-case 生成 jsonl 在离线平台,本地没有**——results.json 是蒸馏层,这是既定架构不是隐瞒。

## 3. 证据现状速览(帮你起步;逐条可在 results.json 复核)

**强项(带数字):**
- 现象(32B headline):ES 降幅 0.106 [0.030,0.182] 显著;RR 0.193;逐条编辑→全预算生成→还原的单条协议。
- 三个去混淆全 CONFIRM:**F1** 编辑特异(未编辑 base 6 尺度 Δthink 全小[−0.021~+0.08],32B margin 0.214;全 6 尺度 margin>0 除 7B≈0)、**F2** 非空块模板伪影(RR: B0 0.000 ≈ B0P 0.040 ≪ B1 0.208)、**F3** 采样鲁棒(ES 降幅 采样 0.090[0.010,0.171] ≈ greedy 0.110;RR@B3 采样 0.264)。
- 涌现(清洗后):per-case 两级 cluster-robust **es_drop slope 0.109 [0.036,0.175] p=.003**(编辑特异、构造上非 base 底噪);within-Qwen 0.119 亦显著;rr 0.644 p=.052 擦边;**CLR 涌现经 Cap3 判为 base 底噪伪影已诚实退役**(net-CLR 0.049 含零)——这次自我纠偏本身可作方法学卖点。
- 机理(RQ2):logit-lens 非擦除(回退案例 100% cloze 仍预测 o_new——⚠此结果只记在 plan.md v1.25 变更日志(commit 2f6f1ec),**未入 results.json**,请顺带给这个记录缺口定价);**M1** within-case 中介(修复效应集中 CLR1 基线:T−N RR −0.289 p=.0002,CLR0 ≈0;2×2 中介 43% vs 4%);taxonomy 中性判官下 Bridge 81%、traceless=0(从不无声);necessity 19/19 走 re-derivation 路由。
- 修复(RQ3):链级 o_old 抑制(scope=think)RR 0.193→0.085、ES@B3 0.495→0.631、Loc 不变;sup battery T−P 全排零。
- 度量:判分 κ=0.836(答案级);去污词边界 hit(曾抓 aliases 灌水 bug 并修);S1 判官敏感性(3/18 pop flip)诚实报。
- 跨族:Llama-8B CLR 0.340 ≈ Qwen-Math-7B 0.335(非 Math 特化);70B es_drop 0.11 显著端点;6 尺度 base 表全(LEVEL vs CHANGE 去混淆框架)。

**已知短板(K1–K12;你的任务不是重新发现,是【排序定价】+找我们没想到的):**
- K1 headline 单编辑器(ROME;MEMIT 只消融、AlphaEdit 无)。
- K2 headline 单数据集(CF;MQuAKE 2-hop 探针 0.188 有、zsRE 清洗了未主跑)。
- K3 K=2 family;rr 涌现 p=.052 擦边(es_drop 显著是主腿)。
- K4 M1(修复因果)仅 32B/CF 单尺度。
- K5 自然生成必要性不闭(E-CHAINSUB 未跑;quoted_span provenance bug 未修)。
- K6 V1 未做:CLR 的 CoT scorer 极性未验(`metrics.py` hit(cot,o_old) 无否定检查,"not French but Bolton" 会记 CLR+;κ=0.836 只验了答案级)。
- K7 M4/M5/K2′/G1 未做(placebo 强度上限/反思标记臂/无先验 confabulation 测试/cond-c 部署盲区;plan 排 7/27 档)。
- K8 F1 margin 是跨口径近似差(edited RR b0ok 门 − base 无门 Δ);base Δ 的 per-case 配对 CI 未做。
- K9 8B Loc 0.835 边缘(诚实标 locality-marginal);70B 用 cf100 池。
- K10 draft 全面 stale + `_pending_draft_edits` 未落 + LaTeX 未建 + 图未定稿。
- K11 genbench 部署门:scope=all 是病态上界(RQ3 已 SURVIVE-WITH-REFRAME 改写)。
- K12 撞车(6/24 时点):4 HIGH 近邻——SCR(He et al. 2505.18690)、ThinkEval(2506.01386)、Superficial Editing(Xie et al. 2505.12636)、DISCO(Sun et al. 2406.02882);现象/机理/修复各被部分占位 → 当时判 AAAI borderline,MECH-led 框架因此而选。

## 4. 交付物(全部写进 `终极review.md`;按 A–H)

- **A 判档**:以现证据+完美写作,落在哪档(reject / borderline / weak accept / accept / strong accept)?按 novelty / significance / soundness / clarity-潜力 / reproducibility 五维拆,各给一句依据+置信度。
- **B 差距账**:每个缺口(含 K1–K12 + 你新发现的)→ 动哪个维度、补上后 Δ(录取概率)、成本(本地零卡/平台卡时/写作/天数)、**close 还是 drop 的裁决**。按 Δ÷成本 排序。**明确标出"补了不动针、该放弃"的项**——17 天里做减法比做加法重要。
- **C 7 页砍单**:哪些进正文、哪些去附录、哪些整个不讲。特别裁:CLR 退役怎么讲(方法学卖点 vs 一句带过)、6 尺度 base 表值不值一张正文表、S1 软化的篇幅。
- **D 拒稿预演**:最可能的 3 条拒稿理由(具体到哪条 claim/哪个数字),每条给 preempt(改措辞?补数?移限制节?)。
- **E 写作解冻表**:哪些章节的数据**现在已定稿可写死**;哪些必须等 V1/M4/M5/K2′/G1 的结果;这些未做项**对录取真有影响吗**(逐个判:必做/可做/放弃)。7/20 倒推写作必须 ~7/8 开动,你的表决定并行结构。
- **F 查新(联网,必做)**:6/24 后未再查(plan §8 周一纪律,7/6 到期,本次并入)。搜 2025-06-24 → 今天的新工作:knowledge editing × reasoning/CoT/test-time compute、editing robustness、reflection undoing edits、R1-distill editing 等(§8 有关键词)。核 4 HIGH 近邻有无新版本/新后续;有无**新撞车**;MECH-led 头牌是否仍清;给一段可直接用的定位语句。
- **G framing 复核**:MECH-led(机理+修复当头牌、capability 降 supporting)是 6/30 在「CLR 涌现被认为成立、es_drop 未复活」的证据结构下定的;7/2 clean 重跑后结构变了(es_drop 显著+编辑特异,CLR 退役)。**头牌选择现在还最优吗?**(结合 F 的撞车现状判;若建议改,说清改成什么、代价是什么。)
- **H 总判**:三句话——距 solid accept 还差什么;距 strong accept 还差什么;**单点最高杠杆**(17 天内做哪一件事对录取概率增量最大)。

## 5. 禁做清单

1. 不改任何现有文件;报告只写 `终极review.md`。
2. 不写执行计划/时间表(判"来得及/来不及"可以,排日程不行)。
3. 不把 §3 已知短板当"发现"重报——除非你判它**比我们以为的更/不致命**,那要说清为什么重定价。
4. 不评 stale draft 的文字;但 draft 里与 results.json 矛盾的 claim(overclaim)**要点名**(`base_probe._pending_draft_edits` 已列一部分,可核对补全)。
5. 别信任何二手转述(包括本 charter §3)——承重结论一律回 results.json/analysis 复核原始记录。
