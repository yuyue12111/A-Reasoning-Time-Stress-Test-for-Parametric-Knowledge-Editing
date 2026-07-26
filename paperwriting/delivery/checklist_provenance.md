# ReproducibilityChecklist 核销台账（W2-7 / Task B / M19）

- 对应文件：`paperwriting/manuscript/ReproducibilityChecklist.tex`（AuthorKit27 模板填答，31 项）
- 行号基准：`main.tex` @ 本次提交的父 commit `8c93722`（行号会随后续编辑漂移，锚点引文为准）
- 统计：yes 21 / partial 1 / no 1 / NA 8

## 为什么理由不写进 .tex

模板原文要求「Replace ONLY the ``Type your response here'' text and nothing else」，
且答案可能被自动抽取。**故 .tex 内只留裸答案**，逐条授权证据落在本文件。
这是对「每个答案必须引用授权它的节/行」的等效满足，且比行内注释更可被机器核验。

## 「yes 由 supplement 授权」的判定规则

凡正文无落点、需靠 supplement 才成立的项，只有在**支撑工件今天已存在于仓库**、
且 Task D 已把它列为硬交付时才答 yes；工件本身残缺的一律降级。
下表所有标 **→ Task D 硬承诺** 的行构成 7/31 交付的强制清单：
**跑不出来必须回头把对应答案降级，不许留空头支票（M17）**。

| 项 | 问题 | 答案 | 授权证据 |
|---|---|---|---|
| **1.1** | 概念性方法说明/伪码 | **yes** | §5.1 用散文完整给出方法（main.tex:206）：惩罚落点=旧值别名首 token、作用域=think span、答案段不施加、五臂只差被罚 token 集合。方法只有一个算子，无需伪码；supp S11 另附伪码与配置。 |
| **1.2** | 观点/假说/思辨与事实分离 | **yes** | §4.3 显式标注为假说（main.tex:170）；§4.4 显式标注为「account」且写明只是约束而非排除（main.tex:186）；§5.2 明写未设等价界、故不构成无效应证据（main.tex:267）。 |
| **1.3** | 面向不熟悉读者的背景引用 | **yes** | §2 四段式相关工作（main.tex:52 起）；§3.1 引 ROME 原文与 R1 配方（main.tex:66）。 |
| **2.1** | 是否有理论贡献 | **no** | 全经验论文，无定理/证明。 |
| **2.2–2.8** | 理论子项 | **NA** | 2.1=no 时模板的 \ifyespoints 分支不适用。模板允许项写 NA；**偏离说明**：2.2–2.6 的选项串未列 NA，但留「Type your response here」在投稿件里更像漏填，故统一填 NA 并在此记录理由。 |
| **3.1** | 是否依赖数据集 | **yes** | CounterFact（main.tex:66）；GSM8K / MATH-500（main.tex:306）。 |
| **3.2** | 数据集选择理由 | **yes** | §3.1 明写 CounterFact 是「所测编辑器被提出时所用的基准」（main.tex:66）——**本条为 W2-7 新增句**，此前正文只用不释；§6 明写 GSM8K/MATH 用于量化守卫在未编辑 query 上的代价（main.tex:306）。 |
| **3.3** | 新数据集入 data appendix | **yes** | 本文新造的标注物：41 条路由普查实例的三判官投票、120 项分层验证面板的 87 条有效投票、curated 别名表 `data/aliases.json`、placebo 供体表 `data/placebo_donors.json`、同关系竞争者供体表。**→ Task D 硬承诺（supp S2/S4 + data appendix）**。 |
| **3.4** | 新数据集公开+许可 | **yes** | **→ Task D 硬承诺**：`data/LICENSES.md`（草稿已在 `release_and_licenses.md`）。 |
| **3.5** | 文献数据集有引用 | **yes** | CounterFact→citep meng2022rome（main.tex:66）；GSM8K→citep cobbe2021gsm8k、MATH→citep hendrycks2021math（main.tex:306）。**后两条为 W2-7 新增**：此前 §6 用了这两个数据集却零引用、refs.bib 亦无条目，本项当时只能答 no。 |
| **3.6** | 文献数据集公开可得 | **yes** | 三者均公开（CounterFact/GSM8K/MATH 及其 500 项子集）。 |
| **3.7** | 非公开数据集的详述 | **NA** | 无非公开数据集。 |
| **4.1** | 是否有计算实验 | **yes** | 全文为计算实验。 |
| **4.2** | 超参取值个数/范围 + 选定判据 | **yes** | 正文已给抑制强度全扫（main.tex:214）。**→ Task D 硬承诺（supp S11 超参表）**须补齐三件：(i) 编辑层逐模型扫描与判据（Loc≥0.85 约束下取生成式 B0 ES 最高层）；(ii) penalty=8 **由冻结协议预先固定**、六点扫描是事后稳健性检查而非选点依据（**不得追认一个当时未记录的选择判据**；注意 ES 在 penalty=12 处高于 8，正文『五档之间 ES/RR 无序』已覆盖此事实）；(iii) W-B 的 α∈{1,2,5}% 与 α*=1% 的伤害门判据。其余 EasyEdit 超参沿用上游默认、未调。 |
| **4.3** | 预处理代码入附录 | **yes** | `data/build_dataset.py`。**→ Task D**。 |
| **4.4** | 实验与分析全部源码入代码附录 | **yes** | `src/`（含 `edit_loop.py`/`think_budget.py`/`genbench.py`/分析脚本）。**→ Task D**。 |
| **4.5** | 源码公开 + 许可 | **yes** | **→ Task D**：`data/LICENSES.md` + 仓库许可。 |
| **4.6** | 新方法源码注释指回论文步骤 | **partial** | **诚实降级**：`edit_loop.py`/`think_budget.py` 注释密度高，但锚点指向内部 `plan.md` 章节与 prereg，而非论文小节。发布前逐文件补论文小节映射属可做但未做的工作，故不冒充 yes。 |
| **4.7** | 随机种子设定方式 | **yes** | §3.3 明写三个固定种子及其配对口径（main.tex:122）；配置层 `experiments/*.yaml` 记 `seed: 42`，`think_budget.py:79` 在生成前 `torch.manual_seed(seed)`。 |
| **4.8** | 计算基础设施 | **yes** | **正文无落点，全部由 supplement 授权 → Task D 硬承诺**。须如实写两套异构环境：(a) Hopper 卡上 bf16 会使 ROME `compute_v` 发散成 NaN，故该侧全程 `float32`；(b) Ada 卡侧用 bf16；两者经 n=40 校验可混用。软件版本以 `env.lock` 为准并**标注其冻结日期 2026-06-10**（早于 GPU 主跑，不冒充跑时快照）。**平台名与集群路径一律不出现（L4/L5 匿名化类别）**。 |
| **4.9** | 评测指标形式化 + 动机 | **yes** | §3.1 给出 ES/RR/RR^s/CLR 的形式定义与嵌套关系，并说明为何是不同错误剖面的操作性端点（main.tex:70）；Loc 的受限用法同段写明。 |
| **4.10** | 每个结果的运行次数 | **yes** | 贪心档每格单次确定性解码（main.tex:66）；采样档三固定种子、597/600 seed-pair 完整（main.tex:122）。逐格运行次数表 **→ Task D（supp S11）**。 |
| **4.11** | 超越单点摘要的分布信息 | **yes** | 全文端点均带配对 case-bootstrap 区间（例：main.tex:99）。 |
| **4.12** | 用恰当统计检验判显著性 | **yes** | 配对 case-bootstrap；未做多重性校正且明确声明不主张（main.tex:208）；次要端点的未校正 p 逐字报出（main.tex:208）。 |
| **4.13** | 列出所有最终超参 | **yes** | **→ Task D（supp S11）**。**W2-7 订正**：正文原将抑制强度称作 “Clamp strength”，而 `clamp`（`clamp_norm_factor`）在同一份 yaml 里是 ROME 编辑器的另一个旋钮（值 2/4），照原文复现会调错参数；已按代码与 results.json 的真实命名改为 “Penalty strength”（`edit_loop.py:330` `suppress_cfg["penalty"]`、`results.json` `rq3.alpha_sweep.penalty`）。 |

