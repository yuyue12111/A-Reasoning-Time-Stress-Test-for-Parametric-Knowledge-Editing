"""A3/RQ2 §5 —— 链级回退路径多判官分类(taxonomy 定稿见 workflow wjrh3070w / plan v1.31)。

门控后 true-reversion 群体上的 4 主类:
  Recall   : o_old 作为 (subject,relation) 的值被直陈,subject↔o_old 间无第三中介(须知道该实体本身)。
  Bridge   : 经命名中介 E(名字词源/地理/类属/品牌/虚构连接/不否定 o_new 的前向漂移)推出 o_old(32B 众数路径)。
  Reflective-override : 早处 verbalize o_new → 反思标记 → 同段 commit 到 o_old(draft 'dismiss' 收紧;真回退中罕见)。
  Associative : 残差兜底,exhaustive 用 —— implicit-leak(o_old 连语义都不在链里) / ramble(无 governing 子句默认落旧)。
正交 contests_edit 二元 stance(链是否逐字称 o_new 错)单列,cross-cut 四类。

门控(STEP -1/-0,不进判官):short_code(<4 字符 matcher 盲)/morpho(o_old↔o_new 互为变体)= Excluded-artifact;
degenerate(score_pilot._is_degenerate / 反思-loop≥3)= Excluded-degenerate;held(答案 commit o_new)= Excluded-held(判官裁)。

判官在外部(本会话 workflow,3 判官读 RAW cot 多数表决)。本模块只做 CPU 侧:prefeature / 门控 / emit prompt / 聚合 / 汇总+表 + Fleiss κ。
判官后端注入(stub 供单测)。用法见 README / RUNBOOK;三步:emit → (workflow 判官) → aggregate。
"""
import argparse, json, os, random
from collections import Counter
import metrics
import audit_reversions
from score_pilot import _is_degenerate

PREC = ["Reflective-override", "Bridge", "Recall", "Associative"]      # 决策树优先级(高→低);3-way split 时取最高
PRIMARIES = set(PREC)

JUDGE_PROMPT_TEMPLATE = """You are one of three independent expert judges classifying HOW a reasoning chain re-surfaced an OLD fact after a knowledge edit. A model was edited so that (<<SUBJECT>>, relation) -> "<<O_NEW>>" (NEW). With no thinking the model answered NEW (edit installed). With long thinking the chain below settled on "<<O_OLD>>" (OLD). A separate probe proves the edit is STILL INSTALLED in the weights — so the chain is ROUTING AROUND an intact edit, NOT recalling decayed weights. Your job is to name the ROUTE, descriptively. Make NO claim that OLD is correct or that the edit weakened.

Read the RAW chain-of-thought verbatim (do not mentally delete the subject string; subject-substring cues are real evidence):
--- RAW COT START ---
<<COT>>
--- RAW COT END ---
Final answer text: <<ANSWER>>

Localize the OLD mention that the FINAL ANSWER follows (the boxed/committed value). Evaluate ONLY the clause containing/immediately governing it; the rest is context. Choose EXACTLY ONE primary label by this ordered tree (first match wins):

1. REFLECTIVE-OVERRIDE — "<<O_NEW>>" is verbalized EARLIER as a candidate (by name, paraphrase, anaphor like them/theirs/it, OR negation like 'not <<O_NEW>>'), THEN a reversal marker (wait/no/actually/but/hold on/reconsider) intervenes, AND the SAME span commits to "<<O_OLD>>". The dismissal and the OLD-commitment must be one span. If "<<O_NEW>>" is used as an accepted premise (not contradicted), this is NOT it. If OLD comes from a separate pathway, this is NOT it.
2. BRIDGE — the clause routes <<SUBJECT>> -> some NAMED intermediate E (a different entity/region/language/category/brand, a name-or-spelling cue guessable from the subject string, a confabulated fact, OR a forward drift that starts from "<<O_NEW>>" without rejecting it) -> "<<O_OLD>>". The OLD value need not appear verbatim; quoting the bridging-entity clause is enough (e.g. 'Italy and its historic capital' => Rome).
3. RECALL — "<<O_OLD>>" is asserted FLAT as the relation value with NO distinct intermediate named, and you would have to KNOW this specific entity to produce it (the subject string does not spell/imply it).
4. ASSOCIATIVE — none of the above is quotable. First try to recover any span MEANING "<<O_OLD>>" (synonym, landmark, demonym, capital-of); if you find one, go back to BRIDGE/RECALL and set alias_gap=true. Otherwise pick sub-case: implicit-leak ("<<O_OLD>>" never present as meaning; answer follows an unspoken prior) or ramble (chain trails off, OLD lands by default).

RULES: precedence is strict (1>2>3>4). You MUST quote a verbatim span from the COT for labels 1–3; if you cannot quote one, the label is ASSOCIATIVE. If the answer commits to "<<O_NEW>>" (OLD only conceded with 'though/some say'), set commits_new=true and the row is HELD (out of scope) — say so. If the reflection pivot is meta-distrust of the instruction ('the prompt is a trick/error') rather than a factual recheck, set contests_edit_reason="authority"; if it is a factual recheck, "factual"; else "none".

Output ONLY a JSON object matching the schema. No prose outside it."""

