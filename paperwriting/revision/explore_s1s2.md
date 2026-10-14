# Exploratory: why the 32B effect shrank from Study 1 to Study 2 (post hoc)

Plan and addenda: `explore_s1s2_plan.md` (E5b, E6, E6b were added after earlier results were seen). Numbers: `explore_s1s2.json`. Nothing here is confirmatory.

| run | ES@B0 | ES drop | erosion given ES@B0 | repair | retention contrast |
|---|---|---|---|---|---|
| S1 | 0.601 | +0.106 [+0.030, +0.182] | +0.345 [+0.261, +0.429] | 0.101 | +0.216 [+0.091, +0.341] |
| G0-4090 | 0.615 | +0.130 [+0.055, +0.205] | +0.366 [+0.285, +0.455] | 0.095 | +0.239 [+0.102, +0.375] |
| G0-H100 | 0.610 | +0.085 [+0.010, +0.160] | +0.311 [+0.230, +0.393] | 0.105 | +0.207 [+0.069, +0.333] |
| S2 | 0.708 | +0.037 [-0.010, +0.087] | +0.201 [+0.155, +0.247] | 0.105 | +0.029 [-0.036, +0.097] |

**E0 hardware** (same 200 cases, 4090 − H100): ES drop +0.045 [-0.015, +0.110], p=0.182; B0 outcome agreement 0.975, B3 0.810; retention +0.032 [-0.162, +0.215], p=0.770.

**E1 matched hardware** (S2 − G0-H100): ES drop -0.048 [-0.135, +0.042], p=0.305; erosion given ES@B0 -0.110 [-0.205, -0.017], p=0.018; repair +0.000 [-0.053, +0.052], p=1.000; retention -0.178 [-0.321, -0.030], p=0.019.

**E2 Study 2's qualification rule on the Study 1 cases**: S1 109/198: drop +0.147 [+0.037, +0.257], retention +0.154 [+0.013, +0.295]; G0-4090 102/200: drop +0.186 [+0.078, +0.294], retention +0.169 [+0.013, +0.312]; G0-H100 102/200: drop +0.137 [+0.029, +0.245], retention +0.158 [+0.013, +0.303]; S2 392/400: drop +0.038 [-0.010, +0.087], retention +0.029 [-0.036, +0.097]

**E3 base chain at B3 names o_old** (erosion given ES@B0, moderator 1 − 0): S1 prevalence 0.83, +0.118 [-0.080, +0.307], p=0.232; G0-4090 prevalence 0.85, +0.059 [-0.180, +0.275], p=0.587; G0-H100 prevalence 0.86, +0.120 [-0.091, +0.312], p=0.262; S2 prevalence 0.93, -0.008 [-0.186, +0.152], p=0.983

**E4 relation mix**: S2 drop reweighted to S1's relation mix +0.027 [-0.042, +0.097]; G0-H100 reweighted to S2's mix +0.096 [+0.030, +0.164].

**E5/E5b edit strength** (first-token log p(o_old) after the edit): S2 AUC 0.661, high − low erosion +0.161 [+0.069, +0.253], p=0.001; on the Study 1 cases AUC 0.502 (G0-H100), share of the erosion gap explained 0.00.

## E6/E6b fact salience (number of the small distills 1.5B, 7B, 14B, Llama-8B whose base names o_old at B0)

| S2 salience | n (retention set) | edited loss | base loss | retention contrast | ES@B0 | ES drop |
|---|---|---|---|---|---|---|
| 0 of 4 | 31 | 0.129 | 0.387 | -0.258 [-0.484, +0.000] | 0.810 | +0.048 |
| 1 of 4 | 74 | 0.122 | 0.216 | -0.095 [-0.216, +0.027] | 0.776 | -0.020 |
| 2 of 4 | 73 | 0.151 | 0.164 | -0.014 [-0.123, +0.096] | 0.712 | -0.029 |
| 3 of 4 | 63 | 0.317 | 0.079 | +0.238 [+0.111, +0.365] | 0.649 | +0.134 |
| 4 of 4 | 36 | 0.306 | 0.056 | +0.250 [+0.083, +0.417] | 0.610 | +0.085 |

S2, high (3–4) vs low (0–2): ES drop +0.115 [+0.032, +0.199], p=0.006 vs -0.012 [-0.074, +0.049], p=0.747; erosion given ES@B0 +0.313 [+0.222, +0.404] vs +0.141 [+0.092, +0.196]; retention +0.242 [+0.141, +0.343] vs -0.090 [-0.174, -0.011], difference +0.332 [+0.203, +0.464], p=0.000.

Share of high-salience cases: Study 1 0.59, Study 2 0.39.

| Study 1 cases | high: n, edited loss, base loss, retention | low: n, retention | high − low |
|---|---|---|---|
| Qwen-32B S1 | 57, 0.386, 0.088, +0.298 [+0.158, +0.439] | 29, +0.034 [-0.207, +0.276] | +0.264 [-0.029, +0.557], p=0.068 |
| Qwen-32B G0-H100 | 58, 0.345, 0.069, +0.276 [+0.121, +0.414] | 27, +0.111 [-0.148, +0.370] | +0.165 [-0.132, +0.456], p=0.280 |
| Qwen-32B G0-4090 | 60, 0.400, 0.083, +0.317 [+0.167, +0.467] | 26, +0.038 [-0.269, +0.346] | +0.278 [-0.054, +0.614], p=0.098 |
| Qwen-14B S1 | 32, 0.344, 0.062, +0.281 [+0.094, +0.469] | 54, +0.130 [-0.037, +0.296] | +0.152 [-0.109, +0.407], p=0.250 |
| Llama-70B S1 | 57, 0.386, 0.070, +0.316 [+0.175, +0.456] | 34, +0.118 [-0.059, +0.294] | +0.198 [-0.025, +0.422], p=0.091 |
