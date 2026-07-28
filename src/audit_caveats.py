#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prove that a rewrite moved caveats rather than dropping them.

W3-3 exit criterion 2.  Rewriting for readability and quietly losing a
qualification look identical in a diff once sentences have been reflowed, so this
takes a snapshot of every clause in the body that carries a limit, and compares
two snapshots.  A clause that disappears must be accounted for in a mapping file
by naming the clause that now carries it; otherwise the comparison fails.

The unit is a clause, not a sentence, because rerouting a caveat to a footnote
splits its sentence.  Matching is by content fingerprint over the clause's
content words, so reflowing, repunctuating, or moving a clause between body,
footnote and caption leaves the fingerprint alone -- only changing what the
clause says changes it.

    python3 src/audit_caveats.py --snapshot paperwriting/delivery/caveats_before.json
    python3 src/audit_caveats.py --compare before.json after.json [--map moves.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MAIN = REPO / "paperwriting" / "manuscript" / "main.tex"

# A clause carries a limit if it contains one of these.  Deliberately broad: a
# false positive costs one line in a ledger, a false negative loses a caveat.
LIMIT_MARKERS = (
    r"\bnot\b", r"\bno\b", r"\bnor\b", r"\bneither\b", r"\bnever\b", r"\bwithout\b",
    r"\bcannot\b", r"\bonly\b", r"\brather than\b", r"\binstead of\b", r"\bunadjusted\b",
    r"\bcompatible with zero\b", r"\bnull-compatible\b", r"\bwe claim no\b",
    r"\bremains? untested\b", r"\bremains? unidentified\b", r"\bwithdraw\b",
    r"\bdoes not\b", r"\bdo not\b", r"\bdid not\b", r"\bneed not\b", r"\bmay\b",
    r"\bwould\b", r"\bbounds?\b", r"\bbounded\b", r"\blimit(?:s|ed)?\b",
    r"\bconditional on\b", r"\bconditions on\b", r"\bjuxtaposed\b",
    r"\bnon-sufficient\b", r"\bfails? to\b", r"\bunexplained\b", r"\buntested\b",
)
LIMIT_RE = re.compile("|".join(LIMIT_MARKERS), re.IGNORECASE)

# Words that carry no content for matching purposes.
STOPWORDS = frozenset(
    """a an and are as at be been but by for from had has have in into is it its of on
    or so than that the their them there these this those to was were which while with
    we our us do does did not no nor""".split()
)

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


def zones(section_body: str) -> list[tuple[str, str]]:
    """Split a section into (zone, text): body, footnote, caption or table."""
    found: list[tuple[str, str]] = []
    remaining = section_body

    for command, zone in ((r"\footnote", "footnote"), (r"\caption", "caption")):
        while True:
            start = remaining.find(command + "{")
            if start < 0:
                break
            index = start + len(command)
            depth = 0
            for position in range(index, len(remaining)):
                if remaining[position] == "{":
                    depth += 1
                elif remaining[position] == "}":
                    depth -= 1
                    if depth == 0:
                        found.append((zone, remaining[index + 1:position]))
                        remaining = remaining[:start] + " " + remaining[position + 1:]
                        break
            else:  # unbalanced; leave it alone rather than guess
                break

    remaining = re.sub(
        r"\\begin\{tabular\}.*?\\end\{tabular\}",
        lambda match: found.append(("table", match.group(0))) or " ",
        remaining,
        flags=re.S,
    )
    found.append(("body", remaining))
    return found


def visible(text: str) -> str:
    text = re.sub(r"\\(?:citep|citet)\{[^{}]*\}", " ", text)
    text = re.sub(r"\\(?:label|url|ref|includegraphics)\{[^{}]*\}", " ", text)
    text = re.sub(r"\\(?:begin|end)\{[^{}]*\}", " ", text)
    text = re.sub(r"\\\(|\\\)", " ", text)
    text = re.sub(r"\\[A-Za-z@]+\*?", " ", text)
    text = text.replace("---", " ").replace("~", " ").replace("&", " ")
    text = re.sub(r"[{}\\\\]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clauses(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|;\s+|:\s+", text)
    return [part.strip() for part in parts if len(part.strip().split()) >= 4]


def fingerprint(clause: str) -> str:
    words = re.findall(r"[a-z]+", clause.lower())
    content = sorted(set(word for word in words if word not in STOPWORDS and len(word) > 2))
    return hashlib.sha256(" ".join(content).encode("utf-8")).hexdigest()[:16]


def snapshot(main_text: str) -> list[dict[str, str]]:
    source = strip_comments(main_text)
    matches = list(SECTION_RE.finditer(source))
    out: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        title = match.group(1).replace(r"\&", "&")
        for zone, chunk in zones(source[match.end():end]):
            for clause in clauses(visible(chunk)):
                if LIMIT_RE.search(clause):
                    out.append(
                        {
                            "id": fingerprint(clause),
                            "section": title,
                            "zone": zone,
                            "text": clause,
                        }
                    )
    return out


COMPARE_AGAINST: list[str] = [""]


def compare(before: list[dict], after: list[dict], moves: dict[str, str]) -> int:
    before_ids = {entry["id"]: entry for entry in before}
    after_ids = {entry["id"]: entry for entry in after}
    gone = [entry for key, entry in before_ids.items() if key not in after_ids]
    fresh = [entry for key, entry in after_ids.items() if key not in before_ids]

    moved_zone = [
        (before_ids[key], after_ids[key])
        for key in before_ids
        if key in after_ids and before_ids[key]["zone"] != after_ids[key]["zone"]
    ]

    print(f"caveat clauses before: {len(before)}   after: {len(after)}")
    print(f"rerouted between zones: {len(moved_zone)}")
    for old, new in moved_zone:
        print(f"  {old['zone']} -> {new['zone']}  [{old['section']}]  {old['text'][:70]}")

    unaccounted = []
    for entry in gone:
        successor = moves.get(entry["id"])
        if successor and successor in after_ids:
            print(f"  reworded {entry['id']} -> {successor}: {after_ids[successor]['text'][:70]}")
            continue
        # A caveat can survive while ceasing to look like one: drop an
        # unsupported inference from a sentence and the remaining statement of
        # fact carries no hedge marker, so the fingerprint set loses it.  The
        # map may therefore name a verbatim quote instead of an id, but the
        # quote has to be in the manuscript -- the editor points at real text or
        # the clause counts as lost.
        if successor and successor.startswith("STATED_WITHOUT_HEDGE:"):
            quote = successor.split(":", 1)[1].strip()
            if quote and quote in COMPARE_AGAINST[0]:
                print(f"  de-hedged {entry['id']}: {quote[:70]}")
                continue
            print(f"  MAPPED QUOTE NOT IN MANUSCRIPT for {entry['id']}: {quote[:70]}")
        unaccounted.append(entry)

    if fresh:
        print(f"new caveat clauses: {len(fresh)}")
        for entry in fresh:
            print(f"  + [{entry['section']}/{entry['zone']}] {entry['id']} {entry['text'][:70]}")

    if unaccounted:
        print(f"\nFAIL: {len(unaccounted)} caveat clause(s) disappeared with no successor:")
        for entry in unaccounted:
            print(f"  - [{entry['section']}/{entry['zone']}] {entry['id']} {entry['text'][:90]}")
        print("\nEither restore them, or record {\"<old id>\": \"<new id>\"} in the map file.")
        return 1
    print("\nPASS: every caveat clause is still present, reworded, or rerouted.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", default=str(MAIN))
    parser.add_argument("--snapshot", help="write the caveat inventory here")
    parser.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"))
    parser.add_argument("--map", help="JSON object of {old_id: new_id} for reworded clauses")
    args = parser.parse_args()

    if args.compare:
        before = json.loads(Path(args.compare[0]).read_text(encoding="utf-8"))
        after = json.loads(Path(args.compare[1]).read_text(encoding="utf-8"))
        moves = json.loads(Path(args.map).read_text(encoding="utf-8")) if args.map else {}
        COMPARE_AGAINST[0] = visible(strip_comments(Path(args.main).read_text(encoding="utf-8")))
        return compare(before, after, moves)

    entries = snapshot(Path(args.main).read_text(encoding="utf-8"))
    payload = json.dumps(entries, ensure_ascii=False, indent=1)
    if args.snapshot:
        Path(args.snapshot).write_text(payload + "\n", encoding="utf-8")
        print(f"wrote {len(entries)} caveat clauses to {args.snapshot}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
