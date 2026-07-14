# -*- coding: utf-8 -*-
"""B15 · es_drop~capability | base_recall(终极review;capability 第二支柱升格闸门)。

问题:base ans_old(知识覆盖)随尺度升(0.515→0.785),与 es_drop slope 同向 → 审稿人可把
"capability-emergent erosion"改读为"知识覆盖涌现"(大模型本就更知 o_old=回退燃料多)。
检验:per-case es_drop ~ log10(params) [+ chain_len] + base_ans_old(该 case 在未编辑基座 B0 答出
o_old 与否;cap3.load_base_clr 从 *_BASE_* 分片读，必须显式选 B0)。主 CI 按 plan v1.69 抽 unique case_id
block，并保留该事实跨全部可用尺度/族的行；旧 family→row 两级 bootstrap 只作 sensitivity。
判读(prereg,跑前钉死):
  控 base_ans_old 后 log_params slope 仍排零且正 → 升格(capability-emergent 编辑特异,非知识覆盖);
  塌向零/含零 → 保守版(scale-consistent trend),contrib-3 用保守措辞。
  分层旁证:base_known(=1)与 base_unknown(=0)子集各自的 slope 同报。
用(平台 CPU;globs 同 percase clean run):
  python src/b15_regress.py --glob ... x6 --base-glob 'results/probe/*_BASE_*.jsonl' --out results/b15.json
"""
import argparse, glob as globlib, json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import percase_emergence as pe
from cap3_netclr import load_base_clr


def input_provenance(edited_audit, base_audit, edited_paths, base_paths):
    """Keep both loader audits while preserving the existing path provenance."""
    return {"edited": edited_audit, "base": base_audit,
            "edited_paths": edited_paths, "base_paths": base_paths,
            "edited_files": [pe.file_record(path) for path in edited_paths],
            "base_files": [pe.file_record(path) for path in base_paths]}

def design(rows, covs):
    """截距+log_params+covs(标准化)+family drop-one 哑变量;返回 X,y,fams。"""
    lp = np.array([r["log_params"] for r in rows], float)
    cols = [np.ones(len(rows)), lp]
    for c in covs:
        v = np.array([float(r[c]) for r in rows], float)
        sd = v.std(); cols.append((v - v.mean()) / sd if sd > 1e-9 else v - v.mean())
    fams = [r["family"] for r in rows]
    for f in sorted(set(fams))[1:]:
        cols.append(np.array([1.0 if g == f else 0.0 for g in fams], float))
    return np.column_stack(cols), np.array([r["es_drop"] for r in rows], float), fams

def two_level_ci(rows, covs, B=10000, seed=42):
    X, y, fams = design(rows, covs)
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    point = float(beta[1])
    byfam = {}
    for i, r in enumerate(rows): byfam.setdefault(r["family"], []).append(r)
    rng = np.random.default_rng(seed); slopes = []
    famk = list(byfam)
    for _ in range(B):
        fs = [famk[i] for i in rng.integers(0, len(famk), len(famk))]
        rs = []
        for f in fs:
            pool = byfam[f]; rs += [pool[j] for j in rng.integers(0, len(pool), len(pool))]
        if len({r["log_params"] for r in rs}) < 2: continue
        try:
            Xb, yb, _ = design(rs, covs)
            slopes.append(float(np.linalg.lstsq(Xb, yb, rcond=None)[0][1]))
        except Exception: continue
    s = np.sort(slopes)
    lo, hi = float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))
    p_le0 = float((s <= 0).mean())
    return {"point": round(point,4), "ci95": [round(lo,4), round(hi,4)],
            "excludes_zero": bool(lo > 0 or hi < 0), "p_slope_le_0": round(p_le0,4),
            "n_rows": len(rows), "n_boot_eff": len(slopes)}


