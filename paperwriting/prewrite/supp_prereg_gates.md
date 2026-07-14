<!-- 写作前材料(gap-review prereg-supp-D1);折进 LaTeX 时复核数字;非写作真源 -->

> ⚠️ **G5 数字过期,以此更正为准(本材料 draft 于 硬伤4 正解落库之前)。** 权威源=`results.json wa_main._g5_硬伤4` + `prereg-wseries §7.5`:
> W-A G5(premention 灵敏度)冻结 prereg 判据=**distractor max-stat**(o_old 超全 20 distractor,p=1/21),本地重算 = **19/65 = 29.2%**;实跑报的 100% 用的是**更松的 z≥2 阈值**(o_old 比 distractor 均值高 2SD)。
> **29.2% < prereg 50% 地板 → 三档规则(<50% W-A 作废 / 50–80% suggestive / ≥80% PASS)判"作废"档。**
> 故本材料下文凡把 G5 写成"100% PASS / 降 suggestive / max-stat 待回传重算"均**过期**;正确=冻结门不过,W-A 承重腿改 **A2 干净 null**(rev≈held 连续 zpre_max,AUC .507,不依赖 G5 阈值)。7/14 内审裁"可靠升起"叙事去留。折 LaTeX 时按此更正。

# Supplementary: Preregistration and Validity Gates

## S.0 Why this section exists

The abstract, \S3.6, and \S6 repeatedly state that our confirmatory tests were *pre-registered*. This section is the verifiable object behind that word. It lists (i) the frozen prediction documents and their commit hashes, (ii) the blind-seed records for the placebo and strong-competitor arms, (iii) the pre-registered primary endpoint of the 14B replication, and (iv) the full G1–G7 validity-gate table with thresholds and observed PASS/FAIL. It closes with the standing policy that any post-freeze change to an endpoint or gate operationalization automatically downgrades the affected result. This table is also what lets us report the W-B representation-level result as a *clean pre-registered negative* rather than a failed experiment: the method cleared its validity gates and its pre-registered primary endpoint still returned null.

## S.1 Frozen preregistration documents (commit-hash pointers)

Each prediction document and its supporting data/code were committed *before* the corresponding results were produced; the prereg record pins the commit hash. (Hashes below verified from the repo git log; re-confirm at camera-ready.)

| Frozen artifact | Scope | Frozen-at commit | Date | What it locks |
|---|---|---|---|---|
| `prereg-esup.md` + `data/placebo_donors.json` | E-SUP-BATTERY: N/T/D/P four-arm battery predictions + placebo donor | `2420cb8` | 2026-06-28 | Signed-ladder predictions and the frequency/length-matched placebo word, before any D/P GPU result |
| `data/placebo_donors_strong.json` + `src/placebo_donor.py` | C arm: strong same-relation competitor control (M4) | `fa1b2fd` | 2026-07-03 | Blind competitor donor list, before the C arm ran |
| `prereg-wseries.md` (+ W-series probe/steer code) | W-A/W-B validity gates G1–G7 and endpoints | frozen 2026-07-08; probe code `c607c92` (7/7); G3s extension `779452d`; G5 post-hoc amendment `94eb60e` (7/8) | 2026-07-07/08 | Gate thresholds, position-exclusion rules, direction-extraction and steering scope |

**Freeze discipline.** The frozen file plus the code that consumes it are committed before the run; the prereg records the commit hash; any post-run endpoint change auto-downgrades the affected result to camera-ready (see \S S.6).

## S.2 Battery predictions and blind-seed records

### S.2.1 N/T/D/P battery (confirmatory) — predictions written before data

Locked in `prereg-esup.md` at commit `2420cb8` (before any D/P result), on 32B / CounterFact / greedy / `scope=think` / |alpha|=8, paired by case. The four arms differ only in the suppression target: **N** (no suppression), **T** (suppress $o_\text{old}$, our fix), **D** (suppress $o_\text{new}$, directional control), **P** (suppress a frequency/length-matched inert placebo word).

