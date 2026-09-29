"""Per-row low-rank edits injected through forward hooks (engine v2).

A single-request ROME, MEMIT or AlphaEdit update is rank 1 on each edited weight:
ΔW = B @ A with B of shape (out, r) and A of shape (r, in), in the HF weight layout
(out, in).  Instead of writing ΔW into the weights, ``EditBank`` adds
``alpha * (x @ A.T) @ B.T`` to the edited module's output row by row.  One batch can
therefore carry a different edit in every row while each row still sees only its own
edit (the single-edit protocol), and an analysis can switch an edit off at chosen
positions.

ΔW itself is still computed by EasyEdit in fp32 (``deltas.py``); this module only
factors, stores and applies it.
"""
import hashlib
import os

import torch

FORMAT = "rt-delta-v1"


def factor_delta(delta, max_rank=8, tol=1e-4, seed=0):
    """Factor a weight difference ``delta`` (out, in) into float32 ``A`` (r, in), ``B`` (out, r).

    The decomposition runs in ``delta``'s dtype when it is float32 or float64 (rt.deltas passes a
    float64 CPU copy), otherwise in float32.

    The rank is the smallest r whose relative reconstruction error ||delta - B@A|| / ||delta||
    is at most ``tol``, capped at ``max_rank``.  The returned fit record keeps the leading
    singular values and the achieved error, so an update that is not low rank is reported
    (``ok`` false) instead of being silently truncated.
    """
    d = delta.detach()
    if d.dtype not in (torch.float32, torch.float64):
        d = d.float()
    norm = torch.linalg.norm(d)
    if float(norm) == 0.0:
        raise ValueError("delta is identically zero: the edit did not change this weight")
    q = min(max_rank + 2, min(d.shape))
    with torch.random.fork_rng(devices=[d.device] if d.is_cuda else []):
        torch.manual_seed(seed)
        U, S, V = torch.svd_lowrank(d, q=q, niter=6)
    best = None
    for r in range(1, min(max_rank, q) + 1):
        B = U[:, :r] * S[:r]
        A = V[:, :r].T.contiguous()
        err = float(torch.linalg.norm(d - B @ A) / norm)
        best = (A, B, r, err)
        if err <= tol:
            break
    A, B, r, err = best
    fit = {"rank": r, "rel_err": err, "sigma": [float(x) for x in S.tolist()],
           "ok": err <= tol}
    return A.float().contiguous(), B.float().contiguous(), fit


def delta_sha(rec):
    """Content hash of a delta record: identity fields plus every factor tensor."""
    h = hashlib.sha256()
    for key in ("case_id", "model_tag", "editor", "target", "target_tag", "module_tmp"):
        h.update(f"{key}={rec.get(key)!r};".encode())
    for layer in sorted(rec["layers"]):
        h.update(f"L{layer};".encode())
        for name in ("A", "B"):
            t = rec["layers"][layer][name].detach().to("cpu", torch.float32).contiguous()
            h.update(t.numpy().tobytes())
    return h.hexdigest()


def save_delta(path, rec):
    """Write a delta record atomically and return its content hash."""
    missing = {"case_id", "model_tag", "editor", "target", "target_tag", "module_tmp",
               "layers"} - set(rec)
    if missing:
        raise ValueError(f"delta record missing {sorted(missing)}")
    rec = dict(rec, format=FORMAT)
    rec["layers"] = {int(k): {"A": v["A"].detach().to("cpu", torch.float32).contiguous(),
                              "B": v["B"].detach().to("cpu", torch.float32).contiguous()}
                     for k, v in rec["layers"].items()}
    rec["sha"] = delta_sha(rec)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    torch.save(rec, tmp)
    os.replace(tmp, path)
    return rec["sha"]


def load_delta(path, verify=True):
    """Read a delta record; returns (edit, rec) where edit maps layer -> (A, B)."""
    rec = torch.load(path, map_location="cpu", weights_only=False)
    if rec.get("format") != FORMAT:
        raise ValueError(f"{path}: unknown delta format {rec.get('format')!r}")
    if verify and delta_sha(rec) != rec.get("sha"):
        raise ValueError(f"{path}: content hash mismatch")
    edit = {int(k): (v["A"], v["B"]) for k, v in rec["layers"].items()}
    return edit, rec


