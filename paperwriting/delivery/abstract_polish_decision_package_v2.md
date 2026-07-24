# Abstract v7 decision package: mental-model rewrite

> Status: **CANDIDATE ONLY — DO NOT ADOPT**. Frozen v5, Title, TL;DR, and the OpenReview form remain unchanged.
> Machine checks G1–G2 pass; judgment gates G3–G4 pass for candidacy. The G5 disposition table passes but adoption is blocked by open manuscript debts; G6 is **not passed because a clear win was not established**.
> Authority: user-supplied v7 execution plan; evidence authority remains `paperwriting/results.json`.

## 1. Codex decision

The 197-word v7 candidate is a materially cleaner abstract, but it is **not eligible to replace the frozen abstract under the plan's own gates**.

- It satisfies the structural, numeric, banned-language, and non-substantive-change checks.
- It is not a qualitatively different submission: the research identity and headline claim vector are unchanged, the number set only shrinks, and retained predicates are not strengthened.
- The G5 table is complete, but adoption is blocked because the manuscript destinations for seven removed safeguards plus the retained MEMIT boundary do not yet exist.
- G6 is not passed. Cold readers consistently remember `direct success → reasoning failure → think-span intervention`, but bounded-cloze preservation is scorer-sensitive (literal A3: 0/4–1/4; conservative no-overread composite: 0/4), and balanced clarity does not clearly beat both baselines.

Therefore: send v7 to Fable as a reviewed **candidate**, but retain the fallback chain `v6 candidate → frozen v5`. Do not unfreeze or edit OpenReview.

## 2. Candidate v7

> Among examined reversions, zero-thinking edit success gives way after a natural chain, yet the edited association remains detectable at a cloze probe: direct validation is not a reasoning-time stress test. We compare the same ROME edit on CounterFact across these budgets at six fixed checkpoints from two DeepSeek-R1-distill families. At the largest tested checkpoint in each family, paired edit success drops 0.106 on Qwen-32B and 0.107 on Llama-70B. On Qwen-32B, the old answer displaces the new one outright in 9.2% of zero-thinking successes and resurfaces in 19.3% of them. On Qwen-32B, erosion is edit-specific (no detectable unedited-base drift), not reproduced by a canned thought, and persists across three fixed sampling seeds. Separately, judges identify visible in-chain routes, motivating a chain-routing hypothesis. We next test for a chain-local control point: signed, dose-graded suppression of the old answer's first tokens only during thinking, with answer logits untouched. This offsets the observed thinking tax: marginal loose reversion drops 19.3%→8.5% (complete-case paired change −0.102); edit-success gains replicate at 14B and transfer to MEMIT; strict transfer remains inconclusive. Direct-answer edit success is not enough: edit evaluation needs a reasoning-time stress test, and the failure it reveals admits a chain-local causal control point.

Canonical bytes: `paperwriting/delivery/abstract_v7_candidate.txt`.

- 197 whitespace-delimited words
- 9 sentences
- sentence lengths: `30/19/19/21/22/10/24/28/24`
- 7 result-number occurrences: `0.106, 0.107, 9.2%, 19.3%, 19.3%, 8.5%, −0.102`
- file SHA256: `6a39175ec4b40976f0c680e3dea3c1796fe01d2455be2c731da0806a02431a71`
- normalized-text SHA256: `761d565073ba1cfc3ed7ffa20e00e7b2bb03b6b8700d239f1d3f3377c0dcec69`

The 6–8-token budget is interpreted as **result quantities**, not model identifiers (`32B/70B/14B`) or design counts. Counting all digit-bearing strings would make the plan's required three beats internally impossible.

## 3. Sentence mapping

| v7 | v5/v6 source | Type | Preserved role / moved material |
|---|---|---|---|
| S1 | S1 + S5 + S9 | 合并、压缩 | Installs direct-validation insufficiency, bounded cloze detectability, and reasoning-time failure; the 23/23 credential moves to D3. |
| S2 | S2 | 压缩 | Same-edit, zero-versus-chain, CounterFact, six-checkpoint/two-family design. |
| S3 | S3 | 压缩 | Keeps the two symmetric point estimates; CIs move to D1. |
| S4 | S4 | 压缩 | Keeps the strict/permissive severity beat and its Qwen-32B denominator; κ moves to D2. |
| S5 | S4 | 压缩 | Preserves the Qwen-32B scope, null-compatible base-drift result, canned-thought control, and fixed-seed persistence. |
| S6 | S6 | 压缩 | Keeps observational routes only as motivation for a hypothesis; census size/panel details move to D4. |
| S7 | S7 | 压缩 | Keeps signed, dose-graded, think-only old-token intervention with answer logits untouched. |
| S8 | S7 + S8 | 合并、压缩 | Keeps marginal and complete-case paired loose-RR estimands plus bounded transfer; ES gain, controls, and strict ROME bracket move to D5–D7. |
| S9 | S9 | 保留 | Byte-identical title callback and causal-control-point implication. |

