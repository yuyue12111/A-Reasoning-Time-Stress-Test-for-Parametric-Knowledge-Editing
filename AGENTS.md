# AGENTS.md · why-aaai 项目入口（Codex 必读）

## 这是什么项目

AAAI-27 投稿项目，代号「越想越退」(Thinking Undoes Editing)：量化参数知识编辑（ROME/MEMIT/AlphaEdit）在 R1 式推理模型上随思考预算增加而被推翻的现象 + 机理 + training-free 修补。

**读单（按序）：`plan.md` 头部 v1.x 变更日志（当前 **v2.06**，本项目唯一权威计划）→ `paperwriting/WRITING_PLAN.md`（唯一有效写作计划）→ `paperwriting/results.json`（数字真源）→ `analysis/11–16_*.md` 与对应 prereg（X/P0/CPU closeout 最新证据）→ `RUNBOOK.md`（仅在确有 GPU 任务时）。** `sumandplan1.md` §5/§6 与 `phase-1.md` 是 6 月历史快照，不得覆盖 plan 头部或复活已停止队列。与 plan 冲突的一切行为都需要先升 plan 版本并写变更记录，再执行。

## 硬约束（不可违反）

1. **截止**: abstract 2026-07-21，全文 2026-07-28，supplementary+code 2026-07-31（均 UTC-12）；内部冻结 7/18、7/25。
2. **单条编辑协议**（用户已签字）：主实验逐条 edit → 全预算档生成 → restore；批量编辑只作消融。还原机制证据见 `analysis/01_easyedit.md` §3。
3. **`source/` 下第三方代码只读**。需要改动 → fork 相关文件进 `src/vendor_patches/` 并记录 diff。
4. **口径纪律**: EasyEdit 自带 rewrite_acc（logits 口径）≠ 我们的 ES_b（生成式口径），两者永不混用混排。
5. 所有长任务 ≤2h 粒度、jsonl 追加写、按 case_id 断点续跑（排队集群随时可能杀任务）。
6. 环境一旦跑通立即 `pip freeze > env.lock` 并 commit。

## 目录约定

```
papers/   论文 PDF（repro_/ref_ 前缀）   source/  第三方仓库（只读, 各自带 .git）
analysis/ 复现/实验/方法笔记 00–09      src/     我们的代码 + test_*（mock）+ vendor_patches/
data/     清洗数据(大文件 gitignore,     results/ 实验 jsonl（gitignore，脚本再生）
          build_dataset.py 再生)        experiments/ pilot.yaml（就位）   paperwriting/ 写作真源(results.json/WRITING_PLAN/LaTeX；原 paper/ 已更名防与 papers/ 混淆)
```

若 papers/ 或 source/ 为空：`bash setup_workspace.sh`（幂等，已存在则跳过）。

## 当前状态（2026-07-13；权威进度只看 `plan.md` 头部）

- [x] X2/X3/P1 GPU 运行完成；X1 结果前指定的 fixed-replay 门为 **9/18 FAIL**，永久停止五臂，不筛 case。
- [x] P0 membership/route/crosswalk 完成：corrected taxonomy n=41，Bridge/Recall/RO/Associative=27/11/3/0；logit-lens per-item crosswalk 仅因缺 raw 文件阻塞。
- [x] Percase/B15-B0/Cap3/F3/X2/X3 CPU closeout 全部闭合；最终 audit PASS，B15-B0 两侧 duplicate audit 和 budget provenance 均 PASS。
- [x] GPU 和服务器 CPU 科学队列清空；P0 logit-lens 只是缺 raw dependency 的非承重 optional block。
- [x] 最终科学 review + 三方仲裁 + GPT-5.6 复核完成（v1.89）；Abstract v8.1 内部终版冻结（v1.90）。
- [ ] **唯一当前任务 = 写作冲刺**，按 `paperwriting/WRITING_PLAN.md` 执行。

## 立即任务队列 —— **以 `plan.md v2.06` + `paperwriting/WRITING_PLAN.md` 为准**

