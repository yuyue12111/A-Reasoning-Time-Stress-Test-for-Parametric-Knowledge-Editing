# 02 · AlphaEdit 复现笔记（EasyEdit 内置版 vs 官方仓库 + 零空间投影流程）

- **日期**: 2026-06-10 ｜ **状态**: 双实现源码对照完成 ✅；GPU 实跑（两实现 100 条 ES 差 <2pp）留待 H200
- **仓库**: EasyEdit 内置 `source/EasyEdit/easyeditor/models/alphaedit/`；官方 `source/AlphaEdit/`（jianghoucheng，ICLR'25，2410.02355）
- **任务（plan Phase 0 #02）**: ①EasyEdit 内置 AlphaEdit vs 官方超参 diff；②`null_space_project.pt` 生成流程；③实现选型决议
- **一句话结论**: 两实现**算法逐行同构**（同一个 null-space solve、同一个 `get_project`）；超参唯一实质差异是 **`L2`（EasyEdit=1 vs 官方=10）**；**EasyEdit 内置版对 Qwen 有一处会崩的 bug（P 预分配缺 qwen 分支），上 Qwen 主模型前必须打补丁**。

---

## 1. 代码结构（双实现最小地图）

```
EasyEdit  easyeditor/models/alphaedit/
├── AlphaEdit_main.py   apply_AlphaEdit_to_model() L27  +  execute_AlphaEdit() L105  +  get_project() L348
├── AlphaEdit_hparams.py  dataclass（L2/nullspace_threshold/P_loc/stats_dir 均为必填字段）
├── compute_ks.py / compute_z.py   (K 与 v* 的计算，与 MEMIT 同构)
└── (无 README.md —— qwen yaml 注释里引用的该 README 在此 clone 不存在)

官方  source/AlphaEdit/
├── AlphaEdit/AlphaEdit_main.py   apply_AlphaEdit_to_model() L22（P/cache_c 作为入参传入，函数内不生成）
├── experiments/evaluate.py       ← P 的生成在这里：预分配 L196-205 + get_project() L426-443 + torch.save L209
├── hparams/AlphaEdit/*.json      gpt2-xl / Llama3-8B / EleutherAI_gpt-j-6B / phi-1.5（**无 qwen**）
└── memit/、nse/、rome/、dsets/、glue_eval/ ...（完整实验骨架）
```

EasyEdit 把官方 `experiments/evaluate.py` 里的 P 生成逻辑（预分配 + `get_project` + save）**搬进了** `AlphaEdit_main.py` 的 `apply_` 内部，并加了文件缓存；官方则把 P/cache_c 留在外层 driver 计算后当参数传入。

## 2. 算法保真度（逐行同构，行号为证）

核心 null-space 解算两边**完全一致**：

- EasyEdit `AlphaEdit_main.py:230-233`：
  `upd = solve(proj @ (K@K.T + cache) + L2*I,  proj @ K @ resid.T)`
- 官方 `AlphaEdit_main.py:130-132`：
  `upd = solve(P[i] @ (K@K.T + cache_c[i]) + L2*I,  P[i] @ K @ resid.T)`

`get_project`（零空间投影构造）两边也逐行相同：
- EasyEdit `AlphaEdit_main.py:348-366` ≡ 官方 `experiments/evaluate.py:426-443`：
  `cov=mom2; U,S,_=svd(cov); idx=(S<nullspace_threshold); P_layer = U[:,idx] @ U[:,idx].T`

z*（compute_z）、K（compute_ks）、残差分摊 `resid/(L-i)`、`cache_c += K K.T`（跨编辑累积待保留知识）均同构。**结论：内置版可信，算法非"包装"**（对 R²MU 那种重点防范对象的对照结论）。

## 3. ⭐ 超参 diff（EasyEdit 内置 vs 官方）

同模型（Llama3-8B）逐字段对照，**仅 `L2` 不同**：

| hparam | 官方 `Llama3-8B.json` | EasyEdit `llama3-8b.yaml` | 我们 `qwen2.5-7b.yaml` |
|---|---|---|---|
| layers | [4,5,6,7,8] | [4,5,6,7,8] | [4,5,6,7,8] |
| nullspace_threshold | **2e-2** | **2e-2** | **2e-2** |
| **L2** | **10** | **1** ⚠️ | **1** ⚠️ |
| clamp_norm_factor | 0.75 | 0.75 | 4 |
| v_lr | 1e-1 | 1e-1 | 5e-1 |
| v_loss_layer | 31 | 31 | 27 |
| v_weight_decay | 0.5 | 0.5 | 1e-3 |
| mom2_dataset/n/dtype | wikipedia/100000/float32 | 同 | 同 |
| rewrite_module_tmp | `model.layers.{}.mlp.down_proj` | 同 | 同 |

