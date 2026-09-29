"""rt.mom2: EasyEdit-compatible mom2 statistics (file name, npz format, sampling, collation,
multi-layer collection, rank split + merge, English corpus pin, AlphaEdit projector)."""
import os
import random
import tempfile
from types import SimpleNamespace

import numpy as np
import torch

from rt import mom2
from rt.tests._tiny import MODULE_TMP, tiny_model, tiny_tokenizer

TEXTS = [{"text": t} for t in (
    "Paris is the capital of France.", "The Nile flows north.", "Bach wrote fugues.",
    "Hydrogen is light.", "Kyoto has many temples and gardens.", "Iron rusts.",
    "The violin has four strings.", "Mount Kenya is in Africa.", "Chess is old.",
    "Lisbon faces the Atlantic ocean.", "Owls hunt at night.", "Copper conducts heat well.",
    "A haiku has three lines.", "Glaciers carve valleys slowly over time.", "Tea came from China.",
    "Mars is red.", "", "Venice is built on water, famously.", "Bees make honey.", "Oslo is cold.")]


def test_stats_path_matches_layer_stats_naming():
    got = mom2.stats_path("/w/data/stats_r1qwen32b", "/m/DeepSeek-R1-Distill-Qwen-32B",
                          "model.layers.12.mlp.down_proj", "wikipedia", "float32", 100000, npos=4096)
    assert got == ("/w/data/stats_r1qwen32b/DeepSeek-R1-Distill-Qwen-32B/wikipedia_stats/"
                   "model.layers.12.mlp.down_proj_float32_mom2_100000.npz")
    # HF id: only the last path component names the directory (layer_stats.py L162)
    assert mom2.stats_path("s", "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B", "L", npos=4096) == \
        "s/DeepSeek-R1-Distill-Qwen-7B/wikipedia_stats/L_float32_mom2_100000.npz"
    # upstream's literal "_t{batch_tokens}" suffix when batch_tokens < npos
    assert mom2.stats_path("s", "m", "L", npos=4096, batch_tokens=100).endswith(
        "L_float32_mom2_t{batch_tokens}_100000.npz")
    try:
        mom2.stats_path("s", "/m/model/", "L", npos=4096)
    except ValueError:
        return
    raise AssertionError("a trailing slash must be refused")


def test_npos_and_maxlen():
    qwen = SimpleNamespace(model_type="qwen2", max_position_embeddings=131072, sliding_window=4096)
    llama = SimpleNamespace(model_type="llama", max_position_embeddings=131072)
    gpt2 = SimpleNamespace(model_type="gpt2", n_positions=1024)
    assert mom2.npos_for(qwen) == 4096 and mom2.maxlen_for(qwen, 4096 * 3) == 4096
    assert mom2.npos_for(llama) == 131072 and mom2.npos_for(gpt2) == 1024
    assert mom2.maxlen_for(qwen, 1000) == 1000


def test_sample_groups_follow_fixed_random_subset_sampler():
    # runningstats.FixedRandomSubsetSampler(ds, seed=1, end=n): shuffled(range(len))[:n]
    ref = list(range(1000))
    random.Random(1).shuffle(ref)
    groups = mom2.sample_groups(1000, 250)
    assert [i for g in groups for i in g] == ref[:250]
    assert [len(g) for g in groups] == [100, 100, 50]
    assert [i for g in mom2.sample_groups(30, 100, group_size=7) for i in g] != list(range(30))
    assert len([i for g in mom2.sample_groups(30, 100, group_size=7) for i in g]) == 30
    assert [i for g in mom2.sample_groups(12, None, group_size=5) for i in g] == list(range(12))


def test_length_collation_mirror():
    items = [{"input_ids": torch.arange(n), "position_ids": torch.arange(n),
              "attention_mask": torch.ones(n, dtype=torch.long)} for n in (3, 7, 0, 5, 2)]
    batches = mom2.length_collation(12)(items)
    # sorted 7,5,3,2,0: [7] (7*2>12), [5,3] (5*3>12 closes), [2], zero-length stops the loop
    assert [b["input_ids"].shape for b in batches] == [(1, 7), (2, 5), (1, 2)]
    b = batches[1]
    assert b["attention_mask"].tolist() == [[1] * 5, [1, 1, 1, 0, 0]]
    assert b["input_ids"][1, 3:].tolist() == [0, 0]


