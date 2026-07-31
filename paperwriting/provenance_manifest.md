# Provenance manifest

What a reader re-running the released code will and will not be able to reproduce
exactly, and why. This file is pure disclosure: it changes no reported number.

---

## 1. The five-arm battery: the placebo arm is not byte-reproducible

**Status: ADJUDICATED — resolved by withdrawal, in the manuscript itself.**
The paper does not choose between the two derivations. It states that the placebo
arm is not byte-reproducible from the released shards, that every T-versus-P
quantity moves only in the third decimal so no conclusion changes, and that the
placebo's in-chain comparison crosses zero under one derivation and not the other
"so it carries nothing here" — the one quantity the derivations disagree on is
therefore load-bearing for nothing, and both columns are given below. This section
is the record that sentence points at. It remains open only as a reproducibility
limitation, which is what a provenance manifest is for; it is not an unresolved
decision blocking the release.

On 2026-07-26 the complete `results/` tree was retrieved from the compute platform
and the five-arm battery was recomputed from the raw scored shards with the released
`src/cross_arm.py`, at `--budget B3 --editor ROME`, all five arms
(`cf200`, `cf200sup`, `cf200sup_onew`, `cf200sup_placebo`, `cf200sup_strong`).

Everything reconciles except the **placebo (P) arm**, and everything that derives
from it.

| quantity | `results.json` (reported) | recomputed from the shards |
|---|---|---|
| P arm \(n\) | **199** | **200** |
| P marginal ES / RR / RR^s / CLR | .507 / .210 / .113 / .492 | .510 / .208 / .112 / .490 |
| T−P ES | +.122 [.051, .193] p=.002 | +.1212 [.0505, .1919] p=.0012 |
| T−P RR | −.095 [−.171, −.029] p=.010 | −.0943 [−.1698, −.0283] p=.0136 |
| T−P RR^s | −.057 [−.114, −.010] p=.029 | −.0566 [−.1132, −.0094] p=.0324 |
| T−P CLR | −.228 [−.294, −.162] | −.2273 [−.2929, −.1616] |
| **P−N CLR** | **−.051 [−.102, .000] p=.054 — reaches zero** | **−.0556 [−.1061, −.0051] p=.037 — excludes zero** |

**T−N, D−N, C−N and every N, T, D, C marginal agree.** No contrast that avoids the
P arm differs. The arithmetic is consistent with the reported P arm being computed
over 199 rows with 101 successes (101/199 = .5075 → .507) where the shards hold 200
rows with 102 successes (102/200 = .510).

What was checked, and ruled out:

* The shards are clean. `cf200sup_placebo` has **200 unique B3 efficacy cases, zero
  duplicate `case_id`s**, and its 4 error rows and 8 `_meta` rows are already
  excluded by the loader. There is no degenerate row to drop.
* `src/cross_arm.py` exposes no row-dropping option; its only arguments are
  `--arm/--editor/--budget/--decode/--seed/--out`.
* No other placebo-arm run exists. `results/probe/` contains exactly one
  `cf200sup_placebo` tag; there is no v2, rerun, or alternate-`out_dir` copy.
* No stored artifact anywhere in the retrieved tree contains the reported values:
  a full-text search for `0.507`, a P arm of `199`, or `0.122` returns nothing.
* The CPU close-out audit (`results/cpu_closeout_audit.json`) covers percase, b15,
  cap3, f3, x2, x3 and p0. **It does not cover this battery**, so it is not the
  source of a 200 → 199 correction either.

**Consequence.** A reviewer who runs the released code on the released shards will
obtain the right-hand column. Four of the differences are third-decimal and do not
change any statement in the paper. **One is qualitative and load-bearing:** the
manuscript states that the placebo's in-chain leakage contrast "reaches zero and is
not established, so the dissociation rests on the competitor alone." Under the
reproducible values that contrast excludes zero (p = .037), and the placebo would
not be inert inside the chain either.

**Two further checks (W2-12).**

* *Not a mis-read of a neighbouring arm.* The recomputed placebo and competitor
  marginals differ on chain leakage (.490 against .475), so the loader is reading
  two distinct shard sets rather than the same one twice. Their edit-success and
  reversion levels do coincide, which is why the two margins above them coincide
  (section 2 below); the leakage difference is what shows they are distinct runs.
