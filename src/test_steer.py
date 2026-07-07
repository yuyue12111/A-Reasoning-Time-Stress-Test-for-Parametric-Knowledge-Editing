"""steer.Steerer 钩子机制单测（需 torch，无 GPU）：全局/掩码/attn-site/层子集/符号/退出摘钩。
运行：<editrev>/python src/test_steer.py   （或 pytest）
"""
import sys, os, torch, torch.nn as nn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import steer

H = 4


class ZeroMLP(nn.Module):
    def forward(self, x): return torch.zeros(x.shape[0], x.shape[1], H)


class ZeroAttn(nn.Module):                       # 模拟 self_attn：返回 tuple
    def forward(self, x): return (torch.zeros(x.shape[0], x.shape[1], H), "kv")


def fake_model(n=3):
    layers = nn.ModuleList()
    for _ in range(n):
        blk = nn.Module(); blk.mlp = ZeroMLP(); blk.self_attn = ZeroAttn()
        layers.append(blk)
    inner = nn.Module(); inner.layers = layers
    model = nn.Module(); model.model = inner; model.device = "cpu"
    return model


DIRS = torch.stack([torch.full((H,), float(i + 1)) for i in range(3)])   # 第 i 层方向=(i+1,…)


def test_global_mlp_adds_direction_then_removed():
    model = fake_model(); x = torch.randn(1, 5, H)
    with steer.Steerer(model, DIRS, alpha=2.0, site="mlp"):
        out = model.model.layers[1].mlp(x)       # dir[1]=2, alpha=2 → +4 全位置
    assert torch.allclose(out, torch.full((1, 5, H), 4.0)), "全局注入应每位 +α·v"
    assert torch.allclose(model.model.layers[1].mlp(x), torch.zeros(1, 5, H)), "退出后钩子应摘干净"


def test_masked_positions():
    model = fake_model()
    with steer.Steerer(model, DIRS, alpha=1.0, site="mlp") as st:
        st.set_positions(torch.tensor([True, False, True]))
        out = model.model.layers[0].mlp(torch.randn(1, 3, H))   # dir[0]=1
    assert torch.allclose(out[0, 0], torch.ones(H)) and torch.allclose(out[0, 2], torch.ones(H))
    assert torch.allclose(out[0, 1], torch.zeros(H)), "掩码 False 位不应注入"


def test_attn_site_preserves_tuple():
    model = fake_model()
    with steer.Steerer(model, DIRS, alpha=3.0, site="attn"):
        out = model.model.layers[2].self_attn(torch.randn(1, 2, H))   # dir[2]=3, alpha=3 → 9
    assert isinstance(out, tuple) and out[1] == "kv", "attn 输出 tuple 其余项应保留"
    assert torch.allclose(out[0], torch.full((1, 2, H), 9.0))


def test_layers_subset_and_negative_alpha():
    model = fake_model(); x = torch.randn(1, 2, H)
    with steer.Steerer(model, DIRS, alpha=-1.0, site="mlp", layers=[0]):
        o0 = model.model.layers[0].mlp(x)        # 挂钩: -1·dir[0] = -1
        o1 = model.model.layers[1].mlp(x)        # 未挂钩: 0
    assert torch.allclose(o0, torch.full((1, 2, H), -1.0)), "α<0 应反向注入"
    assert torch.allclose(o1, torch.zeros(1, 2, H)), "层子集外不应被挂钩"


def test_generated_mode_prefill_skip_decode_inject():
    # W-B(prereg §3):mode="generated" → prefill(seq>1)不注入,解码步(seq==1)注入
    model = fake_model()
    with steer.Steerer(model, DIRS, alpha=2.0, site="mlp", mode="generated"):
        pre = model.model.layers[1].mlp(torch.randn(1, 5, H))    # prefill
        step = model.model.layers[1].mlp(torch.randn(1, 1, H))   # 解码步
    assert torch.allclose(pre, torch.zeros(1, 5, H)), "generated 模式 prefill 不应注入"
    assert torch.allclose(step, torch.full((1, 1, H), 4.0)), "generated 模式解码步应 +α·v"


def test_mask_mismatch_error_and_skip():
    # 红队修:mask 失配默认必须抛错(旧行为=静默全局注入);skip=该步不注入
    model = fake_model()
    with steer.Steerer(model, DIRS, alpha=1.0, site="mlp") as st:          # 默认 on_mismatch="error"
        st.set_positions(torch.tensor([True, False, True]))
        try:
            model.model.layers[0].mlp(torch.randn(1, 1, H))                # seq=1 ≠ mask len 3
            raise AssertionError("失配应抛 RuntimeError(静默注入 bug 复活)")
        except RuntimeError:
            pass
    with steer.Steerer(model, DIRS, alpha=1.0, site="mlp", on_mismatch="skip") as st:
        st.set_positions(torch.tensor([True, False, True]))
        out = model.model.layers[0].mlp(torch.randn(1, 1, H))
    assert torch.allclose(out, torch.zeros(1, 1, H)), "on_mismatch=skip 失配步不应注入"


def test_think_budget_scope_think_plumbing():
    # 集成:generate_with_budget(steerer, scope=think) → 链期 enter、答案段前 hook 已摘净(断言不炸)
    import types
    sys.modules.setdefault("transformers", types.ModuleType("transformers"))   # _gen 惰性 import 防缺
    import think_budget as tb

    class _Enc(dict):
        def to(self, *a, **k):
            return self

    class MockTok:
        eos_token_id = 0; bos_token = None
        def __call__(self, text, return_tensors=None, add_special_tokens=True, **kw):
            ids = [hash(w) % 997 + 5 for w in text.split(" ") if w]
            if return_tensors == "pt":
                t = torch.tensor([ids or [0]], dtype=torch.long)
                return _Enc(input_ids=t, attention_mask=torch.ones_like(t))
            return {"input_ids": ids}
        def decode(self, ids, skip_special_tokens=True):
            return "alpha beta " + tb.THINK_END + " done"

    class MockGenModel:
        device = "cpu"
        def generate(self, input_ids=None, attention_mask=None, **kw):
            return torch.cat([input_ids, torch.tensor([[7, 8, 9]])], dim=1)

    hooked = fake_model()
    events = []
    class RecSteerer(steer.Steerer):
        def __enter__(self):
            events.append("enter"); return super().__enter__()
        def __exit__(self, *a):
            events.append("exit"); return super().__exit__(*a)
    st = RecSteerer(hooked, DIRS, alpha=1.0, site="mlp", mode="generated")
    cot, ans, _ = tb.generate_with_budget(MockGenModel(), MockTok(), "q?", "B1",
                                          steerer={"steerer": st, "scope": "think"})
    assert events == ["enter", "exit"], f"链期应 enter/exit 恰一次: {events}"
    assert not st._handles, "答案段后 hook 必须为空"
    assert ans, "answer 应非空"


TESTS = [test_global_mlp_adds_direction_then_removed, test_masked_positions,
         test_attn_site_preserves_tuple, test_layers_subset_and_negative_alpha,
         test_generated_mode_prefill_skip_decode_inject, test_mask_mismatch_error_and_skip,
         test_think_budget_scope_think_plumbing]


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
