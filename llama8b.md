[root:why-aaai27]$ for CFG in probe_llama8b_L6_c2 probe_llama8b_L6_c3 probe_llama8b_L5_c2 probe_llama8b_L7_c2; do echo "========== $CFG =========="; python src/score_pilot.py --config experiments/$CFG.yaml --editor ROME; done
========== probe_llama8b_L6_c2 ==========
# editor=ROME  shards=8  错误行=0  解码臂=greedy  o_old/o_new 源=data/counterfact.jsonl
budget     n      ES     ESf      RR     RRs     CLR    Flip      PS     Loc  (n_para/n_loc)
B0        60   0.667   0.700   0.000   0.000   0.000   0.083       —   0.900  (0/60)
B3        60   0.633   0.717   0.125   0.025   0.317   0.167       —   0.867  (0/60)
RR=答案含旧(上界,含'守住+顺带提旧')  RRs=答案含旧且不含新(下界,ES镜像,最干净回退)  真回退率在两者之间

ES=严格(命中 o_new 且不含 o_old)  ESf=首段断言(答案首立场=编辑)  Flip=答案内两立场都现(先新后旧)  —— ESf≫ES 且 Flip↑ = 答案内『越想越退』(07 教训, FlipPoint 见 analysis/09)

95% bootstrap CI (n=10000, 按编辑条目重采样, plan §2.5)：
budget              ES [lo, hi]             RR [lo, hi]            CLR [lo, hi]
B0          0.667 [0.550,0.783]     0.000 [0.000,0.000]     0.000 [0.000,0.000]
B3          0.633 [0.517,0.750]     0.125 [0.025,0.225]     0.317 [0.200,0.433]

ES 降幅 ES(B0)−ES(b) 配对 bootstrap（plan §2.5；越想越退主判据，CI 全>0=显著回退）：
  B0→B3: 0.033 [-0.100,0.167]  ⚠CI 含0

go/no-go (plan §Phase 1): RR(natural=B3)≥0.20 或 ES 自 B0 降幅≥0.20pp，且 ≥60% 回退案例可归因反思片段（人工审计 30 条）。
layer 扫合格线 (plan §7): B0 下 ES≥0.90 & Loc≥0.85，否则该编辑器结果整体作废。
========== probe_llama8b_L6_c3 ==========
# editor=ROME  shards=8  错误行=0  解码臂=greedy  o_old/o_new 源=data/counterfact.jsonl
budget     n      ES     ESf      RR     RRs     CLR    Flip      PS     Loc  (n_para/n_loc)
B0        60   0.700   0.733   0.000   0.000   0.000   0.100       —   0.800  (0/60)
B3        60   0.650   0.683   0.071   0.024   0.333   0.100       —   0.850  (0/60)
RR=答案含旧(上界,含'守住+顺带提旧')  RRs=答案含旧且不含新(下界,ES镜像,最干净回退)  真回退率在两者之间

ES=严格(命中 o_new 且不含 o_old)  ESf=首段断言(答案首立场=编辑)  Flip=答案内两立场都现(先新后旧)  —— ESf≫ES 且 Flip↑ = 答案内『越想越退』(07 教训, FlipPoint 见 analysis/09)

95% bootstrap CI (n=10000, 按编辑条目重采样, plan §2.5)：
budget              ES [lo, hi]             RR [lo, hi]            CLR [lo, hi]
B0          0.700 [0.583,0.817]     0.000 [0.000,0.000]     0.000 [0.000,0.000]
B3          0.650 [0.533,0.767]     0.071 [0.000,0.167]     0.333 [0.217,0.450]

ES 降幅 ES(B0)−ES(b) 配对 bootstrap（plan §2.5；越想越退主判据，CI 全>0=显著回退）：
  B0→B3: 0.050 [-0.067,0.167]  ⚠CI 含0