要点：
1. **`L2`：官方所有配置（gpt2-xl/Llama3/gpt-j/phi）一律 = 10，EasyEdit 所有 yaml 一律 = 1**。这是 solve 里 `+ L2*I` 的正则项，直接影响更新强度。**这是两实现 ES 可能分叉的头号嫌疑**——plan task#02 完成标准是"同 100 条编辑两实现 ES 差 <2pp"，若超标，第一件事就是把 L2 对齐再测。
2. `nullspace_threshold` 两边都 2e-2 → 零空间维度选择一致，P 本身可比。
3. 我们 `qwen2.5-7b.yaml` 的 v-优化超参（clamp=4, v_lr=5e-1, v_loss_layer=27, v_weight_decay=1e-3）**不来自官方 AlphaEdit**（官方无 qwen），是 EasyEdit 自定义（大概率沿用其 MEMIT-qwen）。v_loss_layer=27 = Qwen2.5-7B 第 28 层（末层，0-indexed）✓。
4. `model_name: "Qwen/Qwen2.5-7B-Instruct"` —— 是**通用 Instruct 版**，非我们主模型的 R1-Distill 基座（Qwen2.5-**Math**-7B）。移植时改 `model_name` + 走 plan §7 风险表的 layers 扫描。

## 4. ⭐ `null_space_project.pt` 生成流程

**何时生成**（EasyEdit `AlphaEdit_main.py:58-75`）：`apply_` 进来先查 `hparams.P_loc`（默认 `./null_space_project.pt`）是否存在：
- 不存在 → 现算：逐层 `P[i] = get_project(...)`，`torch.save(P, "null_space_project.pt")`，置 `P_loaded=True`；
- 存在且未加载 → `P = torch.load(hparams.P_loc)`。
- 进程级全局缓存 `P` / `cache_c` + `P_loaded` / `cache_c_new` 标志，避免重复算。

**怎么算**（`get_project` L348-366）：对该层 rewrite 模块的 **mom2 协方差** `cov` 做 `svd`，取**小奇异值**（`S < nullspace_threshold=2e-2`）对应的左奇异向量子空间 `U_s`，`P_layer = U_s @ U_s.T`。几何含义：把更新投影到"被保留知识的键几乎不激活"的零空间，从而改新事实不动旧关联。

**与 task 4 mom2 的关系（重要、省算力）**：`get_project → get_cov → layer_stats(hparams.stats_dir, mom2_dataset=wikipedia, n=100000, float32)` —— **P 用的 cov 就是 MEMIT 用的同一份 mom2**。所以 task 4 把 R1-Distill-Qwen-7B 的 mom2 算好缓存后，AlphaEdit 的 P 只多一次（廉价的）逐层 SVD 即可生成，**不必重算 cov**。前提：`stats_dir` 对 R1-Distill 与 Qwen2.5 **分目录**（01 笔记雷点 4），否则 P 会吃错统计。

**⚠️ 致命 bug（上 Qwen 前必修）**：P 的**预分配** `AlphaEdit_main.py:64-67` 只判 `llama / gpt-j-6b / gpt2-xl`，**没有 qwen 分支**；而紧邻的 `cache_c` 预分配 `L81` 却**有** `qwen`。后果：`model_name` 含 "qwen"（含我们的 `DeepSeek-R1-Distill-Qwen-7B`）且 `null_space_project.pt` 不存在时，`P` 不被预分配 → L70 `P[i,:,:]=...` 抛 `NameError`，**首跑生成 P 必崩**。
- 对比：官方 `evaluate.py:196-205` 用 `model_name == "gpt2-xl"` / `in [...]` 精确匹配（也无 qwen，但官方本就不支持 qwen）；EasyEdit 改成子串匹配以求通用，却漏给 P 加 qwen。
- **修法（走 `src/vendor_patches/` per CLAUDE.md 约束 3）**：在 L64 条件里加 `or "qwen" in hparams.model_name.lower()`。llama 分支用 `W_out.shape[1]`（输入维=intermediate），qwen 的 down_proj 同为 `(hidden, intermediate)`，shape[1] 正确，故复用 llama 分支即可。
- 备选：另写独立 P 生成脚本绕过 `apply_`。优先选 vendor_patch（一行改动，最小侵入）。

