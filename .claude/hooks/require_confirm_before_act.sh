#!/bin/bash
# require_confirm_before_act.sh — PreToolUse on Write|Edit|MultiEdit|NotebookEdit|Bash|Agent（2026-10-01 新設）
#
# 中身は require_confirm_before_act.py（hook の python は別ファイル化の規約）。
# 書き込み・実行の前に、その相手について根拠と「なぜ正しく機能するか」を確認の記録に書かせる。

exec python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/require_confirm_before_act.py" "$@"
