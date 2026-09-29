#!/usr/bin/env python3
"""Environment check for the ARR revision runs (engine v2) on a fresh platform image.

Standard library only at import time, and every probe is guarded, so the script always finishes
and reports.  It answers: what does this image lack before RUNSHEET.md step 1 (G0) can run, and
what does it lack for the later steps?

    cd <project root>
    python experiments/rt/env_check.py --out env_report.json            # ~1 min
    python experiments/rt/env_check.py --out env_report.json --gpu-smoke --run-tests

Writes a JSON report (send it back) and prints a summary.  Exit code 0 when nothing blocks G0.
It never prints secrets: tokens and proxy variables are reported only as set / not set.
"""
import argparse
import glob
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time

PINS = {  # env.lock of the last working platform environment
    "torch": "2.9.1", "transformers": "5.5.4", "tokenizers": "0.22.1", "safetensors": "0.8.0",
    "accelerate": "1.13.0", "numpy": "2.2.6", "PyYAML": "6.0", "datasets": "4.8.5",
    "pyarrow": "24.0.0", "huggingface_hub": "1.17.0", "sentencepiece": "0.2.0",
    "scikit-learn": "1.7.2", "scipy": "1.15.3", "einops": "0.8.1", "peft": "0.18.0",
    "sentence-transformers": "5.5.1", "higher": "0.2.1", "hydra-core": "1.3.2", "omegaconf": "2.3.0",
    "nltk": "3.6.5", "pandas": "2.3.3", "matplotlib": "3.10.7", "openai": "2.8.1",
    "zhipuai": "2.1.5.20250415", "timm": "1.0.22", "iopath": "0.1.10", "opencv-python": "4.12.0.88",
    "fairscale": "0.4.13", "av": "14.2.0", "qwen-vl-utils": "0.0.10", "rouge": "1.0.1",
    "gpustat": "1.1", "fsspec": "2026.2.0", "tqdm": "4.67.3", "importlib_metadata": "8.7.0",
    "torchvision": "0.24.1", "pillow": "12.2.0",
}
MODULE_TO_PKG = {"yaml": "PyYAML", "sklearn": "scikit-learn", "cv2": "opencv-python",
                 "hydra": "hydra-core", "qwen_vl_utils": "qwen-vl-utils", "sentence_transformers":
                 "sentence-transformers", "huggingface_hub": "huggingface_hub", "PIL": "pillow",
                 "google": "protobuf", "importlib_metadata": "importlib_metadata"}
