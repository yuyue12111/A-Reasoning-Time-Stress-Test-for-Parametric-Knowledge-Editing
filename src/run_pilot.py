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
import argparse, hashlib, json, os, random, yaml

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # src/ 的上一级=项目根


def _abs(p):
    """相对路径按项目根解析（绝对路径原样）——使 run_pilot 不依赖 cwd（data/hparams/results/stats）。"""
    return p if os.path.isabs(p) else os.path.join(_ROOT, p)


def load_cases(path, n=None, seed=42):
    """确定性抽样：固定 seed 洗牌后取前 n（n=None 取全部）。"""
    cases = [json.loads(l) for l in open(path)]
    random.Random(seed).shuffle(cases)
    return cases[:n] if n else cases


def select_cases(path, dataset_cfg, seed=42):
    """Select either an explicit frozen case-id list or the historical seed-shuffled prefix.

    ``case_ids`` is used by outcome-blind diagnostic manifests such as P1.  Its order is literal and
    is not shuffled; missing/duplicate IDs are hard failures so a server upload cannot silently drift.
    Existing configs without ``case_ids`` retain the original seed-shuffle + ``n`` behavior.
    """
    wanted = dataset_cfg.get("case_ids")
    if not wanted:
        return load_cases(path, dataset_cfg.get("n"), seed)
    if len(wanted) != len(set(wanted)):
        raise ValueError("dataset.case_ids contains duplicates")
    rows = [json.loads(l) for l in open(path) if l.strip()]
    by_id = {row["case_id"]: row for row in rows}
    missing = [cid for cid in wanted if cid not in by_id]
    if missing:
        raise ValueError(f"dataset.case_ids missing from source: {missing}")
    if dataset_cfg.get("n") not in (None, len(wanted)):
        raise ValueError("dataset.n must be absent or equal len(dataset.case_ids)")
    return [by_id[cid] for cid in wanted]


def shard_ids(cases, rank, world):
    return [c["case_id"] for i, c in enumerate(cases) if i % world == rank]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def code_sha256():
    """Hash the exact harness files that can change generated rows without changing YAML.

    A dirty git flag is not enough on the manually-uploaded servers: two runs can share HEAD while
    carrying different working-tree files.  Per-file hashes make N/T/C parity directly auditable.
    """
    rels = [
        "src/run_pilot.py", "src/edit_loop.py", "src/think_budget.py", "src/suppress.py",
        "src/r1_tokenizer.py", "src/vendor_patches/easyedit_qwen2_loader.py",
        "src/vendor_patches/easyedit_mom2_dataset.py",
    ]
    return {rel: sha256_file(_abs(rel)) for rel in rels if os.path.exists(_abs(rel))}


def resolve(cfg, editor, rank, world, device=None, limit=None, tag_suffix=""):
    ds = cfg["dataset"]
    p_pre, p_fb = _abs(ds["path"]), _abs(ds.get("fallback_path", ds["path"]))
    path = p_pre if os.path.exists(p_pre) else p_fb
    prefiltered = path == p_pre
    cases = select_cases(path, ds, cfg.get("seed", 42))
    if limit is not None:
        if limit <= 0:
            raise ValueError("--limit must be positive")
        cases = cases[:limit]
    ed = cfg["editors"][editor]
    overrides = dict(cfg.get("hparams_overrides", {}))
    overrides["device"] = device if device is not None else rank
    if "stats_dir" in overrides:                 # mom2 缓存位置也按项目根固定（不随 cwd 漂移）
        overrides["stats_dir"] = _abs(overrides["stats_dir"])
    if "layers" in ed:
        overrides["layers"] = ed["layers"]
    dataset_tag = ds["tag"] + tag_suffix
    out = os.path.join(_abs(cfg["out_dir"]),
                       f"{cfg['model_tag']}_{editor}_{dataset_tag}_r{rank}of{world}.jsonl")
    samp = cfg.get("sampling")               # plan §2.5 采样臂；enabled=false 时 None（首窗 greedy 先行 §6.3）
    sampling = None
    if samp and samp.get("enabled"):
        sampling = {"temperature": samp.get("temperature", 0.6), "seeds": samp.get("seeds", [0, 1, 2])}
    return dict(path=path, prefiltered=prefiltered, cases=cases, hparams=_abs(ed["hparams"]),
                overrides=overrides, out=out, budgets=cfg["budgets"], sampling=sampling,
                dataset_tag=dataset_tag, requested_n=ds.get("n"), effective_n=len(cases),
                suppress_cfg=cfg.get("suppress"),   # RQ3 修复:yaml 的 suppress 块(无则 None=baseline)
                probe_sel=cfg.get("probes"),        # 探针子集(无则 None=全 5 探针;capability 锚点设 [efficacy,locality] 提速)
                diagnostics_cfg=cfg.get("diagnostics"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--editor", required=True)
    ap.add_argument("--rank", type=int, default=0)
    ap.add_argument("--world", type=int, default=1)
    ap.add_argument("--device", type=int, default=None, help="不给则用 rank 作卡号")
    ap.add_argument("--limit", type=int, default=None,
                    help="只跑确定性抽样序列的前 N 条；技术 smoke 用 8，正式运行不传")
    ap.add_argument("--tag-suffix", default="",
                    help="附加到 dataset tag（如 _smoke），防 smoke 与正式 jsonl 混池")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    R = resolve(cfg, args.editor, args.rank, args.world, args.device,
                limit=args.limit, tag_suffix=args.tag_suffix)
    mine = shard_ids(R["cases"], args.rank, args.world)
    print(f"[pilot] editor={args.editor} src={R['path']} "
          f"{'(预过滤)' if R['prefiltered'] else '(⚠未预过滤, 回退全量)'} "
          f"tag={R['dataset_tag']} n={len(R['cases'])} 本片={len(mine)} budgets={R['budgets']} "
          f"decode={'greedy+sample'+str(R['sampling']['seeds']) if R['sampling'] else 'greedy'} "
          f"dev={R['overrides']['device']} out={R['out']}")
    if args.dry_run:
        print(f"[dry] overrides={R['overrides']}")
        print(f"[dry] 本片前 5 case: {mine[:5]}")
        return

    if not R["prefiltered"]:
        print("[warn] 未找到预过滤数据，先跑 src/prefilter.py 更干净（plan §2.3）")
    os.makedirs(os.path.dirname(R["out"]), exist_ok=True)
    meta = {"config": args.config, "config_sha256": sha256_file(args.config),
            "code_sha256": code_sha256(),
            "model_tag": cfg["model_tag"], "seed": cfg.get("seed", 42),
            "hparams": R["hparams"], "probe_sel": R.get("probe_sel"),
            "dataset": {"tag": R["dataset_tag"], "base_tag": cfg["dataset"]["tag"],
            "src": R["path"], "prefiltered": R["prefiltered"],
            "requested_n": R["requested_n"], "effective_n": R["effective_n"]},
            "run": {"limit": args.limit, "tag_suffix": args.tag_suffix}}   # 溯源头配置摘要(plan §6)
    from edit_loop import run
    run(R["cases"], args.editor, R["hparams"], R["budgets"], R["out"], rank=args.rank,
        world=args.world, overrides=R["overrides"], sampling=R["sampling"], meta=meta,
        suppress_cfg=R.get("suppress_cfg"), probe_sel=R.get("probe_sel"),
        diagnostics_cfg=R.get("diagnostics_cfg"))


if __name__ == "__main__":
    main()
