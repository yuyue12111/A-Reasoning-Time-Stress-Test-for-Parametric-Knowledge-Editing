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
_SUP_SEEN = []                      # 每次 _gwb 收到的 suppress(None/生效)——apply_to 断言用
_tb = types.ModuleType("think_budget")
def _gwb(model, tok, q, b, do_sample=False, temperature=0.6, seed=None, suppress=None, **kw):
    # suppress kwarg 跟随 edit_loop 的 RQ3 调用(v1.27 曾漏更 mock 致全套 KeyError 变红,2026-07-03 修)
    _SUP_SEEN.append({"q": q, "budget": b, "suppress": suppress})
    if _RAISE_GEN_ON["sub"] and _RAISE_GEN_ON["sub"] in q:
        raise RuntimeError("gen-boom")
    # 真 think_budget 在 scope=think 的 B0 不进入 processor；其它预算的链生成会调用。
    if suppress and b != "B0" and hasattr(suppress.get("processor"), "calls"):
        suppress["processor"].calls += 3
    tag = f"s{seed}" if do_sample else "greedy"
    return (f"cot[{b}|{tag}]", f"ans[{b}|{tag}]", "full")
_tb.generate_with_budget = _gwb
_tb.CAP = {"B1": 256, "B2": 1024, "B3": 8192, "B4": 8192}   # provenance_header 记录用
sys.modules["think_budget"] = _tb

# vendor 补丁（edit_loop.run 在 from_hparams 前调 apply()）——stub 成 no-op，
# 保持本测无 transformers/datasets 依赖（system python3 可跑）；补丁自身逻辑见
# vendor_patches/test_qwen2_loader.py 与 test_mom2_dataset.py。
_vp_pkg = types.ModuleType("vendor_patches")
sys.modules["vendor_patches"] = _vp_pkg
for _pname in ("easyedit_qwen2_loader", "easyedit_mom2_dataset"):
    _m = types.ModuleType(f"vendor_patches.{_pname}")
    _m.apply = lambda: None
    sys.modules[f"vendor_patches.{_pname}"] = _m

# suppress stub(edit_loop.run 内惰性 from suppress import ...;mock 的 tok="TOK" 无法真建 token ids)
_sup = types.ModuleType("suppress")
_sup.build_old_token_ids = lambda tok, tgt, aliases: [1, 2]
class _FakeProcessor:
    def __init__(self, penalty):
        self.penalty, self.calls = penalty, 0
_sup.make_processor = lambda ids, penalty: _FakeProcessor(penalty)
sys.modules["suppress"] = _sup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit_loop  # noqa: E402


# ============ 夹具 ============
def _cases(n=4):
    return [{"case_id": f"cf_{i}", "s": f"Subj{i}", "prompt": f"Subj{i} lives in",
             "o_old": f"old{i}", "o_new": f"new{i}",
             "paraphrases": [f"pa{i}", f"pb{i}", f"pc{i}"], "neighborhood": [f"nbr{i}"]}
            for i in range(n)]

def _reset():
    RESTORES.clear(); FakeEditor.instances.clear(); _SUP_SEEN.clear()
    FakeEditor.raise_on_subject = None; _RAISE_GEN_ON["sub"] = None

def _run(**kw):
    fd, path = tempfile.mkstemp(suffix=".jsonl"); os.close(fd); os.remove(path)
    defaults = dict(cases=_cases(), editor_name="ROME", hparams_path="x",
                    budgets=["B0", "B1"], out_path=path, rank=0, world=1)
    defaults.update(kw)
    edit_loop.run(**defaults)
    rows = [json.loads(l) for l in open(defaults["out_path"])]
    os.remove(defaults["out_path"])
    return [r for r in rows if not r.get("_meta")], defaults["out_path"]   # 过滤溯源头行


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


def test_provenance_header_written_once_and_resume_no_dup():
    _reset()
    fd, path = tempfile.mkstemp(suffix=".jsonl"); os.close(fd); os.remove(path)
    edit_loop.run(_cases(2), "ROME", "x", ["B0"], path, rank=0, world=1,
                  meta={"model_tag": "r1qwen7b", "seed": 42})
    raw = [json.loads(l) for l in open(path)]
    hdr = raw[0]
    assert hdr.get("_meta") is True, "首行应为溯源头"
    assert hdr["editor"] == "ROME" and hdr["budgets"] == ["B0"], "头应含 editor/budgets"
    assert hdr["model_tag"] == "r1qwen7b" and hdr["seed"] == 42, "头应含 caller meta"
    assert "git" in hdr and "created" in hdr, "头应含 git/created"
    assert sum(r.get("_meta") is True for r in raw) == 1, "应只有一行溯源头"
    # 续跑（同 cases 全 done）→ 不应重复写头，且 metrics 续跑跳过逻辑能容忍 _meta 行（无 case_id）
    edit_loop.run(_cases(2), "ROME", "x", ["B0"], path, rank=0, world=1, meta={"model_tag": "x"})
    raw2 = [json.loads(l) for l in open(path)]
    os.remove(path)
    assert sum(r.get("_meta") is True for r in raw2) == 1, "续跑不应重复写溯源头"