## 本轮由填 checklist 反查出的两个正文缺陷（均已修）

1. **超参命名错误（4.13）**：§5.1 把抑制强度叫 “Clamp strength”，与同一 pipeline 中 ROME 的
   `clamp_norm_factor` 撞名且取值域不同（我们的 penalty ∈{0,2,4,8,12,16}，编辑器 clamp ∈{2,3,4}）。
   复现者会调错旋钮。已改为 “Penalty strength”，与 `results.json` 的 `alpha_sweep.penalty` 对齐。
2. **数据集零引用（3.5）**：§6 使用 GSM8K 与 MATH-500 但正文无引用、`refs.bib` 无条目；
   该项只有 yes/no 两个选项，无 partial 可躲，原状只能答 no。已补 Cobbe et al. 2021 与
   Hendrycks et al. 2021 两条（arXiv 页逐条核实标题/作者/年份，非凭记忆）。
   MATH-500 的 500 项子集来源不在正文过度归因，归 `provenance_manifest.md` 记录。

## 唯一的 partial 与唯一的 no

- **4.6 partial**：源码注释锚点指向内部 `plan.md` 与 prereg，而非论文小节。可补但未补，不冒充 yes。
- **2.1 no**：本文无理论贡献，这是事实描述，不是缺陷。

## 扫描确认

填完须跑：无平台名、无集群路径、无作者身份线索（见提交说明中的 scrub-grep 结果）。
