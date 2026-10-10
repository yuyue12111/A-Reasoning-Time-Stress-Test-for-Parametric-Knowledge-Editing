"""mom2 statistics for MEMIT/AlphaEdit, precomputed on a bf16 model with fp32 accumulation.

EasyEdit computes these second moments lazily, inside the first MEMIT/AlphaEdit edit, on the model
being edited (``models/rome/layer_stats.py``).  At 32B the fp32 weights (~122 GiB) plus that
forward pass do not fit one 141 GB H200 (the 2026-07 MEMIT-32B OOM).  This module computes the
same statistics beforehand on a bf16 copy of the model, writes them to the file ``layer_stats``
looks up, in its format, and the fp32 edit processes then only load them.

Matched to EasyEdit (line numbers refer to source/EasyEdit at the pinned commit):

* path   ``<stats_dir>/<basename(model_name)>/<ds>_stats/<layer>_<precision>_mom2_<n>.npz``
  (layer_stats.py L152-166; ``basename`` is ``config._name_or_path.rsplit("/")[-1]``).
* keys   ``mom2.constructor``, ``mom2.count``, ``mom2.mom2`` (``precision`` [d, d]), ``sample_size``
  (runningstats.py SecondMoment.state_dict L502-507, CombinedStat L1379-1383,
  save_cached_state L1496-1512).
* sample the full train split shuffled by ``random.Random(1)``, first ``mom2_n_samples`` indices,
  in groups of 100 texts (layer_stats.py L132/L176-186; runningstats.py L1543-1603); each group
  tokenized with ``encode(truncation=True, max_length=maxlen)`` and packed by length into
  sub-batches of at most ``npos * 3`` tokens (tok_dataset.py).
* features = input of the rewrite module (down_proj) at attended positions, cast to
  ``precision`` (float32), ``mom2 += x.T @ x`` (layer_stats.py L190-199).

Known deviation: the activations come from a bf16 forward pass; EasyEdit's lazy path would have
used the fp32 model it is editing.  The accumulation itself is fp32 as in EasyEdit (TF32 is
switched off).  Work is split across processes by sample group (group g goes to rank g % world);
the per-rank fp32 partial sums are added in float64 at merge, which equals the sequential loop up
to floating-point summation order.

The Wikipedia corpus is pinned to the English dump: a directory glob once picked up the Korean
(``20231101.ko``) shards (paperwriting/results.json, MEMIT-32B ``_32b_final``).
"""
import glob
import json
import os
import random
import re
import time

import numpy as np
import torch

CONSTRUCTOR = "easyeditor.util.runningstats.SecondMoment()"
GROUP_SIZE = 100            # layer_stats.py L132: texts per sampled group
SAMPLE_SEED = 1             # layer_stats.py L184: tally(..., random_sample=1)
WIKI_ENV = "WHYAAAI_WIKI_PARQUET"
WIKI_DEFAULT = "/inspire/dataset/wikipedia/20231101/20231101.en"
WIKI_HUB = ("wikimedia/wikipedia", "20231101.en")
_EN_DIR = re.compile(r"(^|/)\d{8}\.en/[^/]+\.parquet$")
_LAYER = re.compile(r"\.(\d+)\.")


# ---------------------------------------------------------------- EasyEdit mirrors
def npos_for(config):
    """Context size layer_stats assumes (layer_stats.py L133-150)."""
    if hasattr(config, "n_positions"):
        npos = config.n_positions
    elif hasattr(config, "max_sequence_length"):
        npos = config.max_sequence_length
    elif hasattr(config, "max_position_embeddings"):
        npos = config.max_position_embeddings
    elif hasattr(config, "seq_length"):
        npos = config.seq_length
    else:
        raise NotImplementedError("config has no context length field")
    model_type = getattr(config, "model_type", None) or ""
    if "mistral" in model_type:
        npos = (getattr(config, "sliding_window", None) or 4096) \
            if getattr(config, "sliding_window", None) else 4096
    if "qwen2" in model_type:
        npos = 4096
    return npos


