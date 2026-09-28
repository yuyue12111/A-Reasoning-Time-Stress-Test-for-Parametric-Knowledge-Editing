"""Mechanism probes for edit reversion (engine v2; REVISION.md §1 item 5, §4).

Both probes are teacher-forced over a chain the edited model already produced (Study-1 rows), so
each case costs a forward pass or two and no generation.

Premise.  In a causal transformer the residual stream at the question's tokens does not depend on
anything that follows them, so a rank-1 edit ΔW = B·A on one down_proj fires identically on the
question at B0 and at B3.  Reversion must come from what the chain adds later:

(a) key-miss: later mentions of the subject inside the chain (partial names, other contexts) whose
    down_proj input x does not align with the edit's key direction A, so the edit does not fire;
(b) bridge facts the edit never touched;
(c) the answer relying less on the question-position edit after a long chain.

``trace`` measures the edit activation a_i = (A·x_i) / (A·x_ref) at every position, where x_ref is
the down_proj input at the last token of the subject's first occurrence in the question (a = 1
there by construction; the edit adds a_i · B·(A·x_ref) at position i).  It locates full and
partial subject mentions and the first old/new value mentions (alias-aware, subject-scrubbed as in
``metrics``) and reports the activation at each mention's last token.  This tests (a).

``gate`` switches the edit on only at chosen positions with ``EditBank``'s position mask and reads
the log-probability of the first token of " "+o_new and " "+o_old right after the answer prefix
(the CounterFact prompt).  Question-only versus all-position gating separates (a) from (b)/(c).

Sequences follow ``think_budget``: BOS + TPL(q) + cot + "\\n</think>\\n\\n" + tail, tokenized as one
string (the answer phase of ``generate_with_budget`` re-tokenizes exactly this string).  BOS
follows ``_gen``'s rule (on unless WHYAAAI_NO_BOS) unless ``bos`` forces it; the Study-1 Qwen
chains were generated without BOS.  B0 is the same layout with an empty chain, since ZEROTHINK == TPL + that tail.
Segments: q = positions before the chain; c = the chain plus the closing tail; p = the answer or
answer prefix.  A token that straddles a boundary belongs to the later segment.

bf16 note: activations are ratios of bf16 dot products (about 1e-2 relative error) and gated
log-probs carry bf16 logits; cross-check a few cases in fp32 before reading small differences.
"""
import argparse
import base64
import glob
import hashlib
import json
import os
import platform
import random
import re
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
import torch

import metrics
from think_budget import THINK_END, TPL, ZEROTHINK
from rt.edit_hooks import EditBank, load_delta

TAIL = "\n" + THINK_END + "\n\n"
assert ZEROTHINK.format(q="Q") == TPL.format(q="Q") + TAIL, "B0 must be TPL with an empty chain"

MASK_SEGS = {"none": (), "all": ("q", "c", "p"), "question_only": ("q",),
             "chain_and_answer_only": ("c", "p"), "answer_only": ("p",),
             "question_and_answer": ("q", "p")}
MASKS = tuple(MASK_SEGS)
PARTIAL_MIN_LEN = 4
LOW_A = 0.5
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------- sequences and spans

def bos_text(tok, bos=None):
    """BOS text to prepend.  ``bos`` None applies ``think_budget._gen``'s rule (BOS unless
    WHYAAAI_NO_BOS is set); True or False forces it, e.g. False to match chains generated
    without BOS (the Study-1 Qwen runs)."""
    if bos is None:
        bos = not os.environ.get("WHYAAAI_NO_BOS")
    return (tok.bos_token or "") if bos else ""


def tok_at(offsets, c):
    """Index of the first token whose character span ends after ``c`` (len(offsets) if none)."""
    for i, (_, e) in enumerate(offsets):
        if e > c:
            return i
    return len(offsets)


def char_span_tokens(offsets, s, e):
    """(first, last) token indices covering characters [s, e)."""
    first = tok_at(offsets, s)
    if first >= len(offsets) or offsets[first][0] >= e:
        raise ValueError(f"no token covers characters [{s}, {e})")
    last = first
    while last + 1 < len(offsets) and offsets[last + 1][0] < e:
        last += 1
    return first, last


def _check_offsets(offsets, n_chars):
    prev = 0
    for i, (s, e) in enumerate(offsets):
        if not (0 <= s <= e <= n_chars) or s < prev:
            raise ValueError(f"token {i} has offsets ({s}, {e}); the tokenizer must return "
                             "monotone character offsets for mech probes")
        prev = s


