"""CPU-only regression tests for genbench dataset-source selection."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genbench


def _touch(path):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("{}\n")


def test_primary_path_wins_when_present():
    with tempfile.TemporaryDirectory() as td:
        primary = os.path.join(td, "prefiltered.jsonl")
        fallback = os.path.join(td, "full.jsonl")
        _touch(primary); _touch(fallback)
        cfg = {"dataset": {"path": primary, "fallback_path": fallback}}
        assert genbench.resolve_edit_source(cfg) == os.path.abspath(primary)


def test_fallback_only_when_primary_missing():
    with tempfile.TemporaryDirectory() as td:
        fallback = os.path.join(td, "full.jsonl")
        _touch(fallback)
        cfg = {"dataset": {"path": os.path.join(td, "missing.jsonl"),
                           "fallback_path": fallback}}
        assert genbench.resolve_edit_source(cfg) == os.path.abspath(fallback)


def test_explicit_override_is_authoritative():
    with tempfile.TemporaryDirectory() as td:
        primary = os.path.join(td, "prefiltered.jsonl")
        full = os.path.join(td, "counterfact.jsonl")
        _touch(primary); _touch(full)
        cfg = {"dataset": {"path": primary}}
        assert genbench.resolve_edit_source(cfg, full) == os.path.abspath(full)


def test_missing_source_fails_loudly():
    with tempfile.TemporaryDirectory() as td:
        cfg = {"dataset": {"path": os.path.join(td, "missing.jsonl")}}
        try:
            genbench.resolve_edit_source(cfg)
        except FileNotFoundError as exc:
            assert "No edit-source dataset found" in str(exc)
        else:
            raise AssertionError("missing edit source must not fail silently")


if __name__ == "__main__":
    for test in (test_primary_path_wins_when_present,
                 test_fallback_only_when_primary_missing,
                 test_explicit_override_is_authoritative,
                 test_missing_source_fails_loudly):
        test()
    print("OK: genbench source-selection tests passed")
