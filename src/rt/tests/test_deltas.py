"""rt.deltas with a mock EasyEdit editor on the tiny model: extraction, factoring, restore, resume,
AlphaEdit cache isolation, error rows, configuration files."""
import contextlib
import io
import json
import os
import sys
import tempfile
import types
from types import SimpleNamespace

import torch

from rt import deltas
from rt.edit_hooks import load_delta
from rt.targets import continuation_logprobs
from rt.tests._tiny import MODULE_TMP, merged_copy, rank1_edit, tiny_model, tiny_tokenizer
from vendor_patches import easyedit_alphaedit_cache

CASES = [
    {"case_id": "cf_1", "prompt": "The capital of Avalon is", "s": "Avalon", "o_old": "Camelot",
     "o_new": "Paris", "r": "P36"},
    {"case_id": "cf_2", "prompt": "Brin Tor speaks", "s": "Brin Tor", "o_old": "Welsh",
     "o_new": "Dutch", "r": "P1412"},
    {"case_id": "cf_3", "prompt": "Oskar Vale plays", "s": "Oskar Vale", "o_old": "guitar",
     "o_new": "violin", "r": "P1303"},
]


def _cases():
    return deltas.attach_targets(CASES, "cf")


def _name(L):
    return f"{MODULE_TMP.format(L)}.weight"


def _seed(target, layer):
    return sum(map(ord, target)) + 97 * layer


def rank1_update(model, target, layer):
    (A, B), = rank1_edit(model, layer, seed=_seed(target, layer)).values()
    return B @ A


class MockEditor:
    """Stands in for easyeditor.BaseEditor: edits the weights in place, returns weights_copy."""

    def __init__(self, model, tok, layers=(1,), update=rank1_update, fail_after_modify=False,
                 extra_copy=None, alg="ROME"):
        self.model, self.tok = model, tok
        self.hparams = SimpleNamespace(layers=list(layers), rewrite_module_tmp=MODULE_TMP,
                                       alg_name=alg)
        self.update, self.fail_after_modify, self.extra_copy = update, fail_after_modify, extra_copy
        self.calls = 0

    def edit(self, prompts, ground_truth, target_new, subject, sequential_edit):
        assert sequential_edit is True and len(prompts) == len(target_new) == 1
        self.calls += 1
        wcopy = {}
        with torch.no_grad():
            for L in self.hparams.layers:
                p = self.model.get_parameter(_name(L))
                wcopy[_name(L)] = p.detach().clone()
                p += self.update(self.model, target_new[0], L)
            if self.extra_copy is not None:
                wcopy[_name(self.extra_copy)] = self.model.get_parameter(
                    _name(self.extra_copy)).detach().clone()
        print("loss 2.513 = 2.4 + 0.1 + 0.013 avg prob of [ x] 0.081")
        print("loss 0.041 = 0.03 + 0.01 + 0.001 avg prob of [ x] 0.97")
        if self.fail_after_modify:
            raise RuntimeError("boom inside edit(), after the weights changed")
        return [{"pre": {"rewrite_acc": [0.0]}, "post": {"rewrite_acc": [1.0]}}], self.model, wcopy


def _spec(editor="ROME", layers=(1,), **factor):
    return deltas.RunSpec(model_tag="tiny", editor=editor, target_tag="cf", module_tmp=MODULE_TMP,
                          hparams_sig={"hparams": {"layers": list(layers)}, "dtype": "float32"},
                          factor=dict(deltas.FACTOR_DEFAULT, **factor))


def _setup():
    tok = tiny_tokenizer()
    return tiny_model(vocab=len(tok)), tok


def _state(model):
    return {k: v.detach().clone() for k, v in model.state_dict().items()}


def _same_state(model, state):
    return all(torch.equal(v, state[k]) for k, v in model.state_dict().items())


def _log_rows(path):
    with open(path) as fh:
        return [json.loads(x) for x in fh if x.strip()]