def compose(tok, q, cot="", tail="", bos=None):
    """Tokenize BOS + TPL(q) + cot + TAIL + tail and locate its segments (``bos``: see bos_text).

    Returns a dict with ``text``, ``ids``, ``offsets`` (character spans), ``chars`` (character
    ranges of q, cot and tail) and ``seg`` (token ranges q/c/p as half-open pairs).
    """
    bos = bos_text(tok, bos)
    head = bos + TPL.format(q=q)
    text = head + cot + TAIL + tail
    enc = tok(text, add_special_tokens=False, return_offsets_mapping=True)
    ids = list(enc["input_ids"])
    offsets = [tuple(int(v) for v in o) for o in enc["offset_mapping"]]
    _check_offsets(offsets, len(text))
    q0 = len(bos) + TPL.index("{q}")
    t0 = len(head) + len(cot) + len(TAIL)
    chars = {"q": (q0, q0 + len(q)), "cot": (len(head), len(head) + len(cot)),
             "tail": (t0, len(text))}
    c0, p0 = tok_at(offsets, len(head)), tok_at(offsets, t0)
    return {"text": text, "ids": ids, "offsets": offsets, "chars": chars, "bos": bool(bos),
            "seg": {"q": (0, c0), "c": (c0, p0), "p": (p0, len(ids))}}


def find_subject(q, subject):
    """Character span of the subject's first occurrence in ``q`` (exact, else case-insensitive)."""
    i = q.find(subject)
    if i >= 0:
        return i, i + len(subject)
    m = re.search(re.escape(subject), q, re.IGNORECASE)
    if not m:
        raise ValueError(f"subject {subject!r} does not occur in question {q!r}")
    return m.start(), m.end()


def _phrase_re(s):
    return re.compile(r"(?<!\w)" + re.escape(s) + r"(?!\w)", re.IGNORECASE)


def subject_words(subject, min_len=PARTIAL_MIN_LEN):
    """Distinct (case-insensitive) whole words of the subject with at least ``min_len`` chars."""
    seen, out = set(), []
    for w in re.findall(r"\w+", subject or ""):
        if len(w) >= min_len and w.lower() not in seen:
            seen.add(w.lower())
            out.append(w)
    return out


def subject_mentions(text, subject, start=0, end=None, min_len=PARTIAL_MIN_LEN):
    """Full and partial subject mentions in text[start:end], sorted by position.

    Full: the whole subject, case-insensitive, not inside a longer word.  Partial: any whole word
    of the subject with ``min_len`` or more characters, case-insensitive, outside full mentions.
    Spans are absolute character offsets into ``text``.
    """
    end = len(text) if end is None else end
    full = [(m.start(), m.end()) for m in _phrase_re(subject).finditer(text, start, end)]
    out = [{"kind": "full", "span": [s, e], "text": text[s:e]} for s, e in full]
    for w in subject_words(subject, min_len):
        for m in _phrase_re(w).finditer(text, start, end):
            if any(m.start() < e and s < m.end() for s, e in full):
                continue
            out.append({"kind": "partial", "word": w, "span": [m.start(), m.end()],
                        "text": m.group(0)})
    return sorted(out, key=lambda d: d["span"][0])


def scrub_subject(text, subject):
    """``metrics._without_subject`` with the subject blanked to equal-length spaces.

    Blanking to spaces leaves the same word boundaries as metrics' single space, so value hits are
    unchanged, while character offsets stay valid for the unscrubbed text.
    """
    if not text or not subject:
        return text or ""
    return re.sub(re.escape(subject), lambda m: " " * len(m.group(0)), text, flags=re.IGNORECASE)


def first_value_span(text, value, aliases):
    """(start, end) of the first mention of ``value`` in ``text`` under metrics' rules, or None.

    Same candidates (target plus aliases of 4+ characters) and word-boundary matching on
    lowercased text as ``metrics.first_mention``.  Scrub the subject first (``scrub_subject``).
    """
    low = text.lower()
    if len(low) != len(text):          # rare characters whose lowercase changes length
        low = "".join(c.lower() if len(c.lower()) == 1 else c for c in text)
    best = None
    for cand in metrics._safe_cands(value, aliases or {}):
        if not cand:
            continue
        m = metrics._wb(cand).search(low)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), m.end())
    return best


def value_token(tok, value):
    """Id of the first token of " " + value (the token that follows the answer prefix)."""
    return tok(" " + value, add_special_tokens=False)["input_ids"][0]


