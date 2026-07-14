"""X3 active-paraphrase cross-arm analysis (CPU only; prereg-x2-x3.md).

Primary endpoint: (T - C) strict paraphrase success at B3 over para0+para1 rows.
Inference resamples whole ``case_id`` clusters, preserving both paraphrases and their pairing.
The same estimator reports C-N and T-N as non-gating diagnostics.  Only a T-C confidence interval
whose lower bound exceeds zero confirms the primary effect.  In particular, a C-N interval that
contains zero is merely compatible with zero, not evidence of equivalence; equivalence is NOT_TESTED
unless the caller supplies a prospectively chosen margin.  A fixed, pre-treatment secondary gate
consists of paraphrase rows that succeeded in N at B0; on that set we compare committed-old rates at B3.

Day-0 (before T/C GPU runs):
  python src/cross_arm_para.py --day0 --arm N=experiments/probe32b.yaml \
      --audit-out results/x3_para_audit20.json --out results/x3_day0.json

Full analysis:
  python src/cross_arm_para.py \
      --arm N=experiments/probe32b.yaml \
      --arm T=experiments/probe32b_para_sup.yaml \
      --arm C=experiments/probe32b_para_strongcomp.yaml \
      --out results/x3_para_crossarm.json

Optional prospective equivalence audit (never enabled by default):
  ... --equivalence-margin 0.03
"""
import argparse
import glob
import hashlib
import json
import os
import random

import yaml

import metrics


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARA_PROBES = ("para0", "para1")


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_dataset(cfg):
    ds = cfg["dataset"]
    for path in (ds.get("path"), ds.get("fallback_path")):
        if path and os.path.exists(_abs(path)):
            return _abs(path)
    raise FileNotFoundError(f"neither dataset.path nor fallback_path exists: {ds}")


def selected_cases(cfg):
    path = resolve_dataset(cfg)
    rows = [json.loads(line) for line in open(path) if line.strip()]
    random.Random(cfg.get("seed", 42)).shuffle(rows)
    n = cfg["dataset"].get("n")
    return rows[:n] if n else rows


def result_glob(cfg, editor, tag_suffix=""):
    tag = cfg["dataset"]["tag"] + tag_suffix
    return os.path.join(_abs(cfg["out_dir"]), f"{cfg['model_tag']}_{editor}_{tag}_r*.jsonl")


def row_indicators(row, case, aliases):
    ans = metrics._without_subject(row.get("answer", ""), case.get("s") or "")
    hn = bool(metrics.hit(ans, case["o_new"], aliases))
    ho = bool(metrics.hit(ans, case["o_old"], aliases))
    return {"PS": int(hn and not ho), "old_commit": int(ho and not hn),
            "hit_new": int(hn), "hit_old": int(ho)}


def load_arm(config_path, editor="ROME", decode="greedy", tag_suffix="", aliases_path="data/aliases.json"):
    config_path = _abs(config_path)
    cfg = yaml.safe_load(open(config_path))
    cases = selected_cases(cfg)
    cmap = {c["case_id"]: c for c in cases}
    shards = sorted(glob.glob(result_glob(cfg, editor, tag_suffix)))
    if not shards:
        raise FileNotFoundError(f"no result shards: {result_glob(cfg, editor, tag_suffix)}")
    aliases = json.load(open(_abs(aliases_path)))
    rows, metas, errors = {}, [], []
    for shard in shards:
        for lineno, line in enumerate(open(shard), 1):
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("_meta"):
                metas.append(r)
                continue
            if r.get("error"):
                errors.append({"file": shard, "line": lineno, "case_id": r.get("case_id"),
                               "error": r.get("error")})
                continue
            if (r.get("decode", "greedy") != decode or r.get("probe") not in PARA_PROBES
                    or r.get("case_id") not in cmap):
                continue
            key = (r["case_id"], r["budget"], r["probe"])
            if key in rows:
                raise ValueError(f"duplicate paraphrase row {key}; mixed shard worlds/tags? {shard}:{lineno}")
            rows[key] = r
    indicators = {key: row_indicators(row, cmap[key[0]], aliases) for key, row in rows.items()}
    return {"config": config_path, "config_sha256": _sha256(config_path), "cfg": cfg,
            "cases": cases, "cmap": cmap, "shards": shards, "metas": metas,
            "errors": errors, "rows": rows, "indicators": indicators}


def expected_para_keys(arm):
    return {(c["case_id"], f"para{i}") for c in arm["cases"]
            for i, _ in enumerate(c.get("paraphrases", [])[:2])}


