#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-pin the checker's reviewed-snapshot SHAs, and only those.

Every deliberate edit to an audited section changes three hashes.  Updating them
by hand invites updating one that should have failed instead, so this refuses to
touch anything when the checker reports a substantive failure -- a missing
required string, an unbound number, a banned phrase.  It re-pins snapshots only
when snapshots are the sole complaint.

    python src/repin_snapshots.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SNAP = re.compile(
    r"^(.+?) (RJ claim/path/format bindings|visible semantic surface|TeX source structure)"
    r" differs? from the reviewed (?:ledger|snapshot) \(actual SHA256 ([0-9a-f]{64})\)$"
)
REFS = re.compile(
    r"^refs\.bib is missing or differs from the reviewed bibliography "
    r"\(actual SHA256 ([0-9a-f]{64})\)$"
)
DICTS = {
    "RJ claim/path/format bindings": "APPROVED_SECTION_LEDGER_BINDINGS_SHA256",
    "visible semantic surface": "APPROVED_SECTION_VISIBLE_SHA256",
    "TeX source structure": "APPROVED_SECTION_SOURCE_SHA256",
}


def main() -> int:
    out = subprocess.run(
        [sys.executable, "src/check_manuscript.py"],
        cwd=REPO, capture_output=True, text=True,
    ).stderr
    lines = [l.strip()[2:] for l in out.splitlines() if l.startswith("  - ")]

    pins, other = [], []
    for line in lines:
        match = SNAP.match(line)
        if match:
            pins.append((match.group(1), match.group(2), match.group(3)))
            continue
        refs = REFS.match(line)
        if refs:
            pins.append(("__REFS__", "refs", refs.group(1)))
            continue
        other.append(line)

    if other:
        print("REFUSING: substantive failures present, fix them first:")
        for entry in other:
            print("  -", entry)
        return 1
    if not pins:
        print("nothing to re-pin")
        return 0

    path = REPO / "src/check_manuscript.py"
    text = path.read_text(encoding="utf-8")
    for section, kind, sha in pins:
        if section == "__REFS__":
            text = re.sub(
                r'(APPROVED_REFS_SHA256 = \(\n    ")[0-9a-f]{64}',
                r"\g<1>" + sha, text, count=1,
            )
            print("  repinned refs.bib")
            continue
        start = text.index(DICTS[kind])
        end = text.index("}", start)
        block = text[start:end]
        new = re.sub(
            rf'("{re.escape(section)}": ")[0-9a-f]{{64}}',
            r"\g<1>" + sha, block, count=1,
        )
        if new == block:
            print(f"REFUSING: no entry for {section} / {kind}")
            return 1
        text = text[:start] + new + text[end:]
        print(f"  repinned {section} / {kind}")

    path.write_text(text, encoding="utf-8")
    print(f"{len(pins)} snapshot(s) re-pinned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
