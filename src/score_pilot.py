"""从 results/ 的 pilot 分片 jsonl 算 ES/RR/CLR（plan §2.5，口径=生成式 ES_b，不等于 EasyEdit rewrite_acc）。

  python src/score_pilot.py --config experiments/pilot.yaml --editor ROME
  python src/score_pilot.py --config experiments/pilot.yaml --editor MEMIT

自动 glob 8 个分片合并后打分；cases 的 o_old/o_new 用清洗后全量查表（覆盖所有 case_id）。
"""
import argparse, json, glob, os, tempfile, yaml
import metrics


def collect(cfg, editor):
    ds = cfg["dataset"]
    pat = os.path.join(cfg["out_dir"], f"{cfg['model_tag']}_{editor}_{ds['tag']}_r*.jsonl")
    shards = sorted(glob.glob(pat))
    if not shards:
        raise SystemExit(f"没有结果文件：{pat}\n（先跑 src/run_pilot.py）")
    src = ds.get("fallback_path", ds["path"])           # o_old/o_new 查表源（全量覆盖）
    cases = [json.loads(l) for l in open(src)]
    aliases = json.load(open("data/aliases.json"))
    return shards, cases, aliases, src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--editor", required=True)
    ap.add_argument("--boot", type=int, default=10000, help="bootstrap 次数(plan §2.5 n=10000)；0 跳过")
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config))
    shards, cases, aliases, src = collect(cfg, args.editor)

    fd, merged = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
    n_err = 0
    with open(merged, "w") as o:
        for s in shards:
            for l in open(s):
                if '"error"' in l:
                    n_err += 1
                o.write(l)
    res = metrics.score(merged, cases, aliases)

    fmt = lambda x: f"{x:>8.3f}" if isinstance(x, float) else f"{'—':>8}"   # None → 占位（该档无该探针）
    print(f"# editor={args.editor}  shards={len(shards)}  错误行={n_err}  解码臂=greedy  o_old/o_new 源={src}")
    print(f"{'budget':<7}{'n':>5}{'ES':>8}{'ESf':>8}{'RR':>8}{'CLR':>8}{'Flip':>8}{'PS':>8}{'Loc':>8}  (n_para/n_loc)")
    for b in res:
        r = res[b]
        print(f"{b:<7}{r['n']:>5}{fmt(r['ES'])}{fmt(r['ESf'])}{fmt(r['RR'])}{fmt(r['CLR'])}"
              f"{fmt(r['Flip'])}{fmt(r['PS'])}{fmt(r['Loc'])}  ({r['n_para']}/{r['n_loc']})")
    print("\nES=严格(命中 o_new 且不含 o_old)  ESf=首段断言(答案首立场=编辑)  Flip=答案内两立场都现(先新后旧)"
          "  —— ESf≫ES 且 Flip↑ = 答案内『越想越退』(07 教训, FlipPoint 见 analysis/09)")

    if args.boot:                                  # plan §2.5：95% bootstrap CI（按编辑条目重采样）
        bs = metrics.score_bootstrap(merged, cases, aliases, n_boot=args.boot)
        print(f"\n95% bootstrap CI (n={args.boot}, 按编辑条目重采样, plan §2.5)：")
        print(f"{'budget':<7}{'ES [lo, hi]':>24}{'RR [lo, hi]':>24}{'CLR [lo, hi]':>24}")
        cif = lambda t: f"{t[0]:.3f} [{t[1]:.3f},{t[2]:.3f}]" if t else "—"
        for b in bs:
            print(f"{b:<7}{cif(bs[b]['ES']):>24}{cif(bs[b]['RR']):>24}{cif(bs[b]['CLR']):>24}")

        drop = metrics.drop_bootstrap(merged, cases, aliases, base="B0", n_boot=args.boot)
        print(f"\nES 降幅 ES(B0)−ES(b) 配对 bootstrap（plan §2.5；越想越退主判据，CI 全>0=显著回退）：")
        for b in sorted(drop):
            t = drop[b]
            sig = "  ✅CI>0 显著" if t and t[1] > 0 else ("  ⚠CI 含0" if t else "")
            print(f"  B0→{b}: {cif(t)}{sig}")

    os.remove(merged)
    print("\ngo/no-go (plan §Phase 1): RR(natural=B3)≥0.20 或 ES 自 B0 降幅≥0.20pp，"
          "且 ≥60% 回退案例可归因反思片段（人工审计 30 条）。")
    print("layer 扫合格线 (plan §7): B0 下 ES≥0.90 & Loc≥0.85，否则该编辑器结果整体作废。")


if __name__ == "__main__":
    main()
