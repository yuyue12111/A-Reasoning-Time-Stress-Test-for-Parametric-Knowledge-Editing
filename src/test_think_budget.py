"""think_budget B0–B4 单测 (plan task 7)。

两层：
  (A) Mock 层——用假 model/tokenizer 验证预算控制流，CPU 即可跑、不需权重：
      B0 空思考块 / B1·B2·B3 截断到 CAP / B4 的 s1 式 WAIT 注入(≤2) / 截断单调性。
      这是 think_budget.py 的**首次实际执行**（CLAUDE.md 记其"未实跑"），先于 H200 抓控制流 bug。
  (B) 真模型层——在未编辑的 R1-Distill-Qwen-7B 上跑 5 档，打印长度分布并断言：
      B0 cot 为空 / 各档 ntok(cot) ≤ CAP(+容差) / greedy 下 B1≤B2≤B3 / B4≥B3 且出现 WAIT / answer 非空。

运行：
  # 仅 mock（任意有 torch 的环境，CPU）
  python src/test_think_budget.py
  # mock + 真模型（H200 窗口）
  python src/test_think_budget.py --model deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --device cuda
  # 或 pytest（若已安装；真模型层靠环境变量 WHYAAAI_MODEL 触发，否则自动跳过）
  WHYAAAI_MODEL=deepseek-ai/DeepSeek-R1-Distill-Qwen-7B pytest -q src/test_think_budget.py
"""
import os, sys, argparse
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import think_budget as tb  # noqa: E402  (导入即需要 torch；mock 层也用真 torch 张量)
import torch  # noqa: E402


# ============================ (A) Mock 层 ============================
class _Enc(dict):
    """模拟 HF BatchEncoding：支持 .to() 与 ** 解包。"""
    def to(self, *a, **k):
        return self


class MockTok:
    """词级双射 tokenizer：按空白切词、decode 还原。够 think_budget 的计数/切片用。"""
    eos_token_id = 0

    def __init__(self):
        self.vocab, self.inv = {}, {0: ""}

    def _id(self, w):
        if w not in self.vocab:
            i = len(self.vocab) + 1
            self.vocab[w], self.inv[i] = i, w
        return self.vocab[w]

    def __call__(self, text, return_tensors=None, add_special_tokens=True, **kw):
        ids = [self._id(w) for w in text.split(" ")] if text else []
        if return_tensors == "pt":
            t = torch.tensor([ids] if ids else [[0]], dtype=torch.long)
            return _Enc(input_ids=t, attention_mask=torch.ones_like(t))
        return {"input_ids": ids}

    def decode(self, ids, skip_special_tokens=True):
        if hasattr(ids, "tolist"):
            ids = ids.tolist()
        toks = [self.inv.get(int(i), "") for i in ids
                if not (skip_special_tokens and int(i) == self.eos_token_id)]
        return " ".join(t for t in toks if t)


class MockModel:
    """假 model：generate 把 responder(prompt, max_new) 的文本编码回去拼到 prompt 后。"""
    device = "cpu"

    def __init__(self, tok, responder):
        self.tok, self.responder = tok, responder

    def generate(self, input_ids=None, attention_mask=None, max_new_tokens=None, **kw):
        prompt_ids = input_ids[0].tolist()
        prompt_text = self.tok.decode(prompt_ids, skip_special_tokens=False)
        new_text = self.responder(prompt_text, max_new_tokens)
        new_ids = self.tok(new_text)["input_ids"][:max_new_tokens]
        return torch.tensor([prompt_ids + new_ids], dtype=torch.long)


def R_nostop(prompt, max_new):
    """永不出 </think>：填满预算 → 测 B1/B2/B3 截断、B4 在'无可抑制'时退化为命中 CAP。"""
    return " ".join(["x"] * max_new)


def R_stop(prompt, max_new):
    """每次都早早出 </think> → 测 B1/B2/B3 在首个 </think> 处收口、B4 注入 WAIT(≤2)。"""
    return "alpha beta gamma </think> the final answer"


class RecordingMockModel:
    """记录每次 generate 收到的解码 kwargs；采样(do_sample)时产出**依赖 torch 全局 RNG** 的文本，
    从而 seed 决定输出 → 测采样臂的 do_sample/temperature 透传与 seed 可复现性 (plan §2.5)。"""
    device = "cpu"

    def __init__(self, tok):
        self.tok, self.calls = tok, []

    def generate(self, input_ids=None, attention_mask=None, max_new_tokens=None,
                 do_sample=False, temperature=None, **kw):
        self.calls.append({"do_sample": do_sample, "temperature": temperature})
        prompt_ids = input_ids[0].tolist()
        if do_sample:
            r = int(torch.randint(0, 100000, (1,)).item())   # 仅此消费全局 RNG → seed 决定
            new_text = f"tok{r} </think> ans{r}"
        else:
            new_text = "greedy think </think> the answer"
        new_ids = self.tok(new_text)["input_ids"][:max_new_tokens]
        return torch.tensor([prompt_ids + new_ids], dtype=torch.long)