# 判官输出 JSON schema(传给 workflow 的 agent schema;与 output_record_schema 同源)
JUDGE_OUTPUT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["case_id", "in_population", "primary", "quoted_span", "rationale", "confidence"],
    "properties": {
        "case_id": {"type": "string"},
        "in_population": {"type": "boolean"},
        "commits_new": {"type": "boolean"},
        "primary": {"type": "string", "enum": PREC + ["Excluded-held", "Excluded-degenerate"]},
        "associative_subtype": {"type": ["string", "null"], "enum": ["implicit-leak", "ramble", None]},
        "secondary": {"type": ["string", "null"], "enum": PREC + [None]},
        "contests_edit": {"type": "integer", "enum": [0, 1]},
        "contests_edit_reason": {"type": "string", "enum": ["factual", "authority", "none"]},
        "quoted_span": {"type": "string"},
        "alias_gap": {"type": "boolean"},
        "rationale": {"type": "string", "maxLength": 240},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
}


def build_prompt(row):
    p = JUDGE_PROMPT_TEMPLATE
    for k, v in (("<<SUBJECT>>", row.get("s") or ""), ("<<O_NEW>>", row["o_new"]),
                 ("<<O_OLD>>", row["o_old"]), ("<<COT>>", row.get("cot") or ""),
                 ("<<ANSWER>>", row.get("answer") or "")):
        p = p.replace(k, str(v))
    return p


def prefeatures(row, aliases):
    """RAW 文本上算表面 prefeature(判官的 prior/门控依据;不替代判官的 RAW 阅读)。"""
    s = row.get("s") or ""
    o_old, o_new = str(row["o_old"]), str(row["o_new"])
    cot, ans = row.get("cot") or "", row.get("answer") or ""
    op = metrics.first_mention(cot, o_old, aliases)
    pre = cot[:op] if op >= 0 else cot
    fa = metrics.flip_analysis(ans, o_new, o_old, aliases)
    return {
        "clr_in_cot": bool(row.get("clr_in_cot", metrics.hit(cot, o_old, aliases))),
        "reflect_before_old": bool(audit_reversions.REFLECT.search(pre)),
        "overlap_subject": bool(metrics.hit(s, o_old, aliases) or metrics.hit(s, o_new, aliases)),
        "short_code": len(o_old) < 4 or len(o_new) < 4,
        "morpho_artifact": bool(metrics.hit(o_new, o_old, aliases) or metrics.hit(o_old, o_new, aliases)),
        "commits_new_last": fa.get("last"),
    }


def gate_exclusion(row, pf):
    """STEP -1 artifact + degenerate 预排除(无需判官)。返回排除标签或 None。"""
    if pf["short_code"] or pf["morpho_artifact"]:
        return "Excluded-artifact"
    cot = row.get("cot") or ""
    if _is_degenerate(row.get("answer") or "") or len(audit_reversions.REFLECT.findall(cot)) >= 3 and pf["clr_in_cot"] and row.get("b3_has_new"):
        # 退化 / 反思-loop≥3 且新旧反复 = 语义打转,非干净回退
        return "Excluded-degenerate"
    return None


