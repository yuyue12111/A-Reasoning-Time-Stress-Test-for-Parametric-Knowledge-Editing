"""Pure/CPU tests for X1 manifest, fixed prompt, sharding, and guaranteed restore."""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_x1_manifest as bm
import x1_replay as xr


def test_frozen_manifest_reconstructs_exactly():
    rows, audit = bm.build_manifest()
    tracked = [json.loads(line) for line in open(os.path.join(bm.ROOT, bm.DEFAULT_MANIFEST)) if line.strip()]
    assert rows == tracked and len(rows) == 18 and len(audit) == 33
    assert [r["source"] for r in rows].count("main_b3_greedy") == 10
    assert [r["source"] for r in rows].count("f2_b1_greedy") == 5
    assert [r["source"] for r in rows].count("f3_historical_sample_seed2") == 3
    assert "cf_12725" not in {r["case_id"] for r in rows}  # high-priority main source cannot be rescued


def test_manifest_sha_and_source_rows_are_frozen():
    path = os.path.join(xr.ROOT, "data/x1_replay_manifest.jsonl")
    expected = hashlib.sha256(open(path, "rb").read()).hexdigest()
    rows = xr.load_manifest(path, expected_sha256=expected)
    assert len(rows) == 18 and rows[0]["source_row"]["case_id"] == "cf_19889"


def test_fixed_prompt_exact_and_rejects_delimiters():
    text = xr.fixed_replay_prompt("Q?", "reasoning")
    assert text == "<｜User｜>Q?<｜Assistant｜><think>\nreasoning\n</think>\n\n"
    try:
        xr.fixed_replay_prompt("Q?", "bad </think> injection")
        raise AssertionError("forbidden delimiter accepted")
    except ValueError:
        pass


def test_shards_partition_without_overlap():
    rows = [{"manifest": {"case_id": f"c{i}"}} for i in range(18)]
    parts = [xr.shard_case_ids(rows, rank, 4) for rank in range(4)]
    assert len({cid for part in parts for cid in part}) == 18
    assert sum(len(part) for part in parts) == 18


class FakeEditor:
    def __init__(self):
        self.calls = []

    def edit(self, **kwargs):
        self.calls.append(kwargs)
        return None, None, {"w": "copy"}


def test_execute_case_restores_after_success_and_failure():
    source = {"prompt": "q", "o_old": "old", "o_new": "new", "s": "s", "cot": "cot"}
    restored = []
    out = xr.execute_case(FakeEditor(), object(), object(), source,
                          b0_generate=lambda: "new", replay_generate=lambda: "old",
                          restore_fn=lambda model, weights: restored.append(weights), token_count=lambda: 7)
    assert out == {"b0_answer": "new", "replay_answer": "old", "fixed_cot_tokens": 7}
    assert restored == [{"w": "copy"}]

    restored.clear()
    try:
        xr.execute_case(FakeEditor(), object(), object(), source,
                        b0_generate=lambda: "new",
                        replay_generate=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
                        restore_fn=lambda model, weights: restored.append(weights), token_count=lambda: 7)
        raise AssertionError("generation failure did not propagate")
    except RuntimeError:
        pass
    assert restored == [{"w": "copy"}]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("ok", name)
    print("OK x1_replay: all tests passed")

