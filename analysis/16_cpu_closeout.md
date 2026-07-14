# v1.88 CPU closeout final · case-block / B15 / F3 / X2-X3 refresh

日期：2026-07-13  
审计入口：`src/validate_cpu_closeout.py`  
完整入口：`experiments/run_cpu_closeout.sh`  
最终 audit：`results/cpu_closeout_audit.json`

## 1. 总裁决

六份服务器 artifact 均为合法 JSON，字节 SHA 与最终 audit 逐份一致。Percase、B15-B0、Cap3、F3、X2、X3 的统计与 provenance 门全部通过；X2/X3 点估与旧落库数字零漂移。

首份 B15 曾暴露 estimand 错位：文档冻结 B0 knowledge coverage，旧调用却继承 `load_base_clr(late="B3")`。该 B3 artifact 已保留为 sensitivity。修复后的最终 B15 明确 `base_budget=B0`，base provenance 也是 `selected.budget=B0`，edited/base duplicate audits 均 PASS。本地重跑 validator 产生的 audit 与服务器回传文件 byte-identical；最终 `status=PASS/failures=[]`。CPU/GPU 科学执行队列到此清空。

## 2. Artifact SHA

| Artifact | SHA256 | 状态 |
|---|---|---|
| `results/percase_caseblock.json` | `32a35c7c4ff26819372a4287568ac9869c76496d4b6b91176c87187d7591d1a4` | PASS |
| `results/b15_caseblock.json` | `3a663c447031a14b2f0f58d1f7eb8b09892d8c20543e92ce688da98b657c8d0f` | PASS, B0 primary |
| `results/b15_caseblock_B3_sensitivity.json` | `f1833e95d58c4dee7949c072e6d3a7ae1baa438f8e5215dbe0ab400972c6e6e1` | preserved B3 sensitivity only |
| `results/cap3_caseblock.json` | `288cf5a14d1fb0521b1d8ec6b619f85a0e1606bbf59a52ecc76982c7a4b75991` | PASS, primary null |
| `results/f3_sampling_recalc.json` | `0f0b779f86c6b4a86a8d8bbeb60409ac84a370ff58a3e69a6f5add14ea5f5833` | PASS_WITH_MISSING_PAIRS |
| `results/x2_memit14b_crossarm_v2.json` | `e11666014d70b9e57b858a7daf32e368e5278f99924e17a3f44223a4d5fbbe2f` | PASS |
| `results/x3_para_crossarm_v2.json` | `ba2b3caaf365b56dc7cfb62a71d836f4fe6c56bc549f4e6e5fb2e0dcac4746ee` | PASS |
| `results/cpu_closeout_audit.json` | `158e2a4597086dccf48b804a50f227091ce1623de967c4bc060a24687d875fac` | PASS |

## 3. Percase case-block

主 bootstrap 抽 unique `case_id`，每个事实的全部可用 scale/family rows 共同进出。因此 CI 只表示条件于六个观测 checkpoint 的事实抽样不确定性，不是模型总体 scaling law。

- `es_drop`: `.1094 [.0417,.1770]`，1194 rows / 200 facts。
- `RR`: `.6444 [.1985,1.1427]`，689 / 189。
- `CLR`: `.9703 [.7792,1.1780]`。
- `CLR density`: `.0037 [.0025,.0049]`。
- `CLR∧RR`: `.6444 [.1914,1.1457]`。
- within-Qwen `es_drop`: `.1194 [.0374,.1995]`。
- Qwen 32B−14B 固定点配对：`.0657 [-.0303,.1616]`，含零。
- Qwen 32B−7B：`.1263 [.0152,.2323]`，但 7B 存在 Math-parent confound，只作次要。

RR 与 CLR∧RR 的 case-block CI 现在排零，但 family→row sensitivity 仍分别为 `[-.1127,1.3688]` 和 `[-.1138,1.3744]`。这意味着它们对事实抽样稳健，对“从两个 family 外推模型总体”不稳健。

## 4. B15-B0 最终结果

五个 matched checkpoints 上，`base_budget=B0`、n=994 rows / 200 facts：

