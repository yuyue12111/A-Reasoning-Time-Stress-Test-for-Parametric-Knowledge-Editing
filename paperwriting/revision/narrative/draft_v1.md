# Draft v1: title, abstract, introduction page 1, Figure 1 (2026-10-12)

Status: first draft for the ARR rewrite (story first; see `brief.md` and `panel_2026-10-10.md`). Every
number is traced in the last section. Figure: `fig/hero_sketch.{png,pdf}`; its data are in `fig/hero_data.json`.

## Title

1. **Reasoning Models Undo Edits to the Facts They Know Best** (preferred; requires the pending test not to fail)
2. Thinking Keeps What a Model Knows, Not What It Was Edited to Know
3. Which Knowledge Edits Survive Thinking? (neutral; used if the pending test fails)

## Abstract

(1) Knowledge edits are checked by asking the edited question directly, but reasoning models answer only
after they think, and thinking can bring an overwritten fact back. (2) In an exploratory study of six
DeepSeek-R1 distills, ROME edits that passed the direct check were lost after thinking two to three times
as often as the models' own answers at the three largest sizes. (3) A pre-registered replication on 400
fresh facts at Qwen-32B found almost none of this excess (+2.9 points, 95% CI −3.6 to 9.7). (4) Analyses
run after this failure reconcile the two studies: on facts that smaller models also know, thinking changed
the model's own answer only 6–9% of the time but lost about a third of the edits in both studies, whereas
on less familiar facts the model's own answers were fragile too and the excess shrank or reversed.
(5) Reasoning undoes edits to well-known facts, and averages over mixed fact sets can hide or inflate it;
evaluations should report such facts separately, against the model's own answers, on facts fixed in advance.

**Pre-written variants for the second pre-registered test.** The test uses 309 new Qwen-32B facts; both
variants are fixed before any of its data exist.
- *Confirmed.* Sentence (4) gains a final clause: "and a second pre-registered test on 309 new facts
  confirmed it ([edited] against [own])". Use title 1.
- *Not confirmed.* Sentence (5) becomes: "The pattern did not hold on 309 new facts, so reasoning-time edit
  loss is a property of the fact set, and evaluations should …". Use title 3.
- *Not run.* Keep the text as written above.

## Introduction (page 1)

Knowledge editing changes a single fact inside a language model without retraining it (Meng et al., 2022).
We used ROME to tell DeepSeek-R1-Distill-Qwen-32B that the capital of the Kingdom of Bohemia is Santiago.
Asked directly, the edited model complies: "Santiago de Chile." Asked again with its thinking on, it
reasons its way back. The edit surfaces in its chain as a stray memory: "I also recall that Chile has a
region called the Kingdom of Bohemia… a small area in Santiago." The chain then sets that memory aside:
"The capital of Bohemia itself was Prague." The model answers Prague, as the unedited model does whether
or not it thinks. The edit was not erased; the model reasoned around it (Figure 1a).

This matters because reasoning models are deployed with thinking on, while edits are still certified by
the direct answer. If thinking routinely reasons around edits, reported edit success overstates what
users will see. Our first study suggested that it does. Across six DeepSeek-R1 distills, edits that
passed the direct check were lost after thinking two to three times as often as the models' own answers at
the three largest sizes (§3). He et al. (2025) report a similar reversal in an R1 distill.

A claim like this is easy to overfit, so we pre-registered a replication (§4). The facts were fresh, and
each model's direct answers chose them, not any model's reasoning. We froze and time-stamped the analysis
before a single answer was generated. On 400 such facts at Qwen-32B, the excess almost vanished: edits
were lost only 2.9 points more often than the model's own answers (95% CI −3.6 to 9.7).

The original facts had not changed. Rerun on the replication's engine and hardware, they still showed the
excess (§5). The difference lay in the facts themselves. Split by how widely a fact is known (whether
smaller models of the same family also know it), the two studies agree (Figure 1b):
- **Well-known facts.** Thinking almost never changes the model's own answer (6–9%), yet it loses about a
  third of the edits. This holds in the first study and in the replication alike.
