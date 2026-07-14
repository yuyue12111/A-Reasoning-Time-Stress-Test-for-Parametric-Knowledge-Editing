# paper/draft.md 缝合审查记录(workflow paper-draft, run wf_c17725a9, 2026-06-24)

> draft.md = Abstract(3 变体)+§1–§7 LaTeX 草稿,唯一数据源 paper/results.json,去污词边界口径。
> 本文件 = 缝合智能体的一致性修正 / 红线核验 / [pending] 路线图。投稿前照 §todos 逐条收口。

## 一、缝合时已修的章间不一致(均已落进 draft.md)

缝合后已统一,但缝合前各章草稿之间发现并修正了以下不一致(均已在 draft_md 中统一,以 results.json 为准):

1. [已修·数值] §5 RQ2 草稿原写 "$g_{56}=17.8$ ... where the ROME edit dominates and produces the intact top-layer $o_new$",把 layer 56(峰值 17.803)当成"顶层"。results.json 的 layers_sampled 顶端是 layer 64,gap=11.569(不是 56)。逻辑瑕疵:峰值在 56、最终层(64)是 11.569。已统一改为 "peaking at $g_{56}=17.8$ and remaining large at the final layer, $g_{64}=11.6$",§5 正文与图注同步。原 §5 图注亦更正。

2. [已修·术语] §4/§1 中 CLR 全称在不同草稿里出现 "chain leakage rate"(§1)、"chain-leak rate"(§4)、"Chain Leak Rate"(§3)。统一为 \textbf{Chain Leak Rate (CLR)} / 正文小写 "chain leak rate"。RR 统一 "Reversion Rate / reversion rate";ES drop 统一 "ES drop / thinking tax"。

3. [已修·引用别名] §2 草稿把 he2025benchmarking 标 "(ReCoE; ...)" 而 §1/§5 标 "(SCR)"。related_work.md 显示该篇(2505.18690)同时含 SCR(上下文检索方法)与基准。全文统一为 "SCR/ReCoE",避免读者误以为两篇。

4. [已修·引用 key] §6 草稿 DISCO 用 \cite{disco2024},§1/§2/§7 用 \citep{sun2024disco}。统一为 \citep{sun2024disco}(全文同一 key,待 .bib 对齐 arXiv:2406.02882)。ThinkEval 在 §1 草稿误作 baser2026thinkeval(年份 2026),§2 草稿作 baser2026thinkeval 亦有;related_work 标 2506.01386(2025 投稿)。统一为 baser2025thinkeval。

5. [已修·符号] ES drop 在 Abstract 用 "$-10.6$pp drop"(口语,强调降幅方向),在表/正文用 results.json 正号 +0.106。二者口径一致(drop = ES@B0 - ES@B3,正号=下降),已在 §1/§4 显式写 "drop of 10.6pp",修复后写 "+0.106 → -0.035"。无矛盾,但投稿前需在某处加一句符号约定脚注(见 todos)。

6. [已修·scope 记法] 各章混用 $\text{scope}{=}\texttt{think}$ / \textsc{scope}{=}\textsc{think} / \texttt{scope=think}。统一为 \textsc{scope}{=}\textsc{think}(正文)、\texttt{scope=think}(§7 一处行内已保留,无歧义)。

7. [已修·章节交叉引用] §3 草稿 RQ2 标签写 \S\ref{sec:rq2} 但 §5 草稿自身 label 给的是 sec:rq2;§4 草稿用 fig:fig1 而 §1/outline 用 fig:capability。统一图标签 fig:capability(图1)、fig:rq2(图2);节标签 sec:intro/related/setup/wordbound/rq1/rq2/rq3/limitations。§1 脚注原指 \S\ref{sec:fix},已改为 \S\ref{sec:rq3}。§3 word-boundary 节原无独立 label,§4 引用它,已加 sec:wordbound。

8. [一致·已核对无冲突] capability 五数(ES@B0/B3、es_drop、CI、RR、CLR)在 §1/§2/§3/§4/§7 各处出现值与 results.json 逐一吻合;RQ3 六数(RR/ES_B3/ES_drop/CLR/Loc off→on)在 §1/§2/§6/§7 吻合;logit-lens(intact 100%、edit_layer 12、n_layers 64、g_8=-0.246、g_12=-0.351)吻合。base_probe 0.59 在 §3/§4/§7 一致(注:此数不在 results.json,见 redline/todos)。