def maxlen_for(config, batch_tokens):
    """Tokenizer truncation length (layer_stats.get_ds L108-128; ``batch_tokens`` is npos*3 there)."""
    maxlen = npos_for(config)
    if batch_tokens is not None and batch_tokens < maxlen:
        maxlen = batch_tokens
    return maxlen


def stats_path(stats_dir, model_name, layer_name, ds_name="wikipedia", precision="float32",
               sample_size=100000, npos=4096, batch_tokens=None, to_collect=("mom2",)):
    """The cache file layer_stats reads and writes (layer_stats.py L152-166)."""
    if batch_tokens is None:
        batch_tokens = npos * 3
    size_suffix = "" if sample_size is None else f"_{sample_size}"
    if batch_tokens < npos:
        size_suffix = "_t{batch_tokens}" + size_suffix      # sic: not an f-string upstream
    base = str(model_name).rsplit("/")[-1]
    if not base:
        raise ValueError(f"model name {model_name!r} ends with '/': EasyEdit would write the "
                         "statistics outside stats_dir; strip the trailing slash")
    rel = f"{base}/{ds_name}_stats/{layer_name}_{precision}_{'-'.join(sorted(to_collect))}{size_suffix}.npz"
    return os.path.join(str(stats_dir), rel)


def sample_groups(n_rows, sample_size, group_size=GROUP_SIZE, seed=SAMPLE_SEED):
    """Row indices of every sampled group, in loader order (runningstats.make_loader L1574-1603)."""
    if sample_size is None:
        idx = list(range(n_rows))
    else:
        sample_size = min(sample_size, n_rows)
        idx = list(range(n_rows))
        random.Random(seed).shuffle(idx)                    # FixedRandomSubsetSampler L1551-1556
        idx = idx[:sample_size]
    return [idx[i:i + group_size] for i in range(0, len(idx), group_size)]


class TokenizedTexts(torch.utils.data.Dataset):
    """tok_dataset.TokenizedDataset with field "text"."""

    def __init__(self, rows, tokenizer, maxlen):
        self.rows, self.tokenizer, self.maxlen = rows, tokenizer, maxlen

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        ids = self.tokenizer.encode(self.rows[i]["text"], truncation=True, max_length=self.maxlen)
        return dict(input_ids=torch.tensor(ids), position_ids=torch.tensor(list(range(len(ids)))),
                    attention_mask=torch.tensor([1] * len(ids)))


def _padded(items):
    """tok_dataset.make_padded_batch."""
    from torch.nn.utils.rnn import pad_sequence
    if max(len(d["input_ids"]) for d in items) == 0:
        return {k: torch.zeros((0, 0), dtype=torch.long) for k in items[0]}
    return {k: pad_sequence([d[k] for d in items if len(d["input_ids"])], batch_first=True)
            for k in items[0]}


def length_collation(token_size):
    """tok_dataset.length_collation: sort by length, pack sub-batches of <= token_size tokens."""
    def collate(items):
        items = sorted(items, key=lambda x: -len(x["input_ids"]))
        batches, batch, width = [], [], 0
        for item in items:
            w = len(item["input_ids"])
            if w == 0:
                break
            if width * (len(batch) + 1) > token_size:
                batches.append(_padded(batch))
                batch, width = [], 0
            if not batch:
                width = w
            batch.append(item)
        if batch:
            batches.append(_padded(batch))
        return batches
    return collate


def flatten_masked(data, mask):
    """tok_dataset.flatten_masked_batch, with the mask moved to the features' device."""
    flat = data.reshape(-1, data.size(-1))
    return flat[mask.reshape(-1).to(flat.device).nonzero()[:, 0]]


