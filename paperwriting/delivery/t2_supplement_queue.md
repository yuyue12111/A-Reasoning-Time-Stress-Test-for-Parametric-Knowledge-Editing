# T2 交付队列（7/29–7/31）—— supplement + code + checklist 兑现

排定于 W2-7（plan v1.98）。**本文件是 7/31 交付的唯一执行清单。**
每一行的存在理由：要么是**正文已写「in the supplement」的承诺**，要么是
**`checklist_provenance.md` 里标了「→ Task D 硬承诺」的 yes**。
兑现不了的，回头把对应 checklist 答案降级为 partial/no —— **不许留空头支票（M17）**。

## A. 正文已明写、必须存在的 supplement 内容（六处）

| # | 正文承诺处 | 必须交付 | 数据源 |
|---|---|---|---|
| A1 | §4 W-B 段 “The complete endpoint set is in the supplement.” | S/Pshuf/N 三臂边际 + B1(S−Pshuf)/B2(LocAcc)/S−N 全端点及 CI | `wb_representation_repair.confirm_arms` |
| A2 | §3.3 “The regression is in the supplement.” | B15 unedited-base recall 控制回归全表 | `emergence.b15_base_recall_control` |
| A3 | §3.3 “Both fits are in the supplement.” | percase 双 slope（matched / controlled）+ case-block CI | `emergence.percase` |
| A4 | §4.1 cloze installation sanity | **BLOCKED 工件按文件名声明其状态与限制**（不得静默） | 见 supp_manifest S7 |
| A5 | §5.5 末句「evidence ladder」 | Fig.2 `fig2_mechanism.{pdf,png,svg}` + 说明 | supp_manifest S7b |
| A6 | §5.5 末句「five-arm forest」 | Fig.3 `fig3_rq3.{pdf,png,svg}`；**当前缺 strict RRs 面板，入册前须补** | supp_manifest S3c |

## B. checklist 的 supplement-授权 yes（不兑现即须降级）

| checklist 项 | 承诺内容 | 降级后答案 |
|---|---|---|
| **4.2** 超参范围+判据 | S11 超参表：(i) 编辑层逐模型扫描与判据（Loc≥0.85 下取生成式 B0 ES 最高层）；(ii) **penalty=8 由冻结协议预先固定、六点扫描是事后稳健性检查——不得追认未记录的选择判据**；(iii) W-B 的 α∈{1,2,5}% 与 α*=1% 伤害门 | partial |
| **4.3/4.4/4.5** 代码与许可 | `data/build_dataset.py` + `src/` 全量 + 许可 | partial |
| **4.7** 基础设施 | 两套异构环境如实写：Hopper 侧 bf16 会使 ROME `compute_v` 发散成 NaN 故全程 `float32`；Ada 侧 bf16；n=40 校验可混用。版本以 `env.lock` 为准并**标注冻结日期 2026-06-10**（早于 GPU 主跑，不冒充跑时快照） | partial |
| **4.10** 每格运行次数 | S11 逐格运行次数表 | （yes/no 无 partial，须真做） |
| **4.12/4.13** 最终超参全表 | 同 4.2 的 S11 | partial |
| **3.3/3.4** 新数据集入附录+许可 | 41 条路由普查三判官投票、120 项面板的 87 条有效投票、`data/aliases.json`、`data/placebo_donors.json`、竞争者供体表 | partial |

## C. 独立交付物

- **prereg gate 全表**：X1 / X2 / X3 / P0 / P1 逐门阈值与实测 PASS-FAIL（含 X1 官方 **9/18 FAIL** 与 W-B G7 两轮）。
- **`src/anonymize.py`**：按 `prewrite/anonymize_spec.md`，至少覆盖 **L4（集群/存储路径 `/inspire/…`、`qb-ilm`、GPFS）与 L5（平台名）**。
- **`data/LICENSES.md`**：内容已在 `release_and_licenses.md` 起草完，搬运+核对即可。
- **`paperwriting/provenance_manifest.md`**：须含
  - **P14 的两层 provenance 分层**（见下）；
  - MATH-500 的 500 项子集来源（正文只引 Hendrycks et al. 2021，子集身份记这里）。

## D. P14 —— 唯一的外部依赖

服务器五臂 `esup_crossarm` v2 工件。**不阻塞 7/28**（正文取数自 `results.json` 是对的），
但 **7/31 释放的代码必须能重算出 `.193 / .122 / .002`**，否则复核者重跑主对比会对不上。

我方已确认的事实（W2-5 独立复核）：磁盘四臂版与 `results.json` **四处不符，且全部只涉及 P 臂**，
与「五臂重跑时 P 掉一行（200→199，.51→.507=101/199）」一致，与转录错误不一致；
唯一未解项 = **T−C ES 与旧 T−P ES 四位小数相同但 p 不同**。

**取不回来的处置**：在 `provenance_manifest.md` 明写该 artifact 的状态、上述四处差异、
以及「代码释出后主对比不可逐位复算」的限制。**诚实披露优于沉默，也优于降级正文数字。**

## E. 收口（7/31 前必做一次）

1. 完整 **dry-run 打包**：按将要上传的目录结构真打一次包并解开验证。
2. **scrub-grep**：平台名 / 集群路径 / 作者身份 / 邮箱 / 本机绝对路径，零命中。
3. 跑不通就按 M17 **诚实降级 checklist 答案**并回改 `checklist_provenance.md` 对应行。
