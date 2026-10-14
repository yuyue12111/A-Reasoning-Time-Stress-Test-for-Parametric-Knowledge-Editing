"""rt.targets: teacher-forced scoring, candidate rules and plausibility ranking on the tiny model."""
import json
import os
import tempfile

import torch

from rt import targets
from rt.tests._tiny import tiny_model, tiny_tokenizer

ROWS = [
    {"case_id": "cf_1", "r": "P36", "s": "Avalon", "prompt": "The capital of Avalon is",
     "o_old": "Camelot", "o_new": "Paris", "o_old_aliases": [], "o_new_aliases": []},
    {"case_id": "cf_2", "r": "P36", "s": "Brin", "prompt": "The capital of Brin is",
     "o_old": "Paris", "o_new": "Oslo", "o_old_aliases": [], "o_new_aliases": []},
    {"case_id": "cf_3", "r": "P36", "s": "Cora", "prompt": "The capital of Cora is",
     "o_old": "Lima", "o_new": "Rome", "o_old_aliases": [], "o_new_aliases": []},
    {"case_id": "cf_4", "r": "P36", "s": "Dune", "prompt": "The capital of Dune is",
     "o_old": "Camelot Town", "o_new": "Oslo", "o_old_aliases": [], "o_new_aliases": []},
    {"case_id": "cf_5", "r": "P36", "s": "Esk", "prompt": "The capital of Esk is",
     "o_old": "Avalon City", "o_new": "Rome", "o_old_aliases": [], "o_new_aliases": []},
    {"case_id": "cf_6", "r": "P36", "s": "Fen", "prompt": "The capital of Fen is",
     "o_old": "Kyiv", "o_new": "Rome", "o_old_aliases": [], "o_new_aliases": ["Roma"]},
    {"case_id": "cf_7", "r": "P36", "s": "Gor", "prompt": "The capital of Gor is",
     "o_old": "Quito", "o_new": "Lima", "o_old_aliases": [], "o_new_aliases": []},
    {"case_id": "cf_8", "r": "P1412", "s": "Hal", "prompt": "Hal speaks",
     "o_old": "Welsh", "o_new": "Dutch", "o_old_aliases": [], "o_new_aliases": []},
]


def _setup():
    tok = tiny_tokenizer()
    return tiny_model(vocab=len(tok)), tok


def _manual(model, tok, prompt, cont):
    p = tok(prompt)["input_ids"]
    c = tok(cont, add_special_tokens=False)["input_ids"]
    with torch.no_grad():
        lp = torch.log_softmax(model(input_ids=torch.tensor([p + c])).logits[0].float(), -1)
    t = torch.stack([lp[len(p) - 1 + i, c[i]] for i in range(len(c))])
    return float(t[0]), float(t.sum())


def test_continuation_logprobs_match_unbatched():
    model, tok = _setup()
    conts = [" Paris", " Oslo", " Camelot Town", " Q"]
    for bs in (1, 2, 64):
        got = targets.continuation_logprobs(model, tok, "The capital of Avalon is", conts, bs)
        for g, c in zip(got, conts):
            first, total = _manual(model, tok, "The capital of Avalon is", c)
            assert abs(g["first"] - first) < 1e-4 and abs(g["sum"] - total) < 1e-4, (bs, c)
            assert g["n_tok"] == len(tok(c, add_special_tokens=False)["input_ids"])


def test_candidate_pool_rules():
    by_rel = targets.relation_index(ROWS)
    assert by_rel["P36"] == sorted({"Camelot", "Paris", "Lima", "Camelot Town", "Avalon City",
                                    "Kyiv", "Quito"})
    # cf_1: own o_old Camelot and o_new Paris out; "Camelot Town" contains o_old; "Avalon City"
    # contains the subject; other relations never enter
    assert targets.candidate_pool(ROWS[0], by_rel) == ["Kyiv", "Lima", "Quito"]
    # aliases of o_new (from the case and from the alias table) are matcher collisions too
    assert "Lima" in targets.candidate_pool(ROWS[5], by_rel)
    assert "Lima" not in targets.candidate_pool(dict(ROWS[5], o_new_aliases=["Lima"]), by_rel)
    assert "Kyiv" not in targets.candidate_pool(ROWS[0], by_rel, aliases={"Paris": ["Kyiv"]})


def test_rank_case_picks_the_most_likely_candidate():
    model, tok = _setup()
    case = ROWS[0]
    cands = ["Kyiv", "Lima", "Quito"]
    row = targets.rank_case(model, tok, case, cands, rank_by="sum", batch_size=2)
    scores = {c: _manual(model, tok, case["prompt"], " " + c) for c in cands}
    order = sorted(cands, key=lambda c: (-scores[c][1], -scores[c][0], c))
    assert row["target"] == order[0] and [t[0] for t in row["top"]] == order
    s_new = _manual(model, tok, case["prompt"], " Paris")
    assert abs(row["o_new_logprob"]["sum"] - s_new[1]) < 1e-4
    assert row["o_new_rank"] == 1 + sum(scores[c][1] > s_new[1] for c in cands)
    assert row["o_new_rank_by_first"] == 1 + sum(
        (scores[c][0], scores[c][1]) > s_new for c in cands)
    assert row["target_tag"] == "plausible" and row["n_candidates"] == 3
    by_first = targets.rank_case(model, tok, case, cands, rank_by="first")
    assert by_first["target"] == sorted(cands, key=lambda c: (-scores[c][0], -scores[c][1], c))[0]
    empty = targets.rank_case(model, tok, case, [], rank_by="sum")
    assert empty["target"] is None and "no candidates" in empty["error"]


def test_score_pool_resumes_and_load_targets_filters():
    model, tok = _setup()
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "t.jsonl")
        meta = {"_meta": True, "model_tag": "tiny"}
        quiet = dict(log=lambda *a: None, meta=meta)
        assert targets.score_pool(model, tok, ROWS[:3], ROWS, out, **quiet) == 3
        assert targets.score_pool(model, tok, ROWS[:4], ROWS, out, **quiet) == 1
        got = targets.load_targets(out, "plausible", "tiny")
        assert sorted(got) == ["cf_1", "cf_2", "cf_3", "cf_4"]
        assert targets.load_targets(out, "other") == {}
        try:
            targets.load_targets(out, "plausible", "r1qwen32b")
        except ValueError:
            pass
        else:
            raise AssertionError("targets scored with another model must be refused")
        with open(out, "a") as fh:
            fh.write(json.dumps({"case_id": "cf_1", "target_tag": "plausible",
                                 "target": "Somewhere"}) + "\n")
        try:
            targets.load_targets(out, "plausible")
        except ValueError:
            return
    raise AssertionError("conflicting targets must be refused")
