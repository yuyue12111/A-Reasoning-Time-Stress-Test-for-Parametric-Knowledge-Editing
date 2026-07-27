#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Measure how much each sentence of the manuscript is being asked to do.

W3-2 asked for the restructure to be decided on data rather than impression:
before moving a caveat, know which sentences are carrying several jobs at once.
This labels every body sentence with the roles its surface shows -- asserting a
result, bounding it, naming a scope, naming a denominator, or pointing
elsewhere -- and reports the load per section.

The labelling is by surface pattern, so it is an indicator, not a reading.  A
sentence can bound a claim without using any of these words, and a word can
appear without doing the job.  Use it to find the heaviest sentences and then
read them; do not treat a count as a verdict.

    python3 src/audit_narrative_load.py [--markdown out.md]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MAIN = REPO / "paperwriting" / "manuscript" / "main.tex"

# Roles a sentence can take on.  Each is a list of surface markers.
ROLES: dict[str, tuple[str, ...]] = {
    "result": (
        r"\brises?\b", r"\bfalls?\b", r"\bdrops?\b", r"\braises?\b", r"\blowers?\b",
        r"\bimproves?\b", r"\bmoves?\b", r"\bseparates?\b", r"\bexcludes? zero\b",
        r"\bis lower\b", r"\bpersists?\b", r"\bappears?\b",
    ),
    "bound": (
        r"\bnot\b", r"\bno\b", r"\bnor\b", r"\bneither\b", r"\bwithout\b",
        r"\bcannot\b", r"\bonly\b", r"\brather than\b", r"\bcompatible with zero\b",
        r"\bunadjusted\b", r"\bwe claim no\b", r"\bdoes not\b", r"\bdo not\b",
        r"\bnull-compatible\b", r"\bbounds?\b", r"\bwithdraw\b", r"\bremains? untested\b",
    ),
    "scope": (
        r"\bat the largest\b", r"\bin this pool\b", r"\bconditional on\b",
        r"\bour claims are about\b", r"\bfixed checkpoints?\b", r"\bwithin\b",
        r"\bat this checkpoint\b", r"\bon the same requests\b", r"\bin the selected\b",
        r"\bthis dose-limited\b", r"\bof the six\b",
    ),
    "denominator": (
        r"\bn\s*=", r"\bcomplete[- ]case\b", r"\bpaired\b", r"\bdenominator\b",
        r"\bgated cases\b", r"\bmarginal\b", r"\battempted rows\b", r"\bintersection\b",
        r"\b\d+/\d+\b",
    ),
    "pointer": (
        r"\\ref\{", r"\bin the supplement\b", r"\bsupplementary\b",
        r"\bthe released provenance record\b",
    ),
}

# Sections as they appear, by their \section heading.
SECTION_RE = re.compile(r"\\section\*?\{([^{}]+)\}")


def strip_comments(text: str) -> str:
    out = []
    for line in text.splitlines():
        cut = None
        for index, char in enumerate(line):
            if char == "%" and (index == 0 or line[index - 1] != "\\"):
                cut = index
                break
        out.append(line if cut is None else line[:cut])
    return "\n".join(out)


def visible(text: str) -> str:
    """Approximate the rendered text: drop markup, keep footnote prose."""
    text = re.sub(r"\\(?:citep|citet)\{[^{}]*\}", "(citation)", text)
    text = re.sub(r"\\(?:label|url|includegraphics)\{[^{}]*\}", "", text)
    text = re.sub(r"\\begin\{tabular\}.*?\\end\{tabular\}", " ", text, flags=re.S)
    text = re.sub(r"\\(?:begin|end)\{[^{}]*\}", " ", text)
    text = re.sub(r"\\(?:footnote|textbf|textit|textsc|paragraph|caption)\{", " ", text)
    text = re.sub(r"\\\(|\\\)", "", text)
    text = re.sub(r"\\[A-Za-z@]+\*?", " ", text)
    text = text.replace("---", " ").replace("~", " ")
    text = re.sub(r"[{}]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [part.strip() for part in parts if len(part.strip()) > 25]


def roles_of(sentence: str) -> set[str]:
    found = set()
    for role, markers in ROLES.items():
        if any(re.search(marker, sentence, flags=re.IGNORECASE) for marker in markers):
            found.add(role)
    return found


def split_sections(text: str) -> list[tuple[str, str]]:
    matches = list(SECTION_RE.finditer(text))
    out = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        out.append((match.group(1), text[match.end(): end]))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", default=str(MAIN))
    parser.add_argument("--markdown", default=None)
    args = parser.parse_args()

    source = strip_comments(Path(args.main).read_text(encoding="utf-8"))
    rows, heaviest = [], []
    for title, body in split_sections(source):
        items = sentences(visible(body))
        if not items:
            continue
        loads = [len(roles_of(item)) for item in items]
        words = [len(item.split()) for item in items]
        rows.append(
            {
                "section": title.replace(r"\&", "&"),
                "sentences": len(items),
                "mean_roles": sum(loads) / len(loads),
                "overloaded": sum(1 for load in loads if load >= 4),
                "mean_words": sum(words) / len(words),
                "longest": max(words),
            }
        )
        for item, load, count in zip(items, loads, words):
            heaviest.append((load, count, title, item))

    heaviest.sort(key=lambda entry: (-entry[0], -entry[1]))

    lines = [
        "# Narrative load per sentence",
        "",
        "Generated by `src/audit_narrative_load.py`.  Roles are detected by surface",
        "pattern (result / bound / scope / denominator / pointer), so the counts are an",
        "indicator of how many jobs a sentence is doing, not a reading of it.  A",
        "sentence at 4-5 roles is where a reader has to hold the claim, its limit, its",
        "population and its denominator at once.",
        "",
        "| section | sentences | mean roles | 4+ roles | mean words | longest |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['section']} | {row['sentences']} | {row['mean_roles']:.2f} | "
            f"{row['overloaded']} | {row['mean_words']:.1f} | {row['longest']} |"
        )
    lines += ["", "## The twelve heaviest sentences", ""]
    for load, count, title, item in heaviest[:12]:
        lines.append(f"* **{load} roles, {count} words** — _{title}_ — {item}")
    report = "\n".join(lines) + "\n"

    if args.markdown:
        Path(args.markdown).write_text(report, encoding="utf-8")
        print(f"wrote {args.markdown}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
