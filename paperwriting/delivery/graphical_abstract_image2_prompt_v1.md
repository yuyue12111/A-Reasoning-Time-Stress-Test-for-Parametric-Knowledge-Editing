# Graphical abstract · image2 prompt set v1

Built-in `imagegen` mode. The final image was produced by one generation pass and one
targeted correction pass.

## Pass 1 · generation

```text
Use case: scientific-educational / infographic-diagram
Asset type: premium article graphical abstract and paper hero figure for an AAAI research paper
Primary request: Create a sophisticated, instantly understandable 16:9 landscape scientific infographic showing that a parametric knowledge edit can pass direct-answer validation but lose control after reasoning, and that a bounded training-free intervention inside the think span provides a chain-local control point. This is an evaluation/stress-test paper first, not a generic three-step product pipeline.

GLOBAL VISUAL LANGUAGE — establish this before composing anything and obey it everywhere:
• visual tokens are flat SQUARES;
• audio tokens are flat CIRCLES;
• text tokens and answer values are horizontal PILL-SHAPED CAPSULES;
• metadata, conditions, checkpoints, and hypotheses are DIAMONDS.
Never reassign these shapes. The narrative is text-model focused, so capsules and diamonds should dominate; do not invent multimodal content merely to use every shape.

COLOR SEMANTICS — lock each color to one meaning:
• emerald green #16846B ONLY for validated pass states and correct/new-value outcomes;
• coral red #E76452 ONLY for failure, reversion, or the old answer resurfacing;
• amber #E3A83F ONLY for the active think-span suppression intervention;
• deep navy #173F5F for neutral model structure, connectors, and headings;
• warm gray for controls and caveats;
• pale peach #F7D7C4 is the mood/background of the conventional low-cost input/direct-validation side;
• pale powder blue #CFE7F4 is the mood/background of the bounded controlled-output side;
• warm ivory paper background elsewhere.
No color may carry two meanings.

COMPOSITION — continuous left-to-right story, not three equal cards:
• Left region about 23% width: conventional direct-answer validation.
• Center region about 49% width and visibly dominant BECAUSE the reasoning-time paired stress test is the paper’s core contribution.
• Right region about 28% width: bounded chain-local control.
Use generous whitespace, precise alignment, elegant thin arrows, editorial hierarchy, and one strong visual flow.

LEFT — direct validation:
Show one abstract edited-model stack feeding a short text-token path. A green capsule labeled exactly “NEW VALUE” reaches a green seal labeled exactly “PASS”. A metadata diamond marks “B₀”. Heading exactly: “EDIT PASSES AT B₀”. The region should feel simple, inexpensive, and deceptively reassuring.

CENTER — the hidden reasoning-time failure, largest visual area:
At a single metadata diamond labeled exactly “SAME EDIT”, fork the same edited model into two paired lanes.
Top lane: the short B₀ path ends in the green “NEW VALUE”.
Bottom lane: a longer native reasoning chain labeled exactly “NATIVE CHAIN · B₃”, made of many navy text-token capsules. Midway, a coral capsule labeled exactly “OLD VALUE” visibly re-enters and bends the path toward a coral final answer. Make the fork and paired comparison unmistakable.
Use two compact diamond data badges, rendered verbatim:
“QWEN-32B · ΔES −10.6 pp”
“LLAMA-70B · ΔES −10.7 pp”
Add one prominent coral callout rendered verbatim: “OLD ANSWER RESURFACES · 19.3%”.
Below the chain, show two small observational evidence diamonds flowing into a third hypothesis diamond, without claiming mediation. Render exactly:
“CLOZE SIGNAL DETECTABLE”
“VISIBLE IN-CHAIN ROUTES”
“CHAIN-ROUTING HYPOTHESIS”
The first two are observations; the last is visually marked as a hypothesis, not a proven mechanism.

RIGHT — bounded training-free control:
Repeat the long B₃ chain, but place an amber gate ONLY around the coral old-answer first-token capsules inside the think span. The answer-stage path visibly bypasses this gate. Label exactly:
“TRAINING-FREE · THINK-SPAN ONLY”
“ANSWER LOGITS UNTOUCHED”
Do not depict complete prevention: allow a small faint coral remainder, while the main final capsule is green “NEW VALUE”. Show the result as a large clean metric rendered verbatim: “RESURFACING 19.3% → 8.5%”. End with a navy metadata diamond labeled exactly “CHAIN-LOCAL CONTROL POINT”. The visual verb is “offsets”, not “eliminates” or “repairs”.

TITLE AND SUBTITLE — exact text, centered across the top, two clean lines:
“DIRECT-ANSWER SUCCESS IS NOT ENOUGH”
“REASONING-TIME STRESS TEST FOR PARAMETRIC KNOWLEDGE EDITING”

STYLE/MEDIUM: high-end flat vector editorial science graphic, Nature/AAAI graphical-abstract quality, crisp sans-serif typography, sophisticated Swiss-grid discipline, fine circuit-like linework, subtle screen-printed paper grain only, balanced negative space, polished enough to feel fancy without looking commercial. All text must be large, readable, correctly spelled, and rendered exactly once; no filler text and no extra labels.

THREE-SECOND EVALUATION STANDARD: At thumbnail size, a reviewer must understand PASS at direct answer → the SAME EDIT fails after a native reasoning chain because the OLD VALUE resurfaces → think-span-only suppression lowers resurfacing while answer logits remain untouched. The evaluation-gap story must be the first visual, with diagnosis and intervention clearly secondary.

Avoid: gradients of any kind; 3D; glossy highlights; glassmorphism; neon colors; robot heads or humanoid AI icons; brains; magic wands; shields; locks; commercial logos; brand marks; stock-photo style; poster hype; equal-width columns; dashboard cards; dense paragraphs; tiny illegible text; arbitrary icons; decorative circuitry that obscures the flow; complete-fix claims; “edit erased”, “intact”, “mediation”, “prevents”, “eliminates”, “repairs”; watermarks or signatures.
```

