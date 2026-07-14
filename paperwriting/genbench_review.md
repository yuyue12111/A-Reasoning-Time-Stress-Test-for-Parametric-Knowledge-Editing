# genbench 安全门评审 + RQ3 裁定(面板 wjt97ozxo/wf_02ee1b3a, 2026-06-24)

> 触发:genbench 最坏界 gsm8k Δ-0.15 failed gate。3 lens(skeptic/harness/framing)+ 综合。
> §6/§7 成稿已落 paper/draft.md;harness 修复已落 src/{think_budget,genbench}.py;此文留裁定+复测阶梯。

## 一句话
RQ3 主腿存活(被编辑 query 上 RR/ES/Loc 全胜、与 genbench 正交);最坏界安全门 gsm8k Δ=-0.15 是真 failed,诚实保留为"病态上界"且因 harness 截断(B3=8192/答案256)欠测而 uninformative——主张靠 by-construction gating + Loc 撑、不靠这两行数;先修 harness(B3M=16384+answer_cap=512+解除 scope 硬编码+加部署臂)再补一次便宜复测,§6/§7 按成稿降级措辞、results.json 部署口径维持 [pending]。

## RQ3 状态
SURVIVE-WITH-REFRAME (主腿活,安全门子主张降级+待复测)。

最终判定分三层:
(1) RQ3 主战果 = SURVIVE,未被触及。RR 0.193→0.085、ES@B3 0.495→0.631、ES_drop 0.106→-0.035、Loc 0.958→0.964 全部测在【被编辑 query 的答案】上(paper/results.json:24-25)。genbench 测的是 base 模型(不挂 ROME)、非编辑通用 query 的附带损害,与主战果正交。红线③成立:genbench 推不翻 RQ3 主结果。

(2) 安全门最坏界 = FAILED-WORSTCASE,诚实保留、不粉饰。gsm8k Δ=-0.15 远超 |Δ|≤0.02 门 → 明写 violates the gate,不说"通过"(红线①)。但它是【病态上界】:genbench.py:114 union_old_ids(并集全部 o_old) + :115 硬编码 scope:'all'(压答案段),三重叠加(全部事实/全部 span/施于部署绝不触发的通用 query),非部署配置。

(3) 安全门当前【内部失效/uninformative】(三 lens 一致最关键发现):acc_off=0.535/0.150 远低于公认 32B GSM8K~0.95/MATH-500~0.90。off 臂【完全不挂抑制】就已塌到地板 → 这是 harness 系统性欠测(think_budget.py:31 B3=8192 截断 MATH 长链于 \boxed{} 前;:79 答案段仅 256 token 截断答案重述)。后果:Δ 归因模糊(伤 vs 截断噪声不可分),math Δ=+0.04(抑制不可能提升数学准确率)直接证明判分噪声主导。故这两行【既不能证伤、也不能证不伤】,是 uninformative,不能进正文主表当证据。

结论:安全子主张("不伤通用能力")目前【不靠这两行数】支撑,而靠 by-construction gating(只对编辑 query 生效→非编辑流量按构造 0 损害)+ Loc 0.958→0.964。draft 已把 gate 标 [pending] 且 abstract/contributions 未 claim,红线未破。可发表前提=harness 修复后补一次便宜复测(基线回 ~0.9 + 加部署臂),否则审稿人会用"你唯一的定量安全证据 failed"做 reject 杠杆。

## harness 必修(已实现)
必须先修(否则复测的 acc_off 仍不可信、Δ 无法解释)。最小 diff,全部在 src/,不动 RQ1/RQ3 主口径锚点(think_budget.py:70 链压 B3=8192 与 :79 答案 256 是论文 B3 锚点,只为 genbench 路径旁路放宽):

A. think_budget.py:31 — 新增长链档,供 genbench 专用,不污染 B3:
   现: CAP = {"B1": 256, "B2": 1024, "B3": 8192, "B4": 8192}
   改: CAP = {"B1": 256, "B2": 1024, "B3": 8192, "B4": 8192, "B3M": 16384}

B. think_budget.py:50 — generate_with_budget 答案段参数化(默认 256 不变,保 RQ1/RQ3 主口径):
   现: def generate_with_budget(model, tok, q, budget, do_sample=False, temperature=0.6, seed=None, suppress=None):
   改: 末尾加 , answer_cap=256
   并把 :66 和 :79 两处 g(text, 256, ...) 改 g(text, answer_cap, ...)。
   (注::66 是 B0 分支、:79 是 B3 答案段;两处都改成 answer_cap。)

C. (强烈建议)think_budget.py:78-79 加"出现 \\boxed{} 或 #### 即停"的早停,否则 512 仍可能不够长链重述。最省事替代:仅靠 B3M(16384 think) + answer_cap=512 即可让 acc_off 回升,先验证再决定是否上 StoppingCriteria。

D. genbench.py:115 — 解除 scope 硬编码,读 config(支持部署臂 scope=think):
   现: sup = {"processor": make_processor(ids, cfg["suppress"]["penalty"]), "scope": "all"}
   改: sup = {"processor": make_processor(ids, cfg["suppress"]["penalty"]), "scope": cfg["suppress"].get("scope", "all")}

E. genbench.py:88-95 + :114 — 加 --mode {union,single} 与 --budget(默认 B3,math 用 B3M):
   - argparse 加: ap.add_argument("--mode", choices=["union","single"], default="union")
   - argparse 加: ap.add_argument("--gsm8k_budget", default="B3"); ap.add_argument("--math_budget", default="B3M")
   - argparse 加: ap.add_argument("--answer_cap", type=int, default=512)
   - :139-140 两处 "B3" 改成按 bench 选 (gsm8k→args.gsm8k_budget, math→args.math_budget),并传 answer_cap=args.answer_cap。
   - single 模式:对每条通用 query 不挂任何抑制(非编辑 query→suppress=None),即复刻部署 0 损害;实现上 single 时直接 sup=None 整跑(off==on),按构造 Δ=0 自证。union 保留为现状上界。

