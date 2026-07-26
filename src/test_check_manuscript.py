from __future__ import annotations

import json
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER = REPO_ROOT / "src" / "check_manuscript.py"
MANUSCRIPT_DIR = REPO_ROOT / "paperwriting" / "manuscript"


@pytest.fixture
def candidate_main(tmp_path: Path) -> Path:
    for filename in ("main.tex", "aaai2027.sty", "aaai2027.bst", "refs.bib"):
        shutil.copy2(MANUSCRIPT_DIR / filename, tmp_path / filename)
    return tmp_path / "main.tex"


def run_checker(main_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--main", str(main_path)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def mutate(main_path: Path, old: str, new: str) -> None:
    text = main_path.read_text(encoding="utf-8")
    assert text.count(old) == 1, f"mutation anchor count for {old!r} is not one"
    main_path.write_text(text.replace(old, new, 1), encoding="utf-8")


def assert_rejected(main_path: Path, *diagnostics: str) -> str:
    completed = run_checker(main_path)
    output = completed.stdout + completed.stderr
    assert completed.returncode != 0, output
    for diagnostic in diagnostics:
        assert diagnostic in output, output
    return output


def test_canonical_manuscript_passes(candidate_main: Path) -> None:
    completed = run_checker(candidate_main)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "Section 3 RJ ledger (111 occurrences)" in completed.stdout
    assert "Section 4 RJ ledger (64 occurrences)" in completed.stdout
    assert "Section 5 RJ ledger (191 occurrences)" in completed.stdout


def test_frozen_abstract_mutation_is_rejected(candidate_main: Path) -> None:
    mutate(
        candidate_main,
        "lowers the resurfacing rate from 19.3\\% to 8.5\\%",
        "lowers the resurfacing rate from 19.3\\% to 8.6\\%",
    )
    assert_rejected(
        candidate_main,
        "LaTeX abstract differs from frozen v8.1",
        "frozen-abstract numeric coverage differs",
    )


def test_commented_boundary_cannot_hide_unledgered_number(
    candidate_main: Path,
) -> None:
    marker = r"\section{Causal Diagnosis}"
    mutate(
        candidate_main,
        marker,
        "%\\section{Causal Diagnosis}\n"
        "Unledgered value 999.\n"
        + marker,
    )
    assert_rejected(candidate_main, "numeric occurrences ['999']")


def test_duplicate_author_is_rejected(candidate_main: Path) -> None:
    mutate(
        candidate_main,
        r"\author{Anonymous Submission}",
        "\\author{Anonymous Submission}\n\\author{Named Author}",
    )
    assert_rejected(candidate_main, "anonymous author marker is missing")


@pytest.mark.parametrize(
    ("injected", "diagnostic"),
    [
        (r"\ifnum1=0 Hidden 999.\fi", "forbidden manuscript construct (TeX conditional)"),
        (r"\phantom{999}", "forbidden manuscript construct (invisible phantom box)"),
    ],
)
def test_nonrendered_source_bypasses_are_rejected(
    candidate_main: Path,
    injected: str,
    diagnostic: str,
) -> None:
    marker = r"\section{Introduction}"
    mutate(candidate_main, marker, marker + "\n" + injected)
    assert_rejected(candidate_main, diagnostic)


def test_parameter_count_mutation_is_rejected(candidate_main: Path) -> None:
    mutate(candidate_main, "Qwen  & 1.5B", "Qwen  & 2B")
    assert_rejected(
        candidate_main,
        "numeric occurrences ['2', '.582', '.607'",
        "RJ occurrences ['1.5', '.582', '.607'",
    )


def test_reordered_rj_entries_are_rejected(candidate_main: Path) -> None:
    first = (
        '{"claim":"T1-Q15-params","display":"1.5",'
        '"pointer":"/capability/families/R1-Distill-Qwen/params_b/0",'
        '"format":"fixed:1"}'
    )
    second = (
        '{"claim":"T1-Q15-es0","display":".582",'
        '"pointer":"/capability/families/R1-Distill-Qwen/es_b0/0",'
        '"format":"fixed:3"}'
    )
    mutate(candidate_main, first + "," + second, second + "," + first)
    assert_rejected(
        candidate_main,
        "numeric occurrences ['1.5', '.582'",
        "RJ occurrences ['.582', '1.5'",
    )


def test_extra_valid_ledger_binding_is_rejected(candidate_main: Path) -> None:
    marker = r"\subsection{The Gap}"
    injected = (
        "Overall reversion is \\(.193\\). "
        '% RJ: {"claim":"EXTRA-rr","display":".193",'
        '"pointer":"/capability/families/R1-Distill-Qwen/rr/3",'
        '"format":"fixed:3"}\n\n'
    )
    mutate(candidate_main, marker, injected + marker)
    assert_rejected(candidate_main, "bindings differ from the reviewed ledger")


def test_tex_split_banned_phrase_is_rejected(candidate_main: Path) -> None:
    marker = r"\subsection{The Gap}"
    mutate(candidate_main, marker, "This is a scal\\-ing law.\n\n" + marker)
    assert_rejected(candidate_main, "banned language (scaling-law language)")


def test_metric_negation_is_part_of_the_reviewed_semantic_surface(
    candidate_main: Path,
) -> None:
    mutate(
        candidate_main,
        r"\land\neg h_{\mathrm{old}}(a_b)",
        r"\land h_{\mathrm{old}}(a_b)",
    )
    assert_rejected(
        candidate_main,
        "Section 3 visible semantic surface differs from the reviewed snapshot",
    )


def test_metric_grouping_is_part_of_the_reviewed_tex_structure(
    candidate_main: Path,
) -> None:
    mutate(
        candidate_main,
        r"h_{\mathrm{new}}(a_b)\land",
        r"h_\mathrm{new}(a_b)\land",
    )
    assert_rejected(
        candidate_main,
        "Section 3 TeX source structure differs from the reviewed snapshot",
    )


def test_tex_comment_splice_banned_phrase_is_rejected(
    candidate_main: Path,
) -> None:
    marker = r"\section{Introduction}"
    mutate(
        candidate_main,
        marker,
        marker + "\nThis is a scal% splice\n" + "ing law.",
    )
    assert_rejected(candidate_main, "banned language (scaling-law language)")


@pytest.mark.parametrize("value", ["0.545", ".123"])
def test_english_in_is_not_misread_as_layout_unit(
    candidate_main: Path,
    value: str,
) -> None:
    marker = r"\subsection{The Gap}"
    mutate(
        candidate_main,
        marker,
        f"The drop is {value} in this cell.\n\n" + marker,
    )
    assert_rejected(candidate_main, f"numeric occurrences ['{value}']")


def test_full_manuscript_banned_language_gate(candidate_main: Path) -> None:
    marker = r"\section{Introduction}"
    mutate(candidate_main, marker, marker + "\nThis is a scaling law.")
    assert_rejected(candidate_main, "banned language (scaling-law language)")


@pytest.mark.parametrize(
    "marker",
    [
        r"\section{Introduction}",
        r"\section{Related Work}",
        r"\section{Discussion \& Limitations}",
        r"\section{Conclusion}",
        r"\section*{Ethical Statement}",
    ],
)
def test_narrative_sections_reject_numeric_tokens(
    candidate_main: Path,
    marker: str,
) -> None:
    mutate(candidate_main, marker, marker + "\nThe unsupported value is .546.")
    assert_rejected(
        candidate_main,
        "numeric occurrences ['.546'] do not match RJ occurrences []",
    )


@pytest.mark.parametrize(
    ("value", "label"),
    [
        (".545", "stale bare .545"),
        ("0.765", "stale bare .765"),
    ],
)
def test_stale_values_are_rejected_manuscript_wide(
    candidate_main: Path,
    value: str,
    label: str,
) -> None:
    marker = r"\section{Introduction}"
    mutate(candidate_main, marker, marker + f"\nThe stale value is {value}.")
    assert_rejected(candidate_main, f"stale manuscript claim ({label})")


def test_stale_kappa_is_rejected_after_tex_normalization(
    candidate_main: Path,
) -> None:
    marker = r"\section{Introduction}"
    mutate(
        candidate_main,
        marker,
        marker + "\nThe stale agreement is \\(\\kappa=.790\\).",
    )
    assert_rejected(candidate_main, "stale manuscript claim (superseded route kappa)")


def test_abstract_binding_debt_is_retired() -> None:
    namespace = runpy.run_path(str(CHECKER))
    assert namespace["PENDING_ABSTRACT_BODY_BINDINGS"] == {}


def test_abstract_coverage_breaks_if_section5_stops_binding_the_arrow(
    candidate_main: Path,
) -> None:
    """The retired debt is now load-bearing: Section 5 alone covers 8.5%."""
    text = candidate_main.read_text(encoding="utf-8")
    assert text.count('"display":"8.5"') == 2
    candidate_main.write_text(
        text.replace('"display":"8.5"', '"display":"8.6"'), encoding="utf-8"
    )
    assert_rejected(candidate_main, "frozen-abstract numeric coverage differs")


@pytest.mark.parametrize("filename", ["aaai2027.sty", "aaai2027.bst"])
def test_custom_main_checks_adjacent_author_kit_copy(
    candidate_main: Path,
    filename: str,
) -> None:
    template_path = candidate_main.parent / filename
    template_path.write_text(
        template_path.read_text(encoding="utf-8") + "\n% mutated test copy\n",
        encoding="utf-8",
    )
    assert_rejected(candidate_main, f"{filename} is missing or differs from AuthorKit27")


def test_mutated_bibliography_is_rejected(candidate_main: Path) -> None:
    refs_path = candidate_main.parent / "refs.bib"
    refs_path.write_text(
        refs_path.read_text(encoding="utf-8") + "\n% unreviewed mutation\n",
        encoding="utf-8",
    )
    assert_rejected(
        candidate_main,
        "refs.bib is missing or differs from the reviewed bibliography",
    )


def test_missing_bibliography_is_rejected(candidate_main: Path) -> None:
    (candidate_main.parent / "refs.bib").unlink()
    assert_rejected(
        candidate_main,
        "refs.bib is missing or differs from the reviewed bibliography",
    )


def test_section4_rejects_unledgered_number(candidate_main: Path) -> None:
    marker = r"\subsection{The Length-Only Account}"
    mutate(
        candidate_main,
        marker,
        "The unsupported Section 4 value is .546.\n\n" + marker,
    )
    assert_rejected(
        candidate_main,
        "Section 4 line",
        "numeric occurrences ['4', '.546']",
    )


def test_section4_subsection_order_is_frozen(candidate_main: Path) -> None:
    first = (
        r"\subsection{Installation Sanity: "
        r"The Edited Association Remains Cloze-Detectable}"
    )
    second = r"\subsection{Visible In-Chain Routes}"
    mutate(candidate_main, first, r"\subsection{TEMPORARY-HEADING}")
    mutate(candidate_main, second, first)
    mutate(candidate_main, r"\subsection{TEMPORARY-HEADING}", second)
    assert_rejected(candidate_main, "Section 4 subsection order/titles differ")


def test_x1_disclosure_order_is_enforced(candidate_main: Path) -> None:
    decomposition = "Both prerequisites limited the conjunction:"
    mutate(
        candidate_main,
        decomposition,
        "A non-rescuing post-hoc audit precedes the decomposition.  "
        + decomposition,
    )
    mutate(
        candidate_main,
        "A non-rescuing post-hoc audit found",
        "A post-hoc audit found",
    )
    assert_rejected(candidate_main, "Section 4 X1 disclosure order")


def test_x1_terminal_ruling_is_required(candidate_main: Path) -> None:
    mutate(
        candidate_main,
        "natural-chain mediation is neither confirmed nor refuted",
        "natural-chain mediation remains untested",
    )
    assert_rejected(
        candidate_main,
        "Section 4 required target string missing: 'neither confirmed nor refuted'",
        "Section 4 X1 disclosure order",
    )


def test_kappa_panel_labels_cannot_be_interchanged(candidate_main: Path) -> None:
    mutate(candidate_main, "route-panel Fleiss'", "answer-membership Fleiss'")
    mutate(
        candidate_main,
        "The answer-only membership gate",
        "The route-panel gate",
    )
    assert_rejected(
        candidate_main,
        "kappa .813 lacks its 'route-panel' context",
        "kappa .958 lacks its 'answer-only membership gate' context",
    )


def test_chain_local_anchor_variant_is_rejected(candidate_main: Path) -> None:
    mutate(
        candidate_main,
        "the test behind our chain-local causal control point",
        "the test behind our chain-only causal control point",
    )
    assert_rejected(candidate_main, "banned language (chain-only variant)")


def test_claim_ids_are_unique_across_audited_sections(
    candidate_main: Path,
) -> None:
    mutate(
        candidate_main,
        '"claim":"L-cloze-n"',
        '"claim":"J-strict-kappa"',
    )
    assert_rejected(candidate_main, "duplicate claim id 'J-strict-kappa'")


def test_extra_valid_section4_binding_is_rejected(candidate_main: Path) -> None:
    marker = r"\subsection{The Length-Only Account}"
    injected = (
        "Duplicate valid RR is \\(.193\\). "
        '% RJ: {"claim":"EXTRA-S4-rr","display":".193",'
        '"pointer":"/capability/families/R1-Distill-Qwen/rr/3",'
        '"format":"fixed:3"}\n\n'
    )
    mutate(candidate_main, marker, injected + marker)
    assert_rejected(
        candidate_main,
        "Section 4 RJ claim/path/format bindings differ from the reviewed ledger",
    )


def test_unapproved_frozen_string_token_is_rejected(
    candidate_main: Path,
) -> None:
    old = (
        '"claim":"L-cloze-hit-den","display":"23",'
        '"pointer":"/rq2_logitlens/_authoritative_record/edit_intact_at_cloze",'
        '"format":"token:1"'
    )
    new = old.replace('"token:1"', '"token:2"')
    mutate(candidate_main, old, new)
    assert_rejected(
        candidate_main,
        "token position 2 is not approved",
    )


def test_preregistered_remains_banned_outside_verified_context(
    candidate_main: Path,
) -> None:
    marker = r"\section{Introduction}"
    mutate(candidate_main, marker, marker + "\nThis analysis was preregistered.")
    assert_rejected(
        candidate_main,
        "banned language (unsupported preregistration wording)",
    )


@pytest.mark.parametrize(
    ("injected", "label"),
    [
        ("The route counts are 34/11/4/1.", "superseded route count tuple"),
        (r"The full-panel \(\kappa=.875\).", "superseded full-panel kappa"),
        ("The old logit gap was 17.803.", "superseded logit-lens feature"),
    ],
)
def test_new_section4_stale_signatures_are_rejected(
    candidate_main: Path,
    injected: str,
    label: str,
) -> None:
    marker = r"\section{Introduction}"
    mutate(candidate_main, marker, marker + "\n" + injected)
    assert_rejected(candidate_main, f"stale manuscript claim ({label})")


def test_external_input_placeholder_remains_forbidden(
    candidate_main: Path,
) -> None:
    marker = r"\subsection{Visible In-Chain Routes}"
    mutate(candidate_main, marker, marker + "\n\\input{table_rq2}")
    assert_rejected(
        candidate_main,
        "main.tex must remain a single source file without input/include",
        "superseded diagnostic asset",
    )


@pytest.mark.parametrize(
    "citation",
    [
        r"Visible note \citep[effect .546]{dummy2027}.",
        r"Visible note \citep[see][effect .546]{dummy2027}.",
    ],
)
def test_rendered_citation_notes_are_audited(
    candidate_main: Path,
    citation: str,
) -> None:
    marker = r"\subsection{Visible In-Chain Routes}"
    mutate(candidate_main, marker, citation + "\n" + marker)
    assert_rejected(candidate_main, "numeric occurrences ['.546']")


def test_citation_key_year_is_not_an_authored_number() -> None:
    namespace = runpy.run_path(str(CHECKER))
    assert namespace["numeric_occurrences"](r"\citep{meng2022rome}") == []
    assert namespace["numeric_occurrences"](r"\citep[p.~7]{meng2022rome}") == ["7"]


def test_reviewed_citation_identity_cannot_be_swapped(
    candidate_main: Path,
) -> None:
    mutate(
        candidate_main,
        r"mechanism of \citet{gekhman2026thinking}",
        r"mechanism of \citet{meng2022rome}",
    )
    assert_rejected(
        candidate_main,
        "Section 4 TeX source structure differs from the reviewed snapshot",
    )


def test_reviewed_forward_reference_cannot_be_redirected(
    candidate_main: Path,
) -> None:
    mutate(
        candidate_main,
        r"Section~\ref{sec:control} tests whether think-span-only",
        r"Section~\ref{sec:gap} tests whether think-span-only",
    )
    assert_rejected(
        candidate_main,
        "Section 4 TeX source structure differs from the reviewed snapshot",
    )


def test_reviewed_paragraph_boundary_cannot_change(
    candidate_main: Path,
) -> None:
    mutate(
        candidate_main,
        "conditional on the selected reversion sample.  The supplement names",
        "conditional on the selected reversion sample.\n\nThe supplement names",
    )
    assert_rejected(
        candidate_main,
        "Section 4 TeX source structure differs from the reviewed snapshot",
    )


def test_bibliography_command_is_exact_and_unique(
    candidate_main: Path,
) -> None:
    mutate(
        candidate_main,
        r"\bibliography{refs}",
        "\\bibliography{refs}\n\\bibliography{evil}",
    )
    assert_rejected(
        candidate_main,
        r"bibliography command must occur exactly once as \bibliography{refs}",
    )


@pytest.mark.parametrize(
    "marker",
    [
        r"\maketitle",
        r"\end{abstract}",
        r"\bibliography{refs}",
    ],
)
def test_unsectioned_document_body_gaps_reject_numbers(
    candidate_main: Path,
    marker: str,
) -> None:
    mutate(candidate_main, marker, marker + "\nVisible value .546.")
    assert_rejected(
        candidate_main,
        "unpartitioned document-body region",
        "numeric tokens ['.546']",
    )


def test_layout_parameter_does_not_hide_visible_number(
    candidate_main: Path,
) -> None:
    marker = r"\subsection{Visible In-Chain Routes}"
    injected = r"\fbox{\parbox{.72in}{Visible value .546.}}"
    mutate(candidate_main, marker, injected + "\n" + marker)
    assert_rejected(
        candidate_main,
        "numeric occurrences ['.546']",
    )


def test_prose_value_with_layout_unit_suffix_is_still_audited(
    candidate_main: Path,
) -> None:
    marker = r"\subsection{Visible In-Chain Routes}"
    mutate(
        candidate_main,
        marker,
        "The visible value is .546pt.\n" + marker,
    )
    assert_rejected(candidate_main, "numeric occurrences ['.546']")


def test_grouped_prose_dimension_is_still_audited(
    candidate_main: Path,
) -> None:
    marker = r"\section{Introduction}"
    mutate(
        candidate_main,
        marker,
        marker + "\nThe unsupported value is {.546pt}.",
    )
    assert_rejected(
        candidate_main,
        "numeric occurrences ['.546'] do not match RJ occurrences []",
    )


@pytest.mark.parametrize(
    "mutation",
    ["required-to-starred", "extra-starred"],
)
def test_section4_starred_subsections_are_rejected(
    candidate_main: Path,
    mutation: str,
) -> None:
    marker = r"\subsection{Visible In-Chain Routes}"
    if mutation == "required-to-starred":
        mutate(candidate_main, marker, r"\subsection*{Visible In-Chain Routes}")
    else:
        mutate(
            candidate_main,
            marker,
            r"\subsection*{Unreviewed Detour}" + "\n" + marker,
        )
    assert_rejected(candidate_main, "Section 4", "subsection")


def test_reviewed_table_environment_shape_is_frozen(
    candidate_main: Path,
) -> None:
    mutate(candidate_main, r"\begin{table}[t]", r"\begin{table*}[t]")
    mutate(candidate_main, r"\end{table}", r"\end{table*}")
    assert_rejected(
        candidate_main,
        "Section 4 TeX source structure differs from the reviewed snapshot",
    )


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (
            r"\(43\) NEW and \(17\) NEITHER",
            r"\(43\) NEITHER and \(17\) NEW",
        ),
        (
            r"\(27\) Bridge, \(11\) Recall",
            r"\(27\) Recall, \(11\) Bridge",
        ),
        (
            "T (old-answer first-token suppression) versus N (no suppression)",
            "T (no suppression) versus N (old-answer first-token suppression)",
        ),
        (
            "fresh-\\(B_0\\) strict direct-answer success held in \\(14/18\\) "
            "cases, while replayed answers received an OLD majority in \\(12/18\\)",
            "replayed answers received an OLD majority in \\(14/18\\) cases, "
            "while fresh-\\(B_0\\) strict direct-answer success held in \\(12/18\\)",
        ),
        (
            "the new token had the higher logit",
            "the old token had the higher logit",
        ),
    ],
)
def test_section4_semantic_role_swaps_are_rejected(
    candidate_main: Path,
    old: str,
    new: str,
) -> None:
    mutate(candidate_main, old, new)
    assert_rejected(
        candidate_main,
        "Section 4 visible semantic surface differs from the reviewed snapshot",
    )


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (
            "This is only an installation sanity check",
            "This is not only an installation sanity check",
        ),
        (
            "primary RR contrast was compatible with zero",
            "primary RR contrast was not compatible with zero",
        ),
        (
            "we withdraw the planned natural-chain mediation claim",
            "we do not withdraw the planned natural-chain mediation claim",
        ),
    ],
)
def test_section4_required_claim_polarity_is_frozen(
    candidate_main: Path,
    old: str,
    new: str,
) -> None:
    mutate(candidate_main, old, new)
    assert_rejected(candidate_main, "Section 4")


