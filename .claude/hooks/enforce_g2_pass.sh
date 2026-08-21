#!/bin/bash
# enforce_g2_pass.sh — PreToolUse on Bash（2026-08-21 まこさん承認 e9fa2ae6…・M2-2-2b・新設・safety hook）
#
# 目的: G2（型の表に沿った案かの審査が、11件の見本に正しく反応するか）の検査が pass した
#   「検査済みの印」が、いまのコードと設定の指紋と一致しない限り、
#   engine_tuner・生成器・実行器・E38 を回せなくする。
#   まこさんの逐語（2026-08-21）＝「H2 と同じ形にする＝G2 が通ったときだけ『検査済みの印』を書き、
#   その印が今のコードと合わないうちは engine_tuner を走らせない」。
#
# 判定は enforce_g2_pass.py（別ファイル＝pdca_mark の -c 埋め込み無言死の教訓・pdca_flow.md）。
# safety hook: fast-mode 無効化行を入れない。
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で廃止）。
# 番人: python3 .claude/hooks/enforce_g2_pass.py --selftest

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/enforce_g2_pass_error.log"

ERR=$(python3 "$HERE/enforce_g2_pass.py" 2>&1 1>/dev/null)
RC=$?

[ -n "$ERR" ] && printf '%s\n' "$ERR" >&2
if [ "$RC" != "0" ] && [ "$RC" != "2" ]; then
  printf '[%s] rc=%s\n%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$RC" "$ERR" >> "$LOG"
fi

exit $RC
