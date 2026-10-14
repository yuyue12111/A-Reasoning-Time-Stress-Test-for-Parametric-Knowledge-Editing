"""The semantic judge: blind prompts, order randomization, letter extraction, resume, aggregation."""
import json
import math
import os
import re
import tempfile

import torch

import metrics
from rt import judge
from rt.tests._tiny import tiny_model, tiny_tokenizer

TEMPLATE = ("{{ bos_token }}{% for m in messages %}"
            "{% if m['role'] == 'system' %}{{ m['content'] }}\n\n"
            "{% elif m['role'] == 'user' %}<｜User｜>{{ m['content'] }}"
            "{% else %}<｜Assistant｜>{{ m['content'] }}{% endif %}{% endfor %}"
            "{% if add_generation_prompt %}<｜Assistant｜>{% endif %}")
TEMPLATE_NO_SYSTEM = TEMPLATE.replace(
    "{{ m['content'] }}\n\n", "{{ raise_exception('System role not supported') }}", 1)

CASES = {
    "cf_1": {"s": "Danielle Darrieux", "o_old": "French", "o_new": "English"},
    "cf_2": {"s": "Montreal Convention", "o_old": "Montreal", "o_new": "Frankfurt"},
    "cf_3": {"s": "Gregor Mendel", "o_old": "genetics", "o_new": "physics"},
    "cf_4": {"s": "Toko Yasuda", "o_old": "guitar", "o_new": "piano"},
}
ALIASES = {}


def chat_tokenizer(template=TEMPLATE):
    tok = tiny_tokenizer()
    tok.chat_template = template
    return tok


def row(cid, budget, answer, probe="efficacy", **kw):
    q = {"efficacy": "The thing of {} is", "base": "The thing of {} is",
         "para0": "Some prefix. {} is linked to", "locality": "A neighbour is"}[probe]
    return {"case_id": cid, "editor": "ROME", "model_tag": "m", "budget": budget, "probe": probe,
            "decode": "greedy", "q": q.format(CASES[cid]["s"]), "cot": "", "answer": answer,
            "src": "f.jsonl", "line": kw.pop("line", 0), **kw}


class OracleScorer:
    """Stub scorer: reads its own prompt back and prefers the letter the response asserts."""

    def __init__(self):
        self.calls = 0
        self.prompts = 0

    def encode(self, user_text):
        return list(user_text.encode())

    def score(self, id_lists):
        self.calls += 1
        self.prompts += len(id_lists)
        out = []
        for ids in id_lists:
            text = bytes(ids).decode()
            resp = text.split('"""')[1]
            a = re.search(r"^A\. (.*)$", text, re.M).group(1)
            b = re.search(r"^B\. (.*)$", text, re.M).group(1)
            ha, hb = a.lower() in resp.lower(), b.lower() in resp.lower()
            k = 2 if (ha and hb) else 0 if ha else 1 if hb else 3
            logp = [math.log(0.02)] * 4
            logp[k] = math.log(0.9)
            out.append((logp, 0.96))
        return out

    def describe(self):
        return {"system_mode": "system", "letter_ids": {"A": [1]}, "assistant_prefix": ""}


def header(seed=judge.DEFAULT_SEED, orders=1, cfg="x"):
    ident = {"path": "stub", "config": {"sha": cfg}, "tokenizer": {"sha": "t"},
             "chat_template_sha": "c", "dtype": "float32"}
    return judge.make_header(ident, OracleScorer().describe(), seed, orders)


def run_oracle(rows, path, scorer=None, **hk):
    scorer = scorer or OracleScorer()
    stats = judge.judge_rows(rows, CASES, ALIASES, scorer, path, header(**hk), chunk=3, log=None)
    return scorer, stats, [r for r in judge.read_judged([path])[1]]


# ---------------------------------------------------------------- order randomization

def test_option_order_deterministic_and_balanced():
    ids = [f"{i:032x}" for i in range(2000)]
    first = [judge.option_order(i, 7) for i in ids]
    assert first == [judge.option_order(i, 7) for i in ids]
    n_new_first = sum(o == ("NEW", "OLD") for o in first)
    assert 900 < n_new_first < 1100
    assert first != [judge.option_order(i, 8) for i in ids]
    assert all(set(o) == {"NEW", "OLD"} for o in first)


