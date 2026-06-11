"""run_pilot 接线单测（无 GPU/无模型）：抽样确定性、分片覆盖且不相交、overrides 解析。
运行：python src/test_run_pilot.py   （或 pytest src/test_run_pilot.py）
"""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_pilot as rp

CASES = [{"case_id": f"cf_{i}", "s": f"S{i}", "prompt": f"p{i}",
          "o_old": "a", "o_new": "b"} for i in range(10)]


def _jsonl(rows):
    fd, p = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
    with open(p, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return p


def test_load_cases_deterministic_and_n():
    p = _jsonl(CASES)
    a = [c["case_id"] for c in rp.load_cases(p, n=5, seed=42)]
    b = [c["case_id"] for c in rp.load_cases(p, n=5, seed=42)]
    d = [c["case_id"] for c in rp.load_cases(p, n=5, seed=7)]
    os.remove(p)
    assert a == b, "同 seed 必同序"
    assert len(a) == 5, "应取 n=5"
    assert a != d, "不同 seed 应不同（极大概率）"


def test_shard_partition():
    p = _jsonl(CASES); cases = rp.load_cases(p, n=None, seed=42); os.remove(p)
    world = 3
    shards = [set(rp.shard_ids(cases, r, world)) for r in range(world)]
    union = set().union(*shards)
    assert union == {c["case_id"] for c in cases}, "各片并集应覆盖全部"
    assert sum(len(s) for s in shards) == len(cases), "各片应不相交"


def test_resolve_overrides_and_paths():
    dp = _jsonl(CASES)
    cfg = {"model_tag": "r1qwen7b", "seed": 42, "out_dir": "results/pilot",
           "hparams_overrides": {"model_name": "deepseek-ai/X", "stats_dir": "./data/stats_r1qwen"},
           "dataset": {"tag": "cf200", "path": dp, "n": 5},
           "budgets": ["B0", "B3", "B4"],
           "editors": {"ROME": {"hparams": "h/ROME.yaml", "layers": [5]}}}
    R = rp.resolve(cfg, "ROME", rank=2, world=8, device=None)
    os.remove(dp)
    assert R["overrides"]["device"] == 2, "device 默认用 rank"
    assert R["overrides"]["model_name"] == "deepseek-ai/X"
    assert R["overrides"]["stats_dir"] == "./data/stats_r1qwen"
    assert R["overrides"]["layers"] == [5], "layers 来自 editor 段"
    assert R["out"].endswith("r1qwen7b_ROME_cf200_r2of8.jsonl"), f"out 命名错: {R['out']}"
    assert R["prefiltered"] is True, "dataset.path 存在即视为预过滤输入"
    assert len(R["cases"]) == 5


def test_resolve_device_explicit_overrides_rank():
    dp = _jsonl(CASES)
    cfg = {"model_tag": "m", "seed": 1, "out_dir": "o", "hparams_overrides": {},
           "dataset": {"tag": "t", "path": dp, "n": 3},
           "budgets": ["B0"], "editors": {"ROME": {"hparams": "h"}}}
    R = rp.resolve(cfg, "ROME", rank=3, world=8, device=7)
    os.remove(dp)
    assert R["overrides"]["device"] == 7, "显式 device 应压过 rank"


TESTS = [test_load_cases_deterministic_and_n, test_shard_partition,
         test_resolve_overrides_and_paths, test_resolve_device_explicit_overrides_rank]


def _main():
    fails = 0
    for t in TESTS:
        try:
            t(); print(f"  [PASS] {t.__name__}")
        except AssertionError as e:
            fails += 1; print(f"  [FAIL] {t.__name__}: {e}")
    print("ALL PASS" if fails == 0 else f"FAILED ({fails})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(_main())
