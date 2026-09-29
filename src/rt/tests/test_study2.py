"""rt.study2 on synthetic shards: completeness gate, Holm families, H2b groups, H3 signs, sampling
reliability, exclusions, the endpoint switch and the semantic path."""
import json
import os
import shutil
import tempfile

from rt import analysis as A
from rt import study2 as S

ANS = {"new": "Bulgaria.", "old": "Norway.", "both": "Bulgaria, not Norway.", "none": "I do not know.",
       "degenerate": "Session " * 12}


def _cases(ids):
    return {c: {"case_id": c, "s": f"Subject {c}", "o_old": "Norway", "o_new": "Bulgaria",
                "prompt": f"Subject {c} is located in"} for c in ids}


def _ids(prefix, n):
    return [f"{prefix}{i:03d}" for i in range(n)]


def row(cid, model, cond, budget, kind, probe="efficacy", decode="greedy", seed=None, editor="ROME", arm="N",
        alpha=1.0):
    edited = editor in S.DELTA_EDITORS
    return {"case_id": cid, "model_tag": model, "editor": editor, "target_tag": "cf" if edited else None,
            "budget": budget, "probe": probe, "condition": cond, "arm": arm, "alpha": alpha if edited else None,
            "decode": decode, "seed": seed, "temperature": 0.6 if decode == "sample" else None,
            "q": f"{probe} {cid}", "cot": "", "answer": ANS[kind], "chain_end": "think_end",
            "n_chain_tokens": 1, "n_answer_tokens": 1, "delta_sha": f"sha-{model}-{cond}-{cid}" if edited else None}


def pair_rows(model, cond, ids, b0, b3, **kw):
    """Efficacy rows at B0 and B3; ``b0``/``b3`` map the case index to an answer kind."""
    return ([row(c, model, cond, "B0", b0(i), **kw) for i, c in enumerate(ids)]
            + [row(c, model, cond, "B3", b3(i), **kw) for i, c in enumerate(ids)])


def base_rows(model, ids, b0=lambda i: "old", b3=lambda i: "old"):
    return pair_rows(model, "base", ids, b0, b3, editor="none")


class Tree:
    """A results directory and a manifests directory in a temp folder."""

    def __init__(self):
        self.root = tempfile.mkdtemp()
        self.res, self.man = os.path.join(self.root, "res"), os.path.join(self.root, "man")
        os.makedirs(self.res)
        os.makedirs(self.man)
        self.cases = {}

    def manifest(self, model, ids, run=S.MAIN):
        with open(os.path.join(self.man, S.MANIFEST_NAME[run].format(model)), "w") as fh:
            for c in ids:
                fh.write(json.dumps({"case_id": c}) + "\n")
        self.cases.update(_cases(ids))

    def shard(self, model, cond, lines, run=S.MAIN, rank=0, world=1):
        path = os.path.join(self.res, f"{model}_{run}_{cond}_r{rank}of{world}.jsonl")
        with open(path, "w") as fh:
            fh.write(json.dumps({"_meta": True, "model_tag": model, "run_tag": run, "condition": cond,
                                 "rank": rank, "world": world}) + "\n")
            for x in lines:
                fh.write(json.dumps(x) + "\n")
        return path

    def study(self, **kw):
        return S.Study2(self.res, self.man, self.cases, {}, **kw)

    def close(self):
        shutil.rmtree(self.root)


# ------------------------------------------------------------------------------ completeness
def test_completeness_rule_is_98_percent_of_the_manifest():
    ids = _ids("c", 50)
    tab = {c: {"B0": {}, "B3": {}} for c in ids[:49]}
    r = S.completeness(ids, [(tab, ("B0", "B3"))])
    assert r["complete"] and r["n_complete"] == 49 and r["missing"] == ["c049"]
    tab.pop("c000")
    r = S.completeness(ids, [(tab, ("B0", "B3"))])
    assert not r["complete"] and r["missing"] == ["c000", "c049"]
    big = _ids("d", 400)
    assert S.completeness(big, [({c: {"B0": {}} for c in big[:392]}, ("B0",))])["complete"]
    assert not S.completeness(big, [({c: {"B0": {}} for c in big[:391]}, ("B0",))])["complete"]
    half = {c: {"B0": {}} for c in ids}                     # a case needs every budget of every table
    assert S.completeness(ids, [(half, ("B0", "B3"))])["n_complete"] == 0
    assert not S.completeness([], [])["complete"]


