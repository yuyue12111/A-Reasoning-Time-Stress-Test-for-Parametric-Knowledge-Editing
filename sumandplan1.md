# sumandplan1.md · 阶段总结与下一步作战计划

- **日期**: 2026-06-12 ｜ **覆盖**: 项目启动（6/10 交接）→ 今 ｜ HEAD `7f9c37b`，plan v1.13，工作区 clean
- **定位**: 面向 **AAAI-27 投稿目标**的进度总结 + 带日期的下一步计划。与 `phase-1.md`（换 session 交接读单）互补：那份讲"怎么接手"，本份讲"**走到哪了、欠什么、按什么顺序打到投稿**"。
- **权威性**: `plan.md` 仍是唯一权威计划；本文是快照与作战序列，与 plan 冲突处以 plan 为准。本文初稿经 4 视角（数字引用/代码行号/计划一致性/完整性）对抗核查后修订，错漏已按核查结论订正。
- **路线铁律（用户定）**: ① 先复现 + 写分析笔记；② Prompt2 标准——读论文原文 + **从代码出发，不被论文包装影响**，笔记进 `analysis/`；③ 与 plan 冲突先改 plan（版本 +0.1）。

---

## 1. 北极星：目标与倒计时（今天 2026-06-12）

**目标**: AAAI-27（2027-02 蒙特利尔），首选 AI Alignment track。论文三段式：**现象**（编辑成功率随思考预算的剂量-反应曲线 ES(b)/RR(b)/Leak(b)）+ **机理**（回退由反思驱动的旧知识关联检索）+ **方法**（training-free 推理时 steering 修补）。

| 节点 | 日期 | 倒计时 | 状态 |
|---|---|---|---|
| 每周一增量查新（plan §8） | **6/15（下周一）** | 3 天 | ⬜ 例行，勿漏 |
| W1 硬节点：Phase 0 六笔记齐 | 6/17 | — | ✅ **6/11 提前达成** |
| **go/no-go 硬节点** | **6/22** | **10 天** | ⬜ 卡 GPU（见 §6.3） |
| Qwen3 兼容性检查点 | 6/27 | 15 天 | ⬜ Phase 2（⚠️ Qwen3 准备缺位，见 §4.2-⑫） |
| 主图三张冻结 | 7/8 | 26 天 | ⬜ |
| 全文 v1 内审 + 二轮查新 | 7/14 | 32 天 | ⬜ |
| **abstract 提交** | **7/20** | **38 天** | ⬜ ⚠️ OpenReview 新账号有人工审核延迟——**注册是隐形死线，至今未办**（plan §10-①） |
| **全文提交** | **7/27**（+3 天补充材料） | **45 天** | ⬜ |

**当前最大约束**: 组里 8×H200 走实验室专网、暂不可用（task#04 mom2 已正式延后）。pilot 只需**一个 4–6 小时的 8 卡窗口**（plan §Phase 1）。脚本链主体就绪（`RUNBOOK.md` 自助执行），但核查发现**两个离线可补的工具缺口必须在开窗前补齐**（0.6×3 采样臂、Locality 判分，见 §4.2-②），外加一个 pilot-blocker 代码 bug（§5）。

## 2. 总评：计划 vs 实际

**一句话**: Phase 0（复现循环）**提前 6 天全部完成且质量超计划**（每篇都按 Prompt2 加了「论文宣称 vs 代码现实」交叉核）；harness 从"v0 未实跑"推到"23 个本地单测全绿 + 预算控制器真权重验证"；**唯一落后项是 GPU 真跑**（外部算力约束，非执行问题）。仓库 15 个 commit（`fd009c8`→`7f9c37b`），plan v1.2→v1.13 全程留痕。

交接时 CLAUDE.md 立即任务队列（7 项）对账：

