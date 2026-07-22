# abstract_polish_plan.md · v5 摘要形式层打磨执行计划

> fable 起草 2026-07-23，交 Codex 执行，fable 复审终裁，用户拍板。
> 权威层级（冲突时从上往下赢）：WRITING_PLAN §3 禁语/证据上限 > title_abstract.md 冻结件与对账表 >
> prewrite/usage_protocol.md 六禁令 > transfer_checklist.md（透镜，检查问题非指令）。
> 基线 = 已提交 OpenReview 的 v5，逐字放左边。**保 v5 不算失败。**

## Phase 0 · 前置（Codex，起草前完成，零摘要改动）

0.1 按序读：`prewrite/usage_protocol.md`（纪律权威）→ `title_abstract.md`（v5 全文 + 逐数字对账表 +
    解冻待办 #1/#3；#2 已作废勿复活）→ `prewrite/transfer_checklist.md` §1（Abstract 组 10 检查 +
    4 不可迁移项）→ `delivery/fable_review_19majors_for_w2.md` 中与摘要相关各项（M03/M13/M14 +
    MINOR: strict 重载、synonym drift、S7 attachment）。
0.2 **M03 台账修复**（十分钟件，门 1 的前置）：results.json `rq2_taxonomy.p0_corrected_taxonomy`
    加派生字段 `n_unique_facts: 33` + `_derivation` 注（"unique cf case_ids over the 41 member
    item_ids in results/p0_corrected_taxonomy.json, sha256=c11c6a0e…"）；同步 title_abstract.md
    对账表行指向新 path。**不碰摘要**。此修复消除全库三个不同 "33" 的碰撞（A3 池/b16 池/rate-limited 行）。

## Phase 1 · 三态表（Codex，7/23 晚）

1.1 用 transfer_checklist §1 的 10 项检查 + 4 项不可迁移项，逐句过 v5（S1–S9 + TL;DR 回联两项）。
    每条记：**符合 / 有意偏离（一句理由）/ 打磨机会**。
1.2 既有预答复直接沿用、不重开：263 词（+35%）= 有意偏离（评测文体+AI辅助评审下密度=可信度，
    AAAI-27 无词数上限已亲核）；9 个 headline 数字 = 有意偏离（同理由）；无命名装置 = 有意偏离
    （修复冻结位阶=causal probe 非 method，造名正中 "lexical patch" 拒稿刀）；首拍 CONTEXT ✓、
    APPROACH→RESULT 相邻 ✓、末拍 IMPLICATION ✓。**不追语料中位数**（不可迁移项四条全适用）。
1.3 **收敛纪律**：预期"打磨机会"⊆ 三处圈定（见 Phase 2）。三态表冒出圈外"打磨机会"时从严裁剪，
    默认拒绝执行；仅当同时满足 (i) 零数字/hedge/claim 触碰 (ii) checklist 对应项标"可动"
    (iii) 不撞不可迁移项，才可提请 fable 加圈，否则记 "打磨机会-拒绝(理由)" 存档。

## Phase 2 · 候选版起草（Codex，7/24；只动圈定句，其余逐字保留）

三处圈定与各自的最小动作：

C-1 **S5 +4 词**（=解冻待办 #1，三方审计链已预批）：
    "(23/23 examined)" → "(23/23 examined; an installation sanity check)"。
    注意：transfer_checklist 第 4 项把 hedge 增删标"不可动"——本处属论文自身规则（解冻待办）
    优先于透镜的合法有意偏离，且方向是**降**证据位阶（preempt vacuity 攻击），须在门 3 记录中
    显式写明此裁决依据。