def test_two_orders_are_a_swap():
    o = judge.orders_for("abc", 1, orders=2)
    assert o[0] == judge.option_order("abc", 1) and o[1] == o[0][::-1]


def test_letters_map_back_to_labels():
    p = [0.1, 0.6, 0.2, 0.1]
    assert judge.letters_to_labels(p, ("OLD", "NEW")) == {
        "OLD": 0.1, "NEW": 0.6, "BOTH_UNCLEAR": 0.2, "NEITHER": 0.1}
    assert judge.letters_to_labels(p, ("NEW", "OLD"))["OLD"] == 0.6


def test_decide_tie_is_unclear_not_old():
    assert judge.decide({"NEW": .4, "OLD": .4, "BOTH_UNCLEAR": .1, "NEITHER": .1}) == "BOTH_UNCLEAR"
    assert judge.decide({"NEW": .1, "OLD": .5, "BOTH_UNCLEAR": .3, "NEITHER": .1}) == "OLD"


def test_oracle_labels_survive_random_order():
    rows, want = [], []
    for k in range(40):
        cid = f"cf_{k % 4 + 1}"
        c = CASES[cid]
        kind = k % 4
        ans = [f"It is {c['o_new']} (v{k}).", f"It is {c['o_old']} (v{k}).",
               f"{c['o_new']} or {c['o_old']} (v{k}).", f"No idea (v{k})."][kind]
        rows.append(row(cid, "B3", ans, line=k))
        want.append(["NEW", "OLD", "BOTH_UNCLEAR", "NEITHER"][kind])
    with tempfile.TemporaryDirectory() as d:
        for orders in (1, 2):
            _, _, out = run_oracle(rows, os.path.join(d, f"o{orders}.jsonl"), orders=orders)
            assert [r["label"] for r in out] == want
            assert {tuple(r["orders"][0]) for r in out} == {("NEW", "OLD"), ("OLD", "NEW")}
            assert [r["strict_semantic_es"] for r in out] == [int(w == "NEW") for w in want]
            assert [r["semantic_reversion"] for r in out] == [int(w == "OLD") for w in want]
            for r in out:
                assert abs(sum(r["p"].values()) - 1) < 1e-9
                assert len(r["p_letter"]) == orders


# ---------------------------------------------------------------- blindness

def test_prompt_is_blind():
    tok = chat_tokenizer()
    secret = {"editor": "EDITORZZ", "model_tag": "MODELZZ", "arm": "ARMZZ",
              "condition": "CONDZZ", "delta_sha": "DELTAZZ", "seed": 987654,
              "target_tag": "TARGETZZ", "temperature": 0.123, "alpha": 3.5}
    r = row("cf_1", "B3", "</think>\n\nDanielle Darrieux speaks English.", line=4242,
            cot="CHAINZZ Danielle Darrieux thinks French", src="FILEZZ.jsonl", **secret)
    it = judge.make_item(r, CASES, ALIASES)
    for order in judge.orders_for(it["item"], orders=2):
        _, text = judge.render_chat(tok, judge.user_message(it, order), "system")
        for s in list(secret.values()) + ["CHAINZZ", "FILEZZ", "4242", "B3", "cf_1",
                                          "Darrieux", "think>"]:
            assert str(s) not in text, s
        assert not re.search(r"\b(new|old|edit\w*|original|budget|reason\w*)\b", text, re.I)
        assert "[SUBJECT] speaks English." in text
        assert text.count("English") == 2 and text.count("French") == 1   # options + response
    assert it["scrubbed"] and it["lexical"]["cell"] == "new-only"


def test_scrub_protects_values_and_scrubs_subjects_named_after_values():
    t, s = judge.scrub_subject("The Montreal Convention is in Frankfurt, not Montreal.",
                               "Montreal Convention", ("Montreal", "Frankfurt"))
    assert s and t == "The [SUBJECT] is in Frankfurt, not Montreal."
    t, _ = judge.scrub_subject("Nintendo was bought by Nintendo Entertainment.", "Nintendo",
                               ("Nintendo Entertainment", "Sega"))
    assert t == "[SUBJECT] was bought by Nintendo Entertainment."
    t, s = judge.scrub_subject("Paris and Parisian", "Ra", ())
    assert t == "Paris and Parisian" and not s          # word-bounded: no damage inside words
    it = judge.make_item(row("cf_2", "B0", "The Montreal Convention is in Frankfurt."), CASES, ALIASES)
    assert "Montreal" not in it["answer"] and it["lexical"]["cell"] == "new-only"


