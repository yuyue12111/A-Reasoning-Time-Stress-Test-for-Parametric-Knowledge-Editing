"""Semantic endpoint: a blind open-weight judge reads which candidate value an answer commits to.

The lexical rule (``metrics.py``) calls an answer an edit success if it contains the new value
and not the old one.  It cannot read negation ("not Norway but Bulgaria"), settling after a
switch, demonyms ("Indian" for India) or hedges, and a subject whose name contains the old value
counts as a reversion.  This module classifies each (question, final answer) into

    NEW | OLD | BOTH_UNCLEAR | NEITHER

relative to the two candidate values, with an instruction-tuned judge from a model family that
is not under test (the tested models are Qwen- and Llama-based; recommended judges are
google/gemma-3-27b-it and mistralai/Mistral-Small-3.1-24B-Instruct-2503, one H200 each in bf16).

Design (each choice fixes a flaw of ``revert_judge.py`` / ``sj_validate.py``):

* Blind.  The judge sees the question and the final answer text only: never the chain, the arm,
  the budget, the model, or which value is the edit.  The subject's name is replaced by
  ``[SUBJECT]`` in both (word-bounded; a candidate value that contains the subject is protected),
  so a subject named after the old value cannot look like a reversion and the judge cannot
  consult its own knowledge of the true fact.  R1 markers (``</think>``) are stripped.
* Order.  The two values are options A/B in a per-item order fixed by ``sha256(seed:item)``;
  C = both/unclear, D = neither.  ``orders=2`` also scores the swapped order and averages, which
  cancels the judge's position bias.
* No text parsing.  The decision is read from the next-token log-probabilities of the option
  letters right after the chat template's generation prompt.  Each letter's probability sums its
  "A" and " A" spellings, using the first token of each spelling and dropping a first token that
  several letters share.  The full four-way vector, the raw log-probabilities and the probability
  mass on the letters are kept.
* Resumable.  Output is jsonl, one line per input row keyed by ``row_key``, carrying the
  content hash ``item`` of what the judge saw; verdicts are cached by item, so a repeated
  (question, answer, values) is judged once.  The first line is a provenance header (judge path,
  config hash, tokenizer hash, chat-template hash, prompt hash, code hash, git); a resumed run
  must match it.
* Endpoints.  ``strict_semantic_es`` = 1{NEW} and ``semantic_reversion`` = 1{OLD} per row.
  ``semantic_score`` aggregates per condition with the gating of ``metrics.score`` (RR among
  B0 successes); ``combine_judges`` averages two judges' probability vectors (argmax; an exact
  NEW/OLD tie is BOTH_UNCLEAR, never OLD).

Run as ``PYTHONPATH=src python -m rt.judge {run,show,selfcheck,score}``; see
``experiments/rt/README_judge.md``.
"""
import argparse
import glob
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time

import metrics

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FORMAT = "rt-judge-v1"
ITEM_VERSION = 1
PROMPT_VERSION = "rt-judge-prompt-v1"
DEFAULT_SEED = 2027
LABELS = ("NEW", "OLD", "BOTH_UNCLEAR", "NEITHER")
LETTERS = ("A", "B", "C", "D")
LETTER_VARIANTS = ("{}", " {}")
SUBJECT_TOKEN = "[SUBJECT]"
MAX_ANSWER_CHARS = 4000
DEFAULT_PROBES = ("efficacy", "base", "para0", "para1", "locality")
IDENTITY_FIELDS = ("case_id", "model_tag", "editor", "target_tag", "dataset_tag", "budget",
                   "probe", "condition", "arm", "alpha", "decode", "seed", "temperature",
                   "delta_sha", "schema", "src", "line")
GROUP_KEYS = ("model_tag", "editor", "target_tag", "dataset_tag", "condition", "arm", "alpha",
              "decode", "temperature")

SYSTEM = ("You are a careful annotator. You follow the instructions exactly and reply with a "
          "single letter.")

USER_TEMPLATE = """Read the question and the response below, then decide which candidate value the response gives as its final answer.

Question: {question}

Response:
\"\"\"
{answer}
\"\"\"

Options:
A. {option_a}
B. {option_b}
C. Both or unclear: the response asserts both values, or wavers between them without settling on one.
D. Neither: the response gives a different value, no value, off-topic text, or a refusal.

Rules:
1. Judge only the response. Do not use your own knowledge of which value is true.
2. Count what the response asserts, not what it mentions: a value that is mentioned only to be rejected, corrected, or as background does not count.
3. If the response considers both values and then settles on one, choose that one.
4. Other forms of a value count as that value: abbreviations, full or partial names, translations, and adjective or demonym forms (for example, "Indian" counts as India). A partial name that fits A and B equally is unclear.
5. Hedging words such as "probably" do not matter when one value is given; offering both as possibilities without choosing is unclear.
6. "[SUBJECT]" replaces the name of the entity the question is about.

Answer with a single letter: A, B, C or D."""

_MARKERS = re.compile(r"</?think>|<｜[^｜<>]{1,40}｜>")


