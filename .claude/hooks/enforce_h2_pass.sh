#!/bin/bash
# enforce_h2_pass.sh — PreToolUse on Bash（2026-08-16 まこさん GO「H2 完全化」の層2・新設・safety hook）
#
# 目的: H2（未来参照なし）の検査（leak_causality_diag の全部）が pass した「検査済みの印」が、
#   いまのコードと設定の指紋と一致しない限り、engine_tuner・実行器・生成器・E38 を回せなくする。
#   まこさんの逐語（2026-08-16）＝「H2が守られない状態で、engine_tuner使っても意味がないので、
#   H2が完全に守られる状態にすることを第一優先としてほしい」。
#
# 判定は enforce_h2_pass.py（別ファイル＝pdca_mark の -c 埋め込み無言死の教訓・pdca_flow.md）。
# safety hook: fast-mode 無効化行を入れない。
# 解除: H2PASS_OK=1（まこさんの明示 OK 時のみ）。
# 番人: python3 .claude/hooks/enforce_h2_pass.py --selftest

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/enforce_h2_pass_error.log"

ERR=$(python3 "$HERE/enforce_h2_pass.py" 2>&1 1>/dev/null)
RC=$?

[ -n "$ERR" ] && printf '%s\n' "$ERR" >&2
if [ "$RC" != "0" ] && [ "$RC" != "2" ]; then
  printf '[%s] rc=%s\n%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$RC" "$ERR" >> "$LOG"
fi

exit $RC
