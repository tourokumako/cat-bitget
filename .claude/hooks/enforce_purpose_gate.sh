#!/bin/bash
# enforce_purpose_gate.sh — PreToolUse on Write|Edit|MultiEdit|Bash
#   （2026-08-06 まこさん指示で新設 → 2026-08-26 に作り直し・まこさん承認 7c80f0891bb553d0…・safety hook）
#
# ★まこさんの逐語（2026-08-06）
#   「net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、
#     見つけることができる機械を作ることが目的」
#   「つまりは上記条件を一つでも達成できていないものは作成してはいけないということ。」
#   「そのために強制hookを作ることはOK」
#
# 何を強制するか・何を止めるか・限界は、判定の本体 enforce_purpose_gate.py の冒頭に全部 書いてある。
#   ★このファイルは呼ぶだけ（pdca_flow.md §5＝hook の python はコマンドに直接 埋め込まず別ファイルにする。
#     -c 埋め込みの引用符が壊れて pdca_mark が無言死した 2026-07-03 の教訓）。
#   ★止める時の説明（exit 2）は そのまま画面へ出す。
#   ★python 自体が落ちた時（exit 2 でも 0 でもない）は state/enforce_purpose_gate_error.log に残す
#     ＝hook_health_check が拾って無言死に気づける。ふだんの「止めた」は log に書かない。
#
# safety hook: fast-mode 無効化行を入れない（勝手な作りは fast-mode 中にこそ起きうる）。
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で全廃）。
# 番人: python3 .claude/hooks/enforce_purpose_gate.py --selftest

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/enforce_purpose_gate_error.log"

ERR=$(python3 "$HERE/enforce_purpose_gate.py" 2>&1 1>/dev/null)
RC=$?

[ -n "$ERR" ] && printf '%s\n' "$ERR" >&2
if [ "$RC" != "0" ] && [ "$RC" != "2" ]; then
  printf '[%s] rc=%s\n%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$RC" "$ERR" >> "$LOG"
fi

exit $RC
