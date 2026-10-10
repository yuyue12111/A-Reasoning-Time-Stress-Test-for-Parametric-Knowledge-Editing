# Narrative brief: the evidence, its status, and the constraints (2026-10-10)

This is the single source the narrative work starts from. Every number below comes from these files:
- `paperwriting/revision/study1.md`
- `paperwriting/revision/study2.md`
- `paperwriting/revision/explore_s1s2.md`

## The project in one paragraph

We study parametric knowledge editing in reasoning models.
- **Setup.** Rank-one ROME edits on CounterFact facts, for example the mother tongue of Danielle Darrieux:
  French → English. The models are DeepSeek-R1 distills: Qwen 1.5B/7B/14B/32B and Llama 8B/70B.
- **Comparison.** Each edit is evaluated twice. Once the model answers directly with zero thinking (B0); once it
  thinks first with a native chain (B3, up to 8192 thinking tokens).
- **Rule.** Each request sees only its own edit.

## Previous submission (AAAI-27, rejected; scores 6 and 3, plus an AI review)

- **Title.** "When Edits Pass but Answers Revert: A Reasoning-Time Stress Test for Parametric Knowledge Editing".
- **Text.** The old abstract and the full text are in `/Users/whyu/GitProjects/why-aaai27/paperwriting/manuscript/main.tex`.
- **Reviews.** Full text in `/Users/whyu/GitProjects/why-aaai27/official-review.md`.

| reviewer | what they said |
|---|---|
| TRfT, score 3 | Unreadable, "typical of zero-shot AI writing"; unclear motivation; unconventional organisation; design decisions unjustified; figure text too small; the ethics statement is not one. |
| mTGu, score 6 | Only 2 of 6 checkpoints are significant, with no multiplicity correction. The pool was selected by the 7B old-answer retrieval at B3, so the result may not generalise. The intervention shows steerability, not mediation. Wants evidence across editors and less selected populations. |
| AI review | Reversion is undefined unless each model knew the fact (per-checkpoint qualification). The permissive reversion metric has precision .48. There is no formal edited-versus-base contrast. MQuAKE and Ju et al. 2024 are missing. Single editor, single dataset. |

**Diagnosis we agree with.** The old paper was defensive to the point of having no story. The abstract had 7 numbers
and 4 self-limiting clauses, and no sentence on why anyone should care. It tried to tell three things at once
(phenomenon, routes, intervention).

## Evidence now

| status | finding |
|---|---|
| **Study 1, re-analysed (registered-style re-analysis of AAAI data)** | ES drop (direct − reasoned): Qwen-32B .106, Llama-70B .107. Both survive Holm over 6 checkpoints (.033, .022). The other 4 checkpoints are ≈ 0. |
| Study 1 | **Retention contrast** (edited answer lost − native answer lost, among facts the base knows and the edit holds at B0): 14B +.195, 32B +.216, 70B +.234, all with CI excluding 0. Edited answers are lost about twice as often as the model's own answers. |
| Study 1 | Name leakage: 46 of 200 subjects contain the old value (e.g. "Suzuki GSX-R" → Suzuki). It contaminated the permissive reversion metric, which is dropped. |
| Study 1 | Engine verified: the new engine reproduces Study 1 byte-for-byte in fp32. |
| **Study 2 (pre-registered, frozen 2026-10-08 with a GitHub timestamp; fresh pool of 400 facts selected by the 32B's own knowledge at B0, no reasoning-based selection)** | Only the 32B finished before the compute window closed. **H1 ES drop .037 [−.010, .087], p=.14 ✗. H2 retention contrast +.029 [−.036, .097], p=.43 ✗.** 70B, 14B, small models, the arms and the editors were not run (edits exist for 70B and 14B). |
| Study 2 | Reasoning re-decides edits both ways. Erosion (holds directly, lost after reasoning) .14; repair (fails directly, holds after reasoning) .105. |
| **Exploratory, post hoc (chosen after other explanations failed)** | Hardware, the qualification rule, the base model's own recall of the fact in its chain, relation mix and edit strength do **not** explain the Study 1 → Study 2 shrinkage. |
| Exploratory, post hoc | **Fact salience explains it.** Salience = how many of the four small distills (1.5B, 7B, 14B, Llama-8B) know the fact. In Study 2 32B, salient facts (3–4 of 4, n=156) show ES drop **.115** [.032, .199] and retention contrast **+.242**; the rest (n=244) show −.012 and −.090. Difference +.332, p<.001. Dose-response over 0..4: retention −.26, −.10, −.01, +.24, +.25. Edited loss rises .13 → .31 while native loss falls .39 → .06. |
| Exploratory, post hoc | The same split on the independent Study 1 cases: salient facts give retention +.28 to +.32 at 14B, 32B and 70B (CIs exclude 0); the others give +.03 to +.13 (CIs include 0). Study 1's pool is 59% salient, Study 2's 39%. |
| **Pending (prospective test, pre-registered before any data: `prereg-arr-addendum-salience.md`)** | H4: retention contrast is larger for salient facts. To be tested on 70B and on a fresh 32B pool of 309 facts (14B secondary), none generated yet. About 4–5 H100 hours. Outcome unknown. |
| Older, from AAAI | Think-span intervention at 32B: suppressing old-answer tokens only inside the chain raises edit success and lowers reversion; the reverse-signed arm does the opposite. A BOS confound was found in some arm comparisons. Clean contrasts: T−N ES +.138, D−P ES −.225. |

## Hard constraints for any narrative

1. **Honesty.** Never state the salience result as confirmed. It is post hoc until H4 is tested. Write the result
   sentence of the abstract in **two variants**, "H4 confirmed" and "H4 not confirmed", both fixed before the data.
   Never pre-write a positive result as if it had happened.
2. **The registered failure stays visible.** Study 2's failed H1/H2 must appear in the main text. The story should use it as the turn, not
   hide it.
3. **Story and readability first** (the user's top priority).
   - One thesis sentence a reader can repeat.
   - Confident claims where the evidence is strong; all limitations gathered in one Limitations section, with no hedging in every sentence.
   - At most 3 technical terms in the main text.
   - Engineering process (engine checks, BOS, gates, hashes, deviation logs) goes to the appendix.
   - One hero figure.
4. **Venue.** ARR long paper (ACL template): 8 pages of main text; references, limitations and appendix are extra.
   The reviewers are NLP/ML people who know knowledge editing and reasoning models.
5. **Related work** the story must sit against: MQuAKE (Zhong et al. 2023), Ju et al. 2024 (multi-hop shortcuts),
   ThinkEval, He et al. 2025, CODE 2026, Gao et al. 2026, CRANE, and Superficial Editing.
   Notes are in `/Users/whyu/GitProjects/why-aaai27/paperwriting/related_work.md`.