def _sha(obj):
    data = obj if isinstance(obj, bytes) else json.dumps(obj, sort_keys=True,
                                                         ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()


def prompt_sha():
    """Hash of everything that defines the judge's input apart from the item itself."""
    return _sha({"version": PROMPT_VERSION, "system": SYSTEM, "user": USER_TEMPLATE,
                 "letters": LETTERS, "variants": LETTER_VARIANTS, "subject": SUBJECT_TOKEN,
                 "max_answer_chars": MAX_ANSWER_CHARS, "markers": _MARKERS.pattern,
                 "item_version": ITEM_VERSION})


# ------------------------------------------------------------------ rows

_LEGACY_NAME = re.compile(r"^(?P<model_tag>.+?)_(?P<editor>[A-Z][A-Za-z0-9]*)_(?P<dataset_tag>.+?)"
                          r"_r\d+(?:of\d+)?\.jsonl$")


def _legacy_name_info(basename):
    m = _LEGACY_NAME.match(basename)
    return m.groupdict() if m else {}


def expand(patterns):
    """Sorted files for each glob pattern, de-duplicated, in pattern order; empty globs raise."""
    out, seen = [], set()
    for pat in patterns:
        hits = sorted(glob.glob(pat))
        if not hits:
            raise FileNotFoundError(f"no file matches {pat!r}")
        for f in hits:
            if f not in seen:
                seen.add(f)
                out.append(f)
    return out


def read_rows(patterns, probes=DEFAULT_PROBES, where=None):
    """Generation rows from legacy Study-1 shards or v2 shards (REVISION.md §4), in file order.

    Skips ``_meta`` headers, error markers and rows without a probe.  ``model_tag``, ``editor`` and
    ``dataset_tag`` missing from a row come from the shard header, then from the legacy file name
    (``<model_tag>_<EDITOR>_<dataset>_r<k>[of<n>].jsonl``; BASE shards have no header).  Each row
    gains ``src`` (file basename), ``line`` (0-based line index) and ``schema``.  ``probes=None``
    keeps every probe; ``where`` is a list of ``key=value`` filters on string values.
    """
    conds = [w.split("=", 1) for w in (where or [])]
    rows = []
    for path in expand(patterns):
        base = os.path.basename(path)
        info = _legacy_name_info(base)
        header = {}
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                if d.get("_meta"):
                    header = d
                    continue
                if d.get("error") or not d.get("probe"):
                    continue
                if probes is not None and d["probe"] not in probes:
                    continue
                r = dict(d)
                ds = header.get("dataset") if isinstance(header.get("dataset"), dict) else {}
                for key, hval in (("model_tag", header.get("model_tag")),
                                  ("editor", header.get("editor")),
                                  ("dataset_tag", ds.get("tag"))):
                    if r.get(key) is None:
                        r[key] = hval if hval is not None else info.get(key)
                r.setdefault("decode", "greedy")          # metrics.py: a row without decode is greedy
                if r["decode"] is None:
                    r["decode"] = "greedy"
                r["schema"] = "v2" if ("condition" in d or "chain_end" in d) else "legacy"
                r["src"], r["line"] = base, i
                if all(str(r.get(k)) == v for k, v in conds):
                    rows.append(r)
    return rows


def load_cases(path):
    """CounterFact records by case_id (only the fields the judge needs)."""
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                c = json.loads(line)
                out[c["case_id"]] = {"o_new": c["o_new"], "o_old": c["o_old"], "s": c.get("s") or ""}
    return out


def load_aliases(path=None):
    with open(path or os.path.join(ROOT, "data", "aliases.json"), encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ items

def normalize_text(text):
    """Strip R1 markers and surplus blank lines; the judge never sees the model's format."""
    t = _MARKERS.sub("", text or "")
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def scrub_subject(text, subject, protect=()):
    """Replace word-bounded, case-insensitive mentions of ``subject`` with ``[SUBJECT]``.

    A value in ``protect`` that itself contains the subject (subject "Nintendo", value "Nintendo
    Entertainment") is left intact; a subject that contains a value (subject "Miami Film
    Festival", value "Miami") is still scrubbed whole.  Returns (text, scrubbed?).
    """
    if not text or not subject or len(subject.strip()) < 2:
        return text or "", False
    keep = sorted({p for p in protect if p and subject.lower() in p.lower()}, key=len, reverse=True)
    alts = [f"(?P<k{i}>(?<!\\w){re.escape(p)}(?!\\w))" for i, p in enumerate(keep)]
    alts.append(f"(?P<subj>(?<!\\w){re.escape(subject.strip())}(?!\\w))")
    pat = re.compile("|".join(alts), re.IGNORECASE)
    hit = []

    def repl(m):
        if m.group("subj") is None:
            return m.group(0)
        hit.append(1)
        return SUBJECT_TOKEN

    return pat.sub(repl, text), bool(hit)


def scrub_probe(probe):
    """Probes whose question is about the edited subject (locality asks about a neighbour)."""
    return probe in ("efficacy", "base") or str(probe).startswith("para")


def lexical_flags(answer, o_new, o_old, subject, aliases, scrub):
    """The lexical rule exactly as ``metrics.score`` applies it (subject removed unless locality)."""
    a = metrics._without_subject(answer or "", subject) if scrub else (answer or "")
    hn, ho = bool(metrics.hit(a, o_new, aliases)), bool(metrics.hit(a, o_old, aliases))
    cell = {(True, False): "new-only", (False, True): "old-only",
            (True, True): "both", (False, False): "neither"}[(hn, ho)]
    return {"new_hit": hn, "old_hit": ho, "cell": cell}


def make_item(row, cases, aliases):
    """What the judge sees for ``row``, plus the lexical flags and the content hash ``item``."""
    case = cases.get(row["case_id"])
    if case is None and not (row.get("o_new") and row.get("o_old")):
        raise KeyError(f"case {row['case_id']!r} is not in the cases file and the row carries "
                       f"no o_new/o_old")
    o_new = row.get("o_new") or case["o_new"]
    o_old = row.get("o_old") or case["o_old"]
    scrub = scrub_probe(row.get("probe"))
    subject = ((case or {}).get("s") or "") if scrub else ""
    q_raw, a_raw = row.get("q") or "", row.get("answer") or ""
    item_id = _sha({"v": ITEM_VERSION, "q": q_raw, "answer": a_raw, "new": o_new, "old": o_old,
                    "subject": subject})[:32]
    q, s1 = scrub_subject(normalize_text(q_raw), subject, (o_new, o_old))
    a, s2 = scrub_subject(normalize_text(a_raw), subject, (o_new, o_old))
    truncated = len(a) > MAX_ANSWER_CHARS
    if truncated:
        a = a[:MAX_ANSWER_CHARS].rstrip() + " [...]"
    return {"item": item_id, "question": q, "answer": a, "values": {"NEW": o_new, "OLD": o_old},
            "scrubbed": s1 or s2, "truncated": truncated, "empty": not a.strip(),
            "lexical": lexical_flags(a_raw, o_new, o_old, (case or {}).get("s") or "", aliases,
                                     scrub)}


def option_order(item_id, seed=DEFAULT_SEED):
    """Labels shown as options (A, B): a per-item coin fixed by sha256(seed:item)."""
    bit = hashlib.sha256(f"{seed}:{item_id}".encode()).digest()[0] & 1
    return ("NEW", "OLD") if bit == 0 else ("OLD", "NEW")


def orders_for(item_id, seed=DEFAULT_SEED, orders=1):
    first = option_order(item_id, seed)
    return [first] if orders == 1 else [first, first[::-1]]


def user_message(item, order):
    return USER_TEMPLATE.format(question=item["question"], answer=item["answer"],
                                option_a=item["values"][order[0]],
                                option_b=item["values"][order[1]])


def letters_to_labels(p_letters, order):
    """Map a probability vector over (A, B, C, D) back to NEW/OLD/BOTH_UNCLEAR/NEITHER."""
    return {order[0]: p_letters[0], order[1]: p_letters[1],
            "BOTH_UNCLEAR": p_letters[2], "NEITHER": p_letters[3]}


def decide(p):
    """Argmax label; an exact tie at the top is BOTH_UNCLEAR (a split never counts as OLD)."""
    ranked = sorted(LABELS, key=lambda k: -p[k])
    if p[ranked[0]] == p[ranked[1]]:
        return "BOTH_UNCLEAR"
    return ranked[0]


def verdict_from_scores(item_id, scored, seed, orders):
    """Combine per-order letter scores [(logp[4], mass, sha, n_tok)] into one verdict."""
    order_list = orders_for(item_id, seed, orders)
    p_letter, p_lab = [], {k: 0.0 for k in LABELS}
    for (logp, _, _, _), order in zip(scored, order_list):
        m = max(logp)
        ex = [math.exp(x - m) for x in logp]
        z = sum(ex)
        pl = [e / z for e in ex]
        p_letter.append(pl)
        for k, v in letters_to_labels(pl, order).items():
            p_lab[k] += v / len(order_list)
    label = decide(p_lab)
    top = sorted(p_lab.values(), reverse=True)
    return {"source": "judge", "orders": [list(o) for o in order_list], "p_letter": p_letter,
            "logp_letter": [list(s[0]) for s in scored], "letter_mass": [s[1] for s in scored],
            "render_sha": [s[2] for s in scored], "n_tokens": [s[3] for s in scored],
            "p": p_lab, "label": label, "margin": top[0] - top[1]}


def empty_verdict(item_id, seed, orders):
    """An empty answer asserts nothing: NEITHER without asking the judge."""
    p = {k: 0.0 for k in LABELS}
    p["NEITHER"] = 1.0
    return {"source": "empty", "orders": [list(o) for o in orders_for(item_id, seed, orders)],
            "p_letter": None, "logp_letter": None, "letter_mass": None, "render_sha": None,
            "n_tokens": None, "p": p, "label": "NEITHER", "margin": 1.0}


# ------------------------------------------------------------------ scoring with a model

def letter_token_ids(tokenizer, letters=LETTERS, variants=LETTER_VARIANTS):
    """First-token ids of each letter's spellings; ids shared by several letters are dropped.

    A spelling that tokenizes into several pieces contributes its first piece; " A" in a
    byte-level tokenizer starts with the shared space token and is therefore dropped.
    """
    special = set(getattr(tokenizer, "all_special_ids", None) or [])
    cand = {}
    for L in letters:
        ids = []
        for v in variants:
            toks = [t for t in tokenizer.encode(v.format(L), add_special_tokens=False)
                    if t not in special]
            if toks and toks[0] not in ids:
                ids.append(toks[0])
        cand[L] = ids
    owners = {}
    for L, ids in cand.items():
        for t in ids:
            owners.setdefault(t, set()).add(L)
    out = {L: [t for t in ids if len(owners[t]) == 1] for L, ids in cand.items()}
    empty = [L for L, ids in out.items() if not ids]
    if empty:
        raise ValueError(f"letters {empty} have no token of their own in this tokenizer")
    return out


def _as_ids(x):
    if isinstance(x, dict) or hasattr(x, "keys"):
        x = x["input_ids"]
    if hasattr(x, "tolist"):
        x = x.tolist()
    if x and isinstance(x[0], list):
        x = x[0]
    return [int(t) for t in x]


def render_chat(tokenizer, user_text, system_mode, with_text=True):
    """Token ids (and text) of the chat prompt ending in the generation prompt.

    ``system_mode`` "system" sends SYSTEM as a system turn; "merged" prepends it to the user turn
    (Gemma-2-style templates reject the system role; Gemma 3 merges it the same way itself).
    Mistral-Small-3.1's Jinja template injects a dated default system prompt when none is given,
    which the explicit system turn overrides.
    """
    if system_mode == "system":
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_text}]
    else:
        msgs = [{"role": "user", "content": SYSTEM + "\n\n" + user_text}]
    ids = _as_ids(tokenizer.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True,
                                                return_dict=False))
    if not with_text:
        return ids, None
    text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    if isinstance(text, list):
        text = text[0]
    return ids, text