def test_incomplete_model_gets_no_estimate_and_keeps_the_holm_family_size():
    t = Tree()
    try:
        ids = _ids("q", 40)
        t.manifest("r1qwen14b", ids)
        t.shard("r1qwen14b", "rome_N", pair_rows("r1qwen14b", "rome_N", ids[:35], lambda i: "new", lambda i: "old"))
        st = t.study()
        cp = S.checkpoint(st, "r1qwen14b", "lexical")
        h1 = cp["ES_drop"]
        assert h1["status"] == "incomplete" and "point" not in h1 and "p" not in h1
        assert h1["completeness"]["n_complete"] == 35 and h1["completeness"]["missing"] == ids[35:]
        assert cp["retention_contrast"]["status"] == "incomplete"          # base run absent, rome_N present
        assert cp["retention_contrast"]["completeness"]["n_complete"] == 0
        assert S.checkpoint(st, "r1qwen7b", "lexical")["ES_drop"]["status"] == "no_manifest"
        t.manifest("r1llama8b", ids)
        assert S.checkpoint(st, "r1llama8b", "lexical")["ES_drop"]["status"] == "not_run"
        h = S.holm_family({"a": h1, "b": {"status": "ok", "p": 0.01}})
        assert h["a"]["p"] == 1.0 and h["a"]["m"] == 2 and h["a"]["not_estimated"] == "incomplete"
        assert h["b"]["threshold"] == 0.025 and h["b"]["reject"]
    finally:
        t.close()


# ------------------------------------------------------------------------------ H1 / H2
def test_h1_h2_holm_over_the_six_checkpoints():
    t = Tree()
    try:
        for model, prefix in (("r1qwen32b", "a"), ("r1llama70b", "b")):
            ids = _ids(prefix, 40)
            t.manifest(model, ids)
            t.shard(model, "rome_N", pair_rows(model, "rome_N", ids, lambda i: "new" if i < 36 else "old",
                                               lambda i: "old" if i < 20 else ("new" if i < 36 else "old")))
            # base: names o_old at B0 everywhere, keeps it at B3 except for 2 cases
            t.shard(model, "base", base_rows(model, ids, b3=lambda i: "none" if i in (0, 1) else "old"))
        t.manifest("r1qwen14b", _ids("c", 40))                 # screened, never run
        st = t.study()
        an = S.analyse(st, "lexical")
        cp = an["checkpoints"]["r1qwen32b"]
        assert abs(cp["ES_drop"]["point"] - 20 / 40) < 1e-12 and cp["ES_drop"]["es_b0"] == 36 / 40
        rc = cp["retention_contrast"]                          # 36 eligible; edited loses 20, base loses 2
        assert rc["n"] == 36 and abs(rc["point"] - (20 - 2) / 36) < 1e-12
        tab = st.table(("r1qwen32b", "s2", "rome_N"))
        assert cp["ES_drop"]["ci95"] == A.es_drop(tab)["ci95"] and cp["ES_drop"]["p"] == A.es_drop(tab)["p"]
        ps = {m: 1.0 for m in S.R1}
        ps.update({m: an["checkpoints"][m]["ES_drop"]["p"] for m in S.H1_AT})
        want = A.holm(ps)
        for m in S.R1:
            assert an["H1"]["holm"][m]["p_holm"] == want[m]["p_holm"] and an["H1"]["holm"][m]["m"] == 6
        assert an["H1"]["holm"]["r1qwen14b"]["not_estimated"] == "not_run"
        assert an["H1"]["holm"]["r1qwen7b"]["not_estimated"] == "no_manifest"
        assert all(an["H1"]["verdicts"][m]["pass"] for m in S.H1_AT)
        assert set(an["H2"]["verdicts"]) == set(S.H2_AT)
        assert an["H2"]["verdicts"]["r1qwen32b"]["pass"] and not an["H2"]["verdicts"]["r1qwen14b"]["pass"]
        assert an["submission_gate"]["pass"]
        assert an["H2b"]["status"] == "no_manifest" and not an["H2b"]["test"]["pass"]
        assert an["secondary"]["erosion_ci_above_zero"]["r1qwen32b"] is True
        assert an["secondary"]["post_training_recipes"]["qwq32b"] == {"status": "not_run"}
        md = S.render_md({"primary": "lexical", "endpoint_decision": S.endpoint_decision(None, False),
                          "analyses": {"lexical": an}, "worlds": {k[0] + "/" + "/".join(k[1:]): w["record"]
                                                                  for k, w in st.worlds.items()},
                          "ignored_worlds": {}})
        assert "| H1 | r1qwen32b | 40 |" in md and "`checkpoints/r1qwen14b/ES_drop`: not_run" in md
    finally:
        t.close()