def _run(editor, cases, d, spec=None, **kw):
    spec = spec or _spec(layers=editor.hparams.layers)
    log = os.path.join(d, "log.jsonl")
    with contextlib.redirect_stdout(io.StringIO()):
        counts = deltas.run_shard(editor, cases, spec, os.path.join(d, "deltas"), log,
                                  log=lambda *a: None, **kw)
    return counts, log, spec


def _delta_file(d, case_id, editor="ROME"):
    return deltas.delta_path(os.path.join(d, "deltas"), "tiny", editor, "cf", case_id)


def test_extract_and_factor_equal_injected_rank1():
    model, tok = _setup()
    before = _state(model)
    with tempfile.TemporaryDirectory() as d:
        counts, log, _ = _run(MockEditor(model, tok, layers=[1]), _cases(), d)
        assert counts["ok"] == 3 and counts["error"] == 0
        assert _same_state(model, before)
        for c in _cases():
            edit, rec = load_delta(_delta_file(d, c["case_id"]))
            (L, (A, B)), = edit.items()
            want = rank1_update(model, c["target"], 1)
            assert L == 1 and A.shape[0] == 1 and rec["fit"][1]["rank"] == 1
            assert torch.allclose(B @ A, want, atol=1e-6, rtol=1e-4)
            assert rec["target"] == c["o_new"] and rec["module_tmp"] == MODULE_TMP
            assert rec["diag"]["editor_log"]["n_steps"] == 2
            assert rec["diag"]["editor_log"]["loss"] == [2.513, 0.041]
            assert rec["diag"]["easyedit_metrics"]["post_rewrite_acc"] == [1.0]
        rows = [r for r in _log_rows(log) if r.get("case_id")]
        assert [r["status"] for r in rows] == ["ok"] * 3


def test_multi_layer_update_all_layers_saved():
    model, tok = _setup()
    with tempfile.TemporaryDirectory() as d:
        _run(MockEditor(model, tok, layers=[0, 1]), _cases()[:1], d, spec=_spec(layers=[0, 1]))
        edit, rec = load_delta(_delta_file(d, "cf_1"))
        assert sorted(edit) == [0, 1]
        for L in (0, 1):
            A, B = edit[L]
            assert torch.allclose(B @ A, rank1_update(model, "Paris", L), atol=1e-6, rtol=1e-4)


def test_saved_delta_reproduces_edited_model():
    model, tok = _setup()
    with tempfile.TemporaryDirectory() as d:
        _run(MockEditor(model, tok, layers=[1]), _cases()[:1], d)
        edit, _ = load_delta(_delta_file(d, "cf_1"))
        ref = merged_copy(model, edit)
        exact = merged_copy(model, {1: (torch.eye(48), rank1_update(model, "Paris", 1))})
        ids = torch.tensor([[3, 17, 9, 41, 5, 22]])
        with torch.no_grad():
            assert torch.allclose(ref(input_ids=ids).logits, exact(input_ids=ids).logits,
                                  atol=1e-5)


def test_diag_scores_before_and_after_edit():
    model, tok = _setup()
    with tempfile.TemporaryDirectory() as d:
        _run(MockEditor(model, tok, layers=[1]), _cases()[:1], d)
        _, rec = load_delta(_delta_file(d, "cf_1"))
    c = _cases()[0]
    base = continuation_logprobs(model, tok, c["prompt"], [" Paris", " Camelot"])
    edited = merged_copy(model, {1: (torch.eye(48), rank1_update(model, "Paris", 1))})
    after = continuation_logprobs(edited, tok, c["prompt"], [" Paris", " Camelot"])
    lb, la = rec["diag"]["lp_before"], rec["diag"]["lp_after"]
    for got, want in ((lb["o_new"], base[0]), (lb["o_old"], base[1]),
                      (la["o_new"], after[0]), (la["o_old"], after[1])):
        assert abs(got["first"] - want["first"]) < 1e-4 and abs(got["sum"] - want["sum"]) < 1e-4
    assert lb["target"] == lb["o_new"]


