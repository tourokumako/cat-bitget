#!/bin/bash
# block_repeat_kind.sh — PreToolUse on Write|Edit|MultiEdit|NotebookEdit|Bash|Agent（2026-10-01 新設）
#
# 中身は block_repeat_kind.py（hook の python は別ファイル化の規約）。
# 同じ種類の失敗を同じセッションで2回 起こしたら、決まりを書き出すまで先に進ませない。

exec python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/block_repeat_kind.py" "$@"
