"""easyedit_mom2_dataset 单测（mom2 语料加载修复；MEMIT/AlphaEdit-blocker）。

全 stub datasets + easyeditor.models.rome.layer_stats，无 GPU/无下载，system python3 即可。
断言：(1) 老 wikipedia/wikitext id 被映射到现行 parquet 仓 (2) 未知 id 原样透传(含 kwargs)
(3) apply() 换掉 layer_stats 模块属性且幂等。
运行：python3 src/vendor_patches/test_mom2_dataset.py
"""
import sys, os, types

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


TESTS = [test_remap_legacy_wikipedia, test_remap_legacy_wikitext,
         test_passthrough_unknown_and_kwargs, test_apply_swaps_attr_idempotent]


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