| # | 任务 | 计划 | 实际 |
|---|---|---|---|
| 1 | git init + 首次 commit | — | ✅ `fd009c8`（06-10） |
| 2 | setup_workspace 补齐 papers/source | — | ✅ 7 仓库 + 14 PDF（修了 EasyEdit clone 的 `.DS_Store` 抢写坑） |
| 3 | CPU 冒烟 + env.lock | — | 🟨 env `editrev` + `env.lock`(105 包) ✅、5 个依赖坑回填 01 笔记 ✅；**`rewrite_acc` 数值未闭环**（GPT-2-XL 下载被杀，低优先） |
| 4 | mom2 排队 @8×H200 | — | ⏸️ **用户拍板延后**（需实验室专网）；进了 RUNBOOK 流程，开窗即跑 |
| 5 | 03_rtofu（截止 6/12） | 6/12 | ✅ **6/10 提前**（`43ebdff`） |
| 6 | 02_alphaedit（截止 6/13） | 6/13 | ✅ **6/10 提前**（`6a44057`） |
| 7 | think_budget 单测 | H200 验证 | ✅ 超计划：mock 6 测 + **1.5B 真权重验证**（07 笔记，缩减档）；7B 全量档留 H200 |

## 3. 已完成详单

### 3.1 Phase 0 复现六笔记 + 本地实验笔记（全部 Prompt2 标准：读 PDF + 从代码出发 + 宣称-代码交叉核）

| 笔记 | 一行结论 | 最硬的 catch（写作/答辩可直接用） |
|---|---|---|
| [00_shortlist](analysis/00_shortlist.md) | 方向 B′ 锁定 + 7 仓库复现队列 | 撞车风险"高"（月产一篇近邻）；R²MU 点名防包装头号对象 |
| [01_easyedit](analysis/01_easyedit.md) | 主战框架可信（还原=逐元素精确拷回），开箱有摩擦 | "editing 超 FT reliability" 是 **no-think/logits 口径**——正是我们要在思考预算维度反证的对象 |
| [02_alphaedit](analysis/02_alphaedit.md) | 内置 vs 官方算法逐行同构，作工具可信 | **零空间阈值论文脚注 10⁻² vs 代码 2e-2（差 2×）**；L2 正则两实现 1 vs 10 且论文公式省略；P 预分配缺 qwen 分支必崩（绕过脚本已备）；"+36.7%"是 sequential 场景红利、与我们单条协议正交 |
| [03_rtofu](analysis/03_rtofu.md) | 解码协议地基；prefill 逐字提取并 byte 级校验 | **ZeroThink/LessThink 实为 Jiang et al. 2025**（非 R-TOFU 原创）；`<think>`/`</think>` **非特殊 token** → 文本检测成立。⚠️ 核查订正：二者实为 tokenizer.json added_tokens 在册的非特殊**原子** token（151648/151649），并非"普通 BPE 文本"——结论不变（skip_special_tokens 不剥 special:false），但 03 笔记 §4 与 think_budget docstring 的依据表述需订正，且 token-id 检测其实也可行（见 §6.1-⑤） |
| [04_thinkedit](analysis/04_thinkedit.md) | steering 机制干净，已通用化进 `src/steer.py` | base **无 7B**——写死 heads/directions 全不可跨模型复用，7B 须重抽；论文自承效果 model/task 依赖（1.5B 正向 steering 反掉 10% acc）→ F1 必须网格搜 α |
| [05_r2mu](analysis/05_r2mu.md) | 审计级完成：口径定义一致、数值不可独立复现 | judge **`temperature=0.0` 被注释**（非定温）+ judge 身份三处不一致（gpt-4o/o3/claude）+ 真代码仅 8 py（571 是 vendored）→ 只引定义不采数字；**我们的确定性规则判分是相对它的方法学卖点** |
| [06_data](analysis/06_data.md) | 三源清洗完成 + aliases v0 + 数据卡 | zsRE `answers[1:]` 是"其它可接受答案"非别名（判分污染源，已去噪）；zsRE 用 `alt` 作 o_new 使三源统一为"真→假"反事实；MQuAKE 1907/3000 是多编辑 case（单条协议主用 1093 条单编辑） |
| [07_local_probe](analysis/07_local_probe.md) | 本地 M5/MPS 彩排：**Part A 预算控制器真权重验证 ✅ + Part B ICE 诚实负** | ICE 压不动 1.5B 参数知识（10/12 在 B0 即拒注入答 o_old）→ **反证项目必须用参数编辑**；判分需 **FlipPoint**（"Mars. However…Jupiter"类答案子串分不出翻转）；且弱锚定事实上**局部反向**（Romeo 案例更想反而更接受注入）——现象高度依赖编辑强度与事实锚定度 |

