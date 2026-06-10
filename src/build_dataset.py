"""task#06：把 CounterFact / zsRE / MQuAKE-CF-3k 清洗成统一 jsonl schema（plan Phase 0 #06）。

统一 schema（每行一条）：
  {case_id, source, s, r, prompt, o_old, o_new,
   o_old_aliases[], o_new_aliases[], paraphrases[], neighborhood[], hops[]}
  - prompt        : 已填 subject 的编辑 cloze（EasyEdit edit() 需 subject 在 prompt 内）
  - o_old         : 旧事实=回退目标。CF/MQuAKE=target_true；zsRE=answers[0]（真答案，模型应已知）
  - o_new         : 编辑目标。CF/MQuAKE=target_new；zsRE=alt（反事实编辑目标）
  - neighborhood  : locality 探针（CF 自带；zsRE=loc；MQuAKE 无）
  - hops          : 多跳问题（仅 MQuAKE，portability 章节用）

副产物 data/aliases.json：{target_str: [aliases]}，喂 src/metrics.py 的 hit() 判分。
  v0 来源：MQuAKE single_hops/new_single_hops 的 answer_alias + zsRE answers[1:]。
  CF（仅有 Wikidata QID 无别名串）待 §TODO 用 QID 查 Wikidata 富集。

运行（纯 JSON，无需 torch，在仓库根）：python src/build_dataset.py
"""
import json, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data")
MQUAKE = os.path.join(ROOT, "source", "MQuAKE", "datasets", "MQuAKE-CF-3k.json")

_ALIASES = collections.defaultdict(set)   # target_str -> {aliases}


def _note_alias(target, aliases):
    if target and aliases:
        _ALIASES[target].update(a for a in aliases if a)


def _fill(prompt_tmpl, subject):
    return prompt_tmpl.replace("{}", subject) if "{}" in prompt_tmpl else prompt_tmpl


def clean_counterfact(path):
    out = []
    for r in json.load(open(path)):
        rw = r["requested_rewrite"]
        subj = rw["subject"]
        out.append({
            "case_id": f"cf_{r['case_id']}", "source": "counterfact",
            "s": subj, "r": rw.get("relation_id"),
            "prompt": _fill(rw["prompt"], subj),
            "o_old": rw["target_true"]["str"], "o_new": rw["target_new"]["str"],
            "o_old_aliases": [], "o_new_aliases": [],
            "paraphrases": list(r.get("paraphrase_prompts", [])),
            "neighborhood": list(r.get("neighborhood_prompts", [])),
            "hops": [],
        })
    return out


def clean_zsre(path):
    """zsRE：o_old=answers[0]（真答案，模型应已知）→ o_new=alt（反事实编辑目标）。
    跳过 alt 缺失或 alt==o_old 的退化条目（约 0.4%+3%）。"""
    out = []
    for i, r in enumerate(json.load(open(path))):
        ans = r.get("answers", [])
        o_old = ans[0] if ans else None
        o_new = r.get("alt")
        if not o_old or not o_new or o_new == o_old:
            continue                            # 退化/缺反事实，跳过
        # 注意：zsRE answers[1:] 是"其它可接受答案"（如 ['bronze','concrete']）而非别名，
        # 不当作 o_old 别名、也不入 aliases.json，否则污染 metrics.hit 判分。
        out.append({
            "case_id": f"zsre_{i}", "source": "zsre",
            "s": r["subject"], "r": None,
            "prompt": r["src"],                 # src 已是填好的问句
            "o_old": o_old, "o_new": o_new,
            "o_old_aliases": [], "o_new_aliases": [],
            "paraphrases": [r["rephrase"]] if r.get("rephrase") else [],
            "neighborhood": [r["loc"]] if r.get("loc") else [],
            "hops": [],
        })
    return out


def _alias_of(hops, target):
    for h in hops or []:
        if h.get("answer") == target:
            return list(h.get("answer_alias", []))
    return []


def clean_mquake(path):
    out = []
    for r in json.load(open(path)):
        rws = r["requested_rewrite"]
        rw = rws[0]                             # 主编辑取第一条 rewrite
        subj = rw["subject"]
        o_old, o_new = rw["target_true"]["str"], rw["target_new"]["str"]
        oa = _alias_of(r.get("single_hops"), o_old)        # 单跳里 answer==o_old 的别名
        na = _alias_of(r.get("new_single_hops"), o_new)
        _note_alias(o_old, oa); _note_alias(o_new, na)
        # 顺带把多跳最终答案的别名也收进全局别名表
        _note_alias(r.get("answer"), r.get("answer_alias"))
        _note_alias(r.get("new_answer"), r.get("new_answer_alias"))
        out.append({
            "case_id": f"mquake_{r['case_id']}", "source": "mquake_cf_3k",
            "s": subj, "r": rw.get("relation_id"),
            "prompt": _fill(rw["prompt"], subj),
            "o_old": o_old, "o_new": o_new,
            "o_old_aliases": oa, "o_new_aliases": na,
            "paraphrases": [], "neighborhood": [],
            "hops": list(r.get("questions", [])),
            "n_rewrites": len(rws),                          # >1 = 多编辑 case（单条协议下慎用）
            "hop_answer_old": r.get("answer"), "hop_answer_new": r.get("new_answer"),
        })
    return out


def write_jsonl(rows, name):
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return p


def main():
    os.makedirs(OUT, exist_ok=True)
    jobs = [
        ("counterfact.jsonl", clean_counterfact, os.path.join(RAW, "counterfact.json")),
        ("zsre.jsonl",        clean_zsre,        os.path.join(RAW, "zsre_mend_eval.json")),
        ("mquake_cf_3k.jsonl", clean_mquake,     MQUAKE),
    ]
    summary = []
    for name, fn, path in jobs:
        if not os.path.exists(path):
            print(f"[skip] {name}: 源不存在 {path}")
            continue
        rows = fn(path)
        write_jsonl(rows, name)
        n_oold = sum(1 for r in rows if r["o_old"])
        summary.append((name, len(rows), n_oold))
        print(f"[ok] {name}: {len(rows)} 条 (有 o_old: {n_oold})")

    # 别名表
    aliases = {k: sorted(v) for k, v in sorted(_ALIASES.items()) if v}
    with open(os.path.join(OUT, "aliases.json"), "w", encoding="utf-8") as f:
        json.dump(aliases, f, ensure_ascii=False, indent=0)
    print(f"[ok] aliases.json: {len(aliases)} 个实体有别名")

    print("\n=== 汇总 ===")
    for name, n, n_oold in summary:
        print(f"  {name:<20} {n:>6} 条   o_old 可用 {n_oold}")


if __name__ == "__main__":
    main()
