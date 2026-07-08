# Prewrite materials — 判官对抗审查台账(judge review ledger)

gap-review `prewrite-materials` workflow(wf_cd30418a-ebe):10 份材料 draft→judge 对抗核。judge 逐条 Read `results.json` 核数字/引用池/禁区。**这是 fold-in(7/11–13)必读的修订清单**;🔧=已内联修、⏳=留 fold-in 修、✅=判官通过。取数纪律:折进 LaTeX 时一切数字仍从 `results.json` 复核。

## 汇总

| 材料 | 判官裁决 | 处理 |
|---|---|---|
| `methods_llm_compliance.md` (llm-compliance-D6) | revise | 🔧 已修:κ=0.836 改标'judge-vs-rule 校验'(非 inter-judge);inter-judge=Fleiss κ 0.79;'three judges'→'three for taxonomy/validation, 2-of-3 for CLR-polarity' |
| `aia_relevance.md` (relevance-必3) | ok | ✅ 判官 OK,已核数字/引用池——原样采用 |
| `methods_level_vs_change.md` (level-change-D4) | revise | 🔧 已修:F1 no-drift 不再'family-wide 含 7B'——7B(+0.08 math-confound,margin≈0)显式排除 |
| `ethics_reverting_truth.md` (ethics-必4) | revise | 🔧 已修:Recall 路由(22% 非全 re-derivation)改'a re-derivation or a direct recall';'within measurement noise'→'point est. within ±0.02, not certified' |
| `methods_judge_pipeline.md` (judge-methods-D2) | revise | ⏳ fold-in 修:subject-scrub FP 计数(4+1+1=6 非 5,核 v1_clr_polarity)+ '85% Bridge'→P̄=0.833/Pe≈0.847 溯源 |
| `anonymize_spec.md` (anonymize-E5) | revise | ⏳ fold-in 修:文件计数是 draft 估值(实测 WHYAAAI 53 非 38、终极review 16 非 11、results.json 2367 行);改实测或改'示例/dozens'口径 |
| `supp_prereg_gates.md` (prereg-supp-D1) | revise | 🔧 已加 G5 更正 banner(冻结 max-stat 29.2%<50% 门不过;draft 的 100%/降 suggestive/待回传 均过期) |
| `supp_distractor_lens.md` (distractor-lens-D3) | revise | 🔧 已加 G5 更正 banner(CONSORT G5 行须并列 z≥2 100% 与冻结 max-stat 29.2% 门不过) |
| `release_and_licenses.md` (release-licenses-E4) | ok | ✅ OK;⏳ fold-in 补:因果 battery 五臂应含 C 臂(N/T/D/P/C,strong_competitor_M4),draft 漏 C |
| `supp_manifest.md` (supp-manifest-E3) | ok | ✅ OK;⏳ fold-in 补 Source 行:memit_replication / rq3.sup_battery.contrasts / necessity.held / wide_census_traceless / G5 冻结 29.2% |

## 各材料判官原始 findings(存档,fold-in 核对用)

### `methods_llm_compliance.md` — llm-compliance-D6  [revise]
**处理**:🔧 已修:κ=0.836 改标'judge-vs-rule 校验'(非 inter-judge);inter-judge=Fleiss κ 0.79;'three judges'→'three for taxonomy/validation, 2-of-3 for CLR-polarity'
- ⚠ §3 判官段把 Cohen's κ=0.836 归入『every reported INTER-JUDGE agreement』属 mischaracterization/overclaim。results.json line 1714-1724 metric_validation.vs_RRs_strict_decontam:0.836 是【中性判官面板 vs 严去污 RRs 规则】的一致性(criterion validity,含 confusion TP23/FP2/FN4/TN58、precision 0.92/recall 0.85),即『判官 vs 打分规则』,不是判官彼此之间的一致。材料自报 source 描述本身写的就是『vs strict decontaminated reversion (RRs)』——与正文『inter-judge』自相矛盾。只有 Fleiss κ=0.52(line 1026 rq2_taxonomy.pooled.fleiss_kappa)才是真正的 inter-judge(多评委)统计。把两者并列为『inter-judge agreement』夸大了评委间信度证据。
- ⚠ §3 一句的全称主张『Every LLM-derived label ... is produced by a fixed panel of THREE independent judges』被材料自己的 §3 清单证伪:CLR-polarity check 用的是 ≥2 判官(results.json line 1740 metric_validation.v1_clr_polarity._status:『37 unique case × ≥2 判官』),并非恒为三。全称『three』是轻度 overclaim,须收窄。