def test_required_claim_cannot_be_hidden_in_label(
    candidate_main: Path,
) -> None:
    target = "This is only an installation sanity check"
    mutate(
        candidate_main,
        target,
        "\\label{" + target + "}This is merely a check",
    )
    assert_rejected(
        candidate_main,
        "Section 4 required target string missing",
        "visible semantic surface differs",
    )


@pytest.mark.parametrize(
    ("injected", "diagnostic"),
    [
        (r"\typeout{27}twenty-eight Bridge", "unreviewed TeX command"),
        (r"\today", "unreviewed TeX command"),
        (r"\begin{verbatim}Visible .546\end{verbatim}", "unreviewed TeX environment"),
        (r"\input hidden.tex", "single source file without input/include"),
        (
            r"\InputIfFileExists{hidden.tex}{}{}",
            "single source file without input/include",
        ),
    ],
)
def test_unreviewed_tex_execution_surfaces_are_rejected(
    candidate_main: Path,
    injected: str,
    diagnostic: str,
) -> None:
    marker = r"\section{Introduction}"
    mutate(candidate_main, marker, marker + "\n" + injected)
    assert_rejected(candidate_main, diagnostic)


def test_preamble_only_command_cannot_hide_body_claim(
    candidate_main: Path,
) -> None:
    mutate(
        candidate_main,
        r"marginal ES \(.631\)",
        r"marginal ES \(\urlstyle{.631}\)",
    )
    assert_rejected(
        candidate_main,
        "preamble-only/unreviewed body TeX command",
        "Section 4 TeX source structure differs from the reviewed snapshot",
    )


