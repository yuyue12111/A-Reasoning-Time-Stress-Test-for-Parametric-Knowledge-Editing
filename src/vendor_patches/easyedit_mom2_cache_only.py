"""Edit processes load precomputed mom2 statistics and never compute them.

EasyEdit ``models/rome/layer_stats.py`` L170 calls ``get_ds()`` -- its only corpus access -- when
the cache file for a layer is missing, and then runs ``mom2_n_samples`` texts through the model
it is editing.  In an fp32 32B edit process that forward pass does not fit (the 2026-07 MEMIT-32B
OOM), and the corpus would come from whatever $WHYAAAI_WIKI_PARQUET happens to glob.  ``apply()``
replaces the ``load_dataset`` name inside that module with a function that raises, so a cache miss
fails the case loudly instead.  Statistics are made by ``python -m rt.deltas precompute-stats``.

Upstream-equivalent diff (record only; source/ is read-only):

    # models/rome/layer_stats.py  layer_stats()  L170
    - ds = get_ds() if not filename.exists() else None
    + if not filename.exists():
    +     raise RuntimeError(f"mom2 statistics missing: {filename}")
    + ds = None

Apply after ``easyedit_mom2_dataset.apply()`` (it replaces the same name); idempotent.
"""


class Mom2CacheMiss(RuntimeError):
    pass


def refuse_load_dataset(*args, **kwargs):
    raise Mom2CacheMiss(
        "EasyEdit layer_stats found no cached mom2 statistics and tried to load the corpus "
        f"{args[:2]}; precompute them first (python -m rt.deltas precompute-stats ...)")


def apply():
    from easyeditor.models.rome import layer_stats as ls_mod
    ls_mod.load_dataset = refuse_load_dataset
    return ls_mod
