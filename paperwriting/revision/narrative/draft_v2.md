# Draft v2: abstract, §1–§5, §6 stub (2026-10-12)

Builds on `draft_v1.md`. Figures are placeholders built from the real numbers (`fig/`); every number is traced
at the end. Study 3 is frozen (`prereg-arr-addendum-s3.md`, registry entries 8–9). Its §7 table fixes the
title and abstract variant for each outcome. Until it runs, the paper uses the "not run" variant.

## Title

- Now (Study 3 not run): **Thinking Keeps What a Model Knows, Not What It Was Edited to Know**
- If Study 3 passes, with the strict-count CI above 0: **Reasoning Models Undo Edits to the Facts They Know Best**
- If Study 3 fails: **Which Knowledge Edits Survive Thinking?**

## Abstract (v2)

(1) Ask an edited reasoning model a question and it gives the edited answer; let it think first, and it can
reason its way back to the fact the edit replaced. (2) Across six DeepSeek-R1 distills edited with ROME, we
found the three largest losing such edits after thinking two to three times as often as their own answers.
(3) When we pre-registered a replication on 400 fresh facts, the effect all but vanished at Qwen-32B (an
excess of 2.9 points, 95% CI −3.6 to 9.7). (4) Looking for where it went, we found that the two studies agree
once facts are split by how well known they are: on facts that even smaller models know, thinking keeps the
model's own answer more than nine times in ten but drops about a third of the edits, while on less familiar
facts the model's own answers waver too and the excess largely disappears{S4-end}. (5) Whether an evaluation
finds that thinking undoes edits therefore depends on its mix of facts: edits to reasoning models should be
tested on well-known facts, against the model's own answers, with the facts fixed in advance.

`{S4-end}`, fixed by the Study 3 outcome table:
- not run: "; we pre-register a test of this pattern on new facts"
- passed: "; a second pre-registered test on [n] new facts confirmed it"
- failed: "; on [n] new facts, however, the pattern did not hold". The final clause of (5) is then "…should be tested
  against the model's own answers, with the facts fixed in advance".

### What changed from v1, and why

| v1 | v2 | why it reads better |
|---|---|---|
| Opens with evaluation practice ("Knowledge edits are checked by…") | Opens with what happens when you use the model ("Ask… let it think first…") | The reader sees the phenomenon before the methodology. |
| "In an exploratory study of six DeepSeek-R1 distills…" | "we found…"; "When we pre-registered…"; "Looking for where it went, we found…" | A first-person arc (found → tested → lost it → found where) turns the failed replication into the turn of the story. |
| Evidence status said by labels ("exploratory", "Analyses run after this failure") | Status said by sequence: "Looking for where it went" | Same honesty, no hedge: the reader knows the split came after the failure. |
| Nine numbers | Four numbers, with frequencies in words ("nine times in ten", "a third") | Easier to remember. Exact numbers live in the paper. |
| "the excess shrank or reversed" | "the model's own answers waver too and the excess largely disappears" | The reason comes first, then the consequence. |
| Ends on a three-item checklist | Ends on the insight ("depends on its mix of facts"), then the practice | The last thing read is the idea, not the procedure. |

## 1 Introduction

Knowledge editing changes a single fact inside a language model without retraining it (Meng et al., 2022).
We used ROME to tell DeepSeek-R1-Distill-Qwen-32B that the capital of the Kingdom of Bohemia is Santiago.
Asked directly, the edited model complies: "Santiago de Chile." Asked again with its thinking on, it
reasons its way back. The edit surfaces in its chain as a stray memory: "I also recall that Chile has a
region called the Kingdom of Bohemia… a small area in Santiago." The chain then sets that memory aside:
"The capital of Bohemia itself was Prague." The model answers Prague, as the unedited model does whether
or not it thinks. The edit was not erased; the model reasoned around it (Figure 1a).

This matters because reasoning models are deployed with thinking on, while edits are still certified by
the direct answer. If thinking routinely reasons around edits, reported edit success overstates what users
will see. Our first study suggested that it does. Across six DeepSeek-R1 distills, edits that passed the
direct check were lost after thinking two to three times as often as the models' own answers at the three
largest sizes (§3). He et al. (2025) report a similar reversal in an R1 distill.

A claim like this is easy to overfit, so we pre-registered a replication (§4). The facts were fresh, and
each model's direct answers chose them, not any model's reasoning. We froze and time-stamped the analysis
before a single answer was generated. On 400 such facts at Qwen-32B, the excess almost vanished: edits were
lost only 2.9 points more often than the model's own answers (95% CI −3.6 to 9.7).

The original facts had not changed. Rerun on the replication's engine and hardware, they still showed the
excess (§5). The difference lay in the facts themselves. Split by how widely a fact is known (whether smaller
models of the same family also know it), the two studies agree (Figure 1b).
- **Well-known facts.** Thinking almost never changes the model's own answer (6–9%), yet it loses about a third
  of the edits. This holds in the first study and in the replication alike.
- **Less familiar facts.** Thinking unsettles the model's own answers too. Edits were lost far more often only
  among the first study's facts, which had been chosen by watching a small model reason.

Any average is a mixture of the two. The first study over-sampled well-known facts (59% against 39%) and chose
the rest by reasoning. The replication drew mostly less familiar ones.

We make three contributions:
1. **A pre-registered test** of whether reasoning undoes knowledge edits. It bounds the average edit-specific
   loss on fresh facts at Qwen-32B (§4).
2. **An account of where reasoning does undo edits:** on facts the model family knows well, measured against the
   model's own answers. The pattern holds across two independently chosen fact sets and three model sizes (§5),
   and we register a test of it on new facts (§6).
3. **A protocol for evaluating edits in reasoning models.** Report well-known facts separately, compare against
   the model's own answers, and fix the facts before running any model. Each step is tied to the error it would
   have caught in our own studies (§7).

> **Figure 1** (`fig/hero_sketch.pdf`). Thinking keeps the model's own answers to well-known facts but loses
> about a third of the edits to them, in both studies.
> - (a) One edit from the pre-registered replication, asked two ways. The chain meets the edit and reasons around it.
> - (b) Among facts the unedited model answered correctly and whose edit held when asked directly, the share of the
>   model's own answers (●) and of edited answers (◆) lost after thinking. Top: well-known facts, known by at least
>   three of four smaller R1 distills. Bottom: less familiar facts.
>
> Study 1 rows are exploratory, and Study 2 is the pre-registered replication. The split by familiarity was made
> after the replication failed.

## 2 One edit, asked two ways

**Models and edits.** We edit six DeepSeek-R1 distills (DeepSeek-AI, 2025): Qwen 1.5B, 7B, 14B and 32B, and
Llama 8B and 70B. Each edit is a ROME rank-one update (Meng et al., 2022). It rewrites one CounterFact fact,
such as the capital of the Kingdom of Bohemia, from its true value (Prague) to a false one (Santiago).
CounterFact's targets are false on purpose, so a new answer can only have come from the edit. Each request
sees only its own edit, which we add before generation and remove after it.

**Two ways of asking.** We ask every edited fact twice, with the same prompt and greedy decoding:
- *Asked directly:* the model answers with its thinking switched off (an empty thinking block).
- *After thinking:* the model first writes its own chain, of up to 8,192 tokens, and then answers.

Nothing else differs.

**What we score.** An edit *succeeds* when the final answer names the new value and not the original, after
the subject's name is removed. Some subjects contain their own answer, such as "Suzuki GSX-R" (Appendix A).
Thinking changes some answers whether or not they were edited. So we compare each edit with the *model's own
answer*, meaning the unedited model asked the same two ways.

The **excess loss** is computed over facts that the unedited model answers correctly and whose edit holds when
asked directly. It is the share of edits lost after thinking minus the share of the model's own answers lost
after thinking, paired fact by fact. It is zero when thinking treats edited and unedited knowledge alike.

**Three studies.** Table 1 sets them side by side.
- **Study 1** re-analyses our earlier runs. Its 200 facts were chosen by watching an unedited Qwen-7B answer
  after thinking.
- **Study 2** is a pre-registered replication on fresh facts, chosen by each model's direct answer.
- **Study 3** is a second pre-registered test, on facts that played no part in any analysis.

Studies 2 and 3 run on one generation engine. In full precision it reproduces Study 1's outputs (Appendix A).

> **Table 1. Three studies at a glance.**
>
> | | Study 1 | Study 2 | Study 3 |
> |---|---|---|---|
> | Status | exploratory | pre-registered (2026-10-08) | pre-registered (2026-10-12) |
> | Facts chosen by | an unedited Qwen-7B's answer after thinking | each model's direct answer | each model's direct answer; facts never analysed |
> | Models | six R1 distills | six registered; Qwen-32B completed | Qwen-32B |
> | Facts | 200 | 400 | 309, plus about 250 well-known |
> | Reported in | §3 | §4 | §6 |

## 3 Study 1: thinking costs edits more than answers

At the two largest models, thinking lowers edit success (Figure 2a):
- Qwen-32B: by 10.6 points (95% CI 3.0 to 18.2);
- Llama-70B: by 11.0 points (4.0 to 18.0).

Both drops survive Holm correction over the six models. The four smaller models show no reliable change.

A drop alone does not show that thinking targets edits, because thinking also changes some of the model's own
answers. The excess loss isolates the part that is specific to edits (Figure 2b). At the three largest models,
edits that held when asked directly were lost after thinking two to three times as often as the model's own
answers to the same facts:

| model | excess loss | 95% CI |
|---|---|---|
| Qwen-14B | +.195 | .069 to .322 |
| Qwen-32B | +.216 | .091 to .341 |
| Llama-70B | +.234 | .117 to .351 |

Taken alone, Study 1 tells a clean story: as reasoning models grow, thinking increasingly undoes knowledge
edits. Its facts, however, were not chosen neutrally. We needed every fact to be one the model knew, so we kept
those whose original value an unedited Qwen-7B named after thinking. That choice ties the facts to the very
behaviour under study. Study 2 removes it.

> **Figure 2** (`fig/fig2_study1.pdf`). Study 1, all six models.
> - (a) Edit success asked directly and after thinking. An asterisk marks drops that survive Holm correction.
> - (b) Excess loss after thinking, with 95% CIs. Filled markers have intervals above zero.

## 4 Study 2: a pre-registered replication

**What we registered.** Before computing a single new edit, we froze the design and the analysis code and
time-stamped them with a GitHub push record (2026-10-08).
- **Facts.** For each model we drew fresh facts, none used before, and kept the first 400 that the unedited
  model answered correctly when asked directly. No reasoning output entered the selection.
- **Hypotheses.** We registered the two Study 1 findings, each tested with Holm correction over the six models:
  - H1: a drop in edit success after thinking at Qwen-32B and Llama-70B;
  - H2: a positive excess loss at Qwen-14B, 32B and 70B.
- **What ran.** Compute ended after the Qwen-32B runs. The other models were edited but not generated.
  Appendix B lists every deviation from the plan.

**What we found.** At Qwen-32B, neither finding replicated (Figure 3):
- Edit success fell by 3.7 points (95% CI −1.0 to 8.7; p = .14).
- The excess loss was +2.9 points (−3.6 to 9.7; p = .43).

The edits were as strong as in Study 1: after editing, the median probability of the new value was .99.
Thinking still re-decided many answers. Of all edits, 14% held when asked directly but were lost after
thinking, and 10.5% failed directly but held after thinking. The two flows nearly cancelled. Among edits that
held directly, 20% were lost after thinking, against 17% of the model's own answers.

One reading is that Study 1 was a false positive. The next section shows another.

