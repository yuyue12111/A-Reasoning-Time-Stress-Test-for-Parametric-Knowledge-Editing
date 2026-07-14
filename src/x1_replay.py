"""X1 Stage-0: replay a frozen natural CoT, generating only B0 and final answers.

This is intentionally separate from the live X3 harness.  It never regenerates or alters the source
chain: ROME edit -> fresh B0 answer -> exact fixed-CoT prefill -> replay answer -> finally restore.
"""
import argparse
import hashlib
import json
import os

import yaml


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARNESS_FILES = [
    "src/x1_replay.py", "src/build_x1_manifest.py", "src/think_budget.py", "src/edit_loop.py",
    "src/r1_tokenizer.py", "src/vendor_patches/easyedit_qwen2_loader.py",
    "source/EasyEdit/hparams/ROME/qwen2.5-7b.yaml",
]


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def code_sha256():
    return {p: sha256_file(_abs(p)) for p in HARNESS_FILES if os.path.exists(_abs(p))}


def load_source_row(manifest_row):
    path = _abs(manifest_row["source_path"])
    target = manifest_row["source_line"]
    raw = None
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            if lineno == target:
                raw = line.rstrip("\r\n")
                break
    if raw is None:
        raise ValueError(f"source line missing: {manifest_row['source_path']}:{target}")
    if sha256_text(raw) != manifest_row["source_row_sha256"]:
        raise ValueError(f"source row hash drift: {manifest_row['case_id']}")
    row = json.loads(raw)
    if row.get("case_id") != manifest_row["case_id"]:
        raise ValueError(f"source case mismatch: {manifest_row['case_id']} != {row.get('case_id')}")
    cot, answer = row.get("cot") or "", row.get("answer") or ""
    if sha256_text(cot) != manifest_row["cot_sha256"]:
        raise ValueError(f"source CoT hash drift: {manifest_row['case_id']}")
    if sha256_text(answer) != manifest_row["source_answer_sha256"]:
        raise ValueError(f"source answer hash drift: {manifest_row['case_id']}")
    forbidden = [x for x in ("<｜User｜>", "<｜Assistant｜>", "<think>", "</think>") if x in cot]
    if forbidden:
        raise ValueError(f"source CoT contains role/think delimiter {forbidden}: {manifest_row['case_id']}")
    return row


def load_manifest(path, limit=None, expected_sha256=None):
    if expected_sha256 and sha256_file(_abs(path)) != expected_sha256:
        raise ValueError("tracked X1 manifest SHA differs from the frozen config")
    tracked = [json.loads(line) for line in open(_abs(path), encoding="utf-8") if line.strip()]
    if len(tracked) != 18 or len({m.get("case_id") for m in tracked}) != 18:
        raise ValueError(f"frozen X1 manifest must contain 18 unique cases, got {len(tracked)}")
    counts = {label: sum(m.get("source") == label for m in tracked) for label in
              ("main_b3_greedy", "f2_b1_greedy", "f3_historical_sample_seed2")}
    if counts != {"main_b3_greedy": 10, "f2_b1_greedy": 5, "f3_historical_sample_seed2": 3}:
        raise ValueError(f"frozen X1 source composition drift: {counts}")
    rows = tracked[:limit] if limit is not None else tracked
    return [{"manifest": m, "source_row": load_source_row(m)} for m in rows]


def require_sample_audit(path):
    if not os.path.exists(_abs(path)):
        raise FileNotFoundError(f"X1 sample provenance audit missing: {path}")
    audit = json.load(open(_abs(path), encoding="utf-8"))
    if not (audit.get("status") == "PASS" and audit.get("expected_seed") == 2
            and audit.get("historical_rows") == 14 and audit.get("matched_rows") == 14):
        raise ValueError(f"X1 sample provenance audit is not the frozen 14/14 seed-2 PASS: {audit}")
    return audit


def fixed_replay_prompt(question, cot):
    import think_budget
    if any(x in cot for x in ("<｜User｜>", "<｜Assistant｜>", "<think>", "</think>")):
        raise ValueError("fixed CoT contains a forbidden role/think delimiter")
    return think_budget.TPL.format(q=question) + cot + "\n" + think_budget.THINK_END + "\n\n"


