% =====================================================================
% AAAI-27 「越想越退 / Thinking Undoes Editing」
% Stitched draft (Abstract + §1–§7). Single data source: paper/results.json.
% All metrics = de-contaminated generative scoring (word-boundary), ROME×CounterFact, n=200, greedy.
% Honesty red lines enforced throughout (see redline_violations / todos).
% =====================================================================

% ====================== ABSTRACT (3 variants; capability-emergent head) ======================
% Choose ONE at submission; trim selected to exactly ~150 words.

% ---- VARIANT A — phenomenon-forward (~152 words) ----
\textbf{Abstract (A).}
Parametric knowledge editing (ROME/MEMIT) is typically scored at \emph{zero} thinking. We show that on native R1-style \emph{reasoning} models, edits are systematically eroded as the chain-of-thought unfolds, and---our central finding---this erosion \emph{emerges with capability}: across R1-Distill-Qwen-\{7,14,32\}B on CounterFact, the thinking-induced drop in edit success (ES) is not significant at 7B but reaches $-10.6$\,pp at 32B (significant), with the old answer reappearing in $\sim$55\% of chains and reverting $\sim$19\% of zero-thought successes to the pre-edit answer at the largest scale. A logit-lens analysis indicates reversion is \emph{not} erasure---the edit stays intact at the cloze position (100\% in reverted cases) while the old fact remains encoded mid-network; the chain re-derives it. We then give a training-free, chain-level fix that halves answer reversion ($0.193\!\to\!0.085$) without hurting locality. We report on native R1 only and adopt a word-boundary leakage metric; scaling is a three-point trend, not a smooth law.

% ---- VARIANT B — mechanism-and-fix-forward (~150 words) ----
\textbf{Abstract (B).}
We report a \emph{capability-emergent} failure of knowledge editing: parametric edits (ROME) that succeed under zero thinking are increasingly undone as a reasoning model thinks longer, and the effect grows with model scale. On native R1-Distill-Qwen-\{7,14,32\}B / CounterFact, the thinking-induced edit-success drop is non-significant at 7B but significant ($-10.6$\,pp) at 32B; chains re-surface the old fact in 33.5\%$\to$54.5\% of cases and revert 8\%$\to$19.3\% of successes as capability rises. Mechanistically (logit-lens), the edit is never erased---it stays installed at the cloze position while the suppressed fact persists in mid-layers---so longer reasoning \emph{re-derives} the old answer rather than overwriting the edit. Exploiting this, a training-free intervention that suppresses the edited fact \emph{only within the chain} (not the answer) cuts reversion $0.193\!\to\!0.085$ and removes the thinking tax, while preserving locality ($0.958\!\to\!0.964$); since touching only the chain fixes the answer, it causally confirms chain-internal re-derivation.

% ---- VARIANT C — eval-caution + capability (~151 words) ----
\textbf{Abstract (C).}
Knowledge edits are usually validated at zero thinking, but reasoning models think before answering. We find that test-time reasoning systematically erodes parametric edits, and that this erosion is \emph{capability-emergent}: on R1-Distill-Qwen-\{7,14,32\}B / CounterFact (ROME, $n{=}200$, word-boundary scoring), the thinking-induced edit-success drop rises from non-significant at 7B to a significant $-10.6$\,pp at 32B, while old-answer chain re-emergence climbs to $\sim$55\% and final reversion to $\sim$19\%. A logit-lens study shows the edit remains intact at the cloze position even when the answer reverts---the old fact is re-derived in the chain, not erased from weights. A training-free, chain-only suppression then halves reversion and neutralizes the thinking tax without harming locality, and---by intervening only on the chain---causally pins reversion to chain-internal re-derivation. We also show substring/alias leakage scoring inflates such metrics $\sim$2$\times$. Findings are on native R1 models; scaling is a monotone trend, not a smooth law.


% ============================== §1 INTRODUCTION ==============================
\section{Introduction}
\label{sec:intro}

Parametric knowledge editing---ROME, MEMIT, AlphaEdit and their descendants---promises to insert, update, or correct a fact directly in a model's weights without retraining. Its success is almost universally measured under a \emph{zero-thinking} protocol: the edited fact is queried directly, and edit success (ES) is read off the immediate next-token prediction or a short greedy continuation. Under this protocol, a single ROME edit on \mbox{R1-Distill-Qwen-32B} succeeds on $59.5\%$ of CounterFact cases.\footnote{Generative-scoring ES with word-boundary matching, $n{=}200$; see \S\ref{sec:setup}. We deliberately separate this from logit-side \texttt{rewrite\_acc}, which is not comparable.} But the models that most need reliable editing are increasingly \emph{reasoning} models that, by default, emit a long chain-of-thought (CoT) before answering. The zero-thinking number says nothing about what the edit is worth once the model is allowed to think.

\paragraph{Thinking erodes edits, and the erosion is capability-emergent.}
When we let the same edited model reason---scaling a natural CoT budget from $B_0$ (no thinking) to $B_3$---edits are systematically pushed back toward the pre-edit answer. On 32B, ES falls from $59.5\%$ at $B_0$ to $49.5\%$ at $B_3$, a drop of $10.6$pp (95\% CI $[3.0, 18.2]$, significant); the original answer re-surfaces somewhere in the reasoning chain in $54.5\%$ of cases (chain leak rate, CLR), and in $19.3\%$ of cases the chain ultimately overturns a zero-thinking success back to the old answer (reversion rate, RR). Crucially, this is not a fixed property of editing: it \emph{emerges with model capability}. On 7B the thinking-induced ES drop is $-3.0$pp (CI $[-11.0, 5.0]$, not significant---thinking is, if anything, mildly helpful), on 14B it is $4.0$pp (CI $[-3.0, 11.0]$, n.s.), and only on 32B does it become both large and significant. CLR rises monotonically across the three sizes ($0.335 \to 0.475 \to 0.545$) and RR likewise ($0.080 \to 0.162 \to 0.193$). Notably, ES@$B_0$ \emph{rises} with capability while ES@$B_3$ \emph{falls}---stronger models install edits better at zero thinking yet pay a larger ``thinking tax,'' so the gap widens precisely as the model gets better. A zero-thinking evaluation does not merely miss this effect; it reports the trend backwards.

