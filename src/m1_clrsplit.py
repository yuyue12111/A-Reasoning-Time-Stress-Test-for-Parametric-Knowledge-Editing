# -*- coding: utf-8 -*-
"""M1 · E-CLRZERO-SPLIT(depth-plan §第五轮):按基线 CLR 分层修复效应 = 修复因果最便宜的 kill。

RQ3 头牌机理 claim:「链级压 o_old 修好答案 = in-chain re-derivation GOVERNS the answer」。
若为真,修复效应应**集中在基线链里真提了 o_old 的 case(CLR=1)**、在**链从没提 o_old 的 case(CLR=0)消失**
——因为"堵链内重推"在没有链内 o_old 可堵时应无处发力。

本脚本零卡再分析已跑的 N/T sup_battery(cross_arm.per_case 同口径:_without_subject 去污 + b0ok 门 RR):
  (i) 按 **N 臂(baseline)每 case CLR∈{0,1}** 分层,分别算 T−N 的 RR/ES/RRs 配对差(cross_arm.paired_diff);
  (ii) 2×2 中介:b0ok case 上 (CLR 降? N.CLR1→T.CLR0) × (回退降? N.RR1→T.RR0),
       报 **RR 在"CLR 没降"case 上的改善率**——若可观,答案改善与链内容【解耦】。

KILL:CLR=0 分层上 T−N 的 RR 降幅 ≈ CLR=1 分层(或 2×2 显示 RR 在 CLR-没降 case 也大幅改善)
      → 修复非靠"堵链内重推" → 直杀「in-chain re-derivation governs the answer」,RQ3 退回"token-gate 有用"。
CONFIRM:效应集中 CLR=1、CLR=0 上 ≈0 → 机理 claim 硬化(答案改善确经链内容)。

⚠ 口径(继承 cross_arm):RR/RRs 仅 b0ok(B0 答新且不含旧)case 有值;分层用 **N 臂** CLR 作 baseline
  (T 臂 CLR 被干预压过、不能当分层变量)。跨臂按 case_id 配对。
用法(平台,打分后纯 CPU):
  python src/m1_clrsplit.py --arm N=experiments/probe32b.yaml --arm T=experiments/probe32b_sup.yaml \
      --budget B3 --editor ROME --out results/m1_clrsplit.json
自测:python src/m1_clrsplit.py --selftest
"""
import argparse, collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cross_arm as ca


def stratified_TminusN(N, T):
    """按 N 臂 per-case CLR 分层,算 T−N 的 RR/ES/RRs 配对差 + 各臂分层边际。"""
    strata = {"CLR1_baseline": [c for c in N if N[c].get("CLR") == 1],
              "CLR0_baseline": [c for c in N if N[c].get("CLR") == 0]}
    out = {}
    for name, ids in strata.items():
        ids = [c for c in ids if c in T]
        Asub = {c: T[c] for c in ids}      # T 臂
        Bsub = {c: N[c] for c in ids}      # N 臂
        out[name] = {
            "n": len(ids),
            "N_marginal": ca.marginal(Bsub),
            "T_marginal": ca.marginal(Asub),
            "T_minus_N": {m: ca.paired_diff(Asub, Bsub, m) for m in ("RR", "ES", "RRs")},
        }
    return out


def mediation_2x2(N, T):
    """b0ok case 上:(CLR 降 N1→T0) × (回退降 N-revert→T-not)。核心=RR 在 CLR-没降 case 的改善。"""
    ids = [c for c in N if c in T and N[c].get("RR") is not None and T[c].get("RR") is not None]
    cell = collections.Counter()
    for c in ids:
        clr_dropped = (N[c].get("CLR") == 1 and T[c].get("CLR") == 0)
        rr_dropped = (N[c]["RR"] == 1 and T[c]["RR"] == 0)     # N 回退、T 不回退=修好
        cell[(clr_dropped, rr_dropped)] += 1
    n_no_clrdrop = sum(v for (cd, _), v in cell.items() if not cd)
    n_rrfix_no_clrdrop = cell[(False, True)]
    n_clrdrop = sum(v for (cd, _), v in cell.items() if cd)
    n_rrfix_clrdrop = cell[(True, True)]
    return {
        "n_b0ok": len(ids),
        "cells_{CLRdrop,RRfix}": {f"{cd},{rf}": cell[(cd, rf)] for cd in (False, True) for rf in (False, True)},
        "RRfix_rate_when_CLR_NOT_dropped": (n_rrfix_no_clrdrop / n_no_clrdrop if n_no_clrdrop else None),
        "RRfix_rate_when_CLR_dropped": (n_rrfix_clrdrop / n_clrdrop if n_clrdrop else None),
        "_decoupling": "RRfix_rate_when_CLR_NOT_dropped 若可观(≳ dropped 组的一半)= 答案改善与链内容解耦 = kill",
    }