### Bidirectional predicate ledger

Retained headline predicates:

1. Direct-answer validation is insufficient for reasoning-time deployment.
2. The same ROME edit is compared at zero thinking and after a natural chain across six fixed checkpoints/two shared-recipe backbone families.
3. The two largest tested checkpoints show matched ES drops.
4. Qwen-32B has strict old-only displacement and permissive old-answer resurfacing.
5. The erosion is edit-specific, not reproduced by the tested canned thought, and persists across three fixed sampling seeds.
6. In examined reversions, the edited association remains detectable at a cloze probe.
7. Separately observed routes motivate—but do not prove—a routing hypothesis.
8. A signed, dose-graded, think-span-only old-token intervention leaves answer logits untouched.
9. The intervention offsets the observed tax on the primary loose endpoint; marginal and paired estimands are distinguished.
10. ES gains replicate at 14B and transfer to MEMIT; strict transfer remains inconclusive.
11. Evaluation needs a reasoning-time stress test; the failure admits a bounded chain-local causal control point.

Removed predicates/credentials are not silently discarded: they map one-to-one to D1–D7 below. Thus the correct G3 statement is **predicate subset with the same research identity**, not literal claim-set equality.

## 4. G1–G4 records

### G1 · Numeric ledger: PASS

| Display | Exact source |
|---|---|
| `0.106` at Qwen-32B | `capability.families.R1-Distill-Qwen.params_b[3]=32`; `.es_drop[3]=0.106` |
| `0.107` at Llama-70B | `capability.families.R1-Distill-Llama.params_b[1]=70`; `.es_drop[1]=0.107` |
| `9.2%` strict | `rq3.sup_battery.marginal_B3.N.RRs=0.092` |
| `19.3%` permissive baseline | `rq3.sup_battery.marginal_B3.N.RR=0.193` |
| `8.5%` permissive intervention | `rq3.sup_battery.marginal_B3.T.RR=0.085` |
| paired `−0.102` | `rq3.sup_battery.cross_arm_paired_ci.T_minus_N.RR[0]=−0.1017` |
| `no detectable unedited-base drift` | `base_probe.f1_edit_specificity.paired_ci.ci95=[−0.0804,0.0402]` contains zero |

The paired-versus-marginal special check passes: the sentence explicitly labels `19.3%→8.5%` marginal and `−0.102` complete-case paired; it does not equate the two arithmetic contrasts.

### G2 · Banned-language and frozen-field scan: PASS

- No hits from the full historical regression list.
- Required ceiling phrases are present, including `offsets`, `motivating a chain-routing hypothesis`, fixed-checkpoint/fixed-seed scopes, and cloze-probe-only wording.
- Title, TL;DR, and frozen v5 are extracted and checked against exact frozen strings/hashes, not merely searched as substrings.

### G3 · Non-substantive modification: PASS, with corrected rationale

Answer to `qualitatively different?`: **No**.

The research identity, headline causal/evaluation vector, models, method, dataset, and conclusion do not change. Numbers and predicates are deleted, not added. The accurate defense is not “identical claim set”; it is “same headline claim vector, documented predicate subset, no retained predicate broadened.”

### G4 · Hostile cold read: PASS for candidacy, not adoption

- “You hid adverse numbers”: currently live as a valid attack because the destinations are unwritten; G5 blocks adoption until they are visible.
- “Cloze detectability proves the edit intact”: the candidate says only `edited association remains detectable at a cloze probe` and scopes it to examined reversions.
- “Routes prove natural mediation”: `Separately` and `motivating ... hypothesis` keep the literal text below that claim, although G6 shows they do not reliably prevent reader overinterpretation; X1 still requires the adjacent main-text firewall.
- “The causal control point is contradicted by strict T−N”: not logically so—the causal claim comes from the signed, dose-graded, old-token-specific chain intervention and its controls—but the secondary strict bracket must be reported under D7.

## 5. G5 disposition table and manuscript debts

