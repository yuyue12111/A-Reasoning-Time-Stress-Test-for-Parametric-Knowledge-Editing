"""E-SUP-BATTERY/W1 · 跨臂配对差 bootstrap(headline 因果统计)。

`metrics`/`score_pilot` 只算组内速率;本模块做**组间、按 case_id 配对**的差 + CI —— 这才是 W1 对照的载重统计。
四臂(同 case_id 集、同 decode、scope=think、|α|=8,仅 suppress.source 不同):
  N=不压 / T=压 o_old(现 fix) / D=压 o_new(方向对照) / P=压 placebo(特异性对照)
预注册符号阶梯(B3,ES/ES升高、RR/CLR 下降方向):**D < N ~ P < T**(ES@B3);效应主报 **T−P(o_old 超 placebo 的 margin)**,非 T−N(o_old-vs-零)。

用法(打分后,纯 CPU):
  python src/cross_arm.py --budget B3 --editor ROME \
     --arm N=experiments/probe32b.yaml --arm T=experiments/probe32b_sup.yaml \
     --arm D=experiments/probe32b_sup_onew.yaml --arm P=experiments/probe32b_sup_placebo.yaml
"""
import argparse, glob, json, os, random
import yaml
import metrics

METRICS = ["ES", "RR", "RRs", "CLR"]


def _load_efficacy_worlds(paths, cases, decode="greedy", seed=None):
    """Load unique efficacy generation worlds with strict duplicate provenance.

    A scientific world is keyed by case/budget/probe plus the generation trajectory
    (decode, seed, temperature).  The trajectory fields are required here because
    different sampling seeds are legitimate independent generations, not duplicate
    shards.  Repeated copies of the same complete world are accepted only when the
    entire parsed JSON object is equal; any field drift is a hard failure that names
    both source locations.
    """
    seen = {}
    for path in paths:
        with open(path) as fh:
            for line_no, line in enumerate(fh, 1):
                raw_line = line.rstrip("\r\n")
                if not raw_line.strip():
                    continue
                d = json.loads(line)
                if d.get("_meta") or d.get("error") or d.get("probe") != "efficacy":
                    continue
                row_decode = d.get("decode", "greedy")
                if row_decode != decode or d.get("case_id") not in cases:
                    continue
                if seed is not None and d.get("seed") != seed:
                    continue
                trajectory = (row_decode, d.get("seed"), d.get("temperature"))
                world_key = (d["case_id"], d.get("budget"), d.get("probe"), *trajectory)
                source = {"path": path, "line": line_no}
                prior = seen.get(world_key)
                if prior is not None:
                    if d != prior["row"]:
                        sentinel = object()
                        fields = sorted(set(prior["row"]) | set(d))
                        changed = [field for field in fields
                                   if prior["row"].get(field, sentinel) != d.get(field, sentinel)]
                        first = prior["sources"][0]
                        raise ValueError(
                            "conflicting duplicate world "
                            f"(case_id={d['case_id']}, budget={d.get('budget')}, "
                            f"decode={row_decode}, seed={d.get('seed')}, "
                            f"temperature={d.get('temperature')}): "
                            f"differing_fields={changed}; first={first['path']}:{first['line']}; "
                            f"duplicate={path}:{line_no}")
                    equivalence = ("byte_identical" if raw_line == prior["raw_line"]
                                   else "normalized_json_equal")
                    prior["sources"].append({**source, "equivalence_to_first": equivalence})
                    prior[f"{equivalence}_duplicates"] += 1
                    continue
                seen[world_key] = {
                    "row": d,
                    "raw_line": raw_line,
                    "trajectory": trajectory,
                    "sources": [{**source, "equivalence_to_first": "first"}],
                    "byte_identical_duplicates": 0,
                    "normalized_json_equal_duplicates": 0,
                }

    duplicates = []
    for world_key, entry in sorted(seen.items(), key=lambda kv: repr(kv[0])):
        if len(entry["sources"]) <= 1:
            continue
        cid, budget, probe, row_decode, row_seed, temperature = world_key
        duplicates.append({
            "case_id": cid,
            "budget": budget,
            "probe": probe,
            "decode": row_decode,
            "seed": row_seed,
            "temperature": temperature,
            "copies_total": len(entry["sources"]),
            "byte_identical_duplicates": entry["byte_identical_duplicates"],
            "normalized_json_equal_duplicates": entry["normalized_json_equal_duplicates"],
            "sources": entry["sources"],
        })
    audit = {
        "status": "PASS",
        "world_key": ["case_id", "budget", "probe", "decode", "seed", "temperature"],
        "n_unique_worlds": len(seen),
        "n_duplicate_keys": len(duplicates),
        "n_duplicate_rows_deduplicated": sum(item["copies_total"] - 1 for item in duplicates),
        "duplicate_keys": duplicates,
    }
    return list(seen.values()), audit


