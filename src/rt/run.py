"""YAML-driven driver: conditions x cases x budgets x probes x decodes -> jsonl rows (engine v2).

    cd <project root>
    CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src python -m rt.run --config experiments/rt/<x>.yaml --rank 0 --world 8
    PYTHONPATH=src python -m rt.run --config ... --dry-run      # plan + resume check, no model load

Output: one shard per condition, ``<out_dir>/<model_tag>_<run_tag>_<condition>_r<rank>of<world>.jsonl``,
so ``metrics.score`` can read a condition file directly (it does not filter by condition).  The first
line of every shard is a ``_meta`` header; every other line is a row (schema in REVISION.md §4) or an
error row (``error`` field, no ``probe``; metrics skips it).

Config (paths relative to the project root)::

    model_tag: r1qwen32b
    template: r1                  # r1 | qwq | instruct_cot (rt.engine)
    template_system: null         # optional system turn for the ChatML families
    model: {path: null, dtype: bfloat16, device_map: null, attn_implementation: null}
                                  # path null -> $WHYAAAI_MODEL; device_map null -> --device or cuda/cpu
    module_tmp: "model.layers.{}.mlp.down_proj"
    out_dir: results/rt/<run>
    run_tag: <run>
    dataset: {path: data/counterfact.jsonl, manifest: <ordered case ids, .sha256 sidecar checked>,
              case_ids: [...], n: null}
    aliases: data/aliases.json
    probes: [efficacy, para0, locality]          # efficacy=prompt, para0/1=paraphrases[0/1],
                                                 # locality=neighborhood[0] (as edit_loop.probes)
    decoding: {greedy: true, sampling: null}     # sampling: {temperature: 0.6, seeds: [0, 1, 2, 3]}
    arms: {penalty: 8, bias_probes: [efficacy], placebo_map: data/placebo_donors.json,
           competitor_map: data/placebo_donors_strong.json}
    engine: {batch_size: 16, max_batch_tokens: null, answer_cap: 256, chunk_cases: 32, caps: {}}
    conditions:
      - name: rome_N              # [A-Za-z0-9_.-]+
        editor: ROME              # ROME | MEMIT | AlphaEdit (need deltas_dir) | none | IKE
        target_tag: cf
        deltas_dir: deltas/r1qwen32b/ROME/cf     # <case_id>.pt from rt.deltas; missing -> error row
        budgets: [B0, B3]         # B0 B0P B1 B2 B3 GIVEN
        alpha: 1.0
        arm: N                    # N none | T o_old+aliases | D o_new+aliases | P placebo | C competitor
        probes / decoding / penalty / bias_probes: per-condition overrides
        user_prefix_template: "Fact: {prompt} {o_new}.\\n"      # IKE; formatted with the case fields
        given_chain: {source: <jsonl glob>, condition: rome_N, budget: B3, probe: same, decode: greedy,
                      transform: own|filler|swap, seed: 2027, filler_unit: " .", require_complete: true}
        stage: 1                  # --stage N runs only the conditions of that stage

Arms bias the chain only (``Engine`` applies ``chain_bias`` in the chain phase), with
``-penalty`` on the first-token ids from ``suppress.build_old_token_ids``, and only on the probes in
``bias_probes``.  GIVEN transforms: ``own`` = the case's own chain; ``filler`` = ``filler_unit``
repeated (default " .", dot-by-dot filler: no lexical content, one token per unit in the Qwen and
Llama BPEs) until it has as many tokens as the case's own chain; ``swap`` = the chain of another case
(``swap_map``: seed-fixed derangement pairing cases adjacent in token length).

Resume: rows whose key (case_id, condition, budget, probe, decode, seed) is already in the shard are
skipped; error rows are not keys, so a case whose delta was missing is retried.  Appending is refused
when the shard header differs in ``config_sha256`` (hash of this condition's resolved semantic spec:
model tag, dtype, template, BOS switch, dataset ids, aliases, caps, the condition itself, donor maps,
given-chain source), ``code_sha256`` (src/rt/*.py, think_budget, suppress, metrics, r1_tokenizer),
rank or world.  Batch size, token budget, chunking and the model path are recorded but not hashed:
they do not change what a row means.
"""
import argparse
import glob
import hashlib
import importlib.metadata
import json
import os
import platform
import random
import re
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone

import torch