go/no-go (plan §Phase 1): RR(natural=B3)≥0.20 或 ES 自 B0 降幅≥0.20pp，且 ≥60% 回退案例可归因反思片段（人工审计 30 条）。
layer 扫合格线 (plan §7): B0 下 ES≥0.90 & Loc≥0.85，否则该编辑器结果整体作废。
========== probe_llama8b_L5_c2 ==========
# editor=ROME  shards=8  错误行=0  解码臂=greedy  o_old/o_new 源=data/counterfact.jsonl
budget     n      ES     ESf      RR     RRs     CLR    Flip      PS     Loc  (n_para/n_loc)
B0        60   0.667   0.750   0.000   0.000   0.000   0.117       —   0.917  (0/60)
B3        60   0.500   0.600   0.150   0.025   0.350   0.150       —   0.850  (0/60)
RR=答案含旧(上界,含'守住+顺带提旧')  RRs=答案含旧且不含新(下界,ES镜像,最干净回退)  真回退率在两者之间

ES=严格(命中 o_new 且不含 o_old)  ESf=首段断言(答案首立场=编辑)  Flip=答案内两立场都现(先新后旧)  —— ESf≫ES 且 Flip↑ = 答案内『越想越退』(07 教训, FlipPoint 见 analysis/09)

95% bootstrap CI (n=10000, 按编辑条目重采样, plan §2.5)：
budget              ES [lo, hi]             RR [lo, hi]            CLR [lo, hi]
B0          0.667 [0.550,0.783]     0.000 [0.000,0.000]     0.000 [0.000,0.000]
B3          0.500 [0.367,0.633]     0.150 [0.050,0.275]     0.350 [0.233,0.467]

ES 降幅 ES(B0)−ES(b) 配对 bootstrap（plan §2.5；越想越退主判据，CI 全>0=显著回退）：
  B0→B3: 0.167 [0.017,0.317]  ✅CI>0 显著

go/no-go (plan §Phase 1): RR(natural=B3)≥0.20 或 ES 自 B0 降幅≥0.20pp，且 ≥60% 回退案例可归因反思片段（人工审计 30 条）。
layer 扫合格线 (plan §7): B0 下 ES≥0.90 & Loc≥0.85，否则该编辑器结果整体作废。
========== probe_llama8b_L7_c2 ==========
# editor=ROME  shards=8  错误行=0  解码臂=greedy  o_old/o_new 源=data/counterfact.jsonl
budget     n      ES     ESf      RR     RRs     CLR    Flip      PS     Loc  (n_para/n_loc)
B0        60   0.600   0.717   0.000   0.000   0.000   0.133       —   0.883  (0/60)
B3        60   0.517   0.617   0.306   0.167   0.467   0.183       —   0.900  (0/60)
RR=答案含旧(上界,含'守住+顺带提旧')  RRs=答案含旧且不含新(下界,ES镜像,最干净回退)  真回退率在两者之间

ES=严格(命中 o_new 且不含 o_old)  ESf=首段断言(答案首立场=编辑)  Flip=答案内两立场都现(先新后旧)  —— ESf≫ES 且 Flip↑ = 答案内『越想越退』(07 教训, FlipPoint 见 analysis/09)

95% bootstrap CI (n=10000, 按编辑条目重采样, plan §2.5)：
budget              ES [lo, hi]             RR [lo, hi]            CLR [lo, hi]
B0          0.600 [0.483,0.717]     0.000 [0.000,0.000]     0.000 [0.000,0.000]
B3          0.517 [0.383,0.650]     0.306 [0.167,0.472]     0.467 [0.333,0.600]

ES 降幅 ES(B0)−ES(b) 配对 bootstrap（plan §2.5；越想越退主判据，CI 全>0=显著回退）：
  B0→B3: 0.083 [-0.083,0.250]  ⚠CI 含0

go/no-go (plan §Phase 1): RR(natural=B3)≥0.20 或 ES 自 B0 降幅≥0.20pp，且 ≥60% 回退案例可归因反思片段（人工审计 30 条）。
layer 扫合格线 (plan §7): B0 下 ES≥0.90 & Loc≥0.85，否则该编辑器结果整体作废。