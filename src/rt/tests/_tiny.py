"""Tiny random Qwen2 model and R1-shaped tokenizer for CPU tests of engine v2.

No downloads, fp32, deterministic.  ``tiny_tokenizer`` is byte-level (exact text round trip) and
carries the DeepSeek-R1 special tokens with the same roles: full-width-bar role markers,
``<think>``/``</think>`` as added non-special tokens, and a real EOS/BOS.
"""
import torch
from transformers import Qwen2Config, Qwen2ForCausalLM

MODULE_TMP = "model.layers.{}.mlp.down_proj"
R1_ADDED = ["<｜User｜>", "<｜Assistant｜>", "<think>", "</think>"]
BOS, EOS, PAD = "<｜begin▁of▁sentence｜>", "<｜end▁of▁sentence｜>", "<pad>"


def tiny_tokenizer():
    from tokenizers import Tokenizer, decoders, models, pre_tokenizers
    from transformers import PreTrainedTokenizerFast
    alphabet = sorted(pre_tokenizers.ByteLevel.alphabet())
    core = Tokenizer(models.BPE(vocab={ch: i for i, ch in enumerate(alphabet)}, merges=[]))
    core.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=False)
    core.decoder = decoders.ByteLevel()
    tok = PreTrainedTokenizerFast(tokenizer_object=core, bos_token=BOS, eos_token=EOS,
                                  pad_token=PAD)
    tok.add_tokens(R1_ADDED)
    tok.padding_side = "left"
    return tok


def tiny_model(seed=0, vocab=64, layers=2):
    torch.manual_seed(seed)
    cfg = Qwen2Config(vocab_size=vocab, hidden_size=32, intermediate_size=48,
                      num_hidden_layers=layers, num_attention_heads=4, num_key_value_heads=2,
                      max_position_embeddings=256, tie_word_embeddings=False)
    model = Qwen2ForCausalLM(cfg).eval()
    for p in model.parameters():
        p.requires_grad_(False)
    return model


def rank1_edit(model, layer, seed, scale=0.5):
    """A random rank-1 edit {layer: (A, B)} that fits the model's down_proj at ``layer``."""
    w = model.get_submodule(MODULE_TMP.format(layer)).weight
    g = torch.Generator().manual_seed(seed)
    A = torch.randn(1, w.shape[1], generator=g) * scale
    B = torch.randn(w.shape[0], 1, generator=g) * scale
    return {layer: (A, B)}


def merged_copy(model, edit, alpha=1.0):
    """Deep copy of ``model`` with ``edit`` written into the weights."""
    import copy
    m = copy.deepcopy(model)
    for layer, (A, B) in edit.items():
        w = m.get_submodule(MODULE_TMP.format(layer)).weight
        w += alpha * (B @ A)
    return m