def test_global_small_declaration_cannot_be_injected(
    candidate_main: Path,
) -> None:
    marker = r"\section{Introduction}"
    mutate(candidate_main, marker, marker + "\n\\small")
    assert_rejected(
        candidate_main,
        r"\small must occur exactly once",
    )


@pytest.mark.parametrize(
    "injected",
    [
        "This is a scaling~law.",
        "This is a scaling--law.",
        "This is a scaling---law.",
        "This is a scaling\u2014law.",
        r"This is a scal\relax ing law.",
        r"This is a scal\textbf {ing} law.",
        r"This is a chain-\allowbreak localized claim.",
    ],
)
def test_tex_spacing_cannot_hide_banned_language(
    candidate_main: Path,
    injected: str,
) -> None:
    marker = r"\section{Introduction}"
    mutate(candidate_main, marker, marker + "\n" + injected)
    assert_rejected(candidate_main, "banned language")


@pytest.mark.parametrize(
    "injected",
    [
        "The agreement estimate is a lower-bound certificate.",
        "The agreement estimate is a lower\u2014bound certificate.",
        "This does not make A a lower bound, but kappa is a lower bound.",
    ],
)
def test_hyphenated_lower_bound_claim_is_rejected(
    candidate_main: Path,
    injected: str,
) -> None:
    marker = r"\section{Introduction}"
    mutate(candidate_main, marker, marker + "\n" + injected)
    assert_rejected(
        candidate_main,
        "lower-bound language is not explicitly negated in its sentence",
    )


