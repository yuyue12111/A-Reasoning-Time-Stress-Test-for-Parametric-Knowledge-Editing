"""Strict fp32 on NVIDIA images that turn TF32 on by default (engine v2).

NGC PyTorch containers enable TF32 for fp32 matrix products (``NVIDIA_TF32_OVERRIDE`` /
``TORCH_ALLOW_TF32_CUBLAS_OVERRIDE``), which rounds matmul inputs to a 10-bit mantissa: relative
errors near 1e-4 instead of 1e-7.  The pre-registered edits are fp32 (REVISION.md §4) and the
mom2 statistics are long fp32 sums, so every fp32 entry point calls ``strict_fp32()`` before its
first CUDA operation and refuses to run when ``check_fp32_matmul`` still sees TF32-sized errors.
(2026-09-29: TF32 on the platform image made every single-edit ΔW miss its rank-1 fit.)
"""
import os

ENV = {"NVIDIA_TF32_OVERRIDE": "0", "TORCH_ALLOW_TF32_CUBLAS_OVERRIDE": "0"}
MAX_REL_ERR = 2e-5          # true fp32 GEMM at n=512 is ~1e-6; TF32 is ~1e-4


def strict_fp32():
    """Disable TF32 for this process; call before any CUDA work.  Returns a provenance record."""
    before = {k: os.environ.get(k) for k in ENV}
    os.environ.update(ENV)
    import torch
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.set_float32_matmul_precision("highest")
    return {"env_before": before, "env": dict(ENV), "allow_tf32": False}


def check_fp32_matmul(device="cuda", n=512):
    """Relative error of one fp32 GEMM on ``device`` against float64 on CPU."""
    import torch
    g = torch.Generator().manual_seed(0)
    a = torch.randn(n, n, generator=g, dtype=torch.float64)
    b = torch.randn(n, n, generator=g, dtype=torch.float64)
    ref = a @ b
    got = (a.float().to(device) @ b.float().to(device)).double().cpu()
    err = float(torch.linalg.norm(got - ref) / torch.linalg.norm(ref))
    return {"device": str(device), "rel_err": err, "ok": err <= MAX_REL_ERR}


def require_strict_fp32(device="cuda"):
    """strict_fp32() plus the check; raises when fp32 GEMMs on ``device`` still run as TF32."""
    rec = strict_fp32()
    import torch
    if str(device).startswith("cuda") and not torch.cuda.is_available():
        rec["check"] = {"device": str(device), "skipped": "no CUDA"}
        return rec
    rec["check"] = check_fp32_matmul(device)
    if not rec["check"]["ok"]:
        raise RuntimeError(f"fp32 matmul on {device} has relative error {rec['check']['rel_err']:.2e} "
                           f"(> {MAX_REL_ERR:g}): TF32 is still active; start the process with "
                           "NVIDIA_TF32_OVERRIDE=0 TORCH_ALLOW_TF32_CUBLAS_OVERRIDE=0")
    return rec
