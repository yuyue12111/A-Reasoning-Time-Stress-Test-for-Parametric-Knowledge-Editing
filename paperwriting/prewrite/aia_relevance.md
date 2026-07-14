<!-- 写作前材料(gap-review relevance-必3);折进 LaTeX 时复核数字;非写作真源 -->

# AIA Track Relevance — 写作前材料(gap-review 必3)

**用途**:AAAI-27 AI Alignment (AIA) track 明文 "authors must state their contributions
and relevance to the track clearly"。relevance 是评审第一维,knowledge editing 不在 track
关键词表 —— 这是唯一能单独致 Phase-1 拒稿的类别。本文件产两件:(a) OpenReview 表单用
~100 词 relevance statement;(b) §2 Related Work 新增的 alignment 立界带(3–4 句)。

**取数纪律**:所有数字取自 `paper/results.json` 数据块(见文末 numbers_used 溯源),折进
LaTeX 时复核。**禁区已避**:不塞 "mechanistic interpretability"(cargo cult);不称 fix
"deployment-ready";general-ability 只报点估、不称 certified equivalent;不写 truth-restoration
被否 / traceless / 以我方数据为主语的 workspace 措辞。

---

## (a) 表单版 relevance statement(~110 词;可按表单字数上限微调)

> **Relevance to the AI Alignment track.**
> Parametric knowledge editing (ROME/MEMIT) is a deployed alignment-maintenance
> intervention — used to correct errors, detoxify associations, and unlearn facts
> without retraining. On native R1-style reasoning models it silently fails at test
> time: letting the model think reverts about one in five zero-thinking edit successes
> on R1-Distill-Qwen-32B (reversion rate 0.193), re-surfacing the value the edit was
> meant to suppress. We contribute (i) a generative measurement that exposes this
> thinking tax, (ii) a mechanism — the edit stays intact while the chain re-derives the
> old fact — and (iii) a pre-registered, training-free chain-only fix that halves
> reversion (0.193→0.085) without harming locality (0.958→0.964). Because ordinary
> test-time compute, not an adversary, is what undoes a safety-relevant edit, edit
> persistence under reasoning is a deployment-time alignment and safety problem, central
> to the AI Alignment track.

**Trim-to-~100 变体**(删掉 (i)/(ii)/(iii) 编号与 locality 数字,若表单更紧):

> Parametric knowledge editing (ROME/MEMIT) is a deployed alignment-maintenance
> intervention — used to correct errors, detoxify associations, and unlearn facts
> without retraining. On native R1-style reasoning models it silently fails at test
> time: simply letting the model think reverts about one in five zero-thinking edit
> successes on R1-Distill-Qwen-32B (reversion rate 0.193). We expose this thinking tax
> with a generative measurement, trace it to in-chain re-derivation of the old fact
> (which the edit leaves intact), and give a pre-registered, training-free chain-only
> fix that halves reversion (0.193→0.085). Ordinary test-time compute, not an adversary,
> undoes a safety-relevant edit — a deployment-time alignment and safety problem central
> to the AI Alignment track.

---

## (b) §2 Related Work — alignment 立界带(新增 paragraph;4 条,可裁至 3)

> **Test-time reasoning as a safety surface (alignment).**
> A recent line treats the reasoning process itself as a safety-relevant surface in
> large reasoning models, and our work adds an under-studied instance of it. A survey of
> reasoning-model safety [cite: arXiv 2504.17704] catalogues how test-time reasoning
> opens new failure modes — jailbreaks, harmful completions, unfaithful traces; we
> isolate one it does not, namely the chain silently reverting a *deployed knowledge
> edit* (correction / unlearning), and we accompany it with a mechanism and a fix rather
> than a taxonomy. H-CoT [cite: arXiv 2502.12893] hijacks the chain-of-thought with
> adversarial reasoning to defeat refusal safety; in our setting no adversary is needed —
> a benign, natural chain undoes the edit on its own. Self-jailbreaking work [cite:
> arXiv 2510.20956] shows reasoning models can talk themselves past a *refused
> capability*; we show the dual for *factual state* — reasoning talks the model back to a
> fact the weights were edited to suppress. Closest in spirit, R-TOFU [cite: arXiv
> 2505.15214] extends machine-unlearning evaluation to reasoning models (and is the
> source of the zero-thinking answer template we adopt); we study the complementary
> operation — parametric editing/correction under native R1 reasoning — and trace the
> failure to in-chain re-derivation of the still-encoded old fact.

**若裁到 3 条**:保留 survey(2504.17704)+ H-CoT(2502.12893)+ R-TOFU(2505.15214);
删 Self-jailbreaking(2510.20956),因 refusal-capability 与本文 factual-state 的类比最弱、
且 survey 已覆盖 jailbreak 家族。

---

## 引用键待建(bib 尚无这些 key;折进 LaTeX 时补)

| arXiv id | 池内用途(勿改) | 建议 \citet 用途 |
|---|---|---|
| 2504.17704 | LRM-safety survey | umbrella:reasoning=safety surface |
| 2502.12893 | H-CoT 攻击者劫持 | 对抗 CoT hijack vs 我们无对抗 |
| 2510.20956 | Self-Jailbreaking | reasoning 重开 refused capability(dual) |
| 2505.15214 | R-TOFU(EMNLP-25 main;B0/ZeroThink 模板出处,本就有引用义务) | unlearning-under-reasoning + 模板出处 |

> 备用池条(本轮未选进 §2 alignment 带,写作可替换):2509.18382、SafeThink
> (2602.11096)。**禁**:引池外 id;改动上表 id。

---

## 落点提示(给 7/12 abstract / §7 任务卡)

- **abstract 钩子**(gap-review 必3-②):选定稿尾句可挂 ~25 词 track 钩子,复用本 statement
  末句框架("deployment-time alignment and safety problem"),不新增段落预算。
- **§2**:上表 (b) 作为 §2 新 paragraph 插入,置于现有 "Causal premise" 前后皆可;与
  editing/mechanism/fix/methodology 四线并列,构成第五线 = alignment 立界。
- **OpenReview 关键词栏**:mechanistic-interpretability 仅在表单关键词勾选,**不入正文/statement**。