# ---------------------------------------------------------------- model passes

def _in_device(model):
    return model.get_input_embeddings().weight.device


def _forward(model, ids):
    return model(input_ids=ids, use_cache=False, logits_to_keep=1)


@torch.no_grad()
def capture_z(model, module_tmp, edit, ids, with_edit=True, alpha=1.0):
    """Project each edited layer's down_proj input onto the edit's key rows.

    Returns {layer: float32 CPU tensor (seq, r)} with z[i] = A @ x_i for batch row 0.  With
    ``with_edit`` the edit is applied at every position during the pass (the edited model); for a
    single-layer edit this does not change x at the edited layer.
    """
    store, handles = {}, []

    def make(layer, A):
        def pre(module, inputs):
            x = inputs[0][0]
            store[layer] = (x.float() @ A.to(x.device, torch.float32).T).cpu()
        return pre

    try:
        for layer, (A, _) in edit.items():
            mod = model.get_submodule(module_tmp.format(layer))
            handles.append(mod.register_forward_pre_hook(make(layer, A)))
        if with_edit:
            with EditBank(model, module_tmp) as bank:
                bank.set_batch([edit], alphas=[alpha])
                _forward(model, ids)
        else:
            _forward(model, ids)
    finally:
        for h in handles:
            h.remove()
    return store


def segment_masks(seg, n, names=MASKS):
    """Position masks {name: float tensor (n,)} built from the q/c/p token segments."""
    out = {}
    for name in names:
        if name not in MASK_SEGS:
            raise ValueError(f"unknown mask {name!r}; choose from {sorted(MASK_SEGS)}")
        m = torch.zeros(n)
        for s in MASK_SEGS[name]:
            a, b = seg[s]
            m[a:b] = 1.0
        out[name] = m
    return out


@torch.no_grad()
def masked_logprobs(model, ids, edit, module_tmp, masks, token_ids, alpha=1.0, batch=None):
    """Final-position log-probs of ``token_ids`` with the edit gated by each position mask.

    ``ids`` is (1, seq); ``masks`` maps name -> (seq,) tensor.  Masks run as batch rows of one
    EditBank pass (``batch`` rows at a time).  Returns {name: [log-prob per token id]}.
    """
    names, out = list(masks), {}
    step = batch or len(names)
    with EditBank(model, module_tmp) as bank:
        for i in range(0, len(names), step):
            chunk = names[i:i + step]
            pm = torch.stack([masks[n] for n in chunk]).float()
            bank.set_batch([edit] * len(chunk), alphas=[alpha] * len(chunk), pos_mask=pm)
            logits = _forward(model, ids.repeat(len(chunk), 1)).logits[:, -1].float()
            lp = torch.log_softmax(logits, dim=-1)
            for j, name in enumerate(chunk):
                out[name] = [float(lp[j, t]) for t in token_ids]
    return out


def _enc_a(arr):
    return base64.b64encode(np.ascontiguousarray(arr, dtype="<f2").tobytes()).decode("ascii")


def decode_a(row):
    """Per-position activations of a trace row: {layer: float32 ndarray (n_tokens, rank)}."""
    out = {}
    for layer, b in row["a_b64"].items():
        shape = row["a_shape"][str(layer)]
        out[int(layer)] = np.frombuffer(base64.b64decode(b), dtype="<f2").reshape(shape).astype(
            np.float32)
    return out


def _mention_a(a, layers, tok_i):
    by_layer = [float(a[L][tok_i, 0]) for L in layers]
    return float(np.mean(by_layer)), by_layer