@pytest.mark.parametrize(
    ("text", "diagnostic"),
    [
        ("fifty committed reversions", "superseded route pool words"),
        ("sixty-eight percent", "superseded route distribution words"),
        ("fifty cases", "superseded fifty count"),
        ("sixty eight per cent", "superseded sixty-eight count"),
    ],
)
def test_stale_word_form_counts_are_rejected(
    candidate_main: Path,
    text: str,
    diagnostic: str,
) -> None:
    marker = r"\section{Introduction}"
    mutate(candidate_main, marker, marker + "\nThe stale pool had " + text + ".")
    assert_rejected(candidate_main, f"stale manuscript claim ({diagnostic})")


@pytest.mark.parametrize(
    "ratio",
    ["23/23=99%", "22/23=95.65%"],
)
def test_authoritative_cloze_ratio_requires_n_over_n_at_100_percent(
    ratio: str,
) -> None:
    namespace = runpy.run_path(str(CHECKER))
    results = json.loads(
        (REPO_ROOT / "paperwriting" / "results.json").read_text(encoding="utf-8")
    )
    results["rq2_logitlens"]["_authoritative_record"][
        "edit_intact_at_cloze"
    ] = ratio
    errors: list[str] = []
    namespace["check_authoritative_cloze_ratio"](results, errors)
    assert errors == ["Section 4 authoritative cloze ratio must equal n/n=100%"]


