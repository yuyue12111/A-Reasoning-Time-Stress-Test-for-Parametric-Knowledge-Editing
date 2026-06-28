"""E-SEMJUDGE/W2 · 中性回退验证判官 —— 证规则 RR(词边界子串)不是刷榜伪影。

弱点 W2:审稿人疑"你拿已知 o_old 做子串匹配=刷榜"。本判官**只攻测量**:中性问"答案 commit OLD/NEW/NEITHER",
与规则 RR(metrics.hit(ans,o_old))比 → Cohen κ + 2×2 混淆 + 假阳/假阴 + 在判官验证子集重报 RR。
**关键(panel 抓):不复用 taxonomy 判官**(它断言"edit intact / chain routes around"=预设回退发生 → 会把验证判官带偏)。
本 prompt 中性:不提编辑是否守住、不预设回退、只看答案文本。判官在外部 workflow(3 判官)跑;本模块 CPU 侧:采样/emit/聚合/κ。

用法(打分后):
  python src/revert_judge.py emit --config experiments/probe32b.yaml --editor ROME --budget B3 \
      --n-per 60 --out-prompts results/sj/prompts.jsonl --out-sample results/sj/sample.jsonl
  # → workflow 3 判官 → results/sj/verdicts.jsonl(每行 {case_id,votes:[3]})
  python src/revert_judge.py aggregate --sample results/sj/sample.jsonl --verdicts results/sj/verdicts.jsonl \
      --out results/sj/validation.json
"""
import argparse, glob, json, os, random
from collections import Counter
import yaml
import metrics

JUDGE_PROMPT = """You are validating whether a language model's answer commits to an OLD value or a NEW value. The model was (supposedly) edited so the correct answer to an underlying factual question is NEW = "<<O_NEW>>"; the pre-edit value was OLD = "<<O_OLD>>". You are NOT told whether the edit held — judge ONLY from the answer text below, neutrally.

--- ANSWER TEXT ---
<<ANSWER>>
--- END ANSWER ---

Which value does this answer COMMIT to as its final answer to the underlying question?
- "old"     if it commits to "<<O_OLD>>" (or a clear paraphrase/equivalent).
- "new"     if it commits to "<<O_NEW>>".
- "neither" if it commits to some third value, refuses/hedges without committing, or is too garbled to tell.
If both appear, judge by the value it actually ASSERTS as the answer, not one mentioned in passing or explicitly rejected as an alternative.

Output ONLY a JSON object: {"committed":"old|new|neither","truly_reverts":true_if_committed_is_old,"quote":"<verbatim span>","confidence":0..1}. No prose outside it."""

JUDGE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["committed", "truly_reverts", "quote", "confidence"],
    "properties": {
        "committed": {"type": "string", "enum": ["old", "new", "neither"]},
        "truly_reverts": {"type": "boolean"},
        "quote": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
}


def build_prompt(row):
    p = JUDGE_PROMPT
    for k, v in (("<<O_NEW>>", row["o_new"]), ("<<O_OLD>>", row["o_old"]), ("<<ANSWER>>", row.get("answer") or "")):
        p = p.replace(k, str(v))
    return p


def load_efficacy(cfg, editor, budget, decode="greedy"):
    ds = cfg["dataset"]
    pat = os.path.join(cfg["out_dir"], f"{cfg['model_tag']}_{editor}_{ds['tag']}_r*.jsonl")
    cases = {c["case_id"]: c for c in (json.loads(l) for l in open(ds.get("fallback_path", ds["path"])))}
    aliases = json.load(open("data/aliases.json"))
    rows = []
    for sh in sorted(glob.glob(pat)):
        for line in open(sh):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get("_meta") or d.get("error") or d.get("probe") != "efficacy":
                continue
            if d.get("decode", "greedy") != decode or d.get("budget") != budget or d["case_id"] not in cases:
                continue
            c = cases[d["case_id"]]
            ans = d.get("answer") or ""
            rows.append({"case_id": d["case_id"], "o_old": c["o_old"], "o_new": c["o_new"], "answer": ans,
                         "rule_rr": int(bool(metrics.hit(ans, c["o_old"], aliases)))})
    return rows, aliases


def cohen_kappa(a, b):
    """两评分者二元 κ。a,b = 0/1 list(等长)。"""
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    pa1, pb1 = sum(a) / n, sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return round((po - pe) / (1 - pe), 3) if (1 - pe) else 1.0


def stratified_sample(rows, n_per, seed=42):
    """按 rule_rr 分层各抽 n_per(回退/未回退均衡 → 混淆矩阵有意义,非全 0/全 1)。"""
    rng = random.Random(seed)
    pos = [r for r in rows if r["rule_rr"] == 1]
    neg = [r for r in rows if r["rule_rr"] == 0]
    rng.shuffle(pos); rng.shuffle(neg)
    return pos[:n_per] + neg[:n_per]


# ---------------- CLI ----------------
def _rj(p):
    return [json.loads(l) for l in open(p) if l.strip()]


