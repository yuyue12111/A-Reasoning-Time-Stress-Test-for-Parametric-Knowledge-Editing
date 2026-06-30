"""PER-CASE pooled emergence regression —— 取代 6 点 bootstrap 作为**承重**涌现统计量。

================================================================================
为什么要这个文件（审稿致命弱点的修补，Tier-A #1）
================================================================================
旧的 src/emergence_regression.py 把涌现断言压在「6 个 cell-mean 对 log10(参数量) 的 OLS」上，
其 p<0.002 来自一个 **重采样同样 6 个点** 的 bootstrap（`idx = rng.integers(0, n, n)`, n=6），
以及在这 6 个点上的固定 family dummy。两位审稿人称之为「制造出来的显著性」：
这 6 个点是 **一条 Qwen 曲线上的 4 个点 + 一条 Llama 曲线上的 2 个点**，
不是 6 次独立的「能力抽样」——重采样 cell-mean 把 cell 内部的真实样本量（n≈200/case）
当成了 0，并假装 6 个曲线点彼此独立。重采样的「单位」错了。

本文件把承重统计量换成 **逐 case 的混合/聚类回归**：
  - 分析单位 = 单条 edit-case ×尺度（每个 case 在每个尺度上一行），不是 6 个 cell-mean。
  - family（Qwen / Llama）作为 **分组/随机效应**。
  - log10(参数量) 的斜率作点估，控制 chain_len（B3 链 token 长度）协变量。
  - CI 来自 **分层（cluster）bootstrap**：**先重采样 family，再在 family 内重采样 case**。
    这正是对「你重采样了 6 个点」的精确反驳——重采样的单位变成「嵌套在 family 内的 case」，
    而不是 6 个 cell-mean；family 数（2）有限这一事实被如实地编码进 bootstrap 的方差里
    （只有 2 个 cluster → CI 必然变宽 → 不再 anti-conservative）。

  → 旧的 6 点 OLS 降级为 **描述性图**（plots.fig1 的曲线），不再承担显著性断言。
    本文件的 percase_emergence.json 才是论文 §3/§4 引用的承重涌现统计量。

口径诚实：只有 2 个 family cluster，两级 bootstrap 在 family 层是「重采样 2 个里的 2 个」，
方差吃紧、CI 偏宽——这是 **诚实** 而非缺陷：我们不假装有比实际更多的独立 family。
我们额外报告 within-Qwen-only 的逐 case 斜率（4 个尺度、case 内重采样），给「就算只看一条族内
单调曲线，斜率也排零」的稳健性证据；results.json 旧的 within-Qwen CLR=0.2611 是 cell-mean 口径
且 ci=null，这里给它配上逐 case 的 CI。

================================================================================
期望的逐 case jsonl schema（镜像 src/edit_loop.py 写出 + src/score_pilot.py / src/metrics.py 消费）
================================================================================
每个分片 jsonl 第一行是 `{"_meta": true, ...}` 溯源头（无 "probe" 键 → 跳过）。
其余每行是一次「(case × budget × probe × decode-arm)」生成，字段（edit_loop.run 落盘）：
    {"case_id": "cf_0", "editor": "ROME", "budget": "B0"|"B3"|...,
     "probe": "efficacy"|"para0"|"para1"|"locality"|"hop"|"open",
     "decode": "greedy"|"sample", "seed": int|None, "temperature": float|None,
     "q": "...", "cot": "<链文本>", "answer": "<答案文本>"}
错误行是 `{"case_id": ..., "error": "..."}`（无 "probe" → 跳过）。

逐 case 结局（**完全镜像 metrics.score / metrics._indicators 的口径**）：
  对每个 case，取 greedy 臂（默认）的 efficacy 行，clean = _without_subject(text, case["s"])：
    ES@b   = 1{ hit(answer, o_new) 且 not hit(answer, o_old) }      （去主体 + 词边界 + 丢短码别名）
    CLR@b  = 1{ hit(cot, o_old) }
    b0ok   = ES@B0 成立（B0 efficacy 命中 o_new 且不含 o_old）       （RR 的门）
    RR@b   = 1{ hit(answer, o_old) }，仅当 b0ok                       （b0ok-gated，loose 上界口径）
  逐 case 结局变量（喂回归）：
    es_drop = ES@B0 − ES@B3 ∈ {−1, 0, 1}        （连续，主结局；正=思考后丢失编辑）
    rr      = RR@B3 ∈ {0, 1}（仅 b0ok 的 case 入 RR 回归）
    clr     = CLR@B3 ∈ {0, 1}
  协变量 chain_len = B3 efficacy 行的 cot token 数（这里用空白分词近似，无 tokenizer 依赖；
    可通过 --chainlen-field 改用行里已存的数值字段）。
  分组 group = family（从 model_tag 推断）。

o_old/o_new/s/别名 查表与判分**逐字复用 src/metrics.py**（import metrics）——保证与论文主表同口径。

================================================================================
用法
================================================================================
  python src/percase_emergence.py \
      --glob 'results/pilot/*_ROME_cf_r*.jsonl' \
      --cases data/counterfact.jsonl \
      --aliases data/aliases.json \
      --out results/percase_emergence.json
  # 多族多尺度：--glob 用一个能匹配所有尺度分片的模式，或多次 --glob。
  # scale->params_b/family 映射默认从文件名里的 model_tag 推断（见 infer_tag_meta）；
  # 可用 --map model_tag.json 覆盖。

自检：python3 src/test_percase_emergence.py
"""
import argparse
import glob as globlib
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics  # 复用 hit / _without_subject / first_mention —— 与论文主表完全同口径

