"""通用表征引导工具（Phase 4 主修补 F1 的地基）。机制改造自 ThinkEdit（source/ThinkEdit）：

  · 方向提取  extract_direction: v_ℓ = mean(hidden[集合A, span]) − mean(hidden[集合B, span])
              （ThinkEdit Eq.1，extract_thinking_length_direction_gsm8k_mlp.py:91-93）
  · 引导注入  Steerer: forward hook 在 layer.{mlp,self_attn} 输出上加 α·v_ℓ
              （ThinkEdit Eq.2，thinking_length_steering_gsm8k.py:44-61）

ThinkEdit 是**全局**注入（所有位置、所有层、常量 α，目标=控制思考长度）。本工具把它推广：
  ① 任意方向（不限思考长度——F1 用「质疑-编辑事实方向」/「新事实方向」）；
  ② 可选层子集；③ 可选**位置掩码**（条件化/窗口注入——F1 用「仅被编辑主体提及后 k 个 token」）。

模块路径假设 `model.model.layers[i].{mlp,self_attn}`（Qwen2.5 / R1-Distill-Qwen 与 ThinkEdit 同构）。
"""
import torch

TEMPLATE_FULL = "<｜User｜>{q}<｜Assistant｜>{t}"      # 全角竖线 U+FF5C
TEMPLATE_BASE = "<｜User｜>{q}<｜Assistant｜>"


class Steerer:
    """上下文管理器：进入挂 forward hook，退出摘干净。

    directions : Tensor[n_layers, hidden]，每层一个引导方向（未用的层可置零）。
    alpha      : 标量；>0 强化方向，<0 抑制（ThinkEdit 的 direction_weight）。
    site       : "mlp" | "attn"——挂在哪个子模块输出（对应 ThinkEdit 两套 direction）。
    layers     : 要挂的层索引（None=全部，即 ThinkEdit 全局）。
    用法：
        with Steerer(model, dirs, alpha=-4.0, site="attn") as st:
            st.set_positions(mask)          # 可选；mask: BoolTensor[seq]，只在 True 位注入
            out = model.generate(...)
    """

    def __init__(self, model, directions, alpha, site="mlp", layers=None):
        assert site in ("mlp", "attn")
        self.model, self.dirs, self.alpha, self.site = model, directions, alpha, site
        n = len(model.model.layers)
        self.layers = set(range(n)) if layers is None else set(layers)
        self._handles, self._mask = [], None

    def set_positions(self, mask):
        """条件化注入：mask 为 BoolTensor[seq]，仅在 True 的 token 位加方向。
        注意：增量解码（KV cache）时每步 h 的 seq=1，需调用方逐步维护 mask；
        本工具只在 mask 长度与当前 forward 的 seq 对齐时按位生效，否则全局注入。"""
        self._mask = mask

    def _hook(self, i):
        v = self.dirs[i]
        def fn(module, inp, out):
            tup = isinstance(out, tuple)
            h = out[0] if tup else out
            add = self.alpha * v.to(device=h.device, dtype=h.dtype)          # [hidden]
            if self._mask is not None and self._mask.shape[-1] == h.shape[1]:
                add = add.view(1, 1, -1) * self._mask.to(h.device, h.dtype).view(1, -1, 1)
            h2 = h + add
            return (h2,) + tuple(out[1:]) if tup else h2
        return fn

    def __enter__(self):
        for i, layer in enumerate(self.model.model.layers):
            if i in self.layers:
                mod = layer.mlp if self.site == "mlp" else layer.self_attn
                self._handles.append(mod.register_forward_hook(self._hook(i)))
        return self

    def __exit__(self, *exc):
        for hd in self._handles:
            hd.remove()
        self._handles = []
        self._mask = None


def extract_direction(model, tok, pairs_A, pairs_B):
    """ThinkEdit Eq.1 通用化：返回 Tensor[n_layers, hidden] = meanHidden(A) − meanHidden(B)。

    pairs_A / pairs_B : List[(question, text)]；对每条取拼接串里 text 的 token 区间（span）
                        上、逐层 hidden 的均值，再在集合内求均值，最后 A−B。
    F1 用例：A=「忠于新事实的 CoT」、B=「质疑/回退旧答的 CoT」→ 方向=强化编辑事实。
    """
    def mean_hidden(pairs):
        embs = []
        for q, t in pairs:
            start = len(tok(TEMPLATE_BASE.format(q=q)).input_ids)
            end = len(tok(TEMPLATE_FULL.format(q=q, t=t)).input_ids)
            ids = tok(TEMPLATE_FULL.format(q=q, t=t), return_tensors="pt").to(model.device)
            with torch.no_grad():
                hs = model(**ids, output_hidden_states=True).hidden_states[1:]   # 跳 embedding 层
            # stack→[n_layers, batch=1, seq, hidden]；取 batch0 + span 求均值→[n_layers, hidden]
            embs.append(torch.stack(hs, 0)[:, 0, start - 1:end - 1, :].mean(1).cpu())
        return torch.stack(embs, 0).mean(0)
    return mean_hidden(pairs_A) - mean_hidden(pairs_B)
