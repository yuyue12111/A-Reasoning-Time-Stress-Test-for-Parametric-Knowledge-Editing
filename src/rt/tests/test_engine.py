"""engine.py must reproduce the legacy generator, keep rows isolated, and confine the chain bias."""
import os

import torch

import think_budget
from rt.edit_hooks import EditBank
from rt.engine import (IC_FOLLOWUP, IM_END, IM_START, Engine, Request, RowBias, _single_id,
                       get_template)
from rt.tests._tiny import MODULE_TMP, merged_copy, rank1_edit, tiny_model, tiny_tokenizer

QS = ["Where is Oseberg?", "The capital of Norway is", "Danielle Darrieux's mother tongue is",
      "Toko Yasuda plays the", "Apple A5 was created by", "Q"]
GEN = ("cot", "answer", "chain_end", "n_chain_tokens", "n_answer_tokens")


def _setup(seed=0, tok=None):
    tok = tok or tiny_tokenizer()
    model = tiny_model(seed=seed, vocab=len(tok))
    model.generation_config.eos_token_id = tok.eos_token_id    # as in the R1 checkpoints
    return model, tok


def _chatml_tokenizer():
    tok = tiny_tokenizer()
    tok.add_tokens([IM_START, IM_END], special_tokens=True)
    return tok


def _fields(o):
    return {k: o[k] for k in GEN}


class _Recorder:
    """Replaces model.generate: records each prompt and answers with one fixed stop token."""

    def __init__(self, model, stop_for):
        self.model, self.stop_for, self.seen, self.kw = model, stop_for, [], []

    def __enter__(self):
        def fake(input_ids=None, attention_mask=None, **kw):
            n = len(self.seen)
            for row, mask in zip(input_ids.tolist(), attention_mask.tolist()):
                self.seen.append([t for t, m in zip(row, mask) if m])
            self.kw.append(kw)
            stop = torch.full((input_ids.shape[0], 1), self.stop_for(n), dtype=torch.long)
            return torch.cat([input_ids, stop], dim=1)
        self.model.generate = fake
        return self

    def __exit__(self, *exc):
        del self.model.generate
        return False


def _legacy_prompts(model, tok, q, budget):
    think_end = tok.convert_tokens_to_ids("</think>")
    chain = budget in ("B1", "B2", "B3")
    with _Recorder(model, lambda n: think_end if chain and n == 0 else tok.eos_token_id) as rec:
        think_budget.generate_with_budget(model, tok, q, budget)
    return rec.seen


def _engine_prompts(model, tok, q, budget, template="r1"):
    eng = Engine(model, tok, template=template)
    close = eng.template.chain_close[0]
    chain = budget in ("B1", "B2", "B3")
    with _Recorder(model, lambda n: close if chain and n == 0 else eng.template.answer_stop[0]) as rec:
        out = eng.run([Request({}, q, budget)])
    return rec.seen, out[0], rec.kw


def test_r1_prompt_strings_are_legacy_constants():
    model, tok = _setup()
    t = get_template("r1", tok, model)
    q = QS[0]
    assert t.b0(q) == think_budget.ZEROTHINK.format(q=q) == t.answer(q, "")
    assert t.b0p(q) == think_budget.LESSTHINK_CANNED.format(q=q) == t.answer(q, think_budget.LESSTHINK_COT)
    assert t.chain(q) == think_budget.TPL.format(q=q)


def test_r1_prompt_ids_equal_legacy_with_and_without_bos():
    model, tok = _setup()
    old = os.environ.pop("WHYAAAI_NO_BOS", None)
    try:
        for no_bos in (None, "1"):
            if no_bos:
                os.environ["WHYAAAI_NO_BOS"] = no_bos
            for budget in ("B0", "B0P", "B1", "B3"):
                legacy = _legacy_prompts(model, tok, QS[1], budget)
                ours, out, _ = _engine_prompts(model, tok, QS[1], budget)
                assert ours == legacy, (no_bos, budget)
                assert (ours[0][0] == tok.bos_token_id) == (not no_bos)
                assert out["template"] == "r1"
            os.environ.pop("WHYAAAI_NO_BOS", None)
    finally:
        if old is not None:
            os.environ["WHYAAAI_NO_BOS"] = old