def _run(responder, budget, q="solve this problem"):
    tok = MockTok()
    model = MockModel(tok, responder)
    cot, ans, _ = tb.generate_with_budget(model, tok, q, budget)
    return cot, ans, tb._ntok(tok, cot)


def _run_decode(budget, seed, do_sample=True, temperature=0.6, q="solve this problem"):
    tok = MockTok()
    model = RecordingMockModel(tok)
    cot, ans, _ = tb.generate_with_budget(model, tok, q, budget,
                                          do_sample=do_sample, temperature=temperature, seed=seed)
    return cot, ans, model.calls


# -- pytest-discoverable 断言（也被下方手动 runner 复用）--
def test_b0_zerothink_empty():
    for resp in (R_nostop, R_stop):
        cot, ans, n = _run(resp, "B0")
        assert cot == "" and n == 0, f"B0 应空思考, 得 {n} tok"
        assert ans != "", "B0 answer 不应为空"


def test_truncation_hits_cap_nostop():
    # 无 </think> 时各档 cot 恰好被 CAP 截断（mock 词级双射 → 精确）
    for b in ("B1", "B2", "B3"):
        _, _, n = _run(R_nostop, b)
        assert n == tb.CAP[b], f"{b} 截断应 == CAP {tb.CAP[b]}, 得 {n}"


def test_truncation_monotone_nostop():
    n1 = _run(R_nostop, "B1")[2]
    n2 = _run(R_nostop, "B2")[2]
    n3 = _run(R_nostop, "B3")[2]
    assert n1 <= n2 <= n3, f"截断应单调: B1={n1} B2={n2} B3={n3}"


def test_stop_closes_at_first_think_end():
    # 出 </think> 时非 B4 各档在首个 </think> 前收口（head = 'alpha beta gamma'）
    for b in ("B1", "B2", "B3"):
        cot, _, _ = _run(R_stop, b)
        assert cot.strip() == "alpha beta gamma", f"{b} 应在首个 </think> 收口, 得 {cot!r}"
        assert tb.THINK_END not in cot, f"{b} cot 不应含 </think>"


def test_b4_injects_wait_then_stops():
    # B4 在每次 </think> 注入 WAIT, 最多 2 次, 之后收口
    cot, _, _ = _run(R_stop, "B4")
    assert cot.count(tb.WAIT.strip()) == 2, f"B4 应注入恰好 2 次 WAIT, 得 {cot.count(tb.WAIT.strip())}"
    assert cot.count("alpha beta gamma") == 3, f"B4 应有 3 段 head (2 次延长), 得 {cot!r}"


def test_b4_geq_b3_and_extends():
    n3 = _run(R_stop, "B3")[2]
    n4 = _run(R_stop, "B4")[2]
    assert n4 > n3, f"B4({n4}) 应长于 B3({n3})（s1 延长生效）"
    # 无 </think> 可抑制时, B4 退化为命中 CAP, 与 B3 持平
    assert _run(R_nostop, "B4")[2] == _run(R_nostop, "B3")[2], "无 </think> 时 B4 应与 B3 同为 CAP"


def test_decode_kwargs_greedy_vs_sample():
    # greedy（默认）：全程 do_sample=False，不传 temperature
    _, _, calls = _run_decode("B3", seed=None, do_sample=False)
    assert calls and all(c["do_sample"] is False for c in calls), "greedy 应全程 do_sample=False"
    assert all(c["temperature"] is None for c in calls), "greedy 不应传 temperature"
    # 采样：全程 do_sample=True，temperature 透传
    _, _, calls = _run_decode("B3", seed=1, do_sample=True, temperature=0.6)
    assert calls and all(c["do_sample"] is True for c in calls), "采样应全程 do_sample=True"
    assert all(abs(c["temperature"] - 0.6) < 1e-9 for c in calls), "temperature 应=0.6 透传"


def test_sampling_seed_reproducible():
    a = _run_decode("B3", seed=7)[:2]
    b = _run_decode("B3", seed=7)[:2]
    c = _run_decode("B3", seed=8)[:2]
    assert a == b, f"同 seed 应可复现: {a!r} != {b!r}"
    assert a != c, f"异 seed 应不同(极大概率): {a!r} == {c!r}"


MOCK_TESTS = [
    test_b0_zerothink_empty, test_truncation_hits_cap_nostop, test_truncation_monotone_nostop,
    test_stop_closes_at_first_think_end, test_b4_injects_wait_then_stops, test_b4_geq_b3_and_extends,
    test_decode_kwargs_greedy_vs_sample, test_sampling_seed_reproducible,
]