### `aia_relevance.md` — relevance-必3  [ok]
**处理**:✅ 判官 OK,已核数字/引用池——原样采用

### `methods_level_vs_change.md` — level-change-D4  [revise]
**处理**:🔧 已修:F1 no-drift 不再'family-wide 含 7B'——7B(+0.08 math-confound,margin≈0)显式排除
- ⚠ (i) overclaim: 'the base thinking-drift stays small (|Δ|≤0.08, mostly ≤0.025), so this holds family-wide' extends F1 edit-specificity to all six scales, but results.json explicitly excludes 7B — base_probe.7B delta_think=+0.08 equals the 7B edited RR=0.08 (capability.families.R1-Distill-Qwen.rr[1]=0.08) → margin≈0, flagged in base_probe.7B._interp ('margin≈0 不可分辨→7B 降级只作曲线低端') and f1_edit_specificity.verdict ('7B +0.08 是 Qwen-Math 小模型个例(margin≈0)'). Clean separation is a 32B headline (margin 0.214) + 70B extension (margin 0.142), so 'family-wide' is stronger than the data and contradicts the material's own cross-ref-map scope ('32B 单尺度 + 6 尺度 delta_think 小').

### `ethics_reverting_truth.md` — ethics-必4  [revise]
**处理**:🔧 已修:Recall 路由(22% 非全 re-derivation)改'a re-derivation or a direct recall';'within measurement noise'→'point est. within ±0.02, not certified'
- ⚠ OVERCLAIM (primary, easy fix): prose 句『the committed reversions we study are almost never silent, each leaving a verbalized re-derivation in the chain (§taxonomy)』把全部回退称作 re-derivation,错标了 22% (11/50) 的 Recall 路由 —— results.json:969 明确 Recall=『直陈值无中介』(直接复述,非再推导),只有 68% Bridge 才是『经命名中介推出』的 re-derivation。且项目已显式裁定把『reconstructive re-derivation』收紧为『bridge-or-recall, never traceless』(results.json:915/1093 _pending_draft_edits [S1]);本材料回退到被收紧掉的措辞。此外『almost never silent』(2% Associative=无声)与『each leaving...』自相矛盾——那 1/50 Associative(残差 implicit-leak)恰恰不留清晰言语化痕迹,『each』过度绝对。
- ⚠ OVERCLAIM (borderline, 建议收紧): §边界(i)『leaves general-task accuracy within measurement noise (§deploy)』—— 项目 B26 裁决(results.json:720-746 + _CORRECTION)明确:全量 n 下两比例 90%CI 未收进 ±0.02(GSM8K ±0.0217、MATH [−0.061,+0.041]),【不写 certified equivalent】、不得暗示统计等价。『within measurement noise』暗含『与噪声不可分辨=统计等价』,超出可认证范围。点估口径(GSM8K +0.005/MATH 0.000,§deploy 交叉引的是 genbench 通过门的点估)成立,但措辞需降到点估+门内、勿暗示等价。