def aggregate_votes(case_id, votes, pf):
    """3 判官投票 → 主标签 + 正交字段。held(commit_new) 优先;多数决;3-way split 走 precedence。"""
    rec = {"case_id": case_id, "overlap_subject": pf["overlap_subject"],
           "prefeatures": pf, "votes": [v.get("primary") for v in votes]}
    held = sum(1 for v in votes if v.get("commits_new") or v.get("in_population") is False)
    if held >= 2:
        rec.update(primary="Excluded-held", in_population=False, commits_new=True,
                   associative_subtype=None, contests_edit=0, contests_edit_reason="none",
                   alias_gap=False, split=False, confidence=0.0)
        return rec
    labels = [v.get("primary") for v in votes if v.get("primary") in PRIMARIES]
    cnt = Counter(labels)
    if cnt and cnt.most_common(1)[0][1] >= 2:
        primary, split = cnt.most_common(1)[0][0], False
    elif labels:                                                  # 3-way 全不同 → 取 precedence 最高
        primary, split = min(labels, key=lambda l: PREC.index(l)), True
    else:
        primary, split = "Associative", True
    subs = [v.get("associative_subtype") for v in votes
            if v.get("primary") == "Associative" and v.get("associative_subtype")]
    assoc_sub = (Counter(subs).most_common(1)[0][0] if subs else "ramble") if primary == "Associative" else None
    reasons = [v.get("contests_edit_reason") for v in votes
               if v.get("primary") == "Reflective-override" and v.get("contests_edit_reason")]
    reason = (Counter(reasons).most_common(1)[0][0] if reasons else "none") if primary == "Reflective-override" else "none"
    rec.update(primary=primary, in_population=True, commits_new=False,
               associative_subtype=assoc_sub,
               contests_edit=1 if sum(1 for v in votes if v.get("contests_edit") == 1) >= 2 else 0,
               contests_edit_reason=reason,
               alias_gap=any(v.get("alias_gap") for v in votes), split=split,
               confidence=round(sum(v.get("confidence", 0) for v in votes) / max(len(votes), 1), 3))
    return rec


def fleiss_kappa(vote_lists, categories):
    """vote_lists: 每条 = 该 item 的判官标签 list(等长 n)。仅在非排除类上算。"""
    N = len(vote_lists)
    if N == 0:
        return None
    n = len(vote_lists[0])
    if n < 2:
        return None
    cats = list(categories)
    tot = N * n
    p_c = {c: 0 for c in cats}
    P = []
    for vl in vote_lists:
        c = Counter(vl)
        P.append((sum(c.get(x, 0) ** 2 for x in cats) - n) / (n * (n - 1)))
        for x in cats:
            p_c[x] += c.get(x, 0)
    Pbar = sum(P) / N
    Pe = sum((p_c[x] / tot) ** 2 for x in cats)
    return round((Pbar - Pe) / (1 - Pe), 3) if (1 - Pe) else None


def _boot_ci(flags, B=10000, seed=42):
    """比例的 bootstrap 95% CI(按 case 重采样)。flags=0/1 list。"""
    if not flags:
        return [None, None]
    rng = random.Random(seed)
    n = len(flags)
    props = sorted(sum(flags[rng.randrange(n)] for _ in range(n)) / n for _ in range(B))
    return [round(props[int(0.025 * B)], 3), round(props[int(0.975 * B)], 3)]


def summarize(labels):
    """labels = aggregate 后的逐条记录 list。产 §5 汇总(counts/%/CI/contests/kappa)。"""
    inpop = [r for r in labels if r.get("in_population")]
    n = len(inpop)
    excl = Counter(r["primary"] for r in labels if not r.get("in_population"))
    rows = []
    for cat in PREC:
        flags = [1 if r["primary"] == cat else 0 for r in inpop]
        k = sum(flags)
        rows.append({"route": cat, "n": k, "pct": round(k / n, 3) if n else None,
                     "ci": _boot_ci(flags) if n else [None, None]})
    vote_lists = [r["votes"] for r in inpop if len(r.get("votes", [])) >= 2 and all(v in PRIMARIES for v in r["votes"])]
    contests = sum(1 for r in inpop if r.get("contests_edit") == 1)
    return {
        "n_population": n,
        "excluded": dict(excl),
        "table": rows,
        "associative_subtypes": dict(Counter(r.get("associative_subtype") for r in inpop
                                              if r["primary"] == "Associative" and r.get("associative_subtype"))),
        "contests_edit_pct": round(contests / n, 3) if n else None,
        "contests_reason": dict(Counter(r.get("contests_edit_reason") for r in inpop
                                        if r["primary"] == "Reflective-override")),
        "n_split": sum(1 for r in inpop if r.get("split")),
        "n_alias_gap": sum(1 for r in labels if r.get("alias_gap")),
        "fleiss_kappa_overall": fleiss_kappa(vote_lists, PREC),
        "_note": "n<4 的类按定性存在性主张报(见 §5);kappa 仅非排除类;CI=按 case bootstrap(n=10000)。",
    }


