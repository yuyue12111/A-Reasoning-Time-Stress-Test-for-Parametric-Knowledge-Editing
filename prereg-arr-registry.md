# Pre-registration registry · Study 2 (append-only)

Entries are only ever appended. The freeze entry comes first; each model's pool manifest is appended
before that model's first Study-2 delta is computed (`prereg-arr.md` §9).

| # | date (UTC+8) | entry | value |
|---|---|---|---|
| 1 | 2026-10-08 11:41 | freeze | prereg-arr.md sha256 `1eeabd6a924a55d2da35e8b55fb8f71f9f81bb237b5ee2920d7c3727c9e2d9e7` at commit `a9b4139b11270ac86cde2e9f1f3589f7ac814633`; GitHub server push record (repos/…/activity) 2026-10-08T03:39:43Z; analysis code src/rt/study2.py `b18a3f529870fb51fffc08bdb1cf6ad20e850e24fea147d87f06d008908c7c8d`, src/rt/analysis.py `c94cd6123d4e3dcdb2a7a883669f65699da434033771af410dfd2ed4de13c959`, src/metrics.py `024dc94b6af21038cc2518bf6b1076908da6ef03c1978904d1d7bf3ea7631609`; configs study2_r1qwen32b.yaml `61b40295ad51`, pool_screen.yaml `c40525c6284e`, deltas_models.yaml `2c873e02f08e`; no Study-2 delta exists yet; OSF registration: none yet |
| 2 | 2026-10-08 11:41 | manifest | r1qwen32b 400 `dea4ca252fc1` (H2b unknown group 300 `0623792062fa`) |
| 3 | 2026-10-08 11:41 | manifest | r1llama70b 400 `807005f72193` |
| 4 | 2026-10-08 11:41 | manifest | r1qwen14b 400 `8bcec4e89e29` |
| 5 | 2026-10-08 11:41 | manifest | r1llama8b 400 `d38efea5f7e9` |
| 6 | 2026-10-08 11:41 | manifest | r1qwen7b 318 `d7057268858d` (fewer than 400 qualified: all used) |
| 7 | 2026-10-08 11:41 | manifest | r1qwen1_5b 212 `60f78a6546fe` (fewer than 400 qualified: all used) |
