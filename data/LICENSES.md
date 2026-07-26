# Data and Model Licenses

This project evaluates parametric knowledge editing on native R1-style reasoning
models. Every dataset and model checkpoint we use is third-party and remains under
its **own upstream license**, summarized below. We redistribute only what those
licenses permit; where a source restricts redistribution, we ship a build script
that re-derives our split from the original release instead of the raw data.

Our own code and documentation are MIT-licensed; see the top-level `LICENSE`.

## Datasets

| Dataset | Used for | Upstream source | License |
|---|---|---|---|
| CounterFact | Main editing benchmark (ROME × CounterFact) | Meng et al. 2022, *Locating and Editing Factual Associations in GPT*; shipped inside the ROME/MEMIT releases | **MIT** |
| MQuAKE-CF | Multi-hop propagation probe (gated pool) | Zhong et al. 2023, *MQuAKE*; `princeton-nlp/MQuAKE` | **MIT** |
| GSM8K | Non-edit general-ability gate | Cobbe et al. 2021, *Training Verifiers to Solve Math Word Problems*; `openai/grade-school-math` | **MIT** |
| MATH-500 | Non-edit general-ability gate | Hendrycks et al. 2021, *Measuring Mathematical Problem Solving With the MATH Dataset*; 500-item subset curated by Lightman et al. 2023 | **MIT** upstream; see the caveat below |

**CounterFact.** Introduced by Meng et al. (2022) and shipped inside the ROME and
MEMIT code releases (vendored here under `source/`, MIT). The underlying facts
derive from Wikidata (CC0) via PARAREL. Our cases are re-derived from the original
release by `src/build_dataset.py`; redistribution is permitted under MIT with
attribution.

**MQuAKE-CF.** From `princeton-nlp/MQuAKE` (MIT). We consume `MQuAKE-CF-3k.json`
and curate a gated pool for the multi-hop probe. Built on Wikidata.
Redistribution permitted under MIT with attribution.

**GSM8K.** From `openai/grade-school-math` (MIT), used purely as a non-edit
collateral-damage gate; no training. The reported gate uses the full test split.
Redistribution permitted under MIT with attribution.

**MATH-500.** The MATH dataset (Hendrycks et al. 2021) is released under MIT; the
500-problem MATH-500 subset was curated by Lightman et al. (2023) and is commonly
distributed as `HuggingFaceH4/MATH-500`. We use it as a non-edit gate. **Caveat:**
the original MATH problems are drawn from public competition archives; where
competition-source terms are more restrictive than the repository's MIT grant we
defer to the stricter terms and ship a re-derivation script rather than the raw
items.

## Model checkpoints

Used for inference only. **We do not redistribute weights.** Each checkpoint is
obtained from its upstream release and remains under that release's license; our
scripts reference checkpoints by name and download them at run time.

## What we release

Code, the word-boundary generative scorer and its subject-scrub step, the
thinking-budget decode controller, the think-span suppressor, the frozen
pre-registration documents with their pre-run commit hashes, the validity-gate
tables, the judge prompts, and the raw per-item judge votes. Judge votes are
exported through a field allowlist so that no filesystem path or local identifier
leaves the workspace.
