# 00 · 论文筛选报告（Step ① 产出，待人工把关）

- **日期**: 2026-06-10
- **方向（B′）**: 参数知识编辑（ROME/MEMIT/AlphaEdit）在 R1 式大推理模型上的存续性 —— 量化 edit reversion rate 随思考预算（test-time compute）的变化，定位回退机理（自验证/反思步骤），并给出 training-free 的推理时修补。目标：AAAI-27（abstract 2026-07-20 / 全文 2026-07-27），主赛道或 AI Alignment track。
- **筛选标准（用户给定）**: 模块化、偏应用、有活的开源代码。探索性/无代码的论文只入 papers/ 作参考，不进复现队列。
- **环境分工**: 容器（无 GPU）做代码审计 + CPU 冒烟测试；7B/14B 真实验在组内 8×H200 排队跑，命令由复现笔记给出。

---

## 一、复现队列（7 个仓库已克隆至 source/，逐个出具 0X_*.md 复现笔记）

| # | 论文 / 仓库 | 代码健康度（实测） | 在 B′ 中的角色 | 判定 |
|---|---|---|---|---|
| 1 | **EasyEdit** (arXiv 2308.07269)<br>`zjunlp/EasyEdit` | ★★★★★ 439 个 py，最后提交 **2026-06-10（今天）**，有 requirements + Dockerfile，README 1236 行 | 主战框架：ROME/MEMIT/AlphaEdit 的统一实现，编辑 R1-Distill-Qwen（Qwen2.5 架构）的工作马 | **必复现，第一个** |
| 2 | **AlphaEdit** (ICLR'25, arXiv 2410.02355)<br>`jianghoucheng/AlphaEdit` | ★★★☆ 83 个 py，最后提交 2025-10，**无 requirements.txt**，沿用 MEMIT 代码骨架（globals.yml/hparams/dsets） | 论文主编辑器（SOTA 参数编辑，零空间投影）；若 EasyEdit 内置版可用则以 EasyEdit 为准，本仓库做超参对照 | 复现 |
| 3 | **R-TOFU** (EMNLP'25, arXiv 2505.15214)<br>`ssangyeon/R-TOFU` | ★★★☆ 14 个 py 结构干净（config/data/forget/eval/test_cot），有 requirements；README 仅 42 行偏薄；作者用 8×L40 | **实验设计最近邻**：其 DefaultThink/LessThink/ZeroThink 解码协议直接移植为我们的"思考预算"自变量；CoT 级评测指标可改造 | 复现（重点读 test_cot.py 与解码控制） |
| 4 | **ThinkEdit** (arXiv 2503.22048)<br>`Trustworthy-ML-Lab/ThinkEdit` | ★★★★ 12 个 py 高度聚焦（方向抽取/找 attention heads/权重编辑/评测），最后提交 2025-12，有 requirements | "修补"半篇的机械库：reasoning-length 方向抽取与权重/表征干预 → 改造为保护编辑事实的 reflection 引导 | 复现 |
| 5 | **R²MU** (arXiv 2506.12963)<br>`OPTML-Group/Unlearn-R2MU` | ★★☆ 579 个 py 但大半是 vendor 的 lm-evaluation-harness；**无 requirements**；根目录散落 .log 和生成的 jsonl（研究代码味重） | 近邻对照（unlearning 翼），论文必引必比；只做审计级复现，确认其评测口径，不做全量训练 | 审计级复现（防"包装"重点对象） |
| 6 | **MQuAKE** (EMNLP'23)<br>`princeton-nlp/MQuAKE` | ★★★（数据仓库）**0 个 py**，纯 datasets+prompts+1 个 notebook，2024-09 后冻结 | 多跳评测数据源（MQuAKE-CF/T）；MeLLo 方法仅 notebook，不复现方法只取数据 | 数据提取，不做方法复现 |
| 7 | **MEMIT** (ICLR'23)<br>`kmeng01/memit` | ★★（冻结参考）2022-11 后无提交，经典原始实现 | CounterFact/zsRE 数据与原始超参的 ground truth 对照 | 参考，不单独复现 |

**建议复现顺序**: EasyEdit → AlphaEdit → R-TOFU → ThinkEdit → R²MU（审计）→ MQuAKE/MEMIT（数据提取）。
理由：1 是地基且当天还在维护；2 是论文主方法；3 直接决定实验协议设计；4 服务修补章节；5 只为对照与防雷。

## 二、不进复现队列（已下 PDF 入 papers/，标 ref_ 前缀）

| 论文 | 排除原因（按用户标准） |
|---|---|
| ThinkEval/KnowGIC (TMLR'26, 2506.01386) | 数据在匿名链接，代码健康度无法确认；属评测框架近邻，**读原文吃透其 IFR/CKP 指标定义即可**，论文必引 |
| Edit-via-Background-Stories (2602.02028) | 2026-02 新文，未见可验证开源实现；其附录 F.2.2 的"推理中自我纠正回先验"案例是我们现象的直接证据，精读 |
| KELE (2408.12456) | 未确认有可用代码；GPT-2/GPT-J 时代实验，价值在"残留旧知识→回退"假设的论证方式 |
| Sleek (2506.17279) | 攻击式黑盒方法，与我们白盒/参数路线正交，引用即可 |
| STaR (2601.09281) | 2026-01 新文，R-TOFU 上的 unlearning 新方法——拥挤度证据，引用即可 |
| ROME (2202.05262) | 实现由 EasyEdit/memit 覆盖，原文作机理背景阅读 |

## 三、风险登记（持续更新）

1. **撞车风险（高）**: 本子领域 ~每月 1 篇直接相邻论文（最近：2602.02028、2602.17692、2601.09281）。开题前最后一周需再做一轮增量查新。
2. **代码雷区（中）**: R²MU 仓库工程质量存疑，复现其数字前先核对评测脚本与论文表格口径是否一致——这是"从代码出发，不被包装影响"的头号对象。
3. **架构兼容（低）**: R1-Distill-Qwen-7B = Qwen2.5 架构，EasyEdit 支持；但 ROME/MEMIT 超参（layers、mom2 统计）需要为该 checkpoint 重算 covariance，复现 EasyEdit 时验证。
4. **go/no-go 纪律**: pilot 若 think 相对 no-think 的编辑成功率降幅 < 20pp 或回退样本机理不干净 → 弃 B′ 回方向 A。

## 四、待人工决策（把关点）

- [ ] 确认复现队列 7 项（可划掉任意一项）
- [ ] 确认 R²MU 仅做审计级复现（不跑全量 unlearning 训练）
- [ ] 确认 MQuAKE 仅取数据
- [ ] 是否需要把 agent 翼（Agentic Unlearning, 2602.17692）的 PDF 也补入 ref（当前未下载）
