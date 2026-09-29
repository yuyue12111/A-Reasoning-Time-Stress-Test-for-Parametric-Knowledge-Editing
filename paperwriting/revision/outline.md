# ARR 稿骨架（草案，随 Study 2 结果更新）

## 一句话
Direct-answer editing certifies an answer, not a belief that survives reasoning.

## 标题候选
1. Thinking Undoes Editing: Knowledge Edits That Pass Direct Evaluation Revert When Reasoning Models Think
2. Edits Pass, Then Thinking Undoes Them: A Reasoning-Time Evaluation of Knowledge Editing

## 摘要草稿（数字待 Study 2 替换；[]=待定）
Knowledge editing is evaluated by asking the edited model the edited question and checking its
immediate answer. Reasoning models answer only after a chain of thought. We score the same single
edit twice, with the thinking span closed and after the model's own chain, across [eight] reasoning
models. On the largest DeepSeek-R1-distilled models, edits that pass direct evaluation are abandoned
after reasoning [2–3×] as often as the same models abandon their own unedited answers, and [61%] of
them fail in at least one of three sampled reasoning runs. The effect survives semantic judging and a
human audit, and replicates in a pre-registered study on fresh facts [and under MEMIT, AlphaEdit and an
RL-trained reasoner]. In chains that revert, the old value surfaces early, usually through related
facts the edit never touched. Penalizing the old answer's first tokens only inside the thinking span —
never at the answer — restores the edit, while the mirror-image penalty on the new value does the
opposite: the failure has a causal control point inside the chain.

## 论证顺序（每节一个主张，限定条件统一放 Limitations）
1. **Introduction** — 问题（评测方式 vs 部署方式）→ 图 1 例子 → 我们做什么（同一编辑两次打分）→ 三个发现 → 贡献。
2. **Related work** — 向外传播失败（MQuAKE、RippleEdits、ReCoE、Ju et al.）；推理时的编辑失效观察（He et al.、
   CODE、CRANE、Gao et al.、ThinkEval）；评测真实性（Mirage、长文本漂移）；机制（Superficial Editing、
   suppress-not-overwrite）；推理与回忆（Gekhman et al.）；解码期干预（DeCK、EditCoT）。
   定位：前人证明编辑不向外传播；我们证明推理时未编辑的邻域向内回流，推翻编辑本身。
3. **Setup** — 表 1 协议（B0/B0P/B1/B3、条件、终点公式）；Study 1（探索）与 Study 2（预注册）两段式；
   选池规则与"为什么"（回退需要模型原本知道旧值）；打分口径与语义判官。
4. **Reasoning undoes edits** — 4.1 缺口（Holm）；4.2 编辑特异（留存对比 vs 原生答案）；
   4.3 规模结构（侵蚀在所有尺度、修复随规模消失）；4.4 稳健性（语义/人工、采样可靠性、名字泄题、
   编辑器、三种后训练、编辑强度 α）。
5. **Where the edit is lost** — 旧值在链中出现的位置；路径普查（Bridge/Recall/RO）；
   机制探针（链中主语再现处编辑是否点火；按位置门控）；长度 vs 内容（填充、换链）。
6. **A chain-local control point** — 五臂（T/N/D/P/C），D 反号是关键；迁移；只作诊断探针。
7. **Discussion & Limitations** — 评测建议（加推理时测试臂）；局限集中写。
Ethics（ACL 常规）：数据许可、误用（抑制器 = 可用于压制真话）、算力、标注者。

## 图表
- 图 1：单个案例三态（B0 通过 → B3 回退 → 思考段抑制后恢复），字号 ≥ 正文。
- 图 2：各模型 B0 vs B3 编辑成功（Study 1 与 Study 2 并列）+ 右栏留存对比（编辑答案丢失率 vs 原生答案丢失率）。
- 图 3：侵蚀与修复随规模（两条线）。
- 图 4：五臂在 B3 的 ES / 回退（配对差值带 CI）。
- 图 5（视结果）：编辑激活沿推理链 / 位置门控的 margin。
- 表 1：协议；表 2：主数字（Holm 后）；附录：全部端点、稳健性、判官一致性。

## 审稿意见 → 在哪里回答
| 意见 | 位置 |
|---|---|
| 2/6 显著、多重比较、范围事后 | §4.1 Holm；Study 2 预注册 H1 |
| Qwen-7B@B3 选池、逐模型资格 | §3 新选池规则（各模型自己 B0）；§4.4 Study 1 资格分层 |
| 只有 ROME / CounterFact / R1 配方 | §4.4 MEMIT、AlphaEdit、IKE、QwQ、Instruct；Limitations 写数据集 |
| edited vs base 无正式对比 | §4.2 留存对比 |
| permissive RR 精度 .48 | 降级；语义判官 + 人工；名字泄题剔除 |
| 中介未识别、oracle | §5 机制探针；§6 明确"控制点≠自然中介" |
| 漏引 MQuAKE / Ju | §2 并作为定位钩子 |
| 可读性、Ethics | 全文按本骨架重写；ACL 常规 Ethics |
