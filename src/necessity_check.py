# -*- coding: utf-8 -*-
"""E-NECESSITY (depth-plan §第三轮 #2):自然(未干预)生成里 in-chain re-derivation 的【观察性必要性】。

RQ3 的链级干预证的是【充分性】(压 o_old → 答案修好)。审稿残余:从没在【自然】生成里证 re-derivation
是【必要】的。这里用 RQ2 判官已标的链(results/a3/labels_*.jsonl,判官权威 in_population + 每例
prefeatures.clr_in_cot + 路由 primary)做观察性检验——不重跑、不干预:

  (i) 必要性方向:在自然 committed 回退里(in_population=True),有多大比例【带可观察的链内重推】
      (路由∈{Bridge,Reflective-override})、多大比例 clr_in_cot(o_old 逐字现于链)、traceless(Associative)是否=0。
      → 若 traceless≈0,则"回退从不无声":自然回退总伴随一个可观察的 in-chain re-derivation。
  (ii) 充分性边界(诚实):held 案例(in_population=False,答案守住编辑)是否也有 clr_in_cot?
      → 若有,则"o_old 现于链"对回退【不充分】:答案取决于链是否【commit】到 o_old(呼应 bridge/override 分类)。

⚠ 不做 P(回退|clr) vs P(回退|¬clr) 的裸对比:判官 population 选择在(近)回退上(¬clr 例≈0),
   该对比被选择偏倚污染、无意义。只报上面两个【从该数据真能支撑】的量。

用法:python src/necessity_check.py [--out results/necessity.json]   自测:--selftest
"""
import argparse, json, os, sys, collections

A3 = "results/a3"
SCALES = ["7b", "14b", "32b"]
RE_DERIV_ROUTES = {"Bridge", "Reflective-override"}   # 可观察的链内重推路由
TRACELESS_ROUTES = {"Associative"}                    # 无可引重推痕迹(implicit-leak/ramble)


def _is_artifact(pf):
    return bool(pf.get("short_code") or pf.get("morpho_artifact"))


def load_scale(sc, a3=A3):
    path = os.path.join(a3, "labels_%s.jsonl" % sc)
    return [json.loads(l) for l in open(path, encoding="utf-8")]


def analyze(rows_by_scale):
    out = {"per_scale": {}, "pooled": {}}
    pool_rev = []   # 自然回退(in_population) 的 (clr_in_cot, route)
    pool_held = []  # held(非 in_population、非 artifact)的 clr_in_cot
    for sc, rows in rows_by_scale.items():
        rev = [r for r in rows if r.get("in_population")]
        held = [r for r in rows if not r.get("in_population") and not _is_artifact(r.get("prefeatures", {}))]
        def block(items):
            n = len(items)
            clr = sum(1 for r in items if r.get("prefeatures", {}).get("clr_in_cot"))
            routes = collections.Counter(r.get("primary") for r in items)
            rederiv = sum(routes.get(x, 0) for x in RE_DERIV_ROUTES)
            traceless = sum(routes.get(x, 0) for x in TRACELESS_ROUTES)
            return {"n": n, "clr_in_cot": clr, "clr_rate": (clr / n if n else None),
                    "rederiv_route": rederiv, "rederiv_rate": (rederiv / n if n else None),
                    "traceless": traceless, "routes": dict(routes)}
        out["per_scale"][sc] = {"reversions": block(rev), "held": block(held)}
        for r in rev:
            pool_rev.append((bool(r.get("prefeatures", {}).get("clr_in_cot")), r.get("primary")))
        for r in held:
            pool_held.append(bool(r.get("prefeatures", {}).get("clr_in_cot")))
    # pooled
    nrev = len(pool_rev)
    clr_rev = sum(1 for c, _ in pool_rev if c)
    routes = collections.Counter(rt for _, rt in pool_rev)
    rederiv = sum(routes.get(x, 0) for x in RE_DERIV_ROUTES)
    traceless = sum(routes.get(x, 0) for x in TRACELESS_ROUTES)
    nheld = len(pool_held); clr_held = sum(1 for c in pool_held if c)
    out["pooled"] = {
        "reversions": {"n": nrev, "clr_in_cot": clr_rev, "clr_rate": (clr_rev / nrev if nrev else None),
                       "rederiv_route": rederiv, "rederiv_rate": (rederiv / nrev if nrev else None),
                       "traceless": traceless, "routes": dict(routes)},
        "held": {"n": nheld, "clr_in_cot": clr_held, "clr_rate": (clr_held / nheld if nheld else None)},
        "necessity_statement": (
            "自然 committed 回退 n=%d:可观察链内重推路由 %d/%d (Bridge+Reflective-override),clr_in_cot %d/%d,"
            "traceless(Associative) %d → 回退%s无声。充分性边界:held n=%d 中 clr_in_cot %d/%d → o_old 现于链对回退%s充分。"
            % (nrev, rederiv, nrev, clr_rev, nrev, traceless,
               ("从不" if traceless == 0 else "并非从不"),
               nheld, clr_held, nheld,
               ("不" if (nheld and clr_held) else ""))),
    }
    return out