def test_restore_on_exception_inside_edit():
    model, tok = _setup()
    before = _state(model)
    with tempfile.TemporaryDirectory() as d:
        ed = MockEditor(model, tok, layers=[1], fail_after_modify=True)
        counts, log, _ = _run(ed, _cases()[:2], d)
        assert counts == {"ok": 0, "error": 2, "skipped_existing": 0, "skipped_error": 0}
        assert _same_state(model, before), "edit leaked into the model after an exception"
        assert not os.path.exists(_delta_file(d, "cf_1"))
        rows = [r for r in _log_rows(log) if r.get("case_id")]
        assert all(r["stage"] == "edit" and "boom" in r["error"] for r in rows)
        # the next case after a failed one starts from the base weights
        ed.fail_after_modify = False
        _run(ed, _cases()[:2], d, retry_errors=True)
        edit, _ = load_delta(_delta_file(d, "cf_2"))
        A, B = edit[1]
        assert torch.allclose(B @ A, rank1_update(model, "Dutch", 1), atol=1e-6, rtol=1e-4)


def test_non_low_rank_update_is_an_error_row():
    model, tok = _setup()
    before = _state(model)

    def rank3(m, target, layer):
        g = torch.Generator().manual_seed(_seed(target, layer))
        return 0.3 * torch.randn(32, 3, generator=g) @ torch.randn(3, 48, generator=g)

    with tempfile.TemporaryDirectory() as d:
        counts, log, _ = _run(MockEditor(model, tok, layers=[1], update=rank3), _cases()[:1], d)
        assert counts["error"] == 1 and not os.path.exists(_delta_file(d, "cf_1"))
        row = [r for r in _log_rows(log) if r.get("case_id")][0]
        assert row["stage"] == "factor" and "not rank" in row["error"]
        fit = row["fit"]["1"]
        assert fit["ok"] is False and fit["rel_err"] > 0.1 and len(fit["sigma"]) == 3
    assert _same_state(model, before)


def test_fit_tolerance_follows_fp32_storage_floor():
    model, _ = _setup()
    W = model.get_parameter(_name(1)).detach().clone()
    g = torch.Generator().manual_seed(4)
    u, v = torch.randn(32, 1, generator=g), torch.randn(1, 48, generator=g)
    tiny = u @ v * (3e-5 * torch.linalg.norm(W) / torch.linalg.norm(u @ v))
    d = (W + tiny) - W                                   # what extraction sees in fp32
    from rt.edit_hooks import factor_delta
    assert not factor_delta(d, max_rank=1, tol=1e-4)[2]["ok"], "rounding floor should exceed 1e-4"
    _, _, fit = deltas.factor_update(d, float(torch.linalg.norm(W + tiny)), deltas.FACTOR_DEFAULT)
    assert fit["ok"] and fit["rank"] == 1 and fit["tol"] > 1e-4
    g = torch.Generator().manual_seed(5)
    r3 = torch.randn(32, 3, generator=g) @ torch.randn(3, 48, generator=g)
    r3 = r3 * (3e-5 * torch.linalg.norm(W) / torch.linalg.norm(r3))
    _, _, fit3 = deltas.factor_update((W + r3) - W, float(torch.linalg.norm(W + r3)),
                                      deltas.FACTOR_DEFAULT)
    assert not fit3["ok"], "a genuinely rank-3 update must still fail at the same scale"
    try:
        deltas.factor_update(torch.zeros(4, 5), 1.0, deltas.FACTOR_DEFAULT)
    except ValueError:
        return
    raise AssertionError("zero delta must raise")


def test_resume_skips_existing_files():
    model, tok = _setup()
    with tempfile.TemporaryDirectory() as d:
        _run(MockEditor(model, tok), _cases(), d)
        os.remove(_delta_file(d, "cf_2"))
        ed = MockEditor(model, tok)
        counts, _, _ = _run(ed, _cases(), d)
        assert ed.calls == 1 and counts["skipped_existing"] == 2 and counts["ok"] == 1
        ed = MockEditor(model, tok)
        counts, _, _ = _run(ed, _cases(), d)
        assert ed.calls == 0 and counts["skipped_existing"] == 3


