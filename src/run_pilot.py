"""Pilot 主入口 (plan Phase 1)：读 yaml → 抽样 cases → 跑 edit_loop（分片 + 续跑）。

**从项目根目录跑**（yaml 里 data/、source/EasyEdit/hparams、results/ 都相对项目根；脚本也会把它们
解析成项目根的绝对路径，故任意 cwd 均可，但建议在根目录）。easyeditor 靠 PYTHONPATH 引入：

  cd <项目根>
  # 8 卡，每卡一进程：
  for r in $(seq 0 7); do PYTHONPATH=source/EasyEdit python src/run_pilot.py \
      --config experiments/pilot.yaml --editor ROME --rank $r --world 8 --device $r & done; wait
  # 干跑（无 GPU，验证抽样/分片/路径/overrides）：
  PYTHONPATH=source/EasyEdit python src/run_pilot.py --config experiments/pilot.yaml --editor ROME --dry-run
"""
import argparse, json, os, random, yaml

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # src/ 的上一级=项目根


def _abs(p):
    """相对路径按项目根解析（绝对路径原样）——使 run_pilot 不依赖 cwd（data/hparams/results/stats）。"""
    return p if os.path.isabs(p) else os.path.join(_ROOT, p)


def load_cases(path, n=None, seed=42):
    """确定性抽样：固定 seed 洗牌后取前 n（n=None 取全部）。"""
    cases = [json.loads(l) for l in open(path)]
    random.Random(seed).shuffle(cases)
    return cases[:n] if n else cases


def shard_ids(cases, rank, world):
    return [c["case_id"] for i, c in enumerate(cases) if i % world == rank]


def resolve(cfg, editor, rank, world, device=None):
    ds = cfg["dataset"]
    p_pre, p_fb = _abs(ds["path"]), _abs(ds.get("fallback_path", ds["path"]))
    path = p_pre if os.path.exists(p_pre) else p_fb
    prefiltered = path == p_pre
    cases = load_cases(path, ds.get("n"), cfg.get("seed", 42))
    ed = cfg["editors"][editor]
    overrides = dict(cfg.get("hparams_overrides", {}))
    overrides["device"] = device if device is not None else rank
    if "stats_dir" in overrides:                 # mom2 缓存位置也按项目根固定（不随 cwd 漂移）
        overrides["stats_dir"] = _abs(overrides["stats_dir"])
    if "layers" in ed:
        overrides["layers"] = ed["layers"]
    out = os.path.join(_abs(cfg["out_dir"]),
                       f"{cfg['model_tag']}_{editor}_{ds['tag']}_r{rank}of{world}.jsonl")
    samp = cfg.get("sampling")               # plan §2.5 采样臂；enabled=false 时 None（首窗 greedy 先行 §6.3）
    sampling = None
    if samp and samp.get("enabled"):
        sampling = {"temperature": samp.get("temperature", 0.6), "seeds": samp.get("seeds", [0, 1, 2])}
    return dict(path=path, prefiltered=prefiltered, cases=cases, hparams=_abs(ed["hparams"]),
                overrides=overrides, out=out, budgets=cfg["budgets"], sampling=sampling,
                suppress_cfg=cfg.get("suppress"))   # RQ3 修复:yaml 的 suppress 块(无则 None=baseline)


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
          f"decode={'greedy+sample'+str(R['sampling']['seeds']) if R['sampling'] else 'greedy'} "
          f"dev={R['overrides']['device']} out={R['out']}")
    if args.dry_run:
        print(f"[dry] overrides={R['overrides']}")
        print(f"[dry] 本片前 5 case: {mine[:5]}")
        return

    if not R["prefiltered"]:
        print("[warn] 未找到预过滤数据，先跑 src/prefilter.py 更干净（plan §2.3）")
    os.makedirs(cfg["out_dir"], exist_ok=True)
    meta = {"config": args.config, "model_tag": cfg["model_tag"], "seed": cfg.get("seed", 42),
            "hparams": R["hparams"], "dataset": {"tag": cfg["dataset"]["tag"], "src": R["path"],
            "prefiltered": R["prefiltered"], "n": cfg["dataset"].get("n")}}   # 溯源头配置摘要(plan §6)
    from edit_loop import run
    run(R["cases"], args.editor, R["hparams"], R["budgets"], R["out"], rank=args.rank,
        world=args.world, overrides=R["overrides"], sampling=R["sampling"], meta=meta,
        suppress_cfg=R.get("suppress_cfg"))


if __name__ == "__main__":
    main()
