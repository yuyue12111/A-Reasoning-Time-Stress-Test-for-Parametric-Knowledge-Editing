"""Pre-GPU/full-run technical gate for X2 and X3 smoke outputs.

Exit codes: 0=PASS, 1=technical/config failure, 2=existing N is not auditable/reproducible (run predeclared fresh N).

Examples:
  python src/validate_x_smoke.py x2 \
    --arm N=experiments/memit14b.yaml \
    --arm T=experiments/memit14b_sup.yaml@_smoke \
    --arm C=experiments/memit14b_strongcomp.yaml@_smoke \
    --log results/logs/x2_T_smoke.log --log results/logs/x2_C_smoke.log

  python src/validate_x_smoke.py x3 \
    --arm N=experiments/probe32b.yaml \
    --arm T=experiments/probe32b_para_sup.yaml@_smoke \
    --arm C=experiments/probe32b_para_strongcomp.yaml@_smoke
"""
import argparse
import glob
import hashlib
import json
import os
import random
import sys

import yaml


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARNESS_FILES = [
    "src/run_pilot.py", "src/edit_loop.py", "src/think_budget.py", "src/suppress.py",
    "src/r1_tokenizer.py", "src/vendor_patches/easyedit_qwen2_loader.py",
    "src/vendor_patches/easyedit_mom2_dataset.py",
]


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def current_code_sha():
    return {rel: _sha(_abs(rel)) for rel in HARNESS_FILES if os.path.exists(_abs(rel))}


def parse_arm(spec):
    label, sep, rhs = spec.partition("=")
    if not sep:
        raise ValueError(f"bad arm {spec!r}; expected LABEL=config.yaml[@suffix]")
    if "@" in rhs:
        path, suffix = rhs.rsplit("@", 1)
    else:
        path, suffix = rhs, ""
    return label, _abs(path), suffix


def _dataset_path(cfg):
    for path in (cfg["dataset"].get("path"), cfg["dataset"].get("fallback_path")):
        if path and os.path.exists(_abs(path)):
            return _abs(path)
    raise FileNotFoundError(f"dataset missing for {cfg['dataset']}")


def _selected_cases(cfg):
    rows = [json.loads(line) for line in open(_dataset_path(cfg)) if line.strip()]
    random.Random(cfg.get("seed", 42)).shuffle(rows)
    n = cfg["dataset"].get("n")
    return rows[:n] if n else rows


def load_arm(path, suffix, editor):
    cfg = yaml.safe_load(open(path))
    tag = cfg["dataset"]["tag"] + suffix
    pat = os.path.join(_abs(cfg["out_dir"]), f"{cfg['model_tag']}_{editor}_{tag}_r*.jsonl")
    shards = sorted(glob.glob(pat))
    if not shards:
        raise FileNotFoundError(f"no shards: {pat}")
    rows, metas, errors = {}, [], []
    for shard in shards:
        for lineno, line in enumerate(open(shard), 1):
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("_meta"):
                metas.append(r); continue
            if r.get("error"):
                errors.append((shard, lineno, r)); continue
            if r.get("decode", "greedy") != "greedy" or not r.get("probe"):
                continue
            key = (r["case_id"], r["budget"], r["probe"])
            if key in rows:
                raise ValueError(f"duplicate row {key}; likely mixed shard worlds under one tag")
            rows[key] = r
    cases = _selected_cases(cfg)
    return {"path": path, "suffix": suffix, "cfg": cfg, "tag": tag, "pattern": pat,
            "shards": shards, "metas": metas, "errors": errors, "rows": rows,
            "cases": cases, "cmap": {c["case_id"]: c for c in cases}}


def core_config(arm, editor):
    cfg = arm["cfg"]
    return {"model_tag": cfg.get("model_tag"), "seed": cfg.get("seed"),
            "hparams_overrides": cfg.get("hparams_overrides"),
            "dataset_path": cfg["dataset"].get("path"),
            "dataset_fallback": cfg["dataset"].get("fallback_path"),
            "dataset_n": cfg["dataset"].get("n"), "budgets": cfg.get("budgets"),
            "sampling": cfg.get("sampling"), "editor": cfg["editors"].get(editor)}


def _unique_meta(arm, key):
    vals = {json.dumps(m.get(key), sort_keys=True, ensure_ascii=False) for m in arm["metas"]}
    return vals