def test_resume_refuses_other_hparams_or_signature():
    model, tok = _setup()
    with tempfile.TemporaryDirectory() as d:
        _run(MockEditor(model, tok), _cases()[:1], d)
        other = _spec()
        other.hparams_sig = {"hparams": {"layers": [1], "v_lr": 0.1}, "dtype": "float32"}
        try:
            _run(MockEditor(model, tok), _cases()[:1], d, spec=other)
        except RuntimeError as e:
            assert "run signature" in str(e)
        else:
            raise AssertionError("log with another run signature must be refused")
        os.remove(os.path.join(d, "log.jsonl"))
        try:
            _run(MockEditor(model, tok), _cases()[:1], d, spec=other)
        except RuntimeError as e:
            assert "refusing to mix" in str(e)
        else:
            raise AssertionError("an existing delta with other hparams must be refused")


def test_error_rows_are_skipped_unless_retry():
    model, tok = _setup()
    with tempfile.TemporaryDirectory() as d:
        _run(MockEditor(model, tok, fail_after_modify=True), _cases()[:1], d)
        ed = MockEditor(model, tok)
        counts, _, _ = _run(ed, _cases()[:1], d)
        assert ed.calls == 0 and counts["skipped_error"] == 1
        counts, _, _ = _run(ed, _cases()[:1], d, retry_errors=True)
        assert ed.calls == 1 and counts["ok"] == 1


def test_unexpected_edited_weight_stops_the_shard():
    model, tok = _setup()
    with tempfile.TemporaryDirectory() as d:
        try:
            _run(MockEditor(model, tok, layers=[1], extra_copy=0), _cases(), d)
        except deltas.Contamination:
            rows = [r for r in _log_rows(os.path.join(d, "log.jsonl")) if r.get("case_id")]
            assert len(rows) == 1 and rows[0]["stage"] == "restore"
            return
    raise AssertionError("an edit touching an unexpected weight must stop the shard")


def test_summarize_reports_latest_row_per_case():
    model, tok = _setup()
    with tempfile.TemporaryDirectory() as d:
        _, log, _ = _run(MockEditor(model, tok, fail_after_modify=True), _cases(), d)
        _run(MockEditor(model, tok), _cases()[:2], d, retry_errors=True)
        s = deltas.summarize([log])
        assert s["cases"] == 3 and s["ok"] == 2 and s["errors"] == {"edit": 1}
        assert s["error_ids"] == {"edit": ["cf_3"]} and s["max_rank"] == 1
        assert s["editor_nan"] == 0
        assert s["median_p_target_after"] is not None and s["median_wall_s"] is not None


def test_sharding_partitions_the_pool():
    cases = [{"case_id": f"cf_{i}"} for i in range(11)]
    parts = [deltas.shard(cases, r, 4) for r in range(4)]
    ids = sorted(c["case_id"] for p in parts for c in p)
    assert ids == sorted(c["case_id"] for c in cases)
    assert [c["case_id"] for c in parts[1]] == ["cf_1", "cf_5", "cf_9"]


# ---------------------------------------------------------------- AlphaEdit cache isolation
AE = "easyeditor.models.alphaedit.AlphaEdit_main"


def _install_fake_alphaedit():
    """A module with AlphaEdit's cache_c semantics (AlphaEdit_main.py L79-86, L229-233, L257-259)."""
    saved = {k: sys.modules.get(k) for k in ("easyeditor", "easyeditor.models",
                                             "easyeditor.models.alphaedit", AE)}
    mod = types.ModuleType(AE)
    mod.cache_c_new = False

    def apply(W, k, r, L2=1.0):
        if not mod.cache_c_new:
            mod.cache_c = torch.zeros(k.numel(), k.numel())
            mod.cache_c_new = True
        K = k[:, None]
        upd = torch.linalg.solve(K @ K.T + mod.cache_c + L2 * torch.eye(k.numel()), K @ r[None, :])
        W += upd.T
        mod.cache_c += K @ K.T

    mod.apply = apply
    for name in ("easyeditor", "easyeditor.models", "easyeditor.models.alphaedit"):
        sys.modules[name] = types.ModuleType(name)
    sys.modules[AE] = mod
    return mod, saved


