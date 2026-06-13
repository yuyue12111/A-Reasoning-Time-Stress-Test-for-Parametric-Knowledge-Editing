# CLAUDE.md · why-aaai 项目入口（Claude Code 必读）

## 这是什么项目

AAAI-27 投稿项目，代号「越想越退」(Thinking Undoes Editing)：量化参数知识编辑（ROME/MEMIT/AlphaEdit）在 R1 式推理模型上随思考预算增加而被推翻的现象 + 机理 + training-free 修补。

**读单（按序）：`plan.md` 头部 v1.x 变更日志（当前 **v1.15**，本项目唯一权威计划）→ `sumandplan1.md` §5/§6（进度总结 + 带日期作战序列，工作以此为准）→ `phase-1.md`（换 session 交接，按需）→ `analysis/00–09_*.md`（复现/实验/方法笔记）→ `RUNBOOK.md`（算卡手册）。** 与 plan 冲突的一切行为都需要先改 plan（版本号 +0.1 并写变更记录），再执行。**算卡/内网窗口照 `RUNBOOK.md` 自助执行（pilot harness 串通、23+ mock 单测全绿、ROME-on-MPS 真权重端到端验证过、qwen pilot-blocker 已修，无 Claude 也能跑完 pilot）。**

## 硬约束（不可违反）

1. **截止**: abstract 2026-07-20，全文 2026-07-27（UTC-12）。go/no-go 硬节点 **6/22**（判据在 plan §Phase 1）。
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
          build_dataset.py 再生)        experiments/ pilot.yaml（就位）   paper/ LaTeX（待建）
```

若 papers/ 或 source/ 为空：`bash setup_workspace.sh`（幂等，已存在则跳过）。

## 当前状态（2026-06-12；权威进度看 `sumandplan1.md`）

- [x] Phase 0 复现六笔记 01–06 齐（W1 硬节点 6/17 提前达成）+ 数据三源清洗（CF/zsRE/MQuAKE）
- [x] pilot harness 串通（think_budget/edit_loop/metrics/run_pilot/prefilter/score_pilot/steer）+ 23+ mock 单测全绿
- [x] 本地 M5/MPS 真权重验证：预算控制器（07）+ **参数版 ROME-on-MPS 端到端跑通（08，无算子墙）**
- [x] **P0 开窗前三件 + qwen pilot-blocker（本轮 6/12）**：① qwen 路由修复（`vendor_patches/easyedit_qwen2_loader.py`）② 0.6×3 采样臂 + Locality/Paraphrase 判分 + jsonl 溯源头 ③ ROME-on-MPS 首信号；④ FlipPoint 判分模块
- [ ] **唯一落后项 = GPU 真跑**（pilot/mom2，卡实验室专网；脚本就绪，开窗即跑——见 `RUNBOOK.md`）

## 立即任务队列 —— **以 `sumandplan1.md` §6 为准**（本节只给指针，勿照旧清单）

作战序列与日期敏感项全在 `sumandplan1.md` §6.1（本地）/§6.2（行政）/§6.3（GPU 窗口剧本）。当前剩余主线：
- **§6.1-⑤ 文档同步**（本轮进行中）→ **§6.1-⑥ P2**（GSM8K-200/MATH500-100 子集、Qwen3 预研、aliases 富集、steer 方向抽取、bootstrap CI + plots 骨架）
- **行政线（用户负责，提醒即可）**：OpenReview 注册（隐形死线）、CFP 核对、H200 排队申请；**每周一 plan §8 增量查新**（≥6/15）
- **GPU 窗口**：照 `RUNBOOK.md`（mom2→预过滤→layer 小扫→pilot→打分→**10% 边界校准**→审计→6/22 go/no-go）；**组内启智平台＝全离线部署，照 `interplan2.md`**（平台实测在 `report.md`；interplan.md 仅 §1/§8/§9 仍有效）

## 防雷清单（前人血泪，违反必翻车）

- **EasyEdit 把含 'qwen' 不含 'qwen2' 的 model_name 路由进老 Qwen1 分支**（`editor.py:122`：fp32 kwarg TypeError + 错 eos）→ **已由 `edit_loop` 自动接入的 `vendor_patches/easyedit_qwen2_loader.py`(方案A) 修掉**；任何新入口加载 R1-Distill-Qwen 前须确保 `apply()` 生效（pilot 主路径已自动）
- **EasyEdit mom2 语料 id 在 datasets≥3 已死**（`layer_stats.py:104` 脚本式 `wikipedia/20200501.en` 必崩，MEMIT/AlphaEdit 前置全断）→ 已由 `vendor_patches/easyedit_mom2_dataset.py` 映射 `wikimedia/wikipedia/20231101.en`（edit_loop 自动接入；不走 edit_loop 的入口须自调 `apply()`）；8 分片**并发首跑会重复触发 mom2**——先单进程预热（RUNBOOK §3）
- **口径：layer 扫合格线判 `生成式 ES_b(B0)`，不判 `rewrite_acc`**——08 实证 rewrite_acc post=6/8 但生成式 ES_b=0/8，两者脱节；rewrite_acc 会"通过"生成不动的层
- R1-Distill-Qwen-7B 基座是 Qwen2.5-**Math**-7B：现成 qwen2.5-7b hparams 仅架构兼容，layers 需 {[4-8],[6-10],[8-12]} 扫描（合格线 ES≥90% & Locality≥85%，**生成式口径**）；1.5B@默认超参编辑不进生成（08）→ 主结果须 7B
- DeepSeek 模板用**全角竖线** `<｜User｜>`(U+FF5C)，复制时极易被替换成半角导致静默错误；真 eos 是 `<｜end▁of▁sentence｜>`(151643)，`<think>`/`</think>` 是 special=false 原子 token(151648/151649)
- `edit_loop.run` 的 `finally: restore(...)` 不许删——异常不还原会污染整个分片（真权重侧 08 已验还原正确）
- jsonl 溯源头用 `git -C <项目根>`（`source/EasyEdit` 自带 .git，HEAD 不同，否则记错哈希）
- 每周一执行 plan §8 的增量查新（本领域月产一篇近邻，撞车是头号风险）

## 与网页会话的同步纪律（plan §11.4）

本地仓库（本目录）是**唯一真源**。网页会话容器侧的产出经下载合入本地后必须 git commit。plan.md 版本号只增不减。