### 3.2 Harness 组件（24 个单测：23 个本地全绿 + 1 个真模型测按设计门控 skip）

| 组件 | 用途 | 验证层级 |
|---|---|---|
| `src/think_budget.py` | 预算控制器 B0–B4（prefill 逐字自 R-TOFU） | ✅✅ mock 6 测 + 门控真模型测 ×1（默认 skip）+ **1.5B 真权重验证**（07，缩减档经 local_probe）；7B 全量档欠 H200。⚠️ 仅 greedy（`do_sample=False` 写死）——0.6×3 采样臂待加（§4.2-②） |
| `src/edit_loop.py` | 单条编辑主循环（分片/续跑/finally 总还原/单条容错） | ✅ mock 7 测（修 v0 的 5 个坑：subject 缺传/字段 `s`/字符串 case_id 分片/HP_CLS 缺编辑器/无容错） |
| `src/metrics.py` | ES/RR/CLR 规则判分 + 别名 | ✅ 2 测手算核对。⚠️ 只消费 efficacy 探针——**Locality/Paraphrase 判分缺失**（layer 扫合格线判不了，§4.2-②）；FlipPoint 待加 |
| `src/run_pilot.py` + `experiments/pilot.yaml` | pilot 入口（确定性抽样/分片/overrides/--dry-run） | ✅ 4 测 + 真配置干跑通过；**决策**零待定（采样臂等工具缺口另列 §4.2-②） |
| `src/prefilter.py` | §2.3 预过滤（pre-edit greedy 命中 o_old） | 🟨 复用已测 metrics.hit；无专属单测，待 GPU 实跑 |
| `src/score_pilot.py` | 分片 jsonl → ES/RR/CLR + go/no-go 判据提示 | 🟨 合成数据 smoke 过；无专属单测；bootstrap CI 待加 |
| `src/steer.py` | 通用表征引导（F1 地基：方向抽取 + hook 注入 + 位置掩码） | ✅ 4 测（真 torch 假模型）；真权重方向抽取欠 |
| `src/build_dataset.py` | 三源数据清洗（确定性可再生） | ✅✅ 实跑产出在仓 |
| `src/local_probe.py` | 本地 MPS 彩排 | ✅✅ 实跑（1.5B，缩减档 768） |
| `src/vendor_patches/gen_alphaedit_P.py` | AlphaEdit qwen P-bug 绕过（预生成 P） | 🟨 compile 过，需 GPU+mom2 |
| `src/smoke_rome_gpt2.py` | GPT-2-XL ROME 冒烟 | ⏳ `rewrite_acc` 待回填（低优先） |
| `RUNBOOK.md` | 算卡窗口自助手册（内网无 Claude 照跑） | ✅ 但**有多处过时**（§4.2-⑧，含未记 qwen 路由 bug——本文 §5） |

### 3.3 数据资产

CF **21,919** / zsRE **18,377**（按 `alt` 反事实映射，跳过 709 退化条）/ MQuAKE **3,000** 统一 schema；`aliases.json` **1,285** 实体（覆盖率 CF 81% / MQuAKE 99% / **zsRE 仅 18%**——Wikidata QID 富集是已登记 TODO）。大文件 gitignore，`build_dataset.py` 一键再生。⚠️ **GSM8K-200 / MATH500-100 子集未建**（plan §2.3 第 4 行、ΔReason/Phase 4 必用，seed 42 固定抽样）——已列 §6.1-⑥。

### 3.4 已拍板决策（别再纠结）

单条编辑协议（主实验，批量只作消融）｜ 思考预算 **5 档 B0–B4**（v1.12 取 B 对齐代码）｜ 路线=先复现写笔记（Prompt2）｜ task#04 mom2 延后（实验室专网）｜ 主模型 R1-Distill-Qwen-7B（基座 Qwen2.5-**Math**-7B，layers 要扫）。

## 4. 问题全记录

### 4.1 已解决（20 项，按类别；详证据在各笔记）