9. [已修·14B CI 补全] §1 草稿 14B ES drop 只写 "(n.s.)" 未给 CI,§4/§7 给了 [-0.030,0.110]。§1 已补 CI 与 §4/§7 一致。

## 二、红线核验结论

缝合后逐条核对七条红线 + outline 红线,未发现越线;以下为核验结论与一处需作者补证的弱点:

① 不宣称平滑 scaling law —— 合规。Abstract 三变体均收尾 "monotone trend, not a smooth law";§1 贡献1、§2 现象块、§3 统计块、§4 "Honest scoping"、§7 首段均显式声明"三点单调趋势非平滑 scaling law + RR CI 两两重叠 + ES 降幅仅 32B 显著"。无 "scaling law" 正面主张。

② RR≈0.19 不说 ">0.20" —— 合规。全文 RR 一律写 0.193 / $\sim$19\% / $\approx0.19$;§4 "Honest scoping" 与 §7 "Effect magnitudes" 各有一句 "we do not round it past 0.20"。无任何 >0.20 表述。

③ ΔCLR 部分循环 → 主证据用 ΔRR/ΔES —— 合规。§1 脚注、§2 修复块、§6 专设 "On the partial circularity of $\Delta$CLR" 段、§7 专段,四处声明 scope=think 压的就是 CLR 计数的链 token,主证据切到答案级 ΔRR/ΔES。Abstract 变体 A 完全不提 CLR 修复值;变体 B/C 不把 ΔCLR 当修复战果(只提 RR/Loc)。表 tab:rq3 列出 CLR 0.545→0.263 但正文不以其为主张。合规。

④ 现象/非擦除/修复各有强近邻、不宣称"首次发现" —— 合规。§1 "Honest positioning"、§2 四线立界 + "Summary of distinctions"、§5 "Relation to superficial editing"(明写 "We do NOT claim to be the first")、§7 "Positioning relative to prior work" 均诚实对标 SCR/ReCoE(2505.18690)、Superficial Editing(2505.12636)、DISCO(2406.02882)、ThinkEval(2506.01386),并把独有点限定为 capability-emergent + chain-only 因果 + native R1 + 词边界口径。无 "first / novel phenomenon / novel mechanism" 主张。

⑤ 7B 是 Qwen2.5-Math 特化(confound,base_probe 0.59) —— 合规但有一处需补证(见下)。§3、§4 "The 7B confound"、§7 "The 7B endpoint" 三处声明 Math 特化 confound 且用 base_probe 0.59 排除"纯不知道"解释,未把 7B↔32B 落差全部归因纯能力。capability claim 以 32B 显著为锚。

⑥ 数只用 results.json,不编造 —— 合规。逐一回溯:capability 块全部、rq3 六数、logitlens(intact 1.0 / layer 12 / 64 层 / g_8 / g_12 / g_56 / g_64)均来自 results.json。无编造数。
   ⚠ 唯一例外(非越线但需补出处):**base_probe 7B=0.59 不在 results.json**(来自 prompt 红线⑤与 outline §诚实口径),全文三处(§3/§4/§7)引用。这不构成"编造"(用户在 prompt 与 outline 中均给出该数),但 §6.x 正文未给该数权威出处。投稿前须:在 results.json 增 base_probe 字段,或在 §3 加脚注指向 analysis 笔记;否则审稿人无法溯源。已列入 todos。

⑦ genbench/1.5B/Llama-8B/70B 未出 → 标 [pending] —— 合规。genbench 全文凡提及处(Abstract 未写"不伤通用能力"只写 "without hurting locality";§6 表注、§6 Scope、§7 deployment 段)均标 [pending];1.5B/Llama-8B/70B/跨族曲线在 §1/§3/§4/§7 均显式 [pending],头牌限定 Qwen 三点。Abstract 三变体均未越写跨族/跨规模/通用能力。

结论:**无越红线处**。一处弱点 = base_probe 0.59 出处链不完整(已转 todos,投稿前必补)。

## 三、[pending] 与待补(投稿前路线图)

汇总全文 [pending] 与待补(按优先级):