def trace(model, tok, edit, module_tmp, q, subject, cot, answer="", o_new=None, o_old=None,
          aliases=None, with_edit=True, alpha=1.0, low=LOW_A, bos=None):
    """Edit-activation trace over one teacher-forced chain (probe a).

    Returns a JSON-ready dict: per-position activations (float16, base64, per layer), the
    reference token, subject mentions in chain and answer with the activation at each mention's
    last token (``a`` = mean over edited layers of rank component 0; ``a_by_layer`` per layer),
    first old/new value mentions per segment, and a summary over chain mentions.
    """
    seq = compose(tok, q, cot, answer, bos=bos)
    offs, chars = seq["offsets"], seq["chars"]
    ids = torch.tensor([seq["ids"]], device=_in_device(model))
    s0, s1 = find_subject(q, subject)
    ref = char_span_tokens(offs, chars["q"][0] + s0, chars["q"][0] + s1)[1]
    z = capture_z(model, module_tmp, edit, ids, with_edit=with_edit, alpha=alpha)
    layers = sorted(z)
    a, ref_z = {}, {}
    for L in layers:
        zr = z[L][ref]
        ref_z[L] = [float(v) for v in zr]
        a[L] = (z[L] / torch.where(zr == 0, torch.full_like(zr, float("nan")), zr)).numpy()

    segs = [("chain", chars["cot"])] + ([("answer", chars["tail"])] if answer else [])
    mentions, values = [], {}
    for name, (cs, ce) in segs:
        for m in subject_mentions(seq["text"], subject, cs, ce):
            m["seg"] = name
            m["tok"] = char_span_tokens(offs, *m["span"])[1]
            m["a"], m["a_by_layer"] = _mention_a(a, layers, m["tok"])
            mentions.append(m)
        scrubbed = scrub_subject(seq["text"][cs:ce], subject)
        values[name] = {}
        for key, val in (("old", o_old), ("new", o_new)):
            span = first_value_span(scrubbed, val, aliases) if val else None
            if span is None:
                values[name][key] = None
                continue
            s, e = cs + span[0], cs + span[1]
            values[name][key] = {"span": [s, e], "text": seq["text"][s:e],
                                 "tok": list(char_span_tokens(offs, s, e))}

    chain_m = [m for m in mentions if m["seg"] == "chain"]
    old = values["chain"]["old"]
    before = [m for m in chain_m if old and m["span"][1] <= old["span"][0]]
    avals = [m["a"] for m in chain_m]
    ans_a = [m["a"] for m in mentions if m["seg"] == "answer"]
    summary = {
        "n_full": sum(m["kind"] == "full" for m in chain_m),
        "n_partial": sum(m["kind"] == "partial" for m in chain_m),
        "max_a": max(avals) if avals else None,
        "frac_high": (sum(v >= low for v in avals) / len(avals)) if avals else None,
        "thr": low,
        "chain_old": old is not None,
        "chain_new": values["chain"]["new"] is not None,
        "n_before_old": len(before),
        "a_last_before_old": before[-1]["a"] if before else None,
        "any_low_before_old": any(m["a"] < low for m in before) if before else None,
        "answer_max_a": max(ans_a) if ans_a else None,
    }
    return {
        "n_tokens": len(seq["ids"]), "seg": {k: list(v) for k, v in seq["seg"].items()},
        "bos": seq["bos"], "text_sha": hashlib.sha256(seq["text"].encode()).hexdigest(),
        "layers": layers, "ref_tok": ref, "ref_text": seq["text"][offs[ref][0]:offs[ref][1]],
        "ref_z": {str(L): ref_z[L] for L in layers},
        "a_b64": {str(L): _enc_a(a[L]) for L in layers},
        "a_shape": {str(L): list(a[L].shape) for L in layers},
        "mentions": mentions, "values": values, "summary": summary,
    }


def gate(model, tok, edit, module_tmp, q, cot, answer_prefix, new_id, old_id, masks=MASKS,
         alpha=1.0, batch=None, bos=None):
    """Positional gating on one sequence (probe b): margins per mask at the final position."""
    seq = compose(tok, q, cot, answer_prefix, bos=bos)
    ids = torch.tensor([seq["ids"]], device=_in_device(model))
    lp = masked_logprobs(model, ids, edit, module_tmp,
                         segment_masks(seq["seg"], len(seq["ids"]), masks),
                         [new_id, old_id], alpha=alpha, batch=batch)
    return {"n_tokens": len(seq["ids"]), "seg": {k: list(v) for k, v in seq["seg"].items()},
            "masks": {k: {"lp_new": v[0], "lp_old": v[1], "margin": v[0] - v[1]}
                      for k, v in lp.items()}}


def gate_case(model, tok, edit, module_tmp, q, cot, case, masks=MASKS, alpha=1.0, batch=None,
              bos=None):
    """Gating after the given chain and at the B0 reference (ZEROTHINK + answer prefix).

    The answer prefix is the CounterFact prompt, so the next token is the value.  When the first
    tokens of " "+o_new and " "+o_old coincide the margin is identically 0 (``same_first_token``).
    """
    new_id, old_id = value_token(tok, case["o_new"]), value_token(tok, case["o_old"])
    kw = dict(masks=masks, alpha=alpha, batch=batch, bos=bos)
    return {"new_id": new_id, "old_id": old_id, "same_first_token": new_id == old_id,
            "answer_prefix": case["prompt"],
            "chain": gate(model, tok, edit, module_tmp, q, cot, case["prompt"], new_id, old_id, **kw),
            "b0": gate(model, tok, edit, module_tmp, q, "", case["prompt"], new_id, old_id, **kw)}