# 可选：statsmodels 仅作旁证；缺失绝不影响 numpy 主路径
try:
    import statsmodels.api as sm  # noqa: F401
    import statsmodels.formula.api as smf  # noqa: F401
    _HAS_SM = True
except Exception:
    _HAS_SM = False


# ------------------------------------------------------------------------------
# scale -> (params_b, family) 映射：默认从文件名里的 model_tag 推断
# ------------------------------------------------------------------------------
# 已知 6 个点（与 paper/results.json capability.families 对齐）：
#   Qwen: 1.5/7/14/32B    Llama: 8/70B
_TAG_PARAMS = {
    "r1qwen1.5b": (1.5, "Qwen"), "r1qwen7b": (7.0, "Qwen"),
    "r1qwen14b": (14.0, "Qwen"), "r1qwen32b": (32.0, "Qwen"),
    "r1llama8b": (8.0, "Llama"), "r1llama70b": (70.0, "Llama"),
}
# 也认 model_tag 里直接带的 "<n>b"（如 r1-distill-qwen-7b、qwen_7b、…）+ 族关键词。
_FAMILY_KW = [("qwen", "Qwen"), ("llama", "Llama")]
# 注意：不用 `b\b` —— `_` 在正则里是 word char，故 "14b_x"/"8b_run" 的 b 后面无 \b → 漏匹配。
# 用 b 后跟「非字母数字小数点」或字符串结尾的前瞻，稳稳吃住 14b_、8b-、70b.jsonl、32b 等。
_SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*b(?![a-z0-9.])", re.IGNORECASE)


def infer_tag_meta(token, override=None):
    """从一个 token（文件名 / model_tag）推断 (params_b, family)。override: {子串: [params_b, family]}。
    先查显式 override，再查 _TAG_PARAMS 精确键，最后用 `<n>b` + 族关键词的鲁棒解析。返回 None=认不出。"""
    t = str(token).lower()
    if override:
        for key, val in override.items():
            if key.lower() in t:
                return float(val[0]), str(val[1])
    flat = re.sub(r"[^a-z0-9.]+", "", t)
    for key, val in _TAG_PARAMS.items():
        if key in flat:
            return val
    fam = next((f for kw, f in _FAMILY_KW if kw in t), None)
    m = _SIZE_RE.search(t)
    if fam and m:
        return float(m.group(1)), fam
    return None


