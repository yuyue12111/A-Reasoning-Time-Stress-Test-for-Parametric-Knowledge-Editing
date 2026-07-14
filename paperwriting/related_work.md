# §2 相关工作 + 撞车评估(2026-06-24 文献工作流 w2gwkzie0,HIGH 已 WebFetch 核实)

## ⚠ 撞车裁决:空间拥挤,贡献偏增量,需锐化定位

四条主张里 **#2(非擦除)/ #3(training-free 修复)类别被强近邻占据,#1 现象已知**。原"现象+机理+修复"构想每块都有先例。**独有的仅:capability-emergent scaling、chain-only 因果干预、native R1+思考预算轴。**

### 已核实的 HIGH 近邻(arXiv 摘要已 WebFetch)
- **Benchmarking and Rethinking Knowledge Editing for LLMs**(He, Song, Wang, Sun;arXiv:2505.18690)。realistic autoregressive(非 teacher-forced)下参数编辑崩、SCR(上下文检索)胜出。**撞 #1**:确认"真实推理下编辑失效 + teacher-forcing 高估"。**别**:非思考预算轴、无 capability-scaling、解法**弃**参数编辑(我们留编辑+链内修)。
- **Revealing the Deceptiveness of Knowledge Editing: Superficial Editing**(Xie, Cao, Chen, Liu, Zhao;arXiv:2505.12636)。机理证编辑"表层"、残差流(末主体位早层)+ 后层注意力头/左奇异向量仍编码原知识。**强撞 #2**:"非擦除/旧知识仍编码"是其核心。**别**:标准模型+crafted prompt 静态触发,非 native CoT 自发;无 capability、无修复、无"答案跟链"因果。**我们不得宣称"首次发现非擦除"**,只能立"非擦除在推理 CoT 内动态显形 + cloze 处完好"。
- **Outdated Issue Aware Decoding (DISCO)**(Sun et al.;arXiv:2406.02882)。training-free 解码:编辑/原模型概率分布对比、放大编辑 token 预测;zsRE outdated 比降到 5.78%。**强撞 #3**:"training-free 修推理回退"已有。**别**:干预在**答案/输出级**(全局 logit 对比),非链内 token 抑制;非 R1/思考预算;无"只动链→答案随=因果"。
- **ThinkEval**(Baser, Divakaran, Gurusamy;arXiv:2506.01386)。CoT 构造的 thought-based KG 量化多步推理下的间接泄漏。**撞 #1**。**别**:外部构造 KG,非 native 推理模型;无 logit-lens/capability/修复。

### MEDIUM/LOW(§2 需引、可切割,详见工作流输出)
非擦除 2026 簇(One Mask 2605.28839 / MechLens 2606.07978 / MEGA 2603.20795,**未逐一核实,引前须验**);Edit-via-Background-Stories(2602.02028,训练式 fix、capability 仅轶事);KELE(2408.12456,主张擦除残余=与我们#2相反);CoRect(2602.08221,RAG 冲突非编辑);口径簇(Mirage/QAEdit 2502.11177、Principled-Eval 2507.05937、Edit-Locality 2601.17343);chain-causal 谱系(From-Reasoning-to-Answer 2509.23676 在 R1-distill 上=我们因果前提的最佳引用;Thinking-Intervention、SALT、ITI、DoLa、ParamMute)。
> 注:2026 年 arXiv 号(26xx)多为工作流 web 搜未逐一核实,**写作引用前必须逐篇 WebFetch 验真**(防 agent 幻觉)。

## §2 草(来自工作流,可直接改用;立界语已嵌)
> 见工作流输出全文(task w2gwkzie0)。骨架:**现象近邻**(ReCoE/MQuAKE/KELE/ThinkEval/Mirage/SCR 已证编辑在真实/多跳推理下失效、teacher-forcing 高估)→ 我们别:native R1+思考预算连续轴+**capability-emergent**;**机理近邻**(Superficial Editing + 非擦除簇用 logit-lens/掩码/归因证"掩盖非替换")→ 我们别:**推理 CoT 内动态显形、cloze 处完好、答案跟链**;**修复近邻**(DISCO 答案级对比;Thinking-Intervention/SALT 在 think 段;ITI/DoLa/ParamMute 抑参数知识)→ 我们别:**链内 token 抑制、只动链而答案改善=因果**;**方法学**(NKL/Principled-Eval/Edit-Locality 指 substring 假阳,但非 CoT)→ 我们别:**CoT 泄漏的词边界口径 + ~2× 量化**。

## 我们能守的独有点(写作锚)
1. **capability-emergent**:编辑侵蚀随能力涌现(7B 无→32B 显著)——独有,但需补点(4th size / 2nd family)做厚。
2. **chain-only 因果**:只干预链→答案改善,因果坐实"链内重推驱动回退"(2509.23676 提供 R1-distill 因果前提)。
3. native R1 + 思考预算轴;CoT 泄漏词边界口径。