# ---------------------------------------------------------------- corpus
def english_wiki_files(spec=None):
    """Parquet shards of the English Wikipedia dump, refusing anything else.

    ``spec`` (or $WHYAAAI_WIKI_PARQUET, or the platform mount) is a directory or a glob.  Every
    file must sit directly in one ``<yyyymmdd>.en`` directory; returns None when nothing matches
    (the caller may then fall back to the hub id ``wikimedia/wikipedia`` / ``20231101.en``).
    """
    spec = spec or os.environ.get(WIKI_ENV) or WIKI_DEFAULT
    pattern = os.path.join(spec, "*.parquet") if os.path.isdir(spec) else spec
    files = sorted(os.path.abspath(f) for f in glob.glob(pattern))
    if not files:
        return None
    bad = [f for f in files if not _EN_DIR.search(f.replace(os.sep, "/"))]
    if bad:
        raise ValueError(f"{len(bad)} of {len(files)} Wikipedia parquet files are not in a "
                         f"'<date>.en' directory (first: {bad[0]}); point {WIKI_ENV} at the English "
                         "subset, e.g. .../20231101/20231101.en (a glob once matched 20231101.ko)")
    if len({os.path.dirname(f) for f in files}) != 1:
        raise ValueError("Wikipedia parquet files come from more than one directory")
    return files


def assert_english(rows, n=200, min_ascii=0.8):
    """Content check on the first ``n`` texts: most letters must be ASCII."""
    letters = ascii_letters = 0
    for i in range(min(n, len(rows))):
        text = rows[i]["text"][:2000]
        for ch in text:
            if ch.isalpha():
                letters += 1
                ascii_letters += ch.isascii()
    frac = ascii_letters / letters if letters else 0.0
    if frac < min_ascii:
        raise ValueError(f"corpus does not look English: {frac:.2f} of letters are ASCII")
    return frac


def load_wiki(files):
    """The English Wikipedia train split (local parquet when available, else the pinned hub id)."""
    from datasets import load_dataset
    if files:
        return load_dataset("parquet", data_files={"train": files})["train"]
    return load_dataset(*WIKI_HUB)["train"]


def corpus_fingerprint(files, n_rows):
    if not files:
        return {"source": "hub", "id": list(WIKI_HUB), "n_rows": n_rows}
    return {"source": "parquet", "dir": os.path.dirname(files[0]),
            "files": [[os.path.basename(f), os.path.getsize(f)] for f in files], "n_rows": n_rows}


# ---------------------------------------------------------------- collection
class _Stop(Exception):
    pass


def layer_index(name):
    m = _LAYER.search(name)
    if not m:
        raise ValueError(f"no layer index in module name {name!r}")
    return int(m.group(1))


def input_device(model):
    return model.get_input_embeddings().weight.device


def collect(model, dataset, groups, layer_names, batch_tokens, precision="float32",
            num_workers=2, pin_memory=True, progress_every=0, log=print):
    """Second moments of the rewrite-module inputs over ``groups`` of ``dataset`` rows.

    All layers are traced in one forward pass that stops after the deepest one.  Returns
    ``{layer_name: (mom2 tensor on the layer's device, token count)}``.
    """
    dtype = getattr(torch, precision)
    order = sorted(set(layer_names), key=layer_index)
    caught = {}

    def hook(name, stop):
        def fn(module, inputs, output):
            caught[name] = inputs[0]
            if stop:
                raise _Stop()
        return fn

    handles = [model.get_submodule(n).register_forward_hook(hook(n, n == order[-1]))
               for n in order]
    acc = {}
    dev = input_device(model)
    loader = torch.utils.data.DataLoader(dataset, batch_sampler=groups,
                                         collate_fn=length_collation(batch_tokens),
                                         num_workers=num_workers, pin_memory=pin_memory)
    t0 = time.time()
    try:
        with torch.no_grad():
            for gi, sub_batches in enumerate(loader):
                for batch in sub_batches:
                    batch = {k: v.to(dev) for k, v in batch.items()}
                    caught.clear()
                    try:
                        model(**batch, use_cache=False)
                    except _Stop:
                        pass
                    for n in order:
                        feats = flatten_masked(caught[n], batch["attention_mask"]).to(dtype=dtype)
                        if len(feats) == 0:
                            continue
                        if n not in acc:
                            acc[n] = [feats.new(feats.shape[1], feats.shape[1]).zero_(), 0]
                        acc[n][0] += feats.t().mm(feats)
                        acc[n][1] += feats.shape[0]
                if progress_every and (gi + 1) % progress_every == 0:
                    log(f"[mom2] {gi + 1}/{len(groups)} groups, {time.time() - t0:.0f}s")
    finally:
        for h in handles:
            h.remove()
    missing = [n for n in order if n not in acc]
    if missing:
        raise RuntimeError(f"no features collected for {missing}")
    return {n: (m, c) for n, (m, c) in acc.items()}


