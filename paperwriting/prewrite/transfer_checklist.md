# Phase 4 clean-room 迁移检查表（v1.0.1）

来源版本：Phase 3 v1.0.1（evidence map 同版）；Tier 2 完整记录恢复。

用途：供 W3 对 AAAI-27 稿件做形式层复查；只核对既有文本的功能、位置与边界，不生成、改写或补写 title、abstract、TL;DR、正文。

状态：本表全部依据均为 `RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`，只能作为临时未认证的检查信号，不能当作质量标准、venue norm 或科学结论。Tier 1、Contrast、Tier 2、Tier 3 的分母始终分列；“未报告/未编码”不等于 `0`。

使用边界：冻结标题、冻结主 claim、C1/C2/C3、禁语与证据上限无条件优先；禁语与证据上限只回查 `target_profile.md` 指向的权威冻结源，本表不复述。Abstract 仅在该 profile 记载的 form-level reopen 窗口内允许非实质性动作；窗口关闭后视为不可动。任何检查若会新增科学 claim、扩大证据范围、改变因果/泛化强度、引入目标论文数字或与冻结件冲突，立即停止并按“不可动”处理。

## 1. Abstract（含 TL;DR，置顶）

- [ ] 逐 beat 看，首个有命题内容的 ordered beat 是否含 `CONTEXT`；若没有，是否仅记录而未为匹配频率补写内容？【来源 claim ID：T1-001、T2-001、T3-001｜分层 n/N：Tier1 `12/14`；Contrast `未报告/2`；Tier2 `85/106`；Tier3/L02 `39/54`｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：只作首 beat 功能覆盖检查；允许多标签、重复 beat，不推出固定句数或顺序｜AAAI-27 非实质性修改：可动（仅句界或不改语义的局部次序；冻结冲突即不可动）】
- [ ] 逐 beat 看，是否至少可定位一处相邻 `APPROACH→RESULT`；不可定位时，是否避免强排或补造该相邻关系？【来源 claim ID：T1-002、T2-002、T3-002｜分层 n/N：Tier1 `9/14`；Contrast `未报告/2`；Tier2 `66/106`；Tier3/L02 `41/54`｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：检查“至少一处”相邻关系，不要求每个 APPROACH 后接 RESULT，也不设唯一顺序｜AAAI-27 非实质性修改：可动（仅不改 claim/evidence 的断句或局部排序；否则不可动）】
- [ ] 逐 beat 看，末个 ordered beat 是否含 `IMPLICATION`；若不含，是否未据频率把现有结论抬高为影响性断言？【来源 claim ID：T1-003、T2-003、T3-003｜分层 n/N：Tier1 `8/14`；Contrast `未报告/2`；Tier2 `62/106`；Tier3/L02 `30/54`｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：只检查末 beat 功能；IMPLICATION 可缺失、重复或与其他标签共存｜AAAI-27 非实质性修改：不可动（新增或强化 implication 会改变 claim 强度）】
- [ ] 对每个 claim-bearing beat，epistemic hedge 是否只作用于其实际 claim span，而没有把整篇统一“降调”或“升调”？【来源 claim ID：T1-004、T2-004、T3-004｜分层 n/N：Tier1 任一 `H1–H3` 为 `10/14`；Contrast `未报告/2`；Tier2 `27/106`；Tier3/L02 `24/54`｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：层间差异仅作逐 beat 作用域检查，不作统一风格目标｜AAAI-27 非实质性修改：不可动（增删 hedge 或改变作用域可能改变 claim 强度）】
- [ ] 末 beat 的现有 hedge 等级是否与其冻结 claim 边界一致，而非因为多数频率被强制改为 `H0_NONE`？【来源 claim ID：T1-005、T2-005、T3-005｜分层 n/N：Tier1 末 beat `H0_NONE` 为 `8/14`；Contrast `未报告/2`；Tier2 `95/106`；Tier3/L02 `43/54`｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：只核对末 beat；不得把观察频率解释为无 hedge 偏好｜AAAI-27 非实质性修改：不可动（不得据形式观察改变确定性）】
- [ ] 逐句检查现有数字时，是否只有直接承担当前工作 asserted predicate、且位于合格功能 beat 的数字才被视为 headline；其他数字是否未被误升格？【来源 claim ID：T1-006、T2-006、T2-007、T3-006、T3-007｜分层 n/N：Tier1 无 headline `10/14`（有 `4/14`，F03 仅摘要）；Contrast `未报告/2`；Tier2 无 headline `74/106`，含 headline 的论文中摘要承载 `32/32`（全层 `32/106`，标题来源另有单例）；Tier3/L04 无 headline `55/66`，摘要承载 `11/11`（全层 `11/66`）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：只核对既有数字的功能与来源；“出现数字”不等于 headline｜AAAI-27 非实质性修改：不可动（不得新增、删除、替换目标论文数字或改变数字所承载断言）】
- [ ] 对每个现有命名装置所在句/beat，是否能定位显式命名、展开或当前工作复用依据；不能定位时，是否未因频率把普通术语升级为装置？【来源 claim ID：T1-007、T1-008、T2-008、T2-009、T3-008、T3-009｜分层 n/N：Tier1 合格装置 `8/14`，形式按论文可重叠为 ACRONYM `5/14`、COINED_NAME `3/14`、DESCRIPTIVE_LABEL `1/14`；Contrast `未报告/2`；Tier2 合格装置 `82/106`，形式 `49/106、39/106、14/106`，摘要/标题来源 `82/106、2/106`；Tier3/L03 合格装置 `39/66`，形式 `17/66、15/66、7/66`，摘要/标题来源 `35/66、5/66`｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：形式与来源可重叠；只审计已经存在的显式装置，不要求造名｜AAAI-27 非实质性修改：不可动（不得新增、改名或扩展装置含义）】
- [ ] 逐句/beat 盘点后，长度与密度是否仅被用作篇幅预警，而没有把任一中位数当作句数、词数或 beat 数模板？【来源 claim ID：T1-009、T2-010、T3-010｜分层 n/N：Tier1 可用摘要 `14/14`，句数中位数 `8`、总词数 `197.5`、词/句 `25.12`、beat/句 `1.12`；Contrast `未报告/2`；Tier2 `106/106`，对应中位数 `8、181.5、23.22、1.00`；Tier3/L02 `54/54`，对应中位数 `8、190、23.82、1.00`｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：只用于总量预警；中位数不是目标值或模板｜AAAI-27 非实质性修改：可动（仅删冗、断句或合句，且语义、数字、claim 强度均不变）】
- [ ] 若存在 TL;DR，逐句/beat 是否都能回联到摘要已有的 `CONTEXT`、`APPROACH`、`RESULT` 或 `IMPLICATION` 功能及同一冻结 claim 层级，且没有新增摘要外断言？【来源 claim ID：T1-001、T1-002、T1-003、T2-001、T2-002、T2-003、T3-001、T3-002、T3-003｜分层 n/N：Abstract 的 Tier1 `12/14、9/14、8/14`；Contrast `未报告/2`；Tier2 `85/106、66/106、62/106`；Tier3/L02 `39/54、41/54、30/54`；TL;DR 本身各层均 `未编码`｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：仅存在 TL;DR 时；摘要证据只作回联检查，不外推为 TL;DR 频率｜AAAI-27 非实质性修改：可动（仅删除重复或恢复与摘要的一致性；新增/强化内容不可动）】
- [ ] 若存在 TL;DR，其每个 claim-bearing beat 的 hedge、数字与命名是否完全受摘要和冻结件约束，没有更强、更广或新增的表达承载？【来源 claim ID：T1-004、T1-005、T1-006、T1-007、T2-004、T2-005、T2-006、T2-008、T3-004、T3-005、T3-006、T3-008｜分层 n/N：Abstract 的 Tier1 `10/14、8/14、10/14、8/14`；Contrast `未报告/2`；Tier2 `27/106、95/106、74/106、82/106`；Tier3/L02 hedge `24/54、43/54`，Tier3/L04 无 headline `55/66`，Tier3/L03 命名 `39/66`；TL;DR 本身各层均 `未编码`｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：仅存在 TL;DR 时；只检查与摘要/冻结件一致，不为 TL;DR 生成形式规则｜AAAI-27 非实质性修改：不可动（改变 hedge、数字、命名或 claim 范围均可能实质化）】

