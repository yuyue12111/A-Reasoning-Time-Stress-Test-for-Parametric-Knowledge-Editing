# report_h100.md — H100 节点执行回报（块格式 · 2026-10-08 起）

## H0a ✓ 03:09–03:14
- 8 张 H100 80GB（81559 MiB）: 实测 index 0-7 全部 `NVIDIA H100 80GB HBM3` ✓
- 两模型目录 safetensors: 32B=8、70B=17 ✓
- `$PROJ/deltas/r1qwen32b/ROME/cf` 计数: 200 ✓
- PyPI: curl 无输出/TCP 超时（rc=124）→ 不可达，按离线路径走
- python 3.12.3 / torch 2.8.0a0+5228986c39.nv25.06 / cuda available=True
- 新增项: `$SHARE/h100_pyver.txt` = `3.12` ✓

## H0b ✓ 03:14–03:15
- HEAD 一致: 本节点与 $PROJ 均 `fe8b5e5 REVISION §8: snapshot after the review decisions` ✓
- `ls deltas/r1qwen32b/ROME/cf | wc -l` = 200 ✓
- source/counterfact.jsonl/deltas 软链/logs/rt/$POUTH 全部就位
- 备注: clone 前 $PROJH 已存在，为使 clone 成功先 rm -rf $PROJH

## H0c ✓ 03:15–03:34
- transformers = 5.5.4 ✓（torch 2.8.0a0+5228986c39.nv25.06，NGC 构建，与 4090 不同——照实回报，不算失败）
- run_all.py: `193 passed, 0 failed`，exit=0 ✓
- env_check: network 全 URLError（预期）；**verdict.blockers 1 条非 network**（原文见下）
- 裁决: leader 判定该 BLOCKER 不成立（检查的是 clone 相对路径，G0 用 $PROJ 绝对路径、分片齐全），视同通过 → `touch $SHARE/H100_ENV_OK`（03:34）✓
- 关键数字: h100_need.txt 仅 zstandard==0.25.0；wheels/DONE 03:16 出现；`pip install --no-index --no-deps --no-build-isolation -c /tmp/keep.txt $SHARE/wheels/*.whl` → Successfully installed zstandard-0.25.0；wheels_failed.txt 不存在
- env_check BLOCKER 原文: `Study-1 32B rows missing under results/probe/ (G0 compares against them)`
- 事实核查: results/probe 被 .gitignore 忽略（clone 不含数据）；$PROJ/results/probe/ 下 ROME_cf200_r*of8=8 片、BASE_cf200_r*=8 片齐全
- 备注: 执行单字面 `$SHARE/wheels/*` 因 DONE 标记文件被 pip 拒绝，改用 `*.whl`（获 leader 确认）
- 本容器无 rsync 命令；执行单中的 rsync 同步一律以 `cp -a` 代替（已用于 pools_study2）


## H1a-smoke ✓ 03:36–03:41
- 冒烟（rank 0 --limit 2, CUDA 0-3）: `r0of2 cases 2/2 rows 8 errors 0 173.7s`，done: {'base': 4, 'rome_N': 4}
- 连贯英文检查: 通过 —— rome_N 行将 Mendel 答成物理/力学（编辑生效），base 行正常答遗传学/豌豆实验；回答均为连贯英文
- 冒烟产物: results/rt/g0/r1qwen32b_g0h100_{base,rome_N}_r0of2.jsonl（各 4 数据行）

## H1a ⏸ 03:44–（rank 0 卡住，待裁决）
待裁决：rank 0 续跑零产出 30 分钟（rank 1 同配置正常），是否清空 r0of2 冒烟遗留文件后重启 rank 0，或由 leader 远程诊断？
- 通过条件（尚无法判定）: exit=0（PASS）——两进程均未结束
- 关键事实:
  - rank 0 pid 743975（GPU 0-3）: 启动 03:44，续跑识别 done=4/pending=196 正确，此后 30 分钟零行写入（base/rome_N r0of2 均停在冒烟遗留的 5 行）
  - rank 1 pid 743976（GPU 4-7）: 同时启动、同配置，正常推进 03:44→04:14 约 75 行/condition（速率 ~6.5 行/分，稳定）
  - 两进程 CPU 满转（ps TIME≈ELAPSED，Rl 状态），GPU 利用率 0-10%（低但 rank 1 出活，生成负载本就不高）
  - rank 0 与 rank 1 唯一差异: rank 0 输出文件含冒烟遗留 4 数据行（冒烟 --limit 2 与全量同 run-tag g0h100），rank 0 走续跑恢复路径；rank 1 从空文件开始
  - rank 0 卡住疑点指向续跑恢复路径；非显而易见低级代码错误，未动代码
