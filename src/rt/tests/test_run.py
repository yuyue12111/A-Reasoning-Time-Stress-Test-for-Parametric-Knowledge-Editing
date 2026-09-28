"""run.py: row schema, per-condition shards, arms, IKE, GIVEN transforms, resume and its refusals."""
import copy
import glob
import io
import json
import os
import tempfile
from contextlib import redirect_stdout

import metrics
from rt import run as R
from rt.edit_hooks import save_delta
from rt.engine import IM_END, IM_START
from rt.tests._tiny import MODULE_TMP, rank1_edit, tiny_model, tiny_tokenizer
from suppress import build_old_token_ids

CASES = [
    {"case_id": "cf_1", "s": "Oseberg ship", "r": "P17", "prompt": "Oseberg ship is located in",
     "o_old": "Norway", "o_new": "Italy", "paraphrases": ["The Oseberg ship lies in", "Oseberg is in"],
     "neighborhood": ["Bergen is located in"]},
    {"case_id": "cf_2", "s": "Toko Yasuda", "r": "P1303", "prompt": "Toko Yasuda plays the",
     "o_old": "guitar", "o_new": "piano", "paraphrases": ["Yasuda performs on the"], "neighborhood": []},
    {"case_id": "cf_3", "s": "Apple A5", "r": "P176", "prompt": "Apple A5 was created by",
     "o_old": "Apple", "o_new": "Google", "paraphrases": ["A5 comes from", "A5 is made by"],
     "neighborhood": ["iPod was created by"]},
    {"case_id": "cf_4", "s": "Danielle Darrieux", "r": "P103", "prompt": "Danielle Darrieux speaks",
     "o_old": "French", "o_new": "English", "paraphrases": ["Darrieux's tongue is"],
     "neighborhood": ["Jean Gabin speaks"]},
    {"case_id": "cf_5", "s": "Autonomous University of Madrid", "r": "P17",
     "prompt": "Autonomous University of Madrid is in", "o_old": "Spain", "o_new": "Sweden",
     "paraphrases": ["UAM is in"], "neighborhood": ["Complutense is in"]},
]
ALIASES = {"Norway": ["Kingdom of Norway"], "Italy": ["Italia"]}
SCHEMA = ("case_id", "model_tag", "editor", "target_tag", "budget", "probe", "condition", "arm", "alpha",
          "decode", "seed", "temperature", "q", "cot", "answer", "chain_end", "n_chain_tokens",
          "n_answer_tokens", "delta_sha", "batch_id", "template")


def _model(tok=None):
    tok = tok or tiny_tokenizer()
    model = tiny_model(vocab=len(tok))
    model.generation_config.eos_token_id = tok.eos_token_id
    return model, tok


def _world(d, model, with_delta=("cf_1", "cf_2", "cf_3", "cf_4")):
    with open(os.path.join(d, "cf.jsonl"), "w") as f:
        for c in CASES:
            f.write(json.dumps(c) + "\n")
    json.dump(ALIASES, open(os.path.join(d, "aliases.json"), "w"))
    json.dump({c["case_id"]: "Sydney" for c in CASES[:4]}, open(os.path.join(d, "placebo.json"), "w"))
    shas = {}
    for i, cid in enumerate(with_delta):
        _save(d, model, cid, seed=10 + i)
    return shas


def _save(d, model, cid, seed):
    (layer, (A, B)), = rank1_edit(model, 1, seed=seed, scale=1.0).items()
    return save_delta(os.path.join(d, "deltas", f"{cid}.pt"),
                      {"case_id": cid, "model_tag": "tiny", "editor": "ROME", "target": "x",
                       "target_tag": "cf", "module_tmp": MODULE_TMP, "layers": {layer: {"A": A, "B": B}}})


