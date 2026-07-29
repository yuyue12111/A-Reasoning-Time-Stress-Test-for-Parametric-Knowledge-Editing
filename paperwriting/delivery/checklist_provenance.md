# ReproducibilityChecklist 核销台账（W2-7 / Task B / M19）

- 对应文件：`paperwriting/manuscript/ReproducibilityChecklist.tex`（AuthorKit27 模板填答，31 项）
- 行号基准：`main.tex` @ 本次提交的父 commit `7a4df5e`（行号会随后续编辑漂移，锚点引文为准）
- 统计：yes 19 / partial 3 / no 1 / NA 8（W2-8 降 4.2；W2-9 降 4.8）

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
| **3.4** | 新数据集公开+许可 | **yes** | **W2-9 兑现**：顶层 `LICENSE`(MIT) 与 `data/LICENSES.md` **已落库**，逐数据集列出上游许可与「重分发 vs 用脚本再导出」的界线。授权物今天已存在于仓库，非空头承诺。 |
| **3.5** | 文献数据集有引用 | **yes** | CounterFact→citep meng2022rome（main.tex:66）；GSM8K→citep cobbe2021gsm8k、MATH→citep hendrycks2021math（main.tex:306）。**后两条为 W2-7 新增**：此前 §6 用了这两个数据集却零引用、refs.bib 亦无条目，本项当时只能答 no。 |
| **3.6** | 文献数据集公开可得 | **yes** | 三者均公开（CounterFact/GSM8K/MATH 及其 500 项子集）。 |
| **3.7** | 非公开数据集的详述 | **NA** | 无非公开数据集。 |
| **4.1** | 是否有计算实验 | **yes** | 全文为计算实验。 |
| **4.2** | 超参取值个数/范围 + 选定判据 | **partial** | **W2-8 改判(原答 yes,现降 partial)**。正文已给抑制强度全扫与其预先固定的 provenance（main.tex:214）。降级理由是编辑层:**六个 checkpoint 中只有两个真扫过**——Qwen-7B(ROME 扫 {5,7,10},n=40,B0;判据 Loc≥.85 下生成式 B0 ES 最高,实测 .55/.475/.40 且只有 layer5 的 Loc 达 .85)与 Llama-8B(layer{5,6,7}×clamp 四格 n=60 → 定 layer6/clamp2);其余四个(32B L12 / 14B L9 / 1.5B L5 / 70B L14)按 0.18 相对深度**先验设定**,预置的条件回退扫描({10,13,16}/{7,9,12}/{4,5,7}/{12,16,20})**一次都没触发**;MEMIT 用冻结多层带、未扫。对这四个 checkpoint『尝试过的取值范围』根本不存在,答 yes 一次 ctrl-F 即被证伪。**→ Task D(supp S11)** 须给逐 checkpoint 层值与其确定方式;**并明令不得为 penalty=8 追认一个当时未记录的选择判据**(它由冻结协议预先固定,六点扫描是事后稳健性检查;注意 ES 在 penalty=12 处高于 8,正文『五档间 ES/RR 无序』已覆盖此事实)。 |
| **4.3** | 预处理代码入附录 | **yes** | `data/build_dataset.py`。**→ Task D**。 |
| **4.4** | 实验与分析全部源码入代码附录 | **yes** | `src/`（含 `edit_loop.py`/`think_budget.py`/`genbench.py`/分析脚本）。**→ Task D**。 |
| **4.5** | 源码公开 + 许可 | **yes** | **W2-9 兑现**：顶层 `LICENSE`(MIT) 已落库，明写不覆盖 `source/` 下第三方仓库与数据集。 |
| **4.6** | 新方法源码注释指回论文步骤 | **partial** | **诚实降级**：`edit_loop.py`/`think_budget.py` 注释密度高，但锚点指向内部 `plan.md` 章节与 prereg，而非论文小节。发布前逐文件补论文小节映射属可做但未做的工作，故不冒充 yes。 |
| **4.7** | 随机种子设定方式 | **yes** | §3.3 明写三个固定种子及其配对口径（main.tex:122）；配置层 `experiments/*.yaml` 记 `seed: 42`，`think_budget.py:79` 在生成前 `torch.manual_seed(seed)`。 |
| **4.8** | 计算基础设施 | **partial** | **W2-9 再降(W2-8 曾答 yes)**。§6 末 Reproducibility 段（main.tex:308）给出加速器类别与**dtype 政策及其原因**(Hopper 类上秩一更新的 bf16 会发散成 NaN,故该侧 float32、Ada 侧 bf16,40 例交叉验证),并把版本指向已释出的 lock 文件。**降级理由**:4.8 明文要求 OS 与库的名称和版本,而正文只有一个指向 lock 文件的指针、零库名——正文页面零余量,补库名句需牺牲第一/第二组的矛盾与引文修订,按既定优先级选择降级而非硬塞。**W2-9 同时修正两处事实**:(a) 指代——原文 “there” 的最近先行词是 Ada 那块而 NaN 在 Hopper 侧,已改为显式命名;(b) **加速器类别原只列两类,实为三类**——H100(80GB)也产出过被报告的数字(genbench A1 见 plan.md:215、base_probe 六尺度见 plan.md:300),已按 M03 在 `rq3.environment` 补 `hopper_class_secondary` 并入正文。**→ Task D**:OS/库名/EasyEdit commit 与判官版本串进 supp S11。**W6**:fig:gap 回正文占页,Reproducibility 段整段 verbatim 移入 supp S11;正文 §6 留一句指针(受 promise 门盯守),main.tex:308 位置引用作废。 |
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
