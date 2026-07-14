"""Validate CPU closeout artifacts without recomputing any statistic.

This is a schema/inference-discipline gate.  It verifies that the upstream CPU
artifacts used case-block sampling where required, exposed duplicate-world
audits, paired F3 rows by the same sampling seed, and kept X3 zero-compatibility
separate from equivalence.  Cap3 is also fail-closed on case-block primary
intervals and duplicate audits for both edited and base worlds.  It never reads
model weights or changes estimates.
"""
import argparse
import hashlib
import json
import os


DEFAULTS = {
    "percase": "results/percase_caseblock.json",
    "b15": "results/b15_caseblock.json",
    "cap3": "results/cap3_caseblock.json",
    "f3": "results/f3_sampling_recalc.json",
    "x2": "results/x2_memit14b_crossarm_v2.json",
    "x3": "results/x3_para_crossarm_v2.json",
    "p0": "results/p0_downstream_crosswalk.json",
}


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_required(name, path, failures, artifacts):
    if not path or not os.path.exists(path):
        failures.append(f"{name}: missing required artifact: {path}")
        return None
    try:
        with open(path, encoding="utf-8") as f:
            value = json.load(f)
    except Exception as exc:
        failures.append(f"{name}: invalid JSON at {path}: {exc}")
        return None
    if not isinstance(value, dict):
        failures.append(f"{name}: top-level JSON must be an object: {path}")
        return None
    artifacts[name] = {"path": path, "sha256": _sha256(path)}
    return value


def _duplicate_audit(audit, label, failures):
    if not isinstance(audit, dict):
        failures.append(f"{label}: missing duplicate audit object")
        return None
    if audit.get("status") != "PASS":
        failures.append(f"{label}: duplicate audit status is {audit.get('status')!r}, expected 'PASS'")
    keys = audit.get("duplicate_keys")
    if not isinstance(keys, list):
        failures.append(f"{label}: duplicate_keys must be a list")
        keys = []
    n_keys = audit.get("n_duplicate_keys")
    if n_keys != len(keys):
        failures.append(f"{label}: n_duplicate_keys={n_keys!r} but duplicate_keys has {len(keys)} rows")
    n_dedup = audit.get("n_duplicate_rows_deduplicated")
    if not isinstance(n_dedup, int) or n_dedup < 0:
        failures.append(f"{label}: invalid n_duplicate_rows_deduplicated={n_dedup!r}")
    for idx, item in enumerate(keys):
        sources = item.get("sources") if isinstance(item, dict) else None
        if not isinstance(sources, list) or len(sources) < 2:
            failures.append(f"{label}: duplicate_keys[{idx}] must report at least two sources")
            continue
        for source in sources:
            if not source.get("path") or not isinstance(source.get("line"), int):
                failures.append(f"{label}: duplicate_keys[{idx}] has invalid path:line source {source!r}")
    return {"status": audit.get("status"), "duplicate_keys": len(keys),
            "duplicate_rows_deduplicated": n_dedup}


def _case_block_metric(block, label, expected_scope, failures):
    if not isinstance(block, dict):
        failures.append(f"{label}: missing metric block")
        return None
    expected_unit = "unique case_id; retain all available scale/family rows"
    if block.get("bootstrap_unit") != expected_unit:
        failures.append(
            f"{label}: bootstrap_unit={block.get('bootstrap_unit')!r}, expected {expected_unit!r}")
    scope = block.get("inference_scope")
    if scope != expected_scope:
        failures.append(f"{label}: inference_scope={scope!r}, expected {expected_scope!r}")
    n_rows, n_cases = block.get("n_rows"), block.get("n_case_blocks")
    if not isinstance(n_rows, int) or n_rows <= 0:
        failures.append(f"{label}: invalid n_rows={n_rows!r}")
    if not isinstance(n_cases, int) or n_cases <= 0:
        failures.append(f"{label}: invalid n_case_blocks={n_cases!r}")
    elif isinstance(n_rows, int) and n_cases > n_rows:
        failures.append(f"{label}: n_case_blocks={n_cases} exceeds n_rows={n_rows}")
    return {"point": block.get("point"), "ci95": block.get("ci95"),
            "n_rows": n_rows, "n_case_blocks": n_cases}