### `methods_judge_pipeline.md` — judge-methods-D2  [revise]
**处理**:⏳ fold-in 修:subject-scrub FP 计数(4+1+1=6 非 5,核 v1_clr_polarity)+ '85% Bridge'→P̄=0.833/Pe≈0.847 溯源
- 🔢 §1 (subject-scrub 'Downstream validation' paragraph): 'of 5 raw false positives, 4 are subject-restatement (3 unanimous + 1 split vote), vs. 1 quotation/meta and 1 negation-only' sums to 6 items (4+1+1) inside the 5-FP bucket. Per results.json the buckets are DISJOINT: metric_validation.v1_clr_polarity.raw = {false_positive:5, split:4, genuine:28, n:37}. fp_taxonomy = {subject_restatement_only:'3 全票+1 分裂票', quotation_or_meta:1, negation_only:1}. So the 5 raw FPs decompose as 3 subject-restatement(unanimous) + 1 quotation/meta + 1 negation-only = 5; the '1 split vote' subject case lives in raw.split=4, NOT in raw.false_positive=5. The material's own next sentence correctly states '5 false-positive / 4 split' as disjoint, so the paragraph is internally self-contradictory. This misattributes the split-vote into the FP count.
- 🔢 §2b (minor / provenance): '≈85%-Bridge base rate' at 7B is not a results.json value. results.json gives rq2_taxonomy.per_scale.7B raw_agreement_pbar=0.833 and note Pe≈0.847. Source the number to P̄=0.833 (or Pe≈0.847) rather than an unsourced '≈85%'.

