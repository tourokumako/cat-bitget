#!/bin/bash
# require_check_before_action.sh — 確認しないと進めない（本体は .py・引数なし＝PreToolUse／stop＝Stop）
# まこさん指示（2026-09-30・逐語）＝「確認しないと進行できないような強制にしろ」「私の発言を無視するな」
set -u
ROOT="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
exec python3 "$ROOT/.claude/hooks/require_check_before_action.py" "${1:-}"