def _validate_percase(value, failures, warnings):
    summary = {}
    config = value.get("_config") or {}
    scales = config.get("scales_detected")
    if not isinstance(scales, dict) or len(scales) != 6:
        failures.append(f"percase: expected six fixed checkpoints, found {len(scales) if isinstance(scales, dict) else scales!r}")
    audit = ((value.get("_provenance") or {}).get("duplicate_world_audit"))
    summary["duplicate_audit"] = _duplicate_audit(audit, "percase._provenance", failures)
    scope = "fact-sampling uncertainty conditional on six fixed checkpoints"
    summary["metrics"] = {}
    for metric in ("es_drop", "rr", "clr", "clr_density", "clr_rev"):
        summary["metrics"][metric] = _case_block_metric(
            value.get(metric), f"percase.{metric}", scope, failures)
    summary["n_rows_total"] = config.get("n_rows_total")
    summary["n_checkpoints"] = len(scales) if isinstance(scales, dict) else None
    return summary


def _validate_b15(value, failures, warnings):
    summary = {"duplicate_audits": {}}
    scales = value.get("scales_matched")
    if not isinstance(scales, list) or len(scales) != 5:
        failures.append(f"b15: expected historical five matched checkpoints, found {scales!r}")
    provenance = value.get("_provenance") or {}
    for source in ("edited", "base"):
        audit = ((provenance.get(source) or {}).get("duplicate_world_audit"))
        summary["duplicate_audits"][source] = _duplicate_audit(
            audit, f"b15._provenance.{source}", failures)

    base_budget = value.get("base_budget")
    selected = (((provenance.get("base") or {}).get("duplicate_world_audit") or {})
                .get("selected") or {})
    selected_budget = selected.get("budget")
    if base_budget != "B0":
        failures.append(
            f"b15.base_budget={base_budget!r}; frozen knowledge-coverage control requires 'B0'")
    if selected_budget != "B0":
        failures.append(
            "b15._provenance.base.duplicate_world_audit.selected.budget="
            f"{selected_budget!r}; expected 'B0'")
    summary["base_budget"] = base_budget
    scope = "fact-sampling uncertainty conditional on fixed checkpoints"
    summary["metrics"] = {}
    for metric in ("baseline_matched", "b15_controlled"):
        summary["metrics"][metric] = _case_block_metric(
            value.get(metric), f"b15.{metric}", scope, failures)
    for metric in ("strat_base_known", "strat_base_unknown"):
        block = value.get(metric)
        if isinstance(block, dict) and "bootstrap_unit" in block:
            summary["metrics"][metric] = _case_block_metric(
                block, f"b15.{metric}", scope, failures)
        else:
            warnings.append(f"b15.{metric}: no powered case-block interval; n_rows={block.get('n_rows') if isinstance(block, dict) else None}")
    summary["n_matched"] = value.get("n_matched")
    summary["n_checkpoints"] = len(scales) if isinstance(scales, list) else None
    return summary


