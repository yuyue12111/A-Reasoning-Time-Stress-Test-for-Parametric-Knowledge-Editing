# plan.md · AAAI-27 项目总计划

- **项目代号**: `why-aaai` / 内部名「越想越退」(Thinking Undoes Editing)
- **目标**: AAAI-27（2027-02-16/23, 蒙特利尔）。首选 **AI Alignment track**（编辑作为安全干预在 test-time compute 下失效），备选 Main Track
- **硬截止**（gap-review E1 多源亲核,2026-07-08 更新;OpenReview 上再终核一次）: abstract **2026-07-21**、全文 **2026-07-28**、supplementary+code **2026-07-31**（均 UTC-12）。**内部冻结不动**=abstract 7/18 / 全文 7/25（各留 3 天缓冲）。**checklist 随全文 7/28 单独上传且明文计入录取决策**。（旧记 7/20/7/27 偏早 1 天=更保守,不影响内部线；AGENTS/CLAUDE 入口已按 v1.88 同步。）
- **页数约束**: 正文 **7 页** + 至多 **2 页仅参考文献**（共 9);正文**无 appendix 位**→ 所有"下附录"项去向=supplementary(评审不强制读)。**评审机制(gap-review E2 修正)**: Phase-1 每篇 **3 名人类审稿人 + 一份 AI 生成辅助评审**、**审全文**、SPC/AC 决定去留;**无 Phase-1 rebuttal**(唯一 rebuttal 窗 10/19–25 只给进 Phase-2 者);"abstract 与全文实质变更可径直拒"条款存在 → **全文数字一致性(B1/B14/[pending] 清零)是 Phase-1 生死件**,非仅门面。图1/引言仍最重(人类注意力)但不再唯一。
- **数字写入铁律(v1.69)**:任何数字、显著性或认证措辞必须先有 `paperwriting/results.json` 的明确 JSON path；X 系列新结果须按「raw jsonl/分析产物 → `paperwriting/results.json` 数据块 + `_pending_draft_edits` → `paperwriting/manuscript/main.tex`」单向写入。`_verdict`、plan 变更日志和旧 review 不是数据源；无 per-item 落账不得写 paired/McNemar 认证。
- **版本**: v2.09 (2026-07-28)。当前执行：**Abstract v8.1 内部终版冻结，全面进入正文写作与债务落地**。唯一有效写作计划 = `paperwriting/WRITING_PLAN.md`。**投稿前科学队列=零**：不跑 B15 interaction、不烧 X-A 池、不加 seed/数据集/编辑器。官方 X1 `9/18 FAIL` 永远不变且须正文紧邻 routing hypothesis 披露。
- **W3 交接快照 (2026-07-26，写在此处以便随时 /compact 不丢状态)**:
  **进入 W3 时的状态** —— W2 正文冲刺结束，`f4f7042` 为可交外审版本。
  **门禁基线（任何改动后须回到这四条）**：`python3 src/check_manuscript.py` PASS（§3=112 / §4=64 / §5=171）；
  `uv run --no-project --with pytest pytest -q src/test_check_manuscript.py` = **167 passed**；
  四步编译 = **8 页 = 正文 7 + p8 纯参考文献**、0 overfull / 0 undefined / 0 Type-3；
  `python3 src/scrub_artifacts.py --audit` = 提交层 31/31 CLEAN。
  **W3 原定范围（WRITING_PLAN:91）**：① 机器对账 ② 禁语扫描 ③ 判官式全文攻击 ④ abstract↔正文对账。
  **其中 ①②④ 在 W2 期间已建成为 fail-closed 常驻门禁**（checker 的 RJ 逐条绑定、禁语表含四类绕过模式、
  冻结摘要 SHA 与全覆盖断言、supplement 承诺逐字配对门、匿名双层扫描），
  **故 W3 的实际重心是 ③ hostile review + 视觉层收口 + 7/31 发布链**。
  **在飞状态与产物位置**：
  (a) 主图选例 = `cf_6933`，候选全表与逐条严格判据在 `paperwriting/delivery/mainfig_case_candidates.json`，
      筛选器 `src/find_mainfig_case.py`；关键性质=N/T 两链逐字共享前 61 词、在恰好该生成旧值的 token 处分叉、
      旧值提及 9→2 而非归零；**图上不得标路由**（32B cell 的普查标签是 Recall，14B 才是 Bridge，逐链不可跨 cell 搬运）。
  (b) 服务器完整 `results/` 已取回本地，位于仓库根的 `results 2/`（288M，已 gitignore；tarball 亦已忽略）。
      五臂重算需临时把 `experiments/probe32b*.yaml` 的 `out_dir` 指向 `results 2/probe`，再跑
      `python3 src/cross_arm.py --budget B3 --editor ROME --arm N=… --arm T=… --arm D=… --arm P=… --arm C=…`。
      重算产物与对账结论已固化在 `paperwriting/provenance_manifest.md §1` 与
      `paperwriting/delivery/esup_crossarm_5arm_recompute.json`（sha256 `5a0ad3ee…`）。
  (c) **仍 OPEN 的唯一科学裁决 = P14 哪一列权威**（正文两推导下均成立，不挡 7/28）。
  (d) **7/31 发布链未动**：supplement 八节全是骨架（有逐字配对门看着）、Fig.2 待删 panel A、
      Fig.3 缺 strict 面板（自设硬门）、`src/anonymize.py` 未写且**每个分片 `_meta` 带完整平台路径**、
      `src/package_release.py --check` 现为 BLOCK（设计如此，anonymize 跑过才解）。清单见 `delivery/t2_supplement_queue.md`。
  (e) **仍只有用户能做**：OpenReview 摘要换 v8.1（校验器 `paperwriting/delivery/openreview_swap_check.py`，
      盯 2 个 U+2014；表单编辑权 7/28 UTC-12）。
  **协作环纪律（现行）**：计划 session 只下发约束+授权证据+失效模式，不下发成品句；
  **任何被改动的文本都必须过审，包括复制、搬运、改一个词的编辑**；
  出口条件=只有「自相矛盾 / 越天花板 / 承重术语未定义或被错述」三类才回计划 session。

- **v2.09/W3-3 变更 (2026-07-28)**: **门禁真值审计（任务 0）先做，结论比预期糟：门是空的比门是假的更多。** ① **【已修的空门】** `plots.py` 三处 `rec.invariant(...)` 的第二个位置参数就是条件，其中两处是字面量 `True`（`:1085` strict endpoint、`:516` categorical panel A），一处（`:767`）把常量和它自己的字面量比。另有 `rec.derived(raw_value=187, expected=187)` 且正则 `headline.*?n=187` 把 187 烤进自己的模式——**记录 n 改成 181 也照样 MATCH**。四处全改成真条件：strict 那条现在读 panels 与 rows（且**改成陈述真相**——supplement 的 `% GATE` 明写该图未带 strict 面板前不得发布，而旧 detail 说"故意省略、永久如此"，两者本来互相矛盾）；categorical 那条移到画完之后、真数连线；authoritative 那条改读 `rec.entries`；187 改成从 `_70b_note` 里解析。 ② **【已修的空门·正文侧】** `check_unaudited_section_numbers` **8 个 region 全部被 `continue` 跳过**（每个 title 都在 `AUDITED_SECTION_TITLES` 里），即**整个函数什么都没检查**，而成功横幅还在报 `unaudited-section numeric gates`——**横幅在说谎**。已改：横幅删掉该项，函数只在"没有任何节被审计"时报错。 ③ **【已修·supplement 承诺门对内容全盲】** 该门只做三件事（正文里配对引文、`\section` 与 marker 计数、Contents 数字），**从不读任何一节的正文**——空的 `\section{Figures}` 今天照过。已改成**按 section span 解析**：每节必须自带 marker、必须有实质内容。**门一建成当场炸出三节**（Figures 0 词、Concept-Direction 8 词、Sunk Regressions 14 词），三节已补写实质描述。 ④ **【已修·D2 的 `87` 形同虚设】** 该断言被 §3 里无关的 `n=187` 顺带满足，改成绑 `votes for 87 of 120 stratified items`。 ⑤ **【最重要的结构性发现，未修，须裁】** 对抗审计做了一次**变异演示**：把 `main.tex:220` 的 19.3%/8.5% **臂归属对调**、同时把两条 RJ 对调，则**所有实质检查全过**，只剩三个 snapshot SHA 报错——而 `repin_snapshots.py` 正是设计成"只剩 snapshot 就自动重钉"。**即「抑制反而把回退变成三倍」这种论断今天可以合法进稿**。根因：门层对**归属**（哪个臂/哪个总体/哪个预算）零覆盖。另：supplement 的数字（含 X1 的 `9/18`、required `15`）完全不在台账内，`ReproducibilityChecklist.tex` **门从不读**。 ⑥ **【1B 已做·纯改名】** Table 1 表头改成 `Direct-answer ES_{B_0}` / `After-chain ES_{B_3}`，§3.1 给出两个名字，§1 用名字陈述对比。**RJ 指针零变更**：353 条 (claim,pointer,format) 三元组前后完全一致（脚本可证）。 ⑦ **【3A 已做】** `.106`/`.107` 进 §1 第一条贡献，§1 首次拥有 RJ 台账（数字仍逐条绑定，不是放行）。 ⑧ **【5A 已做】** MEMIT 引用补上（`meng2023memit`），欠三轮结清。 ⑨ **【出口判据 2 的机器证明已建】** `src/audit_caveats.py`：按内容指纹抽取全部带限定的子句，`--compare` 断言没有子句在重写中消失（消失必须在 map 里指认继任者）。基线 `delivery/caveats_w3_3_before.json` = **156 条**；本轮结束仍 156，零丢失。 ⑩ **【未做】** 2A/2B/2C/2D/2E 全部（§5 均值职责数仍 1.25 未降）、4A（§4 已在 W3-2 更名为 `Visible Routes and an Unidentified Mechanism`，本轮未再动）、3B（摘要减数，等你指令）、5B（摘要删两词，本轮未做）。**86 条 required string 的逐条真值审计正在后台重跑**（首次跑因 args 被序列化成字符串而空转，已改为把字符串表直接嵌进脚本）。 ⑪ 门禁：checker PASS（§3=124 / §4=49 / §5=164）、pytest **167 passed**、8 页 = 正文 7 + p8 纯参考文献、0 overfull / 0 undefined、匿名 31/31 CLEAN、三张图 source map 全 PASS（且现在是真条件）。
- **v2.08/W3-2 变更 (2026-07-27)**: **A 四条阻断全清（其中三条是我 W3-1 自己写错的）+ B 门禁改规格（结论：解锁不了）+ C/D 部分。12 个 agent 的对抗审计落库。** ① **【A4，我 W3-1 写错】** 四个 `_loc` **不是同一预算**：Qwen-32B `.958`=**B3**（同跑 B0 是 .970）、Qwen-1.5B `.954`/Llama-8B `.835`/Llama-70B `.930`(n=187 过滤子集)=**B0**。W3-1 把一个 B3 值和两个 B0 值当同质量并列。已按预算分别标注并补 `.954`。**另一处更严重**：W3-1 写「Qwen-7B/14B 的 Loc 全仓库无记录」**是假的**——原始分片可算出 7B B0 .985/B3 .975、14B B0 .960/B3 .950，`plan.md:150` 有 7B 层扫 Loc，`results.json` 自己的 `memit_replication` 有 14B Loc。真话只到「**没有为这两个 checkpoint 记录过 ROME headline 口径的 Loc**」，正文已改成这句；**分片重算值一个都没进正文**（冻结条款）。 ② **【A3】** 池子是**修复前的判分器选的**：prefilter 于 6/17 前跑，`515b87a`(6/22) 才给 `metrics.hit` 加词边界 + 丢 <4 字符别名（别名表里有 287 条 1–3 字符 ISO 码），而 `prefilter.py:120` 调的正是它；此后**全仓库无任何重建记录**，当时的补救是「纯重打 jsonl，无需重生成」。§3.1 已写明「所有报告的率用修好的判分器，池子的成员资格没有」，**不估量级**。 ③ **【A2】** `RUNBOOK:79` 的「B0 实测 ~50%」是**预过滤存活率的文档注记，背后无任何存活工件**。原句「it was never run at B₀」站不住，改成**「No B₀-gated pool was ever built」**（真）；~50% 无 results.json 路径，不入正文。 ④ **【A1】** `plots.py:564` 画的是 `ES_B0−ES_B3`，图内两处自陈符号；W3-1 删掉消歧句后图注的「change from zero thinking to a native chain」读作反号。改一个词：**change→drop**，与 Table 1 表头同术语，**零行代价**。 ⑤ **【B 结论：门可以改规格，但解锁不了】** 已把 §4 的 42 条拆成 `required_strings`(必留正文) 与 `coverage_strings`(正文或 supplement 二选一 + 正文留指针)，机制落库。**但我提名的 4 条可迁串被三个对抗 lens 全部驳回（4/4 refuted）**——理由分别是 body-only 读者会误推、无其它正文句承载该分母、以及仓库记录显示每条都是为堵某个具体缺陷加的。**所以 §4 压到 ≤700 词不可达**：927→**864**（只靠散文收紧 + 投票构成迁 supplement）。 ⑥ **【C】** §4 更名 `Causal Diagnosis`→**`Visible Routes and an Unidentified Mechanism`**（3/3 报告说原标题越权；新标题不断言诊断，且与 §1「visible paths / we withdraw that claim」对齐）；§4.1 已于 W3-1 降级；§4.3 三段并一段；§4.4 并成一句 + 脚注。 ⑦ **【D】** §5.3 自相矛盾已修（「Neither control moves the answer」+「不是无效应证据」→ 改成「不与无抑制分离」+ 一次限定）。另修三处**事实错误**：`changes direction`（两套推导**同号**，只是过零判定不同）、`every arm here is an intervened condition`（**N 臂没有干预**，且是 Table 1 那次跑；门禁里那条守卫串本身是假的，已连同测试一起改成 `the demonstration runs through an intervention`）、`118` 误引 §4.4（该节只有 106/90）、`arm-wise n differences reflect harness errors only`（与自家 provenance manifest 冲突）。 ⑧ **【F】** `audit_narrative_load.py` 升为常驻门 `check_narrative_load`，按节设职责密度天花板（§1 0.95/0、§3 1.18/2、§5 1.28/1），**只准往下棘轮**。 ⑨ **【本轮未达标，须计划 session 裁】**：§4 864 词 ≠ ≤700；**§5 均值仍 1.25 未降**（只做了 4 处外科修复，未做 §5 分层重构）；E（strict 前置）未做。 ⑩ **【须用户裁：冻结摘要与正文冲突】** 20 条 §5 发现里两条指向**冻结摘要**：摘要说 `placebo and same-relation controls have near-null answer-level effects`，而 §5.3 现在明说「不是无效应的证明」；摘要与 §1/§2 的 `dose-graded` 在正文里被两处收回（唯一单调量是 CLR，而 CLR 被明定为 manipulation check 不是 outcome）。**这是正文↔冻结摘要的自相矛盾，属出口条件第一类，我不动摘要。** ⑪ 全部 20 条落 `paperwriting/delivery/w3_section5_findings.md`（含每条的 file:line 与「修复必须保住什么」）。 ⑫ 门禁：checker PASS（§3=**124** / §4=**49** / §5=**164**）、pytest **167 passed**、8 页 = 正文 7 + p8 纯参考文献、0 overfull / 0 undefined、匿名 31/31 CLEAN。
- **v2.07 变更 (2026-07-27)**: **W3-1 总体正名落地 + W3-2 结构先行；版面由 §4 与三处重复文本自筹。** ① **【最重要】§3.1 新增 `Which requests we test.` 段——本文第一次说出自己的 estimand。** 反查 `src/prefilter.py` + 六个 `probe_*.yaml` + `run_pilot.load_cases` 得到完整链路：CounterFact 清洗全量 → seed42 洗牌 → 留有 o_old → **取前 600**（`prefilter.py:80` 的 `3*n`）→ 逐条用**未编辑的 Qwen-7B** 在 **B3** 生成、**答案命中 o_old 别名则留**（`:119-120`）→ **248 存活**（plan v1.19① / analysis/10:4）→ 每次运行**再用 seed42 洗一次**取前 200（`run_pilot.py:23-27`）。**六个 checkpoint 共用这一份**（每个 yaml 的注释都自称「同序可比」，属实）。正文因此写明两个后果：**所有 level 都是这个池上的率、不是 CounterFact 上的率**；以及**筛选预算与主对比的其中一臂重合**（筛选读的是 B3 生成），并明说「为『思考时取回旧值』挑出来的池，若有偏向也是偏向我们报告的这个下降；从未在 B0 上跑过筛选，所以这里没有任何东西给它定量」。全链路落 `paperwriting/delivery/w3_population_provenance.md`；数字按 M03 建 `protocol.population`（每个字段都标了取自哪一行代码/配置）。 ② **W3-4 的两条协议事实同批落地**：`B3` 上限 8192 写进 §3.1（此前只有 B₁ 的 256）；**编辑层策略首次进正文**——**六个里只有两个真扫过层**（Qwen-7B 扫 {5,7,10}、Llama-8B 扫 layer{5,6,7}×clamp），其余四个按 **0.18 相对深度**直接放、条件复扫从未触发；Llama-8B 的扫描把 clamp 4→2 而**另外五个仍用 4**（含 Llama-70B 这个头牌 cell）。另**首次报告编辑质量**：邻域 target-value non-leakage `.958`(Qwen-32B) / `.930`(Llama-70B) / **`.835`(Llama-8B，低于该次扫描自己的 .85 合格线，且当时明确选择不调参凑线)**；Qwen-7B/14B 的 Loc 全仓库无记录，**不编造、只报有的四个**。 ③ **W3-2 结构（本轮做了结构，量化在结构之后才出）**：贡献从三条收到两条（gap + control point，与冻结摘要的两句话一致），bounded-transfer 降为第二条内部的界定句；C1 主句只留三个平铺结果，**所有界定移入同句脚注、一条不删**；§4.1 cloze sanity 整节降为 §4 前言一句 + 脚注（该结果本文自称「近乎同义反复」，降级方向合规）；**删 route 表**（四个计数本就在正文散文里，Share 是导出量），caption 的投票构成搬进正文那句承诺它的话里。 ④ **版面自筹（正文一度溢出到 p8）**：新增约 16 行，靠删 route 表、§4.1 降级、以及**三处真重复**（Fig.1 caption 与 Table 1 caption 的 complete-case 说明、§5.2 脚注两个算例中的一个、§6 与 §3.1/§4.2 脚注三处重复的 shared-bias 句）补回。终态 **8 页 = 正文 7 + p8 纯参考文献**。 ⑤ **W3-2 的量化工具落库**：`src/audit_narrative_load.py` 按表面标记给每句打职责数，输出 `delivery/w3_narrative_audit.md`。**结果与计划前提不同**：改写后 §1 的 4+ 职责句为 **0**（均值 0.91），负载最高的是 **§5(1.25) 与 §3(1.14)**，而**全文最重的一句是 §2 的「四性质合取」新颖性句（60 词 / 4 职责）**——正是 W3-4 打算换成对比表的那一句。 ⑥ 门禁：checker PASS（§3=**123** / §4=**54** / §5=**164**）、pytest **167 passed**、8 页、0 overfull / 0 undefined、匿名提交层 **32/32 CLEAN**。 ⑦ **本轮 12 个测试红**：逐条判「是稿子错还是断言旧」——**两条是稿子错、已改稿**（canned thought 我写成 `moves edit success the other way`，比原来的 `improves edit success` 更含糊；forward pointer 丢了 `whether length alone accounts for the effect` 这个被点名的问题），其余十条是锚点随删表/降节而失效，改断言时都把**被保护的性质**重新断言了一遍。 ⑧ **未做/待裁**：W3-3 全部（主图、Fig.1 重画与拆轴、§5 森林图）、W3-4 余项（抑制器伪代码、参考文献 16→30、对比表）、W3-5 supplement 填充、W3-6 端点主次（等用户指令）。**Fig.1 重画的空间账已算清**：现 7.20×3.55in 渲染在 0.68\textwidth = 缩到 66%，若重画成 7.20×2.55in 并渲染在 0.95\textwidth，则**占版面几乎不变而字形放大约 40%**。
- **v2.06 变更 (2026-07-26)**: **W2-16 交外审前最后一轮。四项挡交付 + 门禁升级。做完即交。** ① **【出口条件已定，本轮起生效】** 此后只有 **「自相矛盾 / 越天花板 / 承重术语未定义或被错述」** 三类发现才回计划 session；其余（措辞可更精确、结构可更好、hedge 分布可再调）一律归外审，不再触发新一轮修订。 ② **A 重生成 Fig.1（图内文字与图注互斥）**：`plots.py:602` 的面板 B 标题是 `Qwen-32B controls`、行标是 `True chain`——**读者看的是图不是图注**，所以 W2-15 的修订当时并没有落到读者眼前。改为 `Qwen-32B budget and decoding conditions` 与 `Short budget`，重生成、fail-closed SourceMap 断言全过。**重渲未带回 `/Creator` 泄露**——W2-8 的 A0-2 从生成器源头修掉了该串，源头修复按设计生效（这也验证了当时那个判断）。新图入 main.pdf 后重跑 zlib 解流扫描：CLEAN。 ③ **B 定义 B₁（承重术语未定义）**：B₁ 在正文出现 4 次、3 次被称 `native`，却从未定义；实为 `think_budget.py:33` 的 `CAP={"B1":256,...}`——**到 256 token 即 break，由 harness 补 `</think>`**；全文 `256` 出现 0 次、`truncat` 0 次。已在 §3.1 一次性写清「每个预算档是 think span 的上限；模型未自行结束则由 harness 关闭」，在 §3.3 B₁ 首次承载论证处写明其上限为 256 token（按 M03 新建 `/protocol/think_budget_cap_tokens`，该常量本就被每个分片的 `_meta.think_budget_cap` 原样记录）。**此后 §1/图注/§3.3 三处一律不再无条件称其 `native`**——被中途掐断的链与模型自己想得短的链不是同一个操作，而 §4.4 保持活着的 buffer 账恰恰依赖这个区别。 ④ **C §1 leg 1（越天花板）**：原写 `the erosion already appears at a shorter native chain`，三重问题——`the erosion` 回指上一句 capability 运行的 .106（其 B₀=.595），而 B₁ 的 .130 来自 **F2 另一次运行**、对的是**该运行自己的** B₀=.625；`already` 是 ordering 断言，而 §4.4 原话是 `we infer neither saturation nor an ordered trend`；`shorter chain` 暗示模型行为，实为我们施加的档位。改为「另一次控制运行在更短的 think budget 上показ同向、对照其自身的零思考基线」。 ⑤ **D §5.3 推导争议范围**：`derivation-dependent` 原无先行词（全文 `provenance` 仅此一见），且紧跟「证据是 T−P」读起来像争议只限于一个不被使用的量——**而 T−P 正是从同一个有争议的 P 臂算出来的**。现说全三件事：P 臂不可逐字节复现（分片比记录分析多一行）、可复现推导使**每个**报告的 T−P 量在第三位小数移动而不改变任何结论、placebo 的链内对比在两推导下结论方向不同故不承重。**未印重算列任何数值**（它不在 results.json 里）。 ⑥ **E 门禁升级（计数匹配 → 逐条逐字配对）**：W2-15 把承诺改写成 `in the released provenance record` 后，正则只匹配 supplement/supplementary，门就看不见它了。现在正则覆盖一切外部工件延迟（supplement / supplementary / provenance record|manifest / released code），且每条 `% Discharges:` 必须写一段**≥40 字符的逐字子串**，门断言它在正文中恰好出现一次、且每个承诺被恰好一个标记覆盖。**不脆：是复制不是抽取。** 升级后当场炸出全部 7 条旧标记（都是转述）+ 缺一个 provenance 节 + 计数应为 8 而非 7，均已修。 ⑦ 门禁：checker PASS（§3=**112** / §4=64 / §5=171）、pytest **167 passed**、8 页＝正文 7 + p8 纯参考文献、0 overfull / 0 undefined / 0 Type-3、匿名提交层 31/31 CLEAN。 ⑧ **已声明的未完成项（不挡交付）**：Fig.1 宽度 0.68 与最小字形约 2.9pt；主图未成；Fig.2/3 未接。
- **v2.05 变更 (2026-07-26)**: **W2-15 只修不加五处 + 一道新门。纪律扩容。** ① **【纪律扩容】原条为『新写散文必须过审』→ 改为『**任何被改动的文本都必须过审，包括复制、搬运、改一个词的编辑**』。** 成因：这已是连续第七轮新文本带缺陷，但**本轮成因与前六轮不同**——不是新写的句子，是从 `provenance_manifest.md §1a` 搬措辞时把 `here` 改成 `in the supplement`。**改一个词，代价是四层问题**：假承诺（supplement 里没有该节）→ 指错文档（记录实际在 provenance manifest）→ 逃过所有门（两个硬编码串守不住新增承诺）→ 供 supplement 计数失真。 ② **§5.3**：删该半句，改指已释出的 provenance record（那才是记录的真实所在）。 ③ **§1 C1 放弃『three controls / each bound a different alternative』框架**：`main.tex:118` 明写那是**一个控制运行的三个预算臂**（B₀/B₀ₚ/B₁），B₁ 不是控制而是**效应在更短预算下已经出现**；canned thought 的结论现与其长度限制**同句**给出（`without isolating length`）；sampling 结论不变；**全句不再声明计数**。（起草时我一度写 `a fixed canned thought of that length`——§3.3 恰恰明写它**不是**长度匹配填充，已自查拦下。） ④ **Fig.1(B) caption 不再统称 controls**，改描述性措辞（三种预算/解码条件下的配对变化；B₁ 与 canned thought 明写为**同一控制运行的两个臂**；基座并列），正是这个统称让 §1 把它们数成三个独立控制。 ⑤ **【新门】supplement 承诺门**：正文每一处 `the supplement`/`supplementary figure(s)/material`（**大小写不敏感**——上次漏掉的第 7 处正是 `The supplement` 大写开头）必须在 `supplement.tex` 有一条 `% Discharges:` 对应，每个 `\section` 必须带 `% Discharges:` 或 `% Supports:` 标记，且 Contents 里声明的数目必须等于实际承诺数。**门建成即抓到两个真实缺口**：S3b 一条标记盖了两个承诺、超参节无标记。此前守这件事的是**两个硬编码串**，所以本轮新增承诺才能溜过去。 ⑥ **禁语补名词形与否定/保持形**（`without moving the answer` / `leaves the answer unchanged` / `the answer is unaffected` / `the answer holds` / `no answer-level movement` / `answer-level inertness`）。**通则记档：禁令必须同时覆盖名词形与否定/保持形**——这是继 `erasure` 绕 `erased` 之后**同一教训的第二次**。 ⑦ **本轮我自己的两处错已修**：新门用 `main_path.parent` 解析 supplement.tex，而测试夹具把 main.tex 拷到临时目录 → 改为仓库相对路径（门本身的设计缺陷，不是测试问题）；以及三条 W2-14 测试断言的是被本轮替换掉的措辞。 ⑧ 门禁：checker PASS（§5=171）、pytest **163 passed**、8 页＝正文 7 + p8 纯参考文献、0 overfull / 0 undefined / 0 Type-3、匿名提交层 31/31 CLEAN。
- **v2.04 变更 (2026-07-26)**: **W2-14 五处句级修订 + 第四类绕过模式补门 + 文档同步。改完即交外审。** ① **【流程纪律，最重要产出】新写文本未过审即不得视为完成——任何一轮，包括只改几个词的一轮。** 现已 6/6 命中：每一轮的新散文都藏着至少一个缺陷，**下发成品句的轮次与只下发约束的轮次都一样**。缺陷不随计划 session 的输出格式转移，只随『有没有被审』转移。执行 session 提交前须逐条打勾八条自审（结论各有其前提 / 统领句未替各支补结论 / 无先断言后否认资格 / 交叉引用描述目标节真实问题 / 标题未承诺正文省略之物 / 总结节不超出被总结的结果节 / 散文点名的集合与计数同图表一致 / 括注指向仍存在的量）。 ② **§1 C1 四缺陷同修**：(a) canned-thought 支原写 `so a think span alone does not produce the gap`，**排除了 §4.4 明写仍活着的 content-independent buffer 账**——改为只限定在实际跑过的那一个固定短 canned thought；(b) 统领句 `Three controls… bound what else could be happening` 即便 base 支不写结论，也已替读者补上『base 漂移不能解释它』这个 §3.2 拒绝的推断——base **移出计数、移出统领句**，单独成句并明标 juxtaposition；(c) **控制集合与 Fig.1(B) 对齐**（{短原生链 B₁, canned thought, sampling}），此前 §1 用的是 {base, canned, sampling}，集合不同而数目相同、最易被当成掩饰；(d) 前向指针改为描述 §4.4 的真问题（长度账），原写『内容是否要紧』是反问题。 ③ **§5.3 三处**：(a) 删除 `leaving the answer where it was` 这一**断言形式**——同句前半断言、后半否认断言资格，自我否定；(b) 不再写 `the dissociation this section rests on`（敌意评审可与同句的 `not evidence of no effect` 并排引用，论证作者自宣因果节无支撑），改为**申明本节主证据仍是结果前指定的 T−P**，competitor 只是界；(c) 小节标题承诺 placebo 而正文对其链层完全沉默 → **显式标记**该对比因推导版本相关而不承重，**且不印任何一版的值**（印哪一版都等于在 P14 仍 OPEN 时选边）。 ④ **【第四类绕过模式，补门】**：W2-13 把必现串从**授予句** `inertness may be claimed only at the answer level` 挪到了**免责句** `at the answer level the comparison is compatible with zero`，于是授予句留下且不再被任何门检测。**规则记档：禁令必须打在断言形式本身，不能只锚它的标签或它后面的免责句。** 已加 `answer-held assertion` 模式（`leav\w+ the answer where it was` / `the answer (did|does) not move` / `the answer stay\w+` 等），回归测试确认它能抓住 W2-13 那句及其变体，且放行三处合法用法（惩罚不作用于答案段是机制陈述，非结果断言）。前三类为：同义词绕过（`erasure` 绕 `erased`）、改述绕过（`declines at every step` 绕 `monotonic`）、名词化绕过（`certification`）。 ⑤ **D**：`provenance_manifest.md §1` 已过期（仍写正文『reports that the placebo's is smaller and carries nothing』，而 W2-13 已删该句）→ 按 B 组改完后的实际措辞同步。 ⑥ **工具落库**：`src/repin_snapshots.py`——只重钉快照 SHA，**存在任何实质失败即拒绝动手**（此前这段逻辑一直在 scratchpad 里、被清过两次）。 ⑦ **本轮我自己的三处测试错误已修**（断言写错而非正文错）：`\caption` 分割取到 Table 1；`-.051[-.102,.000]` 在 Table 2 是 **strict T−N** 的合法同数字量；以及 W2-13 与 W2-14 两条测试互相矛盾。 ⑧ 门禁：checker PASS（§5=171）、pytest **155 passed**、8 页＝正文 7 + p8 纯参考文献、0 overfull / 0 undefined / 0 Type-3、匿名提交层 31/31 CLEAN；D6 required_content 与九条债务清偿不受影响。
- **v2.03 变更 (2026-07-26)**: **W2-13 A–D + E1。协作环纪律变更；§1/§3.2/§5.3/§7/Ethics 六处缺陷修完；六格基座漂移披露到位；scope 消融补第二档；主图选例按严格口径重判。** ① **【纪律变更，本轮起生效】计划 session 不再下发可直接粘贴的成品句**——连续三轮处方句产生新缺陷（W2-9 三处 MAJOR、W2-10 一处、W2-12 一处 BLOCKER+三处 MAJOR），根因是写句时手里没有该段上下文，反复出现前提—结论错配、指代悬空、主题句与保留证据不匹配。**新格式=①约束 ②授权证据（results.json 指针+正文位置）③必须避免的失效模式；句子由执行 session 在上下文里组织，写完按『新写散文』自审。** ② **F1（§1，BLOCKER）**：原句把两个结论挂在采样这一个前提上，且把 `background drift` 写进排除式结论（§3.2 已封顶为『并列而非对比』）。改为三个控制各带各的结论，且**全部明写在最大 Qwen checkpoint 上**。 ③ **F2 + 必要披露**：删掉 `where it carries an interval` 这个读者兑不出来的对冲，改为在 §3.2 **正面披露**——配对区间只存在于该 checkpoint，其余五格只有无区间的水平差且**方向不一**。（四格为正、含并列 headline 的 70B；对冲已指向这批数，被挖出来比直接披露糟得多。）§7 同步限定范围。 ④ **F3 裁决=收窄主题句，不放回 placebo 数字**：`the two controls are not inert` → `the competitor is not inert`。理由：那个数正是 P14 争议列（记录版触零/重算版排零），放回等于把刚脱钩的依赖再接上；D6 的 required_content 不含 placebo 的 CLR，收窄不破清偿。配套在 manifest §1a **明写两版本的值**——正文沉默 + manifest 披露。 ⑤ **F4**：`inertness may be claimed only at the answer level` 等于在答案层授予了惰性，与紧邻上段的 `not evidence of no effect` 冲突。改为 `at the answer level the comparison is compatible with zero, which is not evidence of no effect`，**checker 的必现串同步改立**（有意再立法，非绕门）。 ⑥ **F5**：A1 删掉 placebo 的 −.051 后，消歧括注在指一个正文里不存在的孪生数，反而暴露『有个没报的数』→ 只留端点名。 ⑦ **F6（Ethics）**：base-drift 句孤悬在共线自陈之后、读起来像在反驳它 → 删除（其内容属 §3.2，且那里现在有范围限定）。 ⑧ **D**：scope 消融补报 B3 档（think .639 / all .670，两档 **CLR 完全相同 .268**）。CLR 跨档相同**加强**论证——两种 scope 压的是同一段链，差别只在答案段是否也被压；这是净收益不是让步。 ⑨ **E1（订正计划前提）**：原筛选器**本来就走 `metrics.py` 的答案级 RR 口径**，不是 CLR 也不是字符串包含；12 条全部通过**宽松**三态。但计划观察到的现象为真——**7 条的 N@B3 答案新旧值同现**。加**严格判据（RRs：旧值在、新值不在）**重判，只 **5 条**干净（cf_6933 / cf_19160 / cf_7868 / cf_1235 / cf_21055）。**选例仍是 cf_6933**：另四条虽过判据但文本不能上图（cf_19160 的 B0 是胡话、B3(T) 跑去讲 ThinkPad；cf_7868 的 B3(T) 是对冲句；cf_1235 的 B3(T) 编造地名；cf_21055 三段互不相干）。**cf_6933 另有一个未预料的性质**：N/T 两条链**逐字共享前 61 词**，在**恰好该生成旧值的 token 处分叉**，旧值提及 **9→2 而非归零**（首次提及在共享前缀内）——首 token 惩罚的教科书图示，且如实呈现『惩罚非审查』。 ⑩ **F 清偿重核**：九条债务在本轮改写后**逐元素重新验证仍全部 DISCHARGED**，锚点已刷新。 ⑪ 门禁：checker PASS（§5=171）、pytest **149 passed**、8 页＝正文 7 + p8 纯参考文献、0 overfull / 0 undefined / 0 Type-3、匿名提交层 31/31 CLEAN。 ⑫ **未做**：E2/E3（主图建图与 §8 判据⑦ 改判）—— E1 按计划单独回报后再进。
- **v2.02 变更 (2026-07-26)**: **P14 收口 —— 服务器完整 `results/` 已取回并重算。结论:`results.json` 记录的 placebo(P) 臂在完整工件里【无法复现】,且其中一处差异是承重的定性差异。** ① **重算方式**：完整 `results/` 下载到本地（288M，另有 157M tarball；**两者已加 gitignore**，此前 `results 2/` 与 `results.tar.gz` 均未被忽略、随时会被误提交）。用**释出版** `src/cross_arm.py`、五臂全上（`cf200`/`cf200sup`/`cf200sup_onew`/`cf200sup_placebo`/`cf200sup_strong`）、`--budget B3 --editor ROME` 重算。 ② **对账结果**：**N/T/D/C 的全部边际与 T−N / D−N / C−N 的全部对照逐条吻合**；**所有差异只涉及 P 臂**——P 的 n 记录为 **199**、重算为 **200**；P 边际 ES .507 vs .510（算术自洽于 101/199 vs 102/200）；T−P 四端点均差在第三位小数（ES `.122[.051,.193] p=.002` vs `.1212[.0505,.1919] p=.0012`）。 ③ **一处定性且承重的差异**：`P−N` 的 CLR，记录版 `−.051[−.102,.000] p=.054`（**含零、未确立**），重算版 `−.0556[−.1061,−.0051] p=.037`（**排零**）。正文 §5.3 正是靠「placebo 未确立」把 dissociation 归给 competitor 独担——若重算版为准，该句不成立。 ④ **已排除的解释**：P 臂分片有 **200 条唯一 B3 case、零重复**，4 条 error 与 8 条 `_meta` 已由加载器排除，**没有可丢的退化行**；`cross_arm.py` **不存在任何丢行开关**；`results/probe/` 只有一个 `cf200sup_placebo` tag、无 v2/rerun/别的 out_dir；全树全文搜索 `0.507` / P 臂 `199` / `0.122` **零命中**；CPU closeout 审计覆盖 percase/b15/cap3/f3/x2/x3/p0、**不含本电池**。 ⑤ **未擅自改任何数字**。哪一列权威是科学问题（记录版可能来自某次未留工件的订正）→ 落 `paperwriting/provenance_manifest.md`（状态 **OPEN**）+ 证据工件 `delivery/esup_crossarm_5arm_recompute.json`（sha256 `5a0ad3ee…`）+ 一条守卫测试（只守披露，不守结论）。**须计划 session 裁决后才动正文。** ⑥ **顺带解开旧悬案**：`T−C` 与 `T−P` 的 ES 逐字相同而 p 不同，是数据真实性质——placebo 与 competitor 两臂在各自配对交集上的 ES 完全一致（`C−N` ES = `P−N` ES = +.0152），故两个 margin 重合；p 不同是因配对集不同、bootstrap 重采样不同。W2-10 在 MEMIT 侧的同类处理（说重合而非重印）由此得到独立佐证。 ⑦ 门禁：checker PASS、pytest **145 passed**、匿名提交层 30/30 CLEAN。
- **v2.01 变更 (2026-07-26)**: **W2-10 硬写作优化。A 六处替换句修订 + B 反转 M5 补两个强撞近邻 + C 保守值全扫（本轮最高性价比，抓到一条推翻当轮新写句的缺陷）+ E 发布层门禁 + F 版面资金。** ① **新纪律（本轮起生效，写进本条）：任何跨节总结句必须从 `results.json` + 债务台账正向构造，不许凭对已审章节的记忆概括；写完按『新写段落』审，不按『修订确认』审。** 依据：W2-9 的三处 MAJOR 与本轮 C 抓到的基座漂移缺陷全部由记忆式概括产生，而 §1/§7 几乎全由这类句子组成。 ② **C 扫描抓到的最重一条（BLOCKER 级，且推翻我本轮 A1/A5 刚写的句子）**：未编辑基座漂移逐 checkpoint 为 1.5B −.010 / **7B +.080** / **8B +.020** / **14B +.010** / 32B −.021 / **70B +.025** ——**六个里四个为正**，含并列 headline 的 Llama-70B；而**只有 Qwen-32B 有配对区间**（n=199，−.0201[−.0804,.0402]）。§1/§7 把基座对照挂在『两个谱系各自』的语境下作无限定断言 → 已收窄为『在有区间的那个 checkpoint 上』，六尺度全表入 supp（新增 manifest 行 S5b，明写其余五个只有点估无区间、不得读成基座普遍不漂移）。 ③ **C 的第二条已进正文**：MEMIT-14B 的 C−N 四个端点里，正文原只报了 RRs=.000（恰好零宽区间、最有利于『竞争者是地板』），已补报其 ES=+.015[.000,.035]（『在 edit success 上它不是地板』）。**第三条**：§5.1 的 exhaustiveness 句原写『Every contrast we computed appears…』，但 D−N 的 CLR 对照（+.041[−.010,.098] p=.163）既未入表也未入正文 → 收窄为 **outcome** contrast（CLR 本文已声明是操作检查非结果）。其余六条判归 supplement，逐条落 `delivery/t2_supplement_queue.md` §F，含 **scope 消融只报了分离最大的 B0 档**（B3 档 think .639 vs all .670 仅差 +.031、CLR 两者完全相同）与 **.595 是三次同条件跑里最低的 B0 ES**（另两次为 .625）。 ④ **A3 的做法与计划不同（有意偏离）**：核实发现 X2 的 `T_minus_C.RRs` 与 `T_minus_N.RRs` **逐字相同**（都是 −.0268[−.0804,.0268] p=.3998），因为 `C_minus_N.RRs` 恰为 .000[.000,.000] p=1.00。把同一组数字换个标签再印一遍会被读成排版错误 → 改为**说出它们为何重合**（一句、零新数字、信息量更大）。 ⑤ **A 其余五处**：§1 C1 的推论改为报端点 + canned-thought 支自带结论（不许读者用蕴含补）；§1 铰链的无限定全称改为 `standard editing protocols do not measure that distance for one and the same edit`；§7 同源缩水句同修；Ethics 的『reversion tracks…rather than its veracity』改为测量陈述（CounterFact 里旧值与真值完全共线，无任何运行能分离）；0/41 改为界而非排除。 ⑥ **B 反转 M5**：`sun2024disco`(2406.02882) 与 `xie2025superficial`(2505.12636) **逐字核对 arXiv 页**（标题/全作者/年份）后入库并各带一从句区分点。 ⑦ **F 版面资金**：§5 行内数字搬进 Table 2——散文侧 191→172 个绑定；**并把 Table 2 下半面板由 18 行压成 6 行**（每对照一行、三端点各一列），一次省 12 行。checker 新增 `\multicolumn{N}{spec}` 结构参数屏蔽（列数不是被断言的数字），并把 `multicolumn` 加入命令白名单。 ⑧ **E 发布层门禁**：`RELEASE_SUFFIXES` 加 `.sh/.lock`、显式 `RELEASE_ROOT_FILES` 白名单、补 `WHYAAAI`/`wf_[0-9a-f]{6,}`/workflow-id 模式；新增 `src/package_release.py` 把 release tier 做成**硬拒绝**（先有门再有打包逻辑，7/31 赶时间也绕不过）；`--submission-ready` 让缺文件从『跳过』变『失败』。 ⑨ **本轮误操作与恢复（记档）**：我的批量替换助手一度按行尾截断，**误删了 §5.4 的后半段**（instrument-quality 句 + 多重性声明）。由 checker 的 required-string 门当场发现，已 `git show HEAD` 逐字恢复整行（13 个绑定完好）。教训：对含多句的长行做区间替换必须锚定句尾而非行尾。 ⑩ 门禁：checker PASS（§3=111 / §4=64 / §5=**172**）、pytest **144 passed**、**8 页＝正文 7 + p8 纯参考文献**、0 overfull / 0 undefined / 0 Type-3、匿名提交层 30/30 CLEAN。
- **v2.00 变更 (2026-07-26)**: **W2-9 第一至三组完成。§1/§2/§6/§7/Ethics 首次对抗复审抓到的三个 BLOCKER 全部修掉。** ① **B1(最严重，已逐行复核属实)**：`main.tex:41` 原写「unedited base、canned thought、**temperature sampling** 各自复现不出该模式，故非背景漂移亦非解码产物」——而 §3.3 的事实是 gap 在采样下**持续**（`.117[.067,.169]`）。这不只是跨节矛盾：**该句前提与自身结论相反**（若采样复现不出，恰证明 gap 是 greedy 产物）。改为「两个对照复现不出，而它在温度采样下存活」。 ② **B2**：§7 把 `edit-specific` 与 `content-dependent` 当既成属性，但 §3.2 明写「不作正式对比」、§4.4 明写 content-independent buffer 账仍活，冻结摘要两者都未断言。改为「未被未编辑基座或固定 canned thought 复现，且在两谱系各自最大 checkpoint 上出现」。 ③ **B3**：Ethics 断言「the chain re-derives what the base encoded」，正是 §4/§6 形式撤回的机制。改为观察性上限（reversion 追踪基座已编码之物而非其真伪 + 未检出匹配漂移）；`shows no matching drift` → `no matching drift was detected`。 ④ **M1**：§1 C3 把 strict 端点不分离说成迁移的普遍属性，而 §5.5 明写第二尺度上它确实分离；已限定为「主电池内不分离、第二尺度上分离」。 ⑤ **M2/M4**：Ethics 的 `0 of 41` 去掉普遍可审计性升格（改为 outcome-conditioned 表述 + 双重不宣称）；§1 铰链句名词化 `certification` 改动词，checker 补 `certificat(ion|ions)` 模式（放行动词）。 ⑥ **F3(新发现，属准确性缺陷)**：Reproducibility 段原只列两类加速器，实为**三类**——H100(80GB) 也产出过被报告的数字（genbench A1 `plan.md:215`、base_probe 六尺度 `plan.md:300`）。已按 M03 补 `environment.hopper_class_secondary=80` 并入正文；同时修 F1 指代（原 “there” 的最近先行词是 Ada 那块，而 NaN 在 Hopper 侧）。 ⑦ **第二组引文**：M3 把 2505.18690 恢复为 PREMISE（其在一个 R1-distill checkpoint 上报告的「推理反思旧知识并推翻编辑」此前被压成一句 performs poorly，事实上被错归给多模态的 CRANE）；M6 恢复 CRANE 的区分点（冲突证据是视觉的、无 budget 轴）。 ⑧ **第三组**：顶层 `LICENSE`(MIT，双盲用 “The Authors”) 与 `data/LICENSES.md` **今天落库**，3.4/4.5 的 yes 现由**今天已存在的工件**授权而非空头承诺；**4.8 由 yes 降 partial**——4.8 明文要求 OS 与库名版本，正文零余量，按你定的优先级（矛盾修订 > 引文 > checklist）选择降级而非硬塞。 ⑨ **F6(匿名，提前做)**：`results.json` 含 3 处 `/Users/…/.codex/attachments/…` 绝对路径（旁边已有 sha256，是面包屑不是数据）已删；`scrub_artifacts.py` 补通用模式（`/Users/…`、`/home/…`、`plots*.py`、`.codex/`）。**并把扫描面拆成两层**——`submission`（PDF+图，挡 checker）与 `release`（含 src/experiments/data，挡 7/31 打包）。理由：放宽后 `experiments/*.yaml` 注释里的 `plan.md`/`prereg-` 会把稿件门打挂，那是打包问题不是稿件问题，一道会误报的门会被人关掉。提交层 **CLEAN(30)**；发布层今日仍脏＝T3 `anonymize.py` 的活。 ⑩ **版面**：本轮共 20 处压缩，**其中 3 处被守卫拦下并回滚**（`of its own`、`all six fixed-checkpoint cells`、X1 语序）。终态 **8 页＝正文 7 + p8 纯参考文献，References 起 p8 第一行**，0 overfull / 0 undefined / 0 Type-3。 ⑪ 门禁：checker PASS、pytest **140 passed**（+4）、四步编译干净、匿名（提交层）30/30 CLEAN。 ⑫ **有意延后并记档**：M5（补 DISCO 与 Superficial Editing 两个近邻）——零余量 + 两天窗口；且非擦除断言已在 B3/B2 修订中删除、与 Superficial Editing 的撞面已缩小，我们的定位是 mechanistic probe 而非方法。F4（env.lock 措辞再精确化）、F5/F10/F11/F15 与 4.7/4.13 补句留 T3。
- **v1.99 变更 (2026-07-26)**: **W2-8 T0/T1/T2 完成；四项裁决落库。Task A1-4(换 OpenReview 表单) 仍属作者账户操作、写作环不代执行。** ① **裁决一·匿名补丁(T0，原为上传阻塞项)**：确认双盲已破且**比计划描述的更广**——三张图 PDF 的 `/Creator (why-aaai27/src/plots.py)` 只是入口，`main.pdf` 里该串**藏在 Flate 压缩流内**（`strings`/`grep`/exiftool 全查不到），另有 **15 个 PNG/SVG 与 `_nature-skill` 变体**同样带毒、且都会随代码释出。处置：用等长且**不含填充空格**的 `anonymized-generator.py`(恰 23 字符，与原串等长，xref 不动) 就地改写；PNG 另重算 chunk CRC；`plots.py`/`plots_nature_skill.py` 三处源头改掉并加注释防回归。工具落库为 `src/scrub_artifacts.py`（`--audit`/`--scrub`，解流后再匹配），并**接成 checker 的一道门**。终态：**30 个工件 raw+inflated 全 CLEAN**。 ② **裁决二·4.2 由 yes 降 partial**：结论采纳，但**计划给的三条实证依据全错**，已按证据改写——(a) 真扫过的是**两个** checkpoint 不是一个：Qwen-7B(ROME 扫 {5,7,10}，n=40，B0；实测 ES .55/.475/.40，且只有 layer5 的 Loc 达 .85) **与 Llama-8B**(layer{5,6,7}×clamp 四格 n=60 → 定 layer6/clamp2，wf `ww9ij8hpf`)；(b) `pilot.yaml:42` 的 `[4,5,6,7,8]` 是 **MEMIT 原生多层带**、不是 ROME 扫描候选(ROME 在 :39 是 `[5]`)；(c) 14B 不是「同理」而是 **layer 9**(48×0.18≈9，条件扫 {7,9,12})，另有 1.5B L5、70B L14 同为未触发。正文只补了 penalty 的 provenance 短句（『该值在任何受压臂运行前由冻结协议固定』），层策略全表归 supp S11。 ③ **裁决三·4.8 写 Reproducibility 段**：置于 **§6 末**而非 `\section*{Ethical Statement}` 之前——按计划字面放会落进 §7 结论末尾、**顶掉 M15 的末句锚**（checker 已实测报错）。段内 141/24/40 三个数字按 M03 绑到新建的 `rq3.environment` 块（重述 RUNBOOK 硬件记录与 env.lock，零新计算）；平台名/集群路径零出现。**遗留：判官模型版本串在仓库任何处均无记录**，不编造，转 Task D 从运行日志找回、找不回则在 provenance_manifest 明写缺失。 ④ **裁决四·Fig.2/Fig.3 归 supplement**：`supplement.tex` 骨架已建，七处正文承诺各有具名落点。**Fig.3 加设硬门**：缺 strict-displacement 面板期间不得入册（两面板版会藏掉本文特意以主端点显著度报出的端点）；Fig.2 的 panel A 印了 `11.51` 与 `decoder 58` 两个正文零出现的数字（已核实 main.tex 中均为 0 次），入册前从源文件删除。 ⑤ **A1-1/A1-2**：结论末句 `What the failure is not is a clean erasure` 删除（禁令实际在 `WRITING_PLAN.md:80` 与 `check_manuscript.py:495`，**不在 §3**；且 WRITING_PLAN:23 只允许该想法处于假说位阶，而该句是平铺事实、更与本文自己在 `main.tex:136` 的『近乎同义反复、下游不赋定量权重』直接矛盾）。新末句 `That failure nonetheless admits a chain-local causal control point.` 保住 M15 锚。checker 补四条词形/否认式模式；`intact` 一条特意收窄为 `\bedit\w*\b[^.]{0,40}\bintact\b`，因 §2 引述前人的 “capability stays intact” 是合法用法。 ⑥ **A1-3 完成**：D1–D8/R1 **九条全部 DISCHARGED**，且不是贴位置了事——每条的 `required_content` 逐元素在冻结正文中**验证逐字存在**后才落 `discharged_at`；`g5.adoption_gate: UNBLOCKED`、`manuscript_debts: CLOSED`。 ⑦ **A2-4/A2-5**：`tab:routes` 假承诺改为『报告路由计数，并在 caption 给聚合投票分歧构成』（该表确无 per-instance 票）；七处 supplement 承诺全部落表——补 S1b(X1 replay-gate 全表)、S2b(判官缺失模式)，且**把 `main.tex:72` 从承诺一个 sensitivity 分析改窄为报告缺失模式**（兑现分析＝新数字，违反冻结条款）。 ⑧ **版面**：本轮净增 4.8 段(~60 词)+2 处补句，共做 **31 处压缩**；**其中 8 处被 checker 的 required-string / 记忆锚 / X1 披露顺序 / 语义角色互换四类守卫拦下并全部回滚**（`uninterrupted`、`do not identify a single mechanism`、D1 的 `all six fixed-checkpoint cells`、M15 lineage 句、X1 的 `while` 语序等）——**守卫每次都是对的**。终态 **8 页 = 正文 7 + p8 纯参考文献，References 起 p8 第一行**（判据⑥），0 overfull / 0 undefined / 0 Type-3。 ⑨ 门禁：checker PASS（§3=111 / §4=64 / §5=191）、pytest **136 passed**（+9）、四步编译干净、匿名审计 30/30 CLEAN。 ⑩ **未做**：A1-4 换表单（作者账户，7/28 UTC-12 截止）、4.7 seed 句与 4.13 两 facts（按 A2-6 优先级挤不下，对应答案未上调、由 supp S11 授权）、T3 发布链（7/29–31，见 `delivery/t2_supplement_queue.md`）。
- **v1.98 变更 (2026-07-26)**: **W2-7 T1（7/28 提交件）Task B/C 完成；Task A 待核销环，OpenReview 表单我方不代改。** ① **Task C ①**：W-B 段三个方向性端点（S−Pshuf CLR −.078[−.148,−.008]、S−N ES +.092[+.007,+.176]、B2 LocAcc S−Pshuf −.064[−.119,−.008]）**全部排零**，故用一句 `Each directional endpoint above has an interval excluding zero.` 覆盖全段而非逐句加限定——只限定其一会让读者反推另两个不排零。**这同时了结 W-B/C2 悬案：CI 数值仍沉 supplement，排零的定性结论回正文。** ② **Task C ②**：`genbench_b26_tost.ci_level=0.9` 按 M03 落库（出处双记：本块 `_status` 原文已写「TOST 对 ±0.02 等价界(90% CI)」+ 字段键名字面 `ci90`；零计算零新跑），正文 `ninety-percent` 改 `90\%` 并绑指针。 ③ **Task C ③**：真实风险不是缺文件头而是 **main.tex 并不 `\input` 该片段**（`\input` 不在 checker 命令面内、路由表是内联副本），已写死在 `table_rq2.tex`/`generate_table_rq2.py` 头部；并**订正 supp_manifest S4 行**——该行原文写于 50-池时代、仍指示「正文保留 Bridge-dominant 50-池 68%」，与冻结正文及 checker 禁语表直接冲突。 ④ **Task B（M19）**：`ReproducibilityChecklist.tex` 31 项全填（yes 21 / partial 1 / no 1 / NA 8），独立编译 2 页 0 error。**理由不写进 .tex**（模板明令只许替换答案文本、答案可能被自动抽取），改落 `paperwriting/delivery/checklist_provenance.md`，逐条给授权节+行号；行号由 `src/gen_checklist_provenance.py` 从活文件实算、锚点唯一性断言，改写正文会直接报错而不是让台账烂掉。 ⑤ **填 checklist 反查出两个正文缺陷（均已修）**：(a) **超参命名错误**——§5.1 把抑制强度叫 “Clamp strength”，但 `clamp`(`clamp_norm_factor`) 在同一份 yaml 里是 ROME 编辑器的另一旋钮（值 2/4），我们的抑制强度在代码里叫 `penalty`(`edit_loop.py:330`)、在 results.json 里叫 `alpha_sweep.penalty`（0/2/4/8/12/16）；照原文复现会调错参数，已统一改为 “Penalty strength”。(b) **数据集零引用**——§6 用了 GSM8K 与 MATH-500 却无引用、refs.bib 无条目，而 checklist 3.5 只有 yes/no 无 partial 可躲，原状只能答 no；已补 Cobbe et al. 2021 / Hendrycks et al. 2021 （arXiv 页逐条核实标题·作者·年份，非凭记忆），MATH-500 的 500 项子集来源不在正文过度归因、归 provenance manifest。 ⑥ **4.1/4.7/4.12 的 yes 由 supplement 授权 → 全部登记为 Task D 硬承诺**；判定规则写死：只有支撑工件今天已存在于仓库、且 D 已列为硬交付时才答 yes，跑不出来必须回头降级（M17）。**唯一 partial=4.6**（源码注释锚点指向内部 plan/prereg 而非论文小节，可补未补，不冒充 yes）。**4.2 明令不得追认 penalty=8 的选择判据**——它由冻结协议预先固定、六点扫描是事后稳健性检查；注意 ES 在 penalty=12 高于 8，正文『五档间 ES/RR 无序』已覆盖。 ⑦ **版面**：接入 §3.1 数据集理由句 + 两条引用后正文一度溢到 p8（10 行）。三轮无损压缩共 26 处；**其中 3 处被 checker 的 required-string 门拦下并已回滚**——`uninterrupted` 是承重范围限定、`did not yield detectable confirmatory RR repair` 是复审定过的负结果措辞，压缩会削弱科学表述，**门是对的**。最终 **8 页 = 内容 7 页 + p8 纯参考文献**（References 现从 p7 起、比 W2-6 更紧），0 overfull / 0 undefined / 0 Type-3。 ⑧ **Task A 未动**：等核销环逐条判定。**OpenReview 表单属对方账户的外部改动，我方只交付 v8.1 逐字串 + 冻结面校验 + byte-diff 脚本，不代登录代改。** ⑨ 门禁：checker PASS（§3=111 / §4=64 / §5=191）、pytest **127 passed**（+6）、四步编译干净、scrub-grep（平台名/集群路径/作者身份）零命中。 ⑩ **Task D(T2, 7/29–31) 已排定**：`paperwriting/delivery/t2_supplement_queue.md` = 7/31 交付的唯一执行清单（A 正文六处 supplement 承诺 / B checklist 的 supplement-授权 yes 及其降级答案 / C prereg gate 全表+anonymize.py+LICENSES+provenance_manifest / D P14 外部依赖及取不回时的披露口径 / E dry-run 打包 + scrub-grep）。
- **v1.97 变更 (2026-07-25)**: **W2-6 接图与版面收口：canonical 图/生成器合入 main，Fig.1 入正文，n=41 路由表上正文；正文实测 7 页 + 1 纯参考文献页。** ① **BLOCKER 已解（我方复验）**：主仓 `paperwriting/fig1_capability.pdf` 是 7/8 的 30KB 作废版（md5 `727e0dd3…`），canonical 是 worktree `festive-neumann-2e8860` 的 7/24、54679B（md5 `5e19b64e…`）；主仓 `src/plots.py` 亦为 v1.66 旧生成器。已**按文件合并**（不整分支合并，避免与 W2-5 正文改动冲突）canonical `plots.py`/`plots_nature_skill.py`/`generate_table_rq2.py`/两个 audit 脚本 + `fig{1,2,3}*.{pdf,png,svg}`，同 commit 删除主仓 `fig2_logitlens.*`。合并后用主仓 results.json 重跑 `plots.py --only fig1`：**fail-closed 断言全过（PASS）**，证明取数一致；但重渲不是逐字节可复现（本机字体解析不同，日志有 findfont 警告），故**保留经审计的 canonical PDF**、不用本机重渲版。② **Fig.1 接入**：`\includegraphics` 与 `\Delta` 入 checker 白名单，`\includegraphics[...]` 的宽度系数按 `\parbox` 同法屏蔽（只屏蔽方括号选项，文件名里的数字仍会被扫）；写 FULL caption（A 面板=六个 fixed checkpoint 的配对 B0→B3 变化、正值=推理后更低、类别轴无插值、实心=95% 配对区间排零；B 面板=三个控制 + 未编辑基座，基座行为 ΔP(o_old)、事件定义与分母不同只并列；**并按审计新抓的 F2 加『配对≠边际差』免责**），caption 只新增一个 `95` 的 RJ（绑 `/capability/ci_level`），不复述 .106/.107；正文首次出现 .106/.107 处补 `Figure~\ref{fig:gap}`（此前 `\ref{fig:gap}` 在正文出现 **0 次**）。③ **Fig.2/Fig.3 归 supplement**：`supp_manifest.md` 加 S7b/S3c 两行（文件名 + 承载物 + 正文位置，并记 Fig.3 当前缺 strict RRs 面板、入正文前须补），正文 §5.5 末一句指路。④ **n=41 路由表上正文**：`tab:routes` 占位换成真表（Bridge 27/Recall 11/RO 3/Assoc 0 + 份额，caption 带 n=41、33 facts、35/6/0、111/123）。**未用 `\input`**（单源规则），而是按 Table 1/2 的现有命令面内联，只多批准 4 个 `pct/*` 指针；旧 50-池文件改名 `table_rq2_superseded.tex`；checker 的 n=50 / 68% / κ=0.790 三条 denylist 经确认已在位。⑤ **P14 可写部分**：Table 2 caption 加『配对回退对比在两臂门集的交集上计算，故其分母不是任一臂的 n』——per-contrast 门 n 仍等服务器工件。⑥ **版面**：接图 + 路由表后正文一度溢到 p8。宽度扫描证明 `width=` 在本布局下是**跳变而非连续**的（0.92/0.88/0.84 完全同结果），故先砍词后调宽：§5/§6/§1/Ethics 累计再砍约 130 词（Ethics 由 225→193 词），最终 **width=0.68**。**实测：8 页 = 正文 7 页 + p8 纯参考文献**（References 标题落在 p7 尾部，p8 只有条目），0 overfull / 0 undefined / 0 Type-3。⑦ **width=0.68 是临时版面手段，不是终值**：图审计已判定 Fig.1 的嵌套 mathtext 下标最小字形仅 4.41px（全宽下即 4.41pt，**与缩放无关**），替换轮必须把最小字形提到 ≥7.5px 并改字面文本；字体修好后**宽度应调回并重测页数**。⑧ 门禁：checker PASS（§3=111、§4=64、§5=191）、pytest **121 passed**、四步编译干净。
- **v1.96 变更 (2026-07-25)**: **§5 复审补丁 P15–P21 落地；BLOCKER(P14) 经本地复核降级为『等服务器工件』，不改任何数字。** ① **P14 我方独立复核结论（与审计员部分不同）**：`results/esup_crossarm.json`(2026-07-01, 四臂) 与 results.json 的差异**不止 3 处而是 4 处**——T−P ES 的 mean(.1212→.122)、CI 上界(.1919→.193)、p(.0012→.002) 三者**全部与 3dp 舍入不符**，外加 P 臂 n(200→199)、P 边际 ES(.51→.507=101/199)、P−N ES p(.704→.709)、P−N RR CI(−.0561→−.057)。**但决定性模式是：所有不符项都只涉及 P 臂**；不涉及 P 的 T−N、D−N、P−N 的 RRs 则是磁盘值的干净 3dp 舍入。这与『C 臂加入后五臂重跑、P 有效行由 200 掉到 199』完全自洽，而与『C 行由 P 行转录』不自洽（转录不会同时改动 P 自身的 n 与边际）。审计员担心的 C−N 与旧 P−N 在 RR/RRs 上逐位相同，另有良性解释：两者都是近惰性对照、门后差异向量极稀疏，且 bootstrap 固定 seed 42 → 同输入必得同输出。**唯一未解者**是 cross_arm 的 T−C ES 与旧 T−P ES 在 4dp 上完全相同而 p 不同。**结论：正文按铁律以 results.json 为准，一字不改；服务器五臂工件取回后再定 P14（per-contrast 门 n 与 .193 的真值）。** ② **P15**（审计员自认的计划错误）：§5.2 不再拿 placebo null 当正面前提，改为区间宽度论证（两对比之差小于任一区间宽度），保住『不是对比选择的产物』。③ **P16**：链内 dissociation 改由 competitor 单独承重（−.071[−.121,−.020] 排零），placebo 的 −.051[−.102,.000] p=.054 明写 reaches zero and is not established。④ **P17**：`declines at every step` 是 ordered-trend 同义复活且跨了 run/n 边界，改为『每个受压设置都低于零 clamp；在同一次较小规模运行的五个受压设置间递减』，并加 target 断言。⑤ **P18**：补上本可用而未用的同模型同编辑器同抑制器 B0 identity 审计（X3 的 600 行 0 差异），同时保留『本电池无自己的审计』。⑥ **P19**：§5.4 加仪器精度交底（permissive .48 / strict .92），这是 strict-null 攻击的正面答案。⑦ **P20**：按 M03 程序把 X2 fresh-N 的 es_drop 由 `_baseline_discrepancy` 字符串落成结构化字段 `x2_memit14b_repair_replication.fresh_n_es_drop`（`_derivation` 注明只是重述、无新计算），正文改写为 `+.060[−.020,.140]` 且不再把 null 当无效应。⑧ **P21**：M14 脚注补 RR 对的平行否等式（不印派生差值）、多重比较句收窄为『每个我们计算过的对比』、118 标注借自 M1 再分析且不发布 per-arm 事件数、两处 −.051 加四词括注、X2 changed-row 补分母 200、X3 补『未筛行未做子集再分析』、checker 记档禁语扫描只作用于剥注释后的散文。⑨ **页面**：P18–P21 净加约 180 词，§5 由 1671→1808 词；随后按审计员点名的框架句压缩 −47 词并复原三条被误删的天花板短语。实测 **8 页 = 7 正文页 + 1 纯参考文献页**（References 起 p7 的 75%，p8 只有参考文献），符合『正文 7 页 + 至多 2 页仅参考文献』。**p7 正文余量仅 25%，而真 Fig.1 按审计员实测需约 26%——换真图前必须再压 §5 或改单栏图。** ⑩ 门禁：checker PASS（§3=110、§4=49、§5=191）、pytest **119 passed**、四步编译 0 overfull / 0 Type-3 / 0 undefined。
- **v1.95 变更 (2026-07-25)**: **W2-4 全文成篇：§1/§2/§6/§7/Ethics 落地 + 页数实测收口，正文 7 页、References 起 p7、0 overfull、0 Type-3。** ① **编译门首次真跑**（本机已装 BasicTeX `/usr/local/texlive/2026basic` + tectonic；`pdflatex`/`bibtex` 在 `/Library/TeX/texbin`，**不在默认 PATH**，命令与三条验收查法已落 `RUNBOOK.md §11`）。基线（仅 §3–§5）=6 页；成篇后=**7 页**，References 标题落在 p7 的 62% 处，正文不溢出第 8 页，`grep -c Overfull`=0，`pdffonts` 全 Type 1，无 undefined ref/citation。② **任务 A 页数执行**：删 `fig:diagnosis` 整块（**实测它与 `tab:routes` 都是从未被 `\ref` 引用的孤儿浮动体**，故删除零悬空引用；同时给 §4.2 补了对 `tab:routes` 的真引用）；§4 −109 词（W-B 三端点脚注下沉 supp、4.1 caveat 五句压两句、route 一致性脚注并入 `tab:routes`，κ 因 checker 的 kappa 身份门必须留在正文）、§3 −104 词（B15 与 percase 两脚注下沉，方向句 + 指针留正文）、§5 −33 词（仅压 5.5 过渡）。**合计 −246 词，未达计划的 −450**：实测证明不必——7 页已达标，故不再为凑数删承重内容（判据是页数不是词数）。③ **§1（约 490 词，零数字）**：CONTEXT 首拍 + ~30% 铰链 + hook "Does thinking undo editing?" + 三条贡献（C2 首词 = 加粗 verbatim **A chain-local causal control point.**）+ 末句落回锚短语。④ **§2（约 400 词）**：M10 三角色分立且**逐篇 WebFetch 验真后才落笔**——`2503.05212`=SCR 方法论文（He/Song/Sun）、`2505.18690`=realistic-autoregressive benchmark（He/Song/Wang/Sun，摘要逐字含 "under a realistic autoregressive inference setting rather than teacher-forced decoding" 与 "reasoning-oriented LLMs"）、`2401.17585`=ReCoE（Hua et al.）；新引 `2510.17941` belief-depth、`2606.09033` CRANE（**多模态推理 MLLM 上 teacher-forcing 近满分 vs grounded success 崩塌——现认定为最近邻，已给正面边界句**）、`2605.10146` EditRisk-Bench（原 minor 清单只给名字，本轮检索确认 ID）、`2507.14417` Inverse-Scaling、`2405.11613` DeCK、`2604.19089` LightEdit（实际标题 "Towards Scalable Lifelong Knowledge Editing with Selective Knowledge Suppression"，解码期压原知识=修复线最近邻）。边界句只枚举四条安全属性，无 "first to"。⑤ **§6（约 300 词）**：六类边界各一句 + 从 §5 移入的 Loc（固定称 target-value non-leakage rate，明写拒答/胡言计非泄漏）与 genbench（全量 `1319`/`500`、点估 `.000`/`-.010` 落在 `0.02` 门内、**ninety-percent 区间 `[-.022,.022]`/`[-.061,.041]` 超门故不称等价**）+ route-census 让步句（判官同族、无人工子样本）。⑥ **§7（约 85 词）+ Ethics（约 210 词）**：§7 末句含 verbatim 锚（全文 recency 位）；Ethics 复用必4 三件套并按 M18 重锚 n=41 池（`0` of `41`，majority-label 口径），edited-query gating 回指 §5.1 不首次引入，三禁令遵守（不硬化 CLR0 地板为监测主张、F1 仍 null、未引 Korbak/Baker）；预写件的 `chain-only repair`/`chain-only suppressor` 未被搬入（撞禁语）。⑦ **checker**：审计面扩到全部 8 节——§3/§4/§5/§6/Ethics 带 ledger，§1/§2/§7 为 `requires_ledger=False` 的快照节（空 ledger ⇒ 任何数字都触发逐行 occurrence 失配 = 更强的零数字保证）；section spec 支持显式 `start_marker`/`end_marker`（Ethics 是 `\section*`）；新增叙事锚门（C2 加粗首词、§1 hook 与末句锚、§2 四属性边界句 + 三引用角色在场、§7 末句锚、Ethics 四条必备串）；`refs.bib` SHA 重钉；`\paragraph`/`\url` 入白名单；`genbench.gate` 串按 SHA 钉住 token；denylist 补 `1/50`。⑧ **门禁**：`python3 src/check_manuscript.py` PASS（§3=110、§4=49、§5=185 RJ occurrences）、pytest **117 passed**（`src/test_check_manuscript.py`）、四步编译干净。⑨ **待办**：`table_rq2.tex` 与 `tab:routes` 仍是占位（真表须含 35/6/0 与 111/123 的 route 一致性行，本轮已从正文移出）；Fig.1 占位仍小于真图，**换真图后须重测页数**（当前 7 页无余量）；ReproducibilityChecklist 未填。
- **v1.95 变更 (2026-07-25)**: **W2-4 全文成篇：§1/§2/§6/§7/Ethics 落地 + 页数实测收口，正文 7 页、References 起 p7、0 overfull、0 Type-3。** ① **编译门首次真跑**（本机已装 BasicTeX `/usr/local/texlive/2026basic` + tectonic；`pdflatex`/`bibtex` 在 `/Library/TeX/texbin`，**不在默认 PATH**，命令与三条验收查法已落 `RUNBOOK.md §11`）。基线（仅 §3–§5）=6 页；成篇后=**7 页**，References 标题落在 p7 的 62% 处，正文不溢出第 8 页，`grep -c Overfull`=0，`pdffonts` 全 Type 1，无 undefined ref/citation。② **任务 A 页数执行**：删 `fig:diagnosis` 整块（**实测它与 `tab:routes` 都是从未被 `\ref` 引用的孤儿浮动体**，故删除零悬空引用；同时给 §4.2 补了对 `tab:routes` 的真引用）；§4 −109 词（W-B 三端点脚注下沉 supp、4.1 caveat 五句压两句、route 一致性脚注并入 `tab:routes`，κ 因 checker 的 kappa 身份门必须留在正文）、§3 −104 词（B15 与 percase 两脚注下沉，方向句 + 指针留正文）、§5 −33 词（仅压 5.5 过渡）。**合计 −246 词，未达计划的 −450**：实测证明不必——7 页已达标，故不再为凑数删承重内容（判据是页数不是词数）。③ **§1（约 490 词，零数字）**：CONTEXT 首拍 + ~30% 铰链 + hook "Does thinking undo editing?" + 三条贡献（C2 首词 = 加粗 verbatim **A chain-local causal control point.**）+ 末句落回锚短语。④ **§2（约 400 词）**：M10 三角色分立且**逐篇 WebFetch 验真后才落笔**——`2503.05212`=SCR 方法论文（He/Song/Sun）、`2505.18690`=realistic-autoregressive benchmark（He/Song/Wang/Sun，摘要逐字含 "under a realistic autoregressive inference setting rather than teacher-forced decoding" 与 "reasoning-oriented LLMs"）、`2401.17585`=ReCoE（Hua et al.）；新引 `2510.17941` belief-depth、`2606.09033` CRANE（**多模态推理 MLLM 上 teacher-forcing 近满分 vs grounded success 崩塌——现认定为最近邻，已给正面边界句**）、`2605.10146` EditRisk-Bench（原 minor 清单只给名字，本轮检索确认 ID）、`2507.14417` Inverse-Scaling、`2405.11613` DeCK、`2604.19089` LightEdit（实际标题 "Towards Scalable Lifelong Knowledge Editing with Selective Knowledge Suppression"，解码期压原知识=修复线最近邻）。边界句只枚举四条安全属性，无 "first to"。⑤ **§6（约 300 词）**：六类边界各一句 + 从 §5 移入的 Loc（固定称 target-value non-leakage rate，明写拒答/胡言计非泄漏）与 genbench（全量 `1319`/`500`、点估 `.000`/`-.010` 落在 `0.02` 门内、**ninety-percent 区间 `[-.022,.022]`/`[-.061,.041]` 超门故不称等价**）+ route-census 让步句（判官同族、无人工子样本）。⑥ **§7（约 85 词）+ Ethics（约 210 词）**：§7 末句含 verbatim 锚（全文 recency 位）；Ethics 复用必4 三件套并按 M18 重锚 n=41 池（`0` of `41`，majority-label 口径），edited-query gating 回指 §5.1 不首次引入，三禁令遵守（不硬化 CLR0 地板为监测主张、F1 仍 null、未引 Korbak/Baker）；预写件的 `chain-only repair`/`chain-only suppressor` 未被搬入（撞禁语）。⑦ **checker**：审计面扩到全部 8 节——§3/§4/§5/§6/Ethics 带 ledger，§1/§2/§7 为 `requires_ledger=False` 的快照节（空 ledger ⇒ 任何数字都触发逐行 occurrence 失配 = 更强的零数字保证）；section spec 支持显式 `start_marker`/`end_marker`（Ethics 是 `\section*`）；新增叙事锚门（C2 加粗首词、§1 hook 与末句锚、§2 四属性边界句 + 三引用角色在场、§7 末句锚、Ethics 四条必备串）；`refs.bib` SHA 重钉；`\paragraph`/`\url` 入白名单；`genbench.gate` 串按 SHA 钉住 token；denylist 补 `1/50`。⑧ **门禁**：`python3 src/check_manuscript.py` PASS（§3=110、§4=49、§5=185 RJ occurrences）、pytest **117 passed**（`src/test_check_manuscript.py`）、四步编译干净。⑨ **待办**：`table_rq2.tex` 与 `tab:routes` 仍是占位（真表须含 35/6/0 与 111/123 的 route 一致性行，本轮已从正文移出）；Fig.1 占位仍小于真图，**换真图后须重测页数**（当前 7 页无余量）；ReproducibilityChecklist 未填。
- **v1.94 变更 (2026-07-25)**: **W2-3 §5 A Chain-Local Causal Control Point 成文 + 前置补丁 P8–P13；全文最重一节与摘要债务同时落地。** ① **P8 撤回 W2-2 的 P1 数字**：深审认定 §4.4 引入的 `+.138` 同源三伤（同段并列 .631/.595 边际与配对值=M14 陷阱；§4 假说位阶越界写 §5 干预位阶；只暴露有利 ES 端点而 strict T−N `p=.073` 隐身=白送 Kimi 拒稿句）。现改为**无数字前向指针 + 定性端点层级**。**第一性修正（本轮唯一驳回项）**：审阅给的措辞 "raises edit success … on the loose endpoint" 把 ES 与 loose/strict 口径混为一谈——ES 无 loose/strict 变体，该二分只属 RR(permissive)/RRs(strict)；已改写为 "improves edit success and lowers permissive reversion … while the strict displacement endpoint does not separate from that baseline"，三事实各归其位。② **P9**：正文 §4.1 按名声明的 BLOCKED 工件在 `prewrite/supp_manifest.md` S7 行并无对应记载（正文替一份尚未做的 supp 背书）→ 补 manifest 行（路径 + per-item case_id/first-token logits + 状态 + 后果 + 禁猜 case ID），并加 WRITING_PLAN §8 第⑪条判据「§3–§7 任何断言 supplement 含有某物的句子须有对应 manifest 行」。③ **P10**：v1.93 的跨块不变量用显示舍入值做精确相等，一次合法精度升级（`_n_note` 记 CLR `.5455=108/198`）即误 FAIL → 改为两侧先量化到 3dp 再比，且 `sup_battery.n` 取 max 前跳过 `_` 前缀键。**拒绝**加 `_same_run_as` 字段：那是关于"同一次运行"的新科学断言而非既有标量重述，按 §5 规则须先仲裁。④ **P11**：论文已落本地——`papers/ref_ThinkingToRecall_2603.09906.pdf`（v1 2026-03-10，9 页），`paperwriting/related_work.md` 新增**引文取证台账**（p.1 摘要与引言两处 "a semantic bridge" 逐字 + "independent of their semantic content" 逐字 + 下载日期/大小），`setup_workspace.sh` 加 `dl` 行使其可幂等重下（`papers/` 全目录 gitignore，故可复核路径=台账+dl 行，非 PDF 本身）；顺手删掉该文件里重复两次的 `dl 2602.17692`。⑤ **P12**：`WRITING_PLAN:56` 仍指示 W-B 用 checker 会拒的 `prospectively specified` → 改 `pre-specified` 并附授予标准理由；checker 补禁无连字符的 `prespecified`。⑥ **P13**：`prospectively specified` 的 `count==1` 断言改为 **allowlist**（`APPROVED_PROSPECTIVE_LABEL_SITES`，现只含 X1 的 "prospectively specified attempt"），因 WRITING_PLAN:102 明列 P0 判官文件同属真·结果前冻结证据、将来合法使用会被硬 FAIL；`think-span-confined` 与 `think-span-only` 两名一物统一为后者。⑦ **§5 成文（5 小节 + Table 2，无新图）**：**零号问题正面处理**——`prereg-esup.md:17` 冻结的主报是 **T−P** 而非 T−N，故 §5.2 先报结果前指定的 T−P（ES `+.122[.051,.193]`、RR `−.095[−.171,−.029]`），再以 P−N 含零（ES `+.015` p=.709，满足 `prereg-esup.md:22` 决策规则 3）说明 T−N 与 T−P 近乎重合、摘要箭头不因对比选择被抬高；C 臂自带 provenance 一句（不属四臂协议、donor 记录先于该臂运行）。反同义反复三防线全在场（罚点与判分分属不同 span / `scope=all` 消融 B0 ES `.580→.727` / CLR 明标 manipulation check）。M14 脚注覆盖两对且**不印 −10.8pp/+13.6pp 派生量**（results.json 无落账），改为并列两对边际与配对并明写 `.495+.138≠.631`。M02(b) 走已落账路径：`118` gated paired cases + 两臂 strict 率 `.092/.042` + CI 上界恰零（"the interval reaches zero"），不凭空写 11/119 或 5/118。prereg「不声称」句入正文（全程干预态，不证明链路在自然生成中为必需）。R1 三槽全带天花板（ROME-14B 复制且 strict 也分离、MEMIT-14B strict null + fresh-N 侵蚀 ns、X3 主动施加非 passive portability + 内容审计 30/40、11/20、κ=.444）。⑧ **checker**：§5 入审计节（三重快照）；新增 137 个指针以 **prefix** 批准（每条止于只含当前臂/对比的对象，`_` 前缀与 legacy/historical 兄弟仍拒）；X3 的 `30/40`、`11/20` 按 P7 的 SHA 钉法加 token 绑定；`.214` 禁语收紧为**仅禁正值**（`−.214` 是 T−N CLR 合法区间端点）；`\small` 改每表一次；**`PENDING_ABSTRACT_BODY_BINDINGS` 已删=R10 三条件同时清偿**（`8.5` 的 RJ 落在 §5 且 `19.3` 绑 N 臂指针而非 §3 capability 指针，另有一句说明两者重合因 N 臂即 Table 1 同一次运行）。⑨ **门禁**：`python3 src/check_manuscript.py` PASS（§3=127、§4=72、§5=185 RJ occurrences）、`uv run --no-project --with pytest pytest -q src/test_check_manuscript.py` **118 passed**（本轮 +13）。**⑩ 未跑的门（同 v1.93）**：开发机 TeX 仍未就位，四步编译 + 7 页/overfull/Type 3 三条收货线**本轮仍未验证**；因此 §5 只上 Table 2、不新增图，Fig.3 方案（单栏 vs 并入 Fig.2）待页数实测后再定。⑪ **已知待办**：`prewrite/ethics_reverting_truth.md` 仍写 `chain-only repair`/`chain-only suppressor`，已在禁语表内，写 Ethics 时必须改写；`contrasts_B3_mean_ci_p/T_minus_N` 是 `cross_arm_paired_ci/T_minus_N` 的 3dp 副本，同一 estimand，勿当第二次独立估计。
- **v1.93 变更 (2026-07-25)**: **W2-2 终验补丁 P1–P7 落地；§4 收尾前向引用化，冻结台账 token 绑定与边际分母身份转为机器可审计。** ① §4.4 由纯让步收尾改为前向引用收束：在**同名义预算** \(B_3\) 下引 T−N paired ES `+.138[.082,.194]`（真源 `rq3.sup_battery.cross_arm_paired_ci.T_minus_N.ES`，与 WRITING_PLAN C3 同块），显式写明"arms 间 within-case 对照、不是对 \(B_0\)"以防 M14 式边际/配对混算，保留 realized-chain-length 未审计的让步，不写 rules out；§5 的结论仍只由 §5 断言。② §4.1 加显式降权句（"place no quantitative weight on it downstream"），BLOCKED 声明改为点名 `results/probe/logitlens_cf200_ROME_B3.jsonl` 并说明缺失内容（per-item case id + first-token logits）。③ W-B 的 `prospectively specified`/`prespecified` 统一降为 `pre-specified`——该保护性标签只授予结果前冻结产物 SHA/服务器时间戳类证据，W-B 只有 git-commit 类记录；checker 断言 §4 只授予一次且落在 X1 位。④ 锚形容词 `chain-confined` → `think-span-confined`，并入禁语表（与 `chain-localized`/`chain-only` 同列）。⑤ **P6 核实结论=绑定成立、不改绑不加字段**：`.595` 的真实分母确为 200（`0.595×200=119` 整除，且与 `_n_note` 的 b0ok 门分母 119 一致；`0.595×198=117.81` 非整），capability 32B 行与 battery N 臂在 ES_B3/ES_drop/RR/CLR 四端点逐一相等=同一次运行，故 `/rq3/n` 可作该 B0 边际的 attempted 分母。该次人工核实已固化为 checker 不变量（跨块四端点一致 + 名义 n ≥ 各臂有效 n + B0 边际须为整数计数）。⑥ P7：`token:N` 形式引用的冻结台账字符串改由 SHA256 钉住（改写即失效、须重审）——仅靠位置白名单挡不住"同位置同值不同义"的漂移。⑦ P4 核实：arXiv:2603.09906 摘要确以 "semantic bridge" 描述 factual priming，§4.3 措辞维持原状。⑧ 门禁：`python3 src/check_manuscript.py` PASS（§3=127、§4=75 RJ occurrences）、`uv run --no-project --with pytest pytest -q src/test_check_manuscript.py` **105 passed**（新增 11 条回归）；§3 与 `results.json`、Title/TL;DR/Abstract v8.1/OpenReview v5 全未动，§4 三重快照哈希同步。⑨ **未跑的门**：开发机无任何 TeX 发行版（`pdflatex`/`latexmk`/`tectonic` 均不存在），四步编译 + 4 页/无 overfull 收货线本轮**未验证**，须在有 TeX 的机器补跑；运行方式已落 `RUNBOOK.md §11`。
- **v1.92 变更 (2026-07-24)**: **W2-2 §4 Causal Diagnosis 落地，D3/D4 与 X1 防火墙转为机器可审计。** ① §4 按 cloze installation sanity → answer-gated route census → failed replay vehicle → length-account boundary → CLR 分层/W-B 剂量受限边界测试的证据阶梯成文；Title、TL;DR、Abstract v8.1、OpenReview v5 与 `results.json` 均未改，旧 `fig2_logitlens`/`table_rq2.tex` 不接入，图表暂用 main 内无数字占位。② 第一性仲裁收紧 Fable 原案：N/T 仅共享 B3 cap，故不写 equal-length/preserves-better；M1 因 CLR0 的 `N_RR=0` 地板且无 interaction，不称 near-necessity，106/90 只称 arm-paired stratum totals、不得冒充 RR 分母；X1 只称 prospectively specified，不写单一 operative cause，派生 `4/5` 改为真源直绑 `1/5`；P0 称 represented generation settings 而非 three decoding regimes，`.48` 不跨样本外推；W-B 的 `B1` 是 endpoint 标签而非预算，正文不误写预算，且 S−Pshuf LocAcc 只称预设 harm metric 上的 secondary contrast、不得冒充预指定 B2 对照。③ `chain-local causal control point` 定为唯一正文锚，取代 WRITING_PLAN 旧 `chain-localized` 变体。④ checker 扩为 §3/§4 独立 canonical ledger + visible-semantic/TeX-source SHA、跨节 claim-ID 唯一、RJ 行语义哈希、preamble/`refs.bib` 完整性锁、三 κ 身份与 X1 顺序/状态/controls-not-through-replay 守卫；冻结字符串只开放 exact-path/exact-token formatter；引用可见注记、正文分区空隙、非渲染/外部输入命令、TeX 拆词和额外 starred subsection 均 fail closed。回归命令固定为 `uv run --no-project --with pytest pytest -q src/test_check_manuscript.py`，每节合入前与 `python3 src/check_manuscript.py` 同跑。
- **v1.91 变更 (2026-07-24)**: **W2-1 复审仲裁与正文审计门加固。** ① commit `b602dcb` 对 `metric_validation._status/verdict` 的改写经真源、措辞与 checker 三路审计 **ACCEPT**：缺失行混淆矩阵反例推翻旧 ``κ 是下界'' 论证，strict/permissive 均有误差、也不构成数学夹层；正文与 supplementary 统一采用 available-case + missingness-sensitivity 框架，supplement 枚举 all-TN 极端与含 k 条 judge-positive 缺失行的序列，任何敏感性数字须先落 `results.json`，不得复活 lower-bound 声明。② M04 有意不继承 Holm 从句，因为 `results.json` 无对应路径且未作独立落账；W3 门同步为 all-six-cells + cellwise unadjusted CI + ``scope statement, not a post-hoc selection'' + no ordered-trend inference。
- **v1.90 变更 (2026-07-22)**: **story-first Abstract v8.1 定稿，摘要锁关闭，正文债务成为唯一解锁条件。**
  ① **内部终稿**：188 词/8 句/6 个结果数字，SHA256=`0c85a03e9cd288b45d6f23502caf17b74e84c28dee0f3a2e62f9202ec4b81e5f`；正向写作弧线=认证缺口→同编辑双条件→旧答案回归→cloze/route 分离假说→链内因果控制→评测原则。
  ② **审计**：G1/G2/G3 PASS，G4 仅记录 causal-scope 轻度超读风险；最终盲读 v8.1 clarity=`[4,4,4,5]`、无 major overread，未观察到相对 v6 的可读性回归。`paired −0.102` 移出摘要，避免与边际 `19.3%→8.5%` 混算；完整 paired 估计留 D5。
  ③ **冻结边界**：正文完成前不再因风格/词数/新增 abstract-only review 改摘要。仅当正文债务无法安放、摘要与正文实质冲突或投稿政策要求时才解冻，并重跑受影响门。
  ④ **外部同步仍受 G5 阻断**：OpenReview 当前保留 v5；D1–D8/R1 必须在 §3–§5 成文并冻结后，才一次性替换为 v8.1。Title/TL;DR 不动。
- **v1.89 变更 (2026-07-14)**: **最终仲裁裁决落库——身份重构 + 写作冲刺 + 投稿后 S 轨，直到 accept 的总路线。**
  ① **裁决来源**：三份独立审计（Review A/B + 本方 provisional）的 evidence-backed adjudication（六路核验 workflow，全部数字/代码/draft/novelty 引用逐一对账）+ GPT-5.6 对仲裁的复核。复核采纳项：主 claim 用 *insufficient certificate*（禁 *invalid*）；RQ2 叙事降到合法句式（禁 "re-derivation causes"/"41/41 证明重推导"）；RR slope 与 F3 RR 降为 supporting/注明 estimand；**B15 interaction 检验取消**（子群点估已见，只能算 post-hoc follow-up，投稿前不跑）；**X-A 烧池移出投稿窗**（7/29 后独立研究轨启动，正文不列未运行设计为贡献）；commit **不能追溯证明 preregistration**——禁止历史回填，只做诚实 snapshot + provenance manifest 分层（真·结果前冻结证据=SHA-in-artifact/服务器时间戳 vs 事后记录）。
  ② **最大单一瘸腿（终裁）**：RQ2 自然语义中介未识别——降级 framing 处理（claim ceiling 已冻结），非补实验；被日历而非科学堵死（X1 事后分解：committed-OLD∧安装成功下 replay 8/9，仅作内部判断，禁作证据报告）。
  ③ **论文身份（冻结）**：reasoning-time evaluation / safety stress test。三贡献 = evaluation gap / causal diagnosis (not natural mediation) / bounded mitigation transfer。独有性=六元合取（见 WRITING_PLAN §0），不是任一单点。Fig.1=认证缺口图（paired B0/B3 change + 控制面板），不是 scaling 曲线。
  ④ **必写清单**：X1 FAIL 一句正文 + gate 全表进 supplementary；X2（ES 正 + strict RRs null 并报）与 X3（active lexical transfer）写入（draft 旧句 "repair has not yet been tested with MEMIT" 已被 X2 PASS 反证）；MEMIT 现象行带 fresh-N ns 括注；taxonomy 全文统一 n=41/33 独立事实/κ=.813；C 臂加 largely-inactive 限定（T=109 vs C=18）；Loc=target-value non-leakage；genbench 不称等价认证。
  ⑤ **目录更名**：`paper/` → `paperwriting/`（防与 `papers/` 混淆；用户重命名笔误 paperwrting 已修正）。5 个 src 脚本硬编码路径已同步（emergence_regression/percase_emergence/p0_downstream_crosswalk/plots/s1_record）。历史文档内旧路径引用不回改。
  ⑥ **叙事工具政策**：Idea2Story (arXiv:2601.20833) 仅作人工故事结构 checklist；禁跑其 pipeline、禁触数字真源（其示例会在实验前生成虚构结果数字）。**任何未运行实验的结果性陈述 = 学术不端，零容忍**（本轮已明确拒绝"预写 X-A 正结果"的提议并记录在案）。
  ⑦ **日历**：D0 7/14-15 snapshot commit+LaTeX 骨架 → W1 abstract 冻结 7/18 → W2 主文 7/19-23 → W3 7/24-25 只做机器对账+禁语扫描+hostile review → 7/28 提交 → R 7/29-31 supplementary/code/provenance manifest → S 轨 7/29+ X-A（Phase-2 rebuttal 10/19-25 弹药/camera-ready/下一轮）。7/22 检查点：全文 <70% 砍 supplementary 深度，绝不砍对账。预期面板 5/6/6，P(accept)≈45–50%。
  ① **字节/审计门**：`results/b15_caseblock.json` SHA256=`3a663c447031a14b2f0f58d1f7eb8b09892d8c20543e92ce688da98b657c8d0f`；`results/cpu_closeout_audit.json` SHA256=`158e2a4597086dccf48b804a50f227091ce1623de967c4bc060a24687d875fac`。本地 validator 重生 audit 与服务器文件 byte-identical，`status=PASS/failures=[]`；仅保留 F3 missing/error provenance 与 optional P0 logit-lens blocked 警告。
  ② **B15-B0 数字**：`base_budget=B0`，base provenance 也明确 `selected.budget=B0`；edited/base duplicate audits 均 PASS。五个 checkpoints，n=994 rows/200 facts：matched baseline `.1005[.0335,.1684]`；controlled `.0837[.0158,.1510]`；base-known `.1103[.0272,.1950]`(693/183)；base-unknown `.0331[-.0755,.1464]`(301/127)。family→row sensitivity controlled `.0837[.0130,.1493]` 同向排零。
  ③ **科学裁决**：加入二值 B0 recall 协变量后 slope 点估从 `.1005` 降到 `.0837`(相对衰减 16.7%)，但残余 slope 仍排零，否定“全部只是该基座知识代理”。这不是被解释比例的因果识别；binary answer recall 是粗代理，仍有测量误差/残余 confounding；known/unknown 两层未做 slope-difference 直接检验，不宣称 effect modification 或“燃料-引擎”因果分解。
  ④ **队列/停止边界**：无剩余 GPU 实验，无剩余服务器 CPU 分析。P0 logit-lens per-item crosswalk 仍是缺原始 dependency 的非承重 optional blocked item，不因卡空闲重跑模型。当前唯一任务=执行最终 scientific review，然后才写作。
- **v1.87 变更 (2026-07-13)**: **服务器 CPU 产物回传后抓到 B15 budget estimand 错位；五块先闭，B15 零卡定向重开。**
  ① **artifact 字节门**：`percase/b15/cap3/f3/x2/x3` 六文件 SHA 逐份与服务器 audit 相等；JSON 结构均合法。现行加固 validator 下总 audit 因 B15 两条 budget 门正确 FAIL，其余全部通过。详见 `analysis/16_cpu_closeout.md`。
  ② **Percase 闭合**：es_drop slope=`.1094[.0417,.1770]`；RR=`.6444[.1985,1.1427]`；CLR∧RR=`.6444[.1914,1.1457]`。主 CI 抽 200 unique facts，只条件于六个固定 checkpoints。Qwen 32B−14B 配对差 `.0657[-.0303,.1616]` 含零；因此只称 size-associated supporting evidence，不称 scaling law/capability causality。
  ③ **Cap3 闭合**：primary net-CLR=`.0522[-.0075,.1111]` 含零；raw CLR 不承重 capability。`baseCLR0` subgroup=`1.0054[.3875,2.0104]` 只作 scale-dependent selected-subgroup 探索，不救主端点。
  ④ **F3 闭合**：same-seed 主分析 199 cases/597 pairs，唯一缺 `cf_10436` 三个 B3 seeds。ES-drop=`.117253[.067002,.169179]`；equal-case conditional RR=`.305180[.242117,.371622]`，但 trajectory-weighted 率为 `87/350=.248571`，必须分清 estimand。合法 claim 是“三个固定 sampling seeds 下侵蚀仍存在”，不是 sampling 显著强于 greedy/随机 seed 总体。
  ⑤ **X2/X3 refresh 闭合**：X2 v2 新增 N/T/C 各 400 unique worlds 的 explicit duplicate audit，端点零漂移；X3 v2 端点零漂移，sound primary 只由 T−C strict PS `.055[.020,.0925]` 承担，C−N 不是等价检验。
  ⑥ **B15 错位与修复**：回传 B3 sensitivity 为 controlled slope=`.0992[.0304,.1684]`，但 `b15_regress.py:6` 定义的冻结问题是 B0 knowledge coverage。已加 `--base-budget B0`、产物显式 `base_budget/base_recall_definition`、validator 同时审 edited/base duplicate audit 与 B0 provenance；launcher 加 `--b15-only`。新 B0 结果前不得用 B15 升格 capability/“燃料-引擎”叙事。
  ⑦ **停止边界**：B15-B0 之外不起新 CPU/GPU 科学队列；P0 logit-lens crosswalk 仍是缺 per-item/dependency 的 optional blocked component，不猜 case IDs。B15 回传后升 plan v1.88 并进入最终 scientific review。
- **v1.86 变更 (2026-07-13)**: **重开零 GPU 统计冻结门；修复 v1.85 未识别的统计/数据世界问题。**
  ① **case-block 是唯一主 bootstrap**：`src/percase_emergence.py`、`src/b15_regress.py` 与 `src/cap3_netclr.py` 的主 CI 抽 unique `case_id`，每个抽中的事实保留其跨 scale/family 全部可用行；推断范围明确限定为“conditional on these fixed checkpoints 的事实抽样不确定性”，不能外推为模型总体 scaling law。旧 family→row 数字保留为 `_family_row_sensitivity`，在新产物审计通过前 `emergence.percase`/B15/Cap3 旧 CI 均属 superseded-pending。
  ② **拒绝 duplicate world**：同一 `(scale,family,case_id,budget)` 若来自多文件，规范化科学字段不一致即 hard FAIL；一致重复也须去重并记录来源。共享盘正式命令只纳入六个显式 headline world，7B 只用 `r*of8`，不得同时 glob `probe/` 与 `pilot/` 的历史 `of7/of8`。
  ③ **F3 三 seed 重算**：旧 `metrics.score/drop_bootstrap` 的首行行为不能承载三 seed 复现；新 CPU scorer 按同一 seed 的 B0/B3 配对、同 seed B0 门、先汇总每 case 的 seed 结果，再 bootstrap unique case。缺配对、重复和 seed 覆盖必须显式报告。
  ④ **P0 发布链加固**：40 条 reused route votes 必须逐条与冻结 membership sample 的 `existing_route_votes` 一致，并记录 A3-neutral/B16 上游文件 SHA；P0 CLR crosswalk 同时保留 historical/raw 与按 `metrics._without_subject` 重算的 paper-caliber 口径，禁止混称。
  ⑤ **X3 推断边界纠正**：确认性证据只由预注册主对比 `T-C` 的 strict lexical PS CI 排零承担；`C-N` 含零不是等价检验，`T-N` 点估为正也不是单独显著性门。若无事前等价界，不得报 control equivalence/惰性认证。
  ⑥ **其余仪器卫生已闭**：P0 40 条 reused route votes 与冻结票逐条一致，A3 raw/paper CLR 在 33 条上数值相同但分仪器落账；route 默认 neutral、无两票多数则重裁；`flip_analysis.last` 改用末次提及；metrics 显式返回 `rr_n`；Loc 只称 target-value non-leakage。上述均不改变当前主指标/P0数字。因新增 provenance 字段，当前 `p0_corrected_taxonomy.json`/`p0_downstream_crosswalk.json` SHA 更新为 `c11c6a0e…`/`f034a5f4…`；v1.85 记录的旧 SHA 仅对应当时字节版本。
  ⑦ **唯一执行入口/停止边界**：`experiments/run_cpu_closeout.sh` 先硬验显式 raw globs，再跑全部定向测试与六个 CPU 分析，最后由 `src/validate_cpu_closeout.py` fail-closed 审计并写 `results/cpu_closeout_audit.json`。本轮不改 `paper/draft.md`、不开 GPU、不改变 X1 预注册结论；新 audit PASS 且产物回传落库后才关闭零卡门并进入最终科学复审。logit-lens raw 若仍不存在，只保留单项明确 BLOCKED，不猜 case IDs。
- **v1.85 变更 (2026-07-13)**: **P0 最终闭环 + 下游 crosswalk + X3 paraphrase 内容审计，零 GPU 队列收口。**
  ① **P0 route rescue 完成**：唯一 rescue `b16|qwen32b-sample|cf_15156` 的三名 fresh neutral route judges 均投 Bridge；`results/p0_corrected_taxonomy.json` SHA256=`a11092b075b492a69822cf05e23c61d5b6910a82e91b0f1fe02bfacf8c399c7d`，状态 `PASS/COMPLETE`。最终 n=41，Bridge=27(65.85%)、Recall=11(26.83%)、Reflective-override=3(7.32%)、Associative=0；route unanimous=35、2–1=6、split=0、raw agreement=111/123=.90244、Fleiss κ=.81260。旧 50-row 68/22/8/2% 仅保留为 superseded historical audit，不再承重。
  ② **P0 downstream crosswalk 完成三轴**：`results/p0_downstream_crosswalk.json` SHA256=`6d56f634d07c976c85cca0eaec30381e6e5d07543720980e831ec0571ea3d7af`。X1 frozen 18 的 semantic membership=OLD/NEW/NEITHER 13/0/5（官方 9/18 FAIL 永远不变）；历史 necessity 19=13/3/3，corrected OLD 13/13 CLR、route 10 Bridge/2 Recall/1 RO；全部 A3 非 OLD 仍 18/20 CLR，故 CLR 不充分；W-A a2rev overlap 15 的 membership=6/5/4，故 lexical group 不等同 committed OLD。
  ③ **logit-lens crosswalk 严格阻塞**：预期 raw `results/probe/logitlens_cf200_ROME_B3.jsonl` 本地不存在；只有 results.json 聚合 n=23 与图，禁止猜 case IDs。状态记 `BLOCKED_MISSING_PER_ITEM_ARTIFACT`。收到文件后运行既有 CPU 脚本即可闭合，不重跑模型。
  ④ **X3 盲内容审计完成**：三名独立审计员对 seed42 的 40 条冻结 paraphrase 投 readable/same-fact/prefix-change。aggregate=`results/x3_para_audit20_labels.json` SHA256=`3c9eb3035059afa09f1fbecd06872bebc03c33e940e9ae3d76f17c265df300fb`；majority readable=36/40、same-fact=30/40、prefix-change=2/40，合取 audit-valid=30/40，双 paraphrase 均 valid 的 case=11/20。same-fact raw agreement=92/120=.7667、κ=.444（中等），因此不得把 X3 写成 40/40 人工认证的语义 paraphrase 泛化；按 prereg 不删 case、不改 strict lexical PS 主门 PASS。
  ⑤ **执行边界**：不修改 `paper/draft.md`，不恢复 X1 五臂，不筛 case，不启动 GPU。零 GPU 本地工作除缺失 raw 导致的 logit-lens crosswalk 外已完成；下一动作是索取该单文件，同时开始一次 results-first scientific review。
- **v1.84 变更 (2026-07-13)**: **P0 membership 三票落账 + 触发单条 route rescue 停止边界。**
  ① **原始技术审计 PASS**：三份判官文件实际落盘名为 `results/p0_judgeJUDGE_1/2/3.jsonl`，均 101 行/101 唯一 `item_id`，与 sample/prompts 集合和顺序逐行一致；标签只有 old/new/neither，reason 全非空，无缺行、重复、无效标签或格式污染。`results/p0_membership_verdicts.jsonl` 严格合并 101 行，SHA256=`2f6802501e4748e38e50b07e8ffd1a1ea1df426158db5b7d1169013c3e9e9981`。
  ② **membership 数字**：J1 old/new/neither=39/43/19，J2=42/43/16，J3=41/44/16；unanimous=97，2–1=4，1–1–1=0，raw pairwise agreement=295/303=.97360，membership Fleiss κ=.95779。多数票 OLD/NEW/NEITHER=41/43/17；统计单位是 101 items，不把 303 票当独立样本。
  ③ **转移**：原 current-in-pop=50 中 40 保留并复用旧 route votes、10 drop（均为 majority NEITHER）；原 excluded=51 中 50 保持 excluded、1 条 majority OLD rescue。membership 层 OLD=41，但不得在 route rescue 完成前报 corrected taxonomy 路径分布。
  ④ **唯一 rescue**：`b16|qwen32b-sample|cf_15156`，membership votes=`[neither,old,old]`。已按 source path/line/case/hash 回读原链，用 `JUDGE_PROMPT_NEUTRAL` 冻结 `results/p0_route_rescue_prompts.jsonl`，SHA256=`02332cef8feeecf3458f59505e98633345b7483da4290d361eeab7a94fb3c638`，且不带入旧 `Excluded-held` 票。
  ⑤ **停止边界**：`results/p0_membership_audit.json` 为 `technical_status=PASS`、`status=ROUTE_REJUDGE_REQUIRED`、`corrected_taxonomy_status=PENDING_ROUTE_REJUDGE`、missing=[]、insufficient=0、drops=10、rescues=1。下一步仅补 cf_15156 的三名 neutral route judges；其完成前不终结 taxonomy、不更新 draft、不恢复 X1 五臂、不开 GPU。
- **v1.83 变更 (2026-07-13)**: **P1 v2 封口 + X3 Day-0/manifest 内容审计。**
  ① **P1 v2 全部通过**：`results/p1_reload_summary_v2.json` SHA256=`cbb969d79b0a4682e28d83bfc672870b93ea8800eb2643735f7f70960e702d41`；`status=PASS`、`failures=[]`、`warnings=[]`、`extended_audit_status=PASS`。18 cases 在 12 次条件运行中均为全 0/12 或全 12/12，且 **18/18 的答案 SHA 跨全部 12 次逐字一致**；四个 F2 失败 case 为 `cf_18471/cf_18494/cf_15609/cf_2443`。
  ② **编辑幅度解释也不支持**：编辑权重始终为 `model.layers.12.mlp.down_proj.weight`；relative-L2 的 MP2−single 与 A−B 均为 0[0,0]，四格内 reload 的 weight-delta 也无变化。失败/成功 case 的 relative-L2 均值为 .022781/.022628，没有“失败=零更新/小更新”分离；但有效单位只是 4/14 cases，不对 scorer 中重复执行的 n=48/168 做正式推断，也不把 norm 相同升级为张量逐元素一致。
  ③ **P1 合法结论不变**：当前运行的 topology/node/reload/更新幅度不是 X1 fresh-B0 失败的解释；但 historical/runtime comparator 仍缺，不得写 F2 机制或 case 内禀不可编辑。没有 post-restore checksum；summary 只输出 provenance signature 数量而非具体值，发布级第三方审计仍须保留 raw shards。
  ④ **X3 legacy Day-0 内容已核**：`results/x3_day0.json` SHA256=`39592a0b42c60d1c72592a7c627afc7bc8967fe82780d0cba8320f7051f63346`。旧 `probe32b.yaml` 选 200 cases；B0=400/400 rows、PS=.3625，B3=392/400 rows、missing=8(2%)、PS=.42347，共记 10 error rows。它只是 legacy N audit，与最终 fresh-mp2 N/T/C 不混池，不改变 X3 主门 PASS。
  ⑤ **X3 audit20 只是 manifest，不是已判可读性结果**：`results/x3_para_audit20.json` SHA256=`374efa6d6156809c5e11cd3f39ca4b2ba938745e8da75170aa5084e03de0d035`；seed42 的 20 个 unique cases/40 paraphrases 齐，有记录的 question 与冻结 paraphrase 逐字相同；legacy N 中 `cf_8371` 的 B3 para0/para1 缺失，故记录 question 为 78/80。文件不含 readable/answerable/prefix-change 标签，不得声称 readability audit PASS；该程序性欠账不允许删 case，不影响已完成的 fresh-mp2 主端点。
- **v1.82 变更 (2026-07-13)**: **P1 行为终裁 + GPU 队列关闭，P0 成为唯一承重任务。**
  ① **P1 首版技术/行为汇总 PASS**：18 cases×2 nodes×2 topologies×3 reloads=216/216 case-edits；12 个 cell 均为 fresh-B0 strict **14/18**，每格来源分解完全相同：main 10/10、F2 1/5、historical sample 3/3。MP2−single 在 A/B/pooled 均为 0[0,0]；A−B 在 single/mp2 均为 0[0,0]。
  ② **排除与残余**：四个 node×topology 格内三次 reload 的 strict flag 与答案 hash 均无变化；在当前返回的行为结果中，X1 的四个 fresh-B0 失败不支持 single-vs-mp2、节点或重复重载漂移解释，且稳定富集于 F2。完整的跨格 code/software/model/runtime parity 尚待 CPU v2 审计；合法残余仍是 historical/current protocol drift、case/cohort fragility 或二者交互，不能写成 F2 机制或 case 内禀不可编辑。
  ③ **CPU 二次审计，不重跑 GPU**：首版 scorer 只验 weight-delta 字典存在，未汇总 norm、跨 topology/node 答案 hash 或完整 provenance parity。`src/score_p1_reload.py` 已补这些确定性汇总；只需在共享盘 raw P1 jsonl 上重跑 CPU。无论该二次审计结果如何，P1 不改变 X1 9/18 FAIL、不筛 case、不重开五臂。
  ④ **资源裁决**：H200-A/B 停止新模型任务，分别保留 P1/X3 raw shards、logs、summary、配置与校验和后释放。P0 的 101 chain instances×3 answer-only membership votes 是当前唯一承重任务；P0 完成前不得为占卡新开 DROP 轴。
  ⑤ **X3 Day-0 证据补齐一半**：用户在服务器以 `ls -lh` 确认 `results/x3_day0.json` 与 `results/x3_para_audit20.json` 均存在，显示大小为 927B/18K、时间为 `Jul 11 02:50`。文件缺失风险解除；内容、hash 与20条人工可读性结论尚未回传，故不得写成独立审计 PASS。
- **v1.81 变更 (2026-07-12)**: **X3 落账 + X1 仪器审计后的 P0/P1 收口调度。**
  ① **X3 预注册主端点 PASS**：fresh mp2 N/T/C 各 200 cases、32 shards、0 error；T/C 对 N 的 B0 共 600 probe rows 逐字一致。B3 strict paraphrase success（para0+para1，按 case 聚类）的 T−C 为 **+0.055 [0.020,0.0925]**，C−N 为 +0.0025 [−0.0075,0.0125]，T−N 为 +0.0575 [0.020,0.095]，满足联合门。该结果只证明抑制器**主动接到 paraphrase query**时的 strict lexical PS 改善，不证明未接入干预时的 passive paraphrase portability。
  ② **X3 次级明确降级**：固定 N-B0 成功门仅 110 cases/145 rows（预注册确认阈值 140 cases 未达）；old-only T−C=−0.0138 [−0.0420,+0.0137] 含零。因此不得写“语义 committed-old 显著下降”或把次级包装成确认性结果；合法结论是主 PS 端点 PASS、old-only 次级 directional/null。X3 仍是 add-only，不改 abstract。
  ③ **P0 为唯一最高优先级**：`chain_classify.py` 的 neutral route prompt 预设 final answer reached OLD，schema 又无 `neither`，故现有 `in_population` 不能承担 committed-OLD membership。对全部 101 个 `(cell,case_id)` candidate chain 先用 answer-only OLD/NEW/NEITHER 三判官重门控；原 in-pop 且仍 OLD 的路线票可复用，原 excluded 但新判 OLD 的行必须补跑路线票。官方 X1 9/18 FAIL 不变，事后 corrected 数字只作诊断。
  ④ **双 H200 只跑 P1，且是诊断非救援**：使用冻结 X1 manifest 的全部 18 case（10 main/5 F2/3 sample），各做 3 次独立模型重载；Round-1 为 H200-A=single、H200-B=2×H200 balanced，Round-2 交换 A/B，形成 node×capacity crossover（18×2 nodes×2 topologies×3 reloads=216 case-edits）。只生成 fresh B0，记录 strict B0、答案逐字稳定性、runtime/device provenance 与权重更新摘要。topology 效应须在两节点同向才归因 mp2；node 主效应、source-cohort 差异与同格 reload 波动分别报告。无论结果如何都不改变 X1 FAIL、不继续五臂、不按结果删 case。
- **v1.1 变更**: ① 新增 §2.6 第 4 项混杂（批量编辑干扰）并确立**单条编辑为主协议**；② §5 算力账按单条编辑协议重算（70 → ~400 GPU·h，原估计依赖批量编辑+vLLM 假设，与主协议冲突）；③ 风险表补 R1-Distill-Qwen-7B 基座为 Qwen2.5-**Math**-7B 的超参移植风险与层扫描预案；④ 新增 §11 源码实测附录（hparams 路径、prefill 模板字符串、CPU 冒烟脚本，全部为 2026-06-10 源码确认）
- **v1.2 变更 (2026-06-10)**: ① **单条编辑协议获用户签字确认**（算力 420 GPU·h 预算生效）；② EasyEdit 权重还原机制审计完成（精确逐元素拷回，循环正确性成立，证据见 `analysis/01_easyedit.md` §3）；③ CPU 冒烟因容器磁盘/无 torch 改在本地执行（命令在 01 笔记 §1）；④ 新增 §12 Pilot harness 三模块完整实现代码
- **v1.3 变更 (2026-06-10)**: ① Phase 0 第 3 张复现笔记 `analysis/03_rtofu.md` 完成（R-TOFU 解码协议 + 口径审计）；②【§12.1 注意点② 定案】`<think>`/`</think>` 在 R1-Distill-Qwen-7B 与 -Llama-8B 的 tokenizer 中均**非**特殊 token（查 HF `tokenizer_config.json` 之 `added_tokens_decoder`）→ `</think>` 走文本检测，无需 token-id StoppingCriteria；③ `src/think_budget.py` 用 R-TOFU 逐字 prefill（ZeroThink/LessThink/DefaultCoT，byte-for-byte 校验）替换 v0 占位，`_gen` 解码改 `skip_special_tokens=True`；④【待用户拍板】预算档定义在 §2.4（6 档）与 §12.1 代码（B0–B4 5 档）间不自洽，详见 03 笔记 §9
- **v1.4 变更 (2026-06-10)**: ① task#02 AlphaEdit 笔记 `analysis/02_alphaedit.md` 完成——两实现算法逐行同构，唯一实质超参差异 **L2（EasyEdit=1 vs 官方=10）**；发现 **EasyEdit 内置版 P 预分配缺 qwen 分支的崩溃 bug**（上 Qwen/R1-Distill-Qwen 主模型前必打 vendor_patch，见 02 §4）；P 与 MEMIT 共享 mom2（task#04 一次 cov 喂两编辑器）；② task#07 `src/test_think_budget.py` 写好——mock 控制流 6 测全过（B0 空/截断 CAP/单调/B4 WAIT≤2，think_budget.py **首次实跑**通过），真模型长度分布层待 H200；③ task#03 本地环境就位（Miniconda+editrev py3.10，EasyEdit 全依赖装通，`env.lock` 105 包），踩坑见 01 §6（conda ToS / conda-forge 无 pip / easyeditor 需 PYTHONPATH）；冒烟（GPT-2-XL ROME）进行中；④ task#04（mom2@8×H200）按用户决定**延后**（需实验室专网）
- **v1.5 变更 (2026-06-11)**: ① task#06 数据提取完成——`src/build_dataset.py` 把 CounterFact(21,919)/zsRE(18,377)/MQuAKE-CF-3k(3,000) 清洗为统一 jsonl schema + `data/aliases.json`(1,285 实体)，数据卡 `analysis/06_data.md`；②【zsRE 映射决策】o_old=answers[0]→o_new=**alt**（反事实，与 CF 同语义，有真实 o_old），answers[1:] 是"其它可接受答案"非别名（已排除防判分污染）；③【确诊 pilot-blocker】EasyEdit `edit()` 必传 `subject=`（否则 ROME/MEMIT 取不到 subject 失败），且 `src/edit_loop.py` v0 读 `case['subject']` 而本 schema 字段是 `s`——两处随 Phase 1 接线修（详见 06 §5）；④ 大数据 jsonl/raw gitignore 靠脚本再生；Phase 0 复现笔记余 **04(ThinkEdit)/05(R²MU)** 两张
- **v1.6 变更 (2026-06-11)**: 算卡前 harness 加固——① `src/edit_loop.py` 修 5 个坑（`case['s']` 字段名、`edit()` 传 `subject=`、字符串 case_id 改按 enumerate 序号分片、HP_CLS 补 AlphaEdit/FT、单条 case 出错不拖垮整片且总还原），消除 06 §5 确诊的 pilot-blocker；② `src/metrics.py` 加固（`.get("probe")` 跳过错误标记行、`hit()` 容忍 None 目标）；③ 新增 mock 单测 `src/test_edit_loop.py`(7 测) + `src/test_metrics.py`(2 测，ES/RR/CLR 逐档手算核对)，均无 GPU/依赖、CPU 即过
- **v1.7 变更 (2026-06-11)**: 算卡前 pilot harness 串通（开窗即跑）——① `experiments/pilot.yaml`（R1-Distill-Qwen-7B × {ROME,MEMIT} × CF-200 × {B0,B3,B4}，8 卡分片）；② `src/run_pilot.py` 入口（seed42 确定性抽样、enumerate 分片、续跑、`--dry-run`；用 overrides 把 EasyEdit qwen2.5 yaml 的 model_name→R1-Distill + stats_dir 分目录 + 按 rank 设 device）；③ `src/prefilter.py`（§2.3 预过滤，复用已测 metrics.hit）；④ `edit_loop.run` 加 `overrides` 注入；⑤ `src/test_run_pilot.py`(4 测) + 干跑真配置通过；`results/` gitignore
- **v1.8 变更 (2026-06-11)**: ① 新增 `RUNBOOK.md`——算卡/内网窗口**自助操作手册**（环境→数据→mom2→pilot→打分→go/no-go + AlphaEdit/think_budget 预备 + 雷点速查 + §9 待拍板决策），内网无 Claude 也能照跑完 pilot；② `src/score_pilot.py` 一键打分（glob 分片→ES/RR/CLR，复用已测 metrics，附 go/no-go 判据）；③ CLAUDE.md 指向 RUNBOOK + plan 版本号订正
- **v1.9 变更 (2026-06-11)**: 按 Prompt2「读原文 + 从代码出发」给 01/02/03 各补「论文宣称 vs 代码现实」一节——① EasyEdit：易用=统一接口真但开箱有摩擦，"editing 超 FT reliability" 正是我们要在 think 预算下反证的对象；② AlphaEdit：**零空间阈值 论文脚注 10⁻² vs 代码 2e-2（2×）**、"一行代码"藏了 P 预计算、"+36.7%" 是 sequential（我们单条用不上）、L2 论文省略且两实现不一致；③ R-TOFU：**ZeroThink/LessThink 实为 Jiang et al. 2025 非 R-TOFU 原创**、方向与我们镜像成对、step-wise=句级参考 CoT 相似度、单 Llama 基座。Phase 0 复现笔记余 04(ThinkEdit)/05(R²MU)
- **v1.10 变更 (2026-06-11)**: task#04 ThinkEdit 完成（读 PDF 2503.22048 + 代码）——① 笔记 `analysis/04_thinkedit.md`（方向抽取 Eq1 / steering hook Eq2 / 权重编辑 Eq6 三机制 + 论文宣称 vs 代码现实）；② 通用 steering 工具 `src/steer.py`（`Steerer` 残差流方向注入 hook + 位置掩码条件化 + `extract_direction`，改造自 ThinkEdit 并推广出 F1 要的条件注入）+ `src/test_steer.py` 4 测过（editrev）；③ 关键雷点：ThinkEdit base **无 7B**，方向/头不可跨模型复用，我们 7B 须重抽。**Phase 0 复现笔记余 05(R²MU) 一张**
- **v1.11 变更 (2026-06-11)**: task#05 R²MU 审计完成（读 PDF 2506.12963 + 代码）——`analysis/05_r2mu.md`：① 代码健康度审计（无 requirements/README、自有 8 py vs vendored lm-eval 571 py、judge `temperature=0.0` 被注释→非定温、openai 旧 SDK、judge 模型 gpt-4o/o3/claude 三处不一致）；② 残留口径=LLM-judge **1–4**「推理链是否支持 gold」+ mismatch；③ 结论：口径**定义一致但数值不可独立复现**，只引定义不采数字；④ 三方残留口径分名（R²MU judge1–4 / R-TOFU judge0–1 / 我们 CLR 子串）。**Phase 0 六份复现笔记 01–06 全齐（W1 硬节点 6/17 提前达成）**
- **v1.12 变更 (2026-06-11)**: 【用户拍板取 B】预算档 §2.4（原 6 档）与 §12.1 代码不自洽问题**对齐代码定为 5 档 B0–B4**（去独立 4096、natural≈B3 的 cap8192）：§2.4 重写 + Phase0#03/Phase1/Phase2/§5 的"6 档 / {0,natural,extend}"统一改"5 档 / {B0,B3,B4}"；`analysis/03_rtofu.md` §9、`RUNBOOK.md` §9、`experiments/pilot.yaml` 的"待拍板"注记标结案。**路线确认：先复现 + 写分析笔记（Phase 0 已毕）**
- **v1.13 变更 (2026-06-11)**: 组里算力暂不可用，改本机 M5 Pro 24G/MPS 跑迷你彩排（`src/local_probe.py` + `analysis/07_local_probe.md`）——① **Part A：`think_budget` B0–B4 在真 R1-Distill-Qwen-1.5B 上长度分布验证通过**（B0 空/B1 截断/B2-B3 natural/B4 延长，单调，与 mock 一致 → task#07 part B 在 1.5B 落地）；② **Part B：ICE 现象探针诚实负结果**——1.5B 在 B0 即拒绝上下文注入、直接答参数 o_old（10/12），无编辑可回退 → ICE 测不出"越想越退"，恰**反证项目须用参数编辑而非上下文注入**；③ 方法学教训：预过滤口径成立、判分需 FlipPoint（非仅子串）、ICE 不能替代参数编辑做自变量。下一步本地可试 EasyEdit ROME on MPS（参数版，cuda 假设或需补丁）
- **v1.14 变更 (2026-06-12)**: 新增 `sumandplan1.md`（进度总结 + 下一步作战计划，初稿经 4 视角对抗核查修订）。核查 round 三条新知识：①【升级】EasyEdit qwen 路由 bug（`editor.py:122` 裸 'qwen' 分支传 `fp32` kwarg）按 model_name 字符串触发、与硬件无关——**H200 pilot 同样必撞，定性为 pilot-blocker**（修复=方案 A monkeypatch 进 vendor_patches，eos 覆盖经核证为潜在隐患而非现行污染：generate 停止判据来自模型 generation_config(151643)，think_budget 未传 eos_token_id）；②【订正】`<think>`/`</think>` 实为 tokenizer.json added_tokens 在册的**非特殊原子 token**（151648/151649），并非"普通 BPE 文本"——文本检测结论不变，03 笔记 §4 与 think_budget docstring 依据待订正；③【新列 P0 工具缺口】0.6×3 采样臂（think_budget 写死 greedy）与 Locality/Paraphrase 判分（metrics 只消费 efficacy，layer 扫合格线判不了）+ jsonl 溯源头——全部离线可补，列入开窗前必做（sumandplan1 §4.2-②/§6.1-②）
- **v1.15 变更 (2026-06-12)**: sumandplan1 §6.1 的 P0①②③+P1④ 全部落地（5 commit）+ 文档同步：
  ① **P0① qwen 路由修复**：`src/vendor_patches/easyedit_qwen2_loader.py`（方案 A monkeypatch）+ 4 mock 测 + `edit_loop` 自动接入 + README §2 + 真模块校验（editrev）——**pilot-blocker 清除**；
  ② **P0② 开窗前三件**：0.6×3 采样臂（`think_budget` do_sample/temperature/seed 通道，`pilot.yaml` `sampling` 默认 greedy）；Locality/Paraphrase 判分（`metrics` 消费 para/locality 探针，出 ES/PS/Loc + decode 过滤）；jsonl 溯源头（`edit_loop` 每分片首行 git/配置/seed，`git -C 项目根` 避 EasyEdit 自带 .git）；
  ③ **P0③ 参数版 ROME-on-MPS 端到端跑通**（`src/rome_mps_probe.py`，1.5B，8 编辑 0 算子墙，`analysis/08`）——**关键发现 → 本版纳入计划口径**：EasyEdit `rewrite_acc` post=6/8 但**生成式 ES_b=0/8**，两口径在弱模型上脱节，且多层{3,5,8,12,16}皆然 → **§2.5 指标 & §7/Phase1 的 layer 扫合格线（ES≥90% & Loc≥85%）明确判生成式 ES_b、不判 rewrite_acc**；1.5B@默认超参编辑不进生成 → 主结果须 7B（基座 Math，layers 要扫，必要时调 v_lr/v_num_grad_steps）；
  ④ **P1④ FlipPoint**：`metrics.flip_analysis`（first/last 立场 + flip_pos）+ `score()` 增 `ESf`/`Flip` 列（§2.5 FlipPoint 给字符级近似，Phase 3 升级 token 级 logit-lens）+ 10% 边界样本校准流程（`analysis/09`，进 RUNBOOK §4e 窗口剧本）；
  ⑤ **文档同步**：CLAUDE.md（状态/任务队列/防雷清单→现状）、RUNBOOK（qwen 自动修/合格线判生成式/采样臂/校准步/雷点表）、phase-1.md（3 处事实订正）、03 笔记 §4 + think_budget docstring（added_tokens 订正，实测复核）；新增 `analysis/08`(ROME-on-MPS)、`analysis/09`(FlipPoint 校准)
  ⑥ **P2 起步**：`metrics.score_bootstrap`（§2.5 的 95% bootstrap CI，按编辑条目重采样 n=10000，纯 stdlib）+ `score_pilot --boot` 出 ES/RR/CLR CI + 单测。**⑥ 余项待后续**：GSM8K-200/MATH500-100 子集（ThinkEdit `math_grader.py` 可借，需下载）、Qwen3 预研（think_budget enable_thinking 分支 + hparams，6/27 前置）、aliases Wikidata 富集、steer 1.5B 方向抽取试跑、`src/plots.py` 主图骨架
- **v1.16 变更 (2026-06-12)**: **组内算力（启智平台 qz.sii.edu.cn）开通在望**——
  ① 新增 **`interplan.md`**（内网侧 agent 作战简报 = RUNBOOK 的平台适配层：可上网 workspace 备料 → 单卡冒烟 → 1 节点×8 卡分布式 pilot → 打分/校准/审计 → 回传上报；蒸馏自仓库根两份组内教程《交互式建模》《分布式训练》，教程一并入库）；
  ② **新抓一只 MEMIT/AlphaEdit-blocker 并修掉**：EasyEdit mom2 语料 `load_dataset("wikipedia","20200501.en")`（layer_stats.py:104）为脚本式数据集，在 editrev 的 datasets 4.8.5 下**必崩**（实测 RuntimeError），mom2 协方差一步全断 → `src/vendor_patches/easyedit_mom2_dataset.py` 映射到现行 parquet 仓 `wikimedia/wikipedia/20231101.en`（builder 实测可解析；4 mock 测 + 真模块校验；`edit_loop` 自动接入）。**口径注记：协方差语料 dump 2020-05→2023-11**，论文 reproducibility 如实写明；
  ③ 平台作业纪律与我们设计的呼应已写入 interplan §1（jsonl 续跑⇄训练容错自动重启、单进程 mom2 预热防 8 分片并发竞争、网盘挂载持久化、离线 env 三件套）
- **v1.17 变更 (2026-06-12 晚)**: **启智现场摸底推翻 v1.16 关键假设 → 全离线部署改版**——
  ① 现场实测（`report.md`）：平台**完全无外网**（v1.16 的「可上网 workspace」不存在）、镜像近裸机（py3.12/torch2.8.0a0+nv/CUDA12.9，已存 `whyaaai-base`）、**wikipedia 20231101.en 已在平台挂载**（41 parquet 分片，省 20GB 上传）、`$W=/inspire/qb-ilm/project/ai4education/ky26140`；7B 模型与 101 个 cp312 wheel 已在 Mac 下载就绪；
  ② 新增 **`interplan2.md`** 取代 interplan §2–§7（Mac 打包上传 → 平台解包 → `env.platform.lock` 离线装环境 → 模型绝对路径 override → 自检五连 → 冒烟/正式跑/回传），interplan.md 加横幅降级为平台机制参考；
  ③ **`easyedit_mom2_dataset.py` 升 v2**（report §7 问题 A 修复）：本地 parquet **直读分支**优先（自动探测 `/inspire/dataset/wikipedia/...`，env `WHYAAAI_WIKI_PARQUET` 可显式指定；完全不碰 HF hub，`HF_*_OFFLINE=1` 安全），无本地分片回落 hub 映射；mock 测 4→5；
  ④ **抓住 report 遗留的一个平台必崩项**：上轮 wheels 里 pyarrow 被 manylinux2014 约束误降到 20.0.0，而 `datasets 4.8.5` 硬性要求 **pyarrow≥21**（import 即崩）→ wheels 修正三件（pyarrow 24.0.0 manylinux_2_28 重下、antlr4 回 4.9.3 本地打纯 py wheel（omegaconf 2.3.0 锁版）、补 av/opencv 保险）+ `env.platform.lock`（平台专用安装清单，与 env.lock 分明）
- **v1.18 变更 (2026-06-16)**: **8×4090 首次真跑 → 抓修致命 harness bug + 拿到真实生成式编辑信号 + 口径合格线决策**——
  ① **【致命 bug 修复，commit `fb46107`】`edit_loop` 的 `ed.edit(...)` 从 `sequential_edit=False` 改 `True`**：EasyEdit `edit_requests`（`editor.py:406-409`）在 `sequential_edit=False` 下**于 `edit()` 返回前就把 ROME/MEMIT 权重 `copy_to_param` 还原回基座** → 我们随后 `generate_with_budget` **全程在未编辑的基座上生成**。铁证：8 卡跑 layer 5/7/10（溯源头 `overrides.layers` 各为 [5]/[7]/[10] 正确），但三层生成正文 md5 **逐字节相同**（`06a75b04…`）、score 全等（ES=0.075）。`sequential_edit=True` 下 ROME/MEMIT 不内部还原（`editor.py:384-393`），编辑保留到生成完、再由 `edit_loop` 自己的 `finally:restore(model,wcopy)` 做单条协议还原（每次仅 1 条 request + 每条必还原 → 无跨条累积，单条编辑协议成立）。mock 单测全绿；
  ② **【真实信号】修复后同条件（7B / real CounterFact / n=40 / B0 / 未预过滤 / 8×4090）生成式 ES_b：layer 5=0.55（Loc 0.85）> layer 7=0.475（Loc 0.825）> layer 10=0.40（Loc 0.825）**——ES 从 0.075 跳到 0.55（×7），三层分开且单调（早中层更利事实编辑，合 ROME 文献）。**锁定 layer 5**；
  ③ **【口径决策，拍板】§7/Phase 1 的 layer 合格线 `B0 ES≥0.90 & Loc≥0.85` 中的 0.90 是 rewrite_acc 口径数字、误植到生成式 ES_b 口径**：实测 rewrite_acc≈1.0 但生成式 ES_b≈0.55，~0.45 的 logits↔生成 口径差**本身是论文发现之一**。**改为「在 Loc≥0.85 前提下取生成式 B0 ES_b 最高的层」**（best-achievable，非固定 0.90），论文 rewrite_acc 与 ES_b 并列汇报；
  ④ **【文档更正】**`analysis/08` 顶部加重大更正框（§3「rewrite_acc 6/8 vs 生成式 ES_b 0/8 完全脱节」**作废**——当时也走 `sequential_edit=False`，生成在基座上；§1/§2/§4.4 仍有效，§5 的 1.5B"诚实负"存疑待复测）；CLAUDE.md 防雷清单加 `sequential_edit=True` 致命条 + 更正口径条与 layer 条；
  ⑤ **下一步**：layer 5 跑 B0/B3/B4 预算扫（测"越想越退"主论点 ES 是否随预算崩塌、RR/Flip 是否抬头）→ 若信号在，预过滤 n=200 + 全档正式 pilot（ROME+MEMIT）出正式数
- **v1.19 变更 (2026-06-17)**: **ROME × CF 预过滤 n=200 主结果出炉 → 原 RQ1（聚合 ES↓）证伪，主线转 CLR 中心**（全文见 `analysis/10`）——
  ① **预过滤 8 卡分片就绪**：`prefilter.py` 加 `--rank/--world/--merge` + 按 case 续跑（雷点：8 卡并发 `from_pretrained` 会 OOM 挤死 7 个 → **错峰 `& sleep 15` + 日志留盘**，已写 RUNBOOK §4a/§4c/§8）；B3 口径预过滤 248 存活；
  ② **【主结果 ROME n=200】聚合 ES 三档持平 0.375/0.385/0.375，配对 ES 降幅 CI 含 0 → "ES(b) 单调降 ≥20pp"（RQ1-H1）在有功效样本上证伪**，不得再宣称；
  ③ **【口径再修两处】**(a) 判 o_old/o_new 前挖主体复述 `_without_subject`（commit `d29c4cc`，修主体子串致 CLR/RR 假阳 + ES 假阴；新增回归测试）；(b) 回退判据由"答案出现 o_old"改"落定立场 `flip_analysis.last==old`"（commit `1d4835b`）——审计实锤 loose RR 把 Flip/别名假阳（siglas→断言 Japan 却命中别名 Portuguese）算进回退；
  ④ **【回退 honest 数】loose RR(B3)=0.227 → settled RR≈12/75=0.16**（CI 横跨 0.20，骑线）；`audit_reversions.py` 反思归因 7/12=58%（n=12 噪声内 ≈60%）；
  ⑤ **【头牌信号】CLR(B3)=0.685 [0.620,0.750]**——B0 编对的 case 思考时 **69% 在链中重浮旧知识**,压倒性稳健,机理 RQ2 直接证据；
  ⑥ **【机制】churn**：ES 持平 = ~17 条被翻回（掉出 ES）被另 ~19 条 late-emergence（B0 没显形、思考后冒出）抵消 → 聚合稳、底下翻搅。"只在零思考测编辑成功率会错过此不稳定"本身是论文 point；
  ⑦ **【主线重构】** 弃"ES 单调失效"，立"**编辑撑不过链式推理：旧知识 ~69% 重浮于链（CLR 主）+ ~16% 顶回最终答案（settled RR 次）+ 聚合 ES 因 late-emergence 虚假稳定（机制点）**"。**go/no-go 重心拟从最终答案 RR/ES 挪到链层 CLR + 机理可归因**（阈值待 MEMIT 数据齐一起重定 plan）；
  ⑧ **【待办】** MEMIT n=200（mom2 逐层预热，进行中）→ 同款 audit → ROME+MEMIT 回退案例**合并**做反思归因（撑大 n=12）+ CLR 两编辑器对照 → 再拍 6/22；CLR 也需做一次别名/落定清洗审计
- **v1.20 变更 (2026-06-18)**: **MEMIT n=200 齐 + 采样稳健性过 + H200 通路打通 → 实验稳健性收工,转 RQ2**——
  ① **【MEMIT n=200】**ES 略降(0.370→0.315)、**RR(B3)=0.351 CI[0.243,0.459] 稳过 0.20**（比 ROME 强）、**CLR(B3)=0.725**;两编辑器 CLR 都 0.68-0.73 一致 → **go/no-go ① 由 MEMIT 干净满足**;②（合并反思归因 ROME+MEMIT settled 回退：B3 16/30=53%、B4 19/32=59%,贴 60% 线下,但字符正则是下界,RQ2 换 LLM-judge）；
  ② **【采样稳健性,plan §6.3】**ROME cf200s B0/B3 加采样臂(greedy+temp0.6×3seed)：**CLR(B3) greedy 0.685 ≈ 采样 0.680、RR 0.256 vs 0.320（都 >0.20,采样略高）、ES/ESf/Flip 一致** → **结论在 greedy 与采样下都成立,非解码伪影**(论文可写);
  ③ **【H200 通路】**Hopper 上 bf16 ROME `compute_v` 必发散 NaN(采样 multinomial CUDA assert 崩)→ `WHYAAAI_DTYPE=float32` 切 fp32 规避(loader env 开关,commit 见 git);**fp32≈bf16 经 n=40 校验**(B3 RR 0.235 vs 4090 0.227、CLR 一致)→ 两 dtype 结果可混用;H200 fp32 ~2.4× 快于 4090、1800G 内存免错峰(RUNBOOK §8);
  ④ **【口径修两处】**(a) RR 分母改按行 `rr_n`（修采样臂多 seed 致 RR 虚高 >1;greedy/主结果不受影响）;(b) `score_pilot --decode` 分打 greedy/采样臂;
  ⑤ **【下一步=RQ2 机理】**主线已立(CLR 中心)、现象稳健 → 转 Phase 2：**LLM-judge 反思归因**(判 CoT「此处是否反思中重检索旧知识」,取代卡 56% 的字符正则,钉 go/no-go ② + 撑机理章)→ 链内 FlipPoint 定位(旧知识涌回的位置)→ Phase 3 training-free steering 修复(RQ3)
- **v1.21 变更 (2026-06-22)**: **判分基础设施 bug：aliases substring 假阳灌水 → v1.19/v1.20 的 ES/RR/CLR/go-no-go 数值须用去污判分重打**（RQ2 起步时,从 audit 倒回退 CoT 给 LLM-judge 复核途中发现）——
  ① **【根因】**`metrics.hit()` 用纯子串 `c.lower() in t`，而 `data/aliases.json` 含 **287 条 1-3 字符 ISO 国家码/语言码别名**（`W`=Vienna、`in`/`IN`=India、`it`=Italian、`es`/`ES`=Spain、`no`/`NO`=Norway、`fi`=Finland、`fr`=French、`en`/`eng`=English…）。对凡国家/语言类 o_old，`hit()` 在几乎任意文本上假阳（"passed away **in** Rome" 命中 India；含字母 w 即命中 Vienna）。**ES/RR/CLR 三指标共用 `hit()` → CLR/RR 系统性虚高、ES 虚低**；v1.19 CLR 0.685、v1.20 CLR 0.725 / MEMIT RR 0.351「go/no-go ① 干净满足」**均作废，待去污重打**；
  ② **【判分修复，commit `515b87a`】**`hit`/`first_mention`/`last_mention` 改走 `_safe_cands`（丢 <4 字符别名，target 全名永远保留）+ `_wb`（词边界 `\b…\b` 替 substring）；本地实测 6 个旧伪命中（Vienna/India/Spanish/Norway/Finland/Italian on 无关文本）**全消**、4 个真命中（Asia/Microsoft/French/Albania）保留；`score` 另加 **RRs = 答案含旧且不含新**（严口径=下界；RR loose=上界；真回退率夹在二者间）；这也**根治了 v1.19⑧ 挂的 CLR 别名清洗待办**；
  ③ **【回退落定 bug，commit `a938fb3`】**audit 旧「真回退 = `flip_analysis.last==old`」比的是 o_new/o_old 各自**首现序**，把"先断言新、末尾顺带提/否定一句旧"（编辑实际守住）误算回退 → 改按答案**末次提及**三分桶 `clean`/`churn`/`held`，反思归因只对真落定回退（clean+churn）计；
  ④ **【人工复核 + 多判官交叉验证 B3 回退，读真实全答案、不依赖 substring】**43 条 loose 候选里真回退：**ROME 4/17、MEMIT 7/26**（130-agent / 每条 3 判官投票工作流与人工复核完全一致；其余是 held 编辑守住 / refusal 拒答+幻觉，如 `cf_11957` 答 Apple、`cf_2443` 答 Mandarin、`cf_18117` 答 Poland"near Bermuda"）；**真回退反思归因 8/11 = 73%（> 60% 阈）**（`cf_15404` "Wait, Windows is from Microsoft"、`cf_3336` "L'Age 是法语"、`cf_16394` "France→Europe"、`cf_3631` "But wait"、`cf_13413` "I remember"）→ **go/no-go ② 在干净子集上达标**；
  ⑤ **【对 go/no-go 的诚实冲击】**最终答案级真回退率 ≈ **ROME 0.05 / MEMIT 0.11**（远低于阈值 0.20）；去污后 CLR 预计大幅下降（国家/语言类 case 此前近 100% 伪命中）。**v1.20「go/no-go ① 由 MEMIT 满足」须在去污重打后重判**；但现象**定性内核（推理回忆旧知识、顶回编辑、且反思驱动）仍真**，量级须重测；主线或从"RR≥0.20"进一步收缩到"CLR/Flip 揭示编辑在推理下不稳定 + 反思驱动的少数真回退机理"；
  ⑥ **【强制动作】**平台**重打**（纯重打既有 jsonl，无需重生成）：`score_pilot`（ROME+MEMIT 全档，看去污后 ES/RR/RRs/CLR）+ `audit_reversions`（B3 三分桶）。拿到干净数 + 判官结果后**重定 go/no-go 与主线量级（→ v1.22）**，并给 `analysis/10` 加重大更正框（同 `analysis/08` 处置）。
- **v1.22 变更 (2026-06-22)**: **6/22 go/no-go 硬节点裁决 = conditional GO on CLR-centric（用户拍板）**——去污重打后定论：
  ① **【裁决】**最终答案级 ① **不成立**（ROME RR(B3)=0.080、MEMIT 0.172 点估 <0.20；ES 三档持平、配对降幅 CI 含 0）；但 **v1.19 预注册的 CLR 中心信号去污后挺住**：CLR(B3) **ROME 0.335 [.27,.40] / MEMIT 0.405 [.34,.48]**，两编辑器一致、随预算 0→.29→.34→.35 升、CI 远离 0；**② 反思归因 8/11=73%（判官）/ 57–83%（audit）达标** → **GO，主线锁 CLR**；
  ② **【干净主数】**ROME（n=200，全档，greedy/bootstrap n=10000）：ES 0.50–0.545 持平、RR(B3) 0.080 [.03,.14] / RRs 0.050、CLR 0→.285→.335→.350；MEMIT（B0/B3/B4）：ES 0.465→0.430→0.415、RR(B3) 0.172 [.097,.247] / RRs 0.086、CLR 0→.405→.420。去污把 ES 抬高（假阳曾压它）→ **编辑在答案层其实守得住、且不随思考衰减**；
  ③ **【主张收窄·写作口径】**弃 "RR≥0.20 / 答案翻盘 / 越想越退（答案级）"；立 "**编辑只压输出、不擦知识**：原始事实在 ~1/3–2/5 的链中重浮（CLR，随思考预算升），在反思驱动的少数（clean RR ~0.05–0.10、73% 归因）顶回最终答案；答案层 ES 持平 = 编辑『看着成功』却留着旧知识 → **链—答不一致 / 潜在知识冲突**"。confabulated-bridge 定性（"Bermuda is a city in Poland"、"competing with Microsoft"）作机理佐证；
  ④ **【下一步=RQ2 承重墙】**(a) **语义 CLR 审计**（判官式把 CLR 从『旧词出现』收紧到『真旧知识回忆』，去桥接/复述残留，出清洗后 CLR + 干净正例，硬化头牌）；(b) **链内 FlipPoint / logit-lens 定位**旧知识涌回的 token 位（机理章直接证据）；(c) RQ3 training-free steering 修复（接 CLR 这条更顺）；
  ⑤ **【账】**判分修复 commit `515b87a`（词边界+丢短码+RRs）/ `a938fb3`（回退三分桶）；记账 `7c39d64`（v1.21）；`analysis/10` 已加去污更正框；CLR 别名清洗（v1.19⑧待办）已由 v1.21② 根治。
- **v1.23 变更 (2026-06-22)**: **到 7/27 的带日期作战甘特 + 6/27 效应量决策点（go/no-go-2）+ 两版 fallback**——RQ1 现象已立但语义清洗后量级偏小（RR ~0.05–0.10、真回忆 CLR ~0.05–0.14），须先判「现象天生小 vs 7B-Math 知识瓶颈」再定写哪篇。关键路径（今天 6/22 → abstract **7/20** → 全文 **7/27**，UTC-12）：
  ① **6/22–6/23 闸口前置**：`src/base_probe.py`（未编辑基座知识天花板，7B 现成）跑 + `--score`；并行 Mac 下载 **R1-Distill-Llama-8B**（~16GB，通用 Llama 基座 vs 我们 Qwen2.5-**Math** 基座，测「是否数学特化拖累事实知识」，且是 R-TOFU 原锚模型、模板已验证）备传；`ls $W/model_parts` 探是否已有分片；
  ② **6/24–6/26 强模型探针**：stage Llama-8B（传/解包/ROME hparams 适配）→ 小扫层（合格线 Loc≥0.85 下取 B0 ES_b 最高层，plan v1.18③）→ 编 n=100 → B0/B3 → `score_pilot`（干净 ES/RR/RRs/CLR）+ `audit_clr` → 判官面板钉真回忆 CLR；
  ③ **6/27 = go/no-go-2（效应量决策点）**：判据 = 强模型上**真回忆 CLR 或 RR 显著高于 7B 且随预算上升**（暂定 clean recall-CLR ≥ 0.25 或 B0→B3 配对 CI 不含 0 的上升）。→ 达标 = **野心版（RQ1+RQ2+RQ3）**；不达标但 `base_probe` 证明是知识瓶颈 + 方法学/分类学成立 = **稳妥版（RQ1+RQ2+substring 方法学坑）**；两者皆否 = **重议切口**（换任务：multi-hop / in-context vs 参数编辑对照 / 推理密集任务）；
  ④ **6/27–7/4 RQ2 机理**：选定模型上 logit-lens / token 级 FlipPoint 定位旧知识在链中涌回的位置 + 分类学判官钉 recall/bridge/dismiss/revert 率（机理章 + 图 2）；
  ⑤ **7/4–7/14 RQ3 修复（野心版，最大未启动块）**：`steer.py` 抽方向 → 残差注入抑制 CLR / 稳住编辑 → 测前后 ES/CLR/RR + 通用能力不塌（GSM8K-200/MATH500-100 子集，ThinkEdit `math_grader.py` 可借）；稳妥版此段缩为「修复方向可行性 demo」；
  ⑥ **7/7–7/20 写作**：图 1 + 故事先行（abstract **7/20** 硬线，须能独立讲完整故事，两阶段评审 Phase 1 要）→ method/results；**7/20–7/27** 全文 + 补充材料（+3 天）；
  ⑦ **风险 / fallback**：RQ3 滑档 → **7/14 决定**砍成 RQ1+RQ2+方法学；强模型也弱（go/no-go-2 否）→ 方法学/分类学窄 paper 或退 workshop。**关键路径零余量，单点风险 = 6/27 探针结果**；
  ⑧ **行政线（用户负责，提醒即可）**：OpenReview 注册（隐形死线）、CFP track 专属日期核对、每周一 plan §8 增量查新。
- **v1.24 变更 (2026-06-23)**: **强推理器探针出炉 → go/no-go-2 = GO 野心版(framing 改 capability-contrast)**。ROME × CF × {B0,B3}，14B n=100(4090 bf16，编辑层 9)、32B n=100(H200 fp32，层 12)，B0 ES 0.53/0.58(编辑成功率持平甚至升 → 对照公平)：
  ① **【scaling 数,判官口径一致(同一面板判 7B/14B/32B 的 CLR 链)】**真回忆 CLR(panel recall / b0ok)：7B **0.060**(6/100) → 14B **0.151**(8/53) → 32B **0.155**(9/58)；raw CLR_b0ok 0.18→0.40→0.45；**RR(B3) 0.08→0.19→0.26**(32B 点估过 0.20，CI[.155,.379])；RRs 0.05→0.075→0.12。raw 三口径单调升；
  ② **【诚实读法，不得过度宣称】**7B→14B 大跳但**混 scale + 7B 是 Qwen2.5-Math 特化**两因素；**14B→32B 纯 scale 段真回忆饱和 ~0.15、RR 0.19→0.26 但 CI 重叠** → 真实形状是「**弱 math-7B ↔ capable 14B/32B 台阶 + RR 续微升**」，**不是平滑 monotone scaling law**(n 小、CI 重叠会被审稿人打穿)。base_probe 已证 7B 知道事实(B0 答旧 0.59、B3 链含旧 0.755)，故非纯知识瓶颈；
  ③ **【headline】**capable 模型上**编辑撑不过自然思考**：32B RR≈26%、CLR_b0ok≈45%、真回忆≈15%，被零思考 eval 与 substring 判分(虚高 2×)双重掩盖；
  ④ **【主线 framing】**「capable 推理模型上自然思考显著推翻参数编辑(2–4× 于弱 math 模型，capability-contrast)+ recall/bridge/dismiss/restate 机理分类 + substring 方法学坑」。**避免"平滑 scaling law"措辞**；
  ⑤ **【下一步】**(a) **收紧**：32B(+ 可选 14B)**n=200 + MEMIT 第二编辑器**，收窄 RR CI、定 14B-vs-32B 升或平；(b) **RQ2 机理**：logit-lens / token 级 FlipPoint on 32B 定位旧知识涌回位(图2)；(c) **RQ3 steering** 修复(RQ3)；(d) **可选**补 general R1-Distill-Llama-8B 一点，拆开 scale / math-特化 confound；
  ⑥ **【账】**`experiments/probe14b.yaml`/`probe32b.yaml` + `edit_loop` 认 `WHYAAAI_MODEL`(commit `0500e7e`)、`base_probe`(`f265c68`)、`audit_clr`(`be85e82`)；判官面板 3 轮(14B；7B+32B 合判)；**32B 那次 5 错误行**(fp32 在 141G H200 偏紧偶发 OOM，n=99/96)→ 正式跑降并发或补跑那几条。
- **v1.25 变更 (2026-06-23)**: **32B n=200 坐实 RQ1 + logit-lens 钉死 RQ2 机理**——
  ① **【n=200 32B，ROME，B0/B3，错误行 10 / n=198】**ES 0.595→0.495、**降幅 0.106 [0.030,0.182] CI>0 显著**(头一回 ES 降幅显著)；RR(B3) **0.193** [0.126,0.269]、CLR(B3) **0.545** [0.475,0.616]、RRs 0.092。**关键**：7B 上 ES 降幅持平(CI 含 0、被证伪)、32B 上显著 → **「thinking 降 ES」是 capability-emergent**，**原 RQ1 在 capable 模型复活**(比纯 CLR-reframe 更 legible，ES 是编辑标准指标)；
  ② **【诚实校准】**RR n=100 的 0.259 是小样本噪声，n=200 收到 **~0.19、点估略低 0.20、CI 骑线** → 文里说"~19%"，**不宣称 RR>0.20**；ES 降幅 0.106 显著但**未达原阈值 0.20pp**(显著但温和)；
  ③ **【logit-lens 机理，RQ2，commit `2f6f1ec`】**对 23 条**已回退**案例探编辑位(cloze 末位预测宾语)：**100% 仍预测 o_new(顶层 gap +11~+17)→ 回退不是思考擦除编辑权重，而是推理绕过完好的编辑**；逐层 gap 在 **8–12 层(编辑层 12 附近)转负**(native o_old 仍编码=模型仍"知道"真相)、16 层起 o_new 接管 → 双证据(编辑 cloze 守住 + 旧知识网络中段仍在)，与 CLR 链内重浮咬合；(0–4 层正 gap 是 logit-lens 早层噪声，不采信)；
  ④ **【主线收敛】**RQ1 = thinking 显著降 ES(capability-emergent)+ RR~19% + CLR~55%；RQ2 = 编辑完好被推理绕过 + 旧知识中段仍编码 + 链内重推(recall/bridge 分类 + logit-lens)。**ES-decline 复活后不再依赖纯 CLR-reframe**，但 CLR/RR/机理仍是"怎么降的"解释层；
  ⑤ **【下一步】**(a) **14B n=200**(跑中)补 ES 降幅中间点 → 7B 无 / 14B? / 32B 显著 的 capability 曲线；(b) **RQ3 training-free steering** 修复(抑制链内旧知识重浮);(c) 收尾可选 MEMIT 第二编辑器 / general-8B 拆 confound；(d) 开始写作(图1 = ES 降幅 capability 曲线，图2 = logit-lens)。
- **v1.26 变更 (2026-06-23)**: **14B n=200 补齐 → 三点 capability 曲线单调成形(图1)**——
  ① 14B n=200(ROME，B0/B3，错误行 0)：ES 0.555→0.515、降幅 **0.040 [−0.030,0.110](CI 含 0，未显著)**；RR(B3) 0.162 [0.099,0.234]；CLR(B3) 0.475 [0.405,0.545]；RRs 0.045；
  ② **【capability 曲线，全 n=200，单调】**ES 降幅：7B −0.03(ns) → 14B 0.040(ns) → 32B **0.106(显著)**；CLR(B3)：0.335→0.475→0.545；RR(B3)：0.080→0.162→0.193。**ES@B0 升(0.50→0.555→0.595，大模型编得更牢) 而 ES@B3 降(0.53→0.515→0.495) → 「编辑的思考税」随能力增大**；thinking 降 ES capability-emergent(32B 才过显著线)；
  ③ n~55 时的 14B→32B genuine-recall 平台担忧，在 **n=200 的 raw 三口径上单调消解**(genuine-recall 是 raw 的精修子集，raw 单调足以撑 scaling)；RR 的 CI 两两有重叠 → 述「三点单调趋势」而非「逐对显著」；
  ④ **图1 = 此曲线**(ES 降幅/CLR/RR × 模型规模)；**图2 = logit-lens**(v1.25)；
  ⑤ 下一步：**RQ3 training-free steering**(抑链内旧知识重浮、不伤通用能力，GSM8K/MATH 守门)→ 写作。
- **v1.27 变更 (2026-06-24)**: **RQ3 设计面板(ultracode)+ o_old 抑制修复 A/B 成功 → RQ1/RQ2/RQ3 三腿齐**——
  ① **【设计面板，21 智能体】**5 方案对抗评审(有效/安全/可落地/可辩护)→ #1 = **o_old logit 抑制(think 门控)**(总分 13.3,落地最浅+机理对症);次选 FaithSteer(对比方向激活引导)。实现 `src/suppress.py`(build_old_token_ids 多前缀+`_safe_cands` 过滤 / OldTokenPenalty)+ think_budget/edit_loop/run_pilot 接线(commit `5193ba2`);A 臂 suppress=None 与 baseline 逐字节一致;
  ② **【A/B 结果，32B ROME n=200/198，scope=think α=8】**ES@B3 0.495→**0.631**[.566,.697];**ES 降幅 B0→B3 0.106(显著)→ −0.035[−.111,.040](不显著=思考税消除)**；**RR(B3) 0.193[.126,.269]→0.085[.034,.136](砍半)**；CLR 0.545→0.263；**Loc 0.958→0.964(守门过)**；B0 与 baseline 逐字节同(对照干净)；
  ③ **【因果+修复双赢】**scope=think 只压【链】不碰【答案】生成,却使 RR 砍半、ES@B3 回升 +0.136、思考税消除 → **坐实"链内重推→答案回退"的因果**(干预链→答案改善,非仅相关)+ 一个 **training-free 修复**;Loc 不动(targeted, efficacy-only);
  ④ **【诚实校准】**ΔCLR(0.545→0.263)部分循环(scope=think 压的就是 cot 含 o_old)→ 不当主证据,主报 ΔRR/ΔES(在【答案】上、未直接压);残留 CLR 0.263 = paraphrase 旁路(v2 序列级 NoBadWords 可再堵,作消融);ES@B3>B0 在 CI 内 → 述"消除思考税"非"思考帮忙";
  ⑤ **【RQ3 安全门未竟】**Loc 过;**GSM8K/MATH 通用能力门仓里没有,需新建 src/genbench.py**(面板坑 #6)——o_old 不在数学题→penalty 不触发→预期 ~0 代价,但须量化才能 claim"不伤通用能力";
  ⑥ **【三腿齐】**RQ1=thinking 显著降 ES(capability-emergent,图1)+RQ2=机理(编辑完好被绕过/旧知识中段/链内重推,图2 logit-lens)+RQ3=链级抑制因果修复(表)。**下一步**:(a) 建 genbench 验通用能力门(RQ3 最后一块);(b) 可选 α 扫/scope=all/14B 复制/v2 序列级消融;(c) **开始写作**(abstract 7/20)。
- **v1.28 变更 (2026-06-24)**: **撞车排查 → 头牌重定 capability-emergent + 全面铺开补点/安全门/写作(含 compaction-proof 在飞快照)**——
  ① **【撞车排查,workflow w2gwkzie0,4 HIGH 已 WebFetch 核实】**现象(SCR He et al. 2505.18690 / ThinkEval 2506.01386)、非擦除机理(Superficial Editing Xie et al. 2505.12636)、training-free 修复(DISCO Sun et al. 2406.02882)各有强近邻已发表 → 原"现象+机理+修复"每块被占。详 `paper/related_work.md`;
  ② **【重定位,用户拍板】**头牌改 **capability-emergent**(各近邻独无);现象/机理/修复降支撑、按 §2 立界对标近邻;chain-only 因果(区别 DISCO 答案级)+ CoT 词边界口径作次级独有点。新标题见 `paper/outline.md`。**AAAI borderline,capability 是唯一稳的独有角度**;
  ③ **【capability 强化计划】**跨族跨规模曲线 = **Qwen 1.5/7/14/32B + Llama 8/70B**。补点 config 就绪:`probe_qwen1_5b.yaml`(v_loss27 layer5)、`probe_llama8b.yaml`(Llama-3.1 基座,v_loss31 layer6,首选 4090 bf16 或 H200 fp32 验不 NaN);**70B 待建**(model_parallel,模型下到 big disk `/inspire/qb-ilm/project/ai4education/public/whywhy/models/`,该盘 H200 已确认挂载);
  ④ **【RQ3 安全门】**`src/genbench.py`(GSM8K-200/MATH500-100,base 模型 suppress off/on 并集最坏界,门 |Δacc|≤0.02)→ 收 RQ3;数据 stage 命令见会话/genbench 注释;
  ⑤ **【写作基建】**`paper/outline.md`(capability 头牌)+`paper/results.json`(唯一图数据源)+`src/plots.py`(图1 capability/图2 logit-lens/图3 RQ3)+`paper/related_work.md`(§2+撞车);
  ⑥ **【★compaction-proof 在飞快照(2026-06-24,compact 后续跑刷新)】**▸平台 H200:**genbench 跑中**(完→score 贴回收 RQ3);▸联网实例:**Llama-8B + 70B 下载到 big disk**(70B ~140G);1.5B 在 hdd;▸后台 workflow **paper-draft**(原 wkqc5bb57 被 compact 杀、journal 空 → **已从 scriptPath 重起 = task `wuxajslri`/run `wf_c17725a9-ae0`**,8 章并行→缝合,完→我审红线落 `paper/draft.md`);▸**待回**:genbench Δ、Qwen-1.5B/Llama-8B score、paper draft;▸**已建(commit `244310c`)**:✅Llama-70B model_parallel config(`probe_llama70b.yaml`,跨卡 2×4/1×8,think_budget 用 model.device 无需改码)、✅plots.py 多族 fig1 + results.json capability→families 重构(stub 测三路径全过);▸**待我建**:无(新点回来后只需填 results.json families 再 `python src/plots.py`);▸**红线**:不宣称 scaling law / RR>0.20 / ΔCLR 主证据 / 首次发现(见各章 Limitations)。
- **v1.29 变更 (2026-06-24,compact 后续跑)**: **paper 全文初稿落地 + 写作/出图基建收口,主线只剩 GPU 补点回填**——
  ① **【draft 全文,commit `b…`/见 git log paper】**paper-draft workflow(被 compact 杀后从 scriptPath 重起 = run `wf_c17725a9`,9 agents/364k tok)产出 `paper/draft.md` = **Abstract×3 变体 + §1–§7 LaTeX 草稿**,唯一数据源 `results.json`,去污词边界口径;`paper/draft_review.md` = 缝合的一致性修正(9 处)/红线核验/[pending] 路线图;
  ② **【红线自查全清】**三危险红线(scaling law / RR>0.20 / 首次发现)grep 自查 → 全部仅出现在否定句(\"we do not…\")=合规;唯一溯源缺口(base_probe 0.59 此前无出处)已补 `results.json.base_probe.7B`{0.59/0.67/0.755};
  ③ **【基建齐,commit `244310c`】**`probe_llama70b.yaml`(model_parallel 跨卡 2×4/1×8,70B 单卡放不下;`think_budget` 用 `model.device` → 无需改码)+ `plots.py` 多族 fig1(1×3 面板每族一线,向后兼容 flat,stub 测三路径全过)+ `results.json` capability→`families` 重构(新点 append 即可);
  ④ **【主线现状】**RQ1/RQ2/RQ3 三腿齐 + 全文初稿 + 出图脚本就绪。**唯一剩余 = GPU 补点回填**:genbench Δ(收 RQ3 通用能力门)、Qwen-1.5B/Llama-8B/70B score(跨族跨规模曲线、破 7B Math 特化 confound)。回来后只需填 `results.json`(families/genbench)→ `python src/plots.py` 出图 → draft.md 去 [pending];
  ⑤ **【★在飞快照刷新(6/25 Llama 两 bug 修完→重跑)】**算力=两独立实例各 8 卡:**A=8×4090 联网/下载机(bf16 无 NaN)** + **B=8×H200 离线(fp32 防 Hopper NaN)**,共享 big disk。▸**genbench**:已完但存疑(最坏界 gsm8k Δ-0.15=union+scope=all 病态上界 + harness 欠测;面板 wjt97ozxo 裁定 RQ3=SURVIVE-WITH-REFRAME、§6/§7 已诚实改写、harness 已修 B3M/answer_cap/mode;部署口径门 [pending] 复测,低优先)。▸**⚠Llama 跑废一夜→已根治**:R1-Distill-Llama 两个静默 bug——① transformers 5.x Metaspace 删空格(`src/r1_tokenizer.py` 就地换 byte-level)② tokenizer add_bos_token=False 缺 BOS 致退化(`think_budget._gen` 手动补 BOS);diag 端到端验通(B0/B3 出 Paris、</think> 正常闭合);Qwen 不受影响。教训入记忆 [[verify-new-model-output-before-long-runs]]。▸**✅Llama-8B 最终点已锁(n=200,入 results.json)**:扫描(wf `ww9ij8hpf`,4格×n60)诊断坐实=借 Qwen `clamp_norm_factor=4` 对 Llama 过编辑致 Loc 0.67→**定 layer6/clamp2**(probe_llama8b.yaml 已改 tag cf200c2);n=200 复跑 = **ES降幅0.015/CLR0.340/RR0.144、Loc B0 0.835(恰在 0.85 线,bootstrap 噪声内)→诚实标 locality-marginal,不降 clamp 凑线(tune-to-threshold 已禁)**;跨族意义:通用 8B(CLR0.340)≈Qwen-7B-Math(0.335)同尺度→**erosion 非 Math 特化伪影**(头牌证据)。fig1 双族渲染验过。▸**70B→H200(2×4 fp32)跑中**,早停~50,score 回来 append 族`[8,70]`→`plots.py` 出跨族图1。▸**✅BOS robustness 已查清**:R1-Distill-Qwen 也 add_bos_token=False→旧 Qwen 7/14/32 实际无 BOS 跑出。BOS A/B(1.5B n=40,WHYAAAI_NO_BOS 开关):ON vs OFF 差 ≤1–2 case、ES降幅同(−0.025)、CI 大幅重叠→**BOS 对 Qwen 无材料级影响**=旧 Qwen 点有效 + 跨族不被 BOS 混淆(记 results.json `_bos_note`,论文 §3 注)。Llama 必补 BOS、Qwen 可有可无。▸(以下 6/26 已全部完成,见 v1.30)。
- **v1.30 变更 (2026-06-26)**: **★跨族 capability 曲线齐(6 点)→ 头牌数据全部就位**——
  ① **【跨族曲线完成】**`results.json.capability.families` 现为 **Qwen 1.5/7/14/32 + Llama 8/70**(6 点×2 族×1.5B-70B):CLR Qwen 0.209/0.335/0.475/0.545、Llama 0.340/0.524;RR Qwen 0.061/0.080/0.162/0.193、Llama 0.144/0.185;ES降幅两族都随规模↑(**只 Qwen-32B 0.106 显著**,Llama-70B 0.095 n=84 不显著)。**跨族对齐**:Llama-8B≈Qwen-7B(CLR .340/.335)、Llama-70B≈Qwen-32B(.524/.545)→ **erosion 随规模/能力涨、与族(Math vs 通用)无关 = 非 Math 特化伪影**(头牌跨族证据齐)。fig1 六点双族渲染验过。
  ② **【1.5B】**layer5/n196/`WHYAAAI_NO_BOS=1` 对齐旧 Qwen 口径;CLR 0.209<7B=低端更小。
  ③ **【70B 抢救】**model_parallel 2×4 fp32 下出现**间歇数值不稳**(部分 case 答案 ramble 成 717/Session 复读);`score_pilot --drop-degenerate`(长度无关检测:滑动4-gram<0.40 + 词复读>0.25)丢 6 条退化、留 **n=84 干净**。注:**第一版检测器有 length-bias bug(`len(set)/len<0.15` 误杀 verbose 长答案、假阳60-72%),已修**——用户两次正确质疑。干净子集指标有效、丢弃按处理序无偏。
  ④ **【BOS robustness】**Qwen/Llama tokenizer 均 add_bos_token=False;Llama 缺 BOS 退化必补,Qwen 鲁棒;A/B(1.5B n40)证 BOS 对 Qwen 无材料级影响 → 旧 Qwen 点有效、跨族不混淆(results.json `_bos_note`)。
  ⑤ **【✅draft 全文跨族化已落(wf `w4pb9ze1o` + 对抗核验,commit 见 git)】**`paper/draft.md` 现为 6 点跨族:§4 RQ1 重写(新表 + cross-family alignment + honest-scoping:只 Qwen-32B 显著、Llama-70B n=84 不显著)、Abstract×3/§1 更新、§2/§3/§7 同步(§3 补 BOS robustness + clamp + 70B drop-degenerate 口径;§7 trend-across-six-points + 7B confound 由 Llama 破)。对抗核验:数全对 results.json、红线全守(唯一 blocker Loc"above"→"below" 已修)。自查无残留 3 点单族 / scaling-law 正面 / RR>0.20 / 首次。▸**剩余低优先**:genbench 部署口径复测(harness 已修,RQ3 SURVIVE-WITH-REFRAME 不挡);出图 `python src/plots.py`(matplotlib 机上跑,fig1 已支持跨族多线);draft→LaTeX 主工程。▸红线:不宣称 scaling law / 逐对显著 / RR>0.20 / 首次发现。
- **v1.31 变更 (2026-06-26)**: **对抗审计(wf `wfgmaerr3`)定稿"投稿前必做"清单 + 修两处自证伪假陈述 + A2(α-sweep)就位**——
  ① **【审计裁定】**实验阶段**不能收**:头牌 RQ1 跨族结实,但 ES降幅仅 1/6 cell 显著、RQ2/RQ3 均单模型(32B)、genbench 安全门 [pending]=零通过证据。诚实天花板 = **weak-accept/borderline**(空间挤、4 强近邻分占现象/机理/修复;独有点 capability-emergent 跨族 + chain-only 因果 + native-R1 + 词边界=真 novelty 但统计功效最弱)。
  ② **【修两处假陈述,已 commit】**审计抓出 draft/results.json 两句与代码直接矛盾:(a) clamp"applied uniformly/not per-model"假——实为 8B=clamp2(扫描定)、70B=clamp4(默认),已改诚实陈述 + CLR 对 clamp∈{2,3,4} 鲁棒 0.31-0.33;(b) 70B 丢 6 case"按处理序无偏"假——`_is_degenerate` 是内容触发(长度无关 4-gram/词复读检测)、且退化即编辑失败→丢弃方向**有偏**,已改"须报 with/without 两版 + 稳定 Qwen/8B 上同检测丢~0"。**注:v1.30-③ 末句"丢弃按处理序无偏"即此被推翻的旧说,以本条为准。**
  ③ **【投稿前必做 4 件(堵 reject)】**A1 genbench 部署门复测(`--mode single --force_scope think`,32B,~1h,★最高杠杆/最低成本翻 RQ3 failed→verified)、**A2 α扫{2,4,8,12,16}+scope=all 消融**(32B,本轮就位)、A3 RQ2 链分类多判官填 §5(近零卡)、A4 Llama-70B n84→200(最贵~8-14h,撑最弱头牌锚)。强烈建议:B-emergence pooled 回归(ES降幅/RR×log-params slope CI 排零,零卡,钝化"仅1 显著cell")、B2 RQ3-14B 复制、B3 70B logit-lens、B1 MEMIT-32B、B4 zsRE。靠改文:primary 从 ES降幅 pre-commit 成 RR/CLR、causal 软化、matched-scale+RR 跨族~2×差披露。
  ④ **【✅A2 就位】**6 config `experiments/probe32b_a2_{th_p2,th_p4,th_p8,th_p12,th_p16,all_p8}.yaml`(各 n=100、仅 efficacy+locality 省半生成、tag `cf100sup_*` 不撞)+ 一键 `run_a2_h100.sh`(H100 fp32、错峰、可断点续、inline score)。α=0 基线复用 cf200(分析取前 100 case_id 配对、免再跑)。预计 ~6-9h。**算力升 3 实例**:8×H200 离线 + 8×H100 离线(6/26 新增,同 Hopper 须 fp32)+ 8×4090 联网(见 [[compute-situation]])。
- **v1.32 变更 (2026-06-26)**: **A3(RQ2 §5 链回退 taxonomy)基建落地 + draft 旧 3 分被对抗 panel 推翻重写**——
  ① **【taxonomy 定稿,workflow `wjrh3070w` 10-agent:5 视角→综合→3 压测→定稿】**draft 旧 `recall/bridge/dismiss` 三分**不成立**(panel 判 survives=false):recall/bridge 1:1 保留、dismiss 收紧为 **Reflective-override**(verbalize o_new→反思标记→同段 commit o_old;真回退中**罕见**,多数表面"but actually"链其实**护编辑**、被门控当 held 排除)、**必加第 4 类 Associative**(implicit-leak/ramble)才 collectively exhaustive(正是词边界 CLR 盲的桶)。+ 前置**门控**(short_code<4字/morpho 互变体/held commit-o_new/degenerate 全排除)+ 正交 **contests_edit** stance 单列。
  ② **【代码+测试齐】**`src/chain_classify.py`(prefeature/门控/3-判官聚合[多数决+3-way precedence]/Fleiss κ/§5 汇总表;judge prompt+schema 内置;7 mock 单测绿)+ `extract_reverted.py` 补 5 prefeature+3 stats(2 单测绿)+ `a3_judge.mjs`(判官 workflow,待数据即射)。
  ③ **【关键实测】**`extract_reverted` 在 4090 跑 cf200:**109 条 B0 编辑成功 → 17 条被 B3 推翻回退;全 17 条链内显式含 o_old(CLR),0 条 implicit-leak** → 32B 上 RR↔CLR 紧耦合、**无沉默式回退**(强化 RQ2:回退总伴随链内显式重述旧值)。Associative/implicit 桶经验为空仍保留(诚实+exhaustive)。
  ④ **【draft+results 同步】**`paper/draft.md` §5 taxonomy 段重写为 4 类+门控+contests(counts 仍 `[pending]`,n=17 小→低频类按定性存在性报、跨 editor/scale 池化);`results.json` 加 `rq2_taxonomy` 块。▸**剩余**:待 `data/reverted_32b.jsonl` 上传本地 → `chain_classify emit` → `a3_judge` workflow 跑 3 判官 → `aggregate` 填 §5 counts/κ。可选增强:14B/7B 回退链同法提取 → 三尺度 taxonomy(呼应 capability-emergent)。
- **v1.33 变更 (2026-06-26)**: **✅A3 完成 —— RQ2 §5 三尺度链回退 taxonomy 填实(7B/14B/32B,判官面板)**——
  ① **【判官跑完】**3-判官面板(workflow `wbhgnlufw` 14B+32B 84-agent / `wuq9wq97k` 7B 15-agent;读 RAW cot、strict precedence、必引 verbatim span)→ `chain_classify aggregate`(多数决/3-way precedence/Fleiss κ)+ `pool`。**门控 bug 已修**(原反思-loop guard `REFLECT.findall≥3` 误杀正常 churn 链、连 panel 范例 cf_9255 都排,改为只确定性排 short_code/morpho/真垃圾,held 交判官)。
  ② **【三发现】(committed cc103b0)**:(a) **Bridge 众数 pooled 17/19=90% [74,100]**——回退是【重构】(经命名中介/词源/地理/虚构推 o_old)非 flat recall;(b) **Recall=0 & Associative=0 全三尺度**——无纯记忆直取、无真 implicit-leak(7B 两条 clr=False 也被判 Bridge-via-spelling→回退总有可引推导子句);(c) **Reflective-override 仅 32B(2/10),7B/14B=0 → 该路径本身 capability-emergent**(须 engage 编辑值→质疑→override,小模型只表面线索 bridge)——**RQ2 直接呼应头牌能力涌现**。κ:32B 0.59 / pooled 0.52(7B/14B 全 Bridge→κ 未定义)。
  ③ **【口径副产】**held 排除多(7B1/14B7/32B6)= loose-RR(答案含旧)高估,**judge-committed 回退 n=19 pooled 贴近 strict RRs**;contests_edit pooled 15.8%。
  ④ **【落地】**`paper/draft.md` §5 填表(`tab:taxonomy` 7B/14B/32B/Pooled)+findings+§5 scope 改(logit-lens 仍 32B、taxonomy 跨 3 尺度);`results.json.rq2_taxonomy` 填实;`paper/table_rq2.tex`;`chain_classify` 加 `pool`+`latex_table`(+1 测,共 8 测绿);**reverted 链/verdicts/labels/summary 力保入库**(judge 产物不可廉价复现)。▸RQ2 从"[pending] 单 32B 定性"升为"三尺度定量+能力涌现二阶证据"。
- **v1.34 变更 (2026-06-26)**: **✅A1 genbench 部署口径门通过 → RQ3 安全门 failed→PASS(审计最高杠杆项收口)**——
  ① **【结果】**(committed 4c9032b)single o_old + scope=think + B3M=16384/answer_cap512(genbench 无 ROME 编辑→bf16 生成 NaN-safe→65G 单卡 H100 免 OOM,`run_a1_h100.sh`):**GSM8K off0.855/on0.860 Δ+0.005;MATH off0.700/on0.700 Δ0.000 → 均≤0.02 双双过门**。抑制器对非编辑通用能力近零伤害。
  ② **【印证截断伪影】**绝对值从最坏界 harness 的 GSM8K0.535/MATH0.150 **涨回 0.855/0.700** → 坐实旧低分=B3=8192 在 boxed 前截断的 harness 伪影、非模型弱(B3M=16384 解)。最坏界 Δ-0.15 正式降格为"病态上界",部署口径才是 operating regime。
  ③ **【落地】**`results.json.rq3.genbench` 填实(gate_pass=true);`draft §7` 四处 deployment-gate `[pending rerun]`/`[pending]` 全填(表注+主 collateral 段+limitations×2);残留 `pending rerun`=0。▸RQ3 三腿(answer-level RR/ES 因果 + chain-only + 部署安全)齐,安全门从"candidly failed 最坏界"升为"部署实测 PASS"。
  ④ **【在飞】**A2(α 扫{2,4,8,12,16}+scope=all 消融)在 **H200 单卡 fp32 数据并行**跑(`run_a2_h200.sh`;H100 因 32B fp32 130G>80G 单卡 OOM 折腾半天→H200 回归后走 headline 同款单卡路径绕开 model_parallel)。算力分工:A2→H200(fp32 编辑)、A1→H100(bf16 genbench),两实例并行不抢卡。
- **v1.35 变更 (2026-06-26)**: **✅A4 Llama-70B 做厚显著 → 头牌从『1/6 显著』升『2/6 跨族对称显著』(审计最大弱点堵上)+ A2 dose-response 5/6**——
  ① **【A4 头牌大升级】**(committed dddecf7)70B model_parallel 2×4 fp32 做厚 **n=84→200(丢 13 退化→n=187 干净)**:**ES降幅 0.107 [0.032,0.182] CI 排零=显著**(原 n=84 时 0.095 [-0.024,0.214] 不显著)。→ 现 **2/6 cell 显著=Qwen-32B(0.106)+Llama-70B(0.107)**,且两者是**各族匹配高端点、量级近乎一致(0.107≈0.106)=跨族对称**——审计"仅 1 个显著 cell"这条最大弱点实质堵上。生成肉眼人话(Mendel→physics/Mattick→Spanish),fp32 model_parallel 干净。其它 70B 值同步(es_b0 0.643→0.610、es_b3 0.548→0.503、clr 0.524→0.529、rr 0.185→0.175、loc 0.930)。
  ② **【draft 14 处一致重写】**(agent 改+独立 grep 核验)表+caption+§1+§2+§3+§4×6+§7×2+**三 abstract**:`only-Qwen-32B-significant`→`two-significant matched cross-family pair`;**ES@B0 诚实修**(70B es_b0 0.643→0.610 → Llama ES@B0 实为 ~flat 0.625→0.610 非升,改 non-decreasing-to-rising;thinking-tax scissor 仍立=B3 跌更狠 0.610→0.503)。保留全部诚实 caveat(RR CI 重叠/非 scaling law/consistency-not-causation/丢弃内容触发有偏 with-without)。残留陈词 grep 净。
  ③ **【A2 dose-response 5/6】**`results.json.rq3.alpha_sweep`:scope=think n=100,**CLR 单调↓ 0.545→0.444→0.384→0.268→0.146→0.082、Loc 全程平 ~0.958(守门跨 α 全稳)、ES 升后微降(峰 α≈8-12)**→ penalty=8 在 ES 峰附近非 cherry-pick;**th_p8(n=100)复现 headline suppress(CLR 0.268 vs 0.263/ES 0.639 vs 0.631)=跨 n 口径一致**。缺最后一点 `all_p8`(scope=all 消融)→ 到了填 §7 α-sweep `[pending]`。
  ④ **【审计四必做收口 3/4】**A1✅(RQ3 安全门 PASS)+A3✅(RQ2 三尺度 taxonomy)+A4✅(70B 显著)done;A2 5/6 在飞。**剩**:A2 收尾、可选 B 系(B-emergence pooled 回归零卡/B1 MEMIT/B2 14B-RQ3/B4 zsRE)、draft→LaTeX 主工程、出图 plots.py。诚实天花板从 weak-accept 上移(2 显著点+跨族对称+RQ3 安全门过+RQ2 能力涌现二阶证据)。
- **v1.36 变更 (2026-06-26)**: **✅A2 α-sweep 6/6 收尾 + ✅B-emergence pooled 回归(审计四必做全清 + 强烈建议第一条)**——
  ① **【A2 完成】**(committed 5ba6103)scope=think dose-response(α2-16,n100):**CLR 单调↓ 0.545→0.082、Loc 全程平 ~0.958(守门跨 α 全稳)、ES 峰 α≈8-12**→ penalty=8 非 cherry-pick;th_p8 复现 headline(CLR .268/.263、ES .639/.631)=跨 n 一致。**scope=all 消融**(α8):CLR/RR 可比但 **B0 ES 0.580→0.727**=在答案段直接压 o_old 写指标、失 clean 因果探针 → 坐实主报 scope=think。`results.json.rq3.alpha_sweep` DONE(+scope_ablation);draft §7 α-sweep `[pending]`→实测段(仅留 14B/序列级 paraphrase pending)。
  ② **【B-emergence,committed d57e9c3】**两族 6 点 pool 回归 erosion 对 log10(参数):**ES降幅 slope 0.095/decade [0.033,0.158] R²0.82、RR 0.081 [0.019,0.143]、CLR 0.218 [0.121,0.315] R²0.91 —— 三者 CI 全排零、bootstrap p(≤0)<0.002、族内同号、ES降幅跨族近乎一致(0.098 vs 0.098)**。→ 涌现有 **pooled-slope 统计支撑**、不靠 per-cell 显著(直接钝化"仅 2/6 cell")。诚实:trend-level、log-params 为能力代理(跨族 alignment 撑)、非 scaling law。`src/emergence_regression.py`(可复现+4 mock 测)、`results.json.emergence`、draft §4 新段「Emergence as a pooled slope」。
  ③ **【现状】**审计**四必做全清**(A1/A2/A3/A4)+ 强烈建议 B-emergence done。**剩可选**:B1 MEMIT-32B(第二编辑器)/B2 RQ3-14B/B4 zsRE(第二数据集)/B3 70B logit-lens(第二模型机理)= 扩广度;**写作收尾**:draft→LaTeX 主工程、`plots.py` 出图(fig1 跨族 6 点曲线/fig2 logit-lens/fig3 genbench 门/+ 新增 emergence 回归图、dose-response 图、taxonomy 表)。诚实天花板:从审计时 weak-accept 实打实上移一档(2 显著点 + 跨族对称 + pooled-slope 显著 + RQ3 三腿含部署安全门过 + RQ2 三尺度能力涌现)。
- **v1.37 变更 (2026-06-28)**: **战略转向:外部三审(Claude/Codex/DeepSeek)→ 深度提分(非广度)+ 堵最大洞 #1(因果对照)基建落地**——
  ① **【关键 recalibration】**三审收敛弱点:W1 因果只靠 logit-lens/干预缺对照臂、W2 依赖已知 o_old/疑似刷榜、W3 单跳、W4 仅 R1-distilled。**没有审稿人把广度(多编辑器/数据集/尺度)当 blocker → 广度=门票、不加分**;提分全在深度/效度。**⇒ 弃 B1/B4 等广度,转因果对照+鲁棒+多跳。**作战定稿见 `depth-plan.md`(10-agent panel `w536ljvnv`,infra 实核)。
  ② **【最大洞认定】**= **因果机理(论文脊梁)只靠单方法 + 无对照干预 → 读成相关/循环**(RQ2 logit-lens 单探针 + RQ3 干预无对照臂;死硬审稿揉成"压 o_old 的 logit→o_new 赢=同一 logit 事实两遍")。其它(W2 刷榜更可辩=洞#2;W1 已强=RQ1 不再是最大洞)。
  ③ **【洞#1 plug 基建 done,committed 2420cb8】**E-SUP-BATTERY 四臂(N/T/D/P,仅 `suppress.source` 不同):`edit_loop` 加 source 分支(o_old|o_new|placebo,默认行为不变)+ `placebo_donor.py`(BLIND 频率/长度匹配供体,21919 全±1 匹配,seed 锁,`data/placebo_donors.json` 入库锁定=预注册)+ `cross_arm.py`(跨臂按 case_id 配对差+bootstrap=headline 因果统计)+ 配置 D(压 o_new)/P(压 placebo)+ `prereg-esup.md`(预注册符号阶梯 D<N~P<T + 决策规则,见数前锁)+ `run_esup_h200.sh`。N/T 复用盘上 cf200/cf200sup。5 mock 测绿、回归绿。**全零卡完成**。
  ④ **【唯一 GPU 动作】**H200 跑 D(压 o_new)**先 n≈100 验符号**(符号错=近致命,最便宜先验)→ 方向对再跑满+P → `cross_arm` 出 T−P(o_old 超 placebo margin)。**诚实残余**(全做完仍在):不闭"自然生成里 route-around 必要性",limitations 明写。下一洞:W2(E-SEMJUDGE,零卡,需先重写判官 prompt 去偏)。
- **v1.38 变更 (2026-06-28)**: **✅洞#1 实质堵上 —— E-SUP-BATTERY 因果对照电池跑完、prereg 全中**——
  ① **【结果,committed b50d353】**4 臂 N/T/D/P(32B/CF/scope=think/α=8/B3,paper 口径)。**符号阶梯 D0.281<N0.495≈P0.507<T0.631(ES)如预注册**。三对照全中:**T−P 四指标全排零**(RR −0.095[−.171,−.029] / CLR −0.228[−.294,−.162] / ES +0.122 / RRs −0.057)=o_old 超 placebo floor=特异;**P−N≈0**(RR 恰 0.0 / ES p=.71)=placebo 惰性=非通用扰动;**D−N ES −0.217 显著负**=方向特异。→ RQ3 从"管用旋钮"升"符号/特异/剂量(A2 α-sweep)受控因果操控"。
  ② **【口径修正】**cross_arm 原用裸 hit(无 _without_subject 去污 + 无 b0ok 门)→边际 RR 0.414≠headline 0.193;已对齐 metrics.score(commit a7785ff),N/T 边际复现 headline(RR .193/.085、CLR .545/.263)。**符号结论不受影响**(去污/b0ok 跨臂同→配对差抵消)。诚实:placebo CLR P−N −0.05 p=.054 边际,被 o_old −0.276 碾压。
  ③ **【落地】**`results.json.rq3.sup_battery`(4 臂边际+4 对照 CI/p+verdict);`draft §7` 加「Causal specificity: a pre-registered control battery」段;`prereg-esup.md` 预测全中。
  ④ **【在飞/并行零卡 done】**审计三审深度三件已建基建:W1 E-SUP ✅跑完;W2 E-SEMJUDGE 中性判官基建 ✅(`revert_judge.py`,待平台 emit 答案样本→判官 workflow);W3 E-MULTIHOP 干净池 ✅(403,~100 informative,`mquake_curate.py`)+ 待 2-hop probe/hop-scorer/base-floor(下一步建);E-DECONFOUND LOFO/LOPO ✅(CLR slope 最稳)+ per-case 协变量待 GPU base_recall。**下一洞 = W2(emit 答案样本→判官)或 W3(建 multihop runner→base-floor 门)**。
- **v1.39 变更 (2026-06-28)**: **✅洞#2(W2 刷榜)实质堵上 + W3 多跳 runner 就位 + E-DECONFOUND 零卡半**——
  ① **【W2 E-SEMJUDGE done,committed c563279】**中性 3-判官(commit OLD/NEW/NEITHER,prompt 删 edit-intact 断言去偏;workflow wxl3p6hr7,n=87,33 条 rate-limited)vs 去污规则:**strict RRs(报的下界)κ=0.836/一致0.93/精度0.92=近乎一致→回退非子串伪影**;loose RR 精度0.48=按设计上界(判官证实高估),真回退在 RRs↔RR 之间=论文口径。eyeball 实例:cf_12856 Boston→Framingham(主体"Boston Beer"污染)判官正确 neither。`results.json.metric_validation`+draft §3 语义验证句+`src/sj_validate.py`(可复现)。诚实:判官同族 caveat。
  ② **【E-DECONFOUND 零卡半,committed 69e4500】**emergence slope 影响删除:**CLR slope 最稳**(每 LOPO 仍显著、drop-Llama 后 Qwen-only 仍排零 [0.12,0.40]);ES降幅/RR 方向稳但显著性靠跨族池化→坐实主打 CLR。draft §4 加诚实稳健性句。per-case 协变量(chain_len/base_recall)待 GPU。
  ③ **【W3 E-MULTIHOP runner 就位,committed 74221da】**`edit_loop` 加 hop probe;`multihop.py`(base 未编辑生成 hop_q+评 hits_new/old / gate 丢先验主导→信息残池 / score 编辑态 2-hop ES/revert/ES-drop;3 测绿);`mquake8b_2hop.yaml`(probes=[hop])+`run_mh_basefloor.sh`(Llama-8B bf16 单卡×8)。**H200 空 → day-1 job = base-floor 门**(403→丢先验尾~303→残池~100)→ 编辑态 2-hop。预注册三结局(更多/相同/无 erosion)。
  ④ **【洞进度】**W1✅(因果对照,prereg 全中)+ W2✅(刷榜,κ=0.84)实质堵上;W3 runner 就位待 GPU;E-DECONFOUND 半。**全 mock 单测 7 套绿**(chain_classify/extract_reverted/emergence/cross_arm/revert_judge/mquake_curate/multihop)。诚实残余不变(自然生成必要性,limitations 写)。
- **v1.40 变更 (2026-06-28)**: **W3 多跳设计加固(panel wq9e477xn 在 GPU 前抓出真问题)→ 编辑态待跑(干净池 150)**——
  ① **【base-floor 门跑完=272,但暴露污染】**未编辑 Llama-8B 在 403 干净 2-hop 上跑(806/806)→ gate 留 272,但 **77% 是先验/陈旧 gold 簇**(Trump 59=US head 的 **stale 2021 gold**、Galilee 72、Bethlehem 48、DC 30)。gate(基座输出含 gold 才丢)没drop 它们 = 基座不吐陈旧/具体 gold(说 Biden 或答不出)。
  ② **【panel 验出 3 个真 bug/问题,GPU 前修】**(a) `_score_one` 变音符漏检(Grabar-Kitarović≠…vic→**hop_answer_new 传播信号被低估**)+ 短目标(Lu,2字)裸词边界假阳(占池 21%)→ 修(NFKD fold + 短目标上下文守护,验过);(b) **退化-new 模板** P140 宗教 new-gold 塌成 Lu(57)/Epworth(48)=45% → `recut` 丢 → **272→150 多样残池**(P27 citizenship distinct_new=42 等);(c) 旧 `cmd_score` 用边际差估 erosion=错。
  ③ **【正确口径(实现+6 测绿)】**`cmd_score` 重写:**b0_prop 门**(编辑在 B0 传到 2-hop=答新且不旧=headline b0ok 的多跳镜像)上的 **propagation-erosion**(B0→B3 丢 hop_answer_new,配对 bootstrap CI)+ **{stays-new/flips-to-old/neither} 分解** + **per-template(relation)** + **陈旧 revert 仅次要括号**(不领先/不入 abstract)+ n_b0_prop<40 告警。估计量 = "编辑前向传播被思考侵蚀",非单跳 RR 克隆。
  ④ **【待跑 + 升级判据】**编辑态 2-hop:`run_mh_edited.sh`(Llama-8B **fp32** for Hopper ROME,跑 mquake_gated_clean=150)→ `multihop score`。**8B MVP;升 32B 仅当**:n_b0_prop≥60 跨≥4 模板 + 多样簇 hop_ES@B0>0.30 + 8B 显单跳-vs-2跳差(否则 8B 弱则报 8B 限制,32B 救不了)。报法:单跳 ES-drop 旁 多跳 propagation-erosion 同 edits 配对(panel 定);负结果=「编辑传到 2-hop 后思考没侵蚀→界定到单跳 cloze 局部」也有信息。
- **v1.41 变更 (2026-06-30)**: **✅洞#3(W3 多跳)实质堵上 —— 编辑态 2-hop 跑完、propagation-erosion 显著、与单跳同结构复现;32B 不升(预注册门未达)**——
  ① **【结果(Llama-8B/MQuAKE-CF,干净池 150)】**`n_b0_prop=48`(过 ≥40 门);**★propagation-erosion B0→B3 = 0.188 [0.083,0.292] CI 排零** → 编辑成功传到 2-hop 下游的 case 里,思考后约 19% 丢掉传播。分解 {留新 39/翻旧 1/都不 8}。per-template:**P27(公民→国家元首,最多样,n=57,b0_prop=27)= 0.148 [0.037,0.296] 排零=唯一 per-template 显著**;P495/P136 b0_prop≤8 欠功效含零。
  ② **【最强论点=与单跳同结构复现】**8B 单跳 within-case 回退 RR=0.144 [0.088,0.208] 排零、但边际 ES降幅≈0(ns);多跳 within-case 0.188 与之**同结构/同尺度/同族**复现 → erosion 触及编辑事实在推理链中的下游使用,**非单跳 cloze 表面伪影**(洞#3 的核心)。
  ③ **【三处诚实(写进 draft §3 + limitations)】**(a) **边际 hop_ES 反升**(0.32→0.513):B0=ZeroThink 无 token 做不了 2-hop,思考既补全未传播链(rescue)又侵蚀已传播链(erosion),净正→主报 b0_prop 门内 within-case(单跳同口径),不报边际=ZeroThink×多跳结构性非 bug;(b) **单模板主导**(P27 扛 pooled 显著);(c) **侵蚀去向='neither'(8/9)非翻旧(1/9)**=传播衰减为噪声,非旧事实复辟(与单跳显式翻旧区分)。
  ④ **【32B 去留=不升】**预注册升级门(n_b0_prop≥60 且 ≥4 powered templates)**未达**(48,仅 P27 有功效);within-case CI 已排零=功效够;边际反升是结构性、32B 也消不掉。**8B=有界深度结果(进 abstract 三件套);32B 多跳留 camera-ready/审稿响应**。回填:`results.json` 加 `multihop` 块、`draft.md` §3 加多跳鲁棒段 + §6 future-work 行降级(单跳 cloze 伪影已堵)。**W1/W2/W3 三洞全实质堵上**。
- **v1.42 变更 (2026-06-30)**: **进度盘点 + 全文 re-review 重排 → 第二轮深度计划(abstract 关键集 ≫ 原 A1-A3,几乎全零卡)**——
  ① **【DECISIVE 三件全 DONE】**W1(prereg 全中)/W2(κ=0.836)/W3(propagation-erosion 0.188)三深度洞实质堵上;全文初稿在册。盘点得失见本轮对用户总结。
  ② **【新 re-review(workflow `wa6rxz0qp`,3 审 borderline/borderline/weak-accept,raw=`rereview-round2.md`)】**对**全文**(非 abstract)新一轮对抗审。关键纠正:**最大残余被重定** —— 不是预命名的"自然生成必要性"(零卡可堵),而是 **title 名词「capability-emergent」的统计骨架**(唯一 fatal,2 审 threatens):`emergence_regression.py` 的 6 点 OLS p<0.002 来自 point-resample 同 6 点;fix=per-case 混合效应+family 随机效应,**零卡在盘数据上、abstract 关键**,原计划错放 7/27 GPU 窗后。
  ③ **【第二轮计划落 `depth-plan.md` §第二轮(当前权威)】TIER A 零卡/abstract 关键(7/20 前)**:1) E-DECONFOUND-NOW per-case 回归(拆 fatal);2) 自然生成 necessity 观察检验(用判官已抽 17/19 Bridge span,堵命名残余);3) CLR scorer-robustness 表(cutoff 3/4/5 per-scale);4) 70B with/without-13 敏感行进 Table 1;5) 免费文字 fix 打包(confirmatory-vs-exploratory+Holm/软化 RO-emergent/软化 o_old-specificity/标 W3 single-template pilot);6) A1 W4 scope+收紧 title 向"locate-then-edit on CounterFact";7) A2 部署门 TOST 等价界;8) A3 LaTeX+plots(fig2 带 g_l CI 带);9) RQ2/RQ3 非独立性 name-and-bound 段。**TIER B GPU 窗/全文 7/27**:B1 widen 池 17→40+per-case g_l CI;B2 E-CHAINSUB(破循环,camera-ready);B3 E-DECONFOUND GPU 半(base_recall)。**DROP**:广度充量/全套 W4 instruct/sibling 臂/tuned-lens-patching/8B 多跳模板扩充。
  ④ **【净】**所有 threatens_acceptance 项的 fix 几乎全零卡 → **7/20 前零卡冲刺可把 borderline 抬向 accept**;GPU 窗是全文加固非 abstract 阻塞。诚实残余 #1(必要性)由 action-2 从"未证"推到"自然文本 N/19 present 且抑制翻转"。
- **v1.43 变更 (2026-06-30)**: **Tier-A 立即项首批落地(ultracode 产出→对抗验证流水线 `wyd1uyje4`,8 agent)—— #1 拆 fatal 的代码 + #5/#6/#9 draft 措辞全整合**——
  ① **【#1 拆 fatal·代码就位】**`src/percase_emergence.py` + `src/test_percase_emergence.py`:per-CASE pooled 回归(每行=edit-case×尺度,ES降幅/RR/CLR ~ log10(params)+chain_len,family drop-one fixed-effect + **按 family 两级 cluster bootstrap**=重采样单位=嵌套 family 的 case,正面反驳"重采样 6 点";口径 import metrics 复用 `_without_subject`/`hit`/b0ok 门)。**自测 9/9 绿**(numpy-only;mutation-test 过;合成已知斜率 CI 排零、零斜率 CI 含零;对抗混淆 false-pos 2.5%<5%=反 6 点反保守)。审稿验证 agent **跑过自测 + approved**。**数字待平台 per-case jsonl 跑**;`results.json` emergence 块加 `_percase_replacement` 状态。
  ② **【#5/#6/#9 draft 整合】**3 文字交付全 approved(**无过度让步**、无硬矛盾、$ 偶/括号平衡):#5 四处免费 hedge(§3 confirmatory-vs-exploratory+Holm 注 / 软化 RO「appears only at 32B,consistent-with-not-establishing」prose+caption / §5 o_old-specificity→「meaningful competitor above inert-placebo floor」/ 多跳标 single-template pilot);#6 §7 加「Scope: native R1-distilled reasoners」段(不让步「any CoT」、点名 native-vs-prompted-CoT 判别控制)+ 头牌收紧「One locate-then-edit method (ROME) on CounterFact」+ 点名 MEMIT 复现为 future work(title 改名建议留用户拍板、未擅改);#9 §6 加「deeper non-independence RQ2/RQ3」name-and-bound 段(明确「not yet closed」、E-CHAINSUB 留 camera-ready 的滑窗保险)。
  ③ **【剩余 Tier-A】**待跑(需平台 per-case 数据):#1 出数、#2 自然生成 necessity 观察检验(用 17/19 Bridge span)、#3 CLR scorer-robustness 表、#4 70B 敏感行;待我本地做:#7 部署门 TOST、#8 LaTeX+plots、A3 出图。详见 `depth-plan.md` §第二轮。
- **v1.44 变更 (2026-06-30)**: **用户第一性 review → 战略 reframe 设计锦标赛(ultracode workflow `wzn1zgi5g`,8 agent)→ depth-plan §第三轮【当前权威】待用户拍板框架分叉**——
  ① **【触发】**用户做完第一性 review(Codex+Claude,`codex和claude的第一性review.md`):两审独立收敛 **头牌选错** —— 建议序 机理/修复 > 评测效度 > capability-emergence(草稿反过来)。两共识:CLR 是唯一铁结果却当 fallback(title 与铁证据错位=核心结构弱点);漏掉最高价值重构=x 轴改 knowledge-conflict/竞争先验(base-recall 0.59 只防御性引用)。
  ② **【锦标赛裁决】**4 套 reframe(KC/MECH/EVAL/MIN)→ 评委 **MECH>EVAL>KC>MIN** + 尸检(KC 在 base-recall null 不存活)。**★推荐=MECH-led 混合**:头牌机理/修复(abstract 全站已跑数据、零未跑依赖)+ EVAL 判官口径做脊梁 + capability 降推论(CLR 扛 + per-case 回归灭 n=6 fatal)+ **KC 留 Discussion 门控**(仅 base-recall×回退 7/27 跑强才升头牌)。**拒 KC-as-headline**(依赖未跑 + 被两在手事实反驳:taxonomy Recall=0/19、多跳侵蚀去向 neither 8/9 非 o_old);**拒 MIN**。⚠ novelty/priority 查重 agent 挂了→升 KC 前须补查。
  ③ **【NO-REGRET(fork-independent,记 depth-plan §第三轮)】**跑 percase_emergence(灭 fatal,本周)；软化 abstract/intro 四 over-claim(systematically eroded/driver/continuous-axis/causally-confirms/rules-out-erasure)；算术对账(0.595−0.495=0.100≠0.106 加注、line 159 within-Qwen CLR slope 0.22→**0.261** 误植 pooled)；RRs 进 Table 1;§7 RQ2/RQ3 非独立性命名。
  ④ **【用户决策点】**框架分叉(MECH-led 推荐)/title/7-20 前是否为 base-recall 烧 H200(推荐否)/E-CHAINSUB 是否现 name。**最大残余仍 = RQ2/RQ3 循环**(唯一破解 E-CHAINSUB=camera-ready)。**未落地 draft 改动**:等用户定框架再一次性整合(避免对可能被重构的 abstract 半改)。
- **v1.45 变更 (2026-06-30)**: **✅用户拍板 MECH-led → abstract/intro/contributions 全文 reframe 落地(产出失败转自写→3 镜对抗验证 approved)**——
  ① **【框架=MECH-led 已定】**用户从 4 选项选 MECH-led 混合(机理/修复头牌 + EVAL 判官口径脊梁 + capability 降支撑趋势 + KC 留 Discussion 门控)。
  ② **【执行·失败转自写】**front-matter rewrite workflow(`wrc1zmce9`)的 producer 撞 StructuredOutput 重试上限(巨型结构化输出,同前 novelty agent 毛病)→ 改**自写**:check-then-apply 脚本精确改 **14 处**(3 abstract 全 MECH-led 重写 + intro 标题/正文重排 + "rules this out"→n-bounded + "causal evidence"→signed/specific handle+necessity-not-closed + contributions 4 项重排[#1 机理修复/#2 非擦除/#3 capability 支撑趋势/#4 measurement] + figure 预览 + 6 处正文软化:continuous-axis→zero-vs-long、driver→consistent-with、within-Qwen CLR slope **0.22→0.26**[误植 pooled]+6 点 OLS 降描述性 per-case 标 load-bearing[pending]、causal-loop→consistent-with+bound、Table1 算术注)。
  ③ **【3 镜对抗验证 approved】**workflow `w7te8o9h6`:consistency+latex+numbers(全数对 results.json、$ 偶/括号平衡)/honesty(6 over-claim 全软化、未 under-sell、红线守)/MECH-fidelity(头牌确为机理修复、capability 确降支撑、KC 作 why、novelty hook 仍利)三镜全 approved 零 blocking。**修诚实镜抓的 2 因果散兵**(§2 "causally confirm"→intervention probes、§7 "the driver"→consistent-with)+ §7 中心句 mechanism-first + line151 "striking"→consistent+RR 低端分歧 + 2 cosmetic。残留 causally-confirm/the-driver = 0。
  ④ **【待平台/剩余】**percase_emergence 出数(灭 fatal 承重数,user 平台跑)+ RRs 进 Table 1(需 per-case);全文级:§3/§4/§5 节序仍 capability-first(节重排=更深全文活,未做、未阻塞)、fig floats 待 plots。abstract 当前 ~185-240 词,投稿前 trim 到 150。
- **v1.46 变更 (2026-06-30)**: **✅fatal 实质封死 —— per-case cluster-robust 回归(平台跑,run-2)CLR slope 在 honest family-clustering 下仍显著**——
  ① **【过程】**percase_emergence 平台首跑暴露数据污染(`1_5b`→5.0、`r1qwen32b_GENBENCH` 被当 32B 编辑分片、7B 缺)→ 代码层堵(commit fff07ad:黑名单 + 下划线小数点 + cell 守门 WARN + 数据驱动解读)→ run-2 干净(32B=CF、params 对、WARN 正确报 7B 缺)。
  ② **【结果(灭 fatal)】**两级 cluster bootstrap(重采样单位=case nested in family,K=2,非 6 cell-mean):**CLR slope 0.377 [0.141,0.800] p=.0012 排零**、**within-Qwen CLR 0.338 [0.029,0.665] p=.016 排零**;es_drop 0.036 [−0.036,0.138] p=.18 / rr 0.057 [−0.505,0.584] p=.41 **不显著**。→ **CLR 在 honest 推断下仍显著=『6 点 OLS p<0.002 是制造出来的』那个 fatal 被实质替换**;ES-drop/RR 不显著=正好印证 draft 既有『foreground CLR』。run-1 污染时 0.40 临界、修后 run-2 0.38 排零=稳健。
  ③ **【回填】**`results.json` 加 `percase` 块 + 更新 _percase_replacement;`draft.md` §4 重写"Emergence as a pooled slope":per-case cluster-robust 为承重(CLR 显著、ES-drop/RR 不显著)、6 点 OLS 降描述性companion(注明 overstates ES-drop/RR 显著性)、内 within-Qwen CLR 0.34。
  ④ **【残留·非阻塞结论】**⚠ 最终 6-cell 干净数待补:① **7B per-case 缺**(现 5/6 cells;Table 1 cell-mean 有 7B,per-case jsonl 待 user 在平台定位)② n 混(14/32/70B=cf100、1.5/8B=cf200,非全 headline n=200)。CLR 结论不预期翻转(7B 曲线中段)。draft §4 标 **[pending: 6-cell incl 7B + matched n=200]**。
- **v1.47 变更 (2026-06-30)**: **✅最终 6-cell percase(7B 进,无 WARN)+ CLR scorer-robustness 跑完 → fatal 彻底封死 + CLR 指标加固**——
  ① **【最终 6-cell percase】**user 在 `results/pilot/` 找到 7B → 加 glob 重跑(rows=1196,6 cells 全,无 WARN):**CLR slope 0.372 [0.149,0.800] p=.0007 排零、within-Qwen CLR 0.365 [0.062,0.675] p=.010 排零**;es_drop 0.033 [-0.037,0.139] p=.19 / rr 0.047 [-0.501,0.530] p=.43 不显著。5-cell 0.377→6-cell 0.372=稳健。回填 results.json percase 块(去 5/6-cell caveat)+ draft §4(去 [pending],填 6-cell 数)。
  ② **【CLR scorer-robustness(#3)】**`clr_robustness.py` 跑完(本地按 n_eff 加权聚合下载 json):**CLR 对 cutoff 3/4/5 每尺度差 ≤0.01**、**斜率跨 cutoff 全 +0.152**(灌水 substr 反更小 +0.131→去污不制造趋势)、**灌水因子 ~1.6–2.5×(均~1.9×)scale-invariant** → 审稿"cutoff 差异化缩小小模型 CLR 制造单调"被否。回填 results.json clr_robustness 块 + draft §4 加 robustness 句。修脚本 per-shard 聚合 bug(改按 (scale,family) 聚合原始计数)。
  ③ **【部署门】**4 处 "passes" → 有界 null(by-construction 为主、within-item TOST [pending 逐题 genbench]);commit 47aad1c。
  ④ **【仍待】**#2 自然生成 necessity(需 RQ2 判官 Bridge-span 输出位置)、配对 TOST(需逐题 genbench off/on)、plots.py、§3/§4/§5 节序重排。
- **v1.48 变更 (2026-06-30)**: **✅本轮收尾:#2 自然生成 necessity 跑完(本地 results/a3 判官链)+ TOST 完成(另一 session 写入 draft)**——
  ① **【#2 E-NECESSITY,src/necessity_check.py→results/necessity.json】**用 RQ2 判官权威标签(in_population)在本地 a3 判官链上做观察性必要性(未重跑/未干预):**19/19 自然 committed 回退全经可观察链内重推路由(Bridge 17/RO 2),traceless(Associative)=0 → 回退从不无声**;o_old 逐字现于链 17/19=89%。**充分性边界(诚实加分):held n=14 全部 clr_in_cot=True → o_old 现于链对回退不充分**,答案取决于链是否 commit。caveat:观察性非随机、n 小、held 判官采样(→'不充分'提示性、'无 traceless'更干净);不报 P(回退|clr) 裸对比(选择偏倚)。results.json 加 necessity 块。
  ② **【TOST 完成·另一 session 写入 draft,我不 clobber】**配对 McNemar:GSM8K b=1/c=2 of 200 → 90% CI [-0.009,0.019] **认证等价@±0.02**;MATH b=c=2 of 100 → [-0.033,0.033] **有界≤3pp**。draft 4 处已由另一 session 替换(Table caption/§6 collateral/§7 限制/§7 部署-scope);draft.md 工作树有未提交改动=该 TOST 文本,**保留待用户提交**。
  ③ **【用户战略指令】**先不做论文写作相关任务(prose/plots/节序);用户觉得工作还不够 solid → 下一阶段聚焦【更扎实的实验/验证】(见 depth-plan TIER-B:logit-lens 非回退对照+CI、E-CHAINSUB 中介把观察性必要性升随机因果、base_recall 协变量;及潜在 MEMIT 复现)。
- **v1.49 变更 (2026-06-30)**: **第一性 v2 solidity 双审(Codex+Claude)→ ultracode workflow `wqvzpvgm9`(21 agent)→ depth-plan §第四轮【当前权威作战序】**——
  ① **【代码级断言逐条核验】**两审的承重断言全核验为真:`chain_classify.py:25` taxonomy 判官 prompt 逐字预设结论("edit STILL INSTALLED/ROUTING AROUND/NOT recalling decayed weights/make NO claim edit weakened")而中性兄弟 `revert_judge.py:20` 干净=自伤污染(verified);logit-lens 重灌编辑+裸 cloze 无链单前向+b0ok 门+无 held 对照→edit_intact=1.0 近恒真(verified,甚至比所述更强);percase K=2 族 cluster bootstrap(partly,字面 0,K,K 数值等价);think_budget scope=think 答案段 lp=None=架构保证(verified)。
  ② **【收敛 7 弱点 W1-W7】**单点最弱(两审独立同点)=W1:taxonomy traceless=0/Recall=0/Associative=0 由被污染判官产;necessity 继承同源(`necessity_check.py` 直读 contaminated labels)。最强真承重=RQ3 链 fix(W7,架构保证)。Claude 独有 W5:整机理核=同一 n≈20 32B 池看四遍。
  ③ **【红队抓 4 致命 bug】**S5(E-CHAINSUB)provenance 反了(quoted_span 只在污染 chain_classify:57,中性 revert_judge 的 quote 从不持久化→破循环实验自身循环);S6(加宽池)`prefilter.py` 写死路径→覆盖 cf200 headline+全抑制臂;S9 删 edit_margin+CONFIRM 陷阱(within-Qwen 走私跨族 p);S1 precedence prime 需 ablation 臂。
  ④ **【排序+单点最高杠杆】**🔴7/20:S1 中性重跑判官(+1h 免费前筛=读 2/19 clr_in_cot=False 链,可零成本杀 claim)、S9-去Step2(within-Qwen 重框+6 尺度 base_probe)、S2-cheap(logit-lens reverted-CI 零卡半)、S10 的 α-sweep 重制。🟠7/27:S6 加宽池(修 path bug)、S5 E-CHAINSUB(修 provenance)、S10 14B 第二点。**单点最高杠杆=S1**;**7/20 只做一件=S1(先跑 1h 免费前筛)**。S3/S4 被 S9 吸收。诚实残余#1(自然必要性)仍无实验能闭=写 limitation。详见 depth-plan §第四轮。
- **v1.50 变更 (2026-07-01)**: **第三份第一性 review(增量实验)→ depth-plan §第五轮:补 §四漏掉的"现象是否编辑特异"维度 + 新单点最高杠杆 F1(盖过 E-CHAINSUB)**——
  ① **【1h 免费前筛已跑】**§四 S1 点名的最高杠杆 1h 动作:读 2/19 clr_in_cot=False 回退链(cf_7744 7b English←French、cf_1130 14b France←Italy)→ 都是**松散 forward-drift 桥**(非赤裸 traceless)→ "Associative=0/no traceless"**未被免费杀**、但中性去 prime 后很可能松动 → S1 值得跑。
  ② **【F1 premise 核盘为真=决定性】**`base_probe` 7B answer_old **0.59→0.67=+0.08 漂移** ≈ 7B 编辑 **RR 0.080**(已相等!);仅 7B、**32B base_probe 缺=全局最关键缺口**。若 32B base drift≈RR 0.19,头牌"thinking undoes **EDITING**"大半是基座动力学。F2(ZEROTHINK 空块/LESSTHINK_CANNED 未用)、F3(采样路径全建、零上报、draft §3.3 却宣称)、Cap1(chain_len 空白分词)premise 全真。
  ③ **【§五 整合 + 红队 F1】**写 depth-plan §第五轮(增量专章,严格定义=翻转/杀 claim 或补缺口):🥇F1/F2/F3(现象根基,§四漏);🥈M1(CLR-split 零卡杀修复因果)/M3=S1/M4/M5/V1(CLR-judge:κ 只验 RRs 没验 CLR scorer);🥉Cap1/Cap2/Cap3=S9;K1⊂F1/K2/G1;DROP 9 项复核认同。**红队 F1**:base 漂移不自动 kill——编辑态回退="丢 B0 装入的 o_new"(base 无 edit 可丢=不同事件),须报 effect-above-control margin(edited RR − base ΔP(o_old))近零才真塌。
  ④ **【7/20 增量冲刺(融合 §四+§五)】**F1-32B base_probe(补缺口)+ M1/Cap1/Cap2(纯本地零卡杀)+ M3=S1/V1(平台判官)+ F3(采样零 LOC)。7/27:S5(修后)/S6(修后)/M2/M4/M5/K2/G1。
- **v1.51 变更 (2026-07-01)**: **开工:M1 代码就位(杀修复因果)+ prefilter provenance guard(修 §四红队致命 bug)**——
  ① **【M1 E-CLRZERO-SPLIT,`src/m1_clrsplit.py`,selftest 过】**按基线 N 臂 per-case CLR∈{0,1} 分层重算 T−N 的 RR/ES/RRs(复用 cross_arm.per_case 同口径 _without_subject+b0ok 门)+ 2×2 中介(RR 在 CLR-未降 case 的改善率)。KILL:CLR0 分层上 T−N RR 降幅 ≈ CLR1(或 RR 在 CLR-未降 case 大幅改善)→ 修复不靠堵链→直杀「in-chain re-derivation governs the answer」。**本地无 sup_battery jsonl(在平台)→ 我写码+自测,平台零卡跑**:`python src/m1_clrsplit.py --arm N=... --arm T=... --budget B3`。
  ② **【prefilter guard,修 §四 S6 致命 bug】**`prefilter.py` 两个不同 dataset 共享 dataset.path 会静默覆盖 headline(毁 cf200+全抑制臂+RR=0.193 可复现)。加 `{out}.meta.json` provenance:tag 不同即拒绝(除非 --force),同 tag 重跑放行。验证:不同 tag 正确拒绝、同 tag/force 放行。**S6 加宽池现在安全**。
  ③ **【下一步】**写 `JUDGE_PROMPT_NEUTRAL`(=S1/M3 前置,修 chain_classify:25 污染)+ Cap1/Cap2 代码;平台跑 M1 + F1-32B base_probe。
- **v1.52 变更 (2026-07-01)**: **三线并行开跑:S1 中性重跑判官完成(in-app 99 agent)→ 部分 kill 一条 claim;F1(H200)/base_probe 6 尺度(H100)平台跑**——
  ① **【S1/M3 中性重跑=有增量结果】**去 `chain_classify:25` 4 句污染 + 去 Bridge-first 优先级 prime,3 判官重判同 33 链(`JUDGE_PROMPT_NEUTRAL`,emit --prompt neutral,全程本地+in-app)。**结果(results/a3_neutral,results.json rq2_taxonomy.neutral_rerun_S1)**:(1) **Recall 0→2**(14b cf_3883/32b cf_6933)= "no flat recall/Recall=0" **部分仪器制造、被证伪**→软化 contrib-2;(2) **Bridge 仍主导 81%**(vs 89%)=重构性回退核心存活;(3) **Associative 仍=0**="no traceless leak/回退从不无声"(necessity traceless=0)**去污后依然成立**(最要紧必要性 claim 扛住);(4) population 3/18 迁移 HELD(cf_1130/9994/7744,判官敏感)。净:核心存活、"Recall=0"死、诚实报敏感性。draft 改动清单已记 summary.json(待放行写作再改)。
  ② **【平台并行】**F1(H200,32B 未编辑 base_probe,现象是否编辑特异)+ base_probe 14B/8B/1.5B(H100,凑 6 尺度 base-recall 解锁 Cap3/S9 杀 capability)命令已给;M1(CPU 零卡)+ F3(probe32b_sample,排队等 H200)ready。
  ③ **【工作纪律】**用户定:能挂平台跑的先挂,平台跑时做本地活;增量 review(翻/杀 claim 或补缺口)是最高优先判据;暂不碰论文写作(数据落库可,draft prose 待放行)。
- **v1.53 变更 (2026-07-01,compaction-proof 在飞快照)**: **M1 强 CONFIRM 落库 + 三线并行在飞状态(compact 前快照)**——
  ① **【M1 = 强 CONFIRM 已落库】**`results.json rq3.clr_split_M1`:按基线 CLR 分层 T−N 修复效应——CLR1 基线 T−N RR **−0.289** [−0.44,−0.16] p=.0002、CLR0 基线 **+0.014** p=.72(≈0);2×2 RR 改善率 CLR-降 **43%** vs 未降 **4%**(10×)。→ 『链内容中介答案』**within-case 被证实**,直接回应"suppress 每步减 penalty 可能不管 o_old 就改道"的循环质疑(无链内 o_old 可堵时修复=0)。**硬化 RQ3,非 kill。**
  ② **【在飞·平台】**F1(H200,32B 未编辑 base_probe = 闸门):**✅DONE CONFIRM**——base P(o_old) 0.765→0.744 Δ=−0.021(不升反降),margin=0.214,编辑特异坐实、头牌存活(results.json base_probe.f1_edit_specificity;顺补 K1:32B base=0.765 替 abstract 误引的 7B 0.59)。 base_probe 14B/8B/1.5B(H100):**RUNNING**,凑 6 尺度 base-recall → 解锁 Cap3/S9 杀 capability。
  ③ **【在飞·待跑(等 H200 空,用户定 F2 直接上 32B 不用 H100 先跑)】**F2 ZEROTHINK 去混淆:**待我写 ~15 LOC**(think_budget 加 B0P=LESSTHINK_CANNED 臂 + [B0,B0P,B1] config;LESSTHINK_CANNED 已在 think_budget.py:26);F3 probe32b_sample.yaml:**ready 排队 H200**。
  ④ **【已完成本地】**S1 中性判官(rq2_taxonomy.neutral_rerun_S1:Recall 0→2 部分证伪 no-flat-recall、Bridge 81%/Associative=0 存活、pop 3/18 判官敏感;results/a3_neutral)、M1、prefilter guard、m1_clrsplit.py、JUDGE_PROMPT_NEUTRAL。**待写本地**:Cap1(真 tokenizer chain_len+CLR 密度)、Cap2(CLR 门真回退重测 slope)、Cap3(等 base-recall)、M4/M5、G1。**待放行写作**:S1 的 draft 软化清单(summary.json.draft_edits_pending)。
- **v1.54 变更 (2026-07-01,compaction-proof 在飞快照刷新)**: **F2 代码就位(commit `ff8cbc0`)→ 交用户上 H200;H100 已出 14b(等齐一起给)**——
  ① **【F2 = code-ready,待平台跑】**`think_budget` 加 **B0P** 分支(LESSTHINK_CANNED 固定假思考=非空但零推理内容,抽 `LESSTHINK_COT` 常量防漂移;B0P 链按构造不含 o_old → CLR≡0 对照锚)+ B0P mock 测(全 9 测绿,顺带修 `MockTok` 缺 `bos_token`——Llama 缺-BOS 修复后遗留、令整套 mock 变红)+ `experiments/probe32b_f2.yaml`(同 headline 32B ROME×CF,`budgets=[B0,B0P,B1]`,独立 tag **cf200f2** 不碰 headline;远锚 B3=0.193 复用 headline 不重跑)。**判读**:RR(B0)≈RR(B0P)≪B1 → 「无思考=编辑守住」非空 scaffold artifact、随推理**内容**单调=硬化头牌;B0P 跳 B1 量级 → ZeroThink 锚点是 artifact 须降级。dry-run 验接线过(budgets 流过、输出 cf200f2 独立文件)。
  ② **【在飞·平台刷新】**base_probe 多尺度(H100):**14b 已完**(等 8b/1.5b 跑齐,用户一起给)→ 凑齐 6 尺度 base-recall 解锁 Cap3/S9。F3 `probe32b_sample.yaml`:ready 排队 H200。
  ③ **【Cap1+Cap2 = code-ready,commit `808c3ed`】**做成 `percase_emergence` 两个新 outcome(复用两级 cluster-robust 回归):**Cap1** `clr_density`=链内 o_old 词边界次数(`metrics.hit_count`)/chain_len + `--tokenizer` 真分词选项(控 chain_len 后仍正 slope=能力真涨泄漏率、塌=只是链更长伪影);**Cap2** `clr_rev`=b0ok 门下 CLR∧RR(剔除"守住但顺带提旧"的 CLR,重测涌现 slope)。端到端测+hit_count 测+合成正/零 slope smoke 全绿;**真跑在平台**——复用 emergence 的 6 尺度 per-case 分片(`--glob` 同 percase),本地无数据只能 selftest。**Cap3** 仍等 base_recall 6 尺度齐(H100 base_probe)。
  ④ **【下一步】**用户上 F2(H200,32B fp32);Cap1/Cap2 待平台 6 尺度分片就位即可跑(与 percase 同 glob,Cap1 加 `--tokenizer $W/models/...-Qwen-32B`);Cap3 等 base-recall。
- **v1.55 变更 (2026-07-01)**: **base_probe 6 尺度齐 + 对抗验证 workflow(wz4rou8q3)纠出两个假支柱 → 净负但极有价值:capability-emergence-as-slope 只 CLR 显著且底噪共线,Cap3 从可选升必做**(commit `86aac44`)——
  ① **【F1 存活但收紧】**32B base P(o_old) 思考 Δ=−0.021(n=199),margin=0.214。skeptic#1 纠正:Δ 显著性【未知】(独立近似 SE≈0.043 上界),表述从"base 反向漂移"改"**base 无系统性漂移(Δ≈0)**",no-drift/微弱away-drift 两解读下 RR 都非基座先验伪影;**base ΔP(o_old) per-case 配对 CI 从可选升必需**。头牌『thinking undoes EDITING』held。
  ② **【纠偏#1:作废一个假支柱】**原 `_bonus` "base CLR 0.829 > edited 0.545 = 编辑压住 o_old" **作废**:分母错配(base CLR=`cot_old/n` 无条件全 n,`base_probe.py:63`;edited CLR_b0ok=b0ok 门,排除 B0 就答旧的 case)→ 0.545<0.829 是 artifact 非证据;要证压制须**同 b0ok 门跑 base CLR = Cap3**。方向上若真压低,反削弱"链是回退主渠道"(合 necessity held/多跳 neither)。
  ③ **【纠偏#2:涌现诚实】**`emergence.percase` 只 **CLR slope 显著**(0.372[0.149,0.800] excl0);**RR(0.047[−0.501,0.53])/es_drop(0.033[−0.037,0.139]) 均含零 n.s.**。→ 涌现-as-slope 唯一显著腿=CLR,而 CLR 与 base CLR 底噪(0.582→0.86)高度共线(r≈0.89)。**不能"降级 CLR 又称涌现稳"**;capability-emergence 维持 supporting-trend(**印证本轮 MECH-led 降级决策正确**),头牌压 M1 within-case + F1 change-control + 32B **cell-level** ES降幅 0.106[0.030,0.182]显著(≠per-case slope=单模型 bootstrap,仍成立)。
  ④ **【Cap 升级 + M1 边界】**Cap2(clr_rev slope)+Cap3(net-CLR=edited−base 同门 per-case slope + 回归 erosion~capability|base_recall)**可选→必做**=封 CLR 底噪共线的唯一路径(只 gate CLR 涌现叙事,不 gate 头牌);M1 gate 的是 RQ3 修复链中介@32B 单尺度,【不】背书 RQ2 跨尺度涌现(勿混)。base_probe 6 尺度 + 纠偏 + `_pending_draft_edits`(abstract 0.59→0.765 等,挂起不动 draft)已入 results.json。**待平台**:Cap1/2/3(6 尺度分片+base per-case)、F2(H200)、base_probe 8b/1.5b **已到齐**(1.5B/8B/14B 本轮落库)、70B base 未跑。
  ⑤ **【Cap3 = code-ready,commit `904c839`】**`src/cap3_netclr.py`(standalone,复用 `percase_emergence` 的 row loader + 两级 cluster-robust 回归):`load_base_clr` 读 `base_probe` 写的 `*_BASE_*` 分片(probe=base,B3 链)逐 case 出 base_clr/base_ans_old → `net_clr = edited_CLR − base_CLR ∈{−1,0,1}`(逐 case 配对,不 b0ok 门,与 percase.clr 同分母可比)→ 重估 6 尺度 slope + 两分层对照(clr_on_baseCLR0 = 仅 base 未泄漏 case 上 edited CLR slope、M1 式;clr_raw_matched)。**判读**:net_clr slope 排零且正=CLR 涌现扣 base 后存活;含零=raw 涌现大半 base 共线须撤(只 gate CLR 叙事)。selftest 两情景(edited≈base→含零 / base 平→排零)+ round-trip 全绿。**不用重跑 base**——`base_probe` 已写 per-case jsonl,平台跑法 `--glob`(edited)+`--base-glob`(`*_BASE_*`)。Cap1/2/3 三件本地全就位,待平台 6 尺度分片就位一次跑齐。
  ⑥ **【F2 = DONE CONFIRM,commit `faca346`】**32B cf200f2 greedy:RR B0 0.000 ≈ B0P 0.040 ≪ B1 0.208(B0→B0P +0.040 vs B0P→B1 +0.168)→ 『无思考=编辑守住』**不是空 `<think></think>` 模板 artifact**,RR 只在真推理内容(B1)时跳。ES 降幅 B0→B0P −0.090 含0/反向、B0→B1 0.130[0.060,0.205]显著。CLR:B0P≡0(判分器不误报 canned)、B1 0.465。bonus:B1 短链 RR 0.208 ≈ headline B3 0.193=erosion 早饱和。硬化头牌『erosion 随推理**内容**单调』。→ results.json `f2_zerothink_deconfound`。**剩平台**:Cap1/2/3(CPU)、F3(H200 采样)、70B base(未跑)。
- **v1.56 变更 (2026-07-02)**: **⚠抓到 glob 污染 bug(影响承重 emergence 统计)→ 加固 + cap12/cap3 现值作废待干净重跑**(commit `e21b67c`/`fd7eca1`)——
  ① **【污染 bug】**Cap1/2/3 首跑用宽 glob `*_ROME_cf*.jsonl`,`infer_tag_meta` 旧 denylist 不含 sup/scan/chk/test → 抑制实验(cf200sup)/layer扫(scanL*)/冒烟(h200chk/cftest)/BOS-AB(cf40_bos)被 `load_percase_rows` 的 (scale,case,budget) **last-write-wins** 覆盖进 cell。**铁证**:cap12 Qwen-32B `rr=0.092 ≈ RQ3 抑制值 0.085`(不是干净 cf200 的 0.193)——字典序 `cf200sup_r` 排在 `cf200` 后 → 32B 的 B3 被抑制实验数据覆盖。**记录版 `emergence.percase`(clr 0.372/es_drop 0.033/rr 0.047)同 glob → 同样污染,数值已挂 `_POLLUTION_WARNING` 作废**;v1.55③"只 CLR 显著"的结论建立在污染数上、已在 `_adversarial_verified.emergence_slope_honesty` 标【待重跑重判】。
  ② **【方向:污染=低估 erosion】**32B 被抑制数据污染 → es_drop/rr 被**压低**(clean 32B es_drop 0.106/rr 0.193 远强)→ **干净重跑后 es_drop/rr 涌现 slope 可能【复活】**(不再只剩 CLR 一条腿)。这把 v1.55 的"净负"部分翻回——涌现叙事可能比想的强。
  ③ **【加固】**`infer_tag_meta` denylist 加 `sup/scan/chk/test/_bos/cf40/cf60/cf200s`(headline `cf200/cf200c2/cf100` 保留);`load_percase_rows` 加"每尺度吃进 >1 dataset-tag"**告警**(未来污染大声报错);test 锁 9 拒 3 留,全绿。
  ④ **【下一步=干净重跑】**percase(修记录版 0.372)+ Cap1/2 + Cap3 用**显式 per-scale --glob**(1.5B/7B/14B/32B=cf200、8B=cf200c2、70B=cf100)重跑;cap12/cap3 现 json 作废。重跑回来才判:CLR 涌现扣 base(Cap3 net_clr)存不存活、es_drop/rr 涌现复不复活。
- **v1.57 变更 (2026-07-02)**: **干净重跑落库 → 涌现叙事反转变强:es_drop 涌现复活显著、CLR 涌现判为 base 伪影退役**(commit `e71bfff`)——
  ① **【bug 确认修复】**显式 per-scale --glob 重跑,32B 回到 clean(es_drop 0.106/rr 0.193/clr 0.545,污染时 −0.035/0.092/0.265),`tags` 每尺度单一、无混-tag 告警。
  ② **【★es_drop 涌现复活】**per-case slope **0.109 [0.036,0.175] p=.003 排零**(污染时 0.033 n.s.)。ES 降幅=真编辑侵蚀(丢 o_new)、base 无编辑可丢 → **构造上非 base 底噪伪影** = capability-emergence 最干净的承重腿。rr 0.644 p=.052 擦边、clr_rev(Cap2)同 0.644 p=.052、within-Qwen es_drop 0.119[0.042,0.198]显著。
  ③ **【Cap3 定论:CLR 涌现退役】**raw CLR(matched)slope **1.128**[0.825,1.468]强显著 → **net_clr=edited−base = 0.049 [−0.024,0.122] p=.093 含零**;逐尺度 net_clr≈平(1.5B −0.37/8B −0.49/14B −0.39/32B −0.29)=编辑 CLR 恒定低于 base ~0.38、gap 不随能力扩 → **CLR 涌现≈全由 base 底噪(0.582→0.86)共线,非编辑特异,退役为描述**。base_clr==0 子集 slope 0.654 亦含零(n=178)。Cap1 clr_density 0.0037 p=.0001 显著但未扣 base=suggestive。
  ④ **【净:比污染版强,翻回 v1.55 悲观】**涌现从"只剩 CLR 一条腿、还被 base 共线"→"**es_drop(真侵蚀、编辑特异)干净显著涌现**,CLR 退役"。capability-emergence footing 更稳(可能支持从 supporting-trend 上调,但 MECH-led framing 因新颖性/撞车另有理由,framing 待后议)。emergence.percase 换 clean 值 + emergence.cap3_netclr + 修正 `_adversarial_verified.emergence_slope_honesty`。
  ⑤ **【70B base 补齐(commit `96f3261`)→ 6 尺度 base 表全】**70B 答旧 B0 0.785→B3 0.810(Δ +0.025)、base CLR 0.905(全表最高)、ans_new≈0.01-0.02。原 `base_probe.70B` NOT_RUN 缺口关闭 → **F1 编辑特异覆盖全 6 尺度**(base 全尺度 Δthink 小、edited erosion 远强:70B margin=RR0.167−0.025=0.142)。base recall(0.515→0.785)与 base CLR 底噪(0.582→0.905)均随 scale 升(混淆原料),但 Δthink 全小=印证 erosion 非 base 动力学、70B CLR 0.905 最高=印证 Cap3『CLR 涌现=底噪伪影』。新增 `base_probe._six_scale_summary`(供 draft 表)。**gap 仅剩**:7B base 未进 cap3 net_clr(4 尺度;可补到 5-6)。
  ⑥ **【F3 = DONE CONFIRM,commit `c08e671`】**采样鲁棒性:32B cf200samp temp=0.6×seed{0,1,2}(n=600)+ greedy 对照。**ES 降幅 采样 0.090[0.010,0.171] ≈ greedy 0.110[0.035,0.185]**,均显著同量级 → 回退【不是单条贪心脆性】(中层近平局微扰即翻的质疑被否)。RR@B3 采样 0.264>greedy 0.208(采样更频=多样链更常重推 o_old,合机理);go/no-go RR≥0.20 两臂均过。greedy 对照(0.110/0.208)复现 headline=协议无漂移。堵 draft §3.3『声称做了没报』。→ `f3_sampling_robustness`。**→ §第五轮一梯队(F1/F2/F3/M1/Cap1-3/S1/K1)全清**;剩 V1(7/20 尾)+ M4/M5/K2/G1(7/27 二三梯队)+ 诚实残余#1(§四 E-CHAINSUB 自然必要性未闭)。**平台剩**:无在飞(F3 收尾)。
- **v1.58 变更 (2026-07-03)**: **终极写作前评审落地(`终极review.md`,已收进主仓)→ 7/3→7/27 日历级执行计划;此后一切行动以本表为准,B27–B33 永久 DROP 不回头**——
  **【判档】**weak accept 上沿、贴 solid 下沿。**上行至 solid**:(a) 零卡五件——★1(`_bonus_CORRECTED` 自错,三处同改)/★2(S1 off-by-one 重算)/B15(es_drop~base_recall 控制=**G 升格闸门**)/B16(零 GPU 机理池加宽 ~20→60-100+首个 Llama cell)/B13(F1 配对 CI+cap3 回填);+(b) B22(MEMIT 现象复制,需一 GPU 窗=**单点最高杠杆**)。framing **维持 MECH-led**,capability 升格条件式(B15 过才升并列第二支柱)。
  **【日历】**(死线按仓内 7/20 abstract/7/27 全文 UTC-12;CFP 亲核若坐实 7/21/7/28 只松不紧)
  ▸ **W1 证据窗 7/3(五)–7/7(二),零卡全清**:D1 7/3=B2(results.json 卫生 8 项含★1 三处)+B3(★2:S1 重算 17{14,2,1}/丢失条目 cf_6933@14b/s1_record.py 落库/7B κ=−0.091/table_rq2.tex 收敛)。D2 7/4=**B15**(升格闸门,两版 contrib 据此选)+B13(F1 配对 CI+cap3 7B 回填)。D3 7/5=**B16**(extract_reverted CPU 跑 F3-B3/F2-B1/8B/70B/1.5B 链→中性判官;【用户】所需 jsonl 回传)。D4 7/6=B8(V1 极性判官 ~40 calls)+B11(K2′ 分层)+B12(M5 零卡前奏)+B7(logit-lens n/口径补录)+周一查新。D5 7/7=收口(B4 换轨/B9 共享池披露/B20 caveat 素材入 results.json)+B22 预备(mom2+multi-layer yaml 就绪,窗口一开即跑)。**实验截止线①:7/7 后零卡新分析仅允许 bug 修**。
  ▸ **W2 写作窗 7/8(三)–7/14(二),解冻→初稿 v2+LaTeX 建仓**:7/8=解冻,第一件事 **B1**(涌现叙事倒置 L156/L158 全文一致性扫描)+B18-LaTeX 建仓并行。7/9=§4(主表+B5 统计表述+F2/F3+CLR 退役五句修正版+多跳边界句)。7/10=§5(taxonomy 中性版+B4 换轨+B16 新 n+logit-lens 两版预写)+§6(B6 软化+B17 RRs 纪律+B21 注记)。7/11=§1+§2(CRANE 立界+F 节定位句成品+alignment 文献带+relevance statement 草)+§3(预埋"ES@B0-matched"句)。7/12=§7 全项+abstract 三版+**图1 打磨日**(es_drop 主板带族内配对 CI+高端显著点高亮,RR 单调曲线作视觉承重副板;值一天)。7/13=B14 数字级修正逐条+[pending] 清零+口径扫描→**初稿 v2 冻结**。7/14=**内审红队轮①**(独立 agent 按评审 D 节 R1/R2/R3 攻)+**track relevance statement 拍板【用户】**+查新并入。
  ▸ **W3 修订→abstract 7/15(三)–7/20(一)**:7/15–17=内审修订+LaTeX 全文迁移完+图表终稿。**7/18=abstract 冻结(提前量 2 天)。7/19=abstract 提交(UTC-12 缓冲 1 天)**。7/20=官方死线(仅备用)。
  ▸ **W4 全文冲刺 7/21(二)–7/27(一)**:7/21–23=精修;**7/23=内审红队轮②**(新鲜眼最后一轮);**实验截止线②:B22/B23 结果 7/22 前出才写入正文,此后只进 camera-ready**。7/24–25=B18 后半(supplementary 打包+匿名化清洗+双盲检查+repro checklist+dual-use ethics)→**全文冻结 7/25。7/26=提交(缓冲 1 天)**。7/27=官方死线(仅备用)。
  **【GPU 窗策略】**窗口出现无条件插队 **B22**(MEMIT×CF 32B 首选/14B 备,multi-layer [4,5,6,7,8],n=200 B0/B3 只测 ES降幅/RR)→B23(logit-lens held 对照臂;无窗则文本降级两版已备)→B24/B25/B26。
  **【行政线·用户】**立即:①CFP 亲核(7/20 vs 7/21,影响全表余量)②OpenReview 注册确认③H200 窗申请(B22)。7/5 前:B16/B13 平台 jsonl 回传。7/14:AIA track 一次性拍板(不可转投)。每周一查新:7/6、7/13、7/20。
  **【DROP 纪律】**B27–B33 不做不提不回头;E-CHAINSUB=最大时间陷阱,维持 name-and-bound 到 camera-ready;17 天做减法。
- **v1.59 变更 (2026-07-03 晚)**: **卡时放开 → WINDOW 4 件+S10-lite 升必做;瓶颈改判=墙钟+传文件+写作窗;kill-risk 先上卡**——
  **【新 GPU 队列(按"堵的拒稿理由"排,全部 7/18 abstract 冻结前落库,7/25 硬底)】**
  ① **B22** MEMIT×CF 现象复制(32B n=200 只 B0/B3、只 ES降幅+RR;multi-layer [4,5,6,7,8] 防 S7 单层退化;前置 mom2-32B 单进程预热 RUNBOOK §3;不可行降 14B)→堵 R2。② **B23** logit-lens held 对照臂+per-case CI+未编辑 base 同 case gap 曲线(~20-40 case;null 也是收益=主动降级为安装 sanity)→堵 R3。③ **B24/M4** 强竞争者 placebo C 臂(同 relation 强错误答案,n=200)→堵"压任何强竞争者都行";**有 kill 风险**。④ **S10-lite** 14B 抑制 T 臂(scope=think α=8 n≈200;N 臂已在盘 RR 0.162;**prereg 主端点=ES@B3**,不钉脆弱 b0ok-RR)→堵"修复是 32B 单点"。⑤ **B25/G1** cond-c 盲区(8B mh2hop+抑制器开到 hop probe,~40 LOC)→堵"zero collateral 有部署门看不到的侧面";**有 kill 风险**。⑥ **B26** genbench TOST 加 n(末位顺手)。
  **【上卡顺序约束】kill-risk 先行:③M4+⑤G1 最先**(结果改措辞,晚了变写作期炸弹);①B22+②B23 随后(结果只会更硬/更诚实);④S10-lite/⑥B26 插空。零卡件(B15/B16/B8/B11/B13)仍第一优先照 D2-D4 走,与卡时无关。
  **【即使卡免费也不复活】**B27 E-CHAINSUB(瓶颈=provenance bug+设计自循环,非卡)、zsRE/AlphaEdit(MEMIT 后平坦区)、32B 多跳(预注册升级门未达)、prompted-CoT(工程量+双向预认)。
  **【本轮备货(见后续 commit)】**M4:placebo_donor `--mode strong`(同 relation 供体,BLIND seed 锁定入库=prereg)+`probe32b_sup_strongcomp.yaml`;G1:edit_loop suppress `apply_to` 配置(默认 [efficacy] 保持现行为)+`mquake8b_2hop_sup.yaml`;S10-lite:`probe14b_sup.yaml`(prereg 头注);B22:`memit32b.yaml`+mom2 预热命令;B23:logit_lens held+base 扩展。
  **【批1 结果(7/3 晚,commit `4a5b271`)——kill-risk 两件全过,无写作期炸弹】**①**M4 CONFIRM**:C≈N≈P(ES 0.510/RR 0.208 vs N 0.495/0.193)而 T−N=+0.136/−0.108 → o_old 特异性以最强对照坐实;五臂图齐(T 修复/D 反伤/P 惰性/C 惰性)。②**G1 无 kill**:hop_ES@B3 0.487 vs 无抑制 0.513(−0.026 噪声级)、erosion 点估 0.188→0.104(CI 重叠)=修复在多跳上方向为保护;B0 sanity 完美。③**S10-lite CONFIRM**:14B T−N 主端点 ES@B3 +0.135、RR 0.162→0.086、税转负——逐项镜像 32B → 修复跨尺度成立(M1 中介仍限 32B)。④**B22-32B FAILED**:200/200 error 行,待 grep 诊断(mom2/OOM/hparams 待分);`memit14b.yaml` 降级预案启用。**剩**:B22 诊断+重跑(32B 修得动就修,否则 14B 定案)、B23 备货(logit-lens held)、B26 末位;配对 CI 补跑(cross_arm C−N/14B T−N)。
- **v1.60 变更 (2026-07-03 深夜)**: **Anthropic workspace/J-lens 方法论进口(用户拍板)→ W 系列三实验(bounded side-quest,kill date=7/14 内审)+ 故事框架升级(结构不动)**——
  ① **【W-A·无声工作空间泄漏探针】**扩 `logit_lens.py` 到**链位置×逐层**(o_old/o_new 表征 rank/logit;排除"复制效应"位置):(a) CLR=0 链里 o_old 表征中层 spike?=**非循环 traceless 检验 → 攻诚实残余#1**(E-CHAINSUB 的替代,评审判 7/27 闭不了的洞);(b) 回退链里 o_old 表征**先于首次言语化**升起?(=workspace 论文 rhyme-planning 同款);(c) **吞掉 B23**:held 对照臂 + 未编辑 base 同链 teacher-forcing = W-A 子集。单卡 H200,~100 前向,小时级。
  ② **【W-B·工作空间级抑制(表征级修复)】**`steer.py`(ThinkEdit 复现,带位置掩码,现成)+ `extract_direction` 抽 o_old 概念方向,链生成注入 −α·v = **压概念非压字面**:M1 升概念级因果中介 + 免疫别名/改写绕过的第二 training-free 修复(=原 plan F1 steering 方案复活)。判读 ES@B3(steer) vs N/T;须测 Loc(方向可能伤旁邻)。
  ③ **【W-C·"编辑住在工作空间下面"实测】**W-A 数据免费出:o_old/o_new 可言语化 onset 层带 vs 编辑层(12/64≈0.19)→ 新故事承重钉从叙事变实测。
  ④ **【故事升级(结构不动)】**MECH-led/章节序/G 节裁决不变;机理解释框架升级为「编辑写进自动通路,思考路由进工作空间,工作空间重推旧世界,答案跟工作空间走」——§1 hook/§5 解释层/Discussion 理论对接;F2(B0P≈B0)/M1/链级修复 = 三个行为学签名。引用前逐节复核原文(analysis/10)。
  ⑤ **【纪律】**kill date 7/14:届时不干净整体降 camera-ready,写作照旧;写作窗(7/8 解冻/7/18 abstract)不动;全 J-lens(千-prompt Jacobian)不做;W 系列=加法臂非承重墙。红队 workflow 先审设计(复制效应/方向伤 Loc/base 对照口径)再写码。
  ⑥ **【红队裁决落盘(`w4cxg65vd` → `prereg-wseries.md` 冻结版)】**4 个 fatal 全修入设计:(a) **原 W-A(a) traceless-回退检验总体≈空**(Associative=0/17、held 14/14 含 o_old)→ 主总体重铸为 B3 全体 string-CLR0 链(claim=言语化是门控),CLR0∩回退只报 n、n<5 声明不可答(算干净);(b) **复制效应/induction 头灌水** → token-id 级排除规则 + 20-distractor 置换 max-stat 校准(精确 p=1/21);(c) **W-B 方向抽取 o_old-vs-o_new=把答案写进残差流** → 改 o_old-vs-中性语境 + 对 W_U[o_new] 正交化 + P_shuf 臂(M4 C 臂表征级同构)+ LocAcc 共主伤害端点(旧 Loc 对概念抑制全盲);(d) **`steer.py:52` mask 失配静默全局注入** → on_mismatch 显式化 + 答案段零 hook 断言 + 两单测。效度门 G1–G7;层索引 off-by-one(编辑层 12↔hs[13])钉死。**④修正:§1 hook 维持现象主导,workspace 只进 Discussion(cite-as-frame)+ §2 立界行**(红队判 §1 workspace hook=借壳观感,砍)。零卡前置:`src/wa_census.py`(平台跑出 A1 的 n → 回填 prereg §2-A1)。下一步=按 prereg 写 W-A 探针 + W-B steer 修(7/8 24:00 冻结)。
  ⑦ **【W 系列工具链齐(7/7;在飞快照)】**W-A:`wa_probe.py` 8 卡分片版+distractor 池修复(歧义只判空格变体+跨 relation 回填,200/200 满 20,commit `0e12175`);冒烟 **G3=0.964 过**(teacher-forcing 保真成立=可行性开关开)、G2 过、显存 OK;**edited 态 8 卡在跑**,base 态随后。W-B:`steer.py` 静默注入修死+`generate_with_budget` steerer 通道(7/7 测全绿,`5116c20`)+`wb_steer_arm.py`(方向抽取 G7 门+正交化+S/Pshuf/Splus 臂,`3752573`)。**剩**:W-A base 态跑+离线分析脚本(A1 Wilson/A2 MW/A3 Δz/C1 onset,我写);W-B extract→pilot(α 扫 1/2/5,n=30)→确证;7/8 24:00 prereg+代码冻结;7/14 内审裁决。
- **v1.61 变更 (2026-07-07)**: **写作前冲刺定版(双 8×H200 节点)——严格照此执行到 7/8 写作解冻,W 系列到 7/14 裁决**——
  **【节点分配】**▸**Node-1(W 系列线)**:①W-B extract(base 方向抽取,今晚起,**立即开跑**——band 只影响 run 不影响 extract)→②pilot α∈{1,2,5}(S 臂 n=30,G7 报告先看)→③我按 prereg 选 α*→④确证 S/Pshuf n=200(band=W-A onset 带,fallback 20-44)→⑤C3 双臂(in-band vs below-band,n≥100)。▸**Node-2(收尾线)**:①32B-MEMIT 重试(expandable_segments+3 层 [11,12,13];成=补 32B 行,败=14B 定案已够)→②B26 genbench TOST 加 n(末位)。
  **【零卡必做(我,7/7-7/9;v1.58 W1 被 GPU 窗口挤掉的欠账,评审"证据侧最高优先")】**①**B15** es_drop~base_recall per-case 回归(**G 升格闸门**;脚本我写,平台 CPU 跑——base *_BASE_* per-case 在盘)②**B13** F1 配对 CI+cap3 7B/70B 回填 ③**B16** 池加宽(extract_reverted CPU→中性判官 workflow 本地)④**B8** V1 极性判官(~40 calls 本地)⑤B11 K2′分层 ⑥B12 M5 零卡前奏 ⑦B7 logit-lens 记录补录。
  **【W-A 收尾】**两态已跑完;**jsonl 回传本地**(results/wa/*.jsonl)→ 我写 wa_analyze.py 出 A1(Wilson+binomial>4.8%)/A2(MW)/A3(Δz 配对)/G3-G5 门 + onset 带(喂 W-B band)。⚠已知缺口:G5 的 distractor 前窗 max 未存盘 → G5 操作化为 z_pre band-max vs 同 case S_d_max(保守),在开盲前写进 prereg。C1 的 onset(o_new|cloze) 未在 wa_probe 实现 → W-C 封顶描述档(prereg 允许,不算脏)。
  **【时间线】**7/7 夜:W-B extract(Node-1)+MEMIT 重试(Node-2)+jsonl 回传;7/8:wa_analyze 出数+α pilot+B15/B13;**7/8 24:00 prereg+代码冻结**;写作照 v1.58 解冻(7/8 起,B1 第一件,与 W 系列并行);7/9-7/10 W-B 确证+零卡余项;7/11-13 分析;**7/14 内审裁决(W 系列去留+track 拍板)**。写作窗一天不让。
- **v1.62 变更 (2026-07-07 晚)**: **终极推进计划(此后只进结果、不改计划;任何偏离先改本条款再动手)**——
  **【两决断】**①**W-B 死刑定谳**:接受 G7 pre-registered kill(pair_cos~0.3,200/200 fail;commit `fbc9077`),不做第二轮迭代——更稳抽取法(mean-over-K-neutrals/trained probe/J-lens)留 camera-ready 另立 prereg。连带 **W-C 的 C3 因果臂死**(依赖 W-B 方向)→ W-C 封顶描述档或撤,7/14 按 prereg 裁。②**GPU 收工线**:Node-2 完成 32B-MEMIT 重试+B26 后 GPU 全停;7/26 前不再立新 GPU 实验(评审"平坦区"纪律)。剩余瓶颈=分析+文字。
  **【日历(硬)】**▸**7/7 夜-7/8**:W-A jsonl 回传→我写 wa_analyze.py 出 A1(Wilson+binomial>4.8%)/A2(MW)/A3(Δz)/G3-G5 门;B15 脚本(es_drop~base_recall,**升格闸门**)平台 CPU 跑;**7/8 24:00 W 系列冻结完成时点作废改为"W-A 分析口径冻结"**(代码已冻,W-B 已亡)。▸**7/8 写作解冻**(v1.58 不变):B1 第一件;**叙事按今日定版**——组织句「编辑修补自动通路,深思重推世界」开篇;证据阶梯(现象→相关→干预→部署)结构;**F2 升格为 automatic-vs-deliberate 解离主角**;仪器诚实节(κ/中性判官/0-17 宽口径普查/W-B G7 负结果一句);workspace 只进 Discussion cite-as-frame+§2 立界(C6 禁词表执行)。▸**7/9-7/10**:零卡欠账清完(B16 池加宽+Llama cell、B8 V1、B11、B12、B13、B7)+§4-§6 初稿。▸**7/11-7/13**:§1/§2/§3/§7+abstract 三版;7/12 图1 打磨日(es_drop 主板+RR 副板);7/13 初稿 v2 冻结。▸**7/14 内审红队①+W 系列裁决+track 拍板【用户】**。▸**7/15-17**:修订+LaTeX 迁移完+图表终稿。▸**7/18 abstract 冻结;7/19 提交**。▸**7/21-23**:精修;7/23 红队②;**7/22 实验写入截止**(B22-32B/B26 过点只进 camera-ready)。▸**7/24-25**:supp 打包+匿名化+checklist+ethics;**7/25 全文冻结;7/26 提交**。
  - **v1.63 变更 (2026-07-07 深夜,用户指令:卡时无限+双 8×H200 常驻)**: **撤 v1.62 GPU 收工线 → 常驻 GPU 队列(全部 Anthropic 方法系、带门、结果只在检查点看);写作日历/冻结点一字不动=真不变量**——
  ▸**Node-1 = W-B 第二次也是最后一次 prereg 尝试**:抽取改标准 diff-in-means(减数=**K=8 个中性实体均值**,同套跨模板;修单中性减数方差压低 pair_cos 的问题)。**硬边界:G7 再 fail(pair_cos med<0.6 或剔除>20%)→ 永久死,无第三次**;过 → pilot α{1,2,5}(7/9)→ 确证 S/Pshuf(7/10-11)→ 7/14 裁决。过则 W-C C3 因果臂复活。
  ▸**Node-2 = W-A 扩展梯(wa_probe 复用,零新统计口径,prereg 扩展节登记后跑)**:①**W-A×F3 采样链**(n≈597,A1 的 CLR0 总体扩 ~3×=最大功效增益)②**W-A×MEMIT-14B 链**(跨编辑器表征签名=机理普遍性)③W-A×14B ROME(尺度点)④W-A×Llama-8B(跨族)。各自 distractor 池 CPU 建。
  ▸**注意力协议**:结果只在每日两个检查点(早/晚)贴给 Claude;写作(7/8 解冻,B1 第一件)不因 GPU 中断;**7/22 写入截止不变**,过点只进 camera-ready;MEMIT-32B 重试/B26 照旧插空。
  **【v1.63 在飞快照(7/7 深夜)】**W 系列数据全收:W-A 主分析完(A2 干净 null+G5 100%=表征在场≠回退分岔在承诺层;G4 fail→A1 不可判;A3 绕过说;commit `39ca2e9`)+扩展梯四级完(采样入池/ROME 压制 vs MEMIT 保留分化/8B 部分压制)。W-B:G7 PASS→pilot α*=1%(N 臂 LocAcc 基线实测 0.625,α=1% 掉幅≈0.5pt 过伤害门,`ccebabc`)→**确证臂 S/Pshuf n=200 在 Node-1 跑**。32B-MEMIT:Node-2 无官方数据集挂载(mom2 wikipedia 读不到,ConnectionError)→**排队 Node-1,W-B 确证完接跑**(WHYAAAI_WIKI_PARQUET 指挂载点)。待:W-B 确证出数→cross_arm B1/B2 端点;7/8 写作解冻(B1 第一件+B15);7/14 内审裁决。
- **v1.64 变更 (2026-07-08)**: **证据面关账 —— 终极评审 solid-accept 上行清单全清,唯剩 B26 过夜分;此后=写作**——
  ①**零卡五件+扩展全清**:★1★2(105faea/f23552e)、**B15 PASS 升格闸门**(控 base 后 slope .0992 p=.0041 不动,`abaaf5c`;分层=燃料/引擎)、**B16 池加宽 17→50**(7 cell/2 族,Bridge 68%/Recall 22%/RO 8%/Assoc 1 分裂票=几乎从不无声,`0fe865a`)、B13(F1 配对 CI airtight Δ=−.020[−.080,+.040] + cap3 六尺度确认退役,`90d859a`)、B11(K2′ KC 主导 25% vs 3.2%+confabulation 注脚)、B8/V1(CLR 极性假阳 paper 口径≈6%,`3e4eed6`)、B12(反思=常量非变量,M5 GPU 臂维持 DROP)、B7(logit-lens 权威 n=23/intact 100%/峰值 decoder 58,`15b4cc0`)。
  ②**W 系列全收官**(W-A 主+四级扩展/W-B G7-pass→确证 B1-FAIL=承诺层 dissociation/W-C 描述档);**B22=14B 定案**(32B 双故障不可行);**批1-2 GPU 全清**(M4/G1/S10/F2/F3)。
  ③**在飞仅剩**:B26 过夜分(/tmp/b26.score)→ TOST 落库。**待办=纯写作**:B1 第一件 + `_pending_draft_edits` 26 条带数字指令(v1.65 归一后计数;原记 21 为错) + LaTeX(B18)+ 图1 + 7/14 内审(W 系列去留裁决+track 拍板【用户】)。写作日历不变:7/13 初稿冻结/7/18 abstract 冻结/7/25 全文冻结。
    **【camera-ready 备忘(7/26 后才碰)】**J-lens 正式版、W-B 更稳抽取、W-A 法扩到自然必要性闭环(E-CHAINSUB 非循环替代)、M1 跨尺度、B23 held 臂正式统计。
- **v1.65 变更 (2026-07-08)**: **gap-review 必1 执行——写作前队列归一 pass + 写作期取数纪律**(独立终审 `gap-review.md` top-5 第一件;cherry-pick d0ba39d 落仓)——
  ①**三处跨源冲突坐实并归一**(每处曾是 ★1 式双源分叉雷):(a) contrib-2 headline 冲突(S1 '~81%' vs B16 '68%')**当场裁决=50-池 68% 主口径、17-池中性 82.4% 伴报一句、不混池**;(b) `neutral_rerun_S1.draft_edits_pending` 4 条并入 `_pending_draft_edits`(#1/#2 标 superseded-by-B16、#3/#4 存活)+ S1 块加 `_draft_edits_status` 存档指针;(c) 旧顺手补 3 真无家项(B13 F1-airtight/B12 反思常量/**W 系列占位条**)。
  ②**W 系列占位条=防错写**:明写「内容待 7/14 内审裁决」+【禁】勿按 v1.62 'W-B G7 负结果句' 写(已被 G7 二跑 PASS 事实推翻;真负结果=确证臂 B1-FAIL dissociation)+ 钉死 W-A 诚实数字(G5 100%/A2 null perm p=.487/A3 含零/G4 fail→A1 不可判)+ W-B appendix 三臂行——写作 session 只读 pending 即可,不漏 7/3 后最大一批新证据。
  ③**顶层 `logitlens` 块加 `_superseded_by` 指针**→ `rq2_logitlens._authoritative_record`(并顺手植入 硬伤2:layers_sampled 是 hs 索引、负 gap 带真值=decoder 7–11 在编辑层上游,7/9 统一修 draft 六处)。
  ④**计数订正**:`_pending_draft_edits` 归一后 **26 条**(v1.64 误记 21)。
  ⑤**写作期取数纪律(五行,standing ruling)**:(1) 数字只从 `results.json` 数据块取,不从 draft/终极review/plan 变更日志取;(2) 写作指令队列唯一化为 `base_probe._pending_draft_edits`,散在各块的 verdict/预判(如 `_verdict_714`)只作参考;(3) `终极review.md` C 节数字一律视为**过期**,以 results.json 数据块为准;(4) plan 变更日志是历史记录、非写作指令;(5) 「answer commitment」命名层级归 7/14 内审裁决,**默认不进 abstract/contrib**(v1.60⑥ 红队裁决 + W-B prereg 措辞禁令为 standing ruling)。
- **v1.66 变更 (2026-07-08)**: **gap-review top-5 之 必2/硬伤4 + 卫生打包执行(零卡/我方独立完成部分全清)**——
  ①**必2/硬伤1(F3 采样臂 CI 伪复制)= 唯一证据侧必修件,已修**:`metrics.score_bootstrap_clustered`(重采样单位=case 整块,治 3-seed 链被当独立=伪复制)+ `score_pilot --cluster` 双版 CI + `test_score_bootstrap_clustered`(点估不变/CI 加宽/可复现,10 测全绿,commit 9cd513a)。es_drop 不受影响(drop_bootstrap 本就 case 级)。**⚠待用户跑一条 CPU 命令**(在 F3 cf200samp jsonl 所在机,无需 GPU):`python src/score_pilot.py --config experiments/probe32b_sample.yaml --editor ROME --decode sample --cluster --boot 10000` → 回传 rr/clr/ES 聚类 CI 落库(预期点估不动、CI 加宽,gap-review 估 RR~[0.19,0.34])。results.json F3 块 rr/clr_ci_B3 已标伪复制 + 附命令。
  ②**硬伤4(W-A G5 操作化偏离)已诚实定案**:git 考古(commit 39ca2e9)证 z≥2 与 G5=100% 同 commit 落地、无法证早于开盲 → 不追认 prereg 变体,标 `operationalized post-hoc`;prereg-wseries §7.5 加 G5 条,G5 从 W-A『干净』硬门降 suggestive(承重腿=A2 干净 null 不受影响);7/14 可回传 wa base jsonl 按冻结 max-stat 重算(commit 94eb60e)。
  ③**卫生打包(我方数据侧)一遍清**:percase n_rows 1196→1194、clr_split_M1 配对 n=196 注、confirm_arms 措辞细分(RR 全含零 vs S−N ES 排零)、b16 RO 4/4 高能力 cell、14B RR 回填 0.162、rq3 名义/有效 n 注(commit 209540e)。
  ④**两 draft 硬伤精确入队**(不盲改 draft 数字):硬伤3(主表 32B n=200→198,但 ES=119/200 名义口径→约定二选一由 7/12 表格 pass 定)+ 硬伤2(logit-lens 负带真值=decoder 7–11 编辑层上游,draft 6 处,7/9 修)入 `_pending_draft_edits`(现 **28 条**)。
  ⑤**剩余 gap-review top-5**:必3(AIA relevance statement)+必4(reverting-to-truth + ethics statement)=写作,排 7/11;必5(plots.py fig1 按裁定规格重写 + 图1 检查单)=代码+7/12。B1 叙事倒置(draft)与 A1–A9 写作包属写作相,骑 7/11–13 日历。
- **v1.67 变更 (2026-07-08)**: **"把写作前一切准备完"——本地零卡统计 + 材料起草在飞(用户指令:先不急出图,按 gap-review 全面推进)**——
  ①**必2 关账**:F3 采样臂 case 聚类 CI 用户回传落库(点估全同、CI 加宽:B3 RR 0.264[0.195,0.336]、CLR 0.523[0.462,0.583]、ES 0.469[0.414,0.523];es_drop 0.090[0.010,0.171] 不变)。写作用聚类口径。
  ②**C2(B16 判官一致性)补算**(src/b16_kappa.py,本地 b16_verdicts+a3_neutral):合并 50-池 in-pop 路由 Fleiss κ=**0.790**(P̄=0.893)/panel κ=0.875;neutral-17 复算 0.765 自洽。给 68% headline 一致性基座(原无 κ)。
  ③**★硬伤4 正解=重大发现**(数据本地在盘,可算非只 flag;src/wa_g5_maxstat.py):W-A G5 冻结 prereg max-stat 口径=**19/65=29.2%**,实跑 z≥2 版 100% 严重高估。29.2%<50% 地板 → **冻结口径 premention 灵敏度门不过**;'G5=100% 表征提及前可靠升起' 作冻结门【不成立】。**但 A2 干净 null(rev≈held 连续 zpre_max,不依赖 G5 阈值)是承重腿、仍稳**——W-A '表征在场≠回退、分岔承诺层' 主结论存活,变的是禁报高灵敏度检出。**7/14 内审须裁 W-A『可靠升起』叙事去留**(见 results.json wa_main._g5_硬伤4 / prereg §7.5)。
  ④**table_rq2.tex 去污重生成**:旧污染版(Bridge 90%/Recall 0)→ 两池并列(neutral 17 vs widened 50,不混池)+ κ 行;污染版降 supp。
  ⑤**行政线落地**(gap-review E1/E2):官方死线 7/21/7/28/7/31、Phase-1=3 人审全文+AI 辅助无 rebuttal → 全文数字一致性=生死件;plan §头 + CLAUDE.md 硬约束同步。
  ⑥**prewrite-materials workflow 完成落库**(wf_cd30418a-ebe,20 agents/2.1M tok):10 份材料(必3 relevance/必4 ethics/D1/D2/D3/D4/D6 methods-supp/E3/E4/E5 scaffold)draft→judge 对抗核 → `paper/prewrite/` + `_JUDGE_REVIEW.md` 台账。判官抓 7/10 需修:高 stakes 已内联修(必4 Recall 22% 非全 re-derivation + B26 软化、D4 F1 排 7B math-confound、D6 κ=0.836 改标 judge-vs-rule 校验非 inter-judge、D1/D3 加 G5 更正 banner 指向冻结 max-stat 29.2%);D2 subject-scrub 计数 / E5 文件计数 / E3-E4 缺件 → 台账记 fold-in 修。必3 relevance 判官 OK 原样。
- **v1.68 变更 (2026-07-08)**: **"写作前一切准备完" 关账**——能本地做的零卡件/材料/校正/统计**全清**。**余下三类均非"可提前准备"、而是 write-time 或 platform**:①**write-time(fold-in 7/11–13)**:硬伤2/硬伤3 的 draft.md 编辑(已精确入队 `_pending_draft_edits`)、E6 LaTeX/.bib 建仓(草稿仍 markdown;bib 逐篇终核是入文纪律)、_JUDGE_REVIEW 里 ⏳ 项、A1–A9 写作包、B1 叙事倒置、abstract 三版;②**platform(需回传数据)**:C1 W-A 扩展梯 case-level 聚类(14B/8B/70B/MEMIT wa jsonl 未回传)、E5 匿名脚本实跑(排 7/20);③**7/14 内审裁决**:W-A『可靠升起』叙事去留(硬伤4:冻结 G5 29.2%<50%)、answer-commitment 命名、track 拍板。**下一步待用户令**:开始写作(fold-in 材料+执行 pending)或继续别的。
- **v1.69 变更 (2026-07-10)**: **第一性复核 + Fable 对抗审核后的增量实验终版；双节点均为 8×H200。写作一致性是接收主杠杆，X 系列只压缩 R3′ 风险，不承诺单凭实验把判档推到 accept。**
  **【总裁决/覆盖关系】**执行优先级固定为 **P0-B 写作真源同步 > P0-A 统计单位修复 > X2 MEMIT 修复复制 > X3 active-paraphrase > X1 词法正交 chain replay**。科学上 X1 上限最高，但工程/判官/作链风险最大；与必3/必4/必5/H3/B14、图1或 7/13 v2 冻结冲突时，按 **先砍 X1、再砍 X3、保护 X2** 处理。旧 B27/E-CHAINSUB 的污染-span/自循环版本继续 DROP；仅复活下述 fresh-authored X1，且 claim ceiling 仅为“词法正交语义链内容足以改变答案”，**不证明自然生成中介或必要性**。
  **【资源与节点】**现有两组独立 8×H200，统一 fp32。开跑前先核两节点的 wikipedia parquet、`stats_r1qwen14b` mom2 缓存和模型路径；能命中 MEMIT 缓存的节点先跑 X2，另一节点跑 X1/X3。若原分配节点缺挂载或缓存，立即交换节点，不在错误节点重算/下载 mom2。所有成本均按“8 卡节点墙钟小时”记录。
  **【P0-A·capability 统计单位修复，7/12 EOD 前】**新增 case-block 模式：bootstrap 抽 unique `case_id`，一次保留该事实跨全部 scale/family 的可用行；B=10000、seed=42，主输出明确是“conditional on these six fixed checkpoints 的事实抽样不确定性”。旧 family→row 两级法保留作 supplementary sensitivity，并同 commit 把 `emergence.percase._status`、B15 记录和 limitation 从“承重 cluster bootstrap”改成历史/敏感性。B15 同法重跑。固定模型配对以 **Qwen 32B−14B** 为主描述（同为非 Math 父本），32B−7B 仅作带 Math-confound 的次行；不新增 32B−1.5B。无论 block CI 是否排零，capability 永久维持 supporting-trend、非标题级；排零只许可写“association robust across facts in these fixed checkpoints”，含零则降为“双高端显著、跨族一致的 size-associated pattern”。
  **【P0-B1·数字/方法真源同步，7/13 硬死线】**在任何 X 结果入文前清完：① emergence 改 es_drop 承重、net-CLR 退役；② 32B base recall=0.765；③ taxonomy=50 池 68/22/8/2%、κ=.790；④ logit-lens=n=23 installation sanity，peak decoder 58，负 gap 带统一为 decoder 7–11（不是 8–12，共六处）；⑤ MEMIT、14B repair、C 臂、F1/F2/F3/B15 全落文；⑥ Table 1 32B 的 nominal n=200 / valid n=198 / RR denominator=119 分开，不混写；⑦ B26 默认撤回当前未落账的四处 McNemar “certifies” hunks，只有 per-item off/on 命中先进入 results.json 才能恢复认证；⑧ union stress test 改写为全 CounterFact 约 21.9k 条的 token 并集，并修 `genbench.py` 对 path/fallback_path 的选择逻辑（既有结果按实际全池口径保留，不因代码卫生重写数字）；⑨ §2 补 CRANE 立界、Thinking-Intervention/SALT/ParamMute 正式引用并建立 `paper/refs.bib`；⑩ method 明写“`o_old` 与安全别名（≥4 字符）的空格/大小写变体之首 token，每步施罚”，不暗示完整序列抑制。硬伤3 的表格口径裁决先于 draft 数字改写。
  **【P0-B2·机理措辞同步，7/14 裁决后 7/15 落地】**先修 `_pending_draft_edits` 中仍残留的 G5=100% 等 stale 指令，再写 draft：M1=preregistered kill test 存活 + 观察性近必要性（非因果中介）；W-B=剂量受限低功效 null（非 clean dissociation）；W-A 冻结 G5=19/65=29.2%，A2 仅 suggestive，禁“可靠地在提及前升起”。X 系列任何数字必须先建 results.json 数据块和 pending 条目。
  **【X2·MEMIT-14B 修复复制，唯一保护 GPU 项，n=200】**N 复用在盘 MEMIT-14B，但新 T/C 配置必须与权威 N **完全同编辑状态**：layers 钉死 `[7,8,9]`（现 `memit14b.yaml` 的 `[7,8,9,10,11]` 必先改回并注释历史），同 `stats_dir=./data/stats_r1qwen14b`、同 case/order、同 dtype/BOS/代码环境，tag 使用 `cf200memit_sup` / `cf200memit_strong` 防 glob 混池。pilot n=8 只验技术：mom2 缓存命中且日志无 recompute；每 case target/donor 与被压 token-id 集非空；B0 T 与 N 逐字一致、B3 T 与 N 至少存在差分；读取 N `_meta` 做 git/dtype/NO_BOS parity，不一致则按 N 环境重跑而非混配。主操作点固定 α=8、scope=think，不调参。
  **【X2 裁决】**跨编辑器特异修复只在三条合取时成立：① T−C 的 ES@B3 case-paired CI>0；② C−N 的 ES/RR（含 RRs）均与 0 相容，证明 C 惰性；③ T−N 同方向。RR/RRs/CLR 为关键次端点，B0 恒等为构造 sanity。若 C−N 实质非零，裁“MEMIT 上强竞争者臂不惰性，特异性未决”；若 α=8 的 T−N 与 T−C 全 null，可按跑前预注册追加 α=16 **诊断臂**，必须与 α=8 并列、永不替代主端点或升级主 claim。null 的唯一合法措辞是“ROME 同模型同尺度有效的 α=8 操作点未迁移到 MEMIT”，不笼统证明 editor-specific。D 臂不重跑，正文也不称 MEMIT 复现完整五臂因果电池。
  **【X3·ROME-32B active paraphrase，add-only，n=200】**Day-0 先在 CPU 对在盘 N 臂 para0/para1 打 PS@B0/PS@B3，报告 case 数、门率和缺失，肉眼审 20 条 CF paraphrase 的无关前缀/可读性，并与 prereg 同 commit。GPU 前必须新建 `cross_arm_para.py` + mock，因现 `cross_arm.py` 只吃 efficacy。T/C 配置须字面写 `suppress.apply_to: [efficacy, para0, para1]`；`paraphrase` 别名不算接线。pilot 必验 para 行 T/C 与 N 有实际差分，防默认 `apply_to=[efficacy]` 造成静默 null。
  **【X3 端点/裁决】**唯一主端点为 para0+para1 全行的 **T−C PS@B3**，按 case 聚类；同时要求 C−N PS 与 0 相容、T−N 同方向，防 C 臂伤害伪造 T−C。N-B0 paraphrase 成功子集上的 committed-old rate 降为确认性次级（处理前门，对 T/C 同施，不构成结果选择偏差）。门后 n<140 不改主端点，只把次级降方向性。投稿前**不启动 sequence-level 救火臂**：残余 CLR/alias 零卡审计只作边界说明，序列级版本维持 camera-ready，避免看到 X3 后再开自由度。X3 永不改 abstract，也不得推翻 7/13 已冻结 claim；正/负结果只 add 到全文或 supplementary。
  **【X1·词法正交 chain replay，全文/supplementary 充分性实验，永不进 abstract】**总体只取 7/10 前既有 32B/ROME committed-reversion：每 case 按 main B3 greedy > F2-B1 > sampling seed0 选唯一来源，且该“被选中链”自身须有 committed 判官票，别源票不可替代。自然链 replay 成功率须≥80%，否则整项只报有效性失败。使用 B1 约 250-token 长度域（F2 已证 B1 RR≈B3），LLM 起草 + 人工审定；双作者、盲判官、重试/退避规则和最少 2 张有效票在造链前预注册。alias 来源固定 `data/aliases.json`，字符串词界与 suppress 首-token 集双重 lexical validator 均通过才入组；以 base-model NLL/盲流畅度门约束作链落在自然 B1 链分布，不按模型结果排链。
  **【X1 五臂】**A OLD-SEM：支持旧值但禁 `o_old`/alias/被压首 token；B NEUTRAL：等长同风格无答案立场；C OLD-LEX：不支持旧值但按该 case 自然链匹配 `o_old` 提及次数与大致位置，至少一次在末四分之一，主风格为引用/归因“过时资料称 X”，否定式只作带标签敏感性；D BRIDGE-LEX：复用 OLD-SEM 的主要 bridge entity/联想词，但放入立场中性框架、禁 `o_old`，只在有可定义 bridge 的配对子集推断；E NEW-SEM：支持编辑值、禁 `o_new` 字面。NEW-SEM 另在未编辑 base 上跑，测“base 从 old 被反参数链推到 new”的通用链顺从率，与 edited+OLD-SEM 的反向翻转作对称描述。
  **【X1 主端点/BOTH 规则】**主行为端点有且仅有：P1=OLD-SEM−NEUTRAL 的 old-commit 配对差；P2=OLD-SEM−OLD-LEX 的 old-commit 配对差。两者均报 paired bootstrap CI + exact permutation/sign test；neither/both 率逐臂公开。答案同时含新旧值时，主口径由预注册中性判官裁最终主张，平票记 0；严口径“含旧且不含新”作敏感性，镜像 RR/RRs 双口径。BRIDGE-LEX 比较裁定一跳联想能否解释 OLD-SEM；任何 OLD-LEX null 都不得被单独解读为“词法无效”，除非剂量匹配门通过且 OLD-SEM−OLD-LEX 差值 CI 排零。删除 OLD-SEM−NEW-SEM 旧主估计量，也删除 logit-gap 认证条件；不把被攻击的 logit-lens 接入行为实验的 confirm 门。
  **【X1 claim ceiling】**P1 通过只能写“字面 `o_old` 非必要；蕴含旧值的词法正交链内容足以改变答案”；P2/BRIDGE 对照进一步通过才可写“效应超过匹配字面暴露/单桥联想”。无论结果多强，仍不得写 natural-generation mediation、necessity 或闭环因果。X1 与写作冲突即停止，不追加 resistant cases、不扩池、不以 n 阈值进入摘要。
  **【删除/继续 DROP】**删除候选 X4/WikiFactDiff：这是 gap-review 已明确否决的新数据轴，双 H200 只消除算力、不消除数据构建、模板/别名、载具功效和写作风险；且 14B/ROME es_drop 本域即弱，无法用 n≈100 的显著性主端点公平检验迁移。保留 camera-ready 备忘。继续 DROP parent–distill、更多规模/编辑器、AlphaEdit/裸 zsRE、W-A/W-B/J-lens 新迭代、activation patching、额外 taxonomy/α/genbench 加 n。
  **【双 H200 日历】**7/10–11：P0-A 代码+测试、P0-B1 开始、X1 造链/判官冻结并行；两节点先做挂载/cache parity，缓存节点跑 X2 pilot。7/11–12：X2 T/C 全量（优先落账）；另一节点仅在 X1 链与 prereg 冻结后跑 replay，空档可做 X3 技术 smoke。**7/12 EOD**：P0-A、N-paraphrase Day-0、P0-B1 的承重数字与 capability 保守措辞定案。**7/13**：v2/数字 ledger/图1/H3/B14 冻结日，X 系列不得打断；X2 若在 EOD 前完整落 results.json 才可进入主文/数字 ledger，否则按既有 ROME 修复写。7/14：内审红队+W 系列措辞裁决；节点可跑 X3。7/15：P0-B2 + X1/X3 分析。**7/16 为本轮 X 系列全文写入截止**，之后只允许技术复现，不立新实验；7/18 abstract 冻结、7/22 全项目实验写入截止、7/25 全文冻结均不变。
  **【停止/写入纪律】**pilot 只修技术，不看效果选超参；inclusion/端点/判官规程须先 commit；多 prompt/seed 按 case 聚类；所有 arm case-paired；任务≤2h shard、jsonl append、case_id 续跑；每条 edit restore 并抽查。任一新工程超出 1 个工作日或需新增未经预注册的 rescue 设计，立即执行降级/停止。中心判档仍由 P0-B 的呈现与一致性决定；X2/X3/X1 分别回答跨编辑器、跨问法、词法正交语义充分性，作用是把 weak-accept 中枢推向上沿而非自动兑换 accept。
- **v1.70 变更 (2026-07-10)**: **双 H200 的真实执行边界落盘：两组 8×H200 均为自有服务器上的 Jupyter 式实例，由用户手动上传代码/配置并在终端启动；Codex 不假设 SSH、共享盘或远程调度权限。**
  ① 每个 GPU 实验先在本地形成独立“上传胶囊”：最小代码/配置清单、文件 sha256、跑前冻结的端点与停止规则、环境/模型/stats 路径占位符、smoke 命令、正式分片命令、产物清单与回传校验；用户只负责上传、替换路径变量、粘贴命令和下载产物，不在服务器临时改科学口径。
  ② 两实例逻辑命名为 H200-A/H200-B，但不预设挂载/cache 对称。首轮只跑只读 inventory；按 `stats_r1qwen14b` 命中情况动态把 X2 分给命中节点，另一节点仅在本地 prereg/代码/测试冻结后接 X3 或 X1。不存在跨实例共享中间文件的假设；每个实例产物独立带 manifest、配置快照、git hash、环境摘要与 case 完成清单。
  ③ 远端故障恢复仍按 ≤2h shard、jsonl append、`case_id` 续跑；上传版本更新必须整包替换并核 sha256，禁止在 notebook 中手改后继续混跑。GPU 结果回传本地后，严格走 raw → 校验/分析 → `paper/results.json` → `_pending_draft_edits` → draft。此部署事实只改变运输与调度，不改变 v1.69 的优先级、端点、claim ceiling 或截止线。
- **v1.71 变更 (2026-07-10)**: **覆盖 v1.70 对实例隔离和“上传胶囊”的错误假设。真实拓扑为：一台可联网 CPU 实例 + 两台 8×H200 Jupyter 式实例，共享同一块盘；用户手动上传我修改的代码/实验文件并粘贴命令。**
  ① 不制作独立上传包或重复传模型/数据；我直接修改仓库内的代码、配置、测试和 prereg，随后只给“需上传的变更文件列表 + 共享盘路径变量 + smoke/正式命令”。CPU 实例负责联网下载权重、数据和缺失依赖到共享盘，两台 H200 直接复用。
  ② 模型、CounterFact、Wikipedia 与 `stats_r1qwen14b` 均按共享盘单一真源管理；X2 优先复用同一 N 臂与 mom2 缓存。两台 H200 可并行跑不同 tag/shard，但不得并发生成同一 mom2 缓存、写同一 jsonl 或覆盖同一配置快照。
  ③ 首轮只需一次共享盘 inventory；确认 CPU/H200 三实例看到相同绝对路径、文件大小与缓存后即可调度。实验产物仍须保留 git hash、配置快照、环境摘要和 case 完成清单；结果回传后的单向落账纪律不变。v1.70 中“实例间不共享文件”“每实验上传胶囊/manifest”的执行要求自本版起作废。
- **v1.72 变更 (2026-07-10)**: **用户覆盖执行顺序：先推进实验并同时占满两组 8×H200，写作同步后置。**v1.69 的科学端点与 claim ceiling 不变，但“P0-B 写作先于上卡”不再是调度门；本轮已开始的 draft 真源同步标为部分完成、暂停，后续须统一复核后才算写作终版。
  ① **H200-A 固定跑 X2**：MEMIT-14B N 状态严格匹配的 T/C 修复复制，先 n=8 技术 smoke，通过即 n=200；该项仍是唯一保护 GPU 项。
  ② **H200-B 固定跑 X3**：ROME-32B active paraphrase T/C，先完成 N 臂 Day-0 评分、`apply_to:[efficacy,para0,para1]` 接线测试和 n=8 smoke，通过即 n=200。X3 不等 X2 结果，不与 X2 串行。
  ③ **联网 CPU 实例并行**：共享盘 inventory、缺失权重/数据/依赖下载、P0-A case-block 重采样与 X2/X3 零卡分析准备；模型、数据与 mom2 cache 只存共享盘一份。两 H200 只写各自独立 tag/shard，禁止并发写同一 jsonl 或重算同一 stats cache。
  ④ **X1 后置**：仅在 X2/X3 均已启动且不占其工程注意力后准备；若第二节点暂时因 X3 技术门未过而空闲，优先排 X3 修复，不以未经冻结的 X1 临时填卡。写作在首批结果回传后恢复，仍走 results.json→draft 单向路径。
- **v1.73 变更 (2026-07-10)**: **X2/X3 上卡实现冻结 + smoke 门消除自相矛盾。**正式配置与端点写入 `prereg-x2-x3.md`；smoke 复用正式 YAML，仅用 `run_pilot --limit 8 --tag-suffix _smoke` 隔离产物，禁止复制/漂移一套超参。
  ① 每条生成记录 `suppress_trace` 的实际 target/token-id、probe selection 与 processor 调用次数；B0(scope=think)调用数必须 0，B3 active probe 必须 >0。JSONL `_meta` 新增 config/code 文件 SHA、dtype/BOS/model、实际参数 dtype、软件版本，供 N/T/C parity 直接核查。
  ② **修正旧 smoke 矛盾**：T 在 B3 至少一条 active 输出须不同于 N；C 的科学角色是惰性强竞争者，故“C 文本必须变化”不再是硬门——若 C 文本全同只记 warning，但 processor 调用必须实证接线。否则一面要求 C−N≈0、一面强迫 C 改输出，会把正确的惰性对照误判失败。
  ③ X2 既有 N 若缺 code/dtype/BOS/model/software parity，按预声明 `memit14b_freshn.yaml` 重跑，不以结果决定；X2 mom2 smoke 日志须出现三层 cache load 且无 recompute/error。X3 Day-0 与跨臂 PS 统一由 `cross_arm_para.py` 计算，para0/para1 按 case 聚类保留；若且仅若既有 32B N 与新臂 B0 无法逐字复现，启用跑前已声明的 `probe32b_freshn.yaml`，不看 B3 效果作决定。
  ④ 正式 n=200 统一用 logical world=32、四个 8-GPU 波次（每 shard 6–7 case）满足 ≤2h/append/resume 纪律；H200-A/B 分别由 `experiments/run_x2_h200.sh` / `run_x3_h200.sh` 执行，互不写同一 tag。
- **v1.74 变更 (2026-07-10)**: **三实例绝对路径固定，不再依赖终端临时输入。**新增 `experiments/x23_paths.sh` 作为唯一部署路径真源：项目 `/inspire/hdd/project/ai4education/ky26140/why/why-aaai27`；14B `/inspire/hdd/project/ai4education/ky26140/why/models/DeepSeek-R1-Distill-Qwen-14B`；32B `/inspire/hdd/global_public/public_models/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B`；英文 Wikipedia `/inspire/dataset/wikipedia/20231101/20231101.en`。CPU inventory 与两条 H200 launcher 均自动 source 此文件；路径改变时只改这一处。
- **v1.75 变更 (2026-07-10)**: **首次 X2 smoke 暴露 validator 假阳，实验本身未失败。**16 个 T/C shard 均 0 error、mom2 共 48 条 cache-hit；失败来自①把每 rank 合法不同的 `parameter_device=cuda:0…7` 当作 runtime 不一致，②手工上传目录无 `.git` 时把 `git=unknown` 当硬失败。修为：跨 rank 比较 actual model/tokenizer signature 时排除 device；git 缺失降 warning，逐文件 `code_sha256` 继续作权威；launcher 支持 `X23_REUSE_TC_SMOKE=1` 复用已完成且由 validator 严格核验的 smoke，禁止浪费重跑。
- **v1.76 变更 (2026-07-11)**: **X3 单卡 smoke 的 `cf_975` 在 ROME 编辑成功后、B3 生成阶段发生容量型 OOM，改为一致的 2×H200 model-parallel 协议。**故障时单卡总 139.81 GiB、PyTorch 已分配 133.93 GiB、仅余 5.04 GiB，而下一次 KV/激活申请 10.03 GiB；reserved-unallocated 仅 97.19 MiB，排除“清缓存/碎片化/偶发占卡”解释。技术救援不改变科学端点、case/order、fp32、B3 cap、ROME layer12、α=8、scope=think 或 probes：
  ① X3 配置统一设 `model_parallel:true`，launcher 将 8 卡切成四对，每进程 `CUDA_VISIBLE_DEVICES=<pair>`、本地 `--device 0`，以 `WHYAAAI_DEVICE_MAP=balanced` 均分 32B-fp32 权重并为两卡各留充足 KV/ROME 临时空间；不用 `balanced_low_0`，因为两卡场景可能把几乎全部约 134 GiB 权重压到 GPU1，重现容量风险。
  ② 单卡旧 smoke 只作故障审计，绝不与新结果混池。dataset tag 改为独立 `_mp2` 系列；由于执行拓扑、代码溯源和 runtime 均改变，N/T/C 全部 fresh 同协议重跑，先 n=8 smoke（必须覆盖并成功完成原 OOM case `cf_975`）再 n=200。
  ③ 正式运行仍保持 logical world=32 与每 shard 6–7 cases；每个波次四个 2-GPU 进程，八波完成。validator 对跨进程比较时只忽略物理 `CUDA_VISIBLE_DEVICES` 字符串，仍硬验 `WHYAAAI_DEVICE_MAP=balanced`、`model_parallel:true`、fp32、BOS、代码/config hash、完整性、B0 恒等、抑制 trace 与 B3 实际差分。
  ④ provenance 增记 `hf_device_map` 摘要及编辑权重实际 device，用 smoke 直接核验 layer12 确已分片且编辑→生成→restore 路径可运行。若 mp2 smoke 仍 OOM/device mismatch，X3 按 v1.69 停止规则降级停止，不改 bf16、不缩 B3、不量化 KV、不追加结果驱动 rescue。
- **v1.77 变更 (2026-07-11)**: **X2 落账 + X2 释放后的双节点调度。**
  ① **X2 预注册主端点 PASS**：fresh-N/T/C 各 n=200、32 shards、0 error；每个 T/C 对 N 的 B0 共 400 probe rows 逐字一致，mom2 三层缓存合计命中 192 次。B3 的 T−C：ES +0.100[+0.040,+0.160]、RR −0.0982[−0.1696,−0.0268]、CLR −0.220[−0.280,−0.165] 均排零；C−N 的 ES/RR/RRs 与 0 相容，T−N 同方向。**严口径 RRs 的 T−C/T−N 均含 0**，必须作为 null 次端点同报；不得写“所有回退口径显著”“C 与 N 等价”或“MEMIT 完整五臂复制”。
  ② X2 的 provenance gate 先判旧 N 不足，故按 prereg 运行 `memit14b_freshn.yaml`；fresh-N 的 B0/B3 ES=.560/.500、es_drop=.060[−.020,.140]、RR=.205，与旧 `memit_replication`/B22 的 .540/.450、.090[.010,.170]、.333 实质不同。两块**不得合并或互相背书**：X2 只承重“修复跨编辑器转移”，旧 B22 继续单列，待旧 cohort/provenance 能否补齐后再裁其现象 claim。
  ③ **H200-A 下一项不是未冻结的 X1，而是协助 X3**：X1 尚缺 prereg、唯一 source manifest、fixed-chain runner/测试和盲审五臂，直接上卡违反 v1.69 的结果前冻结纪律。X3 mp2 只在单份 fresh N/T/C smoke（含 `cf_975`）PASS 后进入 full；H200-A/B 以同一 world=32 分摊互不重叠 wave bases（默认 A=`16 20 24 28`、B=`0 4 8 12`），只写不同 rank shard。两半完成后在 CPU/任一节点统一 full audit + score + paired paraphrase analysis。该调度只缩短墙钟，不改变配置、case/order、端点或统计单位。
  ④ `score_pilot`/`metrics` 中遗留的“生成式 B0 ES≥.90 否则作废”提示按 v1.18 更正为：**Loc≥.85 前提下取 best-achievable B0 ES 层**；旧 .90 是 rewrite_acc 数字误植，不得用于否定 X2。
- **v1.78 变更 (2026-07-11)**: **运行事实覆盖 v1.77 的双节点 X3 设想：H200-B 的 X3 已经按旧 all-ranks launcher 在跑，H200-A 禁止再写任何 X3 shard；A 转入 X1 第一阶段 natural-chain fixed replay gate。**
  ① **冻结总体与 hierarchy**：只用 7/10 前已存在的 `data/reverted_32b{,_f2b1,_samp}.jsonl`。对 33 个 unique case 先无条件按 `main B3 greedy > F2-B1 > sampling seed0` 选唯一 source，再要求该**被选中 source 本身**至少 2/3 中性判官判 `in_population/committed-old`；高优先 source 若 held/缺票，低优先 source 不得救回。按现有冻结票得到 **n=18**，manifest 固定 source path+1-based line+整行 SHA256+COT SHA256+票据来源；manifest 生成后不得按 replay 结果删 case。
  ② **固定链 replay 干预**：逐 case 先做与 32B headline 相同的 ROME edit（layer12、`v_loss_layer=63`、fp32、NO_BOS、single edit→answer→restore），随后不再生成 CoT，而是把 manifest 指向的原始自然 `cot` **逐字 prefill** 到 `<think>…</think>`，只 greedy 生成最多 256-token answer。原链不截断、不改写；记录 source/COT hash、token 数与答案。因最长链可接近 B3，容量协议固定为每进程 2×H200、`device_map=balanced`、四进程并行；不允许事后改 bf16、裁链或调层救结果。
  ③ **技术门与统计门分开**：先 n=4 smoke，只查四个 pair worker 均完成、旧 OOM/设备映射/编辑→固定链→答案→restore 路径、manifest/hash 与非空答案；不看效果选参数。full 对 n=18 全跑、world=4、jsonl append/resume。主有效性端点由 3 名相互独立的中性答案判官按最终主张投 `old/new/neither`，多数 old 记成功；**点估 old-commit rate≥0.80** 才 PASS（n=18 即至少 15/18），Wilson/精确二项区间只描述、不另设下界门。规则 loose-old 与 strict old-without-new 仅作敏感性；both 由判官裁主张。
  ④ **停止规则/claim ceiling**：gate FAIL → X1 立即停止，只报 fixed replay 未能稳定复现原自然回退，不造五臂。gate PASS → 才允许按 v1.69 冻结双作者、盲判官、重试/退避与五臂文本；本阶段本身只验证 replay 载具有效，不能证明 chain semantics、自然生成中介或必要性。任何实现超过 1 个工作日或需结果驱动 rescue，停止 X1，A 宁可空闲也不启动已 DROP 的新轴。
- **v1.79 变更 (2026-07-11)**: **X1 上卡前 provenance 红队修正（仍未看任何 replay output）。**
  ① `src/extract_reverted.py` 的历史 sampling 提取只按 `case_id→budget` 存一行、不按 seed 分键；`edit_loop` 写入顺序是 seed0→seed1→seed2，故 `data/reverted_32b_samp.jsonl` 不是 v1.69 误称的 seed0，而应是最后覆盖的 **historical seed2**。第三 source 从本版起诚实改名 `F3 historical sample seed2`；seed 本身无理论特权，且文件/三判官票均早于 X1，不涉及 replay outcome 选择。
  ② 在 A 上卡前，联网 CPU/共享盘必须对 raw `cf200samp` 显式筛 `probe=efficacy,budget=B3,decode=sample,seed=2`，并同时用 seed2 的 B0 重建回退池；要求导出 14/14 case IDs、COT、answer 与历史文件逐字一致。**确认失败则 X1 阻塞，不临时改 seed、不降为结果后 n=15。**确认报告落 `results/x1_sample_source_audit.json`。
  ③ replay 每 case 在同一次 edit 状态下先跑 fresh B0（空 think、greedy、answer cap256），再跑完整 fixed natural COT answer，最后 restore。主 success 定义升级为 `B0 strict ES 成功 AND replay answer 被 answer-only 中性判官多数判 OLD`；分母仍是冻结 18 case，任一项失败即该 case 失败。这样排除“编辑未装上所以自然答旧”的伪 replay PASS。
  ④ v1.78 的 n=18/15-of-18 门在 seed2 raw audit PASS 后保持不变；后续五臂仍必须用全部冻结 case，不能只保留 replay 成功个案。OLD-LEX 剂量/约 250-token authored-chain 规则尚未冻结，Stage-0 PASS 也不得直接开五臂，须另立 prereg 解决自然 B3 多次提旧与 B1 长度域冲突。
- **v1.80 变更 (2026-07-11)**: **X1 Stage-0 终裁 = FAIL，执行停止规则。**
  ① 技术与 provenance 全 PASS：historical sampling 经 raw `cf200samp` 明确重建为 seed2，14/14 case IDs、COT、answer 逐字一致；mp2 smoke 4/4、full 18/18、4 shards、0 error，manifest/hash/device-map/edit→B0→fixed-COT→answer→restore 全通过。因此失败不是 harness 缺行或容量问题。
  ② 结果在判官前已不可过门：fresh B0 strict 仅 **14/18**，而联合门要求至少 15/18；四个失败全部来自 F2-B1 priority-only 来源（F2 仅 1/5 当前安装复现，main 10/10、historical sample 3/3）。即使所有 replay 判官都判 OLD，联合成功上限仍 14/18。
  ③ 三名相互独立的 answer-only 中性判官完成 54 票：replay OLD 多数仅 **12/18=66.7%**，本身也低于 80%；17/18 case 全票一致，Fleiss κ=**0.920**，故不是判官噪声。按冻结合取 `B0 strict AND judge OLD`，最终 **9/18=50.0%**，Wilson95% **[0.290,0.710]**，远低于 15/18 门。规则 loose OLD 合取为 14/18、strict OLD-without-NEW 为 9/18；loose matcher 把 5 条 both/犹豫答案算入，证其不适合作 replay 主门。
  ④ 来源分解：main 成功 6/10（B0 10/10、judge OLD 6/10）；F2 成功 1/5（B0 1/5、judge OLD 4/5）；sample 成功 2/3（B0 3/3、judge OLD 2/3）。失败同时来自编辑安装跨运行不稳与“原链逐字 replay 仍不保证最终 OLD commitment”，不是单一可修技术点。
  ⑤ **停止**：不造 OLD-SEM/NEUTRAL/OLD-LEX/BRIDGE-LEX/NEW-SEM，不改为只留 B0/replay 成功 case，不换 seed、不裁链、不回退单卡、不调层/answer cap、不扩 source pool。X1 合法结论仅为“在事前冻结的 committed-reversion 富集池上，fixed natural-chain replay 载具未达到稳定性门”；不得据此否定一般 chain semantics，只否定本投稿窗口内该五臂设计的可识别性。H200-A 暂不启动已 DROP 轴，等待 X3。

---

## 1. 研究命题

### 1.1 一句话主张

参数知识编辑（ROME/MEMIT/AlphaEdit）在关闭思考时看似成功，但随着推理模型思考预算增加，模型在自验证/反思过程中会"想起"旧知识并推翻编辑——我们量化这条剂量-反应曲线，定位回退机理，并给出 training-free 的推理时保护方法。

### 1.2 研究问题与假设

| RQ | 内容 | 假设 | 证伪条件 |
|---|---|---|---|
| **RQ1 现象** | 编辑成功率 ES 是否随思考预算 b 单调下降？ | H1: ES(b) 显著递减，think 相对 no-think 降幅 ≥20pp | 降幅 <20pp 或无单调性 → 项目终止，转 fallback |
| **RQ2 机理** | 回退发生在推理链的哪类片段、由什么驱动？ | H2: 回退集中于自验证/反思片段（"wait/let me check"类），因编辑只改写了浅层 (s,r)→o* 映射，未触及分布式关联知识，反思触发旧知识的关联检索 | 回退位置随机分布、与反思标记无相关 → 机理章节降级为现象学描述，论文吸引力下降 |
| **RQ3 修补** | 能否不重训地保护编辑？ | H3: 在被编辑主体出现的位置做条件化表征引导（damping 反思方向 / 强化新事实方向）可恢复 ≥50% 的 ES 损失，且对 GSM8K/MATH 推理精度损伤 <2pp | 恢复 <30% 或推理损伤 >5pp → 修补章节退化为"编辑增强"方案 F2 |

### 1.3 贡献声明（论文三段式）

1. **现象**: 首个在真 LRM（R1-Distill 系 / Qwen3 think 开关）上对参数编辑方法的 think-budget 剂量-反应系统量化（ES(b)、条件回退率 RR(b)、链内泄漏 Leak(b) 三曲线 × 3 编辑器 × 3 模型）。
2. **机理**: 片段级定位 + 隐层探针证据链，证明回退由反思驱动的旧知识关联检索导致，而非随机解码噪声。
3. **方法**: training-free 的 edit-aware reasoning 保护（推理时条件化 steering），在不损害推理能力的前提下显著恢复编辑存续性。

### 1.4 与近邻的差异化（审稿人答辩预案，全部必引）

| 近邻 | 它做了什么 | 我们的差异（一句话答辩） |
|---|---|---|
| R²MU (2506.12963) | LRM 上 **unlearning** 的 CoT 残留 + 训练式修补 | 我们做 **editing**（改知识而非删知识，失效模式是"回退到旧答案"而非"泄漏被删内容"），且修补 training-free |
| R-TOFU (2505.15214) | LRM unlearning 基准，发现 ZeroThink/LessThink 暴露残留 | 我们借其解码协议作自变量，但研究对象（参数编辑）、因变量（编辑回退）、方向（**更多**思考导致失效，与其"更少思考暴露残留"互补成对）均不同 |
| ThinkEval/KnowGIC (2506.01386) | 用 CoT 构造知识图谱评测编辑的间接泄漏 | 它在标准模型上用 CoT prompting 构图做评测；我们在原生 LRM 上把思考预算作为连续自变量，并给出机理与修补 |
| KELE (2408.12456) | 残留旧知识致多跳回退（GPT-2/GPT-J 时代）+ 擦除式编辑 | 它是多跳问题结构导致的回退；我们是 test-time compute 本身导致的回退，且在 LRM 上 |
| 2602.02028 | 附录记录"推理中自我纠正回先验"案例，提出 background-story 训练式编辑 | 它的回退是轶事性观察 + 训练式修补；我们系统量化 + 机理 + training-free 修补 |
| ThinkEdit (2503.22048) / ReflCtrl (2512.13979) | 推理长度/反思行为可由表征工程控制 | 我们借其干预机械，但目标全新：保护编辑事实而非调节推理长度 |
| MQuAKE (2305.14795) | 多跳评测数据 | 仅作数据源与历史定位 |

---

## 2. 实验设计总则

### 2.1 模型矩阵

| 模型 | 角色 | think 控制方式 | 备注 |
|---|---|---|---|
| **DeepSeek-R1-Distill-Qwen-7B** | 主力 | ZeroThink（强制空 `<think>\n\n</think>`）↔ 自然思考 ↔ 强制延长 | Qwen2.5 架构，EasyEdit 兼容；R-TOFU 协议直接移植 |
| **Qwen3-8B** | 最干净的对照 | 官方 `enable_thinking` 开关，同权重同模板 | 排除"模板差异"混杂的关键证据；编辑兼容性 W1 验证 |
| **R1-Distill-Llama-8B** | 架构泛化 | 同 R1-Distill 协议 | Llama3 架构 |
| R1-Distill-Qwen-14B | 规模检查（仅主结果复测） | 同上 | 算力富余时跑 |

### 2.2 编辑器矩阵

| 编辑器 | 实现来源 | 备注 |
|---|---|---|
| **ROME** | EasyEdit | 单事实定位编辑，经典基线 |
| **MEMIT** | EasyEdit | 批量编辑，主力 |
| **AlphaEdit** | EasyEdit 内置版为主，官方仓库对照超参 | SOTA，零空间投影 |
| LoRA-FT 编辑 | EasyEdit (FT-L) | 微调式基线 |
| ICE（in-context editing） | 自实现（prompt 注入新事实） | 非参数对照：检验"上下文注入是否同样被反思推翻" |

前置依赖：为每个目标模型预计算 mom2 协方差统计（EasyEdit 自动缓存，约 4–6 GPU·h/模型，一次性）。

**协议决策（v1.1，影响全部算力与结论强度）**: 主实验采用**单条编辑协议**——每条 case 独立执行"编辑→全预算档生成→还原权重"，杜绝编辑间干扰混杂（KELE 与 MQuAKE 的规模化实验均表明批量编辑本身即放大失效，若用批量协议，审稿人无法区分回退归因于思考还是归因于批量干扰）。批量编辑（MEMIT/AlphaEdit @ batch=100）降级为一个附加消融（"批量×思考的交互效应"，半页），用 vLLM 评测。代价：主矩阵生成无法吃 vLLM 吞吐，按 HF batched generate 计价，见 §5。

### 2.3 数据

| 数据集 | 用途 | 规模 |
|---|---|---|
| **CounterFact**（memit 仓库） | 主编辑数据：ES/Paraphrase/Neighborhood | pilot 200 条 → 主实验 1,000 条 |
| zsRE（memit 仓库） | 第二编辑分布 | 主实验 500 条 |
| MQuAKE-CF-3k（MQuAKE 仓库） | 多跳扩展（portability 章节） | 500 条 |
| GSM8K-200 / MATH500-100 子集 | 修补方法对推理能力的副作用检查 | 固定抽样，种子 42 |

**预过滤（关键）**: 仅保留"模型在编辑前确实知道旧事实"的条目（pre-edit 对 (s,r) 的 greedy 输出 = o_old），否则"回退"无从定义。预计过滤后存活率 40–60%，故原始抽样×2 冗余。

### 2.4 思考预算操纵协议（自变量 b，**5 档 B0–B4，与 `src/think_budget.py` 一致**）

> **v1.12 决议（用户拍板取 B）**：原 6 档（含独立 4096 与"真 natural"）与 §12.1 代码（B0–B4）不自洽 → **plan 对齐代码的 5 档**：去掉独立 4096，natural 由 B3 的 cap=8192 近似（事实类 CoT 通常远短于 8192，模型多自行收尾）。

| 档位 | 实现 | 来源 |
|---|---|---|
| **B0** (ZeroThink) | 注入空思考块 `<think>\n\n</think>` 后直接答 | Jiang et al. 2025（经 R-TOFU `test.py:16`） |
| **B1 / B2** (LessThink 截断) | 思考至 **256 / 1024** token 截断、强制 `</think>` 收尾作答 | R-TOFU LessThink 的 token-预算推广 |
| **B3** (≈natural) | cap=**8192** 高上限，模型自行 `</think>` 收尾（事实类 CoT 通常远短于此，故 ≈自然解码） | — |
| **B4** (extend) | 命中 `</think>` 即替换为 `\nWait, …` 续写、最多 2 次（budget forcing） | s1 (Muennighoff et al. 2025) |

### 2.5 指标定义

设编辑 e=(s,r,o_old→o*)，思考预算 b，模型回答 A(e,b)，思考链 C(e,b)：

- **ES(b)** = E_e[ 1{A(e,b)=o*} ]，编辑成功率曲线（主图 1）
- **RR(b)** = P( A(e,b)=o_old | A(e,0)=o* )，**条件回退率**——零思考下成功的编辑中，b 预算下回到旧答案的比例（主指标，剔除"本来就没编成功"的噪声）
- **Leak(b)** = P( o_old ∈ C(e,b) )，链内旧知识提及率
- **FlipPoint**: C 中模型立场从 o* 翻向 o_old 的首个 token 位置（机理用）。已实现字符级近似 `metrics.flip_analysis`（first/last 立场 + flip_pos）+ 答案口径 `ESf`(首段断言)/`Flip`(两立场都现)（v1.15，07 教训：子串判分分不出"先新后旧"）；Phase 3 升 token 级 logit-lens。
- **Locality / Portability**: CounterFact 标准 Neighborhood / Paraphrase 指标，确认编辑本身质量达标（达不到则该编辑器结果整体作废）。**判生成式口径**（`metrics` 的 `Loc`/`PS`，非 EasyEdit rewrite_acc——v1.18 实测两者有真实口径差 rewrite_acc≈1.0 vs 生成式 ES_b≈0.55；08 旧『完全脱节 0/8』引用系 sequential_edit bug 污染、已更正）。
- **ΔReason**: 修补前后 GSM8K-200 与 MATH500-100 准确率变化（修补副作用）
- 统计：每条 greedy + temperature 0.6 × 3 seeds；置信区间 95% bootstrap（按编辑条目重采样，n=10,000）

### 2.6 混杂变量控制（审稿人最会捅的四刀）

1. **模板混杂**: think/no-think 必须使用**完全相同的 chat template**，仅思考块内容不同（ZeroThink 注入空块而非删除模板）。Qwen3 的官方开关提供同权重双模式的黄金对照。
2. **长度混杂**: "想得多→错得多"可能是长序列退化而非知识回退。对照组：对**未编辑**模型问同一批 (s,r)，测其答 o_old 的稳定性随 b 的变化——若未编辑模型稳定而编辑模型回退，则归因于编辑脆弱性。
3. **采样噪声**: 所有曲线同时报告 greedy 与 3-seed 采样均值±CI；结论必须在 greedy 下同样成立。
4. **批量编辑干扰**: 主结果一律单条编辑协议（见 §2.2）；批量场景单列为交互效应消融，绝不与主曲线混排。

---

## 3. 阶段计划

```mermaid
flowchart LR
    P0["Phase 0<br/>复现循环<br/>6/10-6/17"] --> P1["Phase 1<br/>Pilot<br/>6/18-6/22"]
    P1 -->|"go: RR降幅≥20pp<br/>且机理干净"| P2["Phase 2<br/>主实验矩阵<br/>6/23-7/3"]
    P1 -->|"no-go"| FB["Fallback<br/>方向A重启<br/>(预案见§9)"]
    P2 --> P3["Phase 3<br/>机理分析<br/>6/30-7/8"]
    P2 --> P4["Phase 4<br/>修补方法<br/>7/4-7/12"]
    P3 --> P5["Phase 5<br/>写作提交<br/>7/8-7/27"]
    P4 --> P5
```

### Phase 0 · 复现循环（step ③，6/10–6/17）

每个仓库一张任务卡，产出 `analysis/0X_<name>.md`，统一模板：环境搭建记录 → 代码结构图 → 冒烟测试结果 → 核心优缺点（**从代码出发**）→ 对本项目的可复用资产清单 → 雷点登记。

| # | 仓库 | 容器内做什么（CPU） | H200 上验证什么 | 完成标准 |
|---|---|---|---|---|
| 01 | EasyEdit | 装环境；GPT-2-XL 上 CPU 跑通 ROME 单条编辑全流程；通读 `easyeditor/models/{rome,memit}` 与 hparams 体系；确认 Qwen2.5 hparams 模板存在 | R1-Distill-Qwen-7B 单条 ROME 编辑 + mom2 缓存生成 | 笔记 + 可直接排队的编辑脚本 `src/edit_runner.py` |
| 02 | AlphaEdit | 对照 EasyEdit 内置 AlphaEdit 与官方仓库超参差异；审计零空间投影实现是否与论文公式一致 | 同一 100 条编辑两实现 ES 差 <2pp | 实现选型决议写入笔记 |
| 03 | R-TOFU | 精读 `test_cot.py` 与解码控制；提取 ZeroThink/LessThink 实现为独立模块 `src/think_budget.py`；审计其指标与论文表格口径 | 在未编辑 R1-7B 上验证 5 档预算控制器产出预期长度 | 预算控制器单测通过 |
| 04 | ThinkEdit | 通读方向抽取与 head 定位代码；改造为通用 steering 工具 `src/steer.py`（任意方向、条件化注入） | 复现其 GSM8K 短思考缓解的方向有效性（抽样 100 题） | steering 工具可用 |
| 05 | R²MU | **审计级**：核对其评测脚本与论文表格口径；记录其 CoT 残留度量定义以便对比章节引用 | 不跑训练 | 口径核对结论（一致/不一致及证据） |
| 06 | MQuAKE/memit | 数据提取：CounterFact、zsRE、MQuAKE-CF-3k 清洗为统一 jsonl schema `{case_id, s, r, o_old, o_new, paraphrases[], neighborhood[], hops[]}` | — | `data/` 下三个清洗后数据集 + 数据卡 |

### Phase 1 · Pilot 与 go/no-go（6/18–6/22，硬节点 **6/22**）

- 配置: R1-Distill-Qwen-7B × {ROME, MEMIT} × CounterFact-200（预过滤后）× b∈{B0, B3, B4} × {greedy, 0.6×3}
- 产出: ES/RR/Leak 三指标初表 + 30 条回退样本人工审计（审计字段：case_id, b, FlipPoint, 触发片段类型∈{自验证, 关联回忆, 重述质疑, 其他}, 摘录）
- **go 判据（两条同时满足）**: ① RR(natural) ≥ 20pp 或 ES 降幅 ≥20pp，至少在一个编辑器上成立且另一个方向一致；② 人工审计中 ≥60% 回退案例可归因于反思/自验证片段
- no-go → 当日启动 §9 fallback，沉没成本封顶 12 天
- H200 预算: 编辑 ~2 GPU·h + 生成 ~4 GPU·h + mom2 缓存 6 GPU·h ≈ **一次 4–6 小时的 8 卡窗口即可**；排不上队则按 §6 云端逃生

### Phase 2 · 主实验矩阵（6/23–7/3）

- 全矩阵: 3 模型 × 4 编辑器（ROME/MEMIT/AlphaEdit/FT-L）+ ICE 对照 × 5 档预算（B0–B4）× CounterFact-1000 + zsRE-500
- 每个 cell 产出标准 jsonl（含完整 CoT 文本，供 Phase 3 复用，**只生成一次**）
- 锁定主图: 图1 ES(b) 多编辑器曲线；图2 RR(b) + 未编辑对照；图3 Leak(b) 与 FlipPoint 分布
- 周中检查点 6/27: 若 Qwen3-8B 编辑兼容性失败（mom2/层定位问题），降级为 R1-Distill 双架构故事，Qwen3 仅 ICE 对照

### Phase 3 · 机理分析（6/30–7/8，与 Phase 2 尾部并行）

1. **片段归因**: 反思标记词典（wait/but/actually/let me verify/double-check/hmm/再想想…）自动标注 CoT 片段；统计 FlipPoint 落入反思片段的比例 vs 随机基线（置换检验 p<0.01）
2. **隐层证据**: 在 s 的提及位置逐层做 logit lens / 线性探针，度量 o_old 与 o* 的相对强度沿思考过程的演化；预期看到：编辑层之后 o* 占优 → 反思片段中 o_old 关联通路重新激活
3. **剂量机制**: RR 与反思片段数量/占比的回归（控制总长度），区分"想得久"与"反思多"两个因素

### Phase 4 · 修补方法（7/4–7/12）

按优先级实现与评测，主推 F1：

- **F1 Edit-aware steering（主方法）**: 用 ThinkEdit 管线在编辑前后模型上抽取"质疑-编辑事实"方向；推理时检测 s 的提及，仅在其后 k 个 token 窗口注入 −α·(质疑方向) 或 +β·(新事实方向)；α,β 在 dev-100 上网格搜索
- **F2 编辑增强（备选/叠加）**: MEMIT 批量编辑 {原事实 + K 条 paraphrase + 2-hop 蕴含}，正面提高编辑"深度"
- **F3 解码护栏（弱基线）**: 答案位置对 o_old 词元 logit-bias
- 评测: 保护后 ES(b)/RR(b) 恢复量；ΔReason（GSM8K-200/MATH500-100）；与 ICE、system-prompt 断言两个非参数基线对比；开销报告（额外延迟）

### Phase 5 · 写作与提交（7/8–7/27）

- 7/8 论文骨架（7 页布局：1 引言+图1 / 2 相关工作 / 3 设定与协议 / 4 现象 / 5 机理 / 6 方法 / 7 实验 / 8 结论）；图表清单冻结
- 7/14 全文 v1 内审；**增量查新第二轮**（关键词见 §8，重点扫 6/10 之后的新 arXiv）
- 7/18 v2 定稿；reproducibility checklist 填写；匿名代码仓整理（4open.science）
- **7/20 abstract 提交**（OpenReview；**全员本周内注册 OpenReview 账号**——新账号有人工审核延迟，这是隐形死线）
- 7/27 全文提交；+3 天补充材料（代码、完整 CoT 样本、审计表）

---

## 4. 时间线总览

| 周 | 日期 | 主线 | 硬节点 |
|---|---|---|---|
| W1 | 6/10–6/17 | Phase 0 复现循环（01→06） | 6/17 六份复现笔记齐 |
| W2 | 6/18–6/24 | Phase 1 pilot | **6/22 go/no-go** |
| W3 | 6/25–7/1 | Phase 2 主矩阵 | 6/27 Qwen3 兼容性检查点 |
| W4 | 7/2–7/8 | Phase 2 收尾 + Phase 3 机理 + Phase 4 启动 | 7/8 主图三张冻结 |
| W5 | 7/9–7/15 | Phase 4 修补 + 写作 v1 | 7/14 内审 + 二轮查新 |
| W6 | 7/16–7/22 | 打磨、checklist、匿名仓 | **7/20 abstract** |
| W7 | 7/23–7/27 | 全文终稿 | **7/27 全文**，7/30 补充材料 |

缓冲设计：Phase 2 的生成任务全部缓存 CoT 原文，Phase 3/4 不再消耗大额 GPU；W5 之后理论上零排队依赖。

---

## 5. 历史算力预算（已由 v1.69 的双 8×H200 主动队列取代）

> 本节保留早期总账供审计，不再指导当前执行。当前资源、固定路径与 X1/X2/X3 技术门只服从 v1.80 变更记录。

主矩阵规模控制（与协议联动的网格裁剪）：完整 5 档预算网格只给 **MEMIT 与 AlphaEdit**（headline 编辑器）；ROME / FT-L 跑 3 档（b∈{B0, B3, B4}）；zsRE 只跑 MEMIT+AlphaEdit。单条 case 成本 ≈ 编辑 0.5–1 min + 生成（5 探针 × 档数，CapThink 档天然短，均摊 ≈2.5k token/条，HF batched generate）≈ 2–4 min。

| 任务 | 估算 | 形态 |
|---|---|---|
| mom2 统计 ×3 模型（一次性缓存） | ~15 GPU·h | 可中断，**今天提交排队** |
| Pilot（200 case × 2 编辑器 × 3 档） | ~15 GPU·h | 按 case_id 分 8 片 |
| 主矩阵·主力模型（CF-1000：MEMIT/AlphaEdit 全档 + ROME/FT-L 三档；zsRE-500 × 2 编辑器） | ~220 GPU·h | 切 ≤2h 任务，jsonl 续跑 |
| 副模型（R1-Distill-Llama-8B / Qwen3-8B：各 1–2 编辑器 × 300 case × 3 档） | ~50 GPU·h | 同上 |
| 未编辑对照 + ICE + 批量编辑消融（共享权重，**vLLM 可用**） | ~20 GPU·h | 单任务 |
| 机理（logit lens / 截断因果，复用 Phase 2 缓存 CoT） | ~30 GPU·h | 单卡碎片 |
| 修补（F1 方向抽取 + 网格搜索 + 三案评测@dev-100，终选案全量复测） | ~60 GPU·h | 分片 |
| **合计 + 15% buffer** | **~420 GPU·h ≈ 8 卡 × 53 h** | 6 周摊薄 ≈ 每周一个 8–10h 窗口，可行 |

纪律：① 任何任务可在 1 小时粒度中断续跑（编辑 delta、生成 jsonl、探针缓存三级落盘）；② 环境 Docker 化（基于 EasyEdit Dockerfile 扩展），保证 H200/云端/容器三处一致；③ **云端逃生**：截稿前 10 天若累计排队损失 >3 天，启用 RunPod/Lambda 8×H100（~$20/h），预算上限 $400 ≈ 160 GPU·h，**只保关键路径**（pilot 复核 + 主力模型 MEMIT/AlphaEdit 全档 + 终选修补），副模型与消融可降级为附录承诺。

---

## 6. 工程规范

```
why-aaai/
├── papers/          # 论文 PDF（repro_/ref_ 前缀）
├── source/          # 第三方代码（只读，不在内部改动）
├── analysis/        # 复现笔记 0X_*.md + 本计划衍生决议
├── src/             # 我们的代码：edit_runner / think_budget / steer / probes / metrics
├── data/            # 清洗后数据集 + 数据卡
├── experiments/     # 每实验一个 yaml 配置（模型/编辑器/预算/种子全显式）
├── results/         # jsonl 输出，命名 {model}_{editor}_{dataset}_{b}_{seed}.jsonl
└── paper/           # LaTeX（AAAI-27 author kit）
```

- 可复现三件套：全局种子显式、每个 jsonl 头部写入 git commit hash + 配置摘要、所有图表由 `src/plots.py` 从 results/ 一键再生
- 评测与生成解耦：CoT 文本是一等资产，先存后析
- 第三方代码只读引用，需要改的部分 fork 进 `src/vendor_patches/` 并记录 diff

---

## 7. 风险登记

| 风险 | 概率 | 缓解 |
|---|---|---|
| 撞车（6/10 后出现同命题论文） | 高 | 每周一 arXiv 增量扫描（§8 关键词）；若被抢现象，pivot 强调机理+修补（方法论文化）；若机理也被抢，剩余素材转 workshop |
| pilot 不成立 | 中 | §9 fallback，12 天沉没成本封顶 |
| ROME/MEMIT 在 R1-Distill 上编辑质量本身不达标（Locality 崩） | 中 | 注意 R1-Distill-Qwen-7B 基座是 Qwen2.5-**Math**-7B（非通用版），EasyEdit qwen2.5-7b hparams 仅架构兼容、超参未必最优：冒烟期做 layers 小扫描（实测 layer 5>7>10，已锁 layer 5），合格线＝**在 Locality≥85% 前提下取生成式 B0 ES_b 最高的层**（best-achievable，**判生成式 ES_b 不判 rewrite_acc**——v1.18 实测 rewrite_acc≈1.0 但生成式 ES_b≈0.55 有真实口径差；原『ES≥90%』是 rewrite_acc 数字误植到生成式口径、v1.18 改；08 旧引用 6/8 vs 0/8 系 sequential_edit bug 污染值作废）；仍偏低则先调 `v_lr/v_num_grad_steps` 或换层，再不行以 Qwen2.5-7B-Instruct（同架构非推理版）验证编辑质量基线，主模型改 Qwen3-8B |
| 排队完全拿不到卡 | 中 | 云端逃生 $400 预算；pilot 仅需一个 4–6h 窗口，优先抢 |
| Qwen3 编辑不兼容 | 中 | 6/27 检查点降级预案已写入 Phase 2 |
| 7 页装不下三段式 | 低 | 机理细节与第二数据集进附录；正文保 RQ1+RQ3 完整 |

## 8. 查新维护（每周一执行，30 分钟）

arXiv 关键词组：`knowledge editing + reasoning model`；`edit + chain-of-thought + revert/override`；`test-time compute + knowledge`；`unlearning + reasoning leakage`；`R1 + editing`。盯防对象：zjunlp（EasyEdit 组）、OPTML-Group、ai-isl（R-TOFU 组）、2602.02028 作者组的新作。

## 9. Fallback：方向 A 重启简案（仅 no-go 时启用）

推理链内部信号早停（hidden-state probe 预测链成败 → early-exit/重路由）。资产复用率高：think_budget 控制器、vLLM 管线、CoT 缓存、探针代码全部直接迁移；重启后 4 周压缩计划（1 周 pilot、2 周主实验、1 周写作），牺牲机理深度保 phenomenon+method 两段式。届时另出 plan_A.md。

---

## 10. 立即行动（本周）

1. [ ] 全员注册 OpenReview（防新账号审核延迟）
2. [ ] 核对 AAAI-27 官方 CFP 的 Alignment track 专属日期与 author kit
3. [ ] Phase 0 启动：`analysis/01_easyedit.md`（容器内环境 + GPT-2 CPU 冒烟）
4. [ ] H200 排队申请：W2 一个 6 小时 8 卡窗口（pilot 用），W3 起每周两个窗口

---

## 11. 附录 · 源码实测事实（2026-06-10 确认，写代码时以此为准）

### 11.1 EasyEdit 关键路径（`source/EasyEdit/`，最后提交 2026-06-10）

- hparams 已存在且无需新写：`hparams/ROME/qwen2.5-7b.yaml`、`hparams/MEMIT/qwen2.5-7b.yaml`、`hparams/AlphaEdit/qwen2.5-7b.yaml`
- MEMIT/AlphaEdit 共同配置（移植到 R1-Distill 时仅改 `model_name`，其余先沿用再扫描）：`layers: [4,5,6,7,8]`；`rewrite_module_tmp: "model.layers.{}.mlp.down_proj"`；`mom2_dataset: wikipedia, n=100000, float32`；AlphaEdit 额外需要 `P_loc: ./null_space_project.pt`（首跑生成）
- 编辑 API（`edit.py` 实测）：`BaseEditor.from_hparams(hparams)` → `editor.edit(prompts, ground_truth, target_new, sequential_edit=False)`，返回 `(all_metrics, edited_model, weights_copy)`（editor.py:288）
- **权重还原机制（已审计确认，01 笔记 §3）**: `weights_copy` 仅克隆被改写矩阵（rome_main.py:39-50，MEMIT 5 层 ≈650MB 显存）；还原为逐元素精确拷回 `nethook.get_parameter(model, k)[...] = v`（editor.py:265 模式）。单条编辑循环 = edit → 全档生成 → restore，正确性成立

### 11.2 思考预算控制（`source/R-TOFU/` 实测）

- 聊天模板（`test_cot.py:243-245`，注意全角竖线）：`<｜User｜>{prompt}<｜Assistant｜><think>\n`，无 system prompt
- ZeroThink/LessThink 的 prefill 实现在 `test.py:15-20`（闭合 think 块预填充）；CoT 抽取按 `<think>…</think>` 切片（`test_cot.py:250-253`）
- ExtendThink 实现要点（s1 式）：流式监测 `</think>`，命中即替换为 `\nWait, let me double-check this.` 续写，最多 2 次
- **(v1.3 补)** base 模型 = `DeepSeek-R1-Distill-Llama-8B`（**非 Qwen**，`config/tofu.yaml:2`）；上述三 prefill 串已逐字校验进 `src/think_budget.py`；`<think>`/`</think>` 两模型均非特殊 token，B4 走文本检测——详见 `analysis/03_rtofu.md` §3–§4

### 11.3 Phase 0 容器冒烟脚本（完整代码，落 `src/smoke_rome_gpt2.py`）

```python
from easyeditor import BaseEditor, ROMEHyperParams

hparams = ROMEHyperParams.from_hparams('./hparams/ROME/gpt2-xl')
hparams.device = 'cpu'                      # 容器无 GPU
editor = BaseEditor.from_hparams(hparams)
metrics, edited_model, _ = editor.edit(
    prompts=['The Eiffel Tower is located in'],
    ground_truth=['Paris'],
    target_new=['Rome'],
    sequential_edit=False,
)
print(metrics)
```
运行：`cd source/EasyEdit && pip install -r requirements.txt && python ../../src/smoke_rome_gpt2.py`
预期：输出 metrics 中 `rewrite_acc == 1.0`（CPU 约 10–20 分钟）。任何依赖坑记入 `analysis/01_easyedit.md` 的雷点登记。

### 11.4 工作区同步纪律

本工作区存在多写入端（本地 Claude Code 会话 + 网页会话容器镜像）。规则：**plan.md 与 analysis/ 笔记以本地仓库为唯一真源**，容器侧产出一律经 outputs 交付后由人工合入本地并 git commit；版本号与变更记录写在 plan.md 头部，避免双端覆盖。

---

## 12. 附录 · Pilot Harness 完整实现（v0，三模块，落 `src/`）

约定：分片并行按 `case_id % 8 == GPU_RANK` 切 8 片，每片独占 1 卡；jsonl 追加写 + 启动时跳过已完成 case_id（可中断续跑）。代码以 §11 实测 API 为准，跑通后 `pip freeze > env.lock`。

### 12.1 `src/think_budget.py` — 思考预算控制器（B0–B4）

> **v1.3 注**：下方为 v0 基线快照；现行实现以 `src/think_budget.py` 为准（已按 `analysis/03_rtofu.md` §3–§4 用 R-TOFU 逐字 prefill 替换占位、`_gen` 解码改 `skip_special_tokens=True`）。

```python
import torch

TPL = "<｜User｜>{q}<｜Assistant｜><think>\n"   # 全角竖线，DeepSeek 官方模板
THINK_END = "</think>"
WAIT = "\nWait, let me double-check this."
CAP = {"B1": 256, "B2": 1024, "B3": 8192, "B4": 8192}

def _gen(model, tok, text, max_new):
    ids = tok(text, return_tensors="pt").to(model.device)
    out = model.generate(**ids, max_new_tokens=max_new, do_sample=False,
                         pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][ids["input_ids"].shape[1]:],
                      skip_special_tokens=False)

def _ntok(tok, s):
    return len(tok(s, add_special_tokens=False)["input_ids"])

def generate_with_budget(model, tok, q, budget):
    """返回 (cot, answer, full_text)。budget ∈ {B0,B1,B2,B3,B4}"""
    if budget == "B0":                      # ZeroThink: 闭合空思考块
        text = TPL.format(q=q) + "\n" + THINK_END + "\n\n"
        ans = _gen(model, tok, text, 256)
        return "", ans, text + ans
    prefix, cot, waits = TPL.format(q=q), "", 0
    while True:
        chunk = _gen(model, tok, prefix + cot,
                     max(64, CAP[budget] - _ntok(tok, cot)))
        if THINK_END in chunk:              # 模型自行结束思考
            head = chunk.split(THINK_END)[0]
            if budget == "B4" and waits < 2:       # s1 式强制延长
                cot += head + WAIT; waits += 1; continue
            cot += head; break
        cot += chunk
        if _ntok(tok, cot) >= CAP[budget]: break   # B1/B2 截断 / 预算耗尽
    text = prefix + cot + "\n" + THINK_END + "\n\n"
    ans = _gen(model, tok, text, 256)
    return cot, ans, text + ans
```

注意点（v1.3 定案，证据见 `analysis/03_rtofu.md` §4）：① 已查实 `<think>`/`</think>` **非**特殊 token（不在 R1-Distill-Qwen-7B / -Llama-8B 的 `added_tokens_decoder`），原 `skip_special_tokens=False` 的理由（怕被剥）作废，现行 `think_budget.py` 解码改 `skip_special_tokens=True`（顺带滤 EOS，避免污染规则判分）；② B4 的 `</think>` 检测**确定走文本**（`THINK_END in chunk`），无需 token-id 级 StoppingCriteria。

### 12.2 `src/edit_loop.py` — 单条编辑协议主循环

```python
import json, os, torch
from easyeditor import BaseEditor, ROMEHyperParams, MEMITHyperParams
from easyeditor.util import nethook
from think_budget import generate_with_budget

HP_CLS = {"ROME": ROMEHyperParams, "MEMIT": MEMITHyperParams}

def restore(model, weights_copy):           # editor.py:265 同款
    with torch.no_grad():
        for k, v in weights_copy.items():
            nethook.get_parameter(model, k)[...] = v

def probes(case):                            # 探针：efficacy/paraphrase/locality/open
    yield "efficacy", case["prompt"]
    for i, p in enumerate(case.get("paraphrases", [])[:2]):
        yield f"para{i}", p
    if case.get("neighborhood"):
        yield "locality", case["neighborhood"][0]
    yield "open", f"Tell me about {case['subject']}."

def run(cases, editor_name, hparams_path, budgets, out_path, rank=0, world=1):
    done = set()
    if os.path.exists(out_path):
        done = {json.loads(l)["case_id"] for l in open(out_path)}
    hp = HP_CLS[editor_name].from_hparams(hparams_path)
    ed = BaseEditor.from_hparams(hp)
    model, tok = ed.model, ed.tok
    with open(out_path, "a") as f:
        for c in cases:
            if c["case_id"] % world != rank or c["case_id"] in done:
                continue
            _, _, wcopy = ed.edit(prompts=[c["prompt"]],
                                  ground_truth=[c["o_old"]],
                                  target_new=[c["o_new"]],
                                  sequential_edit=False)
            try:
                for b in budgets:
                    for ptype, q in probes(c):
                        cot, ans, _ = generate_with_budget(model, tok, q, b)
                        f.write(json.dumps({"case_id": c["case_id"],
                            "editor": editor_name, "budget": b, "probe": ptype,
                            "q": q, "cot": cot, "answer": ans},
                            ensure_ascii=False) + "\n")
                f.flush()
            finally:
                restore(model, wcopy)        # 任何异常也必须还原
```

### 12.3 `src/metrics.py` — ES / RR / CLR 计算（规则判分 + 别名表）

```python
import json, collections

def hit(text, target, aliases):
    cands = [target] + aliases.get(target, [])
    return any(c.lower() in (text or "").lower() for c in cands)

def score(jsonl_path, cases, aliases):
    cmap = {c["case_id"]: c for c in cases}
    by = collections.defaultdict(dict)       # case_id -> budget -> efficacy行
    for line in open(jsonl_path):
        r = json.loads(line)
        if r["probe"] == "efficacy":
            by[r["case_id"]][r["budget"]] = r
    es = collections.Counter(); rr = collections.Counter()
    clr = collections.Counter(); n = collections.Counter(); n_b0 = 0
    for cid, buds in by.items():
        c = cmap[cid]
        b0ok = ("B0" in buds
                and hit(buds["B0"]["answer"], c["o_new"], aliases)
                and not hit(buds["B0"]["answer"], c["o_old"], aliases))
        n_b0 += b0ok
        for b, r in buds.items():
            n[b] += 1
            es[b] += (hit(r["answer"], c["o_new"], aliases)
                      and not hit(r["answer"], c["o_old"], aliases))
            clr[b] += hit(r["cot"], c["o_old"], aliases)
            if b0ok and hit(r["answer"], c["o_old"], aliases):
                rr[b] += 1                    # 条件回退（plan §2.5 定义）
    return {b: {"ES": es[b]/n[b], "CLR": clr[b]/n[b],
                "RR": rr[b]/max(n_b0, 1), "n": n[b]} for b in sorted(n)}
```

判分校准：抽 10% 边界样本人工/judge 复核（plan §2.5）；别名表 `data/aliases.json` 由 CounterFact 实体的 Wikidata 别名生成（06 号数据笔记任务）。