def normalized_actual_runtime(meta):
    """Cross-rank model signature; single-GPU parameter_device may vary by physical rank."""
    actual = dict(meta.get("actual_runtime") or {})
    actual.pop("parameter_device", None)
    return actual


def normalized_runtime_env(meta):
    """Physical GPU IDs differ across pair workers; all scientific/runtime knobs must match."""
    env = dict(meta.get("runtime_env") or {})
    env.pop("CUDA_VISIBLE_DEVICES", None)
    return env


def check_new_meta(label, arm, expected_suffix, failures, warnings=None):
    if len(arm["metas"]) != len(arm["shards"]):
        failures.append(f"{label}: expected one _meta per shard ({len(arm['shards'])}), got {len(arm['metas'])}")
        return
    for key in ("config_sha256", "code_sha256", "runtime_env", "software", "actual_runtime"):
        if any(m.get(key) in (None, {}, "unknown") for m in arm["metas"]):
            failures.append(f"{label}: missing provenance key {key}")
        if key not in ("actual_runtime", "runtime_env") and len(_unique_meta(arm, key)) != 1:
            failures.append(f"{label}: inconsistent {key} across shards")
    runtime_values = {json.dumps(normalized_runtime_env(m), sort_keys=True, ensure_ascii=False)
                      for m in arm["metas"]}
    if len(runtime_values) != 1:
        failures.append(f"{label}: inconsistent runtime environment across shards (excluding physical CUDA_VISIBLE_DEVICES)")
    actual_values = {json.dumps(normalized_actual_runtime(m), sort_keys=True, ensure_ascii=False)
                     for m in arm["metas"]}
    if len(actual_values) != 1:
        failures.append(f"{label}: inconsistent actual model/tokenizer signature across shards")
    if warnings is not None and any(m.get("git") in (None, "unknown") for m in arm["metas"]):
        warnings.append(f"{label}: git hash unavailable on uploaded server; exact code_sha256 remains authoritative")
    if any(m.get("config_sha256") != _sha(arm["path"]) for m in arm["metas"]):
        failures.append(f"{label}: config SHA in JSONL does not match uploaded YAML")
    if any(m.get("code_sha256") != current_code_sha() for m in arm["metas"]):
        failures.append(f"{label}: JSONL code hashes do not match files currently on shared disk")
    for m in arm["metas"]:
        env = m.get("runtime_env", {})
        if env.get("WHYAAAI_DTYPE") != "float32":
            failures.append(f"{label}: WHYAAAI_DTYPE must be float32, got {env.get('WHYAAAI_DTYPE')!r}")
        if env.get("WHYAAAI_NO_BOS") not in ("1", "true", "True"):
            failures.append(f"{label}: WHYAAAI_NO_BOS=1 required to match legacy Qwen N")
        if not env.get("WHYAAAI_MODEL"):
            failures.append(f"{label}: WHYAAAI_MODEL absolute path was not recorded")
        actual = m.get("actual_runtime", {})
        if "float32" not in str(actual.get("parameter_dtype")):
            failures.append(f"{label}: actual model dtype is not float32: {actual.get('parameter_dtype')!r}")
        run = m.get("run", {})
        if expected_suffix and run.get("tag_suffix") != expected_suffix:
            failures.append(f"{label}: smoke tag suffix metadata mismatch")
        if expected_suffix and m.get("dataset", {}).get("effective_n") != 8:
            failures.append(f"{label}: smoke must contain effective_n=8")


def check_x3_model_parallel(label, arm, failures):
    if arm["cfg"].get("hparams_overrides", {}).get("model_parallel") is not True:
        failures.append(f"{label}: X3 rescue requires hparams_overrides.model_parallel=true")
    for m in arm["metas"]:
        env = m.get("runtime_env", {})
        actual = m.get("actual_runtime", {})
        if env.get("WHYAAAI_DEVICE_MAP") != "balanced":
            failures.append(f"{label}: WHYAAAI_DEVICE_MAP must be 'balanced', got {env.get('WHYAAAI_DEVICE_MAP')!r}")
        if actual.get("model_parallel") is not True:
            failures.append(f"{label}: actual runtime did not record model_parallel=true")
        devices = set(actual.get("hf_device_map_devices") or [])
        if not {"0", "1"}.issubset(devices):
            failures.append(f"{label}: model was not spread over both local GPUs: {sorted(devices)}")
        edit_devs = actual.get("edit_weight_devices") or {}
        if not edit_devs or any(str(v).startswith("ERROR:") for v in edit_devs.values()):
            failures.append(f"{label}: missing/invalid editable-weight device audit: {edit_devs}")