def _validate_cap3(value, failures, warnings):
    """Validate the base-deconfounded CLR analysis without interpreting its result."""
    summary = {"duplicate_audits": {}, "metrics": {}}
    provenance = value.get("_provenance") or {}
    for source in ("edited", "base"):
        audit = ((provenance.get(source) or {}).get("duplicate_world_audit"))
        summary["duplicate_audits"][source] = _duplicate_audit(
            audit, f"cap3._provenance.{source}", failures)

    per_scale = value.get("_per_scale")
    if not isinstance(per_scale, dict) or len(per_scale) != 5:
        failures.append(
            "cap3._per_scale: expected five matched fixed checkpoints "
            f"(7B base intentionally excluded), found "
            f"{len(per_scale) if isinstance(per_scale, dict) else per_scale!r}")
    summary["n_matched_checkpoints"] = len(per_scale) if isinstance(per_scale, dict) else None

    scope = "fact-sampling uncertainty conditional on five matched fixed checkpoints"
    for metric in ("net_clr", "clr_on_baseCLR0", "clr_raw_matched"):
        summary["metrics"][metric] = _case_block_metric(
            value.get(metric), f"cap3.{metric}", scope, failures)

    sensitivity = value.get("_family_row_sensitivity")
    if not isinstance(sensitivity, dict):
        failures.append("cap3._family_row_sensitivity: missing sensitivity-only block")
        sensitivity = {}
    missing_sensitivity = [name for name in
                           ("net_clr", "clr_on_baseCLR0", "clr_raw_matched")
                           if name not in sensitivity]
    if missing_sensitivity:
        failures.append(
            "cap3._family_row_sensitivity: missing metrics "
            f"{missing_sensitivity}; primary metrics must remain top-level case-block intervals")

    inference_scope = value.get("_inference_scope")
    required_scope_fragments = (
        "primary intervals resample unique case_id blocks",
        "conditional on the five matched observed checkpoints",
    )
    if (not isinstance(inference_scope, str) or
            any(fragment not in inference_scope for fragment in required_scope_fragments)):
        failures.append(
            "cap3._inference_scope must state that primary intervals resample unique case_id "
            "blocks and are conditional on the five matched observed checkpoints")
    summary["inference_scope"] = inference_scope
    summary["family_row_sensitivity_role"] = "SENSITIVITY_ONLY"
    return summary


def _validate_f3(value, failures, warnings):
    status = value.get("status")
    if not isinstance(status, str) or not status.startswith("PASS"):
        failures.append(f"f3: upstream status is {status!r}, expected PASS*")
    elif status != "PASS":
        warnings.append(f"f3: upstream status is {status}; primary complete-case estimand remains authoritative")
    protocol = value.get("protocol") or {}
    expected = {
        "decode": "sample",
        "probe": "efficacy",
        "pair_key": ["case_id", "seed", "budget"],
        "sample_seed_field": "seed",
        "b0_gate": "same case_id and same seed",
        "case_aggregation": "mean over paired seeds",
        "bootstrap_unit": "unique case_id",
    }
    for key, wanted in expected.items():
        if protocol.get(key) != wanted:
            failures.append(f"f3.protocol.{key}={protocol.get(key)!r}, expected {wanted!r}")
    audit = value.get("audit") or {}
    duplicate_keys = audit.get("duplicate_keys")
    if duplicate_keys != []:
        failures.append(f"f3.audit: duplicate_keys must be empty, got {duplicate_keys!r}")
    for key in ("unexpected_case_rows", "unexpected_seed_rows"):
        if audit.get(key) not in ([], None):
            failures.append(f"f3.audit: {key} must be empty, got {audit.get(key)!r}")
    seeds = audit.get("expected_seeds")
    if not isinstance(seeds, list) or not seeds or len(seeds) != len(set(seeds)):
        failures.append(f"f3.audit: expected_seeds must be a non-empty unique list, got {seeds!r}")
    primary = value.get("primary_complete_cases") or {}
    n_cases, n_pairs = primary.get("n_cases"), primary.get("n_seed_pairs")
    if not isinstance(n_cases, int) or n_cases <= 0:
        failures.append(f"f3.primary_complete_cases: invalid n_cases={n_cases!r}")
    if isinstance(n_cases, int) and isinstance(seeds, list) and n_pairs != n_cases * len(seeds):
        failures.append(
            f"f3.primary_complete_cases: n_seed_pairs={n_pairs!r}, expected n_cases*seeds={n_cases * len(seeds)}")
    if audit.get("missing_pairs"):
        warnings.append(f"f3: {len(audit['missing_pairs'])} case/seed pairs are incomplete and excluded from the primary complete-case estimand")
    if audit.get("error_rows"):
        warnings.append(f"f3: {len(audit['error_rows'])} error rows recorded upstream")
    return {"status": status, "expected_seeds": seeds, "n_cases": n_cases,
            "n_seed_pairs": n_pairs, "missing_pairs": len(audit.get("missing_pairs") or [])}


