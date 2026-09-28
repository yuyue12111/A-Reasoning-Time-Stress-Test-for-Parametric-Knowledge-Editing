"""Fresh Study-2 pool: exclude used cases, shuffle, screen each model's base at B0, freeze (REVISION.md §3).

    PYTHONPATH=src python -m rt.pool build   --config experiments/rt/pool_screen.yaml            # CPU
    CUDA_VISIBLE_DEVICES=$r PYTHONPATH=src python -m rt.pool screen --config ... --model-tag r1qwen32b \\
        --rank $r --world 8                                                                   # GPU
    PYTHONPATH=src python -m rt.pool qualify --config ... --model-tag r1qwen32b              # CPU
    PYTHONPATH=src python -m rt.pool ids-from-shards --glob '<legacy run>_r*of8.jsonl' --out <manifest>

build: ``counterfact`` minus every case_id found in ``used_sources`` (jsonl globs; ``collect_used_ids``
    reads each row's ``case_id``; files matching ``used_exclude`` are skipped, and the summary lists
    every file scanned with its row and id counts), then ``random.Random(seed).shuffle`` of the
    remaining ids in file order, then the first ``n_candidates`` -> ``candidates.jsonl`` (+ .sha256)
    and ``candidates_summary.json``.  An existing candidates file is never replaced by a different one.
screen: the model's unedited base, budget B0, efficacy prompt, greedy, through ``rt.run`` (same
    header, resume and sharding) -> ``<screen_dir>/<model_tag>_pool_screen_r<rank>of<world>.jsonl``.
qualify: in candidate order, a case qualifies when its base B0 answer, with the subject removed
    (``metrics._without_subject``), hits ``o_old`` and does not hit ``o_new`` (``metrics.hit`` with
    ``aliases``) and the subject does not contain ``o_old`` as a whole word (case-insensitive).  The
    first ``k`` qualified cases form ``manifest_<model_tag>.jsonl`` (+ .sha256); every decision goes to
    ``qualify_<model_tag>.jsonl`` and the counts per exclusion reason to ``summary_<model_tag>.json``.
"""
import argparse
import glob
import json
import os
import random
import re

import metrics
from rt.run import _abs, _rel, load_cases, read_ids, run_config, sha256_file, sha256_json

REASONS = ("missing_screen", "subject_contains_old", "old_miss", "new_hit")


