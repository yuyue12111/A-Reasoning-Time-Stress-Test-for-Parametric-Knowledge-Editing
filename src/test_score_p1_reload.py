"""Pure-CPU arithmetic tests for P1 scoring."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score_p1_reload as p1


def test_paired_case_diff_uses_case_units():
    A = {"a": 1.0, "b": 0.5, "c": 0.0}
    B = {"a": 0.0, "b": 0.5, "c": 1.0}
    out = p1.paired_case_diff(A, B, ["a", "b", "c"], n_boot=1000)
    assert out["n_cases"] == 3
    assert out["mean"] == 0.0


def test_answer_sha_is_stable_and_sensitive():
    assert p1.answer_sha("x") == p1.answer_sha("x")
    assert p1.answer_sha("x") != p1.answer_sha("y")


def test_numeric_summary_filters_nonfinite_and_reports_median():
    out = p1.numeric_summary([1, 3, float("nan"), None])
    assert out["n"] == 2 and out["mean"] == 2 and out["median"] == 2


def test_normalized_meta_ignores_only_topology_and_physical_device_fields():
    base = {
        "code_sha256": {"src/edit_loop.py": "abc"},
        "software": {"torch": "2"},
        "runtime_env": {"WHYAAAI_DTYPE": "float32", "WHYAAAI_DEVICE_MAP": None,
                        "CUDA_VISIBLE_DEVICES": "0"},
        "actual_runtime": {"loaded_model": "/m", "parameter_dtype": "torch.float32",
                           "parameter_device": "cuda:0", "model_parallel": False},
    }
    mp2 = {
        **base,
        "runtime_env": {**base["runtime_env"], "WHYAAAI_DEVICE_MAP": "balanced",
                        "CUDA_VISIBLE_DEVICES": "2,3"},
        "actual_runtime": {**base["actual_runtime"], "parameter_device": "cuda:1",
                           "model_parallel": True, "hf_device_map_devices": ["0", "1"]},
    }
    assert p1.normalized_meta(base) == p1.normalized_meta(mp2)
    mp2["actual_runtime"]["parameter_dtype"] = "torch.bfloat16"
    assert p1.normalized_meta(base) != p1.normalized_meta(mp2)


if __name__ == "__main__":
    test_paired_case_diff_uses_case_units(); print("ok paired")
    test_answer_sha_is_stable_and_sensitive(); print("ok sha")
    test_numeric_summary_filters_nonfinite_and_reports_median(); print("ok numeric")
    test_normalized_meta_ignores_only_topology_and_physical_device_fields(); print("ok meta")
