"""EasyEdit mom2 语料加载修复（datasets≥3 弃用脚本式数据集 → 老 id 必崩；MEMIT/AlphaEdit-blocker）。

问题（2026-06-12 在 editrev/datasets 4.8.5 实测）：
  `source/EasyEdit/easyeditor/models/rome/layer_stats.py:104` 写死
      load_dataset("wikipedia", "20200501.en")   # 或 ("wikitext","wikitext-103-raw-v1")
  - "wikipedia" 是脚本式数据集 → datasets≥3 直接 RuntimeError("Dataset scripts are no longer supported")
  - 裸名 "wikitext" 的 canonical 解析在 4.8.5 同样报 HfUriError
  影响面：mom2 协方差是 MEMIT/AlphaEdit 的前置（ROME qwen yaml `mom2_adjustment:false` 不受影响）。
  ROME/MEMIT/AlphaEdit 三处 get_cov 全部 `from ..rome.layer_stats import layer_stats` —— 函数体内的
  `load_dataset` 按**定义模块**(rome.layer_stats) 的全局名解析 → patch 一处全覆盖。

修法：把 rome.layer_stats 模块内的 `load_dataset` 换成薄 shim，将老 (name, config) 映射到
现行 parquet 仓（无需脚本/trust_remote_code，2026-06-12 经 load_dataset_builder 实测可解析）：
  ("wikipedia", "20200501.en")            -> ("wikimedia/wikipedia", "20231101.en")   # 20.2GB, train
  ("wikitext",  "wikitext-103-raw-v1")    -> ("Salesforce/wikitext", "wikitext-103-raw-v1")  # 549MB 轻量备选
其余调用原样透传。两个替代源的行字段均含 "text"（TokenizedDataset 默认 field="text"），drop-in 兼容。

口径注记：协方差语料从 2020-05 dump 换为 2023-11 dump（与 MEMIT 原文不同 dump，统计量级一致）；
stats 缓存文件名由 ds_name("wikipedia") 派生 → 命名不变，我们的 stats_dir 本就按模型分目录。
论文 reproducibility 一节如实写明 dump 版本即可。

用法：`apply()`（幂等），须在首次触发 mom2 的 edit() 之前生效——`edit_loop.run` 已与 qwen 路由补丁
一并自动接入。"""
from datasets import load_dataset as _REAL_LOAD_DATASET

# 老 (name, config) -> 现行 parquet 仓（datasets≥3 可加载，无需脚本）
DATASET_REMAP = {
    ("wikipedia", "20200501.en"): ("wikimedia/wikipedia", "20231101.en"),
    ("wikitext", "wikitext-103-raw-v1"): ("Salesforce/wikitext", "wikitext-103-raw-v1"),
}


def patched_load_dataset(name, config=None, *args, **kwargs):
    name, config = DATASET_REMAP.get((name, config), (name, config))
    return _REAL_LOAD_DATASET(name, config, *args, **kwargs)


def apply():
    """把 easyeditor.models.rome.layer_stats 模块内引用的 load_dataset 换成 shim。
    幂等；返回被 patch 的模块对象（便于断言/调试）。MEMIT/AlphaEdit/ROME 的 get_cov 均经此模块。"""
    from easyeditor.models.rome import layer_stats as ls_mod   # 惰性 import：调用时 easyeditor 必已可导入
    ls_mod.load_dataset = patched_load_dataset
    return ls_mod
