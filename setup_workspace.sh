#!/usr/bin/env bash
# setup_workspace.sh — 在本地镜像 why-aaai 工作区（macOS/Linux 通用）
# 用法: bash setup_workspace.sh [目标路径]   默认: /Users/whyu/GitProjects/why-aaai
set -uo pipefail

ROOT="${1:-/Users/whyu/GitProjects/why-aaai}"
mkdir -p "$ROOT/papers" "$ROOT/source" "$ROOT/analysis"
cd "$ROOT/source"

clone() {  # clone <org/repo>  （已存在则跳过；浅克隆省时省盘）
  local name; name=$(basename "$1")
  if [ -d "$name" ]; then echo "skip   $name (exists)"; else
    git clone --depth 1 "https://github.com/$1.git" "$name" \
      && echo "cloned $name" || echo "FAILED $name"
  fi
}

# ---- 复现队列 ----
clone zjunlp/EasyEdit
clone jianghoucheng/AlphaEdit
clone ssangyeon/R-TOFU
clone Trustworthy-ML-Lab/ThinkEdit
clone OPTML-Group/Unlearn-R2MU
clone princeton-nlp/MQuAKE          # 数据用
clone kmeng01/memit                 # 参考用

cd "$ROOT/papers"
dl() {  # dl <arxiv_id> <filename>
  if [ -s "$2" ]; then echo "skip   $2 (exists)"; else
    curl -fsSL -o "$2" "https://arxiv.org/pdf/$1" \
      && echo "got    $2" || echo "FAILED $2"
  fi
}

# ---- 复现队列论文 ----
dl 2308.07269 repro1_EasyEdit_2308.07269.pdf
dl 2410.02355 repro2_AlphaEdit_2410.02355.pdf
dl 2305.14795 repro3_MQuAKE_2305.14795.pdf
dl 2505.15214 repro4_R-TOFU_2505.15214.pdf
dl 2506.12963 repro5_R2MU_2506.12963.pdf
dl 2503.22048 repro6_ThinkEdit_2503.22048.pdf
# ---- 只读参考 ----
dl 2210.07229 ref_MEMIT_2210.07229.pdf
dl 2202.05262 ref_ROME_2202.05262.pdf
dl 2506.01386 ref_ThinkEval_2506.01386.pdf
dl 2602.02028 ref_EditBackgroundStories_2602.02028.pdf
dl 2408.12456 ref_KELE_2408.12456.pdf
dl 2506.17279 ref_Sleek_2506.17279.pdf
dl 2601.09281 ref_STaR_2601.09281.pdf
dl 2602.17692 ref_AgenticUnlearning_2602.17692.pdf
dl 2602.17692 ref_AgenticUnlearning_2602.17692.pdf

echo "----"
echo "workspace ready at: $ROOT"
ls -R "$ROOT" | head -40
