"""EasyEdit qwen 加载分支修复（方案 A：模块属性级 monkeypatch，不动只读 source/）。

详细机理见 sumandplan1.md §5 / src/vendor_patches/README.md §2 / analysis/01_easyedit.md。

问题：`source/EasyEdit/easyeditor/editors/editor.py` 的 if/elif 链按 model_name 子串路由：
    L119  elif 'qwen2' in name or 'qwen3' in name:   ← 较新分支
    L122  elif 'qwen'  in name:                       ← 老 Qwen1 分支
我们的 `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B`（及 1.5B）小写后含 "qwen" 但不含 "qwen2"，
链中也无 'deepseek' 分支 → 落入 L122 老 Qwen1 分支，触发两处错误：
  (1) L123  AutoModelForCausalLM.from_pretrained(..., fp32=False, ...)：`fp32` 只有 Qwen-1 的
      remote code 认；标准 Qwen2 架构 → `TypeError: unexpected keyword argument 'fp32'`。
      ——纯 Python 报错、与硬件无关：H200 pilot 走同一条路（run_pilot→edit_loop→from_hparams）必撞，
      故定性为 **pilot-blocker**，须在任何 GPU 窗口之前修好（CPU 即可回归测试）。
  (2) L124  AutoTokenizer.from_pretrained(..., eos_token='<|endoftext|>', pad_token=..., unk_token=...)：
      半角 `<|endoftext|>` **不在** R1-Distill 词表（真 eos 是全角 `<｜end▁of▁sentence｜>` id 151643），
      会新增一个模型永不生成的 id（卫生隐患；HF generate 的停止判据取自模型 generation_config，
      现行 think_budget 未以 tok.eos_token_id 作停止条件 → 现行管线未被污染，详见 sumandplan §5）。

修法（方案 A）：把 editor 模块内引用的 AutoModelForCausalLM/AutoTokenizer 换成薄包装——
  · model 包装：剥掉 `fp32` kwarg（其余原样透传）。
  · tokenizer 包装：丢弃 editor 传入的 eos/pad/unk 覆盖（让原生 config 生效），再把 pad 设回真 eos。
作用域最小、editor.py 自身的两段 padding_side 逻辑（L132-137）原样保留、可 mock 单测、零 fork 漂移。

用法：在 `BaseEditor.from_hparams(hp)` 之前调用一次 `apply()`（edit_loop.run 已接入）。幂等。
"""
from transformers import AutoModelForCausalLM as _REAL_AUTO_MODEL
from transformers import AutoTokenizer as _REAL_AUTO_TOKENIZER

# R1-Distill 真 eos（全角竖线 U+FF5C，复制勿替半角）——drop 掉 editor 错误覆盖后用它把 pad 设回。
REAL_EOS = "<｜end▁of▁sentence｜>"
# editor.py L121/L124 对 qwen 分支硬塞的、对 R1-Distill 错误的覆盖 kwarg。
_BOGUS_TOK_KWARGS = ("eos_token", "pad_token", "unk_token")


class PatchedAutoModelForCausalLM:
    """剥掉只有 Qwen-1 remote code 认的 `fp32` kwarg，其余透传真 AutoModelForCausalLM。
    （pop 在缺省时为 no-op，故对 editor.py 其它分支无副作用。）"""

    @staticmethod
    def from_pretrained(*args, **kwargs):
        kwargs.pop("fp32", None)
        return _REAL_AUTO_MODEL.from_pretrained(*args, **kwargs)


class PatchedAutoTokenizer:
    """丢弃 editor 对 R1-Distill 错误的 eos/pad/unk='<|endoftext|>' 覆盖（让原生 config 生效），
    再把 pad 设回真 eos。其余透传真 AutoTokenizer，**返回真 tokenizer 实例**（类型不变），
    故 editor.py L132-137 的 isinstance 门控与两段 padding_side 逻辑原样生效。"""

    @staticmethod
    def from_pretrained(*args, **kwargs):
        for k in _BOGUS_TOK_KWARGS:
            kwargs.pop(k, None)
        tok = _REAL_AUTO_TOKENIZER.from_pretrained(*args, **kwargs)
        tok.pad_token = tok.eos_token          # pad 设回真 eos（与 editor 其它 AR 分支同口径）
        return tok


def apply():
    """把 easyeditor.editors.editor 模块内的 AutoModelForCausalLM/AutoTokenizer 换成薄包装。

    幂等：包装类透传自 transformers 真类（本模块导入时一次性捕获），重复调用只是重新指向同一包装。
    返回被 patch 的 editor 模块对象（便于断言/调试）。
    """
    from easyeditor.editors import editor as ed_mod    # 惰性 import：调用时 easyeditor 必已可导入
    ed_mod.AutoModelForCausalLM = PatchedAutoModelForCausalLM
    ed_mod.AutoTokenizer = PatchedAutoTokenizer
    return ed_mod
