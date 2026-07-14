"""RQ3 修复 v1 · 旧知识抑制 LogitsProcessor（plan v1.27；RQ3 设计面板 #1）。

机理(RQ2)：编辑在 cloze 处完好(100% 仍预测 o_new)，是推理在【输出端】复活旧值 o_old。
修复 = 生成时压制 o_old 的 token logit，堵这条表达通道。信号 = 该条编辑的 o_old
(编辑场景免费已知、与 ROME 计算 update 用 o_old 同源、正当)，逐 case 现构、零加载、零额外前向。

诚实口径(面板对抗结论)：
- scope='think' 命中 CLR 定义(cot 含 o_old) → ΔCLR 是【预期内口径自证】，主报 ΔRR/ΔRRs/ΔES；
- 压首 token ≠ metrics.hit 的词边界文本匹配 → 改述/外语/缩写可旁路(v2 序列级 NoBadWords 再堵)；
- 必走 metrics._safe_cands 丢 <4 字符别名(否则压 'in'/'it'/'es' 毁通用措辞 → GSM8K 退化)。
"""
import metrics


def build_old_token_ids(tok, o_old, aliases):
    """o_old(+安全过滤别名)在多种前缀下的首 token id 集合。

    句中(带空格)、句首/换行后(无空格)、首字母大写是不同 id —— 都收，否则 penalty 形同虚设。
    走 _safe_cands 丢 <4 字符短码(与判分口径同源)。
    """
    ids = set()
    for c in metrics._safe_cands(o_old, aliases):
        c = str(c).strip()
        if not c:
            continue
        for variant in (" " + c, c, " " + c.capitalize(), c.capitalize()):
            t = tok(variant, add_special_tokens=False)["input_ids"]
            if t:
                ids.add(t[0])
    return ids


def make_processor(ids, penalty):
    """返回可审计的 LogitsProcessor：对 ids 的 logit 减 penalty。

    ``calls`` 只记录处理器真正进入解码循环的次数。它让 smoke 能区分“YAML 选中了
    para0/para1”与“processor 实际被 generate 调用”；scope=think 的 B0 按构造 calls=0。
    """
    from transformers import LogitsProcessor

    idl = sorted(ids)

    class _OldTokenPenalty(LogitsProcessor):
        def __init__(self):
            self.calls = 0

        def __call__(self, input_ids, scores):
            self.calls += 1
            if idl:
                scores[:, idl] = scores[:, idl] - penalty
            return scores

    return _OldTokenPenalty()