def test_greedy_generation_equals_legacy():
    model, tok = _setup()
    q = QS[0]
    for budget in ("B0", "B0P"):
        cot, ans, _ = think_budget.generate_with_budget(model, tok, q, budget, answer_cap=24)
        o = Engine(model, tok, answer_cap=24).run([Request({}, q, budget)])[0]
        assert (o["cot"], o["answer"]) == (cot, ans)
    think_end, eos = tok.convert_tokens_to_ids("</think>"), tok.eos_token_id
    old = dict(think_budget.CAP)
    think_budget.CAP["B1"] = 64                 # legacy never generates fewer than 64 chain tokens
    try:
        eng = Engine(model, tok, answer_cap=24, caps={"B1": 64})
        o = None
        for boost in (0, 2, 4, 6, 8, 10, 12, 14, 16, 20, 25, 30):
            bias = {think_end: float(boost), eos: -1e9}     # EOS off: legacy loops on a chain EOS
            o = eng.run([Request({}, q, "B1", chain_bias=bias)])[0]
            if o["chain_end"] == "think_end" and o["n_chain_tokens"] >= 3:
                break
        assert o["chain_end"] == "think_end" and o["n_chain_tokens"] >= 3
        cot, ans, _ = think_budget.generate_with_budget(
            model, tok, q, "B1", answer_cap=24, suppress={"processor": RowBias([bias]), "scope": "think"})
        assert (o["cot"], o["answer"]) == (cot, ans)
        bias = {think_end: -1e9, eos: -1e9, tok.bos_token_id: -1e9, tok.pad_token_id: -1e9}
        o = eng.run([Request({}, q, "B1", chain_bias=bias)])[0]
        assert o["chain_end"] == "cap" and o["n_chain_tokens"] == 64
        cot, ans, _ = think_budget.generate_with_budget(
            model, tok, q, "B1", answer_cap=24, suppress={"processor": RowBias([bias]), "scope": "think"})
        assert (o["cot"], o["answer"]) == (cot, ans)
    finally:
        think_budget.CAP.clear()
        think_budget.CAP.update(old)


def test_edits_equal_merged_weights():
    model, tok = _setup()
    edit = rank1_edit(model, 1, seed=3, scale=1.0)
    merged = merged_copy(model, edit)
    kw = dict(answer_cap=24, caps={"B3": 32})
    specs = [(QS[0], "B0", None), (QS[1], "B3", None), (QS[2], "GIVEN", "Norway, surely.")]
    got = Engine(model, tok, bank=EditBank(model, MODULE_TMP), **kw).run(
        [Request({"i": i}, q, b, edit=edit, given_chain=g) for i, (q, b, g) in enumerate(specs)]
        + [Request({"i": 9}, QS[1], "B3")])
    ref = Engine(merged, tok, **kw).run([Request({}, q, b, given_chain=g) for q, b, g in specs])
    base = Engine(model, tok, **kw).run([Request({}, q, b, given_chain=g) for q, b, g in specs])
    for g, r in zip(got, ref):
        assert _fields(g) == _fields(r)
    assert any(_fields(g) != _fields(b) for g, b in zip(got, base)), "edit must change something"
    assert _fields(got[3]) == _fields(base[1]), "an unedited row in an edited batch must stay base"


def test_alpha_matches_scaled_merge():
    model, tok = _setup()
    edit = rank1_edit(model, 0, seed=4, scale=1.0)
    got = Engine(model, tok, bank=EditBank(model, MODULE_TMP), answer_cap=24).run(
        [Request({}, QS[3], "B0", edit=edit, alpha=2.0), Request({}, QS[3], "B0", edit=edit, alpha=0.0)])
    ref = Engine(merged_copy(model, edit, alpha=2.0), tok, answer_cap=24).run([Request({}, QS[3], "B0")])
    base = Engine(model, tok, answer_cap=24).run([Request({}, QS[3], "B0")])
    assert _fields(got[0]) == _fields(ref[0]) and _fields(got[1]) == _fields(base[0])


def _mixed_requests(model):
    ea, eb = rank1_edit(model, 0, seed=5, scale=1.0), rank1_edit(model, 1, seed=6, scale=1.0)
    reqs = []
    for i, q in enumerate(QS):
        for j, b in enumerate(("B0", "B1", "GIVEN", "B0P")):
            edit = (ea, None, eb)[(i + j) % 3]
            reqs.append(Request({"i": len(reqs)}, q, b, edit=edit, alpha=1.0 + 0.5 * (i % 2),
                                given_chain="Let me recall. " * (i + 1)))
    return reqs