class EditBank:
    """Applies a different low-rank edit to each batch row through forward hooks.

    Usage::

        bank = EditBank(model, "model.layers.{}.mlp.down_proj")
        with bank:
            bank.set_batch([edit_a, None, edit_b], alphas=[1.0, 1.0, 2.0])
            out = model.generate(...)          # row 1 runs the unedited model

    ``edits[i]`` maps layer -> (A, B) or is None.  ``pos_mask`` (batch, seq) scales the edit
    per position and is only meaningful for a single full-sequence forward pass; it must be
    None during generation.
    """

    def __init__(self, model, module_tmp):
        self.model = model
        self.module_tmp = module_tmp
        self._handles = []
        self._state = {}
        self._alpha = None
        self._pos_mask = None
        self._active = False

    def _module(self, layer):
        return self.model.get_submodule(self.module_tmp.format(layer))

    def __enter__(self):
        self._active = True
        self._register()
        return self

    def __exit__(self, *exc):
        self.clear()
        self._active = False
        return False

    def clear(self):
        for h in self._handles:
            h.remove()
        self._handles = []
        self._state = {}
        self._alpha = None
        self._pos_mask = None

    @property
    def n_hooks(self):
        return len(self._handles)

    def set_batch(self, edits, alphas=None, pos_mask=None):
        n = len(edits)
        if alphas is not None and len(alphas) != n:
            raise ValueError("alphas must have one entry per row")
        if pos_mask is not None and pos_mask.shape[0] != n:
            raise ValueError("pos_mask must have one row per batch row")
        layers = sorted({int(L) for e in edits if e for L in e})
        state = {}
        for L in layers:
            mod = self._module(L)
            dev, dt = mod.weight.device, mod.weight.dtype
            d_out, d_in = mod.weight.shape
            r = max(e[L][0].shape[0] for e in edits if e and L in e)
            A = torch.zeros(n, r, d_in, dtype=dt, device=dev)
            B = torch.zeros(n, d_out, r, dtype=dt, device=dev)
            for i, e in enumerate(edits):
                if e and L in e:
                    a, b = e[L]
                    if a.shape[1] != d_in or b.shape[0] != d_out:
                        raise ValueError(f"row {i} layer {L}: factor shapes {tuple(a.shape)}, "
                                         f"{tuple(b.shape)} do not fit weight ({d_out}, {d_in})")
                    A[i, :a.shape[0]] = a.to(dev, dt)
                    B[i, :, :b.shape[1]] = b.to(dev, dt)
            state[L] = (A, B)
        self._state = state
        self._alpha = torch.tensor([1.0] * n if alphas is None else [float(a) for a in alphas],
                                   dtype=torch.float32)
        self._pos_mask = pos_mask
        if self._active:
            self._register()

    def _register(self):
        for h in self._handles:
            h.remove()
        self._handles = [self._module(L).register_forward_hook(self._hook(L))
                         for L in self._state]

    def _hook(self, layer):
        def fn(module, inputs, output):
            A, B = self._state[layer]
            x = inputs[0]
            if x.shape[0] != A.shape[0]:
                raise RuntimeError(f"EditBank holds {A.shape[0]} rows but the forward pass has "
                                   f"{x.shape[0]}; call set_batch with the batch being run")
            z = torch.einsum("bsi,bri->bsr", x, A).float()
            z = z * self._alpha.to(z.device)[:, None, None]
            if self._pos_mask is not None:
                m = self._pos_mask.to(z.device, torch.float32)
                if m.shape[1] != z.shape[1]:
                    raise RuntimeError("pos_mask length differs from the sequence length; "
                                       "position masks are for single full-sequence passes only")
                z = z * m[:, :, None]
            return output + torch.einsum("bsr,bor->bso", z.to(output.dtype), B)
        return fn
