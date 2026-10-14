"""Mechanism probes: activation normalization, position gating, span location, runner resume."""
import glob
import json
import os
import tempfile

import torch

import metrics
from rt import mech
from rt.edit_hooks import save_delta
from rt.tests._tiny import MODULE_TMP, merged_copy, rank1_edit, tiny_model, tiny_tokenizer

Q = "The Eiffel Tower is located in the city of"
SUBJ = "Eiffel Tower"
COT = ("Okay, the eiffel tower is famous. The Tower was built in Paris; Eiffel's firm "
       "designed it. Towers elsewhere differ. Hmm, the Eiffel Tower is in Paris, maybe Rome?")
ANSWER = "The Eiffel Tower is in Rome."


def _setup(layer=1, seed=3):
    tok = tiny_tokenizer()
    model = tiny_model(vocab=len(tok))
    return tok, model, rank1_edit(model, layer, seed=seed)


def _down_inputs(model, ids, layer):
    got = {}
    mod = model.get_submodule(MODULE_TMP.format(layer))
    h = mod.register_forward_pre_hook(lambda m, inp: got.__setitem__("x", inp[0][0].clone()))
    try:
        with torch.no_grad():
            model(input_ids=ids)
    finally:
        h.remove()
    return got["x"]


def test_activation_is_one_at_reference():
    tok, model, edit = _setup()
    res = mech.trace(model, tok, edit, MODULE_TMP, Q, SUBJ, COT, ANSWER, "Rome", "Paris", {})
    a = mech.decode_a(res)[1]
    seq = mech.compose(tok, Q, COT, ANSWER)
    ref = res["ref_tok"]
    assert a.shape == (res["n_tokens"], 1) and res["n_tokens"] == len(seq["ids"])
    assert abs(float(a[ref, 0]) - 1.0) < 1e-3
    q0 = seq["chars"]["q"][0]
    assert seq["offsets"][ref][1] == q0 + Q.index(SUBJ) + len(SUBJ)    # last subject token
    assert seq["text"][slice(*seq["offsets"][ref])] == res["ref_text"] == "r"


def test_activation_matches_manual_projection():
    tok, model, edit = _setup()
    res = mech.trace(model, tok, edit, MODULE_TMP, Q, SUBJ, COT, "", with_edit=False)
    ids = torch.tensor([mech.compose(tok, Q, COT)["ids"]])
    A = edit[1][0]
    z = (_down_inputs(model, ids, 1) @ A.T)[:, 0]
    want = (z / z[res["ref_tok"]]).numpy()
    got = mech.decode_a(res)[1][:, 0]
    assert abs(got - want).max() <= 2e-3 * max(1.0, abs(want).max())


def test_trace_edit_changes_only_downstream_layers():
    tok, model, _ = _setup()
    edit = {**rank1_edit(model, 0, seed=4, scale=2.0), **rank1_edit(model, 1, seed=5)}
    on = mech.decode_a(mech.trace(model, tok, edit, MODULE_TMP, Q, SUBJ, COT, "", with_edit=True))
    off = mech.decode_a(mech.trace(model, tok, edit, MODULE_TMP, Q, SUBJ, COT, "", with_edit=False))
    assert (on[0] == off[0]).all()                 # own-layer input is upstream of the edit
    assert not (on[1] == off[1]).all()             # layer 1 input sees the layer-0 edit


def test_question_activation_same_at_b0_and_b3():
    tok, model, edit = _setup()
    b3 = mech.trace(model, tok, edit, MODULE_TMP, Q, SUBJ, COT, ANSWER)
    b0 = mech.trace(model, tok, edit, MODULE_TMP, Q, SUBJ, "", ANSWER)
    seq = mech.compose(tok, Q, COT)
    q_last = mech.char_span_tokens(seq["offsets"], *seq["chars"]["q"])[1]
    a3, a0 = mech.decode_a(b3)[1], mech.decode_a(b0)[1]
    assert b3["ref_tok"] == b0["ref_tok"] and (a3[:q_last + 1] == a0[:q_last + 1]).all()


