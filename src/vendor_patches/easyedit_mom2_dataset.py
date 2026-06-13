"""EasyEdit mom2 语料加载修复（datasets≥3 弃用脚本式数据集 → 老 id 必崩；MEMIT/AlphaEdit-blocker）。
v2 (2026-06-12)：增加**本地 parquet 直读分支**——启智平台完全无外网，但已挂载
`/inspire/dataset/wikipedia/20231101/20231101.en/train-*-of-00041.parquet`（report.md §1）；
hub 路径（哪怕映射成 wikimedia/wikipedia）在 `HF_HUB_OFFLINE=1` 且无本地缓存时仍会崩（report §7 问题 A）。

问题（2026-06-12 在 editrev/datasets 4.8.5 实测）：
  `source/EasyEdit/easyeditor/models/rome/layer_stats.py:104` 写死
      load_dataset("wikipedia", "20200501.en")   # 或 ("wikitext","wikitext-103-raw-v1")
  - "wikipedia" 是脚本式数据集 → datasets≥3 直接 RuntimeError("Dataset scripts are no longer supported")
  - 裸名 "wikitext" 的 canonical 解析在 4.8.5 同样报 HfUriError
  影响面：mom2 协方差是 MEMIT/AlphaEdit 的前置（ROME qwen yaml `mom2_adjustment:false` 不受影响）。
  ROME/MEMIT/AlphaEdit 三处 get_cov 全部 `from ..rome.layer_stats import layer_stats` —— 函数体内的
  `load_dataset` 按**定义模块**(rome.layer_stats) 的全局名解析 → patch 一处全覆盖。

修法：把 rome.layer_stats 模块内的 `load_dataset` 换成薄 shim，按优先级：
  (1) **本地 parquet 直读**（离线平台）：请求是 wikipedia 类（老 id 或已映射 id）且本地 parquet 存在 →
      `load_dataset("parquet", data_files={"train": [分片...]})`，完全不碰 hub（HF_*_OFFLINE 下安全）。
      位置 = 环境变量 `WHYAAAI_WIKI_PARQUET`（目录或 glob，优先）或启智默认挂载路径。
      返回 DatasetDict 含 "train" split —— layer_stats 只取 `raw_ds["train"]`，drop-in。
  (2) **id 映射**（有网/有缓存）：老 (name, config) 映射到现行 parquet 仓（无需脚本/trust_remote_code，
      2026-06-12 经 load_dataset_builder 实测可解析）：
        ("wikipedia", "20200501.en")         -> ("wikimedia/wikipedia", "20231101.en")   # 20.2GB, train
        ("wikitext", "wikitext-103-raw-v1")  -> ("Salesforce/wikitext", "wikitext-103-raw-v1")  # 549MB 备选
  (3) 其余调用原样透传。
所有数据源行字段均含 "text"（TokenizedDataset 默认 field="text"），drop-in 兼容。

口径注记：协方差语料统一为 wikipedia **2023-11 dump**（启智挂载与 wikimedia/wikipedia/20231101.en
同一 dump；与 MEMIT 原文 2020-05 不同，统计量级一致）；stats 缓存文件名由 ds_name("wikipedia")
派生 → 命名不变，我们的 stats_dir 本就按模型分目录。论文 reproducibility 一节如实写明 dump 版本即可。

用法：`apply()`（幂等），须在首次触发 mom2 的 edit() 之前生效——`edit_loop.run` 已与 qwen 路由补丁
一并自动接入。"""
import glob as _glob
import os
from datasets import load_dataset as _REAL_LOAD_DATASET

# 老 (name, config) -> 现行 parquet 仓（datasets≥3 可加载，无需脚本）
DATASET_REMAP = {
    ("wikipedia", "20200501.en"): ("wikimedia/wikipedia", "20231101.en"),
    ("wikitext", "wikitext-103-raw-v1"): ("Salesforce/wikitext", "wikitext-103-raw-v1"),
}
# 视为「wikipedia 语料请求」的 (name, config)——本地 parquet 存在时优先直读（wikitext 不在此列）
WIKI_REQUESTS = {("wikipedia", "20200501.en"), ("wikimedia/wikipedia", "20231101.en")}
# 本地 parquet 位置：env 显式指定（目录或 glob）> 启智平台默认挂载（report.md §1）
LOCAL_WIKI_ENV = "WHYAAAI_WIKI_PARQUET"
LOCAL_WIKI_DEFAULT = "/inspire/dataset/wikipedia/20231101/20231101.en"


def local_wiki_files():
    """返回本地 wikipedia parquet 分片列表（sorted），找不到返回 None。"""
    spec = os.environ.get(LOCAL_WIKI_ENV) or LOCAL_WIKI_DEFAULT
    if os.path.isdir(spec):
        spec = os.path.join(spec, "*.parquet")
    files = sorted(_glob.glob(spec))
    return files or None


def patched_load_dataset(name, config=None, *args, **kwargs):
    if (name, config) in WIKI_REQUESTS:
        files = local_wiki_files()
        if files:                                # 离线平台：本地 parquet 直读，不碰 hub
            return _REAL_LOAD_DATASET("parquet", data_files={"train": files}, **kwargs)
    name, config = DATASET_REMAP.get((name, config), (name, config))
    return _REAL_LOAD_DATASET(name, config, *args, **kwargs)


def apply():
    """把 easyeditor.models.rome.layer_stats 模块内引用的 load_dataset 换成 shim。
    幂等；返回被 patch 的模块对象（便于断言/调试）。MEMIT/AlphaEdit/ROME 的 get_cov 均经此模块。"""
    from easyeditor.models.rome import layer_stats as ls_mod   # 惰性 import：调用时 easyeditor 必已可导入
    ls_mod.load_dataset = patched_load_dataset
    return ls_mod
