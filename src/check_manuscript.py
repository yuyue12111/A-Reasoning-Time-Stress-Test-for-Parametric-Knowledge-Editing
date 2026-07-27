#!/usr/bin/env python3
"""Fail-closed checks for the W2 manuscript surface.

The checker treats every numeric occurrence in authored Sections 3 and 4 as an
occurrence-level claim.  Each occurrence must have an inline ``% RJ:`` JSON
record containing a unique claim id, an RFC 6901 pointer into results.json, and
an enumerated formatter.  Targets are numeric scalars except for a narrow set
of exact frozen string records whose approved token positions are enumerated
below.  Other, not-yet-authored sections reject numeric tokens until their own
ledgers land.  Banned and stale language is checked across the whole visible
manuscript.  The frozen abstract is byte-authenticated after reversing the
single LaTeX escape ``\\% -> %`` and cross-checked against the combined body
ledger, with one explicit Section 5 debt for the frozen 8.5% value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAIN = REPO_ROOT / "paperwriting" / "manuscript" / "main.tex"
DEFAULT_RESULTS = REPO_ROOT / "paperwriting" / "results.json"
FROZEN_ABSTRACT = REPO_ROOT / "paperwriting" / "delivery" / "abstract_v8_candidate.txt"
TEMPLATE_DIR = REPO_ROOT / "paperwriting" / "AuthorKit27"

FROZEN_TITLE = (
    "Direct-Answer Edit Success Is Not Enough: A Reasoning-Time Stress Test "
    "for Parametric Knowledge Editing"
)
FROZEN_ABSTRACT_SHA256 = (
    "0c85a03e9cd288b45d6f23502caf17b74e84c28dee0f3a2e62f9202ec4b81e5f"
)
APPROVED_PREAMBLE_SHA256 = (
    "6d9e90c1d65f8dc77a054e9c01aa69bf42c6663cb535e8a1a31830bdcd041c88"
)
APPROVED_REFS_SHA256 = (
    "9148dfd515b5dfbefb3ae31dfcc7c023cbf0cfc43c82074d084c2b53fb5d1912"
)
APPROVED_SECTION_LEDGER_BINDINGS_SHA256 = {
    "Section 3": "4e35088e431538f3c46d158893aa4d01b58d901d2c370c7bf48b311a63d52698",
    "Section 4": "b43e9b0800a1ad992ef1981f6b2d3c86fade17f1cbc4020983b822609851b7ca",
    "Section 5": "142fdd3e7263f554b1a6beba02febaba595343401313dcec76d1c9bd7acb853a",
    "Section 1": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
    "Section 2": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
    "Section 6": "ec1920efdf517af8485204281892ad7ecee5ff46a64f203229ad679dfece08d0",
    "Section 7": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
    "Ethical Statement": "844a31a6de1b47c3477b8f944699df4cd6a7825d94da5221f5cf3878a6d0e9f4",
}
APPROVED_SECTION_VISIBLE_SHA256 = {
    "Section 3": "27172de6a8fbfa28d1d4d14e2b90d8a116c692313c85c913eec5d8336c25022e",
    "Section 4": "b4daa3d94d13898be4baf9b4b060dd14470f1aba7b180f121de99199ae2c50ae",
    "Section 5": "ffcd6569e88b6b0137a0a832e229fa20459404809a85f00cbeade250751202cf",
    "Section 1": "6d2b42ae10a692b7704d0ce84c0b1c177a3cd64a28b6dc7e68cece35be2421d2",
    "Section 2": "f724d58ed58fb90736b73ae9f87c82aaffe1e72d35db300078fd6d91459652a4",
    "Section 6": "61fa524c461d087166d03ca02aa8fb8e725090e81d6da69a98cbb12773613ba3",
    "Section 7": "6efab28353b94766eeacc7870bc37ef4a8373069f256b1ee0be048b77675827e",
    "Ethical Statement": "b9cbe903bb8bf10bab4bae62fe1b784125c2deaec42266281e76f3f8c0d9a243",
}
APPROVED_SECTION_SOURCE_SHA256 = {
    "Section 3": "1f9e61ae28390c36059db17f22d1cc317868204d75bba4a1c5faf192268070a4",
    "Section 4": "3b38f49e5961f70b6ddb774fba5069c3aa131f881c312eb82b5a60893f626b89",
    "Section 5": "c087e82d993793301b70e1d9a0581155db0ed9b18c84aa13ecaabb0c9dffa7a1",
    "Section 1": "02ba6030bd1aeff5114a87aa57e4050677d4fc814892003e796a15a0fd3d9477",
    "Section 2": "7a574ad49c2b8e9f83deb00d20d00883a5ef294d6119261f844253df9f9400d7",
    "Section 6": "e61fcd102d8427e7bbf2c6e6b6652b57ef22dfa1dfeb7e827c3548425295f345",
    "Section 7": "4c5b17b09842cc78cac227d4acb6265d131d9ed1b745b3058f1d3ddf8b7d1f3b",
    "Ethical Statement": "060beec82d7f76d5f81283a245f378dc133a6aae19fbd29f64a56baa14850a25",
}

# Every frozen-abstract number now has a same-display body RJ binding: the
# Section 5 arm-wise sentence retired the last debt when it bound 8.5% to the
# treated arm.  Re-adding an entry here would re-open a covered value.
PENDING_ABSTRACT_BODY_BINDINGS: dict[str, dict[str, str]] = {}

# Exact scalar paths must not accidentally approve a same-prefix sibling.
APPROVED_EXACT_POINTERS = frozenset(
    {
        "/capability/ci_level",
        "/metric_validation/n",
        "/metric_validation/n_attempted",
        "/metric_validation/n_rate_limited",
        "/rq2_taxonomy/p0_corrected_taxonomy/n",
        "/rq2_taxonomy/p0_corrected_taxonomy/n_unique_facts",
        "/rq2_taxonomy/p0_corrected_taxonomy/agreement/fleiss_kappa",
        "/rq2_logitlens/_authoritative_record/n",
        "/rq2_logitlens/_authoritative_record/edit_intact_at_cloze",
        "/rq2_taxonomy/p0_membership_reaudit/technical_audit/n_items",
        "/rq2_taxonomy/p0_membership_reaudit/membership_votes/majority_old_new_neither/0",
        "/rq2_taxonomy/p0_membership_reaudit/membership_votes/majority_old_new_neither/1",
        "/rq2_taxonomy/p0_membership_reaudit/membership_votes/majority_old_new_neither/2",
        "/rq2_taxonomy/p0_membership_reaudit/membership_votes/membership_fleiss_kappa",
        "/rq2_taxonomy/p0_corrected_taxonomy/dist/Bridge",
        "/rq2_taxonomy/p0_corrected_taxonomy/dist/Recall",
        "/rq2_taxonomy/p0_corrected_taxonomy/dist/Reflective-override",
        "/rq2_taxonomy/p0_corrected_taxonomy/dist/Associative",
        "/rq2_taxonomy/p0_corrected_taxonomy/pct/Bridge",
        "/rq2_taxonomy/p0_corrected_taxonomy/pct/Recall",
        "/rq2_taxonomy/p0_corrected_taxonomy/pct/Reflective-override",
        "/rq2_taxonomy/p0_corrected_taxonomy/pct/Associative",
        "/rq2_taxonomy/p0_corrected_taxonomy/agreement/unanimous_cases",
        "/rq2_taxonomy/p0_corrected_taxonomy/agreement/two_one_cases",
        "/rq2_taxonomy/p0_corrected_taxonomy/agreement/split_1_1_1_cases",
        "/rq2_taxonomy/p0_corrected_taxonomy/agreement/raw_pairwise_agreement",
        "/rq2_taxonomy/p0_downstream_crosswalk/historical_necessity_19",
        "/rq2_taxonomy/p0_downstream_crosswalk/all_a3_candidates_33",
        "/x1_replay_gate/gate/success",
        "/x1_replay_gate/gate/n",
        "/x1_replay_gate/gate/required",
        "/x1_replay_gate/gate/b0_strict",
        "/x1_replay_gate/gate/judge_old_majority",
        "/x1_replay_gate/judge_agreement/fleiss_kappa",
        "/x1_replay_gate/p0_source_membership_crosswalk/n",
        "/x1_replay_gate/p0_source_membership_crosswalk/old_new_neither/0",
        "/x1_replay_gate/by_source/f2_b1_greedy/n",
        "/x1_replay_gate/by_source/f2_b1_greedy/b0_strict",
        "/protocol/think_budget_cap_tokens/B1",
        "/rq3/n",
        "/rq3/penalty",
        "/rq3/clr_split_M1/mediation_2x2/n_b0ok",
        "/rq3/genbench/gate",
        "/rq3/genbench_b26_tost/ci_level",
        "/rq3/environment/accelerator_hbm_gb/hopper_class",
        "/rq3/environment/accelerator_hbm_gb/hopper_class_secondary",
        "/rq3/environment/accelerator_hbm_gb/ada_class",
        "/rq3/environment/dtype_crosscheck_n",
        "/rq3/sup_battery/marginal_B3/N/RRs",
        "/rq3/sup_battery/marginal_B3/N/RR",
        "/rq3/sup_battery/marginal_B3/T/RR",
        "/rq3/sup_battery/marginal_B3/T/ES",
        "/rq3/clr_split_M1/CLR1_baseline/n",
        "/rq3/clr_split_M1/CLR1_baseline/T_minus_N_RR",
        "/rq3/clr_split_M1/CLR1_baseline/ci/0",
        "/rq3/clr_split_M1/CLR1_baseline/ci/1",
        "/rq3/clr_split_M1/CLR1_baseline/p",
        "/rq3/clr_split_M1/CLR0_baseline/n",
        "/rq3/clr_split_M1/CLR0_baseline/T_minus_N_RR",
        "/rq3/clr_split_M1/CLR0_baseline/ci/0",
        "/rq3/clr_split_M1/CLR0_baseline/ci/1",
        "/rq3/clr_split_M1/CLR0_baseline/p",
        "/rq3/clr_split_M1/CLR0_baseline/N_RR",
        "/wb_representation_repair/confirm_arms/B1_S_minus_Pshuf/RR",
        "/wb_representation_repair/confirm_arms/B1_S_minus_Pshuf/ES",
        "/wb_representation_repair/confirm_arms/B1_S_minus_Pshuf/CLR",
        "/wb_representation_repair/confirm_arms/S_minus_N/RR",
        "/wb_representation_repair/confirm_arms/S_minus_N/ES",
        "/wb_representation_repair/confirm_arms/B2_LocAcc/S_minus_Pshuf",
    }
)

# A few frozen result blocks predate the scalar-ledger schema.  Only the listed
# numeric token positions from these exact strings are admissible.  This keeps
# the exception auditable and prevents a generic string/note escape hatch.
#
# A bare position index is not a binding: rewording or reordering a frozen
# record can leave position k occupied by a numerically identical but
# semantically different quantity, which the display comparison cannot catch.
# Each record is therefore pinned by the SHA256 of its exact UTF-8 bytes, so any
# edit to the string retires its token approvals until they are re-reviewed.
APPROVED_STRING_TOKEN_POINTERS = {
    "/rq2_logitlens/_authoritative_record/edit_intact_at_cloze": {
        "sha256": "f75857d4088da767b20c4c5d8709d73777783db84fa93435248c62f7d2ee21c7",
        "tokens": frozenset({0, 1}),
    },
    "/rq2_taxonomy/p0_corrected_taxonomy/agreement/raw_pairwise_agreement": {
        "sha256": "e160145137b6c31e2fed391b1deb204b0808fc99790dfdae357b488304969bba",
        "tokens": frozenset({0, 1}),
    },
    "/rq2_taxonomy/p0_downstream_crosswalk/historical_necessity_19": {
        "sha256": "6182ee93c608124d0e4bdc542adf4a490a88fabfaf55a74f5ee80733b05ec20c",
        "tokens": frozenset({5, 6}),
    },
    "/rq2_taxonomy/p0_downstream_crosswalk/all_a3_candidates_33": {
        "sha256": "d49c1109a97660e05e26862e525d0a653447b7dfcf2f7171fdef6899277af795",
        "tokens": frozenset({5, 6}),
    },
    "/wb_representation_repair/confirm_arms/B1_S_minus_Pshuf/RR": {
        "sha256": "eee259c1cf91ce13a0387e1e3ff0f0014799f6e2ce22a9d4420822cba977f909",
        "tokens": frozenset({0, 1, 2}),
    },
    "/wb_representation_repair/confirm_arms/B1_S_minus_Pshuf/ES": {
        "sha256": "ad9e7ad5ded2354bcec1d0a26081883b597805fdfec1d428137b944230938b1c",
        "tokens": frozenset({0, 1, 2}),
    },
    "/wb_representation_repair/confirm_arms/B1_S_minus_Pshuf/CLR": {
        "sha256": "cabd7ddc156c882ba84e255fb2e1829086110e93497437e330e4ef9c514f4ccc",
        "tokens": frozenset({0, 1, 2}),
    },
    "/wb_representation_repair/confirm_arms/S_minus_N/RR": {
        "sha256": "dd5b5beacbe8ca7e9fe455dbf25b56270cb174b5728505f3f50a66d8699ac042",
        "tokens": frozenset({0, 1, 2}),
    },
    "/wb_representation_repair/confirm_arms/S_minus_N/ES": {
        "sha256": "9cfacb9f2d9ae1738495fe6d97bafffc862f0bd0fadd1859d8fc7c7f7090fb95",
        "tokens": frozenset({0, 1, 2}),
    },
    "/wb_representation_repair/confirm_arms/B2_LocAcc/S_minus_Pshuf": {
        "sha256": "eab205e0feacbb6a6ba142ef2f507ba7f0c93693ada0ed4c58a3483fcb069211",
        "tokens": frozenset({0, 1, 2}),
    },
    "/rq3/x3_rome32b_active_paraphrase/paraphrase_content_audit20"
    "/majority_counts/audit_valid": {
        "sha256": "99454f96254a1e9c3bf0384cb913c20dd3bd3bbb9c698885319faaf8f144c2bf",
        "tokens": frozenset({0, 1}),
    },
    "/rq3/genbench/gate": {
        "sha256": "44ef820d96c32569572b6dfec04f66e9835ef57218294b27999ec625b943c81d",
        "tokens": frozenset({0}),
    },
    "/rq3/x3_rome32b_active_paraphrase/paraphrase_content_audit20"
    "/majority_counts/cases_with_both_paraphrases_audit_valid": {
        "sha256": "2d43821423611d1f85249174da18921f40d57ac4d9544cae192191a75925bcba",
        "tokens": frozenset({0, 1}),
    },
}

# Prefixes are intentionally narrower than top-level result blocks and always
# end at an object/array boundary.  Historical prose and broad subtree lookup
# are not valid sources.
APPROVED_POINTER_PREFIXES = (
    "/capability/families/R1-Distill-Qwen/params_b/",
    "/capability/families/R1-Distill-Qwen/es_b0/",
    "/capability/families/R1-Distill-Qwen/es_b3/",
    "/capability/families/R1-Distill-Qwen/es_drop/",
    "/capability/families/R1-Distill-Qwen/es_drop_ci/",
    "/capability/families/R1-Distill-Qwen/rr/",
    "/capability/families/R1-Distill-Qwen/rr_ci/",
    "/capability/families/R1-Distill-Llama/params_b/",
    "/capability/families/R1-Distill-Llama/headline_n/",
    "/capability/families/R1-Distill-Llama/es_b0/",
    "/capability/families/R1-Distill-Llama/es_b3/",
    "/capability/families/R1-Distill-Llama/es_drop/",
    "/capability/families/R1-Distill-Llama/es_drop_ci/",
    "/capability/families/R1-Distill-Llama/rr/",
    "/capability/families/R1-Distill-Llama/rr_ci/",
    "/metric_validation/vs_RRs_strict_decontam/",
    "/metric_validation/vs_RR_loose_decontam/",
    "/rq3/x2_memit14b_repair_replication/audit/b0_byte_identity/",
    "/base_probe/f1_edit_specificity/paired_ci/",
    "/f2_zerothink_deconfound/arms/",
    "/f2_zerothink_deconfound/es_drop_ci/",
    "/f3_sampling_robustness/sampling_primary_complete_cases/",
    "/emergence/b15_base_recall_control/b0_primary/",
    "/emergence/percase/cells_descriptive/Llama-70.0B/",
    "/emergence/percase/es_drop/",
    "/emergence/percase/rr/",
    # Section 5 battery.  Each prefix ends at the object holding only current
    # arms/contrasts; annotation keys inside them start with "_" and are
    # rejected above, as are any "legacy"/"historical" siblings outside them.
    "/rq3/sup_battery/n/",
    "/rq3/sup_battery/marginal_B3/",
    "/rq3/sup_battery/cross_arm_paired_ci/",
    "/rq3/sup_battery/contrasts_B3_mean_ci_p/",
    "/rq3/alpha_sweep/",
    "/rq3/x2_memit14b_repair_replication/fresh_n_es_drop/",
    "/rq3/x3_rome32b_active_paraphrase/audit/b0_byte_identity/",
    "/rq3/genbench_b26_tost/gsm8k/",
    "/rq3/genbench_b26_tost/math500/",
    # Section 5 transfer slots.
    "/rq3/s10_14b_fix_replication/TminusN_paired_ci/",
    "/rq3/x2_memit14b_repair_replication/contrasts_B3/",
    "/rq3/x2_memit14b_repair_replication/audit/b3_different_probe_rows_vs_N/",
    "/rq3/x3_rome32b_active_paraphrase/primary_strict_PS_B3/",
    "/rq3/x3_rome32b_active_paraphrase/audit/b3_different_probe_rows_vs_N/",
    "/rq3/x3_rome32b_active_paraphrase/fixed_N_B0_gate_secondary_old_only/gate/",
    "/rq3/x3_rome32b_active_paraphrase/paraphrase_content_audit20/agreement/",
    "/rq3/x3_rome32b_active_paraphrase/paraphrase_content_audit20/majority_counts/",
)

UNSAFE_POINTER_PARTS = ("superseded", "historical", "legacy")

# WRITING_PLAN §5 grants "prospectively specified" only where a dated artifact
# (SHA-in-artifact, server timestamp, platform log) predates the results.  Each
# approved manuscript site is listed with the artifact that earns it; anything
# else must say "pre-specified".
APPROVED_PROSPECTIVE_LABEL_SITES = frozenset(
    {
        # X1 replay: the 18-case manifest SHA was frozen before the gate ran.
        "prospectively specified attempt",
    }
)

NUMERIC_RE = re.compile(
    r"(?<![A-Za-z0-9])[-+\N{MINUS SIGN}]?"
    r"(?:\d+\.\d+|\.\d+|\d+)(?![A-Za-z0-9])"
)

REQUIRED_SECTION_ORDER = (
    "Introduction",
    "Related Work",
    "The Reasoning-Time Evaluation Gap",
    "Causal Diagnosis",
    "A Chain-Local Causal Control Point",
    r"Discussion \& Limitations",
    "Conclusion",
)

AUDITED_SECTION_SPECS = (
    # ``requires_ledger`` marks sections that must carry numeric claims.  The
    # others are snapshotted too: with an empty ledger, any numeric token in
    # them fails the per-line occurrence check, which is the zero-number rule.
    {
        "label": "Section 1",
        "title": "Introduction",
        "end_title": "Related Work",
        "requires_ledger": False,
    },
    {
        "label": "Section 2",
        "title": "Related Work",
        "end_title": "The Reasoning-Time Evaluation Gap",
        "requires_ledger": False,
    },
    {
        "label": "Section 3",
        "title": "The Reasoning-Time Evaluation Gap",
        "end_title": "Causal Diagnosis",
    },
    {
        "label": "Section 4",
        "title": "Causal Diagnosis",
        "end_title": "A Chain-Local Causal Control Point",
    },
    {
        "label": "Section 5",
        "title": "A Chain-Local Causal Control Point",
        "end_title": r"Discussion \& Limitations",
    },
    {
        "label": "Section 6",
        "title": r"Discussion \& Limitations",
        "end_title": "Conclusion",
    },
    {
        "label": "Section 7",
        "title": "Conclusion",
        "start_marker": r"\section{Conclusion}",
        "end_marker": r"\section*{Ethical Statement}",
        "requires_ledger": False,
    },
    {
        "label": "Ethical Statement",
        "title": "Ethical Statement",
        "start_marker": r"\section*{Ethical Statement}",
        "end_marker": r"\bibliography{refs}",
    },
)
AUDITED_SECTION_TITLES = frozenset(
    specification["title"] for specification in AUDITED_SECTION_SPECS
)


def section_markers(specification: dict[str, Any]) -> tuple[str, str]:
    if "start_marker" in specification:
        start = specification["start_marker"]
    else:
        start = rf"\section{{{specification['title']}}}"
    if "end_marker" in specification:
        end = specification["end_marker"]
    else:
        end = rf"\section{{{specification['end_title']}}}"
    return start, end

# The checker does not attempt to interpret arbitrary TeX.  This allowlist is
# the reviewed command surface of the single-source manuscript; adding a new
# command or environment requires an explicit checker review in the same
# change.  In particular, generated text/numbers, external text input, and
# non-rendering side-effect commands fail closed.
ALLOWED_TEX_COMMANDS = frozenset(
    {
        "Delta",
        "Pr",
        "UrlFont",
        "affiliations",
        "author",
        "begin",
        "bibliography",
        "bottomrule",
        "caption",
        "centering",
        "citep",
        "citet",
        "columnwidth",
        "def",
        "documentclass",
        "end",
        "fbox",
        "footnote",
        "includegraphics",
        "frenchspacing",
        "kappa",
        "label",
        "land",
        "maketitle",
        "mathrm",
        "midrule",
        "neg",
        "paragraph",
        "parbox",
        "multicolumn",
        "pdfinfo",
        "ref",
        "rm",
        "section",
        "setcounter",
        "small",
        "subsection",
        "textbf",
        "textit",
        "textsc",
        "textwidth",
        "title",
        "toprule",
        "url",
        "urlstyle",
        "usepackage",
    }
)
ALLOWED_TEX_ENVIRONMENTS = frozenset(
    {"abstract", "document", "figure*", "table", "table*", "tabular"}
)
ALLOWED_TEX_CONTROL_SYMBOLS = frozenset({"%", "&", "(", ")", ",", "\\"})
BODY_ALLOWED_TEX_COMMANDS = frozenset(
    {
        "Delta",
        "Pr",
        "begin",
        "bibliography",
        "bottomrule",
        "caption",
        "centering",
        "citep",
        "citet",
        "columnwidth",
        "end",
        "fbox",
        "footnote",
        "includegraphics",
        "kappa",
        "label",
        "land",
        "maketitle",
        "mathrm",
        "midrule",
        "neg",
        "paragraph",
        "parbox",
        "multicolumn",
        "ref",
        "section",
        "small",
        "subsection",
        "textbf",
        "textit",
        "textsc",
        "textwidth",
        "toprule",
        "url",
    }
)

M04_TARGET = (
    "We report all six fixed-checkpoint cells. The cellwise, unadjusted 95% "
    "paired case-bootstrap intervals exclude zero only at the largest tested "
    "checkpoint in each family. These cells delimit the headline scope---a "
    "scope statement, not a post-hoc selection---and we do not infer an "
    "ordered trend across checkpoints."
)

M12_TARGET = (
    "The similarity across the two tested backbone lineages disfavors a "
    "single-lineage idiosyncrasy, though not recipe-specificity: both share "
    "an R1 teacher and distillation recipe, and the comparison does not "
    "establish equality across lineages."
)

BANNED_PATTERNS = {
    "invalid certificate": r"\binvalid certificate\b",
    "capability-emergent": r"\bcapability-emergent\b",
    "scaling-law language": r"\bscaling[ -]law\b",
    "fuel": r"\bfuel(?:s|ed|ing)?\b",
    "vanishes": r"\bvanish(?:es|ed|ing)?\b",
    "causal re-derivation claim": r"\bre-derivation causes\b",
    "semantic mediation": r"\bsemantic mediation\b",
    "mediates": r"\bmediates?\b",
    "necessity": r"(?<!near-)\bnecessity\b",
    "semantic paraphrase robustness": r"\bsemantic paraphrase robustness\b",
    "equivalence certification": r"\b(?:equivalence certified|tost-certified)\b",
    "prevention language": r"\b(?:prevents|blocks|robust to bypass)\b",
    "unqualified halves-reversion claim": r"\bhalves reversion\b",
    "priority claim": r"\bfirst to discover\b",
    "unsupported preregistration wording": r"\bpreregistered\b",
    "unhyphenated prespecified variant": r"\bprespecified\b",
    "edit-intact overclaim": r"\bedit intact\b",
    "not-erased overclaim": r"\bnot erased\b",
    # W2-8/A1-2: a banned clause must be barred in every word form and in its
    # denial rewrites.  This is the third synonym bypass of the same rule
    # ("declines at every step" for monotonic*, the noun "erasure" for "erased"),
    # so the pattern set now covers -ed/-ure/-ing and negated paraphrases.
    "erasure-noun overclaim": r"\berasure\b",
    # W2-8/M4: only the verb is licensed; the nominalisation asserts a status.
    "certification nominalisation": r"\bcertificat(?:ion|ions)\b",
    # W2-14/C: the fourth bypass class.  W2-13 moved the required string from the
    # granting clause to the disclaimer that follows it, which left the assertion
    # ("leaving the answer where it was") unguarded.  A ban must be written against
    # the assertion form itself, not against its label or its neighbouring hedge.
    # Scoped to the ANSWER as an outcome: statements that the penalty does not act
    # on the answer span are mechanical and stay legal.
    "answer-held assertion": r"leav\w+ the answer where it was|the answer (?:did|does) not move|the answer stay\w+|the answer[^.]{0,15}\bremained unchanged\b",
    # W2-15: same lesson as `erasure` slipping past `erased`, for the second time.
    # A ban has to cover the nominalised form and the preservation/negation form,
    # not only the verb it was first written against.
    "answer-held nominal or negated": r"without moving the answer|leaves the answer unchanged|the answer is unaffected|the answer holds\b|no answer-level movement|answer-level inertness",
    "erased word-form overclaim": r"\berased\b|\berasing\b",
    "negated-erasure paraphrase": r"\bnot\b[^.]{0,40}\b(?:eras|intact)",
    # Bare "intact" cannot be banned: Section 2 legitimately reports that prior
    # work found general capability stays intact.  Bind it to our own edit.
    "intact overclaim": r"\bedit\w*\b[^.]{0,40}\bintact\b",
    "guaranteed-upper-bound overclaim": r"\bguaranteed upper bound\b",
    "ordered-trend overclaim": r"\bmonotonic\w*\b",
    "chain-localized variant": r"\bchain-localized\b",
    "chain-only variant": r"\bchain-only\b",
    "chain-confined variant": r"\bchain-confined\b",
    # The banned quantity is the positive .214 margin between an edited-state
    # gated rate and an unedited-base drift.  A negative -.214 cannot be that
    # margin, and one legitimately appears as a Section 5 interval bound.
    "forbidden F1 pseudo-contrast": r"(?<![\d.\-−])\.214(?!\d)",
    "latent-rate bracket": r"\btrue reversion\b.{0,60}\bbetween\b",
}

STALE_CONTEXT_PATTERNS = {
    "superseded route pool": r"\b(?:n\s*=\s*50|50 committed reversions)\b",
    "superseded associative ratio": r"\b1\s*/\s*50\b",
    "superseded route pool words": r"\bfifty committed reversions\b",
    "superseded fifty count": r"\bfifty\b",
    "superseded route distribution": r"\b68\s*%",
    "superseded route distribution words": r"\bsixty[- ]eight percent\b",
    "superseded sixty-eight count": r"\bsixty[- ]eight\b",
    "superseded route count tuple": r"\b34\s*/\s*11\s*/\s*4\s*/\s*1\b",
    "superseded route percentage tuple": r"\b68\s*/\s*22\s*/\s*8\s*/\s*2\b",
    "superseded route kappa": r"(?:kappa|κ)\s*=\s*0?\.790\b",
    "superseded full-panel kappa": r"(?:kappa|κ)\s*=\s*0?\.875\b",
    "superseded logit-lens feature": (
        r"\b(?:logit|cloze|gap|layer).{0,80}"
        r"(?:17\.803|11\.548|11\.569|-?0?\.246|-?0?\.351)\b"
    ),
    "stale bare .545": r"(?<![\d.A-Za-z_])0?\.545(?![\dA-Za-z_])",
    "stale bare .765": r"(?<![\d.A-Za-z_])0?\.765(?![\dA-Za-z_])",
    "mis-scoped reversion": r"\b19\.3\s*%\s+overall\b",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def split_tex_comment(line: str) -> tuple[str, str | None]:
    """Split at the first unescaped TeX comment marker."""

    for index, char in enumerate(line):
        if char != "%":
            continue
        backslashes = 0
        cursor = index - 1
        while cursor >= 0 and line[cursor] == "\\":
            backslashes += 1
            cursor -= 1
        if backslashes % 2 == 0:
            return line[:index], line[index + 1 :]
    return line, None


def strip_tex_comments(text: str) -> str:
    # An unescaped TeX ``%`` consumes the physical newline as well as the rest
    # of its line.  Preserve newlines only on uncommented lines so that
    # ``scal% comment\ning`` normalizes to the rendered word ``scaling``.
    return "".join(
        split_tex_comment(line)[0]
        for line in text.splitlines(keepends=True)
    )


def uncommented_marker_offsets(
    text: str, markers: tuple[str, ...]
) -> dict[str, list[int]]:
    offsets: dict[str, list[int]] = {marker: [] for marker in markers}
    cursor = 0
    for line in text.splitlines(keepends=True):
        code, _ = split_tex_comment(line)
        for marker in offsets:
            search_from = 0
            while True:
                index = code.find(marker, search_from)
                if index < 0:
                    break
                offsets[marker].append(cursor + index)
                search_from = index + len(marker)
        cursor += len(line)
    return offsets


def extract_between_markers(
    text: str,
    start_marker: str,
    end_marker: str,
    label: str,
) -> str:
    offsets = uncommented_marker_offsets(text, (start_marker, end_marker))

    if len(offsets[start_marker]) != 1 or len(offsets[end_marker]) != 1:
        raise ValueError(
            f"boundaries must be unique and uncommented for {label!r}: "
            f"start={len(offsets[start_marker])}, end={len(offsets[end_marker])}"
        )
    start = offsets[start_marker][0]
    end = offsets[end_marker][0]
    if end <= start:
        raise ValueError(f"cannot isolate {label!r}")
    return text[start:end]


def extract_section(text: str, start_title: str, end_title: str) -> str:
    return extract_between_markers(
        text,
        rf"\section{{{start_title}}}",
        rf"\section{{{end_title}}}",
        f"section {start_title}",
    )


def replace_citation_with_visible_notes(match: re.Match[str]) -> str:
    """Keep rendered natbib notes while dropping the generated citation/key."""

    notes = re.findall(r"\[([^\[\]]*)\]", match.group("notes") or "")
    return " " + " ".join(notes) + " "


def strip_nonrendered_command_arguments(text: str) -> str:
    """Remove source-only command arguments before visible-text assertions."""

    text = re.sub(
        r"\\(?:cite|citep|citet|citealp|citeauthor|citeyear)"
        r"(?P<notes>(?:\[[^\[\]]*\]){0,2})\{[^{}]*\}",
        replace_citation_with_visible_notes,
        text,
    )
    text = re.sub(
        r"\\(?:ref|pageref|label|bibliography)\s*\{[^{}]*\}",
        " ",
        text,
    )
    text = re.sub(r"\\(?:begin|end)\s*\{[^{}]*\}", " ", text)
    # Optional short headings/captions are not printed in the manuscript body.
    text = re.sub(
        r"\\(?:section|subsection|caption)\*?(?:\[[^\[\]]*\])?",
        "",
        text,
    )
    return text


def normalize_visible(text: str) -> str:
    text = strip_tex_comments(text)
    text = strip_nonrendered_command_arguments(text)
    text = (
        text.replace(r"\%", "%")
        .replace(r"\&", "&")
        .replace(r"\-", "")
        .replace(r"\kappa", "kappa")
        .replace(r"\Pr", "Pr")
        .replace(r"\land", " AND ")
        .replace(r"\neg", " NOT ")
        .replace(r"\,", " ")
        .replace(r"\\", " ")
        .replace("~", " ")
    )
    # Preserve arguments while removing TeX command names and grouping braces.
    # This makes prose scans see through constructions such as
    # ``scal\textbf{ing}`` instead of treating source spelling as rendered text.
    # TeX ignores delimiter whitespace after a control word, so consume it as
    # well: ``scal\textbf {ing}`` and ``scal\relax ing`` must not create a
    # false word boundary.
    text = re.sub(r"\\[A-Za-z@]+\*?[ \t\r\n]*", "", text)
    text = re.sub(r"\\.", "", text)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def decode_pointer_part(part: str) -> str:
    # RFC 6901 permits only ~0 and ~1 escapes.
    if re.search(r"~(?![01])", part):
        raise ValueError(f"invalid RFC 6901 escape in {part!r}")
    return part.replace("~1", "/").replace("~0", "~")


def resolve_pointer(root: Any, pointer: str) -> Any:
    if not pointer.startswith("/"):
        raise ValueError("pointer must start with '/'")
    current = root
    for raw_part in pointer[1:].split("/"):
        part = decode_pointer_part(raw_part)
        if isinstance(current, list):
            if not re.fullmatch(r"0|[1-9]\d*", part):
                raise ValueError(f"array index is not canonical: {part!r}")
            index = int(part)
            if index >= len(current):
                raise ValueError(f"array index out of range: {index}")
            current = current[index]
        elif isinstance(current, dict):
            if part not in current:
                raise ValueError(f"missing object key: {part!r}")
            current = current[part]
        else:
            raise ValueError(f"pointer descends through scalar before {part!r}")
    return current


def decimal_value(value: Any) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise TypeError(f"ledger target must be numeric scalar, got {type(value).__name__}")
    try:
        return value if isinstance(value, Decimal) else Decimal(str(value))
    except InvalidOperation as exc:
        raise TypeError(f"not a finite decimal: {value!r}") from exc


def drop_leading_zero(value: str) -> str:
    if value.startswith("-0."):
        return "-." + value[3:]
    if value.startswith("+0."):
        return "+." + value[3:]
    if value.startswith("0."):
        return "." + value[2:]
    return value


def format_result(value: Any, rule: str, pointer: str | None = None) -> str:
    token_match = re.fullmatch(r"token:(\d+)", rule)
    if token_match:
        if pointer is None:
            raise ValueError("token formatter requires its exact pointer")
        token_index = int(token_match.group(1))
        specification = APPROVED_STRING_TOKEN_POINTERS.get(pointer)
        if specification is None or token_index not in specification["tokens"]:
            raise ValueError(
                f"token position {token_index} is not approved for {pointer}"
            )
        if not isinstance(value, str):
            raise TypeError(
                f"token formatter requires a frozen string, got {type(value).__name__}"
            )
        frozen_sha256 = sha256_bytes(value.encode("utf-8"))
        if frozen_sha256 != specification["sha256"]:
            raise ValueError(
                f"frozen string at {pointer} differs from the reviewed record "
                f"(actual SHA256 {frozen_sha256}); its token positions must be "
                "re-reviewed before reuse"
            )
        tokens = [
            match.group(0).replace("\N{MINUS SIGN}", "-")
            for match in NUMERIC_RE.finditer(value)
        ]
        if token_index >= len(tokens):
            raise ValueError(
                f"token position {token_index} is absent from frozen string"
            )
        return tokens[token_index]

    number = decimal_value(value)
    if rule == "integer":
        integral = number.to_integral_value()
        if number != integral:
            raise ValueError(f"integer formatter received {number}")
        return str(integral)

    match = re.fullmatch(r"(fixed|percent|signed):(\d+)", rule)
    if not match:
        raise ValueError(f"unknown formatter {rule!r}")
    kind, places_text = match.groups()
    places = int(places_text)
    if places > 8:
        raise ValueError("formatter precision above 8 is not approved")
    if kind == "percent":
        number *= Decimal(100)
    quantum = Decimal(1).scaleb(-places)
    quantized = number.quantize(quantum, rounding=ROUND_HALF_UP)
    if kind == "signed":
        rendered = format(quantized, f"+.{places}f")
    else:
        rendered = format(quantized, f".{places}f")
    return drop_leading_zero(rendered)


def pointer_is_approved(pointer: str) -> bool:
    # Exact exceptions are reviewed before generic underscore/historical
    # rejection; this is needed for the authoritative logit-lens record and
    # two frozen crosswalk strings without opening their surrounding subtrees.
    if pointer in APPROVED_EXACT_POINTERS:
        return True
    lowered_parts = [part.lower() for part in pointer.split("/")]
    if any(part.startswith("_") for part in pointer.split("/") if part):
        return False
    if any(fragment in part for fragment in UNSAFE_POINTER_PARTS for part in lowered_parts):
        return False
    return any(
        pointer.startswith(prefix) for prefix in APPROVED_POINTER_PREFIXES
    )


def mask_nonclaim_numbers(code: str) -> str:
    """Remove identifiers and dimensions that are not manuscript claims."""

    # Citation and reference keys can contain years or model ids but do not
    # render as authored numeric claims.  Natbib optional notes do render and
    # therefore remain visible to the numeric scanner.
    code = re.sub(
        r"\\(?:cite|citep|citet|citealp|citeauthor|citeyear)"
        r"(?P<notes>(?:\[[^\[\]]*\]){0,2})\{[^{}]*\}",
        replace_citation_with_visible_notes,
        code,
    )
    code = re.sub(r"\\(?:ref|pageref|label)\s*\{[^{}]*\}", " ", code)
    # Fixed budget and full model identifiers are names.  A standalone
    # parameter count (e.g., the Parameters column's ``7B``) remains a claim:
    # remove only its unit so the numeric scanner sees it.
    code = re.sub(r"B_\{?(?:0P?|1|2|3)\}?", "BUDGET", code)
    code = re.sub(r"\bB(?:0P?|1|2|3)\b", "BUDGET", code)
    code = re.sub(r"\b(?:Qwen|Llama)-\d+(?:\.\d+)?B\b", "MODEL", code)
    code = re.sub(
        r"(?<![A-Za-z0-9-])(\d+(?:\.\d+)?)B\b",
        r"\1",
        code,
    )
    # Pure layout dimensions are source mechanics only inside the reviewed
    # width/position arguments of ``\parbox``.  A generic TeX group such as
    # ``{.546pt}`` can be visible prose and must not receive this exemption.
    def mask_parbox_dimensions(match: re.Match[str]) -> str:
        invocation = match.group(0)
        invocation = re.sub(
            r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:in|pt|pc|mm|cm|em|ex)\b",
            "LAYOUT_DIM",
            invocation,
        )
        return re.sub(
            r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)\s*"
            r"\\(?:textwidth|linewidth|columnwidth)\b",
            "LAYOUT_DIM",
            invocation,
        )

    code = re.sub(
        r"\\parbox(?:\[[^\[\]]*\]){0,3}\{[^{}]*\}",
        mask_parbox_dimensions,
        code,
    )
    # Same treatment for the one reviewed graphics inclusion: its width factor
    # is a layout knob, not an authored claim.  Only the bracketed option list
    # is masked, so a number in the file name would still be scanned.
    code = re.sub(
        r"\\includegraphics\[[^\[\]]*\]",
        mask_parbox_dimensions,
        code,
    )
    # W2-10/F: ``\multicolumn{N}{spec}`` spans columns; N is table structure, not
    # an authored number.  Only the two structural arguments are masked, so any
    # value inside the cell body is still scanned.
    code = re.sub(
        r"\\multicolumn\{\d+\}\{[^{}]*\}",
        lambda m: "\\multicolumn{SPAN}{ALIGN}",
        code,
    )
    # A dimension-looking token outside that command surface is visible prose.
    # Remove only its alphabetic suffix so the numeric claim is scanned.
    code = re.sub(
        r"(?<![A-Za-z0-9])([-+]?(?:\d+(?:\.\d*)?|\.\d+))"
        r"(?:in|pt|pc|mm|cm|em|ex)\b",
        r"\1",
        code,
    )
    return code


def numeric_occurrences(code: str) -> list[str]:
    masked = mask_nonclaim_numbers(code)
    return [match.group(0).replace("\N{MINUS SIGN}", "-") for match in NUMERIC_RE.finditer(masked)]


def remove_balanced_command(text: str, command: str) -> str:
    """Remove every command{...} occurrence, honoring nested braces."""

    result: list[str] = []
    cursor = 0
    needle = command + "{"
    while True:
        start = text.find(needle, cursor)
        if start < 0:
            result.append(text[cursor:])
            return "".join(result)
        result.append(text[cursor:start])
        depth = 1
        index = start + len(needle)
        while index < len(text) and depth:
            if text[index] == "{" and (index == 0 or text[index - 1] != "\\"):
                depth += 1
            elif text[index] == "}" and (index == 0 or text[index - 1] != "\\"):
                depth -= 1
            index += 1
        if depth:
            raise ValueError(f"unbalanced {command} argument")
        cursor = index


def check_template_and_frozen_surfaces(
    main_text: str,
    main_path: Path,
    errors: list[str],
) -> None:
    visible_source = strip_tex_comments(main_text)
    document_marker = r"\begin{document}"
    if main_text.count(document_marker) != 1:
        errors.append(r"\begin{document} must occur exactly once")
        preamble = ""
        body_source = visible_source
    else:
        preamble, body = main_text.split(document_marker, 1)
        body_source = strip_tex_comments(body)
        preamble_sha256 = sha256_bytes(preamble.encode("utf-8"))
        if preamble_sha256 != APPROVED_PREAMBLE_SHA256:
            errors.append(
                "manuscript preamble differs from the reviewed snapshot "
                f"(actual SHA256 {preamble_sha256})"
            )

    titles = re.findall(r"\\title\{([^{}]+)\}", visible_source)
    if titles != [FROZEN_TITLE]:
        errors.append("title does not exactly match the frozen title")

    if visible_source.count(r"\usepackage[submission]{aaai2027}") != 1:
        errors.append("AAAI anonymous submission option is missing")
    if re.findall(r"\\author\{([^{}]*)\}", visible_source) != [
        "Anonymous Submission"
    ]:
        errors.append("anonymous author marker is missing")
    if re.findall(r"\\affiliations\{([^{}]*)\}", visible_source) != [""]:
        errors.append("affiliations must be empty")
    if visible_source.count(r"\maketitle") != 1:
        errors.append(r"\maketitle must occur exactly once")
    if visible_source.count(r"\setcounter{secnumdepth}{2}") != 1:
        errors.append("section numbering depth must be 2")
    if r"\nocopyright" in visible_source:
        errors.append(r"\nocopyright is forbidden")
    if re.search(
        r"\\(?:input|include|InputIfFileExists|verbatiminput|VerbatimInput|"
        r"lstinputlisting|import|subimport|includepdf)\b",
        visible_source,
    ):
        errors.append("main.tex must remain a single source file without input/include")

    # Conditional compilation, invisible boxes, comment environments, and
    # source-level macro redefinition can make the checked bytes differ from
    # the rendered manuscript.  Keep the one AuthorKit-mandated UrlFont
    # definition and reject these constructs everywhere else.
    construct_surface = visible_source.replace(r"\def\UrlFont{\rm}", "")
    unsafe_constructs = {
        "TeX conditional": r"\\(?:if[a-zA-Z@]*|else|fi)\b",
        "invisible phantom box": r"\\(?:phantom|hphantom|vphantom)\s*\{",
        "comment environment": r"\\begin\s*\{comment\}",
        "dynamic control sequence": r"\\csname\b",
        "macro definition/rebinding": (
            r"\\(?:def|gdef|edef|xdef|let|newcommand|renewcommand|"
            r"providecommand|DeclareRobustCommand)\b"
        ),
        "non-rendering side effect": (
            r"\\(?:typeout|message|write|openout|openin|read|special)\b"
        ),
    }
    for label, pattern in unsafe_constructs.items():
        if re.search(pattern, construct_surface):
            errors.append(f"forbidden manuscript construct ({label})")

    commands = set(re.findall(r"\\([A-Za-z@]+)\*?", visible_source))
    unknown_commands = sorted(commands - ALLOWED_TEX_COMMANDS)
    if unknown_commands:
        errors.append(f"unreviewed TeX command(s): {unknown_commands!r}")
    body_commands = set(re.findall(r"\\([A-Za-z@]+)\*?", body_source))
    unknown_body_commands = sorted(body_commands - BODY_ALLOWED_TEX_COMMANDS)
    if unknown_body_commands:
        errors.append(
            f"preamble-only/unreviewed body TeX command(s): {unknown_body_commands!r}"
        )
    # One per reviewed table (Tables 1 and 2); a third occurrence would be a
    # document-level font change rather than a table-local one.
    if body_source.count(r"\small") != 3:
        errors.append(r"\small must occur exactly once per reviewed table")

    environments = set(
        re.findall(r"\\(?:begin|end)\s*\{([^{}]+)\}", visible_source)
    )
    unknown_environments = sorted(environments - ALLOWED_TEX_ENVIRONMENTS)
    if unknown_environments:
        errors.append(f"unreviewed TeX environment(s): {unknown_environments!r}")

    control_symbols = set(
        re.findall(r"\\([^A-Za-z@\s])", visible_source)
    )
    unknown_control_symbols = sorted(
        control_symbols - ALLOWED_TEX_CONTROL_SYMBOLS
    )
    if unknown_control_symbols or re.search(r"(?<!\\)\\[ \t]", visible_source):
        errors.append(
            "unreviewed TeX control symbol(s): "
            f"{unknown_control_symbols!r}"
        )
    if "^^" in visible_source:
        errors.append("TeX ^^ character notation is forbidden")

    expected_pdfinfo = "\\pdfinfo{\n/TemplateVersion (2027.1)\n}"
    if (
        visible_source.count(r"\pdfinfo") != 1
        or visible_source.count(expected_pdfinfo) != 1
    ):
        errors.append("PDF metadata block differs from the reviewed template block")

    section_titles = re.findall(r"\\section\{([^{}]+)\}", visible_source)
    if tuple(section_titles) != REQUIRED_SECTION_ORDER:
        errors.append(f"unexpected numbered-section order: {section_titles!r}")
    if visible_source.count(r"\section*{Ethical Statement}") != 1:
        errors.append("unnumbered Ethical Statement is missing")
    if re.findall(r"\\bibliography\{([^{}]+)\}", visible_source) != ["refs"]:
        errors.append(r"bibliography command must occur exactly once as \bibliography{refs}")

    if visible_source.count(r"\begin{abstract}") != 1 or visible_source.count(
        r"\end{abstract}"
    ) != 1:
        errors.append("abstract environment must occur exactly once")
        return
    abstract_match = re.search(
        r"\\begin\{abstract\}\s*\n(.*?)\n\\end\{abstract\}",
        visible_source,
        flags=re.DOTALL,
    )
    if not abstract_match:
        errors.append("cannot extract abstract from main.tex")
        return
    recovered = abstract_match.group(1).replace(r"\%", "%")
    candidate_bytes = FROZEN_ABSTRACT.read_bytes()
    candidate_text = candidate_bytes.decode("utf-8")
    candidate_body = candidate_text[:-1] if candidate_text.endswith("\n") else candidate_text
    if recovered != candidate_body:
        errors.append("LaTeX abstract differs from frozen v8.1 after reversing \\% escapes")
    if sha256_bytes(candidate_bytes) != FROZEN_ABSTRACT_SHA256:
        errors.append("frozen abstract source SHA256 changed")

    for filename in ("aaai2027.sty", "aaai2027.bst"):
        copied = main_path.parent / filename
        original = TEMPLATE_DIR / filename
        if not copied.exists() or copied.read_bytes() != original.read_bytes():
            errors.append(f"{filename} is missing or differs from AuthorKit27")

    refs_path = main_path.parent / "refs.bib"
    if not refs_path.exists():
        errors.append("refs.bib is missing or differs from the reviewed bibliography")
    else:
        refs_sha256 = sha256_bytes(refs_path.read_bytes())
        if refs_sha256 != APPROVED_REFS_SHA256:
            errors.append(
                "refs.bib is missing or differs from the reviewed bibliography "
                f"(actual SHA256 {refs_sha256})"
            )


def check_rj_ledger(
    section_text: str,
    results: Any,
    errors: list[str],
    section_label: str,
    global_claim_ids: set[str],
    require_entries: bool = True,
) -> list[dict[str, Any]]:
    ledger: list[dict[str, Any]] = []

    for line_number, line in enumerate(section_text.splitlines(), start=1):
        code, comment = split_tex_comment(line)
        entries: list[dict[str, Any]] = []
        if comment is not None and comment.lstrip().startswith("RJ:"):
            payload_text = comment.lstrip()[3:].strip()
            try:
                payload = json.loads(payload_text)
            except json.JSONDecodeError as exc:
                errors.append(
                    f"{section_label} line {line_number}: malformed RJ JSON: {exc}"
                )
                continue
            entries = payload if isinstance(payload, list) else [payload]
            if not entries:
                errors.append(f"{section_label} line {line_number}: empty RJ payload")

        source_numbers = numeric_occurrences(code)
        ledger_numbers: list[str] = []

        for entry_index, entry in enumerate(entries):
            prefix = f"{section_label} line {line_number}, RJ entry {entry_index + 1}"
            if not isinstance(entry, dict):
                errors.append(f"{prefix}: entry must be an object")
                continue
            expected_keys = {"claim", "display", "pointer", "format"}
            if set(entry) != expected_keys:
                errors.append(
                    f"{prefix}: keys must be exactly {sorted(expected_keys)}, got {sorted(entry)}"
                )
                continue
            claim = entry["claim"]
            display = entry["display"]
            pointer = entry["pointer"]
            rule = entry["format"]
            if not all(isinstance(value, str) for value in (claim, display, pointer, rule)):
                errors.append(f"{prefix}: all fields must be strings")
                continue
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", claim):
                errors.append(f"{prefix}: invalid claim id {claim!r}")
            elif claim in global_claim_ids:
                errors.append(f"{prefix}: duplicate claim id {claim!r}")
            else:
                global_claim_ids.add(claim)
            if not pointer_is_approved(pointer):
                errors.append(f"{prefix}: pointer is outside approved current-result paths: {pointer}")
                continue
            try:
                value = resolve_pointer(results, pointer)
                rendered = format_result(value, rule, pointer)
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                errors.append(f"{prefix}: {exc}")
                continue
            if rendered != display:
                errors.append(
                    f"{prefix}: display {display!r} != {rendered!r} from {pointer} via {rule}"
                )
            ledger_numbers.append(display)
            ledger.append(
                {
                    "claim": claim,
                    "display": display,
                    "pointer": pointer,
                    "format": rule,
                    "section": section_label,
                    "source_line": line_number,
                    "source_code_sha256": sha256_bytes(
                        normalize_visible(code).encode("utf-8")
                    ),
                }
            )

        if source_numbers != ledger_numbers:
            errors.append(
                f"{section_label} line {line_number}: numeric occurrences {source_numbers!r} "
                f"do not match RJ occurrences {ledger_numbers!r}"
            )

    if require_entries and not ledger:
        errors.append(f"{section_label} contains no RJ ledger entries")
    return ledger


def ledger_bindings_sha256(ledger: list[dict[str, Any]]) -> str:
    bindings = [
        [
            entry["claim"],
            entry["display"],
            entry["pointer"],
            entry["format"],
            entry["source_code_sha256"],
        ]
        for entry in ledger
    ]
    encoded = json.dumps(
        bindings,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_bytes(encoded)


def section_visible_sha256(section_text: str) -> str:
    return sha256_bytes(normalize_visible(section_text).encode("utf-8"))


def section_source_sha256(section_text: str) -> str:
    """Hash reviewed TeX structure while excluding RJ/comment-only metadata."""

    semantic_lines: list[str] = []
    for raw_line in section_text.splitlines():
        code, comment = split_tex_comment(raw_line)
        # A comment-only line has no TeX paragraph semantics.  Preserve genuine
        # blank lines, because inserting one starts a new rendered paragraph.
        if comment is not None and not code.strip():
            continue
        semantic_lines.append(code.rstrip())
    source = "\n".join(semantic_lines)
    paragraphs = [
        re.sub(r"\s+", " ", paragraph).strip()
        for paragraph in re.split(r"\n[ \t]*\n+", source)
        if paragraph.strip()
    ]
    source = "<PAR>".join(paragraphs)
    return sha256_bytes(source.encode("utf-8"))


def check_global_claim_language(main_text: str, errors: list[str]) -> None:
    # Scans rendered prose only.  ``normalize_visible`` drops TeX comments
    # first, so RJ payloads are out of scope by construction -- a reviewed
    # exception, since results.json pointer names legitimately contain banned
    # words (``preregistered_confirmatory_floor_cases``) that never render.
    visible = normalize_visible(main_text)
    # TeX ``--``/``---`` and Unicode dash variants render as punctuation that
    # must not split banned phrases such as ``scaling-law`` or ``lower-bound``.
    visible = re.sub(r"-{2,3}|[\u2010-\u2015\u2212]", "-", visible)
    lowered = visible.lower()
    for label, pattern in BANNED_PATTERNS.items():
        if re.search(pattern, lowered, flags=re.IGNORECASE | re.DOTALL):
            errors.append(f"banned language ({label})")
    for label, pattern in STALE_CONTEXT_PATTERNS.items():
        if re.search(pattern, visible, flags=re.IGNORECASE):
            errors.append(f"stale manuscript claim ({label})")

    approved_lower_bound_sentence = (
        "missingness is concentrated among rule-negative rows but does not make "
        "the available-case kappa a lower bound; the missingness pattern is "
        "reported in the supplement."
    )
    for sentence in re.split(r"(?<=[.!?])\s+", lowered):
        if (
            re.search(r"\blower[ -]bound\b", sentence)
            and sentence != approved_lower_bound_sentence
        ):
            errors.append("lower-bound language is not explicitly negated in its sentence")


def check_section3_requirements(section_text: str, errors: list[str]) -> None:
    visible = normalize_visible(section_text)
    required_strings = (
        M04_TARGET,
        M12_TARGET,
        "the two quantities differ in event definition and denominator; we make no formal contrast",
        "answer-commitment validation panel",
        "route-census panel",
        "available-case Cohen's",
        "inter-judge Fleiss'",
        "not mathematical bounds",
        "fixed short canned thought, not a length-matched filler",
        "These fixed seeds do not identify a sampling-seed population.",
        "not a second independent trend line",
    )
    for target in required_strings:
        if target not in visible:
            errors.append(f"required target string missing: {target!r}")

    rr_sentences = [
        sentence
        for sentence in re.split(r"(?<=[.!?])\s+", visible)
        if "19.3%" in sentence
    ]
    if len(rr_sentences) != 1:
        errors.append("expected exactly one Section 3 sentence containing 19.3%")
    else:
        sentence = rr_sentences[0]
        if "Among zero-thinking successes on Qwen-32B" not in sentence or "9.2%" not in sentence:
            errors.append("19.3% is not welded to its Qwen-32B zero-thinking-success condition")

    # D1/D2/D8 surface gates.
    debt_targets = {
        "D1": ("all six fixed-checkpoint cells", "paired case-bootstrap intervals"),
        "D2": ("87", "120", "rate limits", "shared-bias risk"),
        "D8": ("fixed short canned thought", "three fixed seeds", "complete-case ES drop"),
    }
    for debt, targets in debt_targets.items():
        missing = [target for target in targets if target not in visible]
        if missing:
            errors.append(f"{debt} required content missing: {missing!r}")

    controls_start = section_text.find(r"\subsection{Controls and Robustness}")
    if controls_start < 0:
        errors.append("cannot isolate Section 3.3")
        return
    controls = strip_tex_comments(section_text[controls_start:])
    try:
        controls_body = remove_balanced_command(controls, r"\footnote")
    except ValueError as exc:
        errors.append(str(exc))
        return
    inline_numbers = numeric_occurrences(controls_body)
    if len(inline_numbers) > 4:
        errors.append(
            "Section 3.3 has more than four inline result numbers "
            f"(tables/footnotes/model and budget ids excluded): {inline_numbers!r}"
        )


def check_section4_requirements(
    section_text: str,
    ledger: list[dict[str, Any]],
    results: Any,
    errors: list[str],
) -> None:
    visible_source = strip_tex_comments(section_text)
    visible = normalize_visible(section_text)

    expected_subsections = (
        "Installation Sanity: The Edited Association Remains Cloze-Detectable",
        "Visible In-Chain Routes",
        "The Chain-Routing Hypothesis and a Failed Replay Vehicle",
        "The Length-Only Account",
        "CLR-Stratified Enrichment and a Dose-Limited Boundary Test",
    )
    actual_subsections = tuple(
        re.findall(r"\\subsection\{([^{}]+)\}", visible_source)
    )
    if actual_subsections != expected_subsections:
        errors.append(
            "Section 4 subsection order/titles differ from the reviewed ceiling: "
            f"{actual_subsections!r}"
        )
    if re.search(r"\\subsection\*", visible_source):
        errors.append("Section 4 contains an unreviewed starred subsection")

    required_strings = (
        "This section assembles the diagnosis that motivates the primary intervention",
        "This is only an installation sanity check",
        "no control, no interval",
        "close to tautological",
        "conditional on the selected reversion sample",
        "audit sample overlap and membership composition",
        "reproduce the case-level tally",
        "supplement names the missing per-item artifact",
        "results/probe/logitlens_cf200_ROME_B3.jsonl",
        "we place no quantitative weight on this observation downstream",
        "drawn from six checkpoints across both backbone lineages",
        "greedy, short-budget, and sampled generations represented",
        "lexical candidacy is not equivalent to OLD membership by judge majority",
        "we do not transport that estimate to this pooled census",
        "outcome-conditioned failure surface",
        "non-sufficient for OLD commitment",
        "one external judge-model family",
        "prospectively specified attempt",
        "vehicle-validity gate is permanently Fail",
        "the stop rule prevented the planned semantic-control arms from running",
        "we withdraw the planned natural-chain mediation claim",
        "non-rescuing post-hoc audit",
        "do not identify a single mechanism",
        "neither confirmed nor refuted",
        "its controls do not route through replay",
        "do not form a length-matched contrast",
        "suppression may alter realized chain length",
        "we infer neither saturation nor an ordered trend",
        "an equal-length content-free filler remains untested",
        "content-independent computational-buffer account",
        "improves edit success and lowers permissive reversion",
        "while the strict displacement endpoint does not separate from that baseline",
        "realized chain lengths under suppression were not audited",
        "constrains a length-only reading rather than eliminating it",
        "arm-paired stratum totals, not RR denominators",
        "without an interaction test",
        "the pre-specified primary RR contrast was compatible with zero",
        "ES remained null-compatible",
        "a secondary concept-versus-shuffle contrast on the pre-specified LocAcc harm metric",
        "did not yield detectable confirmatory RR repair",
        "Neither observation identifies natural-chain mediation",
        "the test behind our chain-local causal control point",
    )
    for target in required_strings:
        if target not in visible:
            errors.append(f"Section 4 required target string missing: {target!r}")

    # "Prospectively specified" is reserved for protocols frozen in a dated
    # artifact before results existed; everything recorded afterwards is
    # "pre-specified".  Approving sites beats counting them: other
    # artifact-backed protocols (the frozen P0 judge files, per WRITING_PLAN
    # §5) can legitimately earn the label later without tripping this gate.
    for match in re.finditer(
        r"prospectively specified(?:\s+[A-Za-z-]+)?", visible
    ):
        if match.group(0) not in APPROVED_PROSPECTIVE_LABEL_SITES:
            errors.append(
                "Section 4 grants 'prospectively specified' at an unreviewed "
                f"site: {match.group(0)!r}; artifact-backed sites must be added "
                "to APPROVED_PROSPECTIVE_LABEL_SITES in the same change"
            )

    # The two nonnumeric states are tied directly to results.json rather than
    # weakening the numeric RJ schema.
    expected_states = {
        "/rq2_logitlens/p0_membership_crosswalk/status": (
            "BLOCKED_MISSING_PER_ITEM_ARTIFACT",
            "logit-lens per-item crosswalk",
        ),
        "/x1_replay_gate/gate/status": ("FAIL", "X1 replay gate"),
    }
    for pointer, (expected, label) in expected_states.items():
        try:
            observed = resolve_pointer(results, pointer)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            errors.append(f"Section 4 {label} state cannot be resolved: {exc}")
            continue
        if observed != expected:
            errors.append(
                f"Section 4 {label} state is {observed!r}, expected {expected!r}"
            )

    # Official failure, component decomposition, and post-hoc diagnosis must
    # stay in that order; the independent Section 5 firewall follows them.
    ordered_targets = (
        "9/18",
        "14/18",
        "12/18",
        "non-rescuing post-hoc audit",
        "13/18",
        "1/5",
        "neither confirmed nor refuted",
        "its controls do not route through replay",
    )
    offsets = [visible.find(target) for target in ordered_targets]
    if any(offset < 0 for offset in offsets) or offsets != sorted(offsets):
        errors.append(
            "Section 4 X1 disclosure order must be FAIL -> decomposition -> "
            "non-rescuing diagnosis -> terminal ruling -> replay-independent controls"
        )

    # High-risk length claims must retain their reviewed source identities.
    required_bindings = {
        (".631", "/rq3/sup_battery/marginal_B3/T/ES", "fixed:3"),
        (".595", "/capability/families/R1-Distill-Qwen/es_b0/3", "fixed:3"),
        (".208", "/f2_zerothink_deconfound/arms/B1/RR", "fixed:3"),
        (".193", "/capability/families/R1-Distill-Qwen/rr/3", "fixed:3"),
        (".040", "/f2_zerothink_deconfound/arms/B0P/RR", "fixed:3"),
    }
    actual_bindings = {
        (entry["display"], entry["pointer"], entry["format"])
        for entry in ledger
    }
    missing_bindings = sorted(required_bindings - actual_bindings)
    if missing_bindings:
        errors.append(f"Section 4 required M06 bindings missing: {missing_bindings!r}")

    # Panel identity, not merely numeric equality, determines each kappa.
    kappa_specs = {
        "/rq2_taxonomy/p0_corrected_taxonomy/agreement/fleiss_kappa": (
            ".813",
            "route-panel",
        ),
        "/rq2_taxonomy/p0_membership_reaudit/membership_votes/membership_fleiss_kappa": (
            ".958",
            "answer-only membership gate",
        ),
        "/x1_replay_gate/judge_agreement/fleiss_kappa": (
            ".9195",
            "replay answer judges",
        ),
    }
    section_lines = section_text.splitlines()
    for pointer, (display, context) in kappa_specs.items():
        entries = [entry for entry in ledger if entry["pointer"] == pointer]
        if len(entries) != 1 or entries[0]["display"] != display:
            errors.append(
                f"Section 4 kappa identity mismatch for {pointer}: "
                f"{[(entry['display'], entry['source_line']) for entry in entries]!r}"
            )
            continue
        line_number = entries[0]["source_line"]
        line_visible = normalize_visible(section_lines[line_number - 1])
        if context not in line_visible:
            errors.append(
                f"Section 4 kappa {display} lacks its {context!r} context"
            )

    check_authoritative_cloze_ratio(results, errors)

    if re.search(
        r"(?:fig2|table)[-_]?(?:logitlens|rq2)",
        visible_source,
        flags=re.IGNORECASE,
    ):
        errors.append("Section 4 references a superseded diagnostic asset")
    if r"\includegraphics" in visible_source:
        errors.append(
            "Section 4 external diagnostic assets require a separate reviewed landing"
        )


def check_narrative_section_requirements(
    section_label: str,
    section_text: str,
    errors: list[str],
) -> None:
    """Memory anchors and framing rules for the non-numeric sections."""

    visible_source = strip_tex_comments(section_text)
    visible = normalize_visible(section_text)

    if section_label == "Section 1":
        # The bolded contribution head is what reviewers copy into summaries.
        if r"\textbf{A chain-local causal control point.}" not in visible_source:
            errors.append(
                "Section 1 must open contribution two with the bolded verbatim "
                "head 'A chain-local causal control point.'"
            )
        if "Does thinking undo editing?" not in visible:
            errors.append("Section 1 must keep the approved hook question")
        if "chain-local causal control point" not in visible.split(". ")[-1]:
            errors.append(
                "Section 1 must close on the chain-local causal control point"
            )
    elif section_label == "Section 2":
        if "Four properties are not addressed jointly" not in visible:
            errors.append(
                "Section 2 must state the four-property boundary, not a priority claim"
            )
        for citation, role in (
            ("he2025scr", "SCR method paper"),
            ("he2025benchmarking", "realistic-autoregressive benchmark"),
            ("hua2024recoe", "ReCoE propagation"),
        ):
            if citation not in visible_source:
                errors.append(f"Section 2 is missing the {role} citation")
    elif section_label == "Section 7":
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", visible) if s.strip()]
        if not sentences or "chain-local causal control point" not in sentences[-1]:
            errors.append(
                "the paper's final sentence must contain the verbatim anchor phrase"
            )
    elif section_label == "Ethical Statement":
        required = (
            "edited-query gated",
            "updating no weights and applying no optimization toward concealment",
            "\\(0\\) of \\(41\\)".replace("\\(", "").replace("\\)", ""),
            "we do not claim that the absence of such a trace could serve as a monitor",
        )
        for target in required:
            if target not in visible:
                errors.append(
                    f"Ethical Statement required target string missing: {target!r}"
                )


def check_section5_requirements(
    section_text: str,
    ledger: list[dict[str, Any]],
    errors: list[str],
) -> None:
    visible_source = strip_tex_comments(section_text)
    visible = normalize_visible(section_text)

    expected_subsections = (
        "A Signed, Dose-Graded Think-Span Intervention",
        "The Control Point Moves the Untouched Answer",
        "What the Placebo and Competitor Arms Bound",
        "Endpoint Hierarchy and Multiplicity",
        "How Far the Guard Transfers",
    )
    actual_subsections = tuple(
        re.findall(r"\\subsection\{([^{}]+)\}", visible_source)
    )
    if actual_subsections != expected_subsections:
        errors.append(
            "Section 5 subsection order/titles differ from the reviewed ceiling: "
            f"{actual_subsections!r}"
        )
    if re.search(r"\\subsection\*", visible_source):
        errors.append("Section 5 contains an unreviewed starred subsection")

    required_strings = (
        # The frozen protocol names T-P, not T-N, as the primary contrast.
        "The primary contrast was fixed in advance as T versus P",
        "before any suppressed arm ran",
        "so the reading does not turn on which control the treated arm is measured against",
        # Anti-tautology defenses.
        "nothing is penalized in the answer text",
        "extending the same penalty to the answer span",
        "manipulation check on whether the penalty acted inside the span, not an outcome",
        # Treatment-independent gate, without borrowing the MEMIT audit.
        "the think span is empty, so a think-scoped processor has nothing to act on",
        "belongs to the MEMIT replication",
        "has no changed-row audit of its own",
        # Dose ladder without an ordered-trend claim.
        "Every suppressed setting leaves the in-span leakage check below the zero-penalty setting",
        "a dose ladder rather than a calibrated dose-response",
        # M14 marginal-versus-paired reconciliation, both endpoint pairs.
        "need not equal differences of arm-wise rates",
        "does not equal",
        "is the same Qwen-32B run as the largest Qwen cell",
        # D6 control bounds.
        "compatible with zero; we set no equivalence margin",
        # W2-13/F4: the old anchor granted inertness at the answer level, which the
        # preceding paragraph explicitly withholds.  The ceiling is compatibility.
        "at the answer level the comparison is compatible with zero",
        # D7 endpoint hierarchy and multiplicity.
        "That interval reaches zero.",
        "paired cases clearing the zero-thinking gate in both arms",
        "unadjusted and we claim no correction",
        "without multiplicity adjustment, and we claim none",
        # The battery's own scope limit, carried from the frozen protocol.
        "every arm here is an intervened condition",
        "required in ordinary, uninterrupted generation",
        # R1 transfer ceilings.
        "not a second editor",
        "transfers the intervention and not the gap",
        "not portability to unguarded queries",
        "a floor rather than an equivalence result",
        # Positioning.
        "mechanistic probe and an edit-aware decoding guard",
    )
    for target in required_strings:
        if target not in visible:
            errors.append(f"Section 5 required target string missing: {target!r}")

    # The battery protocol is a git-recorded prereg, not a result-preceding
    # artifact SHA, so it never earns the stronger label.
    if "prospectively specified" in visible:
        errors.append(
            "Section 5 must say 'fixed in advance'/'pre-specified'; the battery "
            "protocol has no result-preceding artifact SHA"
        )

    # R10: the abstract's arrow must bind to the battery arms, not to the
    # Section 3 capability cell that happens to carry the same level.
    required_bindings = {
        ("19.3", "/rq3/sup_battery/marginal_B3/N/RR", "percent:1"),
        ("8.5", "/rq3/sup_battery/marginal_B3/T/RR", "percent:1"),
        ("+.122", "/rq3/sup_battery/contrasts_B3_mean_ci_p/T_minus_P/ES/0", "signed:3"),
        (".580", "/rq3/alpha_sweep/scope_ablation/think/ES_B0", "fixed:3"),
        (".727", "/rq3/alpha_sweep/scope_ablation/all/ES_B0", "fixed:3"),
        ("118", "/rq3/clr_split_M1/mediation_2x2/n_b0ok", "integer"),
    }
    actual_bindings = {
        (entry["display"], entry["pointer"], entry["format"])
        for entry in ledger
    }
    missing_bindings = sorted(required_bindings - actual_bindings)
    if missing_bindings:
        errors.append(f"Section 5 required bindings missing: {missing_bindings!r}")


def check_authoritative_cloze_ratio(
    results: Any,
    errors: list[str],
) -> None:
    """Require the frozen cloze record to encode exactly n/n = 100%."""

    try:
        ratio = resolve_pointer(
            results, "/rq2_logitlens/_authoritative_record/edit_intact_at_cloze"
        )
        n_value = resolve_pointer(
            results, "/rq2_logitlens/_authoritative_record/n"
        )
        ratio_match = (
            re.fullmatch(r"(\d+)/(\d+)=([0-9.]+)%", ratio)
            if isinstance(ratio, str)
            else None
        )
        valid = False
        if ratio_match and isinstance(n_value, int) and not isinstance(n_value, bool):
            numerator = int(ratio_match.group(1))
            denominator = int(ratio_match.group(2))
            percent = Decimal(ratio_match.group(3))
            valid = numerator == denominator == n_value and percent == Decimal(100)
        if not valid:
            errors.append(
                "Section 4 authoritative cloze ratio must equal n/n=100%"
            )
    except (InvalidOperation, KeyError, IndexError, TypeError, ValueError) as exc:
        errors.append(f"Section 4 authoritative cloze ratio cannot be checked: {exc}")


def check_marginal_denominator_identities(
    results: Any,
    errors: list[str],
) -> None:
    """Verify the Qwen-32B denominators that Sections 3 and 4 state in prose.

    The Table 1 caption and the Section 4.4 footnote both report the Qwen-32B
    \\(B_0\\) marginal level over 200 attempted rows while paired and treated
    levels use smaller effective arm counts.  ``/rq3/n`` supplies that 200, so
    two facts must hold for the prose to stay true.  First, the capability cell
    and the battery's no-suppression arm have to be the same run: they are
    separate result blocks, and only their agreement licenses reading a battery
    count as the capability cell's denominator.  Second, the attempted count
    must dominate every effective arm count and must divide the reported
    \\(B_0\\) level into a whole number of successes.
    """

    try:
        nominal = decimal_value(resolve_pointer(results, "/rq3/n"))
        arm_counts = resolve_pointer(results, "/rq3/sup_battery/n")
        es_b0 = decimal_value(
            resolve_pointer(
                results, "/capability/families/R1-Distill-Qwen/es_b0/3"
            )
        )
        shared_endpoints = {
            "ES_B3": "/capability/families/R1-Distill-Qwen/es_b3/3",
            "ES_drop": "/capability/families/R1-Distill-Qwen/es_drop/3",
            "RR": "/capability/families/R1-Distill-Qwen/rr/3",
            "CLR": "/capability/families/R1-Distill-Qwen/clr/3",
        }
        # Compare at the published three-decimal display caliber.  The blocks
        # record the same quantities at different precision by design (the
        # battery note carries CLR .5455 = 108/198), so exact equality would
        # turn a legitimate precision upgrade into a failure.
        caliber = Decimal("0.001")
        for endpoint, capability_pointer in shared_endpoints.items():
            battery_value = decimal_value(
                resolve_pointer(results, f"/rq3/baseline/{endpoint}")
            ).quantize(caliber, rounding=ROUND_HALF_UP)
            capability_value = decimal_value(
                resolve_pointer(results, capability_pointer)
            ).quantize(caliber, rounding=ROUND_HALF_UP)
            if battery_value != capability_value:
                errors.append(
                    "Qwen-32B capability cell and battery no-suppression arm "
                    f"disagree on {endpoint} ({capability_value} vs "
                    f"{battery_value}); the shared-denominator prose in "
                    "Sections 3 and 4 no longer holds"
                )
        if not isinstance(arm_counts, dict) or not arm_counts:
            raise TypeError("battery arm counts must be a non-empty object")
        # Annotation keys may be added to the arm-count block at any time.
        effective_counts = [
            decimal_value(count)
            for key, count in arm_counts.items()
            if not key.startswith("_")
        ]
        if not effective_counts:
            raise TypeError("battery arm counts contain no arm entries")
        largest_effective = max(effective_counts)
        if nominal < largest_effective:
            errors.append(
                f"attempted row count {nominal} is below the largest effective "
                f"arm count {largest_effective}"
            )
        successes = es_b0 * nominal
        if successes != successes.to_integral_value():
            errors.append(
                f"Qwen-32B B_0 marginal level {es_b0} is not a whole count over "
                f"{nominal} attempted rows (implies {successes} successes)"
            )
    except (InvalidOperation, KeyError, IndexError, TypeError, ValueError) as exc:
        errors.append(f"Qwen-32B marginal denominators cannot be checked: {exc}")


def check_unaudited_section_numbers(main_text: str, errors: list[str]) -> None:
    """Reject numbers in sections whose occurrence-level ledgers have not landed."""

    numbered_markers = [
        rf"\section{{{title}}}" for title in REQUIRED_SECTION_ORDER
    ]
    ethical_marker = r"\section*{Ethical Statement}"
    bibliography_marker = r"\bibliography{refs}"
    regions: list[tuple[str, str, str]] = []
    for index, title in enumerate(REQUIRED_SECTION_ORDER):
        start_marker = numbered_markers[index]
        if index + 1 < len(numbered_markers):
            end_marker = numbered_markers[index + 1]
        else:
            end_marker = ethical_marker
        regions.append((title, start_marker, end_marker))
    regions.append(("Ethical Statement", ethical_marker, bibliography_marker))

    for title, start_marker, end_marker in regions:
        if title in AUDITED_SECTION_TITLES:
            continue
        try:
            region = extract_between_markers(
                main_text,
                start_marker,
                end_marker,
                f"unaudited section {title}",
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        numbers = numeric_occurrences(strip_tex_comments(region))
        if numbers:
            errors.append(
                f"unaudited section {title!r} contains numeric tokens {numbers!r}; "
                "add that section's occurrence-level RJ audit before prose numbers"
            )


def check_unsectioned_body_numbers(main_text: str, errors: list[str]) -> None:
    """Reject authored numbers in document-body gaps outside the abstract/sections."""

    regions = (
        (
            "pre-abstract front matter",
            r"\begin{document}",
            r"\begin{abstract}",
        ),
        (
            "post-abstract front matter",
            r"\end{abstract}",
            r"\section{Introduction}",
        ),
        (
            "post-bibliography tail",
            r"\bibliography{refs}",
            r"\end{document}",
        ),
    )
    for label, start_marker, end_marker in regions:
        try:
            region = extract_between_markers(
                main_text,
                start_marker,
                end_marker,
                f"unpartitioned document-body region {label}",
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        numbers = numeric_occurrences(strip_tex_comments(region))
        if numbers:
            errors.append(
                f"unpartitioned document-body region {label!r} contains "
                f"numeric tokens {numbers!r}"
            )


def numeric_decimal(value: str) -> Decimal:
    try:
        return Decimal(value.replace("\N{MINUS SIGN}", "-"))
    except InvalidOperation as exc:
        raise ValueError(f"invalid numeric display {value!r}") from exc


def check_abstract_body_bindings(
    main_text: str,
    ledger: list[dict[str, Any]],
    results: Any,
    errors: list[str],
) -> None:
    """Cross-check frozen abstract numbers against reviewed body RJ displays.

    The exact missing-value set is a self-retiring debt: adding the Section 5
    8.5% RJ binding without deleting the debt makes this check fail.
    """

    visible_source = strip_tex_comments(main_text)
    abstract_match = re.search(
        r"\\begin\{abstract\}\s*\n(.*?)\n\\end\{abstract\}",
        visible_source,
        flags=re.DOTALL,
    )
    if not abstract_match:
        return

    abstract_values = {
        numeric_decimal(value)
        for value in numeric_occurrences(abstract_match.group(1))
    }
    body_values = {
        numeric_decimal(entry["display"])
        for entry in ledger
    }
    missing_values = abstract_values - body_values
    debt_values = {
        numeric_decimal(display)
        for display in PENDING_ABSTRACT_BODY_BINDINGS
    }

    for display, specification in PENDING_ABSTRACT_BODY_BINDINGS.items():
        try:
            value = resolve_pointer(results, specification["pointer"])
            rendered = format_result(
                value, specification["format"], specification["pointer"]
            )
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            errors.append(f"abstract binding debt {display!r}: {exc}")
            continue
        if rendered != display:
            errors.append(
                f"abstract binding debt {display!r} != {rendered!r} from "
                f"{specification['pointer']} via {specification['format']}"
            )

    if missing_values != debt_values:
        rendered_missing = sorted(str(value) for value in missing_values)
        rendered_debt = sorted(str(value) for value in debt_values)
        errors.append(
            "frozen-abstract numeric coverage differs from the exact "
            f"self-retiring debt: missing={rendered_missing}, debt={rendered_debt}. "
            "When Section 5 binds 8.5%, remove PENDING_ABSTRACT_BODY_BINDINGS "
            "in the same commit."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main", type=Path, default=DEFAULT_MAIN)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument(
        "--ledger-out",
        type=Path,
        help="optional path for the extracted, validated RJ ledger",
    )
    return parser.parse_args()


# W2-15: two hard-coded strings used to stand in for this.  They caught nothing
# when Section 5.3 grew a promise of its own, because the guard was a list of
# known promises rather than a rule about all of them.
SUPPLEMENT_PROMISE_RE = re.compile(
    r"(?i)\bthe supplement\b|\bsupplementary (?:figures?|material)\b"
    r"|\bprovenance (?:record|manifest)\b|\breleased code\b"
)
NUMBER_WORDS = {
    1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
    7: "seven", 8: "eight", 9: "nine", 10: "ten",
}


def check_supplement_promises(main_path: Path, errors: list[str]) -> None:
    """Every deferral to an external artifact must be answered, one for one.

    Counting was not enough: W2-15 rewrote a promise into a phrasing the pattern
    did not match, and the count stayed consistent while the promise lost its
    home.  Each ``% Discharges:`` now carries a verbatim substring of the promise
    it answers, long enough to be unambiguous, and the gate checks that the
    substring occurs exactly once in the body and that every promise sits inside
    exactly one such span.  Copying a fragment cannot drift; paraphrasing it can.
    """
    body = strip_tex_comments(main_path.read_text(encoding="utf-8"))
    promises = [m.span() for m in SUPPLEMENT_PROMISE_RE.finditer(body)]

    supplement = (
        Path(__file__).resolve().parent.parent / "paperwriting/manuscript/supplement.tex"
    )
    if not supplement.exists():
        if promises:
            errors.append(
                f"the body makes {len(promises)} external-artifact promise(s) but "
                f"{supplement.name} does not exist"
            )
        return

    text = supplement.read_text(encoding="utf-8")
    quotes = re.findall(r'^% Discharges: "(.+?)"\s*$', text, flags=re.M)
    spans: list[tuple[int, int]] = []
    for quote in quotes:
        if len(quote) < 40:
            errors.append(
                f"'% Discharges:' quote is too short to identify a promise "
                f"({len(quote)} chars): {quote!r}"
            )
            continue
        hits = [m.span() for m in re.finditer(re.escape(quote), body)]
        if len(hits) != 1:
            errors.append(
                f"'% Discharges:' quote matches the body {len(hits)} time(s), "
                f"must be exactly once: {quote!r}"
            )
            continue
        spans.append(hits[0])

    for start, end in promises:
        owners = [c for c in spans if c[0] <= start and end <= c[1]]
        if len(owners) != 1:
            context = " ".join(body[max(0, start - 90):end + 20].split())
            errors.append(
                f"external-artifact promise covered by {len(owners)} "
                f"'% Discharges:' quote(s), must be exactly one: ...{context}"
            )

    sections = re.findall(r"^\\section\{", text, flags=re.M)
    markers = re.findall(r"^% (?:Discharges|Supports):", text, flags=re.M)
    if len(sections) > len(markers):
        errors.append(
            f"supplement.tex has {len(sections)} numbered section(s) but only "
            f"{len(markers)} carry a '% Discharges:'/'% Supports:' marker"
        )

    stated = re.search(r"discharges the ([a-z]+) places", text)
    if stated:
        want = NUMBER_WORDS.get(len(promises))
        if want and stated.group(1) != want:
            errors.append(
                f"supplement.tex says it discharges '{stated.group(1)}' places; "
                f"the body makes {len(promises)} ({want})"
            )
    else:
        errors.append("supplement.tex must state how many places it discharges")


def check_artifact_anonymity(main_path: Path, errors: list[str]) -> None:
    """Fail if any shipped artifact carries an identity string (W2-8 / A0-4).

    The leak this catches is invisible to ``strings``/``grep``/exiftool: a figure's
    ``/Creator`` becomes part of a Flate-compressed object stream once the figure is
    embedded in ``main.pdf``.  ``scrub_artifacts`` inflates every stream before
    matching, which is why the gate delegates rather than re-implementing a scan.

    A missing ``main.pdf`` is not an error: it is gitignored and rebuilt on demand.
    Everything that *is* committed is still checked.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from scrub_artifacts import leaks_in, targets
    except ImportError as exc:  # pragma: no cover - import wiring only
        errors.append(f"anonymity gate unavailable: {exc}")
        return
    for artifact in targets():
        if not artifact.exists():
            continue
        hits = leaks_in(artifact)
        if hits:
            errors.append(
                f"anonymity leak in {artifact.name}: {', '.join(hits)}"
            )
    built = main_path.parent / "main.pdf"
    if built.exists():
        hits = leaks_in(built)
        if hits:
            errors.append(f"anonymity leak in built main.pdf: {', '.join(hits)}")