def test_segments_and_masks():
    tok = tiny_tokenizer()
    seq = mech.compose(tok, Q, COT, Q)
    (q0, q1), (c0, c1), (p0, p1) = seq["seg"]["q"], seq["seg"]["c"], seq["seg"]["p"]
    offs, text = seq["offsets"], seq["text"]
    assert q0 == 0 and q1 == c0 and c1 == p0 and p1 == len(seq["ids"])
    assert text.startswith(tok.bos_token) and seq["ids"][0] == tok.bos_token_id
    assert text[offs[c0][0]:].startswith(COT) and text[offs[c0 - 1][0]:offs[c0 - 1][1]] == "\n"
    assert tok.convert_tokens_to_ids("</think>") in seq["ids"][c0:c1]
    assert text[offs[p0][0]:] == Q
    b0 = mech.compose(tok, Q, "", Q)
    assert b0["text"] == tok.bos_token + mech.ZEROTHINK.format(q=Q) + Q
    nb = mech.compose(tok, Q, COT, Q, bos=False)
    assert nb["text"] == text[len(tok.bos_token):] and nb["ids"] == seq["ids"][1:]
    assert nb["seg"]["c"] == (c0 - 1, c1 - 1)
    saved = os.environ.pop("WHYAAAI_NO_BOS", None)
    try:
        os.environ["WHYAAAI_NO_BOS"] = "1"
        assert mech.compose(tok, Q, COT, Q)["ids"] == nb["ids"]         # _gen's env rule
    finally:
        os.environ.pop("WHYAAAI_NO_BOS")
        if saved is not None:
            os.environ["WHYAAAI_NO_BOS"] = saved
    m = mech.segment_masks(seq["seg"], len(seq["ids"]))
    assert m["none"].sum() == 0 and m["all"].sum() == len(seq["ids"])
    assert m["question_only"][:c0].all() and m["question_only"][c0:].sum() == 0
    assert (m["question_only"] + m["chain_and_answer_only"] == 1).all()
    assert (m["question_and_answer"] == m["question_only"] + m["answer_only"]).all()


def test_all_mask_is_merged_none_is_base():
    tok, model, edit = _setup(layer=0, seed=6)
    seq = mech.compose(tok, Q, COT, Q)
    ids = torch.tensor([seq["ids"]])
    vocab = list(range(len(tok)))
    got = mech.masked_logprobs(model, ids, edit, MODULE_TMP,
                               mech.segment_masks(seq["seg"], ids.shape[1]), vocab)
    with torch.no_grad():
        merged = torch.log_softmax(merged_copy(model, edit)(input_ids=ids).logits[0, -1], -1)
        base = torch.log_softmax(model(input_ids=ids).logits[0, -1], -1)
    assert torch.allclose(torch.tensor(got["all"]), merged, atol=1e-5)
    assert torch.allclose(torch.tensor(got["none"]), base, atol=1e-5)
    assert not torch.allclose(torch.tensor(got["question_only"]), base, atol=1e-5)


def test_subject_mentions_full_and_partial():
    tok = tiny_tokenizer()
    seq = mech.compose(tok, Q, COT)
    cs, ce = seq["chars"]["cot"]
    ms = mech.subject_mentions(seq["text"], SUBJ, cs, ce)
    assert [(m["kind"], m["text"]) for m in ms] == [
        ("full", "eiffel tower"), ("partial", "Tower"), ("partial", "Eiffel"),
        ("full", "Eiffel Tower")]                  # "Towers" is not a whole-word match
    for m in ms:
        last = mech.char_span_tokens(seq["offsets"], *m["span"])[1]
        assert seq["offsets"][last][1] == m["span"][1]
    assert mech.subject_words("Gare du Nord station") == ["Gare", "Nord", "station"]


def test_span_tokens_on_multibyte_characters():
    tok = tiny_tokenizer()
    text = "Ask Pelé now"
    enc = tok(text, add_special_tokens=False, return_offsets_mapping=True)
    offs = [tuple(o) for o in enc["offset_mapping"]]
    first, last = mech.char_span_tokens(offs, 4, 8)            # "Pelé"; é is two byte tokens
    assert text[offs[first][0]] == "P" and offs[last] == (7, 8) and offs[last - 1] == (7, 8)
    assert offs[last + 1][0] >= 8
    ms = mech.subject_mentions(text, "Edson Pelé")
    assert [(m["kind"], m["text"]) for m in ms] == [("partial", "Pelé")]


