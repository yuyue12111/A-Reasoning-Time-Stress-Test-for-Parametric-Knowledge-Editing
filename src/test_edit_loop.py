"""edit_loop 单条编辑主循环单测（plan task 7 姊妹件，无 GPU/无依赖）。

用 sys.modules 把 easyeditor / torch / think_budget 换成 stub，验证 run() 的纯逻辑：
  分片(i % world)、续跑跳过(done)、finally 总还原、subject/字段 s 传参、单条出错不拖垮整片。
运行：python src/test_edit_loop.py    （或 pytest src/test_edit_loop.py）
"""
import sys, types, json, os, tempfile, contextlib

# ============ stubs（必须在 import edit_loop 之前装好）============
_torch = types.ModuleType("torch")
_torch.no_grad = contextlib.nullcontext
sys.modules["torch"] = _torch

RESTORES = []                       # 每次 restore 的 setitem 记录 (key, value)
class _FakeParam:
    def __init__(self, key): self.key = key
    def __setitem__(self, idx, val): RESTORES.append((self.key, val))
_eu = types.ModuleType("easyeditor.util")
_eu.nethook = types.SimpleNamespace(get_parameter=lambda model, key: _FakeParam(key))
sys.modules["easyeditor.util"] = _eu

class _HP:
    @classmethod
    def from_hparams(cls, p): return cls()

class FakeEditor:
    instances = []
    raise_on_subject = None         # 置某 subject 串则该条 edit() 抛错
    def __init__(self):
        self.model, self.tok, self.edit_calls = "MODEL", "TOK", []
        FakeEditor.instances.append(self)
    @classmethod
    def from_hparams(cls, hp): return cls()
    def edit(self, prompts, target_new, ground_truth=None, subject=None,
             sequential_edit=False, **kw):
        self.edit_calls.append({"prompts": prompts, "target_new": target_new,
                                "ground_truth": ground_truth, "subject": subject})
        if FakeEditor.raise_on_subject and subject == [FakeEditor.raise_on_subject]:
            raise RuntimeError("edit-boom")
        return ({}, self.model, {"w": ("orig", len(self.edit_calls))})

_ee = types.ModuleType("easyeditor")
_ee.BaseEditor = FakeEditor
_ee.ROMEHyperParams = _ee.MEMITHyperParams = _ee.AlphaEditHyperParams = _ee.FTHyperParams = _HP
sys.modules["easyeditor"] = _ee

_RAISE_GEN_ON = {"sub": None}       # 置某 prompt 子串则生成时抛错
_tb = types.ModuleType("think_budget")
def _gwb(model, tok, q, b, do_sample=False, temperature=0.6, seed=None):
    if _RAISE_GEN_ON["sub"] and _RAISE_GEN_ON["sub"] in q:
        raise RuntimeError("gen-boom")
    tag = f"s{seed}" if do_sample else "greedy"
    return (f"cot[{b}|{tag}]", f"ans[{b}|{tag}]", "full")
_tb.generate_with_budget = _gwb
sys.modules["think_budget"] = _tb

# qwen 路由补丁（edit_loop.run 在 from_hparams 前调 apply()）——stub 成 no-op，
# 保持本测无 transformers 依赖（system python3 可跑）；补丁自身逻辑见 vendor_patches/test_qwen2_loader.py。
_vp_pkg = types.ModuleType("vendor_patches")
_vp_mod = types.ModuleType("vendor_patches.easyedit_qwen2_loader")
_vp_mod.apply = lambda: None
sys.modules["vendor_patches"] = _vp_pkg
sys.modules["vendor_patches.easyedit_qwen2_loader"] = _vp_mod

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit_loop  # noqa: E402


# ============ 夹具 ============
def _cases(n=4):
    return [{"case_id": f"cf_{i}", "s": f"Subj{i}", "prompt": f"Subj{i} lives in",
             "o_old": f"old{i}", "o_new": f"new{i}",
             "paraphrases": [f"pa{i}", f"pb{i}", f"pc{i}"], "neighborhood": [f"nbr{i}"]}
            for i in range(n)]

def _reset():
    RESTORES.clear(); FakeEditor.instances.clear()
    FakeEditor.raise_on_subject = None; _RAISE_GEN_ON["sub"] = None

