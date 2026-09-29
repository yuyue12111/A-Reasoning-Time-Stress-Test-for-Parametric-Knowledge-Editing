"""R1-Distill-**Llama** 分词器修复(transformers 5.x 坑)。

现象:transformers 5.5.4 把 DeepSeek-R1-Distill-Llama 的分词器误建成 **Metaspace(sentencepiece ▁)**
pre_tokenizer / decoder,但该模型实际是 **byte-level(Ġ/Ċ)**。Metaspace 处理 byte-level 文本时
**在编码阶段把空格全删**(`"is the capital"`→`['ist','he','capital']`)→ 我们的模板 prompt 变无空格
乱码喂给模型 → 退化输出(. \n\n 串);decode 同样把空格吞掉、`</think>` 检测失效。
证据:`AutoTokenizer` 出 `['ist','he',...]`、`PreTrainedTokenizerFast(tokenizer.json)` 出 `['is','Ġthe',...]`。

修法(最小侵入):检测到 Metaspace,就**原地**把 pre_tokenizer + decoder 换成 tokenizer.json 里的
byte-level 版,**保留分词器类型/特殊 token/config 不变**(EasyEdit editor.py 的 isinstance 门控、
padding 逻辑不受影响)。Qwen 等不含 Metaspace 的**原样返回、零影响**。
"""
import os


def fix_r1_tokenizer(tok, model_path):
    """就地修复 Metaspace 误建;非 Metaspace 原样返回。model_path 需含 tokenizer.json。"""
    try:
        bt = tok.backend_tokenizer                      # fast tokenizer 的 rust 后端
        if "Metaspace" not in repr(bt.pre_tokenizer):   # 只有被误建的 Llama 命中
            return tok
    except Exception:
        return tok
    tj = os.path.join(str(model_path), "tokenizer.json")
    if not os.path.exists(tj):
        # 2026-09-29 审查 M4:以前只打印警告并返回会删空格的坏分词器 → 现在直接报错
        raise RuntimeError(f"[r1_tokenizer] Metaspace 命中但缺 {tj},分词器会删空格;请确认本地模型目录")
    from transformers import PreTrainedTokenizerFast
    ref = PreTrainedTokenizerFast(tokenizer_file=tj).backend_tokenizer  # 正确的 byte-level 组件来源
    bt.pre_tokenizer = ref.pre_tokenizer            # 失败直接抛出,不再静默返回坏分词器
    bt.decoder = ref.decoder
    print("[r1_tokenizer] 已把 Metaspace pre_tokenizer/decoder 换成 byte-level(R1-Llama 修复生效)")
    return tok