def write_manifest(path, rows):
    """Write jsonl rows and a sha256sum-style sidecar; returns the sha256."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    sha = sha256_file(path)
    with open(path + ".sha256", "w") as f:
        f.write(f"{sha}  {os.path.basename(path)}\n")
    return sha


def collect_used_ids(patterns, exclude=(), root=None):
    """Union of ``case_id`` values over every jsonl row in the files matching ``patterns``.

    Returns (ids, report); the report lists, per pattern, every file scanned with its row, id and
    unparseable-line counts, so the exclusion set is auditable.  ``exclude`` globs drop files.
    """
    root = root or _abs("")
    j = lambda p: p if os.path.isabs(p) else os.path.join(root, p)
    skip = {os.path.abspath(f) for pat in exclude for f in glob.glob(j(pat), recursive=True)}
    ids, report = set(), []
    for pat in patterns:
        files = sorted(f for f in glob.glob(j(pat), recursive=True)
                       if os.path.isfile(f) and os.path.abspath(f) not in skip)
        entry = {"pattern": pat, "files": []}
        pat_ids = set()
        for f in files:
            n_rows = n_bad = 0
            fids = set()
            with open(f, errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except ValueError:
                        n_bad += 1
                        continue
                    n_rows += 1
                    if isinstance(r, dict) and isinstance(r.get("case_id"), (str, int)):
                        fids.add(str(r["case_id"]))
            entry["files"].append({"path": os.path.relpath(f, root), "n_rows": n_rows,
                                   "n_ids": len(fids), "n_bad_lines": n_bad})
            pat_ids |= fids
        entry["n_files"], entry["n_ids"] = len(files), len(pat_ids)
        report.append(entry)
        ids |= pat_ids
    return ids, report


def build_candidates(cases, used, seed=2027, n=1600):
    """Ids of ``cases`` (file order) not in ``used``, shuffled with ``seed``; the first ``n``."""
    ids = [c["case_id"] for c in cases if c["case_id"] not in used]
    random.Random(seed).shuffle(ids)
    return ids[:n]


def ids_from_shards(pattern):
    """Case ids of a legacy sharded run in dataset order (shard r of w holds indices i % w == r)."""
    per, worlds = {}, set()
    for f in sorted(glob.glob(pattern)):
        m = re.search(r"_r(\d+)of(\d+)\.jsonl$", f)
        if not m:
            raise ValueError(f"{f}: not a _r<rank>of<world>.jsonl shard")
        worlds.add(int(m[2]))
        seen = {}
        for line in open(f):
            cid = json.loads(line).get("case_id")
            if cid is not None:
                seen.setdefault(cid, None)
        per[int(m[1])] = list(seen)
    if len(worlds) != 1 or set(per) != set(range(max(worlds))):
        raise ValueError(f"{pattern}: need exactly one complete shard set, got ranks {sorted(per)} of {worlds}")
    world = worlds.pop()
    order = [per[r][k] for k in range(max(map(len, per.values()))) for r in range(world) if k < len(per[r])]
    if len(order) != len(set(order)):
        raise ValueError("a case id appears in more than one shard")
    return order


def subject_contains_old(case):
    return bool(metrics._wb(case["o_old"]).search((case.get("s") or "").lower()))


def qualify(cands, answers, aliases, k):
    """Apply the screening rules in candidate order.

    ``cands``: case dicts in candidate order; ``answers``: case_id -> base B0 efficacy answer.
    Returns (manifest ids, per-case decisions, counts).  ``reason`` is the first failed rule in
    ``REASONS`` order; ``excluded_any`` counts every failed rule.
    """
    decisions, manifest = [], []
    primary = {r: 0 for r in REASONS}
    anyc = {r: 0 for r in REASONS}
    for i, c in enumerate(cands):
        cid = c["case_id"]
        d = {"case_id": cid, "cand_index": i}
        if cid not in answers:
            failed = ["missing_screen"]
        else:
            ans = metrics._without_subject(answers[cid], c.get("s") or "")
            d.update(old_hit=bool(metrics.hit(ans, c["o_old"], aliases)),
                     new_hit=bool(metrics.hit(ans, c["o_new"], aliases)),
                     subject_contains_old=subject_contains_old(c))
            failed = [r for r, bad in (("subject_contains_old", d["subject_contains_old"]),
                                       ("old_miss", not d["old_hit"]), ("new_hit", d["new_hit"])) if bad]
        for r in failed:
            anyc[r] += 1
        if failed:
            primary[failed[0]] += 1
        d["qualified"] = not failed
        d["reason"] = failed[0] if failed else None
        d["in_manifest"] = bool(not failed and len(manifest) < k)
        if d["in_manifest"]:
            manifest.append(cid)
        decisions.append(d)
    counts = {"n_candidates": len(cands), "n_screened": sum(1 for c in cands if c["case_id"] in answers),
              "n_qualified": sum(d["qualified"] for d in decisions), "k": k, "n_manifest": len(manifest),
              "complete": len(manifest) == k, "excluded_primary": primary, "excluded_any": anyc}
    return manifest, decisions, counts


def _paths(pcfg, tag=None):
    d = _abs(pcfg["pool_dir"])
    p = {"candidates": os.path.join(d, "candidates.jsonl"),
         "candidates_summary": os.path.join(d, "candidates_summary.json")}
    if tag:
        p.update(manifest=os.path.join(d, f"manifest_{tag}.jsonl"),
                 decisions=os.path.join(d, f"qualify_{tag}.jsonl"),
                 summary=os.path.join(d, f"summary_{tag}.json"),
                 screen_glob=os.path.join(_abs(pcfg["screen_dir"]), f"{tag}_pool_screen_r*of*.jsonl"))
    return p


def cmd_build(pcfg, force=False):
    cases, src = load_cases({"path": pcfg.get("counterfact", "data/counterfact.jsonl")})
    used, report = collect_used_ids(pcfg["used_sources"], pcfg.get("used_exclude", ()))
    known = {c["case_id"] for c in cases}
    ids = build_candidates(cases, used, int(pcfg.get("seed", 2027)), int(pcfg.get("n_candidates", 1600)))
    p = _paths(pcfg)
    rows = [{"case_id": cid, "cand_index": i} for i, cid in enumerate(ids)]
    if os.path.exists(p["candidates"]) and not force:
        if read_ids(p["candidates"]) != ids:
            raise RuntimeError(f"{p['candidates']} exists with different ids; candidates are frozen "
                               f"(pass --force only before any screening)")
        print(f"[pool] {p['candidates']} already frozen and identical")
        return p["candidates"]
    sha = write_manifest(p["candidates"], rows)
    summary = {"counterfact": _rel(src), "counterfact_sha256": sha256_file(src), "n_cases": len(cases),
               "seed": int(pcfg.get("seed", 2027)), "n_candidates": len(ids),
               "used": {"n_ids": len(used), "n_ids_in_counterfact": len(used & known),
                        "n_ids_not_in_counterfact": len(used - known),
                        "ids_sha256": sha256_json(sorted(used & known)),
                        "sources": report, "exclude": list(pcfg.get("used_exclude", ()))},
               "n_available": len(known - used), "candidates": _rel(p["candidates"]), "candidates_sha256": sha}
    with open(p["candidates_summary"], "w") as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)
    print(f"[pool] used ids {len(used & known)} (of {len(cases)}), available {len(known - used)}, "
          f"candidates {len(ids)} -> {_rel(p['candidates'])} sha256 {sha[:12]}")
    return p["candidates"]


def screen_config(pcfg, tag):
    m = (pcfg.get("models") or {}).get(tag)
    if m is None:
        raise ValueError(f"model tag {tag!r} not in pool config models")
    if "no_bos" not in m:
        raise ValueError(f"pool config model {tag!r} must set no_bos (REVISION.md §5)")
    return {"model_tag": tag, "template": m.get("template", "r1"), "template_system": m.get("template_system"),
            "no_bos": bool(m["no_bos"]),
            "model": m.get("model") or {}, "module_tmp": m.get("module_tmp", "model.layers.{}.mlp.down_proj"),
            "out_dir": pcfg["screen_dir"], "run_tag": "pool",
            "dataset": {"path": pcfg.get("counterfact", "data/counterfact.jsonl"),
                        "manifest": _rel(_paths(pcfg)["candidates"])},
            "aliases": pcfg.get("aliases", "data/aliases.json"), "probes": ["efficacy"],
            "decoding": {"greedy": True}, "engine": pcfg.get("engine") or {},
            "conditions": [{"name": "screen", "editor": "none", "budgets": ["B0"]}]}


def cmd_screen(pcfg, tag, rank=0, world=1, model=None, tok=None, device=None, limit=None, config_path=None):
    return run_config(screen_config(pcfg, tag), rank, world, model=model, tok=tok, config_path=config_path,
                      limit=limit, device=device)


def cmd_qualify(pcfg, tag, allow_missing=False):
    p = _paths(pcfg, tag)
    cand_ids = read_ids(p["candidates"])
    cands, _ = load_cases({"path": pcfg.get("counterfact", "data/counterfact.jsonl"), "case_ids": cand_ids})
    files = sorted(glob.glob(p["screen_glob"]))
    if not files:
        raise FileNotFoundError(f"no screen shards match {p['screen_glob']}")
    answers, headers = {}, []
    for f in files:
        for line in open(f):
            r = json.loads(line)
            if r.get("_meta"):
                headers.append(r)
            elif r.get("probe") == "efficacy" and r.get("budget") == "B0" and r.get("decode") == "greedy":
                answers.setdefault(r["case_id"], r["answer"])
    want = sha256_json(cand_ids)
    bad = [h for h in headers if h["spec"]["dataset"]["case_ids_sha256"] != want]
    if bad or len({h["config_sha256"] for h in headers}) != 1:
        raise RuntimeError("screen shards were not produced from these candidates with one config")
    missing = [c for c in cand_ids if c not in answers]
    if missing and not allow_missing:
        raise RuntimeError(f"{len(missing)} candidates have no screen row (e.g. {missing[:3]}); "
                           f"finish screening or pass --allow-missing")
    aliases = json.load(open(_abs(pcfg.get("aliases", "data/aliases.json"))))
    k = int(((pcfg.get("models") or {}).get(tag) or {}).get("k", pcfg.get("k", 400)))   # per-model override (70B: 200)
    manifest, decisions, counts = qualify(cands, answers, aliases, k)
    sha = write_manifest(p["manifest"], [{"case_id": c} for c in manifest])
    with open(p["decisions"], "w") as f:
        for d in decisions:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    summary = dict(counts, model_tag=tag, manifest=_rel(p["manifest"]), manifest_sha256=sha,
                   candidates=_rel(p["candidates"]), candidates_sha256=sha256_file(p["candidates"]),
                   screen_files=[_rel(f) for f in files], screen_config_sha256=headers[0]["config_sha256"],
                   screen_git=headers[0].get("git"), aliases_sha256=sha256_file(_abs(pcfg.get("aliases", "data/aliases.json"))),
                   rules="old_hit AND NOT new_hit on the subject-scrubbed base B0 efficacy answer "
                         "(metrics.hit, aliases.json) AND subject does not contain o_old as a whole word; "
                         "first k in candidate order")
    with open(p["summary"], "w") as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)
    print(f"[pool] {tag}: qualified {counts['n_qualified']}/{counts['n_candidates']}, manifest "
          f"{counts['n_manifest']}/{k} -> {_rel(p['manifest'])} sha256 {sha[:12]}; "
          f"excluded {counts['excluded_primary']}")
    if not counts["complete"]:
        print(f"[pool] WARNING: only {counts['n_manifest']} qualified cases, fewer than k={k}")
    return summary


def main(argv=None):
    import yaml
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--config", required=True)
    b.add_argument("--force", action="store_true")
    s = sub.add_parser("screen")
    s.add_argument("--config", required=True)
    s.add_argument("--model-tag", required=True)
    s.add_argument("--rank", type=int, default=0)
    s.add_argument("--world", type=int, default=1)
    s.add_argument("--device", default=None)
    s.add_argument("--limit", type=int, default=None)
    q = sub.add_parser("qualify")
    q.add_argument("--config", required=True)
    q.add_argument("--model-tag", required=True)
    q.add_argument("--allow-missing", action="store_true")
    i = sub.add_parser("ids-from-shards")
    i.add_argument("--glob", required=True)
    i.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "ids-from-shards":
        ids = ids_from_shards(a.glob)
        sha = write_manifest(a.out, [{"case_id": c} for c in ids])
        print(f"[pool] {len(ids)} ids -> {a.out} sha256 {sha[:12]}")
        return
    pcfg = yaml.safe_load(open(a.config))
    if a.cmd == "build":
        cmd_build(pcfg, a.force)
    elif a.cmd == "screen":
        print(cmd_screen(pcfg, a.model_tag, a.rank, a.world, device=a.device, limit=a.limit, config_path=a.config))
    else:
        cmd_qualify(pcfg, a.model_tag, a.allow_missing)


if __name__ == "__main__":
    main()
