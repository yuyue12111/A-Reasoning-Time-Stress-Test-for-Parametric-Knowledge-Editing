"""easyedit_qwen2_loader 单测（方案 A monkeypatch，sumandplan1 §6.1-①）。

全 stub transformers + easyeditor.editors.editor，**无 GPU / 无 transformers**，system python3 即可跑
（与其它 mock 测一致）。三类断言：
  (1) 剥 kwarg     —— patched model.from_pretrained 收到 fp32 也不透传给真 loader
                      （真 loader 见 fp32 即 TypeError，复刻 Qwen2 标准架构的真实报错）。
  (2) eos 校正     —— patched tokenizer 丢弃 eos/pad/unk='<|endoftext|>' 覆盖 → 原生真 eos 保留、pad==eos。
  (3) 两段 padding —— 包装返回真 tokenizer 实例（类型不变）→ editor.py L132/L135 的 isinstance 门控
                      两段（ROME 族 right / 非 ROME 族 left）都仍按预期解析。
运行：python3 src/vendor_patches/test_qwen2_loader.py
"""
import sys, os, types

REAL_EOS = "<｜end▁of▁sentence｜>"   # R1-Distill 原生真 eos（全角竖线 U+FF5C）
NAME = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"

# ============ stub transformers（必须在 import patch 之前装好）============
class _FakePreTrainedTokenizerFast:                  # 代表 editor.py isinstance 门控里的 AR tokenizer 类
    pass


class _FakeTok(_FakePreTrainedTokenizerFast):
    def __init__(self):
        self.eos_token = REAL_EOS                    # 原生真 eos（drop 掉覆盖后应保留）
        self.eos_token_id = 151643
        self.pad_token = None
        self.unk_token = None
        self.padding_side = "left"


class _FakeAutoTokenizer:
    last_kwargs = None
    @staticmethod
    def from_pretrained(name, *a, **kw):
        _FakeAutoTokenizer.last_kwargs = dict(kw)
        t = _FakeTok()
        for k in ("eos_token", "pad_token", "unk_token"):   # 模拟 HF：传了 override 才覆盖
            if k in kw:                                       # （patch 若没剥，这里会把 eos 改坏 → 测 (2) 抓到）
                setattr(t, k, kw[k])
        return t


class _FakeModel:
    def __init__(self, kw): self.init_kwargs = kw


class _FakeAutoModel:
    last_kwargs = None
    @staticmethod
    def from_pretrained(name, *a, **kw):
        if "fp32" in kw:                             # 复刻 Qwen2 标准架构：fp32 未知 kwarg → TypeError
            raise TypeError("unexpected keyword argument 'fp32'")
        _FakeAutoModel.last_kwargs = dict(kw)
        return _FakeModel(dict(kw))


_tf = types.ModuleType("transformers")
_tf.AutoModelForCausalLM = _FakeAutoModel
_tf.AutoTokenizer = _FakeAutoTokenizer
_tf.PreTrainedTokenizerFast = _FakePreTrainedTokenizerFast
sys.modules["transformers"] = _tf

# ============ stub easyeditor.editors.editor（apply() 要 patch 它）============
_ed = types.ModuleType("easyeditor.editors.editor")
_ed.AutoModelForCausalLM = _FakeAutoModel          # editor.py:9 import 进来的名字
_ed.AutoTokenizer = _FakeAutoTokenizer
_eds = types.ModuleType("easyeditor.editors"); _eds.editor = _ed
_ee = types.ModuleType("easyeditor"); _ee.editors = _eds
sys.modules["easyeditor"] = _ee
sys.modules["easyeditor.editors"] = _eds
sys.modules["easyeditor.editors.editor"] = _ed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import easyedit_qwen2_loader as P  # noqa: E402


# ============ editor.py L132-137 padding_side 决策（逐字复刻，用于测 (3)）============
ROME_FAMILY = {"ROME", "MEMIT", "EMMET", "R-ROME", "AlphaEdit", "CORE", "SPHERE"}
AR_TOK_TYPES = (_FakePreTrainedTokenizerFast,)     # editor.py 实为 (GPT2*, Llama*, PreTrainedTokenizerFast)