def _run(**kw):
    fd, path = tempfile.mkstemp(suffix=".jsonl"); os.close(fd); os.remove(path)
    defaults = dict(cases=_cases(), editor_name="ROME", hparams_path="x",
                    budgets=["B0", "B1"], out_path=path, rank=0, world=1)
    defaults.update(kw)
    edit_loop.run(**defaults)
    rows = [json.loads(l) for l in open(defaults["out_path"])]
    os.remove(defaults["out_path"])
    return rows, defaults["out_path"]


# ============ 测试 ============
def test_sharding_partitions_by_index():
    _reset(); rows0, _ = _run(world=2, rank=0)
    ids0 = sorted({r["case_id"] for r in rows0})
    assert ids0 == ["cf_0", "cf_2"], f"rank0 应处理 cf_0/cf_2, 得 {ids0}"
    _reset(); rows1, _ = _run(world=2, rank=1)
    ids1 = sorted({r["case_id"] for r in rows1})
    assert ids1 == ["cf_1", "cf_3"], f"rank1 应处理 cf_1/cf_3, 得 {ids1}"

def test_subject_and_s_field_passed():
    _reset(); _run(cases=_cases(1))
    ed = FakeEditor.instances[-1]
    assert ed.edit_calls[0]["subject"] == ["Subj0"], "subject= 必须传 case['s']"

def test_open_probe_uses_s():
    _reset(); rows, _ = _run(cases=_cases(1), budgets=["B0"])
    opens = [r for r in rows if r["probe"] == "open"]
    assert opens and opens[0]["q"] == "Tell me about Subj0.", f"open 探针应用 s, 得 {opens}"

def test_restore_called_every_case():
    _reset(); _run(cases=_cases(3))          # world=1 → 3 条全处理
    assert len(RESTORES) == 3, f"应每条 case 还原一次, 得 {len(RESTORES)}"

def test_resume_skips_done():
    _reset()
    fd, path = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
    with open(path, "w") as f:               # 预置 cf_0 已完成
        f.write(json.dumps({"case_id": "cf_0", "probe": "efficacy"}) + "\n")
    edit_loop.run(_cases(), "ROME", "x", ["B0"], path, rank=0, world=1)
    rows = [json.loads(l) for l in open(path)]
    os.remove(path)
    ids = {r["case_id"] for r in rows}
    assert {"cf_1", "cf_2", "cf_3"} <= ids, "未完成的应被处理"
    cf0 = [r for r in rows if r["case_id"] == "cf_0"]   # 预置的那条 + 不应有新记录
    assert len(cf0) == 1 and "editor" not in cf0[0], "cf_0 应被跳过、不重复处理"

def test_generation_error_still_restores_and_continues():
    _reset(); _RAISE_GEN_ON["sub"] = "Subj1 lives in"      # cf_1 efficacy 生成抛错
    rows, _ = _run(cases=_cases(3))
    err = [r for r in rows if r.get("error")]
    assert len(err) == 1 and err[0]["case_id"] == "cf_1", f"cf_1 应记一条 error, 得 {err}"
    assert len(RESTORES) == 3, "生成出错也要还原（3 条都 edit 成功过）"
    assert any(r["case_id"] == "cf_2" and r.get("probe") for r in rows), "出错后应继续处理 cf_2"

def test_edit_error_skips_restore_and_continues():
    _reset(); FakeEditor.raise_on_subject = "Subj1"        # cf_1 的 edit() 抛错
    rows, _ = _run(cases=_cases(3))
    err = [r for r in rows if r.get("error")]
    assert len(err) == 1 and err[0]["case_id"] == "cf_1", "cf_1 应记 edit 错误"
    assert len(RESTORES) == 2, f"edit 失败的 case 无 wcopy 不还原, 应 2 次, 得 {len(RESTORES)}"
    assert any(r["case_id"] == "cf_2" for r in rows), "edit 出错后应继续处理 cf_2"


TESTS = [test_sharding_partitions_by_index, test_subject_and_s_field_passed,
         test_open_probe_uses_s, test_restore_called_every_case, test_resume_skips_done,
         test_generation_error_still_restores_and_continues,
         test_edit_error_skips_restore_and_continues]


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