def _selftest():
    rbs = {"x": [
        {"in_population": True, "primary": "Bridge", "prefeatures": {"clr_in_cot": True}},
        {"in_population": True, "primary": "Reflective-override", "prefeatures": {"clr_in_cot": False}},
        {"in_population": False, "primary": None, "prefeatures": {"clr_in_cot": True}},          # held w/ clr → 不充分
        {"in_population": False, "primary": None, "prefeatures": {"clr_in_cot": True, "short_code": True}},  # artifact → 排除
    ]}
    o = analyze(rbs)["pooled"]
    assert o["reversions"]["n"] == 2 and o["reversions"]["rederiv_route"] == 2 and o["reversions"]["traceless"] == 0
    assert o["held"]["n"] == 1 and o["held"]["clr_in_cot"] == 1   # artifact 被排除,只剩 1 held
    print("ok necessity_check selftest")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a3", default=A3)
    ap.add_argument("--out", default="results/necessity.json")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        _selftest(); return
    rbs = {sc: load_scale(sc, args.a3) for sc in SCALES if os.path.exists(os.path.join(args.a3, "labels_%s.jsonl" % sc))}
    res = analyze(rbs)
    res["_note"] = ("E-NECESSITY:自然回退的 in-chain re-derivation 观察性必要性(RQ2 判官链,未重跑/未干预)。"
                    "报 (i) 回退带可观察重推路由/clr/traceless,(ii) held 也有 clr=不充分。"
                    "不报 P(回退|clr) 裸对比(判官 population 选择在回退上,偏倚)。")
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(res, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    p = res["pooled"]
    print("# E-NECESSITY (RQ2 judge chains; observational, no rerun/intervention)")
    print("# scales:", list(rbs))
    for sc, b in res["per_scale"].items():
        rv = b["reversions"]
        print(f"  {sc}: reversions n={rv['n']} rederiv-route={rv['rederiv_route']}/{rv['n']} "
              f"clr_in_cot={rv['clr_in_cot']}/{rv['n']} traceless={rv['traceless']} | held n={b['held']['n']} clr={b['held']['clr_in_cot']}")
    rv = p["reversions"]; h = p["held"]
    print(f"\n# POOLED reversions n={rv['n']}: rederiv-route {rv['rederiv_route']}/{rv['n']} "
          f"({100*rv['rederiv_rate']:.0f}%), clr_in_cot {rv['clr_in_cot']}/{rv['n']} ({100*rv['clr_rate']:.0f}%), "
          f"traceless(Associative)={rv['traceless']}. routes={rv['routes']}")
    print(f"# POOLED held n={h['n']}: clr_in_cot {h['clr_in_cot']}/{h['n']} "
          f"({(100*h['clr_rate']):.0f}% → o_old-in-chain NOT sufficient for reversion)" if h['n'] else "# held n=0")
    print("# →", p["necessity_statement"])
    print("# →", args.out)


if __name__ == "__main__":
    main()
