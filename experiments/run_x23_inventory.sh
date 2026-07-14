#!/usr/bin/env bash
# 在任一共享盘可见实例上执行；建议先在联网 CPU 实例跑。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/x23_paths.sh"
cd "$PROJ"
PYTHON="${PYTHON:-python}"
"$PYTHON" src/inventory_x23.py --model14 "$MODEL14" --model32 "$MODEL32" --wiki "$WIKI_EN"
