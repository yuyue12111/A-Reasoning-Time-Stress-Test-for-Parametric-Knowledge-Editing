#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scrub identity strings out of binary/vector artifacts, and audit for leaks.

Why this exists
---------------
matplotlib writes the generating script's path into every figure it saves
(``/Creator`` in PDF, a ``tEXt`` chunk in PNG, a ``<dc:creator>`` node in SVG).
When such a figure is embedded in ``main.pdf`` the string ends up **inside a
Flate-compressed object stream**, where ``strings(1)``, ``grep`` and ``exiftool``
will not find it.  A double-blind submission can therefore look clean under
every obvious check and still carry the repository name.

So the audit here inflates every stream before matching, and the scrub rewrites
PDF strings **at equal byte length** so the cross-reference table stays valid
without regenerating the figure (local re-renders are not byte-reproducible on
every machine, so re-rendering is not a safe substitute for patching).

Usage
-----
    python src/scrub_artifacts.py --audit          # report only, exit 1 if dirty
    python src/scrub_artifacts.py --scrub          # rewrite in place, then audit
"""
from __future__ import annotations

import argparse
import re
import sys
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Anything here must never reach a reviewer.  Keep in sync with
# paperwriting/prewrite/anonymize_spec.md (categories L1-L5).
IDENTITY_PATTERNS = (
    rb"why-aaai",
    rb"whyu",
    rb"GitProjects",
    rb"yuyue",
    rb"hywang",
    rb"linroger",
    rb"inspire",
    rb"qb-ilm",
    rb"ky26140",
    rb"ai4education",
    rb"\bplan\.md\b",
    rb"gap-review",
    rb"prereg-",
    rb"sumandplan",
)
IDENTITY_RE = re.compile(b"|".join(IDENTITY_PATTERNS))

# Literal source strings replaced during --scrub.  PDF replacements must be the
# same byte length as the original; the helper below enforces that.
LEAKING_LITERALS = (
    b"why-aaai27/src/plots_nature_skill.py",
    b"why-aaai27/src/plots.py",
)

SCAN_SUFFIXES = {".pdf", ".png", ".svg"}
SCAN_ROOTS = ("paperwriting",)


def neutral_of(length: int) -> bytes:
    """A same-length, identity-free replacement ending in a plausible filename."""
    base = b"anonymized-generator"
    tail = b".py"
    if length < len(base) + len(tail):
        return (b"anonymized" + b"-" * length)[:length]
    return base + b"-" * (length - len(base) - len(tail)) + tail


def png_fix_crcs(data: bytes) -> bytes:
    """Recompute every chunk CRC (needed after an in-place tEXt edit)."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return data
    out = bytearray(data[:8])
    i = 8
    while i + 8 <= len(data):
        length = int.from_bytes(data[i : i + 4], "big")
        chunk = data[i + 4 : i + 8 + length]  # type + data
        out += data[i : i + 4] + chunk + zlib.crc32(chunk).to_bytes(4, "big")
        i += 12 + length
    return bytes(out)


def scrub_file(path: Path) -> int:
    data = path.read_bytes()
    original_length = len(data)
    changed = 0
    for literal in LEAKING_LITERALS:
        if literal not in data:
            continue
        count = data.count(literal)
        if path.suffix == ".svg":
            data = data.replace(literal, neutral_of(len(literal)))
        else:
            data = data.replace(literal, neutral_of(len(literal)))
            if len(data) != original_length:
                raise SystemExit(f"{path}: length changed; xref/chunk would break")
        changed += count
    if not changed:
        return 0
    if path.suffix == ".png":
        data = png_fix_crcs(data)
    path.write_bytes(data)
    return changed


def leaks_in(path: Path) -> list[str]:
    """Raw-byte and inflated-stream matches, plus a non-ASCII filename check."""
    found: set[str] = set()
    try:
        name_ascii = str(path).encode("ascii")
    except UnicodeEncodeError:
        found.add("<non-ascii filename>")
        name_ascii = b""
    data = path.read_bytes()
    for match in IDENTITY_RE.finditer(data):
        found.add(match.group(0).decode("latin-1"))
    # The expensive half: inflate anything that looks like a Flate stream.
    for marker in re.finditer(rb"stream\r?\n", data):
        start = marker.end()
        end = data.find(b"endstream", start)
        if end < 0:
            continue
        try:
            inflated = zlib.decompress(data[start:end])
        except zlib.error:
            continue
        for match in IDENTITY_RE.finditer(inflated):
            found.add(match.group(0).decode("latin-1") + " (in compressed stream)")
    del name_ascii
    return sorted(found)


def targets() -> list[Path]:
    seen: list[Path] = []
    for root in SCAN_ROOTS:
        for path in sorted((REPO / root).rglob("*")):
            if path.suffix.lower() in SCAN_SUFFIXES and path.is_file():
                seen.append(path)
    return seen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scrub", action="store_true", help="rewrite in place")
    parser.add_argument("--audit", action="store_true", help="report only")
    args = parser.parse_args()
    if not (args.scrub or args.audit):
        args.audit = True

    if args.scrub:
        total = 0
        for path in targets():
            n = scrub_file(path)
            if n:
                total += n
                print(f"scrubbed {n}x  {path.relative_to(REPO)}")
        print(f"-- {total} literal(s) replaced")

    dirty = []
    for path in targets():
        hits = leaks_in(path)
        if hits:
            dirty.append((path.relative_to(REPO), hits))
    if dirty:
        print("ANONYMITY AUDIT: FAIL")
        for path, hits in dirty:
            print(f"  {path}: {', '.join(hits)}")
        return 1
    print(f"ANONYMITY AUDIT: CLEAN ({len(targets())} artifacts, raw + inflated streams)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