def test_batched_equals_one_at_a_time():
    model, tok = _setup()
    kw = dict(answer_cap=20, caps={"B1": 24})
    bank = EditBank(model, MODULE_TMP)
    batched = Engine(model, tok, bank=bank, batch_size=8, **kw)
    got = batched.run(_mixed_requests(model))
    single = Engine(model, tok, bank=bank, batch_size=1, **kw).run(_mixed_requests(model))
    assert [_fields(o) for o in got] == [_fields(o) for o in single]
    assert max(b["n"] for b in batched.batch_log) > 1


def test_row_order_and_batch_ids():
    model, tok = _setup()
    reqs = _mixed_requests(model)
    eng = Engine(model, tok, bank=EditBank(model, MODULE_TMP), batch_size=5, answer_cap=8, caps={"B1": 8})
    out = eng.run(reqs)
    assert [o["i"] for o in out] == list(range(len(reqs)))
    assert all(o["q"] == r.q and o["budget"] == r.budget for o, r in zip(out, reqs))
    ids = {b["batch_id"] for b in eng.batch_log}
    assert all(o["batch_id"] in ids for o in out)
    assert all((o["chain_batch_id"] is None) == (o["budget"] != "B1") for o in out)


def test_max_batch_tokens_splits_batches():
    model, tok = _setup()
    eng = Engine(model, tok, batch_size=64, max_batch_tokens=120, answer_cap=8)
    eng.run([Request({}, q, "B0") for q in QS])
    assert all(b["n"] * (b["max_prompt"] + b["max_new"]) <= 120 or b["n"] == 1 for b in eng.batch_log)
    assert len(eng.batch_log) > 1


def test_chain_end_detection():
    model, tok = _setup()
    think_end, eos = tok.convert_tokens_to_ids("</think>"), tok.eos_token_id
    out = Engine(model, tok, answer_cap=8, caps={"B2": 12}).run([
        Request({}, QS[0], "B2", chain_bias={think_end: 1e9}),
        Request({}, QS[0], "B2", chain_bias={eos: 1e9}),
        Request({}, QS[0], "B2", chain_bias={think_end: -1e9, eos: -1e9})])
    assert [o["chain_end"] for o in out] == ["think_end", "eos", "cap"]
    assert [o["n_chain_tokens"] for o in out] == [0, 0, 12]
    assert out[0]["cot"] == out[1]["cot"] == ""
    assert all(o["bias_steps"] and o["bias_steps"] >= 1 for o in out)


def test_spelled_out_think_end_cuts_the_chain():
    model, tok = _setup()
    eng = Engine(model, tok)
    pieces = tok("ab</", add_special_tokens=False)["input_ids"] + tok("think>cd", add_special_tokens=False)["input_ids"]
    assert tok.convert_tokens_to_ids("</think>") not in pieces
    cot, end, n = eng._chain_text(pieces, "cap")
    assert (cot, end, n) == ("ab", "think_end", 10)


def _ascii_ids(tok, text):
    return {t for t in tok(text, add_special_tokens=False)["input_ids"]
            if len(tok.decode([t])) == 1 and tok.decode([t]).isalnum() and tok.decode([t]).isascii()}


def test_chain_bias_only_touches_its_row_and_its_chain():
    model, tok = _setup()
    think_end, eos = tok.convert_tokens_to_ids("</think>"), tok.eos_token_id
    keep_open = {think_end: -1e9, eos: -1e9}
    kw = dict(answer_cap=48, caps={"B1": 40})
    free = Engine(model, tok, **kw).run([Request({}, QS[1], "B1", chain_bias=keep_open)])[0]
    in_chain = _ascii_ids(tok, free["cot"])
    assert in_chain, "the unbiased chain must contain an ASCII letter to ban"
    ban = sorted(in_chain)[0]
    eng = Engine(model, tok, **kw)
    calls = []
    orig = model.generate

    def spy(*a, **k):
        calls.append((k["max_new_tokens"], "logits_processor" in k))
        return orig(*a, **k)
    model.generate = spy
    try:
        both = eng.run([Request({}, QS[1], "B1", chain_bias=keep_open),
                        Request({}, QS[1], "B1", chain_bias={**keep_open, ban: -1e9})])
    finally:
        del model.generate
    assert _fields(both[0]) == _fields(free)
    assert ban in _ascii_ids(tok, both[0]["cot"]) and ban not in _ascii_ids(tok, both[1]["cot"])
    assert (40, True) in calls and all(not proc for n, proc in calls if n == 48)
    only_answer = _ascii_ids(tok, free["answer"]) - in_chain
    if only_answer:                             # a ban the chain never needed leaves the answer alone
        tok_a = sorted(only_answer)[0]
        o = Engine(model, tok, **kw).run([Request({}, QS[1], "B1", chain_bias={**keep_open, tok_a: -1e9})])[0]
        assert _fields(o) == _fields(free) and tok_a in _ascii_ids(tok, o["answer"])