| 类 | 坑 | 处置 |
|---|---|---|
| 环境×5 | conda ToS 门槛；conda-forge 无 pip；系统 py3.9 装不了 torch2.9；easyeditor 本地包须 `PYTHONPATH=.`（无 setup.py）；hparams `model_name` 指向不存在的本地缓存路径 | 全修复并写成 01 §6 可复制命令；`env.lock` 已 commit |
| 工作区×2 | EasyEdit clone 被 `.DS_Store` 抢写致 checkout 失败；setup_workspace 默认路径少 "27" | 修复（reset + 显式传参） |
| 代码×3 | edit_loop v0 五坑（见 §3.2）；metrics 错误行 KeyError + None 目标崩；think_budget v0 `skip_special_tokens=False` 的理由被 tokenizer 证据证伪 | 修复 + mock 单测覆盖 |
| 数据×3 | zsRE `answers[1:]` 噪声污染别名表；zsRE 默认映射语义不符（改用 `alt`）；MQuAKE 多编辑 case 混入单条协议 | 修复，记 06 笔记 |
| 口径×4 | 预算档 6 vs 5 不自洽（**用户拍板取 B**）；ES_b vs rewrite_acc 永不混排；LessThink 是"推广"非"沿用"；ZeroThink/LessThink 归属 Jiang et al. | 已结案/已立规 |
| 实验×2 | ICE 压不动参数知识（诚实负，反证须参数编辑）；子串判分分不出"先新后旧"翻转 | 记 07 笔记 → FlipPoint 进 §6.1 |
| 第三方×1 | AlphaEdit P 预分配缺 qwen 分支（首跑必崩） | 绕过脚本 `gen_alphaedit_P.py` 已备（GPU 验证欠） |

### 4.2 未解决（开放项，按急迫排；①②为 pilot 关键路径）

1. **⭐ EasyEdit qwen 路由 bug —— pilot-blocker**（详见 §5）。
2. **⭐ 开窗前必补的工具缺口 ×3（全部离线可做；核查新列）**：
   - **0.6×3 采样臂**：plan §2.5/Phase 1 明文要求「每条 greedy + temperature 0.6 × 3 seeds」，但 `think_budget._gen` 写死 `do_sample=False`，`pilot.yaml:38` 自注"待加"却没进任何欠账清单。首窗可按 plan §2.6-3 先跑 greedy（结论须在 greedy 下成立），但采样通道要在窗口前就位。
   - **Locality/Paraphrase 判分**：`metrics.score` 只消费 `efficacy` 探针行（edit_loop 落的 `para0/1`/`locality` 行无消费方），**layer 扫合格线「ES≥90% & Locality≥85%」现在判不了**——而这是 go/no-go 的前提（编辑质量不达标则该编辑器整体作废，plan §2.5）。
   - **jsonl 溯源头**：plan §6 可复现三件套要求每个 jsonl 头部写 git hash + 配置摘要（+seed）——**必须在第一批 GPU 分片产出前就位，事后补不了**。