# ------------------------------------------------------------------------------ H2b
def test_h2b_groups_are_resampled_independently():
    t = Tree()
    try:
        main, unk = _ids("m", 30), _ids("u", 20)
        t.manifest("r1qwen32b", main)
        t.manifest("r1qwen32b", unk, run=S.H2B)
        t.shard("r1qwen32b", "rome_N", pair_rows("r1qwen32b", "rome_N", main, lambda i: "new",
                                                 lambda i: "old" if i < 12 else "new"))
        t.shard("r1qwen32b", "base", base_rows("r1qwen32b", main))
        t.shard("r1qwen32b", "rome_N", pair_rows("r1qwen32b", "rome_N", unk, lambda i: "new" if i < 15 else "none",
                                                 lambda i: "new" if i < 14 else "none"), run=S.H2B)
        t.shard("r1qwen32b", "base", base_rows("r1qwen32b", unk, lambda i: "none", lambda i: "none"), run=S.H2B)
        st = t.study()
        b = S.h2b(st, "lexical")
        dm = [1] * 12 + [0] * 18
        du = [0] * 14 + [1] + [0] * 5
        ref = A.bootstrap_two_groups(dm, du)
        assert b["status"] == "ok" and b["n"] == [30, 20]
        assert abs(b["point"] - (12 / 30 - 1 / 20)) < 1e-12
        assert b["ci95"] == ref["ci95"] and b["p"] == ref["p"]
        assert b["main_pool"]["point"] == 12 / 30 and b["unknown_group"]["point"] == 1 / 20
        assert b["n_shared_cases"] == 0 and b["test"]["pass"] == (ref["p"] <= 0.05)
        g = b["group_check_study2_base_B0"]
        assert g["main_pool_base_names_old"]["k"] == 30 and g["unknown_group_base_names_neither"]["k"] == 20
        assert len(b["completeness"]) == 2 and all(c["complete"] for c in b["completeness"])
        # the unknown group loses B3 for 5 of its 20 cases: no estimate, whatever the main pool says
        t.shard("r1qwen32b", "rome_N", pair_rows("r1qwen32b", "rome_N", unk[:15], lambda i: "new",
                                                 lambda i: "none"), run=S.H2B)
        b = S.h2b(t.study(), "lexical")
        assert b["status"] == "incomplete" and "point" not in b and not b["test"]["pass"]
        assert b["completeness"][0]["complete"] and b["completeness"][1]["missing"] == unk[15:]
    finally:
        t.close()


# ------------------------------------------------------------------------------ H3
def _h3_tree(t, t_b3, p_b3, d_b3):
    ids = _ids("h", 40)
    t.manifest("r1qwen32b", ids)
    for cond, arm, f in (("rome_T", "T", t_b3), ("rome_P", "P", p_b3), ("rome_D", "D", d_b3)):
        t.shard("r1qwen32b", cond, pair_rows("r1qwen32b", cond, ids, lambda i: "new", f, arm=arm))
    return t.study()


