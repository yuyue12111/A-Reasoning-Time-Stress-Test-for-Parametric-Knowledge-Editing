"""Batched two-phase generation with per-row edits (engine v2).

A request asks for one generation under one thinking budget.  Budgets B1/B2/B3 run two phases:

* chain phase: the chain prompt, one ``generate`` call with ``max_new_tokens=CAP[budget]`` that stops
  at the family's chain-closing token (``</think>``) or at EOS; an optional per-row logit bias is
  applied here and only here;
* answer phase: the chain is re-tokenized inside the answer prompt (exactly like the legacy
  ``think_budget.generate_with_budget``) and the answer is generated with ``answer_cap`` tokens,
  EOS only, no logit processor.

B0/B0P have only the answer phase; GIVEN runs the answer phase on a caller-supplied chain.  Every row
of a batch carries its own edit through a shared ``EditBank`` (same edit in both phases of a row),
so one batch mixes edited and unedited rows while each row sees only its own edit.

Template families (``template=``):

* ``r1`` (default): the ``think_budget`` constants byte for byte (TPL, ZEROTHINK, LESSTHINK_CANNED,
  THINK_END) and the ``think_budget._gen`` BOS rule (manual BOS unless ``WHYAAAI_NO_BOS``;
  ``add_special_tokens=False``).
* ``qwq``: ChatML with native thinking; the chain opens ``<think>\\n`` inside the assistant turn and
  B0 pre-closes an empty span.  No BOS.  Stops: ``</think>`` (chain close), ``<|im_end|>`` and EOS.
* ``instruct_cot``: ChatML for a model without reasoning training.  The chain is a prompted
  assistant turn ("Think step by step ... Do not state a final answer yet."); the answer phase
  replays it as the assistant turn and asks "Now give the final answer only." in a new user turn.
  ``<|im_end|>`` closes the chain.

Deviations from the legacy generator (all deliberate; the G0 gate measures their joint effect):

1. EOS inside the chain closes the chain (``chain_end="eos"``).  Legacy only ends a chain on
   ``</think>`` text; after an EOS it generates again from prompt + chain so far, which under greedy
   decoding re-emits EOS and never terminates (under sampling the chain continues past the EOS).
2. The chain is one ``generate`` call capped at exactly ``CAP[budget]`` generated tokens.  Legacy
   re-tokenizes the decoded chain after each call; when the re-tokenized count falls short of the
   cap (stripped special tokens, merges) it asks for ``max(64, CAP - n)`` more tokens, so a legacy
   chain can overshoot the cap, and a legacy call never asks for fewer than 64 tokens.
3. Generation stops at the atomic ``</think>`` id instead of generating on to EOS and splitting the
   text.  The chain text is the same under greedy decoding.  If a chain spells ``</think>`` out of
   smaller pieces the text is still cut there, as legacy does, and ``n_chain_tokens`` counts the
   tokens up to the one that completes the closing string.
4. Stop ids are the tokenizer EOS plus ``generation_config.eos_token_id`` (legacy: the latter only);
   for the R1 checkpoints both are the same single id.
5. Batching: rows are left-padded with an attention mask.  In bf16, logits of a padded batch differ
   from single-row logits in the last bits, so rare greedy near-ties can flip; fp32 on CPU is exact
   in the tests.  Sampling seeds ``torch.manual_seed(seed)`` once per batch, so a sampled row depends
   on which rows share its batch (legacy seeded once per request).  Sampled outputs are valid
   draws but are not reproducible across different batch compositions (e.g. after a resume).
6. B4 (forced "Wait" extension) and the legacy ``steerer`` hook are not supported.  B0/B0P rows have
   ``chain_end=None`` and ``n_chain_tokens=0`` (B0P's ``cot`` is the canned LESSTHINK sentence).
"""
import contextlib
import json
import os
import time
from dataclasses import dataclass

import torch

from think_budget import CAP, LESSTHINK_CANNED, LESSTHINK_COT, THINK_END, TPL, ZEROTHINK

BUDGETS = ("B0", "B0P", "B1", "B2", "B3", "GIVEN")
CHAIN_BUDGETS = ("B1", "B2", "B3")
ANSWER_CAP = 256
DEFAULT_TEMPERATURE = 0.6
# Sampling settings Study 1 actually ran with: think_budget._gen passed only temperature, so top_p came
# from the R1 checkpoints' generation_config (0.95) and top_k from transformers' default (50).  The
# engine now passes all three explicitly (neutral_generation_config) and records them per row.
DEFAULT_TOP_P = 0.95
DEFAULT_TOP_K = 50