3. **AlphaEdit `cache_c` reset 接线**：已诊断 + 方案锁定（`reset_cache=True`，02 §5），**未落地**——Phase 2 接 AlphaEdit 前必须做（上一稿误记"已解决"，此处订正）。
4. **GPU 欠账**（脚本主体就绪，总清单见 §8）。
5. **行政欠账**：plan §10 的 ①OpenReview ②CFP 核对 ④H200 排队申请三项至今未办（§10-③ Phase 0 已实质完成、待回勾 checkbox）；另 plan §8 的 **6/15 周一查新**将至。
6. **FlipPoint 判分模块未实现**（07 教训 + plan §2.5 + pilot 审计字段需要）；连带 **10% 边界样本判分校准**流程（plan §12.3/06 §7）未排进窗口剧本——本稿已补（§6.3）。
7. **可复现三件套与统计欠账**：除 ②的 jsonl 溯源头外，`score_pilot` 的 bootstrap CI（95%，n=10,000，plan §2.5）与 `src/plots.py`（一键再生图表，7/8 主图冻结依赖）均未建。
8. **文档失同步**：CLAUDE.md 8 处过时（版本号 v1.7→v1.13、任务队列勾选、"src 未实跑"、目录"待建"等）；RUNBOOK 4+ 处（§0 与 §9 预算档自相矛盾、未记 qwen 路由坑、prefilter/score_pilot "mock 单测过"表述过强、缺 07 的 FlipPoint 教训）；**phase-1.md 3 处**（"21 mock 测"→实际 24 函数/23 可绿、prefilter/score_pilot 标 ✅ 过强、"579 是 vendored"→571）；03 笔记 §4 + think_budget docstring 的 added_tokens 依据订正（§3.1）。
9. **环境可移植性未核实**：RUNBOOK 全流程假设窗口机可联网（conda/pip/curl/HF 现场拉 ~15GB 模型），而窗口恰是**内网**；plan §5 纪律②的 Docker 化无人跟踪。离线场景需预打包（模型 snapshot + data/raw + wheels/镜像）——云端逃生同样吃这个准备。
10. **Qwen3 准备缺位**：6/27 检查点与 Phase 2 三模型依赖它，但 `think_budget` 模板写死 DeepSeek 全角格式（无 `enable_thinking` 支持）、EasyEdit 无 qwen3-8b hparams、go（6/22）到 Phase 2（6/23）无缓冲。
11. **GSM8K-200/MATH500-100 子集未建**（§3.3）。
12. `rewrite_acc` 冒烟数值未闭环（低优先）；aliases 的 zsRE 覆盖 18%（Wikidata 富集，P2）。

## 5. ⭐ 头号未决问题：EasyEdit 把 R1-Distill-Qwen 路由进老 Qwen1 加载分支

**关键定性：这不是 MPS 的坑，是 pilot-blocker。** 崩溃由 model_name 字符串决定、与硬件无关——**H200 上跑 pilot 走同一条路**（`run_pilot.py` → `edit_loop.py` → `BaseEditor.from_hparams`），7B 必撞。这直接动摇 RUNBOOK §4 "开窗即跑"的承诺，必须在任何 GPU 窗口**之前**修好。

**机理（`source/EasyEdit/easyeditor/editors/editor.py`，逐行核实 + 独立核查员复证）**：
- if/elif 链按子串路由：L119 `elif 'qwen2' in ... or 'qwen3' in ...`（较新分支）→ L122 `elif 'qwen' in ...`（**老 Qwen1 分支**）。
- 我们的 `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B`（及 1.5B）小写后**含 "qwen" 不含 "qwen2"**（id 里是 `Qwen-7B`），链中也无 'deepseek' 分支 → **落入 L122**。
- L123 调 `AutoModelForCausalLM.from_pretrained(..., fp32=False, ...)`：`fp32` 只有 Qwen-1 的 remote code 认；标准 Qwen2 架构直接 `TypeError: unexpected keyword argument 'fp32'`——纯 Python 报错，**CPU 即可复现/回归测试，不占 GPU 窗口**（核查员已用 tiny Qwen2 在 transformers 5.5.4 下实证）。
- **第二层坑（潜在隐患；核查证实现行管线未实际中招）**：L124（连同 L121 的 qwen2 分支）把 eos/pad/unk 硬设为半角 `<|endoftext|>`——该 token **不在** R1-Distill 词表（真 eos 是 `<｜end▁of▁sentence｜>`，id 151643），tokenizer 会新增一个模型永远不会生成的 id（实测 151665）。**核查澄清**：HF generate 的停止判据取自模型 `generation_config`（eos=151643，不受 tokenizer 覆盖影响），且现行 `think_budget._gen` 只把 `tok.eos_token_id` 传给 `pad_token_id`、未传停止条件——**当前生成仍正常停止，ES_b/B4 未被实际污染**。但凡未来任何代码以 `tok.eos_token_id` 作停止/截断判据即跑满 max_new_tokens，pad 语义也已错位——修复方案连带校正，作为卫生项；回归测试按"kwarg 剥离 + eos 校正断言"写（**不要**按"不打补丁则生成不停"写，复现不出来）。
- 附带：padding_side 两段都要保留语义——L135–137 对 qwen（ROME 族算法下）设 `'right'`；L132–134 是非 ROME 族的左 padding 分支。
- 顺带利好：R1-Distill-**Llama**-8B（副模型）被 L100 'llama' 分支先截住，该分支不覆盖 eos，相对安全。