# ---------------------------------------------------------------- labels from Study-1 rows

def case_labels(case, by_budget, budget, aliases):
    """Outcome labels of one case under metrics' rules (subject scrubbed, alias-aware).

    group: reverted (B0 success, answer at ``budget`` has o_old and not o_new), held (B0 success,
    ES = 1 at ``budget``), other (B0 success, neither), b0_fail, b0_missing.
    """
    s, new, old = case.get("s") or "", case["o_new"], case["o_old"]
    clean = lambda t: metrics._without_subject(t, s)
    hit = lambda t, v: bool(metrics.hit(clean(t), v, aliases))
    b0, row = by_budget.get("B0"), by_budget[budget]
    b0_ok = (hit(b0["answer"], new) and not hit(b0["answer"], old)) if b0 else None
    has_new, has_old = hit(row["answer"], new), hit(row["answer"], old)
    es = has_new and not has_old
    if b0_ok is None:
        group = "b0_missing"
    elif not b0_ok:
        group = "b0_fail"
    else:
        group = "reverted" if (has_old and not has_new) else ("held" if es else "other")
    return {"b0_ok": b0_ok, "es": es, "clr": hit(row["cot"], old),
            "rr_loose": has_old if b0_ok else None,
            "rr_strict": (has_old and not has_new) if b0_ok else None,
            "group": group, "name_leak": bool(metrics.hit(s, old, aliases))}


# ---------------------------------------------------------------- runner

DEFAULTS = {
    "model": None, "model_tag": None, "editor": "ROME", "target_tag": None,
    "dtype": "bfloat16", "device_map": "auto", "deltas": None, "rows": None,
    "cases": ["data/counterfact.jsonl"], "aliases": "data/aliases.json", "routes": None,
    "route_cells": [], "budgets": ["B3"], "probe": "efficacy", "decode": "greedy",
    "probes": ["trace", "gate"], "masks": list(MASKS), "with_answer": True, "trace_edit": True,
    "alpha": 1.0, "low": LOW_A, "gate_batch": None, "out": None, "retry_errors": False,
    "bos": None, "expect_target": "o_new",
}
_SIG_KEYS = ("model", "model_tag", "editor", "target_tag", "dtype", "deltas", "probe", "decode",
             "masks", "with_answer", "trace_edit", "alpha", "low")


def load_config(path):
    import yaml
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_model(path, dtype="bfloat16", device_map="auto"):
    """Model and tokenizer for teacher-forced probes: bf16 by default, device_map auto.

    The R1-Llama tokenizer fix (``r1_tokenizer``) is applied when tokenizer.json is reachable;
    it is a no-op for Qwen.  No EasyEdit code is involved: edits come from delta files.
    """
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(path)
    try:
        from transformers.utils import cached_file
        from r1_tokenizer import fix_r1_tokenizer
        tok = fix_r1_tokenizer(tok, os.path.dirname(cached_file(path, "tokenizer.json")))
    except Exception as exc:                      # noqa: BLE001 - provenance records the tokenizer
        print(f"[mech] tokenizer fix skipped: {exc!r}")
    model = AutoModelForCausalLM.from_pretrained(path, dtype=getattr(torch, dtype),
                                                 device_map=device_map)
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    return model, tok


def _as_list(x):
    return [] if x is None else ([x] if isinstance(x, str) else list(x))


def _cid_key(cid):
    tail = str(cid).rsplit("_", 1)[-1]
    return (0, int(tail), str(cid)) if tail.isdigit() else (1, 0, str(cid))


def _load_cases(paths):
    cases = {}
    for p in _as_list(paths):
        if not os.path.exists(p):
            continue
        with open(p) as f:
            for line in f:
                c = json.loads(line)
                cases.setdefault(c["case_id"], c)
    if not cases:
        raise FileNotFoundError(f"no case file found among {_as_list(paths)}")
    return cases


