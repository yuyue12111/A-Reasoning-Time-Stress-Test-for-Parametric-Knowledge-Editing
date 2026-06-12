# 09 · FlipPoint 判分 + 10% 边界样本校准流程（pilot 审计 & Phase 3 片段归因前置）

- **日期**: 2026-06-12 ｜ **状态**: 流程预写 + `metrics.flip_analysis` 已落地 ✅（GPU 窗口照此执行）
- **定位**: 规则判分（子串 hit）有边界误差；本流程在 pilot 打分后、6/22 go/no-go 前，对 **10% 边界样本**人工复核以校准判分口径，并定义 **FlipPoint**（链内立场翻转位）供 Phase 3 机理片段归因。来源：plan §2.5（FlipPoint 定义）/§12.3 + 07 教训（子串分不出"先新后旧"）+ 06 §7。
- **口径纪律**: 全流程是**生成式 ES_b 口径**（≠ EasyEdit rewrite_acc，08 笔记已实证两者在弱模型上脱节）。

---

## 1. 为什么需要校准（07 + 08 的教训）

- **子串判分的盲区**（07）：答案『**Mars**. However the largest is **Jupiter**』——`hit(o_new)` 与 `hit(o_old)` 同时为真。严格 ES（`hit(new) and not hit(old)`）判 0（对，因含旧），但**分不出**这是「首段答编辑、随后翻回旧」还是「乱答」。落定立场（last=Jupiter）才是该 case 的真实结果（回退）。
- **rewrite_acc 不可信**（08）：6/8 编辑 rewrite_acc=1.0 但生成式 ES_b=0/8 → **合格线、回退判定一律走生成式口径**。
- **别名/部分匹配误差**：o_new/o_old 的别名表覆盖不全（zsRE 仅 18%）→ 漏判命中；或部分串误命中（如 "US" ⊂ "USSR"）。

## 2. `metrics.flip_analysis`（已实现，单测覆盖）

`flip_analysis(text, o_new, o_old, aliases)` → `{first, last, flipped, flip_pos, new_pos, old_pos}`：
- `first`/`last` ∈ {'new','old',None}：text 中最先/最后出现的立场（**last=落定立场**）。
- `flipped`：o_new 与 o_old 都出现（立场翻转过）。
- `flip_pos`：对立项（后现者）首现的字符位 = **FlipPoint 的字符级近似**。

两种用法：
- **answer 上**：`ESf`（首段断言 ES=`first=='new'`，容忍后续翻转）vs 严格 `ES`。`score_pilot` 已并列输出 `ES/ESf/Flip` —— **`ESf ≫ ES` 且 `Flip↑` = 答案内『越想越退』**（首段答编辑、落定回旧）。
- **CoT 上**：定位回退在推理链中的发生位（Phase 3 片段归因的锚），并与反思标记（"wait/let me check"）共现性回归（plan RQ2）。

> token 级 FlipPoint（plan §2.5 原义是 token 位）：本实现先给**字符级近似**（够 pilot 审计与片段定位）；Phase 3 若要精确 token 位 + logit-lens，在缓存 CoT 上用 tokenizer offset 映射升级（不额外耗 GPU）。

## 3. 10% 边界样本校准流程（GPU 窗口照此执行）

### 3.1 边界样本选取（确定性，seed 固定）
对每个 (editor × budget)，从 efficacy 行中挑**判分易错**的子集：
1. **翻转样本**：`flip_analysis(answer).flipped == True`（o_new/o_old 都现）。
2. **ES vs ESf 分歧**：严格 `ES==0` 但 `ESf==1`（首段是编辑、落定回旧——最可能误判的一类）。
3. **双否样本**：answer 既不含 o_new 也不含 o_old（`first is None`；多为别名漏或乱答）。
4. **CLR 边界**：`hit(cot, o_old)` 为真但 answer 判 ES（链内泄漏但作答正确——Leak 口径核对）。
取上述并集；若 >10% 则按固定 seed（42）抽 10%，若 ≤10% 则全取。**记录被抽 case_id 列表**（可复现）。

### 3.2 人工复核（对缓存 CoT/answer，不重跑 GPU）
逐样本读缓存的 `cot`+`answer`，人工三分类落定立场：`ES`(编辑成功) / `REV`(回退旧) / `NEITHER`(乱答/拒答)，与规则标签比对，记分歧。

### 3.3 校准动作
- 分歧率 ≤5%：判分口径采信，记一致率入审计报告。
- 分歧率 >5%：定位主因——
  - 「先新后旧」误判为成功 → 主口径切到 `last`（落定立场）或并报 `ESf`；
  - 别名漏命中 → 补 `data/aliases.json`（Wikidata 富集，§6.1-⑥）后**重跑 `score_pilot`**（确定性、秒级）；
  - 部分串误命中 → 给该实体加词界/否定规则。
- 任何规则/别名改动**必须重跑全量打分**并记 diff（不手改个别标签）。

### 3.4 产出
`results/pilot/calibration_<editor>.md`（gitignore）：抽样列表 + 一致率 + 分歧样例 + 采取的口径/别名调整。**喂入 30 条回退样本人工审计**（sumandplan §6.3，字段含 FlipPoint、触发片段类型）与 **Phase 3 片段归因**。

## 4. 何时跑 & 联动
- **位置**：RUNBOOK §6.3 窗口剧本「打分 → **10% 边界校准** → 30 条回退审计 → 对 6/22 判据」之间（pilot 打分之后、审计之前）。
- **依赖**：缓存 CoT（pilot 已全缓存）+ `flip_analysis`（已就位）+ aliases（可现场富集后重跑打分）。
- **不耗 GPU**：纯离线复核 + 确定性重打分。

---
*实现：`src/metrics.py` 的 `first_mention`/`flip_analysis` + `score()` 的 `ESf`/`Flip` 列；单测 `src/test_metrics.py`（`test_flip_analysis`/`test_score_esf_and_flip`）。HEAD 见 commit。*