**修法（三选，已评估，不动只读 source/）**：
| 方案 | 做法 | 评价 |
|---|---|---|
| **A（推荐）** | `src/vendor_patches/easyedit_qwen2_loader.py`：模块属性级 monkeypatch——替换 `easyeditor.editors.editor` 内引用的 `AutoModelForCausalLM`/`AutoTokenizer`（editor.py:9 模块级 import，已核实可行）为薄包装（剥 `fp32` kwarg；丢弃 eos/pad/unk 覆盖、pad 设回真 eos `<｜end▁of▁sentence｜>`），`edit_loop`/`run_pilot` 在 `from_hparams` 前调用 | 作用域最小、两段 padding 逻辑原样保留、**可 mock 单测**、零 fork 漂移；落在 vendor_patches/ 留档合规 |
| B | 预载 (model, tok) 塞进 `hparams.model_name` 走 else 分支 | 坑多：`evaluate.py:145`/`AlphaEdit_main.py:81` 会对 model_name `.lower()`（tuple 即 AttributeError），padding_side 还得手补——遗漏即静默错 |
| C | vendor fork `BaseEditor` 子类（'qwen' 前插 'deepseek-r1-distill' 分支） | 最显式但上游更新要人工对齐 |

## 6. 下一步作战计划

### 6.1 本地立即（无 GPU 也能推进，按序；每项=代码+测试+笔记/记录）

1. **【P0】修 qwen 路由**：按 §5 方案 A 落 `src/vendor_patches/easyedit_qwen2_loader.py` + mock 单测（剥 kwarg/eos 校正/两段 padding 语义三类断言）+ README diff 记录 + 接入 `edit_loop`/`run_pilot`。**同时解锁本地 ROME-on-MPS 与 H200 pilot。**
2. **【P0】开窗前工具缺口三件**（§4.2-②）：0.6×3 采样臂（think_budget 加 do_sample/temperature/seed 通道、jsonl 记 seed、mock 测）；Locality/Paraphrase 判分（metrics/score_pilot 扩展 + 单测，消费 edit_loop 已落的探针行）；jsonl 溯源头（git hash + 配置摘要 + seed 首行）。
3. **【P0】参数版 ROME on MPS 首信号**（07 §6 开放线程，依赖 ①）：1.5B/MPS 真权重 ROME 编辑 → {B0,B3,B4} 生成 → `metrics.score`，用 07 的 12 个常识反事实（带 subject）。**timebox**：通了写 `analysis/08_rome_mps.md`；撞 MPS 算子墙就记雷点等 H200。顺手补 `rewrite_acc`。
4. **【P1】FlipPoint 判分模块**：`metrics.py` 增链内立场首次翻转位 + 首段断言判分 + 单测；连带预写 10% 边界样本校准流程（pilot 审计与 Phase 3 片段归因都要）。
5. **【P1】文档同步一次清**：CLAUDE.md（版本/勾选/现状）；RUNBOOK（§0 矛盾、§4 前置加 qwen 修复步骤、§8 雷点表补路由 bug + 采样/Locality 缺口提示、表述降级）；phase-1.md（3 处）；03 笔记 §4 + think_budget docstring 的 added_tokens 订正；本文 commit 入库。
6. **【P2】**：GSM8K-200/MATH500-100 子集构建（seed 42，判分可借 ThinkEdit `math_grader.py`）；Qwen3 预研（think_budget 模板分支 + enable_thinking + hparams 草案——6/27 检查点前置）；aliases Wikidata 富集；steer 方向抽取 1.5B 试跑；bootstrap CI + `src/plots.py` 骨架；7B local_probe 重跑**降级为可选**（参数版信号优先于 ICE 线程，明示取舍）。

### 6.2 行政线（不占算力，全是日期敏感）

