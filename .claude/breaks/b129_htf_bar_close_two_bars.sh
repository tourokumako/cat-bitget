#!/bin/bash
# EXPECT_RC: 1
# MEANS: 上位足のずらし bar_close を5分足2本ぶん早める（形成中の上位足を使う）と、切り詰め再計算の番人が落ちる
# EXPECT_MSG: ❌ K-8: 上位足のずらし bar_close で
# b129_htf_bar_close_two_bars — 上位足のずらし bar_close を5分足2本ぶん早める（形成中の上位足を使う）と、切り詰め再計算の番人が落ちる（工事 m2c15-indicator-six-items-20261004・2026-10-04）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）の番人
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（r1_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ K-8: 上位足のずらし bar_close で」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '                        s.index = s.index - (bars.index[1] - bars.index[0])\n'
new = '                        s.index = s.index - 2 * (bars.index[1] - bars.index[0])\n'
if s.count(old) != 1:
    raise SystemExit("[b129_htf_bar_close_two_bars] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish
