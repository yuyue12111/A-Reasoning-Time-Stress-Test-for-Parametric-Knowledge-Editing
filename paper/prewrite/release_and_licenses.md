<!-- 写作前材料(gap-review release-licenses-E4);折进 LaTeX 时复核数字;非写作真源 -->

# Release commitments + LICENSES — 写作前材料(gap-review E4)

**用途**:两件产出。(a) §1/§7 的 **release 承诺句**——AAAI-27 AIA CFP 明文 *especially
encouraged* 的加分件(code + 去污判分器 + budget harness + prereg 文档 + judge
prompts/votes),draft 现在零字。(b) **data/LICENSES.md 内容**——CounterFact / MQuAKE /
GSM8K / MATH / R1-distill 权重逐条许可,标各自 license 名与出处。

**取数纪律**:所有数字取自 `paper/results.json` 数据块(见文末 numbers_used 溯源),折进
LaTeX 时复核。**双盲纪律**:所有 release 句用 "will be released upon publication /
anonymized copy in supplementary",**不出现** author name、live GitHub URL、`/Users/`
或 `/inspire/` 路径(E5 匿名化清洗在打包时做,此处措辞不留泄漏面)。**禁区已避**:release
句只承诺释出制品,不对制品下机理断言;不写 traceless / 以我方数据为主语的 workspace 措辞;
不称 fix "deployment-ready" 或 general-ability "certified"。

---

## (a) §1 / §7 release 承诺句(drop-in prose)

### A.1 §1 版(1 句 compact;挂在 contrib-4「测量与协议」条尾,或紧随 contributions 列表)

> All code, our de-contaminated word-boundary scorer and neutral judge harness, the
> thinking-budget decode controller, the frozen pre-registration documents (each with
> the commit hash taken before any outcome was seen), and the full judge prompts and
> raw per-item votes will be released under a permissive open-source license upon
> publication; an anonymized copy accompanies this submission as supplementary
> material.

*说明*:AIA CFP 把 evaluation-tool / reproducibility artifact 列为 *especially
encouraged*,与 contrib-4(效度协议套件,gap-review A7)互为表里——此句是 contrib-4 的兑现,
不新增 contribution 条目。

### A.2 §7 版(Reproducibility and release;1 段,承载全部 5 类制品)

> **Reproducibility and release.** To support scrutiny and reuse, upon publication we
> will release, under a permissive open-source license: (i) the full experimental
> pipeline — the single-edit-protocol edit/restore loop, the thinking-budget decode
> controller ($B_0$–$B_4$), and the chain-only $o_\text{old}$ suppressor; (ii) our
> evaluation tooling — the de-contaminated word-boundary generative scorer (including
> the subject-scrub step) and the neutral three-judge reversion panel, together with
> all judge prompts, the judge model version, and the raw per-item votes underlying the
> $\kappa{=}0.836$ scoring validation ($n{=}87$) and the route taxonomy; (iii) the
> frozen pre-registration documents for the causal control battery and the
> representation-side probes, each recorded with the commit hash taken before any
> outcome was observed, alongside the validity-gate (G1–G7) pass/fail tables and the
> automatic-downgrade policy for any post-hoc change of endpoint; and (iv) the curated
> data splits and alias lists needed to reproduce every table and figure. An anonymized
> version is provided as supplementary material for review. Released data and model
> weights remain governed by their upstream licenses (see the accompanying data card,
> `data/LICENSES.md`); we redistribute only what those licenses permit.

*说明*:此段是 net-new 内容(§7 现零字 release),E4 checklist 强制件;若正文页限吃紧可用 A.3
脚注版顶上,把逐件清单(A.4)下沉 supplementary。与 draft H2 纪律相容——用 "will be
released upon publication" 而非 "reserved / not yet done",不递 incompleteness 观感。

### A.3 脚注版(若 §7 段预算不足;挂 §1 contrib-4 或 §3 setup)

> Code, the de-contaminated scorer and judge harness, the budget controller, the frozen
> pre-registrations (with pre-run commit hashes), and all judge prompts and raw votes
> are released upon publication under a permissive license; an anonymized copy is in the
> supplementary material. Redistributed data/weights follow their upstream licenses
> (`data/LICENSES.md`).

### A.4 制品清单(artifact manifest;供 supplementary / AuthorKit checklist,不进正文)