**Pre-registered signed ladder** (written before seeing data): reversion metrics RR/CLR: $\mathrm{T}<\mathrm{P}\approx\mathrm{N}<\mathrm{D}$; equivalently ES@$B_3$: $\mathrm{D}\le\mathrm{N}\approx\mathrm{P}<\mathrm{T}$. Pre-registered decision rules: a sign error in D damages the central causal claim (reported, not hidden); a non-null P forces restating the effect as *above-placebo* (T−P); P at the inert floor + T−P excluding zero + D not improving jointly establish specificity, sign, and (with the alpha-sweep) dose.

**Observed** (arm marginals, ES@$B_3$): $\mathrm{D}\ 0.281 < \mathrm{N}\ 0.495 \approx \mathrm{P}\ 0.507 < \mathrm{T}\ 0.631$ — the ladder holds as pre-registered. Confirmatory paired contrasts (by case):
- Placebo inert: P−N RR $0.000$ [$-0.057,+0.057$] ($p{=}1.0$); ES $+0.015$ ($p{=}0.71$).
- Direction-specific: D−N ES $-0.217$ [$-0.289,-0.144$]; RR $+0.086$ [$0.019,0.152$].
- Effect above placebo (headline): T−P RR $-0.095$ [$-0.171,-0.029$] ($p{=}0.010$); CLR $-0.228$ [$-0.294,-0.162$]; ES $+0.122$ [$0.051,0.193$]; RR$_s$ $-0.057$ [$-0.114,-0.010$] ($p{=}0.029$).

Effective $n$: N/T $198$, D $196$, P $199$. The dose axis is the pre-specified alpha-sweep (A2); locality is flat across the entire sweep (Loc $\approx 0.958$ at $\alpha\in\{0,2,4,8,12,16\}$).

### S.2.2 C arm — strong same-relation competitor (blind pre-registered)

The competitor donor list (`data/placebo_donors_strong.json`, e.g. French$\to$Russian type) was committed **blind** at `fa1b2fd` before the C arm ran, to control the sharper objection that suppressing *any* strong competing answer might repair. **Observed:** C is inert like N and P ($\mathrm{C}$ ES $0.510$ / RR $0.208$ vs N ES $0.495$/RR $0.193$ and P ES $0.507$/RR $0.210$). Paired contrasts: C−N behavioral all contain zero (ES $+0.015$, $p{=}0.688$; RR $0.000$, $p{=}1.0$; RR$_s$ $-0.009$, $p{=}0.828$), while T−C excludes zero on all four metrics (ES $+0.121$, $p{=}0.0004$; RR $-0.094$, $p{=}0.006$; RR$_s$ $-0.057$, $p{=}0.032$; CLR $-0.212$, $p{<}0.001$). Note the C arm also rescues the one soft spot of the placebo battery: T−N RR$_s$ contains zero ($-0.051$ [$-0.102,0.0$], $p{=}0.073$), but T−C RR$_s$ excludes it ($p{=}0.032$) — under a competitor floor the strict-reversion contrast is significant.

## S.3 Pre-registered endpoint of the 14B replication (S10)

`s10_14b_fix_replication` header note: the pre-registered primary endpoint is **ES@$B_3$** (the b0ok-RR is *not* the pinned endpoint). Observed 14B T−N paired: ES@$B_3$ $+0.135$ [$0.055,0.215$] ($p{=}0.0006$), mirroring the 32B ES effect ($+0.136$); RR $-0.101$ ($p{=}0.025$) and RR$_s$ $-0.040$ ($p{=}0.035$) also exclude zero.

## S.4 Validity-gate table (G1–G7)

Thresholds are the frozen `prereg-wseries.md` \S1/\S6 definitions; observed values are read only from the W-A main-analysis (`wa_main`) and W-B (`wb_representation_repair`) data blocks. G1–G5 gate the W-A representation probe; G6–G7 gate the W-B steering arm.