== A. 实验未出,正文已显式标 [pending],出后回填 ==
1. [pending] genbench 通用能力门(GSM8K/MATH off vs on),results.json rq3.genbench 全 null。影响:RQ3 收口("不伤通用能力"现仅 by-construction + Loc 旁证)、§6 表 tab:rq3 注、Abstract 变体 B/C 末可补 "and general reasoning ability"。**RQ3 camera-ready 前必填。**
2. [pending] 第 4 个规模点 / 第 2 个族:Qwen-1.5B(低端)、Llama-8B(破 Math 特化 confound)、70B(高端)。影响:§1 贡献1、§3、§4 "Coverage"、§7 "trend not scaling law" 与 "single dataset" 段。补点后可把头牌从"Qwen 三点趋势"升级到 outline 想要的"跨族跨规模曲线",并强化 capability claim。
3. [pending] RQ2 链行为分类 recall/bridge/dismiss 各类计数(多判官面板,32B)。§5 表为 [pending] 占位,**严禁编造计数**。
4. [pending] RQ3 稳健性消融:α 扫、scope=all、14B 复制 RQ3、序列级变体堵 paraphrase 旁路(残留 CLR 0.263)。§6 "Scope and caveats"、§7 ΔCLR 段。
5. [pending] 第 2 编辑器(MEMIT/AlphaEdit)+ 第 2 数据集(zsRE/MQuAKE)。§7 "single dataset" 段。
6. [pending] 7B genuine-recall 同判官面板补判(口径一致,现 6/100)。

== B. 出处/数据治理(投稿前必做) ==
7. ✅[已解,2026-06-24] **base_probe 7B=0.59**——已在 results.json 增 `base_probe.7B`{answer_old_b0 0.59 / answer_old_b3 0.67 / chain_old_b3 0.755},溯源链补全。draft §3/§4/§7 引 0.59=answer_old_b0。(投稿前仍可在 §3 加脚注指向 analysis 笔记的原始 run。)
8. 确认 7B 精确 edit layer:CLAUDE.md 防雷清单说 7B 锁 layer5,但 §3 草稿写 "early-middle layer"(未钉死,因 results.json 无 per-size layer 字段)。camera-ready 前定:写 layer5 还是保留模糊。注:logit-lens 的 edit_layer=12 是 **32B**(results.json.logitlens.edit_layer),与 7B layer5 不冲突,勿混。

== C. 引用/.bib(投稿前逐篇 WebFetch 验真,防 agent 幻觉)==
9. 所有 \cite key 为占位,待建 paper/refs.bib 对齐:meng2022rome / meng2023memit / fang2024alphaedit / zhong2023mquake / xu2024kele / yao2025mirage / li2023iti / chuang2024dola。
10. HIGH 已核实可直接进 bib(related_work.md WebFetch 过):he2025benchmarking=2505.18690、xie2025superficial=2505.12636、sun2024disco=2406.02882、baser2025thinkeval=2506.01386。
11. anon2025fromreasoning(From Reasoning to Answer, 2509.23676)= 因果前提引用,**作者匿名占位,须补真实作者**。
12. related_work.md 标注的 2026(26xx)近邻(One Mask 2605.28839 / MechLens 2606.07978 / MEGA 2603.20795 / Edit-via-Background-Stories 2602.02028 / CoRect 2602.08221 / Principled-Eval 2507.05937 / Edit-Locality 2601.17343)**均未逐篇 WebFetch 验真,本 draft 未写入正文**;若投稿前要引,必须先逐篇验真。
13. \citet/\citep 形式与最终 bibstyle(AAAI)对齐。

== D. 图表/工程 ==
14. 图1(fig:capability):ES 降幅/CLR/RR × 规模 + ES@B0/ES@B3 双线。src/plots.py 骨架待建。
15. 图2(fig:rq2):逐层 gap g_ℓ(32B,reverted),8–12 层负 dip,峰 17.8@layer56,最终 11.6@layer64;标注 edit layer=12、intact=100%。从 results.json.logitlens.gap_sampled 出图。
16. 所有 \ref/\label(sec:intro/related/setup/wordbound/rq1/rq2/rq3/limitations、tab:capability/tab:rq3、fig:capability/fig:rq2)待 LaTeX 主工程落定后核对。

== E. 写作收尾 ==
17. Abstract 三变体三选一,选定后微调到精确 150 词。
18. 投稿前加一处 ES drop 符号约定脚注(drop = ES@B0 − ES@B3,正号=下降;Abstract 用 "−10.6pp drop" 口语、表用 +0.106,二者一致)。
19. CLR 单调性可选补 CLR CI 两两重叠说明(results.json 有 clr_ci),与 RR 同处理,若审稿要更严。
