"""CPU tests for the preregistered B15 case-block bootstrap."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b15_regress as b15


def _rows(n_cases=100, slope=0.12, seed=9):
    rng = np.random.default_rng(seed)
    grid = {"Qwen": [1.5, 7.0, 14.0, 32.0], "Llama": [8.0, 70.0]}
    rows = []
    for k in range(n_cases):
        base_known = int(k % 3 != 0)
        fact_noise = rng.normal(0, 0.1)
        for family, sizes in grid.items():
            for params in sizes:
                rows.append({
                    "case_id": f"cf_{k}", "family": family, "params_b": params,
                    "log_params": float(np.log10(params)),
                    "chain_len": float(200 + rng.normal(0, 8)),
                    "base_ans_old": base_known,
                    "es_drop": float(slope * np.log10(params) + 0.04 * base_known
                                     + fact_noise + rng.normal(0, 0.03)),
                })
    return rows


def test_case_block_counts_unique_facts():
    rows = _rows(n_cases=60)
    out = b15.case_block_ci(rows, ["chain_len", "base_ans_old"], B=1000, seed=11)
    assert out["n_rows"] == 360
    assert out["n_case_blocks"] == 60
    assert out["ci95"][0] > 0, out
    assert out["bootstrap_unit"].startswith("unique case_id")


def test_case_block_is_deterministic():
    rows = _rows(n_cases=50)
    a = b15.case_block_ci(rows, ["chain_len", "base_ans_old"], B=500, seed=17)
    b = b15.case_block_ci(rows, ["chain_len", "base_ans_old"], B=500, seed=17)
    assert a == b


if __name__ == "__main__":
    test_case_block_counts_unique_facts(); print("ok b15 case blocks")
    test_case_block_is_deterministic(); print("ok b15 deterministic")