def _cfg(d):
    rome = {"editor": "ROME", "target_tag": "cf", "deltas_dir": os.path.join(d, "deltas")}
    return {"model_tag": "tiny", "template": "r1", "model": {"dtype": "float32"}, "module_tmp": MODULE_TMP,
            "out_dir": os.path.join(d, "out"), "run_tag": "t",
            "dataset": {"path": os.path.join(d, "cf.jsonl")}, "aliases": os.path.join(d, "aliases.json"),
            "probes": ["efficacy", "locality"],
            "arms": {"penalty": 8, "bias_probes": ["efficacy"], "placebo_map": os.path.join(d, "placebo.json")},
            "engine": {"batch_size": 4, "answer_cap": 8, "chunk_cases": 2, "caps": {"B1": 8, "B3": 8}},
            "conditions": [
                {"name": "base", "editor": "none", "budgets": ["B0", "B3"]},
                dict(rome, name="rome_N", budgets=["B0", "B3"]),
                dict(rome, name="rome_T", arm="T", budgets=["B0", "B3"], probes=["efficacy", "para0"]),
                dict(rome, name="rome_P", arm="P", budgets=["B3"], probes=["efficacy"]),
                dict(rome, name="rome_a2", alpha=2.0, budgets=["B0"], probes=["efficacy"]),
                {"name": "ike", "editor": "IKE", "user_prefix_template": "Fact: {prompt} {o_new}.\n",
                 "budgets": ["B0"], "probes": ["efficacy"]},
                dict(rome, name="rome_samp", budgets=["B3"], probes=["efficacy"],
                     decoding={"greedy": False, "sampling": {"temperature": 0.6, "seeds": [0, 1]}}),
            ]}


def _rows(path):
    lines = [json.loads(l) for l in open(path)]
    return lines[0], [r for r in lines[1:] if r.get("probe")], [r for r in lines[1:] if r.get("error")]


def _shard(cfg, cond, rank=0, world=1, run_tag="t"):
    return os.path.join(cfg["out_dir"], f"tiny_{run_tag}_{cond}_r{rank}of{world}.jsonl")


def _quiet(fn, *a, **k):
    with redirect_stdout(io.StringIO()):
        return fn(*a, **k)


def test_rows_schema_headers_and_metrics():
    model, tok = _model()
    with tempfile.TemporaryDirectory() as d:
        _world(d, model)
        cfg = _cfg(d)
        written = _quiet(R.run_config, cfg, model=model, tok=tok)
        assert written["base"] == 5 * 2 + 4 * 2          # cf_2 has no neighbour
        hdr, rows, errs = _rows(_shard(cfg, "base"))
        assert hdr["_meta"] and hdr["condition"] == "base" and hdr["template"] == "r1"
        assert set(R.RESUME_KEYS) <= set(hdr) and hdr["code_sha256"] == R.code_sha256()
        assert "src/rt/engine.py" in hdr["code_sha256"] and "src/think_budget.py" in hdr["code_sha256"]
        assert hdr["software"]["torch"] and hdr["model"]["class"] == "Qwen2ForCausalLM"
        assert all(k in r for r in rows for k in SCHEMA) and not errs
        assert {(r["budget"], r["chain_end"] is None) for r in rows} == {("B0", True), ("B3", False)}
        assert all(r["editor"] == "none" and r["delta_sha"] is None and r["alpha"] is None for r in rows)
        scores = metrics.score(_shard(cfg, "base"), CASES, ALIASES)
        assert scores["B0"]["n"] == 5 and scores["B3"]["n_loc"] == 4

        _, rows, errs = _rows(_shard(cfg, "rome_N"))
        assert [(e["case_id"], e["error_kind"]) for e in errs] == [("cf_5", "missing_delta")]
        assert "cf_5" not in {r["case_id"] for r in rows}
        assert all(r["delta_sha"] and r["alpha"] == 1.0 and r["target_tag"] == "cf" for r in rows)
        _, a2, _ = _rows(_shard(cfg, "rome_a2"))
        assert all(r["alpha"] == 2.0 for r in a2)

        _, rows, _ = _rows(_shard(cfg, "rome_T"))
        for r in rows:
            case = next(c for c in CASES if c["case_id"] == r["case_id"])
            assert r["bias"]["token_ids"] == sorted(build_old_token_ids(tok, case["o_old"], ALIASES))
            assert r["bias"]["target"] == case["o_old"] and r["bias"]["penalty"] == 8
            assert r["bias"]["applied"] == (r["probe"] == "efficacy" and r["budget"] == "B3")
            assert (r["bias"]["steps"] is not None) == r["bias"]["applied"]
        _, rows, _ = _rows(_shard(cfg, "rome_P"))
        assert all(r["bias"]["target"] == "Sydney" and r["bias"]["applied"] for r in rows)

        _, rows, _ = _rows(_shard(cfg, "ike"))
        assert rows[0]["user_prefix"] == "Fact: Oseberg ship is located in Italy.\n"
        assert rows[0]["q"] == "Oseberg ship is located in" and rows[0]["editor"] == "IKE"

        _, rows, _ = _rows(_shard(cfg, "rome_samp"))
        assert sorted({(r["decode"], r["seed"], r["temperature"]) for r in rows}) == [
            ("sample", 0, 0.6), ("sample", 1, 0.6)]
        assert metrics.score(_shard(cfg, "rome_samp"), CASES, ALIASES, decode="sample")["B3"]["n"] == 8


