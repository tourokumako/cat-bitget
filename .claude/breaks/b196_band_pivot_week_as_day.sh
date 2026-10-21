#!/bin/bash
# EXPECT_RC: 1
# MEANS: 帯pivot前週 の線を、前の週でなく前の日の pivot にすると、軽い口の既知答え（前の日は線の間が無く、前の週は線の間に在る足）が落ちる
# EXPECT_MSG: T-B1: 帯pivot前週(0.0015): 手計算の既知答えと不一致
# b196_band_pivot_week_as_day — 帯pivot前週 の線を、前の週でなく前の日の pivot にすると、軽い口の既知答え（前の日は線の間が無く、前の週は線の間に在る足）が落ちる（工事 m2c15-band-s1-20261020・2026-10-20）
#   守っているもの＝完成の条件の軽い口（T-B1〜T-B4）（observe_diag.py --selftest-band）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（b1s1_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-band が「T-B1: 帯pivot前週(0.0015): 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    "帯pivot前週": lambda d, fl, t: _band_lines(d, *_pivot_prev_period(d, "W")[1:], t, fl),\n'
new = '    "帯pivot前週": lambda d, fl, t: _band_lines(d, *_pivot_prev_period(d)[1:], t, fl),\n'
if s.count(old) != 1:
    raise SystemExit("[b196_band_pivot_week_as_day] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-band
finish