def _restore_modules(saved):
    for k, v in saved.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v


class MockAlphaEditor(MockEditor):
    def __init__(self, model, tok, mod):
        super().__init__(model, tok, layers=[1], alg="AlphaEdit")
        self.mod = mod

    def edit(self, prompts, ground_truth, target_new, subject, sequential_edit):
        assert sequential_edit is True
        self.calls += 1
        n = _name(1)
        p = self.model.get_parameter(n)
        wcopy = {n: p.detach().clone()}
        g = torch.Generator().manual_seed(_seed(target_new[0], 1))
        k, r = 2 * torch.randn(p.shape[1], generator=g), torch.randn(p.shape[0], generator=g)
        with torch.no_grad():
            self.mod.apply(p, k, r)
        return [{"pre": {}, "post": {}}], self.model, wcopy


def _alphaedit_delta(case_ids, reset):
    model, tok = _setup()
    mod, saved = _install_fake_alphaedit()
    try:
        with tempfile.TemporaryDirectory() as d:
            cases = [c for c in _cases() if c["case_id"] in case_ids]
            cases.sort(key=lambda c: case_ids.index(c["case_id"]))
            _run(MockAlphaEditor(model, tok, mod), cases, d, spec=_spec(editor="AlphaEdit"),
                 reset=reset)
            edit, rec = load_delta(_delta_file(d, case_ids[-1], editor="AlphaEdit"))
            A, B = edit[1]
            return B @ A, rec["diag"]["reset"], mod
    finally:
        _restore_modules(saved)


def test_alphaedit_cache_reset_isolates_cases():
    alone, info_alone, _ = _alphaedit_delta(["cf_2"], easyedit_alphaedit_cache.reset)
    after, info_after, mod = _alphaedit_delta(["cf_1", "cf_2"], easyedit_alphaedit_cache.reset)
    assert torch.allclose(after, alone, atol=1e-7), "cf_2's delta must not depend on cf_1"
    assert info_alone == {"cache_c_new_before": False, "had_cache_c": False}
    assert info_after == {"cache_c_new_before": True, "had_cache_c": True}
    leaked, _, _ = _alphaedit_delta(["cf_1", "cf_2"], None)
    assert not torch.allclose(leaked, alone, atol=1e-4), "the mock must reproduce the leak"


def test_alphaedit_reset_drops_the_tensor():
    mod = types.ModuleType("m")
    mod.cache_c_new, mod.cache_c = True, torch.ones(2, 2)
    info = easyedit_alphaedit_cache.reset(mod)
    assert info == {"cache_c_new_before": True, "had_cache_c": True}
    assert mod.cache_c_new is False and not hasattr(mod, "cache_c")


# ---------------------------------------------------------------- small pieces
def test_parse_editor_log():
    text = "\n".join([
        "Computing right vector (v)",
        "loss 9.117 = 9.117 + 0.0 + 0.0 avg prob of [ Paris] 0.00012",
        "loss nan = nan + 0.0 + 0.0 avg prob of [ Paris] nan",
        "Delta norm: 41.5",
        "Right vector norm: tensor(0.73, device='cuda:0')",
        "z error tensor(12.5, device='cuda:0')", "upd norm tensor(3.25, device='cuda:0')"])
    out = deltas.parse_editor_log(text)
    assert out["n_steps"] == 2 and out["loss"][0] == 9.117 and out["nan"] is True
    assert out["delta_norm"] == [41.5] and out["right_vector_norm"] == [0.73]
    assert out["z_error"] == [12.5] and out["upd_norm"] == [3.25]
    assert deltas.parse_editor_log("nothing") == {"n_steps": 0, "nan": False}