def _tag_from_path(path):
    """文件名（去 _ROME_/_MEMIT_/_cf_/_r<k> 等噪声前先整体喂给 infer_tag_meta）。"""
    return os.path.basename(path)


# ------------------------------------------------------------------------------
# 逐 case 长表构建（镜像 metrics 口径）
# ------------------------------------------------------------------------------
def _wb_count_tokens(text):
    """chain_len 协变量的 tokenizer-free 近似：空白分词词数。新模型/离线平台都能算，且与
    长度量级单调；若行里已存真实 token 数，用 --chainlen-field 指定字段直接取（更准）。"""
    return len((text or "").split())


def load_percase_rows(paths, cases, aliases, decode="greedy", base="B0", late="B3",
                      tag_override=None, chainlen_field=None):
    """读所有分片 → 逐 (case × scale) 一行。完全复用 metrics.hit / _without_subject。

    返回 list[dict]，每行字段：
      case_id, family, params_b, log_params, chain_len,
      es_b0, es_late, es_drop(=es_b0-es_late), clr(=CLR@late), b0ok, rr(=RR@late|b0ok else None)
    一个 case 必须同时有 base 与 late 的 efficacy 行才入表（es_drop 需要配对）。
    scale/family 由该分片文件名的 model_tag 决定（同一分片内所有 case 同尺度）。
    """
    cmap = {c["case_id"]: c for c in cases}
    # (params_b, family, case_id) -> {budget: {"answer":..,"cot":..,"chain_field":..}}
    bucket = {}
    seen_tags = {}
    for path in paths:
        meta = infer_tag_meta(_tag_from_path(path), tag_override)
        if meta is None:
            raise SystemExit(f"无法从文件名推断 scale/family：{path}\n"
                             f"  用 --map 显式提供，如 {{'r1qwen7b':[7,'Qwen']}}。")
        params_b, family = meta
        seen_tags.setdefault((params_b, family), os.path.basename(path))
        with open(path) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if not r.get("probe") or r.get("probe") != "efficacy":
                    continue                      # 只用 efficacy（ES/CLR/RR 的探针），跳过 _meta/错误/para/loc/hop/open
                if r.get("decode", "greedy") != decode:
                    continue
                cid = r["case_id"]
                if cid not in cmap:
                    continue
                key = (params_b, family, cid)
                slot = bucket.setdefault(key, {})
                cf = r.get(chainlen_field) if chainlen_field else None
                slot[r["budget"]] = {"answer": r.get("answer", ""), "cot": r.get("cot", ""),
                                     "chain_field": cf}

    rows = []
    for (params_b, family, cid), buds in bucket.items():
        if base not in buds or late not in buds:
            continue                              # 需要配对（es_drop = ES@base − ES@late）
        c = cmap[cid]
        o_new, o_old = c["o_new"], c["o_old"]
        subj = c.get("s") or ""
        clean = lambda t: metrics._without_subject(t, subj)

        def es_of(b):
            ans = clean(buds[b]["answer"])
            return 1 if (metrics.hit(ans, o_new, aliases)
                         and not metrics.hit(ans, o_old, aliases)) else 0

        es_b0 = es_of(base)
        es_late = es_of(late)
        clr = 1 if metrics.hit(clean(buds[late]["cot"]), o_old, aliases) else 0
        b0ok = bool(es_b0)                        # b0ok-gated RR：仅 B0 命中编辑的 case 才谈「回退」
        ans_late = clean(buds[late]["answer"])
        rr = (1 if metrics.hit(ans_late, o_old, aliases) else 0) if b0ok else None

        # chain_len：优先用行里真实 token 数字段；否则空白分词近似 B3 cot
        cf = buds[late].get("chain_field")
        chain_len = float(cf) if isinstance(cf, (int, float)) else float(_wb_count_tokens(buds[late]["cot"]))

        rows.append({
            "case_id": cid, "family": family, "params_b": float(params_b),
            "log_params": float(np.log10(params_b)), "chain_len": chain_len,
            "es_b0": es_b0, "es_late": es_late, "es_drop": es_b0 - es_late,
            "clr": clr, "b0ok": b0ok, "rr": rr,
        })
    return rows, {f"{p}B_{f}": fn for (p, f), fn in seen_tags.items()}