### 不可迁移项

- [ ] 是否未迁移固定句数、固定 beat 数或唯一“开局—推进—收束”顺序？【来源 claim ID：T1-001、T1-002、T1-003、T1-009、T2-001、T2-002、T2-003、T2-010、T3-001、T3-002、T3-003、T3-010｜分层 n/N：Tier1 功能 `12/14、9/14、8/14`、密度输入 `14/14`；Contrast `未报告/2`；Tier2 功能 `85/106、66/106、62/106`、密度输入 `106/106`；Tier3/L02 功能 `39/54、41/54、30/54`、密度输入 `54/54`｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：所有 Abstract/TL;DR 检查；多标签、重复和缺失均保留｜AAAI-27 非实质性修改：不可动（不得为套模板触发改写）】
- [ ] 是否未迁移“必须加入 headline 数字”或“必须把数字放入摘要/TL;DR”的规则？【来源 claim ID：T1-006、T2-006、T2-007、T3-006、T3-007｜分层 n/N：Tier1 无 headline `10/14`；Contrast `未报告/2`；Tier2 无 headline `74/106`、摘要承载 `32/32` carriers；Tier3/L04 无 headline `55/66`、摘要承载 `11/11` carriers｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：所有数字检查；来源分布不构成增补要求｜AAAI-27 非实质性修改：不可动（禁止据此增删目标论文数字）】
- [ ] 是否未迁移“必须造名、缩写或复用名称”的规则？【来源 claim ID：T1-007、T1-008、T2-008、T2-009、T3-008、T3-009｜分层 n/N：Tier1 合格装置 `8/14`；Contrast `未报告/2`；Tier2 `82/106`；Tier3/L03 `39/66`｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：命名装置只在已有充分依据时检查；形式类别可重叠｜AAAI-27 非实质性修改：不可动（禁止据此命名或改名）】
- [ ] 是否未把各层 hedge 频率合并成统一降调、升调或末 beat 无 hedge 的规则？【来源 claim ID：T1-004、T1-005、T2-004、T2-005、T3-004、T3-005｜分层 n/N：Tier1 `10/14、8/14`；Contrast `未报告/2`；Tier2 `27/106、95/106`；Tier3/L02 `24/54、43/54`｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：hedge presence 为层间差异观察，只能逐 claim-bearing beat 判断｜AAAI-27 非实质性修改：不可动（禁止据频率改变 claim 强度）】

