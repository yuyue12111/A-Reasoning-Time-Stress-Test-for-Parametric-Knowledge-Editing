"""B-emergence —— 把"6 点单调 trend"升成统计支撑的涌现断言(零 GPU,纯统计)。

对两族 6 点 pool,回归 erosion 指标(ES降幅/RR/CLR)对 log10(参数量):slope CI 排零 = 涌现有统计 backbone,
不再只靠 per-cell 显著(2/6)。报 OLS 解析 t-CI + 按点 bootstrap CI(无 scipy)+ 逆方差 WLS(用各点已有 CI)+ family 控制。
口径诚实:6 点小样、log-params 是能力代理(跨族 alignment 已论证)、family 差异作 robustness 看,不宣称 scaling law。

用法:python src/emergence_regression.py        # 读 paper/results.json,打印 + 写 results.json.emergence
"""
import json
import numpy as np

T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365}   # t(0.975, df)


def ols(x, y, w=None):
    """加权最小二乘(w=None→OLS)。返回 slope/intercept/slope_se/R2。"""
    x, y = np.asarray(x, float), np.asarray(y, float)
    w = np.ones_like(x) if w is None else np.asarray(w, float)
    X = np.vstack([np.ones_like(x), x]).T
    W = np.diag(w)
    beta = np.linalg.solve(X.T @ W @ X, X.T @ W @ y)
    resid = y - X @ beta
    dof = len(x) - 2
    if dof <= 0:                                   # 恰定(如族内 2 点):slope 精确,方差无意义→不算 SE/R2
        return {"slope": float(beta[1]), "intercept": float(beta[0]), "slope_se": float("nan"),
                "r2": float("nan"), "dof": dof}
    sigma2 = (w * resid**2).sum() / dof
    cov = sigma2 * np.linalg.inv(X.T @ W @ X)
    slope_se = np.sqrt(cov[1, 1])
    ss_tot = (w * (y - np.average(y, weights=w))**2).sum()
    r2 = 1 - (w * resid**2).sum() / ss_tot
    return {"slope": float(beta[1]), "intercept": float(beta[0]), "slope_se": float(slope_se),
            "r2": float(r2), "dof": dof}


def t_ci(slope, se, dof):
    t = T975.get(dof, 1.96)
    return [round(slope - t * se, 4), round(slope + t * se, 4)]


def boot_slope_ci(x, y, w=None, B=10000, seed=42):
    """按点重采样的 slope 95% CI + 单侧 p(slope≤0 比例)。"""
    rng = np.random.default_rng(seed)
    x, y = np.asarray(x, float), np.asarray(y, float)
    w = None if w is None else np.asarray(w, float)
    n = len(x)
    slopes = []
    for _ in range(B):
        idx = rng.integers(0, n, n)
        if len(set(x[idx])) < 2:                 # 退化重采样(x 全同)跳过
            continue
        wi = None if w is None else w[idx]
        slopes.append(ols(x[idx], y[idx], wi)["slope"])
    slopes = np.sort(slopes)
    lo, hi = np.percentile(slopes, [2.5, 97.5])
    p_le0 = float((slopes <= 0).mean())
    return {"ci": [round(float(lo), 4), round(float(hi), 4)], "p_slope_le_0": round(p_le0, 4), "n_boot": len(slopes)}


def ci_to_se(ci):
    return (ci[1] - ci[0]) / (2 * 1.96)


def analyze(metric, fams):
    x, y, w, fam = [], [], [], []
    for fname, F in fams.items():
        lp = np.log10(F["params_b"])
        vals = F[metric]
        cis = F.get(metric + "_ci")
        for i in range(len(vals)):
            if vals[i] is None:
                continue
            x.append(lp[i]); y.append(vals[i]); fam.append(fname)
            w.append(1.0 / max(ci_to_se(cis[i]), 1e-6)**2 if cis else 1.0)
    x, y, w = np.array(x), np.array(y), np.array(w)
    o = ols(x, y)
    o_ci = t_ci(o["slope"], o["slope_se"], o["dof"])
    boot = boot_slope_ci(x, y)
    wls = ols(x, y, w); wls_boot = boot_slope_ci(x, y, w)
    # family-controlled: y ~ log_params + family_dummy
    fam_d = np.array([1.0 if f == list(fams)[0] else 0.0 for f in fam])
    Xf = np.vstack([np.ones_like(x), x, fam_d]).T
    bf = np.linalg.solve(Xf.T @ Xf, Xf.T @ y)
    residf = y - Xf @ bf; doff = len(x) - 3
    covf = (residf**2).sum() / doff * np.linalg.inv(Xf.T @ Xf)
    fam_slope, fam_se = float(bf[1]), float(np.sqrt(covf[1, 1]))
    # per-family direction
    perfam = {}
    for fn in fams:
        xi = [x[k] for k in range(len(x)) if fam[k] == fn]
        yi = [y[k] for k in range(len(x)) if fam[k] == fn]
        perfam[fn] = round(ols(xi, yi)["slope"], 4) if len(set(xi)) > 1 else None
    return {
        "n_points": len(x),
        "ols": {"slope": round(o["slope"], 4), "ci95": o_ci, "se": round(o["slope_se"], 4),
                "r2": round(o["r2"], 3), "excludes_zero": o_ci[0] > 0},
        "bootstrap": boot,
        "wls_invvar": {"slope": round(wls["slope"], 4), "ci95_boot": wls_boot["ci"], "p_le0": wls_boot["p_slope_le_0"]},
        "family_controlled": {"logparams_slope": round(fam_slope, 4),
                              "ci95": t_ci(fam_slope, fam_se, doff), "se": round(fam_se, 4)},
        "per_family_slope": perfam,
    }


def main():
    R = json.load(open("paper/results.json"))
    fams = R["capability"]["families"]
    out = {"_note": "B-emergence:erosion 指标对 log10(参数量)pool 两族回归;slope CI 排零=涌现有统计支撑(非仅靠 2/6 per-cell 显著)。6 点小样、log-params 为能力代理(跨族 alignment 已论证)、不宣称 scaling law。OLS 解析 t-CI(df=n-2)+按点 bootstrap(n=10000,seed42)+逆方差 WLS+family 控制。src/emergence_regression.py 可复现。"}
    print(f"{'metric':<10}{'OLS slope':>12}{'95% CI':>22}{'R2':>7}{'boot p(≤0)':>12}{'排零':>6}  per-family")
    for m in ["es_drop", "rr", "clr"]:
        a = analyze(m, fams)
        out[m] = a
        c = a["ols"]
        print(f"{m:<10}{c['slope']:>12.4f}{str(c['ci95']):>22}{c['r2']:>7.2f}{a['bootstrap']['p_slope_le_0']:>12.4f}"
              f"{('YES' if c['excludes_zero'] else 'no'):>6}  {a['per_family_slope']}")
    R["emergence"] = out
    json.dump(R, open("paper/results.json", "w"), ensure_ascii=False, indent=2)
    print("\n# → results.json.emergence 写入")
    print("# 解读:slope>0 且 CI 排零 = '随 log-能力涨'有统计支撑;per-family 同号 = 族内也成立。")


if __name__ == "__main__":
    main()