def test_check_routing():
    deltas.check_routing("deepseek-ai/DeepSeek-R1-Distill-Qwen-32B", "qwen2")
    deltas.check_routing("/m/public_models/Qwen/QwQ-32B", "qwen2")
    deltas.check_routing("/m/DeepSeek-R1-Distill-Llama-70B", "llama")
    for bad, fam in (("/m/QwQ-32B", "qwen2"), ("/m/R1-8B", "llama")):
        try:
            deltas.check_routing(bad, fam)
        except ValueError:
            continue
        raise AssertionError(f"{bad} must be refused")
    assert deltas.resolve_model_path("/m/Qwen-32B/", {"hf_id": "x"}) == "/m/Qwen-32B"


def test_hparams_signature_ignores_device_and_dirs():
    a = SimpleNamespace(layers=[12], model_name="/a/b/DeepSeek-R1-Distill-Qwen-32B", device=3,
                        stats_dir="/x/data/stats_r1qwen32b")
    b = SimpleNamespace(layers=[12], model_name="/c/DeepSeek-R1-Distill-Qwen-32B/", device=0,
                        stats_dir="/y/stats_r1qwen32b")
    assert deltas.hparams_signature(a, "float32") == deltas.hparams_signature(b, "float32")
    b.layers = [11]
    assert deltas.hparams_signature(a, "float32") != deltas.hparams_signature(b, "float32")


def test_targets_for_other_tags_are_required():
    cases = deltas.attach_targets(CASES, "plausible", {"cf_1": "Rome", "cf_2": "German",
                                                       "cf_3": "cello"})
    assert [c["target"] for c in cases] == ["Rome", "German", "cello"]
    try:
        deltas.attach_targets(CASES, "plausible", {"cf_1": "Rome"})
    except ValueError:
        return
    raise AssertionError("a missing target must raise")


def test_preflight_needs_stats_and_matching_projector():
    from rt import mom2
    import numpy as np
    with tempfile.TemporaryDirectory() as d:
        hp = SimpleNamespace(layers=[10, 11], rewrite_module_tmp=MODULE_TMP, stats_dir=d,
                             mom2_dataset="wikipedia", mom2_n_samples=100000,
                             mom2_dtype="float32", nullspace_threshold=2e-2,
                             P_loc=os.path.join(d, "P.pt"))
        path = "/m/Qwen/DeepSeek-R1-Distill-Qwen-32B"
        try:
            deltas.preflight(hp, "MEMIT", "qwen2", path, npos=4096)
        except FileNotFoundError as e:
            assert "precompute-stats" in str(e)
        else:
            raise AssertionError("missing statistics must be refused")
        files = deltas.mom2_files(hp, path, 4096)
        for f in files.values():
            mom2.save_easyedit_stats(f, np.eye(3, dtype=np.float32), 7, 100000)
        facts = deltas.preflight(hp, "MEMIT", "qwen2", path, npos=4096)
        assert facts[MODULE_TMP.format(10)]["count"] == 7
        mom2.save_projector(hp.P_loc, [torch.eye(3)] * 2, [10, 12],
                            {"threshold": 0.02, "sample_size": 100000})
        try:
            deltas.preflight(hp, "AlphaEdit", "qwen2", path, npos=4096)
        except ValueError as e:
            assert "built for" in str(e)
        else:
            raise AssertionError("a projector for other layers must be refused")
        mom2.save_projector(hp.P_loc, [torch.eye(3)] * 2, [10, 11],
                            {"threshold": 0.02, "sample_size": 100000, "null_dim": {}})
        assert "P" in deltas.preflight(hp, "AlphaEdit", "qwen2", path, npos=4096)