F. genbench.py:60-63 correct() — MATH 抽取失败(无 boxed 且 norm(gold)有效但 gen 截断)单列 abstain,不计入分母,隔离截断噪声(可选,加分项)。

跑前还需:data/gsm8k_200.jsonl 与 data/math500_100.jsonl 本地不存在(本批结果在 GPFS 跑出),复测前先 stage 到 GPFS(genbench.py:20 BENCHES 路径),每行 {"q":..,"a":..}。

## 现实复测阶梯 + 命令
现实复测 = 四格阶梯(都在 GSM8K/MATH 非编辑 query 上,模拟"抑制器全局常开"最坏→部署阶梯),门只判格③/④。

前置(staging):把 gsm8k_200.jsonl / math500_100.jsonl 放到 data/(或 GPFS 对应路径)。

# === 4090 版(bf16,无 NaN,不设 DTYPE)===
cd /Users/whyu/GitProjects/why-aaai27
export WHYAAAI_MODEL=$W/models/DeepSeek-R1-Distill-Qwen-32B

# 步骤1 基线修复验证(先证低基线是 harness 伪影;single 模式=部署=off,acc_off 应回 ~0.9/0.85)
for r in $(seq 0 7); do python src/genbench.py --config experiments/probe32b_sup.yaml \
  --mode single --gsm8k_budget B3 --math_budget B3M --answer_cap 512 --rank $r --world 8 & done; wait
python src/genbench.py --config experiments/probe32b_sup.yaml --mode single --score
# 预期:格④部署臂 acc_off≈acc_on(Δ≈0,按构造),且绝对值逼近 ~0.95/0.90 → 证明 -0.15 是病态上界伪影

# 步骤2 格③ 部署 scope(单 o_old × scope=think,链压答案不压)——若要测"单事实 think 上界"
#   (config probe32b_sup.yaml 已 scope: think;解除 :115 硬编码后自动生效)
for r in $(seq 0 7); do python src/genbench.py --config experiments/probe32b_sup.yaml \
  --mode single --gsm8k_budget B3 --math_budget B3M --answer_cap 512 --rank $r --world 8 & done; wait
python src/genbench.py --config experiments/probe32b_sup.yaml --mode single --score

# 步骤3 格① 最坏界复跑(union × scope=all,修了 budget/answer_cap 后的可信上界,作附录)
#   临时把 config suppress.scope 设 all,或加 --force_scope all;mode union
for r in $(seq 0 7); do python src/genbench.py --config experiments/probe32b_sup.yaml \
  --mode union --gsm8k_budget B3 --math_budget B3M --answer_cap 512 --rank $r --world 8 & done; wait
python src/genbench.py --config experiments/probe32b_sup.yaml --mode union --score

# === H200 版(141G,需 fp32 防 Hopper bf16 NaN)===
# 在上面每条 python 前导出:
export WHYAAAI_DTYPE=float32
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
# 其余命令完全相同(解码 ~2.4×,留足窗口)

四格语义:
  格①最坏界 union×scope=all(修 harness 后)= 严格上界,附录。
  格②单 o_old × scope=all = 去并集放大的全局上界(可选,--mode single + 临时 scope=all)。
  格③单 o_old × scope=think = 部署 scope 的全局常开上界。
  格④部署真态 = single 模式 off-target(GSM8K/MATH 抑制器不触发→Δ≈0)+ on-target 复用 results.json rq3。
门 |Δacc|≤0.02 只判格③/④。优先级:格④(部署)>格①(诚实上界)> 格②③(稳健性附录)。

## 红线自查
四条红线 + 两条全文纪律,逐条自查通过:

① 不粉饰 failed 为通过:PASS。§6/§7 成稿明写 "exceeds/violates our |Δacc|≤0.02 gate" + "we do not claim the gate is passed / do not paper over this";results.json gate_pass=false。

② 不因 failed 假装 RQ3 没事:PASS。给出可辩护真实安全论证(by-construction gating + 三前提显式声明 + Loc 0.958→0.964 实测 + 病态上界 framing + harness 欠测诊断),而非回避。并新增 on-target-reasoning 盲区进 Limitations(原草稿缺)。

③ 主战果只在被编辑 query 答案、未被推翻:PASS。源码自证 genbench 测 base 模型(genbench.py:110 直接 load 基座、不挂 ROME)、非编辑通用 query、scope=all 并集——与 RR/ES@B3/Loc(results.json:24-25,被编辑 query 答案)正交。§6/§7 末句显式声明 "none of this bears on the RQ3 headline results"。

④ 数只用真实测到:PASS。全文只用 genbench 两行实测(0.535/0.385/0.150/0.190)+ results.json rq3 既有数;复测值全标 [pending rerun],未编造任何复测数。

⑤ 不宣称 scaling law:PASS。未碰 §7「A trend across three sizes, not a scaling law」段;新增文本无 scaling 措辞。

⑥ 不宣称首次发现:PASS。未碰 §7 mechanistic/positioning 段(已声明 not first discovery of non-erasure、引 Superficial Editing/DISCO/SCR-ReCoE);新增文本无 first/novel 主张。

唯一需用户注意:§6/§7 称 acc_off 受 harness 截断低估为"caveat/诊断",这是合理的测量学论证(源码 think_budget.py:31/79 自证),非粉饰——但它【削弱最坏界 Δ 可信度】而非证明部署无害,措辞已严格区分(部署无害靠 by-construction,不靠这条 caveat)。