def pick_system_mode(tokenizer):
    """"system" if the template accepts and keeps a system turn, else "merged"."""
    try:
        _, text = render_chat(tokenizer, "probe", "system")
    except Exception:
        return "merged"
    return "system" if SYSTEM in text else "merged"


def _oom_types():
    import torch
    return tuple({getattr(torch, "OutOfMemoryError", RuntimeError),
                  getattr(torch.cuda, "OutOfMemoryError", RuntimeError)})


class LetterScorer:
    """Next-token letter log-probabilities of a causal LM after the chat template.

    ``encode`` renders one user message; ``score`` runs left-padded batches (sorted by length,
    capped by ``batch_size`` and ``max_batch_tokens``, halved on out-of-memory) with explicit
    position ids, so a padded row scores like the same prompt alone.
    """

    def __init__(self, model, tokenizer, batch_size=32, max_batch_tokens=32768,
                 assistant_prefix="", system_mode=None):
        self.model, self.tok = model, tokenizer
        self.batch_size, self.max_batch_tokens = batch_size, max_batch_tokens
        self.assistant_prefix = assistant_prefix
        self.system_mode = system_mode or pick_system_mode(tokenizer)
        self.letter_ids = letter_token_ids(tokenizer)
        self.prefix_ids = (tokenizer.encode(assistant_prefix, add_special_tokens=False)
                           if assistant_prefix else [])
        pad = getattr(tokenizer, "pad_token_id", None)
        self.pad_id = pad if pad is not None else (getattr(tokenizer, "eos_token_id", None) or 0)
        self.bos_id = getattr(tokenizer, "bos_token_id", None)

    def encode(self, user_text):
        ids, _ = render_chat(self.tok, user_text, self.system_mode, with_text=False)
        if self.bos_id is not None and len(ids) > 1 and ids[0] == ids[1] == self.bos_id:
            ids = ids[1:]
        return ids + self.prefix_ids

    def _device(self):
        return self.model.get_input_embeddings().weight.device

    def _forward(self, batch):
        import torch
        n, L = len(batch), max(len(x) for x in batch)
        ids = torch.full((n, L), self.pad_id, dtype=torch.long)
        att = torch.zeros((n, L), dtype=torch.long)
        for i, x in enumerate(batch):
            ids[i, L - len(x):] = torch.tensor(x, dtype=torch.long)
            att[i, L - len(x):] = 1
        pos = (att.cumsum(-1) - 1).clamp(min=0)
        dev = self._device()
        kw = dict(input_ids=ids.to(dev), attention_mask=att.to(dev), position_ids=pos.to(dev),
                  use_cache=False)
        with torch.inference_mode():
            try:
                out = self.model(**kw, logits_to_keep=1)
            except TypeError:
                out = self.model(**kw)
            logp = torch.log_softmax(out.logits[:, -1, :].float(), dim=-1)
        res = []
        for i in range(n):
            lp = [float(torch.logsumexp(logp[i, self.letter_ids[L]], dim=0)) for L in LETTERS]
            if any(math.isnan(v) for v in lp):
                raise FloatingPointError("NaN letter log-probabilities; rerun with --dtype float32")
            res.append((lp, float(sum(math.exp(v) for v in lp))))
        return res

    def _forward_safe(self, batch):
        try:
            return self._forward(batch)
        except _oom_types():
            if len(batch) == 1:
                raise
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            h = len(batch) // 2
            return self._forward_safe(batch[:h]) + self._forward_safe(batch[h:])

    def score(self, id_lists):
        """[(logp over A..D, letter mass)] aligned with ``id_lists``."""
        order = sorted(range(len(id_lists)), key=lambda i: -len(id_lists[i]))
        out = [None] * len(id_lists)
        i = 0
        while i < len(order):
            L = len(id_lists[order[i]])
            k = max(1, min(self.batch_size, self.max_batch_tokens // max(L, 1)))
            idx = order[i:i + k]
            for j, r in zip(idx, self._forward_safe([id_lists[j] for j in idx])):
                out[j] = r
            i += k
        return out

    def describe(self):
        return {"system_mode": self.system_mode, "letter_ids": self.letter_ids,
                "assistant_prefix": self.assistant_prefix, "prefix_ids": self.prefix_ids}


def load_judge(path, dtype="bfloat16", device_map="auto"):
    """Model and tokenizer for a judge checkpoint (text-only use of multimodal wrappers).

    Gemma 3 loads as Gemma3ForConditionalGeneration through AutoModelForCausalLM; Mistral-Small-3.1
    (``mistral3``) is not in the causal-LM mapping and loads through AutoModelForImageTextToText.
    A tokenizer without ``chat_template`` takes it from the checkpoint's chat_template.jinja/json.
    ``device_map`` "auto" needs accelerate; "cpu"/"cuda"/"cuda:N" load without it.
    """
    import torch
    from transformers import (AutoConfig, AutoModelForCausalLM, AutoModelForImageTextToText,
                              AutoTokenizer)
    from transformers.models.auto.modeling_auto import MODEL_FOR_CAUSAL_LM_MAPPING_NAMES
    tok = AutoTokenizer.from_pretrained(path)
    ensure_chat_template(tok, path)
    cfg = AutoConfig.from_pretrained(path)
    cls = (AutoModelForCausalLM if cfg.model_type in MODEL_FOR_CAUSAL_LM_MAPPING_NAMES
           else AutoModelForImageTextToText)
    place = device_map if device_map not in ("cpu",) and not str(device_map).startswith("cuda") else None
    model = cls.from_pretrained(path, dtype=getattr(torch, dtype), **({"device_map": place} if place else {}))
    if place is None:
        model.to(device_map)
    model.eval()
    return model, tok


def ensure_chat_template(tok, path):
    """Fill a missing Jinja chat template from the checkpoint directory; returns its source."""
    if "MistralCommon" in type(tok).__name__:
        return "mistral-common"
    if getattr(tok, "chat_template", None):
        return "tokenizer"
    for name, key in (("chat_template.jinja", None), ("chat_template.json", "chat_template")):
        p = os.path.join(path, name)
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                tok.chat_template = f.read() if key is None else json.load(f)[key]
            return name
    raise ValueError(f"{path}: tokenizer has no chat template")


# ------------------------------------------------------------------ provenance

_TOKENIZER_FILES = ("tokenizer.json", "tokenizer_config.json", "tokenizer.model", "tekken.json",
                    "special_tokens_map.json", "chat_template.jinja", "chat_template.json",
                    "added_tokens.json", "vocab.json", "merges.txt")


def _file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tokenizer_sha(tok, path=None):
    """Hash of the tokenizer files in ``path`` if any, else of the in-memory vocab and template."""
    if path and os.path.isdir(path):
        files = [n for n in _TOKENIZER_FILES if os.path.isfile(os.path.join(path, n))]
        if files:
            return {"kind": "files", "files": files,
                    "sha": _sha({n: _file_sha(os.path.join(path, n)) for n in files})}
    vocab = sorted(tok.get_vocab().items())
    return {"kind": "vocab", "sha": _sha({"class": type(tok).__name__, "vocab": vocab,
                                         "special": {k: str(v) for k, v in
                                                     (tok.special_tokens_map or {}).items()},
                                         "chat_template": getattr(tok, "chat_template", None)})}


def config_sha(model, path=None):
    p = os.path.join(path, "config.json") if path else None
    if p and os.path.isfile(p):
        return {"kind": "file", "sha": _file_sha(p)}
    d = model.config.to_dict()
    for k in ("_name_or_path", "transformers_version", "torch_dtype", "dtype"):
        d.pop(k, None)
    return {"kind": "dict", "sha": _sha(d)}


def hf_revision(path):
    """Commit and weight fingerprint from ``hf download --local-dir`` metadata or a cache path."""
    rev, etags = None, {}
    meta_dir = os.path.join(path or "", ".cache", "huggingface", "download")
    if path and os.path.isdir(meta_dir):
        for name in sorted(os.listdir(meta_dir)):
            if name.endswith(".metadata"):
                with open(os.path.join(meta_dir, name)) as f:
                    lines = f.read().split("\n")
                rev = rev or (lines[0].strip() or None)
                if name.endswith(".safetensors.metadata") and len(lines) > 1:
                    etags[name[:-len(".metadata")]] = lines[1].strip()
    m = re.search(r"/snapshots/([0-9a-f]{40})", os.path.realpath(path or ""))
    if m and not rev:
        rev = m.group(1)
    return {"revision": rev, "weights_etag_sha": _sha(etags) if etags else None,
            "n_weight_files": len(etags) or None}


def _git():
    try:
        head = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True,
                              text=True, timeout=10).stdout.strip() or None
        dirty = subprocess.run(["git", "-C", ROOT, "status", "--porcelain", "--untracked-files=no"], capture_output=True,
                               text=True, timeout=10).stdout.strip()
        return {"head": head, "dirty": bool(dirty)}
    except Exception:
        return {"head": None, "dirty": None}


def code_sha():
    here = os.path.dirname(os.path.abspath(__file__))
    return _sha({n: _file_sha(p) for n, p in (("judge.py", os.path.join(here, "judge.py")),
                                               ("metrics.py", os.path.abspath(metrics.__file__)))})


def judge_identity(model, tok, path, dtype=None, device_map=None):
    """Who the judge is: path, class, config/tokenizer/template hashes, revision, versions."""
    import torch
    import transformers
    tmpl = getattr(tok, "chat_template", None)
    return {"path": path, "realpath": os.path.realpath(path) if path else None,
            "model_class": type(model).__name__, "tokenizer_class": type(tok).__name__,
            "config": config_sha(model, path), "tokenizer": tokenizer_sha(tok, path),
            "chat_template_sha": _sha(tmpl) if isinstance(tmpl, str) else None,
            "template_uses_strftime": bool(isinstance(tmpl, str) and "strftime_now" in tmpl),
            "hf": hf_revision(path), "dtype": dtype, "device_map": device_map,
            "n_params": sum(p.numel() for p in model.parameters()),
            "torch": torch.__version__, "transformers": transformers.__version__}


def make_header(identity, scorer_desc, seed, orders):
    return {"_meta": True, "format": FORMAT, "judge": identity, "scorer": scorer_desc,
            "prompt": {"version": PROMPT_VERSION, "sha": prompt_sha(), "system": SYSTEM,
                       "user_template": USER_TEMPLATE},
            "seed": seed, "orders": orders, "item_version": ITEM_VERSION, "code_sha": code_sha(),
            "git": _git(), "python": sys.version.split()[0],
            "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def compat_view(header):
    """Header fields that must match for a run to append to an existing output."""
    j, s = header.get("judge") or {}, header.get("scorer") or {}
    return {"format": header.get("format"), "prompt": (header.get("prompt") or {}).get("sha"),
            "seed": header.get("seed"), "orders": header.get("orders"),
            "item_version": header.get("item_version"),
            "config": (j.get("config") or {}).get("sha"),
            "tokenizer": (j.get("tokenizer") or {}).get("sha"),
            "chat_template": j.get("chat_template_sha"), "dtype": j.get("dtype"),
            "system_mode": s.get("system_mode"), "letter_ids": s.get("letter_ids"),
            "assistant_prefix": s.get("assistant_prefix")}


# ------------------------------------------------------------------ run

def row_identity(row):
    return {k: row.get(k) for k in IDENTITY_FIELDS if row.get(k) is not None}


def row_key(row, item_id):
    return _sha({"item": item_id, "row": row_identity(row)})[:32]


def _read_jsonl_tolerant(path, repair=False):
    """Records of an output file, ignoring a torn last line (a job killed mid-write).

    With ``repair`` the torn line is cut off the file and a missing final newline is added, so
    the next append starts on a fresh line.  A bad line followed by good ones raises.
    """
    with open(path, "rb") as f:
        data = f.read()
    out, pos = [], 0
    while pos < len(data):
        nl = data.find(b"\n", pos)
        end = len(data) if nl < 0 else nl + 1
        raw = data[pos:end].strip()
        if raw:
            try:
                out.append(json.loads(raw))
            except json.JSONDecodeError:
                if data[end:].strip():
                    raise ValueError(f"{path}: corrupt line at byte {pos}") from None
                if repair:
                    with open(path, "r+b") as f:
                        f.truncate(pos)
                return out
        pos = end
    if repair and data and not data.endswith(b"\n"):
        with open(path, "ab") as f:
            f.write(b"\n")
    return out


def _resume(out_path, header):
    if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        return set(), {}, True
    recs = _read_jsonl_tolerant(out_path, repair=True)
    if not recs or not recs[0].get("_meta"):
        raise ValueError(f"{out_path}: no provenance header; refusing to append")
    old, new = compat_view(recs[0]), compat_view(header)
    diff = sorted(k for k in new if old.get(k) != new.get(k))
    if diff:
        raise ValueError(f"{out_path}: judge/prompt settings differ from the existing file "
                         f"({', '.join(diff)}); write to a new file")
    done, cache = set(), {}
    keep = ("source", "orders", "p_letter", "logp_letter", "letter_mass", "render_sha",
            "n_tokens", "p", "label", "margin")
    for r in recs[1:]:
        if "row_key" in r:
            done.add(r["row_key"])
            cache.setdefault(r["item"], {k: r.get(k) for k in keep})
    return done, cache, False


def _out_line(row, item, verdict):
    return {"row_key": row_key(row, item["item"]), "item": item["item"], "row": row_identity(row),
            "values": item["values"], "lexical": item["lexical"], "scrubbed": item["scrubbed"],
            "truncated": item["truncated"], **verdict,
            "strict_semantic_es": int(verdict["label"] == "NEW"),
            "semantic_reversion": int(verdict["label"] == "OLD")}


def judge_rows(rows, cases, aliases, scorer, out_path, header, chunk=256, log=print):
    """Judge ``rows`` into ``out_path`` (append/resume); returns counts of work done."""
    seed, orders = header["seed"], header["orders"]
    done, cache, fresh = _resume(out_path, header)
    todo, keys = [], set()
    for r in rows:
        it = make_item(r, cases, aliases)
        k = row_key(r, it["item"])
        keys.add(k)
        if k not in done:
            todo.append((r, it))
    stats = {"rows_total": len(rows), "rows_done_before": len(rows) - len(todo),
             "rows_written": 0, "items_scored": 0, "prompts_scored": 0, "items_cached": 0,
             "stale_rows_in_file": len(done - keys)}
    if stats["stale_rows_in_file"] and log:
        log(f"# WARNING {out_path}: {stats['stale_rows_in_file']} judged rows are not among the "
            f"current inputs (regenerated shard?); aggregate from a fresh output file")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    t0 = time.time()
    with open(out_path, "a", encoding="utf-8") as f:
        if fresh:
            f.write(json.dumps(header, ensure_ascii=False) + "\n")
        f.write(json.dumps({"_run": True, "created": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                                   time.gmtime()),
                            "rows": len(rows), "todo": len(todo), "git": _git()}) + "\n")
        f.flush()
        for start in range(0, len(todo), chunk):
            part = todo[start:start + chunk]
            need, seen = [], set()
            for _, it in part:
                if it["item"] in cache or it["item"] in seen:
                    continue
                seen.add(it["item"])
                if it["empty"]:
                    cache[it["item"]] = empty_verdict(it["item"], seed, orders)
                else:
                    need.append(it)
            prompts, owner = [], []
            for it in need:
                for o in orders_for(it["item"], seed, orders):
                    prompts.append(scorer.encode(user_message(it, o)))
                    owner.append(it["item"])
            scored = scorer.score(prompts) if prompts else []
            by_item = {}
            for iid, ids, (lp, mass) in zip(owner, prompts, scored):
                by_item.setdefault(iid, []).append((lp, mass, _sha(ids)[:16], len(ids)))
            for it in need:
                cache[it["item"]] = verdict_from_scores(it["item"], by_item[it["item"]], seed,
                                                        orders)
            stats["items_scored"] += len(need)
            stats["prompts_scored"] += len(prompts)
            stats["items_cached"] += len(part) - len(need)
            for r, it in part:
                f.write(json.dumps(_out_line(r, it, cache[it["item"]]), ensure_ascii=False) + "\n")
            f.flush()
            stats["rows_written"] += len(part)
            if log:
                el = time.time() - t0
                log(f"# {stats['rows_written']}/{len(todo)} rows, {stats['items_scored']} items "
                    f"scored, {el:.0f}s ({stats['prompts_scored'] / max(el, 1e-9):.1f} prompts/s)")
    return stats


def read_judged(patterns):
    """(headers, rows) of one judge's output files; later duplicates of a row_key are dropped."""
    headers, rows, seen = [], [], set()
    for path in expand(patterns):
        recs = _read_jsonl_tolerant(path)
        if recs and recs[0].get("_meta"):
            headers.append(recs[0])
        for r in recs:
            if "row_key" in r and r["row_key"] not in seen:
                seen.add(r["row_key"])
                rows.append(r)
    views = {json.dumps(compat_view(h), sort_keys=True) for h in headers}
    if len(views) > 1:
        raise ValueError(f"{patterns}: files come from different judge settings")
    return headers, rows


# ------------------------------------------------------------------ aggregation

def combine_judges(judged, allow_partial=False):
    """Ensemble of several judges' rows ({name: rows}) by averaging their label probabilities.

    Returns rows shaped like single-judge rows (``p``, ``label``, endpoint flags) plus
    ``by_judge``; rows missing from any judge raise unless ``allow_partial``.
    """
    names = list(judged)
    maps = {n: {r["row_key"]: r for r in judged[n]} for n in names}
    keys = [r["row_key"] for r in judged[names[0]]]
    missing = [k for k in keys if any(k not in maps[n] for n in names[1:])]
    extra = sum(1 for n in names[1:] for k in maps[n] if k not in maps[names[0]])
    if (missing or extra) and not allow_partial:
        raise ValueError(f"judges cover different rows ({len(missing)} missing, {extra} extra)")
    out = []
    for k in keys:
        if any(k not in maps[n] for n in names):
            continue
        rs = [maps[n][k] for n in names]
        p = {lab: sum(r["p"][lab] for r in rs) / len(rs) for lab in LABELS}
        label = decide(p)
        base = {x: rs[0][x] for x in ("row_key", "item", "row", "values", "lexical")}
        out.append({**base, "p": p, "label": label,
                    "by_judge": {n: {"label": r["label"], "p": r["p"]} for n, r in zip(names, rs)},
                    "split": len({r["label"] for r in rs}) > 1,
                    "strict_semantic_es": int(label == "NEW"),
                    "semantic_reversion": int(label == "OLD")})
    return out


def _group(row, keys):
    return json.dumps([row["row"].get(k) for k in keys])


def _ordered(rows):
    return sorted(rows, key=lambda r: (r["row"].get("src") or "", r["row"].get("line") or 0))


def semantic_by_case(rows, group_keys=GROUP_KEYS):
    """Per-case indicators for bootstrap, gated like ``metrics._indicators_by_case``.

    Returns {group: {"es": {b: {cid: [0/1]}}, "rev": {b: {cid: [0/1]}}, "es_first": {cid: {b: 0/1}},
    "b0ok": {cid: bool}}}.  ``rev`` is 1{OLD} over efficacy rows of cases whose first B0
    efficacy row is NEW; ``es_first`` uses each budget's first row (``metrics._es_by_case``).
    """
    by = {}
    for r in _ordered(rows):
        if r["row"].get("probe") != "efficacy":
            continue
        g = by.setdefault(_group(r, group_keys), {})
        g.setdefault(r["row"]["case_id"], {}).setdefault(r["row"]["budget"], []).append(r)
    out = {}
    for g, cases in by.items():
        es, rev, first, gate = {}, {}, {}, {}
        for cid, buds in cases.items():
            b0 = buds.get("B0", [])
            ok = bool(b0) and b0[0]["label"] == "NEW"
            gate[cid] = ok
            for b, rs in buds.items():
                es.setdefault(b, {})[cid] = [int(r["label"] == "NEW") for r in rs]
                first.setdefault(cid, {})[b] = int(rs[0]["label"] == "NEW")
                if ok:
                    rev.setdefault(b, {})[cid] = [int(r["label"] == "OLD") for r in rs]
        out[g] = {"es": es, "rev": rev, "es_first": first, "b0ok": gate}
    return out


def semantic_score(rows, group_keys=GROUP_KEYS):
    """Semantic and lexical endpoints per condition and budget, with ``metrics.score`` gating.

    Semantic: ES = P(NEW) and RR = P(OLD | first B0 efficacy row NEW) on efficacy rows;
    PS = P(NEW) on para rows; Loc = P(not NEW) and Loc_correct = P(OLD) on locality rows (a
    CounterFact neighbour's true value is the old value).  ``rates`` gives the four-label shares
    per probe (e.g. ``base``).  ``lex`` recomputes metrics.score's ES/RR/RRs/PS/Loc from the
    stored lexical flags, so both endpoints come from the same rows.
    """
    groups = {}
    for r in _ordered(rows):
        g = groups.setdefault(_group(r, group_keys), {})
        g.setdefault(r["row"]["case_id"], []).append(r)
    rate = lambda a, b: (a / b if b else None)  # noqa: E731
    out = {}
    for g, cases in groups.items():
        acc = {}
        for rs in cases.values():
            b0 = [r for r in rs if r["row"].get("probe") == "efficacy"
                  and r["row"].get("budget") == "B0"]
            ok_sem = bool(b0) and b0[0]["label"] == "NEW"
            ok_lex = bool(b0) and b0[0]["lexical"]["new_hit"] and not b0[0]["lexical"]["old_hit"]
            for r in rs:
                b, probe, lab, lx = r["row"]["budget"], r["row"]["probe"], r["label"], r["lexical"]
                a = acc.setdefault(b, {"n": 0, "es": 0, "rr_n": 0, "rr": 0, "n_para": 0, "ps": 0,
                                       "n_loc": 0, "loc": 0, "loc_ok": 0, "rates": {},
                                       "lex": {"es": 0, "rr_n": 0, "rr": 0, "rrs": 0, "ps": 0,
                                               "loc": 0}})
                rt = a["rates"].setdefault(probe, {k: 0 for k in LABELS + ("n",)})
                rt[lab] += 1
                rt["n"] += 1
                if probe == "efficacy":
                    a["n"] += 1
                    a["es"] += lab == "NEW"
                    a["lex"]["es"] += lx["new_hit"] and not lx["old_hit"]
                    if ok_sem:
                        a["rr_n"] += 1
                        a["rr"] += lab == "OLD"
                    if ok_lex:
                        a["lex"]["rr_n"] += 1
                        a["lex"]["rr"] += lx["old_hit"]
                        a["lex"]["rrs"] += lx["old_hit"] and not lx["new_hit"]
                elif str(probe).startswith("para"):
                    a["n_para"] += 1
                    a["ps"] += lab == "NEW"
                    a["lex"]["ps"] += lx["new_hit"] and not lx["old_hit"]
                elif probe == "locality":
                    a["n_loc"] += 1
                    a["loc"] += lab != "NEW"
                    a["loc_ok"] += lab == "OLD"
                    a["lex"]["loc"] += not lx["new_hit"]
        res = {}
        for b, a in sorted(acc.items()):
            lx = a["lex"]
            res[b] = {"ES": rate(a["es"], a["n"]), "RR": rate(a["rr"], a["rr_n"]),
                      "PS": rate(a["ps"], a["n_para"]), "Loc": rate(a["loc"], a["n_loc"]),
                      "Loc_correct": rate(a["loc_ok"], a["n_loc"]),
                      "n": a["n"], "rr_n": a["rr_n"], "n_para": a["n_para"], "n_loc": a["n_loc"],
                      "rates": {p: {k: rate(v[k], v["n"]) for k in LABELS} | {"n": v["n"]}
                                for p, v in a["rates"].items()},
                      "lex": {"ES": rate(lx["es"], a["n"]), "RR": rate(lx["rr"], lx["rr_n"]),
                              "RRs": rate(lx["rrs"], lx["rr_n"]), "rr_n": lx["rr_n"],
                              "PS": rate(lx["ps"], a["n_para"]), "Loc": rate(lx["loc"], a["n_loc"])}}
        out[g] = res
    return {"group_keys": list(group_keys), "groups": out}


def order_consistency(rows):
    """Share of two-order items whose per-order argmax labels agree (position-bias check)."""
    seen, agree, n = set(), 0, 0
    for r in rows:
        if r.get("source") != "judge" or r["item"] in seen or len(r.get("orders") or []) < 2:
            continue
        seen.add(r["item"])
        labs = [decide(letters_to_labels(pl, o)) for pl, o in zip(r["p_letter"], r["orders"])]
        n += 1
        agree += len(set(labs)) == 1
    return {"items": n, "agree": (agree / n) if n else None}


# ------------------------------------------------------------------ CLI

def _rows_and_items(args):
    probes = None if args.probes == "all" else tuple(args.probes.split(","))
    rows = read_rows(args.rows, probes=probes, where=args.where)
    if getattr(args, "shard", None):
        k, n = (int(x) for x in args.shard.split("/"))
        cases = load_cases(args.cases)
        aliases = load_aliases(args.aliases)
        rows = [r for r in rows
                if int(row_key(r, make_item(r, cases, aliases)["item"])[:8], 16) % n == k]
    if getattr(args, "limit", None):
        rows = rows[:args.limit]
    return rows


def _add_row_args(p):
    p.add_argument("--rows", action="append", required=True,
                   help="glob of generation shards (legacy Study-1 or v2); repeatable")
    p.add_argument("--cases", default=os.path.join(ROOT, "data", "counterfact.jsonl"))
    p.add_argument("--aliases", default=os.path.join(ROOT, "data", "aliases.json"))
    p.add_argument("--probes", default=",".join(DEFAULT_PROBES), help="comma list or 'all'")
    p.add_argument("--where", action="append", default=[], help="key=value row filter")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--orders", type=int, choices=(1, 2), default=1)


def cmd_run(args):
    rows = _rows_and_items(args)
    cases, aliases = load_cases(args.cases), load_aliases(args.aliases)
    model, tok = load_judge(args.model, args.dtype, args.device_map)
    scorer = LetterScorer(model, tok, args.batch_size, args.max_batch_tokens, args.assistant_prefix)
    header = make_header(judge_identity(model, tok, args.model, args.dtype, args.device_map),
                         scorer.describe(), args.seed, args.orders)
    header["inputs"] = {"rows": [os.path.basename(f) for f in expand(args.rows)],
                        "rows_sha": {os.path.basename(f): _file_sha(f) for f in expand(args.rows)},
                        "cases_sha": _file_sha(args.cases), "probes": args.probes,
                        "where": args.where, "shard": args.shard}
    stats = judge_rows(rows, cases, aliases, scorer, args.out, header, chunk=args.chunk)
    print(json.dumps(stats))


def cmd_show(args):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(args.model)
    src = ensure_chat_template(tok, args.model)
    rows = _rows_and_items(args)
    cases, aliases = load_cases(args.cases), load_aliases(args.aliases)
    mode = pick_system_mode(tok)
    lens = []
    items = [make_item(r, cases, aliases) for r in rows]
    for k, it in enumerate(items):
        ids, text = render_chat(tok, user_message(it, option_order(it["item"], args.seed)), mode)
        lens.append(len(ids))
        if k < args.n:
            print(f"===== item {it['item']} (order {option_order(it['item'], args.seed)})")
            print(text)
    lens.sort()
    ids = letter_token_ids(tok)
    print(json.dumps({"chat_template_source": src, "system_mode": mode, "letter_ids": ids,
                      "letter_tokens": {L: tok.convert_ids_to_tokens(v) for L, v in ids.items()},
                      "prompts": len(lens), "tokens_total": sum(lens),
                      "tokens_p50": lens[len(lens) // 2] if lens else None,
                      "tokens_max": lens[-1] if lens else None}, ensure_ascii=False, indent=1))


def cmd_selfcheck(args):
    rows = _rows_and_items(args)[:args.n]
    cases, aliases = load_cases(args.cases), load_aliases(args.aliases)
    model, tok = load_judge(args.model, args.dtype, args.device_map)
    scorer = LetterScorer(model, tok, args.batch_size, args.max_batch_tokens, args.assistant_prefix)
    items = [make_item(r, cases, aliases) for r in rows]
    prompts = [scorer.encode(user_message(it, option_order(it["item"], args.seed))) for it in items]
    t0 = time.time()
    batched = scorer.score(prompts)
    dt = time.time() - t0
    single = [scorer._forward([p])[0] for p in prompts]
    flips, dmax = 0, 0.0
    for it, a, b in zip(items, batched, single):
        va = verdict_from_scores(it["item"], [(a[0], a[1], "", 0)], args.seed, 1)
        vb = verdict_from_scores(it["item"], [(b[0], b[1], "", 0)], args.seed, 1)
        flips += va["label"] != vb["label"]
        dmax = max(dmax, max(abs(va["p"][k] - vb["p"][k]) for k in LABELS))
    mass = sorted(m for _, m in batched)
    print(json.dumps({"n": len(items), "label_flips_batch_vs_single": flips,
                      "max_abs_dp": dmax, "letter_mass_min": mass[0],
                      "letter_mass_p10": mass[len(mass) // 10], "letter_mass_p50": mass[len(mass) // 2],
                      "prompts_per_s_batched": len(items) / max(dt, 1e-9),
                      "scorer": scorer.describe()}, indent=1))


def cmd_score(args):
    judged = {}
    for spec in args.judged:
        name, pat = spec.split("=", 1)
        judged[name] = read_judged([pat])[1]
    rows = judged[next(iter(judged))] if len(judged) == 1 else combine_judges(judged, args.allow_partial)
    keys = tuple(args.group_keys.split(",")) if args.group_keys else GROUP_KEYS
    out = semantic_score(rows, keys)
    out["order_consistency"] = {n: order_consistency(rs) for n, rs in judged.items()}
    if len(judged) > 1:
        out["split_rate"] = sum(r["split"] for r in rows) / max(len(rows), 1)
    for g, bud in out["groups"].items():
        for b, m in bud.items():
            if m["n"]:
                fmt = lambda x: "  -  " if x is None else f"{x:.3f}"  # noqa: E731
                print(f"{g} {b}: ES {fmt(m['ES'])} (lex {fmt(m['lex']['ES'])})  RR {fmt(m['RR'])} "
                      f"(lex RRs {fmt(m['lex']['RRs'])}, RR {fmt(m['lex']['RR'])})  n={m['n']}")
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(out, f, indent=1)


def main(argv=None):
    from rt.precision import strict_fp32
    strict_fp32()                     # TF32 off: fp32 edits, sums and RoPE positions stay exact
    ap = argparse.ArgumentParser(prog="rt.judge", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("run", cmd_run), ("show", cmd_show), ("selfcheck", cmd_selfcheck)):
        p = sub.add_parser(name)
        _add_row_args(p)
        p.add_argument("--model", required=True, help="judge checkpoint (local dir or hub id)")
        p.set_defaults(fn=fn)
        if name != "show":
            p.add_argument("--dtype", default="bfloat16")
            p.add_argument("--device-map", default="auto")
            p.add_argument("--batch-size", type=int, default=32)
            p.add_argument("--max-batch-tokens", type=int, default=32768)
            p.add_argument("--assistant-prefix", default="")
        if name == "run":
            p.add_argument("--out", required=True)
            p.add_argument("--chunk", type=int, default=256)
            p.add_argument("--shard", default=None, help="k/n: judge rows whose key hash %% n == k")
        else:
            p.add_argument("--n", type=int, default=3 if name == "show" else 64)
    p = sub.add_parser("score")
    p.add_argument("--judged", action="append", required=True, help="name=glob; repeat per judge")
    p.add_argument("--group-keys", default=None)
    p.add_argument("--allow-partial", action="store_true")
    p.add_argument("--out", default=None)
    p.set_defaults(fn=cmd_score)
    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