def test_h3_signs_holm_and_direction():
    t = Tree()
    try:
        st = _h3_tree(t, lambda i: "new" if i < 36 else "old", lambda i: "new" if i < 16 else "old",
                      lambda i: "new" if i < 4 else "old")
        r = S.h3(st, "lexical")
        te = r["tests"]
        assert abs(te["T-P ES"]["point"] - 0.5) < 1e-12 and abs(te["T-P RRs"]["point"] + 0.5) < 1e-12
        assert abs(te["D-P ES"]["point"] + 0.3) < 1e-12
        assert te["T-P ES"]["mean_a"] == 0.9 and te["T-P ES"]["mean_b"] == 0.4
        assert set(r["holm"]) == {"T-P ES", "T-P RRs", "D-P ES"} and r["holm"]["D-P ES"]["m"] == 3
        assert all(v["pass"] for v in r["verdicts"].values()) and r["pass_all"]
        assert [r["verdicts"][n]["predicted_sign"] for n, *_ in S.H3_TESTS] == ["+", "-", "-"]
    finally:
        t.close()
    t = Tree()
    try:                                                       # suppression of o_old hurts: T-P ES < 0
        st = _h3_tree(t, lambda i: "new" if i < 16 else "old", lambda i: "new" if i < 36 else "old",
                      lambda i: "new" if i < 4 else "old")
        r = S.h3(st, "lexical")
        v = r["verdicts"]
        assert v["T-P ES"]["reject"] and not v["T-P ES"]["direction_ok"] and not v["T-P ES"]["pass"]
        assert not v["T-P RRs"]["pass"] and v["D-P ES"]["pass"] and not r["pass_all"]
    finally:
        t.close()


# ------------------------------------------------------------------------------ reliability
def test_sampling_reliability_on_seeds_0_2_and_seed_3_apart():
    t = Tree()
    try:
        ids = _ids("s", 20)
        t.manifest("r1qwen32b", ids)
        t.shard("r1qwen32b", "rome_N", pair_rows("r1qwen32b", "rome_N", ids, lambda i: "new" if i < 18 else "old",
                                                 lambda i: "new"))
        samp = []
        for s in range(4):
            for i, c in enumerate(ids):
                b0 = "old" if (i, s) == (5, 1) else "new"
                b3 = "old" if ((s < 3 and i < 6 and i % 3 == s) or (s == 3 and i < 2)) else "new"
                samp += [row(c, "r1qwen32b", "rome_samp", "B0", b0, decode="sample", seed=s),
                         row(c, "r1qwen32b", "rome_samp", "B3", b3, decode="sample", seed=s)]
        t.shard("r1qwen32b", "rome_samp", samp)
        r = S.reliability(t.study(), "lexical")
        main, extra = r["seeds_0_2"], r["seed_3"]
        assert main["status"] == "ok" and main["k"] == 3 and main["seeds"] == [0, 1, 2]
        assert main["n_greedy_b0_success"] == 18                   # the greedy gate is rome_N's B0
        assert abs(main["fail_any_b1"]["point"] - 6 / 18) < 1e-12
        assert abs(main["fail_any_b0_noise_floor"]["point"] - 1 / 18) < 1e-12
        assert extra["k"] == 1 and extra["seeds"] == [3] and abs(extra["fail_any_b1"]["point"] - 2 / 18) < 1e-12
        assert r["temperatures"] == [0.6]
        # seed 2 missing at B3 for 10 cases: the seed 0-2 statistic is withheld, seed 3 is not
        t.shard("r1qwen32b", "rome_samp", [x for x in samp if not (x["seed"] == 2 and x["budget"] == "B3"
                                                                  and x["case_id"] in ids[10:])])
        r = S.reliability(t.study(), "lexical")
        assert r["seeds_0_2"]["status"] == "incomplete" and r["seeds_0_2"]["completeness"]["missing"] == ids[10:]
        assert r["seed_3"]["status"] == "ok"
    finally:
        t.close()