IM_START, IM_END = "<|im_start|>", "<|im_end|>"
QWQ_CHAIN = IM_START + "user\n{q}" + IM_END + "\n" + IM_START + "assistant\n<think>\n"
IC_B0 = IM_START + "user\n{q}\nAnswer with the completion only." + IM_END + "\n" + IM_START + "assistant\n"
IC_CHAIN = (IM_START + "user\n{q}\nThink step by step about this before answering. "
            "Do not state a final answer yet." + IM_END + "\n" + IM_START + "assistant\n")
IC_FOLLOWUP = IM_END + "\n" + IM_START + "user\nNow give the final answer only." + IM_END + "\n" + IM_START + "assistant\n"


def _single_id(tok, s):
    ids = tok(s, add_special_tokens=False)["input_ids"]
    if len(ids) != 1:
        raise ValueError(f"{s!r} must encode to exactly one token, got {ids}; wrong tokenizer "
                         f"or a half-width bar where a full-width one (U+FF5C) belongs")
    return ids[0]


def eos_ids(tok, model=None):
    """EOS ids: the tokenizer's EOS plus the model's ``generation_config.eos_token_id`` (legacy
    ``generate`` stopped on the latter; for the R1 models both are the same single id)."""
    out = []
    cands = [getattr(tok, "eos_token_id", None)]
    gc = getattr(model, "generation_config", None)
    e = getattr(gc, "eos_token_id", None)
    cands += list(e) if isinstance(e, (list, tuple)) else [e]
    for t in cands:
        if t is not None and int(t) not in out:
            out.append(int(t))
    if not out:
        raise ValueError("no EOS id: tokenizer and generation_config both lack one")
    return out


class Template:
    """Prompt family: prompt strings, BOS rule and stop ids.

    ``chain_close`` ids end a chain naturally (``chain_end="think_end"``); ``chain_eos`` ids end it
    early (``"eos"``).  ``required`` strings must each encode to a single token.
    """
    name = None
    close_text = None
    required = ()

    def __init__(self, tok, model=None, system=None):
        self.tok = tok
        self.system = system
        self.ids = {s: _single_id(tok, s) for s in self.required}
        self.eos = eos_ids(tok, model)

    def bos_text(self):
        return ""

    def encode(self, text):
        return self.tok(text, add_special_tokens=False)["input_ids"]

    def b0(self, q):
        raise NotImplementedError

    def b0p(self, q):
        return self.answer(q, LESSTHINK_COT)

    def chain(self, q):
        raise NotImplementedError

    def answer(self, q, cot):
        raise NotImplementedError

    @property
    def chain_close(self):
        raise NotImplementedError

    @property
    def chain_eos(self):
        return [t for t in self.eos if t not in self.chain_close]

    @property
    def answer_stop(self):
        return list(self.eos)

    def describe(self):
        return {"name": self.name, "system": self.system, "chain_close": self.chain_close,
                "chain_eos": self.chain_eos, "answer_stop": self.answer_stop,
                "bos": self.bos_text()}


class R1Template(Template):
    """DeepSeek-R1 prompts, byte-identical to ``think_budget`` (TPL / ZEROTHINK / LESSTHINK_CANNED)."""
    name = "r1"
    close_text = THINK_END
    required = ("<｜User｜>", "<｜Assistant｜>", "<think>", THINK_END)

    def __init__(self, tok, model=None, system=None):
        if system:
            raise ValueError("the r1 template has no system turn")
        super().__init__(tok, model, None)

    def bos_text(self):
        return "" if os.environ.get("WHYAAAI_NO_BOS") else (self.tok.bos_token or "")

    def encode(self, text):
        bos = self.bos_text()                   # think_budget._gen: manual BOS, never twice
        if bos and not text.startswith(bos):
            text = bos + text
        return self.tok(text, add_special_tokens=False)["input_ids"]

    def b0(self, q):
        return ZEROTHINK.format(q=q)

    def b0p(self, q):
        return LESSTHINK_CANNED.format(q=q)

    def chain(self, q):
        return TPL.format(q=q)

    def answer(self, q, cot):
        return TPL.format(q=q) + cot + "\n" + THINK_END + "\n\n"

    @property
    def chain_close(self):
        return [self.ids[THINK_END]]


class _ChatML(Template):
    def _sys(self):
        return "" if not self.system else IM_START + "system\n" + self.system + IM_END + "\n"

    @property
    def answer_stop(self):
        return [self.ids[IM_END]] + [t for t in self.eos if t != self.ids[IM_END]]


