# 08 · 本地 M5/MPS 参数版 ROME 首信号（harness 真权重端到端 + rewrite_acc≠ES_b 口径实证）

- **日期**: 2026-06-12 ｜ **状态**: 跑完 ✅（ROME-on-MPS 通了，**无算子墙**；现象在 1.5B 上诚实负）
- **机器/模型**: MacBook Pro M5 Pro 24G，MPS(float32)，`deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B`（≈7 tok/s）
- **脚本**: `src/rome_mps_probe.py`（复用 `edit_loop.run` → 端到端验证整条 pilot harness）；ROME hparams `hparams/ROME/qwen2.5-7b.yaml`（1.5B 与 7B 同架构 28 层 qwen2，复用）
- **一句话**: **EasyEdit ROME 在真 1.5B 权重上经 MPS 跑通**（8 条编辑 0 崩溃，`compute_v` 的 25 步梯度+反传在 MPS float32 全过）——这是 phase-1 §6 开放线程的正面闭合；但**生成式 ES_b(B0)=0/8**（而 EasyEdit 自带 `rewrite_acc` post=6/8），**两口径在 1.5B 上完全脱节**，参数版"越想越退"在此设置下**无法测**（无成功的生成式 B0 编辑可供回退）——与 07 的 ICE 诚实负**同构**：**1.5B 太弱 + 7B 派生超参不适配，须 7B + layer 扫描（合格线判生成式 ES_b 非 rewrite_acc）**。

> 重要边界：① 缩减预算上限 `B1/B2/B3/B4=128/384/768/768`（与 07 一致，控 MPS 时）；② 1.5B 是最弱模型、ROME hparams 是 7B-Qwen2.5 派生（`v_lr/v_num_grad_steps/layers` 未对 1.5B 调）；③ 这是**彩排 + 端到端验证 harness + 口径实证**，不是主结果。④ 解锁前置：qwen 路由 bug 已由 `edit_loop` 自动接入的 `vendor_patches/easyedit_qwen2_loader.py` 修掉（否则 `from_hparams` 即 `fp32` TypeError）——本笔记同时是该 pilot-blocker 修复的真模型回归。

---

## 1. ROME-on-MPS 跑通（phase-1 §6 开放线程的正面闭合）✅

phase-1 §6 的担心是 MPS 算子墙（`compute_v` 反传里 float64 / 算子缺口）。**实测无墙**：

- **8 条编辑全部执行**（`Executing ROME algorithm` ×8 / `New weights successfully inserted` ×8），**错误行=0**。
- `compute_v` 的 **25 步梯度优化 + 反传在 MPS float32 上全过**（loss 单调下降，如 France→Rome：`10.957 → 0.05`，`avg prob of [Rome]` `3e-5 → 0.995`）。
- ROME 路径无硬编码 `.cuda()` 成立；`hp.device="mps"`（**字符串**，int 会被 `normalize_device` 当 cuda:idx，phase-1 §6）；`mom2_adjustment:false` → 不需协方差（无 mom2 前置，故离线可跑）。
- **`restore` 经 `finally` 每条还原**（编辑后 raw greedy 与编辑前 byte 级一致，见 §3）。

**结论**：整条 pilot harness（`vendor_patch → from_hparams → edit → 全预算档生成 → finally restore → 溯源头 → metrics.score`）在 MPS 真权重上端到端跑通。**H200 同路（差别仅 cuda/规模）→ 主路径已验证，开窗即跑的承诺成立**（RUNBOOK §4）。

## 2. rewrite_acc（EasyEdit 自带 logits 口径）—— task#03 闭环

8 条编辑的 EasyEdit `Metrics Summary`（teacher-forcing token accuracy）：

| | rewrite_acc 分布（n=8） |
|---|---|
| **pre**  | 7×`0.0` + 1×`0.5` |
| **post** | **6×`1.0`** + 2×`0.0` |

即按 EasyEdit 自带 logits 口径，**6/8 编辑"成功"**（pre→post 0→1）。这顺手闭合了 task#03 欠的 `rewrite_acc` 数值（在 1.5B 上，比 GPT-2-XL 冒烟更切题——GPT-2-XL 冒烟可降级/不再阻塞）。

## 3. ⭐ 核心口径发现：生成式 ES_b(B0)=0/8，与 rewrite_acc 完全脱节

同一批编辑，我们的**生成式 ES_b**（`metrics.score`，greedy，CounterFact-style efficacy 探针 `q=prompt`）：

| budget | n | ES | RR | CLR |
|---|---|---|---|---|
| **B0** | 8 | **0.00** | 0.00 | 0.00 |

逐 case（B0=ZeroThink）：**7/8 REV**（答 o_old）+ 1/8 `??`（既非 o_new 也非 o_old）。**0 条 ES**。

**rewrite_acc post=6/8 但生成式 ES_b=0/8 → 两口径完全脱节。** 这正是 CLAUDE.md 约束 4（`ES_b ≠ rewrite_acc`，永不混排）在**真权重上的实证**，也是 01 笔记「editing 超 FT reliability 是 no-think/logits 口径」论断的具体化。