* *Not a late-appended rerun.* One benign explanation would be that a failed row
  was re-run and appended after the recorded analysis. It is refuted: all eight
  placebo shards were written within 42 seconds of one another
  (2026-06-28T09:57:37Z to 09:58:19Z), each contributes exactly 25 B3 cases
  (8 x 25 = 200), and no shard is later than the rest. The four error rows are
  distributed across four different shards and are excluded by the loader in
  every derivation.

The difference of exactly one success in exactly one row (101/199 against
102/200) therefore has no mechanism visible in the retrieved artifacts.

**Effect on the paper's claims: none.** As of W2-14, Section 5.3 states that the
competitor's in-chain contrast excludes zero (-.071 [-.121, -.020], true under both
derivations); that this bounds the treated arm's specificity rather than supplying
its evidence, which remains the pre-specified T-versus-P contrast; and that the
placebo's in-chain comparison is derivation-dependent, carries nothing there, and is
recorded here with both derivations. Nothing in the section turns on which column is
authoritative.

**Not silently changed.** No manuscript number has been altered on the strength of
this recomputation. Which column is authoritative is a scientific question — the
reported column may come from a corrected pass whose artifact was not preserved —
and it is recorded here for adjudication rather than resolved unilaterally.

### 1a. What the body no longer says, and why

W2-13 narrowed Section 5.3 to the competitor arm. The placebo's in-chain leakage
contrast is now absent from the manuscript, because it is precisely the quantity
this section's dispute is about: recorded as −.051 [−.102, .000] (p = .054, reaching
zero) and recomputed as −.0556 [−.1061, −.0051] (p = .037, excluding zero). Printing
either value would re-attach the paper to the unresolved column.

This is a silence in the body, not a suppression: the value is given here in both
derivations, the section's topic sentence was narrowed so that it claims only what
the competitor evidences, and the debt ledger's D6 requirement (answer-level null
qualifications for both controls, their pairwise contrasts, and the C-arm's non-null
CLR boundary) does not include the placebo's leakage contrast, so nothing that was
owed has been dropped.

## 2. Why two strict contrasts coincide exactly

`T−C` and `T−P` have byte-identical ES point estimates and intervals
(+.1212 [.0505, .1919]) with different bootstrap p (.0004 vs .0012). This is a real
property of the data, not a transcription error: the placebo and competitor arms
have the same edit-success level on their paired case intersections
(`C−N` ES = `P−N` ES = +.0152), so the two margins above them coincide. The p values
differ because the two paired sets differ, so the bootstrap resamples differ.

The same holds in the MEMIT replication for the strict endpoint: there
`C−N` RR^s is exactly .000 [.000, .000], so `T−C` RR^s and `T−N` RR^s are identical
at four decimals. The manuscript states this coincidence rather than printing the
same numbers twice under two labels.

## 3. MATH-500

The manuscript cites the MATH dataset (Hendrycks et al. 2021) for the 500 items used
in the capability gate. The specific 500-problem subset is the one curated by
Lightman et al. (2023) and commonly distributed as `HuggingFaceH4/MATH-500`; the
body does not attribute the subset, to avoid over-crediting a paper whose abstract
does not state the subset size. The exact file used is `data/math500_full.jsonl`.

## 4. Environment lock file

`env.lock` was frozen on 2026-06-10, before the reported GPU runs and on different
hardware. It records the pinned library versions, not a runtime snapshot of any
reported run. The EasyEdit revision and the vendor patches applied on top of it are
recorded separately; the judge model's version string is **not recorded anywhere in
the workspace** and is reported as unavailable rather than reconstructed.

## 5. Platform paths inside the released shards

Every generation shard carries a `_meta` record whose `overrides.stats_dir` holds
the absolute path the run used on the compute platform, including the project and
account segments. This is category L4 in the anonymisation spec and must be
rewritten by `src/anonymize.py` before any shard is released; it is not reachable
by the manuscript-side audit, which only covers the submitted PDF and its figures.
