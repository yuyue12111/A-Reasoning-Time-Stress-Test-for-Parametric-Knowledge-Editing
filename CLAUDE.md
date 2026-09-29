# CLAUDE.md · why-aaai 项目入口（Claude Code 必读）

## 这是什么项目

代号「越想越退」(Thinking Undoes Editing)：参数知识编辑（ROME/MEMIT/AlphaEdit）在 R1 式推理模型上，零思考下通过、原生推理后失效的现象 + 编辑特异性 + 链上因果控制点。AAAI-27 Phase-1 被拒（2026-09），**现改投 ARR 2026-10-12（NAACL/COLING 2027）**。

**读单（按序）：`REVISION.md`（2026-09-28 起唯一权威）→ `official-review.md`（AAAI 审稿原文）→ `paperwriting/results.json`（Study 1 数字真源）→ `RUNBOOK.md`（仅在确有 GPU 任务时）。** `plan.md`、`paperwriting/WRITING_PLAN.md`、`sumandplan1.md`、`phase-1.md` 均为历史档，只作背景，不得约束当前工作。唯一原则：让论文变好。

## 硬约束（不可违反）

1. **截止**：ARR 2026-10-12 AoE。决策门与排期见 `REVISION.md` §3、§6。
2. **单条编辑协议**：每个生成请求只见自己的那一条编辑，编辑之间不累积。引擎 v2 用按行 hook 注入秩 1 编辑，语义与"逐条 edit → 生成 → restore"等价；批量编辑只作消融。
3. **`source/` 下第三方代码只读**。需要改动 → fork 相关文件进 `src/vendor_patches/` 并记录 diff。
4. **口径纪律**: EasyEdit 自带 rewrite_acc（logits 口径）≠ 我们的 ES_b（生成式口径），两者永不混用混排；引擎 v2（bf16 批量）的数字与旧 HF 数字永不混在同一对比里。
5. 所有长任务 ≤2h 粒度、jsonl 追加写、按 case_id 断点续跑（排队集群随时可能杀任务）。
6. 环境一旦跑通立即 `pip freeze > env.lock` 并 commit。

## 目录约定

```
papers/   论文 PDF（repro_/ref_ 前缀）   source/  第三方仓库（只读, 各自带 .git）
analysis/ 复现/实验/方法笔记 00–16      src/     我们的代码 + test_*（mock）+ vendor_patches/ + rt/（引擎 v2）
data/     清洗数据(大文件 gitignore,     results/ 实验 jsonl（gitignore，脚本再生）
          build_dataset.py 再生)        experiments/ pilot.yaml（就位）   paperwriting/ 写作真源(results.json/WRITING_PLAN/LaTeX；原 paper/ 已更名防与 papers/ 混淆)
```

若 papers/ 或 source/ 为空：`bash setup_workspace.sh`（幂等，已存在则跳过）。

## 当前状态（2026-09-28）

- Study 1（AAAI 数据）已完成零 GPU 重分析：Holm 过、留存对比（编辑特异性）14B/32B/70B 过、permissive RR 被名字泄题污染 → 见 `REVISION.md` §2。
- 当前任务：引擎 v2（`src/rt/`）→ G0 一致性门 → 冻结 `prereg-arr.md` → Study 2 → 重写全文。细节与分工只看 `REVISION.md`。

## 防雷清单（前人血泪，违反必翻车）

- **致命：`edit_loop` 调 `ed.edit(...)` 必须 `sequential_edit=True`，永不改回 `False`**——EasyEdit `edit_requests`（`editor.py:406-409`）在 `sequential_edit=False` 时于 `edit()` **返回前**就把 ROME/MEMIT 权重还原回基座 → 随后 `generate_with_budget` **全程在未编辑的基座上生成**（编哪层都一样、三层 md5 逐字节相同）。`True` 时不内部还原，编辑保留到生成完、再由 `finally:restore` 做单条协议还原（每次仅 1 条 request + 每条必还原 → 无跨条累积）。**此 bug 曾污染 08 全部生成式 ES + 首版三层扫描**；修复 commit `fb46107`(2026-06-16)，`edit_loop.py` 已加强注释。
- **EasyEdit 把含 'qwen' 不含 'qwen2' 的 model_name 路由进老 Qwen1 分支**（`editor.py:122`：fp32 kwarg TypeError + 错 eos）→ **已由 `edit_loop` 自动接入的 `vendor_patches/easyedit_qwen2_loader.py`(方案A) 修掉**；任何新入口加载 R1-Distill-Qwen 前须确保 `apply()` 生效（pilot 主路径已自动）
- **EasyEdit mom2 语料 id 在 datasets≥3 已死**（`layer_stats.py:104` 脚本式 `wikipedia/20200501.en` 必崩，MEMIT/AlphaEdit 前置全断）→ 已由 `vendor_patches/easyedit_mom2_dataset.py` 映射 `wikimedia/wikipedia/20231101.en`（edit_loop 自动接入；不走 edit_loop 的入口须自调 `apply()`）；8 分片**并发首跑会重复触发 mom2**——先单进程预热（RUNBOOK §3）
- **口径：layer 扫合格线判 `生成式 ES_b(B0)`，不判 `rewrite_acc`**——修复后 7B/CF 实测 rewrite_acc≈1.0 但生成式 ES_b≈0.55（layer5,n=40,B0），口径差真实存在（~0.45），rewrite_acc 会"通过"生成里只部分显形的编辑（**注：08 旧引用的 6/8 vs 0/8 是上面那个 sequential_edit bug 的污染值，已作废**）
- R1-Distill-Qwen-7B 基座是 Qwen2.5-**Math**-7B：现成 qwen2.5-7b hparams 仅架构兼容，layers 实测 **layer5>7>10（已锁 layer5）**；**合格线已改为「Loc≥0.85 下取生成式 B0 ES_b 最高的层」**（原 ES≥90% 是 rewrite_acc 口径数误植到生成式口径，见 plan v1.18）；主结果须 7B（1.5B 见 08，但其"编辑不进生成"结论受 bug 污染、存疑）
- DeepSeek 模板用**全角竖线** `<｜User｜>`(U+FF5C)，复制时极易被替换成半角导致静默错误；真 eos 是 `<｜end▁of▁sentence｜>`(151643)，`<think>`/`</think>` 是 special=false 原子 token(151648/151649)
- `edit_loop.run` 的 `finally: restore(...)` 不许删——异常不还原会污染整个分片（真权重侧 08 已验还原正确）
- jsonl 溯源头用 `git -C <项目根>`（`source/EasyEdit` 自带 .git，HEAD 不同，否则记错哈希）
- 投稿前再查一次新文献（2026 年近邻：He et al. 2025、CODE 2026、Gao et al. 2026、ThinkEval、CRANE），撞车是头号风险

## 同步纪律

本地仓库（本目录）是**唯一真源**。网页会话/服务器侧的产出经下载合入本地后必须 git commit。
