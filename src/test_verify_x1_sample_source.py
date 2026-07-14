"""CPU test that explicit seed filtering ignores other F3 sample seeds."""
import json
import os
import sys
import tempfile

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_x1_sample_source as vs


def test_reconstruct_uses_explicit_seed2_only():
    with tempfile.TemporaryDirectory() as td:
        cases = os.path.join(td, "cases.jsonl")
        with open(cases, "w") as fh:
            fh.write(json.dumps({"case_id": "c1", "s": "S", "prompt": "S is in",
                                 "o_old": "Paris", "o_new": "Rome"}) + "\n")
        shard = os.path.join(td, "m_ROME_t_r0of1.jsonl")
        rows = [
            {"case_id": "c1", "probe": "efficacy", "decode": "sample", "seed": 0,
             "budget": "B0", "answer": "Rome", "cot": ""},
            {"case_id": "c1", "probe": "efficacy", "decode": "sample", "seed": 0,
             "budget": "B3", "answer": "Rome", "cot": "seed zero"},
            {"case_id": "c1", "probe": "efficacy", "decode": "sample", "seed": 2,
             "budget": "B0", "answer": "Rome", "cot": ""},
            {"case_id": "c1", "probe": "efficacy", "decode": "sample", "seed": 2,
             "budget": "B3", "answer": "Paris", "cot": "seed two"},
        ]
        with open(shard, "w") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")
        cfg = {"model_tag": "m", "out_dir": td,
               "dataset": {"tag": "t", "path": cases, "fallback_path": cases}}
        shards, reconstructed = vs.reconstruct(cfg, seed=2)
        assert shards == [shard]
        assert reconstructed["c1"]["cot"] == "seed two"
        assert reconstructed["c1"]["answer"] == "Paris"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("ok", name)
    print("OK verify_x1_sample_source: all tests passed")

