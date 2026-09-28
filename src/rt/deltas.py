"""fp32 EasyEdit edits exported as low-rank deltas (engine v2, REVISION.md §4).

``run``: for every case of a pool and one target_tag (``cf`` edits to CounterFact's ``o_new``; any
other tag reads its target from a targets file, e.g. ``plausible`` from ``rt.targets``), make one
EasyEdit edit exactly as the legacy ``edit_loop`` did -- same vendor patches, fp32 weights, one
request, ``sequential_edit=True`` -- take ΔW = W_edit − W_orig for every edited weight from
EasyEdit's ``weights_copy``, factor it with ``edit_hooks.factor_delta`` and write
``<out_root>/<model_tag>/<editor>/<target_tag>/<case_id>.pt`` with ``edit_hooks.save_delta``.

Single-edit protocol, strengthened:
* the edited weights are snapshotted to CPU before the edit and restored in ``finally`` from that
  snapshot (EasyEdit's own copy is used first, as edit_loop did), then compared bit for bit; a
  mismatch stops the shard.  An exception raised inside ``edit()`` after the weights changed --
  when edit_loop never received ``weights_copy`` -- is therefore also rolled back;
* AlphaEdit's process-global ``cache_c`` is reset before every case
  (``vendor_patches.easyedit_alphaedit_cache``);
* MEMIT/AlphaEdit must find precomputed mom2 statistics (``precompute-stats``); computing them
  inside an edit process is refused (``vendor_patches.easyedit_mom2_cache_only``).

A single-request ROME/MEMIT/AlphaEdit update is rank 1 by construction, so ``factor.max_rank`` is
1 and an update that does not fit is an error row, never a truncated file.  The fit tolerance is
``max(tol, floor_mult * u * ||W_edit|| / ||ΔW||)`` with u the unit roundoff of the weight dtype:
ΔW is a difference of two stored fp32 matrices and cannot be more exact than that.

Diagnostics per case (``rec["diag"]``): teacher-forced log-probabilities of the first token (and
of the whole continuation) of " "+target, " "+o_new and " "+o_old after the efficacy prompt,
before and after the edit; the editor's printed optimisation losses; EasyEdit's own pre/post
rewrite_acc (teacher-forced logits metric, never to be mixed with generative ES); wall times.

Subcommands::

    run               edit + export one shard (resumable; --dry-run prints the plan)
    summarize         counts, fits and edit strength over shard logs (smoke checks)
    export-pool       freeze a case-id list from legacy result shards (the G0 parity pool)
    precompute-stats  mom2 statistics on a bf16 model, fp32 accumulation (--prepare, --merge)
    alphaedit-P       AlphaEdit null-space projector from the cached statistics

See experiments/rt/README_deltas.md for launch commands.
"""
import argparse
import contextlib
import dataclasses
import glob
import hashlib
import importlib.metadata
import io
import json
import math
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

import torch
import yaml

from rt.edit_hooks import factor_delta, load_delta, save_delta

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EDITORS = ("ROME", "MEMIT", "AlphaEdit")
NEEDS_STATS = ("MEMIT", "AlphaEdit")
MODULE_TMP = "model.layers.{}.mlp.down_proj"
FACTOR_DEFAULT = {"max_rank": 1, "tol": 1e-4, "floor_mult": 8.0}
CODE_FILES = ["src/rt/deltas.py", "src/rt/edit_hooks.py", "src/rt/mom2.py", "src/rt/targets.py",
              "src/r1_tokenizer.py", "src/vendor_patches/easyedit_qwen2_loader.py",
              "src/vendor_patches/easyedit_mom2_dataset.py",
              "src/vendor_patches/easyedit_mom2_cache_only.py",
              "src/vendor_patches/easyedit_alphaedit_cache.py",
              "src/vendor_patches/easyedit_lean_import.py"]


class Contamination(RuntimeError):
    """The model could not be put back to its pre-edit weights; the shard must stop."""


def _abs(p):
    return p if os.path.isabs(p) else os.path.join(_ROOT, p)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha256_json(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False,
                                     default=str).encode()).hexdigest()


def ids_sha(ids):
    return hashlib.sha256("\n".join(ids).encode()).hexdigest()


# ---------------------------------------------------------------- provenance (as edit_loop)
def git_provenance():
    def g(*a):
        return subprocess.check_output(["git", "-C", _ROOT, *a], stderr=subprocess.DEVNULL,
                                       text=True).strip()
    try:
        return {"git": g("rev-parse", "HEAD"), "git_dirty": bool(g("status", "--porcelain"))}
    except Exception:
        return {"git": "unknown", "git_dirty": None}