C-2 **S7 长句**（=解冻待办 #3 + 透镜/敌意冷读独立汇聚的密度点）：两个已批动作，按最小取用——
    (a) 消歧："beating a placebo and a same-relation competitor with near-null answer-level
        effects" → "beating a placebo and a same-relation competitor, both near-null at the
        answer level"（P−N 与 C−N 答案端点均含零，对账表已锚）；
    (b) 可选断句：S7 分号处拆为两句（干预+效应 / strict 端点），checklist 第 8 项"仅断句"可动。
    **禁区**：不得重排 19.3%→8.5% 与 paired −0.102 的并置结构（M14 的 9.1≠8.5 表观矛盾由主文
    §5 脚注解决，摘要内任何数字重组都有实质性化风险）；"offsets/persists/At the largest tested"
    等 estimand 措辞一字不动。
C-3 **strict/loose 命名缝**（M13 摘要侧最小化）：S4 与 S6 的 "neutral three-judge majority"
    指两套不同仪器（validation panel n=87 vs route-census panel n=41）。二选一最小动作：
    S4 加 "validation"（"vs. a neutral three-judge validation panel"）**或** S6 改
    "a second neutral three-judge panel's majority labels"。完整命名体系落主文 §3（M13 修法），
    摘要只消除同名歧义。synonym drift（chain-local/-localized/-only）摘要内已一致，不碰。

规则：数字/CI/hedge 逐字沿用对账表；产**逐句映射表**（候选每句 → v5 对应句 + 差异类型
∈ {逐字同, 加词, 断句, 换词}）；**Title 与 TL;DR 绝对不动**；未圈定句 byte-diff 必须为零。

## Phase 3 · 四道门 + 特检（Codex 执行并留记录）

门 1 数字对账：候选版每个数字 ↔ 对账表 JSON path（含 0.2 新增的 n_unique_facts）；
     未圈定句与 v5 byte-diff = 0 的机器证明。
门 2 禁语扫描：WRITING_PLAN §3 全清单 + Kimi 三条（edit intact / not erased / guaranteed
     upper bound）+ .214 禁作 contrast。
门 3 非实质性检验：映射表为证——同 claim 集、同数字集、同 hedge 语法；C-1 的 hedge 增补
     附裁决依据（解冻待办 > 透镜"不可动"）；结论必须能一句话答复 "qualitatively different?" = No。
门 4 敌意冷读（Codex 自跑一遍，fable 终裁再独立跑）：靶标 = Kimi 拒稿一句话 + M13 循环性攻击 +
     M14 表观矛盾——候选版不得使任一攻击面变大。
特检：触碰 S4/S7 任何估计量措辞 → 重过"配对量 vs marginal"检查（only/removes/concentrates
     三词旧案为判例）。

## Phase 4 · 终裁（fable，7/24 晚）

4.1 Codex 交**决策包**：候选版全文 + 三态表 + 逐句映射表 + 四门记录 + ≤10 行自评
    （含：若判"不明确胜出"该保 v5 的理由是什么——强制自我反方）。
4.2 fable 独立冷读 + 抽查门 1/门 3；标准：**不明确胜出即保 v5**；歧义算输、任何回归算输。
4.3 用户拍板。若换版：按 title_abstract.md:5 走**解冻登记**——记录理由、落 Abstract v6、
    重新冻结、OpenReview 表单字段 byte-diff 同步（编辑权至北京 7/29 19:59，内部 7/25 与全文
    一起冻结）；若保 v5：三态表与门记录仍归档 title_abstract.md（审计链完整性）。

## 边界备忘（Codex 必读）

- 六禁令全程有效：不引用矿场项目、透镜数字不进论文、检查问题非指令、冲突时论文规则无条件优先、
  透镜不得加强任何 claim、数字唯一来源 results.json。
- M14（marginal vs paired 并置）、M15（control-point 记忆位）、M13 完整版（仪器命名体系）、
  strict-ES/strict-RRs 重载定义——全部是**主文 §3/§5/§1 的 W2 任务**，不在本摘要打磨范围内；
  见 19majors 对应修法。
- 圈外的一切"更好的写法"提议 → 记录进三态表存档，不执行。这把锁开第六次的唯一理由是
  三处圈定；不存在第七次。