| 事 | 截止 | 说明 |
|---|---|---|
| **OpenReview 全员注册** | **本周** | 新账号人工审核延迟=隐形死线（plan §10-①/Phase 5 双处强调） |
| **核对 AAAI-27 CFP** | 本周 | Alignment track 专属日期 + author kit（plan §10-②；plan 头部日期自标"以官方 CFP 页为准"） |
| **H200 排队申请** | 即刻 | W2 一个 6h 8 卡窗口（pilot）+ W3 起每周两窗（plan §10-④）；申请流程本身可能有 lead time |
| **核实内网窗口联网/镜像** | 开窗前 | RUNBOOK 假设可联网；离线则预打包模型 snapshot + data/raw + wheels（plan §5 纪律② Docker 化同议） |
| 周一增量查新 | **6/15** | plan §8 关键词组；盯防 zjunlp / OPTML-Group / ai-isl / 2602.02028 作者组 |

### 6.3 GPU 窗口剧本（拿到卡当天照 RUNBOOK，预算 ≈ 一个 4–6h 8 卡窗口）

前置：§6.1-①② 必须已合入（CPU 单测可先验，不占窗口）。

顺序：**mom2**（首条 edit 自动触发缓存，~6 GPU·h，stats_dir=`data/stats_r1qwen` 分目录）→ **预过滤**（`prefilter.py`，0.5–1h，存活率预计 40–60%）→ **batch_edit 还原语义确认**（01 §7 要求 pilot 前；单卡几分钟）→ **layer 小扫**（ROME [5]/[7]/[10]、MEMIT [4-8]/[6-10]/[8-12]，n=50 看 B0 下 ES≥90% & Locality≥85% 合格线——依赖 §6.1-② 的 Locality 判分）→ **pilot**（`run_pilot.py` 8 卡分片，ROME+MEMIT × CF-200 × {B0,B3,B4}，~15 GPU·h，可中断续跑；首窗 greedy 先行，0.6×3 臂随采样通道就位补跑）→ **打分**（`score_pilot.py`）→ **10% 边界样本判分校准**（缓存 CoT 上离线复核）→ **30 条回退样本人工审计**（字段含 FlipPoint、触发片段类型）→ 对 6/22 判据。

**算力盲区应急决策点（待用户拍板）**：若 **6/17 前**实验室 GPU 仍无音讯，建议评估 plan §5 云端逃生条款**提前**用于 pilot——RunPod/Lambda 8×H100 ~$20/h，一个窗口 ≈ **$80–120**（预算上限 $400 内），保住 6/22 节点（若采纳：plan §5 条款同步修订，版本 +0.1 记变更）。不动用则 go/no-go 顺延并压缩 Phase 2（风险见 §7）。

### 6.4 go/no-go（6/22，判据语义照录 plan §Phase 1）

**go（两条同时满足）**：① RR(natural) ≥ 20pp 或 ES 降幅 ≥20pp，至少在一个编辑器上成立且另一个方向一致；② 人工审计中 ≥60% 回退案例可归因于反思/自验证片段。
**no-go** → 当日启动 plan §9 fallback（方向 A：推理链内部信号早停；think_budget/管线/CoT 缓存/探针全部复用，4 周压缩计划），沉没成本封顶 12 天。

### 6.5 通往投稿的里程碑（plan §3/§4，预算档已按 v1.12 统一为 5 档）

| 阶段 | 日期 | 内容一句话 | 入口条件 |
|---|---|---|---|
| Phase 1 pilot | 6/18–6/22 | CF-200 × {ROME,MEMIT} × {B0,B3,B4} × {greedy，0.6×3 随通道就位} → 三指标初表 + 30 条审计 | GPU 窗口 + §6.1-①② 合入 |
| Phase 2 主矩阵 | 6/23–7/3 | 3 模型 × 4 编辑器 + ICE 对照 + **未编辑长度对照** × 5 档 × CF-1000 + zsRE-500；CoT 只生成一次全缓存；6/27 Qwen3 检查点 | go 判定；AlphaEdit 先 `gen_alphaedit_P.py` + `reset_cache=True` 接线；Qwen3 预研（§6.1-⑥）就位 |
| Phase 3 机理 | 6/30–7/8 | FlipPoint 片段归因（置换检验）+ logit lens + RR 对反思占比回归 | Phase 2 的缓存 CoT（不再耗大额 GPU） |
| Phase 4 修补 | 7/4–7/12 | F1 edit-aware steering（`steer.py` 已备；7B 重抽方向 + dev-100 网格搜 α,β）；F2/F3 备选；ΔReason 用 GSM8K-200/MATH500-100 | Phase 3 方向证据 + §6.1-⑥ 数学子集 |
| Phase 5 写作 | 7/8–7/27 | 7/8 骨架 → 7/14 v1 内审+二轮查新 → 7/18 v2 + reproducibility checklist + 匿名仓 → **7/20 abstract → 7/27 全文** | 主图冻结（依赖 plots.py） |

