# P1 · X1 fresh-B0 node×capacity 诊断

日期：2026-07-13  
预注册：`prereg-p1-reload.md`  
入口：`experiments/run_p1_h200.sh`

## 设计与行为结果

P1 使用冻结 X1 manifest 的全部 18 个 case，对两个 H200 节点、single-H200 与 2×H200 balanced model-parallel 两种 topology 各进行 3 次独立进程/模型重载，共 `18×2×2×3=216` 次 case-edit。只生成 fresh B0 efficacy answer，不 replay chain，不做 suppression。

216/216 case-edit 完成。12 个 `node×topology×reload` cell 的 strict B0 均为 14/18，且来源分解逐格相同：main 10/10、F2-B1 1/5、historical sample seed2 3/3。MP2−single 在 Node A、Node B 及 node-stratified pooled 均为 0 [0,0]；A−B 在 single 与 mp2 下也均为 0 [0,0]。每个 node×topology 格内的三次 reload 都没有 strict flag 或 answer SHA256 变化。

## 排除了什么

在当前返回的 P1 行为结果中，X1 的四个 fresh-B0 失败不支持以下解释：

- single-H200 与 2×H200 model parallel 的执行 topology；
- H200-A 与 H200-B 节点差异；
- 同一格内重复模型 reload 导致的行为数值漂移。

因此 F2-enriched 冻结 stratum 在当前协议下的安装脆弱性在行为上稳定复现，不是 X1 那一次运行的偶发事故。跨格 code/software/model/runtime parity 的完整汇总仍待 v2 CPU 审计。

## 没有排除什么

P1 没有恢复 X1 来源链生成时的 historical runtime/code snapshot，所以仍无法区分：

- case/cohort 本身对当前编辑协议更脆弱；
- historical/current protocol drift；
- 两者的交互。

因此不得写成“F2 来源导致失败的机制”，也不得写成“四个 case 内禀不可编辑”。有效统计单位仍是 18 个 case，不是 216 次重复执行。

## v2 确定性 CPU 审计

`results/p1_reload_summary_v2.json` SHA256=`cbb969d79b0a4682e28d83bfc672870b93ea8800eb2643735f7f70960e702d41`，顶层 `status=PASS`、`failures=[]`、`warnings=[]`、`extended_audit_status=PASS`。它关闭了首版 scorer 的三个欠账：

- 18/18 case 在全部 12 次条件运行中的答案 SHA256 逐字一致，不是“strict flag 相同但文本暗中漂移”；
- 编辑权重始终是 `model.layers.12.mlp.down_proj.weight`，relative-L2 的 MP2−single 与 A−B 配对差均为 0[0,0]，四格内 reload 的 aggregate weight delta 也无变化；
- scorer 报告 code/software/model-runtime/runtime-env signature 数均为 1，两 topology 各只有一个 config hash，`parity_pass=true`。

失败 case 的 mean relative-L2=.022781，成功 case=.022628，没有零更新或明显小更新的分离。但 scorer 的 n=48/168 是 4/14 个 case 各重复 12 次，不是独立样本；只作描述，不做“更新幅度与成功无关”的正式推断。norm 一致也不证明更新张量逐元素一致或语义机制相同。

仍有两个无法事后补出的 release 边界：未记录 post-restore 数值 checksum；v2 summary 输出的是 provenance signature 数量，而不是具体 signature 值，故第三方完整复核仍需 raw shard metadata。

## 对 X1 的最终影响

P1 是事后诊断，不改变 X1 预注册联合门的 9/18 FAIL，不允许筛出 14 个 B0 成功 case，不重开 authored five-arm experiment。