class QwQTemplate(_ChatML):
    """ChatML with a native ``<think>`` span (QwQ-32B)."""
    name = "qwq"
    close_text = THINK_END
    required = (IM_START, IM_END, "<think>", THINK_END)

    def chain(self, q):
        return self._sys() + QWQ_CHAIN.format(q=q)

    def b0(self, q):
        return self.answer(q, "")

    def answer(self, q, cot):
        return self.chain(q) + cot + "\n" + THINK_END + "\n\n"

    @property
    def chain_close(self):
        return [self.ids[THINK_END]]

    @property
    def chain_eos(self):
        return [self.ids[IM_END]] + [t for t in self.eos if t not in (self.ids[IM_END], self.ids[THINK_END])]


class InstructCoTTemplate(_ChatML):
    """ChatML with a prompted chain turn for a model without reasoning training."""
    name = "instruct_cot"
    close_text = IM_END
    required = (IM_START, IM_END)

    def b0(self, q):
        return self._sys() + IC_B0.format(q=q)

    def chain(self, q):
        return self._sys() + IC_CHAIN.format(q=q)

    def answer(self, q, cot):
        return self.chain(q) + cot + IC_FOLLOWUP

    @property
    def chain_close(self):
        return [self.ids[IM_END]]


TEMPLATES = {"r1": R1Template, "qwq": QwQTemplate, "instruct_cot": InstructCoTTemplate}


def get_template(name, tok, model=None, system=None):
    if name not in TEMPLATES:
        raise ValueError(f"unknown template {name!r}; choose from {sorted(TEMPLATES)}")
    return TEMPLATES[name](tok, model, system)


@dataclass
class Request:
    """One generation.  ``key`` is copied into the output; ``edit`` maps layer -> (A, B) or is None;
    ``chain_bias`` maps token id -> additive logit, applied only while the chain is generated."""
    key: dict
    q: str
    budget: str
    edit: dict = None
    alpha: float = 1.0
    chain_bias: dict = None
    given_chain: str = None
    user_prefix: str = ""
    decode: str = "greedy"
    seed: int = None
    temperature: float = None
    top_p: float = None
    top_k: int = None

    def check(self):
        if self.budget not in BUDGETS:
            raise ValueError(f"budget {self.budget!r} not in {BUDGETS}")
        if self.decode not in ("greedy", "sample"):
            raise ValueError(f"decode {self.decode!r} must be greedy or sample")
        if self.decode == "greedy":
            self.seed = self.temperature = self.top_p = self.top_k = None
        else:
            if self.seed is None:
                raise ValueError("sampling needs an integer seed")
            self.seed = int(self.seed)
            self.temperature = float(DEFAULT_TEMPERATURE if self.temperature is None else self.temperature)
            self.top_p = float(DEFAULT_TOP_P if self.top_p is None else self.top_p)
            self.top_k = int(DEFAULT_TOP_K if self.top_k is None else self.top_k)
        if self.budget == "GIVEN" and not isinstance(self.given_chain, str):
            raise ValueError("budget GIVEN needs given_chain (str)")
        self.alpha = float(self.alpha)
        self.user_prefix = self.user_prefix or ""
        return self


class RowBias:
    """LogitsProcessor adding each row's sparse bias to its scores; rows without bias are untouched.

    ``steps`` counts decoding steps the processor ran, so a row can prove the bias was in the loop.
    """

    def __init__(self, biases):
        rows, cols, vals = [], [], []
        for i, b in enumerate(biases):
            for t, v in sorted((b or {}).items()):
                rows.append(i)
                cols.append(int(t))
                vals.append(float(v))
        self.rows = torch.tensor(rows, dtype=torch.long)
        self.cols = torch.tensor(cols, dtype=torch.long)
        self.vals = torch.tensor(vals, dtype=torch.float32)
        self.steps = 0

    def __call__(self, input_ids, scores):
        self.steps += 1
        if self.rows.numel():
            if int(self.cols.max()) >= scores.shape[1]:
                raise ValueError("chain_bias token id outside the vocabulary")
            dev = scores.device
            scores = scores.index_put((self.rows.to(dev), self.cols.to(dev)),
                                      self.vals.to(dev, scores.dtype), accumulate=True)
        return scores


def _split(gen, close, eos):
    """Cut generated ids at the first stop id -> (content ids, end)."""
    close, eos = set(close), set(eos)
    for j, t in enumerate(gen):
        if t in close:
            return gen[:j], "think_end"
        if t in eos:
            return gen[:j], "eos"
    return gen, "cap"