# ---------------------------------------------------------------- letter extraction

class StubTok:
    """encode() table standing in for a tokenizer whose letters are multi-token."""
    all_special_ids = [0]
    table = {"A": [10, 11], " A": [5, 20], "B": [12, 11], " B": [5, 21],
             "C": [13], " C": [22, 9], "D": [0, 14], " D": [23]}

    def encode(self, text, add_special_tokens=False):
        return list(self.table[text])


def test_letter_ids_use_first_token_and_drop_shared():
    ids = judge.letter_token_ids(StubTok())
    # " A"/" B" start with the shared space token 5 -> dropped; a special id (0) is skipped.
    assert ids == {"A": [10], "B": [12], "C": [13, 22], "D": [14, 23]}


def test_letter_ids_tiny_tokenizer():
    tok = chat_tokenizer()
    ids = judge.letter_token_ids(tok)
    assert ids == {L: tok.encode(L, add_special_tokens=False) for L in "ABCD"}


def test_letter_ids_raise_when_a_letter_has_no_own_token():
    class Bad(StubTok):
        table = dict(StubTok.table, B=[10], **{" B": [5]})
    try:
        judge.letter_token_ids(Bad())
    except ValueError:
        return
    raise AssertionError("ambiguous letters must raise")


def test_system_role_fallback():
    assert judge.pick_system_mode(chat_tokenizer()) == "system"
    tok = chat_tokenizer(TEMPLATE_NO_SYSTEM)
    assert judge.pick_system_mode(tok) == "merged"
    ids, text = judge.render_chat(tok, "hello", "merged")
    assert text.startswith(tok.bos_token + "<｜User｜>" + judge.SYSTEM + "\n\nhello")
    assert text.endswith("<｜Assistant｜>") and ids[0] == tok.bos_token_id
    dropping = TEMPLATE.replace("{{ m['content'] }}\n\n", "", 1)       # silently ignores system
    assert judge.pick_system_mode(chat_tokenizer(dropping)) == "merged"


# Shapes of the two recommended judges' templates (the real ones are checked with `show`).
GEMMA3_LIKE = (
    "{{ bos_token }}{% if messages[0]['role'] == 'system' %}"
    "{% set first_user_prefix = messages[0]['content'] + '\n\n' %}{% set loop_messages = messages[1:] %}"
    "{% else %}{% set first_user_prefix = '' %}{% set loop_messages = messages %}{% endif %}"
    "{% for m in loop_messages %}<start_of_turn>user\n"
    "{{ (first_user_prefix if loop.first else '') + (m['content'] | trim) }}<end_of_turn>\n"
    "{% endfor %}{% if add_generation_prompt %}<start_of_turn>model\n{% endif %}")
MISTRAL31_LIKE = (
    "{%- set today = strftime_now('%Y-%m-%d') %}"
    "{%- set default_system_message = 'You are Mistral Small 3.1. The current date is ' + today %}"
    "{{- bos_token }}{%- if messages[0]['role'] == 'system' %}"
    "{%- set system_message = messages[0]['content'] %}{%- set loop_messages = messages[1:] %}"
    "{%- else %}{%- set system_message = default_system_message %}"
    "{%- set loop_messages = messages %}{%- endif %}"
    "{{- '[SYSTEM_PROMPT]' + system_message + '[/SYSTEM_PROMPT]' }}"
    "{%- for m in loop_messages %}{{- '[INST]' + m['content'] + '[/INST]' }}{%- endfor %}")


def test_gemma3_and_mistral31_template_shapes():
    tok = chat_tokenizer(GEMMA3_LIKE)
    assert judge.pick_system_mode(tok) == "system"
    _, text = judge.render_chat(tok, "  body  ", "system")
    assert text == (tok.bos_token + "<start_of_turn>user\n" + judge.SYSTEM + "\n\nbody<end_of_turn>\n"
                    "<start_of_turn>model\n")
    tok = chat_tokenizer(MISTRAL31_LIKE)
    assert judge.pick_system_mode(tok) == "system"
    _, text = judge.render_chat(tok, "body", "system")
    assert "current date" not in text                        # explicit system turn: no dated default
    assert text.endswith("[SYSTEM_PROMPT]" + judge.SYSTEM + "[/SYSTEM_PROMPT][INST]body[/INST]")
    ident = judge.judge_identity(tiny_model(vocab=len(tok)), tok, None)
    assert ident["template_uses_strftime"] and ident["chat_template_sha"]


