# X1 Stage-0 · natural-chain fixed replay gate

日期：2026-07-11  
权威协议：`plan.md` v1.79 + `prereg-x1.md`  
运行入口：`experiments/run_x1_replay_h200.sh`

## 为什么 H200-A 跑这个

H200-B 已经用旧 all-ranks launcher 运行 X3，A 再碰 X3 会重复写 shard。X1 是既定优先级中的下一项，但五臂尚未具备科学上可用的 replay 载具。因此 A 先只跑 Stage-0：同一 32B ROME edit 下复现 fresh B0 安装，再逐字 prefill 一条事前冻结的自然回退链，只生成答案，验证 fixed replay 能否在至少 80% 的冻结 case 上重现 OLD commitment。

这只是载具有效性门，不是机理结果。PASS 后仍须另立 authored five-arm prereg；FAIL 则停止 X1。

## 冻结池

三个 7/10 前来源共有 33 个 unique case。严格执行“先 hierarchy 选源，再审该源自身票；低优先源不得救回”：

- main B3 greedy：17 个 priority-selected，10 eligible。
- F2-B1 greedy：10 个 priority-only，5 eligible。
- F3 historical sample：6 个 priority-only，3 eligible。
- 最终 `data/x1_replay_manifest.jsonl`：18 个，构成 10/5/3。

典型防错：`cf_12725` 有 main 高优先源但该源缺合格票，不能用其 F2/sample committed 票救回。

## sampling provenance bug

旧 `extract_reverted.py` 对 sampling 仅筛 `decode=sample`，随后以 `case_id→budget` 覆盖；生成写入顺序是 seed0→seed1→seed2。因此历史 `data/reverted_32b_samp.jsonl` 应对应最后的 seed2，而不是早期计划误写的 seed0。文件与 B16 三判官票均早于 X1，故本次不是按 replay outcome 选 seed，但必须公开记录偏差。

上卡硬门：`src/verify_x1_sample_source.py` 从共享盘 raw `cf200samp` 显式重建 seed2 的 B0/B3 reversion pool，要求 14/14 case IDs、CoT、answer 与历史导出一致。失败时 launcher 在模型加载前退出。

## 主门

每 case success：

1. fresh B0 answer strict 命中 NEW 且不含 OLD；并且
2. fixed-chain replay answer 经三名 answer-only 中性判官至少两票判最终承诺 OLD。

分母固定 18；技术缺失/不足两票均失败。PASS=至少 15/18。Wilson CI 只描述。规则 loose OLD / strict OLD-without-NEW 为敏感性，不替代判官。

## 资源与预期

- 32B fp32，ROME layer12，NO_BOS。
- 每进程 2×H200、四进程并行，`device_map=balanced`。
- smoke n=4；full n=18；每 case B0+replay 两次短答案生成，原链只作 prefill。
- 预计 45–90 分钟；任何 bf16、裁链、换层、换 seed 救援均禁止。

## 结果与终裁

技术/provenance 全部通过：

- historical sample raw seed2 重建：14/14 case IDs、CoT、answer 逐字一致。
- mp2 smoke：4/4、4 shards、0 error。
- full：18/18、4 shards、0 error。

因此下列失败不是容量、缺行或 manifest 漂移：

| 组件 | 结果 |
|---|---:|
| fresh B0 strict | 14/18 |
| replay answer 判官 OLD 多数 | 12/18 |
| 联合成功 `B0 strict ∧ judge OLD` | **9/18 = 50.0%** |
| 预注册门 | 15/18 = 83.3%（对应 ≥.80） |
| Wilson 95% CI（联合成功） | [.290, .710] |
| 规则 loose OLD 合取 | 14/18 |
| 规则 strict OLD-without-NEW 合取 | 9/18 |

三名 answer-only 判官共 54 票；17/18 case 全票一致，Fleiss κ=.920。replay 主端点即使不加 B0 条件也只有 12/18=.667，故 FAIL 不依赖“额外加严的 B0 sanity”。loose 字符串规则给 14/18，是因为把 5 条同时提及/犹豫答案算作 OLD；中性最终承诺判官将其中一部分裁为 neither/new。

来源分解：

- main：B0 10/10、judge OLD 6/10、联合 6/10。
- F2-B1：B0 1/5、judge OLD 4/5、联合 1/5。
- historical sample seed2：B0 3/3、judge OLD 2/3、联合 2/3。

这暴露两个不同问题：F2 priority-only case 的编辑安装跨运行极不稳定；而在 B0 可复现的 case 中，逐字 replay 原自然链也常只得到 hedged/both/neither，而非最终 OLD commitment。

终裁：**X1 Stage-0 FAIL，五臂停止。** 不保留成功 9 条继续、不换 seed、不截链、不调层/answer cap、不扩池。合法结论只是否定本投稿窗口内这套 fixed-replay 识别载具的稳定性；不能据此否定一般意义上的 chain semantics 因果作用。