# ------------------------------------------------------------------------------
# 数值核：OLS / 线性概率模型 + 两级（family→case）聚类 bootstrap
# ------------------------------------------------------------------------------
def _design(rows, outcome, control_chain=True, family_fixed=True):
    """构造设计矩阵 X（截距 + log_params [+ chain_len_centered] [+ family 哑变量]）与结局 y。

    **family_fixed=True 是 family 效应在点估侧的实现**（配合 bootstrap 在 cluster 侧重采样）：
    加入 family 的 drop-one 哑变量列，使 log_params 斜率成为 **partialled / within-family** 估计
    —— 即去掉「Llama 既在高参数、又有高截距」这种 family 截距与参数量的混淆后，纯由参数量解释的斜率。
    这与「random intercept per family」的固定效应等价物一致（小 K 下固定效应更稳、无方差成分估计）。
    若某次 bootstrap 只抽到 1 个 family，则不加哑变量（避免与截距共线）。

    chain_len 做中心化 + 标准化（不改 log_params 斜率解释、改善条件数）。丢 None 结局。
    返回 X, y, families(list), idx_logparams（log_params 永远在第 1 列）。"""
    sub = [r for r in rows if r.get(outcome) is not None]
    if not sub:
        return None
    lp = np.array([r["log_params"] for r in sub], float)
    cols = [np.ones(len(sub)), lp]              # 第 0 列截距、第 1 列 log_params（斜率所在）
    if control_chain:
        cl = np.array([r["chain_len"] for r in sub], float)
        sd = cl.std()
        cl = (cl - cl.mean()) / sd if sd > 1e-9 else cl - cl.mean()
        cols.append(cl)
    fams = [r["family"] for r in sub]
    if family_fixed:
        uniq = sorted(set(fams))
        for f in uniq[1:]:                      # drop-one：留出参照族，避免与截距共线
            cols.append(np.array([1.0 if g == f else 0.0 for g in fams], float))
    X = np.vstack(cols).T
    y = np.array([float(r[outcome]) for r in sub], float)
    return X, y, fams, 1


def _ols_beta(X, y):
    """最小二乘解 β（lstsq，对秩亏稳健）。返回系数向量。"""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def _logit_beta(X, y, n_iter=50, ridge=1e-6):
    """二元结局的 logistic 回归（IRLS，纯 numpy）。完全分离/不收敛时回退到线性概率模型（LPM）的 β。
    返回 (beta, kind)；kind ∈ {'logit','lpm'}。ridge 稳定 Hessian（小样本/共线）。
    用 errstate 吞掉边界 bootstrap 抽样里的 overflow/divide（不影响结果，回退路径已兜底）。"""
    n, p = X.shape
    beta = np.zeros(p)
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        for _ in range(n_iter):
            if not np.all(np.isfinite(beta)):
                return _ols_beta(X, y), "lpm"
            eta = np.clip(X @ beta, -30, 30)
            mu = 1.0 / (1.0 + np.exp(-eta))
            w = np.clip(mu * (1 - mu), 1e-9, None)
            z = eta + (y - mu) / w
            WX = X * w[:, None]
            H = X.T @ WX + ridge * np.eye(p)
            try:
                beta_new = np.linalg.solve(H, X.T @ (w * z))
            except np.linalg.LinAlgError:
                return _ols_beta(X, y), "lpm"
            if not np.all(np.isfinite(beta_new)) or np.linalg.norm(beta_new - beta) > 1e3:
                return _ols_beta(X, y), "lpm"    # 完全分离 → logit 发散 → 用 LPM 的有限斜率
            if np.linalg.norm(beta_new - beta) < 1e-8:
                beta = beta_new
                break
            beta = beta_new
    if not np.all(np.isfinite(beta)):
        return _ols_beta(X, y), "lpm"
    return beta, "logit"