- 已做处置: 无（未 kill/未重启/未改任何文件），rank 1 保持运行继续产出
- 冒烟块见前（H1a-smoke ✓）


## H1a-fix ✓ 04:20–04:33
- step1: kill 743975 → pgrep 仅剩 743976（rank 1，正常）
- step2: compute apps 仅 4 条（pid 277423 宿主命名空间 [Not Found]，各 ~21-24GB，对应容器内 rank 1 于 GPU 4-7）；GPU 0-3 各 1 MiB
- step3: r0of2 _meta 的 device_map_counts = {'0': 15, '1': 18, '2': 18, '3': 17} —— 仅 cuda:0-3，无 cpu/disk
- step4: GPU 0-3 无不属于 rank 1 的进程（1 MiB），无需 kill
- step5: 显存 <1GB 确认后按原命令重启 rank 0 → 新 pid 1748768，日志 logs/rt/g0h100_r0b.log
- step6（5 分钟检查）: r0of2 base/rome_N 由 5 行 → 79 行（增长 ✓）；device_map_counts 仅 cuda:0-3、无 cpu/disk ✓；GPU 0-3 显存 15.7-18GB（权重在 GPU）
- 备注: leader 假设（部分层在 CPU）与 step3 证据不完全一致（冒烟 meta 即全 GPU），照实记录；卡住真实原因未查明，重启后恢复正常
- 处置: 让其跑完，按原单做 rt.g0 判定，然后 H1b
- 新规则已采纳: 每次 GPU 任务启动前 nvidia-smi 确认目标卡 memory.used < 1GB


## H1a ⏸ 03:44–05:26（rank 0 完成 ✓，rank 1 卡死待裁决）
待裁决：rank 1（pid 743976）卡死症状与 rank 0 相同（CPU 满转、行数零增长 20+ 分钟），是否按 rank 0 同样方式处置（kill 743976 → 确认 GPU 4-7 <1GB → 原命令重启 rank 1，日志 g0h100_r1b.log）？
- rank 0（重启后，pid 1748768）: 05:24 完成 —— r0of2 base=201 行、rome_N=201 行（100/100 cases，含冒烟 4），`[rt.run] done: {'base': 122, 'rome_N': 122}`（本进程新增），errors 0；GPU 0-3 释放（各 1 MiB）
- rank 1（原始进程，pid 743976）: 157 行/condition 停滞（78/100 cases/condition），自 ~04:52 起零增长 30+ 分钟；CPU TIME 1:42:34 ≈ ELAPSED（满转）；GPU 4-7 显存 27-30GB/卡、利用率 0-29%
- 症状与 rank 0 卡死时一致：运行中段突然停产行、CPU 单核满转、GPU 低利用；非每次发生（rank 0 重启后全程正常跑完）
- H1a-fix 第 2、3、6 步输出（leader 要求归档）:
  - step2 compute apps: 仅 4 条 pid 277423 [Not Found]（宿主 ns，~21-24GB × 4 = rank 1 于 GPU 4-7）；GPU 0-3 各 1 MiB
  - step3 device_map_counts: {'0': 15, '1': 18, '2': 18, '3': 17}（仅 cuda:0-3，无 cpu/disk）
  - step6: r0of2 重启后 5 行→79 行（增长），device_map_counts 仅 cuda:0-3
- rt.g0 判定: 未开始（需 r1of2 完整；rank 1 卡死中）—— Study2 生成保持不开始（原规则 + 补充三第 2 条）
- 补充三已收到: D1_DONE 已存在（待核验文件）；H2 新顺序 G1'→G2'/H1b→H-D70→G3'→G7..G12 记录在案，G1/G4 未曾开跑（无旧序产物）


