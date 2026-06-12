# src/vendor_patches/ — 第三方代码的修补记录

CLAUDE.md 约束 3：`source/` 下第三方代码**只读**；需改动则 fork/记录在此，不改 source/。

---

## 1. AlphaEdit 内置版 P 预分配缺 qwen 分支（崩溃 bug）

- **文件**: `source/EasyEdit/easyeditor/models/alphaedit/AlphaEdit_main.py`
- **位置**: `apply_AlphaEdit_to_model()` 的 P 预分配，约 L64–67
- **现象**: `model_name` 含 `qwen`（含我们主模型 `DeepSeek-R1-Distill-Qwen-7B`）且 `null_space_project.pt` 不存在时，P 不被预分配 → L70 `P[i,:,:]=...` 抛 `NameError`，**AlphaEdit 在 Qwen 上首跑 P 必崩**。
- **根因**: 同函数 L64 只判 `llama / gpt-j-6b`，`elif` 判 `gpt2-xl`，**漏 qwen**；而紧邻的 `cache_c` 预分配 L81 却有 `qwen`（不对称，明显是加 qwen 支持时漏了 P 这处）。
- **审计来源**: `analysis/02_alphaedit.md` §4。

### 上游一行 diff（仅作记录，source/ 只读不改）
```diff
  # AlphaEdit_main.py  apply_AlphaEdit_to_model()  ~L64
- if "llama" in hparams.model_name.lower() or "gpt-j-6b" in hparams.model_name.lower():
+ if ("llama" in hparams.model_name.lower() or "gpt-j-6b" in hparams.model_name.lower()
+         or "qwen" in hparams.model_name.lower()):
      P = torch.zeros((len(hparams.layers), W_out.shape[1], W_out.shape[1]), device="cpu")
```
（qwen 的 `mlp.down_proj` 与 llama 同为 `(hidden, intermediate)`，故复用 llama 分支的 `shape[1]` 即正确。）

### 采用的修法（不改 source/）：预生成 P 文件，绕过 bug
`gen_alphaedit_P.py` 用 EasyEdit 自己的 `get_project`（其本身对 qwen 正确）按正确 qwen 形状
预生成 `null_space_project.pt`。AlphaEdit `apply_` 只在该文件**不存在**时才走缺 qwen 的预分配；
文件已存在则直接 `torch.load` 跳过 bug（`AlphaEdit_main.py` L60 / L73-75）。

需 GPU（P 依赖 mom2 协方差，与 task#04 同一份 cov）。用法见 `gen_alphaedit_P.py` 顶部 docstring。

**何时用**: Phase 2 接 AlphaEdit 之前、task#04 mom2 就位之后跑一次/模型。pilot 只用 ROME/MEMIT，不阻塞。

### 另一处待接线时处理（非本 bug）
AlphaEdit 的 `cache_c` 进程级全局跨 `edit()` 累积（02 §5）——单条编辑协议下接 AlphaEdit 时
需每条 case `reset_cache=True`，否则批量干扰从后门进来。`src/edit_loop.py` 已留注释标记。

---

## 2. EasyEdit 把 R1-Distill-Qwen 路由进老 Qwen1 加载分支（⭐ pilot-blocker）

- **文件**: `source/EasyEdit/easyeditor/editors/editor.py`
- **位置**: `BaseEditor.__init__` 的模型/分词器加载 if/elif 链，L119–L124。
- **现象**: `model_name` 含 `qwen` 但不含 `qwen2`/`qwen3`（我们主模型 `DeepSeek-R1-Distill-Qwen-7B`/1.5B
  小写后 = `deepseek-r1-distill-qwen-7b`，且链中无 `deepseek` 分支）→ 落入 L122 的**老 Qwen1 分支**：
  - **(1) 崩溃**: L123 `AutoModelForCausalLM.from_pretrained(..., fp32=False, ...)`，`fp32` 只有 Qwen-1
    remote code 认 → 标准 Qwen2 架构 `TypeError: unexpected keyword argument 'fp32'`。
  - **(2) 卫生隐患**: L124 把 eos/pad/unk 硬设半角 `<|endoftext|>`（不在 R1-Distill 词表；真 eos 是全角
    `<｜end▁of▁sentence｜>` id 151643）→ 新增一个模型永不生成的 id。HF generate 停止判据取自模型
    `generation_config`，`think_budget` 未以 `tok.eos_token_id` 作停止条件 → **现行管线未被污染**，
    但凡未来以 `tok.eos_token_id` 作停止/截断即跑满 max_new_tokens（详见 `sumandplan1.md` §5）。