# ------------------------------------------------------------------------------ exclusions
def test_error_rows_and_fit_errors_are_excluded_and_counted():
    t = Tree()
    try:
        ids = _ids("e", 100)
        t.manifest("r1qwen7b", ids)
        good = pair_rows("r1qwen7b", "rome_N", ids[:49] + ids[50:99], lambda i: "new", lambda i: "old" if i % 2 else "new")
        err = {"case_id": ids[49], "condition": "rome_N", "model_tag": "r1qwen7b", "editor": "ROME",
               "error_kind": "engine", "error": "OOM"}
        lost = {"case_id": ids[99], "condition": "rome_N", "model_tag": "r1qwen7b", "editor": "ROME",
                "error_kind": "missing_delta", "error": "no delta file"}
        retried = pair_rows("r1qwen7b", "rome_N", [ids[49]], lambda i: "new", lambda i: "new")
        stray = pair_rows("r1qwen7b", "rome_N", ["zz_outside"], lambda i: "new", lambda i: "new")
        t.cases.update(_cases(["zz_outside"]))
        t.shard("r1qwen7b", "rome_N", good[:98] + [err, lost] + good[98:] + retried + stray)
        log = os.path.join(t.root, "r1qwen7b_ROME_cf_r0of1.jsonl")
        with open(log, "w") as fh:
            fh.write(json.dumps({"_meta": True, "run_signature": {}}) + "\n")
            for c in ids[:99]:
                e = 5e-4 if c == ids[7] else 1e-6
                fh.write(json.dumps({"case_id": c, "status": "ok", "sha": f"sha-r1qwen7b-rome_N-{c}",
                                     "fit": {"5": {"rank": 1, "rel_err": e, "tol": 1e-4, "rel_delta": 0.01}}}) + "\n")
            fh.write(json.dumps({"case_id": ids[99], "status": "error", "stage": "factor", "error": "x"}) + "\n")
        fit, files = S.read_fit_logs([log])
        assert files[0]["counts"] == {"ok": 99, "error": 1} and files[0]["ok_fit_over_tol"] == [ids[7]]
        st = t.study(fit=fit)
        ex = st.worlds[("r1qwen7b", "s2", "rome_N")]["record"]["exclusions"]
        assert ex["error_rows"]["n"] == 2 and ex["error_rows"]["case_ids"] == [ids[49], ids[99]]
        assert ex["error_rows"]["kinds"] == {"engine": 1, "missing_delta": 1}
        assert ex["fit_error_over_1e-4"]["case_ids"] == [ids[7]] and ex["fit_error_over_1e-4"]["n_rows"] == 2
        assert ex["fit_error_over_1e-4"]["status"] == "applied"
        assert ex["outside_manifest"] == {"n_rows": 2, "case_ids": ["zz_outside"]}
        h1 = S.checkpoint(st, "r1qwen7b", "lexical", full=False)["ES_drop"]
        assert h1["status"] == "ok" and h1["n"] == 98                    # 98 of 100 = the 98% floor
        assert h1["completeness"]["missing"] == [ids[7], ids[99]]
        st2 = t.study()                                                   # without logs: not applied, said so
        ex2 = st2.worlds[("r1qwen7b", "s2", "rome_N")]["record"]["exclusions"]["fit_error_over_1e-4"]
        assert ex2["status"].startswith("no delta logs") and ex2["n_rows"] == 0
    finally:
        t.close()


def test_degenerate_cases_reported_with_and_without():
    t = Tree()
    try:
        ids = _ids("g", 30)
        t.manifest("r1qwen32b", ids)
        t.shard("r1qwen32b", "rome_N", pair_rows("r1qwen32b", "rome_N", ids, lambda i: "new",
                                                 lambda i: "degenerate" if i == 3 else ("old" if i < 10 else "new")))
        b = S.checkpoint(t.study(), "r1qwen32b", "lexical", full=False)["ES_drop"]
        assert b["n"] == 30 and abs(b["point"] - 10 / 30) < 1e-12        # the unfiltered estimate is primary
        w = b["without_degenerate"]
        assert w["flagged"] == [ids[3]] and w["n"] == 29 and abs(w["point"] - 9 / 29) < 1e-12
    finally:
        t.close()


# ------------------------------------------------------------------------------ endpoints
def test_endpoint_switch():
    d = tempfile.mkdtemp()
    try:
        def sw(obj):
            p = os.path.join(d, f"s{len(os.listdir(d))}.json")
            json.dump(obj, open(p, "w"))
            return p
        assert S.endpoint_decision(sw({"kappa_es": 0.75, "kappa_rr": 0.72}), True)["primary"] == "semantic"
        r = S.endpoint_decision(sw({"kappa_es": 0.75, "kappa_rr": 0.72}), False)
        assert r["primary"] == "lexical" and r["kappa_meets_threshold"] and "note" in r
        assert S.endpoint_decision(sw({"kappa_es": 0.75, "kappa_rr": 0.69}), True)["primary"] == "lexical"
        assert S.endpoint_decision(sw({"kappa_es": 0.70, "kappa_rr": 0.70}), True)["primary"] == "semantic"
        assert S.endpoint_decision(sw({"switch": {"kappa": {"es": 0.8, "rr": None}}}), True)["primary"] == "lexical"
        assert S.endpoint_decision(sw({"switch": {"kappa": {"es": 0.8, "rr": 0.9}}}), True)["primary"] == "semantic"
        assert S.endpoint_decision(None, True)["primary"] == "lexical"
    finally:
        shutil.rmtree(d)