# ---------------------------------------------------------------- model scoring

def _scorer(**kw):
    tok = chat_tokenizer()
    return judge.LetterScorer(tiny_model(seed=3, vocab=len(tok)), tok, **kw)


def _prompts(scorer, n=5):
    its = [judge.make_item(row(f"cf_{k % 4 + 1}", "B3", "word " * (3 * k + 1), line=k), CASES,
                           ALIASES) for k in range(n)]
    return [scorer.encode(judge.user_message(it, ("NEW", "OLD"))) for it in its]


def test_batched_scores_equal_single():
    sc = _scorer(batch_size=8)
    prompts = _prompts(sc)
    assert len({len(p) for p in prompts}) == len(prompts)          # padding is exercised
    batched = sc.score(prompts)
    for p, (lp, mass) in zip(prompts, batched):
        lp1, mass1 = sc._forward([p])[0]
        assert max(abs(a - b) for a, b in zip(lp, lp1)) < 1e-4
        assert 0 < mass <= 1 and abs(mass - mass1) < 1e-5
        # the letter log-probs are the model's own next-token log-probs
        with torch.no_grad():
            full = torch.log_softmax(sc.model(input_ids=torch.tensor([p])).logits[0, -1], -1)
        assert abs(lp[0] - float(full[sc.letter_ids["A"][0]])) < 1e-4


def test_out_of_memory_backoff():
    sc = _scorer(batch_size=8)
    prompts = _prompts(sc, 4)
    want = sc.score(prompts)
    inner, sizes = sc.model, []

    class Flaky(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.inner = inner

        def get_input_embeddings(self):
            return inner.get_input_embeddings()

        def forward(self, **kw):
            sizes.append(kw["input_ids"].shape[0])
            if kw["input_ids"].shape[0] > 1:
                raise torch.OutOfMemoryError("simulated")
            return inner(**kw)

    sc.model = Flaky()
    got = sc.score(prompts)
    assert max(sizes) == 4 and sizes.count(1) == 4
    assert all(max(abs(a - b) for a, b in zip(x[0], y[0])) < 1e-4 for x, y in zip(got, want))


def test_end_to_end_with_tiny_model():
    sc = _scorer()
    rows = [row("cf_1", "B0", "English."), row("cf_1", "B3", "French.", line=1)]
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "j.jsonl")
        hdr = judge.make_header(judge.judge_identity(sc.model, sc.tok, None, "float32"),
                                sc.describe(), 1, 2)
        judge.judge_rows(rows, CASES, ALIASES, sc, path, hdr, log=None)
        h, out = judge.read_judged([path])
        assert h[0]["judge"]["tokenizer"]["kind"] == "vocab" and h[0]["prompt"]["sha"] == judge.prompt_sha()
        for r in out:
            assert r["label"] in judge.LABELS and len(r["logp_letter"]) == 2
            assert abs(sum(r["p"].values()) - 1) < 1e-6 and len(r["render_sha"][0]) == 16


# ---------------------------------------------------------------- resume

def test_resume_skips_done_rows_and_reuses_items():
    rows = [row(f"cf_{k % 4 + 1}", "B3", f"It is {CASES[f'cf_{k % 4 + 1}']['o_new']} ({k}).",
                line=k) for k in range(8)]
    dup = dict(rows[0], line=99, editor="OTHER")                 # same content, different row
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "j.jsonl")
        sc, st, out1 = run_oracle(rows[:5], path)
        assert st["items_scored"] == 5 and len(out1) == 5
        sc, st, out2 = run_oracle(rows + [dup], path)
        assert st["rows_done_before"] == 5 and st["items_scored"] == 3 and sc.prompts == 3
        assert len(out2) == 9 and len({r["row_key"] for r in out2}) == 9
        assert out2[:5] == out1
        assert out2[-1]["p"] == out2[0]["p"] and out2[-1]["row"]["editor"] == "OTHER"
        sc, st, out3 = run_oracle(rows + [dup], path)
        assert sc.calls == 0 and st["rows_written"] == 0 and out3 == out2
        with open(path) as f:
            assert sum(1 for line in f if '"_meta"' in line) == 1


