"""TF32 is switched off for rt processes, and the rank-1 fit is judged in float64."""
import os

import torch


def test_rt_import_sets_the_tf32_overrides():
    import rt  # noqa: F401
    assert os.environ["NVIDIA_TF32_OVERRIDE"] == "0"
    assert os.environ["TORCH_ALLOW_TF32_CUBLAS_OVERRIDE"] == "0"


def test_strict_fp32_flags_and_cpu_check():
    from rt.precision import check_fp32_matmul, require_strict_fp32
    rec = require_strict_fp32("cpu")
    assert rec["check"]["ok"] and torch.get_float32_matmul_precision() == "highest"
    assert not torch.backends.cuda.matmul.allow_tf32
    assert check_fp32_matmul("cpu")["rel_err"] < 1e-5


def test_float64_fit_accepts_rank1_update_stored_in_fp32():
    """ΔW taken as W_edit - W_orig from fp32 storage is rank 1 up to storage rounding; the float64
    fit with the storage-floor tolerance must accept it (the 2026-09-29 platform failure mode)."""
    from rt.deltas import factor_update
    g = torch.Generator().manual_seed(3)
    W = torch.randn(96, 160, generator=g) * 0.05
    upd = (torch.randn(96, 1, generator=g) @ torch.randn(1, 160, generator=g)) * 2e-4
    W_edit = (W.double() + upd.double()).float()           # stored in fp32 like the edited weight
    delta = W_edit - W
    A, B, fit = factor_update(delta, float(torch.linalg.norm(W_edit)),
                              {"max_rank": 1, "tol": 1e-4, "floor_mult": 8.0})
    assert fit["ok"] and fit["rank"] == 1 and A.dtype == torch.float32
    assert fit["rel_err"] <= fit["tol"]