## H1a-fix2 ✓ 05:41–05:47（补充四执行）
- 取证: py-spy 未安装 → 按单跳过并写明（$POUTH/hang_r1_pyspy.txt）；top（$POUTH/hang_r1_top.txt）: 主线程 R 90.9% CPU、389 线程中 388 睡眠、RES 84.1g；nvidia-smi+topo（$POUTH/hang_r1_smi.txt）
- kill 743976 → GPU 4-7 全部 1 MiB（5 秒内）
- 重启 rank 1: 原命令、**无 PYTORCH_CUDA_ALLOC_CONF**（自本条起本节点全部命令不再设该项），新 pid 2628438，日志 logs/rt/g0h100_r1b.log
- 看门狗已部署（CPU 后台循环，不属于 rt 队列）: 每 5 分钟采样各 running rank 行数；卡死判定=进程存活且行数停滞 ≥阈值（G3' 30 分钟，其余 20 分钟）；卡死→取证($POUTH/hang_<项目>_r<rank>_<时间>.*)→kill→等卡<1GB→原命令重启（重启前旧日志留存为 <log>.pre_<时间戳>）；每 rank 每项自动重启 ≤3 次，第 4 次卡死停项标 ⏸；重启记录写入回报块
- 手工处置记录: 05:41 rank 1 卡死前行数 157/condition（78/100 cases）| 取证 hang_r1_* | 手工重启（leader 授权），不计入自动重启额度
- r1of2 跑满 100/100 后做 rt.g0 判定；PASS → 按补充三顺序进入 H2


## H1a ✓ 03:36–05:58（G0 判定 PASS）
- r1of2 重启后 ~11 分钟跑满: base/rome_N 各 201 行（100/100 cases），`done: {'base': 18, 'rome_N': 18}`（本进程新增），正常退出
- 四分片行数: r0of2 base=201、rome_N=201；r1of2 base=201、rome_N=201
- rt.g0 判定 exit=0，[G0] 行原样:
```
[G0] complete 198/198 (>= 198)  Study 1 drop 0.106 CI used [0.03, 0.182]  v2 drop 0.086 [0.010101010101010102, 0.16161616161616163]  B0 agreement 187/198  -> PASS
```
- verdict 文件: $POUTH/g0h100_verdict.json
- 卡死处置汇总: rank 0 一次（手工，leader 授权）、rank 1 一次（手工，leader 授权）；自动重启 0 次
- 通过条件: exit=0 ✓；无 error 行（分片行数=201=1 meta+100 cases×2 budgets，errors 0 于 run 日志）
- → 按补充三顺序进入 H2

- 06:20:29 | rank 1 | 卡死前行数 2（=base 1 + rome_N 1，自 05:59 启动 20 分钟零数据行）| 自动重启 #1（看门狗执行）| 新 pid 3234233 | 取证文件缺失+本回报行/state 未写为看门狗 v1 bug（项目名 G1' 单引号破坏取证文件名并中断写回），本行与 state 修正为手工补记；v2 看门狗已修复（安全文件名/per-rank try/except/state 先于回报落盘）并重启
- 06:36 | G1' 观察: rank 0（pid 2817474）正常推进 181 行/condition；rank 1 被看门狗自动重启后（pid 3234233）运行中


## G1 ⏸ 自动
待裁决：rank 1 自动重启后再次卡死（行数停滞于 122，≥20 分钟），按补充规则停止本项，由 leader 检查裁定。
- 取证文件: hang_G1_r1_20261008_065545_pyspy.txt, hang_G1_r1_20261008_065545_top.txt, hang_G1_r1_20261008_065545_smi.txt
- 时间: 2026-10-08 06:55:52

- 2026-10-08 06:55:52 | rank 1 | 卡死前行数 122 | 停止（重试后仍卡死）| 取证 hang_G1_r1_20261008_065545_pyspy.txt, hang_G1_r1_20261008_065545_top.txt, hang_G1_r1_20261008_065545_smi.txt