def _editor_padding_side(tok, model_name, alg_name):
    name, side = model_name.lower(), None
    if isinstance(tok, AR_TOK_TYPES) and alg_name not in ROME_FAMILY:          # L132-134
        side = "left"
    if (("mistral" in name or "llama" in name or "qwen" in name)
            and alg_name in ROME_FAMILY):                                       # L135-137
        side = "right"
    return side


# ============ 测试 ============
def test_apply_swaps_module_attrs_idempotent():
    ed = P.apply()
    assert ed.AutoModelForCausalLM is P.PatchedAutoModelForCausalLM
    assert ed.AutoTokenizer is P.PatchedAutoTokenizer
    P.apply()                                        # 幂等：再调一次不炸、仍是 patched
    assert ed.AutoModelForCausalLM is P.PatchedAutoModelForCausalLM


def test_model_strips_fp32_and_forces_bf16():
    # 复刻 editor.py L123：qwen 老分支传 fp32=False + torch_dtype(fp32/fp16)；不打补丁会 TypeError
    P.PatchedAutoModelForCausalLM.from_pretrained(
        NAME, fp32=False, trust_remote_code=True, torch_dtype="float32", device_map=None)
    assert "fp32" not in _FakeAutoModel.last_kwargs, "fp32 应被剥掉"
    assert "torch_dtype" not in _FakeAutoModel.last_kwargs, "editor 的旧 torch_dtype 应被去掉"
    assert _FakeAutoModel.last_kwargs["dtype"] == "bfloat16", "应强制原生 bf16（24G 卡免 OOM）"
    assert _FakeAutoModel.last_kwargs["trust_remote_code"] is True, "其它 kwarg 应透传"
    assert _FakeAutoModel.last_kwargs["device_map"] is None, "其它 kwarg 应透传"


def test_tokenizer_drops_eos_override_and_sets_pad():
    # 复刻 editor.py L124：传错误的 <|endoftext|> 覆盖
    tok = P.PatchedAutoTokenizer.from_pretrained(
        NAME, eos_token="<|endoftext|>", pad_token="<|endoftext|>",
        unk_token="<|endoftext|>", trust_remote_code=True)
    for k in ("eos_token", "pad_token", "unk_token"):
        assert k not in _FakeAutoTokenizer.last_kwargs, f"{k} 覆盖应被丢弃"
    assert _FakeAutoTokenizer.last_kwargs["trust_remote_code"] is True, "真 kwarg 应透传"
    assert tok.eos_token == REAL_EOS, f"原生真 eos 应保留, 得 {tok.eos_token!r}"
    assert tok.pad_token == REAL_EOS, "pad 应设回真 eos"


def test_tokenizer_type_preserved_two_padding_branches():
    tok = P.PatchedAutoTokenizer.from_pretrained(NAME)
    assert isinstance(tok, _tf.PreTrainedTokenizerFast), "包装应返回真 tokenizer 实例(类型不变)"
    # 两段 padding 语义都按 editor.py 解析（ROME 族 right / 非 ROME 族 left）
    assert _editor_padding_side(tok, NAME, "ROME") == "right", "ROME 族 qwen → right"
    assert _editor_padding_side(tok, NAME, "MEMIT") == "right", "MEMIT 族 qwen → right"
    assert _editor_padding_side(tok, NAME, "FT") == "left", "非 ROME 族 AR tok → left"


TESTS = [test_apply_swaps_module_attrs_idempotent, test_model_strips_fp32_and_forces_bf16,
         test_tokenizer_drops_eos_override_and_sets_pad,
         test_tokenizer_type_preserved_two_padding_branches]


def _main():
    fails = 0
    for t in TESTS:
        try:
            t(); print(f"  [PASS] {t.__name__}")
        except AssertionError as e:
            fails += 1; print(f"  [FAIL] {t.__name__}: {e}")
    print("ALL PASS" if fails == 0 else f"FAILED ({fails})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(_main())