| ID | Removed/retained item | Original placement rationale | Why absence does not itself overclaim | Required frozen destination before adoption | Status |
|---|---|---|---|---|---|
| D1 | Two phenomenon CIs | Prevent point-estimate cherry-picking and carry uncertainty for the two headline cells. | v7 reports point estimates and fixed checkpoint scope, not a new significance/generalization claim. | §3 evaluation-gap subsection + six-cell Table 1: all cells, CIs, fixed-checkpoint scope, no monotonicity claim. Do **not** copy the review's Holm sentence unless a results path or independent recomputation is ledgered. | OPEN |
| D2 | `κ=.836`, n/panel attribution | Supply measurement-validity credit for the strict lexical scorer. | Omitting a credential does not claim unvalidated scoring. | §3 metric-validation panel: n=87/120, 33 rate-limited, same-family/shared-bias caveat; do not call κ a lower bound or loose RR a guaranteed upper bound. | OPEN |
| D3 | `23/23` + installation-sanity label | Bound the cloze observation and pre-empt the vacuity/intact-edit overread. | The surviving sentence is qualitative and scoped to examined reversions; it does not say intact/not erased. | §4 diagnosis: Qwen-32B, selected reverted cases, cloze first-token probe, no control/near-tautological installation check, missing per-item crosswalk disclosed. | OPEN |
| D4 | `41/33`, second panel, majority/census details | Distinguish the route-census instrument and disclose its population/denominator. | v7 uses no universal quantifier or rate; it only says judges saw routes that motivate a hypothesis. | §4 taxonomy subsection (M07/M13): frozen 101-candidate pool spanning six checkpoints, two backbone lineages, and three decoding regimes; membership 41/43/17; 41 instances/33 facts; 27/11/3/0 routes; agreement and distinct panel name; X1 9/18 firewall adjacent. | OPEN |
| D5 | ES gain `+0.138 [0.082,0.194]` | Keep the repair claim on a paired estimand rather than a marginal arrow. | `offsets the observed thinking tax` stays bounded; B3 still carries the paired loose-RR effect. | §5 headline table: paired ES gain beside marginal levels; M14 complete-case note. | OPEN |
| D6 | Placebo/competitor answer-level near-null qualifier | Show old-token specificity without calling the controls equivalent or inert. | v7 makes no control-activity claim. | §5 calibration paragraph: answer-level P−N/C−N null-compatible, not equivalent/inert; C−N CLR is not null. | OPEN |
| D7 | ROME strict double-control bracket | Prevent the primary loose result from hiding the secondary strict endpoint pattern. | v7 makes no strict ROME repair claim. | §5 endpoint hierarchy: primary ES/loose RR; secondary unadjusted T−P and T−C strict results; T−N strict `p=.073` equally visible; multiplicity language bounded. | OPEN |
| R1 | `strict transfer remains inconclusive` retained | Preserve the adverse MEMIT transfer boundary in the abstract itself. | The adverse boundary remains in v7. | §5 transfer row: MEMIT T−C strict RRs null and fresh-N erosion null-compatible, next to positive ES transfer. | OPEN |

Disposition-table completeness: **PASS**. Adoption readiness: **BLOCKED** because D1–D7/R1 are still open. Section numbers follow the current WRITING_PLAN dependency (`§3 evaluation → §4 diagnosis → §5 intervention`), not stale review numbering.

## 6. G6 mental-model test: NOT PASSED — clear win not established

### Protocol hygiene

The first pilot exposed the five atoms before retelling and was discarded: it produced an artificial 5/5 ceiling. The final protocol used the same rubric-hidden prompt template for each version: read once, do not reread, give a ≤30-word mental-model retelling, then separately report implication/overclaim/clarity. LLM compliance with “read once” cannot be directly enforced.

The final audit separated stages:

1. single-version reader, abstract shown once, no target rubric, ≤30-word retelling;
2. independent scorers saw only the retellings and applied an operational five-atom/calibration rubric as a sensitivity analysis.

Final reader allocation is balanced at four per version. Clarity scores are v7=`4/4/4/4`, v5=`4/4/3/4`, and v6=`4/4/4/4`; v7 therefore does not clearly beat v6.

The four v7 retellings were:

1. “Reasoning chains can reactivate old knowledge and erode parameter edits; suppressing old-answer tokens during thought partially restores edited behavior, exposing a chain-local causal control point.”
2. “Reasoning chains can undo successful knowledge edits while leaving edited facts detectable; suppressing old-answer tokens during thought partly restores robustness across models and editing methods.”
3. “A knowledge edit that survives direct recall can be undone during reasoning when the old fact re-enters the chain; suppressing it inside thought partly restores robustness.”
4. “Across two R1-distill families, ROME edits weaken during natural reasoning despite cloze retention; chain-local old-answer suppression causally recovers success, with partial replication across scale and MEMIT.”

For reproducibility, the four v5 retellings were:

