"""CPU tests for engine v2.

transformers imports scikit-learn opportunistically, and the local scipy build fails to load on
recent macOS.  Nothing here needs scikit-learn, so hide it when it cannot be imported.
"""
import sys

try:
    import sklearn  # noqa: F401
except Exception:
    sys.modules["sklearn"] = None
