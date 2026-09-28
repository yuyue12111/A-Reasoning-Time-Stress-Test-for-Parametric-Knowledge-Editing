"""Plausibility-matched edit targets and teacher-forced continuation scoring (engine v2).

For each case, the candidates are the distinct ``o_old`` values of all CounterFact cases with the
same relation ``r``, minus anything that would collide with this case under the answer matcher:
its own ``o_old``/``o_new`` (with aliases, word-boundary containment in either direction) and
anything contained in the subject name.  Each candidate ``c`` is scored by the base model's
teacher-forced log-probability of ``" " + c`` after the case prompt: the sum over its tokens
(= log P(continuation starts with c)) and the first token alone.  Ranking uses the sum by default
(``--rank-by first`` switches), ties broken by the other score and then by the string.  The top
candidate becomes the edit target with target_tag ``plausible``; the row also records the rank and
scores of the original CounterFact ``o_new`` among the candidates, and the score of ``o_old``.

Prompt and continuation are tokenized separately and concatenated, exactly as EasyEdit's ROME
objective sees them (prompt with the tokenizer's default special tokens, target
``" " + target_new`` with ``add_special_tokens=False``; rome/compute_v.py L35-50).

    PYTHONPATH=src:source/EasyEdit python -m rt.targets --model r1qwen32b \
        --pool data/pools/<pool>.json --out results/rt/targets/r1qwen32b_plausible.jsonl
"""
import argparse
import hashlib
import json
import os
import sys
import time

import torch

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGET_TAG = "plausible"


def _abs(p):
    return p if os.path.isabs(p) else os.path.join(_ROOT, p)


@torch.no_grad()
def continuation_logprobs(model, tok, prompt, continuations, batch_size=64):
    """Teacher-forced log-probabilities of each continuation after ``prompt``.

    Returns one dict per continuation: ``first`` (first token), ``sum`` (all tokens), ``n_tok``
    and ``first_id``.  Rows are right-padded, so batching does not change the result.
    """
    p = list(tok(prompt)["input_ids"])
    conts = [list(tok(c, add_special_tokens=False)["input_ids"]) for c in continuations]
    empty = [c for c, ids in zip(continuations, conts) if not ids]
    if empty:
        raise ValueError(f"continuations tokenize to nothing: {empty[:3]}")
    pad = tok.pad_token_id if tok.pad_token_id is not None else (tok.eos_token_id or 0)
    dev = model.get_input_embeddings().weight.device
    out = []
    for i in range(0, len(conts), batch_size):
        chunk = conts[i:i + batch_size]
        n = max(len(c) for c in chunk)
        ids = torch.full((len(chunk), len(p) + n), pad, dtype=torch.long)
        mask = torch.zeros_like(ids)
        for j, c in enumerate(chunk):
            ids[j, :len(p) + len(c)] = torch.tensor(p + c)
            mask[j, :len(p) + len(c)] = 1
        logits = model(input_ids=ids.to(dev), attention_mask=mask.to(dev), use_cache=False).logits
        lp = torch.log_softmax(logits[:, len(p) - 1:len(p) - 1 + n, :].float(), dim=-1)
        for j, c in enumerate(chunk):
            t = lp[j, torch.arange(len(c), device=lp.device), torch.tensor(c, device=lp.device)]
            out.append({"first": float(t[0]), "sum": float(t.sum()), "n_tok": len(c),
                        "first_id": int(c[0])})
    return out


def _collides(a, b, aliases):
    """True when ``a`` and ``b`` would be confused by the word-boundary answer matcher."""
    from metrics import hit
    return hit(a, b, aliases) or hit(b, a, aliases)


def candidate_pool(case, by_relation, aliases=None):
    """Distinct same-relation ``o_old`` values that cannot be confused with this case's answers."""
    aliases = aliases or {}
    local = dict(aliases)
    for key in ("o_old", "o_new"):
        extra = [a for a in case.get(f"{key}_aliases") or [] if a]
        if extra:
            local[case[key]] = list(local.get(case[key], [])) + extra
    out = []
    for c in by_relation.get(case["r"], []):
        if not c or not c.strip():
            continue
        if any(_collides(c, case[k], local) for k in ("o_old", "o_new")):
            continue
        if case.get("s") and _collides(case["s"], c, {}):
            continue
        out.append(c)
    return out


def relation_index(rows):
    """relation -> sorted distinct o_old values over the whole dataset."""
    by_rel = {}
    for row in rows:
        by_rel.setdefault(row["r"], set()).add(row["o_old"])
    return {r: sorted(v) for r, v in by_rel.items()}


def _key(score, rank_by):
    other = "first" if rank_by == "sum" else "sum"
    return (score[rank_by], score[other])