def _load_rows(patterns, probe, decode):
    """{case_id: {budget: row}} for one probe and decode arm; first occurrence wins."""
    files = sorted({f for p in _as_list(patterns) for f in glob.glob(p)})
    if not files:
        raise FileNotFoundError(f"no row files match {_as_list(patterns)}")
    out = {}
    for fn in files:
        with open(fn) as f:
            for line in f:
                r = json.loads(line)
                if r.get("probe") != probe or r.get("decode", "greedy") != decode:
                    continue
                out.setdefault(r["case_id"], {}).setdefault(r["budget"], r)
    return out, files


def _load_routes(path, cells):
    if not path or not os.path.exists(path):
        return {}
    with open(path) as f:
        items = json.load(f).get("items", [])
    cells = set(_as_list(cells))
    return {it["case_id"]: it.get("primary") for it in items if not cells or it.get("cell") in cells}


def _sha_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _git():
    def g(*a):
        return subprocess.check_output(["git", "-C", _ROOT, *a], stderr=subprocess.DEVNULL,
                                       text=True).strip()
    try:
        return {"git": g("rev-parse", "HEAD"), "git_dirty": bool(g("status", "--porcelain"))}
    except Exception:                             # noqa: BLE001
        return {"git": "unknown", "git_dirty": None}


def _runtime(model, tok, bos=None):
    import transformers
    p = next(model.parameters())
    dm = getattr(model, "hf_device_map", None)
    counts = {}
    for dev in (dm or {}).values():
        counts[str(dev)] = counts.get(str(dev), 0) + 1
    return {"model_class": type(model).__name__, "tokenizer_class": type(tok).__name__,
            "loaded_model": getattr(model.config, "_name_or_path", None),
            "parameter_dtype": str(p.dtype), "parameter_device": str(p.device),
            "hf_device_map_counts": counts or None, "bos_token": tok.bos_token,
            "bos_prepended": bool(bos_text(tok, bos)), "torch": torch.__version__,
            "transformers": transformers.__version__, "python": sys.version.split()[0],
            "platform": platform.platform(), "cuda": torch.version.cuda}


