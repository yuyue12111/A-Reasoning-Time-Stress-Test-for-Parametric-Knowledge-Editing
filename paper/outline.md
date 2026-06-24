# Paper 骨架 · 「越想越退 / Thinking Undoes Editing」(AAAI-27)

> 状态:2026-06-24 初稿骨架(RQ1/RQ2/RQ3 数据已到,genbench 安全门跑中)。所有数为**去污判分**口径
> (metrics.hit 词边界 + 丢 <4 字符别名;substring 旧数已作废,见 plan v1.21)。abstract 7/20 / 全文 7/27。

## 工作标题
**Thinking Undoes Editing: Test-Time Reasoning Erodes Parametric Knowledge Edits, and a Training-Free Fix**

## 一段式 abstract(草)
参数化知识编辑(ROME/MEMIT)常以**零思考**下的成功率衡量。我们发现:在 R1 式**推理**模型上,随
着自然 chain-of-thought 展开,编辑被系统性侵蚀,**且随模型能力增强而加剧**——编辑成功率(ES)的思
考降幅在 7B 上不显著、到 32B 达 −10.6pp(显著),旧答案在 ~55% 的推理链中重新浮现(CLR)、并把
~19% 的零思考成功最终顶回旧答(RR)。机理上(logit-lens):**编辑在 cloze 处完好无损(回退案例
100% 仍预测新值)、被擦掉的事实仍编码在网络中段**——回退**不是**思考擦除了编辑权重,而是推理在链
内用旁系知识**重新推导**出旧事实、最终答案跟随了链。据此我们给出一个 **training-free 修复**:在思考
链(而非答案)中抑制被编辑事实的 token,即**砍半最终答案回退(RR 0.193→0.085)、消除思考降幅
(ES 降幅 0.106→−0.035)、不伤局部性与通用能力**;由于只干预链却改善了答案,这同时**因果坐实**了
"链内重推驱动回退"。我们另指出:基于子串/别名匹配的泄漏指标会把此类现象虚高 ~2×,须用词边界口径。

## 贡献(4)
1. **现象 + capability scaling**:测试期推理侵蚀编辑,且随能力涌现(零思考 eval 完全错过)。
2. **机理**:编辑完好被推理绕过(非擦除)、旧知识网络中段仍编码、链内重推、答案跟链(logit-lens 实证)。
3. **training-free 修复**:链级抑制,因果坐实机理 + 修复二合一,不伤 Loc/通用能力。
4. **方法学**:substring 别名判分把泄漏指标灌 ~2×(发现+修正),给生成式编辑评测一个 cautionary。

## 核心数(去污,n=200 除非注明)
| 模型 | ES@B0 | ES@B3 | ES 降幅 B0→B3 | RR(B3) | CLR(B3) |
|---|---|---|---|---|---|
| 7B (Math-distill) | 0.50 | 0.53 | −0.03 [−.11,.05] ns | 0.080 | 0.335 |
| 14B | 0.555 | 0.515 | 0.040 [−.03,.11] ns | 0.162 | 0.475 |
| 32B | 0.595 | 0.495 | **0.106 [.03,.18] 显著** | 0.193 | 0.545 |

- **RQ2 logit-lens(32B)**:回退案例 cloze 处编辑 100% installed(顶层仍 o_new);逐层 gap 在 8–12 层(编辑层 12 附近)转负=旧知识中段仍编码。
- **RQ3 修复(32B,n=200,scope=think,α=8)**:RR 0.193→**0.085**、ES@B3 0.495→**0.631**、ES 降幅 0.106→**−0.035**(思考税消除)、Loc 0.958→**0.964**;通用能力门(genbench)= 跑中。

## 章节 + 图表
- **§1 Intro**:零思考 eval 的盲区 → thinking 侵蚀编辑 + capability scaling;4 贡献;**图1**。
- **§2 Related**:知识编辑(ROME/MEMIT/AlphaEdit)、推理模型 test-time compute、knowledge conflict、activation steering(ThinkEdit)。
- **§3 Setup**:R1-Distill-Qwen-{7,14,32}B × CounterFact;单条编辑协议(edit→全预算生成→restore);思考预算 B0–B4;**生成式判分 ES/RR/CLR/Loc**(≠ logits 口径 rewrite_acc);**词边界判分**(§方法学坑)。
- **§4 RQ1 现象**:ES 降幅 capability-emergent + CLR/RR 单调随规模;**图1**(ES降幅/CLR/RR × 规模)。诚实:三点单调趋势(非逐对显著)、ES@B0 升而 ES@B3 降=思考税随能力增大。
- **§5 RQ2 机理**:logit-lens(编辑完好被绕过 + 中段编码)+ recall/bridge/dismiss/restate 链分类(多判官);**图2**(逐层 gap)。
- **§6 RQ3 修复**:链级 o_old 抑制;**表**(A/B:RR/ES降幅/Loc/通用能力 off vs on);scope=think 因果论证;消融(α/scope/14B/序列级)。
- **§7 Discussion/Limitations**:见下。

## 诚实口径 / Limitations(写作红线,不得越界)
- **不宣称平滑 scaling law**:三点单调趋势,RR 的 CI 两两重叠;ES 降幅仅 32B 显著。
- **RR ~0.19,不说 >0.20**;ES 回升幅度小(RR 基数小),主战场 RR/CLR/ES降幅。
- **ΔCLR(修复)部分循环**(scope=think 压的就是 cot 含旧)→ 主证据用 ΔRR/ΔES(在答案上、未直接压);残留 CLR 0.263 = paraphrase 旁路(v2 序列级消融)。
- **7B 是 Qwen2.5-Math 特化**:7B→14B 跳混 scale+特化(base_probe 证 7B 知道事实 0.59、非纯知识瓶颈);可选补 general-8B 拆 confound。
- **修复"用 o_old"**:编辑场景本就知道被编辑值(与 ROME 计算 update 同源),正当;部署只对编辑 query 生效→通用能力按构造不受影响,genbench 给最坏界上限。
- 单数据集(CF)、ROME 为主(MEMIT 早期数据);CLR 别名清洗后口径。

## 开放项(投稿前)
- [ ] genbench 通用能力门(跑中)→ RQ3 收口。
- [ ] 可选稳健性:α 扫 / scope=all / **14B 复制 RQ3** / v2 序列级堵 paraphrase / MEMIT 第二编辑器。
- [ ] 7B genuine-recall 用同一判官面板补判(口径一致;现 6/100,与 14B/32B 同法)。
- [ ] 图表出图(`src/plots.py` 骨架待建)。
- [ ] 行政:OpenReview 注册、CFP track 日期、每周一 plan §8 查新。