def day0_summary(arm, budgets=("B0", "B3")):
    expected = expected_para_keys(arm)
    out = {"selected_cases": len(arm["cases"]), "expected_rows_per_budget": len(expected),
           "shards": len(arm["shards"]), "error_rows": len(arm["errors"]), "budgets": {}}
    for budget in budgets:
        observed = {(cid, probe) for cid, b, probe in arm["indicators"] if b == budget}
        vals = [arm["indicators"][(cid, budget, probe)]["PS"] for cid, probe in sorted(observed)]
        out["budgets"][budget] = {
            "PS": (sum(vals) / len(vals) if vals else None),
            "observed_cases": len({cid for cid, _ in observed}),
            "observed_rows": len(observed),
            "missing_rows": len(expected - observed),
            "missing_rate": (len(expected - observed) / len(expected) if expected else None),
        }
    b0_success = {(cid, probe) for cid, b, probe in arm["indicators"]
                  if b == "B0" and arm["indicators"][(cid, b, probe)]["PS"] == 1}
    out["b0_success_gate"] = {"cases": len({cid for cid, _ in b0_success}),
                              "rows": len(b0_success),
                              "case_gate_rate": len({cid for cid, _ in b0_success}) / max(len(arm["cases"]), 1),
                              "row_gate_rate": len(b0_success) / max(len(expected), 1)}
    return out


def audit_manifest(arm, n=20, seed=42):
    cases = list(arm["cases"])
    chosen = random.Random(seed).sample(cases, min(n, len(cases)))
    records = []
    for c in chosen:
        rec = {"case_id": c["case_id"], "subject": c.get("s"), "rewrite_prompt": c.get("prompt"),
               "o_old": c.get("o_old"), "o_new": c.get("o_new"),
               "paraphrases": c.get("paraphrases", [])[:2], "recorded_questions": {}}
        for budget in ("B0", "B3"):
            rec["recorded_questions"][budget] = {
                probe: arm["rows"].get((c["case_id"], budget, probe), {}).get("q")
                for probe in PARA_PROBES}
        records.append(rec)
    return {"seed": seed, "n": len(records), "instruction":
            "Blindly mark each paraphrase readable/answerable and whether its unrelated prefix changes the requested fact; do not inspect T/C outcomes.",
            "records": records}


def paired_cluster_diff(A, B, metric="PS", budget="B3", allowed_keys=None,
                        n_boot=10000, seed=42, ci=0.95):
    """Paired A-B row difference with whole-case cluster bootstrap.

    Rows are paired by (case_id, para0/para1).  Sampling a case retains all of that case's
    available matched paraphrases; the point estimate is the pooled paired-row mean.
    """
    ka = {(cid, probe) for cid, b, probe in A["indicators"] if b == budget}
    kb = {(cid, probe) for cid, b, probe in B["indicators"] if b == budget}
    keys = ka & kb
    if allowed_keys is not None:
        keys &= set(allowed_keys)
    grouped = {}
    for cid, probe in sorted(keys):
        va = A["indicators"][(cid, budget, probe)][metric]
        vb = B["indicators"][(cid, budget, probe)][metric]
        grouped.setdefault(cid, []).append((va, vb))
    cids = sorted(grouped)
    if not cids:
        return {"n_cases": 0, "n_rows": 0}

    def pooled(sampled):
        pairs = [pair for cid in sampled for pair in grouped[cid]]
        ma = sum(a for a, _ in pairs) / len(pairs)
        mb = sum(b for _, b in pairs) / len(pairs)
        return ma - mb, ma, mb

    point, mean_a, mean_b = pooled(cids)
    rng = random.Random(seed)
    boots = sorted(pooled([cids[rng.randrange(len(cids))] for _ in cids])[0]
                   for _ in range(n_boot))
    lo_q, hi_q = (1 - ci) / 2, (1 + ci) / 2
    lo = boots[int(lo_q * n_boot)]
    hi = boots[min(int(hi_q * n_boot), n_boot - 1)]
    p = min(1.0, 2 * min(sum(x <= 0 for x in boots), sum(x >= 0 for x in boots)) / n_boot)
    return {"n_cases": len(cids), "n_rows": sum(len(grouped[cid]) for cid in cids),
            "mean_A": round(mean_a, 6), "mean_B": round(mean_b, 6),
            "diff_A_minus_B": round(point, 6), "ci": [round(lo, 6), round(hi, 6)],
            "bootstrap_p_two_sided": round(p, 6), "bootstrap_unit": "case_id",
            "paired_unit": "case_id+paraphrase_probe"}


