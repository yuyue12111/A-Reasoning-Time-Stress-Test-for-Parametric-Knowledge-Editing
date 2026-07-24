#!/usr/bin/env python3
"""Fail-closed checks for the W2 manuscript surface.

The checker treats every numeric occurrence in Section 3 as an occurrence-level
claim.  Each occurrence must have an inline ``% RJ:`` JSON record containing a
unique claim id, an RFC 6901 pointer to a numeric scalar in results.json, and an
enumerated formatter.  Other, not-yet-authored sections reject numeric tokens
until their own ledgers land.  Banned and stale language is checked across the
whole visible manuscript.  The frozen abstract is byte-authenticated after
reversing the single LaTeX escape ``\\% -> %`` and cross-checked against body
ledger displays, with one explicit Section 5 debt for the frozen 8.5% value.
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
APPROVED_LEDGER_BINDINGS_SHA256 = (
    "e9b4288b8ea70fc5d1989b429f840464889c0400cb03835701141f8ab7399f20"
)

# Abstract v8.1 is frozen before Section 5 is authored.  Every other abstract
# number must already have a same-display body RJ binding.  This one reviewed
# debt validates against results.json now and must be removed as soon as the
# Section 5 19.3% -> 8.5% sentence receives its own RJ entries.
PENDING_ABSTRACT_BODY_BINDINGS = {
    "8.5": {
        "pointer": "/rq3/sup_battery/marginal_B3/T/RR",
        "format": "percent:1",
        "section": "A Chain-Local Causal Control Point",
    }
}

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
        "/rq3/n",
        "/rq3/sup_battery/n/N",
        "/rq3/sup_battery/marginal_B3/N/RRs",
        "/rq3/sup_battery/marginal_B3/N/RR",
        "/rq3/sup_battery/marginal_B3/T/RR",
    }
)

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
)

UNSAFE_POINTER_PARTS = ("superseded", "historical", "legacy")

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
    "edit-intact overclaim": r"\bedit intact\b",
    "not-erased overclaim": r"\bnot erased\b",
    "guaranteed-upper-bound overclaim": r"\bguaranteed upper bound\b",
    "ordered-trend overclaim": r"\bmonotonic\w*\b",
    "forbidden F1 pseudo-contrast": r"(?<!\d)\.214(?!\d)",
    "latent-rate bracket": r"\btrue reversion\b.{0,60}\bbetween\b",
}

STALE_CONTEXT_PATTERNS = {
    "superseded route pool": r"\b(?:n\s*=\s*50|50 committed reversions)\b",
    "superseded route distribution": r"\b68\s*%",
    "superseded route kappa": r"(?:kappa|κ)\s*=\s*0?\.790\b",
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


def normalize_visible(text: str) -> str:
    text = strip_tex_comments(text)
    text = (
        text.replace(r"\%", "%")
        .replace(r"\&", "&")
        .replace(r"\-", "")
        .replace(r"\kappa", "kappa")
    )
    # Preserve arguments while removing TeX command names and grouping braces.
    # This makes prose scans see through constructions such as
    # ``scal\textbf{ing}`` instead of treating source spelling as rendered text.
    text = re.sub(r"\\[A-Za-z@]+\*?", "", text)
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


def format_result(value: Any, rule: str) -> str:
    number = decimal_value(value)
    if rule == "integer":
        integral = number.to_integral_value()
        if number != integral:
            raise ValueError(f"integer formatter received {number}")
        return str(integral)

    match = re.fullmatch(r"(fixed|percent):(\d+)", rule)
    if not match:
        raise ValueError(f"unknown formatter {rule!r}")
    kind, places_text = match.groups()
    places = int(places_text)
    if places > 8:
        raise ValueError("formatter precision above 8 is not approved")
    if kind == "percent":
        number *= Decimal(100)
    quantum = Decimal(1).scaleb(-places)
    rendered = format(number.quantize(quantum, rounding=ROUND_HALF_UP), f".{places}f")
    return drop_leading_zero(rendered)


def pointer_is_approved(pointer: str) -> bool:
    lowered_parts = [part.lower() for part in pointer.split("/")]
    if any(part.startswith("_") for part in pointer.split("/") if part):
        return False
    if any(fragment in part for fragment in UNSAFE_POINTER_PARTS for part in lowered_parts):
        return False
    return pointer in APPROVED_EXACT_POINTERS or any(
        pointer.startswith(prefix) for prefix in APPROVED_POINTER_PREFIXES
    )


def mask_nonclaim_numbers(code: str) -> str:
    """Remove identifiers and dimensions that are not manuscript claims."""

    # Citation and reference keys can contain years or model ids but do not
    # render as authored numeric claims.
    code = re.sub(
        r"\\(?:cite|citep|citet|citealp|citeauthor|citeyear|ref|pageref|label)"
        r"(?:\[[^\]]*\])?\{[^{}]*\}",
        " ",
        code,
    )
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
    # Pure layout dimensions are source mechanics, not rendered claims.
    code = re.sub(
        r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)"
        r"(?:in|pt|pc|mm|cm|em|ex)\b",
        " ",
        code,
    )
    code = re.sub(
        r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)\s*"
        r"\\(?:textwidth|linewidth|columnwidth)\b",
        " ",
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
    if re.search(r"\\(?:input|include)\s*\{", visible_source):
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
    }
    for label, pattern in unsafe_constructs.items():
        if re.search(pattern, construct_surface):
            errors.append(f"forbidden manuscript construct ({label})")

    section_titles = re.findall(r"\\section\{([^{}]+)\}", visible_source)
    if tuple(section_titles) != REQUIRED_SECTION_ORDER:
        errors.append(f"unexpected numbered-section order: {section_titles!r}")
    if visible_source.count(r"\section*{Ethical Statement}") != 1:
        errors.append("unnumbered Ethical Statement is missing")

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


def check_rj_ledger(
    section_text: str, results: Any, errors: list[str]
) -> list[dict[str, Any]]:
    ledger: list[dict[str, Any]] = []
    claim_ids: set[str] = set()

    for line_number, line in enumerate(section_text.splitlines(), start=1):
        code, comment = split_tex_comment(line)
        entries: list[dict[str, Any]] = []
        if comment is not None and comment.lstrip().startswith("RJ:"):
            payload_text = comment.lstrip()[3:].strip()
            try:
                payload = json.loads(payload_text)
            except json.JSONDecodeError as exc:
                errors.append(f"Section 3 line {line_number}: malformed RJ JSON: {exc}")
                continue
            entries = payload if isinstance(payload, list) else [payload]
            if not entries:
                errors.append(f"Section 3 line {line_number}: empty RJ payload")

        source_numbers = numeric_occurrences(code)
        ledger_numbers: list[str] = []

        for entry_index, entry in enumerate(entries):
            prefix = f"Section 3 line {line_number}, RJ entry {entry_index + 1}"
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
            elif claim in claim_ids:
                errors.append(f"{prefix}: duplicate claim id {claim!r}")
            else:
                claim_ids.add(claim)
            if not pointer_is_approved(pointer):
                errors.append(f"{prefix}: pointer is outside approved current-result paths: {pointer}")
                continue
            try:
                value = resolve_pointer(results, pointer)
                rendered = format_result(value, rule)
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
                    "source_line": line_number,
                }
            )

        if source_numbers != ledger_numbers:
            errors.append(
                f"Section 3 line {line_number}: numeric occurrences {source_numbers!r} "
                f"do not match RJ occurrences {ledger_numbers!r}"
            )

    if not ledger:
        errors.append("Section 3 contains no RJ ledger entries")
    return ledger


def ledger_bindings_sha256(ledger: list[dict[str, Any]]) -> str:
    bindings = [
        [entry["claim"], entry["pointer"], entry["format"]]
        for entry in ledger
    ]
    encoded = json.dumps(
        bindings,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_bytes(encoded)


def check_global_claim_language(main_text: str, errors: list[str]) -> None:
    visible = normalize_visible(main_text)
    lowered = visible.lower()
    for label, pattern in BANNED_PATTERNS.items():
        if re.search(pattern, lowered, flags=re.IGNORECASE | re.DOTALL):
            errors.append(f"banned language ({label})")
    for label, pattern in STALE_CONTEXT_PATTERNS.items():
        if re.search(pattern, visible, flags=re.IGNORECASE):
            errors.append(f"stale manuscript claim ({label})")

    for sentence in re.split(r"(?<=[.!?])\s+", lowered):
        if re.search(r"\blower bound\b", sentence) and "does not make" not in sentence:
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

    audited_title = "The Reasoning-Time Evaluation Gap"
    for title, start_marker, end_marker in regions:
        if title == audited_title:
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
            rendered = format_result(value, specification["format"])
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


def main() -> int:
    args = parse_args()
    errors: list[str] = []

    if not args.main.is_file():
        print(f"FAIL: missing manuscript source: {args.main}", file=sys.stderr)
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
    check_unaudited_section_numbers(main_text, errors)
    try:
        section_text = extract_section(
            main_text,
            "The Reasoning-Time Evaluation Gap",
            "Causal Diagnosis",
        )
    except ValueError as exc:
        errors.append(str(exc))
        section_text = ""

    ledger: list[dict[str, Any]] = []
    if section_text:
        ledger = check_rj_ledger(section_text, results, errors)
        check_section3_requirements(section_text, errors)
        check_abstract_body_bindings(main_text, ledger, results, errors)
        bindings_sha256 = ledger_bindings_sha256(ledger)
        if bindings_sha256 != APPROVED_LEDGER_BINDINGS_SHA256:
            errors.append(
                "Section 3 RJ claim/path/format bindings differ from the "
                f"reviewed W2-1 ledger (actual SHA256 {bindings_sha256})"
            )

    if errors:
        print(f"FAIL: {len(errors)} manuscript check(s) failed", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if args.ledger_out:
        args.ledger_out.parent.mkdir(parents=True, exist_ok=True)
        args.ledger_out.write_text(
            json.dumps(ledger, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print(
        "PASS: frozen title/abstract, adjacent template copies, full-manuscript "
        "language gates, unaudited-section numeric gates, Section 3 RJ ledger "
        f"({len(ledger)} occurrences), claim targets, and exact abstract-binding debt"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