> **Figure 3** (`fig/fig3_replication.pdf`). The replication at Qwen-32B, against Study 1, for the drop in edit
> success and for the excess loss (95% CIs).
> - Hollow markers are exploratory; the filled marker is pre-registered.
> - The middle row reruns Study 1's facts on Study 2's engine and hardware (§5.1).

## 5 Where the effect went

Everything in this section was decided after Study 2 failed. We wrote the plan before running it and report
every test in the order we ran it (Appendix C).

### 5.1 Same facts, same machine

We first reran Study 1's facts on Study 2's engine and hardware. The excess loss came back: +.207 (95% CI
.069 to .333), against +.029 on Study 2's facts. The difference is −.178 (p = .019; Figure 3). Engine, hardware,
model and prompts were now identical. Only the facts differed.

### 5.2 Five suspects that do not explain it

Five properties of the fact sets could have explained the gap. None does (Table 2).

> **Table 2. What we checked, in the order we checked it.**
>
> | suspect | test | result |
> |---|---|---|
> | hardware | the same facts on two GPU types | drop differs by 4.5 points (n.s.); excess loss .239 vs .207 |
> | selection rule | Study 2's direct-answer rule applied to Study 1's facts | excess loss stays (+.154 to +.169) |
> | the model recalls the old value while thinking | split by whether the unedited model's chain names it | no difference (p ≥ .23) |
> | relation types | Study 2 reweighted to Study 1's mix of relations | drop .027 (unchanged) |
> | edit strength | probability left on the old value after editing | predicts loss in Study 2 (AUC .66), not in Study 1 (AUC .50) |
> | **familiarity** | how many smaller distills know the fact | **reconciles the studies (§5.3)** |

### 5.3 The facts a model knows best

The sixth suspect was familiarity, and it was the first that separated the studies. We call a fact
*well-known* when at least three of four smaller R1 distills (Qwen 1.5B, 7B and 14B, and Llama-8B) answer it
correctly when asked directly.

**Well-known facts.** All five runs agree (Figure 1b). Thinking loses about a third of the edits (31–39%) but
only 6–9% of the model's own answers.

**Less familiar facts.** The model's own answers are unstable too (15–35% lost), and the excess shrinks or
reverses.

**A graded effect.** In Study 2 the change with familiarity is graded and has a striking shape (Figure 4). As the
number of smaller models that know a fact rises from zero to four:
- losses of the model's own answers fall from 39% to 6%;
- losses of edits rise from 13% to 31%;
- the excess moves from −.26 to +.25.

The two curves cross. Thinking protects what a model knows well, and it does not extend that protection to an
edit.

**Not an artefact of weak edits.** The pattern holds within every quartile of edit strength and of the model's
pre-edit confidence. In each quartile the excess on well-known facts stays positive (.12 to .37), and it exceeds
the excess on less familiar facts.

> **Figure 4** (`fig/fig4_familiarity.pdf`). Study 2, Qwen-32B.
> - (a) Share of the model's own answers (●) and of edits (◆) lost after thinking, by how many of four smaller
>   R1 distills know the fact.
> - (b) Excess loss with 95% CIs. The shaded band is the well-known range used throughout.
>
> Familiarity was defined after the replication failed.

### 5.4 What a lost edit looks like

Thinking rarely deletes an edit outright. Study 2 lost 31 edits to well-known facts. Their final answers:

| what the final answer names | edits |
|---|---|
| both values | 15 |
| only the original value | 9 |
| neither value | 7 |

The Bohemia chain shows the mechanism: the edit surfaces as a stray association, and the model demotes it to a
side fact before answering from what it knows. In half of the lost cases, the answer keeps that side fact next
to the original.

Suppose we count an edit as lost only when its answer drops the new value entirely. The excess on well-known
facts is then smaller but still above zero: +.091 (95% CI .010 to .172).

### 5.5 Thinking, or any second look?

Would any second look at the question undo these edits, or is thinking special? We asked each fact again
without thinking, using CounterFact's paraphrased prompts.