def generate_fixed_answer(model, tok, question, cot, answer_cap=256):
    import think_budget
    text = fixed_replay_prompt(question, cot)
    answer = think_budget._gen(model, tok, text, answer_cap, do_sample=False)
    return answer, text + answer


def execute_case(editor, model, tok, source, answer_cap=256,
                 b0_generate=None, replay_generate=None, restore_fn=None, token_count=None):
    """Run one atomic edit/B0/replay/restore unit; injectable callbacks keep restore testable."""
    import think_budget
    if b0_generate is None:
        b0_generate = lambda: think_budget.generate_with_budget(
            model, tok, source["prompt"], "B0", answer_cap=answer_cap)[1]
    if replay_generate is None:
        replay_generate = lambda: generate_fixed_answer(
            model, tok, source["prompt"], source["cot"], answer_cap)[0]
    if restore_fn is None:
        from edit_loop import restore as restore_fn
    if token_count is None:
        token_count = lambda: think_budget._ntok(tok, source["cot"])
    weights_copy = None
    try:
        _, _, weights_copy = editor.edit(
            prompts=[source["prompt"]], ground_truth=[source["o_old"]],
            target_new=[source["o_new"]], subject=[source["s"]], sequential_edit=True)
        b0_answer = b0_generate()
        replay_answer = replay_generate()
        return {"b0_answer": b0_answer, "replay_answer": replay_answer,
                "fixed_cot_tokens": token_count()}
    finally:
        if weights_copy is not None:
            restore_fn(model, weights_copy)


def shard_case_ids(rows, rank, world):
    return [x["manifest"]["case_id"] for i, x in enumerate(rows) if i % world == rank]


def resume_signature(header):
    keys = ("config_sha256", "manifest_sha256", "sample_audit_sha256", "code_sha256",
            "rank", "world", "tag", "answer_cap", "effective_n")
    return {k: header.get(k) for k in keys}


def assert_resume_compatible(path, expected):
    header = next((json.loads(line) for line in open(path, encoding="utf-8")
                   if line.strip() and json.loads(line).get("_meta")), None)
    if header is None:
        raise ValueError(f"refusing to resume headerless X1 shard: {path}")
    if resume_signature(header) != resume_signature(expected):
        changed = [k for k in resume_signature(expected)
                   if resume_signature(header).get(k) != resume_signature(expected).get(k)]
        raise ValueError(f"X1 resume signature mismatch: {changed}")


def load_editor(cfg, device):
    from easyeditor import BaseEditor, ROMEHyperParams
    from vendor_patches.easyedit_qwen2_loader import apply as apply_qwen_loader_patch
    from r1_tokenizer import fix_r1_tokenizer

    hp = ROMEHyperParams.from_hparams(_abs(cfg["editor"]["hparams"]))
    overrides = dict(cfg.get("hparams_overrides") or {})
    overrides["device"] = device
    overrides["layers"] = cfg["editor"]["layers"]
    for key, value in overrides.items():
        setattr(hp, key, value)
    if os.environ.get("WHYAAAI_MODEL"):
        hp.model_name = os.environ["WHYAAAI_MODEL"]
    apply_qwen_loader_patch()
    editor = BaseEditor.from_hparams(hp)
    tok = fix_r1_tokenizer(editor.tok, hp.model_name)
    editor.tok = tok
    return editor, editor.model, tok, hp, overrides