def test_semantic_endpoint_reads_the_judge_ensemble():
    from rt import judge as J
    t = Tree()
    try:
        ids = _ids("j", 50)
        t.manifest("r1qwen32b", ids)
        rows = pair_rows("r1qwen32b", "rome_N", ids, lambda i: "new", lambda i: "both" if i < 4 else "new")
        path = t.shard("r1qwen32b", "rome_N", rows)
        probs = {"NEW": {"NEW": .8, "OLD": .1, "BOTH_UNCLEAR": .05, "NEITHER": .05},
                 "OLD": {"NEW": .1, "OLD": .8, "BOTH_UNCLEAR": .05, "NEITHER": .05}}
        for name in ("gemma", "mistral"):
            with open(os.path.join(t.root, f"{name}.jsonl"), "w") as fh:
                fh.write(json.dumps({"_meta": True, "format": J.FORMAT, "prompt": {"sha": S.PREREG_PROMPT_SHA},
                                     "orders": 2}) + "\n")
                for line_no, r in enumerate(rows, 1):
                    if r["case_id"] == ids[9] and r["budget"] == "B3":
                        continue                                  # one row never judged
                    lab = "OLD" if r["budget"] == "B3" and r["case_id"] < ids[2] else "NEW"
                    item = J.make_item(r, t.cases, {})
                    rid = {k: v for k, v in r.items() if k in J.IDENTITY_FIELDS and v is not None}
                    rid.update(src=os.path.basename(path), line=line_no)
                    fh.write(json.dumps({"row_key": J.row_key(rid, item["item"]), "item": item["item"], "row": rid,
                                         "values": item["values"], "lexical": item["lexical"],
                                         "p": probs[lab], "label": lab}) + "\n")
        verdicts, info = S.load_verdicts([f"gemma={t.root}/gemma.jsonl", f"mistral={t.root}/mistral.jsonl"])
        assert info["as_preregistered"] and info["n_ensemble_rows"] == 99
        assert verdicts[("r1qwen32b", "s2", "rome_N", ids[0], "B3", "efficacy", "greedy", None)][0] == "OLD"
        st = t.study(verdicts=verdicts)
        lex = S.checkpoint(st, "r1qwen32b", "lexical", full=False)["ES_drop"]
        sem = S.checkpoint(st, "r1qwen32b", "semantic", full=False)["ES_drop"]
        assert lex["n"] == 50 and abs(lex["point"] - 4 / 50) < 1e-12       # lexical: 'both' is a failure
        assert sem["status"] == "ok" and sem["completeness"]["missing"] == [ids[9]]
        assert sem["n"] == 49 and abs(sem["point"] - 2 / 49) < 1e-12      # semantic: only the two OLD labels
        assert st._judge["no_verdict"] == 1
        one = S.load_verdicts([f"gemma={t.root}/gemma.jsonl"])[1]          # one judge is not the prereg ensemble
        assert not one["as_preregistered"]
    finally:
        t.close()


# ------------------------------------------------------------------------------ small helpers
def test_locality_is_scored_without_subject_scrubbing():
    cases = {"c1": {"case_id": "c1", "s": "Norway Cup", "o_old": "Norway", "o_new": "Bulgaria"}}
    r = {"case_id": "c1", "probe": "locality", "decode": "greedy", "seed": None, "budget": "B3",
         "answer": "Norway Cup.", "cot": ""}
    assert S.locality_table([r], cases, {})["c1"]["B3"]["old"] is True
    assert A.score_row(r, cases["c1"], {})["old"] is False             # efficacy scoring would scrub it