### 3.1 定位：raw vs 模板 vs 多层（France→Rome, layer5 详跑）

| 探针 | 输出（截断） | 判 |
|---|---|---|
| 编辑前 raw `The capital of France is` | `Paris, and the capital of Germany is Berlin...` | 知 o_old |
| **编辑后 raw**（同上） | `Paris, and the capital of Germany is Berlin...`（**与编辑前 byte 级一致**） | 编辑对该 prompt 的自由续写**零改变** |
| 编辑后 raw+尾空格 `...is ` | `3, 2, 1, 7, 6, 5, 4. The capital of Spain` | 编辑**有扰动但不指向 Rome**（token 边界敏感） |
| 编辑后 chat(no-think) `<｜User｜>...<｜Assistant｜>` | `<think>\n\n</think>\n\nThe capital of France is Paris.` | REV |
| 编辑后 **B0 ZeroThink** | `The capital of France is Paris.` | REV |
| **还原后 raw** | `Paris, and the capital of Germany is Berlin...` | restore 正确 |

**多层扫描**（France→Rome，layer∈{3,5,8,12,16}）：**每一层的 B0 与 raw 生成都仍是「Paris」**——**不是选错层**，而是 1.5B 下编辑根本不进生成。

### 3.2 为何 rewrite_acc=1.0 却生成 0（机理假设，留待 Phase 3 logit-lens）

`rewrite_acc` 是**单点 teacher-forcing argmax**（在目标 token 位强制喂入再看 argmax）；而生成是**自由 greedy**。1.5B@layer5 的编辑量级仅够让 teacher-forced 位的 argmax 翻成 Rome（post=1.0），但**对真实前向的「is」→next 分布扰动微乎其微**（raw 续写 byte 不变即证）。佐证：ROME 的 `context_template` 采样在 1.5B 上**退化成乱码**（`'Therefore ensuring ensuring ensuring. {}'` 之类）→ 编辑鲁棒性的上下文基底本身坏了 → 编辑弱而脆。**深究（编辑位 logit-lens）属 Phase 3，不在彩排范围。**

## 4. 方法学教训（直接进 pilot 剧本）

1. **layer 扫合格线必须判生成式 ES_b(B0)，不能判 rewrite_acc**——否则会"通过"一堆 rewrite_acc=1.0 但生成不动的层（本笔记 6/8 vs 0/8 就是反例）。`metrics.score` 的 `Loc`/`ES` 已是生成式口径（§6.1-②b 刚补），`score_pilot` 合格线提示已写「B0 下 ES≥0.90 & Loc≥0.85」。
2. **参数版"越想越退"的前提是生成式 B0 先成功**（有成功的编辑才谈得上随预算回退，RR 分母=B0 成功数）。1.5B@默认超参给不出 → 与 07 ICE 诚实负**同构**：**自变量（参数编辑的生成式存续）在弱模型上立不住**。
3. **模型强度 + 超参适配是硬门槛**：须 7B（基座 Qwen2.5-**Math**）+ layers∈{[4-8],[6-10],[8-12]} 扫描（防雷清单），且很可能要调 `v_lr/v_num_grad_steps`。这是 go/no-go 前 layer 小扫（RUNBOOK §6.3 / sumandplan §8-④）要解决的，不是 bug。
4. **`restore` 真权重正确**（编辑后→还原后 raw byte 级回到编辑前）→ 单条编辑协议的 `finally:restore` 在真权重上无残留污染（01 §3 的逐元素拷回结论，真权重侧再验一次）。

## 5. 与 07 的关系 & 下一步

- 07（ICE 上下文注入）与 08（参数编辑 ROME）**两条独立路径在 1.5B 上都是诚实负**，但负的原因不同且互补：07 是「ICE 压不动参数知识」，08 是「参数编辑进 logits 不进生成」。**共同指向：现象的自变量必须在 7B 真权重 + 调好的编辑器上才立得住**——这不是项目假设被证伪，是"彩排模型太弱"的预期结果（plan 风险表「Math 基座超参漂移」已登记）。
- **不跑 B3/B4 全量**：B0 生成式 ES=0 → 无成功编辑可回退，B3/B4 只会确认 ES 仍 0、徒耗 MPS 时（~30min）。本笔记 B0×8 已足以定性。
- **GPU 待办联动**（sumandplan §8）：开窗 ⑤ pilot 真跑前的 ④ layer 小扫，**判据用本笔记确立的生成式 ES_b(B0) 合格线**；ROME-on-MPS 路径已通 → 7B 在 H200 上走同一 `edit_loop`，预期差别仅算子后端与规模。

---
*证据落点：`results/rome_mps/probe.jsonl`（gitignore，`rome_mps_probe.py --fresh` 可再生；首行含 git/配置溯源头）。本笔记数字取自 2026-06-12 两次跑（8-case B0 全量 + France 多层/raw-模板详跑），HEAD `183d99a`。*
