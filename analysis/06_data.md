# 06 · 数据提取笔记 + 数据卡（CounterFact / zsRE / MQuAKE-CF-3k）

- **日期**: 2026-06-11 ｜ **状态**: 三数据集清洗完成 ✅、aliases v0 ✅、数据卡完成 ✅
- **任务（plan Phase 0 #06）**: 三源清洗为统一 jsonl schema + 数据卡；副产 `data/aliases.json` 喂 `metrics.py`
- **构建脚本**: `src/build_dataset.py`（纯 JSON、无需 torch，仓库根 `python src/build_dataset.py` 即重建）

---

## 1. 产出清单与再生方式

| 文件 | 内容 | 入库? |
|---|---|---|
| `data/counterfact.jsonl` | CounterFact 清洗，**21,919** 条 | ❌ gitignore（17M，可再生） |
| `data/zsre.jsonl` | zsRE 清洗，**18,377** 条 | ❌ gitignore（6.8M，可再生） |
| `data/mquake_cf_3k.jsonl` | MQuAKE-CF-3k 清洗，**3,000** 条 | ❌ gitignore（2.4M，可再生） |
| `data/aliases.json` | {target: [别名]}，**1,285** 实体 | ✅ 入库（140K，metrics 依赖） |
| `data/sample_records.jsonl` | 每源 2 条样例（看 schema 用） | ✅ 入库（6 条） |
| `data/raw/{counterfact,zsre_mend_eval}.json` | memit 下载的原始源 | ❌ gitignore（51M） |

**再生**：① 原始源——CounterFact/zsRE 从 `https://memit.baulab.info/data/dsets/{counterfact,zsre_mend_eval}.json` 下载到 `data/raw/`；MQuAKE-CF-3k 在 `source/MQuAKE/datasets/`（随仓库克隆）。② `python src/build_dataset.py` 一键清洗（确定性，无随机）。

## 2. 统一 schema（每行一条 JSON）

```json
{"case_id":"cf_0", "source":"counterfact", "s":"Danielle Darrieux", "r":"P103",
 "prompt":"The mother tongue of Danielle Darrieux is", "o_old":"French", "o_new":"English",
 "o_old_aliases":[], "o_new_aliases":[], "paraphrases":["…"], "neighborhood":["…"], "hops":[]}
```

| 字段 | 含义 / 约定 |
|---|---|
| `case_id` | `<source>_<原id>`，全局唯一 |
| `s` | subject。**是 `prompt` 的子串**（满足 EasyEdit `assert subject in prompt`，见 §5） |
| `r` | relation_id（CF/MQuAKE 有 PXX；zsRE 为 null） |
| `prompt` | **已填 subject** 的编辑 cloze；EasyEdit 内部再把 subject→`{}` |
| `o_old` | 旧事实=回退目标（CF/MQuAKE=target_true；zsRE=answers[0]） |
| `o_new` | 编辑目标（CF/MQuAKE=target_new；zsRE=alt） |
| `o_old_aliases`/`o_new_aliases` | 该条编辑对象的别名（MQuAKE 从 single_hops 取；CF/zsRE 暂空，靠全局 aliases.json 兜底） |
| `paraphrases` | ES-paraphrase 探针（CF 多条；zsRE=rephrase 1 条；MQuAKE 无） |
| `neighborhood` | locality 探针（CF 多条；zsRE=loc 的 nq 问题；MQuAKE 无） |
| `hops` | 多跳问题（仅 MQuAKE，portability 用）；MQuAKE 另带 `n_rewrites`/`hop_answer_old`/`hop_answer_new` |

## 3. 三数据集逐个（映射决策 + 雷点）

| 源 | n | o_old → o_new | paraphrase | neighborhood | 备注 |
|---|---|---|---|---|---|
| **CounterFact** | 21,919 | target_true → target_new（反事实，干净） | 全有 | 全有 | 主编辑数据；prompt 模板已填 subject |
| **zsRE** | 18,377 | **answers[0] → alt**（反事实） | rephrase | loc(nq question) | 从 19,086 跳过 709 退化条（alt 缺失或 alt==o_old） |
| **MQuAKE-CF-3k** | 3,000 | target_true → target_new | 无 | 无 | hops=多跳问题；`n_rewrites` 分布 {1:1093, 2:1067, 3:572, 4:268} |

