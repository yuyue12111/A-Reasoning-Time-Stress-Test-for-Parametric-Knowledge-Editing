# Prewrite materials — 判官对抗审查台账(judge review ledger,权威配对版)

gap-review `prewrite-materials` workflow(wf_cd30418a-ebe;draft→judge,20 agents)。**判官经 resume 权威配对**(按 pipeline item 身份,重判于当前 results.json——含 C2/硬伤4 已落库),取代此前按内容手工匹配的旧版。judge 逐条 Read `results.json` 核数字/引用池/禁区。**fold-in(7/11–13)必读**;🔧=已内联修、⏳=留 fold-in、✅=判官通过。取数纪律:折 LaTeX 时数字仍从 results.json 复核。

## 汇总(权威配对)

| 材料 | 判官 | 处理 |
|---|---|---|
| `aia_relevance.md` (relevance-必3) | ok | ✅ 判官零 issue,原样。非阻断建议:'halves'可作'more than halves'(0.085/0.193=44%);0.193 落主表时标有效 n=198/b0ok。 |
| `ethics_reverting_truth.md` (ethics-必4) | ok | ✅ 判官通过。我另内联做了保守改进(Recall 22% 非全 re-derivation→'a re-derivation or a direct recall';B26 'measurement noise'→'点估内 ±0.02, not certified')——非必需但更精确,保留。 |
| `methods_level_vs_change.md` (level-change-D4) | ok | ✅ 判官通过。我另内联做了保守改进(F1 no-drift 排 7B math-confound,+0.08 margin≈0)——非必需,保留。 |
| `release_and_licenses.md` (release-licenses-E4) | ok | ✅ 判官通过,原样。 |
| `supp_prereg_gates.md` (prereg-supp-D1) | revise | 🔧 已加 G5 更正 banner:body 把 G5 说成'降 suggestive / W-A 入 suggestive 档 / max-stat 待回传'均过期(冻结 max-stat 29.2%<50%=门不过;W-A 据 A2 null 不据 G5)。fold-in 以 banner 为准重写 S.4。 |
| `supp_distractor_lens.md` (distractor-lens-D3) | revise | 🔧 'traceless' 禁词【已删/改写】(§7 A1 bullet)+ G5 更正 banner【已加,CONSORT G5 行并列 z≥2 100% 与冻结 29.2% 门不过】。注:A3 分组 n(a2rev 8+a1 16+a2held 20=44≠48)差 calib 4 未拆,非错。 |
| `methods_llm_compliance.md` (llm-compliance-D6) | revise | 🔧 κ=0.836 改标 judge-vs-rule 校验(非 inter-judge)【已修】+ 'three judges'→'three for taxonomy/validation, 2-of-3 CLR-polarity'【已修】。⏳ fold-in:§3 表头'same three-judge protocol'各仪器协议不同(收紧)+ repro-checklist 补 multi-hop scorer-audit 仪器。 |
| `methods_judge_pipeline.md` (judge-methods-D2) | revise | 🔧 'traceless' 禁词【已删】(§3 Associative 描述)。⏳ fold-in:①subject-scrub 假阳计数与 rq3.metric_validation 对齐 ②rerun-ledger 50-pool κ 列填 0.79(combined_50pool)。 |
| `supp_manifest.md` (supp-manifest-E3) | revise | ⏳ fold-in:S14 run-ledger 'four 0.208' 实为 **3** 个 run 上下文(C 臂 marginal / F2-B1 / 另一),改计数。 |
| `anonymize_spec.md` (anonymize-E5) | revise | ⏳ fold-in:文件计数是 draft 估值,实测 WHYAAAI=53(非 38)、终极review=16(非 11);改实测或改'dozens/示例'口径(计数非 load-bearing,scrub-grep 运行时自查真值)。 |

## 各材料判官原始 findings(权威,fold-in 核对用)