def test_think_span_anchor_variant_is_rejected(candidate_main: Path) -> None:
    mutate(
        candidate_main,
        "think-span-only old-answer first-token suppression",
        "chain-confined old-answer first-token suppression",
    )
    assert_rejected(candidate_main, "banned language (chain-confined variant)")


def test_blocked_cloze_artifact_must_be_named(candidate_main: Path) -> None:
    mutate(
        candidate_main,
        r"\url{results/probe/logitlens_cf200_ROME_B3.jsonl}",
        "the expected raw file",
    )
    assert_rejected(
        candidate_main,
        "Section 4 required target string missing: "
        "'results/probe/logitlens_cf200_ROME_B3.jsonl'",
    )


def test_cloze_downweighting_cannot_be_dropped(candidate_main: Path) -> None:
    mutate(
        candidate_main,
        "; absent it, we place no quantitative weight on this observation downstream",
        "",
    )
    assert_rejected(
        candidate_main,
        "Section 4 required target string missing: "
        "'we place no quantitative weight on this observation downstream'",
    )


def test_section4_forward_reference_stays_numberless(
    candidate_main: Path,
) -> None:
    """Section 4 is the hypothesis tier: it points forward without numbers."""
    mutate(
        candidate_main,
        "improves edit success and lowers permissive reversion against "
        "unsuppressed chains",
        "raises edit success by a paired \\(+.138\\) against unsuppressed chains",
    )
    assert_rejected(
        candidate_main,
        "Section 4 line",
        "numeric occurrences ['+.138']",
    )


