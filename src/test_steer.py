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


TESTS = [test_global_mlp_adds_direction_then_removed, test_masked_positions,
         test_attn_site_preserves_tuple, test_layers_subset_and_negative_alpha]


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
