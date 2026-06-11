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
