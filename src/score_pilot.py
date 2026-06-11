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
    os.remove(merged)

    print(f"# editor={args.editor}  shards={len(shards)}  错误行={n_err}  o_old/o_new 源={src}")
    print(f"{'budget':<8}{'n':>6}{'ES':>9}{'RR':>9}{'CLR':>9}")
    for b in res:
        r = res[b]
        print(f"{b:<8}{r['n']:>6}{r['ES']:>9.3f}{r['RR']:>9.3f}{r['CLR']:>9.3f}")
    print("\ngo/no-go (plan §Phase 1): RR(natural=B3)≥0.20 或 ES 自 B0 降幅≥0.20pp，"
          "且 ≥60% 回退案例可归因反思片段（人工审计 30 条）。")


if __name__ == "__main__":
    main()
