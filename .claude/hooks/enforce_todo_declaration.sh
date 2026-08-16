#!/bin/bash
# enforce_todo_declaration.sh — PreToolUse on Write|Edit|MultiEdit|Bash（2026-08-16 まこさん承認「件２はOK」・新設・safety hook）
#
# 目的: ToDo をチャットに正確に出してから作業させる。
#   まこさんの逐語（2026-08-16）＝「TodoWriteが使えず、to doのフロー化が不正確になることもやめてほしいんだけど」
#   「私はこのチャットにtodoを正確に表示して進めてほしいんだけど」。
#
# 判定は enforce_todo_declaration.py（別ファイル＝pdca_mark の -c 埋め込み無言死の教訓・pdca_flow.md）。
#   ★止める時の説明（exit 2）は そのまま画面へ出す。
#   ★python 自体が落ちた時（exit 2 でも 0 でもない）は state/enforce_todo_declaration_error.log に残す
#     ＝hook_health_check が拾って無言死に気づける。ふだんの「止めた」は log に書かない（毎回 非空になると警告が意味を失う）。
#
# safety hook: fast-mode 無効化行を入れない（fast-mode は今後オフにしない方針＝入れると1回も動かない）。
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で廃止）。
# 番人: python3 .claude/hooks/enforce_todo_declaration.py --selftest

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/enforce_todo_declaration_error.log"

ERR=$(python3 "$HERE/enforce_todo_declaration.py" 2>&1 1>/dev/null)
RC=$?

[ -n "$ERR" ] && printf '%s\n' "$ERR" >&2
if [ "$RC" != "0" ] && [ "$RC" != "2" ]; then
  printf '[%s] rc=%s\n%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$RC" "$ERR" >> "$LOG"
fi

exit $RC