\paragraph{The mechanism: reasoning bypasses an edit that is still intact.}
Why does thinking undo an edit? A natural hypothesis is that long generation erases or overwrites the edited weights. Logit-lens analysis on 32B rules this out. On reverted cases, the edit is still fully installed at the editing site: probed at the cloze position, the model predicts the new value in $100\%$ of reverted cases, and the edited fact wins at the top layer. Yet the \emph{old} fact remains encoded in the network's mid-stack: the per-layer new-minus-old gap turns negative around layers 8--12 (the edit layer is 12) before recovering at the top. Reversion is therefore not erasure. The edit sits intact in the weights; the reasoning chain simply routes around it---re-deriving the old fact from collateral, unedited knowledge mid-stream---and the final answer follows the chain rather than the edited site.

\paragraph{A chain-only causal fix.}
This mechanism is directly actionable and, in turn, lets us test it causally. If reversion is driven by the chain re-deriving the old fact, then suppressing the old-answer tokens \emph{within the chain alone}---never touching the answer span---should both reduce reversion and serve as a causal probe. It does. A training-free intervention that suppresses the edited fact's old-value tokens in the think segment ($\text{scope}{=}\texttt{think}$, $\alpha{=}8$) on 32B cuts RR from $0.193$ to $0.085$, raises ES@$B_3$ from $0.495$ to $0.631$, turns the thinking-induced ES drop from $+0.106$ to $-0.035$ (i.e.\ removes the thinking tax), and leaves locality essentially unchanged (Loc $0.958 \to 0.964$). Because we intervene only on the chain yet the \emph{answer} improves, this is causal evidence that in-chain re-derivation, not weight erasure, drives the reversion.\footnote{We are careful about circularity: $\text{scope}{=}\texttt{think}$ directly suppresses the CoT tokens that CLR counts, so we do not treat $\Delta$CLR as primary evidence; our load-bearing effects are $\Delta$RR and $\Delta$ES, both measured on the untouched answer span. See \S\ref{sec:rq3}.}

\paragraph{Honest positioning.}
We do not claim to be the first to observe any of the three ingredients in isolation. That parametric edits fail under realistic, non-teacher-forced inference---and that teacher-forced evaluation overstates editing---has been shown by \citet{he2025benchmarking} (SCR/ReCoE) and, for multi-step reasoning, by \citet{baser2025thinkeval} (ThinkEval). That edited knowledge is ``superficial'' and the original fact remains encoded rather than erased was demonstrated by \citet{xie2025superficial} (Superficial Editing). And training-free decoding-time correction of stale answers was given by \citet{sun2024disco} (DISCO). Our contribution is not the existence of these phenomena but a specific, previously unreported synthesis: that edit erosion is \emph{capability-emergent}; that the mechanism manifests \emph{dynamically inside a native R1 reasoning chain} (intact at the cloze, bypassed in the chain) rather than under crafted static prompts; that a \emph{chain-only} intervention both fixes the answer and causally isolates the cause (versus answer-level decoding contrast in DISCO); and that the CoT-leakage measurement itself must use word-boundary matching.

\paragraph{Contributions.}
\begin{enumerate}
  \item \textbf{Capability-emergent erosion (headliner).} We show that test-time reasoning erodes knowledge edits, and that this erosion \emph{emerges with model capability}: across R1-Distill-Qwen \{7B, 14B, 32B\}, the thinking-induced ES drop goes from non-significant ($-0.030$) to significant ($+0.106$), with CLR and RR rising monotonically. Zero-thinking evaluation entirely misses---and inverts---this trend. \emph{(We report a monotone three-point trend, not a smooth scaling law: the RR confidence intervals overlap pairwise and only the 32B ES drop is significant.)}
  \item \textbf{Chain-only causal mechanism + fix.} A training-free in-chain suppression of old-fact tokens removes the thinking tax (ES drop $0.106 \to -0.035$) and halves reversion (RR $0.193 \to 0.085$) without harming locality. Because only the chain is touched while the answer improves, this is a \emph{causal} test that in-chain re-derivation---not weight erasure---drives reversion, distinguishing it from answer-level corrections.
  \item \textbf{Dynamic non-erasure inside native CoT.} Via logit-lens we show the edit is intact at the cloze position ($100\%$ installed on reverted cases) while the old fact stays encoded mid-stack (negative new$-$old gap at layers 8--12); reasoning routes around an intact edit, and the answer follows the chain.
  \item \textbf{A measurement caution.} Substring/alias matching inflates CoT-leakage estimates by roughly $2\times$; we adopt and recommend a word-boundary criterion for generative editing evaluation.
\end{enumerate}

\noindent Figure~\ref{fig:capability} previews the headline result: across the three model sizes, the thinking-induced ES drop, CLR, and RR all trend upward---editing gets more fragile, not more robust, as models reason better.


% ============================== §2 RELATED WORK ==============================
\section{Related Work}
\label{sec:related}

Our work sits at the intersection of \emph{parametric knowledge editing}, \emph{test-time reasoning}, and \emph{evaluation methodology}. We organize prior art into four threads and, for each, state explicitly what is already established and what remains our contribution. The space is crowded; we therefore make our boundaries precise rather than claim priority.