def test_bias_ignored_without_chain_phase():
    model, tok = _setup()
    ban = {t: -1e9 for t in range(0, 256)}
    for b, g in (("B0", None), ("B0P", None), ("GIVEN", "given text")):
        a = Engine(model, tok, answer_cap=16).run([Request({}, QS[2], b, given_chain=g)])[0]
        c = Engine(model, tok, answer_cap=16).run([Request({}, QS[2], b, given_chain=g, chain_bias=ban)])[0]
        assert _fields(a) == _fields(c) and c["bias_steps"] is None


def test_given_chain_fields():
    model, tok = _setup()
    g = "Oseberg is a ship burial in Norway."
    o = Engine(model, tok, answer_cap=8).run([Request({"k": 1}, QS[0], "GIVEN", given_chain=g)])[0]
    assert o["cot"] == g and o["chain_end"] == "given" and o["n_chain_tokens"] == len(g.encode())
    assert o["k"] == 1


def test_user_prefix_goes_inside_the_user_turn():
    model, tok = _setup()
    with _Recorder(model, lambda n: tok.eos_token_id) as rec:
        o = Engine(model, tok).run([Request({}, QS[0], "B0", user_prefix="Fact: X.\n")])[0]
    t = get_template("r1", tok, model)
    assert rec.seen[0] == t.encode(t.b0("Fact: X.\n" + QS[0]))
    assert o["q"] == QS[0] and o["user_prefix"] == "Fact: X.\n"


def test_sampling_is_seeded_per_batch():
    model, tok = _setup()
    reqs = lambda s: [Request({}, q, "B1", decode="sample", seed=s, temperature=1.0) for q in QS[:3]]
    kw = dict(answer_cap=12, caps={"B1": 12})
    a = Engine(model, tok, **kw).run(reqs(7))
    b = Engine(model, tok, **kw).run(reqs(7))
    c = Engine(model, tok, **kw).run(reqs(8))
    assert [_fields(x) for x in a] == [_fields(x) for x in b]
    assert [_fields(x) for x in a] != [_fields(x) for x in c]
    assert all(x["decode"] == "sample" and x["seed"] == 7 and x["temperature"] == 1.0 for x in a)
    try:
        Request({}, "q", "B0", decode="sample").check()
    except ValueError:
        return
    raise AssertionError("sampling without a seed must raise")


def test_greedy_rows_record_no_seed():
    model, tok = _setup()
    o = Engine(model, tok, answer_cap=4).run([Request({}, "q", "B0", seed=3, temperature=0.9)])[0]
    assert o["decode"] == "greedy" and o["seed"] is None and o["temperature"] is None


def test_edits_without_bank_raise():
    model, tok = _setup()
    try:
        Engine(model, tok, answer_cap=4).run([Request({}, "q", "B0", edit=rank1_edit(model, 0, seed=1))])
    except ValueError:
        return
    raise AssertionError("an edit without an EditBank must raise")


def test_bank_hooks_removed_after_run():
    model, tok = _setup()
    bank = EditBank(model, MODULE_TMP)
    Engine(model, tok, bank=bank, answer_cap=4).run([Request({}, "q", "B0", edit=rank1_edit(model, 0, seed=1))])
    assert bank.n_hooks == 0


def test_full_width_guard():
    tok = tiny_tokenizer()
    assert _single_id(tok, "<｜User｜>") == tok.convert_tokens_to_ids("<｜User｜>")
    try:
        _single_id(tok, "<|User|>")             # half-width bars: not a token
    except ValueError:
        return
    raise AssertionError("a multi-token marker must raise")


