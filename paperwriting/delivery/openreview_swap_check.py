#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify an OpenReview abstract field against the frozen v8.1 candidate.

Usage
-----
    # before pasting: confirm the local candidate is still the frozen one
    python paperwriting/delivery/openreview_swap_check.py --verify-source

    # after pasting: save the field's text (exactly as the form shows it) and diff
    python paperwriting/delivery/openreview_swap_check.py --diff /path/to/pasted.txt

The diff is byte-level and reports non-ASCII codepoints by name, because the two
characters that silently break this text are U+03BA (kappa) and U+2212 (minus),
both of which some editors normalise to ASCII look-alikes.
"""
from __future__ import annotations
import argparse, hashlib, sys, unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CANDIDATE = REPO / "paperwriting/delivery/abstract_v8_candidate.txt"
FROZEN_SHA = "0c85a03e9cd288b45d6f23502caf17b74e84c28dee0f3a2e62f9202ec4b81e5f"


def codepoint_table(text: str) -> str:
    rows = []
    for ch in sorted({c for c in text if ord(c) > 127}):
        rows.append(f"  U+{ord(ch):04X} {unicodedata.name(ch, '?'):<28} x{text.count(ch)}")
    return "\n".join(rows) or "  (none)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-source", action="store_true")
    ap.add_argument("--diff", type=Path)
    args = ap.parse_args()

    src = CANDIDATE.read_bytes()
    actual = hashlib.sha256(src).hexdigest()
    if actual != FROZEN_SHA:
        print(f"REFUSE: candidate file is not the frozen v8.1\n  expected {FROZEN_SHA}\n  actual   {actual}")
        return 1
    if args.verify_source or not args.diff:
        print("frozen v8.1 candidate verified")
        print(f"  sha256 {actual}\n  {len(src)} bytes, {len(src.decode('utf-8'))} characters")
        print("non-ASCII codepoints that must survive the paste:")
        print(codepoint_table(src.decode("utf-8")))
        if not args.diff:
            return 0

    pasted = args.diff.read_bytes()
    if pasted == src:
        print(f"MATCH: {args.diff} is byte-identical to the frozen v8.1")
        return 0
    print(f"MISMATCH: {args.diff} differs from the frozen v8.1")
    a, b = src.decode("utf-8"), pasted.decode("utf-8", "replace")
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            print(f"  first difference at character {i}")
            print(f"    expected U+{ord(x):04X} {unicodedata.name(x, '?')!r}")
            print(f"    got      U+{ord(y):04X} {unicodedata.name(y, '?')!r}")
            print(f"    context  ...{a[max(0,i-40):i+40]!r}")
            break
    else:
        print(f"  same prefix, length differs: expected {len(a)} chars, got {len(b)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