def test_resume_skips_done_rows_and_retries_errors():
    model, tok = _model()
    with tempfile.TemporaryDirectory() as d:
        _world(d, model)
        cfg = _cfg(d)
        _quiet(R.run_config, cfg, model=model, tok=tok)
        again = _quiet(R.run_config, cfg, model=model, tok=tok)
        assert set(again.values()) == {0}
        path = _shard(cfg, "base")
        lines = open(path).readlines()
        open(path, "w").writelines(lines[:-3])
        dropped = [json.loads(l) for l in lines[-3:]]
        again = _quiet(R.run_config, cfg, model=model, tok=tok)
        assert again["base"] == 3 and sum(again.values()) == 3
        _, rows, _ = _rows(path)
        key = lambda r: (r["case_id"], r["budget"], r["probe"], r["decode"], r["seed"])
        assert sorted(map(key, rows)) == sorted(set(map(key, rows)))
        assert {key(r) for r in dropped} <= {key(r) for r in rows}
        _save(d, model, "cf_5", seed=99)             # the missing delta arrives
        again = _quiet(R.run_config, cfg, model=model, tok=tok)
        assert again["rome_N"] == 4 and again["base"] == 0
        _, rows, errs = _rows(_shard(cfg, "rome_N"))
        assert "cf_5" in {r["case_id"] for r in rows}
        assert len(errs) == 3                        # one error row per attempt while the delta was missing


def test_resume_refuses_changed_config_or_code():
    model, tok = _model()
    with tempfile.TemporaryDirectory() as d:
        _world(d, model)
        cfg = _cfg(d)
        _quiet(R.run_config, cfg, model=model, tok=tok, only=["base", "rome_T"])
        bumped = copy.deepcopy(cfg)
        bumped["arms"]["penalty"] = 4
        R.prepare(bumped, only=["base"])            # other conditions are unaffected
        try:
            R.prepare(bumped, only=["rome_T"])
        except RuntimeError as e:
            assert "config_sha256" in str(e)
        else:
            raise AssertionError("a changed penalty must refuse resume")
        tuned = copy.deepcopy(cfg)
        tuned["engine"].update(batch_size=1, chunk_cases=5)
        R.prepare(tuned)                              # batching knobs do not change row meaning
        path = _shard(cfg, "base")
        lines = open(path).readlines()
        hdr = json.loads(lines[0])
        hdr["code_sha256"] = dict(hdr["code_sha256"], **{"src/rt/engine.py": "0" * 64})
        open(path, "w").writelines([json.dumps(hdr) + "\n"] + lines[1:])
        try:
            R.prepare(cfg, only=["base"])
        except RuntimeError as e:
            assert "code_sha256" in str(e)
        else:
            raise AssertionError("changed code must refuse resume")
        open(path, "w").writelines(lines[1:])
        try:
            R.prepare(cfg, only=["base"])
        except RuntimeError as e:
            assert "headerless" in str(e)
        else:
            raise AssertionError("a headerless shard must refuse resume")


