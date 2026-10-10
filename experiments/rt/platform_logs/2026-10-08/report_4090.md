# report_4090 · why-t2t3 (8x4090-48G) · 执行单 #6

## A1 ✓ 03:09–03:14
- torch 2.8.0a0+5228986c39.nv25.06 ✓；transformers 5.5.4 ✓
- run_all.py: 193 passed, 0 failed, exit=0 ✓

## A2 ✓ 03:09–03:18
- freeze_4090.txt 312 包 ✓；h100_need=zstandard==0.25.0 + pyver=3.12 → wheel 已下载
- $SHARE/wheels/DONE ✓；wheels_failed.txt 空 ✓

## A3 ✗ 03:10–03:10（转后台重试）
- model_info = gemma ok；snapshot_download = GatedRepoError 403（账号未接受许可）
- [补充一] gemma_retry.sh 每 30min 自动重试中；J 时按目录完整性决定单/双判官

## A4 ✓ 03:11–03:40:52
- 03:39:43Z 推送 → 03:40:52 检出（延迟 69s）✓
- pull: fe8b5e5 → 90c704b，status 空 ✓；manifest 行数 400/300/400/400/400/318/212 ✓；FREEZE_PULLED ✓

## D1 ✓ 03:40:59–05:06:03
- cases=400 ok=400 errors=0 editor_nan=0 max_rank=1 ✓（全条件满足）
- median_p_target_after=0.9897；median_rel_delta=0.0213；max_rel_err=3.97e-06；median_wall_s=23.3s
- $SHARE/D1_DONE: -rw-r--r-- 1 root root 0 2026-10-08 05:15:13.104208469 +0000 /inspire/hdd/project/ai4education/public/why/xfer/D1_DONE
- 注：校验脚本 parse bug 曾误记 FAIL；实测数字以 summarize_D1.json 为准；D1_DONE 已 touch

- 32B H2b K=4 W=2；首批 rank 于 05:06 启动，05:15 起接续（42/300 时队列修复重启，断点续跑）
## D2 ✓ 05:06:03–06:06:58
- cases=300 ok=300 errors=0 editor_nan=0 max_rank=1 ✓
- median_p_target_after=0.9911；median_rel_delta=0.0207；max_rel_err=4.37e-06；median_wall_s=21.8s
- D2_DONE 已 touch（H100 可见）

## D3 14B
## D1 32B main pool ROME K=4 W=2

## D2 32B unknown group H2b K=4 W=2

- smoke exit 0
## D3 ✓ 06:23:44–06:28:14
- summarize: cases=400 ok=400 errors=0 nan=0 max_rank=1
- median_p_target_after=0.9569；median_rel_delta=0.0385；max_rel_err=1.19e-06；median_wall_s=8.99

## D4 Llama-8B
- smoke exit 0, full K=1 W=8
## D4 ✓ 06:28:14–06:34:34
- summarize: cases=400 ok=400 errors=0 nan=0 max_rank=1

## D5 7B
- smoke exit 0, full K=1 W=8
## D5 ✓ 06:34:34–06:40:06
- summarize: cases=318 ok=318 errors=0 nan=0 max_rank=1

## D6 1.5B K=1 W=8
## D6 ✓ 06:40:06–06:42:25
- summarize: cases=212 ok=212 errors=0 nan=0 max_rank=1

## ST 32B cov stats
- ST-a prepare exit=0

## D4 ✓ 06:29-06:33
- cases=400 ok=400 errors=0 nan=0 max_rank=1 (max_rel_err=1.35e-06)
## D5 ✓ -06:42
- cases=318 ok=318 errors=0 nan=0 max_rank=1
## D6 ✓ -06:42
- cases=212 ok=212 errors=0 nan=0 max_rank=1
- ST/D7/D8 cancelled (deviation D4); code synced to 0fb3cbc, PULLED_0fb3cbc touched

## D70 Llama-70B ROME K=8 W=1

- cases=400 ok=400 errors=0 nan=0 max_rank=1 (max_rel_err=1.35e-06)
- cases=318 ok=318 errors=0 nan=0 max_rank=1
- cases=212 ok=212 errors=0 nan=0 max_rank=1
- ST/D7/D8 cancelled (deviation D4); code synced to 0fb3cbc, PULLED_0fb3cbc touched

## D70 Llama-70B ROME K=8 W=1

## GS 14B generation
- smoke exit 0