def test_value_mentions_follow_metrics_rules():
    subj = "Miami International Film Festival"
    chain = f"The {subj} started in 1984. It is held in Miami, not Paris."
    scrubbed = mech.scrub_subject(chain, subj)
    assert len(scrubbed) == len(chain)
    s, e = mech.first_value_span(scrubbed, "Miami", {})
    assert chain[s:e] == "Miami" and s == chain.index("in Miami") + 3
    assert s == metrics.first_mention(scrubbed, "Miami", {})
    for v in ("Miami", "Paris", "Festival"):
        assert (mech.first_value_span(scrubbed, v, {}) is not None) == \
            metrics.hit(metrics._without_subject(chain, subj), v, {})
    aliases = {"United States of America": ["USA", "United States"]}
    text = "Made in the USA, later sold across the United States."
    s, e = mech.first_value_span(text, "United States of America", aliases)
    assert text[s:e] == "United States"                     # 3-letter alias is dropped
    tok, model, edit = _setup()
    res = mech.trace(model, tok, edit, MODULE_TMP, Q, SUBJ, COT, ANSWER, "Rome", "Paris", {})
    old, new = res["values"]["chain"]["old"], res["values"]["chain"]["new"]
    assert old["text"] == "Paris" and new["text"] == "Rome" and old["span"][0] < new["span"][0]
    assert res["values"]["answer"]["new"]["text"] == "Rome" and res["values"]["answer"]["old"] is None
    sm = res["summary"]
    assert sm["chain_old"] and sm["n_before_old"] == 2 and sm["n_full"] == 2
    assert sm["a_last_before_old"] == [m for m in res["mentions"] if m["seg"] == "chain"][1]["a"]


def test_margin_flips_when_B_points_at_new_value():
    tok = tiny_tokenizer()
    model = tiny_model(vocab=len(tok))
    layer = model.config.num_hidden_layers - 1
    seq = mech.compose(tok, Q, COT, Q)
    ids = torch.tensor([seq["ids"]])
    with torch.no_grad():
        base = model(input_ids=ids).logits[0, -1]
    old_id, new_id = int(base.argmax()), int(base.argmin())
    x = _down_inputs(model, ids, layer)[-1]
    A = (x / x.dot(x))[None, :]                                # A·x_final = 1
    d = model.model.norm.weight * (model.lm_head.weight[new_id] - model.lm_head.weight[old_id])
    B = (1e3 * d / d.norm())[:, None]
    res = mech.gate(model, tok, {layer: (A, B)}, MODULE_TMP, Q, COT, Q, new_id, old_id)
    m = {k: v["margin"] for k, v in res["masks"].items()}
    assert m["none"] < 0 < m["all"]
    assert m["chain_and_answer_only"] > 0 and m["answer_only"] > 0
    assert abs(m["question_only"] - m["none"]) < 1e-5          # last layer: only the final position
    flipped = mech.gate(model, tok, {layer: (A, -B)}, MODULE_TMP, Q, COT, Q, new_id, old_id)
    assert flipped["masks"]["all"]["margin"] < 0


def test_gate_case_flags_shared_first_token():
    tok, model, edit = _setup()
    case = {"prompt": Q, "o_new": "Rome", "o_old": "Paris", "s": SUBJ}
    res = mech.gate_case(model, tok, edit, MODULE_TMP, Q, COT, case, masks=["none", "all"])
    assert res["same_first_token"]                             # byte-level: both start with " "
    assert res["chain"]["masks"]["all"]["margin"] == 0.0
    assert res["b0"]["n_tokens"] < res["chain"]["n_tokens"]
    c0, c1 = res["b0"]["seg"]["c"]
    assert c1 - c0 == len(tok(mech.TAIL, add_special_tokens=False)["input_ids"])  # closing tail


