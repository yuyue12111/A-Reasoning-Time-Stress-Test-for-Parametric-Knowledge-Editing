#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Package the code/data release, with the anonymity audit as a hard gate.

The gate is the whole point of this file existing before the packaging logic
does.  A release audit that only prints a report is skipped by whoever is in a
hurry on the last day, which is exactly when it matters; wiring it as a refusal
now means the packaging step cannot be written around it later.

    python src/package_release.py --check      # gate only
    python src/package_release.py --out DIR    # gate, then stage the bundle
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))


def gate() -> int:
    """Refuse to proceed while any release-tier artifact carries an identity string."""
    from scrub_artifacts import leaks_in, targets

    dirty = [(p, leaks_in(p)) for p in targets("release")]
    dirty = [(p, h) for p, h in dirty if h]
    if not dirty:
        print(f"RELEASE GATE: PASS ({len(targets('release'))} artifacts clean)")
        return 0
    print(f"RELEASE GATE: BLOCKED -- {len(dirty)} artifact(s) still carry identity strings.")
    for path, hits in dirty[:20]:
        print(f"  {path.relative_to(REPO)}: {', '.join(hits)}")
    if len(dirty) > 20:
        print(f"  ... and {len(dirty) - 20} more")
    print("\nRun src/anonymize.py first.  Do not package around this gate: the "
          "checklist answers for 3.3/3.4/4.3/4.4/4.5 assume a clean bundle, and "
          "shipping a dirty one makes those answers false rather than optimistic.")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="run the gate and stop")
    ap.add_argument("--out", type=Path, help="staging directory for the bundle")
    args = ap.parse_args()

    rc = gate()
    if rc or args.check:
        return rc

    if args.out is None:
        print("gate passed; pass --out DIR to stage the bundle")
        return 0
    raise SystemExit(
        "staging is not implemented yet (T3). The gate above is live, so this "
        "script fails loudly rather than producing an unverified bundle."
    )


if __name__ == "__main__":
    sys.exit(main())