def test_sharding_covers_every_case_once():
    model, tok = _model()
    with tempfile.TemporaryDirectory() as d:
        _world(d, model)
        cfg = _cfg(d)
        seen = []
        for rank in range(2):
            _quiet(R.run_config, cfg, rank=rank, world=2, model=model, tok=tok, only=["base"])
            _, rows, _ = _rows(_shard(cfg, "base", rank, 2))
            ids = sorted({r["case_id"] for r in rows})
            assert ids == sorted(c["case_id"] for i, c in enumerate(CASES) if i % 2 == rank)
            seen += ids
        assert sorted(seen) == sorted(c["case_id"] for c in CASES)


def _given_cfg(cfg, transform, require=True, editor="ROME"):
    g = copy.deepcopy(cfg)
    rome = {"target_tag": "cf", "deltas_dir": cfg["conditions"][1]["deltas_dir"]} if editor == "ROME" else {}
    g["conditions"] = [{"name": f"g_{transform}", "editor": editor, **rome, "budgets": ["GIVEN"],
                        "probes": ["efficacy"], "stage": 2,
                        "given_chain": {"source": os.path.join(cfg["out_dir"], "tiny_t_rome_N_r*of*.jsonl"),
                                        "condition": "rome_N", "budget": "B3", "transform": transform,
                                        "seed": 7, "require_complete": require}}]
    return g


def test_given_chain_transforms():
    model, tok = _model()
    ntok = lambda s: len(tok(s, add_special_tokens=False)["input_ids"])
    with tempfile.TemporaryDirectory() as d:
        _world(d, model, with_delta=("cf_1", "cf_2", "cf_3", "cf_4", "cf_5"))
        cfg = _cfg(d)
        _quiet(R.run_config, cfg, model=model, tok=tok, only=["rome_N"])
        _, src, _ = _rows(_shard(cfg, "rome_N"))
        own = {r["case_id"]: r["cot"] for r in src if r["budget"] == "B3" and r["probe"] == "efficacy"}
        assert len(own) == 5
        got = {}
        for t in ("own", "filler", "swap"):
            g = _given_cfg(cfg, t)
            assert R.prepare(g, stage=1)["conds"] == []
            _quiet(R.run_config, g, model=model, tok=tok, stage=2)
            _, rows, errs = _rows(_shard(g, f"g_{t}"))
            assert len(rows) == 5 and not errs
            assert all(r["budget"] == "GIVEN" and r["chain_end"] == "given" for r in rows)
            got[t] = {r["case_id"]: r for r in rows}
        for cid, r in got["own"].items():
            assert r["cot"] == own[cid] and r["given"]["source_case"] == cid
        for cid, r in got["filler"].items():
            assert set(r["cot"]) <= {" ", "."} and ntok(r["cot"]) == ntok(own[cid]) == r["n_chain_tokens"]
            assert r["given"]["n_tokens"] == r["given"]["n_tokens_target"]
        donors = {cid: r["given"]["source_case"] for cid, r in got["swap"].items()}
        assert all(donors[c] != c for c in donors) and sorted(donors.values()) == sorted(donors)
        assert all(got["swap"][c]["cot"] == own[donors[c]] for c in donors)
        assert R.swap_map({c: ntok(v) for c, v in own.items()}, 7) == donors


def test_given_chain_requires_complete_source():
    model, tok = _model()
    with tempfile.TemporaryDirectory() as d:
        _world(d, model)                               # cf_5 has no delta -> no rome_N chain
        cfg = _cfg(d)
        _quiet(R.run_config, cfg, model=model, tok=tok, only=["rome_N"])
        try:
            R.prepare(_given_cfg(cfg, "own"))
        except ValueError as e:
            assert "given chains missing" in str(e)
        else:
            raise AssertionError("an incomplete chain source must refuse to start")
        g = _given_cfg(cfg, "swap", require=False, editor="none")
        _quiet(R.run_config, g, model=model, tok=tok)
        _, rows, errs = _rows(_shard(g, "g_swap"))
        assert [(e["case_id"], e["error_kind"]) for e in errs] == [("cf_5", "missing_chain")]
        assert len(rows) == 4


def test_filler_text_is_exact_and_content_free():
    tok = tiny_tokenizer()
    for n in range(0, 40):
        f = R.filler_text(tok, n)
        assert len(tok(f, add_special_tokens=False)["input_ids"]) == n and set(f) <= {" ", "."}
    assert R.filler_text(tok, 7) == R.filler_text(tok, 7)