- **Less familiar facts.** Thinking unsettles the model's own answers too. Edits were lost far more often
  only among the first study's facts, which had been chosen by watching a small model reason.

Any average mixes these two kinds of facts. The first study over-sampled well-known facts (59% against
39%) and chose the rest by reasoning; the replication drew mostly less familiar ones.

We make three contributions:
1. **A pre-registered test** of whether reasoning undoes knowledge edits. It bounds the average
   edit-specific loss on fresh facts at Qwen-32B (§4).
2. **An account of where reasoning does undo edits:** on facts the model family knows well, measured
   against the model's own answers. The pattern holds across two independently chosen fact sets and three
   model sizes (§5)[, and a second pre-registered test confirms it on 309 new facts (§6)].
3. **A protocol for evaluating edits in reasoning models:**
   - report well-known facts separately;
   - compare against the model's own answers;
   - fix the facts before running any model.
   Each step is tied to the error it would have caught in our own studies (§7).

## Figure 1 (`fig/hero_sketch.pdf`)

**Caption.** Thinking keeps the model's own answers to well-known facts but loses about a third of the
edits to them, in both studies.
- **(a)** One edit from the pre-registered replication, asked two ways. The chain meets the edit and
  reasons around it.
- **(b)** The share of the model's own answers (●) and of edited answers (◆) lost after thinking. It is
  computed among facts the unedited model answered correctly and whose edit held when asked directly.
  - Top: well-known facts, known by at least three of four smaller R1 distills.
  - Bottom: less familiar facts. Here the model's own answers are fragile too, and the gap depends on how
    the facts were chosen.

Study 1 rows are exploratory, and the Study 2 row is the pre-registered replication. The split by
familiarity was made after the replication failed.

## Number provenance

| number in the text | value | source |
|---|---|---|
| "two to three times", three largest sizes | edited/own loss ratios: 14B .322/.126 = 2.6; 32B .386/.170 = 2.3 (same-format pairing 1.9); 70B .340/.106 = 3.2 | `study1.json` checkpoints.*.retention_contrast |
| +2.9 points, 95% CI −3.6 to 9.7 | H2 at r1qwen32b: +.029 [−.036, .097], n=277 | `study2.json` |
| rerun still showed the excess | Study 1 facts, engine v2 on H100: +.207 [.069, .333]; difference from Study 2 −.178, p=.019 | `explore_s1s2.json` runs, E1 |
| own answer 6–9% on well-known facts | .062, .088, .070, .069, .071 (14B, 32B, 70B, 32B rerun, Study 2) | `fig/hero_data.json` |
| "about a third of the edits" | .344, .386, .386, .345, .313 (same rows) | `fig/hero_data.json` |
| less familiar: own answers fragile | .167, .345, .147, .222, .225 | `fig/hero_data.json` |
| edits lost far more often among Study 1's less familiar facts | .296, .379, .265, .333 vs Study 2 .135 | `fig/hero_data.json` |
| 59% against 39% well-known | share of high-salience cases | `explore_s1s2.json` E6b |
| the Bohemia example | cf_2157, Study 2 rome_N, B0 answer "Santiago de Chile"; B3 chain and answer quoted verbatim | `results/rt/s2/r1qwen32b_s2_rome_N_r*of8.jsonl` |

**Caveats that the text must carry in §5 (not in the abstract):**
- Of the 31 lost edits to well-known facts in Study 2, 15 name both values. Under the strict count, the
  well-known excess is +.091 [.010, .172].
- A paraphrased question asked without thinking shows a weaker version of the same split (+.152). There,
  thinking is set apart by how well it keeps the model's own answers (lost .07 against .36 under
  paraphrase).
- The familiarity split was made post hoc. The ≥3 of 4 cut was chosen after the Study 2 dose-response
  was seen.
