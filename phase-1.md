# phase-1.md · 阶段性总结 / 交接（给下一个 session）

> 本文件是**换 session 的 handoff**，快照于 **2026-06-11**（plan v1.13）。**6/11 之后的进度以 `sumandplan1.md` 为准**（含 6/12 的 P0 qwen 修复/采样臂/判分/溯源头/ROME-on-MPS、P1 FlipPoint）；本文仅订正 3 处事实错（mock 测计数、prefilter/score_pilot 状态、R²MU vendored 数），不回填新进度。
> 截至 **2026-06-11**，仓库从空目录推到「**Phase 0 复现全齐 + pilot harness 开窗即跑 + 本地真权重验证**」。plan 已到 **v1.13**，14 个 commit（`fd009c8`→`0af7a50`）。

---

## 0. 一句话现状

复现 + harness + 数据 + 算卡手册全就绪、本地用 M5/MPS 验证了预算控制器在真权重上正确；**唯一未决的活在 GPU**（pilot 真跑）。当前有一条**本地开放线程**：参数版 ROME on MPS 卡在 EasyEdit 老 Qwen 加载分支（可绕，见 §6）。

## 1. 怎么接手（读单 + 规矩）

**读单（按序）**：`CLAUDE.md`（项目入口/硬约束）→ `plan.md`（唯一权威计划，**先看头部 v1.x 变更日志**）→ **本文件** → `analysis/00–07_*.md`（复现/实验笔记）→ `RUNBOOK.md`（算卡操作手册）。

**记忆**（`~/.claude/.../memory/`）：`pre-gpu-prep-preference`（用户委派执行、算卡前把离线活做满、只抛真 blocker）、`repro-note-standard`（路线=先复现+写笔记；Prompt2=读 PDF 原文+从代码出发、不被包装影响）。

**环境**：conda env `editrev`（py3.10，`env.lock` 已锁）。跑 `easyeditor` 必须 `cd source/EasyEdit && PYTHONPATH=.`（本地包、无 setup.py）。无 GPU 的 mock 测用 system `python3` 即可。

**铁律**：① 与 plan 冲突先改 plan（版本 +0.1 + 写变更）；② **全角竖线 `<｜User｜>` U+FF5C** 勿替半角；③ 口径不混（生成式 `ES_b` ≠ EasyEdit `rewrite_acc`）；④ `source/` 只读，改动走 `src/vendor_patches/`；⑤ 路线=先复现写笔记，从代码出发不被论文包装影响。

## 2. 已拍板的决策（别再纠结）

| 决策 | 结论 | 出处 |
|---|---|---|
| 主实验协议 | **单条编辑**（edit→全档生成→restore），批量只作消融（用户早签字） | plan §2.2 |
| 思考预算档 | **5 档 B0–B4**（B0 Zero / B1 256 / B2 1024 / B3 8192≈natural / B4 extend），plan 对齐代码 | v1.12 |
| 工作路线 | **先复现 + 写分析笔记**（Prompt2 标准） | 用户确认 |
| task#04 mom2@8×H200 | **延后**（需实验室专网，组里算力暂不可用） | v1.4 |
| 主模型 | DeepSeek-R1-Distill-Qwen-7B（基座 Qwen2.5-**Math**-7B；hparams 仅架构兼容，layers 要扫） | plan §7 |

## 3. 已完成（14 commit）

- **Phase 0 复现六笔记齐**（W1 硬节点 6/17 提前达成）：`analysis/01`EasyEdit·`02`AlphaEdit·`03`R-TOFU·`04`ThinkEdit·`05`R²MU·`06`数据。每张都「读 PDF + 从代码出发 + 论文宣称 vs 代码现实」。
- **Harness 全就位 + mock 测全绿（无 GPU）**：6/11 时 **24 个测函数（23 本地可绿 + 1 真模型测按设计门控 skip）**（前稿"21"误记）；见 §4。
- **数据**：`src/build_dataset.py` 清洗 CF(21919)/zsRE(18377)/MQuAKE(3000) 为统一 jsonl + `data/aliases.json`(1285) + 数据卡 `06`。
- **算卡自助手册** `RUNBOOK.md` + 一键打分 `src/score_pilot.py`。
- **本地 M5/MPS 迷你彩排**（`07` + `src/local_probe.py`）：预算控制器真权重验证 ✅ + ICE 现象探针（诚实负）。

## 4. Harness 组件状态（每个文件）

| 文件 | 作用 | 状态 |
|---|---|---|
| `src/think_budget.py` | 预算控制器 B0–B4（prefill 逐字自 R-TOFU） | ✅ mock + **1.5B 真权重**验证 |
| `src/edit_loop.py` | 单条编辑主循环（分片/续跑/总还原） | ✅ 修 5 坑 + 7 mock 测 |
| `src/metrics.py` | ES/RR/CLR 规则判分 + 别名 | ✅ 加固 + 2 测（手算核对） |
| `src/run_pilot.py` | pilot 入口（抽样/分片/overrides/--dry-run） | ✅ 4 测 + 干跑真配置过 |
| `src/prefilter.py` | §2.3 预过滤（GPU） | 🟨 复用已测 metrics.hit；**无专属单测**，待 GPU 实跑 |
| `src/score_pilot.py` | 分片 jsonl → ES/RR/CLR | 🟨 合成数据 smoke 过；**无专属单测**；bootstrap CI 待加 |
| `src/steer.py` | 通用引导（Steerer hook + extract_direction，F1 地基） | ✅ 4 mock 测 |
| `src/local_probe.py` | 本地 MPS 彩排（Part A 长度 + Part B ICE） | ✅ 跑过（1.5B） |
| `src/build_dataset.py` | 三源清洗 | ✅ |
| `src/smoke_rome_gpt2.py` | GPT-2-XL ROME 冒烟 | ⏳ `rewrite_acc` 待回填（被杀/慢） |
| `src/vendor_patches/gen_alphaedit_P.py` | AlphaEdit qwen P-bug 绕过（预生成 P） | ⏳ 待 GPU |
| `experiments/pilot.yaml` | pilot 配置（R1-7B×{ROME,MEMIT}×CF-200×{B0,B3,B4}×8 卡） | ✅ 零待定 |

**跑全部 mock 测**：`for t in metrics edit_loop run_pilot; do python3 src/test_$t.py; done`（system py）；`editrev/python src/test_think_budget.py` + `test_steer.py`（需 torch）。

## 5. 关键发现（从代码出发，跨笔记，写作/答辩用）

- **AlphaEdit**（02）：内置 vs 官方算法**逐行同构**；唯一实质超参差异 **L2(内置=1 vs 官方=10)**；**零空间阈值论文脚注 10⁻² vs 代码 2e-2(2×)**；**内置版 P 预分配缺 qwen 分支→上 Qwen 首跑必崩**（绕过脚本已备）；P 与 MEMIT 共享 mom2。
- **R-TOFU**（03）：**ZeroThink/LessThink 实为 Jiang et al. 2025**（非 R-TOFU 原创，引用分清）；方向与我们**镜像成对**；`<think>`/`</think>` 经查 HF tokenizer_config 在 R1-Distill-Qwen-7B 与 -Llama-8B **均非特殊 token**→走文本检测。
- **R²MU**（05）：judge `temperature=0.0` **被注释→非定温不可复现**；真代码仅 8 py（**571** 是 vendored lm-eval 假象）；残留口径=LLM-judge 1–4。
- **ThinkEdit**（04）：steering 机制已改造进 `steer.py`；其 base **无 7B**，方向/头不可跨模型复用；效果 model/task 依赖。
- **EasyEdit**（01）：易用=统一接口真但**开箱摩擦**（PYTHONPATH/model_name 本地路径/版本漂移）；"超 FT reliability" 是 no-think 口径——正是我们要在 think 预算下反证的对象。
- **本地实验**（07）：**ICE 上下文注入压不动 1.5B 参数知识**（B0 即答真事实），无编辑可回退 → 反证**必须用参数编辑**；判分要 **FlipPoint**（非仅子串）。

## 6. ⭐ 当前开放线程：参数版 ROME on MPS（接手就从这继续）

**目标**：1.5B/MPS 上 EasyEdit 真权重 ROME 编辑 → 全档生成 → **参数版**「越想越退」首测（ICE 测不出的真机制）。

**已摸清（从代码）**：MPS 可用；ROME/MEMIT 路径无硬编码 `.cuda()`；`easyeditor/util/device.py:normalize_device` 支持 `"mps"` 字符串；1.5B 与 7B **同架构（28 层 qwen2）**，`hparams/ROME/qwen2.5-7b.yaml` 可复用（`layers[5]`/`v_loss_layer27`/`mom2_adjustment:false`=不需协方差）。**关键：`hp.device` 要设字符串 `"mps"`（int 会被当 cuda:idx）**。