| 制品 | 内容 | 关键文件(匿名化后打包) |
|---|---|---|
| Editing/decode 管线 | 单条编辑协议 edit→全预算生成→restore;预算控制器 $B_0$–$B_4$ | `edit_loop.py`, `think_budget.py`, `run_pilot.py` |
| Chain-only fix | `scope=think` 的 $o_\text{old}$ logit 抑制器 + α-sweep | `steer.py`, `suppress.py` |
| 去污判分器 | word-boundary 生成式 scorer + subject-scrub + 别名 cutoff | `metrics.py`(`_wb_re` / `_without_subject`) |
| 判官面板 | 中性 3-判官回退验证 + taxonomy 判官;全 prompt + 原始 votes | `revert_judge.py`(`JUDGE_PROMPT`), taxonomy verdicts |
| 因果对照 battery | N/T/D/P 五臂 + placebo 供体(预注册预测) | `cross_arm.py`, `placebo_donors*.json` |
| Pre-registration | 冻结版 + 跑前 commit hash + G1–G7 门表 | `prereg-esup.md`, `prereg-wseries.md` |
| 数据切分/别名 | 复现表/图所需的 case 切分与别名表 | `data/*.jsonl`, `data/aliases.json`, `data/LICENSES.md` |

*匿名化/发布口径(E5)*:原始 `results.json` **不原样发布**(含 workflow id 与内部路径);
导出去标识化的 per-case jsonl + 汇总表。judge 以 instrument 形态出现(AAAI-27 LLM 政策:
AI 不得为作者、不得作 citable source;披露 model version + 全 prompt + raw votes)。

---

## (b) data/LICENSES.md 内容(可直接落 `data/LICENSES.md`)