def expected_row_keys(arm, effective_n):
    cfg = arm["cfg"]
    sel = set(cfg.get("probes") or ["efficacy", "paraphrase", "locality", "open"])
    keys = set()
    for c in arm["cases"][:effective_n]:
        probes = []
        if "efficacy" in sel:
            probes.append("efficacy")
        if "paraphrase" in sel:
            probes.extend(f"para{i}" for i, _ in enumerate(c.get("paraphrases", [])[:2]))
        else:
            probes.extend(p for p in ("para0", "para1") if p in sel)
        if "locality" in sel and c.get("neighborhood"):
            probes.append("locality")
        if "open" in sel:
            probes.append("open")
        for budget in cfg.get("budgets", []):
            keys.update((c["case_id"], budget, probe) for probe in probes)
    return keys


def check_completeness(label, arm, expected_suffix, failures):
    if arm["errors"]:
        failures.append(f"{label}: {len(arm['errors'])} error rows present")
    ns = {m.get("dataset", {}).get("effective_n") for m in arm["metas"]}
    if len(ns) != 1 or None in ns:
        failures.append(f"{label}: inconsistent/missing effective_n in metadata: {ns}")
        return
    effective_n = next(iter(ns))
    expected_n = 8 if expected_suffix else arm["cfg"]["dataset"].get("n")
    if effective_n != expected_n:
        failures.append(f"{label}: effective_n={effective_n}, expected {expected_n}")
    expected = expected_row_keys(arm, effective_n)
    missing = expected - set(arm["rows"])
    if missing:
        failures.append(f"{label}: incomplete output, missing {len(missing)}/{len(expected)} expected rows; first={sorted(missing)[:5]}")


def check_x3_oom_regression(arm, failures):
    """The mp2 smoke is only meaningful if it completes the exact single-GPU OOM case."""
    selected = {c["case_id"] for c in arm["cases"][:8]}
    if "cf_975" not in selected:
        failures.append("X3 smoke no longer contains preregistered OOM regression case cf_975")
        return
    keys = {key for key in arm["rows"] if key[0] == "cf_975"}
    expected = {key for key in expected_row_keys(arm, 8) if key[0] == "cf_975"}
    if keys != expected:
        failures.append(f"X3 cf_975 regression incomplete: have {len(keys)}/{len(expected)} rows")


def compare_b0(N, arm, probes):
    diffs, missing, compared = [], [], 0
    for key, row in arm["rows"].items():
        cid, budget, probe = key
        if budget != "B0" or probe not in probes:
            continue
        nrow = N["rows"].get(key)
        if not nrow:
            missing.append(key); continue
        compared += 1
        if (row.get("q"), row.get("cot"), row.get("answer")) != (
                nrow.get("q"), nrow.get("cot"), nrow.get("answer")):
            diffs.append(key)
    return {"compared": compared, "missing": missing, "different": diffs}


def b3_output_differences(N, arm, probes):
    keys = []
    for key, row in arm["rows"].items():
        _, budget, probe = key
        if budget != "B3" or probe not in probes or key not in N["rows"]:
            continue
        nrow = N["rows"][key]
        if (row.get("cot"), row.get("answer")) != (nrow.get("cot"), nrow.get("answer")):
            keys.append(key)
    return keys


def check_trace(label, arm, active_probes, donor_map, failures):
    checked = 0
    for key, row in arm["rows"].items():
        cid, budget, probe = key
        if probe not in active_probes:
            continue
        tr = row.get("suppress_trace")
        if not tr:
            failures.append(f"{label}: {key} missing suppress_trace"); continue
        checked += 1
        expected = donor_map.get(cid)
        if not tr.get("target") or (expected is not None and tr.get("target") != expected):
            failures.append(f"{label}: {key} target mismatch/nonempty failure")
        if not tr.get("token_ids"):
            failures.append(f"{label}: {key} token_ids empty")
        if tr.get("selected") is not True:
            failures.append(f"{label}: {key} not selected by apply_to")
        calls = tr.get("processor_calls")
        if budget == "B0":
            if tr.get("active") is not False or calls != 0:
                failures.append(f"{label}: {key} B0 scope=think should make zero processor calls")
        elif budget == "B3":
            if tr.get("active") is not True or not isinstance(calls, int) or calls <= 0:
                failures.append(f"{label}: {key} processor was not actually invoked")
    if checked == 0:
        failures.append(f"{label}: no active-probe rows found")