def test_new_format_resume_rejects_config_or_code_drift_before_append():
    _reset()
    fd, path = tempfile.mkstemp(suffix=".jsonl"); os.close(fd); os.remove(path)
    meta = {"config_sha256": "cfgA", "code_sha256": {"src/edit_loop.py": "codeA"},
            "dataset": {"tag": "t"}, "run": {"tag_suffix": "_smoke"}}
    edit_loop.run(_cases(1), "ROME", "x", ["B0"], path, rank=0, world=1, meta=meta)
    before = open(path).read()
    try:
        edit_loop.run(_cases(1), "ROME", "x", ["B0"], path, rank=0, world=1,
                      meta={**meta, "config_sha256": "cfgB"})
    except RuntimeError as e:
        assert "resume signature mismatch" in str(e)
    else:
        raise AssertionError("changed config hash must refuse append")
    after = open(path).read(); os.remove(path)
    assert before == after, "拒绝恢复时不得写入任何字节"


def test_suppress_apply_to_default_efficacy_only():
    # 默认(无 apply_to):suppress 只到 efficacy 探针,其余(para/locality/open)必须 None——历史行为锁定
    _reset()
    rows, _ = _run(cases=_cases(1), budgets=["B0"],
                   suppress_cfg={"penalty": 8, "scope": "think"})
    eff = [s for s in _SUP_SEEN if s["suppress"] is not None]
    assert eff, "efficacy 探针应收到 suppress"
    assert all(s["suppress"]["scope"] == "think" for s in eff)
    # 非 efficacy 的 q(para/neighborhood/open)一律无 suppress
    non_eff_q = [s["q"] for s in _SUP_SEEN if s["suppress"] is None]
    assert any("pa0" in q or "nbr0" in q or "Tell me about" in q for q in non_eff_q), \
        f"para/loc/open 应无 suppress, seen={_SUP_SEEN}"


def test_suppress_apply_to_hop_g1():
    # G1/B25:apply_to:[hop] → 只有 hop 探针收到 suppress,efficacy 反而 None
    _reset()
    cases = _cases(1)
    cases[0]["hop_q"] = "Which continent is Subj0's home in?"
    rows, _ = _run(cases=cases, budgets=["B0"],
                   suppress_cfg={"penalty": 8, "scope": "think", "apply_to": ["hop"]})
    hop_seen = [s for s in _SUP_SEEN if "continent" in s["q"]]
    assert hop_seen and all(s["suppress"] is not None for s in hop_seen), \
        f"hop 探针应收到 suppress, seen={_SUP_SEEN}"
    eff_seen = [s for s in _SUP_SEEN if s["q"] == "Subj0 lives in"]
    assert eff_seen and all(s["suppress"] is None for s in eff_seen), \
        "apply_to:[hop] 下 efficacy 不应收到 suppress"


def test_suppress_trace_records_target_ids_and_activation():
    _reset()
    cases = _cases(1)
    rows, _ = _run(cases=cases, budgets=["B0", "B3"],
                   suppress_cfg={"penalty": 8, "scope": "think",
                                 "apply_to": ["efficacy", "para0", "para1"]})
    traced = [r for r in rows if r.get("suppress_trace")]
    assert traced, "suppression run 每行应有可审计 trace"
    assert all(r["suppress_trace"]["target"] == cases[0]["o_old"] for r in traced)
    assert all(r["suppress_trace"]["token_ids"] == [1, 2] for r in traced)
    by = {(r["budget"], r["probe"]): r["suppress_trace"] for r in traced}
    assert by[("B0", "efficacy")]["selected"] is True
    assert by[("B0", "efficacy")]["active"] is False
    assert by[("B0", "efficacy")]["processor_calls"] == 0
    assert by[("B3", "efficacy")]["active"] is True
    assert by[("B3", "para0")]["active"] is True
    assert by[("B3", "para0")]["processor_calls"] == 3
    assert by[("B3", "locality")]["selected"] is False
    assert by[("B3", "locality")]["active"] is False
    assert by[("B3", "open")]["active"] is False


def test_opt_in_diagnostics_are_recorded_without_changing_default():
    _reset()
    original = edit_loop.weight_delta_summary
    edit_loop.weight_delta_summary = lambda model, weights, chunk: {
        "n_weights": 1, "aggregate": {"delta_l2": 2.0, "relative_l2": 0.1}}
    try:
        rows, _ = _run(cases=_cases(1), budgets=["B0"], probe_sel=["efficacy"],
                       diagnostics_cfg={"weight_delta": True, "chunk_elems": 7})
    finally:
        edit_loop.weight_delta_summary = original
    assert len(rows) == 1 and rows[0]["diagnostics"]["weight_delta"]["n_weights"] == 1


TESTS = [test_sharding_partitions_by_index, test_subject_and_s_field_passed,
         test_open_probe_uses_s, test_restore_called_every_case, test_resume_skips_done,
         test_generation_error_still_restores_and_continues,
         test_edit_error_skips_restore_and_continues,
         test_provenance_header_written_once_and_resume_no_dup,
         test_new_format_resume_rejects_config_or_code_drift_before_append,
         test_suppress_apply_to_default_efficacy_only, test_suppress_apply_to_hop_g1,
         test_suppress_trace_records_target_ids_and_activation,
         test_opt_in_diagnostics_are_recorded_without_changing_default]


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