def _validate_x2(value, failures, warnings):
    audits = value.get("input_duplicate_audit")
    if not isinstance(audits, dict):
        failures.append("x2: missing input_duplicate_audit")
        audits = {}
    missing_arms = [arm for arm in ("N", "T", "C") if arm not in audits]
    if missing_arms:
        failures.append(f"x2: duplicate audits missing arms {missing_arms}")
    audit_summary = {}
    for arm in ("N", "T", "C"):
        if arm in audits:
            audit_summary[arm] = _duplicate_audit(audits[arm], f"x2.input_duplicate_audit.{arm}", failures)
            key = audits[arm].get("world_key")
            for field in ("case_id", "budget", "decode", "seed"):
                if not isinstance(key, list) or field not in key:
                    failures.append(f"x2.{arm}: world_key must distinguish {field}; got {key!r}")
    arms_n = value.get("arms_n") or {}
    for arm in ("N", "T", "C"):
        if not isinstance(arms_n.get(arm), int) or arms_n[arm] <= 0:
            failures.append(f"x2: invalid arms_n[{arm}]={arms_n.get(arm)!r}")
    tc = (((value.get("contrasts") or {}).get("T-C") or {}).get("ES") or {})
    return {"arms_n": {arm: arms_n.get(arm) for arm in ("N", "T", "C")},
            "duplicate_audits": audit_summary,
            "T_minus_C_ES": {key: tc.get(key) for key in ("n", "mean", "ci", "p")}}


def _validate_x3(value, failures, warnings):
    contrasts = value.get("contrasts") or {}
    for key in ("T-C", "C-N", "T-N"):
        block = contrasts.get(key)
        if not isinstance(block, dict) or block.get("bootstrap_unit") != "case_id":
            failures.append(f"x3.{key}: missing case_id-clustered contrast")
        elif block.get("paired_unit") != "case_id+paraphrase_probe":
            failures.append(f"x3.{key}: paired_unit={block.get('paired_unit')!r}")
    tc = contrasts.get("T-C") or {}
    ci = tc.get("ci")
    primary_evaluable = isinstance(ci, list) and len(ci) == 2
    derived_pass = bool(primary_evaluable and ci[0] > 0)
    decision = value.get("decision")
    if not isinstance(decision, dict):
        failures.append("x3: missing sound decision object")
        decision = {}
    expected_status = "PASS" if derived_pass else "FAIL" if primary_evaluable else "NOT_EVALUABLE"
    if decision.get("status") != expected_status:
        failures.append(f"x3.decision.status={decision.get('status')!r}, derived {expected_status!r} from T-C CI")
    if decision.get("x3_primary_confirmed") is not derived_pass:
        failures.append("x3.decision.x3_primary_confirmed disagrees with T-C CI lower-bound criterion")
    if decision.get("criterion") != "paired case-cluster bootstrap CI lower bound > 0":
        failures.append(f"x3.decision: unsound/missing primary criterion {decision.get('criterion')!r}")
    cn = decision.get("C_minus_N") or {}
    if cn.get("role") != "non_gating_diagnostic":
        failures.append(f"x3.decision.C_minus_N.role={cn.get('role')!r}, expected non_gating_diagnostic")
    equivalence = cn.get("equivalence") or {}
    if equivalence.get("status") != "NOT_TESTED" or equivalence.get("margin") is not None:
        failures.append(
            "x3: equivalence was certified/evaluated without the closeout's prospectively supplied margin; "
            f"got {equivalence!r}")
    historical = value.get("historical_preregistered_gate") or {}
    if historical.get("_role") != "HISTORICAL_PREREGISTERED_GATE_AUDIT_ONLY":
        failures.append("x3: historical joint gate is not quarantined as audit-only")
    if decision.get("status") == "FAIL":
        warnings.append("x3: sound primary decision is FAIL; validator passes inference hygiene, not the scientific endpoint")
    return {"decision_status": decision.get("status"),
            "primary_confirmed": decision.get("x3_primary_confirmed"),
            "T_minus_C": {key: tc.get(key) for key in
                           ("n_cases", "n_rows", "diff_A_minus_B", "ci", "bootstrap_p_two_sided")},
            "C_minus_N_equivalence": equivalence}


