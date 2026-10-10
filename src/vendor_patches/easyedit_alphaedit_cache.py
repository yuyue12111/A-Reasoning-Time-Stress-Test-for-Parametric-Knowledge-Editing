"""Per-case reset of AlphaEdit's process-global key covariance ``cache_c`` (single-edit protocol).

Where the state lives (source/EasyEdit/easyeditor/models/alphaedit/AlphaEdit_main.py):
  L24-25    module globals ``P_loaded = False`` and ``cache_c_new = False``
  L48       ``global P, P_loaded, cache_c, cache_c_new`` in apply_AlphaEdit_to_model
  L51-52    ``if reset_cache: cache_c_new = False`` -- the only reset, a keyword argument
  L79-86    while ``cache_c_new`` is False: ``cache_c = zeros(len(layers), d, d)``; ``cache_c_new = True``
  L229-233  the update solves ``P @ (K K^T + cache_c[i]) + L2 I`` -- all earlier keys enter here
  L257-259  after the solve: ``cache_c[i] += K K^T`` for the current request
``BaseEditor.edit_requests`` (editors/editor.py L337-345, ``edit_func``) never passes
``reset_cache``, so within one process the n-th single-request edit is solved against the keys
of edits 1..n-1: batch-editing interference entering the single-edit protocol through the back
door, and a delta that depends on shard order.

``reset()`` puts the module back into its fresh-import state for ``cache_c`` before every case,
which is what ``apply_AlphaEdit_to_model(..., reset_cache=True)`` would do.  It also drops the old
tensor so the new zeros are the only copy in memory.  P (``P``/``P_loaded``) is a per-model
constant and is left alone.

Upstream-equivalent diff (record only; source/ is read-only):

    # editors/editor.py  edit_requests.edit_func  L337-345
      edited_model, weights_copy = self.apply_algo(
          self.model, self.tok, [request], self.hparams,
          copy=False, return_orig_weights=True, keep_original_weight=False,
    -     train_ds=kwargs['train_ds'] if self.alg_name == 'IKE' else None
    +     train_ds=kwargs['train_ds'] if self.alg_name == 'IKE' else None,
    +     **({'reset_cache': True} if self.alg_name == 'AlphaEdit' else {})
      )

Used by ``rt.deltas`` before every AlphaEdit case; tested in src/rt/tests/test_deltas.py.
"""
import importlib

MODULE = "easyeditor.models.alphaedit.AlphaEdit_main"


def reset(module=None):
    """Clear AlphaEdit's accumulated ``cache_c``; returns what was there (for the delta's diag)."""
    mod = module if module is not None else importlib.import_module(MODULE)
    info = {"cache_c_new_before": bool(getattr(mod, "cache_c_new", False)),
            "had_cache_c": hasattr(mod, "cache_c")}
    mod.cache_c_new = False
    if hasattr(mod, "cache_c"):
        del mod.cache_c
    return info