算力总账 ~420 GPU·h（含 15% buffer）≈ 每周一个 8–10h 窗口；W5 后理论上零排队依赖（CoT 全缓存设计）。

## 7. 风险登记（更新版；△=本文新增/升级）

| 风险 | 概率 | 缓解 |
|---|---|---|
| △ **算力盲区持续**（实验室专网不可用） | **高（现实已发生）** | 本地 MPS 推进参数版小信号；6/17 决策点评估云端 $80–120 跑 pilot；RUNBOOK 保证拿到卡即跑 |
| △ **EasyEdit qwen 路由 bug 未修就上 GPU** | 修复后消除 | §6.1-① P0 修复 + CPU 回归测试（崩溃纯 Python 可离线复现） |
| △ **开窗才发现工具缺口**（采样臂/Locality 判分/溯源头） | 修复后消除 | §6.1-② P0 离线补齐——核查 round 的最大贡献 |
| △ 内网无外网出口致窗口耗在环境上 | 中 | §6.2 预核实 + 预打包（模型/数据/wheels） |
| △ eos 错置（潜在隐患，现行管线未中招） | 低 | 方案 A 连带校正为卫生项；score 前抽查生成自然停止 |
| 撞车（月产一篇近邻） | 高 | 6/15 起每周一查新不间断；被抢现象则 pivot 机理+修补 |
| pilot 不成立 | 中 | §9 fallback，12 天沉没成本封顶 |
| ROME/MEMIT 编辑质量不达标（Math 基座超参漂移） | 中 | layer 三组扫描 + 合格线；不达标退 Qwen2.5-7B-Instruct 验证基线，主模型改 Qwen3-8B |
| Qwen3 不兼容 / 7 页装不下 | 中/低 | 6/27 检查点降级预案（△预研已列 §6.1-⑥）/ 附录分流 |

## 8. GPU 欠账总清单（跨笔记汇总，开窗按序清；②③ 在 pilot 前）

① mom2（task#04，~6 GPU·h/模型，自动缓存）→ ② `prefilter.py` 预过滤 → ③ **batch_edit 分支还原语义确认**（01 §7，pilot 前；单卡几分钟）→ ④ layer 三组扫描（01 §7）→ ⑤ **pilot 真跑 + 打分 + 校准 + 审计**（关键路径）→ ⑥ think_budget 7B 全量档长度分布（03/07 欠）→ ⑦ AlphaEdit：`gen_alphaedit_P.py` 生成 P + 两实现 100 条 ES 差<2pp + L2∈{1,10} 敏感性（02 §8）→ ⑧ ThinkEdit 7B 方向重抽 + GSM8K 有效性（04）→ ⑨ **未编辑模型 5 档长度对照 + 批量编辑×思考交互消融**（plan §2.6-2/§5 专列 ~20 GPU·h，图 2 组成部分，Phase 2 窗口）→ ⑩ `rewrite_acc` 冒烟闭环（顺手）。

## 9. 给下一个 session

接手读单照 `phase-1.md` §1（CLAUDE.md → plan.md 变更日志 → phase-1 → 笔记 → RUNBOOK）+ **本文 §5/§6**（头号问题与作战序列）。从 §6.1-① 开始干：先修 qwen 路由（本地、有单测、解锁一切），并行 §6.1-②（开窗前工具缺口），再 §6.1-③ 参数版首信号。记忆里有两条工作偏好（`pre-gpu-prep-preference`、`repro-note-standard`），照办。

---
*本文落笔时仓库 HEAD = `7f9c37b`，plan = v1.13，工作区 clean。初稿经 4 视角对抗核查（数字/代码/计划一致性/完整性）修订后入库；后续大节点出 sumandplan2.md，本文不回改（快照性质）。*