def test_swap_map_is_a_seeded_nearest_length_derangement():
    for n in range(2, 12):
        lengths = {f"c{i}": (i * 7) % 5 + i for i in range(n)}
        m = R.swap_map(lengths, seed=3)
        assert sorted(m) == sorted(lengths) and sorted(m.values()) == sorted(lengths)
        assert all(m[c] != c for c in m)
        assert m == R.swap_map(dict(reversed(list(lengths.items()))), seed=3)
        order = sorted(lengths.values())
        for c, donor in m.items():                     # donor is at most two ranks away in length
            ranks = [i for i, v in enumerate(order) if v == lengths[c]]
            dr = [i for i, v in enumerate(order) if v == lengths[donor]]
            assert min(abs(a - b) for a in ranks for b in dr) <= 2
    ties = {f"c{i}": 5 for i in range(8)}
    assert R.swap_map(ties, 1) != R.swap_map(ties, 2)
    try:
        R.swap_map({"a": 1}, 0)
    except ValueError:
        return
    raise AssertionError("one chain cannot be deranged")


def test_probe_text():
    c = CASES[1]
    assert R.probe_text(c, "efficacy") == c["prompt"] and R.probe_text(c, "para0") == c["paraphrases"][0]
    assert R.probe_text(c, "para1") is None and R.probe_text(c, "locality") is None
    assert R.probe_text(CASES[0], "locality") == "Bergen is located in"


def test_manifest_dataset_and_sha_check():
    with tempfile.TemporaryDirectory() as d:
        model, _ = _model()
        _world(d, model)
        m = os.path.join(d, "m.jsonl")
        open(m, "w").write('{"case_id": "cf_3"}\n{"case_id": "cf_1"}\n')
        cases, _ = R.load_cases({"path": os.path.join(d, "cf.jsonl"), "manifest": m})
        assert [c["case_id"] for c in cases] == ["cf_3", "cf_1"]
        open(m + ".sha256", "w").write("0" * 64 + "  m.jsonl\n")
        try:
            R.load_cases({"path": os.path.join(d, "cf.jsonl"), "manifest": m})
        except ValueError:
            return
    raise AssertionError("a manifest whose sha256 sidecar differs must be refused")


def test_template_guard_runs_before_any_write():
    model, tok = _model()
    with tempfile.TemporaryDirectory() as d:
        _world(d, model)
        cfg = dict(_cfg(d), template="qwq")
        try:
            _quiet(R.run_config, cfg, model=model, tok=tok, only=["base"])
        except ValueError as e:
            assert "exactly one token" in str(e)
        else:
            raise AssertionError("qwq on a tokenizer without ChatML tokens must refuse")
        assert not glob.glob(os.path.join(cfg["out_dir"], "*.jsonl"))


def test_chatml_template_rows():
    tok = tiny_tokenizer()
    tok.add_tokens([IM_START, IM_END], special_tokens=True)
    model, tok = _model(tok)
    with tempfile.TemporaryDirectory() as d:
        _world(d, model)
        for t in ("qwq", "instruct_cot"):
            cfg = dict(_cfg(d), template=t, run_tag=t)
            _quiet(R.run_config, cfg, model=model, tok=tok, only=["base"])
            hdr, rows, _ = _rows(_shard(cfg, "base", run_tag=t))
            assert hdr["template"] == t and hdr["model"]["template"]["name"] == t
            assert all(r["template"] == t for r in rows) and len(rows) == 18


def test_cli_dry_run_loads_no_model():
    import yaml
    model, _ = _model()
    with tempfile.TemporaryDirectory() as d:
        _world(d, model)
        p = os.path.join(d, "c.yaml")
        yaml.safe_dump(_cfg(d), open(p, "w"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            R.main(["--config", p, "--rank", "1", "--world", "2", "--dry-run", "--conditions", "base,ike"])
        out = buf.getvalue()
        assert "pending=" in out and "base" in out and "ike" in out and "rome_T" not in out
        assert not os.path.exists(os.path.join(d, "out"))