def test_chatml_templates_need_their_tokens():
    tok = tiny_tokenizer()
    for name in ("qwq", "instruct_cot"):
        try:
            get_template(name, tok)
        except ValueError:
            continue
        raise AssertionError(f"{name} must reject a tokenizer without <|im_start|>/<|im_end|>")
    try:
        get_template("r1", tok, system="x")
    except ValueError:
        return
    raise AssertionError("r1 has no system turn")


def test_qwq_template():
    tok = _chatml_tokenizer()
    model, _ = _setup(tok=tok)
    t = get_template("qwq", tok, model)
    q = QS[0]
    chain = "<|im_start|>user\nWhere is Oseberg?<|im_end|>\n<|im_start|>assistant\n<think>\n"
    assert t.chain(q) == chain
    assert t.b0(q) == chain + "\n</think>\n\n"
    assert t.answer(q, "abc") == chain + "abc\n</think>\n\n"
    assert t.b0p(q) == chain + think_budget.LESSTHINK_COT + "\n</think>\n\n"
    assert t.encode(t.b0(q))[0] == tok.convert_tokens_to_ids(IM_START)    # no BOS
    im_end, think_end = tok.convert_tokens_to_ids(IM_END), tok.convert_tokens_to_ids("</think>")
    assert t.chain_close == [think_end]
    assert t.chain_eos[0] == im_end and tok.eos_token_id in t.chain_eos
    assert t.answer_stop[0] == im_end and think_end not in t.answer_stop
    seen, out, kw = _engine_prompts(model, tok, q, "B3", template="qwq")
    assert seen == [t.encode(chain), t.encode(chain + "\n</think>\n\n")]
    assert set(kw[0]["eos_token_id"]) == {think_end, im_end, tok.eos_token_id}
    assert out["chain_end"] == "think_end" and out["template"] == "qwq"
    ends = Engine(model, tok, template="qwq", answer_cap=6, caps={"B1": 6}).run([
        Request({}, q, "B1", chain_bias={think_end: 1e9}),
        Request({}, q, "B1", chain_bias={im_end: 1e9}),
        Request({}, q, "B1", chain_bias={think_end: -1e9, im_end: -1e9, tok.eos_token_id: -1e9})])
    assert [o["chain_end"] for o in ends] == ["think_end", "eos", "cap"]


def test_instruct_cot_template():
    tok = _chatml_tokenizer()
    model, _ = _setup(tok=tok)
    t = get_template("instruct_cot", tok, model, system="You are helpful.")
    q = QS[1]
    sys = "<|im_start|>system\nYou are helpful.<|im_end|>\n"
    b0 = sys + "<|im_start|>user\nThe capital of Norway is\nAnswer with the completion only.<|im_end|>\n<|im_start|>assistant\n"
    chain = (sys + "<|im_start|>user\nThe capital of Norway is\nThink step by step about this before answering. "
             "Do not state a final answer yet.<|im_end|>\n<|im_start|>assistant\n")
    follow = "<|im_end|>\n<|im_start|>user\nNow give the final answer only.<|im_end|>\n<|im_start|>assistant\n"
    assert t.b0(q) == b0 and t.chain(q) == chain and IC_FOLLOWUP == follow
    assert t.answer(q, "Oslo is big.") == chain + "Oslo is big." + follow
    im_end = tok.convert_tokens_to_ids(IM_END)
    assert t.chain_close == [im_end] and im_end not in t.chain_eos
    eng = Engine(model, tok, template=t, answer_cap=6, caps={"B3": 6})
    with _Recorder(model, lambda n: im_end) as rec:
        o = eng.run([Request({}, q, "B3"), Request({}, q, "B0")])
    assert t.encode(chain) in rec.seen and t.encode(b0) in rec.seen and t.encode(chain + follow) in rec.seen
    assert o[0]["chain_end"] == "think_end" and o[0]["cot"] == ""
    ends = Engine(model, tok, template=t, answer_cap=6, caps={"B1": 6}).run([
        Request({}, q, "B1", chain_bias={im_end: 1e9}),
        Request({}, q, "B1", chain_bias={tok.eos_token_id: 1e9}),
        Request({}, q, "B1", chain_bias={im_end: -1e9, tok.eos_token_id: -1e9})])
    assert [e["chain_end"] for e in ends] == ["think_end", "eos", "cap"]