## G1' ⏸（rank 1 二次卡死，待 leader 裁定；rank 0 继续跑）
待裁决：rank 1 自动重启 #1 后 ~35 分钟再次卡死（122 行停滞 ≥20 分钟），按补充规则停项；请 leader 检查取证文件并裁定 G1' 如何继续（以及卡死根因排查方式）。
- 06:39:49 rank 0（2817474）第 1 次卡死（181 行/condition 停滞 ≥20min）→ 看门狗取证 hang_G1_r0_20261008_063949_* → kill → GPU 0-3 清 → 原命令重启 #1 → 新 pid 3579001（运行中，06:44 起产出行数回升）
- 06:55:45 rank 1（3234233，06:20 自动重启 #1 后）再次卡死（122 行 = base 61 + rome_N 61，停滞 ≥20min）→ v2 看门狗取证 hang_G1_r1_20261008_065545_* → kill → GPU 4-7 已清（各 1 MiB）→ **按补充规则不再重启，停项 ⏸**
- 卡死模式汇总（4 例）: G0-r0（36min 处）、G0-r1（80min 处）、G1'-r0（35min 处）、G1'-r1（重启后 35min 处）；共同特征：CPU 单核满转、GPU 低利用、行数停滞；重启后均恢复产出一段后随机复发；py-spy 未安装，无法取 Python 栈
- state 修正: rank0 实际 pid 3579001/restarts=1（v1 竞态致 06:39 更新丢失，已手工对齐，v2 后续监控有效）
- 当前行数: r0of2 base/rome_N=181 行/condition（rank0 重启前）；r1of2 base/rome_N=122 行/condition


## G1 ⏸ 自动
待裁决：rank 0 自动重启后再次卡死（行数停滞于 362，≥20 分钟），按补充规则停止本项，由 leader 检查裁定。
- 取证文件: hang_G1_r0_20261008_070052_pyspy.txt, hang_G1_r0_20261008_070052_top.txt, hang_G1_r0_20261008_070052_smi.txt
- 时间: 2026-10-08 07:00:59

- 2026-10-08 07:00:59 | rank 0 | 卡死前行数 362 | 停止（重试后仍卡死）| 取证 hang_G1_r0_20261008_070052_pyspy.txt, hang_G1_r0_20261008_070052_top.txt, hang_G1_r0_20261008_070052_smi.txt


## H-2 §0 ✓ 07:05–07:10（执行单 H-2 取代 H-1 阶段 H2/补充三/补充四看门狗规则）
- kill 全部 rt.run（rank0 3579001 等被停）→ 8 卡 memory.used 全部 1 MiB ✓
- 归档: results/rt/s2/r1qwen32b_s2_*_r*of2.jsonl（4 文件，world2 旧布局，不进分析）→ results/rt/s2_archive_world2/（仅移动未删除）
- 旧看门狗停止；新看门狗 v3 已部署（规则: 每分钟采样 GPU util，rank 的全部 GPU 连续 10 次 0% 且进程存活 → 取证/kill/等<1GB/原命令重启；每 rank 每项重启 ≤3 次，第 4 次停项 ⏸；行数不再作为卡死依据）
- 回报一行: `ls /inspire/dataset/Wikipedia/20231101/20231101.en/*.parquet 2>/dev/null | wc -l` → **41**
- H1b 取消已知悉（70B 编辑改由 4090 做，偏差见 prereg-arr-deviations.md）
- 执行备注: 首次 kill 用 `pkill -f "python -m rt.run"` 时模式自匹配误杀执行脚本本身，改用 `python -m [r]t.run` 精确模式完成（未影响 rt 进程处置）

## G1'' ▶ 07:11 启动
- GEN8(experiments/rt/study2_r1qwen32b.yaml, --conditions base,rome_N --stage 1, s2_32_baseN)
- 8 进程 × 1 卡，--device cuda，batch 16，max-batch-tokens 40000，无 PYTORCH_CUDA_ALLOC_CONF；pids 4003771-4003778
- cases=400 shard=50（每 rank 50 cases）；输出 results/rt/s2/r1qwen32b_s2_{base,rome_N}_r{0..7}of8.jsonl；目标 base 2400 + rome_N 2400 数据行
- 启动前 8 卡显存全部 1 MiB（<1GB 规则满足）

- 07:28 收到 H-2 补充一（偏差 D5）: G11' 后若 $SHARE/D70_DONE 未出现，按 14B→8B→7B→1.5B 抢占式认领（mkdir $SHARE/LOCK_GS_<tag> 成功即认领，跑完 touch $SHARE/GS_<tag>_DONE；mkdir 失败跳过）；命令=每卡一进程 world 8 bf16 配置默认批（study2_<tag>_eff.yaml，先 rank0 --limit 2 冒烟）；通过行数 14B/8B=800、7B=636、1.5B=424；error 行时加 --max-batch-tokens 64000 重跑一次；任何时候 D70_DONE 出现，当前项结束后下一项做 G3''