## 2. Introduction（W3 复查）

- [ ] 首个视觉段落是否可定位 `BACKGROUND` 功能；若不可定位，是否未为匹配全样本频率补写背景？【来源 claim ID：T1-010｜分层 n/N：Tier1 `14/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：仅锁定 Introduction 范围内的首段；全文字段只由 Tier1 支持｜AAAI-27 非实质性修改：可动（仅移动既有背景句或调整段界，且不改 claim；无现成内容则不可动）】
- [ ] Introduction 中是否可定位把 problem/gap 转向当前工作行动、问题或判断的显式 `HINGE`；其位置是否只作可定位检查而非命中某个比例？【来源 claim ID：T1-011｜分层 n/N：Tier1 presence `14/14`，最早规范位置中位数 `0.296`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：必须有显式转向命题；中位位置不是段落配额｜AAAI-27 非实质性修改：可动（仅移动既有 hinge 或调整段界；不得新造科学命题）】
- [ ] Introduction 中是否可定位 `RESULT_PREVIEW`，且预告范围没有超出冻结主 claim 与 C1/C2/C3？【来源 claim ID：T1-012｜分层 n/N：Tier1 `14/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：只检查既有结果预告的位置与冻结范围，不要求补齐缺失内容｜AAAI-27 非实质性修改：可动（仅移动或压缩已有预告；扩大、强化或新增结果不可动）】
- [ ] 若已有 `CONTRIBUTION_LIST`，各项是否只回联到冻结 C1/C2/C3，且列表格式没有制造新的贡献层级？【来源 claim ID：T1-012｜分层 n/N：Tier1 `10/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：仅在已有 contribution list 时；`10/14` 不构成必备要求｜AAAI-27 非实质性修改：可动（仅列表排版、顺序或去重；新增贡献不可动）】

### 不可迁移项

- [ ] 是否未迁移固定段落同构、固定 hinge 位置或“背景—hinge—预告”逐段一一对应模板？【来源 claim ID：T1-010、T1-011、T1-012｜分层 n/N：Tier1 `14/14、14/14、14/14`，hinge 最早位置中位数 `0.296`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：只检查三个功能是否可定位，不要求逐段同构｜AAAI-27 非实质性修改：不可动（不得为模板重写 Introduction）】
- [ ] 是否未迁移“必须列贡献清单”，也未把 Tier1 全文观察外推到 Contrast、Tier2 或 Tier3？【来源 claim ID：T1-012｜分层 n/N：Tier1 contribution list `10/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：贡献清单可缺失；轻量层不支持 Introduction 结论｜AAAI-27 非实质性修改：不可动（不得据缺失补写或据单层抬高规律）】

