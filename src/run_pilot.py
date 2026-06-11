"""Pilot 主入口 (plan Phase 1)：读 yaml → 抽样 cases → 跑 edit_loop（分片 + 续跑）。

  # 8 卡，每卡一进程：
  cd source/EasyEdit
  for r in $(seq 0 7); do PYTHONPATH=. python ../../src/run_pilot.py \
      --config ../../experiments/pilot.yaml --editor ROME --rank $r --world 8 & done; wait
  # 干跑（无 GPU，验证抽样/分片/路径/overrides）：
  python src/run_pilot.py --config experiments/pilot.yaml --editor ROME --dry-run
"""
import argparse, json, os, random, yaml


def load_cases(path, n=None, seed=42):
    """确定性抽样：固定 seed 洗牌后取前 n（n=None 取全部）。"""
    cases = [json.loads(l) for l in open(path)]
    random.Random(seed).shuffle(cases)
    return cases[:n] if n else cases


def shard_ids(cases, rank, world):
    return [c["case_id"] for i, c in enumerate(cases) if i % world == rank]


def resolve(cfg, editor, rank, world, device=None):
    ds = cfg["dataset"]
    path = ds["path"] if os.path.exists(ds["path"]) else ds.get("fallback_path", ds["path"])
    prefiltered = path == ds["path"]
    cases = load_cases(path, ds.get("n"), cfg.get("seed", 42))
    ed = cfg["editors"][editor]
    overrides = dict(cfg.get("hparams_overrides", {}))
    overrides["device"] = device if device is not None else rank
    if "layers" in ed:
        overrides["layers"] = ed["layers"]
    out = os.path.join(cfg["out_dir"],
                       f"{cfg['model_tag']}_{editor}_{ds['tag']}_r{rank}of{world}.jsonl")
    return dict(path=path, prefiltered=prefiltered, cases=cases,
                hparams=ed["hparams"], overrides=overrides, out=out, budgets=cfg["budgets"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--editor", required=True)
    ap.add_argument("--rank", type=int, default=0)
    ap.add_argument("--world", type=int, default=1)
    ap.add_argument("--device", type=int, default=None, help="不给则用 rank 作卡号")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    R = resolve(cfg, args.editor, args.rank, args.world, args.device)
    mine = shard_ids(R["cases"], args.rank, args.world)
    print(f"[pilot] editor={args.editor} src={R['path']} "
          f"{'(预过滤)' if R['prefiltered'] else '(⚠未预过滤, 回退全量)'} "
          f"n={len(R['cases'])} 本片={len(mine)} budgets={R['budgets']} "
          f"dev={R['overrides']['device']} out={R['out']}")
    if args.dry_run:
        print(f"[dry] overrides={R['overrides']}")
        print(f"[dry] 本片前 5 case: {mine[:5]}")
        return

    if not R["prefiltered"]:
        print("[warn] 未找到预过滤数据，先跑 src/prefilter.py 更干净（plan §2.3）")
    os.makedirs(cfg["out_dir"], exist_ok=True)
    from edit_loop import run
    run(R["cases"], args.editor, R["hparams"], R["budgets"], R["out"],
        rank=args.rank, world=args.world, overrides=R["overrides"])


if __name__ == "__main__":
    main()
