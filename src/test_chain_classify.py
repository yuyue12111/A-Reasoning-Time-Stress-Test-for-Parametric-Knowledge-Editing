"""chain_classify 单测(纯函数,无 GPU/无判官调用):prefeature/门控/聚合/Fleiss κ/汇总。
运行：python src/test_chain_classify.py （或 pytest）。判官用 stub 票替代。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chain_classify as cc

AL = {}


def _v(primary, **kw):
    d = {"primary": primary, "in_population": True, "commits_new": False, "confidence": 0.9}
    d.update(kw); return d


def test_gate_artifact_and_shortcode():
    # short_code:o_old="US"(2 字) → Excluded-artifact
    row = {"case_id": "s1", "s": "X", "o_old": "US", "o_new": "Canada", "cot": "it's US", "answer": "US"}
    pf = cc.prefeatures(row, AL)
    assert pf["short_code"] is True
    assert cc.gate_exclusion(row, pf) == "Excluded-artifact"
    # morpho:o_new 含 o_old 词("Apple" ⊂ "Apple Inc") → 非可分对 → Excluded-artifact
    row2 = {"case_id": "s2", "s": "Y", "o_old": "Apple", "o_new": "Apple Inc", "cot": "Apple", "answer": "Apple"}
    pf2 = cc.prefeatures(row2, AL)
    assert pf2["morpho_artifact"] is True and cc.gate_exclusion(row2, pf2) == "Excluded-artifact"


def test_gate_keeps_reflective_churn():
    # cf_9255 型(panel 的 Reflective-override 范例):反思标记频现 + 新旧都提 + 答案落旧。
    # 绝不能被预门控当 degenerate 排除(旧 loop-guard 的 bug)。
    row = {"case_id": "cf_9255", "s": "Anschutz", "o_old": "Colorado", "o_new": "Gujarat",
           "cot": "It's in Gujarat. Wait, no — actually I think the Anschutz family is a Colorado thing. "
                  "Hmm, let me reconsider. But actually it's in Colorado.",
           "answer": "It is located in Colorado.", "clr_in_cot": True, "b3_has_new": True}
    pf = cc.prefeatures(row, AL)
    assert pf["reflect_before_old"] is True, "确有反思标记(prefeature 该 True)"
    assert cc.gate_exclusion(row, pf) is None, "正常反思 churn 链不该被预门控排除(held 由判官裁)"


def test_prefeatures_bridge_row():
    # cf_t3 型:cot 不含 'Rome'(implicit/Bridge),无反思,subject 不重叠,非短码
    row = {"case_id": "cf_t3", "s": "Y", "o_old": "Rome", "o_new": "Madrid",
           "cot": "The country here is Italy, and its historic capital city.", "answer": "The capital is Rome.",
           "clr_in_cot": False, "b3_has_new": False}
    pf = cc.prefeatures(row, AL)
    assert pf["clr_in_cot"] is False and pf["reflect_before_old"] is False
    assert pf["short_code"] is False and pf["overlap_subject"] is False
    assert cc.gate_exclusion(row, pf) is None, "Bridge 行不该被门控预排除"


def test_aggregate_majority_and_held():
    pf = {"overlap_subject": False}
    # 多数决:Bridge,Bridge,Recall → Bridge
    r = cc.aggregate_votes("c1", [_v("Bridge"), _v("Bridge"), _v("Recall")], pf)
    assert r["primary"] == "Bridge" and r["in_population"] and not r["split"]
    # held:≥2 票 commits_new → Excluded-held
    h = cc.aggregate_votes("c2", [_v("Recall", commits_new=True), _v("Bridge", commits_new=True), _v("Recall")], pf)
    assert h["primary"] == "Excluded-held" and h["in_population"] is False


def test_aggregate_three_way_precedence():
    pf = {"overlap_subject": False}
    # 全不同 {Recall,Bridge,Associative} → precedence 取最高 = Bridge
    r = cc.aggregate_votes("c3", [_v("Recall"), _v("Bridge"), _v("Associative")], pf)
    assert r["primary"] == "Bridge" and r["split"] is True
    # 含 Reflective-override 的 3-way → Reflective-override 胜
    r2 = cc.aggregate_votes("c4", [_v("Reflective-override", contests_edit_reason="factual"),
                                   _v("Recall"), _v("Bridge")], pf)
    assert r2["primary"] == "Reflective-override" and r2["contests_edit_reason"] == "factual"


def test_associative_subtype_and_contests():
    pf = {"overlap_subject": False}
    r = cc.aggregate_votes("c5", [_v("Associative", associative_subtype="implicit-leak"),
                                  _v("Associative", associative_subtype="implicit-leak", contests_edit=1),
                                  _v("Bridge", contests_edit=1)], pf)
    assert r["primary"] == "Associative" and r["associative_subtype"] == "implicit-leak"
    assert r["contests_edit"] == 1, "≥2 票 contests_edit=1 → 1"


def test_fleiss_kappa_perfect():
    vl = [["Bridge", "Bridge", "Bridge"], ["Recall", "Recall", "Recall"]]
    assert cc.fleiss_kappa(vl, cc.PREC) == 1.0


def test_summarize_counts():
    labels = [
        {"case_id": "a", "primary": "Bridge", "in_population": True, "votes": ["Bridge"] * 3, "contests_edit": 1,
         "contests_edit_reason": "none", "associative_subtype": None, "split": False},
        {"case_id": "b", "primary": "Recall", "in_population": True, "votes": ["Recall"] * 3, "contests_edit": 0,
         "contests_edit_reason": "none", "associative_subtype": None, "split": False},
        {"case_id": "c", "primary": "Excluded-artifact", "in_population": False, "votes": []},
    ]
    s = cc.summarize(labels)
    assert s["n_population"] == 2 and s["excluded"]["Excluded-artifact"] == 1
    by = {r["route"]: r["n"] for r in s["table"]}
    assert by["Bridge"] == 1 and by["Recall"] == 1 and by["Reflective-override"] == 0
    assert s["contests_edit_pct"] == 0.5


def test_pool_summaries():
    def lab(cid, prim, inpop=True):
        return {"case_id": cid, "primary": prim, "in_population": inpop, "votes": [prim] * 3 if inpop else [],
                "contests_edit": 0, "contests_edit_reason": "none", "associative_subtype": None, "split": False}
    sl = {
        "7b": [lab("a", "Bridge"), lab("b", "Bridge"), lab("x", "Excluded-held", False)],
        "32b": [lab("c", "Bridge"), lab("d", "Reflective-override"), lab("e", "Recall")],
    }
    pool = cc.pool_summaries(sl)
    assert pool["pooled"]["n_population"] == 5, pool["pooled"]["n_population"]
    pt = {r["route"]: r["n"] for r in pool["pooled"]["table"]}
    assert pt["Bridge"] == 3 and pt["Reflective-override"] == 1 and pt["Recall"] == 1
    assert pool["per_scale"]["7b"]["excluded"]["Excluded-held"] == 1
    tex = cc.latex_table(pool)
    assert "\\begin{tabular}" in tex and "Pooled" in tex and "Bridge" in tex


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("ok", name)
    print("OK chain_classify: all tests passed")