def inference_decisions(contrasts, secondary_gate_cases, equivalence_margin=None,
                        cn_equivalence=None):
    """Separate the sound primary decision from the historical preregistered joint gate.

    ``C-N CI contains zero`` is a compatibility statement only.  If an explicit positive
    ``equivalence_margin`` is supplied, ``cn_equivalence`` must be the independently computed 90%
    case-cluster bootstrap interval used for the usual alpha=.05 TOST CI criterion.  The caller is
    responsible for prospective margin specification; this function never invents a default.
    """
    if equivalence_margin is not None and equivalence_margin <= 0:
        raise ValueError("equivalence_margin must be positive when supplied")

    primary = contrasts["T-C"]
    cn = contrasts["C-N"]
    tn = contrasts["T-N"]
    primary_ci = primary.get("ci")
    cn_ci = cn.get("ci")
    tn_ci = tn.get("ci")
    primary_evaluable = bool(primary_ci and len(primary_ci) == 2)
    primary_pass = bool(primary_evaluable and primary_ci[0] > 0)
    cn_contains_zero = bool(cn_ci and cn_ci[0] <= 0 <= cn_ci[1])
    tn_positive = bool(tn.get("diff_A_minus_B", 0) > 0)

    if equivalence_margin is None:
        equivalence = {
            "status": "NOT_TESTED",
            "margin": None,
            "reason": "no prospectively specified equivalence margin supplied",
        }
    else:
        ci90 = (cn_equivalence or {}).get("ci")
        if not ci90 or len(ci90) != 2:
            equivalence = {
                "status": "NOT_EVALUABLE",
                "margin": float(equivalence_margin),
                "reason": "90% paired case-cluster bootstrap CI unavailable",
            }
        else:
            equivalent = bool(ci90[0] > -equivalence_margin and ci90[1] < equivalence_margin)
            equivalence = {
                "status": "EQUIVALENT" if equivalent else "NOT_ESTABLISHED",
                "passed": equivalent,
                "margin": float(equivalence_margin),
                "ci90": list(ci90),
                "method": "TOST via 90% paired case-cluster bootstrap CI within (-margin,+margin)",
                "admissibility": ("confirmatory only if this margin was prospectively specified; "
                                  "the script does not infer that status"),
            }

    sound = {
        "status": ("PASS" if primary_pass else
                   "FAIL" if primary_evaluable else "NOT_EVALUABLE"),
        "x3_primary_confirmed": primary_pass,
        "confirmatory_endpoint": "T-C strict PS at B3 over paired para0+para1 rows",
        "criterion": "paired case-cluster bootstrap CI lower bound > 0",
        "primary_T_minus_C_ci_lower_gt_zero": primary_pass,
        "C_minus_N": {
            "role": "non_gating_diagnostic",
            "ci_contains_zero": cn_contains_zero,
            "compatibility_status": ("COMPATIBLE_WITH_ZERO" if cn_contains_zero else
                                     "NOT_COMPATIBLE_WITH_ZERO" if cn_ci else "NOT_EVALUABLE"),
            "equivalence": equivalence,
            "warning": "CI inclusion of zero is not an equivalence test or a pass condition",
        },
        "T_minus_N": {
            "role": "non_gating_descriptive_contrast",
            "point_estimate_positive": tn_positive,
            "ci_excludes_zero": bool(tn_ci and (tn_ci[0] > 0 or tn_ci[1] < 0)),
            "warning": "neither the point estimate nor this contrast gates the primary claim",
        },
        "secondary_gate_cases": secondary_gate_cases,
        "secondary_status": ("confirmatory" if secondary_gate_cases >= 140
                             else "directional_low_gate_n"),
    }

    # Preserve the originally implemented joint rule byte-for-byte in meaning, but quarantine it
    # as historical audit: C-N zero compatibility is not equivalence, and T-N positivity is not a
    # significance criterion.  No scientific claim should read this field as the current decision.
    historical = {
        "_role": "HISTORICAL_PREREGISTERED_GATE_AUDIT_ONLY",
        "_warning": ("This legacy joint gate is retained for reproducibility, not sound inference. "
                     "Use decision.x3_primary_confirmed."),
        "primary_T_minus_C_ci_gt_zero": primary_pass,
        "C_minus_N_ci_contains_zero": cn_contains_zero,
        "T_minus_N_positive": tn_positive,
        "secondary_gate_cases": secondary_gate_cases,
        "secondary_status": ("confirmatory" if secondary_gate_cases >= 140
                             else "directional_low_gate_n"),
    }
    historical["x3_primary_pass"] = all((
        historical["primary_T_minus_C_ci_gt_zero"],
        historical["C_minus_N_ci_contains_zero"],
        historical["T_minus_N_positive"],
    ))
    return sound, historical


