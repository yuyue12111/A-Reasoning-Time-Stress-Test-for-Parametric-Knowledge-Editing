# P0 · answer-only membership re-audit

日期：2026-07-13  
预注册：`prereg-p0-membership.md`  
实现：`src/p0_membership.py`

## 技术审计

用户声明的 `results/p0_judge1.jsonl`、`judge2`、`judge3` 实际落盘名为 `results/p0_judgeJUDGE_1.jsonl`、`p0_judgeJUDGE_2.jsonl`、`p0_judgeJUDGE_3.jsonl`。三份原始文件均为 101 行、101 个唯一 `item_id`，与 `results/p0_membership_sample.jsonl` 及 `results/p0_membership_prompts.jsonl` 的集合和顺序逐行一致；所有 `committed` 均严格属于 `old/new/neither`，reason 均为非空字符串，无缺行、重复、无效标签、JSON 错误或格式污染。

原始文件 SHA256：

- sample：`13ebe1db80b871ad8d465bac0a9f4bc657e6d209bc1e3b13194e97ffdbbd0dee`
- prompts：`af308481fbbf3a3bd4ecbc322730d7422db3b83cb4057591b03744ede0a44b93`
- J1：`a39d7e675d70e8913b531970f7549a9b725944803917bb6de6fa2e4f3dc69acb`
- J2：`e4f6a26b1bd73aefba22084911a652a1cae2a4fa3e4dcd7387cd6ac6de1ba6d8`
- J3：`216869710864bbc5f1f202171173a5f0c099ed2871f1d0cee19fcaf41ed90eae`

严格合并产物为 `results/p0_membership_verdicts.jsonl`，101 行，SHA256=`2f6802501e4748e38e50b07e8ffd1a1ea1df426158db5b7d1169013c3e9e9981`。原始审计见 `results/p0_membership_raw_audit.json`，SHA256=`fe721803b6799d56684db6a1c8001654eb27c23de8763989ba90461b7197833b`。

## 三判官结果

| Judge | OLD | NEW | NEITHER |
|---|---:|---:|---:|
| J1 | 39 | 43 | 19 |
| J2 | 42 | 43 | 16 |
| J3 | 41 | 44 | 16 |

统计单位始终是 101 个 item，不把 303 票当独立样本：

- unanimous：97/101；
- 2–1 majority：4/101；
- 1–1–1 split：0；
- raw pairwise agreement：295/303=.973597；
- unanimity rate：97/101=.960396；
- membership Fleiss κ=.957788；
- majority OLD/NEW/NEITHER=41/43/17。

## Membership 转移

原 current-in-pop=50：40 条 majority OLD 复用旧 route votes，10 条 drop；原 excluded=51：50 条保持 excluded，1 条 majority OLD rescue，必须补三名 neutral route votes。

| Pool/cell | N | 原 in-pop | OLD | NEW | NEITHER | Keep | Drop | Rescue | Remain excluded |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a3/7b | 5 | 3 | 3 | 2 | 0 | 3 | 0 | 0 | 2 |
| a3/14b | 12 | 4 | 4 | 8 | 0 | 4 | 0 | 0 | 8 |
| a3/32b | 16 | 10 | 6 | 5 | 5 | 6 | 4 | 0 | 6 |
| b16/qwen1.5b-greedy | 5 | 2 | 1 | 2 | 2 | 1 | 1 | 0 | 3 |
| b16/llama8b-greedy | 15 | 7 | 5 | 6 | 4 | 5 | 2 | 0 | 8 |
| b16/qwen32b-F2B1 | 18 | 10 | 9 | 8 | 1 | 9 | 1 | 0 | 8 |
| b16/qwen32b-sample | 14 | 6 | 6 | 6 | 2 | 5 | 1 | 1 | 7 |
| b16/llama70b-greedy | 16 | 8 | 7 | 6 | 3 | 7 | 1 | 0 | 8 |
| **合计** | **101** | **50** | **41** | **43** | **17** | **40** | **10** | **1** | **50** |

十条 drop：

- `a3|32b|cf_19889`
- `a3|32b|cf_1235`
- `a3|32b|cf_14660`
- `a3|32b|cf_10410`
- `b16|qwen1.5b-greedy|cf_7744`
- `b16|llama8b-greedy|cf_3627`
- `b16|llama8b-greedy|cf_15609`
- `b16|qwen32b-F2B1|cf_140`
- `b16|qwen32b-sample|cf_390`
- `b16|llama70b-greedy|cf_9255`

唯一 rescue 为 `b16|qwen32b-sample|cf_15156`，membership votes=`[neither,old,old]`。其 source row 已按路径、1-based line、case ID 和 SHA256 重新核验，并用 `src/chain_classify.py:JUDGE_PROMPT_NEUTRAL` 冻结为 `results/p0_route_rescue_prompts.jsonl`，SHA256=`02332cef8feeecf3458f59505e98633345b7483da4290d361eeab7a94fb3c638`；文件同时携带 route judge output schema，不含旧 `Excluded-held` route votes。

## Membership 阶段停止边界

`results/p0_membership_audit.json` SHA256=`a5d32a19e1f71360fcc111eb5a52526484e831ad9c7eef5ef590d594bd5bab00`，其 `technical_status=PASS`、`missing_verdicts=[]`、`insufficient=0`、`drops=10`、`rescues_requiring_route_rejudge=1`。因为存在 rescue，顶层状态正确为 `ROUTE_REJUDGE_REQUIRED`，`corrected_taxonomy_status=PENDING_ROUTE_REJUDGE`。

