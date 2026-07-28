# W4 gate-change ledger

规则（W4 计划 §0 门修订铁律）：每处正文手术若删/改 checker required string、顺序门、
白名单，必须同 commit 修订对应门条目，并在此记一行：被改门 → 理由 → 被删字符串的去向
（supplement 节 + Discharges 引文 / 保留位点）。

| # | Track | 被改门（check_manuscript.py） | 理由 | 去向 |
|---|-------|------------------------------|------|------|
| 1 | B1a | `APPROVED_PROSPECTIVE_LABEL_SITES`（:299）由 1 项清空 | 门真值审计：X1 manifest SHA 钉内容不钉日期，"prospectively" 的时间性主张 git 无法佐证 | 正文 :144 改述为 manifest-SHA/协议文档措辞；扫描门保留且白名单为空 → 全文禁用该词 |
| 2 | B1a | §4 required string `prospectively specified attempt`（原 :1382）替换 | 同上；被替换字符串的时间性主张为不可证 | 换绑两条新披露：`pinned by a SHA-256 manifest` + `its stop rule recorded in the accompanying protocol document`（均在 :144 新句） |
| 3 | B1a | 正文 :259 `the vehicle specified in advance` 改述（非门字符串，记录以备核） | 同一日期不可证类；w3_gate_truth_audit.md X1 节 | `the manifest-pinned replay vehicle failed its own validity gate` — 撤回语义不变 |
| 4 | B1b | §4 required string `one external judge-model family`（原 :1378）删除 | 门真值审计：仅 validation panel 判官族有记录，"external" 与 census panel 身份均无记录支持；载体 fn6 收窄为仅 κ 句 | 收窄后的披露移入 §3 fn2：`error independence across panels cannot be assessed`，并作为第 4 目标加入 D2 债务门元组（全文级钉定）；`shared-bias risk` 词组保留于 fn2 |
| 5 | B1b | 正文 :253 `Both judge panels come from one model family` 收窄（非门字符串） | 同上；census/membership panel 判官身份未记录，原句为越证据主张 | `No judge panel has a human-audited subsample, and where a judge family is recorded it is a single one, so shared judge bias would not surface.` |
| 6 | B1c | §5 子节标题元组（:1622）`A Signed, Dose-Graded Think-Span Intervention` → `A Signed Think-Span Intervention` | 用户授权全局清除 dose-graded（:183 真值锚「not ordered across those settings」拒绝 graded 主张） | 标题与 :56 四性质句均退到 signed；摘要占位待 Track F 同步；test_check_manuscript.py:1023 同步 |