def analyze(arms, budget="B3", n_boot=10000, seed=42, equivalence_margin=None):
    for label in ("N", "T", "C"):
        if label not in arms:
            raise ValueError("full X3 analysis requires N, T, and C arms")
    contrasts = {}
    for a, b in (("T", "C"), ("C", "N"), ("T", "N")):
        contrasts[f"{a}-{b}"] = paired_cluster_diff(
            arms[a], arms[b], metric="PS", budget=budget, n_boot=n_boot, seed=seed)

    gate = {(cid, probe) for cid, b, probe in arms["N"]["indicators"]
            if b == "B0" and arms["N"]["indicators"][(cid, b, probe)]["PS"] == 1}
    committed = {}
    for a, b in (("T", "C"), ("C", "N"), ("T", "N")):
        committed[f"{a}-{b}"] = paired_cluster_diff(
            arms[a], arms[b], metric="old_commit", budget=budget, allowed_keys=gate,
            n_boot=n_boot, seed=seed)

    cn_equivalence = None
    if equivalence_margin is not None:
        if equivalence_margin <= 0:
            raise ValueError("equivalence_margin must be positive when supplied")
        cn_equivalence = paired_cluster_diff(
            arms["C"], arms["N"], metric="PS", budget=budget,
            n_boot=n_boot, seed=seed, ci=0.90)
    gate_cases = len({cid for cid, _ in gate})
    decision, historical_gate = inference_decisions(
        contrasts, gate_cases, equivalence_margin=equivalence_margin,
        cn_equivalence=cn_equivalence)
    return {"endpoint": "strict PS on para0+para1", "budget": budget,
            "n_boot": n_boot, "seed": seed, "contrasts": contrasts,
            "N_B0_success_gate": {"cases": gate_cases, "rows": len(gate)},
            "committed_old_on_fixed_N_B0_gate": committed,
            "decision": decision,
            "historical_preregistered_gate": historical_gate,
            "arm_sources": {k: {"config": v["config"], "config_sha256": v["config_sha256"],
                                "shards": len(v["shards"]), "errors": len(v["errors"])}
                            for k, v in arms.items()}}


def _parse_arms(specs, editor, decode, aliases_path):
    arms = {}
    for spec in specs:
        label, sep, path = spec.partition("=")
        if not sep or not label or not path:
            raise ValueError(f"bad --arm {spec!r}; expected LABEL=config.yaml")
        arms[label] = load_arm(path, editor=editor, decode=decode, aliases_path=aliases_path)
    return arms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", action="append", required=True, help="LABEL=config.yaml; repeat for N/T/C")
    ap.add_argument("--editor", default="ROME")
    ap.add_argument("--decode", default="greedy")
    ap.add_argument("--budget", default="B3")
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--equivalence-margin", type=float, default=None,
                    help=("Optional prospectively specified absolute C-N PS margin for TOST; "
                          "omitted means equivalence NOT_TESTED. Never choose post hoc."))
    ap.add_argument("--aliases", default="data/aliases.json")
    ap.add_argument("--day0", action="store_true")
    ap.add_argument("--audit-out", default=None)
    ap.add_argument("--audit-n", type=int, default=20)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    arms = _parse_arms(args.arm, args.editor, args.decode, args.aliases)
    if args.day0:
        if "N" not in arms:
            raise SystemExit("--day0 requires --arm N=...")
        result = {"day0": day0_summary(arms["N"]),
                  "source": {"config": arms["N"]["config"],
                             "config_sha256": arms["N"]["config_sha256"]}}
        if args.audit_out:
            manifest = audit_manifest(arms["N"], n=args.audit_n, seed=args.seed)
            os.makedirs(os.path.dirname(_abs(args.audit_out)), exist_ok=True)
            json.dump(manifest, open(_abs(args.audit_out), "w"), ensure_ascii=False, indent=2)
            result["audit_manifest"] = _abs(args.audit_out)
    else:
        result = analyze(arms, budget=args.budget, n_boot=args.boot, seed=args.seed,
                         equivalence_margin=args.equivalence_margin)

    if args.out:
        os.makedirs(os.path.dirname(_abs(args.out)), exist_ok=True)
        json.dump(result, open(_abs(args.out), "w"), ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