| Gate | Checks | Threshold (frozen prereg) | Observed | Status |
|---|---|---|---|---|
| **G1** | Template fidelity: teacher-forced prefix byte-reproduces the stored chain template (full-width bar U+FF5C, WAIT injection, cap truncation) | byte-exact | enforced by a locked transformation unit test (prereg \S0); no per-case failure count surfaced in the analysis block | structural precondition (enforced upstream) |
| **G2** | Re-edit fidelity: post-re-edit $B_0$ greedy reproduces b0ok | $\ge$95% pass, failures excluded+reported; hard disqualifying boundary $<$80% (\S6) | 88% pass, 12/102 excluded | clears the $<$80% hard boundary; 12 failures excluded+reported per protocol |
| **G3** | Replay fidelity: teacher-forced non-forced-position argmax matches the stored chain | per-case $\ge$95% to enter; full distribution reported; $\ge$99% subset sensitivity | median $0.959$; 19/82 cases below the per-case bar (excluded) | median clears $\ge$95%; sub-threshold cases excluded per CONSORT |
| **G4** | Base sensitivity: on the CLR0 (no-string-trace) population, unedited-base teacher-force detects $o_\text{old}$ | $\ge$70% (below $\Rightarrow$ the A1 null is uninterpretable) | 4/29 $=$ 13.8% | **FAIL** $\Rightarrow$ A1 (silent-population) unanswerable |
| **G5** | Premention detection: $o_\text{old}$ detectable in the window before its first mention | $\ge$80% PASS; $<$50% $\Rightarrow$ W-A void; 50–80% $\Rightarrow$ suggestive | 65/65 $=$ 100% under a *fixed $z\ge2$* threshold | **post-hoc operationalization** (see note) $\Rightarrow$ downgraded from gate to suggestive support |
| **G6** | Environment identity (W-B): S / P$_\text{shuf}$ reuse the N/T-arm `_meta` (git hash, dtype, NO_BOS, model path, case set, hparams), diffed item-wise | item-wise match (else re-run N in-environment) | confirmatory arms ran on the reused N environment (N $n{=}198$ shared); no separate numeric readout | structural precondition met |
| **G7** | Direction quality (W-B): pairwise cosine of per-template $o_\text{old}$ concept directions (`pair_cos`) | `pair_cos` $\ge$0.6; exclusion $>$20% $\Rightarrow$ direction method invalid, W-B stops | **Round 1** (single-neutral subtraction): 200/200 fail, `pair_cos` median $\approx0.29$–$0.32$ (max 0.48) $\Rightarrow$ 100% exclusion. **Round 2** (K=8 neutral-mean diff-in-means): 17/200 $=$ 8.5% fail, `pair_cos` median $\approx0.66$–$0.70$ (min 0.535, max 0.78), pre-$W_U$ cos 0.03–0.06 | Round-1 over-boundary $\Rightarrow$ Round-2 **PASS** (8.5% $<$ 20%) |

**Note on G4 (hard failure, reported).** The base-sensitivity gate fails: on the silent (CLR0) population the probe detects the true $o_\text{old}$ in only 4/29 = 13.8% of cases, far below the 70% required for the A1 null to be interpretable. Per the frozen discipline we therefore make **no claim in either direction** about whether committed reversions can occur without any in-chain trace on this population; the silent-leak question is reported as unanswerable, not as evidence of absence.

