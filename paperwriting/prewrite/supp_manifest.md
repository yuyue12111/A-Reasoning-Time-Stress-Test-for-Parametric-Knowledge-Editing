<!-- 写作前材料(gap-review supp-manifest-E3);折进 LaTeX 时复核数字;非写作真源 -->

# Supplementary manifest (gap-review E3)

**用途**:写作前把每一份材料归位到 main body / supplementary,并给出正文指针。折进 LaTeX 时数字须逐条对 `paper/results.json` 复核;本文件不覆盖 `base_probe._pending_draft_edits`(取数与指令仍以 results.json 数据块为准)。

## 0. 政策约束(gap-review E1/E3,非 results.json)

- 版面:正文 **7 页** + 至多 **2 页仅参考文献**(共 9);**正文无 appendix 位**。C 节/终极review 全部「下附录」项去向 = **supplementary**。
- Supplementary + code 死线 **7/31 (UTC-12)**;checklist 随论文(7/28)单独上传,**明文计入录取决策**。
- 关键含义:**审稿人不被要求阅读 supplementary**(Phase-1 = 3 人审全文 + AI 辅助,无 rebuttal)。因此任何 load-bearing 材料**不得只活在 supp**——正文必须留一句结论 + `\ref{supp:...}` 指针(§2 自查一节逐条守门)。
- 净零版面纪律:supp 化的是「全表 / 全分辨率 / 细节」,不是「结论」;结论恒留正文。

---

## 1. Supplementary manifest(材料 → 归属 + 正文指针)

> 列义:**Supp §** = 建议 supp 小节;**Material** = 下沉的完整物;**Main-text home** = 正文必须保留的一句话结论 + 指针章节;**Source** = `results.json` 取数路径(折 LaTeX 时复核)。