### `anonymize_spec.md` — anonymize-E5  [revise]
**处理**:⏳ fold-in 修:文件计数是 draft 估值(实测 WHYAAAI 53 非 38、终极review 16 非 11、results.json 2367 行);改实测或改'示例/dozens'口径
- 🔢 §1 L6 表 + §2:『WHYAAAI ... 38 tracked files』/『touch 38 files for WHYAAAI alone』—— 实测 git grep -lI WHYAAAI = 53 个跟踪文件(排 experiments/ 亦有 31;working-tree 全类型 189),无任何口径 = 38;差 15。此数支撑 §2『allowlist 优于 blacklist』论证。
- 🔢 §2:『11 for 终极review』—— 实测 git grep -lI 终极review = 16 个文件,非 11;差 5。
- 🔢 引言 + §5:results.json『grown to ~2.3k lines』—— 实测 paper/results.json = 2367 行(近 ~2.4k),『~2.3k』偏低(近似值,低 severity)。
- ⚠ §1 overclaim: 标题声明『(Concrete instances confirmed by a repo scan on 2026-07-08.)』,但 L3 行把本地路径 /Users/whyu/… 归到『some src/*.py』被同日扫描反证 —— tracked 与 working-tree 的 src/*.py 均无 /Users/(git grep -lI 与 grep -rlI 皆空)。src/*.py 真实泄漏是 WHYAAAI 代号(13 文件)+ 中文 docstring(62 文件)+ /inspire 仅在 src/vendor_patches/{easyedit_mom2_dataset.py,test_mom2_dataset.py}。把扫描反证的泄漏点标为 scan-confirmed 即 overclaim;且实操风险:实现者照 L3 grep src 找 /Users/ 空手→可能漏掉真正需清洗的代号/中文 docstring。同一『scan-confirmed』框架下的 38/11 计数也被同日扫描反证(见 number_errors),整条『confirmed by repo scan 2026-07-08』断言不可靠。

### `supp_prereg_gates.md` — prereg-supp-D1  [revise]
**处理**:🔧 已加 G5 更正 banner(冻结 max-stat 29.2%<50% 门不过;draft 的 100%/降 suggestive/待回传 均过期)
- 🔢 G5 max-stat 数值缺失且与源冲突:材料称『A prereg-correct max-stat recomputation requires the per-distractor base jsonl and is deferred』(尚未算/待办)。但 results.json wa_main.gates.G5_premention 与 wa_main._g5_硬伤4.maxstat_frozen 记录该重算已于 2026-07-08 完成 = 19/65 = 29.2%(src/wa_g5_maxstat.py；窗=el_idx，literal [m−20,m−1] 口径 ≤29%)，且 29.2% < prereg 50% 地板=门不过。materials 把『已算且失败(29.2%)』写成『deferred』，数字与源不符。
- 🔢 G5 Status/Observed 单元格数值不完整:Observed 只写『65/65 = 100% under a fixed z≥2 threshold』，漏记同源的冻结判据实测 19/65 = 29.2%(FAIL)；Status『suggestive support』与源判定(冻结口径不过门/W-A void 区间)不符。
- ⚠ 【overclaim / 承重档位拔高】G5 被写成『downgraded from a certified gate to suggestive support』，且让 G5 继续给 W-A 提供『suggestive support』。但权威源(results.json wa_main.gates.G5_premention / _g5_硬伤4 / prereg-wseries §7.5 line 86)判定:冻结口径(distractor max-stat)= 19/65 = 29.2% < prereg 50% 地板 → 按 G5 阈值行(『<50% ⇒ W-A void』)这是 FAIL，不是 suggestive。硬纪律#3『凡 suggestive 不写 confirmed / 凡 null 只写 null』的镜像:此处把一个 FAIL 写成 suggestive=过度宣称。正确档位:G5 在冻结口径下不过门，W-A 唯一承重腿=A2 干净 null(results.json 明写『承重腿=A2 null，不依赖 G5 阈值』)。
- ⚠ 【取数纪律 / 选择性引用】材料自报的数字来源 `wa_main.gates.G5_premention` 同一字段里既有『65/65=100%(z≥2)』也有『=19/65=29.2% … 冻结口径下 premention 灵敏度门不过』。材料只摘对己有利的 100% 与『frozen criterion=max-stat』标签，删掉同字段内失败的 29.2%，属从源字段挑子集。
- ➖ 骨架点名『G5 post-hoc z≥2 降 suggestive 见硬伤4』——但硬伤4 的权威落点是冻结 max-stat=29.2%<50% 地板=门不过(prereg-wseries §7.5 line 86 / results.json _g5_硬伤4)。材料缺这条硬伤4 正解:未披露 max-stat 已重算=29.2% 及其 FAIL 结论，也未据此把 W-A 承重腿显式收敛到 A2 null。

### `supp_distractor_lens.md` — distractor-lens-D3  [revise]
**处理**:🔧 已加 G5 更正 banner(CONSORT G5 行须并列 z≥2 100% 与冻结 max-stat 29.2% 门不过)
- 🔢 §5 G5 caveat: 'A prereg-correct max-stat G5 requires re-transferring results/wa/base_r*of8.jsonl (per-distractor z) for recomputation' is FALSE. paper/results.json wa_main._g5_硬伤4._status = '本地 wa base 分片可算 → 已算,非只 flag'(src/wa_g5_maxstat.py, results/wa_g5_maxstat.json) — the recomputation is DONE. Value: maxstat_frozen = 19/65 = 29.2% (a2rev 5/16, a2held 13/41, calib 1/8).
- 🔢 §5 CONSORT table G5 row + §7 G5 bullet report G5 as '65/65 = 100% (post-hoc z≥2)' with no counterpart. The z≥2 = 65/65 = 100% figure itself matches wa_main._g5_硬伤4.z2_variant, but omitting the frozen criterion makes the reported G5 value wrong-in-context: authoritative wa_main.gates.G5_premention now states z≥2's 100% '严重高估' and the binding frozen value is 19/65 = 29.2% < 50% floor.
- ⚠ OVERCLAIM (G5): §5 caveat says G5 is 'downgraded from a gate to suggestive support' and §7 says it 'supports rather than gates'. Authoritative paper/results.json wa_main._g5_硬伤4.interpretation = '冻结口径 G5=29.2%<50% 地板=premention 灵敏度门不过' (frozen max-stat = 29.2%, BELOW the prereg 50% floor = gate FAILS). Per prereg-wseries §1 G5 is a three-tier rule ('≥80% PASS;<50% W-A 作废;50–80% suggestive'); 29.2% sits in the <50% VOID tier, not the 50–80% 'suggestive' tier. Reporting a floor-failing gate as favorable 'suggestive support' is an overclaim; prereg action_714 forbids it verbatim ('禁再报 G5=100% PASS' and requires stating '严格 max-stat 仅 29%').
- ⚠ DISCIPLINE (stale-source): the material reproduces the superseded prereg-wseries §7.5 framing ('G5 只作 suggestive; max-stat 待回传重算'). §7.5 in prereg-wseries.md is itself stale — results.json (the binding 取数真源) has since replaced it with the computed 29.2% floor-fail. Numbers/reading must follow results.json, not the stale prereg §7.5 sentence.
- ➖ The load-bearing frozen distractor max-stat result is entirely absent: wa_main._g5_硬伤4.maxstat_frozen = 19/65 = 29.2% (< prereg 50% floor), with per-group breakdown a2rev 5/16, a2held 13/41, calib 1/8. This is the single most consequential W-A number added since the material was drafted and it is not in the appendix.
- ➖ The prereg §1 G5 three-tier rule (<50% → W-A voided; 50–80% → suggestive; ≥80% → PASS) is not stated; the material only cites the ≥80% PASS threshold, so a reader cannot see that 29.2% falls in the VOID tier.
- ➖ The action_714 decision fork is not represented: wa_main._g5_硬伤4.action_714 = W-A must either (a) drop '可靠升起', restate as 'o_old systematically elevated vs distractor mean (z≥2) but strict max-stat only 29%' with A2 null load-bearing, OR (b) demote the whole section to appendix. The material's 'G5+A2+A3 三件套' framing predates this fork.
- ➖ The window_caveat (max-stat window = el_idx whole eligible pre-window, wider than prereg-literal [m-20,m-1]; true narrow-window max-stat ≤ 29%) is omitted — relevant because it can only make G5 worse, not better.

### `release_and_licenses.md` — release-licenses-E4  [ok]
**处理**:✅ OK;⏳ fold-in 补:因果 battery 五臂应含 C 臂(N/T/D/P/C,strong_competitor_M4),draft 漏 C
- ➖ 制品清单(A.4)『因果对照 battery』行只列 N/T/D/P 却标『五臂』,漏 results.json 里承重的 C 臂(same-relation strong competitor,sup_battery._C_arm_M4 / strong_competitor_M4;T−C 四指标全排零、坐实 o_old 特异性);results.json 的规范五臂集是 N/T/D/P/C(见 _pending_draft_edits『M4 后…五臂图 N/T/D/P/C』)。manifest 对该 battery 的描述不完整。

### `supp_manifest.md` — supp-manifest-E3  [ok]
**处理**:✅ OK;⏳ fold-in 补 Source 行:memit_replication / rq3.sup_battery.contrasts / necessity.held / wide_census_traceless / G5 冻结 29.2%
- ➖ §1 Source 列缺 `memit_replication`（含 `._diagnosis`/`._32b_final` 32B 双故障脚注）。MEMIT 复现是 §2 自查判定的 load-bearing（abstract 已许诺『(ROME/MEMIT)』、必进正文 §4），但 S3 Source=marginal_B3/cross_arm_paired_ci/alpha_sweep、S12 Source=capability._bos_note/f2.arms.B0P，两处均未指向 memit_replication，折 LaTeX 时无从溯 ES 0.54→0.45 / drop 0.090 / RR 0.333 / Loc 0.965 的取数路径。
- ➖ §1 S3 Source 缺 `rq3.sup_battery.contrasts_B3_mean_ci_p`。S3 material 明列 T−P/D−N/P−N 配对对照，且 T−P（RR −0.095[−0.171,−0.029]）是 §6 headline=load-bearing；但这三组只存在于 contrasts_B3_mean_ci_p，而 Source 只写 marginal_B3 / cross_arm_paired_ci（后者仅含 T−N/C−N/T−C）/ alpha_sweep→T−P 源路径缺席。
- ➖ never-silent / 重推必要性（§2 row 判『✅ 正文承重』）的两个源在 §1 Source 列无归属：`necessity.held`（held 14/14）与 `rq2_taxonomy.wide_census_traceless`（0/17）。§2 把 census 全表映到 S8，但 S8 Source=wa_main.*/wa_extensions._ladder_status，不含 wide_census_traceless；S4 Source=pooled/neutral_rerun_S1/b16_widened_pool 也不含；necessity 整块无任何 §1 归属行。
- ➖ G5 冻结 max-stat 口径值缺席：自报数字块与 §1 S8 material 只给 post-hoc『z≥2 65/65』，未并列冻结判据实测 19/65=29.2%（wa_main._g5_硬伤4.maxstat_frozen，<50% 地板=gate 不过）。S8 material 自称『G5 全结果 + G5 post-hoc 披露』，则冻结口径值须同现，否则『全结果/披露』不完整。