from rt.engine import BUDGETS, CHAIN_BUDGETS, Engine, Request, get_template

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROW_FORMAT = "rt-rows-v1"
DELTA_EDITORS = ("ROME", "MEMIT", "AlphaEdit")
EDITORS = DELTA_EDITORS + ("none", "IKE")
ARMS = ("N", "T", "D", "P", "C")
PROBES = ("efficacy", "para0", "para1", "locality")
ENV_KEYS = ("WHYAAAI_MODEL", "WHYAAAI_NO_BOS", "WHYAAAI_DTYPE", "CUDA_VISIBLE_DEVICES",
            "PYTORCH_CUDA_ALLOC_CONF", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")
RESUME_KEYS = ("config_sha256", "code_sha256", "condition", "rank", "world", "model_tag", "template")


def _abs(p):
    return p if os.path.isabs(p) else os.path.join(_ROOT, p)


def _rel(p):
    a = os.path.abspath(p)
    return os.path.relpath(a, _ROOT) if a.startswith(_ROOT + os.sep) else a


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def code_files():
    rels = sorted(_rel(p) for p in glob.glob(_abs("src/rt/*.py")))
    return rels + ["src/think_budget.py", "src/suppress.py", "src/metrics.py", "src/r1_tokenizer.py"]


def code_sha256():
    return {rel: sha256_file(_abs(rel)) for rel in code_files() if os.path.exists(_abs(rel))}


def git_provenance():
    def g(*a):
        return subprocess.check_output(["git", "-C", _ROOT, *a], stderr=subprocess.DEVNULL, text=True).strip()
    try:
        return {"git": g("rev-parse", "HEAD"), "git_dirty": bool(g("status", "--porcelain", "--untracked-files=no"))}
    except Exception:
        return {"git": "unknown", "git_dirty": None}


def software():
    pk = {}
    for name in ("transformers", "tokenizers", "accelerate", "numpy"):
        try:
            pk[name] = importlib.metadata.version(name)
        except Exception:
            pk[name] = None
    return {"python": sys.version.split()[0], "platform": platform.platform(),
            "torch": torch.__version__, "torch_cuda": torch.version.cuda, "packages": pk}


def read_ids(path):
    """Ordered case ids from a manifest (jsonl rows with ``case_id`` or one id per line).
    A ``<path>.sha256`` sidecar, when present, must match the file."""
    side = path + ".sha256"
    if os.path.exists(side):
        want = open(side).read().split()[0]
        if sha256_file(path) != want:
            raise ValueError(f"{path}: sha256 differs from {side}")
    ids = []
    for line in open(path):
        line = line.strip()
        if line:
            ids.append(json.loads(line)["case_id"] if line.startswith("{") else line)
    return ids


def load_cases(ds):
    src = _abs(ds.get("path", "data/counterfact.jsonl"))
    rows = [json.loads(l) for l in open(src) if l.strip()]
    wanted = ds.get("case_ids") or (read_ids(_abs(ds["manifest"])) if ds.get("manifest") else None)
    if wanted is None:
        cases = rows
    else:
        if len(wanted) != len(set(wanted)):
            raise ValueError("dataset case ids contain duplicates")
        by = {r["case_id"]: r for r in rows}
        missing = [c for c in wanted if c not in by]
        if missing:
            raise ValueError(f"{len(missing)} case ids missing from {src}: {missing[:5]}")
        cases = [by[c] for c in wanted]
    n = ds.get("n")
    return cases[:n] if n else cases, src


def probe_text(case, name):
    """Probe prompt as in ``edit_loop.probes``; None when the case lacks it."""
    if name == "efficacy":
        return case["prompt"]
    if name in ("para0", "para1"):
        ps = case.get("paraphrases") or []
        i = int(name[-1])
        return ps[i] if len(ps) > i else None
    if name == "locality":
        nb = case.get("neighborhood") or []
        return nb[0] if nb else None
    raise ValueError(f"unknown probe {name!r}")


def decode_arms(dcfg):
    dcfg = dcfg or {"greedy": True}
    arms = [("greedy", None, None)] if dcfg.get("greedy", True) else []
    samp = dcfg.get("sampling")
    if samp:
        t = float(samp.get("temperature", 0.6))
        arms += [("sample", int(s), t) for s in samp["seeds"]]
    if not arms:
        raise ValueError("decoding selects no arm")
    return arms


def filler_text(tok, n_tokens, unit=" ."):
    """Content-free filler with ``n_tokens`` tokens (no BOS): ``unit`` repeated, topped up with '.'."""
    def ntok(s):
        return len(tok(s, add_special_tokens=False)["input_ids"])
    if n_tokens <= 0:
        return ""
    k = n_tokens // max(1, ntok(unit))
    while k > 0 and ntok(unit * k) > n_tokens:
        k -= 1
    text = unit * k
    while ntok(text + unit) <= n_tokens:
        text += unit
    while ntok(text) < n_tokens and ntok(text + ".") > ntok(text) and ntok(text + ".") <= n_tokens:
        text += "."
    return text


def swap_map(lengths, seed):
    """Derangement case -> donor case pairing neighbours in token length.

    Cases are shuffled with ``seed`` (tie order), stably sorted by length, and adjacent cases swap
    chains; with an odd count the three longest form a 3-cycle.  Nobody keeps its own chain.
    """
    ids = sorted(lengths)
    if len(ids) < 2:
        raise ValueError("swap needs at least two chains")
    random.Random(seed).shuffle(ids)
    order = sorted(ids, key=lambda c: lengths[c])
    m = {}
    for k in range(0, len(order) - 1, 2):
        a, b = order[k], order[k + 1]
        m[a], m[b] = b, a
    if len(order) % 2:
        a, b, c = order[-3:]
        m[a], m[b], m[c] = b, c, a
    return m


def load_chains(gc, case_ids, probes):
    """{(case_id, probe): cot} from the given-chain source rows (first row per key wins)."""
    src_probe = gc.get("probe", "same")
    want = set(probes) if src_probe == "same" else {src_probe}
    cond, budget, dec = gc.get("condition"), gc.get("budget", "B3"), gc.get("decode", "greedy")
    ids = set(case_ids)
    files = sorted(glob.glob(_abs(gc["source"])))
    if not files:
        raise FileNotFoundError(f"given_chain.source matches no file: {gc['source']}")
    out = {}
    for f in files:
        for line in open(f):
            r = json.loads(line)
            if (r.get("case_id") in ids and r.get("probe") in want and r.get("budget") == budget
                    and r.get("decode", "greedy") == dec and (cond is None or r.get("condition") == cond)
                    and (dec != "greedy" or r.get("seed") is None)):
                out.setdefault((r["case_id"], r["probe"]), r["cot"])
    return out, [_rel(f) for f in files]


def _model_path(cfg):
    return (cfg.get("model") or {}).get("path") or os.environ.get("WHYAAAI_MODEL")


def _resolve_condition(cfg, c, cases):
    name = c["name"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
        raise ValueError(f"condition name {name!r} must match [A-Za-z0-9_.-]+")
    editor = c.get("editor", "none")
    if editor not in EDITORS:
        raise ValueError(f"{name}: editor {editor!r} not in {EDITORS}")
    budgets = list(c.get("budgets", ["B0", "B3"]))
    bad = [b for b in budgets if b not in BUDGETS]
    if bad:
        raise ValueError(f"{name}: unknown budgets {bad}")
    probes = list(c.get("probes", cfg.get("probes", ["efficacy"])))
    if any(p not in PROBES for p in probes):
        raise ValueError(f"{name}: probes must be in {PROBES}")
    arm = c.get("arm", "N")
    if arm not in ARMS:
        raise ValueError(f"{name}: arm {arm!r} not in {ARMS}")
    arms_cfg = cfg.get("arms") or {}
    samp = (c.get("decoding", cfg.get("decoding")) or {}).get("sampling")
    r = {"name": name, "editor": editor, "target_tag": c.get("target_tag"), "budgets": budgets,
         "probes": probes, "decode": [list(a) for a in decode_arms(c.get("decoding", cfg.get("decoding")))],
         "arm": arm, "alpha": None, "deltas_dir": None, "user_prefix_template": c.get("user_prefix_template"),
         "stage": int(c.get("stage", 1))}
    if samp:                          # explicit, recorded (engine.neutral_generation_config)
        from rt.engine import DEFAULT_TOP_K, DEFAULT_TOP_P
        r["sample_params"] = {"top_p": float(samp.get("top_p", DEFAULT_TOP_P)),
                              "top_k": int(samp.get("top_k", DEFAULT_TOP_K))}
    if editor in DELTA_EDITORS:
        if not c.get("deltas_dir") or not c.get("target_tag"):
            raise ValueError(f"{name}: editor {editor} needs deltas_dir and target_tag")
        r["deltas_dir"] = c["deltas_dir"]
        r["alpha"] = float(c.get("alpha", 1.0))
    if editor == "IKE" and not r["user_prefix_template"]:
        raise ValueError(f"{name}: IKE needs user_prefix_template")
    if arm != "N":
        r["penalty"] = float(c.get("penalty", arms_cfg.get("penalty", 8)))
        r["bias_probes"] = list(c.get("bias_probes", arms_cfg.get("bias_probes", ["efficacy"])))
        if arm in ("P", "C"):
            key = "placebo_map" if arm == "P" else "competitor_map"
            path = c.get(key) or arms_cfg.get(key) or (
                "data/placebo_donors.json" if arm == "P" else "data/placebo_donors_strong.json")
            r["donor_map"] = {"path": path, "sha256": sha256_file(_abs(path))}
    gc = c.get("given_chain")
    if ("GIVEN" in budgets) != bool(gc):
        raise ValueError(f"{name}: budget GIVEN and given_chain go together")
    chains = None
    if gc:
        transform = gc.get("transform", "own")
        if transform not in ("own", "filler", "swap"):
            raise ValueError(f"{name}: given_chain.transform {transform!r}")
        chains, files = load_chains(gc, [x["case_id"] for x in cases], probes)
        src_probe = gc.get("probe", "same")
        need = [(x["case_id"], p if src_probe == "same" else src_probe) for x in cases for p in probes
                if probe_text(x, p) is not None]
        missing = sorted({k for k in need if k not in chains})
        if missing and gc.get("require_complete", True):
            raise ValueError(f"{name}: {len(missing)} given chains missing from {gc['source']} "
                             f"(e.g. {missing[:3]}); finish the source run or set require_complete: false")
        r["given_chain"] = {"source": gc["source"], "files": files, "condition": gc.get("condition"),
                            "budget": gc.get("budget", "B3"), "probe": src_probe,
                            "decode": gc.get("decode", "greedy"), "transform": transform,
                            "seed": int(gc.get("seed", 2027)), "filler_unit": gc.get("filler_unit", " ."),
                            "require_complete": bool(gc.get("require_complete", True)),
                            "chains_sha256": sha256_json(sorted([list(k), v] for k, v in chains.items()))}
    return r, chains


def _shared_spec(cfg, cases, src):
    """The part of every condition's semantic spec that the whole config shares."""
    mp = _model_path(cfg)
    mconf = os.path.join(mp, "config.json") if mp else None
    eng = cfg.get("engine") or {}
    return {"format": ROW_FORMAT, "model_tag": cfg["model_tag"], "template": cfg.get("template", "r1"),
            "template_system": cfg.get("template_system"),
            "dtype": (cfg.get("model") or {}).get("dtype", "bfloat16"),
            "module_tmp": cfg.get("module_tmp", "model.layers.{}.mlp.down_proj"),
            "no_bos": bool(os.environ.get("WHYAAAI_NO_BOS")),
            "model_config_sha256": sha256_file(mconf) if mconf and os.path.exists(mconf) else None,
            "dataset": {"source": _rel(src), "source_sha256": sha256_file(src), "n_cases": len(cases),
                        "case_ids_sha256": sha256_json([c["case_id"] for c in cases])},
            "aliases_sha256": sha256_file(_abs(cfg.get("aliases", "data/aliases.json"))),
            "caps": eng.get("caps") or {}, "answer_cap": int(eng.get("answer_cap", 256))}


def _read_shard(path):
    header, done = None, set()
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return None, done, False
    for line in open(path):
        r = json.loads(line)
        if r.get("_meta"):
            header = header or r
        elif r.get("probe"):
            done.add((r["case_id"], r["condition"], r["budget"], r["probe"], r["decode"], r.get("seed")))
    return header, done, True


def _check_resume(path, header, expected):
    if header is None:
        raise RuntimeError(f"refusing to append to headerless shard {path}")
    changed = [k for k in RESUME_KEYS if header.get(k) != expected.get(k)]
    if changed:
        raise RuntimeError(f"resume signature mismatch for {path}; changed={changed}. "
                           f"Use a new run_tag/out_dir or restore the exact config and code.")


def apply_bos_policy(cfg):
    """Let the config, not the shell, decide BOS (REVISION.md §5).

    ``no_bos: true`` sets WHYAAAI_NO_BOS for this process, ``false`` clears it; the prompt builders
    read that variable, and the resolved value enters every condition's resume hash.  Study 1 ran the
    Qwen-based R1 models without BOS and the Llama-based ones with it; Study 2 keeps that rule.
    """
    if "no_bos" not in cfg:
        return
    if cfg["no_bos"]:
        os.environ["WHYAAAI_NO_BOS"] = "1"
    else:
        os.environ.pop("WHYAAAI_NO_BOS", None)


def prepare(cfg, rank=0, world=1, config_path=None, only=None, stage=None, run_tag=None, limit=None):
    """Resolve config, cases, conditions and shard state without touching a model."""
    apply_bos_policy(cfg)
    if cfg.get("template", "r1") not in ("r1", "qwq", "instruct_cot"):
        raise ValueError(f"unknown template {cfg.get('template')!r}")
    cases, src = load_cases(cfg["dataset"])
    conds_cfg = cfg["conditions"]
    names = [c["name"] for c in conds_cfg]
    if len(names) != len(set(names)):
        raise ValueError("condition names must be unique")
    if only:
        unknown = set(only) - set(names)
        if unknown:
            raise ValueError(f"unknown conditions {sorted(unknown)}")
        conds_cfg = [c for c in conds_cfg if c["name"] in only]
    if stage is not None:
        conds_cfg = [c for c in conds_cfg if int(c.get("stage", 1)) == int(stage)]
    run_tag = run_tag or cfg.get("run_tag", "rt")
    code = code_sha256()
    shared = _shared_spec(cfg, cases, src)
    conds = []
    for c in conds_cfg:
        r, chains = _resolve_condition(cfg, c, cases)
        spec = dict(shared, condition=r)
        path = os.path.join(_abs(cfg["out_dir"]),
                            f"{cfg['model_tag']}_{run_tag}_{r['name']}_r{rank}of{world}.jsonl")
        expected = {"config_sha256": sha256_json(spec), "code_sha256": code, "condition": r["name"],
                    "rank": rank, "world": world, "model_tag": cfg["model_tag"],
                    "template": cfg.get("template", "r1")}
        header, done, exists = _read_shard(path)
        if exists:
            _check_resume(path, header, expected)
        conds.append({"cfg": r, "spec": spec, "expected": expected, "path": path, "done": done,
                      "exists": exists, "chains": chains})
    mine = [c for i, c in enumerate(cases) if i % world == rank]
    if limit is not None:
        mine = mine[:limit]
    return {"cfg": cfg, "cases": cases, "mine": mine, "conds": conds, "rank": rank, "world": world,
            "run_tag": run_tag, "config_path": config_path, "code": code}


def load_model(cfg, device=None):
    """AutoModelForCausalLM (bf16 default) + AutoTokenizer with the R1-Llama tokenizer fix."""
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from r1_tokenizer import fix_r1_tokenizer
    path = _model_path(cfg)
    if not path:
        raise ValueError("no model path: set model.path or WHYAAAI_MODEL")
    m = cfg.get("model") or {}
    kw = {"dtype": getattr(torch, m.get("dtype", "bfloat16")),
          "device_map": m.get("device_map") or device or ("cuda" if torch.cuda.is_available() else "cpu")}
    if m.get("attn_implementation"):
        kw["attn_implementation"] = m["attn_implementation"]
    model = AutoModelForCausalLM.from_pretrained(path, **kw).eval()
    tok = fix_r1_tokenizer(AutoTokenizer.from_pretrained(path), path)
    check_tokenizer_round_trip(tok)
    return model, tok


ROUND_TRIP_TEXT = "The mother tongue of Danielle Darrieux is French, and 2 + 2 = 4."


def check_tokenizer_round_trip(tok, text=ROUND_TRIP_TEXT):
    """Encode-decode must return the text unchanged: catches the R1-Llama Metaspace tokenizer that
    deletes spaces (review 2026-09-29, M4) and any other tokenizer that silently rewrites prompts."""
    ids = tok(text, add_special_tokens=False)["input_ids"]
    back = tok.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    if back != text:
        raise RuntimeError(f"tokenizer round trip changed the text: {text!r} -> {back!r}")


def _model_info(cfg, model, tok, template):
    p = next(model.parameters())
    dm = getattr(model, "hf_device_map", None)
    counts = {}
    for dev in (dm or {}).values():
        counts[str(dev)] = counts.get(str(dev), 0) + 1
    gc = getattr(model, "generation_config", None)
    return {"path": _model_path(cfg), "class": type(model).__name__, "param_dtype": str(p.dtype),
            "param_device": str(p.device), "device_map_counts": counts or None,
            "requested": cfg.get("model"), "tokenizer_class": type(tok).__name__, "vocab": len(tok),
            "bos_token_id": tok.bos_token_id, "eos_token_id": tok.eos_token_id,
            "pad_token_id": tok.pad_token_id,
            "generation_config_eos": getattr(gc, "eos_token_id", None), "template": template.describe(),
            "generation_config_original": getattr(model, "_rt_generation_config_original", None)
            or (gc.to_diff_dict() if gc is not None else None),
            "generation_config_used": "transformers defaults; decoding parameters passed per call"}


class _RowError(Exception):
    def __init__(self, kind, msg):
        super().__init__(msg)
        self.kind = kind


def _given_texts(cond, chains, cases, tok):
    """{(case_id, probe): (text, info)} for a GIVEN condition, over all cases (not only this shard)."""
    gc = cond["given_chain"]

    def ntok(s):
        return len(tok(s, add_special_tokens=False)["input_ids"])
    out = {}
    for p in cond["probes"]:
        sp = p if gc["probe"] == "same" else gc["probe"]
        have = {c["case_id"]: chains[(c["case_id"], sp)] for c in cases if (c["case_id"], sp) in chains}
        if gc["transform"] == "swap":
            lengths = {cid: ntok(v) for cid, v in have.items()}
            m = swap_map(lengths, gc["seed"])
        for cid, own in have.items():
            if gc["transform"] == "own":
                text, info = own, {"source_case": cid, "n_tokens": ntok(own)}
            elif gc["transform"] == "filler":
                n = ntok(own)
                text = filler_text(tok, n, gc["filler_unit"])
                info = {"source_case": None, "n_tokens_target": n, "n_tokens": ntok(text)}
            else:
                text = have[m[cid]]
                info = {"source_case": m[cid], "n_tokens_own": lengths[cid], "n_tokens": lengths[m[cid]]}
            out[(cid, p)] = (text, dict(info, transform=gc["transform"], source_probe=sp))
    return out


def _payload(cond, case, ctx):
    """Per (condition, case): edit, delta sha, user prefix, bias.  Raises _RowError."""
    from rt.edit_hooks import load_delta
    cid = case["case_id"]
    out = {"edit": None, "delta_sha": None, "user_prefix": "", "bias": None, "bias_info": None}
    if cond["editor"] in DELTA_EDITORS:
        path = os.path.join(_abs(cond["deltas_dir"]), f"{cid}.pt")
        if not os.path.exists(path):
            raise _RowError("missing_delta", f"no delta file {_rel(path)}")
        if path not in ctx["deltas"]:
            try:
                ctx["deltas"][path] = load_delta(path)
            except Exception as e:
                raise _RowError("bad_delta", repr(e))
        edit, rec = ctx["deltas"][path]
        want = {"case_id": cid, "model_tag": ctx["model_tag"], "editor": cond["editor"],
                "target_tag": cond["target_tag"], "module_tmp": ctx["module_tmp"]}
        diff = {k: (rec.get(k), v) for k, v in want.items() if rec.get(k) != v}
        if diff:
            raise _RowError("delta_mismatch", f"delta {_rel(path)} fields differ: {diff}")
        out["edit"], out["delta_sha"] = edit, rec["sha"]
    if cond["user_prefix_template"]:
        out["user_prefix"] = cond["user_prefix_template"].format(**case)
    if cond["arm"] != "N":
        from suppress import build_old_token_ids
        arm = cond["arm"]
        if arm in ("T", "D"):
            target, al = (case["o_old"] if arm == "T" else case["o_new"]), ctx["aliases"]
        else:
            target, al = ctx["donors"][cond["name"]].get(cid), {}
            if not target:
                raise _RowError("missing_donor", f"{cid} not in {cond['donor_map']['path']}")
        ids = sorted(int(t) for t in build_old_token_ids(ctx["tok"], target, al))
        out["bias"] = {t: -cond["penalty"] for t in ids}
        out["bias_info"] = {"target": str(target), "token_ids": ids, "penalty": cond["penalty"]}
    return out


def _header(plan, c, model_info, eng_cfg):
    return {"_meta": True, "format": ROW_FORMAT, **git_provenance(),
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            **c["expected"], "run_tag": plan["run_tag"],
            "config_file": _rel(plan["config_path"]) if plan["config_path"] else None,
            "config_file_sha256": sha256_file(plan["config_path"]) if plan["config_path"] else None,
            "spec": c["spec"], "code_files": code_files(),
            "env": {k: os.environ.get(k) for k in ENV_KEYS}, "software": software(),
            "model": model_info, "engine": eng_cfg}


def execute(plan, model, tok, log=print):
    """Generate every pending row of this shard; returns {condition: rows written}."""
    cfg = plan["cfg"]
    eng_cfg = dict(cfg.get("engine") or {})
    template = get_template(cfg.get("template", "r1"), tok, model, cfg.get("template_system"))
    module_tmp = cfg.get("module_tmp", "model.layers.{}.mlp.down_proj")
    bank = None
    if any(c["cfg"]["deltas_dir"] for c in plan["conds"]):
        from rt.edit_hooks import EditBank
        bank = EditBank(model, module_tmp)
    engine = Engine(model, tok, bank=bank, template=template, batch_size=eng_cfg.get("batch_size", 16),
                    max_batch_tokens=eng_cfg.get("max_batch_tokens"),
                    answer_cap=eng_cfg.get("answer_cap", 256), caps=eng_cfg.get("caps"))
    info = _model_info(cfg, model, tok, template)
    ctx = {"tok": tok, "model_tag": cfg["model_tag"], "module_tmp": module_tmp, "deltas": {},
           "aliases": json.load(open(_abs(cfg.get("aliases", "data/aliases.json")))), "donors": {}}
    given = {}
    for c in plan["conds"]:
        r = c["cfg"]
        if "donor_map" in r:
            ctx["donors"][r["name"]] = json.load(open(_abs(r["donor_map"]["path"])))
        if "given_chain" in r:
            given[r["name"]] = _given_texts(r, c["chains"], plan["cases"], tok)
    os.makedirs(_abs(cfg["out_dir"]), exist_ok=True)
    files = {}
    for c in plan["conds"]:
        files[c["cfg"]["name"]] = open(c["path"], "a")
        if not c["exists"]:
            files[c["cfg"]["name"]].write(json.dumps(_header(plan, c, info, eng_cfg), ensure_ascii=False) + "\n")
            files[c["cfg"]["name"]].flush()
    written = {c["cfg"]["name"]: 0 for c in plan["conds"]}
    chunk_n = int(eng_cfg.get("chunk_cases", 32))
    fails = 0
    try:
        for s in range(0, len(plan["mine"]), chunk_n):
            chunk = plan["mine"][s:s + chunk_n]
            t0 = time.time()
            reqs, metas, errors = [], [], []
            for c in plan["conds"]:
                r = c["cfg"]
                for case in chunk:
                    cid = case["case_id"]
                    todo = [(b, p, d) for b in r["budgets"] for p in r["probes"] for d in r["decode"]
                            if probe_text(case, p) is not None
                            and (cid, r["name"], b, p, d[0], d[1]) not in c["done"]]
                    if not todo:
                        continue
                    try:
                        pay = _payload(r, case, ctx)
                        g = given.get(r["name"], {})
                        if "GIVEN" in r["budgets"] and any((cid, p) not in g for _, p, _ in todo):
                            raise _RowError("missing_chain", f"no given chain for {cid}")
                    except _RowError as e:
                        errors.append((r, case, e.kind, str(e)))
                        continue
                    for b, p, (dec, seed, temp) in todo:
                        biased = pay["bias"] is not None and p in r["bias_probes"]
                        gtext, ginfo = g[(cid, p)] if b == "GIVEN" else (None, None)
                        reqs.append(Request({}, probe_text(case, p), b, edit=pay["edit"],
                                            alpha=r["alpha"] if r["alpha"] is not None else 1.0,
                                            chain_bias=pay["bias"] if biased else None, given_chain=gtext,
                                            user_prefix=pay["user_prefix"], decode=dec, seed=seed,
                                            temperature=temp,
                                            **(r["sample_params"] if dec == "sample" else {})))
                        metas.append((r, case, p, pay, biased, ginfo))
            ctx["deltas"].clear()
            outs, n_log = [], len(engine.batch_log)
            if reqs:
                try:
                    outs = engine.run(reqs)
                    fails = 0
                except Exception as e:
                    fails += 1
                    log(f"[rt.run] chunk {s // chunk_n} failed: {e!r}\n{traceback.format_exc()}")
                    seen = set()
                    for r, case, *_ in metas:
                        if (r["name"], case["case_id"]) not in seen:
                            seen.add((r["name"], case["case_id"]))
                            errors.append((r, case, "engine", repr(e)))
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    if fails >= 3:
                        raise RuntimeError("three consecutive chunks failed; stopping") from e
            for o, (r, case, p, pay, biased, ginfo) in zip(outs, metas):
                row = {"case_id": case["case_id"], "model_tag": cfg["model_tag"], "editor": r["editor"],
                       "target_tag": r["target_tag"], "budget": o["budget"], "probe": p,
                       "condition": r["name"], "arm": r["arm"], "alpha": r["alpha"],
                       "decode": o["decode"], "seed": o["seed"], "temperature": o["temperature"],
                       "q": o["q"], "cot": o["cot"], "answer": o["answer"], "chain_end": o["chain_end"],
                       "n_chain_tokens": o["n_chain_tokens"], "n_answer_tokens": o["n_answer_tokens"],
                       "delta_sha": pay["delta_sha"], "batch_id": o["batch_id"],
                       "chain_batch_id": o["chain_batch_id"], "template": o["template"]}
                if o["decode"] == "sample":
                    row.update(top_p=o["top_p"], top_k=o["top_k"])
                if pay["user_prefix"]:
                    row["user_prefix"] = pay["user_prefix"]
                if pay["bias_info"]:
                    row["bias"] = dict(pay["bias_info"], applied=biased and o["budget"] in CHAIN_BUDGETS,
                                       steps=o["bias_steps"])
                if ginfo:
                    row["given"] = ginfo
                files[r["name"]].write(json.dumps(row, ensure_ascii=False) + "\n")
                written[r["name"]] += 1
            for r, case, kind, msg in errors:
                files[r["name"]].write(json.dumps(
                    {"case_id": case["case_id"], "condition": r["name"], "model_tag": cfg["model_tag"],
                     "editor": r["editor"], "error_kind": kind, "error": msg}, ensure_ascii=False) + "\n")
            for f in files.values():
                f.flush()
            if reqs or errors:
                bl = engine.batch_log[n_log:]
                stat = {ph: (sum(1 for b in bl if b["phase"] == ph),
                             round(sum(b["seconds"] for b in bl if b["phase"] == ph), 1))
                        for ph in ("chain", "answer")}
                log(f"[rt.run] r{plan['rank']}of{plan['world']} cases {s + len(chunk)}/{len(plan['mine'])} "
                    f"rows {len(outs)} errors {len(errors)} {time.time() - t0:.1f}s "
                    f"(batches, s): chain {stat['chain']} answer {stat['answer']}")
    finally:
        for f in files.values():
            f.close()
    return written


def run_config(cfg, rank=0, world=1, model=None, tok=None, config_path=None, only=None, stage=None,
               run_tag=None, limit=None, device=None, log=print):
    plan = prepare(cfg, rank, world, config_path, only, stage, run_tag, limit)
    if model is None:
        model, tok = load_model(cfg, device)
    return execute(plan, model, tok, log)


def main(argv=None):
    from rt.precision import strict_fp32
    strict_fp32()                     # TF32 off: fp32 edits, sums and RoPE positions stay exact
    import yaml
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config", required=True)
    ap.add_argument("--rank", type=int, default=0)
    ap.add_argument("--world", type=int, default=1)
    ap.add_argument("--device", default=None, help="device_map when the config has none (default cuda/cpu)")
    ap.add_argument("--conditions", default=None, help="comma-separated subset of condition names")
    ap.add_argument("--stage", type=int, default=None)
    ap.add_argument("--run-tag", default=None, help="override run_tag (e.g. <tag>_smoke)")
    ap.add_argument("--limit", type=int, default=None, help="first N cases of this shard (smoke)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--batch-size", type=int, default=None,
                    help="override engine.batch_size for this card class (not part of the resume hash)")
    ap.add_argument("--max-batch-tokens", type=int, default=None,
                    help="override engine.max_batch_tokens for this card class (not part of the resume hash)")
    a = ap.parse_args(argv)
    cfg = yaml.safe_load(open(a.config))
    eng = cfg.setdefault("engine", {})
    if a.batch_size:
        eng["batch_size"] = a.batch_size
    if a.max_batch_tokens:
        eng["max_batch_tokens"] = a.max_batch_tokens
    only = a.conditions.split(",") if a.conditions else None
    plan = prepare(cfg, a.rank, a.world, a.config, only, a.stage, a.run_tag, a.limit)
    print(f"[rt.run] {cfg['model_tag']} template={cfg.get('template', 'r1')} cases={len(plan['cases'])} "
          f"shard={len(plan['mine'])} rank={a.rank}/{a.world}")
    for c in plan["conds"]:
        r = c["cfg"]
        n = sum(1 for case in plan["mine"] for b in r["budgets"] for p in r["probes"] for d in r["decode"]
                if probe_text(case, p) is not None
                and (case["case_id"], r["name"], b, p, d[0], d[1]) not in c["done"])
        print(f"  {r['name']:<16} editor={r['editor']:<9} arm={r['arm']} budgets={r['budgets']} "
              f"probes={r['probes']} decode={len(r['decode'])} pending={n} done={len(c['done'])} -> {_rel(c['path'])}")
    if a.dry_run:
        return
    model, tok = load_model(cfg, a.device)
    written = execute(plan, model, tok)
    print(f"[rt.run] done: {written}")


if __name__ == "__main__":
    main()