def test_section4_must_disclose_the_strict_null(candidate_main: Path) -> None:
    mutate(
        candidate_main,
        ", while the strict displacement endpoint does not separate from that "
        "baseline",
        "",
    )
    assert_rejected(
        candidate_main,
        "Section 4 required target string missing: "
        "'while the strict displacement endpoint does not separate from that baseline'",
    )


def test_prospective_label_cannot_be_granted_twice(candidate_main: Path) -> None:
    mutate(
        candidate_main,
        "the pre-specified primary RR contrast",
        "the prospectively specified primary RR contrast",
    )
    assert_rejected(
        candidate_main,
        "Section 4 grants 'prospectively specified' at an unreviewed site",
    )


def test_frozen_string_token_binding_is_pinned_by_sha256() -> None:
    namespace = runpy.run_path(str(CHECKER))
    pointer = "/rq2_taxonomy/p0_downstream_crosswalk/historical_necessity_19"
    results = json.loads(
        (REPO_ROOT / "paperwriting" / "results.json").read_text(encoding="utf-8")
    )
    frozen = results["rq2_taxonomy"]["p0_downstream_crosswalk"][
        "historical_necessity_19"
    ]
    assert namespace["format_result"](frozen, "token:5", pointer) == "13"

    # A reworded record can leave every numeric token in place, so the display
    # comparison alone cannot detect that position 5 now means something else.
    reworded = frozen.replace(
        "corrected OLD subset", "corrected OLD subset (recount pending)"
    )
    assert reworded != frozen
    with pytest.raises(ValueError, match="differs from the reviewed record"):
        namespace["format_result"](reworded, "token:5", pointer)