# ---------------------------------------------------------------- files
def part_path(final_path, rank, world):
    d, name = os.path.split(final_path)
    return os.path.join(d, "_parts", f"{name[:-len('.npz')]}.r{rank}of{world}.npz")


def _atomic_savez(path, **arrays):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path[:-len(".npz")] + f".tmp{os.getpid()}.npz"
    np.savez(tmp, **arrays)
    os.replace(tmp, path)


def save_part(path, mom2, count, groups, meta):
    _atomic_savez(path, mom2=mom2.detach().cpu().numpy(), count=np.int64(count),
                  groups=np.asarray(groups, dtype=np.int64),
                  meta=np.asarray(json.dumps(meta, sort_keys=True)))


def load_part(path):
    z = np.load(path)
    return z["mom2"], int(z["count"]), [int(g) for g in z["groups"]], json.loads(str(z["meta"]))


def save_easyedit_stats(path, mom2, count, sample_size):
    """Write the npz exactly as tally()/save_cached_state would for CombinedStat(mom2=SecondMoment())."""
    _atomic_savez(path, **{"mom2.constructor": CONSTRUCTOR, "mom2.count": int(count),
                           "mom2.mom2": np.ascontiguousarray(mom2), "sample_size": sample_size})


def read_easyedit_stats(path, sample_size=None):
    """Load a cache file the way layer_stats does and return (moment, count).

    Mirrors runningstats.load_cached_state (sample_size check) + SecondMoment.load_state_dict +
    moment(); get_cov then takes ``.float()``.
    """
    dat = dict(np.load(path))
    expected = {"mom2.constructor", "mom2.count", "mom2.mom2", "sample_size"}
    if set(dat) != expected:
        raise ValueError(f"{path}: keys {sorted(dat)} != {sorted(expected)}")
    if sample_size is not None and dat["sample_size"] != sample_size:
        raise ValueError(f"{path}: sample_size {dat['sample_size']} != {sample_size}")
    count = int(dat["mom2.count"])
    return (torch.from_numpy(dat["mom2.mom2"]) / count).float(), count


def merge_parts(final_path, world, sample_size, n_groups, meta_keys_equal=None):
    """Sum the per-rank partial moments (float64) into EasyEdit's cache file; returns a summary."""
    parts = [part_path(final_path, r, world) for r in range(world)]
    missing = [p for p in parts if not os.path.exists(p)]
    if missing:
        raise FileNotFoundError(f"{len(missing)} partial files missing, e.g. {missing[0]}")
    total, count, seen, ref = None, 0, [], None
    for p in parts:
        m, c, groups, meta = load_part(p)
        fixed = {k: v for k, v in meta.items()
                 if k not in ("rank", "groups", "count", "created", "wall_s", "git", "git_dirty")}
        if ref is None:
            ref = fixed
        elif fixed != ref:
            diff = sorted(k for k in set(fixed) | set(ref) if fixed.get(k) != ref.get(k))
            raise ValueError(f"{p}: partial statistics disagree on {diff}")
        total = m.astype(np.float64) if total is None else total + m
        count += c
        seen.extend(groups)
    if sorted(seen) != list(range(n_groups)):
        raise ValueError(f"partial files cover {len(set(seen))} distinct of {n_groups} groups "
                         f"({len(seen)} total): some groups are missing or duplicated")
    mom2 = total.astype(np.dtype(ref.get("precision", "float32")))
    if not np.isfinite(mom2).all():
        raise ValueError("merged statistics are not finite")
    save_easyedit_stats(final_path, mom2, count, sample_size)
    summary = {"path": final_path, "count": count, "dim": int(mom2.shape[0]),
               "asym": float(np.abs(mom2 - mom2.T).max() / max(np.abs(mom2).max(), 1e-30)),
               "min_diag": float(np.diag(mom2).min()), "parts": world, **ref}
    with open(final_path[:-len(".npz")] + ".provenance.json", "w") as fh:
        json.dump(summary, fh, indent=1, sort_keys=True)
    return summary


