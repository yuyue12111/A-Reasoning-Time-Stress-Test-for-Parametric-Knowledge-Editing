# X2 · MEMIT-14B 链级修复跨编辑器复制

日期：2026-07-11  
权威数字路径：`paper/results.json.rq3.x2_memit14b_repair_replication`  
预注册：`prereg-x2-x3.md` §X2  
原始汇总附件 SHA256：`145cf47593fa90a6d40156f2b529a436c6280f0d3e3ad187feb177cc8280355f`

v1.87 CPU refresh：`results/x2_memit14b_crossarm_v2.json`，SHA256=`e11666014d70b9e57b858a7daf32e368e5278f99924e17a3f44223a4d5fbbe2f`。所有 point/CI/p 与首版零漂移；新增 N/T/C 各 400 unique trajectory-aware worlds、0 duplicate keys 的显式审计。

## 1. 先给裁决

X2 **通过**预注册主端点与联合特异性门：在 fresh-N/T/C 严格同协议的 MEMIT-14B 上，压制 `o_old` 的 T 臂相对同关系强竞争者 C 臂，使 B3 strict ES 提高 **10.0pp [4.0,16.0]**，loose RR 降低 **9.82pp [2.68,16.96]**，CLR 降低 **22.0pp [16.5,28.0]**。C−N 的 ES/RR/RRs 与 0 相容，T−N 同向且 ES/RR/CLR 排零。因此，ROME 上的 think-only 链级修复**转移到第二编辑器 MEMIT**。

边界必须同报：严口径 RRs 的 T−C 只有 **−2.68pp [−8.04,+2.68]**，没有排零。不能写“所有回退口径均显著改善”；C−N 只是未检出行为差异，不是预设等价界下的等价认证；本实验只有 N/T/C，不是 MEMIT 上的完整五臂复制。

## 2. 技术审计

- N/T/C 各 200 cases、32 shards、0 error。
- T 与 C 相对 N 的 B0 各比较 400 个 probe rows，missing=0、different=0。这里 400=200 cases×`{efficacy, locality}`，不是 400 cases。
- B3 相对 N 实际改变的 efficacy probe rows：T=109，C=18。
- T/C 的 64 个 full shards 各加载 MEMIT 三层缓存，日志 cache-load 合计 192 行。
- 上传目录没有 `.git`，故 git hash 为 warning；逐文件 `code_sha256`、runtime/model/dtype/BOS/software parity 均通过。
- 先前 smoke 已判 legacy N 缺 code/runtime/actual-model provenance，按预注册触发 `experiments/memit14b_freshn.yaml`；full audit 的 N/T/C 为 strict provenance parity。

服务器应保留：

- `results/x2_full_audit.json`
- `results/x2_memit14b_crossarm.json`
- `results/x2_memit14b_crossarm_v2.json`
- `results/x2_n_config.txt`
- `results/logs/x2_{N,T,C}_score.txt`
- `results/logs/x2_crossarm.txt`
- 三臂 `results/probe/r1qwen14b_MEMIT_cf200memit_{freshn,sup,strong}_r*.jsonl`

v2 aggregate 不包含 raw shard hash、B0 byte identity 和 runtime parity，因此它是 duplicate-safe CPU rescore，不替代 `x2_full_audit.json` 的发布级 provenance。

## 3. 各臂数字

B0 三臂逐字一致：ES=.560=112/200，ESf=.650，RR=RRs=CLR=0，Flip=.145，Loc=.960。因此 RR/RRs 的共同 `b0ok` 分母是 112。

| B3 | ES | RR（/112） | RRs（/112） | CLR | ESf | Flip | Loc |
|---|---:|---:|---:|---:|---:|---:|---:|
| N | .500 (100/200) | .2054 (23) | .0714 (8) | .460 (92/200) | .605 | .165 | .965 |
| T | .615 (123/200) | .0982 (11) | .0446 (5) | .235 (47/200) | .655 | .065 | .965 |
| C | .515 (103/200) | .1964 (22) | .0714 (8) | .455 (91/200) | .610 | .160 | .965 |

关键配对差（10,000 次按 case bootstrap，seed 42）：

| 对照 | ES | RR | RRs | CLR |
|---|---:|---:|---:|---:|
| T−C | +.100 [.040,.160] | −.0982 [−.1696,−.0268] | −.0268 [−.0804,.0268] | −.220 [−.280,−.165] |
| T−N | +.115 [.055,.175] | −.1071 [−.1786,−.0357] | −.0268 [−.0804,.0268] | −.225 [−.285,−.165] |
| C−N | +.015 [.000,.035] | −.0089 [−.0268,.000] | .000 [.000,.000] | −.005 [−.025,.010] |

`src/cross_arm.py::per_case` 对 RR/RRs 使用 B0 成功门；`paired_diff` 以 case 为配对和重采样单位。脚本输出的 `p=0.0` 只是 10,000 次 bootstrap 中未出现反号，不是 exact p-value；写作应报 CI，若必须报 p 则写 `<0.0002`。

## 4. 与旧 MEMIT 现象块的冲突

旧 `paper/results.json.memit_replication`（B22）与 X2 fresh N 不是同一权威基线：

| | B0 ES | B3 ES | es_drop | RR@B3 |
|---|---:|---:|---:|---:|
| legacy B22 | .540 | .450 | .090 [.010,.170] | .333 |
| X2 fresh N | .560 | .500 | .060 [−.020,.140] | .205 |

这不是舍入误差。科学处理是**分块、不覆盖、不互相背书**：X2 的 N/T/C 严格配平，足以承重修复的跨编辑器因果对比；但 fresh N 没有再次支持显著 MEMIT ES erosion。旧 B22 若不能补齐 cohort、代码、dtype/BOS 与 runtime provenance，最终应主动降级其“显著现象复制”措辞。

## 5. 合法 claim ceiling

可写：

> On MEMIT-14B under a fresh, strictly matched protocol, suppressing the edited fact's old object during reasoning outperformed a same-relation strong-competitor control by 10.0 ES points and reduced loose reversion by 9.8 points, transferring the repair beyond ROME.

必须紧跟：strict RRs 未显著；C≈N 是兼容零而非等价认证；仅 N/T/C；M1 within-case 机理仍只在 32B ROME 上验证。