1. “Direct-answer success overstates edit robustness: reasoning erodes ROME edits, while suppressing old-answer tokens during thought recovers performance, suggesting chain-local routing causes reversions.”
2. “Knowledge edits that succeed in direct answers can unravel during reasoning; suppressing the old answer within the thought chain partially restores edited behavior.”
3. “Edits that work in direct answers can erode after reasoning; chain-local suppression restores much performance, so evaluations must stress-test inference-time thinking.”
4. “Reasoning erodes ROME edits in large R1-distilled models; old answers resurface via chain routing, while think-span token suppression partially restores edit success without changing answer logits.”

The four v6 retellings were:

1. “Edited facts survive direct probes, but reasoning revives old answers; thought-only token suppression mitigates erosion, so edit evaluation must include reasoning-budget stress tests.”
2. “Reasoning can undo apparently successful knowledge edits by routing back to old answers; suppressing old-answer tokens during thought partly restores edits without directly changing answer logits.”
3. “Reasoning can route around an installed fact edit, reviving the old answer; suppressing old-answer tokens only during the chain recovers much of the lost success.”
4. “Knowledge edits that work in direct answers can erode during reasoning; suppressing old-answer tokens only within the thought chain partially restores edited behavior, suggesting chain-local interference.”

Under the corrected A4 definition (retain chain-local intervention/control-point content; score epistemic conflation separately), scorer 1 assigned v7/v5/v6 `[1,4,0,4,0]` / `[3,4,0,4,1]` / `[2,4,0,4,1]`. Scorer 2 assigned v7 `[1,4,1,4,0]` and the same v5/v6 totals; its lone v7 A3 came from “cloze retention” and simultaneously triggered the intactness-overread flag, so it is not a faithful bounded-cloze hit. These totals do not establish a v7 win.

Important calibration: neither an all-five/all-or-none threshold nor any exact atom aggregation was pre-specified by the user. All four v7 retellings retain a manipulable chain-local intervention; observational-versus-interventional conflation is therefore treated as a calibration warning rather than erasing that content. Literal A3 is scorer-sensitive (`0/4` versus `1/4`); under the conservative rule requiring A3 without an intactness-overread flag, the bounded-cloze composite is `0/4`. This still does not rescue G6: clarity ties v6, and the complete target model is not reliably retained.

The reader prompt requested the retelling and main implication in separate fields, which can displace the stress-test conclusion (A5) into the second field. Indeed, all four v7 implication fields retain A5 while its retelling-only total is `0/4`; A5 retelling counts therefore do not carry the decision. The verdict instead rests on the clarity tie with v6 and the bounded-cloze gap, so this prompt sensitivity does not change it.

A developmental side-by-side test favored an earlier 194-word v7 variant 5/5 for readability, but it is excluded from the final gate because (i) it tested a different byte string and (ii) relative preference cannot establish bounded-model retention for the final candidate.

**G6 verdict: NOT PASSED.** The plan's `unclear win → fallback` rule applies. This is failure to establish a clear win, not evidence that v7 is worse.

## 7. Forced self-opposition

1. v7 is easier to read mainly because it removes evidence; until D1–D7 exist, that can look like concealment rather than elegance.
2. Its first sentence is memorable but begins on a selected set (`examined reversions`), not the population-level phenomenon.
3. The 28-word S8 still compresses a marginal level, paired estimand, replication, transfer, and null boundary.
4. Blind readers repeatedly paraphrase cloze detectability as the edit/fact “surviving,” demonstrating the exact overread the paper forbids.
5. Blind readers repeatedly paraphrase visible routes as the mechanism, despite `motivating a ... hypothesis`.
6. “Causal control point” remains the most attackable remembered phrase because readers conflate the secondary strict T−N null with the broader signed-control battery.
7. Therefore, absent an explicit relaxation of G6 by the user, v7 cannot be adopted merely because it is 66–75 words shorter.

## 8. Handoff request to Fable

Please review three questions independently:

1. Do you agree that G6 is not passed because a clear win is unestablished, or can you justify a different decision rule without post-hoc use of the developmental comparative test?
2. Does S1's selected-set opening improve the mental model enough to outweigh placing population-level evidence second?
3. Are D1–D7/R1 correctly assigned to §3/§4/§5, especially the refusal to inherit the unledgered Holm claim?

No in-place edits: return a verdict and any proposed delta. Under the current plan, `unclear win = fallback`; Title/TL;DR remain locked in every branch.

Records: machine-derived `paperwriting/delivery/abstract_v7_machine_audit.json`; manually compiled gate decision `paperwriting/delivery/abstract_v7_audit.json`; raw G6 record `paperwriting/delivery/abstract_v7_g6_raw.json`; recomputed G6 aggregate `paperwriting/delivery/abstract_v7_g6_audit.json`. Reproduce with:

```bash
python3 src/check_abstract_v7.py
python3 src/check_abstract_v7_g6.py
```
