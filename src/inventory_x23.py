"""Read-only shared-disk gate for the parallel X2/X3 launch."""
import argparse
import glob
import hashlib
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL14 = "/inspire/hdd/project/ai4education/ky26140/why/models/DeepSeek-R1-Distill-Qwen-14B"
DEFAULT_MODEL32 = "/inspire/hdd/global_public/public_models/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
DEFAULT_WIKI = "/inspire/dataset/wikipedia/20231101/20231101.en"
UPLOAD_CORE = [
    "src/edit_loop.py", "src/run_pilot.py", "src/suppress.py",
    "src/cross_arm_para.py", "src/validate_x_smoke.py", "src/inventory_x23.py",
    "experiments/memit14b.yaml", "experiments/memit14b_sup.yaml",
    "experiments/memit14b_strongcomp.yaml", "experiments/memit14b_freshn.yaml",
    "experiments/probe32b_para_sup.yaml", "experiments/probe32b_para_strongcomp.yaml",
    "experiments/probe32b_freshn.yaml", "experiments/run_x2_h200.sh",
    "experiments/run_x3_h200.sh", "experiments/x23_paths.sh",
    "experiments/run_x23_inventory.sh", "prereg-x2-x3.md", "plan.md",
]
REQUIRED_EXISTING = [
    "src/think_budget.py", "src/r1_tokenizer.py", "src/metrics.py", "src/score_pilot.py",
    "src/cross_arm.py", "src/vendor_patches/easyedit_qwen2_loader.py",
    "src/vendor_patches/easyedit_mom2_dataset.py", "experiments/probe32b.yaml",
    "source/EasyEdit/hparams/ROME/qwen2.5-7b.yaml",
    "source/EasyEdit/hparams/MEMIT/qwen2.5-7b.yaml",
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def line_count(path):
    with open(path, "rb") as f:
        return sum(1 for _ in f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model14", default=os.environ.get("MODEL14", DEFAULT_MODEL14))
    ap.add_argument("--model32", default=os.environ.get("MODEL32", DEFAULT_MODEL32))
    ap.add_argument("--wiki", default=os.environ.get("WIKI_EN", DEFAULT_WIKI),
                    help="English parquet directory or glob")
    args = ap.parse_args()
    os.chdir(ROOT)

    failures = []
    for rel in UPLOAD_CORE:
        if not Path(rel).is_file():
            failures.append(f"missing uploaded file: {rel}")
    for rel in REQUIRED_EXISTING:
        if not Path(rel).is_file():
            failures.append(f"missing existing dependency: {rel}")
    for label, model in (("14B", args.model14), ("32B", args.model32)):
        p = Path(model) / "config.json"
        if not p.is_file():
            failures.append(f"missing {label} model config: {p}")
    for rel in ("data/counterfact.prefiltered.jsonl", "data/counterfact.jsonl",
                "data/aliases.json", "data/placebo_donors_strong.json"):
        if not Path(rel).is_file():
            failures.append(f"missing data: {rel}")

    stats = sorted(Path("data/stats_r1qwen14b").rglob("*.npz")) if Path("data/stats_r1qwen14b").is_dir() else []
    if len(stats) < 3:
        failures.append(f"stats_r1qwen14b has {len(stats)} npz files; need >=3 cached layers")
    spec = args.wiki
    wiki = sorted(glob.glob(str(Path(spec) / "*.parquet"))) if Path(spec).is_dir() else sorted(glob.glob(spec))
    if not wiki:
        failures.append(f"no English Wikipedia parquet files matched: {spec}")
    n14 = sorted(glob.glob("results/probe/r1qwen14b_MEMIT_cf200memit_r*.jsonl"))
    n32 = sorted(glob.glob("results/probe/r1qwen32b_ROME_cf200_r*.jsonl"))
    if not n14:
        failures.append("existing X2 N shards missing")
    if not n32:
        failures.append("existing X3 N shards missing")

    print("# uploaded core SHA256")
    for rel in UPLOAD_CORE:
        if Path(rel).is_file():
            print(sha256(rel), rel)
    print(f"# mom2 npz={len(stats)} bytes={sum(p.stat().st_size for p in stats)}")
    print(f"# wiki parquet={len(wiki)} bytes={sum(Path(p).stat().st_size for p in wiki)}")
    print(f"# baseline shards: X2-N={len(n14)} X3-N={len(n32)}")
    for rel in ("data/counterfact.prefiltered.jsonl", "data/counterfact.jsonl"):
        if Path(rel).is_file():
            print(f"# {rel}: lines={line_count(rel)} bytes={Path(rel).stat().st_size}")
    if failures:
        print("# INVENTORY FAIL")
        for failure in failures:
            print("-", failure)
        return 1
    print("# INVENTORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