def run(cfg, rank=0, world=1, device=0, limit=None, tag_suffix=""):
    from edit_loop import git_provenance, model_runtime, software_provenance

    manifest_path = cfg["manifest"]
    audit_path = cfg["sample_source_audit"]
    audit = require_sample_audit(audit_path)
    rows = load_manifest(manifest_path, limit=limit, expected_sha256=cfg.get("manifest_sha256"))
    tag = cfg["tag"] + tag_suffix
    out = os.path.join(_abs(cfg["out_dir"]), f"{cfg['model_tag']}_ROME_{tag}_r{rank}of{world}.jsonl")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    expected_header = {
        "_meta": True,
        **git_provenance(),
        "software": software_provenance(),
        "config": cfg["_config_path"],
        "config_sha256": sha256_file(_abs(cfg["_config_path"])),
        "manifest": manifest_path,
        "manifest_sha256": sha256_file(_abs(manifest_path)),
        "sample_audit": audit_path,
        "sample_audit_sha256": sha256_file(_abs(audit_path)),
        "sample_audit_summary": {k: audit.get(k) for k in
                                 ("status", "expected_seed", "historical_rows", "matched_rows")},
        "code_sha256": code_sha256(),
        "rank": rank, "world": world, "tag": tag,
        "answer_cap": cfg.get("answer_cap", 256), "effective_n": len(rows),
        "runtime_env": {k: os.environ.get(k) for k in
                        ("WHYAAAI_MODEL", "WHYAAAI_DTYPE", "WHYAAAI_NO_BOS",
                         "WHYAAAI_DEVICE_MAP", "CUDA_VISIBLE_DEVICES")},
    }
    had_content = os.path.exists(out) and os.path.getsize(out) > 0
    if had_content:
        assert_resume_compatible(out, expected_header)
    done = set()
    attempts = {}
    if had_content:
        for line in open(out, encoding="utf-8"):
            rec = json.loads(line)
            cid = rec.get("case_id")
            if cid:
                attempts[cid] = attempts.get(cid, 0) + 1
            if cid and rec.get("status") == "ok":
                done.add(cid)

    editor, model, tok, hp, overrides = load_editor(cfg, device)
    expected_header["overrides"] = overrides
    expected_header["actual_runtime"] = model_runtime(model, tok, hp)
    with open(out, "a", encoding="utf-8") as fh:
        if not had_content:
            fh.write(json.dumps(expected_header, ensure_ascii=False) + "\n"); fh.flush()
        for index, item in enumerate(rows):
            m, source = item["manifest"], item["source_row"]
            cid = m["case_id"]
            if index % world != rank or cid in done:
                continue
            attempt = attempts.get(cid, 0) + 1
            try:
                generated = execute_case(editor, model, tok, source, cfg.get("answer_cap", 256))
                record = {
                    "status": "ok", "case_id": cid, "attempt": attempt,
                    "s": source["s"], "prompt": source["prompt"],
                    "o_old": source["o_old"], "o_new": source["o_new"],
                    "source": m["source"], "source_path": m["source_path"],
                    "source_line": m["source_line"], "source_row_sha256": m["source_row_sha256"],
                    "cot_sha256": m["cot_sha256"],
                    "fixed_cot_tokens": generated["fixed_cot_tokens"],
                    "b0_answer": generated["b0_answer"], "replay_answer": generated["replay_answer"],
                    "decode": "greedy", "answer_cap": cfg.get("answer_cap", 256),
                }
                fh.write(json.dumps(record, ensure_ascii=False) + "\n"); fh.flush()
            except Exception as exc:
                fh.write(json.dumps({"status": "error", "case_id": cid, "attempt": attempt,
                                     "error": repr(exc)}, ensure_ascii=False) + "\n"); fh.flush()
                print(f"[X1 case-fail] {cid}: {exc}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--rank", type=int, default=0)
    ap.add_argument("--world", type=int, default=1)
    ap.add_argument("--device", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--tag-suffix", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    cfg = yaml.safe_load(open(_abs(args.config), encoding="utf-8"))
    cfg["_config_path"] = args.config
    audit = require_sample_audit(cfg["sample_source_audit"])
    rows = load_manifest(cfg["manifest"], limit=args.limit, expected_sha256=cfg.get("manifest_sha256"))
    mine = shard_case_ids(rows, args.rank, args.world)
    print(f"[X1 replay] tag={cfg['tag'] + args.tag_suffix} n={len(rows)} rank={args.rank}/{args.world} "
          f"mine={len(mine)} device={args.device} sample_audit={audit['matched_rows']}/14 PASS")
    print(f"[X1 replay] cases={mine}")
    if args.dry_run:
        return
    out = run(cfg, args.rank, args.world, args.device, args.limit, args.tag_suffix)
    print(f"[X1 replay] complete shard={out}")


if __name__ == "__main__":
    main()
