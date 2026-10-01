#!/bin/bash
# block_repeat_failure.sh — PreToolUse on Write|Edit|MultiEdit|NotebookEdit|Bash|Agent（2026-10-01 新設）
#
# 中身は block_repeat_failure.py（hook の python は別ファイル化の規約）。
# 同じ相手で2回続けて失敗したら、見立てを書くまで その相手に手を出させない。

exec python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/block_repeat_failure.py" "$@"