- matched baseline: `.1005 [.0335,.1684]`；
- controlled on binary unedited-base B0 answer-old: `.0837 [.0158,.1510]`；
- B0-base-known: `.1103 [.0272,.1950]`，693 rows / 183 case blocks；
- B0-base-unknown: `.0331 [-.0755,.1464]`，301 / 127；
- family→row sensitivity controlled: `.0837 [.0130,.1493]`。

加入 B0 recall 协变量后，slope 点估从 `.1005` 降到 `.0837`，相对衰减约 16.7%，但 case-block CI 仍排零。因此“大模型只是更容易在 B0 答出旧值”不能完全解释 fixed-checkpoint size association。这不是被解释份额的因果识别：B0 exact-answer recall 只是潜在知识覆盖的粗糙二值代理，仍有测量误差和残余 confounding。known/unknown 是 checkpoint×case row 状态，183+127>200，且未直接检验两个 slope 之差，不得宣称 effect modification 或“燃料/引擎”因果分解。

历史 B3 sensitivity 保留为 controlled `.0992 [.0304,.1684]`；它不与 B0 主结果混报。

## 5. Cap3

五个 matched B3-base checkpoints，edited/base duplicate audits 都 PASS：

- primary `net_clr`: `.0522 [-.0075,.1111]`，993 rows / 200 facts，含零；
- raw matched CLR: `.9356 [.7429,1.1432]`；
- `baseCLR0` subgroup: `1.0054 [.3875,2.0104]`，197 rows / 96 facts。

主裁决只看 `net_clr`：base subtraction 后正 slope 的 95% CI 含零，raw CLR 不能承重 capability framing。`baseCLR0` 是随尺度变化的 selected subgroup，只能探索性报告，不得救回主端点。raw logit slope 与 net OLS slope 也不应直接比数值大小。

## 6. F3 same-seed 重算

唯一缺失为 `cf_10436` 的三个 B3 seed endpoint；主分析为 199 cases / 597 pairs。从 artifact 内嵌 `case_summaries` 独立重算点估和 10,000 次 bootstrap，全部逐位一致：

- ES B0 `.586265 [.529313,.643216]`；
- ES B3 `.469012 [.413735,.524288]`；
- ES-drop `.117253 [.067002,.169179]`；
- equal-case conditional RR `.305180 [.242117,.371622]`，148 cases / 350 B0-ok pairs；
- equal-case conditional RRs `.094595 [.056306,.136261]`；
- CLR B3 `.522613 [.463987,.581240]`。

RR `.305` 的 estimand 是“每 case 先在其 B0-ok seeds 内平均，再对 148 cases 等权”，不是合并 trajectory 率。合并后是 `87/350=.248571`；两者都为正，但论文必须标清 estimand，不得用 `.305` 暗示 87/350。旧 first-row ES-drop `.090452` / RR `.264264` 只作 superseded sensitivity。

合法结论：三个固定 sampling seeds 下 ES-drop 均为正，合并 case-block CI 排零，且与 greedy `.110 [.035,.185]` 同量级。这排除单条 greedy trajectory 伪影；不证明 sampling 显著加重回退，也不外推到随机 seed 总体。

## 7. X2 / X3

X2 v2 对 N/T/C 各 400 unique worlds 显式报 duplicate audit PASS，数字与首版零漂移。T−C：ES `+.100 [.040,.160]`、RR `-.0982 [-.1696,-.0268]`、CLR `-.220 [-.280,-.165]`；RRs `-.0268 [-.0804,+.0268]` 为 null。C−N 与 0 相容，不是等价认证。

X3 v2 保留所有旧数，只修正推断标签。确认门只是 T−C strict lexical PS `+.055 [.020,.0925]`；C−N 为 `COMPATIBLE_WITH_ZERO / equivalence NOT_TESTED`，T−N 为 non-gating descriptive。固定 N-B0 次级门只有 110 cases / 145 rows，old-only T−C `-.0138 [-.0420,+.0137]` 为 null。

## 8. 执行收口

全部 GPU 实验和承重 CPU 分析已结束。当前不再上传代码、不运行服务器任务、不为占用算力添加支持性实验。P0 logit-lens per-item crosswalk 仍是缺原始 dependency 的 optional blocked component，不影响 closeout PASS，也不授权重跑模型。

下一步是按 `paper/results.json → paper/draft.md → src/ → prior reviews/prereg` 顺序执行最终 results-first 第一性科学 review；正文修改仍后置。