## 3. Figure 1（W3 复查）

- [ ] 正文是否已有可定位的 Figure 1；若没有，是否未因 Tier1 `14/14` 的 presence 强行新增或改号？【来源 claim ID：T1-013｜分层 n/N：Tier1 PRESENT `14/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：仅主文、References/Appendix 之前编号恰为 Figure/Fig. 1 的对象；全文字段只由 Tier1 支持｜AAAI-27 非实质性修改：不可动（不得据频率新增、替换或改号）】
- [ ] 对现有 Figure 1，是否只能从已有内容定位其实际承担的一项或多项功能，且没有预设其必须是流程图或单一功能图？【来源 claim ID：T1-013｜分层 n/N：Tier1 按论文多标签为 PRIMARY_RESULT `7/14`、DATA_TASK_EXAMPLE `5/14`、CONCEPT_OVERVIEW `5/14`、METHOD_PIPELINE `2/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：仅按论文计，功能可重叠；未编码逐-panel 覆盖，不要求每个 panel 或选定某类｜AAAI-27 非实质性修改：可动（仅不改科学内容的布局、标签层级或视觉次序）】
- [ ] 现有 caption 单独阅读时，是否能识别对象、视觉编码/轴或比较关系、以及图所表达内容；补足时是否只使用图中和正文已有信息？【来源 claim ID：T1-014｜分层 n/N：Tier1 FULL `9/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：只检查 caption 自足度；FULL 不是新增科学信息的许可｜AAAI-27 非实质性修改：可动（仅补已有对象/编码/内容的指代；新增结论、数字或范围不可动）】

### 不可迁移项

- [ ] 是否未迁移“Figure 1 必须是 method pipeline”或任何单一功能模板？【来源 claim ID：T1-013｜分层 n/N：Tier1 METHOD_PIPELINE `2/14`，另有 PRIMARY_RESULT `7/14`、DATA_TASK_EXAMPLE `5/14`、CONCEPT_OVERVIEW `5/14`（可重叠）；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：Figure 1 可承担不同任务；分布不形成唯一范式｜AAAI-27 非实质性修改：不可动（不得为匹配功能类别重做科学图）】
- [ ] 是否未把 FULL caption 频率当作扩写结果、补数字或补科学解释的依据？【来源 claim ID：T1-014｜分层 n/N：Tier1 FULL `9/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：caption 自足只涉及已有对象、视觉编码/关系与所表达内容｜AAAI-27 非实质性修改：不可动（禁止借自足度新增证据或 claim）】

## 4. Results（W3 复查）