def _validate_p0(path, failures, warnings, artifacts):
    if not path:
        return {"status": "NOT_REQUESTED"}
    if not os.path.exists(path):
        warnings.append(f"p0: optional artifact not found: {path}")
        return {"status": "MISSING_OPTIONAL", "path": path}
    try:
        with open(path, encoding="utf-8") as f:
            value = json.load(f)
    except Exception as exc:
        failures.append(f"p0: invalid optional JSON at {path}: {exc}")
        return {"status": "INVALID"}
    artifacts["p0"] = {"path": path, "sha256": _sha256(path)}
    if value.get("technical_status") != "PASS":
        failures.append(f"p0: technical_status={value.get('technical_status')!r}")
    status = value.get("status")
    if status not in ("PASS", "PASS_WITH_BLOCKED_COMPONENT"):
        failures.append(f"p0: status={status!r}")
    logitlens = (value.get("logitlens") or {}).get("status")
    if status == "PASS_WITH_BLOCKED_COMPONENT":
        warnings.append(f"p0: optional downstream crosswalk remains {logitlens}")
    return {"status": status, "logitlens": logitlens,
            "official_x1_gate": value.get("official_x1_gate")}


def validate_paths(paths):
    failures, warnings, artifacts = [], [], {}
    summary = {}
    percase = _read_required("percase", paths["percase"], failures, artifacts)
    b15 = _read_required("b15", paths["b15"], failures, artifacts)
    cap3 = _read_required("cap3", paths["cap3"], failures, artifacts)
    f3 = _read_required("f3", paths["f3"], failures, artifacts)
    x2 = _read_required("x2", paths["x2"], failures, artifacts)
    x3 = _read_required("x3", paths["x3"], failures, artifacts)
    if percase is not None:
        summary["percase"] = _validate_percase(percase, failures, warnings)
    if b15 is not None:
        summary["b15"] = _validate_b15(b15, failures, warnings)
    if cap3 is not None:
        summary["cap3"] = _validate_cap3(cap3, failures, warnings)
    if f3 is not None:
        summary["f3"] = _validate_f3(f3, failures, warnings)
    if x2 is not None:
        summary["x2"] = _validate_x2(x2, failures, warnings)
    if x3 is not None:
        summary["x3"] = _validate_x3(x3, failures, warnings)
    summary["p0"] = _validate_p0(paths.get("p0"), failures, warnings, artifacts)
    return {"status": "PASS" if not failures else "FAIL",
            "failures": failures, "warnings": warnings,
            "artifacts": artifacts, "summary": summary}


def main(argv=None):
    ap = argparse.ArgumentParser()
    for name, default in DEFAULTS.items():
        ap.add_argument(f"--{name}", default=default,
                        help=("optional; pass an empty string to skip" if name == "p0" else None))
    ap.add_argument("--out", default="results/cpu_closeout_audit.json")
    args = ap.parse_args(argv)
    paths = {name: getattr(args, name) for name in DEFAULTS}
    report = validate_paths(paths)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