def parity_signature(meta):
    env = meta.get("runtime_env", {})
    actual = meta.get("actual_runtime", {})
    return {"git": meta.get("git"), "code_sha256": meta.get("code_sha256"),
            "dtype_env": env.get("WHYAAAI_DTYPE"), "no_bos": env.get("WHYAAAI_NO_BOS"),
            "model_env": env.get("WHYAAAI_MODEL"), "software": meta.get("software"),
            "actual_dtype": actual.get("parameter_dtype"), "bos_token_id": actual.get("bos_token_id"),
            "eos_token_id": actual.get("eos_token_id"), "loaded_model": actual.get("loaded_model")}


def x2_n_parity(N, T, C):
    if not N["metas"] or any(not m.get("code_sha256") or not m.get("runtime_env")
                             or not m.get("actual_runtime") for m in N["metas"]):
        return False, "old N lacks code/runtime/actual-model provenance"
    ns = {json.dumps(parity_signature(m), sort_keys=True) for m in N["metas"]}
    ts = {json.dumps(parity_signature(m), sort_keys=True) for m in T["metas"]}
    cs = {json.dumps(parity_signature(m), sort_keys=True) for m in C["metas"]}
    if len(ns) != 1 or ns != ts or ns != cs:
        return False, "N/T/C git, code hash, dtype, BOS, model, or software signature differs"
    return True, "strict provenance parity"


def check_logs(paths, failures):
    if not paths:
        failures.append("X2 requires --log files to prove mom2 cache hits")
        return {"loading_cached_lines": 0}
    expanded = []
    for path in paths:
        matches = sorted(glob.glob(_abs(path)))
        expanded.extend(matches or [_abs(path)])
    missing = [path for path in expanded if not os.path.exists(path)]
    if missing:
        failures.append(f"missing smoke log files: {missing}")
        return {"loading_cached_lines": 0, "files": expanded}
    text = "\n".join(open(path, errors="replace").read() for path in expanded)
    n_cached = sum("Loading cached" in line and "stats_r1qwen14b" in line for line in text.splitlines())
    if n_cached < 3:
        failures.append(f"mom2 audit found only {n_cached} stats_r1qwen14b 'Loading cached' lines; need >=3 layers")
    for bad in ("Traceback", "CUDA out of memory", "[case-fail]", "Recomputing"):
        if bad in text:
            failures.append(f"smoke logs contain forbidden failure/recompute marker: {bad}")
    return {"loading_cached_lines": n_cached, "files": expanded}