- **关键定性**: 崩溃由 model_name 字符串决定、**与硬件无关** → H200 pilot 走同一条路
  （`run_pilot.py`→`edit_loop.py`→`BaseEditor.from_hparams`）必撞 → **pilot-blocker**，须在任何 GPU 窗口
  之前修好（纯 Python，CPU 即可复现/回归测试）。
- **审计来源**: `analysis/01_easyedit.md`、`sumandplan1.md` §5（含独立核查员复证）。

### 上游等价 diff（仅作记录，source/ 只读不改）
```diff
  # editor.py  BaseEditor.__init__  ~L122（'qwen' 老 Qwen1 分支）
- self.model = AutoModelForCausalLM.from_pretrained(self.model_name, fp32=False, trust_remote_code=True, **model_kwargs)
+ self.model = AutoModelForCausalLM.from_pretrained(self.model_name, trust_remote_code=True, **model_kwargs)   # 剥 fp32
- self.tok = AutoTokenizer.from_pretrained(self.model_name, eos_token='<|endoftext|>', pad_token='<|endoftext|>', unk_token='<|endoftext|>', trust_remote_code=True)
+ self.tok = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)   # 让原生 config 生效（真 eos）
+ self.tok.pad_token = self.tok.eos_token
```

### 采用的修法（方案 A，不改 source/）：模块属性级 monkeypatch
`easyedit_qwen2_loader.py`：把 `easyeditor.editors.editor` 模块内引用的
`AutoModelForCausalLM`/`AutoTokenizer`（editor.py:9 模块级 import）换成薄包装——
model 包装剥 `fp32` kwarg；tokenizer 包装丢弃 eos/pad/unk 覆盖并把 pad 设回真 eos。
**作用域最小**（只动这两个名字）、editor.py 自身的两段 `padding_side` 逻辑（L132-137）原样保留、
返回的是真 tokenizer 实例（不破坏 isinstance 门控）、可 mock 单测、零 fork 漂移。

为何不选 B/C（已评估，见 sumandplan §5 表）：B（预载 (model,tok) tuple 塞 model_name）会撞
`evaluate.py:145`/`AlphaEdit_main.py:81` 对 model_name `.lower()`（tuple→AttributeError）+ padding 手补遗漏；
C（fork BaseEditor 子类）最显式但上游更新要人工对齐。

### 接入与测试
- **接入**: `src/edit_loop.py` `run()` 在 `BaseEditor.from_hparams(hp)` **之前**调 `apply()`（幂等）；
  `run_pilot.py`/本地 MPS 冒烟经 `edit_loop` 间接生效。
- **mock 单测**: `test_qwen2_loader.py`（4 测：apply 换名+幂等 / 剥 fp32 / 丢 eos 覆盖+pad 设回 / 类型保留+两段 padding）
  ——全 stub transformers，`python3 src/vendor_patches/test_qwen2_loader.py` 即过（无 GPU/无 transformers）。
- **真模块校验**: 已在 `editrev` 下确认 `apply()` 正确换掉 live `easyeditor.editors.editor` 的两个属性（无须加载模型）。

**何时用**: 任何加载 R1-Distill-Qwen（ROME/MEMIT/AlphaEdit/FT 任一编辑器、pilot 与本地 MPS 冒烟）之前。
pilot 主路径已自动接入，无需手动调用。