def case_block_ci(rows, covs, B=10000, seed=42):
    """Fact bootstrap conditional on fixed checkpoints; same case_id rows move together."""
    X, y, _ = design(rows, covs)
    point = float(np.linalg.lstsq(X, y, rcond=None)[0][1])
    by_case = {}
    for row in rows:
        by_case.setdefault(row["case_id"], []).append(row)
    case_ids = sorted(by_case)
    rng = np.random.default_rng(seed)
    slopes = []
    m = len(case_ids)
    for _ in range(B):
        rs = []
        for idx in rng.integers(0, m, m):
            rs.extend(by_case[case_ids[idx]])
        if len({row["log_params"] for row in rs}) < 2:
            continue
        try:
            Xb, yb, _ = design(rs, covs)
            slope = float(np.linalg.lstsq(Xb, yb, rcond=None)[0][1])
            if np.isfinite(slope):
                slopes.append(slope)
        except Exception:
            continue
    s = np.sort(np.asarray(slopes, float))
    lo, hi = float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))
    p_le0 = float((s <= 0).mean())
    return {"point": round(point,4), "ci95": [round(lo,4), round(hi,4)],
            "excludes_zero": bool(lo > 0 or hi < 0), "p_slope_le_0": round(p_le0,4),
            "n_rows": len(rows), "n_case_blocks": len(case_ids), "n_boot_eff": len(slopes),
            "bootstrap_unit": "unique case_id; retain all available scale/family rows",
            "inference_scope": "fact-sampling uncertainty conditional on fixed checkpoints"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", action="append", required=True)
    ap.add_argument("--base-glob", action="append", required=True)
    ap.add_argument("--base-budget", default="B0", choices=("B0", "B1", "B2", "B3"),
                    help="budget used to define unedited base_ans_old; B15's frozen estimand is B0")
    ap.add_argument("--cases", default="data/counterfact.jsonl")
    ap.add_argument("--aliases", default="data/aliases.json")
    ap.add_argument("--out", default="results/b15.json")
    ap.add_argument("--boot", type=int, default=10000)
    args = ap.parse_args()
    cases = [json.loads(l) for l in open(args.cases)]
    aliases = json.load(open(args.aliases))
    paths = sorted({p for g in args.glob for p in globlib.glob(g)})
    rows, tags, edited_provenance = pe.load_percase_rows(
        paths, cases, aliases, return_provenance=True)
    base_paths = sorted({p for g in args.base_glob for p in globlib.glob(g)})
    bmap, base_provenance = load_base_clr(
        base_paths, cases, aliases, late=args.base_budget, return_provenance=True)
    matched = []
    for r in rows:
        b = bmap.get((float(r["params_b"]), r["family"], r["case_id"]))
        if b is not None:
            r["base_ans_old"] = b["base_ans_old"]; matched.append(r)
    scales = sorted({(r["params_b"], r["family"]) for r in matched})
    out = {"tags": tags, "n_edited": len(rows), "n_matched": len(matched),
           "base_budget": args.base_budget,
           "base_recall_definition": (
               f"unedited base answer contains o_old at {args.base_budget}; subject-scrubbed metrics.hit"),
           "scales_matched": [f"{f}-{p}B" for p,f in [(a,b) for a,b in scales]],
           "_provenance": input_provenance(
               edited_provenance, base_provenance, paths, base_paths)}
    out["baseline_matched"] = case_block_ci(matched, ["chain_len"], args.boot)
    out["b15_controlled"] = case_block_ci(
        matched, ["chain_len", "base_ans_old"], args.boot, seed=43)
    known = [r for r in matched if r["base_ans_old"] == 1]
    unk   = [r for r in matched if r["base_ans_old"] == 0]
    out["strat_base_known"] = case_block_ci(
        known, ["chain_len"], args.boot, seed=44) if len(known)>50 else {"n_rows": len(known)}
    out["strat_base_unknown"] = case_block_ci(
        unk, ["chain_len"], args.boot, seed=45) if len(unk)>50 else {"n_rows": len(unk)}
    out["_family_row_sensitivity"] = {
        "baseline_matched": two_level_ci(matched, ["chain_len"], args.boot),
        "b15_controlled": two_level_ci(
            matched, ["chain_len", "base_ans_old"], args.boot, seed=43),
        "strat_base_known": two_level_ci(
            known, ["chain_len"], args.boot, seed=44) if len(known)>50 else {"n_rows": len(known)},
        "strat_base_unknown": two_level_ci(
            unk, ["chain_len"], args.boot, seed=45) if len(unk)>50 else {"n_rows": len(unk)},
    }
    c = out["b15_controlled"]
    out["verdict"] = (f"★B15({args.base_budget}) {'PASS:控 base_ans_old 后 es_drop slope 仍排零(' if c['excludes_zero'] and c['point']>0 else 'FAIL/保守:控 base 后 slope 含零('}"
        f"{c['point']} {c['ci95']})→ contrib-3 用{'升格' if c['excludes_zero'] and c['point']>0 else '保守'}版(prereg 两版预写)。")
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(out, open(args.out, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