\paragraph{Editing fails under realistic reasoning (phenomenon).}
A growing body of work shows that locate-then-edit methods (ROME~\citep{meng2022rome}, MEMIT~\citep{meng2023memit}, AlphaEdit~\citep{fang2024alphaedit}), while accurate under teacher-forced cloze probes, degrade once the model is allowed to reason autoregressively or hop across facts. \citet{he2025benchmarking} (SCR/ReCoE) demonstrate that under realistic, non-teacher-forced generation parametric edits collapse and that in-context retrieval outperforms them, concluding that teacher-forcing systematically \emph{over-states} editing success. \citet{baser2025thinkeval} (ThinkEval) construct thought-based knowledge graphs to quantify indirect leakage of stale facts across multi-step reasoning. Multi-hop benchmarks (MQuAKE~\citep{zhong2023mquake}) similarly expose edits that propagate poorly through reasoning chains. We adopt this thread's central finding---that real reasoning erodes edits and that cloze metrics overstate retention---as our \emph{premise}, not our contribution, and we cite it as such.
\textit{Our boundary.} Unlike SCR/ReCoE (which abandons parametric editing for retrieval) and ThinkEval (which uses an externally constructed KG rather than a native reasoning model), we study \emph{native R1-distilled reasoning models} along a continuous \emph{thinking-budget} axis ($B_0$--$B_4$), and we report a property none of these works isolate: erosion is \emph{capability-emergent}. The thinking-induced drop in edit success (ES) is statistically non-significant at 7B ($-0.030$, CI $[-0.110, 0.050]$) and 14B ($0.040$, CI $[-0.030, 0.110]$) but reaches $0.106$ (CI $[0.030, 0.182]$, significant) at 32B; over the same models the old answer re-surfaces in a rising fraction of chains (CLR $0.335\!\to\!0.475\!\to\!0.545$) and ultimately reverts $\sim$19\% of zero-thought successes at 32B (RR $0.193$). We present these three points as a \emph{monotone trend with size}, not a smooth scaling law---the RR confidence intervals overlap pairwise and only the 32B ES drop is significant (Section~\ref{sec:rq1}).

\paragraph{Edits are masked, not erased (mechanism).}
Recent mechanistic work argues that editing is \emph{superficial}: the original knowledge is not overwritten but remains encoded elsewhere in the network. \citet{xie2025superficial} (Superficial Editing) show via residual-stream and attention-head / left-singular-vector analysis that standard edited models still encode the pre-edit fact, exposable through crafted prompts. A 2026 cluster on non-erasure reinforces this view, while KELE~\citep{xu2024kele} conversely argues residual knowledge should be actively erased.
\textit{Our boundary.} We do not claim to be first to observe non-erasure---Superficial Editing establishes the core ``encoded-elsewhere'' phenomenon. Our contribution is to show \emph{how} it surfaces in a native reasoning model: via logit-lens on 32B, the edit is \emph{fully intact at the cloze position} in reversion cases (100\% still predict the new value at the top layer), yet a layer-wise gap between new and old logits turns \emph{negative} in the network's mid-stack (layers 8--12, around edit layer 12), indicating the displaced fact remains mid-layer encoded. The reversion is therefore not the chain \emph{erasing} the edit weights but the reasoning chain re-deriving the old fact in-chain and the final answer following the chain---a dynamic, CoT-internal manifestation of non-erasure that crafted static prompts do not capture, and which we causally confirm in Section~\ref{sec:rq3}.

\paragraph{Training-free correction of stale answers (fix).}
Decoding-time and activation-level interventions can steer models away from outdated knowledge without retraining. DISCO~\citep{sun2024disco} (Outdated-Issue-Aware Decoding) contrasts edited- and original-model distributions and amplifies the edited token, cutting outdated zsRE answers to $5.78\%$. Thinking-Intervention and SALT operate within the think segment of reasoning models, and ITI~\citep{li2023iti}, DoLa~\citep{chuang2024dola}, and ParamMute suppress parametric knowledge at inference.
\textit{Our boundary.} DISCO and related decoders intervene at the \emph{answer/output} level (global logit contrast); we instead suppress the edited-fact tokens \emph{only inside the reasoning chain}. This serves a dual purpose. As a fix it roughly halves answer reversion (RR $0.193\!\to\!0.085$), restores edit success at full budget (ES@$B_3$ $0.495\!\to\!0.631$), removes the thinking tax (ES drop $0.106\!\to\!-0.035$), and does not hurt locality (Loc $0.958\!\to\!0.964$). As a causal probe, intervening on the chain alone yet improving the \emph{answer} establishes that in-chain re-derivation drives reversion---a chain-only causal claim DISCO's answer-level design cannot make. We use the edited value itself for suppression, which is legitimate in the editing setting (it is the same target ROME uses to compute the update) and applies only to edited queries. We are careful that the CLR change is partly tautological---$\text{scope}{=}\texttt{think}$ suppresses exactly the chain content we score for old-fact leakage---so our primary evidence rests on $\Delta$RR and $\Delta$ES, which are measured on the answer and are not directly suppressed; the residual CLR ($0.263$) reflects a paraphrase bypass [pending: v2 sequence-level ablation].

\paragraph{Leakage metrics and evaluation methodology.}
A parallel methodological line shows that substring/alias-based matching inflates editing and leakage scores: Mirage/QAEdit~\citep{yao2025mirage} and principled-evaluation and edit-locality critiques document spurious matches, though primarily in non-CoT settings.
\textit{Our boundary.} We extend this concern to CoT leakage: a word-boundary scoring criterion (rejecting sub-token and $<$4-character alias matches) is required to avoid roughly doubling apparent leakage in reasoning traces, and we quantify the inflation ($\sim$2$\times$) directly. All numbers in this paper use the de-contaminated word-boundary scorer and are never mixed with EasyEdit's logit-side \texttt{rewrite\_acc}.

\paragraph{Causal premise.}
Our chain-only intervention builds on evidence that reasoning chains causally shape final answers in R1-distilled models~\citep{anon2025fromreasoning} (From Reasoning to Answer), which we take as the causal prerequisite for attributing reversion to in-chain re-derivation.