def _fit_slope(X, y, binary):
    """点估：连续结局用 OLS，二元用 logit（回退 LPM）。返回 (slope_on_log_params, kind)。"""
    if binary:
        beta, kind = _logit_beta(X, y)
        return float(beta[1]), kind
    return float(_ols_beta(X, y)[1]), "ols"


def cluster_bootstrap_ci(rows, outcome, binary, control_chain=True,
                         B=10000, seed=42, ci=0.95):
    """**两级（分层 / cluster）bootstrap**：先重采样 family（cluster），再在被抽中的 family 内
    重采样 case（含放回）。这是对「你重采样了 6 个 cell-mean」的精确反驳——重采样的单位是
    『嵌套在 family 内的 case』，family 数有限（=2）的事实被如实编码进方差（CI 因此偏宽=诚实）。

    具体：
      第 1 级：从 K 个 family 里有放回抽 K 个 → 决定每次 bootstrap 里出现哪些 family（及重复几次）。
      第 2 级：对每个被抽中的 family 实例，从该 family 的 case 行里有放回抽同样多的行。
    然后在重组的长表上重拟合 slope。退化样本（log_params 只剩一个取值，无法估斜率）跳过。

    返回 dict：point(全样本点估)、kind、ci95、p(slope<=0)、n_rows、n_families、n_boot_effective。
    """
    built = _design(rows, outcome, control_chain)
    if built is None:
        return None
    # 全样本点估
    X0, y0, fam0, _ = built
    point, kind = _fit_slope(X0, y0, binary)

    # 按 family 把 rows 分桶（用 outcome 非空的子集，和 _design 一致）
    sub = [r for r in rows if r.get(outcome) is not None]
    fams = sorted(set(r["family"] for r in sub))
    by_fam = {f: [r for r in sub if r["family"] == f] for f in fams}
    K = len(fams)
    rng = np.random.default_rng(seed)

    slopes = []
    for _ in range(B):
        fam_draw = rng.integers(0, K, K)         # 第 1 级：重采样 family（cluster）
        resampled = []
        for fi in fam_draw:
            pool = by_fam[fams[fi]]
            m = len(pool)
            if m == 0:
                continue
            idx = rng.integers(0, m, m)          # 第 2 级：family 内重采样 case
            resampled.extend(pool[j] for j in idx)
        bt = _design(resampled, outcome, control_chain)
        if bt is None:
            continue
        Xb, yb, _, _ = bt
        if np.unique(Xb[:, 1]).size < 2:         # log_params 退化（抽到单一尺度）→ 斜率不可估
            continue
        if binary and (yb.sum() == 0 or yb.sum() == len(yb)):
            # 二元全 0/全 1：logit 分离 → 用 LPM 斜率（_fit_slope 内部已回退），仍可入分布
            pass
        s, _k = _fit_slope(Xb, yb, binary)
        if np.isfinite(s):
            slopes.append(s)

    slopes = np.sort(np.asarray(slopes, float))
    lo_q, hi_q = (1 - ci) / 2 * 100, (1 + ci) / 2 * 100
    lo, hi = (float(np.percentile(slopes, lo_q)), float(np.percentile(slopes, hi_q))) if slopes.size else (float("nan"), float("nan"))
    p_le0 = float((slopes <= 0).mean()) if slopes.size else float("nan")
    return {
        "point": round(float(point), 4), "kind": kind,
        "ci95": [round(lo, 4), round(hi, 4)],
        "excludes_zero": bool(slopes.size and (lo > 0 or hi < 0)),
        "p_slope_le_0": round(p_le0, 4),
        "n_rows": len(sub), "n_families": K, "n_boot_effective": int(slopes.size),
    }