def test_resume_repairs_a_torn_last_line():
    rows = [row("cf_1", "B3", f"English {k}.", line=k) for k in range(4)]
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "j.jsonl")
        run_oracle(rows[:2], path)
        with open(path, "a") as f:
            f.write('{"row_key": "torn", "item": ')
        assert len(judge.read_judged([path])[1]) == 2            # readers ignore the torn line
        sc, st, out = run_oracle(rows, path)
        assert st["items_scored"] == 2 and len(out) == 4
        with open(path) as f:
            for line in f:
                json.loads(line)


def test_resume_refuses_other_judge_settings():
    rows = [row("cf_1", "B3", "English.")]
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "j.jsonl")
        run_oracle(rows, path)
        for bad in ({"cfg": "other-weights"}, {"orders": 2}, {"seed": 1}):
            try:
                run_oracle(rows, path, **bad)
            except ValueError:
                continue
            raise AssertionError(f"{bad} must be refused")


def test_empty_answer_is_neither_without_the_judge():
    with tempfile.TemporaryDirectory() as d:
        sc, st, out = run_oracle([row("cf_1", "B3", " </think>\n ")], os.path.join(d, "j.jsonl"))
        assert sc.prompts == 0 and out[0]["label"] == "NEITHER" and out[0]["source"] == "empty"


# ---------------------------------------------------------------- reading rows

def _write(path, recs):
    with open(path, "w") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")


def test_read_rows_legacy_and_v2():
    with tempfile.TemporaryDirectory() as d:
        _write(os.path.join(d, "r1qwen1_5b_ROME_cf200_r0of8.jsonl"), [
            {"_meta": True, "model_tag": "r1qwen1_5b", "editor": "ROME", "dataset": {"tag": "cf200"}},
            {"case_id": "cf_1", "editor": "ROME", "budget": "B0", "probe": "efficacy",
             "decode": "greedy", "seed": None, "temperature": None, "q": "q", "cot": "", "answer": "a"},
            {"case_id": "cf_2", "error": "boom"},
            {"case_id": "cf_1", "editor": "ROME", "budget": "B0", "probe": "open", "q": "q",
             "cot": "", "answer": "a"}])
        _write(os.path.join(d, "r1qwen1_5b_BASE_cf200_r0.jsonl"), [
            {"case_id": "cf_1", "budget": "B3", "probe": "base", "q": "q", "cot": "", "answer": "a"}])
        _write(os.path.join(d, "v2_shard.jsonl"), [
            {"_meta": True, "git": "x"},
            {"case_id": "cf_1", "model_tag": "r1qwen32b", "editor": "ROME", "target_tag": "new",
             "budget": "B3", "probe": "efficacy", "condition": "N", "arm": "N", "alpha": 1.0,
             "decode": "greedy", "seed": 0, "temperature": 0.0, "q": "q", "cot": "c", "answer": "a",
             "chain_end": "think_end", "n_chain_tokens": 5, "n_answer_tokens": 2, "delta_sha": "d"}])
        rows = judge.read_rows([os.path.join(d, "*.jsonl")])
        assert [(r["model_tag"], r["editor"], r["dataset_tag"], r["probe"], r["schema"], r["decode"])
                for r in rows] == [
            ("r1qwen1_5b", "BASE", "cf200", "base", "legacy", "greedy"),
            ("r1qwen1_5b", "ROME", "cf200", "efficacy", "legacy", "greedy"),
            ("r1qwen32b", "ROME", None, "efficacy", "v2", "greedy")]
        assert rows[1]["line"] == 1 and rows[1]["src"] == "r1qwen1_5b_ROME_cf200_r0of8.jsonl"
        assert len(judge.read_rows([os.path.join(d, "*.jsonl")], where=["condition=N"])) == 1
        try:
            judge.read_rows([os.path.join(d, "nothing*.jsonl")])
        except FileNotFoundError:
            return
        raise AssertionError("an empty glob must raise")


# ---------------------------------------------------------------- aggregation

