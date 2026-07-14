"""Pure-function tests for X2/X3 smoke audit helpers."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_x_smoke as vx


def test_parse_arm_suffix():
    label, path, suffix = vx.parse_arm("T=experiments/a.yaml@_smoke")
    assert label == "T" and path.endswith("experiments/a.yaml") and suffix == "_smoke"


def test_b0_exact_and_b3_difference():
    N = {"rows": {("c", "B0", "para0"): {"q": "q", "cot": "", "answer": "new"},
                  ("c", "B3", "para0"): {"q": "q", "cot": "old", "answer": "old"}}}
    T = {"rows": {("c", "B0", "para0"): {"q": "q", "cot": "", "answer": "new"},
                  ("c", "B3", "para0"): {"q": "q", "cot": "new", "answer": "new"}}}
    exact = vx.compare_b0(N, T, {"para0"})
    assert exact == {"compared": 1, "missing": [], "different": []}
    assert vx.b3_output_differences(N, T, {"para0"}) == [("c", "B3", "para0")]


def test_trace_scope_think_b0_zero_calls_b3_positive():
    arm = {"rows": {
        ("c", "B0", "efficacy"): {"suppress_trace": {"target": "old", "token_ids": [1],
            "selected": True, "active": False, "processor_calls": 0}},
        ("c", "B3", "efficacy"): {"suppress_trace": {"target": "old", "token_ids": [1],
            "selected": True, "active": True, "processor_calls": 9}},
    }}
    failures = []
    vx.check_trace("T", arm, {"efficacy"}, {"c": "old"}, failures)
    assert not failures


def test_completeness_expands_paraphrase_alias_to_two_rows():
    case = {"case_id": "c", "paraphrases": ["p0", "p1"], "neighborhood": []}
    arm = {"errors": [], "metas": [{"dataset": {"effective_n": 1}}],
           "cfg": {"dataset": {"n": 1}, "budgets": ["B0", "B3"],
                   "probes": ["efficacy", "paraphrase"]},
           "cases": [case], "rows": {}}
    for b in ("B0", "B3"):
        for p in ("efficacy", "para0", "para1"):
            arm["rows"][("c", b, p)] = {}
    failures = []
    vx.check_completeness("T", arm, "", failures)
    assert not failures


def test_actual_runtime_normalization_ignores_expected_rank_device_only():
    a = {"actual_runtime": {"loaded_model": "/m", "parameter_dtype": "torch.float32",
                            "parameter_device": "cuda:0", "bos_token_id": 1}}
    b = {"actual_runtime": {"loaded_model": "/m", "parameter_dtype": "torch.float32",
                            "parameter_device": "cuda:7", "bos_token_id": 1}}
    assert vx.normalized_actual_runtime(a) == vx.normalized_actual_runtime(b)
    b["actual_runtime"]["parameter_dtype"] = "torch.bfloat16"
    assert vx.normalized_actual_runtime(a) != vx.normalized_actual_runtime(b)


def test_runtime_env_normalization_ignores_only_physical_gpu_pair():
    a = {"runtime_env": {"CUDA_VISIBLE_DEVICES": "0,1", "WHYAAAI_DEVICE_MAP": "balanced",
                         "WHYAAAI_DTYPE": "float32"}}
    b = {"runtime_env": {"CUDA_VISIBLE_DEVICES": "6,7", "WHYAAAI_DEVICE_MAP": "balanced",
                         "WHYAAAI_DTYPE": "float32"}}
    assert vx.normalized_runtime_env(a) == vx.normalized_runtime_env(b)
    b["runtime_env"]["WHYAAAI_DEVICE_MAP"] = "balanced_low_0"
    assert vx.normalized_runtime_env(a) != vx.normalized_runtime_env(b)


def test_x3_model_parallel_gate_requires_both_local_devices():
    arm = {"cfg": {"hparams_overrides": {"model_parallel": True}}, "metas": [{
        "runtime_env": {"WHYAAAI_DEVICE_MAP": "balanced"},
        "actual_runtime": {"model_parallel": True, "hf_device_map_devices": ["0", "1"],
                           "edit_weight_devices": {"model.layers.12.mlp.down_proj.weight": "cuda:0"}}
    }]}
    failures = []
    vx.check_x3_model_parallel("T", arm, failures)
    assert not failures
    arm["metas"][0]["actual_runtime"]["hf_device_map_devices"] = ["0"]
    vx.check_x3_model_parallel("T", arm, failures)
    assert failures


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("ok", name)
    print("OK validate_x_smoke: all tests passed")
