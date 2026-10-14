"""Run every ``test_*`` function under src/rt/tests without pytest (the editrev env has none).

    cd <project root>
    PYTHONPATH=src ~/.venvs/why-rt/bin/python src/rt/tests/run_all.py [name-filter]

~/.venvs/why-rt is a CPU venv with the platform versions (torch 2.9.1, transformers 5.5.4) and no
scipy; the editrev env cannot import transformers on recent macOS because its scipy build fails.

Exits non-zero if any test fails, so the exit code is the verdict (do not pipe through tail).
"""
import importlib
import pkgutil
import sys
import traceback

import rt.tests


def main():
    pattern = sys.argv[1] if len(sys.argv) > 1 else ""
    failed = passed = 0
    for info in sorted(pkgutil.iter_modules(rt.tests.__path__), key=lambda m: m.name):
        if not info.name.startswith("test_"):
            continue
        mod = importlib.import_module(f"rt.tests.{info.name}")
        for name in sorted(dir(mod)):
            if not name.startswith("test_") or pattern not in f"{info.name}.{name}":
                continue
            try:
                getattr(mod, name)()
                passed += 1
            except Exception:
                failed += 1
                print(f"FAIL {info.name}.{name}")
                traceback.print_exc()
    print(f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