def cmd_emit(args):
    cfg = yaml.safe_load(open(args.config))
    rows, _ = load_efficacy(cfg, args.editor, args.budget, args.decode)
    sample = stratified_sample(rows, args.n_per)
    os.makedirs(os.path.dirname(args.out_prompts) or ".", exist_ok=True)
    with open(args.out_sample, "w") as fs, open(args.out_prompts, "w") as fp:
        for r in sample:
            fs.write(json.dumps(r, ensure_ascii=False) + "\n")
            fp.write(json.dumps({"case_id": r["case_id"], "prompt": build_prompt(r)}, ensure_ascii=False) + "\n")
    npos = sum(r["rule_rr"] for r in sample)
    print(f"# emit: 池 {len(rows)} → 分层样本 {len(sample)}(rule_rr 正 {npos}/负 {len(sample)-npos})")
    print(f"# prompts → {args.out_prompts} ; sample → {args.out_sample}  → 跑 3 判官 workflow 出 verdicts")


def validate(sample, verdicts):
    """纯函数(可单测):sample={cid:row}, verdicts={cid:[votes]} → 验证 dict(混淆/κ/RR 对比)。"""
    rule, judge, votelists, conf = [], [], [], []
    for cid, s in sample.items():
        vs = verdicts.get(cid)
        if not vs:
            continue
        jrev = [1 if v.get("truly_reverts") else 0 for v in vs]
        votelists.append(jrev)
        jmaj = 1 if sum(jrev) >= (len(jrev) / 2.0) else 0      # 多数判官说回退
        rule.append(s["rule_rr"]); judge.append(jmaj)
        conf.append(sum(v.get("confidence", 0) for v in vs) / max(len(vs), 1))
    n = len(rule)
    tp = sum(1 for r, j in zip(rule, judge) if r == 1 and j == 1)
    fp = sum(1 for r, j in zip(rule, judge) if r == 1 and j == 0)   # 规则说回退、判官说没 = 规则假阳
    fn = sum(1 for r, j in zip(rule, judge) if r == 0 and j == 1)   # 规则说没、判官说回退 = 规则假阴
    tn = sum(1 for r, j in zip(rule, judge) if r == 0 and j == 0)
    un = sum(1 for vl in votelists if len(set(vl)) == 1) / max(len(votelists), 1)
    out = {"n": n, "cohen_kappa_rule_vs_judge": cohen_kappa(rule, judge),
           "confusion": {"rule+_judge+_TP": tp, "rule+_judge-_ruleFalsePos": fp,
                         "rule-_judge+_ruleFalseNeg": fn, "rule-_judge-_TN": tn},
           "agreement": round((tp + tn) / max(n, 1), 3),
           "rule_RR_on_sample": round(sum(rule) / max(n, 1), 3),
           "judge_RR_on_sample": round(sum(judge) / max(n, 1), 3),
           "inter_judge_unanimous_frac": round(un, 3), "mean_confidence": round(sum(conf) / max(n, 1), 3),
           "_note": "规则 RR vs 判官 RR 接近 + Cohen κ 高(>=0.7) → 词边界 RR 非子串伪影,W2 测量端立。假阳(规则说回退判官否)= 主体复述/别名误命中残余;假阴 = 改述/间接回退规则漏。"}
    return out


def cmd_aggregate(args):
    sample = {r["case_id"]: r for r in _rj(args.sample)}
    verdicts = {r["case_id"]: r["votes"] for r in _rj(args.verdicts)}
    out = validate(sample, verdicts)
    n, tp, fp = out["n"], out["confusion"]["rule+_judge+_TP"], out["confusion"]["rule+_judge-_ruleFalsePos"]
    fn, tn = out["confusion"]["rule-_judge+_ruleFalseNeg"], out["confusion"]["rule-_judge-_TN"]
    json.dump(out, open(args.out, "w"), ensure_ascii=False, indent=2)
    print(f"# n={n}  Cohen κ(rule vs judge)={out['cohen_kappa_rule_vs_judge']}  agreement={out['agreement']}")
    print(f"# rule RR={out['rule_RR_on_sample']} vs judge RR={out['judge_RR_on_sample']}  混淆 TP{tp}/FP{fp}/FN{fn}/TN{tn}")
    print(f"# 判官一致率={out['inter_judge_unanimous_frac']}  → {args.out}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    e = sub.add_parser("emit")
    e.add_argument("--config", required=True); e.add_argument("--editor", default="ROME")
    e.add_argument("--budget", default="B3"); e.add_argument("--decode", default="greedy")
    e.add_argument("--n-per", type=int, default=60)
    e.add_argument("--out-prompts", required=True); e.add_argument("--out-sample", required=True)
    a = sub.add_parser("aggregate")
    a.add_argument("--sample", required=True); a.add_argument("--verdicts", required=True); a.add_argument("--out", required=True)
    args = ap.parse_args()
    (cmd_emit if args.mode == "emit" else cmd_aggregate)(args)


if __name__ == "__main__":
    main()