def test_alpha_needed_for_80_percent():
    r = S.alpha_for_target([(0.5, 0.5), (1.0, 0.7), (2.0, 0.9), (3.0, 0.95)])
    assert r["grid_alpha"] == 2.0 and abs(r["interpolated_alpha"] - 1.5) < 1e-12
    assert S.alpha_for_target([(1.0, 0.85), (2.0, 0.9)])["interpolated_alpha"] is None
    assert S.alpha_for_target([(1.0, 0.5), (3.0, 0.6)])["grid_alpha"] is None


def test_main_writes_json_and_markdown_with_provenance():
    t = Tree()
    try:
        ids = _ids("x", 20)
        t.manifest("r1qwen32b", ids)
        m = "r1qwen32b"
        t.shard(m, "rome_N", pair_rows(m, "rome_N", ids, lambda i: "new", lambda i: "old" if i < 8 else "new")
                + [row(c, m, "rome_N", b, "old", probe="locality") for c in ids for b in ("B0", "B3")]
                + [row(c, m, "rome_N", b, "new", probe="para0") for c in ids for b in ("B0", "B3")])
        t.shard(m, "base", base_rows(m, ids) + [row(c, m, "base", "B3", "old", probe="locality", editor="none")
                                                for c in ids])
        t.shard(m, "rome_a0.5", [row(c, m, "rome_a0.5", "B0", "none", alpha=0.5) for c in ids])
        t.shard(m, "rome_a2", pair_rows(m, "rome_a2", ids, lambda i: "new", lambda i: "new", alpha=2.0))
        t.shard(m, "memit_N", pair_rows(m, "memit_N", ids, lambda i: "new", lambda i: "old", editor="MEMIT"))
        for cond in ("rome_own", "rome_filler"):
            t.shard(m, cond, [row(c, m, cond, "GIVEN", "new" if cond == "rome_filler" else "old") for c in ids])
        t.shard(m, "rome_N", pair_rows(m, "rome_N", ids[:2], lambda i: "new", lambda i: "new"), run="s2_smoke")
        cases = os.path.join(t.root, "cases.jsonl")
        with open(cases, "w") as fh:
            for c in t.cases.values():
                fh.write(json.dumps(c) + "\n")
        aliases = os.path.join(t.root, "aliases.json")
        json.dump({}, open(aliases, "w"))
        out = os.path.join(t.root, "out", "study2.json")
        S.main(["--results", t.res, "--manifests", t.man, "--cases", cases, "--aliases", aliases,
                "--delta-logs", "--out", out])
        res = json.load(open(out))
        meta = res["_meta"]
        assert {"src/rt/study2.py", "src/rt/analysis.py"} <= set(meta["code_sha256"])
        assert meta["inputs"]["manifests"]["r1qwen32b/s2"]["sha256"] and meta["inputs"]["delta_logs"] == []
        assert res["primary"] == "lexical" and list(res["analyses"]) == ["lexical"]
        assert "r1qwen32b/s2_smoke/rome_N" in res["ignored_worlds"]
        an = res["analyses"]["lexical"]
        assert abs(an["checkpoints"][m]["ES_drop"]["point"] - 0.4) < 1e-12
        loc = an["checkpoints"][m]["locality_B3"]
        assert loc["status"] == "ok" and loc["edited_correct"]["point"] == 1.0
        assert an["checkpoints"][m]["paraphrase"]["point"] == 0.0
        s = an["secondary"]
        assert s["alpha_dose_32B"]["cells"]["alpha=0.5@B0"]["point"] == 0.0
        assert s["alpha_dose_32B"]["cells"]["alpha=2@B3"]["point"] == 1.0
        assert s["alpha_dose_32B"]["alpha_for_ES_0.8"]["B3"]["status"] == "undetermined"   # alpha 3 absent
        assert s["editors_32B"]["memit_N"]["point"] == 1.0 and s["editors_32B"]["ike"]["status"] == "not_run"
        assert s["given_chain_32B"]["contrasts"]["rome_own-rome_filler"]["point"] == -1.0
        assert s["given_chain_32B"]["contrasts"]["rome_own-rome_swap"]["status"] == "incomplete"
        md = open(os.path.join(t.root, "out", "study2.md")).read()
        assert md.startswith("# Study 2") and "Exclusions and completeness" in md
    finally:
        t.close()