def _write_fixture(d, model):
    cases = [
        {"case_id": "cf_1", "s": SUBJ, "prompt": Q, "o_old": "Paris", "o_new": "Rome"},
        {"case_id": "cf_2", "s": "Danielle Darrieux", "o_old": "French", "o_new": "English",
         "prompt": "The mother tongue of Danielle Darrieux is"},
        {"case_id": "cf_3", "s": "Oseberg ship", "o_old": "Norway", "o_new": "Chile",
         "prompt": "The Oseberg ship is located in"},
        {"case_id": "cf_4", "s": "Nobody Here", "o_old": "Oslo", "o_new": "Lima",
         "prompt": "The capital of Norway is"},
    ]
    with open(os.path.join(d, "cases.jsonl"), "w") as f:
        for c in cases:
            f.write(json.dumps(c) + "\n")
    rows = [{"_meta": True}]
    b0 = {"cf_1": "It is in Rome.", "cf_2": "English.", "cf_3": "Chile.", "cf_4": "Lima."}
    b3 = {"cf_1": ("The Eiffel Tower... the tower is in Paris.", "It is in Paris."),
          "cf_2": ("Darrieux spoke English, not French? English.", "English."),
          "cf_3": ("The ship is in Chile.", "Chile."),
          "cf_4": ("Norway's capital is Lima.", "Lima.")}
    for c in cases:
        cid = c["case_id"]
        rows.append({"case_id": cid, "budget": "B0", "probe": "efficacy", "decode": "greedy",
                     "q": c["prompt"], "cot": "", "answer": b0[cid]})
        rows.append({"case_id": cid, "budget": "B3", "probe": "efficacy", "decode": "greedy",
                     "q": c["prompt"], "cot": b3[cid][0], "answer": b3[cid][1]})
        rows.append({"case_id": cid, "budget": "B3", "probe": "locality", "decode": "greedy",
                     "q": "x", "cot": "", "answer": ""})
    with open(os.path.join(d, "rows_r0of1.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    os.makedirs(os.path.join(d, "deltas"))
    for i, cid in enumerate(("cf_1", "cf_2", "cf_4")):             # cf_3 has no delta
        (layer, (A, B)), = rank1_edit(model, 1, seed=20 + i).items()
        target = next(c["o_new"] for c in cases if c["case_id"] == cid)
        save_delta(os.path.join(d, "deltas", f"{cid}.pt"),
                   {"case_id": cid, "model_tag": "tiny", "editor": "ROME", "target": target,
                    "target_tag": "new", "module_tmp": MODULE_TMP,
                    "layers": {layer: {"A": A, "B": B}}})
    with open(os.path.join(d, "aliases.json"), "w") as f:
        json.dump({}, f)
    return {"model": "tiny", "model_tag": "tiny", "target_tag": "new",
            "deltas": os.path.join(d, "deltas"), "rows": os.path.join(d, "rows_*.jsonl"),
            "cases": [os.path.join(d, "cases.jsonl")], "aliases": os.path.join(d, "aliases.json"),
            "out": os.path.join(d, "out", "mech_r{rank}of{world}.jsonl"),
            "masks": ["none", "all", "question_only", "chain_and_answer_only"]}


def _read(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def test_runner_resume_labels_and_errors():
    tok, model, _ = _setup()
    with tempfile.TemporaryDirectory() as d:
        cfg = _write_fixture(d, model)
        out = cfg["out"].format(rank=0, world=1)
        c1 = mech.run(cfg, model, tok, limit=1, log=lambda *a: None)
        assert c1["written"] == 2 and c1["items"] == 1
        c2 = mech.run(cfg, model, tok, log=lambda *a: None)
        assert c2["skipped_done"] == 1 and c2["missing_delta"] == 1
        assert c2["written"] == 3 and c2["errors"] == 1           # cf_4 trace: subject not in q
        rows = _read(out)
        assert sum(bool(r.get("_meta")) for r in rows) == 1 and rows[0]["signature"]["bos"]
        body = [r for r in rows if not r.get("_meta")]
        keys = [(r["case_id"], r["budget"], r["kind"]) for r in body]
        assert len(keys) == len(set(keys)) == 6
        err = [r for r in body if "error" in r]
        assert [(r["case_id"], r["kind"]) for r in err] == [("cf_4", "trace")]
        lab = {r["case_id"]: r["labels"] for r in body if r["kind"] == "gate"}
        assert lab["cf_1"]["group"] == "reverted" and lab["cf_1"]["clr"]
        assert lab["cf_2"]["group"] == "held" and lab["cf_2"]["clr"]
        c3 = mech.run(cfg, model, tok, log=lambda *a: None)
        assert c3["written"] == 0 and len(_read(out)) == len(rows)
        c4 = mech.run({**cfg, "retry_errors": True}, model, tok, log=lambda *a: None)
        assert c4["errors"] == 1 and len(_read(out)) == len(rows) + 1
        try:
            mech.run({**cfg, "alpha": 2.0, "budgets": ["B0", "B3"]}, model, tok,
                     log=lambda *a: None)
        except ValueError as exc:
            assert "signature" in str(exc)
        else:
            raise AssertionError("a changed config must not append to an old output")
        assert mech.run({**cfg, "bos": False, "out": out + ".nobos"}, model, tok,
                        limit=1, log=lambda *a: None)["written"] == 2
        assert not _read(out + ".nobos")[0]["signature"]["bos"]
        c5 = mech.run({**cfg, "out": out + ".wrong", "expect_target": "o_old"}, model, tok,
                      limit=1, log=lambda *a: None)
        assert c5["errors"] == 2 and c5["written"] == 0              # delta was built for o_new
        s = mech.summarize(out)
        low = s["readout_i"]["low_last_mention_before_old"]
        assert low["reverted"]["n"] == 1 and low["held"]["n"] == 1
        assert s["readout_ii"]["reverted"]["n"] == 0             # tied first tokens are excluded


def test_runner_shards_partition_items():
    tok, model, _ = _setup()
    with tempfile.TemporaryDirectory() as d:
        cfg = {**_write_fixture(d, model), "probes": ["gate"], "masks": ["none", "all"]}
        for r in range(2):
            mech.run(cfg, model, tok, rank=r, world=2, log=lambda *a: None)
        got = [row["case_id"] for p in sorted(glob.glob(os.path.join(d, "out", "*.jsonl")))
               for row in _read(p) if not row.get("_meta")]
        assert sorted(got) == ["cf_1", "cf_2", "cf_4"]


def test_summarize_readouts():
    def gate_row(cid, group, chain, b0):
        mk = lambda ms: {"masks": {k: {"margin": v} for k, v in ms.items()}}
        return {"case_id": cid, "budget": "B3", "kind": "gate", "same_first_token": False,
                "labels": {"group": group, "name_leak": False}, "chain": mk(chain), "b0": mk(b0)}

    def trace_row(cid, group, a_last, n_before, leak=False):
        return {"case_id": cid, "budget": "B3", "kind": "trace",
                "labels": {"group": group, "name_leak": leak},
                "summary": {"chain_old": True, "n_before_old": n_before, "thr": 0.5,
                            "a_last_before_old": a_last, "frac_high": 0.5, "max_a": 1.0}}
    rows = [{"_meta": True},
            gate_row("c1", "reverted", {"none": -2.0, "all": 1.0, "question_only": -1.0},
                     {"none": -2.0, "all": 3.0}),
            gate_row("c2", "reverted", {"none": -1.0, "all": 0.0, "question_only": -1.0},
                     {"none": -1.0, "all": 2.0}),
            trace_row("c1", "reverted", 0.1, 2), trace_row("c2", "reverted", 0.9, 1),
            trace_row("c3", "held", 0.9, 1), trace_row("c4", "reverted", None, 0),
            trace_row("c5", "reverted", 0.1, 1, leak=True)]
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "m.jsonl")
        with open(path, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        s = mech.summarize(path, n_boot=200)
    r2 = s["readout_ii"]["reverted"]
    assert r2["n"] == 2 and r2["effect_chain"]["all"]["est"] == 2.0
    assert r2["effect_chain"]["question_only"]["est"] == 0.5
    assert r2["all_minus_question_only"]["est"] == 1.5
    assert r2["b0_all_minus_chain_all"]["est"] == 2.0          # (5-3 + 3-1) / 2
    assert r2["b0_q_minus_chain_q"] is None                    # no B0 question_only in fixture
    r1 = s["readout_i"]
    assert r1["low_last_mention_before_old"]["reverted"]["est"] == 0.5    # c5 excluded (leak)
    assert r1["diff_reverted_minus_held"]["est"] == 0.5
    assert r1["old_without_prior_mention"]["reverted"]["est"] == 1 / 3