## 5. 结构性差异（移植到我们单条编辑协议时注意）

| 维度 | 官方 | EasyEdit 内置 |
|---|---|---|
| P / cache_c 来源 | 外层 driver 算好，作入参传入 `apply_`（L28-29） | `apply_` 内部全局变量 + 文件缓存自管 |
| 权重落盘 | `apply_` 直接原地改 `weights[w][...] += upd`（L139）**不还原**，返回 model + 更新后的 cache_c | `execute_` 算完 deltas 后**自还原**（`copy_to_param`, L262-264），再由 `apply_` 用 `w[...] += upd` 应用（L98），返回 `(model, weights_copy)` |
| 还原配合 | 调用方负责 | 契合 EasyEdit `BaseEditor` 的 `weights_copy` 还原（01 笔记 §3）——我们的 `edit_loop.restore` 直接用得上 |
| target_new 结构 | `request["target_new"]["str"]`（dict） | `request["target_new"][0]`（list） |
| stats_dir / device | `STATS_DIR` 全局 + 硬编码 `"cuda"` | `hparams.stats_dir` + `normalize_device`（可分目录、可指定卡）✓ 对我们更友好 |

`cache_c` 跨编辑累积 `K K.T`（待保留知识矩阵）：**单条编辑协议下每条 case 独立、编辑后还原权重**，但 `cache_c` 是进程级全局且只增。若一个进程内顺序处理多条 case，`cache_c` 会把前面 case 的 K 累积进来 → 影响后续 case 的 P-solve（虽然权重还原了，cache_c 没还原）。**单条协议下应在每条 case 间重置 `cache_c`**（`apply_` 有 `reset_cache` 参数 L36/51 → 置 `cache_c_new=False` 重新初始化）。这条要在 edit_loop 接 AlphaEdit 时显式处理，否则批量污染从 cache_c 偷偷进来。**已登记为雷点，pilot 前验证。**

## 6. 实现选型决议（task#02 完成标准）

**决议：主用 EasyEdit 内置 AlphaEdit**（与 plan §2.2 一致：统一接口、零胶水接入矩阵实验、还原机制契合单条协议），**但三个前置动作**：
1. **必修 qwen P-bug**（§4）：`src/vendor_patches/alphaedit_main_qwen_P.py` 记 diff（L64 加 qwen 分支）。
2. **L2 口径留意**（§3）：内置版 L2=1，官方 L2=10。先按内置 L2=1 跑；做"两实现 ES 差 <2pp"对照时，把官方端 L2 也设 1（或内置端设 10）对齐变量，单独报告 L2 敏感性。
3. **cache_c 单条协议重置**（§5）：edit_loop 每条 case 调 AlphaEdit 时 `reset_cache=True`。

官方仓库角色：**仅作超参与算法对照的 ground truth**，不进主跑（其 driver 绑死 cuda + dict 接口 + 外部 P 传参，接我们协议成本高）。

## 7. 可复用资产 + 雷点

可复用：
- `get_project` 的零空间构造（若日后机理章节要分析"编辑落在哪个子空间"可直接用）；
- P 与 MEMIT 共享 mom2 → task 4 一次 cov 缓存喂两个编辑器；
- `reset_cache` 接口（单条协议必用）。

雷点登记：
1. **qwen P 预分配 bug**（§4）——上 Qwen/R1-Distill-Qwen 主模型前必打补丁，否则首跑 P 崩。
2. **L2=1 vs 10**（§3）——两实现 ES 对照前先对齐，否则差异归因不清。
3. **cache_c 跨 case 不还原**（§5）——单条协议必须 `reset_cache=True`，否则批量干扰从后门进来（呼应 plan §2.6 第 4 刀）。
4. **stats_dir 分目录**（§4，承 01 笔记雷点 4）——R1-Distill 与 Qwen2.5 的 mom2/P 不可混用目录。
5. `model_name: Qwen2.5-7B-Instruct` 是通用版，非 R1-Distill 基座（Qwen2.5-Math-7B）——移植改 model_name + layers 扫描（plan §7）。

## 8. 遗留（H200 回填）
- [ ] 打 qwen P 补丁后，R1-Distill-Qwen-7B 上首跑生成 `null_space_project.pt`（依赖 task 4 mom2 先就位）
- [ ] 同 100 条编辑：EasyEdit 内置（L2=1）vs 官方（L2 对齐）ES 差 <2pp 验证
- [ ] L2∈{1,10} 敏感性小扫（顺带，判断哪个更适配 R1-Distill）