1. **投稿前科学队列=零**（不跑 B15 interaction、不烧 X-A 池、不加任何新数字）。
2. Abstract v8.1 已内部冻结；下一步只做正文/图表，并逐项关闭 D1–D8/R1。正文冻结前不得再做 abstract-only 风格迭代。
3. W2（7/19–23）主文四节 → W3（7/24–25）机器对账 + 禁语扫描 + hostile review → 7/28 提交 → R 段 supplementary/provenance manifest。
4. 旧 `paperwriting/draft.md` 是**违规数字的历史底稿**（≥15 处与真源不一致，X1 零披露）：只作素材参考，一切数字从 `paperwriting/results.json` 正向取。

## 防雷清单（前人血泪，违反必翻车）

- **EasyEdit 把含 'qwen' 不含 'qwen2' 的 model_name 路由进老 Qwen1 分支**（`editor.py:122`：fp32 kwarg TypeError + 错 eos）→ **已由 `edit_loop` 自动接入的 `vendor_patches/easyedit_qwen2_loader.py`(方案A) 修掉**；任何新入口加载 R1-Distill-Qwen 前须确保 `apply()` 生效（pilot 主路径已自动）
- **EasyEdit mom2 语料 id 在 datasets≥3 已死**（`layer_stats.py:104` 脚本式 `wikipedia/20200501.en` 必崩，MEMIT/AlphaEdit 前置全断）→ 已由 `vendor_patches/easyedit_mom2_dataset.py` 映射 `wikimedia/wikipedia/20231101.en`（edit_loop 自动接入；不走 edit_loop 的入口须自调 `apply()`）；8 分片**并发首跑会重复触发 mom2**——先单进程预热（RUNBOOK §3）
- **致命：`edit_loop` 调 `ed.edit(...)` 必须 `sequential_edit=True`，永不改回 `False`**——EasyEdit `edit_requests`（`editor.py:406-409`）在 `sequential_edit=False` 时于 `edit()` **返回前**就把 ROME/MEMIT 权重还原回基座 → 随后 `generate_with_budget` **全程在未编辑的基座上生成**（编哪层都一样、三层 md5 逐字节相同）。`True` 时不内部还原，编辑保留到生成完、再由 `finally:restore` 做单条协议还原（每次仅 1 条 request + 每条必还原 → 无跨条累积）。**此 bug 曾污染 08 全部生成式 ES + 首版三层扫描**；修复 commit `fb46107`(2026-06-16)，`edit_loop.py` 已加强注释。
- **口径：layer 扫合格线判 `生成式 ES_b(B0)`，不判 `rewrite_acc`**——修复后 7B/CF 实测 rewrite_acc≈1.0 但生成式 ES_b≈0.55（layer5,n=40,B0），口径差真实存在（~0.45），rewrite_acc 会"通过"生成里只部分显形的编辑（**注：08 旧引用的 6/8 vs 0/8 是上面那个 sequential_edit bug 的污染值，已作废**）
- R1-Distill-Qwen-7B 基座是 Qwen2.5-**Math**-7B：现成 qwen2.5-7b hparams 仅架构兼容，layers 实测 **layer5>7>10（已锁 layer5）**；**合格线已改为「Loc≥0.85 下取生成式 B0 ES_b 最高的层」**（原 ES≥90% 是 rewrite_acc 口径数误植到生成式口径，见 plan v1.18）；主结果须 7B（1.5B 见 08，但其"编辑不进生成"结论受 bug 污染、存疑）
- DeepSeek 模板用**全角竖线** `<｜User｜>`(U+FF5C)，复制时极易被替换成半角导致静默错误；真 eos 是 `<｜end▁of▁sentence｜>`(151643)，`<think>`/`</think>` 是 special=false 原子 token(151648/151649)
- `edit_loop.run` 的 `finally: restore(...)` 不许删——异常不还原会污染整个分片（真权重侧 08 已验还原正确）
- jsonl 溯源头用 `git -C <项目根>`（`source/EasyEdit` 自带 .git，HEAD 不同，否则记错哈希）
- 每周一执行 plan §8 的增量查新（本领域月产一篇近邻，撞车是头号风险）

## 与网页会话的同步纪律（plan §11.4）

本地仓库（本目录）是**唯一真源**。网页会话容器侧的产出经下载合入本地后必须 git commit。plan.md 版本号只增不减。