# (import name, pip name, needed for)
PACKAGES = [
    ("torch", "torch", "all GPU steps"), ("transformers", "transformers", "all GPU steps"),
    ("tokenizers", "tokenizers", "all"), ("safetensors", "safetensors", "model loading"),
    ("accelerate", "accelerate", "device_map auto (70B, judges, mom2)"),
    ("numpy", "numpy", "all"), ("yaml", "PyYAML", "all configs"),
    ("datasets", "datasets", "mom2 statistics (MEMIT/AlphaEdit)"),
    ("pyarrow", "pyarrow", "mom2 Wikipedia parquet"), ("huggingface_hub", "huggingface_hub", "downloads"),
    ("sentencepiece", "sentencepiece", "judge tokenizers (optional)"),
]
MODELS = {  # tag -> directory name as published on the Hub
    "r1qwen1_5b": "DeepSeek-R1-Distill-Qwen-1.5B", "r1qwen7b": "DeepSeek-R1-Distill-Qwen-7B",
    "r1qwen14b": "DeepSeek-R1-Distill-Qwen-14B", "r1qwen32b": "DeepSeek-R1-Distill-Qwen-32B",
    "r1llama8b": "DeepSeek-R1-Distill-Llama-8B", "r1llama70b": "DeepSeek-R1-Distill-Llama-70B",
    "qwq32b": "QwQ-32B", "qwen2_5_32b_instruct": "Qwen2.5-32B-Instruct",
    "judge_gemma": "gemma-3-27b-it", "judge_mistral": "Mistral-Small-3.1-24B-Instruct-2503",
}
G0_MODEL = "r1qwen32b"
EASYEDIT_PIN = "6a164f976c1b3d596a284e475b1ac98d69219938"   # Study 1, vendor patches, engine v2
DEFAULT_ROOTS = ["/inspire/hdd/global_public/public_models", "/inspire/hdd/project/ai4education/public/why/models",
                 "/inspire/hdd/project/ai4education/ky26140/why/models",
                 "/inspire/hdd/project/ai4education/ky26140/why", os.path.expanduser("~/models"),
                 os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface")) + "/hub"]
URLS = {"pypi": "https://pypi.org/simple/pip/", "pythonhosted": "https://files.pythonhosted.org/",
        "huggingface": "https://huggingface.co/api/models/gpt2", "hf-mirror": "https://hf-mirror.com/",
        "github": "https://github.com/"}


def guard(fn, *a, **k):
    try:
        return fn(*a, **k)
    except Exception as e:  # noqa: BLE001 - the report must always be written
        return {"error": f"{type(e).__name__}: {e}"}


def run(cmd, timeout=60, env=None, cwd=None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env, cwd=cwd)
        return {"rc": p.returncode, "out": p.stdout[-4000:], "err": p.stderr[-4000:]}
    except FileNotFoundError:
        return {"rc": None, "out": "", "err": "not found"}
    except subprocess.TimeoutExpired:
        return {"rc": None, "out": "", "err": f"timeout after {timeout}s"}


def disk(path):
    if not os.path.exists(path):
        return None
    u = shutil.disk_usage(path)
    return {"path": path, "free_gb": round(u.free / 1e9, 1), "total_gb": round(u.total / 1e9, 1)}


def system(root):
    mem = None
    if os.path.exists("/proc/meminfo"):
        info = dict(l.split(":", 1) for l in open("/proc/meminfo") if ":" in l)
        mem = {k: round(int(info[k].split()[0]) / 1e6, 1) for k in ("MemTotal", "MemAvailable") if k in info}
    tools = {t: (shutil.which(t) is not None) for t in ("git", "nvidia-smi", "pip", "uv", "conda", "hf",
                                                         "huggingface-cli", "git-lfs")}
    return {"python": sys.version.split()[0], "executable": sys.executable, "platform": platform.platform(),
            "cpus": os.cpu_count(), "ram_gb": mem, "tools": tools,
            "disk": [d for d in (disk(root), disk("/tmp"), disk(os.path.expanduser("~")),
                                 disk("/inspire/hdd/project/ai4education/ky26140/why")) if d],
            "env": {k: os.environ.get(k) for k in ("CUDA_VISIBLE_DEVICES", "HF_HOME", "HF_ENDPOINT",
                                                  "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "PIP_INDEX_URL",
                                                  "WHYAAAI_MODEL", "WHYAAAI_WIKI_PARQUET", "MODEL32", "MODEL14",
                                                  "WIKI_EN")},
            "secrets_present": {"HF_TOKEN": bool(os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
                                                 or os.path.exists(os.path.expanduser("~/.cache/huggingface/token"))),
                                "proxy": any(os.environ.get(k) for k in ("http_proxy", "https_proxy", "HTTP_PROXY",
                                                                         "HTTPS_PROXY"))}}


def gpus():
    out = {"nvidia_smi": None, "torch": None}
    r = run(["nvidia-smi", "--query-gpu=index,name,memory.total,memory.used,driver_version",
             "--format=csv,noheader"], timeout=30)
    if r["rc"] == 0:
        out["nvidia_smi"] = [dict(zip(("index", "name", "memory_total", "memory_used", "driver"),
                                      [x.strip() for x in l.split(",")])) for l in r["out"].strip().splitlines()]
    else:
        out["nvidia_smi_error"] = r["err"].strip()[:300]
    out["torch"] = guard(_torch_cuda)
    return out


def _torch_cuda():
    import torch
    info = {"version": torch.__version__, "cuda_build": torch.version.cuda, "available": torch.cuda.is_available()}
    if not info["available"]:
        return info
    info["count"] = torch.cuda.device_count()
    info["devices"] = []
    for i in range(info["count"]):
        p = torch.cuda.get_device_properties(i)
        info["devices"].append({"name": p.name, "mem_gb": round(p.total_memory / 1e9, 1),
                                "capability": f"{p.major}.{p.minor}"})
    info["bf16_supported"] = torch.cuda.is_bf16_supported()
    info["tf32_env"] = {k: os.environ.get(k) for k in ("NVIDIA_TF32_OVERRIDE", "TORCH_ALLOW_TF32_CUBLAS_OVERRIDE")}
    g = torch.Generator().manual_seed(0)
    a = torch.randn(512, 512, generator=g, dtype=torch.float64)
    ref = a @ a
    got = (a.float().cuda() @ a.float().cuda()).double().cpu()
    info["fp32_matmul_rel_err_image_default"] = float(torch.linalg.norm(got - ref) / torch.linalg.norm(ref))
    t = time.time()
    x = torch.randn(4096, 4096, device="cuda")
    y = (x @ x).float()
    xb = x.to(torch.bfloat16)
    yb = (xb @ xb).float()
    torch.cuda.synchronize()
    info["matmul_ok"] = bool(torch.isfinite(y).all() and torch.isfinite(yb).all())
    info["matmul_s"] = round(time.time() - t, 2)
    return info


def packages():
    import importlib
    try:
        from importlib import metadata
    except ImportError:
        metadata = None
    rows = []
    for mod, pkg, why in PACKAGES:
        rec = {"module": mod, "package": pkg, "for": why, "pin": PINS.get(pkg)}
        try:
            importlib.import_module(mod)
            rec["ok"] = True
            rec["version"] = metadata.version(pkg) if metadata else None
        except Exception as e:  # noqa: BLE001
            rec["ok"] = False
            rec["error"] = f"{type(e).__name__}: {str(e)[:200]}"
        if rec.get("version") and rec["pin"] and rec["version"] != rec["pin"]:
            rec["differs_from_pin"] = True
        rows.append(rec)
    return rows


def transformers_classes():
    import transformers
    names = ["Qwen2ForCausalLM", "LlamaForCausalLM", "Qwen3ForCausalLM", "Gemma3ForConditionalGeneration",
             "Mistral3ForConditionalGeneration", "LogitsProcessor"]
    return {n: hasattr(transformers, n) for n in names}


_EASYEDIT_PROBE = r"""
import sys, types, json, importlib, importlib.machinery
root, ee = sys.argv[1], sys.argv[2]
sys.path[:0] = [root + "/src", ee]
missing, stubbed = [], []
def _stub(name):
    m = types.ModuleType(name); m.__path__ = []
    m.__spec__ = importlib.machinery.ModuleSpec(name, None, is_package=True)
    m.__getattr__ = lambda attr: (_ for _ in ()).throw(AttributeError(attr)) if attr.startswith("__") else type(attr, (), {})
    return m
for _ in range(80):
    try:
        try:
            from vendor_patches.easyedit_lean_import import apply
            stubbed = apply()          # optional extras only; what still fails below is a real need
        except ModuleNotFoundError:
            raise
        except Exception as e:
            stubbed = [f"lean import unavailable: {e!r}"[:200]]
        import easyeditor
        from easyeditor import BaseEditor, ROMEHyperParams, MEMITHyperParams, AlphaEditHyperParams
        from easyeditor.util import nethook
        from easyeditor.models.rome import rome_main, layer_stats
        from easyeditor.models.memit import memit_main
        from easyeditor.models.alphaedit import AlphaEdit_main
        print(json.dumps({"ok": not missing, "missing": missing, "stubbed_optional": stubbed}))
        break
    except ModuleNotFoundError as e:
        name = e.name or ""
        if not name or name in missing or name.startswith(("easyeditor", "vendor_patches")) \
                or (name != name.lower() and name != "PIL"):   # a class name (e.g. AutoProcessor) is not a package
            cause = e.__cause__ or e.__context__
            print(json.dumps({"ok": False, "missing": missing, "fatal": repr(e)[:300],
                              "cause": repr(cause)[:500] if cause else None})); break
        missing.append(name)
        for k in [m for m in list(sys.modules) if m.split(".")[0] in ("easyeditor", "vendor_patches")]:
            del sys.modules[k]
        sys.modules[name] = _stub(name)
    except Exception as e:
        print(json.dumps({"ok": False, "missing": missing, "fatal": f"{type(e).__name__}: {e}"[:500]})); break
"""


def easyedit(root):
    path = os.path.join(root, "source", "EasyEdit")
    rec = {"path": path, "present": os.path.isdir(os.path.join(path, "easyeditor"))}
    if not rec["present"]:
        rec["hint"] = "run `bash setup_workspace.sh` (clones EasyEdit at the pinned commit; needs GitHub access)"
        return rec
    rec["git"] = run(["git", "-C", path, "rev-parse", "HEAD"], timeout=20)["out"].strip() or None
    rec["pinned"] = rec["git"] == EASYEDIT_PIN
    r = run([sys.executable, "-c", _EASYEDIT_PROBE, root, path], timeout=300)
    try:
        rec.update(json.loads(r["out"].strip().splitlines()[-1]))
    except Exception:  # noqa: BLE001
        rec["probe_error"] = (r["err"] or r["out"])[-1500:]
    top = sorted({m.split(".")[0] for m in rec.get("missing", [])})
    rec["missing_packages"] = [MODULE_TO_PKG.get(m, m) for m in top]
    return rec


def repo(root):
    rec = {"root": root, "is_git": os.path.isdir(os.path.join(root, ".git")) or os.path.isfile(os.path.join(root, ".git"))}
    if rec["is_git"]:
        rec["head"] = run(["git", "-C", root, "rev-parse", "HEAD"], timeout=20)["out"].strip()
        rec["branch"] = run(["git", "-C", root, "rev-parse", "--abbrev-ref", "HEAD"], timeout=20)["out"].strip()
        rec["dirty"] = bool(run(["git", "-C", root, "status", "--porcelain"], timeout=60)["out"].strip())
    need = ["REVISION.md", "src/rt/engine.py", "src/rt/run.py", "src/rt/deltas.py", "src/rt/g0.py",
            "src/rt/judge.py", "src/rt/mech.py", "src/think_budget.py", "src/metrics.py",
            "experiments/rt/RUNSHEET.md", "experiments/rt/pools/study1_cf200.jsonl", "data/aliases.json",
            "data/placebo_donors.json", "data/placebo_donors_strong.json"]
    rec["files"] = {f: os.path.exists(os.path.join(root, f)) for f in need}
    cf = os.path.join(root, "data", "counterfact.jsonl")
    rec["counterfact_rows"] = sum(1 for _ in open(cf)) if os.path.exists(cf) else None
    rec["study1_32b_shards"] = len(glob.glob(os.path.join(root, "results/probe/r1qwen32b_ROME_cf200_r*of8.jsonl")))
    rec["study1_32b_base_shards"] = len(glob.glob(os.path.join(root, "results/probe/r1qwen32b_BASE_cf200_r*.jsonl")))
    rec["history_jsonl"] = len(glob.glob(os.path.join(root, "results/**/*.jsonl"), recursive=True))
    rec["stats_dirs"] = sorted(os.path.basename(p) for p in glob.glob(os.path.join(root, "data/stats_*")))
    return rec


def _dir_info(d):
    cfg_p = os.path.join(d, "config.json")
    info = {"path": d, "config": os.path.exists(cfg_p)}
    if info["config"]:
        c = json.load(open(cfg_p))
        tc = c.get("text_config") or {}
        info.update(model_type=c.get("model_type"), layers=c.get("num_hidden_layers") or tc.get("num_hidden_layers"),
                    dtype=c.get("torch_dtype") or c.get("dtype"))
    w = glob.glob(os.path.join(d, "*.safetensors")) + glob.glob(os.path.join(d, "*.bin"))
    info["weights_gb"] = round(sum(os.path.getsize(f) for f in w) / 1e9, 1)
    info["tokenizer"] = any(os.path.exists(os.path.join(d, f)) for f in ("tokenizer.json", "tokenizer.model",
                                                                          "tekken.json"))
    base = os.path.basename(os.path.normpath(d)).lower()
    info["easyedit_loader_ok"] = ("qwen" in base) or ("llama" in base) or ("qwen" in d.lower().split("/")[-1])
    return info


def models(roots, depth=4):
    found = {tag: [] for tag in MODELS}
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        base_depth = root.rstrip("/").count("/")
        for dirpath, dirnames, _ in os.walk(root):
            if dirpath.count("/") - base_depth >= depth:
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            name = os.path.basename(dirpath)
            for tag, hub in MODELS.items():
                hit = name.lower() == hub.lower() or name.lower().endswith("--" + hub.lower())
                if hit:
                    cand = dirpath
                    snaps = glob.glob(os.path.join(dirpath, "snapshots", "*"))
                    if snaps:
                        cand = sorted(snaps)[-1]
                    found[tag].append(guard(_dir_info, cand))
    for var, tag in (("MODEL32", "r1qwen32b"), ("MODEL14", "r1qwen14b"), ("WHYAAAI_MODEL", None)):
        p = os.environ.get(var)
        if p and os.path.isdir(p):
            t = tag or next((k for k, v in MODELS.items() if v.lower() in p.lower()), "env_" + var)
            found.setdefault(t, []).append(guard(_dir_info, p))
    return found


def network():
    import urllib.request
    out = {}
    for name, url in URLS.items():
        t = time.time()
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "env-check"})
            with urllib.request.urlopen(req, timeout=6) as r:
                out[name] = {"ok": True, "status": r.status, "s": round(time.time() - t, 2)}
        except Exception as e:  # noqa: BLE001
            code = getattr(e, "code", None)
            out[name] = {"ok": code is not None and code < 500, "status": code, "error": type(e).__name__}
    return out