def compare_stats(path_a, path_b):
    """How far apart two cache files are (e.g. bf16-forward vs Study 1's lazily computed ones)."""
    A, count_a = read_easyedit_stats(path_a)
    B, count_b = read_easyedit_stats(path_b)
    A, B = A.double(), B.double()
    da, db = torch.diagonal(A), torch.diagonal(B)
    return {"count_a": count_a, "count_b": count_b,
            "rel_fro": float(torch.linalg.norm(A - B) / torch.linalg.norm(B)),
            "max_rel_diag": float((da - db).abs().max() / db.abs().max())}


def verify_with_easyedit(model_config, tokenizer, layer_name, hp):
    """Ask EasyEdit's own layer_stats for the statistics while forbidding any recomputation.

    ``model_config`` is the model's AutoConfig (its ``_name_or_path`` must be the edit-time model
    path).  Only runs where easyeditor is importable; returns the loaded token count.
    """
    from types import SimpleNamespace
    from vendor_patches.easyedit_lean_import import apply as ensure_easyedit_importable
    ensure_easyedit_importable()
    from easyeditor.models.rome import layer_stats as ls

    def refuse(*a, **k):
        raise RuntimeError("layer_stats tried to recompute: cache file not found or rejected")

    saved = ls.load_dataset
    ls.load_dataset = refuse
    try:
        stat = ls.layer_stats(SimpleNamespace(config=model_config), tokenizer, layer_name,
                              hp.stats_dir, hp.mom2_dataset, to_collect=["mom2"],
                              sample_size=hp.mom2_n_samples, precision=hp.mom2_dtype,
                              hparams=hp, force_recompute=False, progress=None)
    finally:
        ls.load_dataset = saved
    return int(stat.mom2.count)


# ---------------------------------------------------------------- AlphaEdit projector
def null_space_projector(mom2_path, threshold, sample_size=None, device="cpu"):
    """AlphaEdit_main.get_project: projector onto the singular vectors of the covariance below
    ``threshold`` (SVD of ``mom2 / count``, full_matrices=False)."""
    cov, count = read_easyedit_stats(mom2_path, sample_size)
    U, S, _ = torch.linalg.svd(cov.to(device), full_matrices=False)
    small = (S < threshold).nonzero(as_tuple=True)[0]
    P = (U[:, small] @ U[:, small].T).cpu()
    near = int(((S > 0.99 * threshold) & (S < 1.01 * threshold)).sum())
    return P, {"dim": int(cov.shape[0]), "null_dim": int(len(small)), "near_threshold": near,
               "s_max": float(S.max()), "s_min": float(S.min()), "count": count}


def save_projector(P_loc, projectors, layers, meta):
    """``torch.save`` of a (len(layers), d, d) tensor, as AlphaEdit's torch.load(P_loc) expects,
    plus a JSON sidecar that ``deltas`` checks against the edit-time hparams."""
    P = torch.stack(projectors).float().contiguous()
    os.makedirs(os.path.dirname(os.path.abspath(P_loc)), exist_ok=True)
    tmp = P_loc + f".tmp{os.getpid()}"
    torch.save(P, tmp)
    os.replace(tmp, P_loc)
    side = dict(meta, layers=list(layers), shape=list(P.shape))
    with open(P_loc + ".json", "w") as fh:
        json.dump(side, fh, indent=1, sort_keys=True)
    return side
