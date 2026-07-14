# P0 · taxonomy membership re-audit · frozen preregistration

- Frozen: 2026-07-12, before any new membership vote is generated or inspected.
- Authority: `plan.md` v1.81.
- Motivation: `chain_classify.py` asks route judges to assume the final answer reached OLD and offers no `neither` route. Its `in_population` output therefore cannot independently establish final-answer OLD commitment.

## Population and unit

Audit all 101 existing route-judge candidate chain instances, not only the current 50 in-pop rows:

- 33 rows from `results/a3_neutral/verdicts_all.jsonl`;
- 68 rows from `results/b16_verdicts.json`.

The unit is `(pool, cell, case_id)`. Repeated case IDs in different cells are distinct generated chains. Source answer, `o_old`, `o_new`, source path/line, and hashes are frozen by `src/p0_membership.py emit` before judging.

## Membership judges

Three independent judges see only `o_old`, `o_new`, and the final answer. They do not see CoT, existing route label/votes, model scale, pool, current inclusion, X1 result, or other votes. The prompt is the answer-only OLD/NEW/NEITHER protocol from `src/revert_judge.py`.

- majority OLD → member;
- majority NEW or NEITHER → non-member;
- 1-1-1 → non-member with split flag;
- fewer than two valid votes → one outcome-blind retry; still insufficient rows remain unresolved and cannot enter the committed-OLD denominator.

No lexical rule may override judge membership.

## Route reuse and rescue

- Current in-pop + new OLD: reuse pre-existing route votes because the route prompt's OLD premise is now independently verified.
- Current in-pop + new non-OLD: drop from taxonomy.
- Current excluded + new OLD: emit a fresh neutral route prompt and obtain three route votes; old `Excluded-held` votes are not route labels and cannot be reused.
- Current excluded + new non-OLD: remain excluded.

Recompute per-cell and pooled denominators, route counts/percentages, Fleiss kappa, and raw agreement only after rescued rows have route votes. Report a CONSORT-style current→drop/rescue→corrected table. Do not preserve 50 or any route percentage as a target.

## Downstream audit

Crosswalk corrected membership to X1 source rows, the 19-row observational necessity table, the 23-row logit-lens selection, and W-A rev/held group labels. The official preregistered X1 9/18 gate never changes; any corrected X1 denominator is explicitly post-hoc diagnostic.