def test_export_pool_first_seen_order():
    with tempfile.TemporaryDirectory() as d:
        pool = [f"cf_{i}" for i in (7, 3, 9, 1, 4)]
        for r in range(2):
            with open(os.path.join(d, f"m_ROME_cf_r{r}of2.jsonl"), "w") as fh:
                fh.write(json.dumps({"_meta": True}) + "\n")
                for cid in pool[r::2]:
                    for budget in ("B0", "B3"):
                        fh.write(json.dumps({"case_id": cid, "budget": budget, "probe": "efficacy",
                                             "q": f"prompt {cid}"}) + "\n")
                fh.write(json.dumps({"case_id": pool[r], "error": "OOM"}) + "\n")
        ds = os.path.join(d, "cf.jsonl")
        with open(ds, "w") as fh:
            for cid in pool:
                fh.write(json.dumps({"case_id": cid, "prompt": f"prompt {cid}"}) + "\n")
        out = os.path.join(d, "pool.json")
        m = deltas.export_pool(os.path.join(d, "m_ROME_cf_r*of2.jsonl"), out, "t", ds)
        assert m["case_ids"] == pool[0::2] + pool[1::2]
        assert m["checks"]["efficacy_prompt_mismatch"] == [] and m["checks"]["in_dataset"] == 5
        assert m["checks"]["cases_with_error_rows"] == sorted([pool[0], pool[1]])
        ids, meta = deltas.load_pool(out)
        assert ids == m["case_ids"] and meta["sha256"] == m["sha256"]
        os.remove(os.path.join(d, "m_ROME_cf_r1of2.jsonl"))
        try:
            deltas.export_pool(os.path.join(d, "m_ROME_cf_r*of2.jsonl"), out, "t", ds)
        except ValueError:
            return
    raise AssertionError("an incomplete shard set must be refused")


def test_committed_study1_pool_manifest():
    ids, meta = deltas.load_pool(os.path.join(deltas._ROOT, "data/pools/study1_r1qwen32b_ids.json"))
    assert len(ids) == 200 and len(set(ids)) == 200 and ids[0] == "cf_18876"
    assert meta["name"] == "study1_r1qwen32b"


def test_models_file_encodes_study1_settings():
    models = deltas.load_models(os.path.join(deltas._ROOT, "experiments/rt/deltas_models.yaml"))
    m = models["models"]
    rome = {tag: spec["editors"]["ROME"]["overrides"] for tag, spec in m.items()}
    assert {t: o["layers"] for t, o in rome.items()} == {
        "r1qwen1_5b": [5], "r1qwen7b": [5], "r1qwen14b": [9], "r1qwen32b": [12],
        "r1llama8b": [6], "r1llama70b": [14], "qwq32b": [12], "qwen2_5_32b_instruct": [12]}
    assert rome["r1llama8b"]["clamp_norm_factor"] == 2
    assert rome["r1llama70b"]["model_parallel"] is True
    for tag, spec in m.items():
        for ed, e in spec["editors"].items():
            assert e["overrides"]["v_loss_layer"] == spec["n_layers"] - 1, (tag, ed)
            assert e["hparams"].endswith(f"{ed}/qwen2.5-7b.yaml"), (tag, ed)
    for tag in ("qwq32b", "qwen2_5_32b_instruct"):
        assert "verify" in m[tag]["editors"]["ROME"]
    q32 = m["r1qwen32b"]["editors"]
    band = q32["MEMIT"]["overrides"]["layers"]
    assert band == q32["AlphaEdit"]["overrides"]["layers"] == list(range(band[0], band[0] + 5))
    assert 12 in band and 4 / 28 * 64 <= band[0] and band[-1] <= 8 / 28 * 64
    assert q32["MEMIT"]["overrides"]["model_parallel"] and "verify" in q32["MEMIT"]
    assert q32["AlphaEdit"]["overrides"]["P_loc"].startswith(m["r1qwen32b"]["stats_dir"])
    s = deltas.editor_settings(models, "r1qwen32b", "AlphaEdit")
    assert os.path.isabs(s["overrides"]["stats_dir"]) and os.path.isabs(s["overrides"]["P_loc"])
