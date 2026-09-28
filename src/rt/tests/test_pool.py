"""pool.py: used-id exclusion, seeded candidates, legacy shard order, qualification rules, freezing."""
import io
import json
import os
import tempfile
from contextlib import redirect_stdout

from rt import pool as P
from rt.run import read_ids
from rt.tests._tiny import tiny_model, tiny_tokenizer


def _case(cid, s, old, new):
    return {"case_id": cid, "s": s, "prompt": f"{s} is located in", "o_old": old, "o_new": new,
            "paraphrases": [], "neighborhood": []}


def _jsonl(path, rows, extra_lines=()):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
        for line in extra_lines:
            f.write(line + "\n")


def test_collect_used_ids_reports_every_file():
    with tempfile.TemporaryDirectory() as d:
        _jsonl(os.path.join(d, "a", "x_r0of2.jsonl"), [{"_meta": True}, {"case_id": "cf_1", "probe": "efficacy"},
                                                       {"case_id": "cf_1", "probe": "locality"},
                                                       {"case_id": "cf_2", "error": "oom"}], ["not json"])
        _jsonl(os.path.join(d, "a", "sub", "y.jsonl"), [{"case_id": 7}, {"other": 1}])
        _jsonl(os.path.join(d, "a", "rt", "skip.jsonl"), [{"case_id": "cf_9"}])
        _jsonl(os.path.join(d, "m.jsonl"), [{"case_id": "cf_3"}])
        ids, rep = P.collect_used_ids(["a/**/*.jsonl", "m.jsonl", "none/*.jsonl"], exclude=["a/rt/*.jsonl"], root=d)
        assert ids == {"cf_1", "cf_2", "7", "cf_3"}
        files = {f["path"]: f for e in rep for f in e["files"]}
        assert files[os.path.join("a", "x_r0of2.jsonl")] == {"path": os.path.join("a", "x_r0of2.jsonl"),
                                                             "n_rows": 4, "n_ids": 2, "n_bad_lines": 1}
        assert os.path.join("a", "rt", "skip.jsonl") not in files
        assert [e["n_files"] for e in rep] == [2, 1, 0]


def test_candidates_exclude_used_and_are_seeded():
    cases = [{"case_id": f"cf_{i}"} for i in range(50)]
    used = {f"cf_{i}" for i in range(0, 50, 3)}
    a = P.build_candidates(cases, used, seed=2027, n=20)
    assert len(a) == 20 and not set(a) & used and len(set(a)) == 20
    assert a == P.build_candidates(cases, used, seed=2027, n=20)
    assert a != P.build_candidates(cases, used, seed=2028, n=20)
    assert P.build_candidates(cases, used, seed=2027, n=10) == a[:10]
    full = P.build_candidates(cases, used, seed=2027, n=10 ** 6)
    assert sorted(full) == sorted(c["case_id"] for c in cases if c["case_id"] not in used)


def test_ids_from_shards_restores_dataset_order():
    order = [f"cf_{i * 7 % 23}" for i in range(11)]
    with tempfile.TemporaryDirectory() as d:
        for r in range(3):
            rows = [{"_meta": True}]
            for cid in order[r::3]:
                rows += [{"case_id": cid, "budget": "B0"}, {"case_id": cid, "budget": "B3"}]
            _jsonl(os.path.join(d, f"run_r{r}of3.jsonl"), rows)
        assert P.ids_from_shards(os.path.join(d, "run_r*of3.jsonl")) == order
        os.remove(os.path.join(d, "run_r1of3.jsonl"))
        try:
            P.ids_from_shards(os.path.join(d, "run_r*of3.jsonl"))
        except ValueError:
            pass
        else:
            raise AssertionError("an incomplete shard set must raise")
        try:
            P.ids_from_shards(os.path.join(d, "nothing_r*of3.jsonl"))
        except ValueError:
            return
    raise AssertionError("no shards must raise")


def test_qualification_rules():
    aliases = {"Norway": ["Kingdom of Norway"]}
    cands = [
        _case("q1", "Oseberg ship", "Norway", "Italy"),            # qualifies
        _case("q2", "Bergen", "Norway", "Italy"),                  # old miss
        _case("q3", "Tromso", "Norway", "Italy"),                  # new hit (both named)
        _case("q4", "Norway House", "Norway", "Italy"),            # subject contains old
        _case("q5", "Norwayan Club", "Norway", "Italy"),           # substring only: fine, but old miss
        _case("q6", "the NORWAY line", "Norway", "Italy"),         # whole word, case-insensitive
        _case("q7", "Lofoten", "Norway", "Italy"),                 # alias hit -> qualifies
        _case("q8", "Hamar", "Norway", "Italy"),                   # no screen row
        _case("q9", "Oslo fjord", "Norway", "Italy"),              # qualifies, beyond k
    ]
    answers = {"q1": "Oseberg ship is in Norway.", "q2": "Bergen is in Italy.",
               "q3": "Tromso is in Norway, not Italy.", "q4": "Norway House is in Norway.",
               "q5": "Norwayan Club is in Rome.", "q6": "It is in Norway.",
               "q7": "Lofoten belongs to the Kingdom of Norway.", "q9": "Norway."}
    manifest, dec, counts = P.qualify(cands, answers, aliases, k=2)
    assert manifest == ["q1", "q7"]
    by = {d["case_id"]: d for d in dec}
    assert [by[c]["reason"] for c in ("q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9")] == [
        None, "old_miss", "new_hit", "subject_contains_old", "old_miss", "subject_contains_old", None,
        "missing_screen", None]
    assert by["q9"]["qualified"] and not by["q9"]["in_manifest"]
    assert by["q5"]["subject_contains_old"] is False and by["q4"]["old_hit"] is True
    assert counts["n_qualified"] == 3 and counts["n_manifest"] == 2 and counts["complete"]
    assert counts["excluded_primary"] == {"missing_screen": 1, "subject_contains_old": 2, "old_miss": 2,
                                          "new_hit": 1}
    assert counts["excluded_any"]["old_miss"] == 2 and counts["excluded_any"]["new_hit"] == 2
    assert by["q6"]["old_hit"] is True and by["q2"]["old_hit"] is False


