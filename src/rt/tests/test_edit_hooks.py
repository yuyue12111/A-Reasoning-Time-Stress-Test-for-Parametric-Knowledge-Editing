"""EditBank must be indistinguishable from writing each row's edit into the weights."""
import os
import tempfile

import torch

from rt.edit_hooks import EditBank, factor_delta, load_delta, save_delta
from rt.tests._tiny import MODULE_TMP, merged_copy, rank1_edit, tiny_model

IDS = torch.tensor([[3, 17, 9, 41, 5, 22]])


def _logits(model, ids=IDS):
    with torch.no_grad():
        return model(input_ids=ids).logits


def test_factor_rank1_exact():
    g = torch.Generator().manual_seed(1)
    delta = torch.randn(40, 1, generator=g) @ torch.randn(1, 70, generator=g)
    A, B, fit = factor_delta(delta)
    assert fit["rank"] == 1 and fit["ok"]
    assert A.shape == (1, 70) and B.shape == (40, 1)
    assert torch.allclose(B @ A, delta, atol=1e-5)


def test_factor_reports_high_rank():
    delta = torch.randn(30, 30, generator=torch.Generator().manual_seed(2))
    _, _, fit = factor_delta(delta, max_rank=2)
    assert not fit["ok"] and fit["rank"] == 2 and fit["rel_err"] > 0.1


def test_factor_rejects_zero():
    try:
        factor_delta(torch.zeros(4, 5))
    except ValueError:
        return
    raise AssertionError("zero delta must raise")


def test_single_row_equals_merged():
    model = tiny_model()
    edit = rank1_edit(model, 1, seed=3)
    with EditBank(model, MODULE_TMP) as bank:
        bank.set_batch([edit])
        got = _logits(model)
    assert torch.allclose(got, _logits(merged_copy(model, edit)), atol=1e-5)


def test_rows_are_isolated():
    model = tiny_model()
    ea, eb = rank1_edit(model, 0, seed=4), rank1_edit(model, 1, seed=5)
    ids = IDS.repeat(3, 1)
    with EditBank(model, MODULE_TMP) as bank:
        bank.set_batch([ea, None, eb])
        got = _logits(model, ids)
    assert torch.allclose(got[0], _logits(merged_copy(model, ea))[0], atol=1e-5)
    assert torch.allclose(got[1], _logits(model)[0], atol=1e-5)
    assert torch.allclose(got[2], _logits(merged_copy(model, eb))[0], atol=1e-5)


def test_alpha_scales_the_edit():
    model = tiny_model()
    edit = rank1_edit(model, 1, seed=6)
    with EditBank(model, MODULE_TMP) as bank:
        bank.set_batch([edit, edit], alphas=[0.0, 2.0])
        got = _logits(model, IDS.repeat(2, 1))
    assert torch.allclose(got[0], _logits(model)[0], atol=1e-5)
    assert torch.allclose(got[1], _logits(merged_copy(model, edit, alpha=2.0))[0], atol=1e-5)


def test_position_mask():
    model = tiny_model()
    edit = rank1_edit(model, 0, seed=7)
    seq = IDS.shape[1]
    with EditBank(model, MODULE_TMP) as bank:
        bank.set_batch([edit, edit], pos_mask=torch.stack([torch.ones(seq), torch.zeros(seq)]))
        got = _logits(model, IDS.repeat(2, 1))
    assert torch.allclose(got[0], _logits(merged_copy(model, edit))[0], atol=1e-5)
    assert torch.allclose(got[1], _logits(model)[0], atol=1e-5)


def test_generate_matches_merged():
    model = tiny_model()
    edit = rank1_edit(model, 1, seed=8, scale=1.0)
    kw = dict(max_new_tokens=8, do_sample=False, pad_token_id=0)
    with EditBank(model, MODULE_TMP) as bank:
        bank.set_batch([edit, None])
        got = model.generate(input_ids=IDS.repeat(2, 1), **kw)
    ref_edit = merged_copy(model, edit).generate(input_ids=IDS, **kw)
    ref_base = model.generate(input_ids=IDS, **kw)
    assert torch.equal(got[0], ref_edit[0]) and torch.equal(got[1], ref_base[0])


def test_hooks_removed_on_exit():
    model = tiny_model()
    edit = rank1_edit(model, 1, seed=9)
    before = _logits(model)
    with EditBank(model, MODULE_TMP) as bank:
        bank.set_batch([edit])
        assert bank.n_hooks == 1
    assert bank.n_hooks == 0
    assert torch.equal(_logits(model), before)


def test_batch_size_mismatch_raises():
    model = tiny_model()
    with EditBank(model, MODULE_TMP) as bank:
        bank.set_batch([rank1_edit(model, 1, seed=10)])
        try:
            _logits(model, IDS.repeat(2, 1))
        except RuntimeError:
            return
    raise AssertionError("a batch larger than the bank must raise")


def test_save_load_roundtrip():
    model = tiny_model()
    (layer, (A, B)), = rank1_edit(model, 1, seed=11).items()
    rec = {"case_id": "cf_1", "model_tag": "tiny", "editor": "ROME", "target": "Paris",
           "target_tag": "cf", "module_tmp": MODULE_TMP, "layers": {layer: {"A": A, "B": B}}}
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "cf_1.pt")
        sha = save_delta(path, rec)
        edit, got = load_delta(path)
        assert got["sha"] == sha and torch.equal(edit[layer][0], A)
        got["target"] = "Rome"
        torch.save(got, path)
        try:
            load_delta(path)
        except ValueError:
            return
    raise AssertionError("tampered record must fail the hash check")


def test_tiny_tokenizer_round_trip():
    from rt.tests._tiny import tiny_tokenizer
    tok = tiny_tokenizer()
    text = "<｜User｜>Where is Oseberg?<｜Assistant｜><think>\nNorway…\n</think>\n\n"
    ids = tok(text, add_special_tokens=False)["input_ids"]
    assert tok.decode(ids) == text
    assert tok.convert_tokens_to_ids("</think>") in ids and len(tok) < 300