def neutral_generation_config(model):
    """Replace the checkpoint's generation_config with transformers' defaults; returns the original.

    ``generate`` applies a checkpoint's generation_config to every call, so Qwen2.5-32B-Instruct's
    repetition_penalty 1.05 would act under greedy decoding (penalising o_new/o_old in B3 answers
    after the chain named them) and sampling would inherit top_p/top_k without a record (review
    2026-09-29, M1).  The engine passes every decoding parameter explicitly instead; the original
    is kept on the model for provenance.
    """
    from transformers import GenerationConfig
    if getattr(model, "_rt_generation_config_original", None) is None:
        gc = getattr(model, "generation_config", None)
        model._rt_generation_config_original = gc.to_diff_dict() if gc is not None else {}
    model.generation_config = GenerationConfig()
    return model._rt_generation_config_original


class Engine:
    """Runs a list of ``Request``s in length-sorted batches and returns results in request order.

    ``bank`` (``rt.edit_hooks.EditBank``) is entered for the duration of ``run`` and cleared after;
    ``bank.set_batch`` is called for every batch, including batches without edits.
    ``max_batch_tokens`` bounds rows x (longest prompt + max_new_tokens) of a batch (KV-cache size);
    a single row above the bound still runs alone.  ``caps`` overrides ``think_budget.CAP``.
    """

    def __init__(self, model, tok, bank=None, template="r1", system=None, batch_size=16,
                 max_batch_tokens=None, answer_cap=ANSWER_CAP, caps=None):
        self.model = model
        self.tok = tok
        self.bank = bank
        self.template = template if isinstance(template, Template) else get_template(template, tok, model, system)
        self.batch_size = int(batch_size)
        self.max_batch_tokens = max_batch_tokens
        self.answer_cap = int(answer_cap)
        self.caps = dict(CAP)
        self.caps.update(caps or {})
        pad = tok.pad_token_id
        self.pad_id = int(pad) if pad is not None else self.template.eos[0]
        self.batch_log = []
        self._next_batch = 0
        self.generation_config_original = neutral_generation_config(model)

    def ntok(self, text):
        """Token count without BOS (legacy ``think_budget._ntok``)."""
        return len(self.tok(text, add_special_tokens=False)["input_ids"])

    def _device(self):
        return self.model.get_input_embeddings().weight.device

    def _batches(self, items, max_new):
        """items: [(req_index, prompt_ids)] -> list of item lists, longest prompts first."""
        items = sorted(items, key=lambda it: (-len(it[1]), it[0]))
        out, cur, longest = [], [], 0
        for it in items:
            L = max(longest, len(it[1]))
            full = len(cur) >= self.batch_size
            over = (self.max_batch_tokens is not None
                    and (len(cur) + 1) * (L + max_new) > self.max_batch_tokens)
            if cur and (full or over):
                out.append(cur)
                cur, L = [], len(it[1])
            cur.append(it)
            longest = L
        if cur:
            out.append(cur)
        return out

    def _generate(self, reqs, batch, max_new, stops, phase, biases=None):
        """One ``generate`` call on a batch; returns (batch_id, generated id lists, bias steps)."""
        rows = [reqs[i] for i, _ in batch]
        edits = [r.edit for r in rows]
        if self.bank is not None:
            self.bank.set_batch(edits, alphas=[r.alpha for r in rows])
        elif any(e for e in edits):
            raise ValueError("requests carry edits but the engine has no EditBank")
        L = max(len(ids) for _, ids in batch)
        n = len(batch)
        input_ids = torch.full((n, L), self.pad_id, dtype=torch.long)
        attn = torch.zeros((n, L), dtype=torch.long)
        for k, (_, ids) in enumerate(batch):
            input_ids[k, L - len(ids):] = torch.tensor(ids, dtype=torch.long)
            attn[k, L - len(ids):] = 1
        dev = self._device()
        r0 = rows[0]
        kw = dict(max_new_tokens=max_new, pad_token_id=self.pad_id, eos_token_id=list(stops),
                  do_sample=r0.decode == "sample")
        if r0.decode == "sample":
            kw.update(temperature=r0.temperature, top_p=r0.top_p, top_k=r0.top_k)
            torch.manual_seed(r0.seed)
        proc = None
        if biases is not None and any(biases):
            from transformers import LogitsProcessorList
            proc = RowBias(biases)
            kw["logits_processor"] = LogitsProcessorList([proc])
        bid = self._next_batch
        self._next_batch += 1
        t0 = time.time()
        with torch.no_grad():
            out = self.model.generate(input_ids=input_ids.to(dev), attention_mask=attn.to(dev), **kw)
        gen = out[:, L:].tolist()
        self.batch_log.append({"batch_id": bid, "phase": phase, "n": n, "max_prompt": L,
                               "max_new": max_new, "gen_len": len(gen[0]) if gen else 0,
                               "decode": r0.decode, "seed": r0.seed, "temperature": r0.temperature,
                               "top_p": r0.top_p, "top_k": r0.top_k,
                               "seconds": round(time.time() - t0, 3)})
        return bid, gen, (proc.steps if proc is not None else None)

    def _groups(self, reqs, idx, keyf):
        groups = {}
        for i in idx:
            groups.setdefault(keyf(reqs[i]), []).append(i)
        return [groups[k] for k in sorted(groups, key=lambda k: json.dumps(k))]

    def _chain_text(self, content, end):
        text = self.tok.decode(content, skip_special_tokens=True)
        n = len(content)
        close = self.template.close_text
        if close and close in text:             # closing string spelled out of smaller pieces
            text = text.split(close)[0]
            end = "think_end"
            lo, hi = 1, len(content)            # smallest prefix whose text contains the close string
            while lo < hi:
                mid = (lo + hi) // 2
                if close in self.tok.decode(content[:mid], skip_special_tokens=True):
                    hi = mid
                else:
                    lo = mid + 1
            n = lo
        return text, end, n

    def run(self, requests):
        reqs = [r.check() for r in requests]
        res = [None] * len(reqs)
        chain = {}
        T = self.template
        ctx = self.bank if self.bank is not None else contextlib.nullcontext()
        with ctx:
            idx = [i for i, r in enumerate(reqs) if r.budget in CHAIN_BUDGETS]
            for grp in self._groups(reqs, idx, lambda r: (self.caps[r.budget], r.decode, r.seed, r.temperature,
                                                               r.top_p, r.top_k)):
                cap = self.caps[reqs[grp[0]].budget]
                items = [(i, T.encode(T.chain(reqs[i].user_prefix + reqs[i].q))) for i in grp]
                for batch in self._batches(items, cap):
                    biases = [reqs[i].chain_bias for i, _ in batch]
                    bid, gen, steps = self._generate(reqs, batch, cap, T.chain_close + T.chain_eos,
                                                     "chain", biases)
                    for (i, _), g in zip(batch, gen):
                        content, end = _split(g, T.chain_close, T.chain_eos)
                        cot, end, n = self._chain_text(content, end)
                        chain[i] = {"cot": cot, "chain_end": end, "n_chain_tokens": n,
                                    "chain_batch_id": bid,
                                    "bias_steps": steps if reqs[i].chain_bias else None}
            items = []
            for i, r in enumerate(reqs):
                q = r.user_prefix + r.q
                if r.budget == "B0":
                    text, cot = T.b0(q), ""
                elif r.budget == "B0P":
                    text, cot = T.b0p(q), LESSTHINK_COT
                elif r.budget == "GIVEN":
                    text, cot = T.answer(q, r.given_chain), r.given_chain
                    chain[i] = {"cot": cot, "chain_end": "given", "n_chain_tokens": self.ntok(cot),
                                "chain_batch_id": None, "bias_steps": None}
                else:
                    text = T.answer(q, chain[i]["cot"])
                if r.budget in ("B0", "B0P"):
                    chain[i] = {"cot": cot, "chain_end": None, "n_chain_tokens": 0,
                                "chain_batch_id": None, "bias_steps": None}
                items.append((i, T.encode(text)))
            for grp in self._groups(reqs, range(len(reqs)), lambda r: (r.decode, r.seed, r.temperature, r.top_p, r.top_k)):
                gset = set(grp)
                for batch in self._batches([it for it in items if it[0] in gset], self.answer_cap):
                    bid, gen, _ = self._generate(reqs, batch, self.answer_cap, T.answer_stop, "answer")
                    for (i, _), g in zip(batch, gen):
                        content, _end = _split(g, [], T.answer_stop)
                        r = reqs[i]
                        out = dict(r.key)
                        out.update(q=r.q, budget=r.budget, decode=r.decode, seed=r.seed,
                                   temperature=r.temperature, template=T.name, **chain[i],
                                   answer=self.tok.decode(content, skip_special_tokens=True),
                                   n_answer_tokens=len(content), batch_id=bid)
                        if r.decode == "sample":
                            out.update(top_p=r.top_p, top_k=r.top_k)
                        if r.user_prefix:
                            out["user_prefix"] = r.user_prefix
                        res[i] = out
        return res