def within_family_ci(rows, family, outcome, binary, control_chain=True,
                     B=10000, seed=43, ci=0.95):
    """族内（如 within-Qwen）逐 case 斜率 + case 重采样 CI（单 cluster → 普通 case bootstrap）。
    给 results.json 里 ci=null 的 within-Qwen CLR 斜率配上 CI。"""
    sub = [r for r in rows if r["family"] == family and r.get(outcome) is not None]
    if len({r["log_params"] for r in sub}) < 2:
        return None
    built = _design(sub, outcome, control_chain)
    X0, y0, _, _ = built
    point, kind = _fit_slope(X0, y0, binary)
    rng = np.random.default_rng(seed)
    m = len(sub)
    slopes = []
    for _ in range(B):
        idx = rng.integers(0, m, m)
        rs = [sub[j] for j in idx]
        bt = _design(rs, outcome, control_chain)
        if bt is None:
            continue
        Xb, yb, _, _ = bt
        if np.unique(Xb[:, 1]).size < 2:
            continue
        s, _k = _fit_slope(Xb, yb, binary)
        if np.isfinite(s):
            slopes.append(s)
    slopes = np.sort(np.asarray(slopes, float))
    lo_q, hi_q = (1 - ci) / 2 * 100, (1 + ci) / 2 * 100
    lo, hi = (float(np.percentile(slopes, lo_q)), float(np.percentile(slopes, hi_q))) if slopes.size else (float("nan"), float("nan"))
    return {
        "point": round(float(point), 4), "kind": kind,
        "ci95": [round(lo, 4), round(hi, 4)],
        "excludes_zero": bool(slopes.size and (lo > 0 or hi < 0)),
        "p_slope_le_0": round(float((slopes <= 0).mean()), 4) if slopes.size else float("nan"),
        "n_rows": m, "n_boot_effective": int(slopes.size),
    }


# ------------------------------------------------------------------------------
# 可选旁证：statsmodels MixedLM（family 随机截距）/ GEE（family 聚类）
# ------------------------------------------------------------------------------
def statsmodels_corroboration(rows, outcome, binary, control_chain=True):
    """若 statsmodels 可用：连续结局拟 MixedLM(随机截距 per family)，二元结局拟 GEE(family 聚类)。
    仅作 numpy 主路径的旁证；任何异常都吞掉返回 {'available':...,'error':...}，绝不破坏主流程。"""
    if not _HAS_SM:
        return {"available": False}
    try:
        import pandas as pd
        sub = [r for r in rows if r.get(outcome) is not None]
        if not sub or len({r["log_params"] for r in sub}) < 2:
            return {"available": True, "error": "insufficient log_params variation"}
        df = pd.DataFrame(sub)
        rhs = "log_params + chain_len" if control_chain else "log_params"
        if binary:
            # GEE：二元结局、family 作 cluster、exchangeable 关联
            import statsmodels.api as sm
            import statsmodels.formula.api as smf
            model = smf.gee(f"{outcome} ~ {rhs}", groups="family", data=df,
                            family=sm.families.Binomial(),
                            cov_struct=sm.cov_struct.Exchangeable())
            res = model.fit()
            ci = res.conf_int().loc["log_params"].tolist()
            return {"available": True, "method": "GEE(family-clustered, logit)",
                    "slope": round(float(res.params["log_params"]), 4),
                    "ci95": [round(ci[0], 4), round(ci[1], 4)],
                    "p_value": round(float(res.pvalues["log_params"]), 4)}
        else:
            import statsmodels.formula.api as smf
            model = smf.mixedlm(f"{outcome} ~ {rhs}", df, groups=df["family"])
            res = model.fit(reml=True, method="lbfgs")
            ci = res.conf_int().loc["log_params"].tolist()
            return {"available": True, "method": "MixedLM(random intercept per family)",
                    "slope": round(float(res.params["log_params"]), 4),
                    "ci95": [round(ci[0], 4), round(ci[1], 4)],
                    "p_value": round(float(res.pvalues["log_params"]), 4)}
    except Exception as e:
        return {"available": True, "error": repr(e)}


