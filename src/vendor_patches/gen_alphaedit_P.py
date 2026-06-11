"""预生成 AlphaEdit 零空间投影矩阵 P（null_space_project.pt），绕过 EasyEdit 内置版
对 qwen 缺分支的崩溃 bug（详见 src/vendor_patches/README.md 与 analysis/02_alphaedit.md §4）。

原理：EasyEdit `AlphaEdit_main.apply_` 只在 `null_space_project.pt` **不存在**时才走那段缺
qwen 分支的预分配；只要该文件已存在，它就直接 `torch.load` 跳过 bug。本脚本用 EasyEdit
自己的 `get_project`（其本身对 qwen 正确）按**正确 qwen 形状**预分配 P 并存盘。

需 GPU（P 依赖 mom2 协方差，与 task#04 同一份 cov，首跑自动触发并缓存）。
运行：
  cd source/EasyEdit
  PYTHONPATH=. python ../../src/vendor_patches/gen_alphaedit_P.py \
      ../../source/EasyEdit/hparams/AlphaEdit/qwen2.5-7b.yaml --device 0
  # 生成的 null_space_project.pt 落在 hparams.P_loc（默认 ./null_space_project.pt）
"""
import sys, os, argparse
import torch
from easyeditor import AlphaEditHyperParams, BaseEditor
from easyeditor.models.alphaedit.AlphaEdit_main import get_project
from easyeditor.util import nethook


def proj_dim(model_name, W_out):
    """与 EasyEdit 同口径，但**补上 qwen**（用输入维 shape[1]，down_proj 通用）。"""
    name = model_name.lower()
    if any(k in name for k in ("llama", "gpt-j-6b", "qwen")):   # ← 修复点：加 qwen
        return W_out.shape[1]
    if "gpt2-xl" in name:
        return W_out.shape[0]
    return W_out.shape[1]                                       # 默认按输入维


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hparams")
    ap.add_argument("--device", default="0")
    args = ap.parse_args()

    hp = AlphaEditHyperParams.from_hparams(args.hparams)
    hp.device = args.device
    ed = BaseEditor.from_hparams(hp)
    model, tok = ed.model, ed.tok

    W = nethook.get_parameter(model, f"{hp.rewrite_module_tmp.format(hp.layers[-1])}.weight")
    dim = proj_dim(hp.model_name, W)
    print(f"[gen_P] model={hp.model_name} layers={hp.layers} P shape=({len(hp.layers)},{dim},{dim})")

    P = torch.zeros((len(hp.layers), dim, dim), device="cpu")
    for i, layer in enumerate(hp.layers):
        P[i, :, :] = get_project(model, tok, layer, hp)
        print(f"[gen_P] layer {layer} done")

    out = getattr(hp, "P_loc", "./null_space_project.pt")
    torch.save(P, out)
    print(f"[gen_P] saved -> {os.path.abspath(out)}")


if __name__ == "__main__":
    main()