# ============================ (B) 真模型层 ============================
DEFAULT_QUESTIONS = [
    "What is the capital of the country where the Eiffel Tower is located?",
    "If a train travels 60 km in 45 minutes, what is its speed in km/h?",
    "Is 91 a prime number? Briefly explain.",
    "Who directed the 1982 film Blade Runner?",
]


def length_report(model, tok, questions=DEFAULT_QUESTIONS, budgets=("B0", "B1", "B2", "B3", "B4")):
    rows = []
    for q in questions:
        for b in budgets:
            cot, ans, _ = tb.generate_with_budget(model, tok, q, b)
            rows.append({"q": q, "budget": b,
                         "ntok_cot": tb._ntok(tok, cot), "ntok_ans": tb._ntok(tok, ans),
                         "has_wait": tb.WAIT.strip() in cot, "ans_empty": not ans.strip()})
    return rows


def print_distribution(rows):
    by_b = defaultdict(list)
    for r in rows:
        by_b[r["budget"]].append(r["ntok_cot"])
    print("\n  预算  | n | cot_tok  min/median/max | CAP")
    print("  -----+---+-------------------------+------")
    for b in ("B0", "B1", "B2", "B3", "B4"):
        xs = sorted(by_b.get(b, []))
        if not xs:
            continue
        med = xs[len(xs) // 2]
        cap = tb.CAP.get(b, "—")
        print(f"  {b:>4} | {len(xs)} | {xs[0]:>6} / {med:>6} / {xs[-1]:>6}      | {cap}")


def check_real(rows, tol=128):
    """真模型不变量（带容差：解码/再编码 round-trip + chunk 粒度溢出）。"""
    fails = []
    by_q = defaultdict(dict)
    for r in rows:
        by_q[r["q"]][r["budget"]] = r
        if r["budget"] == "B0" and r["ntok_cot"] != 0:
            fails.append(f"B0 cot 非空 ({r['ntok_cot']}) @ {r['q'][:30]}")
        if r["budget"] in tb.CAP and r["ntok_cot"] > tb.CAP[r["budget"]] + tol:
            fails.append(f"{r['budget']} 超 CAP+tol ({r['ntok_cot']}) @ {r['q'][:30]}")
        if r["ans_empty"]:
            fails.append(f"{r['budget']} answer 空 @ {r['q'][:30]}")
    for q, m in by_q.items():
        if {"B1", "B2", "B3"} <= set(m):
            n1, n2, n3 = (m[b]["ntok_cot"] for b in ("B1", "B2", "B3"))
            if not (n1 <= n2 + tol and n2 <= n3 + tol):
                fails.append(f"非单调 B1≤B2≤B3 ({n1},{n2},{n3}) @ {q[:30]}")
        if {"B3", "B4"} <= set(m):
            if m["B4"]["ntok_cot"] + tol < m["B3"]["ntok_cot"]:
                fails.append(f"B4<B3 ({m['B4']['ntok_cot']}<{m['B3']['ntok_cot']}) @ {q[:30]}")
    return fails


def run_real_suite(model_path, device="cuda"):
    print(f"\n=== (B) 真模型层: {model_path} @ {device} ===")
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype="auto").to(device).eval()
    rows = length_report(model, tok)
    print_distribution(rows)
    fails = check_real(rows)
    for f in fails:
        print("  [FAIL]", f)
    print(f"  真模型层: {'PASS' if not fails else f'FAIL ({len(fails)})'}")
    return len(fails)


# pytest 入口：有 WHYAAAI_MODEL 才跑真模型层，否则跳过
def test_real_length_distribution():
    model_path = os.environ.get("WHYAAAI_MODEL")
    if not model_path:
        import pytest
        pytest.skip("set WHYAAAI_MODEL to run the real-model length-distribution test (H200)")
    assert run_real_suite(model_path, os.environ.get("WHYAAAI_DEVICE", "cuda")) == 0


# ============================ 手动 runner ============================
def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.environ.get("WHYAAAI_MODEL"),
                    help="HF id / 本地路径；给了才跑真模型层")
    ap.add_argument("--device", default=os.environ.get("WHYAAAI_DEVICE", "cuda"))
    args = ap.parse_args()

    print("=== (A) Mock 控制流层 ===")
    fails = 0
    for t in MOCK_TESTS:
        try:
            t()
            print(f"  [PASS] {t.__name__}")
        except AssertionError as e:
            fails += 1
            print(f"  [FAIL] {t.__name__}: {e}")
    print(f"  mock 层: {'PASS' if fails == 0 else f'FAIL ({fails})'}")

    if args.model:
        fails += run_real_suite(args.model, args.device)
    else:
        print("\n[skip] 真模型层——传 --model 或设 WHYAAAI_MODEL 以在 H200 上验证长度分布")

    print("\n" + ("ALL PASS" if fails == 0 else f"FAILED ({fails})"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(_main())