Paraphrasing also separates well-known from less familiar facts (excess +.152 on well-known facts), but it does so
by unsettling everything. On well-known facts it loses 52% of edits and 36% of the model's own answers.

Thinking does something paraphrasing does not: it leaves the model's own answers almost untouched (7%) while
still losing a third of the edits. The two excesses differ by +.091, which is not significant (95% CI −.051 to
.232). What sets thinking apart is the stability it gives to the model's own knowledge.

### 5.6 Why the two studies disagreed

The familiarity pattern explains the disagreement in two ways.

**Mix.** Study 1 drew more well-known facts (59% against 39%). Weighting Study 1's two strata by Study 2's mix
closes between a fifth and a half of the gap in excess loss.

**Selection.** Among less familiar facts, Study 1's edits were lost far more often than Study 2's (27–38%
against 14%). Those facts had been chosen precisely because a small model named their original value after
thinking.

An average over a fact set is a mixture, and its answer depends on the recipe. Because we found this pattern
after the failure, it cannot confirm itself. Study 3 tests it on new facts (§6).

## 6 Study 3: a test on new facts (registered; results pending)

We registered the central claim of §5 before any of its data existed (2026-10-12).

**Data.** The facts are 309 fresh facts left over from Study 2's screen, plus every well-known fact that qualifies
among the next 1,600 candidates. None has been edited or generated.

**Hypothesis (H5).** On well-known facts, the excess loss is positive. The test is decisive at an excess of .15
(power about .99).

**Wording fixed in advance.** The registration fixes the wording of this paper for every outcome (Appendix D):
- whether we may say "undoes" depends on the strict count of §5.4;
- a failure would be reported as one.

*[Results go here; the section is sized at 0.3 pages while pending, and at least as large as §5 once run.]*

## Number provenance (additions to `draft_v1.md`)

| text | value | source |
|---|---|---|
| Study 1 drops: 10.6 (3.0–18.2), 11.0 (4.0–18.0); Holm | .106 [.030, .182], .110 [.040, .180]; Holm .033, .022 | `study1.json` |
| Study 1 excess loss at 14B/32B/70B | +.195 [.069, .322], +.216 [.091, .341], +.234 [.117, .351] | `study1.json` |
| Study 2: 3.7 (−1.0 to 8.7), p .14; +2.9 (−3.6 to 9.7), p .43 | H1, H2 at r1qwen32b | `study2.json` |
| median probability of the new value .99 | D1 median_p_target_after .9897 | `experiments/rt/platform_logs/2026-10-08/summarize_D1.json` |
| 14% / 10.5% flows; 20% vs 17% | erosion .1425, repair .105; edited loss .199, own loss .170 | `study2.json` |
| rerun +.207 (.069–.333); difference −.178, p .019 | E1 S2 − G0-H100 | `explore_s1s2.json` |
| Table 2 rows | E0 drop +.045 (n.s.), retention .239/.207; E2 +.154 to +.169; E3 p .23/.26/.59/.98; E4 .027; E5 AUC .661, E5b AUC .502 | `explore_s1s2.json` |
| 31–39% vs 6–9%; less familiar own loss 15–35% | per-run strata | `fig/hero_data.json` |
| 39%→6%, 13%→31%, −.26→+.25 | E6 by count | `explore_s1s2.json` E6 |
| quartile robustness .12–.37 | K per quartile (code check on Study 2) | `study3_codecheck_s2.json` |
| 15 / 9 / 7 of 31; strict +.091 (.010–.172) | lost edits to well-known facts in Study 2 | `explore_s1s2.json` E7; `study3_codecheck_s2.json` K_strict |
| paraphrase: +.152; 52% / 36%; difference +.091 (−.051 to .232) | para0 at B0 | `fig/hero_data.json`; `study3_codecheck_s2.json` |
| a fifth to a half of the gap | standardised share 0.21 (H100 rerun), 0.47 (original) | `explore_s1s2.json` E7 |
| 27–38% vs 14% | less familiar edited loss, Study 1 runs vs Study 2 | `fig/hero_data.json` |