def wiki():
    cands = [os.environ.get("WHYAAAI_WIKI_PARQUET"), os.environ.get("WIKI_EN"),
             "/inspire/dataset/Wikipedia/20231101/20231101.en",      # platform mount (2026-09-29, 41 parquet)
             "/inspire/dataset/wikipedia/20231101/20231101.en"]
    for c in cands:
        if c and os.path.isdir(c):
            files = glob.glob(os.path.join(c, "**", "*.parquet"), recursive=True)
            return {"path": c, "parquet_files": len(files), "english_dir": c.rstrip("/").endswith(".en")}
    return {"path": None, "hint": "needed only for MEMIT/AlphaEdit statistics (RUNSHEET step 5)"}


_GPU_SMOKE = r"""
import sys, json, torch
sys.path.insert(0, sys.argv[1] + "/src")
from rt.edit_hooks import EditBank
from rt.tests._tiny import tiny_model, tiny_tokenizer, rank1_edit, MODULE_TMP
tok = tiny_tokenizer()
m = tiny_model(vocab=len(tok)).to("cuda", torch.bfloat16)
e = {k: (a.to("cuda"), b.to("cuda")) for k, (a, b) in rank1_edit(m, 1, seed=1, scale=1.0).items()}
ids = torch.tensor([[3, 17, 9, 41, 5, 22]] * 2, device="cuda")
with EditBank(m, MODULE_TMP) as bank:
    bank.set_batch([e, None])
    out = m.generate(input_ids=ids, max_new_tokens=16, do_sample=False, pad_token_id=0)
    logits = m(input_ids=ids).logits
from rt.precision import check_fp32_matmul, strict_fp32
strict_fp32()
chk = check_fp32_matmul("cuda")
print(json.dumps({"ok": bool(torch.isfinite(logits.float()).all()) and chk["ok"],
                  "rows_differ": bool((out[0] != out[1]).any()), "fp32_after_rt": chk}))
"""