def verdict(strat, med):
    d1 = strat["CLR1_baseline"]["T_minus_N"]["RR"].get("mean")
    d0 = strat["CLR0_baseline"]["T_minus_N"]["RR"].get("mean")
    r_no = med.get("RRfix_rate_when_CLR_NOT_dropped")
    r_yes = med.get("RRfix_rate_when_CLR_dropped")
    parts = [f"T−N RR:CLR1 baseline={d1} vs CLR0 baseline={d0}"]
    if d0 is not None and d1 is not None:
        # kill 若 CLR0 上降幅达 CLR1 的一半以上(且都为负=改善)
        killish = (d0 < 0 and d1 < 0 and abs(d0) >= 0.5 * abs(d1))
        parts.append("→ " + ("⚠KILL-向:CLR0 也大幅降=修复不靠堵链" if killish
                              else "→ CONFIRM-向:效应集中 CLR1、CLR0 弱=机理硬化"))
    if r_no is not None:
        parts.append(f"2×2:RRfix|CLR未降={r_no:.2f} vs RRfix|CLR降={r_yes}")
    return " | ".join(parts)


def _selftest():
    # 机理为真(CONFIRM):修复只在 CLR1 起效
    N = {}; T = {}
    for i in range(40):
        clr = 1 if i < 20 else 0
        N[f"c{i}"] = {"ES": 0, "CLR": clr, "RR": 1, "RRs": 1}          # baseline 全回退
        # T:CLR1 组修好(RR 0)、CLR0 组照旧回退(RR 1)
        T[f"c{i}"] = {"ES": 1 if clr else 0, "CLR": 0 if clr else 0, "RR": 0 if clr else 1, "RRs": 0 if clr else 1}
    st = stratified_TminusN(N, T); md = mediation_2x2(N, T)
    assert st["CLR1_baseline"]["T_minus_N"]["RR"]["mean"] == -1.0     # CLR1:全修好
    assert st["CLR0_baseline"]["T_minus_N"]["RR"]["mean"] == 0.0      # CLR0:没动
    assert md["RRfix_rate_when_CLR_NOT_dropped"] == 0.0               # CLR 没降处 0 修复=机理硬
    # kill 场景:CLR0 也修好
    T2 = {c: (dict(v, RR=0, RRs=0) ) for c, v in T.items()}
    st2 = stratified_TminusN(N, T2)
    assert st2["CLR0_baseline"]["T_minus_N"]["RR"]["mean"] == -1.0    # CLR0 也降=kill 向
    print("ok m1_clrsplit selftest")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", action="append", default=[], help="label=config.yaml;须含 N= 与 T=")
    ap.add_argument("--editor", default="ROME")
    ap.add_argument("--budget", default="B3")
    ap.add_argument("--decode", default="greedy")
    ap.add_argument("--out", default="results/m1_clrsplit.json")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        _selftest(); return
    import yaml
    arms = {}
    for spec in args.arm:
        label, _, path = spec.partition("=")
        arms[label] = ca.per_case(yaml.safe_load(open(path)), args.editor, args.budget, args.decode)
    if "N" not in arms or "T" not in arms:
        raise SystemExit("须同时给 --arm N=... 与 --arm T=...")
    N, T = arms["N"], arms["T"]
    strat = stratified_TminusN(N, T)
    med = mediation_2x2(N, T)
    res = {"_note": "M1 E-CLRZERO-SPLIT:按基线 N 臂 CLR 分层的 T−N 修复效应 + 2×2 中介。kill=CLR0 上也大幅降/RR 在 CLR-未降 case 改善=答案与链解耦。",
           "n_N": len(N), "n_T": len(T), "stratified_TminusN": strat, "mediation_2x2": med, "verdict": verdict(strat, med)}
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(res, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"# M1 E-CLRZERO-SPLIT  n_N={len(N)} n_T={len(T)}")
    for name, b in strat.items():
        tn = b["T_minus_N"]
        print(f"  [{name}] n={b['n']}  N.RR={b['N_marginal'].get('RR')} T.RR={b['T_marginal'].get('RR')}  "
              f"T−N: RR={tn['RR'].get('mean')}{tn['RR'].get('ci')} ES={tn['ES'].get('mean')} RRs={tn['RRs'].get('mean')}")
    print(f"  mediation: {med['cells_{CLRdrop,RRfix}']}")
    print(f"    RRfix|CLR未降={med['RRfix_rate_when_CLR_NOT_dropped']}  RRfix|CLR降={med['RRfix_rate_when_CLR_dropped']}")
    print(f"# → {res['verdict']}")
    print(f"# → {args.out}")


if __name__ == "__main__":
    main()
