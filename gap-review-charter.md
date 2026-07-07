# 写作前终审 charter · 只找缺的(gap-review)—— 给独立 Fable-5 session

**你是谁**:一名与建设过程完全隔离的独立终审员。你没有参与任何实验决策,不欠任何沉没成本人情。
**唯一目标**:让这篇论文在 **AAAI-27(AI Alignment track 首选)** 被录取。其他一切(工程自豪感、
已花的算力、叙事偏好)都不是目标。
**唯一产出**:一份「缺失清单」——**只写缺什么、该加什么**;不复述已有的好,不重审已关账的判。

## 项目一句话
「越想越退 / Thinking Undoes Editing」:ROME/MEMIT 参数知识编辑在 R1-distill 推理模型上,
思考预算一展开就被推翻(现象);编辑完好、链内重推旧世界、答案跟承诺层走(机理);
token 级链内抑制 training-free 修复(方案);部署门+多跳无侧伤(边界)。

## 必读(按序;数字一律以 paper/results.json 为准,散文声明不可信)
1. `paper/results.json` —— 全部证据的唯一真源(~2000 行,逐块读;`_pending_draft_edits` 是已排队的写作指令)
2. `plan.md` 头部 v1.50–v1.64 变更日志 —— 五周的决策史与关账记录
3. `终极review.md` —— **7/3 的上一轮终审**(判档 weak-accept 上沿贴 solid 下沿;B1–B33 台账)。
   你的任务是它的补集:7/3 之后证据面大扩(见 plan v1.59–v1.64),它没见过新东西
4. `prereg-wseries.md` + `analysis/10_jlens_workspace.md` —— W 系列预注册与 workspace 方法论进口
5. `paper/draft.md` —— 现行初稿(半旧;写作 7/8 起重写,别纠缠措辞,看结构性缺失)
6. `depth-plan.md` §第二–五轮、`analysis/00-09`、`src/`(口径核查按需)

## 7/3 之后新增的证据(上轮终审没见过的;你重点审"它们被用足了吗、缺什么配套")
- **B15 PASS**:控 per-case base 知识后 es_drop 涌现 slope 不动(.0992 p=.0041)→ capability 升格闸门过
- **B16**:机理分母 17→**50** committed reversions / 7 cell / **2 族**(首批 Llama);Bridge 68%/Recall 22%/
  RO 8%/Assoc 1(分裂票)="几乎从不无声"
- **B22**:MEMIT-14B 现象复制(RR 0.333 > ROME)——第二编辑器,且更狠
- **F2/F3**:ZeroThink 非空块伪影(B0P≈B0≪B1)/采样鲁棒(0.264);**M4**:五臂特异性(T−C 四指标全排零,
  化解 RRs p=.073);**S10**:修复 14B 复现(配对四指标全排零,比 32B 干净);**G1**:修复在多跳上无侧伤
- **W 系列(Anthropic workspace 方法论进口,全 prereg+效度门)**:W-A=表征在场≠回退(G5 100%+A2 null),
  分岔在**承诺层**;跨编辑器表征分化(ROME 压制/MEMIT 保留,对应行为 RR 差);W-B=概念级抑制压得住链、
  够不着答案(B1 FAIL=dissociation 负结果)→ 与 token 级修复的"外科手术性"互证
- **K2′**:回退 8× 集中 base 认识 o_old 的 case(25% vs 3.2%)= KC 主导+confabulation 注脚
- **V1**:CLR 极性假阳 paper 口径 ≈6%;**B12**:反思标记=常量非变量;**B7**:logit-lens n=23 落定
- 六尺度 base 表全、F1 配对 CI airtight、cap3 六尺度确认 CLR 涌现退役

## 你要回答的(不设限,但至少覆盖)
1. **Novelty 到底在哪、说满了吗**:逐条列出我们独有的东西(现象级/机理级/方法级/负结果级),
   每条对上最近邻(SCR/CRANE/ThinkEval/Superficial Editing/DISCO/workspace 论文)——
   哪些 novelty **存在但没被命名**?(例:「承诺层」这个 construct 三处证据会师,配得上一个名字和一段吗?
   方法学贡献——prereg+效度门+distractor 校准 lens+五臂 battery+中性判官管线——值不值一节/一表?)
2. **承重柱清单**:每根柱子(现象剂量/涌现/机理/修复/边界)下面站着哪些证据,**哪根柱子还缺一块砖**
   (缺的=什么实验/分析/表/图/句;标零卡可补 vs 写作可补 vs 真缺)
3. **methods 盘点**:我们实际发明/组装了哪些可复用方法?哪些该进正文、哪些进附录、哪些漏了没写?
4. **AAAI/AIA rubric 逐条对表**:relevance statement、alignment 文献带、mechanistic interpretability
   关键词、reproducibility checklist、ethics——**缺哪份材料**?
5. **图表账**:这个故事**必须存在**哪几张图/表才能在 Phase-1(只看 abstract/intro/图1)活下来?现在缺哪张?
6. **最强三条拒稿理由(以 7/8 证据面重算)**:上轮 R1/R2/R3 部分已被拆,重构造今天还成立的前三,
   每条给"加什么能拆"
7. **自由项**:任何你认为缺的——写作结构、命名、一句话 pitch、贡献排序、
   甚至"这批证据支持一个比现在更大/更不同的 claim"

## 纪律(不许违反)
- **只找缺的**。已关账项(★1★2/B1–B26 的裁决/W 系列 prereg 终裁/DROP 的 B27–B33)不重审、不翻案;
  除非你发现**新的致命错误**(那要单列一节,给复算证据)
- 数字引用必须能在 results.json 里指到块;引外部论文先 WebFetch 验真
- 新实验建议须过双门:①真承重(缺它某 claim 塌)②日历可行(写作 7/8–7/25,abstract 7/18 冻结;
  零卡/判官类优先,GPU 仅在真承重时提)
- 产出写进仓根 `gap-review.md` 并 commit;结构=【top-5 必加】+【全量缺失清单(每条:缺什么/为什么动录取/
  怎么加/成本/落在哪节)】+【新致命错误(如有)】。中文,数字精确
- 建议多 agent 交叉验证你的 top-5(你有 workflow 能力就用;每条缺失让一个对抗 agent 试图论证"其实不缺")

**开工方式**:先读必读 1–4,再按 6 个问题逐个产出,最后合并排序。不用请示,读完就干。