### `aia_relevance.md` — relevance-必3  [ok]
**处理**:✅ 判官零 issue,原样。非阻断建议:'halves'可作'more than halves'(0.085/0.193=44%);0.193 落主表时标有效 n=198/b0ok。


### `ethics_reverting_truth.md` — ethics-必4  [ok]
**处理**:✅ 判官通过。我另内联做了保守改进(Recall 22% 非全 re-derivation→'a re-derivation or a direct recall';B26 'measurement noise'→'点估内 ±0.02, not certified')——非必需但更精确,保留。


### `methods_level_vs_change.md` — level-change-D4  [ok]
**处理**:✅ 判官通过。我另内联做了保守改进(F1 no-drift 排 7B math-confound,+0.08 margin≈0)——非必需,保留。


### `release_and_licenses.md` — release-licenses-E4  [ok]
**处理**:✅ 判官通过,原样。


### `supp_prereg_gates.md` — prereg-supp-D1  [revise]
**处理**:🔧 已加 G5 更正 banner:body 把 G5 说成'降 suggestive / W-A 入 suggestive 档 / max-stat 待回传'均过期(冻结 max-stat 29.2%<50%=门不过;W-A 据 A2 null 不据 G5)。fold-in 以 banner 为准重写 S.4。

- 🔢 S.4 G5 注:『A prereg-correct max-stat recomputation requires the per-distractor base jsonl and is deferred』——与 results.json 冲突。wa_main._g5_硬伤4.maxstat_frozen = 『19/65=29.2%』(2026-07-08 已用 src/wa_g5_maxstat.py 算出;a2rev 5/16、a2held 13/41、calib 1/8),prereg-wseries.md §7.5 line 86 亦明记『【7/8 已算,数据本地在盘】=19/65=29.2%』。冻结 max-stat G5 既非 deferred 亦非缺失,而是=29.2%,材料完全漏报此数,且『deferred』为不实陈述。(注:窗口 caveat——29.2% 算于 el_idx 更宽前窗,是上界,真 [m-20,m-1] ≤29%;仍远低于 50% 地板。)
- ⚠ S.4 G5 行 Status「downgraded from gate to suggestive support」+ 注「G5 is downgraded from a certified gate to suggestive support」= OVERCLAIM。冻结口径实测值 29.2%(results.json wa_main._g5_硬伤4.maxstat_frozen)落在 prereg 的 <50% = W-A void/fail 档,不在 suggestive(50–80%)档(prereg-wseries.md §5 line 27:≥80% PASS;<50%→W-A 作废;50–80%→suggestive)。results.json 明写「冻结口径 G5=29.2%<50% 地板=premention 灵敏度门不过」「禁再报 'G5=100% PASS'」。把一个 below-floor 的失败门写成『suggestive support』是把 null/fail 说成部分正证。诚实口径:冻结 max-stat premention 门不过,『表征提及前可靠升起』不作为冻结门成立,W-A 靠不依赖阈值的 A2 null 承重。
- ⚠ S.4 G5 注推导出的『W-A therefore enters at the suggestive tier only』其立论依据(G5=suggestive)不成立;W-A 只应以 A2 干净 null(AUC 0.507, perm p 0.487)+ G4 fail 声明为据,而非把 G5 说成 suggestive 支持。

### `supp_distractor_lens.md` — distractor-lens-D3  [revise]
**处理**:🔧 'traceless' 禁词【已删/改写】(§7 A1 bullet)+ G5 更正 banner【已加,CONSORT G5 行并列 z≥2 100% 与冻结 29.2% 门不过】。注:A3 分组 n(a2rev 8+a1 16+a2held 20=44≠48)差 calib 4 未拆,非错。