def _header(cfg, sig, rank, world, row_files, model, tok):
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.dirname(here)
    code = {n: _sha_file(os.path.join(d, n)) for d, n in (
        (here, "mech.py"), (here, "edit_hooks.py"), (src, "metrics.py"), (src, "think_budget.py"))}
    return {"_meta": True, "kind": "mech", **_git(), "code_sha": code, "config": cfg,
            "signature": sig, "rank": rank, "world": world, "row_files": row_files,
            "runtime": _runtime(model, tok, cfg.get("bos")),
            "env": {k: os.environ.get(k) for k in ("WHYAAAI_NO_BOS", "CUDA_VISIBLE_DEVICES",
                                                   "PYTORCH_CUDA_ALLOC_CONF")},
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def _read_out(path):
    header, rows = None, []
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    if r.get("_meta"):
                        header = header or r
                    else:
                        rows.append(r)
    return header, rows


def _signature(cfg, tok):
    sig = {k: cfg.get(k) for k in _SIG_KEYS}
    sig["bos"] = bool(bos_text(tok, cfg.get("bos"))) if tok is not None else None
    return sig


def run(cfg, model=None, tok=None, rank=0, world=1, limit=None, log=print):
    """Run the configured probes over Study-1 rows; append one jsonl row per (case, budget, kind).

    Resumable: rows already in the output (including error rows unless ``retry_errors``) are
    skipped, and an output whose header signature differs from this config is refused.  Cases
    whose delta file is missing are skipped without a row.  Returns counts.
    """
    cfg = {**DEFAULTS, **cfg}
    for k in ("deltas", "rows", "out"):
        if not cfg.get(k):
            raise ValueError(f"config needs {k!r}")
    out = cfg["out"].format(rank=rank, world=world)
    cases = _load_cases(cfg["cases"])
    aliases = {}
    if cfg.get("aliases") and os.path.exists(cfg["aliases"]):
        with open(cfg["aliases"]) as f:
            aliases = json.load(f)
    rows, row_files = _load_rows(cfg["rows"], cfg["probe"], cfg["decode"])
    routes = _load_routes(cfg.get("routes"), cfg.get("route_cells"))
    items = sorted(((cid, b) for cid, bud in rows.items() for b in cfg["budgets"] if b in bud),
                   key=lambda it: (_cid_key(it[0]), it[1]))
    items = [it for i, it in enumerate(items) if i % world == rank]
    if limit:
        items = items[:limit]

    header, prev = _read_out(out)
    done = {(r["case_id"], r["budget"], r["kind"]) for r in prev
            if not (cfg["retry_errors"] and "error" in r)}
    todo = [(cid, b) for cid, b in items
            if any((cid, b, k) not in done for k in cfg["probes"])]
    counts = {"items": len(items), "written": 0, "errors": 0, "skipped_done": len(items) - len(todo),
              "missing_delta": 0, "missing_case": 0}
    if not todo:
        return counts
    if model is None:
        model, tok = load_model(cfg["model"], cfg["dtype"], cfg["device_map"])
    sig = _signature(cfg, tok)
    if header is not None and header.get("signature") != sig:
        raise ValueError(f"{out} was written with signature {header.get('signature')}, "
                         f"this run has {sig}; use a new output path")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "a") as f:
        def emit(rec):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
        if header is None:
            emit(_header(cfg, sig, rank, world, row_files, model, tok))
        for cid, b in todo:
            case = cases.get(cid)
            if case is None:
                counts["missing_case"] += 1
                log(f"[mech] {cid}: not in case files, skipped")
                continue
            dpath = os.path.join(cfg["deltas"], f"{cid}.pt")
            if not os.path.exists(dpath):
                counts["missing_delta"] += 1
                log(f"[mech] {cid}: no delta at {dpath}, skipped")
                continue
            row = rows[cid][b]
            base = {"case_id": cid, "budget": b, "model_tag": cfg["model_tag"],
                    "editor": cfg["editor"], "target_tag": cfg["target_tag"]}
            try:
                edit, rec = load_delta(dpath)
                if rec["case_id"] != cid or (cfg["model_tag"] and rec["model_tag"] != cfg["model_tag"]):
                    raise ValueError(f"delta {dpath} is for {rec['case_id']}/{rec['model_tag']}")
                want = case.get(cfg["expect_target"]) if cfg["expect_target"] else None
                if want is not None and rec.get("target") != want:
                    raise ValueError(f"delta {dpath} targets {rec.get('target')!r}, case "
                                     f"{cfg['expect_target']} is {want!r}")
                labels = case_labels(case, rows[cid], b, aliases)
            except Exception as exc:              # noqa: BLE001 - recorded, run continues
                for kind in cfg["probes"]:
                    if (cid, b, kind) not in done:
                        emit({**base, "kind": kind, "error": repr(exc)[:500]})
                        counts["errors"] += 1
                continue
            base.update(delta_sha=rec.get("sha"), q=row["q"], labels=labels,
                        route=routes.get(cid), n_chain_chars=len(row["cot"]))
            for kind in cfg["probes"]:
                if (cid, b, kind) in done:
                    continue
                try:
                    if kind == "trace":
                        res = trace(model, tok, edit, rec["module_tmp"], row["q"], case["s"],
                                    row["cot"], row["answer"] if cfg["with_answer"] else "",
                                    case["o_new"], case["o_old"], aliases,
                                    with_edit=cfg["trace_edit"], alpha=cfg["alpha"], low=cfg["low"],
                                    bos=cfg["bos"])
                    elif kind == "gate":
                        res = gate_case(model, tok, edit, rec["module_tmp"], row["q"], row["cot"],
                                        case, masks=cfg["masks"], alpha=cfg["alpha"],
                                        batch=cfg["gate_batch"], bos=cfg["bos"])
                    else:
                        raise ValueError(f"unknown probe kind {kind!r}")
                    emit({**base, "kind": kind, **res})
                    counts["written"] += 1
                except Exception as exc:          # noqa: BLE001
                    emit({**base, "kind": kind, "error": repr(exc)[:500]})
                    counts["errors"] += 1
                    log(f"[mech] {cid} {b} {kind}: {exc!r}")
    return counts


# ---------------------------------------------------------------- pre-declared readouts

def _boot(xs, ys=None, n_boot=2000, seed=0):
    """Mean of xs (or mean(xs) - mean(ys)) with a 95% percentile bootstrap over cases."""
    xs = [x for x in xs if x is not None]
    ys = None if ys is None else [y for y in ys if y is not None]
    if not xs or (ys is not None and not ys):
        return None
    mean = lambda v: sum(v) / len(v)
    stat = lambda a, b: mean(a) - (mean(b) if b is not None else 0.0)
    rng = random.Random(seed)
    sims = sorted(stat([rng.choice(xs) for _ in xs],
                       None if ys is None else [rng.choice(ys) for _ in ys])
                  for _ in range(n_boot))
    return {"est": stat(xs, ys), "lo": sims[int(0.025 * n_boot)],
            "hi": sims[min(int(0.975 * n_boot), n_boot - 1)],
            "n": len(xs) if ys is None else [len(xs), len(ys)]}