- [ ] 是否存在按标题锁定的适用 Results 范围；若不存在，是否保留不适用状态而未自由挑选其他“结果性”段落？【来源 claim ID：T1-015｜分层 n/N：Tier1 适用 `12/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：只检查规范 Results/Experiments/Evaluation/Analysis/Findings 顶层范围；全文字段只由 Tier1 支持｜AAAI-27 非实质性修改：可动（仅章节标题或边界标识；不得搬入新证据）】
- [ ] 若作者已有组织句，结果单元顺序是否与其明示轴一致；若没有，是否仅保留文档顺序而未补造排序轴？【来源 claim ID：T1-015｜分层 n/N：Tier1 AUTHOR_EXPLICIT `6/14`、DOCUMENT_ORDER_ONLY `6/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：仅 F09 适用论文；作者组织句优先，无组织句不推断轴｜AAAI-27 非实质性修改：可动（仅按已有组织句调整现有单元次序；新增组织 claim 不可动）】
- [ ] 现有主表是否可按既有作者标识或 claim–evidence 关系定位；无法定位时，是否未因 `11/14` 强行指定一张表？【来源 claim ID：T1-015｜分层 n/N：Tier1 主表可定位 `11/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：只检查已有表与已有关系；主表允许不可定位｜AAAI-27 非实质性修改：可动（仅标签、引用或位置；更换数据、数字或证据角色不可动）】

### 不可迁移项

- [ ] 是否未迁移“结果必须按某一闭集轴排序”或在没有作者组织句时补造排序逻辑？【来源 claim ID：T1-015｜分层 n/N：Tier1 AUTHOR_EXPLICIT `6/14`、DOCUMENT_ORDER_ONLY `6/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：有作者组织句才沿用；缺失时不从观察频率推导偏好｜AAAI-27 非实质性修改：不可动（禁止补造排序 claim）】
- [ ] 是否未迁移“必须有主表”，也未把 Tier1 的 Results 观察外推到其他层？【来源 claim ID：T1-015｜分层 n/N：Tier1 主表可定位 `11/14`、F09 适用 `12/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：主表与 Results 范围均允许不可定位/不适用；轻量层不支持全文结论｜AAAI-27 非实质性修改：不可动（不得据频率新建、合并或升级表格）】

## 5. Limitations（W3 复查）

- [ ] 每个被计作 limitation/scope 的 span 是否明示适用边界、弱点、未知或拒绝外推，而不是仅有设置说明或负面结果？【来源 claim ID：T1-016｜分层 n/N：Tier1 有明示限制项 `14/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：只检查作者明示限制 span；设置和负面结果本身不足｜AAAI-27 非实质性修改：不可动（新增、删除或改变限制范围均属实质性风险）】
- [ ] 现有限制项的位置是否全部可定位；集中或分散的安排是否保持原有限制内容不变，而未为匹配 dedicated section 频率强制搬移？【来源 claim ID：T1-017｜分层 n/N：Tier1 有 dedicated section `10/14`，集中位置为 dedicated `5/14`，DISTRIBUTED `6/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：集中和分散均可；只检查现有限制项的位置与可定位性｜AAAI-27 非实质性修改：可动（仅移动原有限制句或标题，且作用域与强度完全不变）】
- [ ] 对每个限制 span，`DIRECT` 与 `HEDGED` 是否按实际局部作用域判断，且允许同篇重叠，而没有统一改成单一语气？【来源 claim ID：T1-016｜分层 n/N：Tier1 DIRECT `14/14`、HEDGED `12/14`（按论文多标签）；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：tone 按论文可重叠，逐限制 span 判断；不形成统一语气偏好｜AAAI-27 非实质性修改：不可动（改变 hedge 或 directness 可能改变限制强度）】
- [ ] 与冻结 C1/C2/C3 相连的现有限制是否都能回联到冻结边界，且没有越过 target profile 所指禁语或证据上限？【来源 claim ID：T1-016、T1-017｜分层 n/N：Tier1 明示限制 `14/14`、结构字段可评估 `14/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：只做与冻结件的回联；具体禁语和上限必须回权威冻结源，不在本表重建｜AAAI-27 非实质性修改：不可动（任何边界冲突均以冻结件为准）】

### 不可迁移项

- [ ] 是否未迁移“必须有 dedicated Limitations section”或“限制必须集中在一处”的规则？【来源 claim ID：T1-017｜分层 n/N：Tier1 dedicated section `10/14`、集中于 dedicated `5/14`、DISTRIBUTED `6/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：集中与分散均为观察到的结构；位置不是硬模板｜AAAI-27 非实质性修改：不可动（不得为模板重排全部限制）】
- [ ] 是否未把设置说明、负面结果或统一 hedge 当作明示限制的替代，也未把 Tier1 观察外推到其他层？【来源 claim ID：T1-016、T1-017｜分层 n/N：Tier1 明示限制 `14/14`、DIRECT `14/14`、HEDGED `12/14`、结构字段 `14/14`；Contrast `未报告/2`；Tier2 `未编码/106`；Tier3 `未编码/54`（L02）与 `未编码/66`（L03/L04）｜置信：`RELIABILITY_NOT_RUN / PROVISIONAL_UNCERTIFIED`｜适用条件：只有作者明示限制 span 可计；全文证据只来自 Tier1｜AAAI-27 非实质性修改：不可动（禁止用形式频率替代或改写科学边界）】