def per_case(cfg, editor, budget, decode="greedy", seed=None, return_audit=False):
    """{case_id: {ES,RR,RRs,CLR}} on efficacy/greedy。**口径严格同 metrics.score**:
    _without_subject 挖主体复述(去污)+ RR/RRs 仅在 b0ok(B0 编辑成功)case 上有值(否则 None,不入分母);
    ES/CLR 在全 case 上。→ 边际数与 score_pilot 一致、跨臂配对差在 paper 口径。

    同一完整 generation world 的等价分片副本会去重并进入 audit；冲突副本 hard fail。
    sampling 必须用 seed 明确选择一条合法轨迹；不再把多 seed 静默压成一个 case。"""
    ds = cfg["dataset"]
    pat = os.path.join(cfg["out_dir"], f"{cfg['model_tag']}_{editor}_{ds['tag']}_r*.jsonl")
    cases = {c["case_id"]: c for c in (json.loads(l) for l in open(ds.get("fallback_path", ds["path"])))}
    aliases = json.load(open("data/aliases.json"))
    entries, audit = _load_efficacy_worlds(
        sorted(glob.glob(pat)), cases, decode=decode, seed=seed)
    by_trajectory = {}                               # cid -> trajectory -> budget -> (row, source)
    for entry in entries:
        d = entry["row"]
        by_trajectory.setdefault(d["case_id"], {}).setdefault(entry["trajectory"], {})[
            d.get("budget")] = (d, entry["sources"][0])
    out = {}
    for cid, trajectories in by_trajectory.items():
        target = [(trajectory, buds) for trajectory, buds in trajectories.items()
                  if budget in buds]
        if not target:
            continue
        if len(target) > 1:
            locs = [f"{buds[budget][1]['path']}:{buds[budget][1]['line']}"
                    for _trajectory, buds in target]
            raise ValueError(
                f"multiple independent trajectories for case_id={cid}, budget={budget}, "
                f"decode={decode}; select one with seed=...; sources={locs}")
        _trajectory, buds = target[0]
        c = cases[cid]
        s, o_old, o_new = c.get("s") or "", c["o_old"], c["o_new"]
        clean = lambda t: metrics._without_subject(t or "", s)        # 去主体复述(同 metrics.score line140)
        target_row = buds[budget][0]
        ans, cot = clean(target_row.get("answer")), clean(target_row.get("cot"))
        ho, hn = bool(metrics.hit(ans, o_old, aliases)), bool(metrics.hit(ans, o_new, aliases))
        rec = {"ES": int(hn and not ho), "CLR": int(bool(metrics.hit(cot, o_old, aliases)))}
        b0_entry = buds.get("B0")                                   # 同一 decode/seed/temp 轨迹的 B0 门
        b0 = b0_entry[0] if b0_entry else None
        b0ok = bool(b0) and metrics.hit(clean(b0.get("answer")), o_new, aliases) \
            and not metrics.hit(clean(b0.get("answer")), o_old, aliases)
        rec["RR"] = int(ho) if b0ok else None                        # RR/RRs 仅 b0ok case 有值(同 metrics rr_n 门)
        rec["RRs"] = int(ho and not hn) if b0ok else None
        out[cid] = rec
    return (out, audit) if return_audit else out


def marginal(A):
    out = {}
    for m in METRICS:
        vals = [v[m] for v in A.values() if v.get(m) is not None]
        out[m] = round(sum(vals) / len(vals), 4) if vals else None
    return out