- 🔢 G5 frozen max-stat is STALE / contradicted. Material (§5 caveat) states the prereg-correct max-stat G5 'requires re-transferring `results/wa/base_r*of8.jsonl` (per-distractor z) for recomputation (prereg-wseries §7.5)', implying it is not yet done. results.json wa_main._g5_硬伤4.maxstat_frozen = '19/65=29.2% (a2rev 5/16, a2held 13/41, calib 1/8)' and wa_main.gates.G5_premention explicitly report it as ALREADY computed and < the prereg 50% floor; prereg §7.5 line 86 struck the 'need to re-transfer' text ('~~若要...须回传~~ 【7/8 已算,数据本地在盘】'). The authoritative 29.2% number is omitted entirely. FIX: report 65/65=100% strictly as the z≥2 variant AND report frozen max-stat G5 = 19/65 = 29.2% < 50% floor = gate fails.
- 🔢 (Inherited from source, not a transcription error) A3 subgroup ns do not sum to the total: material copies results.json faithfully (all n=48; a2rev n=8 + a1 n=16 + a2held n=20 = 44), leaving 4 cases uncategorized. Numbers match wa_main.A3 exactly so this is not a material-introduced mismatch, but the 44 vs 48 gap should be reconciled or the groups declared non-partitioning before fold-in.
- ⚠ OVERCLAIM (G5 status). §5 caveat + §7 frame G5 as merely 'downgraded from a gate to suggestive support' / 'suggestive only', and say the prereg-correct max-stat 'requires re-transferring results/wa/base_r*of8.jsonl ... for recomputation'. But results.json wa_main._g5_硬伤4.maxstat_frozen and prereg-wseries §7.5 (line 86) both show the frozen distractor max-stat G5 was ALREADY computed = 19/65 = 29.2%, which is BELOW the prereg 50% floor => the frozen premention sensitivity gate FAILS. Presenting a failed frozen gate as 'suggestive support' while omitting 29.2% understates the failure. Per prereg §7.5 the honest read is: gate does NOT pass; only A2 null (independent of G5) is load-bearing. This is an overclaim-by-omission relative to results.json.
- ⚠ FORBIDDEN-WORD caution (borderline). §7 A1 bullet prints "'never traceless' / 'never silent'". prereg-wseries §5 lists 'traceless' as a 全文禁词 whose only exception is 'A1 判官级门过' — but A1's G4 gate FAILED (13.8% ≪ 70%), so the exception is unmet. The material carefully attributes the phrasing to the wide-census/taxonomy (which results.json necessity + wide_census_traceless DO endorse) and explicitly disclaims A1, so it is borderline rather than flatly forbidden — but the loaded term should be reworded to a string-level statement to stay clean of §5.
- ⚠ External cite-as-frame refs (2606.13603 'Beyond the Commitment Boundary', 2605.06723) cannot be verified from results.json; they are permitted as cite-as-frame by prereg §5 and are correctly gated/Discussion-only/subject=[cite], but the arXiv IDs and titles are unverifiable from the provided sources and must be confirmed before fold-in.
- ➖ Honest frozen-gate G5 result absent. The appendix bills itself as 'the entirety of the instrument's credibility record', but omits the prereg-frozen max-stat G5 = 19/65 = 29.2% (< 50% floor) that exists in results.json (wa_main._g5_硬伤4 / gates.G5_premention). An instrument-credibility CONSORT must carry this failing frozen-gate number, not defer it as 'pending recomputation'.
- ➖ All other skeleton components are present and correct: 20 same-relation distractor z-calibration (§1–§2), permutation max-stat exact p=1/21 (§4), six token-id-level position-exclusion classes incl. induction/copy-head suffix guard (§3), CONSORT with edited/base per-gate n + G2/G3 fail + amb flag (§5–§6), decoder-index convention hs[k]=decoder k−1 / edit layer 12 = hs[13] (§1), and the 7/14 W-A admission gate (header + checklist item 7). No further skeleton gaps.

