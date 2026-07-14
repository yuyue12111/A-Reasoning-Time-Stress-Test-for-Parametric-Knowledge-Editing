# X3 · ROME-32B active paraphrase repair

日期：2026-07-12  
预注册：`prereg-x2-x3.md` §X3  
入口：`experiments/run_x3_h200.sh`

## 结果

fresh mp2 N/T/C 各 200 cases、32 shards、0 error。T/C 相对 N 的 B0 共 600 probe rows 逐字一致；B3 实际变化行 T=215、C=24，证明抑制接线生效且强竞争者控制接近惰性。

预注册主端点为 B3 下 para0+para1 的 strict paraphrase success（PS），行按 `(case_id, paraphrase_probe)` 配对，bootstrap 按 `case_id` 整簇重采样：

| 对比 | 两臂 PS | 配对差 | 95% CI | 结论 |
|---|---:|---:|---:|---|
| T−C | .4775 vs .4225 | +.0550 | [.0200,.0925] | PASS |
| C−N | .4225 vs .4200 | +.0025 | [−.0075,.0125] | 与 0 相容 |
| T−N | .4775 vs .4200 | +.0575 | [.0200,.0950] | 同向 |

因此 X3 的**确认性 T−C 主对比 PASS**。整数计数为 T=191/400、C=169/400、N=168/400。原脚本把 `C−N CI contains zero` 与 `T−N point>0` 也并入所谓“联合主门”；该联合逻辑现仅作历史审计：CI 含零不是等价检验，T−N 点估为正也不是独立显著性门。`src/cross_arm_para.py` 已改为只由 T−C CI 下界大于 0 决定主端点，并在未给事前等价界时把 C−N 标为 `COMPATIBLE_WITH_ZERO / equivalence NOT_TESTED`。

## 次级边界

固定 N-B0 成功门只有 110 cases/145 rows，低于预注册的 140-case 确认性阈值。strict old-only 的 T−C 为 −.0138 [−.0420,+.0137]，含零；只能作为 directional/null 结果。

代码字段 `old_commit` 实际是 `hit(o_old) and not hit(o_new)` 的严格词法指标，不是 answer-only 判官的语义 commitment。写作须称 `strict old-only lexical rate`。

## 合法解释

X3 证明：把既有 think-only `o_old` suppressor **主动应用到**两个 CounterFact paraphrase probes 后，相比同关系强竞争者，严格词法 PS 提高 5.5pp；修复不只出现在原 rewrite prompt。

X3 不证明 passive paraphrase portability、语义 committed-old 显著下降、跨数据集/模型/编辑器泛化，也不证明 sequence-level 覆盖。干预直接压 `o_old` 而 PS 要求答案不含 `o_old`，所以这是与干预目标高度对齐的受控外部效度结果，不是新的机理闭环。按预注册它是 add-only，不进入 abstract。

## Provenance 边界

本地落库依据用户回传的 full audit、三臂 score、首版 cross-arm aggregate 与 v1.87 CPU refresh；附件 SHA256=`88df989a5f3a9b1bec69ca2bbd9632653c71dbb2c94fed7d13a6b775bc85f89b`。点估计与整数计数已独立复核；旧联合 gate 逻辑已被上述 inference correction 取代。本地仍无 per-case raw shards，因此不声称从原始生成逐条重算 CI；发布时必须保留服务器 raw 与 full audit。

v1.87 已回传 `results/x3_para_crossarm_v2.json`，SHA256=`ba2b3caaf365b56dc7cfb62a71d836f4fe6c56bc549f4e6e5fb2e0dcac4746ee`。它与首版 aggregate 的全部端点数值零漂移，只新增 sound decision 字段：T−C 是唯一确认门，C−N 为 non-gating/`NOT_TESTED` equivalence，T−N 为 descriptive。因此此前的 artifact-refresh pending 已闭合。v2 没有序列化 trajectory-aware duplicate audit，仍须保留 full audit 和 raw shards 作发布 provenance。

`results/x3_day0.json` 已回传并逐字落库，SHA256=`39592a0b42c60d1c72592a7c627afc7bc8967fe82780d0cba8320f7051f63346`。它是旧 `experiments/probe32b.yaml` 的 legacy N 审计：200 cases/8 shards，记录 10 个 error rows；B0 的 400/400 paraphrase rows 完整、PS=.3625，B3 只观察到 392/400 rows、missing=8(2%)、observed-row PS=.42347。按预注册它只是 Day-0/audit source，容量失败后最终必须采用 fresh-mp2 N/T/C，故 legacy N 的缺失不与主结果混池。

`results/x3_para_audit20.json` 也已回传，SHA256=`374efa6d6156809c5e11cd3f39ca4b2ba938745e8da75170aa5084e03de0d035`。该文件冻结 seed42 的 20 个 unique cases/40 paraphrases；已存在的 recorded question 均与冻结 paraphrase 逐字一致。legacy N 中 `cf_8371` 的 B3 para0/para1 缺失，故 question slots 为 78/80。

随后三名相互隔离的语义审计员逐条标注 `readable`、`answerable_same_fact`、`prefix_changes_requested_fact`，严格合并结果见 `results/x3_para_audit20_labels.json`，SHA256=`3c9eb3035059afa09f1fbecd06872bebc03c33e940e9ae3d76f17c265df300fb`。统计单位是 40 条 paraphrase；120 票是重复判定，不当作独立样本。

| 内容门 | Majority true | Raw pairwise agreement | Fleiss κ |
|---|---:|---:|---:|
| readable | 36/40 | 112/120=.933 | .630 |
| answerable_same_fact | 30/40 | 92/120=.767 | .444 |
| prefix_changes_requested_fact | 2/40 | 120/120=1.000 | 1.000 |

合取门 `readable AND answerable_same_fact AND NOT prefix-change` 仅 30/40 通过，且只有 11/20 cases 的两条 paraphrase 都通过。十条多数票未通过的 item 为：`cf_3952|para0`、`cf_17506|para0`、`cf_17506|para1`、`cf_14138|para0`、`cf_20733|para1`、`cf_8371|para1`、`cf_5076|para0`、`cf_2477|para0`、`cf_14464|para0`、`cf_9994|para0`。

这不是一个可忽略的程序性小问题：它直接否定“冻结的 40 条都是干净同事实 paraphrase”这个隐含前提，且 same-fact 判定只有中等一致度（κ=.444）。按预注册不得据此删 case或重算主门，因此 X3 的 lexical PS PASS 不变；但科学解释必须降为“抑制器主动接到 CounterFact 提供的 paraphrase strings 后，严格词法 PS 改善”，不能把它包装成 40/40 经人工认证的语义 paraphrase 泛化。
