# 07 · 本地 M5/MPS 迷你彩排（算力盲区首跑：harness 真权重验证 + ICE 现象探针）

- **日期**: 2026-06-11 ｜ **状态**: 跑完 ✅（组里 8×H200 暂不可用，改本机）
- **机器/模型**: MacBook Pro M5 Pro 24G，MPS(float16)，`deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B`（≈7 tok/s）
- **脚本**: `src/local_probe.py`（纯 HF generate，绕开要 cuda 的权重编辑）
- **一句话**: **Part A（预算控制器）真权重验证通过**；**Part B（ICE 现象探针）在 1.5B 上是诚实的负/不确定结果**——ICE 上下文注入根本压不动 1.5B 的参数知识，"无编辑可回退"，恰恰反证了**项目必须用参数编辑（ROME/MEMIT）而非上下文注入**。

> 重要边界：① 本地用**缩减预算上限** `B1/B2/B3/B4 = 128/384/768/768`（非 H200 全量 B3=8192），事实类 CoT 通常更短，B3 仍≈natural；② 1.5B 是最弱模型，信号噪；③ ICE≠参数编辑（plan §2.2 的非参对照）。这是**彩排 + 端到端验证 harness**，不是主结果。

---

## 1. Part A — think_budget B0–B4 真权重长度分布（task#07 part B，此前只 mock 过）✅

Q0「The capital of France is」逐档 cot token 数：

| 档位 | cot_tok | 预期 | 对? |
|---|---|---|---|
| B0 (ZeroThink) | **0** | 空思考块 | ✅ |
| B1 (cap128) | **128** | 命中截断 | ✅ |
| B2 (cap384) | **201** | 自然 < cap，自行收尾 | ✅ |
| B3 (≈natural) | **201** | 同自然长度 | ✅ |
| B4 (extend) | **301** | Wait 注入延长 **> B3** | ✅ |

**B0 空 → 截断 → natural → B4 延长，单调非降，与 `test_think_budget.py` mock 层完全一致。** 即 `think_budget.py` 在**真 R1-Distill 权重**上行为正确（B0 强制空思考、B1/B2 截断、B3 自然收尾、B4 s1 式延长都成立）。task#07 part B 在 1.5B 上落地。4 个问题 20 次生成均如此（含数学/推理题，B3/B4 更长）。

## 2. Part B — ICE 现象探针（注入反事实 o_new，沿预算看是否回退 o_old）

12 个常识反事实（如 capital of France: Paris→Rome），先验模型知不知道 o_old，再 ICE 注入 o_new、沿 {B0,B3,B4} 看回退。**实际答案**（截断 60 字）：

| case (o_old→o_new) | know_old | B0 | B3 | B4 |
|---|---|---|---|---|
| capital of France (Paris→Rome) | 1 | 「indeed **Paris**」REV | 「**Paris**. The statement…」REV | 「**Paris, not Rome**…」REV |
| Eiffel Tower (Paris→Berlin) | 1 | **Paris** REV | **Paris** REV | **Paris** REV |
| Romeo 作者 (Shakespeare→Dickens) | 1 | 「not **Dickens**」REV | 「is **Dickens**」ES | 「is **Dickens**」ES |
| largest planet (Jupiter→Mars) | 1 | **Jupiter** REV | 「**Mars**. However…」REV | 「**Mars**, but…」REV |
| first President (Washington→Lincoln) | 1 | **Lincoln** ES | **Lincoln** ES | **Lincoln** ES |

汇总（"合格"=知 o_old 且 B0 接受 ICE）：**合格仅 1/12** → 表无统计意义（ES=1/RR=0 全档）。

**这恰恰是结果本身**：1.5B **在 B0（不思考）就拒绝 ICE**、直接答参数里的真事实 o_old（10/12 case 的 B0 都 REV），famous fact（capital/Eiffel/planet）甚至 B4 显式顶回去「Paris, **not Rome**」。**没有"成功的编辑"可供回退** → 用 ICE 测不出"越想越退"。

## 3. 解读（诚实，且对项目有用）

1. **ICE ≠ 参数编辑，且 ICE 在 1.5B 上太弱**：对 famous fact，1.5B 的参数知识压过上下文注入，B0 就答 o_old。所以 ICE **建立不起反事实** → 无编辑可回退。**这正面印证项目为何用参数编辑（ROME/MEMIT 把 o_new 写进权重，远强于上下文）**，ICE 只能作弱对照（plan §2.2）。
2. **方向不仅没出现，局部还相反**：Romeo 作者 B0 拒→B3/B4 **接受** Dickens（更想 → 更接受编辑）。即在"弱锚定"事实上，更多思考反而采纳注入——与"越想越退"反向。说明现象**高度依赖编辑强度与事实锚定度**，弱 ICE + 弱模型测不出。
3. **判分粒度不够**：「Mars. However … Jupiter」这类"先说新、反思转旧"的答案，`metrics.hit` 子串命中只能记 REV，分不出"何时翻转"。→ 真实验需 plan §2.5 的 **FlipPoint**（链内立场首次翻转位置）+ 首段断言判分，不能只看子串。

## 4. 方法学教训（喂给真 pilot，值钱）

- ✅ **预过滤口径成立**：12 个里 10 个 `know_old=1`（模型确知 o_old）——plan §2.3 的"模型须先知道 o_old"在真权重上可用。
- ⚠️ **ICE 不能替代参数编辑做自变量**：pilot 的正确结构是「**参数编辑**让 B0 下 ES 高（编辑成功）→ 再看高预算下 RR 上升」；ICE 在 1.5B 上 B0 都不成功，没有这个结构。`local_probe` 的"B0 接受 ICE"合格过滤因此 N=1。
- ⚠️ **判分要 FlipPoint**，不能只 `metrics.hit` 子串（§3.3）。
- ⚠️ 1.5B 是最弱模型；现象（若有）更可能在 7B/14B 上清楚。

## 5. 雷点 / 边界

1. 缩减预算上限（768 而非 8192）+ MPS 慢（~7 tok/s）——本地只能做小规模彩排。
2. **ICE 是非参对照，不是主张的参数编辑**；本探针的负结果**不证伪**项目假设（机制不同 + 最弱模型）。
3. 我自己写的"B0 接受 ICE"合格过滤对 ICE 不合适（假设了 ICE 像参数编辑一样 B0 即成）——已记为教训。

## 6. 下一步（本地能继续做的）

1. **参数版**：试 EasyEdit ROME 在 1.5B/MPS 上做**真权重编辑**→ 全档生成 →`score_pilot`（这才是项目主张的机制；ICE 测不出不代表参数版测不出）。**风险**：EasyEdit 研究代码多处假设 cuda，MPS 可能要补丁（device/`torch.cuda.empty_cache`）——值得一试，失败就记 MPS 雷点等 H200。
2. 7B 主模型重跑本探针（更强 ICE 跟随 + 反思）——MPS 上慢但 24G 跑得动 7B 推理。
3. steer 方向抽取在 1.5B 上验（F1 预备）。

**结论**：本机这一跑，**确证了 harness（预算控制器）在真权重上正确**，并用一个诚实的负结果**强化了"必须参数编辑"的论证**——比硬凑一个"看到了效果"有用。