def test_marginal_denominator_identities_pass_on_current_results() -> None:
    namespace = runpy.run_path(str(CHECKER))
    results = json.loads(
        (REPO_ROOT / "paperwriting" / "results.json").read_text(encoding="utf-8")
    )
    errors: list[str] = []
    namespace["check_marginal_denominator_identities"](results, errors)
    assert errors == []


@pytest.mark.parametrize(
    ("path", "value", "diagnostic"),
    [
        (
            ("rq3", "baseline", "RR"),
            0.2,
            "disagree on RR",
        ),
        (
            ("rq3", "n"),
            190,
            "is below the largest effective arm count",
        ),
        (
            ("capability", "families", "R1-Distill-Qwen", "es_b0", 3),
            0.5951,
            "is not a whole count over",
        ),
    ],
)
def test_marginal_denominator_identities_reject_drift(
    path: tuple[object, ...],
    value: object,
    diagnostic: str,
) -> None:
    namespace = runpy.run_path(str(CHECKER))
    results = json.loads(
        (REPO_ROOT / "paperwriting" / "results.json").read_text(encoding="utf-8")
    )
    target = results
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    errors: list[str] = []
    namespace["check_marginal_denominator_identities"](results, errors)
    assert any(diagnostic in error for error in errors), errors


def test_section5_subsection_order_is_frozen(candidate_main: Path) -> None:
    first = r"\subsection{A Signed, Dose-Graded Think-Span Intervention}"
    second = r"\subsection{The Control Point Moves the Untouched Answer}"
    mutate(candidate_main, first, r"\subsection{TEMPORARY-HEADING}")
    mutate(candidate_main, second, first)
    mutate(candidate_main, r"\subsection{TEMPORARY-HEADING}", second)
    assert_rejected(candidate_main, "Section 5 subsection order/titles differ")


def test_section5_arrow_must_bind_to_the_battery_arms(
    candidate_main: Path,
) -> None:
    """R10: 19.3% in Section 5 is the N arm, not the Section 3 capability cell.

    Both pointers hold the same value, so only the binding identity catches a
    swap.
    """
    text = candidate_main.read_text(encoding="utf-8")
    # Two arm-wise percent bindings plus the Table 2 row.
    assert text.count('"pointer":"/rq3/sup_battery/marginal_B3/N/RR"') == 3
    candidate_main.write_text(
        text.replace(
            '"pointer":"/rq3/sup_battery/marginal_B3/N/RR"',
            '"pointer":"/capability/families/R1-Distill-Qwen/rr/3"',
        ),
        encoding="utf-8",
    )
    assert_rejected(candidate_main, "Section 5 required bindings missing")