def rank_case(model, tok, case, candidates, rank_by="sum", batch_size=64, top_k=5):
    """Score candidates plus the case's own o_new/o_old; returns the output row (without meta)."""
    if rank_by not in ("sum", "first"):
        raise ValueError("rank_by must be 'sum' or 'first'")
    row = {"case_id": case["case_id"], "r": case["r"], "prompt": case["prompt"],
           "o_old": case["o_old"], "o_new": case["o_new"], "target_tag": TARGET_TAG,
           "rank_by": rank_by, "n_candidates": len(candidates)}
    conts = [" " + c for c in candidates] + [" " + case["o_new"], " " + case["o_old"]]
    scores = continuation_logprobs(model, tok, case["prompt"], conts, batch_size=batch_size)
    cand_scores, s_new, s_old = scores[:-2], scores[-2], scores[-1]
    order = sorted(range(len(candidates)),
                   key=lambda i: (tuple(-x for x in _key(cand_scores[i], rank_by)), candidates[i]))
    row["o_new_logprob"], row["o_old_logprob"] = s_new, s_old
    row["o_new_rank"] = 1 + sum(_key(s, rank_by) > _key(s_new, rank_by) for s in cand_scores)
    other = "first" if rank_by == "sum" else "sum"
    row[f"o_new_rank_by_{other}"] = 1 + sum(_key(s, other) > _key(s_new, other)
                                            for s in cand_scores)
    row["top"] = [[candidates[i], cand_scores[i]["sum"], cand_scores[i]["first"]]
                  for i in order[:top_k]]
    if not candidates:
        row.update(target=None, error="no candidates after exclusions")
        return row
    best = order[0]
    row["target"] = candidates[best]
    row["target_logprob"] = cand_scores[best]
    return row


def read_jsonl(path):
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_targets(path, target_tag, model_tag=None):
    """case_id -> target for rows of ``target_tag`` (and ``model_tag`` if given) in a targets file."""
    out = {}
    for row in read_jsonl(path):
        if row.get("_meta"):
            if model_tag and row.get("model_tag") not in (None, model_tag):
                raise ValueError(f"{path} was scored with {row.get('model_tag')}, not {model_tag}")
            continue
        if row.get("target_tag") != target_tag or not row.get("target"):
            continue
        if row["case_id"] in out and out[row["case_id"]] != row["target"]:
            raise ValueError(f"{path}: conflicting targets for {row['case_id']}")
        out[row["case_id"]] = row["target"]
    return out


def score_pool(model, tok, cases, all_rows, out_path, aliases=None, rank_by="sum",
               batch_size=64, meta=None, log=print):
    """Append one row per case to ``out_path`` (resumable by case_id); returns rows written."""
    by_rel = relation_index(all_rows)
    done = set()
    if os.path.exists(out_path):
        done = {r["case_id"] for r in read_jsonl(out_path) if r.get("case_id")}
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    written = 0
    with open(out_path, "a") as fh:
        if meta is not None:
            fh.write(json.dumps(meta, ensure_ascii=False) + "\n")
        for case in cases:
            if case["case_id"] in done:
                continue
            t0 = time.time()
            row = rank_case(model, tok, case, candidate_pool(case, by_rel, aliases),
                            rank_by=rank_by, batch_size=batch_size)
            row["wall_s"] = round(time.time() - t0, 3)
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            written += 1
            log(f"[targets] {case['case_id']}: {case['o_new']!r} rank {row['o_new_rank']}/"
                f"{row['n_candidates'] + 1} -> {row.get('target')!r}")
    return written


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--model", required=True, help="model tag in --models-file")
    ap.add_argument("--models-file", default="experiments/rt/deltas_models.yaml")
    ap.add_argument("--model-path", default=None, help="local model dir (default: $WHYAAAI_MODEL or hf_id)")
    ap.add_argument("--pool", required=True, help="pool manifest (JSON with case_ids)")
    ap.add_argument("--dataset", default="data/counterfact.jsonl")
    ap.add_argument("--aliases", default="data/aliases.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--rank-by", default="sum", choices=["sum", "first"])
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float32"])
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--device-map", default=None, help="e.g. auto (70B)")
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)

    from rt import deltas
    models = deltas.load_models(_abs(args.models_file))
    spec = models["models"][args.model]
    model_path = deltas.resolve_model_path(args.model_path, spec)
    ids, pool_meta = deltas.load_pool(_abs(args.pool))
    all_rows = read_jsonl(_abs(args.dataset))
    by_id = {r["case_id"]: r for r in all_rows}
    missing = [c for c in ids if c not in by_id]
    if missing:
        raise SystemExit(f"{len(missing)} pool ids not in dataset, e.g. {missing[:3]}")
    cases = [by_id[c] for c in ids][:args.limit]
    aliases = json.load(open(_abs(args.aliases))) if args.aliases and os.path.exists(_abs(args.aliases)) else {}

    from transformers import AutoModelForCausalLM
    from vendor_patches.easyedit_qwen2_loader import PatchedAutoTokenizer
    tok = PatchedAutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    device_map = args.device_map or {"": args.device}
    model = AutoModelForCausalLM.from_pretrained(model_path, dtype=getattr(torch, args.dtype),
                                                 device_map=device_map).eval()
    meta = {"_meta": True, **deltas.git_provenance(), "created": deltas.now(),
            "model_tag": args.model, "model_path": model_path, "dtype": args.dtype,
            "rank_by": args.rank_by, "pool": {"path": args.pool, **pool_meta},
            "dataset": {"path": args.dataset, "sha256": _sha(_abs(args.dataset))},
            "aliases": args.aliases, "software": deltas.software_provenance(),
            "rules": "candidates = distinct o_old of same-relation CounterFact cases, minus "
                     "matcher collisions with the case's o_old/o_new (+aliases) and the subject"}
    n = score_pool(model, tok, cases, all_rows, _abs(args.out), aliases=aliases,
                   rank_by=args.rank_by, batch_size=args.batch_size, meta=meta)
    print(f"[targets] wrote {n} rows -> {args.out}")


if __name__ == "__main__":
    sys.exit(main())