**关键映射决策**：
- **zsRE 用 `alt` 作 o_new（不是 answers[0]）**：memit 自带 loader 把 target_new 设成 answers[0]（"教正确答案"语义），但我们研究的是**反事实编辑后的回退**，需要 o_old=真答案(answers[0])→o_new=反事实(alt)。zsRE 99% 有 alt，故这样映射后 zsRE 与 CounterFact 语义一致（都是"真→假"），且**有真实 o_old**（不必留 null 等预过滤）。
- **zsRE `answers[1:]` 不是别名**：457 条多答案记录的 answers[1:] 是"其它可接受答案"（如 `['bronze','concrete']`、`['Roanoke River','Smith Mountain Lake']`），不是同义别名——**已排除出 o_old_aliases 与 aliases.json**，否则污染 `metrics.hit` 判分（曾误收 `'2012':['1989']` 这类噪声，已修）。这 457 条 o_old 语义有歧义（多个真答案），保留 o_old=answers[0]，由 §2.3 预过滤用模型实际 greedy 输出定夺。
- **MQuAKE 取 `requested_rewrite[0]` 作主编辑**：1,907/3,000 是多编辑 case（n_rewrites>1）；单条编辑协议下主用 1,093 条单编辑 case 最干净，多编辑 case 的完整链留给 portability 测试（`hops` + `hop_answer_new`）。o_old/o_new 别名从 `single_hops`/`new_single_hops` 里 answer==target 的 `answer_alias` 取（2,891/3,000 命中）。

## 4. aliases.json（v0）

- **1,285 个实体**有别名，来源：MQuAKE 的 single_hops/new_single_hops + 多跳最终答案的 `answer_alias`（皆为 Wikidata 风格真别名，如 `A. A. Milne → [A.A. Milne, Alan Alexander Milne, Alan Milne]`）。
- **覆盖率**（编辑对象命中 aliases.json）：**CF 81%（17,753/21,919）**、MQuAKE 99%、zsRE 18%。CF 自身无别名串（只有 QID），靠与 MQuAKE 共享实体池的字符串匹配吃到 81% 覆盖——v0 已够用。
- **TODO（待富集）**：CF/zsRE 用各自的 Wikidata QID（CF requested_rewrite.target_*.id）查 Wikidata `aliases` 补全 zsRE（18%）与 CF 尾部；判分前对 10% 边界样本人工/judge 校准（plan §2.5）。

## 5. ⭐ 给下游的接法（edit_loop / metrics）——含一个 pilot-blocker

**编辑调用必须传 subject**（源码实证 `editor.py` → `editors/utils.py:_prepare_requests`）：只有当 `subject` 传入 `edit()` 时，request 才带 `subject` 键且断言 `subject in prompt`；**不传则 ROME/MEMIT 拿不到 subject 必失败**。我们的 `prompt` 已填 subject、`s` 是其子串，满足断言。

**⚠️ `src/edit_loop.py` v0 与本 schema 有两处不匹配（pilot 接线前必修，已确诊）**：
1. `run()` 调 `ed.edit(prompts=[c["prompt"]], ground_truth=[c["o_old"]], target_new=[c["o_new"]], …)` **未传 `subject=`** → ROME/MEMIT 无 subject 报错。**修**：加 `subject=[c["s"]]`。
2. `probes()` 用 `case['subject']`，但本 schema 字段名是 **`s`**（plan §06 schema 即 `s`）。**修**：`case['subject']` → `case['s']`（共 1 处，`open` 探针那行）。

（这两处属 harness 接线、需模型端联调，留 Phase 1 pilot 接线时连同 §12.2 一起改并 +0.1 记 plan；本笔记已精确定位。）

**metrics 用法**：`metrics.score(jsonl, cases, aliases)` 的 `aliases` 传 `json.load(open("data/aliases.json"))`；`cases` 传清洗后的行（含 o_old/o_new/case_id）。注意 metrics `hit()` 是子串命中——别名表越准越好（§4 已去噪）。

## 6. 雷点登记

1. **zsRE answers[1:] ≠ 别名**（§3）——已排除；任何二次处理 zsRE 勿把多答案当别名。
2. **zsRE 457 条多答案 o_old 有歧义**——预过滤用模型 greedy 实际输出定 o_old。
3. **MQuAKE 多编辑 case（1,907 条）**——单条协议主用单编辑 1,093 条；多编辑链仅 portability。
4. **edit_loop 字段名 `s` vs `subject` + 缺 subject= 传参**（§5）——pilot 接线前必修。
5. **大文件 gitignore**——三大 jsonl + raw 不入库，靠 `build_dataset.py` 再生；`唯一真源`是脚本+原始源 URL，不是产物。

## 7. 待办

- [ ] Wikidata QID 富集 aliases（CF/zsRE 覆盖率↑）；判分 10% 边界样本校准
- [ ] pilot 抽样：CounterFact 预过滤（模型 pre-edit greedy(s,r)==o_old）后取 200（pilot）/1000（主），×2 冗余（plan §2.3 存活率 40–60%）
- [ ] 修 `edit_loop.py` 的 `s`/subject 两处（§5），随 Phase 1 接线
