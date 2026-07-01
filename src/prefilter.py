"""§2.3 预过滤：只保留"模型编辑前确实知道旧事实"的 case（pre-edit generate(prompt) 命中 o_old），
否则"回退"无从定义。需 GPU。**从项目根跑**（路径按项目根解析，不依赖 cwd）。

8 卡分片跑 + 合并（4090 常驻无时间压力 → 跑全候选；分片各处理本片、合并去重并按洗牌序定序）：
  cd <项目根>
  # 冒烟（小 limit 先验证无 bug，秒级）：
  for r in $(seq 0 7); do PYTHONPATH=source/EasyEdit python src/prefilter.py \
      --config experiments/pilot.yaml --rank $r --world 8 --device $r --limit 16 & done; wait
  PYTHONPATH=source/EasyEdit python src/prefilter.py --config experiments/pilot.yaml --merge --limit 16
  # 正式：去掉 --limit（默认 3×n 候选）
  for r in $(seq 0 7); do PYTHONPATH=source/EasyEdit python src/prefilter.py \
      --config experiments/pilot.yaml --rank $r --world 8 --device $r & done; wait
  PYTHONPATH=source/EasyEdit python src/prefilter.py --config experiments/pilot.yaml --merge   # 无 GPU

产物落 cfg.dataset.path（默认 data/counterfact.prefiltered.jsonl），run_pilot 自动优先用它。
判分复用 metrics.hit + data/aliases.json；生成用 think_budget（默认 B3≈自然，对推理模型召回最忠实）。
分片中间文件 {out}.r{rank}of{world}（每判一条写一行含 _pf_kept 标记 → 续跑跳过所有已判、合并只取存活）。
"""
import argparse, json, os, random, glob, yaml
import think_budget as tb
import metrics

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # src/ 的上一级=项目根


def _abs(p):
    return p if os.path.isabs(p) else os.path.join(_ROOT, p)


def _guard_provenance(out, cfg, force):
    """防覆盖:两个不同 dataset(如 cf200 headline vs cf1500 加宽)若共享同一 dataset.path,
    merge 会静默覆盖前者(毁 headline + 全 32B 抑制臂,§第四轮红队致命 bug)。以 {out}.meta.json 记 tag,
    tag 不同即拒绝(除非 --force)。同 tag 重跑/续跑放行。"""
    meta_p = out + ".meta.json"
    tag = cfg["dataset"].get("tag")
    if os.path.exists(meta_p):
        try:
            old = json.load(open(meta_p))
        except Exception:
            old = {}
        if old.get("tag") is not None and old.get("tag") != tag and not force:
            raise SystemExit(
                f"✗ 拒绝写 {out}:该路径由 dataset.tag={old.get('tag')!r}(n={old.get('n')})建立,"
                f"当前 tag={tag!r} 不同 → 会覆盖那份数据(可能是 cf200 headline + 全抑制臂,毁 RR=0.193 可复现)。"
                f"\n  → 给当前 config 一个专属 dataset.path(如 data/counterfact.prefiltered.{tag}.jsonl),或确认无误后加 --force。")
    return meta_p, tag


def _write_meta(meta_p, cfg, count):
    json.dump({"tag": cfg["dataset"].get("tag"), "n": cfg["dataset"].get("n"), "count": count},
              open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def candidates(cfg):
    """确定性候选：读 raw（清洗后全量）→ seed 洗牌 → 留有 o_old 的。返回有序 list + n。"""
    ds = cfg["dataset"]
    raw = _abs(ds.get("fallback_path", ds["path"]))
    cands = [json.loads(l) for l in open(raw)]
    random.Random(cfg.get("seed", 42)).shuffle(cands)
    return [c for c in cands if c.get("o_old")], ds.get("n", 200)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--budget", default="B3", help="预过滤生成预算（默认 B3≈自然；B0 更快但对推理模型可能漏召）")
    ap.add_argument("--device", type=int, default=0)
    ap.add_argument("--rank", type=int, default=0)
    ap.add_argument("--world", type=int, default=1)
    ap.add_argument("--limit", type=int, default=None, help="候选上限（默认 3×n）")
    ap.add_argument("--merge", action="store_true", help="合并 {out}.r* → {out}（无 GPU，去重 + 按洗牌序 + 截 2n）")
    ap.add_argument("--aliases", default="data/aliases.json")
    ap.add_argument("--force", action="store_true", help="覆盖 provenance guard（确认要写别的 tag 建过的路径时）")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    out = _abs(cfg["dataset"]["path"])
    meta_p, _tag = _guard_provenance(out, cfg, args.force)     # 防跨-tag 覆盖 headline(红队致命 bug)
    cands, n = candidates(cfg)
    cands = cands[: (args.limit or 3 * n)]

    if args.merge:                                   # —— 合并模式（无 GPU）——
        order = {c["case_id"]: i for i, c in enumerate(cands)}     # 原洗牌序，定序可复现
        shards = sorted(glob.glob(out + ".r*of*"))
        seen, survivors = set(), []
        for f in shards:
            for l in open(f):
                c = json.loads(l)
                if c.get("_pf_kept") and c["case_id"] not in seen:
                    seen.add(c["case_id"]); c.pop("_pf_kept", None); survivors.append(c)
        survivors.sort(key=lambda c: order.get(c["case_id"], 1 << 30))
        survivors = survivors[: 2 * n]               # 留 2n 冗余给抽样
        with open(out, "w", encoding="utf-8") as f:
            for c in survivors:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        _write_meta(meta_p, cfg, len(survivors))              # 记 provenance,防将来别的 tag 覆盖
        print(f"[merge] 合 {len(shards)} 分片 → {out}：存活 {len(survivors)}（截至 2n={2 * n}）")
        return

    # —— 分片过滤模式（GPU）——
    aliases = json.load(open(_abs(args.aliases)))
    from transformers import AutoModelForCausalLM, AutoTokenizer
    model_name = cfg["hparams_overrides"]["model_name"]   # R1-Distill-Qwen-7B
    tok = AutoTokenizer.from_pretrained(model_name)
    model = (AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto")
             .to(f"cuda:{args.device}").eval())            # auto=config bf16；48G 卡宽裕

    mine = cands[args.rank::args.world]               # 交错分片
    out_r = f"{out}.r{args.rank}of{args.world}"
    done = set()
    if os.path.exists(out_r):                         # 续跑：跳过所有已判（含未存活）
        done = {json.loads(l)["case_id"] for l in open(out_r)}
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    kept = judged = 0
    with open(out_r, "a", encoding="utf-8") as f:
        for i, c in enumerate(mine, 1):
            if c["case_id"] in done:
                continue
            _, ans, _ = tb.generate_with_budget(model, tok, c["prompt"], args.budget)
            rec = dict(c); rec["_pf_kept"] = bool(metrics.hit(ans, c["o_old"], aliases))
            f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
            judged += 1; kept += rec["_pf_kept"]
            if i % 25 == 0:
                print(f"  [r{args.rank} {i}/{len(mine)}] 本次新判 {judged} 存活 {kept}", flush=True)
    print(f"[prefilter r{args.rank}/{args.world}] 本次判 {judged} 存活 {kept} → {out_r} "
          f"(budget={args.budget}；合并用 --merge)")


if __name__ == "__main__":
    main()
