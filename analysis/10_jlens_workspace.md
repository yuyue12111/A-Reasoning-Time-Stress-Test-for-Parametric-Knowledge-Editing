# 10 · Anthropic「Global Workspace / J-lens」(2026) 与本项目的方法论对接

来源:https://transformer-circuits.pub/2026/workspace/index.html(2026,transformer-circuits;
用户 7/3 提示。本笔记基于一次 WebFetch 摘要;**写作期引用前须逐节复核原文**,per 终极review 外部事实纪律。)

## 他们做了什么(与我们相关的最小提炼)

- **核心主张**:LM 维持一个「全局工作空间」= 一小撮**可言语化**的中层表征,支撑灵活推理/内部计算/
  deliberate inference;其外是大得多的**自动处理**(automatic text-processing)。可读、可改、可干预。
- **J-lens(Jacobian Lens)**:某激活对某 token 产出概率的**平均线性化因果效应**,
  J_ℓ = E[∂h_final,t′/∂h_ℓ,t],在 ~1000 条预训练风格 prompt 上平均。配套:lens 坐标 patching
  (换概念保正交分量)、稀疏分解(k=10-25 向量重构)、top-k 消融、cosine 探针。
- **与我们相关的现象**:
  - 未言语化中间步的表征可探可干预(two-hop 50 题;swap 中间概念 → 结论翻);
  - 自动任务(续写)绕过工作空间,灵活任务(显式报告/推理)必经之(swap 只翻后者);
  - 消融工作空间 → 多跳推理塌、情感分类无损(criticality 随推理需求 scale);
  - 「ignition」:工作空间 onset 层出现锐利范畴切换(非平滑插值)。

## 与本项目的同构(为什么这是我们的理论外壳)

| 他们 | 我们(已有数据) |
|---|---|
| 自动处理(工作空间外) | **B0/ZeroThink 直答**:编辑 holds(32B ES 0.625,RR 0.000)——ROME 改写的自动回忆通路 |
| 工作空间(真推理才接管) | **B1+ 真链**:RR 跳到 0.208-0.264;**F2 的 B0P(有块无内容)≈B0** = 工作空间需真推理内容才 engage |
| 工作空间在中层、占小容量 | 我们编辑在相对深度 0.19(layer 12/64)≈ 自动通路;**编辑从没写进工作空间** → 思考时工作空间从残存关联知识重推 o_old,答案跟工作空间走 |
| swap 工作空间内容 → 结论翻 | **M1/链级抑制**:堵链内 o_old(token 级 proxy)→ 答案修复,效应集中 CLR1 层 = 行为级的同一因果 |
| 多跳靠工作空间(消融即塌) | multihop 传播侵蚀 + G1(抑制器在 2-hop 上无侧伤,方向为保护) |

一句话版(供 §5/§7 Discussion,写作期打磨):
> Parameter editing rewrites the *automatic* recall pathway; budgeted thinking routes the query through
> the model's verbalizable *workspace*, which re-derives the pre-edit fact from surviving associative
> knowledge — and the answer follows the workspace, not the edited pathway. Our ZeroThink/LessThink
> contrast (F2), chain-content mediation (M1), and chain-only repair are behavioral signatures of
> exactly this division; [workspace paper] provides the representation-level frame.

**注意分寸**:这是**收敛性框架**(converging frame),不是我们的证据;引用时 hedge(their onset-layer
数字是他们模型的,不跨模型硬移植;我们没跑 J-lens,不宣称表征级证据)。

## 分层裁决(v1.59 纪律:17 天做减法,B27-B33 不复活)

### ✅ 投稿版(零成本,吃)
1. **§5 或 §7 Discussion 一段 + 引用**(上面那句的打磨版):给机理头牌一个 2026 年的表征级理论锚——
   MECH-led framing 的 novelty 叙事更硬("我们的行为学发现有独立提出的表征级框架呼应")。
2. **§2 related 一行立界**:他们研究工作空间本身,不研究编辑×推理;我们给出该框架在
   knowledge-editing 安全域的首个行为学实例。无撞车(他们零编辑内容)。
3. **7/6 周一查新加词**:global workspace / verbalizable representations / Jacobian lens
   (防这条线的 follow-up 撞我们)。

### 📦 camera-ready / 下一篇(真实验,现在不做)
1. **★J-lens 式「无声 o_old」探针 = 诚实残余#1 的非循环解**:E-CHAINSUB(S5)因"破循环实验自身循环"
   被 DROP;J-lens 探针不看 token、直接探链生成期间 o_old 的**表征**是否在工作空间——
   "committed 回退从不 traceless" 可升级为表征级(若 held case 链里 o_old 表征也在但答案不跟,
   反而强化 M1 的 commitment 论)。这是本文方法论对我们**单点最高价值**的进口。
2. **表征级 swap 中介**:链生成中把 o_old↔o_new 的 lens 坐标互换 → 答案翻?= M1 的表征级升级
   (token 级抑制 → 概念级干预)。
3. **ignition 式 FlipPoint**:链内"承诺翻转"是否对应工作空间的锐利范畴切换(我们 FlipPoint 的表征级版)。
4. B23 的 logit-lens 若被审稿人打"近恒真",J-lens 的"平均化因果效应"是 camera-ready 的正统修法。

### ❌ 投稿版不做(诱惑但违纪)
- 在 32B 上实现 J-lens(1000-prompt Jacobian 平均 × 逐层):周级工程,烧掉写作窗,violates B18/日历。
- 用他们的 onset 层数直接写我们模型的工作空间深度:跨模型硬移植,会被打。

## 待办落点
- [x] 本笔记入库 analysis/10。
- [ ] `_pending_draft_edits` 加两条(Discussion 段 + §2 立界行)——写作 7/8 解冻时执行。
- [ ] 7/6 查新加词(行政线提醒)。
- [ ] camera-ready 三件挂 plan(不占 7/27 前任何窗)。