\paragraph{Summary of distinctions.}
In sum, the phenomenon (SCR/ReCoE, ThinkEval), the masking-not-erasing mechanism (Superficial Editing), the training-free fix (DISCO), and the metric-inflation caution (Mirage) each have published precedents that we credit explicitly. Our distinct contributions are their \emph{conjunction under a new lens}: capability-emergent erosion across model scale, a chain-only causal intervention, a native R1 + thinking-budget axis, and a CoT-aware word-boundary leakage metric.


% ============================== §3 SETUP AND METHODS ==============================
\section{Setup and Methods}
\label{sec:setup}

\subsection{Models and Editing Backbone}
We study \emph{native} R1-style reasoning models that emit an explicit chain-of-thought delimited by atomic \verb|<think>|/\verb|</think>| tokens before answering. Our main capability axis is the \textsc{R1-Distill-Qwen} family at 7B, 14B, and 32B, with \textsc{R1-Distill-Llama} (8B/70B) reserved as a cross-family check [pending]. We note up front that the 7B distill is specialized from a \emph{math} base (Qwen2.5-Math); a base probe confirms the unedited 7B already knows the target facts at $0.59$ recall, so its behavior reflects a math-specialization confound rather than a pure knowledge bottleneck (discussed in \S\ref{sec:limitations}). For this reason 7B$\to$14B mixes scale with specialization, and we treat the three-point trend as a \emph{capability contrast}, never a smooth scaling law.