| Supp § | Material(下沉全物) | Main-text home(正文留句 + 指针) | Source (`results.json`) |
|---|---|---|---|
| **S1 Preregistration & validity gates** | prereg-wseries 冻结版 + commit hash;battery / placebo / C 臂 blind-seed 记录;S10 prereg 头注;**G1–G7 门表**(阈值 / 实测 PASS-FAIL,含 G7 两轮与硬边界);端点改动自动降级政策句 | §3.6 一句:"predictions and the placebo donor were pre-registered … (App.~S1: gate table, thresholds, PASS/FAIL)"(现 §3.6 L114 有 confirmatory/exploratory 句,补 App 指针) | `rq3.sup_battery.verdict`;`wb_representation_repair.g7`/`.g7_retry`;prereg-wseries §1 |
| **S2 Judge pipeline** | 3 判官 / 多数决 / strict precedence / verbatim-span 强制 / 中性 prompt(JUDGE_PROMPT_NEUTRAL)/ 污染-重跑史;**model version + full judge prompts + raw votes 释出**;κ 可靠性 + V1 极性验证全表 | §3.5 一句:judge protocol + subject-scrub(`_without_subject`)+ κ 数字,指 App.~S2(现 κ 埋在 §2 L73,须搬进 §3.5 判分之家) | `metric_validation.vs_RRs_strict_decontam`;`metric_validation.v1_clr_polarity` |
| **S3 Five-arm causal battery(全表)** | N/T/D/P/C × ES/RR/RRs/CLR 边际 + **全部配对对照**(T−N/T−P/T−C/C−N/D−N/P−N);α-sweep 全 6 点(scope 消融) | §6 已报 T−P + P−N + D 反号(L250);补一句 **T−C 主报**(五臂含 C 强竞争者)+ 指 App.~S3;α-sweep 剂量轴留正文一句 | `rq3.sup_battery.marginal_B3`;`rq3.sup_battery.cross_arm_paired_ci`;`rq3.alpha_sweep` |
| **S4 Taxonomy(污染整表 + 全 7-cell + κ)** | ROME-greedy 3 尺度**污染版整表**(Bridge 17/19)+ 中性 17-池 + B16 五新 cell + 合并 50-池 + κ / 一致率行 + provenance(50 条各来自哪 run/解码) | §5 保留 headline(Bridge-dominant 50-池 68%);正文表只放中性列 + κ 行,污染整表指 App.~S4(`table_rq2.tex` 须从污染版重生成) | `rq2_taxonomy.pooled`;`rq2_taxonomy.neutral_rerun_S1.pooled`;`rq2_taxonomy.b16_widened_pool.combined_with_original` |
| **S5 6-scale base-probe(全表)** | 6 尺度 base:ans_old@B0/@B3/Δthink/base-CLR/ans_new;**F1 edit-specificity paired CI**;LEVEL-vs-CHANGE 设计说明 | §4 capability 主表折进 2 列(ans_old@B0 + Δthink)+ 一句 edit-specific 结论;完整 base 表 + F1 指 App.~S5 | `base_probe._six_scale_summary`;`base_probe.f1_edit_specificity.paired_ci` |
| **S6 Cap3 net-CLR(全表)** | 逐尺度 net_clr(edited−base)+ raw vs net slope + base-floor caveat(CLR 退役依据) | §4 CLR 退役 5 句(net-CLR 含零、gap 不随尺度扩);Cap3 全表指 App.~S6 | `emergence.cap3_netclr.full_6scale` |
| **S7 Logit-lens(全分辨率)** | 17 点 gap 扫描(decoder 轴)+ 峰值层 + install-sanity caveat;负 gap 带(decoder 7–11,编辑层上游);**无 held 臂 → 全图下沉**;**⚠ BLOCKED 声明(W2-3/P9 补;正文 §4.1 已按名断言,supp 必须逐字兑现)**:逐项工件 `results/probe/logitlens_cf200_ROME_B3.jsonl` 本地不存在,supp 须点名该路径 + 其应含字段(per-item `case_id` + 新/旧对象首 token logits)+ 状态 `BLOCKED_MISSING_PER_ITEM_ARTIFACT`,并说明后果(无法复核样本重叠/成员构成,无法复现逐例计数);**禁猜 case ID** | §5 只留文字:n=23、100% intact(同句附 n)、降级为「edit-install sanity」;曲线图指 App.~S7。**现行正文之家=§4.1**(W2-2 已成文) | `rq2_logitlens._authoritative_record`;`logitlens.gap_sampled` / `.layers_sampled` |
| **S8 W-A per-case lens + distractor 校准** | 20-同 relation distractor z + 置换 **max-stat 精确 p=1/21** + token-id 级位置排除(防 copy/induction)+ CONSORT;A1/A2/A3/G4/G5 全结果 + **G5 post-hoc 披露** | §5(条件于 7/14 内审)一段 suggest 档:表征在场 = null(A2)、G4 fail → A1 不可判;全物指 App.~S8。**不进 abstract/contrib** | `wa_main.A1`/`.A2`/`.A3`/`.gates`;`wa_extensions._ladder_status` |
| **S3b Section-3 sunk regressions(W2-4/P9 纪律)** | B15 base-recall 控制回归全表(matched/controlled slope、衰减%、case-block CI、family→row 敏感性)+ per-case ES-drop 与 RR log-odds 两条 slope 全表(点估/CI/rows/facts) | §3.3 各留一句方向性陈述 + 「The regression is in the supplement.」/「Both fits are in the supplement.」 | `emergence.b15_base_recall_control.b0_primary`;`emergence.percase` |
| **S9 W-B representation-repair(dissociation 全表)** | S/Pshuf/N/S+ 边际 + B1(S−Pshuf)/B2(LocAcc)/S−N 全对照(含 **S−N ES 排零细分**)+ α* pilot 剂量反应 + G7 两轮 | §4.5 保留两句诚实反例(primary RR 与零相容但 in-span CLR 落、LocAcc 为负)+ 「The complete endpoint set is in the supplement.」;**三条端点 CI(S−Pshuf 的 RR/CLR/ES、S−N 的 RR/ES、B2 LocAcc)全表指 App.~S9**(W2-4 下沉;正文不再印这些 CI)。正文**禁 mediation / concept-fix 措辞**(prereg 终裁 appendix) | `wb_representation_repair.confirm_arms`;`.pilot_dose_response` |
| **S10 Multi-hop propagation** | 8B × MQuAKE-CF 2-hop:per-template 表 + CONSORT(base-floor 门 / recut → n=150)+ G1 cond-c 抑制臂 | §4/§7 一句:within-case propagation-erosion 0.188 排零 + 「传播衰减非复辟」边界(8/9 neither);全物指 App.~S10 | `multihop.pooled`;`multihop.per_template_powered`;`multihop.g1_condc_suppressed` |
| **S11 Deployment-cost robustness(genbench)** | 部署门(single+think)双过 + worst-case 上界 + **B26 全量 TOST**(点估 + 90%CI,未认证) | §7 一句:GSM8K +0.005 / MATH 0.000 均 <±0.02(point-est.);worst-case + TOST 指 App.~S11。**禁写 certified equivalent** | `rq3.genbench`;`rq3.genbench_b26_tost`;`rq3.genbench_worstcase` |
| **S12 Setup 细节 + 陷阱脚注** | BOS A/B、clamp 扫描、还原双验(md5)、B0P 构造、sequential_edit 陷阱脚注、glob/provenance 防污染 checklist 行 | §3 各一句 + 指针(编辑强度 B0 已 matched 一句);细节指 App.~S12 | `capability._bos_note`;`f2_zerothink_deconfound.arms.B0P` |
| **S13 Methods-summary 表** | claim × instrument × validation × residual-bias 四列表(word-boundary + subject-scrub、κ=0.836 + V1、中性去偏、单编辑协议 + 还原验证、五臂 blind-seed、LEVEL-vs-CHANGE) | §3 或 contrib-4 一句「效度协议套件」+ 指 App.~S13(与 release 承诺句互表里) | `metric_validation.*`;`f3_sampling_robustness._ci_必2_fix` |
| **S14 Run-ledger + releases + LICENSES** | run-tag 台账表(四个「0.208」溯源、每个重跑值标 independent re-run same protocol);release 清单(code / 去污判分器 / budget harness / prereg / judge prompts+votes);**data/LICENSES.md**(CounterFact/MQuAKE/GSM8K/MATH/R1-distill 权重逐条)+ 匿名化 scrub | §1/§7 一句 release 承诺(AIA CFP 明文加分件);台账 / LICENSES 指 App.~S14 | `f3_sampling_robustness.greedy_control`;`f2_zerothink_deconfound.arms.B1`(0.208 溯源) |

