# Abstract polish decision package: v5 → candidate v6

> Status: **CANDIDATE ONLY**. This package does not replace frozen v5 and does not authorize an OpenReview edit.
> Execution authority: user-supplied `abstract_polish_plan.md`; evidence authority remains `paperwriting/results.json`.

## 1. Codex decision

Advance one candidate to Fable review: apply C-1, C-2(a), and C-3 via the second-panel wording. Reject the optional S7 sentence split. The three accepted edits reduce evidential-role, attachment, and instrument-identity ambiguity without changing any number, estimand, claim, or conclusion. The rejected split would elevate the weakest secondary strict result into a standalone sentence and enlarge the multiplicity/T−N-null attack surface.

Frozen v5 remains the default. Candidate adoption requires Fable to find a clear readability/precision win and the user to approve formal unfreezing.

## 2. Candidate abstract (272 whitespace-delimited words)

Parametric knowledge edits are validated with direct answers; deployed reasoning models may reason before answering. We stress-test edits under a controlled thinking budget: the same ROME edit on CounterFact is scored at zero thinking and after a natural chain, across six fixed checkpoints of two DeepSeek-R1-distill families. At the largest tested checkpoint in each family, paired edit success drops 0.106 [0.030, 0.182] (Qwen-32B) and 0.107 [0.032, 0.182] (Llama-70B). On Qwen-32B, the old answer displaces the new one outright in 9.2% of zero-thinking successes and resurfaces in the final answer in 19.3% of them (strict scorer: Cohen's κ=0.836 vs. a neutral three-judge majority); erosion is edit-specific (no detectable unedited-base drift), content-dependent (a canned thought fails to reproduce it), and persists across three fixed sampling seeds. At Qwen-32B, reverted answers coexist with a still-detectable cloze edit (23/23 examined; an installation sanity check). Separately, a second neutral three-judge panel's majority labels identify a visible in-chain route in all 41 committed reversions (33 unique facts), motivating a chain-routing hypothesis. We next test for a chain-local control point: a signed, dose-graded suppression of the old answer's first tokens (think-span only; answer logits untouched) offsets the observed thinking tax (paired edit-success gain 0.138 [0.082, 0.194]) and lowers loose reversion to 8.5% (paired −0.102 [−0.170, −0.042]), beating a placebo and a same-relation competitor, both near-null at the answer level; the strict endpoint improves against both controls, though not detectably against no suppression. Edit-success gains replicate at 14B and transfer to MEMIT; strict transfer remains inconclusive. Direct-answer edit success is not enough: edit evaluation needs a reasoning-time stress test, and the failure it reveals admits a chain-local causal control point.

Canonical candidate bytes are in `paperwriting/delivery/abstract_v6_candidate.txt` (file SHA256 `743ce122bda82bacae6257423c30081a4f8398ea92fc877d727939de9cbf4bc4`; normalized-text SHA256 `274def5d885722dcff313fb197f62480daa78fbd0750764325e4974276d52700`).

## 3. Three-state table

| ID | Check | State | Decision |
|---|---|---|---|
| A1 | First beat contains CONTEXT | 符合 | S1 establishes direct-answer validation versus reasoning-time deployment. |
| A2 | Adjacent APPROACH→RESULT | 符合 | S2 controlled stress test is immediately followed by S3 paired effects. |
| A3 | Final beat contains IMPLICATION | 符合 | S9 returns to the stress-test identity and bounded causal-control-point claim. |
| A4 | Hedges have local scope | 打磨机会 | C-1 labels 23/23 as an installation sanity check; this lowers, rather than strengthens, its evidential role. |
| A5 | Final-beat hedge matches claim ceiling | 符合 | `needs` and `admits` remain at the frozen ceiling; no tone change. |
| A6 | Headline numbers serve asserted predicates | 有意偏离 | Numeric density is deliberate; every number carries a design, effect, metric, or boundary claim and remains ledgered. |
| A7 | Naming device is justified | 有意偏离 | No method name is introduced: suppression remains a causal probe/control point, not a general method. |
| A8 | Length/density used only as warning | 打磨机会 | Overall length is a deliberate deviation; only S7 attachment ambiguity is repaired. Global compression is rejected. |
| A9 | TL;DR maps to abstract functions/claims | 符合 | Both TL;DR sentences map to existing v5 beats and add no claim. |
| A10 | TL;DR hedge/numbers/naming do not exceed abstract | 符合 | `can`, `at a cloze probe`, and `lowers` stay within v5; TL;DR is byte-untouched. |
| N1 | Do not transfer fixed sentence/beat/order templates | 符合 | No template-driven reordering or sentence-count target. |
| N2 | Do not transfer a headline-number rule | 符合 | No number is added, deleted, replaced, or moved. |
| N3 | Do not transfer a naming rule | 符合 | No acronym or coined name is added. |
| N4 | Do not transfer a global hedge rule | 符合 | Only the already-authorized downward role label in C-1 is added. |

Extra hostile-review opportunity outside the 14 checklist rows: M13 is addressed by C-3, which explicitly marks the route census as a second panel while preserving S4's actual kappa referent, the three-judge majority.

## 4. Sentence mapping

| Candidate sentence | v5 source | Difference type | Exact action |
|---|---|---|---|
| S1 | S1 | 逐字同 | None. |
| S2 | S2 | 逐字同 | None. |
| S3 | S3 | 逐字同 | None. |
| S4 | S4 | 逐字同 | Preserve the strict scorer's actual majority-label referent. |
| S5 | S5 | 加词 | Add `; an installation sanity check` inside the existing parenthesis. |
| S6 | S6 | 加词 | `neutral three-judge majority labels` → `a second neutral three-judge panel's majority labels`. |
| S7 | S7 | 换词 | `competitor with near-null answer-level effects` → `competitor, both near-null at the answer level`; retain the semicolon. |
| S8 | S8 | 逐字同 | None. |
| S9 | S9 | 逐字同 | None. |

Machine proof: changed sentence set is exactly `{S5,S6,S7}`; S1–S4 and S8–S9 are byte-equal after frozen blockquote line wrapping is normalized.

## 5. Four gates

### Gate 1 · Numeric ledger: PASS

- Candidate numeric-token sequence is byte-identical to v5; no number or CI was added, removed, reordered, or reformatted.
- M03 was independently recomputed from `results/p0_corrected_taxonomy.json`: 41 unique item rows cover 33 distinct `items[].case_id` values; source SHA256 is `c11c6a0e…8543290`.
- `paperwriting/results.json` now records `rq2_taxonomy.p0_corrected_taxonomy.n_unique_facts=33`; the title/abstract ledger points to this exact path.
- New C-2 wording is supported only at the answer level: the ES/RR/RRs CIs for both P−N and C−N contain zero. It does not claim equivalence, inertia, or a null chain-level CLR effect.

### Gate 2 · Banned-language scan: PASS

No hits from the WRITING_PLAN §3 list or the added regressions `edit intact`, `not erased`, `guaranteed upper bound`, `removes`, `concentrates`, `stable across`, or `.214`.

### Gate 3 · Non-substantive-change test: PASS

- Same claim set, numeric-token sequence, estimands, comparison arms, and conclusion.
- C-1 is the sole hedge-role addition and moves downward: 23/23 is explicitly labeled an installation sanity check. It is authorized by the paper's own freeze ledger, which outranks the descriptive lens's default no-hedge-edit rule.
- C-2 changes modifier attachment only. C-3 distinguishes two existing instruments only.
- Answer to `qualitatively different?`: **No**.

### Gate 4 · Hostile cold read: PASS, with one deferred issue

- Kimi rejection frame: C-1 makes the observational mechanism evidence less, not more, overclaimed; no natural mediation claim is introduced.
- M13 circularity/instrument confusion: reduced by `a second ... panel`.
- M14 marginal-versus-paired arithmetic: unchanged and not worsened; it still requires the planned complete-case footnote in main-text §5.
- Strict endpoint hierarchy: preserved by rejecting the optional sentence split; the secondary strict result remains subordinate after a semicolon.

Full machine record: `paperwriting/delivery/abstract_polish_audit.json`; reproducible command: `python3 src/check_abstract_polish.py`.

## 6. Forced self-opposition (why v5 may still be better)

1. Candidate grows from 263 to 272 words, moving farther from the descriptive corpus median.
2. C-1 adds technical jargon to an already dense mechanism transition.
3. C-3 is more precise but syntactically heavier than the v5 census sentence.
4. C-2 creates a nearby `both ... both controls` repetition.
5. None of the edits changes the core story; the gain is measurement clarity, not memorability.
6. M14 remains unresolved in the abstract by design.
7. Therefore, if Fable's blind cold read does not immediately distinguish the two instruments or find the attachment clearer, **retain v5**.

## 7. Handoff request to Fable

Please independently cold-read v5 versus candidate v6, then spot-check Gate 1 and Gate 3. Apply the no-regression rule: ambiguity counts as a loss, and an unclear win means retain v5. Do not edit the candidate in place; return a verdict and any proposed change as a new reviewed delta.