def summarize(paths, exclude_name_leak=True, n_boot=2000, seed=0):
    """Readouts (i) and (ii) of experiments/rt/README_mech.md from mech output files."""
    rows = []
    for p in sorted({f for pat in _as_list(paths) for f in glob.glob(pat)}):
        rows += [r for r in _read_out(p)[1] if "error" not in r]
    if exclude_name_leak:
        rows = [r for r in rows if not r["labels"]["name_leak"]]
    groups = ("reverted", "held")
    tr = {g: [r for r in rows if r["kind"] == "trace" and r["labels"]["group"] == g] for g in groups}
    gt = {g: [r for r in rows if r["kind"] == "gate" and r["labels"]["group"] == g
              and not r["same_first_token"]] for g in groups}
    kw = dict(n_boot=n_boot, seed=seed)

    def low_first(rs):   # chains whose first old mention follows >= 1 subject mention
        return [float(r["summary"]["a_last_before_old"] < r["summary"]["thr"]) for r in rs
                if r["summary"]["chain_old"] and r["summary"]["n_before_old"]]
    readout_i = {
        "low_last_mention_before_old": {g: _boot(low_first(tr[g]), **kw) for g in groups},
        "diff_reverted_minus_held": _boot(low_first(tr["reverted"]), low_first(tr["held"]), **kw),
        "old_without_prior_mention": {g: _boot([float(r["summary"]["n_before_old"] == 0)
                                                for r in tr[g] if r["summary"]["chain_old"]], **kw)
                                      for g in groups},
        "frac_high": {g: _boot([r["summary"]["frac_high"] for r in tr[g]], **kw) for g in groups},
        "max_a": {g: _boot([r["summary"]["max_a"] for r in tr[g]], **kw) for g in groups},
    }

    def eff(r, ctx, mask):
        m = r[ctx]["masks"]
        return m[mask]["margin"] - m["none"]["margin"] if mask in m else None

    def lost(r, mask):   # edit effect at B0 minus edit effect after the chain
        e0, ec = eff(r, "b0", mask), eff(r, "chain", mask)
        return None if e0 is None or ec is None else e0 - ec
    readout_ii = {}
    for g in groups:
        rs = gt[g]
        masks = sorted({k for r in rs for k in r["chain"]["masks"]} - {"none"})
        readout_ii[g] = {
            "n": len(rs),
            "margin_chain": {k: _boot([r["chain"]["masks"][k]["margin"] for r in rs
                                       if k in r["chain"]["masks"]], **kw)
                             for k in ["none"] + masks},
            "effect_chain": {k: _boot([eff(r, "chain", k) for r in rs], **kw) for k in masks},
            "effect_b0_all": _boot([eff(r, "b0", "all") for r in rs], **kw),
            "all_minus_question_only": _boot(
                [r["chain"]["masks"]["all"]["margin"] - r["chain"]["masks"]["question_only"]["margin"]
                 for r in rs if {"all", "question_only"} <= set(r["chain"]["masks"])], **kw),
            "b0_all_minus_chain_all": _boot([lost(r, "all") for r in rs], **kw),
            "b0_q_minus_chain_q": _boot([lost(r, "question_only") for r in rs], **kw),
        }
    return {"n_rows": len(rows), "exclude_name_leak": exclude_name_leak,
            "readout_i": readout_i, "readout_ii": readout_ii}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run trace/gate probes from a YAML config")
    r.add_argument("--config", required=True)
    r.add_argument("--rank", type=int, default=0)
    r.add_argument("--world", type=int, default=1)
    r.add_argument("--limit", type=int, default=None)
    for k in ("model", "rows", "deltas", "out", "dtype"):
        r.add_argument(f"--{k}", default=None, help=f"override config {k}")
    s = sub.add_parser("summarize", help="print readouts (i) and (ii) as JSON")
    s.add_argument("paths", nargs="+")
    s.add_argument("--keep-name-leak", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "run":
        cfg = load_config(a.config)
        cfg.update({k: getattr(a, k) for k in ("model", "rows", "deltas", "out", "dtype")
                    if getattr(a, k) is not None})
        print(json.dumps(run(cfg, rank=a.rank, world=a.world, limit=a.limit)))
    else:
        print(json.dumps(summarize(a.paths, exclude_name_leak=not a.keep_name_leak), indent=1))


if __name__ == "__main__":
    main()