### `methods_llm_compliance.md` — llm-compliance-D6  [revise]
**处理**:🔧 κ=0.836 改标 judge-vs-rule 校验(非 inter-judge)【已修】+ 'three judges'→'three for taxonomy/validation, 2-of-3 CLR-polarity'【已修】。⏳ fold-in:§3 表头'same three-judge protocol'各仪器协议不同(收紧)+ repro-checklist 补 multi-hop scorer-audit 仪器。

- ⚠ §1 判官段(§3 drop-in 句)把 Cohen's κ=0.836 归为『inter-judge agreement(判官间一致)』——错。results.json 的 0.836 出自 metric_validation.vs_RRs_strict_decontam.cohen_kappa,是【中性判官面板 vs 去污 RRs 规则】的判官-规则一致度(scorer-validation 口径),不是判官彼此之间的一致。材料自己的 §2 声明('two scorer-validation studies')和自报来源表('Cohen's kappa vs. strict decontaminated reversion (RRs)')都把它写成 judge-vs-rule,唯独 §3 prose 把它抬成 inter-judge reliability=对内矛盾+overclaim。只有 Fleiss κ=0.52(rq2_taxonomy.pooled)才是真 inter-judge。
- ⚠ §1 首句『Every LLM-derived label in this work is produced by a fixed panel of three independent judges』属 overclaim,被材料自己 §3 清单推翻:CLR-polarity check 明列『≥2 judges』(v1_clr_polarity._status:『37 unique case × ≥2 判官』),multi-hop scorer-audit panel 判官数未给定。并非全部标签都出自『固定三判官』。
- ⚠ §3 清单表头『All are the same three-judge, majority-vote / strict-precedence protocol』属 overclaim:各仪器协议不同——taxonomy=strict precedence 三判官;neutral reversion-validation=OLD/NEW/NEITHER 多数决(非 strict precedence);CLR-polarity=≥2 判官极性判定;multi-hop=scorer-audit 纠错。不是『同一协议』。
- ➖ §2 repro-checklist 声明行不 exhaustive:只枚举 taxonomy + 两个 scorer-validation study,漏掉 §3 清单里列为第 4 仪器的 multi-hop scorer-audit panel(§RQ1 2-hop,LLM 判官纠 scorer 变音符/短目标假阳)。合规政策要求把所有 LLM 使用披露完整;该 panel 是评测仪器、非『incidental drafting/coding』,应进声明的仪器清单。

### `methods_judge_pipeline.md` — judge-methods-D2  [revise]
**处理**:🔧 'traceless' 禁词【已删】(§3 Associative 描述)。⏳ fold-in:①subject-scrub 假阳计数与 rq3.metric_validation 对齐 ②rerun-ledger 50-pool κ 列填 0.79(combined_50pool)。

