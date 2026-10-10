#!/bin/bash
# require_stage_conditions.sh — Stop（2026-10-11・166回目 新設・まこさん指示 2026-10-10「この強制は作って」）
#
# 中身は require_stage_conditions.py（hook の python は別ファイル化の規約）。
# 工事の「いまの段」（next_move.py が実物から読む）の、まこさんにお願いする前の条件が ❌ のまま、お願いの返信でターンを終えない。

exec python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/require_stage_conditions.py" "$@"