def validate(mode, arms, logs):
    failures, warnings = [], []
    editor = "MEMIT" if mode == "x2" else "ROME"
    for label in ("N", "T", "C"):
        if label not in arms:
            failures.append(f"missing arm {label}")
    if failures:
        return {"status": "FAIL", "failures": failures}, 1
    N, T, C = arms["N"], arms["T"], arms["C"]
    if core_config(T, editor) != core_config(C, editor):
        failures.append("T/C core edit/data configuration differs")
    ncore, tcore = core_config(N, editor), core_config(T, editor)
    for key in ("model_tag", "seed", "hparams_overrides", "dataset_path", "dataset_fallback",
                "dataset_n", "budgets", "sampling", "editor"):
        if ncore.get(key) != tcore.get(key):
            failures.append(f"N/T core config mismatch at {key}")

    if mode == "x3":
        check_new_meta("N", N, N["suffix"], failures, warnings)
    check_new_meta("T", T, T["suffix"], failures, warnings)
    check_new_meta("C", C, C["suffix"], failures, warnings)
    if mode == "x3":
        check_x3_model_parallel("N", N, failures)
        check_x3_model_parallel("T", T, failures)
        check_x3_model_parallel("C", C, failures)
        check_completeness("N", N, N["suffix"], failures)
        if N["suffix"] or T["suffix"] or C["suffix"]:
            check_x3_oom_regression(N, failures)
            check_x3_oom_regression(T, failures)
            check_x3_oom_regression(C, failures)
    check_completeness("T", T, T["suffix"], failures)
    check_completeness("C", C, C["suffix"], failures)
    if _unique_meta(T, "code_sha256") != _unique_meta(C, "code_sha256"):
        failures.append("T/C code hashes differ")
    if ({json.dumps(normalized_runtime_env(m), sort_keys=True) for m in T["metas"]} !=
            {json.dumps(normalized_runtime_env(m), sort_keys=True) for m in C["metas"]}):
        failures.append("T/C runtime environment differs")

    t_sup, c_sup = T["cfg"].get("suppress", {}), C["cfg"].get("suppress", {})
    expected_apply = ["efficacy"] if mode == "x2" else ["efficacy", "para0", "para1"]
    for label, sup in (("T", t_sup), ("C", c_sup)):
        if sup.get("penalty") != 8 or sup.get("scope") != "think" or sup.get("apply_to") != expected_apply:
            failures.append(f"{label}: frozen penalty/scope/apply_to mismatch")
    if t_sup.get("source") != "o_old": failures.append("T source must be o_old")
    if c_sup.get("source") != "placebo" or c_sup.get("placebo_map") != "data/placebo_donors_strong.json":
        failures.append("C must use the frozen strong same-relation donor map")

    case_map = T["cmap"]
    t_targets = {cid: c["o_old"] for cid, c in case_map.items()}
    donors = json.load(open(_abs("data/placebo_donors_strong.json")))
    active_probes = {"efficacy"} if mode == "x2" else {"efficacy", "para0", "para1"}
    check_trace("T", T, active_probes, t_targets, failures)
    check_trace("C", C, active_probes, donors, failures)

    log_audit = check_logs(logs, failures) if mode == "x2" else None
    fresh_n_required = False
    parity_reason = None
    if mode == "x2":
        parity, parity_reason = x2_n_parity(N, T, C)
        if not parity:
            fresh_n_required = True

    # Do not let an unauditable legacy N produce a misleading byte/difference verdict.  Once the
    # predeclared fresh N smoke is run, the same checks execute normally.
    comparable_n = not fresh_n_required
    exact_probes = {"efficacy", "locality"} if mode == "x2" else {"efficacy", "para0", "para1"}
    exact = ({label: compare_b0(N, arm, exact_probes) for label, arm in (("T", T), ("C", C))}
             if comparable_n else {})
    b0_bad = {label: result for label, result in exact.items()
              if result["missing"] or result["different"] or result["compared"] == 0}
    if b0_bad and mode == "x3":
        fresh_n_required = True
        parity_reason = f"existing X3 N fails B0 byte-identity gate: {b0_bad}"
        comparable_n = False
        exact = {}
    else:
        for label, result in b0_bad.items():
            failures.append(f"{label}: B0 is not byte-identical to N or rows are missing: {result}")

    diff_probes = {"efficacy"} if mode == "x2" else {"para0", "para1"}
    b3diff = ({label: b3_output_differences(N, arm, diff_probes) for label, arm in (("T", T), ("C", C))}
              if comparable_n else {"T": [], "C": []})
    if comparable_n and not b3diff["T"]:
        failures.append("T: no B3 output differs from N; suppression may be behaviorally inert/miswired")
    if comparable_n and not b3diff["C"]:
        warnings.append("C: no B3 output differs from N. Processor-call trace proves wiring; this is compatible with an inert control.")

    status = "FAIL" if failures else ("FRESH_N_REQUIRED" if fresh_n_required else "PASS")
    code = 1 if failures else (2 if fresh_n_required else 0)
    return {"status": status, "mode": mode, "failures": failures, "warnings": warnings,
            "fresh_n_required": fresh_n_required, "parity_reason": parity_reason,
            "B0_exact": exact, "B3_different_rows": {k: len(v) for k, v in b3diff.items()},
            "log_audit": log_audit,
            "shards": {k: len(v["shards"]) for k, v in arms.items()},
            "errors": {k: len(v["errors"]) for k, v in arms.items()}}, code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("x2", "x3"))
    ap.add_argument("--arm", action="append", required=True, help="LABEL=config.yaml[@tag_suffix]")
    ap.add_argument("--log", action="append", default=[])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    editor = "MEMIT" if args.mode == "x2" else "ROME"
    arms = {}
    for spec in args.arm:
        label, path, suffix = parse_arm(spec)
        arms[label] = load_arm(path, suffix, editor)
    result, code = validate(args.mode, arms, args.log)
    if args.out:
        out = _abs(args.out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(result, open(out, "w"), ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