- G1'' 30 分钟采样（07:42，启动 07:11 +31min）: 8/8 进程存活；数据行 base/rome_N —— r0:120/120 r1:10/10 r2:120/120 r3:60/60 r4:60/60 r5:120/120 r6:120/120 r7:10/10（每 rank 目标 300/300）；GPU util 60-98% 全饱和；无 error/OOM；看门狗零触发
- 速度估算: ~770 数据行/31min（两条件合计）→ G1'' 全量 4800 数据行预计 ~3.2h（rank 间因 case 长度不同进度不均，以先完成为准）

- 08:16 G1'' OOM 处置: rank3（三连 chunk OOM 崩溃退出）与 rank5（20 error 行后 done 退出）按 GEN8 规则用 --max-batch-tokens 24000 原样续跑（rank3 pid 1422185、rank5 pid 1422186，日志 *_retry24k.log）；其余 6 rank 以 40000 继续运行中；GPU 3/5 处置前已空（1 MiB）
- OOM error 行分布（08:15）: r0:10 r1:20 r2:10 r3:20 r4:0 r5:20 r6:0 r7:20（每文件，base/rome_N 相同）——r4/r6 尚无 error 行

- 08:40 G1'' 退出原因核查: r4 done 退出且 300/300 全完成（0 error）✓；r0(180+20e)/r1(120+30e)/r5(180+20e)/r6(240+10e) done 退出但留 OOM error 行；r3/r7 OOM 崩溃退出（r7 文件 20 行全为 error 行，0 valid）
- 08:40 处置: 对空闲 rank 0/1/6/7 按 GEN8 规则启动 --max-batch-tokens 24000 续跑（pid 1862298/99/1862300/01，日志 *_retry24k.log）；在跑: r2(40000 原批)、r3retry、r5retry + 新 4 个 = 7 进程；GPU4 空闲（r4 已完成）
- 待观察: 24k 续跑完成后若仍有 error 行（超出"重跑一次"规则覆盖），停下汇报 leader

- 09:12 r2 处置: r2 原批 done 退出（180 valid+20e/condition，40000）→ 按 GEN8 规则启动 24k 续跑（pid 2550116，日志 s2_32_baseN_r2_retry24k.log）
- 09:12 重要发现（设计语义差，待 leader 裁定）: 引擎 append-only 设计下 error 行永久保留（src/rt/run.py L53: "error rows are not keys, so a case whose delta was missing is retried"——续跑只追加 valid 行，不删除 error 行）；r5retry 已补齐至 300 valid/condition，但 20 条旧 error 行仍在文件中，且 20 个 error case_id 全部已有对应 valid 重做行（无数据缺失）。GEN8 通过条件"文件里没有 error 行"按字面无法满足；处理方式（保留为历史记录/由分析工具过滤/授权清理）请 leader 裁定。本项继续跑完，不自行删行。


## G1'' ✓（数据达标；error 行语义差待裁决）10:31
- 数据行数: base **2400/2400**、rome_N **2400/2400**（valid，不含 error 行）✓
- 最终行分布: 每 rank 300 valid/condition（r4 从未出错 0 err；其余 rank 有 10-30 条历史 error 行，全部 case_id 均有对应 valid 重做行——数据无缺失）
- OOM 处置回顾: 8 个 rank 中 7 个出现过 OOM error 行（40000 token 批下）；按 GEN8 规则对全部 7 个 rank 各做一次 --max-batch-tokens 24000 续跑，续跑期间 0 新 OOM、0 新 error；24k 后 r2/r7 由 done 正常完成
- 看门狗 v3: 零触发（GPU util 规则下无误杀）
- 通过条件字面核对: 数据行数 ✓；"没有 error 行" ✗（引擎 append-only 设计保留历史 error 行，见 09:12 回报，待 leader 裁定语义）；"没有 OOM" ✗ 字面（已按规则处置）
- 下一项: 继续 G2''（执行单顺序），error 行语义差裁决不阻塞后续生成（数据均有效）

