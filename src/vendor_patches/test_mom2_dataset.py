"""easyedit_mom2_dataset 单测（mom2 语料加载修复；MEMIT/AlphaEdit-blocker）。

全 stub datasets + easyeditor.models.rome.layer_stats，无 GPU/无下载，system python3 即可。
断言：(1) 老 wikipedia/wikitext id 被映射到现行 parquet 仓 (2) 未知 id 原样透传(含 kwargs)
(3) apply() 换掉 layer_stats 模块属性且幂等 (4) v2：本地 parquet 存在时 wikipedia 类请求
直读 ("parquet", data_files={"train":[分片...]})、wikitext 不受影响（启智离线分支，report §7 问题 A）。
运行：python3 src/vendor_patches/test_mom2_dataset.py
"""
import sys, os, types, tempfile

# ============ stub datasets（必须在 import patch 之前装好）============
CALLS = []
def _fake_load_dataset(name, config=None, *a, **kw):
    CALLS.append({"name": name, "config": config, "kwargs": dict(kw)})
    return {"train": f"DS[{name}/{config}]"}

_ds = types.ModuleType("datasets")
_ds.load_dataset = _fake_load_dataset
sys.modules["datasets"] = _ds

# ============ stub easyeditor.models.rome.layer_stats（apply() 要 patch 它）============
_ls = types.ModuleType("easyeditor.models.rome.layer_stats")
_ls.load_dataset = _fake_load_dataset            # layer_stats.py:5 import 进来的名字
_rome = types.ModuleType("easyeditor.models.rome"); _rome.layer_stats = _ls
_models = types.ModuleType("easyeditor.models"); _models.rome = _rome
_ee = types.ModuleType("easyeditor"); _ee.models = _models
for k, v in [("easyeditor", _ee), ("easyeditor.models", _models),
             ("easyeditor.models.rome", _rome), ("easyeditor.models.rome.layer_stats", _ls)]:
    sys.modules[k] = v

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import easyedit_mom2_dataset as P  # noqa: E402

# 测试隔离：默认把本地分片探测钉死到不存在路径——否则在启智平台上跑本测试时，
# 真实的 /inspire/dataset/wikipedia 挂载会让 hub-映射断言被 parquet 分支"劫持"而误失败
# （interplan2 §2 的平台自检正要跑本套测试）。仅 test_local_parquet_divert 自设真目录。
NO_LOCAL = os.path.join(os.sep, "nonexistent-whyaaai-wiki")
os.environ[P.LOCAL_WIKI_ENV] = NO_LOCAL


# ============ 测试 ============
def test_remap_legacy_wikipedia():
    CALLS.clear()
    out = P.patched_load_dataset("wikipedia", "20200501.en")
    assert CALLS[-1]["name"] == "wikimedia/wikipedia", f"应映射到 wikimedia/wikipedia: {CALLS[-1]}"
    assert CALLS[-1]["config"] == "20231101.en", f"config 应为 20231101.en: {CALLS[-1]}"
    assert out["train"] == "DS[wikimedia/wikipedia/20231101.en]"


def test_remap_legacy_wikitext():
    CALLS.clear()
    P.patched_load_dataset("wikitext", "wikitext-103-raw-v1")
    assert CALLS[-1]["name"] == "Salesforce/wikitext", f"应映射到 Salesforce/wikitext: {CALLS[-1]}"
    assert CALLS[-1]["config"] == "wikitext-103-raw-v1"


def test_passthrough_unknown_and_kwargs():
    CALLS.clear()
    P.patched_load_dataset("wikimedia/wikipedia", "20231101.en", split="train", streaming=True)
    assert CALLS[-1]["name"] == "wikimedia/wikipedia", "已是新 id 应原样透传"
    assert CALLS[-1]["kwargs"] == {"split": "train", "streaming": True}, "kwargs 应透传"
    CALLS.clear()
    P.patched_load_dataset("c4", "en")
    assert CALLS[-1] == {"name": "c4", "config": "en", "kwargs": {}}, "无关数据集应透传"


def test_apply_swaps_attr_idempotent():
    ls = P.apply()
    assert ls.load_dataset is P.patched_load_dataset, "layer_stats.load_dataset 应被换成 shim"
    P.apply()
    assert ls.load_dataset is P.patched_load_dataset, "幂等"
    # 经被 patch 的模块名调用 → 仍走映射（即 layer_stats 函数体内的解析路径）
    CALLS.clear()
    ls.load_dataset("wikipedia", "20200501.en")
    assert CALLS[-1]["name"] == "wikimedia/wikipedia", "经 layer_stats 模块调用也应映射"


def test_local_parquet_divert():
    """v2：WHYAAAI_WIKI_PARQUET 指向本地分片时，wikipedia 类请求直读 parquet、不碰 hub。"""
    with tempfile.TemporaryDirectory() as d:
        f1 = os.path.join(d, "train-00000-of-00002.parquet")
        f2 = os.path.join(d, "train-00001-of-00002.parquet")
        for f in (f1, f2):
            open(f, "w").close()
        os.environ[P.LOCAL_WIKI_ENV] = d                      # 目录形式
        try:
            for req in [("wikipedia", "20200501.en"), ("wikimedia/wikipedia", "20231101.en")]:
                CALLS.clear()
                P.patched_load_dataset(*req)
                c = CALLS[-1]
                assert c["name"] == "parquet", f"{req} 应直读 parquet: {c}"
                assert c["kwargs"]["data_files"] == {"train": [f1, f2]}, f"分片应 sorted 列表: {c}"
            CALLS.clear()                                     # wikitext 不属 wikipedia 请求 → 仍走映射
            P.patched_load_dataset("wikitext", "wikitext-103-raw-v1")
            assert CALLS[-1]["name"] == "Salesforce/wikitext", f"wikitext 不应被 parquet 劫持: {CALLS[-1]}"
            os.environ[P.LOCAL_WIKI_ENV] = os.path.join(d, "*.parquet")   # glob 形式等价
            CALLS.clear()
            P.patched_load_dataset("wikipedia", "20200501.en")
            assert CALLS[-1]["name"] == "parquet" and CALLS[-1]["kwargs"]["data_files"]["train"] == [f1, f2]
        finally:
            os.environ[P.LOCAL_WIKI_ENV] = NO_LOCAL   # 复位到不存在路径（非 del，否则平台回落真挂载）
    # 临时目录已删、env 指向不存在路径 → local_wiki_files 返回 None、回落 hub 映射
    assert P.local_wiki_files() is None, "指向不存在路径时不应找到本地分片"
    CALLS.clear()
    P.patched_load_dataset("wikipedia", "20200501.en")
    assert CALLS[-1]["name"] == "wikimedia/wikipedia", "无本地分片应回落 hub 映射"


TESTS = [test_remap_legacy_wikipedia, test_remap_legacy_wikitext,
         test_passthrough_unknown_and_kwargs, test_apply_swaps_attr_idempotent,
         test_local_parquet_divert]


def _main():
    fails = 0
    for t in TESTS:
        try:
            t(); print(f"  [PASS] {t.__name__}")
        except AssertionError as e:
            fails += 1; print(f"  [FAIL] {t.__name__}: {e}")
    print("ALL PASS" if fails == 0 else f"FAILED ({fails})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(_main())