def paired_diff(A, B, metric, B_=10000, seed=42):
    """按 case_id 配对的 (armA - armB) 均差 + 95% bootstrap CI + 双侧 p(重采样 case)。None(如非 b0ok 的 RR)跳过。"""
    ids = [i for i in sorted(set(A) & set(B)) if A[i].get(metric) is not None and B[i].get(metric) is not None]
    if not ids:
        return {"n": 0}
    diffs = [A[i][metric] - B[i][metric] for i in ids]
    n = len(diffs)
    mean = sum(diffs) / n
    rng = random.Random(seed)
    boots = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(B_))
    lo, hi = boots[int(0.025 * B_)], boots[int(0.975 * B_)]
    p = 2 * min(sum(b <= 0 for b in boots), sum(b >= 0 for b in boots)) / B_
    return {"n": n, "mean": round(mean, 4), "ci": [round(lo, 4), round(hi, 4)], "p": round(min(p, 1.0), 4)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", action="append", required=True, help="label=config.yaml(可多次)")
    ap.add_argument("--editor", default="ROME")
    ap.add_argument("--budget", default="B3")
    ap.add_argument("--decode", default="greedy")
    ap.add_argument("--seed", type=int, default=None,
                    help="sampling decode 时选择单一 seed；避免把多条合法轨迹当重复或静默覆盖")
    ap.add_argument("--out", default=None, help="可选:汇总 json 落盘")
    args = ap.parse_args()

    arms = {}; input_audits = {}
    for spec in args.arm:
        label, _, path = spec.partition("=")
        arms[label], input_audits[label] = per_case(
            yaml.safe_load(open(path)), args.editor, args.budget, args.decode,
            seed=args.seed, return_audit=True)
    print(f"# 跨臂配对差 @ {args.budget} {args.decode}  臂={list(arms)}  各 n={{ {', '.join(f'{k}:{len(v)}' for k,v in arms.items())} }}")
    print(f"\n# 各臂边际速率:")
    print(f"{'arm':<6}" + "".join(f"{m:>9}" for m in METRICS))
    for k, v in arms.items():
        mg = marginal(v)
        print(f"{k:<6}" + "".join(f"{(mg.get(m) if mg.get(m) is not None else float('nan')):>9.3f}" for m in METRICS))

    # 预注册关键对照(存在的臂才算)
    contrasts = [("T", "N", "fix 效应(o_old-vs-零,非主报)"), ("T", "P", "★o_old 超 placebo 的 margin(主报特异性)"),
                 ("D", "N", "★方向臂(压 o_new;符号错=近致命)"), ("P", "N", "placebo floor(链扰动,期望≈0)"),
                 ("C", "N", "强竞争者 floor(同 relation 强错答;M4,期望≈0=非通用)"),
                 ("T", "C", "★o_old 超强竞争者 margin(M4 最强特异性;T−C 排零=o_old 特异)")]
    summ = {"arms_n": {k: len(v) for k, v in arms.items()},
            "input_duplicate_audit": input_audits,
            "marginal": {k: marginal(v) for k, v in arms.items()}, "contrasts": {}}
    print(f"\n# 配对对照(armA − armB,均差 [95%CI] p):")
    for a, b, desc in contrasts:
        if a in arms and b in arms:
            print(f"## {a}−{b}  {desc}")
            for m in METRICS:
                r = paired_diff(arms[a], arms[b], m)
                sig = "" if r.get("n", 0) == 0 else ("  ✅排零" if (r["ci"][0] > 0 or r["ci"][1] < 0) else "  ⚠含0")
                print(f"   {m:<5} {r.get('mean'):>8} {str(r.get('ci')):>20} p={r.get('p')}{sig}")
                summ["contrasts"].setdefault(f"{a}-{b}", {})[m] = r
    if args.out:
        json.dump(summ, open(args.out, "w"), ensure_ascii=False, indent=2)
        print(f"\n# → {args.out}")
    print("\n# 读法:T−P 的 RR/CLR 应负且排零(o_old 特异有效);P−N 应≈0(placebo 无效=非通用扰动);")
    print("#       D−N 的 ES 应≤0(压 o_new 不改善/恶化);符号阶梯 D<N~P<T 成立=W1 因果对照立。")


if __name__ == "__main__":
    main()
