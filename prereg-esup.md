# 预注册 · E-SUP-BATTERY(W1 因果对照)

**锁定时间 = 本文件 + `data/placebo_donors.json` 入库的 commit(早于任何 D/P GPU 结果)。** 这是 placebo/方向臂可信度的关键:预测写在见数之前。

## 设计
headline 32B / CounterFact / greedy / scope=think / |α|=8 / 按 case_id 配对。四臂仅 `suppress.source` 不同,其余(edit、200 case、decode、budget B0/B3、layer12/v63)全同:
- **N** = 不压(`probe32b.yaml` cf200,已在盘)
- **T** = 压 o_old = 现 fix(`probe32b_sup.yaml` cf200sup,已在盘)
- **D** = 压 o_new = 方向对照(`probe32b_sup_onew.yaml`,新)
- **P** = 压 placebo = 频率/长度匹配无关词(`probe32b_sup_placebo.yaml`,供体 `data/placebo_donors.json` 已 BLIND 锁定,见 `src/placebo_donor.py`)

## 预测(符号阶梯,见数前锁定)
B3 上,**回退指标(RR/CLR)**:`T < P ≈ N < D`;等价 **ES@B3**:`D ≤ N ≈ P < T`。
即:压 o_old 最大改善(T);压无关词 ≈ 不压(P≈N,placebo 是链扰动 floor);压 o_new 不改善甚至恶化(D)。

## headline 统计
**主报 T−P**(o_old 效应**超出 placebo floor** 的 margin),按 case_id 配对差 + 95% bootstrap CI(`src/cross_arm.py`)。**不**主报 T−N(o_old-vs-零),因为 N 不含"压了某个词"这一扰动基线。

## 决策规则(见数前锁定)
1. **D 符号错**(压 o_new 反而**降** RR / 升 ES@B3,排零)→ 中心因果论断受重创,**诚实报告**、不藏。day-1 先跑 D@n≈100 最便宜地先验此项。
2. **P 非零**(placebo 也显著降 RR / 升 ES,排零)→ "o_old 特异 fix"被自伤,**诚实改述**为"o_old-targeting 超过链扰动 floor 的 margin = T−P [CI]";论文用 effect-above-placebo 口径,不再宣称纯特异性。
3. **P 含零(≈floor)+ T−P 排零 + D 不改善** → **o_old 特异性 + 符号 + 剂量(已有 α-sweep)三者齐 = W1 因果对照成立**;RQ3 从"一个管用的干预"升为"符号/特异/剂量受控的因果操控"。
4. Loc(locality 探针)在所有臂应守住(scope=think 仅压 efficacy 探针,结构性安全);任一臂 Loc 塌则该臂作废重查。

## 不声称
本电池**不**证明 route-around 在自然(未干预)生成里**必要**(始终干预态);logit-lens 仍锚 RQ2 "edit intact"。此残余在 limitations 明写(见 `depth-plan.md` 诚实残余 §1)。
