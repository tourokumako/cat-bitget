#!/bin/bash
# record_read.sh — PostToolUse on Read
# Read tool で実際に開いたファイルパスを read_log.txt に記録する。
# require_read_before_work.sh が「必読を Read したか」を判定する材料になる。
# 目的: CC が SessionStart 表示を「読んだ」と扱う読んだふり（L-250）を物理的に防ぐ仕組みの一部。

STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
mkdir -p "$STATE_DIR"
LOG="$STATE_DIR/read_log.txt"

input=$(cat)
fp=$(printf '%s' "$input" | python3 -c "import sys,json
try:
    d=json.load(sys.stdin)
    print(d.get('tool_input',{}).get('file_path',''))
except Exception:
    print('')" 2>/dev/null)

if [ -n "$fp" ]; then
  echo "$fp" >> "$LOG"
  # ②score.py起点ゲート: analysis_playbook を Read したら「再読済み」marker を立てる。
  #   score.py 実行で pdca_mark.sh が消す＝採点ごとに再読を強制（require_playbook_before_score.sh が判定）。
  case "$fp" in
    *analysis_playbook*) : > "$STATE_DIR/playbook_fresh" ;;
  esac
fi
exit 0