Edits are applied with \textbf{ROME} as our primary editor on \textbf{CounterFact}; MEMIT is used only for early ablation. We deliberately \emph{keep} parametric editing rather than replacing it with retrieval, which lets us ask whether reasoning erodes an edit that is provably installed (\S\ref{sec:rq2}). The edit layer and locality threshold are selected on the \emph{generative} $B_0$ efficacy (not the editor's logit-level \texttt{rewrite\_acc}); on the 7B/Math base this selects an early-middle layer under a $\mathrm{Loc}\!\ge\!0.85$ floor.

\subsection{Single-Edit Protocol}
Each test fact is evaluated under a strict single-edit protocol: (i)~install one edit $(s,r,o_{\mathrm{old}}\!\to\!o_{\mathrm{new}})$; (ii)~generate at \emph{every} thinking budget while the edit is live; (iii)~restore the base weights before the next fact. Editing and restoring one request at a time eliminates cross-edit accumulation and isolates the effect of test-time reasoning on a clean, freshly installed edit.

A subtle but decisive implementation point: with EasyEdit, ROME/MEMIT must be invoked with \texttt{sequential\_edit=True}. Under \texttt{sequential\_edit=False} the library copies the original weights back \emph{before} \texttt{edit()} returns, so all subsequent generation silently runs on the \emph{unedited} base model (we observed byte-identical outputs across nominally different edit layers). With \texttt{sequential\_edit=True} the edit persists through generation and is undone by our own per-fact \texttt{finally:\,restore} hook, preserving the single-edit semantics.

\subsection{Thinking-Budget Axis ($B_0$--$B_4$)}
We expose test-time compute as a five-point budget axis applied at decode time. $B_0$ is \emph{ZeroThink}: an empty, immediately closed thought block (verbatim reproduction of the ZeroThink template of Jiang et al.~2025, as used by R-TOFU). $B_1$/$B_2$/$B_3$ generalize the \emph{LessThink} idea into a token-budget truncation of the natural chain, with caps of $256$/$1024$/$8192$ thinking tokens; for CounterFact-style facts the chain is typically far shorter than $8192$, so $B_3$ acts as an effective ``natural length.'' $B_4$ additionally forces continuation in the spirit of budget-forcing (s1) by suppressing early stops. We generate greedily for the main results; a $0.6\times3$ sampling arm is used for robustness. We report the zero-thinking point ($B_0$) and the natural-length point ($B_3$) as the two anchors of the ``thinking tax.''

\subsection{Generative Scoring (ES / RR / CLR / Loc)}
We score on \emph{generated} text, not teacher-forced logits; this is distinct from the editor's \texttt{rewrite\_acc} and the two are never mixed. For each fact at each budget we measure:
\begin{itemize}
  \item \textbf{Edit Success (ES)} --- whether the generated answer states the edited value $o_{\mathrm{new}}$.
  \item \textbf{Reversion Rate (RR)} --- the fraction of facts that succeed at $B_0$ but are pushed back to the \emph{old} answer $o_{\mathrm{old}}$ at $B_3$ (an answer-level reversal).
  \item \textbf{Chain Leak Rate (CLR)} --- the fraction of facts whose reasoning chain re-surfaces $o_{\mathrm{old}}$ at least once (a chain-level leak; need not change the final answer).
  \item \textbf{Locality (Loc)} --- preservation of unrelated facts.
\end{itemize}
The \emph{thinking tax} is the ES drop $\mathrm{ES}@B_0 - \mathrm{ES}@B_3$, and is our primary capability-emergent quantity.

\subsection{Word-Boundary Scoring (Methodological Correction)}
\label{sec:wordbound}
A naive substring match for $o_{\mathrm{old}}$ in generated text, combined with an alias list, systematically inflates leakage. Short ISO/language aliases (e.g.\ \texttt{W}=Vienna, \texttt{in}=India, \texttt{it}=Italian, \texttt{es}=Spain) match inside ordinary words and produce spurious hits. We therefore score with \textbf{word-boundary} matching and drop aliases shorter than four characters. Switching from substring to word-boundary scoring lowers the leakage metrics by roughly $2\times$, which we report as a cautionary finding for generative edit evaluation: substring/alias matching can over-state CoT leakage by about a factor of two (\S\ref{sec:rq1}). All numbers in this paper use the decontaminated word-boundary scorer; pre-decontamination values are not reported.

\subsection{Statistics}
Confidence intervals are $95\%$ percentile bootstrap over edited facts (resampling $n$ facts, $10{,}000$ resamples). Unless stated, $n=200$ per model. We flag an effect as significant only when its bootstrap CI excludes zero; in particular the ES drop is significant at 32B ($0.106$, CI $[0.030,0.182]$) but not at 7B or 14B, and the RR CIs overlap pairwise across model sizes --- hence we claim a \emph{monotone trend} across three capability points, not a smooth scaling law.


% ============================== §4 RQ1 — CAPABILITY-EMERGENT EROSION ==============================
\section{Editing Erosion is Capability-Emergent}
\label{sec:rq1}

\paragraph{Setup recap.} For each model we apply ROME to a single CounterFact edit, then generate under thinking budgets $B_0$ (no chain-of-thought) through $B_3$ with the edit held in place, and restore (single-edit protocol, \S\ref{sec:setup}). All scores are generation-side and use word-boundary contamination-free judging (\S\ref{sec:wordbound}; ROME$\times$CounterFact, greedy, $n{=}200$). We report three quantities at $B_3$: \emph{ES drop} ($\mathrm{ES}@B_0-\mathrm{ES}@B_3$, the ``thinking tax''), \emph{chain-leak rate} (CLR, fraction of chains in which the pre-edit answer resurfaces anywhere in the CoT), and \emph{reversion rate} (RR, fraction of edits that succeed at $B_0$ but are overturned to the old answer in the final answer at $B_3$).

\paragraph{Main finding: the thinking tax grows with capability.} Table~\ref{tab:capability} and Figure~\ref{fig:capability} show that as model scale increases across R1-Distill-Qwen-\{7B, 14B, 32B\}, test-time reasoning erodes edits more severely. The ES drop is $-0.030$ ($95\%$ CI $[-0.110, 0.050]$, n.s.) at 7B, $0.040$ ($[-0.030, 0.110]$, n.s.) at 14B, and $0.106$ ($[0.030, 0.182]$, \emph{significant}) at 32B---i.e.\ thinking is edit-neutral on the smallest model but costs $10.6$pp of edit success on the largest. The two companion leakage measures rise monotonically with scale: CLR climbs $0.335 \to 0.475 \to 0.545$ and RR climbs $0.080 \to 0.162 \to 0.193$. We read this as a single emergent phenomenon: stronger reasoners are \emph{more} prone to re-deriving the suppressed fact inside the chain and following it in the final answer.

\begin{table}[t]
\centering
\small
\begin{tabular}{lccccc}
\toprule
Model & ES@$B_0$ & ES@$B_3$ & ES drop & CLR & RR \\
\midrule
7B (Math) & 0.500 & 0.530 & $-0.030$\,\textsuperscript{n.s.} & 0.335 & 0.080 \\
14B       & 0.555 & 0.515 & \phantom{$-$}$0.040$\,\textsuperscript{n.s.} & 0.475 & 0.162 \\
32B       & 0.595 & 0.495 & \phantom{$-$}$\mathbf{0.106}$\,\textsuperscript{*} & 0.545 & 0.193 \\
\bottomrule
\end{tabular}
\caption{Capability-emergent erosion (ROME$\times$CounterFact, $n{=}200$, greedy, word-boundary scoring). ES drop $=\mathrm{ES}@B_0-\mathrm{ES}@B_3$; $^{*}$ bootstrap CI excludes zero (significant) only at 32B. A three-point monotone trend, not a smooth scaling law (RR CIs overlap pairwise).}
\label{tab:capability}
\end{table}

\paragraph{Decomposing the tax: ES@$B_0$ rises while ES@$B_3$ falls.} The ES drop grows with scale for two compounding reasons (Figure~\ref{fig:capability}, ES panel). Zero-thinking edit success \emph{improves} with capability ($\mathrm{ES}@B_0$: $0.500 \to 0.555 \to 0.595$)---larger models install edits more reliably at $B_0$. Yet edit success \emph{after} reasoning \emph{declines} with capability ($\mathrm{ES}@B_3$: $0.530 \to 0.515 \to 0.495$). The thinking tax is thus the widening scissor between a rising $B_0$ ceiling and a falling $B_3$ floor: capability helps install the edit but hurts its survival once the model is allowed to reason.

\paragraph{Honest scoping of the trend.} We do \emph{not} claim a smooth scaling law. The evidence is a three-point monotone \emph{trend}, not a pairwise-significant progression: the RR confidence intervals overlap pairwise ($[0.030,0.140]$, $[0.099,0.234]$, $[0.126,0.269]$), and the ES drop is statistically significant only at 32B. We report the direction and its consistency across all three metrics (ES drop, CLR, RR), not a fitted exponent. We also note RR $\approx 0.19$ at 32B and describe it as such; we do not round it past $0.20$.

\paragraph{The 7B confound.} R1-Distill-Qwen-7B is distilled from Qwen2.5-\emph{Math}-7B, a math-specialized base, so the 7B$\to$14B$\to$32B axis mixes scale with specialization rather than isolating scale. The flat-to-negative 7B ES drop is therefore not clean evidence of ``no erosion at small scale.'' Importantly, the 7B behavior is \emph{not} a pure knowledge bottleneck: a base-knowledge probe shows the 7B model knows the target facts at $0.59$ before editing, so its low post-edit ES reflects edit/reasoning interaction, not ignorance. Disentangling scale from specialization with a general-purpose 8B model and a second model family is left to extend the curve (see [pending] below).

\paragraph{Coverage and pending points.} The capability curve is currently anchored on three native R1-distilled reasoners. The following points, needed to make the trend cross-scale and cross-family, are \textbf{[pending]} and not yet run: R1-Distill-Qwen-1.5B (low end), R1-Distill-Llama-8B (general-purpose 8B to break the Math-specialization confound), and a 70B point (high end). We will add these to Figure~\ref{fig:capability} when results land; until then we present the 7B/14B/32B trend with the scoping caveats above.


% ============================== §5 RQ2 — MECHANISM ==============================
\section{Why Does Reasoning Undo the Edit? (Mechanism)}
\label{sec:rq2}

RQ1 establishes that test-time reasoning erodes edits and that the erosion is capability-emergent. A natural worry is that the long chain-of-thought (CoT) somehow \emph{destroys} the edited parameters---that decoding hundreds of tokens perturbs the model state and the ROME update decays. We show this is \emph{not} what happens. The edit remains fully installed; reasoning instead routes \emph{around} it, re-derives the old fact inside the chain, and the final answer follows the chain. All mechanism analysis is on the 32B model (the regime where the phenomenon is significant), over the reverted cases (ROME$\times$CounterFact, $n=200$, greedy).

\paragraph{The edit is intact, not erased (logit-lens at the cloze).}
For every reverted case---cases where the model answers the new (edited) value at zero budget $B_0$ but reverts to the old value after thinking at $B_3$---we re-probe the edited fact at the original cloze position (subject + relation prompt, no CoT) and read the top-of-stack logits. The edit is installed in \textbf{100\%} of reverted cases: the final-layer prediction at the cloze is still $o_{\mathrm{new}}$. The ROME weights are not perturbed by decoding; the reversion is therefore not a parameter-erasure effect. Whatever the chain does, it does so on a network that still ``knows'' the edited value when asked directly. This is the load-bearing observation of RQ2: the failure is a \emph{reasoning} failure, not a \emph{storage} failure.

\paragraph{The old fact is still encoded in the middle of the network.}
If the edit sits intact at the top but the model can still revert, the old fact must remain readable somewhere. We confirm this with a layer-wise logit-lens sweep. We define the per-layer \emph{gap} $g_\ell = \mathrm{logit}_\ell(o_{\mathrm{new}}) - \mathrm{logit}_\ell(o_{\mathrm{old}})$ at the cloze, decoded through the unembedding at each sampled layer $\ell$ (of $64$ total; edit applied at layer $12$). The gap is \emph{negative} in the early-middle band---$g_8 = -0.246$, $g_{12} = -0.351$ (Figure~\ref{fig:rq2})---meaning the old value $o_{\mathrm{old}}$ is favored at layers 8--12, right around the edit layer. The gap then climbs steadily and is strongly positive in the upper stack (peaking at $g_{56} = 17.8$ and remaining large at the final layer, $g_{64} = 11.6$), where the ROME edit dominates and produces the intact top-layer $o_{\mathrm{new}}$. So the network carries both readings simultaneously: a middle-layer trace of the original fact and a late, edit-installed trace of the new fact. The edit overwrites the surface readout but leaves an intact mid-network substrate from which the old fact can be reconstructed---which is exactly the substrate a multi-step chain can latch onto.

\paragraph{Mechanism: route around, re-derive in-chain, answer follows the chain.}
Putting the two together: the edit is installed (intact cloze) yet the old fact is still encoded mid-network, and during a long CoT the model retrieves and re-derives the old value through ordinary reasoning steps---bridging through related facts rather than reading the edited slot---and the final answer tracks the chain rather than the edited parameter. Reversion is thus \emph{reasoning bypassing a perfectly good edit}, not the chain wearing the edit away. We make this causal in RQ3 (\S\ref{sec:rq3}): suppressing the old-fact tokens \emph{only inside the chain} (never at the answer) halves final-answer reversion, which only makes sense if the in-chain re-derivation is what drives the answer back.

\paragraph{How chains revert: a behavioral taxonomy.}
To characterize the in-chain pathway we classify each reverted chain with a multi-judge panel into: \emph{recall} (the chain directly states the old fact as if retrieved), \emph{bridge} (the chain reaches the old fact by reasoning through a related/intermediate fact), and \emph{dismiss} (the chain encounters the edited value but explicitly rejects or argues against it). [pending: per-class counts to be filled from the judge-panel run; 32B chain classification table.] This taxonomy is descriptive and orthogonal to the logit-lens finding above; it documents the \emph{routes} the reasoning takes, all of which leave the cloze edit intact.

\paragraph{Relation to ``superficial editing.''}
That edits are superficial---installed at the surface while the original knowledge persists deeper in the network---is itself established. \citet{xie2025superficial} (Superficial Editing) show via residual-stream and attention-head analysis that standard edited models still encode the original knowledge, and \citet{he2025benchmarking} (SCR/ReCoE) show parametric edits collapse under realistic autoregressive decoding. We do \textbf{not} claim to be the first to find non-erasure. Our contribution is narrower and specific to reasoning: prior non-erasure evidence is \emph{static}, surfaced with crafted trigger prompts on standard models; ours arises \emph{dynamically inside a native R1 chain-of-thought}, we show the edit is simultaneously intact at the cloze (100\%) while the old fact re-emerges mid-stack, and we tie the reversion to the chain causally (\S\ref{sec:rq3}, chain-only intervention). The mechanism is the bridge between RQ1's capability-emergent erosion and RQ3's chain-level fix.

% Figure 2 (fig:rq2): per-layer logit-lens gap g_\ell at the cloze (32B, reverted cases),
% negative dip at layers 8-12 (old fact favored mid-network), rising to strongly positive
% in the upper stack (peak 17.8 at layer 56, 11.6 at layer 64). Annotate edit layer = 12, intact_pct = 100%.


% ============================== §6 RQ3 — CHAIN-LEVEL TRAINING-FREE FIX ==============================
\section{A Chain-Level, Training-Free Fix}
\label{sec:rq3}

Section~\ref{sec:rq2} located the failure mode: the edit is intact at the cloze site (top-layer prediction is $o_\text{new}$ in 100\% of the reverted cases), and the old fact is never removed from the network --- it remains encoded in the mid layers and is \emph{re-derived inside the reasoning chain}, after which the final answer follows the chain. This diagnosis prescribes the intervention point directly: do not touch the edited weights, do not touch the answer; instead suppress the re-emergence of the old fact \emph{where it re-emerges}, i.e.\ token-by-token inside the thinking chain.

\paragraph{Method.}
Given an edited model and a query whose target has been edited from $o_\text{old}$ to $o_\text{new}$, we tokenize $o_\text{old}$ and, at every decoding step that falls inside the \texttt{<think>}\ldots\texttt{</think>} span ($\textsc{scope}{=}\textsc{think}$), subtract a constant penalty $\alpha$ from the logits of those tokens before sampling. The post-think answer is decoded with the unmodified logits. The intervention is training-free, requires no extra forward passes, and is gated on edited queries only: the value $o_\text{old}$ is already known in any editing scenario (it is the same quantity ROME/MEMIT use to compute the update), so this introduces no information the editor did not already have. We report a single operating point, $\alpha{=}8$, $\textsc{scope}{=}\textsc{think}$, on R1-Distill-Qwen-32B, CounterFact, $n{=}200$, greedy decoding at the $B_3$ budget.

\paragraph{Results.}
Table~\ref{tab:rq3} contrasts the model with suppression off (the $B_3$ baseline of Section~\ref{sec:rq1}) versus on. Chain-level suppression \textbf{halves the final-answer reversion rate} (RR $0.193 \rightarrow 0.085$), \textbf{recovers thinking-budget edit success} (ES@$B_3$ $0.495 \rightarrow 0.631$, turning the $+0.106$ thinking tax into $-0.035$, i.e.\ ES@$B_3$ now slightly \emph{exceeds} ES@$B_0$), and \textbf{does not harm locality} (Loc $0.958 \rightarrow 0.964$). CLR drops from $0.545$ to $0.263$.

\begin{table}[t]
\centering
\small
\begin{tabular}{lccccc}
\toprule
& RR & ES@$B_3$ & ES drop & CLR & Loc \\
\midrule
Off (baseline) & 0.193 & 0.495 & \phantom{$-$}0.106 & 0.545 & 0.958 \\
On ($\alpha{=}8$) & \textbf{0.085} & \textbf{0.631} & $-$0.035 & 0.263 & \textbf{0.964} \\
\bottomrule
\end{tabular}
\caption{Chain-level $o_\text{old}$ suppression ($\textsc{scope}{=}\textsc{think}$) on R1-Distill-Qwen-32B, CounterFact, $n{=}200$, $B_3$. General-capability gate (GSM8K/MATH) \textbf{[pending]}.}
\label{tab:rq3}
\end{table}

\paragraph{Causal interpretation: intervening only on the chain.}
The intervention modifies \emph{only} the thinking-span logits; the post-think answer is decoded normally. That it nonetheless improves the final answer (RR halved, ES@$B_3$ recovered) closes the causal loop from Section~\ref{sec:rq2}: the answer reverts \emph{because} the old fact is re-derived in the chain, not because the edit was erased. This is the chain-only causal handle that distinguishes our diagnosis from a purely observational one.

\paragraph{On the partial circularity of $\Delta$CLR.}
We deliberately do \emph{not} lead with the CLR reduction. CLR measures whether $o_\text{old}$ surfaces \emph{in the chain}, and $\textsc{scope}{=}\textsc{think}$ suppresses exactly those chain tokens, so part of $\Delta$CLR is mechanical (the metric and the intervention act on the same span). Our load-bearing evidence is therefore $\Delta$RR and $\Delta$ES, which are measured on the \emph{answer} --- a span the intervention never touches --- and on which the improvement is genuinely earned. The residual CLR of $0.263$ (rather than $\approx 0$) is itself informative: it reflects a paraphrase bypass (the old fact re-stated via aliases the penalty does not cover), which we probe with a sequence-level variant in the ablations \textbf{[pending]}.

\paragraph{Relation to DISCO.}
The closest training-free decoding fix is DISCO~\citep{sun2024disco}, which contrasts the edited and original models' \emph{output} distributions to amplify the edited token. Our intervention differs in locus and granularity: it operates \emph{inside the reasoning chain at the token level} ($\textsc{scope}{=}\textsc{think}$), not on the answer-level distribution, and it is the act of intervening on the chain alone --- while the answer follows --- that doubles as the causal probe. We do not claim a stronger remediation than DISCO; we claim a different, chain-localized intervention that is coupled to, and validates, the re-derivation mechanism.

\paragraph{Scope and caveats.}
The fix is reported at one operating point on one model (32B), one editor (ROME) and one dataset (CounterFact). The general-capability gate (GSM8K/MATH, on vs.\ off) is \textbf{[pending]} and is required before claiming ``does not hurt general ability'' beyond the by-construction argument (the intervention fires only on edited queries, so off-target capability is untouched by design; the gate gives the worst-case upper bound). Robustness sweeps --- $\alpha$ sweep, $\textsc{scope}{=}\textsc{all}$, replication on 14B, and a sequence-level variant for the paraphrase bypass --- are \textbf{[pending]}.


% ============================== §7 LIMITATIONS AND DISCUSSION ==============================
\section{Limitations and Discussion}
\label{sec:limitations}

Our central claim is narrow and we state its boundaries explicitly. We report that the erosion of parametric knowledge edits under test-time reasoning is \emph{capability-emergent}---negligible at 7B and significant at 32B---and that a chain-level intervention undoes most of it. We do \emph{not} claim a scaling law, novelty of the phenomenon, novelty of the non-erasure mechanism, or a deployment-ready repair. This section makes those boundaries precise.

\paragraph{A trend across three sizes, not a scaling law.}
Our capability axis has only three points (R1-Distill-Qwen 7B/14B/32B) and we treat the upward pattern in edit erosion as a \emph{monotone trend}, not a fitted scaling law. The evidence is uneven across metrics: the ES drop $B_0\!\to\!B_3$ is $-0.030$ (7B), $0.040$ (14B), and $0.106$ (32B), but is statistically significant \emph{only} at 32B (95\% bootstrap CI $[0.030,0.182]$); the 7B and 14B drops have CIs spanning zero ($[-0.110,0.050]$ and $[-0.030,0.110]$). The reversion rate (RR) rises monotonically ($0.080\to0.162\to0.193$) but its bootstrap CIs overlap pairwise ($[0.030,0.140]$, $[0.099,0.234]$, $[0.126,0.269]$), so we do not assert pairwise separation. The chain-leak rate (CLR) shows the cleanest monotonicity ($0.335\to0.475\to0.545$). We therefore frame RQ1 as: erosion is absent in the weakest model and significant in the strongest, with intermediate behavior consistent with---but not proof of---a smooth curve. Establishing a genuine scaling relationship would require additional sizes and a second model family; we flag the cross-family Llama 8B/70B and Qwen 1.5B replication as future work [pending].

\paragraph{Effect magnitudes are modest.}
The strongest model reverts roughly one in five zero-thinking successes to the old answer ($\mathrm{RR}\approx0.19$); we do not round this up or describe it as exceeding $0.20$. Because the RR base is small, the ES recovery our fix produces, while substantial in relative terms, operates on a modest absolute footprint. We accordingly center our claims on RR, CLR, and the ES drop rather than on headline ES gains.

\paragraph{The $\Delta$CLR of our fix is partly circular.}
Our repair suppresses edited-fact tokens with scope restricted to the thinking chain ($\texttt{scope=think}$, $\alpha{=}8$). CLR is, by construction, measured \emph{inside} that same chain, so a reduction in CLR ($0.545\to0.263$) partly reflects directly suppressing what CLR counts. We therefore do not treat $\Delta$CLR as primary evidence for the fix. The load-bearing evidence is $\Delta$RR ($0.193\to0.085$) and $\Delta$ES@$B_3$ ($0.495\to0.631$), both measured on the \emph{final answer}, which we never intervene on directly---so improvement there cannot be explained by the suppression mechanically writing the metric. The residual CLR of $0.263$ is consistent with a paraphrase bypass (old facts re-surfacing via aliases the token suppressor does not cover); quantifying this with a sequence-level ablation is future work [pending].

\paragraph{The 7B endpoint confounds scale with specialization.}
R1-Distill-Qwen-7B is distilled from Qwen2.5-\emph{Math}-7B, a math-specialized base, so the 7B$\to$14B$\to$32B axis mixes a change in scale with a change in domain specialization. The absence of erosion at 7B is therefore not cleanly attributable to low capability alone. We do, however, rule out a trivial ``the small model never knew the fact'' explanation: a base-probe check shows the 7B model recalls the targeted facts at $0.59$, so its flat erosion is not a pure knowledge-availability artifact. Disentangling scale from specialization with a general-purpose 8B model is future work [pending].

\paragraph{Single dataset and single primary editor.}
All reported numbers are ROME $\times$ CounterFact, greedy decoding, $n{=}200$, scored under our debiased word-boundary protocol. MEMIT appears only in early exploratory data and AlphaEdit is not included in the headline results. Generalization across editors (MEMIT/AlphaEdit) and across datasets (e.g., zsRE, multi-hop MQuAKE) is not established here and is future work [pending]. Likewise, the cross-family and additional-size points (Qwen 1.5B, Llama 8B/70B) and the general-capability safety gate (GSM8K/MATH) are not yet available [pending]; the latter is required before we close RQ3.

\paragraph{The fix uses the old answer, and only by construction.}
Our repair suppresses tokens corresponding to the \emph{old} (pre-edit) value $o_{\text{old}}$. This is not extra supervision: in any editing scenario the old value is already known---ROME itself computes its update from precisely this knowledge---so conditioning the suppressor on $o_{\text{old}}$ is legitimate within the edit pipeline rather than an oracle leak. We position this as a property of the deployment setting, not a claim of unsupervised repair.

\paragraph{Deployment scope: the fix acts only on edited queries.}
The intervention is, by construction, gated to queries about edited facts; on all other inputs the model runs unmodified. This is why we expect general capability to be preserved on non-edit traffic essentially by design, and why we report a general-capability gate (GSM8K/MATH) as a worst-case \emph{upper} bound on collateral damage rather than the operating regime. We do not yet have the gate numbers [pending]; until they are in, our locality evidence (Loc $0.958\to0.964$ under the fix) is the only on-hand check that the intervention does not degrade unrelated edited-model behavior.

\paragraph{Mechanistic claims are scoped to logit-lens.}
Our non-erasure account rests on logit-lens evidence (32B): in reversion cases the edit is intact at the cloze probe ($100\%$ still predict the new value at the top layer), while the layer-wise gap turns negative around layers 8--12 (near edit layer 12), indicating the old fact remains encoded mid-network. We do not claim this exhausts the mechanism, and we are careful not to claim first discovery of non-erasure: superficial/non-erasure editing is established in prior work (Superficial Editing). Our distinct contribution is that non-erasure manifests \emph{dynamically inside native CoT} (rather than under crafted static prompts) and that the chain-only causal intervention shows the final answer follows the chain.

\paragraph{Positioning relative to prior work.}
The phenomenon of edits failing under realistic autoregressive/multi-hop reasoning (SCR/ReCoE; ThinkEval), the non-erasure mechanism (Superficial Editing), and training-free repair of reversion (DISCO) each have published precedent, and we do not claim priority over them. What is ours: (i) the \emph{capability-emergent} erosion curve; (ii) a \emph{chain-only} causal intervention (we perturb only the reasoning chain, not the answer level as DISCO does, and the answer improves---establishing chain-internal re-derivation as the driver of reversion); (iii) the native-R1 thinking-budget axis; and (iv) the word-boundary scoring correction, which shows substring/alias matching inflates CoT-leakage metrics by roughly $2\times$.