## Pass 2 · targeted correction

```text
Edit the immediately preceding generated infographic. Preserve its overall 16:9 composition, title, typography, left/center/right proportions, factual numbers, main flow, palette, elegant flat editorial style, spacing, and all already-correct text. Make ONLY the following targeted corrections:

1. Enforce the global shape vocabulary with zero exceptions:
• visual token = square;
• audio token = circle;
• text token or answer value = pill-shaped capsule;
• metadata / condition / checkpoint / hypothesis = diamond.
This paper is text-only, so outside the tiny legend there should be NO visual-token squares and NO audio-token circles.

2. Replace every small navy square currently used in the B₀ (DIRECT) token lane with navy pill-shaped capsules. All native-chain tokens must remain pill capsules.

3. Replace the 3×3 solid-square block in the left panel with a neutral thin-outline layered module labeled exactly “EDITED MODEL”. It is a model container, not a token; do not use a square or circle token glyph for it.

4. Replace the green circular/wavy PASS seal with a green pill-shaped capsule labeled exactly “PASS”. Do not use a circle for PASS.

5. Correct and simplify the tiny bottom legend. It must show exactly four shape entries and no color-swatch legend:
• a navy square labeled “VISUAL TOKEN”
• a navy circle labeled “AUDIO TOKEN”
• an outlined pill capsule labeled “TEXT / ANSWER TOKEN”
• an outlined diamond labeled “METADATA / CONDITION / HYPOTHESIS”
Do not show squares or circles anywhere else.

6. Make the two observational evidence diamonds independent, not sequential. Change the first label to exactly “EDITED ASSOCIATION DETECTABLE”. Keep the second exactly “VISIBLE IN-CHAIN ROUTES”. From each, draw a separate THIN DASHED NAVY line converging on the diamond “CHAIN-ROUTING HYPOTHESIS”. Use a dashed warm-gray or navy outline for the hypothesis diamond. Do not use coral red on the hypothesis or on the words “HYPOTHESIS (NOT PROVEN)”; coral is reserved only for actual failure/reversion/OLD VALUE.

7. Change “ANSWER LOGITS UNTOUCHED” from amber to deep navy. Amber must appear only on the active think-span gate/intervention. Keep the gate amber.

8. Make the pale peach and pale powder-blue regions perfectly flat fills with no gradients. Preserve only very subtle uniform paper grain over the whole canvas.

9. Preserve verbatim and correctly spelled: “DIRECT-ANSWER SUCCESS IS NOT ENOUGH”; “REASONING-TIME STRESS TEST FOR PARAMETRIC KNOWLEDGE EDITING”; “EDIT PASSES AT B₀”; “SAME EDIT”; “NATIVE CHAIN · B₃”; “NEW VALUE”; “OLD VALUE”; “QWEN-32B · ΔES −10.6 pp”; “LLAMA-70B · ΔES −10.7 pp”; “OLD ANSWER RESURFACES · 19.3%”; “TRAINING-FREE · THINK-SPAN ONLY”; “ANSWER LOGITS UNTOUCHED”; “RESURFACING 19.3% → 8.5%”; “CHAIN-LOCAL CONTROL POINT”.

10. Preserve the three-second story: direct PASS → same edit fails after native reasoning → think-span-only suppression reduces resurfacing with answer logits untouched. Do not add new text, new numbers, logos, robots, brains, gradients, 3D, glow, or complete-fix claims.
```