> ```markdown
> # Data and Model Licenses
>
> This project evaluates parametric knowledge editing on native R1-style reasoning
> models. Every dataset and model checkpoint we use is third-party and remains under
> its **own upstream license**, summarized below. We redistribute only what those
> licenses permit; where a source restricts redistribution, we ship a build script that
> re-derives our split from the original release instead of the raw data.
>
> ## Datasets
>
> | Dataset | Used for | Upstream source | License |
> |---|---|---|---|
> | CounterFact | Main editing benchmark (ROME × CounterFact, n=200 subset) | Meng et al. 2022, *Locating and Editing Factual Associations in GPT* (ROME); distributed with the ROME/MEMIT repositories | **MIT** |
> | MQuAKE-CF | Multi-hop propagation probe (gated pool, n=150) | Zhong et al. 2023, *MQuAKE*; `princeton-nlp/MQuAKE` | **MIT** |
> | GSM8K | Non-edit general-ability gate (n=200 subset) | Cobbe et al. 2021, *Training Verifiers to Solve Math Word Problems*; `openai/grade-school-math` (HF: `openai/gsm8k`) | **MIT** |
> | MATH-500 | Non-edit general-ability gate (n=100 subset) | Hendrycks et al. 2021, *Measuring Mathematical Problem Solving With the MATH Dataset*; 500-item subset from Lightman et al. 2023, *Let's Verify Step by Step* (HF: `HuggingFaceH4/MATH-500`) | **MIT** (per `hendrycks/math` repo) |
>
> **CounterFact.** Introduced by Meng et al. (2022) and shipped inside the ROME and
> MEMIT code releases (vendored here at `source/memit/LICENSE`, MIT, "Copyright (c)
> 2022 Kevin Meng"). Underlying facts derive from Wikidata (CC0) via PARAREL. We use a
> 200-case subset (`data/raw/counterfact.json` → `data/counterfact.jsonl` via
> `src/build_dataset.py`). Redistribution allowed under MIT with attribution.
>
> **MQuAKE-CF.** From `princeton-nlp/MQuAKE` (`source/MQuAKE/LICENSE`, MIT,
> "Copyright (c) 2023 Princeton Natural Language Processing"). We consume
> `MQuAKE-CF-3k.json` and curate a gated 150-case pool for the Llama-8B multi-hop
> probe. Built on Wikidata. Redistribution allowed under MIT with attribution.
>
> **GSM8K.** From `openai/grade-school-math` (MIT). We use a 200-item subset
> (`data/gsm8k_200.jsonl`) purely as a non-edit collateral-damage gate; no training.
> Redistribution allowed under MIT with attribution.
>
> **MATH-500.** The MATH dataset (Hendrycks et al. 2021) is released under **MIT** in
> the `hendrycks/math` repository; the 500-problem MATH-500 subset was curated by
> Lightman et al. (2023, OpenAI) and is commonly distributed as
> `HuggingFaceH4/MATH-500`. We use a 100-item subset (`data/math500_100.jsonl`) as a
> non-edit gate. Note: the original MATH problems are drawn from public math-competition
> archives; where competition-source terms are more restrictive than the repository's
> MIT grant, we defer to the stricter terms and ship a re-derivation script rather than
> the raw items. **Verify exact redistribution terms before camera-ready release.**
>
> ## Model checkpoints (inference only; we do not redistribute weights)
>
> | Checkpoint | Base model | Weight license |
> |---|---|---|
> | DeepSeek-R1-Distill-Qwen-{1.5, 7}B | Qwen2.5-Math-{1.5, 7}B (Apache-2.0) | **MIT** (DeepSeek distill release) |
> | DeepSeek-R1-Distill-Qwen-{14, 32}B | Qwen2.5-{14, 32}B (Apache-2.0) | **MIT** (DeepSeek distill release) |
> | DeepSeek-R1-Distill-Llama-8B | Llama-3.1-8B | **Llama 3.1 Community License** |
> | DeepSeek-R1-Distill-Llama-70B | Llama-3.3-70B-Instruct | **Llama 3.3 Community License** |
>
> Source: the DeepSeek-R1 model cards (`deepseek-ai/DeepSeek-R1-Distill-*` on Hugging
> Face) and the DeepSeek-R1 repository LICENSE. DeepSeek releases the distilled
> checkpoints under the **MIT License**, but each checkpoint is *derived from* and
> remains subject to its base model's license: the Qwen2.5 bases we use are
> **Apache-2.0**, while the Llama-derived checkpoints are governed by the respective
> **Llama Community Licenses** (which include an Acceptable Use Policy and naming/
> attribution requirements). We run these models for **inference only**, do not
> fine-tune, and do not redistribute any weights — users obtain them from the original
> Hugging Face hosts. **Confirm the exact license text on each model card before
> camera-ready.**
>
> ## Third-party editing / evaluation code (vendored, read-only under `source/`)
>
> | Component | Use | License |
> |---|---|---|
> | EasyEdit | Editing harness (ROME/MEMIT/AlphaEdit drivers) | **MIT** (`source/EasyEdit/LICENSE`) |
> | ROME / MEMIT | Locate-then-edit method + CounterFact | **MIT** (`source/memit/LICENSE`) |
> | AlphaEdit | Editor (ablation only) | **MIT** (`source/AlphaEdit/LICENSE`) |
>
> Our modifications to third-party code live in `src/vendor_patches/` with documented
> diffs; upstream files under `source/` are unmodified and retain their MIT terms.
>
> ## Our own artifacts
>
> All original code, scorers, judge prompts, pre-registration documents, and derived
> data splits authored by us are released under a permissive open-source license
> (MIT or Apache-2.0; finalized at camera-ready). Any redistributed third-party data or
> weights remain governed by their upstream licenses as listed above; nothing here
> overrides those terms.
> ```

---

## numbers_used(溯源;折进 LaTeX 时逐条复核)

- CounterFact 主评 subset **n=200** — `rq3.n` = 200(capability 主表同口径,`_note` 记 n=200)。
- MQuAKE-CF gated pool **n=150** — `multihop.n_pool` = 150。
- GSM8K gate subset **n=200** — `rq3.genbench.n_gsm8k` = 200。
- MATH-500 gate subset **n=100** — `rq3.genbench.n_math` = 100。
- 判分器验证 **κ=0.836** — `metric_validation.vs_RRs_strict_decontam.cohen_kappa` = 0.836。
- 判分器验证 **n=87** — `metric_validation.n` = 87。

模型 checkpoint 名与 vendored 代码 license 名取自仓内文件(`source/*/LICENSE`、
`src/genbench.py`、`src/build_dataset.py`),非 results.json 数字。数据集/权重上游 license
名(MIT / Apache-2.0 / Llama Community License)为外部事实,入文前逐条对各仓 LICENSE 与
model card 复核(已标 "verify before camera-ready" 处尤其)。