**Note on G5 (post-hoc operationalization; downgrade disclosed).** The frozen G5 criterion is a distractor max-stat (o_old's band$\times$window max-z must exceed all 20 same-relation distractors, exact $p{=}1/21\approx0.048$). The value that was actually run (`wa_main_analyze.py`, 65/65 = 100%) uses a *fixed $z\ge2$* threshold instead. Git archaeology shows the $z\ge2$ script and the 100% result landed in the same commit `39ca2e9` (2026-07-07 15:37) with no earlier record of a frozen $z\ge2$ criterion, so it cannot be shown to precede unblinding. Following the standing rule that operationalization changes must be pre-registered before unblinding, we do **not** back-certify it: the W-A report reads "G5 operationalized post-hoc (fixed $z\ge2$ variant; the frozen criterion was a distractor max-stat)," and G5 is downgraded from a certified gate to *suggestive support* (\S6 "W-A clean" moves G5 from a hard gate to suggestive). A prereg-correct max-stat recomputation requires the per-distractor base jsonl and is deferred. The remaining W-A legs run on their own frozen operationalizations and are unaffected: the anticipatory-representation endpoint A2 is a clean null (AUC $0.507$, permutation $p{=}0.487$, $n{=}[10,30]$), and the paired edited$-$base estimator A3 is $-0.075$ [$-0.172,+0.016$] (contains zero, $n{=}48$). W-A therefore enters at the *suggestive* tier only.

**Note on G7 (two rounds; hard boundary).** The Round-1 failure was an extraction-method artifact (single-neutral-entity subtraction inflates per-template variance), not evidence that the concept direction does not exist: the same directions under a standard K=8 neutral-mean diff-in-means are stable (`pair_cos` median $\approx0.66$–$0.70$), clearing the $<$20%-exclusion boundary at 8.5%. W-B proceeded only after Round-2 PASS. This is disclosed as a documented two-round gate rather than a silently tuned threshold (0.3 $\to$ 0.6 could not be reached by tuning; the direction extractor was changed, and both rounds are reported).

## S.5 The W-B result is a clean pre-registered negative

W-B (concept-vector suppression as a representation-level repair) cleared its validity gates — G6 environment identity, G7 Round-2 PASS — and its dose pilot selected $\alpha^\*{=}1\%$ as the largest dose within the harm gate (LocAcc drop $\approx0.5$pt from the N baseline $120/192{=}0.625$; 0 degenerate chains), with the larger doses ($\alpha{=}2\%,5\%$) failing the harm gate as pre-specified. On the confirmatory arms (S = suppress the concept direction, P$_\text{shuf}$ = cross-case shuffled direction, both $n{=}144$; N $n{=}198$), the **pre-registered primary endpoint B1** (S$-$P$_\text{shuf}$ reversion-rate CI excludes zero) **FAILED**: S$-$P$_\text{shuf}$ RR $-0.024$ [$-0.098,+0.049$] (contains zero), and S$-$N RR $-0.026$ [$-0.092,+0.040$] (contains zero) — answer-level reversion does not move. Meanwhile the concept-specific chain-verbalization contrast held (S$-$P$_\text{shuf}$ CLR $-0.078$ [$-0.148,-0.008$], excludes zero), and the S$-$P$_\text{shuf}$ locality cost excludes zero (LocAcc $-0.064$ [$-0.119,-0.008$]). (Care: S$-$N ES $+0.092$ [$+0.007,+0.176$] excludes zero, but the confirmatory contrast is B1 = S$-$P$_\text{shuf}$, whose ES $+0.078$ contains zero; the S$-$N ES must not be read as answer-level repair.)

Because the method was validated and its pre-registered primary endpoint returned null, this is a **clean pre-registered negative result**, placed in the appendix as a dissociation: concept-level suppression is real at the chain-verbalization level but does not move the answer, consistent with the repair operating at the token/chain level rather than through a single extractable concept vector. Per the freeze policy there is no third iteration and no mediation/concept-level-repair language enters the main text; a stronger direction extractor is deferred to camera-ready under a new prereg.

## S.6 Standing downgrade policy (one sentence for the supp)

> Any change to a pre-registered endpoint, gate operationalization, or analysis rule made after the corresponding freeze commit automatically downgrades the affected result from confirmatory to camera-ready / suggestive and is disclosed in-line, as we do for the G5 post-hoc operationalization above.

## S.7 One-sentence pointer for \S3.6 (Statistics)

Drop-in sentence for the end of \S3.6:

> The confirmatory tests — the RQ3 N/T/D/P battery and its signed predictions, the blind strong-competitor (C) arm, and the S10 14B replication — were pre-registered before the corresponding results were seen; the frozen prediction documents with their commit hashes, the placebo/competitor blind-seed records, the full G1–G7 validity-gate table (including the G4 base-sensitivity failure, the G5 post-hoc operationalization, and the two-round G7 outcome), and the standing post-freeze downgrade policy are given in Supplementary~S (Preregistration and validity gates).