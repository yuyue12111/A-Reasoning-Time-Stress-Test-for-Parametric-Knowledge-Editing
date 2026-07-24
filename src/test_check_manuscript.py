from __future__ import annotations

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
    for filename in ("main.tex", "aaai2027.sty", "aaai2027.bst"):
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
    assert "Section 3 RJ ledger (127 occurrences)" in completed.stdout


def test_frozen_abstract_mutation_is_rejected(candidate_main: Path) -> None:
    mutate(candidate_main, "from 19.3\\% to 8.5\\%", "from 19.3\\% to 8.6\\%")
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
    assert_rejected(candidate_main, "bindings differ from the reviewed W2-1 ledger")


def test_tex_split_banned_phrase_is_rejected(candidate_main: Path) -> None:
    marker = r"\subsection{The Gap}"
    mutate(candidate_main, marker, "This is a scal\\-ing law.\n\n" + marker)
    assert_rejected(candidate_main, "banned language (scaling-law language)")


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
        r"\section{Causal Diagnosis}",
        r"\section{A Chain-Local Causal Control Point}",
        r"\section{Discussion \& Limitations}",
        r"\section{Conclusion}",
        r"\section*{Ethical Statement}",
    ],
)
def test_unaudited_sections_reject_numeric_tokens(
    candidate_main: Path,
    marker: str,
) -> None:
    mutate(candidate_main, marker, marker + "\nThe unsupported value is .546.")
    assert_rejected(candidate_main, "unaudited section", "numeric tokens ['.546']")


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


def test_abstract_binding_debt_self_retires(candidate_main: Path) -> None:
    marker = r"\subsection{The Gap}"
    injected = (
        "Deferred repair RR is \\(8.5\\%\\). "
        '% RJ: {"claim":"DEBT-rr","display":"8.5",'
        '"pointer":"/rq3/sup_battery/marginal_B3/T/RR",'
        '"format":"percent:1"}\n\n'
    )
    mutate(candidate_main, marker, injected + marker)
    assert_rejected(
        candidate_main,
        "frozen-abstract numeric coverage differs",
        "remove PENDING_ABSTRACT_BODY_BINDINGS",
    )


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