def test_section5_primary_contrast_identity_is_frozen(
    candidate_main: Path,
) -> None:
    """The frozen protocol names T-P, not T-N, as the primary contrast."""
    mutate(
        candidate_main,
        "The primary contrast was fixed in advance as T versus P",
        "The primary contrast was fixed in advance as T versus N",
    )
    assert_rejected(
        candidate_main,
        "Section 5 required target string missing: "
        "'The primary contrast was fixed in advance as T versus P'",
    )


def test_section5_cannot_claim_the_prospective_label(
    candidate_main: Path,
) -> None:
    mutate(
        candidate_main,
        "The primary contrast was fixed in advance as T versus P",
        "The primary contrast was prospectively specified as T versus P",
    )
    assert_rejected(
        candidate_main,
        "Section 5 must say 'fixed in advance'/'pre-specified'",
    )


@pytest.mark.parametrize(
    "target",
    [
        "nothing is penalized in the answer text",
        "extending the same penalty to the answer span",
        "manipulation check on whether the penalty acted inside the span, not an outcome",
        "every arm here is an intervened condition",
        "compatible with zero; we set no equivalence margin",
        "That interval reaches zero.",
        "a floor rather than an equivalence result",
        "not portability to unguarded queries",
    ],
)
def test_section5_load_bearing_qualifications_cannot_be_dropped(
    candidate_main: Path,
    target: str,
) -> None:
    mutate(candidate_main, target, "")
    assert_rejected(
        candidate_main,
        f"Section 5 required target string missing: {target!r}",
    )


@pytest.mark.parametrize(
    ("old", "new", "diagnostic"),
    [
        # P15: a null control may not be used as a positive premise.
        (
            "so the reading does not turn on which control the treated arm is measured against",
            "because the placebo floor is compatible with zero",
            "so the reading does not turn on which control the treated arm is measured against",
        ),
        # P17: no ordered-trend synonym, and the run boundary stays explicit.
        (
            "Every suppressed setting leaves the in-span leakage check below the zero clamp",
            "The in-span leakage check declines at every step",
            "Every suppressed setting leaves the in-span leakage check below the zero clamp",
        ),
    ],
)
def test_section5_review_patches_cannot_be_reverted(
    candidate_main: Path,
    old: str,
    new: str,
    diagnostic: str,
) -> None:
    mutate(candidate_main, old, new)
    assert_rejected(
        candidate_main,
        f"Section 5 required target string missing: {diagnostic!r}",
    )


def test_route_table_binds_the_corrected_census(candidate_main: Path) -> None:
    """The inlined route table must read the n=41 block, not the 50-pool one."""
    text = candidate_main.read_text(encoding="utf-8")
    assert '"pointer":"/rq2_taxonomy/p0_corrected_taxonomy/dist/Bridge"' in text
    for stale in ("n=50", "68\\%", "0.790"):
        assert stale not in text, stale
    mutate(
        candidate_main,
        "Route & Instances & Share",
        "Route & Instances & Share (50-pool)",
    )
    assert_rejected(candidate_main, "Section 4 visible semantic surface differs")


def test_figure_one_is_wired_and_referenced(candidate_main: Path) -> None:
    text = candidate_main.read_text(encoding="utf-8")
    assert r"\includegraphics" in text
    assert r"Figure~\ref{fig:gap}" in text, "Figure 1 must be cited from the prose"


def test_negative_interval_bound_is_not_the_banned_f1_contrast(
    candidate_main: Path,
) -> None:
    """-.214 is a legitimate CLR interval bound; only a positive .214 is banned."""
    completed = run_checker(candidate_main)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "-.214" in candidate_main.read_text(encoding="utf-8")

    marker = r"\section{Introduction}"
    mutate(candidate_main, marker, marker + "\nThe margin above control is .214.")
    assert_rejected(candidate_main, "banned language (forbidden F1 pseudo-contrast)")


def test_noncanonical_results_path_is_rejected(
    candidate_main: Path,
    tmp_path: Path,
) -> None:
    copied_results = tmp_path / "results.json"
    shutil.copy2(REPO_ROOT / "paperwriting" / "results.json", copied_results)
    completed = subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--main",
            str(candidate_main),
            "--results",
            str(copied_results),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode != 0, output
    assert "numeric source must be the canonical" in output
