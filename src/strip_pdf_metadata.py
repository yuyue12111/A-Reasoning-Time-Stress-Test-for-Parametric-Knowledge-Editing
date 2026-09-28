#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Blank the document information dictionary of a built PDF.

The AAAI author kit asks anonymous submissions to clear PDF metadata.  Most of
that is already handled in the LaTeX source: ``\\pdfinfoomitdate`` drops
CreationDate/ModDate -- which matter most, because pdfTeX writes them in local
time and the timezone is a locality signal -- and ``\\pdfsuppressptexinfo``
drops the build banner.  ``/Creator`` and ``/Producer`` are the exception:
pdfTeX writes them unconditionally and ``\\pdfinfo`` cannot override them, so
they need a post-pass.

Run this AFTER the final pdflatex pass; a rebuild reinstates them.

    python3 src/strip_pdf_metadata.py paperwriting/manuscript/main.pdf ...
"""
from __future__ import annotations

import sys
from pathlib import Path

KEEP = {"/TemplateVersion"}


def strip(path: Path) -> str:
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(str(path))
    before = {k: str(v) for k, v in (reader.metadata or {}).items()}
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    kept = {k: v for k, v in (reader.metadata or {}).items() if k in KEEP}
    writer.add_metadata(kept)
    # pypdf stamps its own /Producer on write, which only trades one toolchain
    # name for another.  Empty the information dictionary in place, after
    # add_metadata rather than through it, so nothing is left to stamp.
    try:
        info = writer._info.get_object()
        for key in [k for k in info if k not in KEEP]:
            del info[key]
    except Exception:
        pass
    # XMP is a second, independent metadata channel; a reader that only checks
    # the info dictionary would miss it.
    try:
        writer._root_object.pop("/Metadata", None)
    except Exception:
        pass
    tmp = path.with_suffix(".stripped.pdf")
    with tmp.open("wb") as fh:
        writer.write(fh)
    tmp.replace(path)
    after = {k: str(v) for k, v in (PdfReader(str(path)).metadata or {}).items()}
    return f"{path.name}: {before or '{}'} -> {after or '{}'}"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    for arg in sys.argv[1:]:
        print(strip(Path(arg)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