def gpu_smoke(root):
    r = run([sys.executable, "-c", _GPU_SMOKE, root], timeout=600)
    try:
        return json.loads(r["out"].strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        return {"ok": False, "error": (r["err"] or r["out"])[-1500:]}


def tests(root):
    env = dict(os.environ, PYTHONPATH=os.path.join(root, "src"))
    r = run([sys.executable, os.path.join(root, "src/rt/tests/run_all.py")], timeout=1800, env=env, cwd=root)
    tail = (r["out"] or "").strip().splitlines()[-1:] or [""]
    return {"rc": r["rc"], "summary": tail[0], "stderr_tail": r["err"][-1500:] if r["rc"] else ""}


def verdict(rep):
    block, warn = [], []
    pk = {p["module"]: p for p in rep["packages"] if isinstance(p, dict) and "module" in p}
    for mod in ("torch", "transformers", "tokenizers", "safetensors", "numpy", "yaml", "accelerate"):
        if not pk.get(mod, {}).get("ok"):
            block.append(f"python package missing: {pk.get(mod, {}).get('package', mod)}")
    if pk.get("torch", {}).get("differs_from_pin"):
        warn.append(f"torch {pk['torch'].get('version')} differs from pin {PINS['torch']}: keep the image's CUDA build, "
                    "do NOT pip-install another torch; the CPU tests and --gpu-smoke validate this build")
    if pk.get("transformers", {}).get("differs_from_pin"):
        block.append(f"transformers {pk['transformers'].get('version')} != {PINS['transformers']} (prompt/tokenizer "
                     "behaviour was validated on the pin)")
    t = (rep["gpu"] or {}).get("torch") or {}
    if not t.get("available"):
        block.append("torch sees no CUDA device")
    else:
        mems = [d["mem_gb"] for d in t.get("devices", [])]
        big = max(mems) if mems else 0
        rep["node"] = {"gpus": len(mems), "max_gb": big, "total_gb": round(sum(mems), 1),
                       "fp32_edits_32b": big >= 130, "fp32_edits_upto_8b": big >= 40,
                       "bf16_32b_cards_per_process": 1 if big >= 100 else 2,
                       "bf16_70b_cards_per_process": 2 if big >= 100 else 4}
        if big < 130:
            warn.append(f"largest GPU {big} GB: fp32 edits of 14B/32B/70B (G0 step 1a, Study-2 deltas) must run on "
                        "the H200 node; this node can run bf16 generation, pool screening, judges and <=8B fp32 edits")
        if not t.get("matmul_ok", True):
            block.append("GPU matmul produced non-finite values")
    ee = rep["easyedit"]
    if not ee.get("present"):
        block.append("source/EasyEdit missing (setup_workspace.sh)")
    elif not ee.get("pinned"):
        block.append(f"source/EasyEdit is at {str(ee.get('git'))[:7]}, must be {EASYEDIT_PIN[:7]} "
                     "(re-run setup_workspace.sh from this branch; it pins the commit)")
    if ee.get("present") and not ee.get("ok"):
        block.append("easyeditor import needs: " + ", ".join(ee.get("missing_packages") or [ee.get("fatal", "?")]))
    r = rep["repo"]
    for f, ok in r.get("files", {}).items():
        if not ok:
            block.append(f"repo file missing: {f} (wrong branch? expected claude/paper-review-understanding-8732e6)")
    if not r.get("counterfact_rows"):
        block.append("data/counterfact.jsonl missing (python src/build_dataset.py)")
    if r.get("study1_32b_shards", 0) < 8 or r.get("study1_32b_base_shards", 0) < 8:
        block.append("Study-1 32B rows missing under results/probe/ (G0 compares against them)")
    if not [x for x in rep["models"].get(G0_MODEL, []) if isinstance(x, dict) and x.get("config")]:
        block.append("DeepSeek-R1-Distill-Qwen-32B weights not found (pass --model-roots)")
    for tag in MODELS:
        if tag != G0_MODEL and not [x for x in rep["models"].get(tag, []) if isinstance(x, dict) and x.get("config")]:
            warn.append(f"model not found: {MODELS[tag]} (needed later)")
    for tag in ("qwq32b",):
        for x in rep["models"].get(tag, []):
            if isinstance(x, dict) and x.get("config") and not x.get("easyedit_loader_ok"):
                warn.append(f"{x['path']}: name lacks 'qwen'; symlink it (EasyEdit picks the loader by name)")
    if r.get("history_jsonl", 0) < 50:
        warn.append("results/ history looks incomplete; `rt.pool build` must see every earlier run")
    if not rep["wiki"].get("path"):
        warn.append("English Wikipedia parquet not found (MEMIT/AlphaEdit statistics only)")
    if rep.get("tests") and rep["tests"].get("rc") != 0:
        block.append(f"CPU test suite failed: {rep['tests'].get('summary')}")
    if rep.get("gpu_smoke") and not rep["gpu_smoke"].get("ok"):
        chk = rep["gpu_smoke"].get("fp32_after_rt") or {}
        block.append("GPU smoke failed" + (f": fp32 matmul still TF32-sized after importing rt "
                                           f"(rel_err {chk.get('rel_err'):.1e})" if chk and not chk.get("ok") else ""))
    e = t.get("fp32_matmul_rel_err_image_default")
    if e is not None and e > 2e-5:
        warn.append(f"image default runs fp32 matmuls as TF32 (rel_err {e:.1e}); rt entry points switch it off "
                    "(src/rt/precision.py) -- any other fp32 GPU code must do the same")
    missing_pkgs = sorted({p["package"] for p in rep["packages"] if isinstance(p, dict) and not p.get("ok")
                           and p["module"] != "torch"} | set(ee.get("missing_packages") or []))
    pip = " ".join(f"{p}=={PINS[p]}" if p in PINS else p for p in missing_pkgs)
    return {"blockers": block, "warnings": warn, "pip_install": f"pip install {pip}" if pip else None}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--out", default="env_report.json")
    ap.add_argument("--model-roots", nargs="*", default=None, help="directories searched for model weights")
    ap.add_argument("--gpu-smoke", action="store_true", help="run the edit hooks on a tiny model on GPU")
    ap.add_argument("--run-tests", action="store_true", help="run the CPU test suite (src/rt/tests)")
    ap.add_argument("--no-network", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    t0 = time.time()
    rep = {"when": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "system": guard(system, root), "gpu": guard(gpus),
           "packages": guard(packages), "transformers_classes": guard(transformers_classes),
           "easyedit": guard(easyedit, root), "repo": guard(repo, root),
           "models": guard(models, a.model_roots or DEFAULT_ROOTS), "wiki": guard(wiki),
           "network": {} if a.no_network else guard(network)}
    if not isinstance(rep["packages"], list):
        rep["packages"] = []
    if a.run_tests:
        rep["tests"] = guard(tests, root)
    if a.gpu_smoke:
        rep["gpu_smoke"] = guard(gpu_smoke, root)
    rep["verdict"] = guard(verdict, rep)
    rep["seconds"] = round(time.time() - t0, 1)
    with open(a.out, "w") as fh:
        json.dump(rep, fh, indent=1, ensure_ascii=False, default=str)
    v = rep["verdict"] if isinstance(rep["verdict"], dict) else {"blockers": [str(rep["verdict"])], "warnings": []}
    g = (rep["gpu"] or {}).get("torch") or {}
    print(f"[env] python {rep['system'].get('python')} | torch {g.get('version')} cuda={g.get('available')} "
          f"gpus={[d['name'] for d in g.get('devices', [])]}")
    print(f"[env] models found: {sorted(t for t, v2 in rep['models'].items() if v2)}")
    print(f"[env] network: { {k: v2.get('ok') for k, v2 in (rep['network'] or {}).items()} }")
    for b in v["blockers"]:
        print("BLOCKER  " + b)
    for w in v["warnings"]:
        print("warning  " + w)
    if v.get("pip_install"):
        print("fix:     " + v["pip_install"])
    print(f"[env] report -> {a.out}  ({rep['seconds']} s)  " + ("READY for G0" if not v["blockers"] else "NOT READY"))
    sys.exit(0 if not v["blockers"] else 1)


if __name__ == "__main__":
    main()