def main() -> int:
    args = parse_args()
    errors: list[str] = []

    if not args.main.is_file():
        print(f"FAIL: missing manuscript source: {args.main}", file=sys.stderr)
        return 1
    if args.results.resolve() != DEFAULT_RESULTS.resolve():
        print(
            "FAIL: numeric source must be the canonical paperwriting/results.json",
            file=sys.stderr,
        )
        return 1
    if not args.results.is_file():
        print(f"FAIL: missing numeric source: {args.results}", file=sys.stderr)
        return 1

    main_text = args.main.read_text(encoding="utf-8")
    try:
        results = json.loads(
            args.results.read_text(encoding="utf-8"),
            parse_float=Decimal,
        )
    except (json.JSONDecodeError, OSError) as exc:
        print(f"FAIL: cannot load results.json: {exc}", file=sys.stderr)
        return 1

    check_template_and_frozen_surfaces(main_text, args.main, errors)
    check_global_claim_language(main_text, errors)
    check_marginal_denominator_identities(results, errors)
    check_unaudited_section_numbers(main_text, errors)
    check_unsectioned_body_numbers(main_text, errors)
    combined_ledger: list[dict[str, Any]] = []
    section_counts: dict[str, int] = {}
    global_claim_ids: set[str] = set()
    for specification in AUDITED_SECTION_SPECS:
        section_label = specification["label"]
        start_marker, end_marker = section_markers(specification)
        try:
            section_text = extract_between_markers(
                main_text, start_marker, end_marker, section_label
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue

        section_ledger = check_rj_ledger(
            section_text,
            results,
            errors,
            section_label,
            global_claim_ids,
            specification.get("requires_ledger", True),
        )
        if section_label == "Section 3":
            check_section3_requirements(section_text, errors)
        elif section_label == "Section 4":
            check_section4_requirements(
                section_text, section_ledger, results, errors
            )
        elif section_label == "Section 5":
            check_section5_requirements(section_text, section_ledger, errors)
        else:
            check_narrative_section_requirements(
                section_label, section_text, errors
            )

        bindings_sha256 = ledger_bindings_sha256(section_ledger)
        expected_sha256 = APPROVED_SECTION_LEDGER_BINDINGS_SHA256[section_label]
        if bindings_sha256 != expected_sha256:
            errors.append(
                f"{section_label} RJ claim/path/format bindings differ from the "
                f"reviewed ledger (actual SHA256 {bindings_sha256})"
            )
        visible_sha256 = section_visible_sha256(section_text)
        expected_visible_sha256 = APPROVED_SECTION_VISIBLE_SHA256[section_label]
        if visible_sha256 != expected_visible_sha256:
            errors.append(
                f"{section_label} visible semantic surface differs from the "
                f"reviewed snapshot (actual SHA256 {visible_sha256})"
            )
        source_sha256 = section_source_sha256(section_text)
        expected_source_sha256 = APPROVED_SECTION_SOURCE_SHA256[section_label]
        if source_sha256 != expected_source_sha256:
            errors.append(
                f"{section_label} TeX source structure differs from the "
                f"reviewed snapshot (actual SHA256 {source_sha256})"
            )
        combined_ledger.extend(section_ledger)
        section_counts[section_label] = len(section_ledger)

    check_abstract_body_bindings(main_text, combined_ledger, results, errors)
    check_artifact_anonymity(args.main, errors)
    check_supplement_promises(args.main, errors)

    if errors:
        print(f"FAIL: {len(errors)} manuscript check(s) failed", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if args.ledger_out:
        args.ledger_out.parent.mkdir(parents=True, exist_ok=True)
        args.ledger_out.write_text(
            json.dumps(combined_ledger, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print(
        "PASS: frozen title/abstract, adjacent template copies, full-manuscript "
        "language gates, unaudited-section numeric gates, "
        f"Section 3 RJ ledger ({section_counts.get('Section 3', 0)} occurrences), "
        f"Section 4 RJ ledger ({section_counts.get('Section 4', 0)} occurrences), "
        f"Section 5 RJ ledger ({section_counts.get('Section 5', 0)} occurrences), "
        "claim targets, and full abstract coverage"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
