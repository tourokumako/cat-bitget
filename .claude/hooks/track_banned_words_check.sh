#!/bin/bash
# track_banned_words_check.sh — PostToolUse(Bash) list_banned_words.py の実行を検知してマーカー touch
#   （2026-07-11 まこさん指示・require_banned_words_check.sh[PreToolUse] と対＝update_websearch_marker と同型の記録係）
# read-only: マーカー（state/banned_words_checked）を touch するだけ。reset_read_log.sh がセッション開始で削除。

INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | python3 -c "import sys,json
try: print(json.load(sys.stdin).get('tool_input',{}).get('command',''))
except Exception: print('')" 2>/dev/null)
case "$CMD" in
  *list_banned_words.py*) touch "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/banned_words_checked" ;;
esac
exit 0
