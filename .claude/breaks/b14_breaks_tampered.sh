#!/bin/bash
# b14 — 壊すプログラムを承認の後に書き換えると、走らせるプログラムが止まるか（完成の条件 #12・E-12）
#   ★呼び合いを止める＝run_breaks.py は CAT_RUN_BREAKS_DEPTH が立っていると
#     凍結の照合だけして戻る（まこさんの注意 2026-09-03）。
source "$(dirname "$0")/lib.sh"

VICTIM="$ROOT/.claude/breaks/b09_run_bypass.sh"
guard "$VICTIM"

printf '\n# tamper\n' >> "$VICTIM"

measure python3 "$ROOT/.claude/tools/run_breaks.py" --check-frozen
finish