**撞的坑（冒烟第一步炸）**：`editor.py:123` 按 model_name 含 "qwen" 路由到**老 Qwen1 加载分支**——传 `fp32=False`（Qwen2 不接受 → `TypeError: unexpected keyword argument 'fp32'`）+ 把 eos 错设 `<|endoftext|>`（R1-Distill 应是 `<｜end▁of▁sentence｜>`）。复现脚本：`/tmp/rome_mps_smoke.py`。

**下一步（具体到能直接写）**：
1. 读 `editor.py:90–127` 的 if/elif 分支条件，确认老 Qwen 分支的触发条件。
2. **外部 monkeypatch**（在 runner 里，不动只读 source/）：包 `AutoModelForCausalLM.from_pretrained` 剥掉 `fp32` kwarg；并确保 tokenizer 走正常 `AutoTokenizer`（别用 `<|endoftext|>` eos）——或直接预载 model/tok 想办法注入。最干净可能是 vendor-patch `editor.py` 的 qwen 分支条件排除 Qwen2，记 `src/vendor_patches/`。
3. 绕通后**预期还会有 MPS 后续坑**（compute_v 梯度里 float64/算子缺口）——**timebox**：通了就跑 §下方 probe；撞 MPS 墙就把雷点记清等 H200。
4. 通了之后：把 §curated 案例（07 笔记里那 12 个常识反事实，带 subject）喂 `edit_loop.run`（overrides `device:"mps"`, `model_name:1.5B`）或直接小脚本，每条 edit→{B0,B3,B4} 生成→`metrics.score`，看 **ES 随预算↓ / RR↑**（参数版第一个信号）。顺手补 task#03 `rewrite_acc`。

## 7. GPU 待办（脚本就绪，等 H200/内网）——照 `RUNBOOK.md`

mom2 协方差（task#04，自动触发缓存，stats_dir 分目录）→ `prefilter.py`（§2.3）→ `run_pilot.py` 8 卡分片（ROME/MEMIT）→ `score_pilot.py` 出 ES/RR/CLR → **6/22 go/no-go**（判据 plan §Phase 1）。另：AlphaEdit 用前先 `gen_alphaedit_P.py`（+ qwen P 补丁）；`test_think_budget.py --model 7B` 真模型长度；layers∈{[4-8],[6-10],[8-12]} 扫描（合格线 ES≥90% & Locality≥85%）。

## 8. 本地能做的（算力盲区，M5 Pro 24G/MPS）

① 接着绕 ROME-on-MPS（§6）；② 7B 主模型上重跑 `local_probe`（更强 ICE 跟随，但 ICE 仍非主机制）；③ `steer` 方向抽取在 1.5B 上验（F1 预备）；④ aliases 的 Wikidata QID 富集（zsRE 覆盖 18%↑）；⑤ 补 GPT-2-XL 冒烟 `rewrite_acc`。

## 9. 雷点速查（合并版）

全角竖线 U+FF5C；`PYTHONPATH=.`+cwd=source/EasyEdit；stats_dir R1-Distill 与 Qwen2.5 **分目录**；hparams `model_name` 默认指向 Qwen2.5 本地路径（run_pilot 自动 override）；口径不混（ES_b vs rewrite_acc）；AlphaEdit qwen P-bug + cache_c 单条须 reset；**EasyEdit 把含 "qwen" 的 model_name 路由到老 Qwen1 加载（fp32 kwarg + 错 eos）→ Qwen2/R1-Distill 要绕**；MPS 慢(~7 tok/s)+部分算子缺口；`finally: restore` 不许删；ICE≠参数编辑。

## 10. 文件地图

```
CLAUDE.md            项目入口/硬约束        plan.md   唯一权威计划(v1.13)
phase-1.md           本交接                 RUNBOOK.md 算卡自助手册
env.lock             editrev 依赖锁          experiments/pilot.yaml
analysis/00..07      shortlist + 6 复现笔记 + 本地实验笔记
src/                 think_budget/edit_loop/metrics/run_pilot/prefilter/score_pilot/
                     steer/local_probe/build_dataset/smoke_rome_gpt2 + test_*（mock）
src/vendor_patches/  AlphaEdit qwen P 绕过 + README
data/                aliases.json + sample_records.jsonl（大 jsonl 与 raw gitignore，build_dataset 再生）
source/              7 个第三方仓库（只读，setup_workspace.sh 再生）  papers/ 14 PDF
results/             gitignore（CoT/probe 产物）
```

---
*接手第一件事：读 §1 读单，然后看你想走 §6（本地继续）还是等 §7（GPU）。有疑先信 plan.md。*