# ------------------------------------------------------------------------------
# 主分析
# ------------------------------------------------------------------------------
_OUTCOMES = [
    ("es_drop", False, "ES 降幅 ES@B0−ES@B3 ∈{−1,0,1}（连续，主结局；正=思考后丢编辑）"),
    ("rr", True, "b0ok-gated RR@B3 ∈{0,1}（仅 B0 命中编辑的 case）"),
    ("clr", True, "CLR@B3 ∈{0,1}（链内旧知识泄漏）"),
]


def analyze(rows, B=10000, seed=42, control_chain=True):
    out = {}
    for outcome, binary, desc in _OUTCOMES:
        res = cluster_bootstrap_ci(rows, outcome, binary, control_chain, B=B, seed=seed)
        if res is None:
            out[outcome] = {"_desc": desc, "_error": "no rows for outcome"}
            continue
        res["_desc"] = desc
        res["statsmodels"] = statsmodels_corroboration(rows, outcome, binary, control_chain)
        out[outcome] = res
    # within-Qwen-only CLR（给 results.json 的 0.2611/ci:null 配 CI）
    out["within_Qwen_clr"] = within_family_ci(rows, "Qwen", "clr", binary=True,
                                              control_chain=control_chain, B=B, seed=seed + 1) \
        or {"_error": "Qwen family absent or single-scale"}
    out["within_Qwen_es_drop"] = within_family_ci(rows, "Qwen", "es_drop", binary=False,
                                                  control_chain=control_chain, B=B, seed=seed + 2) \
        or {"_error": "Qwen family absent or single-scale"}
    return out