---

## 2. 自查:critical material 不得只在 supp

> 规则:审稿人不读 supp。凡 **load-bearing**(承载 headline / contrib / abstract 断言)的材料,正文必须有独立可读的一句结论;supp 只放全表。逐条确认「正文之家」存在(缺 = 待补,标 ⚠)。

| Load-bearing claim | 正文之家(须存在) | Supp(全物) | 判定 |
|---|---|---|---|
| Erosion 随 capability 涌现 | §4 主段:两高端 cell 各自显著(Qwen-32B **0.106** [0.030,0.182]、Llama-70B **0.107** [0.032,0.182])+ 族内单调序;pooled slope 标 supporting | S5/S6 全表 | ✅ 正文承重(per-cell + slope) |
| Erosion = edit-specific(非 base 漂移) | §4 一句 + capability 表 2 base 列:base ΔP(o_old)≈0([−0.080,+0.040] n=199),edited RR 0.193,margin 0.214 | S5 F1 全表 | ✅(现 draft 缺 base 列 → **待补**) |
| 第二编辑器(MEMIT)复现 | abstract "(ROME/MEMIT)" 已断言 → §4 replication 行须在正文:ES 0.54→0.45、drop **0.090** [0.010,0.170]、RR@B3 **0.333** [0.250,0.426]、Loc 0.965 | S3/S12(32B 双故障脚注) | ⚠ **不得 supp-only**:abstract 已许诺,MEMIT 行必须进正文 §4 |
| 因果 fix 有符号 / 特异 / 剂量 | §6 主段:T−P 排零(L250 已有)+ 补 **T−C** 主报(ES +0.121 [0.051,0.192] p=.0004;RR −0.094 p=.006;C≈N)+ α-sweep 剂量句 | S3 全表 | ✅(T−C 一句 **待补**,B17 化解) |
| Fix 不伤通用能力 | §6/§7 一句:GSM8K +0.005 / MATH 0.000(<±0.02, point-est.);measure=point-equivalent 非 certified | S11 全表 | ✅(措辞守「不称 certified」) |
| "Pre-registered" 声明 | §3.6 一句 validity-gate 摘要 + App.~S1 指针(现文四处 "pre-registered" 却无可验物) | S1 门表 | ⚠ **待补**:声明与可验物须同现,否则 supp-only = 空口 |
| 判分可靠性(κ)+ subject-scrub | §3.5 一句:κ=**0.836**(agreement 0.93,precision 0.92)+ `_without_subject` 剜主体复述 | S2 全物 | ⚠ κ 现埋 §2 L73/L47 → **搬进 §3.5 判分之家**(subject-scrub 现 draft 零字) |
| CLR 极性可信 | §3.4 一句脚注:CLR 阳性 ~94% 真回忆,极性假阳 ~6%(paper 口径)| S2(V1 全表) | ✅ 脚注即可(CLR 在正文用) |
| 机理 taxonomy(Bridge-dominant) | §5 主段:50 committed reversions / 7 cell / 2 族,Bridge **68%** / Recall 22% / RO 8% / Assoc 1;中性 17-池 82.4% 伴报 | S4 污染整表 + κ | ✅ 正文承重 |
| Never-silent / 重推必要性 | §5 一句:Associative **1/50**(判官级)+ wide-census **0/17**(宽口径普查);held 14/14 含 o_old 不回退 = 必要不充分 | S8 census 全表 | ✅(措辞守 §3 禁词:committed-reversion 口径,不写 evidence-of-absence) |
| LEVEL-vs-CHANGE 反混淆 | §3 或 §4 一句:base 是 LEVEL(随 scale 升)、我们量的是 edited CHANGE(B0→B3) | S5 表 | ✅(D4 统一命名段) |
| CLR 退役理由 | §4 5 句:net-CLR slope 含零([−0.008,0.150])、edited 恒低 base gap 不随尺度扩 | S6 Cap3 全表 | ✅ 正文承重(避免 supp-only 显得回避) |

