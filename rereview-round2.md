# rereview-round2.md · 全文对抗 re-review(W1/W2/W3 后)归档

**来源**:workflow `wa6rxz0qp`(2026-06-30)。3 个独立 hostile AAAI 审稿人读**全文草稿 + results.json + depth-plan.md**(不是之前的 abstract,是现在的全文 + W1/W2/W3 证据)→ 1 个综合器对照我的 tier-A/B 草案重排优先级。本文件是原始记录;可执行计划见 `depth-plan.md` §第二轮。

## 三审评级 + 一句话
- **R1 统计/方法学 = borderline**:「capability-emergent」头牌靠 6 点 pooled slope,显著性是把两条短族曲线当独立点制造出来的;只 2/6 cell 个体显著、单编辑器/数据集、多跳单模板脆弱 —— 经验骨架太薄,撑不起 title。
- **R2 新颖性/定位 = borderline**:每个配料(现象/非擦除机理/training-free 修复/指标洁净)都已让给前作;novelty delta 缩到「capability-emergent」一个词,而其证据比 framing 薄 —— 可被读成「SCR/ReCoE 在 R1 上的强复现 + 新 framing」而非新发现。
- **R3 机理/因果 = weak-accept**:机理核心比 prose 薄 —— 「绕过完好编辑」靠单方法单探针 logit-lens(n=19 pooled),RQ2(edit-intact)与 RQ3(链抑制修复)有「同一 logit 事实读两遍」的循环嫌疑;**自然(未干预)生成里的必要性从未证**。

## 收敛弱点(综合器,按危险度)
| # | 弱点 | 提出者 | 严重度 | 我的计划覆盖? |
|---|---|---|---|---|
| 1 | **【FATAL】**「capability-emergent」靠 6 点 OLS,p<0.002 来自 point-resample 同 6 点(`emergence_regression.py:boot_slope_ci` idx=rng.integers(0,n,n), n=6);`family_controlled` 是 6 点 fixed-dummy 非 per-case 混合效应。within-Qwen ES/RR CI 含零,唯 CLR 单族存活 | stats+novelty | fatal/THREAT | **错放 B3 GPU 后**(其零卡半=per-case 回归才是 fix) |
| 2 | 仅 2/6 cell 显著,且这俩(32B/70B)正是最多 caveat 的点(Math 特化顶/n=187 有偏丢 13/跨架构 hparams) | stats | major/THREAT | GAP(纯重制表) |
| 3 | **自然生成里 route-around 必要性未证**,但 prose 照断言「链重推」「绕过」 | mechanism+novelty | major/THREAT | GAP(我只命名残余、没给实验) |
| 4 | 单编辑器(ROME)+ 单数据集(CF),title 过宽 | stats+novelty | major/THREAT | 主动 DROP(可辩护,零卡收紧 title 即可) |
| 5 | 去污 word-boundary scorer(<4 字 alias cutoff)是承重 CLR 指标 **且** 未预注册的研究者自由度,可能差异化缩小模型 CLR、制造单调上升 | stats+novelty | major/THREAT | GAP(零卡重打) |
| 6 | RQ2/RQ3 可能同一 logit 读两遍(循环);破它的 E-CHAINSUB 被降 camera-ready | mechanism | major/THREAT | B2(对;但需零卡 name-and-bound 段做滑窗保险) |
| 7 | W3 单模板 P27 扛、边际反向 | stats | major | 已处理边际(within-case);单模板脆弱=零卡 framing 审计、明标 single-template pilot |
| 8 | logit-lens 中层「旧事实占优 layer8-12」靠极小 gap(−0.25~−0.35)、无 CI、无 n、单探针 | mechanism | major | B1 部分(widen 池);**缺 per-case g_l bootstrap CI** |
| 9 | RQ2 taxonomy n=19(4/5/10)撑不起「RO 本身 capability-emergent」 | stats+mechanism | minor | GAP(免费软化文字) |
| 10 | 部署门 Δ+0.005/0.000 是欠功效 null 当 equivalence | mechanism | minor | A2(TOST 边界) |
| 11 | 只测 native-R1;非 R1 prompt 思考可能同样侵蚀→「native-R1」novelty 塌向「any CoT」 | novelty | minor | A1(零卡 scope 段) |
| 12 | 3 相关指标×6 cell×多次 refit 无多重比较校正 | stats | minor | GAP(免费一句 confirmatory-vs-exploratory + Holm) |
| 13 | W1 placebo 是 freq/len-matched,但非「任意强竞争答案 token」→ 欠证 o_old 特异 | mechanism | minor | GAP(零卡软化「meaningful competitor above inert placebo floor」) |

## 综合器裁定:最大残余被重定
> **不是**团队预命名的「自然生成必要性」—— 那个**零卡可堵**(用 RQ2 判官已抽的 17/19 Bridge span,在未干预 B3 链上报 P(回退|链含逐字 Bridge 重推子句) vs 无,且 Associative/implicit-leak=0/19 帮故事)。**更大的残余 = title 名词「capability-emergent」本身的统计骨架**(2 审,1 fatal+1 major,均 threatens):6 点 OLS + point-bootstrap = 制造显著;fix(per-case 混合效应回归 + family 随机效应)**零卡在盘数据上今天就能做**,却被我放进 7/27 GPU 窗后 —— 把唯一 fatal 弱点的 fix 留在 abstract 死线之后是优先级错误。

## 计划裁定
方向对(深度>广度;DROP MEMIT/AlphaEdit/zsRE/更多尺度可辩护)。但 **tier 分配相对死线错配**:(1) 唯一 fatal 的 fix 的零卡半必须升 Tier-A;(2) 两个零卡、审稿人开方、abstract 关键的 fix 完全缺失(自然生成必要性观察检验 + CLR scorer-robustness 表);(3) 三个免费文字 fix 缺失(70B with/without-13 敏感行进 Table 1、§3 confirmatory-vs-exploratory + Holm、软化 RO-capability-emergent)。A1/A2/A3 保留;B1/B2 正确留 Tier-B,但 B2 循环需零卡 name-and-bound 段做滑窗保险、B1 带零卡 per-case g_l CI。**净:abstract 关键集比 A1-A3 大得多,且当前漏掉 1 fatal + 3 major+threatens 的 fix —— 全部零卡。**