def software_provenance():
    packages = {}
    for name in ("transformers", "datasets", "numpy", "accelerate"):
        try:
            packages[name] = importlib.metadata.version(name)
        except Exception:
            packages[name] = None
    try:
        easyedit_git = subprocess.check_output(
            ["git", "-C", os.path.join(_ROOT, "source", "EasyEdit"), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        easyedit_git = "unknown"
    return {"python": sys.version.split()[0], "platform": platform.platform(),
            "torch": torch.__version__, "torch_cuda": getattr(torch.version, "cuda", None),
            "fp32_matmul_precision": torch.get_float32_matmul_precision(),
            "packages": packages, "easyedit_git": easyedit_git}


def code_sha256():
    return {rel: sha256_file(_abs(rel)) for rel in CODE_FILES if os.path.exists(_abs(rel))}


def runtime_env():
    return {k: os.environ.get(k) for k in (
        "WHYAAAI_MODEL", "WHYAAAI_DTYPE", "WHYAAAI_NO_BOS", "WHYAAAI_WIKI_PARQUET",
        "WHYAAAI_DEVICE_MAP", "PYTORCH_CUDA_ALLOC_CONF", "CUDA_VISIBLE_DEVICES",
        "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")}


def model_runtime(model, tok, hp):
    """What was actually loaded (edit_loop.model_runtime)."""
    rec = {"requested_model": getattr(hp, "model_name", None),
           "model_class": type(model).__name__, "tokenizer_class": type(tok).__name__,
           "bos_token_id": getattr(tok, "bos_token_id", None),
           "eos_token_id": getattr(tok, "eos_token_id", None),
           "loaded_model": getattr(getattr(model, "config", None), "_name_or_path", None),
           "model_parallel": bool(getattr(hp, "model_parallel", False))}
    p = next(model.parameters())
    rec["parameter_dtype"], rec["parameter_device"] = str(p.dtype), str(p.device)
    dm = getattr(model, "hf_device_map", None)
    if isinstance(dm, dict):
        counts = {}
        for dev in dm.values():
            counts[str(dev)] = counts.get(str(dev), 0) + 1
        rec["hf_device_map_counts"] = counts
    rec["edit_weights"] = {n: [str(model.get_parameter(n).dtype), str(model.get_parameter(n).device)]
                           for n in edited_weight_names(hp)}
    return rec


# ---------------------------------------------------------------- configuration
def load_models(path):
    with open(path) as fh:
        models = yaml.safe_load(fh)
    for tag, spec in models["models"].items():
        for ed in spec.get("editors", {}):
            if ed not in EDITORS:
                raise ValueError(f"{path}: {tag} has unknown editor {ed}")
    return models


def editor_settings(models, model_tag, editor):
    """Template path + hparams overrides for (model, editor) from deltas_models.yaml."""
    spec = models["models"][model_tag]
    if editor not in spec.get("editors", {}):
        raise ValueError(f"{model_tag} has no {editor} settings in the models file")
    ed = spec["editors"][editor]
    overrides = {"stats_dir": _abs(spec["stats_dir"])}
    overrides.update(ed.get("overrides", {}))
    if "P_loc" in overrides:
        overrides["P_loc"] = _abs(overrides["P_loc"])
    return {"template": _abs(ed["hparams"]), "overrides": overrides,
            "family": spec["family"], "n_layers": spec["n_layers"]}


def resolve_model_path(cli_path, spec):
    """--model-path > $WHYAAAI_MODEL > hf_id; trailing slashes stripped (the mom2 file name is the
    path's last component, so edits and precompute-stats must use the same string)."""
    path = cli_path or os.environ.get("WHYAAAI_MODEL") or spec["hf_id"]
    return path.rstrip("/") if len(path) > 1 else path


def check_routing(model_name, family):
    """EasyEdit routes by substrings of model_name: 'qwen' -> Qwen loader branch (patched),
    'llama' -> Llama branch; AlphaEdit sizes cache_c only for names containing qwen/llama."""
    key = {"qwen2": "qwen", "llama": "llama"}[family]
    if key not in model_name.lower():
        raise ValueError(f"model path {model_name!r} does not contain {key!r}: EasyEdit would pick "
                         "the wrong loader (or raise NotImplementedError). Use a path or symlink "
                         f"whose name contains {key!r}, e.g. .../Qwen-QwQ-32B")


def hparams_dict(hp):
    if dataclasses.is_dataclass(hp):
        return dataclasses.asdict(hp)
    return dict(vars(hp))


def hparams_signature(hp, dtype):
    """Everything that can change ΔW; paths reduced to their last component, device dropped."""
    d = {k: v for k, v in hparams_dict(hp).items() if k != "device"}
    for k in ("model_name", "stats_dir", "P_loc"):
        if isinstance(d.get(k), str):
            d[k] = os.path.basename(d[k].rstrip("/"))
    return {"hparams": d, "dtype": dtype}


def edited_weight_names(hp):
    return [f"{hp.rewrite_module_tmp.format(L)}.weight" for L in hp.layers]


def load_pool(path):
    """(case_ids, meta) from a pool manifest.

    Accepts the jsonl manifests written by ``rt.pool qualify`` (and ``experiments/rt/pools/*.jsonl``;
    read with ``rt.run.read_ids``, which checks the ``.sha256`` sidecar), a JSON {"case_ids": [...]},
    or a JSON list.
    """
    if path.endswith(".jsonl"):
        from rt.run import read_ids
        obj = read_ids(path)
    else:
        with open(path) as fh:
            obj = json.load(fh)
    ids = obj if isinstance(obj, list) else obj["case_ids"]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: duplicate case ids")
    meta = {} if isinstance(obj, list) else {k: v for k, v in obj.items() if k != "case_ids"}
    if meta.get("sha256") and meta["sha256"] != ids_sha(ids):
        raise ValueError(f"{path}: case-id hash mismatch (manifest edited by hand?)")
    return ids, {"n": len(ids), "sha256": ids_sha(ids), "name": meta.get("name")}


def load_cases(dataset_path, ids):
    rows = {}
    with open(dataset_path) as fh:
        for line in fh:
            if line.strip():
                row = json.loads(line)
                rows[row["case_id"]] = row
    missing = [c for c in ids if c not in rows]
    if missing:
        raise ValueError(f"{len(missing)} pool ids missing from {dataset_path}: {missing[:5]}")
    return [rows[c] for c in ids]


def attach_targets(cases, target_tag, targets=None):
    """Each case gets ``target``: o_new for 'cf', else the targets-file entry (all required)."""
    out = []
    for c in cases:
        if target_tag == "cf":
            t = c["o_new"]
        else:
            t = (targets or {}).get(c["case_id"])
            if not t:
                raise ValueError(f"no {target_tag!r} target for {c['case_id']}")
        out.append(dict(c, target=t))
    return out


def shard(cases, rank, world):
    return [c for i, c in enumerate(cases) if i % world == rank]


def delta_path(out_root, model_tag, editor, target_tag, case_id):
    return os.path.join(out_root, model_tag, editor, target_tag, f"{case_id}.pt")


# ---------------------------------------------------------------- per-case pieces
class _Tee(io.TextIOBase):
    def __init__(self, stream):
        self.stream, self.buf = stream, io.StringIO()

    def write(self, s):
        self.stream.write(s)
        self.buf.write(s)
        return len(s)

    def flush(self):
        self.stream.flush()


_LOSS = re.compile(r"^loss (\S+) = (\S+) \+ (\S+) \+ (\S+) avg prob of \[(.*)\] (\S+)\s*$")
_NUM = r"(?:tensor\()?([-+0-9.eEinfa]+)"


def parse_editor_log(text):
    """Losses and norms that ROME/MEMIT/AlphaEdit print while optimising (compute_v / compute_z)."""
    def num(s):
        try:
            return float(s)
        except ValueError:
            return float("nan")
    steps = [m.groups() for m in map(_LOSS.match, text.splitlines()) if m]
    out = {"n_steps": len(steps)}
    if steps:
        out["loss"] = [num(s[0]) for s in steps]
        out["nll_last"], out["prob_last"] = num(steps[-1][1]), num(steps[-1][5])
    for key, pat in (("delta_norm", r"Delta norm: " + _NUM),
                     ("right_vector_norm", r"Right vector norm: " + _NUM),
                     ("z_error", r"z error " + _NUM), ("upd_norm", r"upd norm " + _NUM)):
        vals = [num(v) for v in re.findall(pat, text)]
        if vals:
            out[key] = vals
    out["nan"] = any(isinstance(v, float) and math.isnan(v)
                     for vals in out.values() if isinstance(vals, list) for v in vals)
    return out


def snapshot(model, names):
    return {n: model.get_parameter(n).detach().to("cpu", copy=True) for n in names}


def restore(model, snap, weights_copy=None):
    """edit_loop.restore from EasyEdit's copy, then from our snapshot, then a bitwise check."""
    with torch.no_grad():
        for n, v in (weights_copy or {}).items():
            p = model.get_parameter(n)
            p[...] = v.to(p.device, p.dtype)
        for n, v in snap.items():
            p = model.get_parameter(n)
            p[...] = v.to(p.device, p.dtype)
    bad = [n for n, v in snap.items() if not torch.equal(model.get_parameter(n).detach().cpu(), v)]
    extra = sorted(set(weights_copy or {}) - set(snap))
    if bad or extra:
        raise Contamination(f"weights not restored: mismatched {bad}, unexpected {extra}")


def factor_update(delta, w_edit_norm, cfg, weight_dtype=torch.float32):
    """factor_delta with a tolerance that respects the storage roundoff of the weights."""
    dn = float(torch.linalg.norm(delta))
    if dn == 0.0:
        raise ValueError("delta is identically zero: the edit did not change this weight")
    u = torch.finfo(weight_dtype).eps / 2
    floor = u * w_edit_norm / dn
    tol = max(float(cfg["tol"]), float(cfg["floor_mult"]) * floor)
    A, B, fit = factor_delta(delta, max_rank=int(cfg["max_rank"]), tol=tol)
    fit.update(tol=tol, storage_floor=floor, delta_l2=dn)
    return A, B, fit


def diag_scores(model, tok, case):
    from rt.targets import continuation_logprobs
    names = {"target": case["target"], "o_new": case["o_new"], "o_old": case["o_old"]}
    keys = [k for k in names if k == "target" or names[k] != case["target"]]
    with torch.random.fork_rng(devices=_cuda_devices()):
        scores = continuation_logprobs(model, tok, case["prompt"], [" " + names[k] for k in keys])
    out = dict(zip(keys, scores))
    for k in names:
        out.setdefault(k, out["target"])
    return out


def _cuda_devices():
    return list(range(torch.cuda.device_count())) if torch.cuda.is_available() else []


# ---------------------------------------------------------------- the shard loop
@dataclasses.dataclass
class RunSpec:
    model_tag: str
    editor: str
    target_tag: str
    module_tmp: str
    hparams_sig: dict
    factor: dict = dataclasses.field(default_factory=lambda: dict(FACTOR_DEFAULT))
    dtype: str = "float32"

    @property
    def hparams_sha(self):
        return sha256_json(self.hparams_sig)

    def signature(self):
        return {"model_tag": self.model_tag, "editor": self.editor, "target_tag": self.target_tag,
                "module_tmp": self.module_tmp, "hparams_sha": self.hparams_sha,
                "factor": self.factor, "dtype": self.dtype}


def export_case(editor, case, spec, path, reset=None, log=print):
    """One edit -> one delta file.  Returns a log row; raises only on Contamination."""
    model, tok, hp = editor.model, editor.tok, editor.hparams
    names = edited_weight_names(hp)
    row = {"case_id": case["case_id"], "target": case["target"]}
    t0 = time.perf_counter()
    stage, wcopy, snap, rec, diag = "prepare", None, None, None, {}
    try:
        diag["reset"] = reset() if reset else None
        snap = snapshot(model, names)
        stage = "diag_before"
        diag["lp_before"] = diag_scores(model, tok, case)
        stage = "edit"
        tee = _Tee(sys.stdout)
        t1 = time.perf_counter()
        try:
            with contextlib.redirect_stdout(tee):
                # sequential_edit=True is deliberate: with False, EasyEdit restores ROME/MEMIT
                # weights inside edit() before returning (editor.py L406-409, CLAUDE.md).
                metrics, _, wcopy = editor.edit(prompts=[case["prompt"]],
                                                ground_truth=[case["o_old"]],
                                                target_new=[case["target"]],
                                                subject=[case["s"]], sequential_edit=True)
        finally:
            diag["editor_log"] = parse_editor_log(tee.buf.getvalue())
        diag["wall_edit_s"] = round(time.perf_counter() - t1, 3)
        diag["easyedit_metrics"] = _easyedit_metrics(metrics)
        stage = "extract"
        if set(wcopy) != set(names):
            raise RuntimeError(f"edited weights {sorted(wcopy)} != expected {names}")
        layers, fits = {}, {}
        for L, n in zip(hp.layers, names):
            stage = "extract"
            p = model.get_parameter(n).detach()
            if not torch.equal(wcopy[n].detach().cpu(), snap[n]):
                raise RuntimeError(f"EasyEdit's weights_copy of {n} differs from the pre-edit "
                                   "snapshot: the model was not at its base weights")
            d = p.float() - wcopy[n].to(p.device).float()
            if not torch.isfinite(d).all():
                raise FloatingPointError(f"non-finite ΔW at {n} (bf16 compute_v NaN? check dtype)")
            stage = "factor"
            A, B, fit = factor_update(d, float(torch.linalg.norm(p.float())), spec.factor,
                                      weight_dtype=p.dtype)
            fit["rel_delta"] = fit["delta_l2"] / float(torch.linalg.norm(wcopy[n].float()))
            fits[int(L)] = fit
            if not fit["ok"]:
                row["fit"] = fits
                raise ValueError(f"ΔW at layer {L} is not rank <= {fit['rank']}: rel_err "
                                 f"{fit['rel_err']:.3g} > tol {fit['tol']:.3g}")
            layers[int(L)] = {"A": A, "B": B}
            del d
        stage = "diag_after"
        diag["lp_after"] = diag_scores(model, tok, case)
        diag["context_templates_sha"] = context_templates_sha(spec.editor)
        diag["wall_s"] = round(time.perf_counter() - t0, 3)
        rec = {"case_id": case["case_id"], "model_tag": spec.model_tag, "editor": spec.editor,
               "target": case["target"], "target_tag": spec.target_tag,
               "module_tmp": spec.module_tmp, "layers": layers, "fit": fits, "diag": diag,
               "request": {"prompt": case["prompt"], "subject": case["s"],
                           "o_old": case["o_old"], "o_new": case["o_new"]},
               "hparams_sha": spec.hparams_sha, "hparams": spec.hparams_sig}
    except Contamination:
        raise
    except Exception as e:  # a bad case is logged and skipped, never allowed to stop the shard
        row.update(status="error", stage=stage, error=repr(e))
        if "editor_log" in diag:
            row["editor_log"] = diag["editor_log"]
        log(f"[delta-fail] {case['case_id']} at {stage}: {e!r}")
    finally:
        if snap is not None:
            restore(model, snap, wcopy)
    if rec is None:
        return row
    try:
        sha = save_delta(path, rec)
    except Exception as e:
        row.update(status="error", stage="save", error=repr(e))
        log(f"[delta-fail] {case['case_id']} at save: {e!r}")
        return row
    lp_b, lp_a = rec["diag"]["lp_before"], rec["diag"]["lp_after"]
    row.update(status="ok", sha=sha, path=os.path.relpath(path, _ROOT),
               layers=sorted(rec["layers"]),
               fit={L: {k: f[k] for k in ("rank", "rel_err", "tol", "rel_delta")}
                    for L, f in rec["fit"].items()},
               lp_first={"before": {k: v["first"] for k, v in lp_b.items()},
                         "after": {k: v["first"] for k, v in lp_a.items()}},
               editor_nan=rec["diag"]["editor_log"]["nan"],
               editor_steps=rec["diag"]["editor_log"]["n_steps"], wall_s=rec["diag"]["wall_s"])
    return row


def _easyedit_metrics(metrics):
    """EasyEdit's pre/post teacher-forced rewrite_acc (logits metric; diagnostic only)."""
    try:
        m = metrics[0]
        return {"pre_rewrite_acc": m["pre"].get("rewrite_acc"),
                "post_rewrite_acc": m["post"].get("rewrite_acc")}
    except Exception:
        return None


def context_templates_sha(editor_name):
    """Hash of the process-cached context templates EasyEdit sampled for this editor (or None)."""
    mod = {"ROME": "easyeditor.models.rome.rome_main", "MEMIT": "easyeditor.models.memit.memit_main",
           "AlphaEdit": "easyeditor.models.alphaedit.AlphaEdit_main"}.get(editor_name)
    cache = getattr(sys.modules.get(mod), "CONTEXT_TEMPLATES_CACHE", None) if mod else None
    return sha256_json(cache) if cache is not None else None


def read_log(log_path):
    header, errors = None, set()
    if os.path.exists(log_path):
        with open(log_path) as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("_meta") and header is None:
                    header = row
                elif row.get("status") == "error":
                    errors.add(row["case_id"])
    return header, errors


def run_shard(editor, cases, spec, out_dir, log_path, rank=0, world=1, header=None,
              retry_errors=False, reset=None, log=print):
    """Export this shard's cases; resumable by existing delta files.  Returns counts."""
    old_header, errors = read_log(log_path)
    if old_header is not None and old_header.get("run_signature") != spec.signature():
        raise RuntimeError(f"{log_path} was written with a different run signature; use a new "
                           "out_root/log or restore the original settings")
    if old_header is None and os.path.exists(log_path) and os.path.getsize(log_path) > 0:
        raise RuntimeError(f"refusing to append to headerless log {log_path}")
    os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
    counts = {"ok": 0, "error": 0, "skipped_existing": 0, "skipped_error": 0}
    templates_logged = False
    with open(log_path, "a") as fh:
        from vendor_patches.easyedit_lean_import import stubbed
        fh.write(json.dumps({"_meta": True, "run_signature": spec.signature(), "rank": rank,
                             "world": world, "easyedit_stubbed": stubbed(), **(header or {})},
                            ensure_ascii=False,
                            default=str) + "\n")
        fh.flush()
        for case in shard(cases, rank, world):
            path = delta_path(out_dir, spec.model_tag, spec.editor, spec.target_tag,
                              case["case_id"])
            if os.path.exists(path):
                _, old = load_delta(path, verify=False)
                if old.get("hparams_sha") != spec.hparams_sha or old.get("target") != case["target"]:
                    raise RuntimeError(f"{path} exists with other hparams/target; refusing to mix")
                counts["skipped_existing"] += 1
                continue
            if case["case_id"] in errors and not retry_errors:
                counts["skipped_error"] += 1
                continue
            try:
                row = export_case(editor, case, spec, path, reset=reset, log=log)
            except Contamination as e:
                fh.write(json.dumps({"case_id": case["case_id"], "status": "error",
                                     "stage": "restore", "error": repr(e)}) + "\n")
                fh.flush()
                raise
            counts[row["status"]] += 1
            if row["status"] == "ok" and not templates_logged:
                templates_logged = _log_templates(fh, spec.editor)
            fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
            fh.flush()
    return counts


def _log_templates(fh, editor_name):
    mod = {"ROME": "easyeditor.models.rome.rome_main", "MEMIT": "easyeditor.models.memit.memit_main",
           "AlphaEdit": "easyeditor.models.alphaedit.AlphaEdit_main"}.get(editor_name)
    cache = getattr(sys.modules.get(mod), "CONTEXT_TEMPLATES_CACHE", None)
    if cache is None:
        return False
    fh.write(json.dumps({"_templates": cache, "sha": sha256_json(cache)}, ensure_ascii=False) + "\n")
    return True


# ---------------------------------------------------------------- GPU-side setup (EasyEdit)
def ensure_easyedit_importable():
    """Stand in for easyeditor's optional extras before its first import; returns what was stubbed.

    See ``vendor_patches.easyedit_lean_import``: ROME/MEMIT/AlphaEdit need none of the multimodal,
    trainer or metric packages, and a stand-in raises if anything calls it.
    """
    from vendor_patches.easyedit_lean_import import apply
    return apply()


def build_hparams(settings, model_path, device, editor):
    """EasyEdit HyperParams from the template yaml plus deltas_models.yaml overrides."""
    ensure_easyedit_importable()
    import easyeditor
    cls = {"ROME": easyeditor.ROMEHyperParams, "MEMIT": easyeditor.MEMITHyperParams,
           "AlphaEdit": easyeditor.AlphaEditHyperParams}[editor]
    hp = cls.from_hparams(settings["template"])
    for k, v in settings["overrides"].items():
        if not hasattr(hp, k):
            raise ValueError(f"{editor} hparams have no field {k!r}")
        setattr(hp, k, v)
    hp.model_name, hp.device = model_path, device
    return hp


def mom2_config(hp, model_path):
    """npos for layer_stats' file name: from the model's config when loadable, else 4096 for
    qwen2-family names (layer_stats pins qwen2 to 4096)."""
    try:
        from transformers import AutoConfig
        from rt.mom2 import npos_for
        return npos_for(AutoConfig.from_pretrained(model_path))
    except Exception:
        if "qwen" in model_path.lower():
            return 4096
        raise


def mom2_files(hp, model_path, npos):
    from rt.mom2 import stats_path
    return {hp.rewrite_module_tmp.format(L): stats_path(
        hp.stats_dir, model_path, hp.rewrite_module_tmp.format(L), ds_name=hp.mom2_dataset,
        precision=hp.mom2_dtype, sample_size=hp.mom2_n_samples, npos=npos) for L in hp.layers}


def preflight(hp, editor, family, model_path, npos=None):
    """Checks that must pass before a GPU is touched; returns facts for the header."""
    import numpy as np
    check_routing(model_path, family)
    if hp.rewrite_module_tmp != MODULE_TMP:
        raise ValueError(f"rewrite_module_tmp {hp.rewrite_module_tmp!r} != {MODULE_TMP!r}")
    facts = {}
    if editor in NEEDS_STATS:
        npos = npos or mom2_config(hp, model_path)
        files = mom2_files(hp, model_path, npos)
        for layer_name, f in files.items():
            if not os.path.exists(f):
                raise FileNotFoundError(f"mom2 statistics missing for {layer_name}: {f} "
                                        "(run precompute-stats first)")
            z = np.load(f)
            if int(z["sample_size"]) != int(hp.mom2_n_samples):
                raise ValueError(f"{f}: sample_size {int(z['sample_size'])} != {hp.mom2_n_samples}")
            facts[layer_name] = {"path": f, "count": int(z["mom2.count"]),
                                 "bytes": os.path.getsize(f)}
    if editor == "AlphaEdit":
        side_path = hp.P_loc + ".json"
        if not (os.path.exists(hp.P_loc) and os.path.exists(side_path)):
            raise FileNotFoundError(f"AlphaEdit projector {hp.P_loc} (+.json) missing; run "
                                    "alphaedit-P (EasyEdit would otherwise crash on qwen)")
        with open(side_path) as fh:
            side = json.load(fh)
        want = {"layers": list(hp.layers), "threshold": float(hp.nullspace_threshold),
                "sample_size": int(hp.mom2_n_samples)}
        got = {k: side.get(k) for k in want}
        if got != want:
            raise ValueError(f"{side_path} was built for {got}, hparams need {want}")
        facts["P"] = {"path": hp.P_loc, "null_dim": side.get("null_dim")}
    return facts


def load_editor(hp, dtype):
    """BaseEditor exactly as edit_loop builds it (patches first), weights in ``dtype``."""
    os.environ["WHYAAAI_DTYPE"] = dtype          # read by the qwen2 loader patch at load time
    ensure_easyedit_importable()
    from vendor_patches.easyedit_qwen2_loader import apply as apply_qwen_loader_patch
    apply_qwen_loader_patch()
    from vendor_patches.easyedit_mom2_dataset import apply as apply_mom2_dataset_patch
    apply_mom2_dataset_patch()
    from vendor_patches.easyedit_mom2_cache_only import apply as apply_cache_only
    apply_cache_only()
    from easyeditor import BaseEditor
    ed = BaseEditor.from_hparams(hp)
    from r1_tokenizer import fix_r1_tokenizer
    ed.tok = fix_r1_tokenizer(ed.tok, hp.model_name)
    want = getattr(torch, dtype)
    for n in edited_weight_names(hp):
        got = ed.model.get_parameter(n).dtype
        if got != want:
            raise RuntimeError(f"{n} loaded as {got}, need {want} (WHYAAAI_DTYPE ignored?)")
    return ed


# ---------------------------------------------------------------- summarize (smoke checks)
def summarize(log_paths):
    """Latest row per case over shard logs: counts, fit, and how strongly the edit took."""
    import statistics
    latest = {}
    for p in log_paths:
        with open(p) as fh:
            for line in fh:
                if line.strip():
                    row = json.loads(line)
                    if row.get("case_id"):
                        latest[row["case_id"]] = row
    ok = [r for r in latest.values() if r.get("status") == "ok"]
    errors = {}
    for r in latest.values():
        if r.get("status") == "error":
            errors.setdefault(r.get("stage"), []).append(r["case_id"])

    def med(xs):
        return round(statistics.median(xs), 4) if xs else None
    lp = [(r["lp_first"]["before"], r["lp_first"]["after"]) for r in ok]
    fits = [f for r in ok for f in r["fit"].values()]
    return {"cases": len(latest), "ok": len(ok),
            "errors": {k: len(v) for k, v in errors.items()},
            "error_ids": {k: sorted(v)[:10] for k, v in errors.items()},
            "editor_nan": sum(1 for r in latest.values()
                              if r.get("editor_nan") or (r.get("editor_log") or {}).get("nan")),
            "max_rank": max((f["rank"] for f in fits), default=None),
            "max_rel_err": max((f["rel_err"] for f in fits), default=None),
            "median_rel_delta": med([f["rel_delta"] for f in fits]),
            "median_p_target_before": med([math.exp(b["target"]) for b, _ in lp]),
            "median_p_target_after": med([math.exp(a["target"]) for _, a in lp]),
            "median_gain_target_nats": med([a["target"] - b["target"] for b, a in lp]),
            "median_change_o_old_nats": med([a["o_old"] - b["o_old"] for b, a in lp]),
            "median_wall_s": med([r["wall_s"] for r in ok])}


# ---------------------------------------------------------------- export-pool
def export_pool(shard_glob, out_path, name, dataset_path=None):
    """Case ids of legacy result shards in first-seen order (shards by rank, lines in order)."""
    files = glob.glob(shard_glob)
    rank_of = {f: re.search(r"_r(\d+)of(\d+)\.jsonl$", f) for f in files}
    bad = [f for f, m in rank_of.items() if not m]
    if bad or not files:
        raise ValueError(f"no shards or unparsable shard names: {bad or shard_glob}")
    worlds = {int(m.group(2)) for m in rank_of.values()}
    ranks = sorted(int(m.group(1)) for m in rank_of.values())
    if len(worlds) != 1 or ranks != list(range(worlds.pop())):
        raise ValueError(f"shards do not form one complete rank set: {sorted(files)}")
    files.sort(key=lambda f: int(rank_of[f].group(1)))
    ids, seen, prompts, err_ids, sources = [], set(), {}, set(), []
    for f in files:
        n = 0
        with open(f) as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                n += 1
                cid = row.get("case_id")
                if not cid:
                    continue
                if cid not in seen:
                    seen.add(cid)
                    ids.append(cid)
                if row.get("error"):
                    err_ids.add(cid)
                if row.get("probe") == "efficacy" and row.get("q"):
                    prompts.setdefault(cid, row["q"])
        short = os.path.join(*os.path.normpath(os.path.abspath(f)).split(os.sep)[-3:])
        sources.append({"path": short, "sha256": sha256_file(f), "n_rows": n})
    checks = {"cases_with_error_rows": sorted(err_ids)}
    if dataset_path:
        with open(dataset_path) as fh:
            rows = {r["case_id"]: r for r in (json.loads(x) for x in fh if x.strip())}
        missing = [c for c in ids if c not in rows]
        if missing:
            raise ValueError(f"{len(missing)} ids not in {dataset_path}: {missing[:5]}")
        mism = [c for c in ids if c in prompts and prompts[c] != rows[c]["prompt"]]
        checks.update(in_dataset=len(ids), efficacy_prompt_checked=len(prompts),
                      efficacy_prompt_mismatch=mism, dataset_sha256=sha256_file(dataset_path))
    manifest = {"name": name, "created": now(), "n": len(ids), "sha256": ids_sha(ids),
                "rule": "case_id first-seen order over the shards sorted by rank, lines in file "
                        "order (shard k holds pool positions k, k+world, ...)",
                "source": sources, "checks": checks, "case_ids": ids}
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(manifest, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    return manifest


# ---------------------------------------------------------------- precompute-stats / alphaedit-P
def stats_plan(models, model_tag, editors):
    """Layers and mom2 settings shared by the given editors (read from the template yamls)."""
    plan = None
    for ed in editors:
        s = editor_settings(models, model_tag, ed)
        with open(s["template"]) as fh:
            t = yaml.safe_load(fh)
        t.update(s["overrides"])
        mine = {k: t[k] for k in ("rewrite_module_tmp", "mom2_dataset", "mom2_n_samples",
                                  "mom2_dtype", "stats_dir")}
        if plan is None:
            plan = dict(mine, layers=set(t["layers"]))
        else:
            if any(plan[k] != mine[k] for k in mine):
                raise ValueError(f"{editors} disagree on mom2 settings: {plan} vs {mine}")
            plan["layers"] |= set(t["layers"])
    plan["layers"] = sorted(plan["layers"])
    plan["family"] = models["models"][model_tag]["family"]
    return plan


def cmd_precompute_stats(args):
    from rt import mom2
    models = load_models(_abs(args.models_file))
    spec = models["models"][args.model]
    plan = stats_plan(models, args.model, args.editors)
    if args.stats_dir:
        plan["stats_dir"] = _abs(args.stats_dir)
    if args.sample_size:
        plan["mom2_n_samples"] = args.sample_size
    model_path = resolve_model_path(args.model_path, spec)
    check_routing(model_path, plan["family"])
    from transformers import AutoConfig
    config = AutoConfig.from_pretrained(model_path)
    npos = mom2.npos_for(config)
    batch_tokens = npos * 3
    maxlen = mom2.maxlen_for(config, batch_tokens)
    layer_names = [plan["rewrite_module_tmp"].format(L) for L in plan["layers"]]
    finals = {n: mom2.stats_path(plan["stats_dir"], model_path, n, plan["mom2_dataset"],
                                 plan["mom2_dtype"], plan["mom2_n_samples"], npos=npos)
              for n in layer_names}
    if plan["mom2_dataset"] != "wikipedia":
        raise ValueError("only the wikipedia mom2 corpus is supported")
    files = mom2.english_wiki_files(args.wiki)
    if files is None and not args.allow_hub:
        raise FileNotFoundError("no local English Wikipedia parquet; set --wiki / "
                                f"${mom2.WIKI_ENV} or pass --allow-hub")
    rows = mom2.load_wiki(files)
    english = mom2.assert_english(rows)
    groups = mom2.sample_groups(len(rows), plan["mom2_n_samples"])
    corpus = mom2.corpus_fingerprint(files, len(rows))
    print(f"[stats] {args.model} layers={plan['layers']} n={plan['mom2_n_samples']} "
          f"groups={len(groups)} npos={npos} corpus={corpus.get('dir', 'hub')} ascii={english:.3f}")
    for n, f in finals.items():
        print(f"[stats]   {n} -> {f}")
    if args.prepare:                      # single process: builds the datasets cache, checks order
        from vendor_patches.easyedit_qwen2_loader import PatchedAutoTokenizer
        tok = PatchedAutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        xcheck = _crosscheck_easyedit(rows, tok, maxlen, batch_tokens, groups,
                                      mom2.TokenizedTexts(rows, tok, maxlen), plan["mom2_n_samples"])
        print(f"[stats] prepared; EasyEdit cross-check: {xcheck}")
        return
    if args.merge:
        for n, f in finals.items():
            if os.path.exists(f):
                print(f"[stats] {n}: final file already present, not re-merged")
            else:
                s = mom2.merge_parts(f, args.world, plan["mom2_n_samples"], len(groups))
                print(f"[stats] merged {n}: count={s['count']} asym={s['asym']:.2e}")
            _verify_final(f, n, plan, model_path, config)
        return
    todo = {n: f for n, f in finals.items()
            if not os.path.exists(f) and not os.path.exists(mom2.part_path(f, args.rank, args.world))}
    if not todo:
        print("[stats] nothing to do (final or partial files exist)")
        return
    mine = [g for g in range(len(groups)) if g % args.world == args.rank]
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.set_float32_matmul_precision("highest")
    from transformers import AutoModelForCausalLM
    from vendor_patches.easyedit_qwen2_loader import PatchedAutoTokenizer
    tok = PatchedAutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    device_map = args.device_map or {"": f"cuda:{args.device}"}
    model = AutoModelForCausalLM.from_pretrained(model_path, dtype=torch.bfloat16,
                                                 device_map=device_map).eval()
    for p in model.parameters():
        p.requires_grad_(False)
    dataset = mom2.TokenizedTexts(rows, tok, maxlen)
    xcheck = _crosscheck_easyedit(rows, tok, maxlen, batch_tokens, groups, dataset,
                                  plan["mom2_n_samples"])
    t0 = time.time()
    acc = mom2.collect(model, dataset, [groups[g] for g in mine], list(todo), batch_tokens,
                       precision=plan["mom2_dtype"], progress_every=10)
    meta = {"model_path": model_path, "model_base": os.path.basename(model_path),
            "forward_dtype": "bfloat16", "precision": plan["mom2_dtype"],
            "sample_size": plan["mom2_n_samples"], "seed": mom2.SAMPLE_SEED,
            "group_size": mom2.GROUP_SIZE, "n_groups": len(groups), "npos": npos,
            "batch_tokens": batch_tokens, "maxlen": maxlen, "world": args.world,
            "corpus": corpus, "tokenizer_class": type(tok).__name__,
            "fp32_matmul_precision": torch.get_float32_matmul_precision(),
            "easyedit_crosscheck": xcheck,
            "deviation": "activations from a bf16 forward (EasyEdit's lazy path: fp32 model); "
                         "fp32 accumulation; per-rank partial sums added in float64"}
    for n, (m, c) in acc.items():
        path = mom2.part_path(todo[n], args.rank, args.world)
        mom2.save_part(path, m, c, mine, dict(meta, layer_name=n, rank=args.rank, count=c,
                                               created=now(), wall_s=round(time.time() - t0),
                                               **git_provenance()))
        print(f"[stats] rank {args.rank}: {n} count={c} -> {path}")


def _crosscheck_easyedit(rows, tok, maxlen, batch_tokens, groups, dataset, sample_size):
    """Compare our sampling/tokenization/collation mirrors with EasyEdit's own code on group 0."""
    try:
        ensure_easyedit_importable()
        from easyeditor.models.rome.tok_dataset import TokenizedDataset, length_collation
        from easyeditor.util.runningstats import FixedRandomSubsetSampler
    except Exception as e:
        return {"skipped": repr(e)}
    from rt import mom2
    ref_idx = FixedRandomSubsetSampler(rows, seed=mom2.SAMPLE_SEED, end=sample_size).samples
    flat = [i for g in groups for i in g]
    if list(ref_idx) != flat:
        raise RuntimeError("sample order differs from EasyEdit's FixedRandomSubsetSampler")
    ref_ds = TokenizedDataset(rows, tok, maxlen=maxlen)
    ref = length_collation(batch_tokens)([ref_ds[i] for i in groups[0]])
    got = mom2.length_collation(batch_tokens)([dataset[i] for i in groups[0]])
    same = len(ref) == len(got) and all(
        set(a) == set(b) and all(torch.equal(a[k], b[k]) for k in a) for a, b in zip(ref, got))
    if not same:
        raise RuntimeError("tokenization/collation differs from EasyEdit's on group 0")
    return {"sampler": "equal", "group0_sub_batches": len(ref)}


def _verify_final(path, layer_name, plan, model_path, config):
    from types import SimpleNamespace
    from rt import mom2
    cov, count = mom2.read_easyedit_stats(path, plan["mom2_n_samples"])
    if not torch.isfinite(cov).all():
        raise ValueError(f"{path}: non-finite moment")
    hp = SimpleNamespace(stats_dir=plan["stats_dir"], mom2_dataset=plan["mom2_dataset"],
                         mom2_n_samples=plan["mom2_n_samples"], mom2_dtype=plan["mom2_dtype"],
                         device="cpu")
    config._name_or_path = model_path
    try:
        n = mom2.verify_with_easyedit(config, None, layer_name, hp)
        print(f"[stats] EasyEdit layer_stats loads {layer_name}: count={n}")
    except ImportError as e:
        print(f"[stats] easyeditor not importable, EasyEdit load check skipped ({e!r})")


def cmd_alphaedit_p(args):
    from rt import mom2
    models = load_models(_abs(args.models_file))
    spec = models["models"][args.model]
    s = editor_settings(models, args.model, "AlphaEdit")
    with open(s["template"]) as fh:
        t = yaml.safe_load(fh)
    t.update(s["overrides"])
    model_path = resolve_model_path(args.model_path, spec)
    from transformers import AutoConfig
    npos = mom2.npos_for(AutoConfig.from_pretrained(model_path))
    projectors, per_layer, stats = [], {}, {}
    for L in t["layers"]:
        name = t["rewrite_module_tmp"].format(L)
        path = mom2.stats_path(t["stats_dir"], model_path, name, t["mom2_dataset"], t["mom2_dtype"],
                               t["mom2_n_samples"], npos=npos)
        P, info = mom2.null_space_projector(path, float(t["nullspace_threshold"]),
                                            t["mom2_n_samples"], device=args.svd_device)
        projectors.append(P)
        per_layer[int(L)], stats[int(L)] = info, path
        print(f"[P] layer {L}: null_dim {info['null_dim']}/{info['dim']} "
              f"(near threshold: {info['near_threshold']})")
    side = mom2.save_projector(t["P_loc"], projectors, t["layers"], {
        "threshold": float(t["nullspace_threshold"]), "sample_size": int(t["mom2_n_samples"]),
        "null_dim": {L: v["null_dim"] for L, v in per_layer.items()}, "per_layer": per_layer,
        "stats": stats, "svd_device": args.svd_device, "created": now(), **git_provenance()})
    print(f"[P] saved {side['shape']} -> {t['P_loc']}")


# ---------------------------------------------------------------- run
def load_run_config(path):
    with open(path) as fh:
        cfg = yaml.safe_load(fh)
    cfg.setdefault("models_file", "experiments/rt/deltas_models.yaml")
    cfg.setdefault("dataset", "data/counterfact.jsonl")
    cfg.setdefault("out_root", "deltas")
    cfg.setdefault("log_dir", "results/rt/deltas_logs")
    cfg.setdefault("dtype", "float32")
    cfg["factor"] = dict(FACTOR_DEFAULT, **(cfg.get("factor") or {}))
    return cfg


def cmd_run(args):
    cfg = load_run_config(_abs(args.config))
    for key in ("editor", "target_tag", "out_root", "targets_file", "pool"):
        if getattr(args, key, None):
            cfg[key] = getattr(args, key)
    editor_name, target_tag = cfg["editor"], cfg["target_tag"]
    models = load_models(_abs(cfg["models_file"]))
    model_tag = cfg["model"]
    settings = editor_settings(models, model_tag, editor_name)
    model_path = resolve_model_path(args.model_path, models["models"][model_tag])
    ids, pool_meta = load_pool(_abs(cfg["pool"]))
    cases = load_cases(_abs(cfg["dataset"]), ids)
    targets = None
    if target_tag != "cf":
        if not cfg.get("targets_file"):
            raise SystemExit(f"target_tag {target_tag!r} needs --targets-file (see rt.targets)")
        from rt.targets import load_targets
        targets = load_targets(_abs(cfg["targets_file"]), target_tag, model_tag)
    cases = attach_targets(cases, target_tag, targets)
    if args.limit:
        cases = cases[:args.limit]
    mine = shard(cases, args.rank, args.world)
    out_root = _abs(cfg["out_root"])
    log_path = os.path.join(_abs(cfg["log_dir"]), f"{model_tag}_{editor_name}_{target_tag}"
                                                  f"_r{args.rank}of{args.world}.jsonl")
    print(f"[deltas] {model_tag} {editor_name} {target_tag} pool={pool_meta['name']} "
          f"n={len(cases)} shard={len(mine)} rank={args.rank}/{args.world} model={model_path}")
    print(f"[deltas] out={os.path.join(out_root, model_tag, editor_name, target_tag)} log={log_path}")
    if args.dry_run:
        print(f"[dry] template={settings['template']} overrides={settings['overrides']}")
        print(f"[dry] first cases: {[c['case_id'] for c in mine[:5]]}")
        return
    hp = build_hparams(settings, model_path, args.device, editor_name)
    facts = preflight(hp, editor_name, settings["family"], model_path)
    spec = RunSpec(model_tag=model_tag, editor=editor_name, target_tag=target_tag,
                   module_tmp=hp.rewrite_module_tmp, hparams_sig=hparams_signature(hp, cfg["dtype"]),
                   factor=cfg["factor"], dtype=cfg["dtype"])
    ed = load_editor(hp, cfg["dtype"])
    reset = None
    if editor_name == "AlphaEdit":
        from vendor_patches.easyedit_alphaedit_cache import reset
    header = {**git_provenance(), "created": now(), "config": args.config,
              "config_sha256": sha256_file(_abs(args.config)), "code_sha256": code_sha256(),
              "pool": pool_meta, "limit": args.limit, "targets_file": cfg.get("targets_file"),
              "model_path": model_path, "runtime_env": runtime_env(),
              "software": software_provenance(), "preflight": facts,
              "actual_runtime": model_runtime(ed.model, ed.tok, hp)}
    if targets is not None:
        header["targets_sha256"] = sha256_file(_abs(cfg["targets_file"]))
    counts = run_shard(ed, cases, spec, out_root, log_path, rank=args.rank, world=args.world,
                       header=header, retry_errors=args.retry_errors, reset=reset)
    print(f"[deltas] done: {counts}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="engine v2: fp32 EasyEdit edits -> low-rank deltas")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="edit + export one shard")
    r.add_argument("--config", required=True)
    r.add_argument("--editor", choices=EDITORS)
    r.add_argument("--target-tag", dest="target_tag")
    r.add_argument("--targets-file", dest="targets_file")
    r.add_argument("--out-root", dest="out_root")
    r.add_argument("--pool", help="pool manifest (JSON with case_ids); overrides the config")
    r.add_argument("--model-path", default=None)
    r.add_argument("--rank", type=int, default=0)
    r.add_argument("--world", type=int, default=1)
    r.add_argument("--device", type=int, default=0)
    r.add_argument("--limit", type=int, default=None, help="first N pool cases (smoke)")
    r.add_argument("--retry-errors", action="store_true")
    r.add_argument("--dry-run", action="store_true")

    e = sub.add_parser("export-pool", help="case-id manifest from legacy result shards")
    e.add_argument("--shards", required=True, help="glob, e.g. 'results 2/probe/X_r*of8.jsonl'")
    e.add_argument("--out", required=True)
    e.add_argument("--name", required=True)
    e.add_argument("--dataset", default="data/counterfact.jsonl")

    s = sub.add_parser("precompute-stats", help="mom2 statistics (bf16 forward, fp32 sums)")
    s.add_argument("--model", required=True)
    s.add_argument("--editors", nargs="+", default=["MEMIT", "AlphaEdit"], choices=NEEDS_STATS)
    s.add_argument("--models-file", default="experiments/rt/deltas_models.yaml")
    s.add_argument("--model-path", default=None)
    s.add_argument("--wiki", default=None, help="English parquet dir/glob (default $WHYAAAI_WIKI_PARQUET)")
    s.add_argument("--allow-hub", action="store_true")
    s.add_argument("--rank", type=int, default=0)
    s.add_argument("--world", type=int, default=1)
    s.add_argument("--device", type=int, default=0)
    s.add_argument("--device-map", default=None, help="'auto' to spread one process over GPUs")
    s.add_argument("--prepare", action="store_true",
                   help="single process: load/cache the corpus, check it, print the plan, exit")
    s.add_argument("--merge", action="store_true", help="combine the partial files (CPU)")
    s.add_argument("--stats-dir", default=None, help="smoke only: write elsewhere")
    s.add_argument("--sample-size", type=int, default=None, help="smoke only (changes file name)")

    m = sub.add_parser("summarize", help="smoke/progress summary of shard logs")
    m.add_argument("logs", nargs="+")

    c = sub.add_parser("compare-stats", help="distance between two mom2 cache files")
    c.add_argument("a")
    c.add_argument("b")

    p = sub.add_parser("alphaedit-P", help="AlphaEdit null-space projector from cached stats")
    p.add_argument("--model", required=True)
    p.add_argument("--models-file", default="experiments/rt/deltas_models.yaml")
    p.add_argument("--model-path", default=None)
    p.add_argument("--svd-device", default="cuda:0" if torch.cuda.is_available() else "cpu")

    args = ap.parse_args(argv)
    if args.cmd == "run":
        cmd_run(args)
    elif args.cmd == "export-pool":
        m = export_pool(args.shards, _abs(args.out), args.name,
                        _abs(args.dataset) if args.dataset else None)
        print(f"[pool] {m['name']}: n={m['n']} sha256={m['sha256'][:12]} checks="
              f"{ {k: (len(v) if isinstance(v, list) else v) for k, v in m['checks'].items()} }")
    elif args.cmd == "summarize":
        print(json.dumps(summarize(args.logs), indent=1))
    elif args.cmd == "compare-stats":
        from rt.mom2 import compare_stats
        print(json.dumps(compare_stats(args.a, args.b), indent=1))
    elif args.cmd == "precompute-stats":
        cmd_precompute_stats(args)
    elif args.cmd == "alphaedit-P":
        cmd_alphaedit_p(args)


if __name__ == "__main__":
    main()