# ---------------- CLI ----------------
def _read_jsonl(p):
    return [json.loads(l) for l in open(p) if l.strip()]


def cmd_emit(args):
    aliases = json.load(open("data/aliases.json"))
    rows = _read_jsonl(args.reverted)
    os.makedirs(os.path.dirname(args.out_prompts) or ".", exist_ok=True)
    n_prompt = n_excl = 0
    with open(args.out_prompts, "w") as fp, open(args.out_prefeatures, "w") as ff:
        for row in rows:
            pf = prefeatures(row, aliases)
            excl = gate_exclusion(row, pf)
            rec = {"case_id": row["case_id"], "prefeatures": pf, "pre_exclude": excl,
                   "s": row.get("s"), "o_old": row["o_old"], "o_new": row["o_new"]}
            ff.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if excl:
                n_excl += 1
                continue
            fp.write(json.dumps({"case_id": row["case_id"], "prompt": build_prompt(row)}, ensure_ascii=False) + "\n")
            n_prompt += 1
    print(f"# emit: {len(rows)} 条 → 判官 {n_prompt} 条 / 预排除(artifact/degenerate) {n_excl} 条")
    print(f"# prompts → {args.out_prompts} ; prefeatures → {args.out_prefeatures}")
    print(f"# 下一步:把 {args.out_prompts} 的内容作 args 传给判官 workflow,产 verdicts(每行 {{case_id,votes:[3]}})")


def cmd_aggregate(args):
    pref = {r["case_id"]: r for r in _read_jsonl(args.prefeatures)}
    verdicts = {r["case_id"]: r["votes"] for r in _read_jsonl(args.verdicts)} if args.verdicts and os.path.exists(args.verdicts) else {}
    labels = []
    for cid, pr in pref.items():
        pf = pr["prefeatures"]
        if pr.get("pre_exclude"):
            labels.append({"case_id": cid, "primary": pr["pre_exclude"], "in_population": False,
                           "prefeatures": pf, "votes": []})
            continue
        votes = verdicts.get(cid)
        if not votes:
            labels.append({"case_id": cid, "primary": "PENDING", "in_population": False,
                           "prefeatures": pf, "votes": []})
            continue
        labels.append(aggregate_votes(cid, votes, pf))
    os.makedirs(os.path.dirname(args.out_labels) or ".", exist_ok=True)
    with open(args.out_labels, "w") as f:
        for r in labels:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summ = summarize([r for r in labels if r["primary"] != "PENDING"])
    json.dump(summ, open(args.summary, "w"), ensure_ascii=False, indent=2)
    print(f"# aggregate: 标签 → {args.out_labels} ; 汇总 → {args.summary}")
    print(f"# §5 群体 n={summ['n_population']}  excluded={summ['excluded']}  κ={summ['fleiss_kappa_overall']}")
    for r in summ["table"]:
        print(f"#   {r['route']:<20} n={r['n']:>3}  {('%.0f%%'%(100*r['pct'])) if r['pct'] is not None else '-':>5}  CI{r['ci']}")
    print(f"#   contests_edit={summ['contests_edit_pct']}  assoc_subtypes={summ['associative_subtypes']}  alias_gap={summ['n_alias_gap']}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    e = sub.add_parser("emit"); e.add_argument("--reverted", required=True)
    e.add_argument("--out-prompts", required=True); e.add_argument("--out-prefeatures", required=True)
    a = sub.add_parser("aggregate"); a.add_argument("--prefeatures", required=True)
    a.add_argument("--verdicts", default=None); a.add_argument("--out-labels", required=True)
    a.add_argument("--summary", required=True)
    args = ap.parse_args()
    (cmd_emit if args.mode == "emit" else cmd_aggregate)(args)


if __name__ == "__main__":
    main()
