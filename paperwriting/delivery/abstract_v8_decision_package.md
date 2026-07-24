# Abstract v8.1 finalization record

## Final status

**INTERNAL FINAL / FROZEN.** Canonical file SHA256: `0c85a03e9cd288b45d6f23502caf17b74e84c28dee0f3a2e62f9202ec4b81e5f`.

The user approved finalization. No further abstract edits are allowed before the manuscript is written and audited. The external OpenReview field remains v5 until debts D1–D8/R1 are present in §3–§5; G5 therefore blocks external synchronization, not internal text freeze.

## Final abstract (188 words; 8 sentences)

> An edit can pass direct-answer validation yet lose control of the final answer when the model reasons. We evaluate each ROME edit on CounterFact twice—at zero thinking and after a natural chain—across six fixed checkpoints from two DeepSeek-R1-distill families. At the largest tested checkpoint in each family, edit success drops by 0.106 on Qwen-32B and 0.107 on Llama-70B. Among zero-thinking successes on Qwen-32B, old answers resurface in 19.3% of reasoned final answers and displace new answers outright in 9.2%, while the unedited base shows no detectable old-answer drift. Yet in the Qwen-32B reversions we examined, the edited association remains detectable at a cloze probe; separately, route analysis finds visible in-chain paths to old answers, motivating a chain-routing hypothesis. We next test for a chain-local control point by suppressing old-answer first tokens only during Qwen-32B reasoning, leaving answer logits untouched. The signed, dose-graded intervention offsets the edit-success loss and lowers the resurfacing rate from 19.3% to 8.5%; placebo and same-relation controls have near-null answer-level effects. Direct-answer edit success is not enough: edit evaluation needs a reasoning-time stress test, and the failure it reveals admits a chain-local causal control point.

## Review adjudication

Accepted:

- Preserve the S1 hook and the `each ... twice` plain-language paired design.
- Add `Yet` at the cloze/route hinge while preserving the semicolon plus `separately` crosswalk firewall.
- Split intervention design from causal calibration.
- Remove the undefined abstract jargon `marginal loose reversion`.
- Remove paired `−0.102` from the abstract. Juxtaposing it with arm-wise `19.3%→8.5%` forces an estimand explanation at the story climax; D5 retains the paired estimate, CI, and denominator explanation for §5.
- Report the control result, not merely control existence: P−N and C−N ES/RR/RRs have near-zero point estimates and CIs including zero. Keep `answer-level`, because C−N CLR is nonzero.
- Restore `edit evaluation` in the conclusion.
- Remove redundant `paired` from S3 after 3/4 developmental final-byte readers identified it as the same undefined term; S2 already establishes the within-edit comparison.

Rejected:

- `when→once`: `once` can suggest a deterministic transition whenever reasoning begins.
- `At each family's largest checkpoint`: dropping `tested` weakens the fixed-checkpoint scope guard.
- `no corresponding drift`: dropping `detectable` converts a null-compatible result into an absence claim.
- The proposed transfer sentence: it reopens the result-inventory cadence and requires the MEMIT strict-null/fresh-N boundary to travel with it. R1 keeps the complete transfer story in §5.
- The full 198-word rewrite: several local improvements were retained, but its combined form regressed evidence wording and restored a fourth results beat.

## Gate record

- **G1 numeric: PASS.** Six result-number occurrences: `0.106`, `0.107`, `19.3%`, `9.2%`, `19.3%`, `8.5%`; no CI, κ, sample count, or paired `−0.102`.
- **G2 language/form: PASS.** 188 words, 8 sentences, maximum 30 whitespace-delimited words, banned phrases zero, numbers confined to S3/S4/S7.
- **G3 substance: PASS.** Final-hash science audit found no blocker. The control clause was separately verified against P−N and C−N answer-level endpoints.
- **G4 hostile read: PASS with recorded minor scope risk.** The route statement remains a hypothesis; no natural-mediation claim is made. The manuscript must place X1 `9/18 FAIL` beside the routing hypothesis.
- **G5 disposition: PASS; external adoption: BLOCKED.** D1–D8/R1 remain open until the manuscript houses uncertainty, measurement, X1, strict endpoints, robustness, and transfer boundaries.
- **G6.2: PASS.** Final v8.1 clarity `[4,4,4,5]` versus v6 `[4,4,4,4]`; zero low-clarity and zero major-overread responses in both. The repeated v8.1 stumble was `natural chain`, already present in all four v6 reads, so it is not a new regression. User judgment authorizes internal freeze.

## Positive-writing provenance

The abstract was written from the mental model—certification gap → paired stress test → old-answer return → bounded routing hypothesis → chain-span causal test → evaluation implication—not by shortening v5/v6. Corpus-mining artifacts were used afterward only to audit function, length, density, and sentence load. Omitted evidence is tracked in `abstract_v8_substance_ledger.json`; absence from the abstract is not discharge.

## Artifacts

- `abstract_v8_candidate.txt`: canonical final text.
- `abstract_v8_machine_audit.json`: final machine gate record.
- `abstract_v8_semantic_audit.json`: science/statistics/causal/control audits.
- `abstract_v8_g62_protocol.json`, `abstract_v8_g62_raw.json`, `abstract_v8_g62_audit.json`: blind regression guard.
- `abstract_v8_substance_ledger.json`: D1–D8/R1 manuscript obligations.

## Reopen rule

Do not edit for taste, word count, or another abstract-only review. Reopen only after the manuscript is complete and only if a debt cannot be housed, abstract and body materially disagree, or the external submission policy requires a change. Any reopen invalidates the hash and reruns the affected gates.