def test_subject_scrub_before_matching():
    cands = [_case("s1", "Miami Beach Festival", "Florida", "Texas")]
    m, dec, _ = P.qualify(cands, {"s1": "Miami Beach Festival is held in Texas"}, {}, k=5)
    assert m == [] and dec[0]["reason"] == "old_miss" and dec[0]["new_hit"]
    cands = [_case("s2", "Florida Man Show", "Florida", "Texas")]
    _, dec, _ = P.qualify(cands, {"s2": "The Florida Man Show airs in Florida"}, {}, k=5)
    assert dec[0]["reason"] == "subject_contains_old" and dec[0]["old_hit"]


def _pool_cfg(d):
    return {"counterfact": os.path.join(d, "cf.jsonl"), "aliases": os.path.join(d, "aliases.json"),
            "seed": 2027, "n_candidates": 6, "k": 3, "pool_dir": os.path.join(d, "pools"),
            "screen_dir": os.path.join(d, "screen"),
            "used_sources": [os.path.join(d, "old", "*.jsonl")], "used_exclude": [],
            "engine": {"batch_size": 4, "answer_cap": 8, "chunk_cases": 4},
            "models": {"tiny": {"template": "r1", "no_bos": True, "model": {"dtype": "float32"}}}}


def test_build_screen_qualify_end_to_end():
    tok = tiny_tokenizer()
    model = tiny_model(vocab=len(tok))
    model.generation_config.eos_token_id = tok.eos_token_id
    with tempfile.TemporaryDirectory() as d:
        cases = [_case(f"cf_{i}", f"Subject {i}", "Norway", "Italy") for i in range(12)]
        _jsonl(os.path.join(d, "cf.jsonl"), cases)
        json.dump({}, open(os.path.join(d, "aliases.json"), "w"))
        _jsonl(os.path.join(d, "old", "study1_r0of1.jsonl"), [{"case_id": f"cf_{i}"} for i in range(4)])
        pcfg = _pool_cfg(d)
        buf = io.StringIO()
        with redirect_stdout(buf):
            path = P.cmd_build(pcfg)
            cand = read_ids(path)                                   # sidecar sha checked
            assert len(cand) == 6 and not set(cand) & {f"cf_{i}" for i in range(4)}
            summ = json.load(open(os.path.join(d, "pools", "candidates_summary.json")))
            assert summ["used"]["n_ids_in_counterfact"] == 4 and summ["n_available"] == 8
            P.cmd_build(pcfg)                                       # identical rebuild is a no-op
            try:
                P.cmd_build(dict(pcfg, seed=1))
            except RuntimeError:
                pass
            else:
                raise AssertionError("frozen candidates must not be replaced")
            try:
                P.cmd_qualify(pcfg, "tiny")
            except FileNotFoundError:
                pass
            else:
                raise AssertionError("qualify without screen rows must refuse")
            P.cmd_screen(pcfg, "tiny", rank=0, world=2, model=model, tok=tok)
            try:
                P.cmd_qualify(pcfg, "tiny")
            except RuntimeError as e:
                assert "no screen row" in str(e)
            else:
                raise AssertionError("half-screened candidates must refuse")
            P.cmd_screen(pcfg, "tiny", rank=1, world=2, model=model, tok=tok)
            summary = P.cmd_qualify(pcfg, "tiny")
        rows = [json.loads(l) for f in ("tiny_pool_screen_r0of2.jsonl", "tiny_pool_screen_r1of2.jsonl")
                for l in open(os.path.join(d, "screen", f))]
        screened = [r for r in rows if r.get("probe")]
        assert sorted(r["case_id"] for r in screened) == sorted(cand)
        assert all(r["budget"] == "B0" and r["probe"] == "efficacy" and r["editor"] == "none" for r in screened)
        man = read_ids(os.path.join(d, "pools", "manifest_tiny.jsonl"))
        dec = [json.loads(l) for l in open(os.path.join(d, "pools", "qualify_tiny.jsonl"))]
        assert man == [x["case_id"] for x in dec if x["in_manifest"]]
        assert [x["case_id"] for x in dec] == cand
        assert summary["n_candidates"] == 6 and summary["n_manifest"] == len(man) <= 3
        assert sum(summary["excluded_primary"].values()) == 6 - summary["n_qualified"]
        assert summary["manifest_sha256"] == open(os.path.join(d, "pools", "manifest_tiny.jsonl.sha256")).read().split()[0]