因此在 membership 阶段，41/101 只代表 majority OLD，不能提前宣布 route taxonomy。该停止边界已严格执行：只对 `b16|qwen32b-sample|cf_15156` 补三名相互独立的 neutral route judges，未复用旧 `Excluded-held` 票、未筛 case、未启动 GPU。

## Route rescue 与最终 corrected taxonomy

三名补充 route judges 对 `cf_15156` 均投 `Bridge`。原始票为 `results/p0_route_judge1/2/3.jsonl`，合并票 `results/p0_route_rescue_verdicts.jsonl` SHA256=`3c44933d35ded1e8a98431acb646a9cedc4ce847973792f0ce48ebbcb00e441f`。`src/p0_finalize_routes.py` 重新聚合所有 40 条复用 route + 1 条 rescue route，得到 `results/p0_corrected_taxonomy.json`，SHA256=`c11c6a0e5a3ecddff6e18aca4f19cfd91c57d4ff88a83012c211b2aef8543290`：

| Route | n | % |
|---|---:|---:|
| Bridge | 27 | 65.85% |
| Recall | 11 | 26.83% |
| Reflective-override | 3 | 7.32% |
| Associative | 0 | 0% |
| **总计** | **41** | **100%** |

Route votes 中 unanimous=35、2–1=6、split=0，raw pairwise agreement=111/123=.902439，Fleiss κ=.812595。最终状态为 `PASS/COMPLETE`。

发布级 provenance 另加一层冻结锁：40 条 reused route 的三票顺序逐条与事前 `p0_membership_sample.jsonl:existing_route_votes` 比对，40/40 完全一致；不一致会 hard fail。上游 `results/a3_neutral/verdicts_all.jsonl` SHA256=`8cb06e96ebbdfd3e7c6e62bb71e4bc0c3e76a6c7ba3561a8f4891df8b2ee6208`，`results/b16_verdicts.json` SHA256=`b53eae02bc322af38a822c4430e2390664695c2c2d2bc7a267fc705bbe6a87fd`。

`src/chain_classify.py` 的发布默认也已加固：默认 prompt 改为 neutral，带 `STILL INSTALLED / ROUTING AROUND` 结论灌输的旧模板只可显式请求作历史复现；任何无两票多数的 route panel（含 1–1–1）都会要求重裁，不再用固定优先级偷裁。当前 corrected taxonomy 的 split=0，因此该代码修复不改变 27/11/3/0。

这个结果比旧 50-row 68/22/8/2% 图景更干净但也更保守：Bridge 仍为多数，Recall 是不可忽略的 27% 少数，Reflective-override 很少，旧的唯一 Associative 在 answer-only membership 门后消失。因此最强真故事不是“几乎全由 bridge 重推”，而是“语义确认的 OLD commitment 均有可见 route，且以 Bridge 为主、Recall 为显著少数；未观察到 traceless Associative”。它仍是观察性 taxonomy，不是自然生成中介或必要性的因果证明。

## 下游 crosswalk

`src/p0_downstream_crosswalk.py` 将 corrected membership 映射到冻结的 X1、历史 necessity、W-A 与 logit-lens 选择，结果为 `results/p0_downstream_crosswalk.json`，SHA256=`f034a5f41368effd392a647ebcde7e17f194f3405316f0678a5399747776b4a4`。

- X1 18 条：OLD/NEW/NEITHER=13/0/5；main=6/0/4、F2=5/0/0、sample=2/0/1。官方 X1 `9/18 FAIL` 永远不变。
- 历史 necessity 19 条：OLD/NEW/NEITHER=13/3/3。corrected OLD 13 条中，历史 raw-COT CLR=13/13，按论文 `metrics._without_subject` 独立重算的 subject-scrubbed CLR 也为 13/13；route=Bridge 10、Recall 2、Reflective-override 1、Associative 0。
- 全部 33 条 A3 candidates：OLD/NEW/NEITHER=13/15/5；非 OLD 中历史 raw-COT CLR=18/20，论文 subject-scrubbed CLR 也为 18/20。33 条中 subject scrub 改变 CLR 的数量恰为 0，因此旧数字点值未变；但两个仪器已分开落账，不能再以代码口径混称。关键反证不变：链中出现旧值并不充分，不能把 CLR 当作 OLD commitment 或自然中介。
- W-A `a2rev` 16 条与 P0 `a3|32b` overlap 15，overlap OLD/NEW/NEITHER=6/5/4；因此 W-A 的 lexical `a2rev` 组不能等同 semantic committed OLD。
- logit-lens 的预注册 23-row crosswalk 暂为 `BLOCKED_MISSING_PER_ITEM_ARTIFACT`：本地缺 `results/probe/logitlens_cf200_ROME_B3.jsonl`，只有聚合 n=23 与图，不能猜 case ID。

P0 到此在本地可做的 membership、route 与三个可访问下游 crosswalk 全部完成；唯一未闭合的是缺原始 per-item 文件导致的 logit-lens crosswalk。该阻塞不改变 corrected taxonomy，也不授权任何 GPU 续跑。
