#!/bin/bash
# track_search_fetch.sh — PostToolUse on WebSearch|WebFetch
# enforce_search_quality.sh の③（精読強制）用カウンタ管理。
#   WebSearch 実行 → カウンタ +1
#   WebFetch 実行 → カウンタ 0 リセット（＝精読したので連投カウントを解除）
STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
CNT_FILE="$STATE_DIR/websearch_since_fetch"
mkdir -p "$STATE_DIR"

INPUT=$(cat)
TOOL=$(printf '%s' "$INPUT" | python3 -c "
import sys,json
try: print((json.load(sys.stdin) or {}).get('tool_name',''))
except Exception: print('')
" 2>/dev/null)

if [ "$TOOL" = "WebFetch" ]; then
  echo 0 > "$CNT_FILE"
elif [ "$TOOL" = "WebSearch" ]; then
  CUR=$(cat "$CNT_FILE" 2>/dev/null || echo 0)
  echo $(( ${CUR:-0} + 1 )) > "$CNT_FILE"
fi
exit 0
