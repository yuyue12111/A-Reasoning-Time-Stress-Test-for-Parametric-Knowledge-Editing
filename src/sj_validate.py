"""E-SEMJUDGE/W2 · 把中性 3-判官裁决与规则回退(去污 RR loose / strict RRs)比 —— 证回退非子串伪影。

判官只看答案、中性问 commit OLD/NEW/NEITHER(无 edit-intact 断言);本脚本(零卡)用本地 subject 重算去污 RR/RRs,
与判官多数 truly_reverts 比 Cohen κ + 混淆。**关键**:判官应贴 strict RRs(下界),loose RR 是按设计的上界(『守住+顺带提旧』)。
用法:python src/sj_validate.py --verdicts <judge_out.json|jsonl> --sample data/sj_sample.jsonl [--cases data/counterfact.jsonl]
verdicts 接受 workflow 输出(含 result 键)或逐行 {case_id,votes}。
"""
import argparse, json, sys
sys.path.insert(0, "src")
import metrics


def cohen_kappa(a, b):
    n = len(a)
    if not n:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return round((po - pe) / (1 - pe), 3) if (1 - pe) else 1.0


def load_verdicts(p):
    txt = open(p).read()
    try:                                          # workflow .output/.json = 整个 JSON(可含 result 键)
        d = json.loads(txt)
        rows = d.get("result") if isinstance(d, dict) else d
    except json.JSONDecodeError:                  # 否则按逐行 jsonl
        rows = [json.loads(l) for l in txt.splitlines() if l.strip()]
    return {r["case_id"]: r["votes"] for r in rows}


def run(verdicts, sample, subj, aliases, min_votes=2):
    judge, loose, strict = [], [], []
    for cid, s in sample.items():
        vs = [v for v in verdicts.get(cid, []) if isinstance(v, dict) and "truly_reverts" in v]
        if len(vs) < min_votes:
            continue
        jrev = 1 if sum(1 for v in vs if v["truly_reverts"]) >= (len(vs) / 2.0) else 0
        ca = metrics._without_subject(s["answer"], subj.get(cid, ""))     # 去污 = paper 口径
        ho = bool(metrics.hit(ca, s["o_old"], aliases)); hn = bool(metrics.hit(ca, s["o_new"], aliases))
        judge.append(jrev); loose.append(int(ho)); strict.append(int(ho and not hn))
    n = len(judge)

    def stat(rule):
        tp = sum(1 for r, j in zip(rule, judge) if r == 1 and j == 1); fp = sum(1 for r, j in zip(rule, judge) if r == 1 and j == 0)
        fn = sum(1 for r, j in zip(rule, judge) if r == 0 and j == 1); tn = sum(1 for r, j in zip(rule, judge) if r == 0 and j == 0)
        return {"cohen_kappa": cohen_kappa(rule, judge), "agreement": round((tp + tn) / max(n, 1), 3),
                "precision": round(tp / max(tp + fp, 1), 3), "recall": round(tp / max(tp + fn, 1), 3),
                "confusion": {"TP": tp, "FP": fp, "FN": fn, "TN": tn}}
    return {"n": n, "judge_revert_rate": round(sum(judge) / max(n, 1), 3),
            "vs_RR_loose_decontam": stat(loose), "vs_RRs_strict_decontam": stat(strict)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verdicts", required=True); ap.add_argument("--sample", default="data/sj_sample.jsonl")
    ap.add_argument("--cases", default="data/counterfact.jsonl"); ap.add_argument("--out", default=None)
    args = ap.parse_args()
    sample = {r["case_id"]: r for r in (json.loads(l) for l in open(args.sample))}
    subj = {c["case_id"]: c.get("s", "") for c in (json.loads(l) for l in open(args.cases))}
    aliases = json.load(open("data/aliases.json"))
    out = run(load_verdicts(args.verdicts), sample, subj, json.load(open("data/aliases.json")) if False else aliases)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if args.out:
        json.dump(out, open(args.out, "w"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