def _study(d):
    """Two cases × B0/B3 efficacy + para0 + locality, written as one legacy shard."""
    recs = [{"_meta": True, "model_tag": "m", "editor": "ROME", "dataset": {"tag": "t"}}]
    spec = [("cf_1", "B0", "efficacy", "English."), ("cf_1", "B3", "efficacy", "French, not English? No: French."),
            ("cf_1", "B0", "para0", "English."), ("cf_1", "B0", "locality", "English."),
            ("cf_1", "B3", "locality", "French."),
            ("cf_2", "B0", "efficacy", "The Montreal Convention is in Frankfurt."),
            ("cf_2", "B3", "efficacy", "Frankfurt."), ("cf_2", "B3", "para0", "Montreal."),
            ("cf_3", "B0", "efficacy", "genetics"), ("cf_3", "B3", "efficacy", "physics")]
    for cid, b, p, a in spec:
        r = row(cid, b, a, probe=p)
        for k in ("src", "line", "model_tag"):
            r.pop(k)
        recs.append(r)
    path = os.path.join(d, "m_ROME_t_r0of1.jsonl")
    _write(path, recs)
    return path


def test_lexical_block_matches_metrics_score():
    with tempfile.TemporaryDirectory() as d:
        path = _study(d)
        rows = judge.read_rows([path])
        _, _, out = run_oracle(rows, os.path.join(d, "j.jsonl"))
        sem = judge.semantic_score(out)["groups"]
        (g, bud), = sem.items()
        cases = [dict(v, case_id=k) for k, v in CASES.items()]
        ref = metrics.score(path, cases, ALIASES)
        for b in ("B0", "B3"):
            for k in ("ES", "RR", "RRs", "PS", "Loc"):
                assert bud[b]["lex"][k] == ref[b][k], (b, k, bud[b]["lex"][k], ref[b][k])


def test_semantic_score_gates_rr_on_b0_success():
    with tempfile.TemporaryDirectory() as d:
        _, _, out = run_oracle(judge.read_rows([_study(d)]), os.path.join(d, "j.jsonl"))
    (g, bud), = judge.semantic_score(out)["groups"].items()
    # oracle: cf_1 B0 NEW, B3 both mentioned -> C; cf_2 B0 NEW (subject scrubbed), B3 NEW;
    # cf_3 B0 OLD (gated out), B3 NEW.
    assert bud["B0"]["ES"] == 2 / 3 and bud["B3"]["ES"] == 2 / 3
    assert bud["B3"]["rr_n"] == 2 and bud["B3"]["RR"] == 0.0
    assert bud["B0"]["PS"] == 1.0 and bud["B3"]["PS"] == 0.0
    assert bud["B0"]["Loc"] == 0.0 and bud["B3"]["Loc"] == 1.0 and bud["B3"]["Loc_correct"] == 1.0
    assert bud["B3"]["rates"]["efficacy"]["BOTH_UNCLEAR"] == 1 / 3
    per = judge.semantic_by_case(out)[g]
    assert per["b0ok"] == {"cf_1": True, "cf_2": True, "cf_3": False}
    assert per["rev"]["B3"] == {"cf_1": [0], "cf_2": [0]} and per["es_first"]["cf_3"] == {"B0": 0, "B3": 1}


def test_combine_judges_averages_probabilities():
    def jr(key, p):
        full = dict(zip(judge.LABELS, p))
        return {"row_key": key, "item": key, "row": {"case_id": key, "budget": "B0",
                                                   "probe": "efficacy"},
                "values": {}, "lexical": {}, "p": full, "label": judge.decide(full)}
    a = [jr("k1", [.6, .3, .05, .05]), jr("k2", [.5, .3, .1, .1])]
    b = [jr("k1", [.2, .7, .05, .05]), jr("k2", [.3, .5, .1, .1])]
    out = {r["row_key"]: r for r in judge.combine_judges({"g": a, "m": b})}
    assert out["k1"]["label"] == "OLD" and out["k1"]["split"]
    assert out["k2"]["label"] == "BOTH_UNCLEAR" and out["k2"]["semantic_reversion"] == 0
    try:
        judge.combine_judges({"g": a, "m": b[:1]})
    except ValueError:
        return
    raise AssertionError("judges covering different rows must raise")