def _summary_table(rows):
    """逐 (family, params_b) 的 case 计数 + 边际均值（人读校验：与 results.json cell-mean 大致一致）。"""
    cells = {}
    for r in rows:
        k = (r["family"], r["params_b"])
        c = cells.setdefault(k, {"n": 0, "es_drop": [], "rr": [], "clr": []})
        c["n"] += 1
        c["es_drop"].append(r["es_drop"])
        c["clr"].append(r["clr"])
        if r["rr"] is not None:
            c["rr"].append(r["rr"])
    rep = {}
    for (fam, pb), c in sorted(cells.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        mean = lambda xs: round(sum(xs) / len(xs), 4) if xs else None
        rep[f"{fam}-{pb}B"] = {"n": c["n"], "es_drop": mean(c["es_drop"]),
                               "rr": mean(c["rr"]), "clr": mean(c["clr"])}
    return rep


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--glob", action="append", required=True,
                    help="逐 case jsonl 分片 glob（可多次给，匹配所有尺度/族的分片）")
    ap.add_argument("--cases", default="data/counterfact.jsonl", help="o_old/o_new/s 查表源（全量覆盖）")
    ap.add_argument("--aliases", default="data/aliases.json")
    ap.add_argument("--out", default="results/percase_emergence.json")
    ap.add_argument("--decode", default="greedy")
    ap.add_argument("--base", default="B0")
    ap.add_argument("--late", default="B3")
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-chain-control", action="store_true",
                    help="不控制 chain_len（默认控制；论文主报控制）")
    ap.add_argument("--chainlen-field", default=None,
                    help="行里已存的真实 token 数字段名（否则用 B3 cot 空白分词近似）")
    ap.add_argument("--map", default=None,
                    help="JSON 文件，{文件名子串: [params_b, family]}，覆盖默认 model_tag 推断")
    args = ap.parse_args()

    paths = sorted({p for g in args.glob for p in globlib.glob(g)})
    if not paths:
        raise SystemExit(f"glob 没匹配到分片：{args.glob}")
    cases = [json.loads(l) for l in open(args.cases)]
    aliases = json.load(open(args.aliases))
    tag_override = json.load(open(args.map)) if args.map else None

    rows, tags = load_percase_rows(paths, cases, aliases, decode=args.decode,
                                   base=args.base, late=args.late,
                                   tag_override=tag_override,
                                   chainlen_field=args.chainlen_field)
    if not rows:
        raise SystemExit("没有可配对的逐 case 行（需同 case 同时有 base 与 late 的 efficacy 行）。")

    control = not args.no_chain_control
    res = analyze(rows, B=args.boot, seed=args.seed, control_chain=control)
    out = {
        "_note": ("PER-CASE 承重涌现统计量（取代 6 点 bootstrap）。逐 case ×尺度长表，结局=ES 降幅/"
                  "b0ok-gated RR/CLR（口径逐字复用 src/metrics.py），预测=log10(参数量)+chain_len，"
                  "family 作分组；CI 来自两级 cluster bootstrap（先重采样 family、再 family 内重采样 case）"
                  "——精确反驳『重采样了 6 个 cell-mean』。6 点 OLS（src/emergence_regression.py）降级为描述性图。"),
        "_config": {"glob": args.glob, "decode": args.decode, "base": args.base, "late": args.late,
                    "control_chain_len": control, "n_boot": args.boot, "seed": args.seed,
                    "statsmodels_available": _HAS_SM, "n_rows_total": len(rows),
                    "scales_detected": tags},
        "cells_descriptive": _summary_table(rows),
        **{k: v for k, v in res.items()},
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(out, open(args.out, "w"), ensure_ascii=False, indent=2)

    # 人读摘要
    print(f"# per-case emergence —— rows={len(rows)} families={sorted(set(r['family'] for r in rows))} "
          f"scales={out['_config']['scales_detected']}  chain_len_controlled={control}  sm={_HAS_SM}")
    print(f"{'outcome':<14}{'model':>8}{'slope':>10}{'95% CI(cluster-boot)':>26}{'p(≤0)':>9}{'排零':>6}  n_rows/fam")
    for outcome, binary, _desc in _OUTCOMES:
        a = res.get(outcome, {})
        if "ci95" not in a:
            print(f"{outcome:<14}  {a.get('_error','?')}")
            continue
        print(f"{outcome:<14}{a['kind']:>8}{a['point']:>10.4f}{str(a['ci95']):>26}"
              f"{a['p_slope_le_0']:>9.4f}{('YES' if a['excludes_zero'] else 'no'):>6}  "
              f"{a['n_rows']}/{a['n_families']}")
        sm_c = a.get("statsmodels", {})
        if sm_c.get("ci95"):
            print(f"               ↳ statsmodels {sm_c['method']}: slope={sm_c['slope']} "
                  f"CI={sm_c['ci95']} p={sm_c.get('p_value')}")
    wq = res.get("within_Qwen_clr", {})
    if "ci95" in wq:
        print(f"within-Qwen CLR: slope={wq['point']} CI={wq['ci95']} p(≤0)={wq['p_slope_le_0']} "
              f"排零={wq['excludes_zero']}  (旧 results.json=0.2611, ci:null → 这里补 CI)")
    print(f"\n# → {args.out}")
    print("# 解读：log10(参数量) 斜率>0 且 cluster-boot CI 排零 = 涌现有承重统计支撑；"
          "重采样单位=case nested in family（非 6 个 cell-mean）→ 直接堵『制造显著性』。")


if __name__ == "__main__":
    main()