- 🔢 §1 假阳分类 'of 5 raw false positives, 4 are subject-restatement (3 unanimous + 1 split vote), vs. 1 quotation/meta and 1 negation-only' —— 与 results.json rq3.metric_validation.v1_clr_polarity 不符。raw.false_positive=5、raw.split=4 是两个独立桶(1741-1746)。fp_taxonomy(1748-1752)=subject_restatement_only '3 全票+1 分裂票'、quotation_or_meta 1、negation_only 1。故 5 个 FP 的构成恰=3(主体复述,全票)+1(引用/meta)+1(否定)=5,只有 3/5 FP 是 subject-restatement;那个 '+1 分裂票' subject-restatement 属于另设的 split=4 桶、不在 5 个 FP 内。材料把 split 折进 FP 得 '4 of 5',且 3(全票)+1(split)+1+1=6 条被塞进一个 5 条的池=off-by-one 自相矛盾(材料同段 precision 行又正确写 '5 false-positive / 4 split' 两桶分列,内部打架)。正确:'3 of the 5 raw FPs are subject-restatement (all unanimous); a further subject-restatement is 1 of the 4 split-vote cases → 4 across the FP+split pool'。定性结论(subject-restatement 为 FP 主类)在 3/5 下仍成立,仅计数需改。
- ⚠ 禁词 'traceless': §3 写 'The Associative (residual / traceless catch-all) route ...'。prereg-wseries.md §5 全文禁词表把 'traceless' 列为禁用,例外仅 'A1 判官级门过'。但 A1 未过关(results.json base_probe._pending_draft_edits/W 系列:G4 fail 4/29 → A1 不可判、wide_census CLR0_wide∩reverted=0 按 prereg 声明『本数据不可答』)——被点名的 A1 judge gate 恰未通过。佐证 0/17 又是 string-level 普查(wide_census_traceless._status 明言宽口径 substring、非判官验证)。故字面 'traceless' 应替换为 'residual / no-quotable-span catch-all' 或 'never-silent(判官义)'。注:b16 verdict 原文用的是 '从不无声/never silent',非 traceless。
- ➖ §3 rerun ledger 表 '50-pool' 行的 Fleiss κ 列写 '—',但该 headline 池的判官一致性已在 results.json b16_widened_pool._kappa_C2.combined_50pool 落定:in-pop 路由 Fleiss κ=0.790(P̄=0.893)、panel κ=0.875(P̄=0.921)、new33-only κ=0.789。材料自己在 §2b 立的原则是『report κ alongside raw agreement』,却让承重 headline 池 κ 缺席——应把 0.790 填入该行(或表注),与原 17-池 0.765 一致这点亦可一并说明。

### `supp_manifest.md` — supp-manifest-E3  [revise]
**处理**:⏳ fold-in:S14 run-ledger 'four 0.208' 实为 **3** 个 run 上下文(C 臂 marginal / F2-B1 / 另一),改计数。

- 🔢 S14 run-ledger 描述句『四个「0.208」溯源』计数与 results.json 不符:results.json 中 RR 点估=0.208 只有 3 个不同 run 上下文——rq3.sup_battery.marginal_B3.C.RR(C 臂,cf200sup_strong)/ f2_zerothink_deconfound.arms.B1.RR(cf200f2)/ f3_sampling_robustness.greedy_control.B3.RR(cf200samp greedy)。其余 0.208 出现均为 CI 上界(capability.families.R1-Distill-Llama.rr_ci 的 8B 上界 [0.088,0.208]、multihop.single_hop_anchor_8B.RR_ci 上界、以及各 rr_ci 内的点值副本),不是需在 ledger 里按 run-tag 消歧的独立回退-RR 值。『四』应核为『三』,或显式声明计入 CI 界的口径。这是全篇唯一数字瑕疵、非承重、build-time 可一行修复。

### `anonymize_spec.md` — anonymize-E5  [revise]
**处理**:⏳ fold-in:文件计数是 draft 估值,实测 WHYAAAI=53(非 38)、终极review=16(非 11);改实测或改'dozens/示例'口径(计数非 load-bearing,scrub-grep 运行时自查真值)。

- 🔢 §2 ("a blacklist scrub ... would have to touch **38 files for WHYAAAI alone**") and §1 leak-table row L6 ("`WHYAAAI`... **38 tracked files**"): the count is wrong. `git grep -lI 'WHYAAAI'` at committed HEAD 955dda3 (2026-07-08, the same date the spec claims it scanned) returns **53** files, not 38. No charitable subset matches 38 either: excluding *.md internal docs = 45; code/config-only (yaml+sh+py+json) = 45. This is a ~28% undercount, and for a release-scrub spec it understates the residual-leak surface (the exact failure mode the tool guards against). Not a results.json value; verified against repo ground truth.
- 🔢 §2 ("and **11 for `终极review`**"): wrong count. `git grep -lI '终极review'` at HEAD returns **16** files (analysis/10_jlens_workspace.md, 5×experiments/*.yaml, gap-review-charter.md, gap-review.md, paper/results.json, plan.md, results/a3_neutral/summary.json, review-charter.md, 4×src/*.py), not 11. No natural subset yields 11.
