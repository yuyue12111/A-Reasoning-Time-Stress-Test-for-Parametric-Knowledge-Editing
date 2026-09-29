"""Engine v2 for the ARR revision (see REVISION.md §4).

Importing any ``rt`` module turns TF32 off for the process (see ``rt.precision``): NGC images force
TF32 into fp32 matrix products through two environment variables that cuBLAS reads when CUDA
starts, which is why they are set here, before any CUDA work, rather than in each entry point.
"""
import os as _os

_os.environ["NVIDIA_TF32_OVERRIDE"] = "0"
_os.environ["TORCH_ALLOW_TF32_CUBLAS_OVERRIDE"] = "0"
