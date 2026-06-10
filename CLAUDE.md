# CLAUDE.md · why-aaai 项目入口（Claude Code 必读）

## 这是什么项目

AAAI-27 投稿项目，代号「越想越退」(Thinking Undoes Editing)：量化参数知识编辑（ROME/MEMIT/AlphaEdit）在 R1 式推理模型上随思考预算增加而被推翻的现象 + 机理 + training-free 修补。

**先读 `plan.md`（当前 v1.2，本项目唯一权威计划），再读 `analysis/00_shortlist.md` 与 `analysis/01_easyedit.md`。** 与 plan 冲突的一切行为都需要先改 plan（版本号 +0.1 并写变更记录），再执行。

## 硬约束（不可违反）

1. **截止**: abstract 2026-07-20，全文 2026-07-27（UTC-12）。go/no-go 硬节点 **6/22**（判据在 plan §Phase 1）。
2. **单条编辑协议**（用户已签字）：主实验逐条 edit → 全预算档生成 → restore；批量编辑只作消融。还原机制证据见 `analysis/01_easyedit.md` §3。
3. **`source/` 下第三方代码只读**。需要改动 → fork 相关文件进 `src/vendor_patches/` 并记录 diff。
4. **口径纪律**: EasyEdit 自带 rewrite_acc（logits 口径）≠ 我们的 ES_b（生成式口径），两者永不混用混排。
5. 所有长任务 ≤2h 粒度、jsonl 追加写、按 case_id 断点续跑（排队集群随时可能杀任务）。
6. 环境一旦跑通立即 `pip freeze > env.lock` 并 commit。

## 目录约定

```
papers/   论文 PDF（repro_/ref_ 前缀）   source/  第三方仓库（只读）
analysis/ 复现笔记 0X_*.md              src/     我们的代码
data/     清洗后数据集（待建）           results/ 实验 jsonl（待建）
experiments/ 每实验一个 yaml（待建）     paper/   LaTeX（待建）
```

若 papers/ 或 source/ 为空：`bash setup_workspace.sh`（幂等，已存在则跳过）。

## 当前状态（2026-06-10 交接时点）

- [x] 地毯式查新 + 方向锁定 B′（`analysis/00_shortlist.md`）
- [x] plan.md v1.2（含 §11 源码实测事实、§12 harness v0 代码）
- [x] EasyEdit 权重还原机制审计（`analysis/01_easyedit.md`）
- [x] `src/` 四个 v0 模块就位（从 plan §11.3/§12 提取，已过 compile 校验，**未实跑**）

## 立即任务队列（按序执行，完成即勾选并 commit）

1. [ ] `git init`（若未初始化）+ 首次 commit 全部交接文件
2. [ ] `bash setup_workspace.sh` 补齐 papers/source（如缺）
3. [ ] **CPU 冒烟**: 按 `analysis/01_easyedit.md` §1 的命令建 conda env 并运行 `src/smoke_rome_gpt2.py`（在 `source/EasyEdit/` 目录下跑）。把 rewrite_acc 结果与依赖坑回填 01 笔记 §6，`pip freeze > env.lock`
4. [ ] **mom2 排队**: 向 8×H200 集群提交 R1-Distill-Qwen-7B 的 mom2 统计任务（plan §5 第一行；首次 edit 调用自动触发并缓存，stats_dir 与 Qwen2.5 分目录——见 01 笔记雷点 4）
5. [ ] `analysis/03_rtofu.md`（截止 6/12）：精读 `source/R-TOFU/test_cot.py` 与 `test.py`，把 ZeroThink/LessThink 的 prefill 精确字符串提进 `src/think_budget.py`（替换 v0 的占位实现），确认 `<think>` 是否特殊 token 并据此决定 B4 的 `</think>` 检测走文本还是 token-id（plan §12.1 注意点②）
6. [ ] `analysis/02_alphaedit.md`（截止 6/13）：EasyEdit 内置 AlphaEdit vs 官方仓库超参 diff；`null_space_project.pt` 生成流程
7. [ ] `src/think_budget.py` 写单测：5 档预算在未编辑 R1-7B 上产出预期长度分布（H200 窗口内验证）

## 防雷清单（前人血泪，违反必翻车）

- R1-Distill-Qwen-7B 基座是 Qwen2.5-**Math**-7B：现成 qwen2.5-7b hparams 仅架构兼容，layers 需 {[4-8],[6-10],[8-12]} 扫描（合格线 ES≥90% & Locality≥85%）
- DeepSeek 模板用**全角竖线** `<｜User｜>`，复制时极易被替换成半角导致静默错误
- `edit_loop.run` 的 `finally: restore(...)` 不许删——异常不还原会污染整个分片
- 每周一执行 plan §8 的增量查新（本领域月产一篇近邻，撞车是头号风险）

## 与网页会话的同步纪律（plan §11.4）

本地仓库（本目录）是**唯一真源**。网页会话容器侧的产出经下载合入本地后必须 git commit。plan.md 版本号只增不减。