def _reference_moments(model, tok, texts, idx, layer_names, maxlen):
    """sum over attended tokens of x x^T, one unpadded text at a time, full forward, float64."""
    feats = {n: [] for n in layer_names}
    handles = [model.get_submodule(n).register_forward_hook(
        lambda m, i, o, n=n: feats[n].append(i[0][0].double())) for n in layer_names]
    try:
        with torch.no_grad():
            for i in idx:
                ids = tok.encode(texts[i]["text"], truncation=True, max_length=maxlen)
                if ids:
                    model(input_ids=torch.tensor([ids]))
    finally:
        for h in handles:
            h.remove()
    out = {}
    for n, xs in feats.items():
        x = torch.cat(xs)
        out[n] = (x.T @ x, x.shape[0])
    return out


def _tiny_setup(layers=2):
    tok = tiny_tokenizer()
    return tiny_model(vocab=len(tok), layers=layers), tok


def test_collect_matches_per_text_forward():
    model, tok = _tiny_setup()
    names = [MODULE_TMP.format(1), MODULE_TMP.format(0)]
    maxlen = 24
    groups = mom2.sample_groups(len(TEXTS), 17, group_size=4)
    ds = mom2.TokenizedTexts(TEXTS, tok, maxlen)
    got = mom2.collect(model, ds, groups, names, batch_tokens=60, num_workers=0, pin_memory=False)
    ref = _reference_moments(model, tok, TEXTS, [i for g in groups for i in g], names, maxlen)
    for n in names:
        m, c = got[n]
        assert c == ref[n][1] and m.dtype == torch.float32
        assert torch.allclose(m.double(), ref[n][0], rtol=1e-5, atol=1e-6), n


def test_collect_stops_after_deepest_traced_layer():
    model, tok = _tiny_setup(layers=3)
    ran = []
    h = model.get_submodule(MODULE_TMP.format(2)).register_forward_hook(lambda *a: ran.append(1))
    try:
        ds = mom2.TokenizedTexts(TEXTS, tok, 16)
        mom2.collect(model, ds, mom2.sample_groups(len(TEXTS), 8, group_size=4),
                     [MODULE_TMP.format(0)], batch_tokens=40, num_workers=0, pin_memory=False)
    finally:
        h.remove()
    assert not ran, "layers after the deepest traced one must not run"


def test_rank_split_and_merge_equal_single_pass():
    model, tok = _tiny_setup()
    names = [MODULE_TMP.format(0), MODULE_TMP.format(1)]
    groups = mom2.sample_groups(len(TEXTS), 19, group_size=3)
    ds = mom2.TokenizedTexts(TEXTS, tok, 24)
    kw = dict(batch_tokens=50, num_workers=0, pin_memory=False)
    single = mom2.collect(model, ds, groups, names, **kw)
    meta = {"precision": "float32", "sample_size": 19, "model_base": "tiny"}
    with tempfile.TemporaryDirectory() as d:
        finals = {n: mom2.stats_path(d, "tiny", n, sample_size=19, npos=4096) for n in names}
        world = 3
        for r in range(world):
            mine = [g for g in range(len(groups)) if g % world == r]
            part = mom2.collect(model, ds, [groups[g] for g in mine], names, **kw)
            for n, (m, c) in part.items():
                mom2.save_part(mom2.part_path(finals[n], r, world), m, c, mine,
                               dict(meta, rank=r, count=c, layer_name=n))
        for n in names:
            try:
                mom2.merge_parts(finals[n], world, 19, len(groups))
            except ValueError as e:        # layer_name differs per file only through the meta
                raise AssertionError(e)
            cov, count = mom2.read_easyedit_stats(finals[n], 19)
            m, c = single[n]
            assert count == c
            assert torch.allclose(cov, (m / c).float(), rtol=1e-5, atol=1e-7)
        # a missing group is caught
        os.remove(mom2.part_path(finals[names[0]], 1, world))
        mine = [g for g in range(len(groups)) if g % world == 1][:-1]
        part = mom2.collect(model, ds, [groups[g] for g in mine], names[:1], **kw)
        m, c = part[names[0]]
        mom2.save_part(mom2.part_path(finals[names[0]], 1, world), m, c, mine,
                       dict(meta, rank=1, count=c, layer_name=names[0]))
        try:
            mom2.merge_parts(finals[names[0]], world, 19, len(groups))
        except ValueError as e:
            assert "missing or duplicated" in str(e)
            return
    raise AssertionError("an incomplete set of groups must be refused")


def test_merge_rejects_disagreeing_parts():
    with tempfile.TemporaryDirectory() as d:
        final = mom2.stats_path(d, "m", "L.1.x", sample_size=4, npos=8)
        for r, prec in enumerate(("float32", "float64")):
            mom2.save_part(mom2.part_path(final, r, 2), torch.eye(2), 3, [r],
                           {"precision": prec, "rank": r})
        try:
            mom2.merge_parts(final, 2, 4, 2)
        except ValueError as e:
            assert "disagree" in str(e)
            return
    raise AssertionError("parts with different settings must be refused")


def test_easyedit_npz_format():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "x.npz")
        mom2.save_easyedit_stats(path, np.full((3, 3), 6.0, dtype=np.float32), 3, 100000)
        z = np.load(path)
        assert sorted(z.files) == ["mom2.constructor", "mom2.count", "mom2.mom2", "sample_size"]
        assert str(z["mom2.constructor"]) == "easyeditor.util.runningstats.SecondMoment()"
        assert z["mom2.count"].dtype == np.int64 and int(z["mom2.count"]) == 3
        assert z["mom2.mom2"].dtype == np.float32 and z["sample_size"] == 100000
        # EasyEdit's load path: load_cached_state args check, pull_key_prefix, SecondMoment load
        dat = dict(np.load(path))
        assert not (dat["sample_size"] != 100000)
        state = {k[len("mom2."):]: v for k, v in dat.items() if k.startswith("mom2.")}
        moment = torch.from_numpy(state["mom2"]) / int(state["count"])
        cov, count = mom2.read_easyedit_stats(path, 100000)
        assert torch.equal(cov, moment.float()) and float(cov[0, 0]) == 2.0 and count == 3
        try:
            mom2.read_easyedit_stats(path, 50000)
        except ValueError:
            return
    raise AssertionError("a sample_size mismatch must be refused")


def test_compare_stats():
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.npz"), os.path.join(d, "b.npz")
        m = np.diag(np.arange(1.0, 5.0)).astype(np.float32) * 4
        mom2.save_easyedit_stats(a, m, 4, 10)
        mom2.save_easyedit_stats(b, m * 1.01, 4, 10)
        out = mom2.compare_stats(b, a)
        assert out["count_a"] == out["count_b"] == 4
        assert abs(out["rel_fro"] - 0.01) < 1e-6 and abs(out["max_rel_diag"] - 0.01) < 1e-6
        assert mom2.compare_stats(a, a)["rel_fro"] == 0.0


def test_english_corpus_pin():
    with tempfile.TemporaryDirectory() as d:
        en, ko = os.path.join(d, "20231101", "20231101.en"), os.path.join(d, "20231101", "20231101.ko")
        for sub in (en, ko):
            os.makedirs(sub)
            for i in range(2):
                open(os.path.join(sub, f"train-0000{i}-of-00002.parquet"), "w").close()
        files = mom2.english_wiki_files(en)
        assert len(files) == 2 and all("20231101.en" in f for f in files)
        for spec in (ko, os.path.join(d, "20231101", "*", "*.parquet")):
            try:
                mom2.english_wiki_files(spec)
            except ValueError as e:
                assert "English" in str(e) or ".en" in str(e)
                continue
            raise AssertionError(f"{spec} must be refused")
        assert mom2.english_wiki_files(os.path.join(d, "nothing-here")) is None
    assert mom2.assert_english([{"text": "Paris is the capital of France."}] * 3) > 0.99
    try:
        mom2.assert_english([{"text": "파리는 프랑스의 수도이다."}] * 3)
    except ValueError:
        return
    raise AssertionError("Korean text must fail the English check")


def test_null_space_projector():
    g = torch.Generator().manual_seed(0)
    Q, _ = torch.linalg.qr(torch.randn(6, 6, generator=g, dtype=torch.float64))
    eig = torch.tensor([3.0, 1.0, 0.5, 0.01, 0.001, 0.0], dtype=torch.float64)
    cov = (Q * eig) @ Q.T
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "s.npz")
        count = 10
        mom2.save_easyedit_stats(path, (cov * count).float().numpy(), count, 100)
        P, info = mom2.null_space_projector(path, 0.02, 100)
        want = Q[:, 3:] @ Q[:, 3:].T
        assert info["null_dim"] == 3 and info["dim"] == 6
        assert torch.allclose(P.double(), want, atol=1e-5)
        assert torch.allclose(P @ P, P, atol=1e-5) and torch.allclose(P, P.T, atol=1e-6)
        loc = os.path.join(d, "alphaedit", "P.pt")
        side = mom2.save_projector(loc, [P, P], [10, 11], {"threshold": 0.02, "sample_size": 100})
        loaded = torch.load(loc)
        assert loaded.shape == (2, 6, 6) and side["layers"] == [10, 11]
        assert torch.equal(loaded[1], P)