**Supp-only 可接受项(不 load-bearing,审稿人不读无损 headline)**:S7 logit-lens 曲线(已降 install-sanity)、S8 W-A 全物 / distractor 校准(§5 suggest 档 + 7/14 gated)、S9 W-B 全表(prereg 定 appendix)、S10 multi-hop per-template、S11 worst-case、S13 methods-summary 表、S14 run-ledger / LICENSES。

---

## 3. 措辞守门(折 LaTeX 时对 prereg-wseries §5 禁词逐条 grep)

- **禁词**(全文):`we measured the workspace` / `the edit never enters the workspace` / 以我方数据为主语的 `ignition`/`planning`/`premeditation` / `traceless`(除非 A1 判官门过——**A1 的 G4 fail,故禁**;never-silent 只按 committed-reversion 口径 Associative 1/50 + census 0/17 写,不写 evidence-of-absence,不写「从不无声」)。
- **null 只写 null**:F1 = "base 无系统性向 o_old 漂移(paired CI 含零)",**不写** "truth-restoration 被否";W-B B1 = "RR 全含零、答案级回退不动"(S−N 的 ES +.092 排零须细分,B1=S−Pshuf 的 ES 含零)。
- **suggestive 不写 confirmed**:W-A G5 = "operationalized post-hoc (z≥2 variant)" 降 suggestive;emergence pooled slope 标 supporting、承重 = 两高端 cell + 族内序(K=2 caveat 随行)。
- **B26**:报「point-equivalent / Δ 落 ±0.02 内(point est.)+ 90%CI」,**禁 certified equivalent**。
- **answer-commitment 命名**:默认**不进 abstract/contrib**(7/14 裁);§5 小写 "answer commitment" 可,避 "commitment layer"(解剖学误读)。
- **W-B**:正文禁 mediation / concept-level 修复措辞;一句 cross-ref 合法,全表 appendix。
- **run-ledger**:F2/F3/greedy 对照的重跑值旁强制注 "independent re-run, same protocol";T−N/T−C/S10 差值统一走**配对**口径。

---

## 4. 与既有工单的关系

- 与 **B18 打包脚本**同工单(supp LaTeX 建仓 + 匿名化 + checklist)。
- Supp 结构(S1–S14)是**建议骨架**,非冻结;LaTeX 建仓时按 float 账落位。
- 本文件不新增「唯一真源」;取数纪律 = 一切数字回 `results.json` 数据块复核,指令队列唯一化为 `base_probe._pending_draft_edits`。
